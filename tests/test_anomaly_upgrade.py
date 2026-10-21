"""
Unit tests for the upgraded Explainable Anomaly Detection Engine.
Verifies 4 severity levels, distinction between potential waste and unusual load,
evidence strength and confidence scoring, and Isolation Forest ethical disclaimers.
"""

import pytest
import pandas as pd
from src.data_generator import generate_energy_dataset
from src.anomaly_detection import detect_anomalies, compute_hourly_baselines


def test_four_tier_severity_levels():
    """Verify Critical, High, Medium, and Low severity classifications."""
    df_spike = generate_energy_dataset(days=60, scenario="sudden_spike", random_seed=42)
    res = detect_anomalies(df_spike, sensitivity_std=2.0)

    alerts = res["alerts"]
    summary = res["summary"]

    assert summary["total_anomalies"] > 0
    # There should be critical or high severity alerts from the 50+ kWh surges
    assert summary["critical_severity"] + summary["high_severity"] > 0

    severities = {a["severity"] for a in alerts}
    # Check that severity levels are properly assigned
    for sev in severities:
        assert sev in ["Critical", "High", "Medium", "Low"]


def test_phenomenon_type_distinction():
    """Verify overnight alerts are labeled Potential Energy Wastage."""
    df_ovn = generate_energy_dataset(days=60, scenario="overnight_waste", random_seed=42)
    res = detect_anomalies(df_ovn)

    ovn_alerts = [a for a in res["alerts"] if a["category"] == "Overnight Baseload Shift"]
    assert len(ovn_alerts) > 0

    for a in ovn_alerts[:10]:
        assert a["phenomenon_type"] == "Potential Energy Wastage"
        assert a["hour"] in [22, 23, 0, 1, 2, 3, 4, 5]
        assert "Hypothesis" in a["investigation_hypothesis"]
        assert len(a["recommended_investigation"]) > 0


def test_evidence_strength_and_confidence():
    """Verify confidence score is between 0 and 1, and evidence strength string is populated."""
    df = generate_energy_dataset(days=60, scenario="sudden_spike", random_seed=42)
    res = detect_anomalies(df)

    for a in res["alerts"][:5]:
        assert 0.0 <= a["confidence_score"] <= 1.0
        assert a["confidence_label"] in ["High Confidence", "Medium Confidence", "Tentative Signal"]
        assert "Z-Score" in a["evidence_strength"]
        assert "NOT a physical probability of machine failure" in a["ml_disclaimer"]
