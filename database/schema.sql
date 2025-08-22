-- Clinical Data ETL Pipeline Database Schema
-- TODO: Candidate to design and implement optimal schema

-- Basic schema provided for bootstrapping
-- Candidate should enhance with proper indexes, constraints, and optimization

-- ETL Jobs tracking table
CREATE TABLE IF NOT EXISTS etl_jobs (
    id UUID PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    study_id VARCHAR(50),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);

-- TODO: Candidate to implement
-- Expected tables to be designed by candidate:
-- - clinical_measurements (raw data)
-- - processed_measurements (transformed data)
-- - participants
-- - studies
-- - data_quality_reports
-- - measurement_aggregations

-- Raw clinical measurements (landing) table
CREATE TABLE IF NOT EXISTS clinical_measurements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    study_id VARCHAR(50) NOT NULL,
    participant_id VARCHAR(50) NOT NULL,
    measurement_type VARCHAR(50) NOT NULL,
    value TEXT NOT NULL,
    unit VARCHAR(20),
    timestamp TIMESTAMP NOT NULL,
    site_id VARCHAR(50) NOT NULL,
    quality_score DECIMAL(3,2),
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Normalized dimension tables
CREATE TABLE IF NOT EXISTS studies (
  study_id TEXT PRIMARY KEY,
  description TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS participants (
  participant_id TEXT PRIMARY KEY,
  study_id TEXT NOT NULL REFERENCES studies(study_id),
  enrolled_at TIMESTAMPTZ,
  demographic JSONB
);

CREATE TABLE IF NOT EXISTS measurement_units (
  unit_id SERIAL PRIMARY KEY,
  unit TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS measurement_types (
  measurement_type_id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  unit_id INT NOT NULL REFERENCES measurement_units(unit_id)
);

-- Processed measurements (transformed data)
CREATE TABLE IF NOT EXISTS processed_measurements (
  measurement_id BIGSERIAL PRIMARY KEY,
  study_id TEXT NOT NULL REFERENCES studies(study_id),
  participant_id TEXT NOT NULL REFERENCES participants(participant_id),
  measurement_type_id INT NOT NULL REFERENCES measurement_types(measurement_type_id),
  measurement_value DOUBLE PRECISION,
  systolic DOUBLE PRECISION,
  diastolic DOUBLE PRECISION,
  quality_score REAL NOT NULL CHECK (quality_score BETWEEN 0 AND 1),
  recorded_at TIMESTAMPTZ NOT NULL,
  loaded_at TIMESTAMPTZ DEFAULT NOW(),
  attributes JSONB DEFAULT '{}'::JSONB
);

-- Data quality reports
CREATE TABLE IF NOT EXISTS data_quality_reports (
  report_id SERIAL PRIMARY KEY,
  study_id TEXT REFERENCES studies(study_id),
  generated_at TIMESTAMPTZ DEFAULT NOW(),
  total_records INT,
  valid_records INT,
  invalid_records INT,
  avg_quality REAL
);

-- Measurement aggregations (e.g., daily summaries)
CREATE TABLE IF NOT EXISTS measurement_aggregations (
  aggregation_date DATE NOT NULL,
  study_id TEXT NOT NULL,
  measurement_type_id INT NOT NULL,
  count INT,
  avg_value DOUBLE PRECISION,
  min_value DOUBLE PRECISION,
  max_value DOUBLE PRECISION,
  PRIMARY KEY (aggregation_date, study_id, measurement_type_id)
);

CREATE INDEX IF NOT EXISTS idx_clinical_measurements_study_id ON clinical_measurements(study_id);
CREATE INDEX IF NOT EXISTS idx_clinical_measurements_participant_id ON clinical_measurements(participant_id);
CREATE INDEX IF NOT EXISTS idx_clinical_measurements_timestamp ON clinical_measurements(timestamp);

-- ETL Jobs indexes
CREATE INDEX IF NOT EXISTS idx_etl_jobs_status ON etl_jobs(status);
CREATE INDEX IF NOT EXISTS idx_etl_jobs_created_at ON etl_jobs(created_at);

CREATE INDEX IF NOT EXISTS idx_processed_measurements_study_type ON processed_measurements(study_id, measurement_type_id);
CREATE INDEX IF NOT EXISTS idx_processed_measurements_time ON processed_measurements(recorded_at);

-- Optional: materialized view for daily aggregation
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_measurement_summary AS
SELECT
  date_trunc('day', recorded_at) AS day,
  study_id,
  measurement_type_id,
  COUNT(*) AS count,
  AVG(measurement_value) AS avg_value,
  MIN(measurement_value) AS min_value,
  MAX(measurement_value) AS max_value
FROM processed_measurements
GROUP BY day, study_id, measurement_type_id;
