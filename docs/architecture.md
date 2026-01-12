# System Architecture — ICU Sepsis Risk Monitoring Pipeline

This document describes the **end-to-end architecture** of the ICU sepsis risk monitoring system,
with a focus on **data flow, component boundaries, and engineering design decisions**.

The system is designed to process longitudinal ICU data, engineer clinically interpretable features,
and compute real-time sepsis risk scores in a **deterministic, explainable, and scalable** manner.

> This system is **not a diagnostic tool** and is intended to support clinical decision-making,
not replace clinician judgment.

---

## High-Level Architecture

```text
ICU Data Sources
  |
  v
Ingestion Layer
  - Schema normalization
  - Basic type validation
  |
  v
Validation Layer
  - Required field checks
  - Value sanity bounds
  - Structural validation
  |
  v
Feature Engineering
  - Clinically interpretable signals
  - Derived vitals (MAP, shock index)
  - Binary risk indicators
  |
  v
Risk Scoring Engine
  - Deterministic scoring logic
  - Threshold-based alerting
  - Explainable factor ranking
  |
  v
Outputs
  - Scored JSON events
  - Alert signals
  - Analytics-ready records

```

---

## Component Overview

1. Ingestion Layer (data_pipeline/ingest.py)

Responsibility
	•	Accept raw ICU observation events
	•	Normalize input structure
	•	Preserve traceability identifiers (patient, admission, timestamp)

Design Characteristics
	•	No business logic
	•	No clinical interpretation
	•	Defensive handling of malformed inputs

This layer acts as the boundary between external systems and internal processing.

---

2. Validation Layer (data_pipeline/validate.py)

Responsibility
	•	Enforce required fields (patient_id, admission_id, timestamp)
	•	Validate vital signs and lab schemas
	•	Surface structured, machine-readable errors

Design Characteristics
	•	Schema-driven checks
	•	Explicit error codes
	•	Fail-fast behavior for invalid events

Validation ensures that downstream components operate on trusted, well-formed data.

---

3. Feature Engineering Layer (data_pipeline/features.py)

Responsibility
	•	Convert a single ICU observation into a model-ready feature vector
	•	Compute clinically meaningful derived features

Examples
	•	Mean Arterial Pressure (MAP)
	•	Shock Index (HR / SBP)
	•	Binary indicators for abnormal vitals and labs

Design Characteristics
	•	Deterministic transformations
	•	Clinically interpretable features
	•	Safe handling of missing or out-of-range values

This layer prioritizes explainability over complexity.

---

4. Risk Scoring Layer (data_pipeline/score.py)

Responsibility
	•	Compute a normalized risk score (0–1)
	•	Assign risk levels (LOW / MEDIUM / HIGH)
	•	Trigger alert signals
	•	Rank contributing risk factors

Design Characteristics
	•	Transparent scoring logic
	•	Threshold-based alerting
	•	Human-readable explanations

The scoring layer is intentionally simple to support auditability and trust.

---

5. Pipeline Orchestration (data_pipeline/pipeline.py)

Responsibility
	•	Coordinate ingestion, validation, feature engineering, and scoring
	•	Provide a single entry point for batch or real-time execution

Design Characteristics
	•	Linear, readable execution flow
	•	No hidden side effects
	•	Easy to adapt for streaming or API-based deployment

This file represents how the system would be run in production environments.

---

## Data Storage & Analytics Layer (SQL)

While this repository does not include live databases, it demonstrates how outputs
would be consumed downstream:
	•	Analytics views for feature inspection
	•	Time-series rollups for population analysis
	•	Integration with dashboards and monitoring tools

SQL definitions live under sql/ and follow analytics engineering best practices.

---

## Non-Goals & Constraints

This repository intentionally excludes:
	•	Real patient data
	•	Trained model artifacts
	•	Deployment configurations
	•	Authentication and authorization logic

The focus is on pipeline design, correctness, and maintainability.

---

## Design Principles
	•	Separation of concerns across pipeline stages
	•	Deterministic behavior for reproducibility
	•	Explainability-first clinical signals
	•	Fail-fast validation to prevent silent errors
	•	Production-style structure, not a research prototype

---

## Summary

This architecture reflects how real-world clinical risk monitoring systems are engineered:
clear boundaries, defensible logic, and an emphasis on trust and correctness.

The goal is to demonstrate production-quality thinking at the intersection of
software engineering, data pipelines, and healthcare analytics.
