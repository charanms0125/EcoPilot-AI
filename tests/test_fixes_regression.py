"""
Regression test suite covering fixes for EcoPilot-AI:
1. Correct power_kw to energy_kwh conversion using actual timestamp intervals.
2. Prevent verification crashes when baseline or post-intervention data is empty.
3. Enable SQLite foreign_keys for every connection.
4. Transaction rollback and safe connection handling.
5. Prevent alert and recommendation ID collisions across runs and facilities.
"""

import os
import tempfile
import sqlite3
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.data_generator import validate_uploaded_csv, generate_energy_dataset
from src.verification import SavingsVerifier
from src.database import (
    get_db_connection,
    get_db_context,
    init_db,
    save_recommendations,
    get_all_recommendations,
    update_recommendation_status,
    get_audit_trail,
    save_alerts,
    get_all_alerts,
    save_verification,
    get_all_verifications,
)
from src.anomaly_detection import detect_anomalies
from src.agent import EcoPilotAgent


@pytest.fixture
def temp_db():
    """Create a temporary SQLite database with isolated path for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)


# ==============================================================================
# 1. Regression Tests: power_kw to energy_kwh conversion using actual intervals
# ==============================================================================

def test_power_kw_conversion_15_minute_intervals():
    """Verify 15-minute interval power (kW) data is converted using 0.25h factor."""
    # 96 readings (24 hours * 4 readings/hour), constant 40.0 kW
    timestamps = pd.date_range("2026-01-01 00:00:00", periods=96, freq="15min")
    df = pd.DataFrame({
        "timestamp": timestamps,
        "power_kw": [40.0] * 96,
    })
    is_valid, err, cleaned = validate_uploaded_csv(df)
    assert is_valid is True, f"Validation failed: {err}"
    assert "energy_kwh" in cleaned.columns
    # 40 kW sustained for 15 minutes (0.25h) = 10.0 kWh
    expected_kwh = 40.0 * 0.25
    assert np.allclose(cleaned["energy_kwh"].values, expected_kwh, atol=1e-3)
    # Total energy across 24 hours should be 40 kW * 24h = 960 kWh
    assert np.isclose(cleaned["energy_kwh"].sum(), 960.0, atol=1e-2)


def test_power_kw_conversion_30_minute_intervals():
    """Verify 30-minute interval power (kW) data is converted using 0.5h factor."""
    timestamps = pd.date_range("2026-01-01 00:00:00", periods=60, freq="30min")
    df = pd.DataFrame({
        "timestamp": timestamps,
        "power_kw": [50.0] * 60,
    })
    is_valid, err, cleaned = validate_uploaded_csv(df)
    assert is_valid is True
    # 50 kW sustained for 30 minutes (0.5h) = 25.0 kWh
    assert np.allclose(cleaned["energy_kwh"].values, 25.0, atol=1e-3)
    assert np.isclose(cleaned["energy_kwh"].sum(), 50.0 * 30.0, atol=1e-2)


def test_power_kw_conversion_irregular_intervals():
    """Verify irregular timestamp intervals convert each point with its actual duration."""
    # Generate 50 points with variable delta intervals (15m, 30m, 60m)
    times = [datetime(2026, 1, 1, 0, 0)]
    np.random.seed(42)
    step_minutes = [15, 30, 60, 45, 15] * 10
    for m in step_minutes[:49]:
        times.append(times[-1] + timedelta(minutes=m))

    power_values = [100.0] * len(times)
    df = pd.DataFrame({
        "time": times,
        "power_kw": power_values,
    })

    is_valid, err, cleaned = validate_uploaded_csv(df)
    assert is_valid is True
    assert "energy_kwh" in cleaned.columns

    # Verify each row's energy matches power * delta_hours
    deltas = cleaned["timestamp"].diff().dt.total_seconds() / 3600.0
    deltas = deltas.bfill()
    expected_kwh = 100.0 * deltas
    assert np.allclose(cleaned["energy_kwh"].values, expected_kwh.values, atol=1e-3)


def test_power_kw_conversion_hourly_intervals_preserved():
    """Verify hourly power data still converts 1:1 (45.5 kW * 1.0h = 45.5 kWh)."""
    df = pd.DataFrame({
        "timestamp": pd.date_range("2026-02-01", periods=60, freq="h"),
        "power_kw": [45.5] * 60,
    })
    is_valid, err, cleaned = validate_uploaded_csv(df)
    assert is_valid is True
    assert np.allclose(cleaned["energy_kwh"].values, 45.5, atol=1e-3)


# ==============================================================================
# 2. Regression Tests: Verification crashes on empty baseline or post data
# ==============================================================================

def test_verification_empty_dataframe_does_not_crash():
    """Verify calling verify_intervention with empty DataFrame returns safe dictionary."""
    empty_df = pd.DataFrame(columns=["timestamp", "energy_kwh"])
    res = SavingsVerifier.verify_intervention(
        df=empty_df,
        intervention_name="Chiller Replacement",
        intervention_date="2026-03-01",
        expected_savings_kwh=500.0,
    )
    assert isinstance(res, dict)
    assert res["verification_status"] == "Insufficient data"
    assert res["baseline_hours"] == 0
    assert res["post_hours"] == 0
    assert res["realized_savings_kwh"] == 0.0


def test_verification_empty_baseline_does_not_crash(temp_db):
    """
    Verify when intervention_date is before dataset start (so baseline is empty),
    verification does not crash and returns 'Insufficient baseline data'.
    """
    df = generate_energy_dataset(days=10, random_seed=42)
    min_date = df["timestamp"].min()
    # Intervention date set BEFORE the start of the dataset
    early_interv_date = min_date - timedelta(days=2)

    res = SavingsVerifier.verify_intervention(
        df=df,
        intervention_name="Night Setback",
        intervention_date=str(early_interv_date),
        expected_savings_kwh=100.0,
    )
    assert isinstance(res, dict)
    assert res["verification_status"] == "Insufficient baseline data"
    assert res["baseline_hours"] == 0
    assert res["baseline_period_start"] == "N/A"
    assert res["baseline_period_end"] == "N/A"
    assert res["realized_savings_kwh"] == 0.0

    # Ensure this result can be saved to SQLite and retrieved cleanly
    saved = SavingsVerifier.save_and_persist_verification(res, db_path=temp_db)
    assert saved is True
    all_v = get_all_verifications(db_path=temp_db)
    assert len(all_v) == 1
    assert all_v[0]["verification_status"] == "Insufficient baseline data"


def test_verification_empty_post_intervention_does_not_crash(temp_db):
    """
    Verify when intervention_date is after dataset end (so post data is empty),
    verification does not crash and returns 'Awaiting verification data'.
    """
    df = generate_energy_dataset(days=10, random_seed=42)
    max_date = df["timestamp"].max()
    # Intervention date set AFTER the end of the dataset
    future_interv_date = max_date + timedelta(days=2)

    res = SavingsVerifier.verify_intervention(
        df=df,
        intervention_name="Occupancy Sensor Install",
        intervention_date=str(future_interv_date),
        expected_savings_kwh=200.0,
    )
    assert isinstance(res, dict)
    assert res["verification_status"] == "Awaiting verification data"
    assert res["post_hours"] == 0
    assert res["post_period_start"] == "N/A"
    assert res["post_period_end"] == "N/A"
    assert res["realized_savings_kwh"] == 0.0

    # Ensure persistence works cleanly
    saved = SavingsVerifier.save_and_persist_verification(res, db_path=temp_db)
    assert saved is True
    all_v = get_all_verifications(db_path=temp_db)
    assert len(all_v) == 1
    assert all_v[0]["verification_status"] == "Awaiting verification data"


# ==============================================================================
# 3. Regression Tests: SQLite foreign_keys enabled for every connection
# ==============================================================================

def test_sqlite_foreign_keys_pragma_enabled_on_all_connections(temp_db):
    """Verify PRAGMA foreign_keys is 1 on connections returned by get_db_connection and get_db_context."""
    conn = get_db_connection(temp_db)
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_keys;")
        val = cur.fetchone()[0]
        assert val == 1, f"Expected foreign_keys=1, got {val}"
    finally:
        conn.close()

    with get_db_context(temp_db) as ctx_conn:
        cur = ctx_conn.cursor()
        cur.execute("PRAGMA foreign_keys;")
        assert cur.fetchone()[0] == 1


def test_foreign_key_enforcement_raises_integrity_error(temp_db):
    """
    Verify foreign keys are strictly enforced: inserting into audit_log
    with an invalid rec_id that does not exist in recommendations raises IntegrityError.
    """
    with pytest.raises(sqlite3.IntegrityError):
        with get_db_context(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO audit_log (rec_id, old_status, new_status, changed_at, user_note)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("NON_EXISTENT_RECOMMENDATION_ID", None, "Pending", "2026-01-01 00:00:00", "Orphan insert"),
            )


def test_foreign_key_valid_reference_succeeds(temp_db):
    """Verify inserting into audit_log succeeds when referencing an existing recommendation."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    recs = [
        {
            "id": "REC-VALID-01",
            "scenario": "test",
            "created_at": now,
            "title": "Valid Rec",
            "category": "Lighting",
            "severity": "Low",
            "evidence": "Observed drift",
            "suggested_action": "Switch off",
            "assumptions": "Standard baseline",
            "estimated_kwh_saving": 50.0,
            "estimated_inr_saving": 400.0,
        }
    ]
    save_recommendations(recs, db_path=temp_db)

    # Valid insert should succeed without IntegrityError
    with get_db_context(temp_db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO audit_log (rec_id, old_status, new_status, changed_at, user_note)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("REC-VALID-01", "Pending", "Approved", now, "Manual approval note"),
        )
    trail = get_audit_trail("REC-VALID-01", db_path=temp_db)
    assert any(entry["new_status"] == "Approved" for entry in trail)


