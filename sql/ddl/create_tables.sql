-- sql/ddl/create_tables.sql
-- BigQuery DDL (representative). This is a warehouse-friendly schema
-- for sepsis risk monitoring outputs (analytics + dashboards).

CREATE SCHEMA IF NOT EXISTS `project_id.icu_analytics`;

-- 1) Patient dimension (minimal, de-identified)
CREATE TABLE IF NOT EXISTS `project_id.icu_analytics.dim_patient` (
  patient_id STRING NOT NULL,
  sex STRING,
  age_years INT64,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- 2) Admission / encounter dimension
CREATE TABLE IF NOT EXISTS `project_id.icu_analytics.dim_admission` (
  admission_id STRING NOT NULL,
  patient_id STRING NOT NULL,
  icu_unit STRING,
  admit_time TIMESTAMP,
  discharge_time TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- 3) Raw event fact table (staged physiological/lab events)
CREATE TABLE IF NOT EXISTS `project_id.icu_analytics.fact_icu_event` (
  event_id STRING NOT NULL,
  patient_id STRING NOT NULL,
  admission_id STRING NOT NULL,
  event_ts TIMESTAMP NOT NULL,

  hr FLOAT64,
  sbp FLOAT64,
  dbp FLOAT64,
  map FLOAT64,
  rr FLOAT64,
  temp_c FLOAT64,
  spo2 FLOAT64,

  wbc FLOAT64,
  lactate FLOAT64,
  creatinine FLOAT64,
  bilirubin FLOAT64,

  source STRING,              -- e.g., "monitor", "lab", "etl"
  ingest_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(event_ts)
CLUSTER BY patient_id, admission_id;

-- 4) Feature snapshot table (what we engineered per event)
CREATE TABLE IF NOT EXISTS `project_id.icu_analytics.fact_sepsis_features` (
  event_id STRING NOT NULL,
  patient_id STRING NOT NULL,
  admission_id STRING NOT NULL,
  event_ts TIMESTAMP NOT NULL,

  -- feature columns (representative)
  hr_z FLOAT64,
  map_z FLOAT64,
  rr_z FLOAT64,
  temp_z FLOAT64,
  lactate_z FLOAT64,

  sirs_flag BOOL,
  organ_dysfunction_flag BOOL,
  missingness_score FLOAT64,

  feature_version STRING,
  computed_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(event_ts)
CLUSTER BY patient_id, admission_id;

-- 5) Risk score table (what downstream apps/dashboards consume)
CREATE TABLE IF NOT EXISTS `project_id.icu_analytics.fact_sepsis_risk_score` (
  score_id STRING NOT NULL,
  event_id STRING NOT NULL,
  patient_id STRING NOT NULL,
  admission_id STRING NOT NULL,
  event_ts TIMESTAMP NOT NULL,

  risk_score FLOAT64 NOT NULL,           -- 0..1
  risk_band STRING NOT NULL,             -- LOW / MODERATE / HIGH / CRITICAL
  alert_triggered BOOL NOT NULL,

  scoring_model STRING,                  -- e.g., "logreg_v1", "xgb_v2"
  score_version STRING,
  scored_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(event_ts)
CLUSTER BY patient_id, admission_id;
