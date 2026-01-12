"""
ingest.py

Ingestion + normalization for ICU sepsis risk monitoring.

Goals:
- Accept JSON (single object or list) and JSONL (newline-delimited JSON)
- Normalize into a consistent internal "event" contract
- Keep ingestion deterministic and defensive
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional


REQUIRED_TOP_LEVEL_FIELDS = ("patient_id", "admission_id", "timestamp")


@dataclass(frozen=True)
class IngestStats:
    total: int
    parsed: int
    dropped: int
    drop_reasons: Dict[str, int]


def _is_jsonl(path: str) -> bool:
    return path.lower().endswith(".jsonl")


def _read_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _read_jsonl(path: str) -> Iterable[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def normalize_event(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a raw record to the internal event schema.

    Expected schema:
    {
      "patient_id": str,
      "admission_id": str,
      "timestamp": str (ISO 8601 recommended),
      "vitals": {...},
      "labs": {...},
      "metadata": {...} (optional)
    }

    Notes:
    - We do NOT create new clinical facts; only map/rename fields.
    - Missing vitals/labs are normalized to empty dicts.
    """

    # Common alias handling (representative)
    patient_id = raw.get("patient_id") or raw.get("patientId") or raw.get("pt_id")
    admission_id = raw.get("admission_id") or raw.get("admissionId") or raw.get("visit_id")
    timestamp = raw.get("timestamp") or raw.get("ts") or raw.get("event_time")

    vitals = raw.get("vitals") or {}
    labs = raw.get("labs") or {}

    # Some datasets store vitals/labs as flat fields; keep minimal mapping
    if not vitals:
        vitals = {
            "heart_rate": raw.get("heart_rate") or raw.get("hr"),
            "respiratory_rate": raw.get("respiratory_rate") or raw.get("rr"),
            "systolic_bp": raw.get("systolic_bp") or raw.get("sbp"),
            "diastolic_bp": raw.get("diastolic_bp") or raw.get("dbp"),
            "temperature_celsius": raw.get("temperature_celsius") or raw.get("temp_c"),
            "oxygen_saturation": raw.get("oxygen_saturation") or raw.get("spo2"),
        }

    if not labs:
        labs = {
            "lactate_mmol_l": raw.get("lactate_mmol_l") or raw.get("lactate"),
            "wbc_count": raw.get("wbc_count") or raw.get("wbc"),
            "creatinine_mg_dl": raw.get("creatinine_mg_dl") or raw.get("creatinine"),
            "platelets": raw.get("platelets") or raw.get("plt"),
        }

    event: Dict[str, Any] = {
        "patient_id": patient_id,
        "admission_id": admission_id,
        "timestamp": timestamp,
        "vitals": vitals or {},
        "labs": labs or {},
        "metadata": raw.get("metadata") or {},
    }

    return event


def load_events(input_path: str) -> List[Dict[str, Any]]:
    """
    Load events from a JSON/JSONL file and normalize.

    Raises:
        FileNotFoundError, ValueError for obvious input issues
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input not found: {input_path}")

    events: List[Dict[str, Any]] = []

    if _is_jsonl(input_path):
        for rec in _read_jsonl(input_path):
            if isinstance(rec, dict):
                events.append(normalize_event(rec))
    else:
        payload = _read_json(input_path)
        if isinstance(payload, dict):
            events.append(normalize_event(payload))
        elif isinstance(payload, list):
            for rec in payload:
                if isinstance(rec, dict):
                    events.append(normalize_event(rec))
        else:
            raise ValueError("Input JSON must be an object or list of objects")

    return events


def ingest_with_stats(input_path: str) -> tuple[List[Dict[str, Any]], IngestStats]:
    """
    Ingest and produce stats. Does not validate clinical values (that's validate.py).
    """
    raw_events = load_events(input_path)

    drop_reasons: Dict[str, int] = {}
    kept: List[Dict[str, Any]] = []

    for ev in raw_events:
        missing = [k for k in REQUIRED_TOP_LEVEL_FIELDS if not ev.get(k)]
        if missing:
            reason = f"missing_{'_'.join(missing)}"
            drop_reasons[reason] = drop_reasons.get(reason, 0) + 1
            continue
        kept.append(ev)

    stats = IngestStats(
        total=len(raw_events),
        parsed=len(raw_events),
        dropped=len(raw_events) - len(kept),
        drop_reasons=drop_reasons,
    )
    return kept, stats