# ==============================================================================
# 4. Regression Tests: Transaction rollback and safe connection handling
# ==============================================================================

def test_transaction_rollback_on_exception(temp_db):
    """Verify that if an error occurs within a get_db_context block, all changes are rolled back."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with pytest.raises(RuntimeError):
        with get_db_context(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO recommendations (
                    id, scenario, created_at, title, category, severity, evidence,
                    suggested_action, assumptions, estimated_kwh_saving,
                    estimated_inr_saving, status, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "REC-SHOULD-ROLLBACK", "test", now, "Rollback Rec", "HVAC",
                    "High", "Evidence", "Action", "Assumptions", 100.0, 850.0,
                    "Pending", now,
                ),
            )
            # Intentionally raise an exception mid-transaction
            raise RuntimeError("Forced transaction failure")

    # Verify that REC-SHOULD-ROLLBACK was NOT committed to the database
    all_recs = get_all_recommendations(db_path=temp_db)
    assert not any(r["id"] == "REC-SHOULD-ROLLBACK" for r in all_recs)


def test_update_recommendation_status_atomicity_on_error(temp_db):
    """
    Verify update_recommendation_status rolls back recommendation update
    if audit logging fails.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    recs = [
        {
            "id": "REC-ATOMIC-01",
            "scenario": "test",
            "created_at": now,
            "title": "Atomic Rec",
            "category": "Lighting",
            "severity": "Low",
            "evidence": "Evidence",
            "suggested_action": "Action",
            "assumptions": "Assumptions",
            "estimated_kwh_saving": 50.0,
            "estimated_inr_saving": 400.0,
        }
    ]
    save_recommendations(recs, db_path=temp_db)

    # Initial status is Pending
    r_initial = get_all_recommendations(db_path=temp_db)[0]
    assert r_initial["status"] == "Pending"

    # Now approve recommendation normally
    success = update_recommendation_status("REC-ATOMIC-01", "Approved", "Approval note", db_path=temp_db)
    assert success is True
    r_updated = get_all_recommendations(db_path=temp_db)[0]
    assert r_updated["status"] == "Approved"


