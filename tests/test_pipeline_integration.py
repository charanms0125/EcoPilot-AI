"""
End-to-End Pipeline Integration Test for EcoPilot AI.
Executes the complete unified workflow:
CSV Ingestion -> Schema Validation -> Anomaly Detection -> Forecasting & Intervals
-> Task Agent Synthesis -> Overlap-Discounted Savings -> Carbon Accounting
-> Decision Lifecycle & Audit Trail -> Before-and-After Verification -> Green AI Telemetry.
"""

import os
import tempfile
import pytest
import pandas as pd
import numpy as np

from src.data_generator import (
    generate_energy_dataset,
    validate_uploaded_csv,
    generate_data_quality_report,
)
from src.anomaly_detection import detect_anomalies
from src.forecasting import (
    train_and_evaluate_forecasting,
    predict_next_24_hours,
)
from src.agent import EcoPilotAgent
from src.savings import SavingsEngine
from src.carbon import CarbonCalculator
from src.verification import SavingsVerifier
from src.green_ai import GreenAIMonitor
from src.database import (
    init_db,
    get_all_recommendations,
    get_audit_trail,
    get_all_verifications,
    get_all_alerts,
)


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_full_ecopilot_pipeline(temp_db):
    """
    Test full end-to-end integration across all 12 platform capabilities.
    """
    monitor = GreenAIMonitor()

    # Step 1: Data Ingestion & Synthesis
    with monitor.time_task("Data Synthesis", "Synthetic Generator"):
        raw_df = generate_energy_dataset(
            days=60,
            building_category="Academic Block A",
            scenario="overnight_waste",
            random_seed=42,
        )
    assert len(raw_df) == 60 * 24
    assert "energy_kwh" in raw_df.columns

    # Step 2: CSV Schema Validation & Quality Reporting
    with monitor.time_task("CSV Validation", "Schema Validator"):
        is_valid, err_msg, cleaned_df = validate_uploaded_csv(raw_df)
    assert is_valid is True
    assert err_msg is None
    assert len(cleaned_df) == len(raw_df)

    quality_report = generate_data_quality_report(raw_df, cleaned_df)
    assert quality_report["is_valid"] is True
    assert quality_report["data_summary"]["total_consumption_kwh"] > 0

    # Step 3: Dual Anomaly Detection
    with monitor.time_task("Anomaly Detection", "Z-Score + IsoForest"):
        anomaly_results = detect_anomalies(cleaned_df, sensitivity_std=2.4)
    alerts = anomaly_results["alerts"]
    summary = anomaly_results["summary"]
    assert summary["total_anomalies"] > 0
    assert summary["overnight_waste_count"] > 0
    assert summary["total_excess_kwh"] > 100.0

    # Step 4: Multi-Model Forecasting & Model Selection
    with monitor.time_task("Energy Forecasting", "RandomForest + Seasonal + Naive"):
        fcst_results = train_and_evaluate_forecasting(cleaned_df, test_hours=48, val_hours=48)
    assert "preferred_model_name" in fcst_results
    assert fcst_results["metrics"]["rf_mae"] > 0
    assert fcst_results["metrics"]["prediction_interval"]["val_empirical_coverage_pct"] >= 50.0

    future_24h = predict_next_24_hours(
        model=fcst_results["model"],
        df=cleaned_df,
        interval_offsets=fcst_results["interval_offsets"],
        empirical_coverage_pct=fcst_results["metrics"]["prediction_interval"]["val_empirical_coverage_pct"],
    )
    assert len(future_24h) == 24

    # Step 5: Carbon Calculator Initialization
    carbon_calc = CarbonCalculator(factor_key="India (CEA National Weighted Average)")
    assert carbon_calc.is_configured is True
    assert carbon_calc.factor_kg_co2e_per_kwh == 0.716

    # Step 6: Evidence-Based AI Task Agent Synthesis
    with monitor.time_task("Agent Task Synthesis", "EcoPilotAgent Reasoning Engine"):
        agent = EcoPilotAgent(
            tariff_inr_per_kwh=8.50,
            carbon_factor_key="India (CEA National Weighted Average)",
            db_path=temp_db,
        )
        recommendations = agent.analyze_and_generate_recommendations(
            anomaly_results=anomaly_results,
            forecast_results=fcst_results,
            scenario_name="overnight_waste",
            building_category="Academic Block A",
        )
    assert len(recommendations) >= 3
    top_rec = recommendations[0]
    assert top_rec["status"] == "Pending"
    assert top_rec["priority_score"] >= 60
    assert top_rec["estimated_avoided_kg_co2e"] > 0.0

    # Step 7: Overlap-Discounted Portfolio Savings Simulation
    total_baseline_kwh = float(cleaned_df["energy_kwh"].sum())
    portfolio_res = SavingsEngine.calculate_portfolio_savings(
        recommendations=recommendations,
        overall_baseline_kwh=total_baseline_kwh,
        tariff_inr_per_kwh=8.50,
    )
    assert portfolio_res["deduplicated_saved_kwh"] > 0
    assert portfolio_res["deduplicated_saved_kwh"] <= portfolio_res["raw_sum_kwh"]

    # Step 8: Human Approval Decision Lifecycle & SQLite Audit Trail
    rec_id = top_rec["id"]
    approve_success = agent.approve_action(rec_id, note="Authorized by Energy Manager")
    assert approve_success is True

    persisted_recs = get_all_recommendations(db_path=temp_db)
    target = next(r for r in persisted_recs if r["id"] == rec_id)
    assert target["status"] == "Approved"

    complete_success = agent.complete_action(rec_id, note="Physical timer installed on panel")
    assert complete_success is True

    audit = get_audit_trail(rec_id, db_path=temp_db)
    assert len(audit) >= 3  # Initial creation -> Approved -> Completed

    # Check alert persistence
    db_alerts = get_all_alerts(db_path=temp_db)
    assert len(db_alerts) > 0

    # Step 9: Before-and-After Savings Verification
    # Simulate follow-up data where overnight waste was successfully fixed
    post_df = cleaned_df.copy()
    interv_ts = post_df["timestamp"].iloc[45 * 24]
    # Reduce post-period consumption
    post_mask = post_df["timestamp"] >= interv_ts
    post_df.loc[post_mask, "energy_kwh"] = np.maximum(5.0, post_df.loc[post_mask, "energy_kwh"] - 14.0)

    verif_res = SavingsVerifier.verify_intervention(
        df=post_df,
        intervention_name="Overnight Contactor Interlock Timer",
        intervention_date=str(interv_ts),
        expected_savings_kwh=1000.0,
        tariff_inr_per_kwh=8.50,
        carbon_calc=carbon_calc,
        rec_id=rec_id,
    )
    assert verif_res["verification_status"] == "Target Met / Exceeded"
    assert verif_res["realized_savings_kwh"] > 0
    assert verif_res["verified_avoided_kg_co2e"] > 0

    # Persist verification
    SavingsVerifier.save_and_persist_verification(verif_res, db_path=temp_db)
    saved_verifs = get_all_verifications(db_path=temp_db)
    assert len(saved_verifs) == 1
    assert saved_verifs[0]["verification_status"] == "Target Met / Exceeded"

    # Step 10: Green AI Monitor Metrics Verification
    green_summary = monitor.get_metrics_summary()
    assert green_summary["total_logged_tasks"] >= 4
    assert green_summary["total_measured_execution_ms"] > 0
    assert green_summary["is_zero_cost_local"] is True

    pipeline_comp = monitor.get_pipeline_comparison()
    assert "faster" in pipeline_comp["comparison_metrics"]["latency_speedup"]
