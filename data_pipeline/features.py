"""
features.py

Feature engineering for ICU sepsis risk monitoring.

This module converts a single longitudinal observation (vitals + labs at a timestamp)
into an explainable, model-ready feature vector.

Design goals:
- deterministic and schema-driven
- defensive handling of missing / invalid values
- clinically plausible, interpretable features (e.g., MAP, shock index)
- no patient identifiers beyond patient_id/admission_id for traceability

Note:
This repository focuses on the engineering of a real-time scoring pipeline.
It does not include proprietary datasets or trained model weights.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple


# ----------------------------
# Helpers
# ----------------------------

def _as_float(x: Any) -> Optional[float]:
    """Best-effort conversion to float; returns None if missing/invalid."""
    if x is None:
        return None
    try:
        v = float(x)
        if v != v:  # NaN
            return None
        return v
    except (TypeError, ValueError):
        return None


def _clamp(v: Optional[float], lo: float, hi: float) -> Optional[float]:
    if v is None:
        return None
    return max(lo, min(hi, v))


def _safe_div(num: Optional[float], den: Optional[float]) -> Optional[float]:
    if num is None or den is None:
        return None
    if den == 0:
        return None
    return num / den


def _bool_to_int(flag: bool) -> int:
    return 1 if flag else 0


def _compute_map(sys_bp: Optional[float], dia_bp: Optional[float]) -> Optional[float]:
    """
    Mean Arterial Pressure approximation:
    MAP ≈ (SBP + 2*DBP)/3
    """
    if sys_bp is None or dia_bp is None:
        return None
    return (sys_bp + 2.0 * dia_bp) / 3.0


# ----------------------------
# Domain thresholds (representative)
# ----------------------------

@dataclass(frozen=True)
class Thresholds:
    # Vitals
    tachycardia_hr: float = 100.0
    tachypnea_rr: float = 22.0
    hypotension_sbp: float = 90.0
    low_map: float = 65.0
    fever_c: float = 38.0
    hypothermia_c: float = 36.0
    low_spo2: float = 92.0

    # Labs
    high_lactate: float = 2.0
    high_wbc: float = 12.0
    low_platelets: float = 150.0
    high_creatinine: float = 1.5

    # Explainability signals
    shock_index_high: float = 0.9  # HR/SBP


DEFAULT_THRESHOLDS = Thresholds()


# ----------------------------
# Feature builder
# ----------------------------

def build_features(
    event: Dict[str, Any],
    thresholds: Thresholds = DEFAULT_THRESHOLDS
) -> Tuple[Dict[str, Any], Dict[str, int]]:
    """
    Build a flat feature vector + flags for explainability.

    Returns:
        features: numeric feature dict (ready for model/scoring)
        flags: binary indicators used for explanation strings
    """

    vitals = event.get("vitals", {}) or {}
    labs = event.get("labs", {}) or {}

    # Extract & sanity clamp
    hr = _clamp(_as_float(vitals.get("heart_rate")), 20, 250)
    rr = _clamp(_as_float(vitals.get("respiratory_rate")), 5, 80)
    sbp = _clamp(_as_float(vitals.get("systolic_bp")), 40, 250)
    dbp = _clamp(_as_float(vitals.get("diastolic_bp")), 20, 150)
    temp_c = _clamp(_as_float(vitals.get("temperature_celsius")), 30, 43)
    spo2 = _clamp(_as_float(vitals.get("oxygen_saturation")), 50, 100)

    lactate = _clamp(_as_float(labs.get("lactate_mmol_l")), 0, 20)
    wbc = _clamp(_as_float(labs.get("wbc_count")), 0, 60)
    creat = _clamp(_as_float(labs.get("creatinine_mg_dl")), 0, 20)
    platelets = _clamp(_as_float(labs.get("platelets")), 0, 1500)

    # Derived signals
    map_val = _compute_map(sbp, dbp)
    shock_index = _safe_div(hr, sbp)

    # Representative rules for interpretable flags (not a diagnosis)
    flags: Dict[str, int] = {
        "tachycardia": _bool_to_int(hr is not None and hr >= thresholds.tachycardia_hr),
        "tachypnea": _bool_to_int(rr is not None and rr >= thresholds.tachypnea_rr),
        "hypotension": _bool_to_int(sbp is not None and sbp <= thresholds.hypotension_sbp),
        "low_map": _bool_to_int(map_val is not None and map_val < thresholds.low_map),
        "fever": _bool_to_int(temp_c is not None and temp_c >= thresholds.fever_c),
        "hypothermia": _bool_to_int(temp_c is not None and temp_c <= thresholds.hypothermia_c),
        "low_spo2": _bool_to_int(spo2 is not None and spo2 < thresholds.low_spo2),
        "elevated_lactate": _bool_to_int(lactate is not None and lactate >= thresholds.high_lactate),
        "high_wbc": _bool_to_int(wbc is not None and wbc >= thresholds.high_wbc),
        "low_platelets": _bool_to_int(platelets is not None and platelets < thresholds.low_platelets),
        "high_creatinine": _bool_to_int(creat is not None and creat >= thresholds.high_creatinine),
        "shock_index_high": _bool_to_int(shock_index is not None and shock_index >= thresholds.shock_index_high),
    }

    # Flat numeric features (use None for missing; scoring can impute)
    features: Dict[str, Any] = {
        # identity fields for traceability (not model features)
        "patient_id": event.get("patient_id"),
        "admission_id": event.get("admission_id"),
        "timestamp": event.get("timestamp"),

        # raw
        "heart_rate": hr,
        "respiratory_rate": rr,
        "systolic_bp": sbp,
        "diastolic_bp": dbp,
        "temperature_celsius": temp_c,
        "oxygen_saturation": spo2,
        "lactate_mmol_l": lactate,
        "wbc_count": wbc,
        "creatinine_mg_dl": creat,
        "platelets": platelets,

        # derived
        "map": map_val,
        "shock_index": shock_index,

        # simple aggregates for models that expect binary features
        "flag_tachycardia": flags["tachycardia"],
        "flag_tachypnea": flags["tachypnea"],
        "flag_hypotension": flags["hypotension"],
        "flag_low_map": flags["low_map"],
        "flag_fever": flags["fever"],
        "flag_hypothermia": flags["hypothermia"],
        "flag_low_spo2": flags["low_spo2"],
        "flag_elevated_lactate": flags["elevated_lactate"],
        "flag_high_wbc": flags["high_wbc"],
        "flag_low_platelets": flags["low_platelets"],
        "flag_high_creatinine": flags["high_creatinine"],
        "flag_shock_index_high": flags["shock_index_high"],
    }

    return features, flags


def summarize_contributors(flags: Dict[str, int]) -> list[str]:
    """
    Convert flags into human-readable contributing factors
    for the API response layer.
    """
    mapping = {
        "elevated_lactate": "elevated_lactate",
        "hypotension": "hypotension",
        "low_map": "low_map",
        "tachycardia": "tachycardia",
        "tachypnea": "tachypnea",
        "fever": "fever",
        "low_spo2": "low_spo2",
        "high_wbc": "high_wbc",
        "low_platelets": "low_platelets",
        "high_creatinine": "high_creatinine",
        "shock_index_high": "shock_index_high",
    }
    return [label for key, label in mapping.items() if flags.get(key) == 1]