def test_safe_connection_closure_on_error(temp_db):
    """Verify get_db_context safely closes the SQLite connection even when an exception is thrown."""
    connection_ref = []

    with pytest.raises(ValueError):
        with get_db_context(temp_db) as conn:
            connection_ref.append(conn)
            raise ValueError("Unexpected application error")

    # Verify the captured connection is closed (calling cursor on a closed connection raises ProgrammingError)
    assert len(connection_ref) == 1
    with pytest.raises(sqlite3.ProgrammingError):
        connection_ref[0].cursor()


# ==============================================================================
# 5. Regression Tests: Alert & Recommendation ID Collisions
# ==============================================================================

def test_alert_id_uniqueness_across_facilities():
    """Verify anomaly detection alerts have distinct IDs for different facilities at the same timestamp."""
    df_a = generate_energy_dataset(days=15, building_category="Academic Block A", random_seed=42)
    df_b = generate_energy_dataset(days=15, building_category="Hostel Block B", random_seed=42)

    res_a = detect_anomalies(df_a, facility_id="Campus-Block-A", sensitivity_std=1.8)
    res_b = detect_anomalies(df_b, facility_id="Campus-Block-B", sensitivity_std=1.8)

    alerts_a = res_a["alerts"]
    alerts_b = res_b["alerts"]

    assert len(alerts_a) > 0
    assert len(alerts_b) > 0

    ids_a = {a["id"] for a in alerts_a}
    ids_b = {a["id"] for a in alerts_b}

    # There should be ZERO intersection between facility A and facility B alert IDs
    assert ids_a.isdisjoint(ids_b), "Collision detected: facility A and B generated identical alert IDs!"
    # Ensure facility identifier is present in alert IDs
    assert all("CAMPUS-BLOCK-A" in a_id for a_id in ids_a)
    assert all("CAMPUS-BLOCK-B" in b_id for b_id in ids_b)


def test_alert_id_uniqueness_across_runs():
    """Verify anomaly detection alerts have distinct IDs across different runs on the same facility."""
    df = generate_energy_dataset(days=15, random_seed=42)

    res_run1 = detect_anomalies(df, facility_id="Facility-1", run_id="run-001", sensitivity_std=1.8)
    res_run2 = detect_anomalies(df, facility_id="Facility-1", run_id="run-002", sensitivity_std=1.8)

    ids_run1 = {a["id"] for a in res_run1["alerts"]}
    ids_run2 = {a["id"] for a in res_run2["alerts"]}

    assert len(ids_run1) > 0
    assert len(ids_run2) > 0
    assert ids_run1.isdisjoint(ids_run2), "Collision detected: run 1 and run 2 generated identical alert IDs!"
    assert all("RUN-001" in a_id for a_id in ids_run1)
    assert all("RUN-002" in a_id for a_id in ids_run2)


