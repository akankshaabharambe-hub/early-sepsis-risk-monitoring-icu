"""
data_pipeline package

Public entry points for the ICU sepsis risk monitoring pipeline.

The intent is to keep external imports stable even as internal modules evolve.
"""

from .ingest import load_events, normalize_event
from .validate import validate_event, validate_events
from .features import build_features, summarize_contributors
from .score import score_event
from .pipeline import run_pipeline

__all__ = [
    "load_events",
    "normalize_event",
    "validate_event",
    "validate_events",
    "build_features",
    "summarize_contributors",
    "score_event",
    "run_pipeline",
]
