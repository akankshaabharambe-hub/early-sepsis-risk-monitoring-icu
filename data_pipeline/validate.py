"""
validate.py

Schema validation + data quality checks for ICU event records.

Goals:
- Ensure required fields exist and are reasonable types
- Validate vitals/labs structures
- Provide human-readable error messages for debugging

This is NOT medical advice and does not diagnose sepsis.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class ValidationErrorDetail:
    code: str
    message: str
    field: Optional[str] = None


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: List[ValidationErrorDetail]


def _is_nonempty_str(x: Any) -> bool:
    return isinstance(x, str) and x.strip() != ""


def _is_dict(x: Any) -> bool:
    return isinstance(x, dict)


def validate_event(event: Dict[str, Any]) -> ValidationResult:
    errors: List[ValidationErrorDetail] = []

    # Required identifiers
    if not _is_nonempty_str(event.get("patient_id")):
        errors.append(ValidationErrorDetail("MISSING_PATIENT_ID", "patient_id is required", "patient_id"))

    if not _is_nonempty_str(event.get("admission_id")):
        errors.append(ValidationErrorDetail("MISSING_ADMISSION_ID", "admission_id is required", "admission_id"))

    if not _is_nonempty_str(event.get("timestamp")):
        errors.append(ValidationErrorDetail("MISSING_TIMESTAMP", "timestamp is required", "timestamp"))

    # Containers
    vitals = event.get("vitals", {})
    labs = event.get("labs", {})

    if not _is_dict(vitals):
        errors.append(ValidationErrorDetail("INVALID_VITALS", "vitals must be an object/dict", "vitals"))

    if not _is_dict(labs):
        errors.append(ValidationErrorDetail("INVALID_LABS", "labs must be an object/dict", "labs"))

    # Light sanity checks (not clinical correctness)
    # We avoid hard failures for missing fields; feature code handles missing defensively.
    if _is_dict(vitals):
        for k in ["heart_rate", "respiratory_rate", "systolic_bp", "diastolic_bp", "temperature_celsius", "oxygen_saturation"]:
            if k in vitals and vitals[k] is not None and not isinstance(vitals[k], (int, float, str)):
                errors.append(
                    ValidationErrorDetail("INVALID_TYPE", f"vitals.{k} must be number-like", f"vitals.{k}")
                )

    if _is_dict(labs):
        for k in ["lactate_mmol_l", "wbc_count", "creatinine_mg_dl", "platelets"]:
            if k in labs and labs[k] is not None and not isinstance(labs[k], (int, float, str)):
                errors.append(
                    ValidationErrorDetail("INVALID_TYPE", f"labs.{k} must be number-like", f"labs.{k}")
                )

    return ValidationResult(ok=len(errors) == 0, errors=errors)


def validate_events(events: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Returns:
      valid_events, invalid_reports

    invalid_reports structure:
    {
      "event": <original event>,
      "errors": [ {code, message, field}, ... ]
    }
    """
    valid: List[Dict[str, Any]] = []
    invalid: List[Dict[str, Any]] = []

    for ev in events:
        res = validate_event(ev)
        if res.ok:
            valid.append(ev)
        else:
            invalid.append(
                {
                    "event": ev,
                    "errors": [e.__dict__ for e in res.errors],
                }
            )

    return valid, invalid
