import os
import csv
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
import uvicorn
import redis
import asyncio
import aiofiles
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

# Import ORM models
from src.models import (
    Base,
    ETLJob,
    Study,
    Participant,
    MeasurementUnit,
    MeasurementType,
    ProcessedMeasurement,
    ClinicalMeasurement,
)

# App setup
app = FastAPI(title="Clinical Data ETL Service", version="1.0.0")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database & Redis configuration
DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
redis_client = redis.Redis.from_url(REDIS_URL)

# ETL parameters
data_dir = os.getenv("DATA_DIR", "./data")
stream_threshold = int(os.getenv("STREAM_THRESHOLD", 100 * 1024 * 1024))

# Caches for dimension lookups by ID
_type_cache: Dict[str, int] = {}
_unit_cache: Dict[str, int] = {}


# Pydantic schemas
class ETLJobRequest(BaseModel):
    jobId: str
    filename: str
    studyId: Optional[str] = None


class ETLJobResponse(BaseModel):
    jobId: str
    status: str
    message: str


class ETLJobStatus(BaseModel):
    jobId: str
    status: str
    progress: Optional[int] = None
    message: Optional[str] = None


async def count_lines(path: str) -> int:
    proc = await asyncio.create_subprocess_exec(
        "wc",
        "-l",
        path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    stdout, _ = await proc.communicate()
    return int(stdout.strip().split()[0])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "etl"}


# ORM helpers
def get_or_create_participant(session, participant_id: str, study_id: str) -> None:
    exists = session.query(Participant).filter_by(participant_id=participant_id).first()
    if not exists:
        session.add(
            Participant(
                participant_id=participant_id, study_id=study_id, demographic="{}"
            )
        )
        session.flush()


def get_or_create_unit(session, unit_text: str) -> int:
    if unit_text in _unit_cache:
        return _unit_cache[unit_text]
    row = session.query(MeasurementUnit).filter_by(unit=unit_text).first()
    if row:
        uid = row.unit_id
    else:
        obj = MeasurementUnit(unit=unit_text)
        session.add(obj)
        session.flush()
        uid = obj.unit_id
    _unit_cache[unit_text] = uid
    return uid


def get_or_create_type(session, name: str, unit_id: int) -> int:
    key = f"{name}||{unit_id}"
    if key in _type_cache:
        return _type_cache[key]
    row = session.query(MeasurementType).filter_by(name=name, unit_id=unit_id).first()
    if row:
        tid = row.measurement_type_id
    else:
        obj = MeasurementType(name=name, unit_id=unit_id)
        session.add(obj)
        session.flush()
        tid = obj.measurement_type_id
    _type_cache[key] = tid
    return tid


# ETL endpoint
@app.post("/jobs", response_model=ETLJobResponse)
async def submit_job(job_request: ETLJobRequest):
    job_id = job_request.jobId
    filename = job_request.filename
    study_id = job_request.studyId

    # Initialize job in Redis
    redis_client.hset(
        job_id,
        mapping={
            "jobId": job_id,
            "filename": filename,
            "studyId": study_id or "",
            "status": "running",
            "progress": 0,
            "message": "Job started",
        },
    )

    filepath = os.path.join(data_dir, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=400, detail="File not found")

    session = SessionLocal()
    try:
        # Ensure study exists
        if study_id:
            session.merge(Study(study_id=study_id))
            session.flush()

        raw_objs: List[ClinicalMeasurement] = []
        proc_objs: List[ProcessedMeasurement] = []

        # large file streaming async
        total = await count_lines(filepath)
        async with aiofiles.open(filepath, mode="r") as af:
            header = await af.readline()
            headers = [h.strip() for h in header.split(",")]
            idx = 0
            async for line in af:
                idx += 1
                rec = dict(zip(headers, line.strip().split(",")))
                # Raw row
                try:
                    raw_objs.append(
                        ClinicalMeasurement(
                            id=str(uuid4()),
                            study_id=study_id,
                            participant_id=rec["participant_id"],
                            measurement_type=rec["measurement_type"],
                            value=rec["value"],
                            unit=rec.get("unit"),
                            timestamp=datetime.fromisoformat(rec["timestamp"]),
                            site_id=rec.get("site_id", ""),
                            quality_score=float(rec.get("quality_score", 0)),
                        )
                    )
                except:
                    continue
                # Processed row
                try:
                    qs = float(rec.get("quality_score", 0))
                except:
                    qs = None
                if qs is not None and qs >= 0.9:
                    raw_val = rec["value"]
                    syst = dias = val = None
                    if "/" in raw_val:
                        try:
                            h, l = raw_val.split("/", 1)
                            syst = float(h)
                            dias = float(l)
                        except:
                            pass
                    else:
                        try:
                            val = float(raw_val)
                        except:
                            pass

                    if val is not None or (syst is not None and dias is not None):
                        get_or_create_participant(
                            session, rec["participant_id"], study_id
                        )
                        uid = get_or_create_unit(session, rec.get("unit", "") or "")
                        tid = get_or_create_type(session, rec["measurement_type"], uid)
                        proc_objs.append(
                            ProcessedMeasurement(
                                study_id=study_id,
                                participant_id=rec["participant_id"],
                                measurement_type_id=tid,
                                measurement_value=val,
                                systolic=syst,
                                diastolic=dias,
                                quality_score=qs,
                                recorded_at=datetime.fromisoformat(rec["timestamp"]),
                                attributes={"raw": raw_val},
                            )
                        )
                redis_client.hset(job_id, "progress", int(idx / total * 100))

        if not raw_objs:
            raise HTTPException(status_code=400, detail="No records found in file")

        # Bulk save both raw and processed
        session.bulk_save_objects(raw_objs)
        session.bulk_save_objects(proc_objs)
        session.commit()

        redis_client.hset(
            job_id,
            mapping={
                "status": "completed",
                "progress": 100,
                "message": f"Loaded {len(proc_objs)} processed rows (and {len(raw_objs)} raw rows)",
            },
        )
    except Exception as e:
        session.rollback()
        redis_client.hset(job_id, mapping={"status": "failed", "message": str(e)})
        logger.error(f"Job {job_id} failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()

    return ETLJobResponse(
        jobId=job_id, status="running", message="Job submitted successfully"
    )


@app.get("/jobs/{job_id}/status", response_model=ETLJobStatus)
async def get_job_status(job_id: str):
    data = redis_client.hgetall(job_id)
    # Guard against non-dict or missing status key
    if not isinstance(data, dict) or b"status" not in data:
        raise HTTPException(status_code=404, detail="Job not found")
    return ETLJobStatus(
        jobId=job_id,
        status=data[b"status"].decode(),
        progress=int(data.get(b"progress", 0)),
        message=data.get(b"message", b"").decode(),
    )


@app.get("/jobs/{job_id}")
async def get_job_details(job_id: str):
    data = redis_client.hgetall(job_id)
    # Guard against non-dict or missing status key
    if not isinstance(data, dict) or b"status" not in data:
        raise HTTPException(status_code=404, detail="Job not found")
    return {k.decode(): v.decode() for k, v in data.items()}


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
