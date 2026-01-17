import math

from data_pipeline.features import build_features


def test_map_and_shock_index_computation():
    """
    Verify derived physiological features are computed correctly.
    """
    event = {
        "patient_id": "P1",
        "admission_id": "A1",
        "timestamp": "2026-01-01T00:00:00Z",
        "vitals": {
            "heart_rate": 120,
            "systolic_bp": 100,
            "diastolic_bp": 60,
            "respiratory_rate": 24,
            "temperature_celsius": 38.5,
            "oxygen_saturation": 94,
        },
        "labs": {
            "lactate_mmol_l": 2.5,
            "wbc_count": 14.0,
            "creatinine_mg_dl": 1.6,
            "platelets": 140,
        },
    }

    features, flags = build_features(event)

    # MAP ≈ (SBP + 2*DBP) / 3 = (100 + 120) / 3 = 73.33
    assert math.isclose(features["map"], 73.33333333333333, rel_tol=1e-3)

    # Shock index = HR / SBP = 120 / 100
    assert math.isclose(features["shock_index"], 1.2, rel_tol=1e-6)

    # Sanity check flags
    assert flags["tachycardia"] == 1
    assert flags["elevated_lactate"] == 1
