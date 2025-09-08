# Assessment - Clinical Data ETL Pipeline

## Project Overview

Complete a partially-built microservices data pipeline for processing clinical trial data.

## Time Expectation

**4-6 hours** to complete all three tasks.

**We encourage you to use AI assistants** such as ChatGPT, Claude, GitHub Copilot, etc. You are welcome to leverage AI tools throughout your development process to help solve problems, implement features, and optimize your workflow. Demonstrating effective use of AI can be a valuable part of this assessment. We're evaluating your problem-solving approach and implementation quality, not your ability to memorize syntax.

## Assessment Delivery

This assessment is provided as a **zip file** containing a partially-implemented microservices project. You will:

1. **Extract** the project files
2. **Push** to your public GitHub repository
3. **Implement** the required features with regular commits
4. **Share** your public repository URL for review with [george.mitra@regeneron.com](mailto:george.mitra@regeneron.com)

## What We'll Review

- **Problem-solving approach**: How you break down and tackle complex challenges
- **Commit history**: Regular commits showing development progress and thought process
- **Code quality**: Architecture decisions, clean implementation, and best practices
- **Feature completion**: All three required tasks implemented and working correctly
- **Error handling**: Edge cases and graceful error management
- **Database design**: Schema optimization for analytical queries
- **Docker integration**: Proper service setup and connectivity
- **Tool utilization and use of AI**: Effective use of available resources, tooling and modern development practices

## Getting Started

### What You'll Start With

Bootstrap application with three Docker services:

#### 1. API Service (TypeScript/Node.js) - 95% Complete ✅

- ETL job triggering (`POST /api/etl/jobs`) and data querying (`GET /api/data`) endpoints complete
- **Your task**: Add status tracking endpoint (`GET /api/etl/jobs/{id}/status`)

#### 2. ETL Service (Python/FastAPI) - 50% Complete ⚠️

- Job submission and status endpoints functional
- Sample data processing framework
- **Your task**: Complete the data processing pipeline and add quality validation

#### 3. PostgreSQL Database - Basic Schema ⚠️

- Tables created automatically on startup
- **Your task**: Design optimal schema and indexes for analytical queries

Technical details are available in [README_technical.md](./README_technical.md).

### 1. Setup Your Repository

```bash
# Extract the provided zip file
unzip clinical-api-etl.zip
cd clinical-api-etl

# Initialize git repository
git init
git add .
git commit -m "Initial project setup"

# Create a public GitHub repository and push
git remote add origin https://github.com/your-username/clinical-api-etl.git
git branch -M main
git push -u origin main
```

### 2. Start the Services

```bash
# Start all services
docker compose up --build

# Verify services are running
curl http://localhost:3000/health  # API Service
curl http://localhost:8000/health  # ETL Service
```

## Your Tasks

### Task 1: Add Status Endpoint (TypeScript)

Implement the `GET /api/etl/jobs/{id}/status` endpoint in the API service.

### Files to Modify:

1. `api-service/src/routes/etl.routes.ts` - Add route
2. `api-service/src/controllers/etl.controller.ts` - Add controller method
3. `api-service/src/services/etl.service.ts` - Add service method

### Requirements:

- Connect to ETL service (`http://etl:8000/jobs/{id}/status`)
- Handle invalid job IDs (404 error)
- Handle connection errors gracefully
- Return consistent JSON response format

### Expected Response:

```json
{
  "success": true,
  "message": "Status retrieved successfully",
  "data": {
    "jobId": "uuid",
    "status": "running|completed|failed",
    "progress": 75,
    "message": "Processing data..."
  }
}
```

### Task 2: Complete ETL Service (Python)

Complete the ETL data processing pipeline and add quality validation in the Python service.

**Missing implementations:**

- Data transformation pipeline
- Quality validation rules
- Database loading
- Error handling

### Task 3: Database Schema Design (PostgresSQL)

Design and implement an optimized schema and indexes for analytical queries in PostgreSQL.

- Normalized tables for clinical data
- Proper indexes for queries
- Foreign key relationships
- Performance optimization

**Example Business Questions to Optimize For:**

- Which studies have the highest data quality scores?

```sql
SELECT
  study_id,
  avg_quality
FROM data_quality_reports
ORDER BY avg_quality DESC
LIMIT 10;
```

- What are the glucose trends for a specific participant over time?

