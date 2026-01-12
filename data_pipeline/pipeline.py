"""
pipeline.py

End-to-end orchestration for early sepsis risk monitoring.

This module wires together:
- ingestion
- validation
- feature engineering
- risk scoring
- alert evaluation

It can be run locally with sample data to demonstrate
the full pipeline behavior without cloud credentials.

IMPORTANT:
This pipeline is for engineering demonstration only.
It does NOT provide medical diagnosis or clinical decisions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

from data_pipeline.ingest import ingest_record
from data_pipeline.validate import validate_record
from data_pipeline.features import build_features
from data_pipeline.score import score_event, evaluate_alert


# ----------------------------
# Pipeline entrypoint
# ----------------------------

def run_pipeline(input_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the full sepsis risk monitoring pipeline
    for a single ICU event.

    Args:
        input_payload: raw ICU event record

    Returns:
        structured pipeline output suitable for APIs,
        alerts, or downstream systems
    """

    # 1. Ingest & normalize
    staged = ingest_record(input_payload)

    # 2. Validate schema & data quality
    validate_record(staged)

    # 3. Feature engineering
    features, flags = build_features(staged)

    # 4. Risk scoring
    scored = score_event(features=features, flags=flags)

    # 5. Alert evaluation
    alert = evaluate_alert(scored)

    return {
        "patient_id": staged.get("patient_id"),
        "admission_id": staged.get("admission_id"),
        "timestamp": staged.get("timestamp"),

        "features": features,
        "clinical_flags": flags,

        "risk_assessment": scored,
        "alert_decision": alert,
    }


# ----------------------------
# CLI support (local demo)
# ----------------------------

def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def main() -> None:
    """
    Local execution entrypoint.

    Example:
        python -m data_pipeline.pipeline \
            examples/sample_input.json \
            examples/expected_output.json
    """
    import sys

    if len(sys.argv) != 3:
        raise RuntimeError(
            "Usage: python -m data_pipeline.pipeline <input.json> <output.json>"
        )

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    raw_input = _load_json(input_path)
    result = run_pipeline(raw_input)
    _write_json(output_path, result)

    print("Pipeline execution complete")
    print(f"Output written to: {output_path}")


if __name__ == "__main__":
    main()
