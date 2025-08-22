import os
import sys
import pytest
from fastapi.testclient import TestClient
from unittest import mock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import src.main

# Import the FastAPI app
from src.main import app, count_lines, SessionLocal  # noqa: E402

client = TestClient(app)


# mock Redis for every test
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


@pytest.fixture
def tmp_csv(tmp_path):
    # Create a temporary CSV file
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
    # Prepare payload
    payload = {
        "jobId": "job-123",
        "filename": os.path.basename(tmp_csv),
        "studyId": "study-xyz",
    }
    # Copy file into expected data_dir
    data_dir = os.getenv("DATA_DIR", "./data")
    os.makedirs(data_dir, exist_ok=True)
    dest = os.path.join(data_dir, payload["filename"])
    with open(tmp_csv, "rb") as src, open(dest, "wb") as dst:
        dst.write(src.read())

    response = client.post("/jobs", json=payload)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["jobId"] == "job-123"
    assert json_data["status"] == "running"
    assert "Job submitted successfully" in json_data["message"]

    # Cleanup
    os.remove(dest)


def test_get_job_details_not_found():
    response = client.get("/jobs/nonexistent")
    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"
