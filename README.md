# Early Sepsis Risk Monitoring in Intensive Care Units

A clinical data processing and risk scoring system designed to support
early identification of sepsis risk in ICU patients using longitudinal
physiological and laboratory data.

This project focuses on the **engineering, data pipeline, and system design**
aspects of building a real-time clinical risk monitoring platform, rather than
on model experimentation alone.

> This repository contains a **representative subset** of the system.  
> Patient data, credentials, and deployment configurations are intentionally
> excluded for privacy, security, and ethical reasons.

---

## Project Context

Sepsis is a time-critical condition in intensive care settings, where early
physiological signals can indicate elevated risk hours before clinical
deterioration becomes obvious.

In practice, building systems to support early detection involves more than
model accuracy. It requires:

- Reliable ingestion of heterogeneous clinical data
- Robust preprocessing and validation
- Careful feature construction over time
- Clear separation between data pipelines and predictive logic
- Outputs that support **clinical decision-making**, not automation

This project was designed with those constraints in mind.

---

## What This Project Demonstrates

### Data Engineering & Pipelines
- Scalable preprocessing of longitudinal ICU patient records
- Schema-driven validation of clinical events and measurements
- Feature construction from time-series vital signs and labs
- Deterministic, reproducible data transformations

### Applied Healthcare Analytics
- Integration of pipeline outputs with a sepsis risk model
- Clinically relevant evaluation metrics (e.g., AUC-ROC)
- Emphasis on early warning sensitivity over raw prediction volume
- Explicit separation between data preparation and model inference

### Software Engineering Practices
- Modular, testable pipeline components
- Clear interface boundaries between ingestion, features, and scoring
- Production-style repository structure and documentation
- Local execution using safe, anonymized example data

---

## High-Level Architecture

```text
Clinical Data Sources
  (Vitals, Labs, Events)
          |
          v
Ingestion & Normalization
          |
          v
Validation & Quality Checks
          |
          v
Time-Series Feature Engineering
          |
          v
Risk Scoring Interface
  (Model Integration)
          |
          v
Structured Risk Outputs
  (Decision Support)
```
A detailed breakdown is available in docs/architecture.md.

---

Repository Structure

```text
docs/                  Clinical context, architecture, and design notes
data_pipeline/         Ingestion, preprocessing, validation, and scoring logic
sql/                   Schema definitions and feature views
examples/              Safe, anonymized sample inputs and outputs
tests/                 Unit tests for pipeline correctness
```

Each layer is intentionally isolated to support testing, iteration, and
responsible system evolution.

---

Example Pipeline Flow

Using representative sample data, the pipeline follows this flow:
```text
raw_patient_events.json
        ↓
ingest.py
        ↓
validate.py
        ↓
features.py
        ↓
risk_scoring.py
        ↓
risk_scores.json
```

These artifacts demonstrate how data moves through the system without exposing
real patient records.

---

Local Execution
This repository supports local execution using anonymized example inputs.
```text
pip install -r requirements.txt

python -m data_pipeline.ingest \
  --input examples/raw_patient_events.json \
  --output examples/processed_features.json

python -m data_pipeline.risk_scoring \
  --input examples/processed_features.json \
  --output examples/risk_scores.json
```

This simulates the end-to-end pipeline without requiring access to clinical
databases or deployment infrastructure.

---

Model Evaluation (Summary)

The integrated sepsis risk model was evaluated using clinically relevant metrics,
with an emphasis on early warning performance.
	•	AUC-ROC: ~0.87 on held-out evaluation data
	•	Evaluation prioritized sensitivity to early physiological deterioration
	•	The system is designed as decision support, not an automated diagnostic

Detailed evaluation notes are documented in docs/model-evaluation.md.

---

Clinical & Ethical Considerations

This project explicitly acknowledges that predictive systems in healthcare:
	•	Must support clinicians, not replace them
	•	Require careful handling of uncertainty and false positives
	•	Must respect patient privacy and data governance
	•	Should be evaluated within clinical workflows, not in isolation

Design decisions reflecting these considerations are documented in
docs/clinical-considerations.md.

---

Scope & Constraints

Excluded from this repository:
	•	Real patient data and identifiers
	•	Hospital-specific schemas and integrations
	•	Deployment, monitoring, and alerting infrastructure
	•	Live model serving endpoints

Included here:
	•	Pipeline structure and interfaces
	•	Feature engineering logic
	•	Risk scoring integration patterns
	•	Evaluation methodology and design rationale

---

Summary

This project reflects how early-warning clinical analytics systems are
engineered in practice: prioritizing data quality, system reliability,
and ethical responsibility alongside predictive performance.

The goal is to demonstrate production-quality thinking at the intersection
of data engineering, applied analytics, and healthcare systems design.
