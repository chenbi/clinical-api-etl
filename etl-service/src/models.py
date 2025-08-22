from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class ETLJob(Base):
    __tablename__ = "etl_jobs"
    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    study_id = Column(String, ForeignKey("studies.study_id"))
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    error_message = Column(String)

    def __repr__(self):
        return f"<ETLJob(id={self.id}, status={self.status})>"


class Study(Base):
    __tablename__ = "studies"
    study_id = Column(String, primary_key=True)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    participants = relationship("Participant", back_populates="study")
    processed_measurements = relationship(
        "ProcessedMeasurement", back_populates="study"
    )

    def __repr__(self):
        return f"<Study(study_id={self.study_id})>"


class Participant(Base):
    __tablename__ = "participants"
    participant_id = Column(String, primary_key=True)
    study_id = Column(String, ForeignKey("studies.study_id"), nullable=False)
    demographic = Column(String)

    study = relationship("Study", back_populates="participants")
    processed_measurements = relationship(
        "ProcessedMeasurement", back_populates="participant"
    )

    def __repr__(self):
        return f"<Participant(participant_id={self.participant_id})>"


class MeasurementUnit(Base):
    __tablename__ = "measurement_units"
    unit_id = Column(Integer, primary_key=True, autoincrement=True)
    unit = Column(String, unique=True, nullable=False)

    types = relationship("MeasurementType", back_populates="unit")

    def __repr__(self):
        return f"<MeasurementUnit(unit={self.unit})>"


class MeasurementType(Base):
    __tablename__ = "measurement_types"
    measurement_type_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    unit_id = Column(Integer, ForeignKey("measurement_units.unit_id"), nullable=False)

    unit = relationship("MeasurementUnit", back_populates="types")
    processed_measurements = relationship(
        "ProcessedMeasurement", back_populates="measurement_type"
    )

    def __repr__(self):
        return f"<MeasurementType(name={self.name}, unit_id={self.unit_id})>"


class ProcessedMeasurement(Base):
    __tablename__ = "processed_measurements"
    measurement_id = Column(Integer, primary_key=True, autoincrement=True)
    study_id = Column(String, ForeignKey("studies.study_id"), nullable=False)
    participant_id = Column(
        String, ForeignKey("participants.participant_id"), nullable=False
    )
    measurement_type_id = Column(
        Integer, ForeignKey("measurement_types.measurement_type_id"), nullable=False
    )
    measurement_value = Column(Float, nullable=False)
    quality_score = Column(Float, nullable=False)
    recorded_at = Column(DateTime, nullable=False)
    loaded_at = Column(DateTime, default=datetime.utcnow)

    study = relationship("Study", back_populates="processed_measurements")
    participant = relationship("Participant", back_populates="processed_measurements")
    measurement_type = relationship(
        "MeasurementType", back_populates="processed_measurements"
    )

    def __repr__(self):
        return (
            f"<ProcessedMeasurement(id={self.measurement_id}, "
            f"study_id={self.study_id}, participant_id={self.participant_id})>"
        )


class ClinicalMeasurement(Base):
    __tablename__ = "clinical_measurements"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    study_id = Column(String, nullable=False)
    participant_id = Column(String, nullable=False)
    measurement_type = Column(String, nullable=False)
    value = Column(String, nullable=False)
    unit = Column(String)
    timestamp = Column(DateTime, nullable=False)
    site_id = Column(String, nullable=False)
    quality_score = Column(Float)
    processed_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return (
            f"<ClinicalMeasurement(id={self.id}, study_id={self.study_id}, "
            f"participant_id={self.participant_id})>"
        )