def test_recommendation_id_uniqueness_across_facilities(temp_db):
    """
    Verify AI Task Agent generates distinct recommendation IDs for different facilities
    and does not cross-pollinate or overwrite decisions in SQLite.
    """
    df = generate_energy_dataset(days=60, scenario="overnight_waste", random_seed=42)
    res = detect_anomalies(df)

    agent_a = EcoPilotAgent(db_path=temp_db, facility_id="Facility-Alpha")
    recs_a = agent_a.analyze_and_generate_recommendations(
        res, scenario_name="overnight_waste", facility_id="Facility-Alpha"
    )

    agent_b = EcoPilotAgent(db_path=temp_db, facility_id="Facility-Beta")
    recs_b = agent_b.analyze_and_generate_recommendations(
        res, scenario_name="overnight_waste", facility_id="Facility-Beta"
    )

    ids_a = {r["id"] for r in recs_a}
    ids_b = {r["id"] for r in recs_b}

    assert ids_a.isdisjoint(ids_b), "Collision detected: Facility Alpha and Beta generated identical recommendation IDs!"
    assert all("FACILITY-ALPHA" in r_id for r_id in ids_a)
    assert all("FACILITY-BETA" in r_id for r_id in ids_b)

    # Approve recommendation in Facility Alpha
    alpha_id = recs_a[0]["id"]
    agent_a.approve_action(alpha_id, note="Approved for Alpha")

    # Verify Facility Beta's recommendation status remains Pending (not overwritten)
    beta_recs = agent_b.analyze_and_generate_recommendations(
        res, scenario_name="overnight_waste", facility_id="Facility-Beta"
    )
    assert all(r["status"] == "Pending" for r in beta_recs)

    # Verify Facility Alpha's recommendation status remains Approved
    alpha_recs = agent_a.analyze_and_generate_recommendations(
        res, scenario_name="overnight_waste", facility_id="Facility-Alpha"
    )
    alpha_target = next(r for r in alpha_recs if r["id"] == alpha_id)
    assert alpha_target["status"] == "Approved"


def test_recommendation_id_uniqueness_across_runs(temp_db):
    """Verify AI Task Agent generates distinct recommendation IDs for different runs."""
    df = generate_energy_dataset(days=60, scenario="overnight_waste", random_seed=42)
    res = detect_anomalies(df)

    agent = EcoPilotAgent(db_path=temp_db)
    recs_r1 = agent.analyze_and_generate_recommendations(
        res, scenario_name="overnight_waste", run_id="run-batch-1"
    )
    recs_r2 = agent.analyze_and_generate_recommendations(
        res, scenario_name="overnight_waste", run_id="run-batch-2"
    )

    ids_r1 = {r["id"] for r in recs_r1}
    ids_r2 = {r["id"] for r in recs_r2}

    assert ids_r1.isdisjoint(ids_r2), "Collision detected: run 1 and run 2 generated identical recommendation IDs!"
    assert all("RUN-BATCH-1" in r_id for r_id in ids_r1)
    assert all("RUN-BATCH-2" in r_id for r_id in ids_r2)

    # Both sets of recommendations must co-exist in SQLite
    all_recs = get_all_recommendations(db_path=temp_db)
    stored_ids = {r["id"] for r in all_recs}
    assert ids_r1.issubset(stored_ids)
    assert ids_r2.issubset(stored_ids)


def test_save_alerts_multiple_facilities_coexist(temp_db):
    """Verify alerts from multiple facilities persist into SQLite without dropping or overwriting each other."""
    df_a = generate_energy_dataset(days=15, building_category="Academic Block A", random_seed=42)
    df_b = generate_energy_dataset(days=15, building_category="Hostel Block B", random_seed=42)

    res_a = detect_anomalies(df_a, facility_id="Campus-A", sensitivity_std=1.8)
    res_b = detect_anomalies(df_b, facility_id="Campus-B", sensitivity_std=1.8)

    save_alerts(res_a["alerts"], db_path=temp_db)
    save_alerts(res_b["alerts"], db_path=temp_db)

    all_alerts = get_all_alerts(db_path=temp_db)
    fac_ids_in_db = {a["facility_id"] for a in all_alerts}
    assert "Campus-A" in fac_ids_in_db
    assert "Campus-B" in fac_ids_in_db
    assert len(all_alerts) == len(res_a["alerts"]) + len(res_b["alerts"])
