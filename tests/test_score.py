from data_pipeline.score import score_event


def test_high_risk_event_scores_high():
    """
    Ensure that multiple abnormal clinical signals
    produce a HIGH risk category.
    """
    features = {
        "patient_id": "P1",
        "admission_id": "A1",
        "timestamp": "2026-01-01T00:00:00Z",
        "heart_rate": 125,
        "systolic_bp": 85,
        "diastolic_bp": 55,
        "map": 65,
        "shock_index": 1.47,
        "lactate_mmol_l": 3.2,
    }

    flags = {
        "tachycardia": 1,
        "tachypnea": 1,
        "hypotension": 1,
        "low_map": 1,
        "fever": 1,
        "hypothermia": 0,
        "low_spo2": 0,
        "elevated_lactate": 1,
        "high_wbc": 1,
        "low_platelets": 0,
        "high_creatinine": 0,
        "shock_index_high": 1,
    }

    result = score_event(features, flags)

    assert result["risk_category"] == "HIGH"
    assert result["risk_score"] >= 0.7
    assert len(result["top_contributing_factors"]) > 0