```sql
SELECT
  pm.recorded_at,
  pm.measurement_value AS glucose_value
FROM processed_measurements pm
JOIN measurement_types mt
  ON pm.measurement_type_id = mt.measurement_type_id
WHERE
  mt.name = 'glucose'
  AND pm.participant_id = 'PARTICIPANT_123'
ORDER BY pm.recorded_at;
```

- How do measurement counts compare across different research sites?

```sql
SELECT
  site_id,
  COUNT(*) AS measurement_count
FROM clinical_measurements
GROUP BY site_id
ORDER BY measurement_count DESC;
```

- Which measurements have quality scores below our threshold?

```sql
SELECT
  id,
  study_id,
  participant_id,
  measurement_type,
  value,
  quality_score,
  timestamp
FROM clinical_measurements
WHERE quality_score < 0.8
ORDER BY quality_score ASC;
```

- What clinical data was collected in the last 30 days?

```sql
SELECT
  *
FROM clinical_measurements
WHERE timestamp >= NOW() - INTERVAL '30 days'
ORDER BY timestamp DESC;
```

- How many participants are enrolled in each study?

```sql
SELECT
  study_id,
  COUNT(*) AS participant_count
FROM participants
GROUP BY study_id
ORDER BY participant_count DESC;
```

- What's the average BMI for participants in a specific study?

```sql
SELECT
  AVG(pm.measurement_value) AS avg_bmi
FROM processed_measurements pm
JOIN measurement_types mt
  ON pm.measurement_type_id = mt.measurement_type_id
WHERE
  mt.name = 'bmi'
  AND pm.study_id = 'STUDY_ABC';
```

**Your schema should efficiently support these types of analytical queries.**

#### Sample Data

The following sample data is included:

- `data/sample_study001.csv` - Glucose, cholesterol, weight, height
- `data/sample_study002.csv` - Blood pressure, heart rate

The system processes clinical trial data in this standardized format:

```csv
study_id,participant_id,measurement_type,value,unit,timestamp,site_id,quality_score
STUDY001,P001,glucose,95.5,mg/dL,2024-01-15T09:30:00Z,SITE_A,0.98
STUDY001,P001,cholesterol,180,mg/dL,2024-01-15T09:30:00Z,SITE_A,0.95
STUDY001,P002,glucose,102.1,mg/dL,2024-01-15T10:15:00Z,SITE_A,0.97
STUDY002,P003,blood_pressure,120/80,mmHg,2024-01-15T11:00:00Z,SITE_B,0.92
```

## Testing Your Implementation

```bash
# 1. Submit a job
curl -X POST http://localhost:3000/api/etl/jobs \
  -H "Content-Type: application/json" \
  -d '{"filename": "sample_study001.csv", "studyId": "STUDY001"}'

# 2. Get job status (your implementation)
curl http://localhost:3000/api/etl/jobs/{job-id}/status

# 3. Query processed data
curl "http://localhost:3000/api/data?studyId=STUDY001"
```

## Submission Instructions

Submit your project by emailing your Git repository URL and any notes to [george.mitra@regeneron.com](mailto:george.mitra@regeneron.com).

### Final Submission Checklist

- [ ] Ensure all services start successfully with `docker compose up --build`
- [ ] Repository is public and URL is shared
- [ ] Brief explanation of AI tool usage is included in the repository
- [ ] Additional comments or notes about your approach are included (optional)

## JSONB Attributes Rationale

The `attributes` JSONB column in `processed_measurements` (and the `demographic` JSONB in `participants`) provide a flexible, schemaless extension point without frequent schema changes:

### Evolving requirements

New data sources may include extra fields (e.g. device IDs, technician notes, batch tags) that don’t yet have dedicated columns. By dumping them into JSONB, we can onboard those fields immediately—and only later promote the most important ones into first-class columns as needed.

### Rich debugging & audit trails

Storing the original raw value or custom parsing hints alongside each record makes it easy to reproduce or troubleshoot oddball rows in production. We can even index on nested keys (for example, `attributes->>'raw' ILIKE '%error%'`) to find problem cases quickly.

### Ad-hoc analytics

Analysts often want to slice and dice on one-off or rarely used properties—say a sensor’s firmware version or a lab’s assay code—without requiring a database migration. JSONB lets us write temporary reports or dashboards on these properties directly in SQL.

### Performance at scale

PostgreSQL’s JSONB is fast (compressed on disk, GIN-indexable) and lets us keep our core schema lean while still supporting arbitrary metadata.

In short, JSONB gives us a “catch-all” slot for growth, observability, and agility—while preserving the performance, integrity, and simplicity of our relational core.
