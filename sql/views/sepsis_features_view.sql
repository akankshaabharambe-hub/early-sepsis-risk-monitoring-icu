-- sql/views/sepsis_features_view.sql
-- Curated view for dashboards + conversational queries.
-- Joins events -> features -> risk scoring in a single analytics contract.

CREATE OR REPLACE VIEW `project_id.icu_analytics.vw_sepsis_risk_monitoring` AS
WITH latest_scores AS (
  SELECT
    s.*,
    ROW_NUMBER() OVER (
      PARTITION BY s.patient_id, s.admission_id, s.event_id
      ORDER BY s.scored_ts DESC
    ) AS rn
  FROM `project_id.icu_analytics.fact_sepsis_risk_score` s
),
latest_features AS (
  SELECT
    f.*,
    ROW_NUMBER() OVER (
      PARTITION BY f.patient_id, f.admission_id, f.event_id
      ORDER BY f.computed_ts DESC
    ) AS rn
  FROM `project_id.icu_analytics.fact_sepsis_features` f
)
SELECT
  e.patient_id,
  e.admission_id,
  e.event_id,
  e.event_ts,

  -- raw measurements (subset)
  e.hr,
  e.map,
  e.rr,
  e.temp_c,
  e.wbc,
  e.lactate,

  -- engineered features
  lf.hr_z,
  lf.map_z,
  lf.rr_z,
  lf.temp_z,
  lf.lactate_z,
  lf.sirs_flag,
  lf.organ_dysfunction_flag,
  lf.missingness_score,
  lf.feature_version,

  -- risk scoring outputs
  ls.risk_score,
  ls.risk_band,
  ls.alert_triggered,
  ls.scoring_model,
  ls.score_version,
  ls.scored_ts

FROM `project_id.icu_analytics.fact_icu_event` e
LEFT JOIN latest_features lf
  ON e.event_id = lf.event_id AND lf.rn = 1
LEFT JOIN latest_scores ls
  ON e.event_id = ls.event_id AND ls.rn = 1;
