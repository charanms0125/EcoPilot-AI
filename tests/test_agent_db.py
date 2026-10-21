"""
Unit tests for Anomaly Detection, AI Task Agent, and SQLite Persistence.
Verifies detection on injected scenarios, recommendation generation,
decision status updates, and audit trail records.
"""

import os
import tempfile
import pytest
import pandas as pd

from src.data_generator import generate_energy_dataset, validate_uploaded_csv
from src.anomaly_detection import detect_anomalies
from src.agent import EcoPilotAgent
from src.database import (
    init_db,
    get_all_recommendations,
    update_recommendation_status,
    get_audit_trail,
    save_simulation,
    get_all_simulations,
)


@pytest.fixture
def temp_db():
    """Create a temporary SQLite database for isolated test execution."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_anomaly_detection_on_known_injected_spike():
    """Verify anomaly detector accurately flags injected high-draw sudden spikes."""
    df = generate_energy_dataset(days=60, scenario="sudden_spike", random_seed=42)
    res = detect_anomalies(df, sensitivity_std=2.5)

    alerts = res["alerts"]
    assert len(alerts) > 0

    # Ensure spike hours were captured
    spike_alerts = [a for a in alerts if a["category"] == "Peak / Unexpected Daytime Spike"]
    assert len(spike_alerts) > 0
    # Check that highest severity alert contains detailed evidence
    top_alert = max(alerts, key=lambda a: a["absolute_diff_kwh"])
    assert top_alert["severity"] in ["High", "Critical"]
    assert top_alert["observed_kwh"] > top_alert["expected_baseline_kwh"]
    assert "Hypothesis" in top_alert["investigation_hypothesis"]


def test_anomaly_detection_on_overnight_waste():
    """Verify overnight waste is detected in nocturnal hours (22:00-06:00)."""
    df = generate_energy_dataset(days=60, scenario="overnight_waste", random_seed=42)
    res = detect_anomalies(df)

    summary = res["summary"]
    assert summary["overnight_waste_count"] > 10
    assert summary["total_excess_kwh"] > 100.0

    ovn_alerts = [a for a in res["alerts"] if a["category"] == "Overnight Baseload Shift"]
    for alert in ovn_alerts[:5]:
        assert alert["hour"] in [22, 23, 0, 1, 2, 3, 4, 5]


def test_agent_generates_evidence_linked_recommendations(temp_db):
    """Verify agent ingests anomalies and creates recommendations with evidence and assumptions."""
    df = generate_energy_dataset(days=60, scenario="overnight_waste", random_seed=42)
    res = detect_anomalies(df)

    agent = EcoPilotAgent(tariff_inr_per_kwh=8.50, db_path=temp_db)
    recs = agent.analyze_and_generate_recommendations(
        anomaly_results=res,
        scenario_name="overnight_waste",
    )

    assert len(recs) > 0
    ovn_rec = next((r for r in recs if "Overnight" in r["title"]), None)
    assert ovn_rec is not None
    assert ovn_rec["status"] == "Pending"
    assert ovn_rec["estimated_kwh_saving"] > 0
    assert ovn_rec["estimated_inr_saving"] > 0
    assert "Assumes" in ovn_rec["assumptions"]
    assert "hours" in ovn_rec["evidence"].lower()


def test_sqlite_decision_lifecycle_and_audit_trail(temp_db):
    """Test full decision lifecycle: Pending -> Approved -> Completed, with audit tracking."""
    agent = EcoPilotAgent(tariff_inr_per_kwh=9.0, db_path=temp_db)
    df = generate_energy_dataset(days=60, scenario="overnight_waste", random_seed=42)
    res = detect_anomalies(df)
    recs = agent.analyze_and_generate_recommendations(res, scenario_name="test_run")

    target_id = recs[0]["id"]

    # 1. Approve recommendation
    success = agent.approve_action(target_id, note="Approved by Campus Facility Lead")
    assert success is True

    updated_recs = get_all_recommendations(db_path=temp_db)
    target_rec = next(r for r in updated_recs if r["id"] == target_id)
    assert target_rec["status"] == "Approved"
    assert "Approved by Campus Facility Lead" in target_rec["notes"]

    # 2. Mark complete
    agent.complete_action(target_id, note="Timer installed on MCCB-3")
    completed_recs = get_all_recommendations(db_path=temp_db)
    target_rec = next(r for r in completed_recs if r["id"] == target_id)
    assert target_rec["status"] == "Completed"

    # 3. Check audit trail
    audit = get_audit_trail(target_id, db_path=temp_db)
    assert len(audit) >= 3  # Initial Creation + Approval + Completion
    statuses = [a["new_status"] for a in audit]
    assert "Pending" in statuses
    assert "Approved" in statuses
    assert "Completed" in statuses


def test_csv_upload_validation():
    """Verify validation of uploaded custom CSV files."""
    # Valid CSV
    valid_df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-01", periods=100, freq="h"),
            "energy_kwh": [25.0] * 100,
        }
    )
    is_valid, err, cleaned = validate_uploaded_csv(valid_df)
    assert is_valid is True
    assert err is None
    assert len(cleaned) == 100

    # Missing energy column
    invalid_df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-01", periods=100, freq="h"),
            "temperature": [28.0] * 100,
        }
    )
    is_valid, err, cleaned = validate_uploaded_csv(invalid_df)
    assert is_valid is False
    assert "Missing required energy" in err
