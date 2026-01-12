# Data Model — ICU Sepsis Risk Monitoring

This document describes the **logical data model** used by the ICU sepsis risk monitoring system.
The model is designed to support **real-time risk scoring**, **clinical explainability**, and
**downstream analytics** without embedding business logic in storage.

The data model prioritizes:
- traceability (patient, admission, timestamp)
- interpretability of features
- compatibility with analytical warehouses

> This repository uses **synthetic sample data only**.  
> No real patient records or PHI are included.

---

## Core Entities

### 1. Patient (Logical Entity)

Represents a unique individual receiving care.

| Field        | Type   | Description                          |
|--------------|--------|--------------------------------------|
| patient_id   | STRING | Stable anonymized patient identifier |

**Notes**
- No demographic or identifying attributes are stored
- Used strictly for event grouping and traceability

---

### 2. Admission (Logical Entity)

Represents a single ICU admission or encounter.

| Field          | Type   | Description                              |
|----------------|--------|------------------------------------------|
| admission_id  | STRING | Unique ICU admission identifier          |
| patient_id    | STRING | Foreign key to patient                   |

A patient may have **multiple admissions**, but each event belongs to exactly one admission.

---

### 3. ICU Observation Event

A single time-indexed clinical snapshot used for scoring.

| Field       | Type     | Description                                 |
|-------------|----------|---------------------------------------------|
| patient_id  | STRING   | Patient identifier                          |
| admission_id| STRING   | Admission identifier                       |
| timestamp   | TIMESTAMP| Observation time                            |
| vitals      | OBJECT   | Vital signs at this timepoint              |
| labs        | OBJECT   | Laboratory values at this timepoint        |
| metadata    | OBJECT   | Optional source / unit information         |

This is the **primary input** to the pipeline.

---

## Vital Signs Schema

Stored as a nested object during ingestion and flattened during feature engineering.

| Field                  | Type   | Units |
|------------------------|--------|-------|
| heart_rate             | FLOAT  | bpm   |
| respiratory_rate       | FLOAT  | /min  |
| systolic_bp            | FLOAT  | mmHg  |
| diastolic_bp           | FLOAT  | mmHg  |
| temperature_celsius    | FLOAT  | °C    |
| oxygen_saturation      | FLOAT  | %     |

All values are validated and range-clamped before feature derivation.

---

## Laboratory Results Schema

| Field               | Type  | Units        |
|---------------------|-------|--------------|
| lactate_mmol_l      | FLOAT | mmol/L      |
| wbc_count           | FLOAT | x10⁹/L      |
| creatinine_mg_dl    | FLOAT | mg/dL       |
| platelets           | FLOAT | x10⁹/L      |

Missing values are permitted and handled defensively.

---

## Feature Table (Analytics-Ready)

After feature engineering, each observation is converted into a **flat feature record**.

### Key Columns

| Field           | Type     | Description                          |
|-----------------|----------|--------------------------------------|
| patient_id      | STRING   | Traceability                         |
| admission_id    | STRING   | Traceability                         |
| timestamp       | TIMESTAMP| Observation time                     |
| map             | FLOAT    | Mean arterial pressure               |
| shock_index     | FLOAT    | HR / SBP                             |
| heart_rate      | FLOAT    | Raw vital                            |
| lactate_mmol_l  | FLOAT    | Raw lab                              |

### Binary Flags (Explainability)

| Field                     | Type | Description                         |
|---------------------------|------|-------------------------------------|
| flag_tachycardia          | INT  | HR ≥ threshold                      |
| flag_hypotension          | INT  | SBP ≤ threshold                     |
| flag_low_map              | INT  | MAP < threshold                     |
| flag_elevated_lactate     | INT  | Lactate ≥ threshold                 |
| flag_shock_index_high     | INT  | Shock index ≥ threshold             |

Flags are used for:
- alert explanations
- clinical review
- model interpretability

---

## Risk Score Output Model

Each processed event produces a **scoring result**.

| Field            | Type    | Description                              |
|------------------|---------|------------------------------------------|
| risk_score       | FLOAT   | Normalized risk (0–1)                    |
| risk_level       | STRING  | LOW / MEDIUM / HIGH                     |
| alert            | BOOLEAN | Whether alert threshold is crossed      |
| top_contributors | ARRAY   | Ranked list of contributing factors     |

This output is suitable for:
- dashboards
- alerting systems
- downstream analytics pipelines

---

## Warehouse Design (Conceptual)

In a production system, data would be stored as:

- **fact_icu_observation** (time-series features)
- **fact_sepsis_risk_score** (scoring outputs)
- **dim_patient**, **dim_admission** (logical dimensions)

This repository includes representative SQL definitions under `sql/`.

---

## Design Principles

- **Flat, analytics-friendly schema**
- **No business logic in storage**
- **Explainability preserved at the data layer**
- **Separation of raw inputs and derived features**

---

## Summary

This data model supports real-time clinical risk monitoring while remaining:
- auditable
- interpretable
- scalable for analytics workloads

It reflects production-style thinking used in healthcare analytics systems.
