"""
score.py

Risk scoring logic for early sepsis monitoring in ICU settings.

This module takes engineered features + clinical flags and produces:
- a numeric risk_score in [0, 1]
- a risk_category (LOW / MEDIUM / HIGH)
- a small, explainable list of contributing factors

Important:
- This is a representative scoring approach for demonstrating pipeline engineering.
- It is NOT a medical device and does not provide clinical diagnosis.
- If you later plug in a trained model, keep this file as the "interface layer"
  (model output -> calibrated score -> thresholds -> explanation).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


# ----------------------------
# Scoring configuration
# ----------------------------

@dataclass(frozen=True)
class ScoringConfig:
    """
    Tunable scoring weights and thresholds.

    - weights reflect relative severity signals
    - thresholds map score -> category
    """
    # weights (representative)
    w_elevated_lactate: float = 2.0
    w_hypotension: float = 1.8
    w_low_map: float = 1.6
    w_shock_index_high: float = 1.2
    w_tachycardia: float = 0.8
    w_tachypnea: float = 0.8
    w_fever_or_hypothermia: float = 0.7
    w_low_spo2: float = 0.7
    w_high_wbc: float = 0.5
    w_low_platelets: float = 0.5
    w_high_creatinine: float = 0.4

    # missingness penalty (keeps score conservative when data is sparse)
    missing_penalty: float = 0.12  # per critical signal missing

    # thresholds
    medium_threshold: float = 0.45
    high_threshold: float = 0.70

    # limit explanation list
    max_contributors: int = 5


DEFAULT_SCORING = ScoringConfig()


# ----------------------------
# Helpers
# ----------------------------

def _present(x: Any) -> bool:
    return x is not None


def _sigmoid(z: float) -> float:
    # stable sigmoid without importing numpy
    # for big negative: exp may underflow -> fine
    import math
    if z >= 0:
        ez = math.exp(-z)
        return 1.0 / (1.0 + ez)
    else:
        ez = math.exp(z)
        return ez / (1.0 + ez)


def _category(score: float, cfg: ScoringConfig) -> str:
    if score >= cfg.high_threshold:
        return "HIGH"
    if score >= cfg.medium_threshold:
        return "MEDIUM"
    return "LOW"


# ----------------------------
# Main scoring
# ----------------------------

def score_event(
    features: Dict[str, Any],
    flags: Dict[str, int],
    cfg: ScoringConfig = DEFAULT_SCORING,
) -> Dict[str, Any]:
    """
    Compute risk score + label + explanation.

    Args:
        features: engineered feature vector from features.build_features()
        flags: binary clinical flags from features.build_features()
        cfg: scoring configuration

    Returns:
        dict suitable for API output / downstream use
    """

    # Weighted sum of key clinical signals (interpretable)
    contributions: List[Tuple[str, float]] = []

    def add(flag_key: str, weight: float, label: str) -> None:
        if flags.get(flag_key) == 1:
            contributions.append((label, weight))

    add("elevated_lactate", cfg.w_elevated_lactate, "elevated_lactate")
    add("hypotension", cfg.w_hypotension, "hypotension")
    add("low_map", cfg.w_low_map, "low_map")
    add("shock_index_high", cfg.w_shock_index_high, "shock_index_high")
    add("tachycardia", cfg.w_tachycardia, "tachycardia")
    add("tachypnea", cfg.w_tachypnea, "tachypnea")

    # fever/hypothermia treated as one bucket
    if flags.get("fever") == 1 or flags.get("hypothermia") == 1:
        contributions.append(("temperature_abnormal", cfg.w_fever_or_hypothermia))

    add("low_spo2", cfg.w_low_spo2, "low_spo2")
    add("high_wbc", cfg.w_high_wbc, "high_wbc")
    add("low_platelets", cfg.w_low_platelets, "low_platelets")
    add("high_creatinine", cfg.w_high_creatinine, "high_creatinine")

    # Missingness handling: penalize when critical signals are absent
    critical_fields = [
        "heart_rate",
        "systolic_bp",
        "diastolic_bp",
        "respiratory_rate",
        "temperature_celsius",
        "oxygen_saturation",
        "lactate_mmol_l",
    ]
    missing_count = sum(1 for k in critical_fields if not _present(features.get(k)))
    missing_pen = cfg.missing_penalty * float(missing_count)

    raw_score = sum(w for _, w in contributions) - missing_pen

    # Calibrate into [0,1]
    # (using sigmoid to make the score stable & monotonic)
    risk_score = _sigmoid(raw_score)

    # Rank explanation contributors
    ranked = sorted(contributions, key=lambda x: x[1], reverse=True)
    top_factors = [name for name, _ in ranked[: cfg.max_contributors]]

    result = {
        # traceability (non-PHI fields only)
        "patient_id": features.get("patient_id"),
        "admission_id": features.get("admission_id"),
        "timestamp": features.get("timestamp"),

        # scoring output
        "risk_score": round(float(risk_score), 4),
        "risk_category": _category(risk_score, cfg),

        # explainability
        "top_contributing_factors": top_factors,
        "missing_critical_signals": missing_count,
    }

    return result


def evaluate_alert(
    scored: Dict[str, Any],
    alert_threshold: float = 0.70,
) -> Dict[str, Any]:
    """
    Alert policy layer: decides whether to trigger an alert.

    Keeps policy separate from scoring so teams can change alerting rules
    without retraining/recalibrating the scoring logic.
    """
    score = scored.get("risk_score")
    if score is None:
        raise ValueError("scored payload missing risk_score")

    alert = float(score) >= float(alert_threshold)

    return {
        "alert": alert,
        "alert_threshold": float(alert_threshold),
        "risk_score": float(score),
        "risk_category": scored.get("risk_category"),
        "top_contributing_factors": scored.get("top_contributing_factors", []),
    }
