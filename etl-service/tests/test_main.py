import os
import sys
import pytest
from fastapi.testclient import TestClient
from unittest import mock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import src.main  # noqa: E402

from src.main import app, count_lines, SessionLocal  # noqa: E402

client = TestClient(app)


# --- mock Redis for every test ---
@pytest.fixture(autouse=True)
def mock_redis(monkeypatch):
    fake_redis = mock.MagicMock()
    monkeypatch.setattr(src.main, "redis_client", fake_redis)
    return fake_redis


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "etl"


@mock.patch("os.path.exists", return_value=False)
def test_submit_job_file_not_found(mock_exists):
    payload = {"jobId": "test-job", "filename": "nonexistent.csv", "studyId": None}
    response = client.post("/jobs", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "File not found"


def test_get_job_status_not_found():
    response = client.get("/jobs/nonexistent/status")
    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


def test_get_job_details_not_found():
    response = client.get("/jobs/nonexistent")
    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


@pytest.fixture
def tmp_csv(tmp_path):
    # Create a temporary CSV file with one valid row
    file_path = tmp_path / "data.csv"
    file_path.write_text(
        "participant_id,measurement_type,value,unit,timestamp,quality_score\n"
        "p1,type1,100,unit1,2021-01-01T00:00:00,0.95\n"
    )
    return str(file_path)


@mock.patch("src.main.count_lines", return_value=1)
@mock.patch("os.path.exists", return_value=True)
@mock.patch("src.main.SessionLocal")
def test_submit_job_success(mock_session, mock_exists, mock_count, tmp_csv, mock_redis):
    payload = {
        "jobId": "job-123",
        "filename": os.path.basename(tmp_csv),
        "studyId": "study-xyz",
    }

    # Ensure data_dir exists and copy file there
    data_dir = os.getenv("DATA_DIR", "./data")
    os.makedirs(data_dir, exist_ok=True)
    dest = os.path.join(data_dir, payload["filename"])
    with open(tmp_csv, "rb") as src, open(dest, "wb") as dst:
        dst.write(src.read())

    response = client.post("/jobs", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["jobId"] == "job-123"
    assert data["status"] == "running"
    assert "Job submitted successfully" in data["message"]

    os.remove(dest)


@mock.patch("src.main.count_lines", return_value=1)
@mock.patch("os.path.exists", return_value=True)
@mock.patch("src.main.SessionLocal")
def test_submit_job_no_records(
    mock_session, mock_exists, mock_count, tmp_path, mock_redis
):
    # CSV with only header → no raw_objs → 400
    empty_csv = tmp_path / "empty.csv"
    empty_csv.write_text(
        "participant_id,measurement_type,value,unit,timestamp,quality_score\n"
    )
    payload = {
        "jobId": "job-404",
        "filename": os.path.basename(str(empty_csv)),
        "studyId": None,
    }
    data_dir = os.getenv("DATA_DIR", "./data")
    os.makedirs(data_dir, exist_ok=True)
    dest = os.path.join(data_dir, payload["filename"])
    with open(str(empty_csv), "rb") as src, open(dest, "wb") as dst:
        dst.write(src.read())

    response = client.post("/jobs", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "No records found in file"

    os.remove(dest)


def test_get_job_status_success(mock_redis):
    # Arrange: Redis returns a valid dict
    src.main.redis_client.hgetall.return_value = {
        b"status": b"completed",
        b"progress": b"75",
        b"message": b"Almost done",
    }
    response = client.get("/jobs/any/status")
    assert response.status_code == 200
    data = response.json()
    assert data["jobId"] == "any"
    assert data["status"] == "completed"
    assert data["progress"] == 75
    assert data["message"] == "Almost done"


def test_get_job_details_success(mock_redis):
    src.main.redis_client.hgetall.return_value = {
        b"status": b"completed",
        b"progress": b"100",
        b"message": b"Done",
        b"jobId": b"any",
    }
    response = client.get("/jobs/any")
    assert response.status_code == 200
    details = response.json()
    assert details["status"] == "completed"
    assert details["progress"] == "100"
    assert details["message"] == "Done"
    assert details["jobId"] == "any"
