# API Contract — ICU Sepsis Risk Scoring

This document describes the **input/output contract** for scoring ICU patient events.
The API is intentionally simple and designed to integrate with dashboards, alerts, or downstream services.

> This system is **not a diagnostic tool** and is not intended to replace clinical judgment.

---

## Input Event Schema (JSON)

A single event represents one observation timepoint for an ICU patient.

```json
{
  "patient_id": "P-1042",
  "admission_id": "A-7781",
  "timestamp": "2026-01-12T04:30:00Z",
  "vitals": {
    "heart_rate": 118,
    "respiratory_rate": 26,
    "systolic_bp": 92,
    "diastolic_bp": 58,
    "temperature_celsius": 38.4,
    "oxygen_saturation": 93
  },
  "labs": {
    "lactate_mmol_l": 2.6,
    "wbc_count": 13.8,
    "creatinine_mg_dl": 1.7,
    "platelets": 142
  },
  "metadata": {
    "unit": "MICU",
    "source": "monitoring_export"
  }
}
```

---

## Output Schema (JSON)

The scoring output is designed to be:
	•	machine-friendly (for alert rules)
	•	human-readable (for clinical review)
	•	traceable (patient/admission/timestamp echo)
```json
{
  "patient_id": "P-1042",
  "admission_id": "A-7781",
  "timestamp": "2026-01-12T04:30:00Z",
  "risk_score": 0.78,
  "risk_level": "HIGH",
  "alert": true,
  "top_contributors": ["elevated_lactate", "tachypnea", "shock_index_high"],
  "features": {
    "map": 69.3,
    "shock_index": 1.28,
    "heart_rate": 118,
    "respiratory_rate": 26,
    "lactate_mmol_l": 2.6
  }
}
```
---

## Local CLI Usage

This repository includes a local pipeline runner that reads sample input and writes a scored output:
```text
python -m data_pipeline.pipeline \
  --input examples/sample_input.json \
  --output examples/expected_output.json
```

---

## Error Handling

Validation errors are returned as structured error arrays (see data_pipeline/validate.py).

Common error codes:
	•	MISSING_PATIENT_ID
	•	MISSING_ADMISSION_ID
	•	MISSING_TIMESTAMP
	•	INVALID_VITALS
	•	INVALID_LABS
	•	INVALID_TYPE

---

## Notes on Privacy

No PHI is included in this repository.
The sample data is synthetic and used only to demonstrate pipeline behavior.

