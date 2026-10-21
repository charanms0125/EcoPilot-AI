"""
Unit tests for the upgraded AI Task Agent and State Machine transitions.
Verifies priority score formula, recommendation schema fields,
valid lifecycle transitions, and rejection of invalid state transitions.
"""

import os
import tempfile
import pytest

from src.data_generator import generate_energy_dataset
from src.anomaly_detection import detect_anomalies
from src.agent import EcoPilotAgent
from src.database import (
    init_db,
    get_all_recommendations,
    update_recommendation_status,
    get_audit_trail,
)


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_priority_score_deterministic():
    """Verify priority score respects bounds [10, 100] and scales with impact."""
    score_high = EcoPilotAgent.calculate_priority_score(
        estimated_kwh_saving=1200.0,
        estimated_inr_saving=10000.0,
        severity="Critical",
        confidence_score=0.9,
    )
    score_low = EcoPilotAgent.calculate_priority_score(
        estimated_kwh_saving=50.0,
        estimated_inr_saving=400.0,
        severity="Low",
        confidence_score=0.7,
    )

    assert 10 <= score_low < score_high <= 100
    assert score_high >= 70


def test_state_machine_rejects_invalid_transitions(temp_db):
    """Verify state machine rejects invalid state jumps (e.g. Rejected -> Completed)."""
    agent = EcoPilotAgent(tariff_inr_per_kwh=8.50, db_path=temp_db)
    df = generate_energy_dataset(days=60, scenario="overnight_waste", random_seed=42)
    res = detect_anomalies(df)
    recs = agent.analyze_and_generate_recommendations(res, scenario_name="test_state")

    rec_id = recs[0]["id"]

    # 1. Reject the recommendation (Pending -> Rejected: valid)
    rejected = agent.reject_action(rec_id, note="Rejected due to budget limits")
    assert rejected is True

    # 2. Attempt invalid jump: Rejected -> Completed (must be REJECTED by state machine)
    invalid_jump = agent.complete_action(rec_id, note="Sneaking into completed")
    assert invalid_jump is False, "State machine failed: Rejected item was marked Completed directly!"

    # 3. Check status is still Rejected
    current_recs = get_all_recommendations(db_path=temp_db)
    current_rec = next(r for r in current_recs if r["id"] == rec_id)
    assert current_rec["status"] == "Rejected"

    # 4. Reopen to Pending first (Rejected -> Pending: valid)
    reopened = update_recommendation_status(rec_id, "Pending", "Reopening for review", temp_db)
    assert reopened is True

    # 5. Now approve (Pending -> Approved: valid)
    approved = agent.approve_action(rec_id, note="Now approved after budget clearance")
    assert approved is True

    # 6. Now complete (Approved -> Completed: valid)
    completed = agent.complete_action(rec_id, note="Installed and operational")
    assert completed is True


def test_recommendation_rich_schema_fields(temp_db):
    """Verify recommendation dict includes carbon impact, risk, effort, and priority fields."""
    agent = EcoPilotAgent(
        tariff_inr_per_kwh=8.50,
        carbon_factor_key="India (CEA National Weighted Average)",
        db_path=temp_db,
    )
    df = generate_energy_dataset(days=60, scenario="overnight_waste", random_seed=42)
    res = detect_anomalies(df)
    recs = agent.analyze_and_generate_recommendations(res, scenario_name="overnight_waste")

    ovn_rec = next(r for r in recs if "Overnight" in r["title"])
    assert ovn_rec["priority_score"] >= 60
    assert ovn_rec["implementation_effort"] in ["Low", "Medium", "High"]
    assert ovn_rec["operational_risk"] in ["Low", "Medium", "High"]
    assert ovn_rec["estimated_avoided_kg_co2e"] > 0.0
    assert len(ovn_rec["recommended_next_action"]) > 0
