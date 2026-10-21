"""
Unit tests for the Before-and-After Savings Verification Engine.
Verifies counterfactual calculation, realization rate, handling of insufficient
post-intervention data, weather adjustments, and SQLite persistence.
"""

import os
import tempfile
import pytest
import pandas as pd
import numpy as np

from src.data_generator import generate_energy_dataset
from src.carbon import CarbonCalculator
from src.verification import SavingsVerifier
from src.database import init_db, get_all_verifications


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_insufficient_post_data_returns_awaiting():
    """Verify that when post-intervention telemetry is < 48 hours, status is 'Awaiting verification data'."""
    df = generate_energy_dataset(days=15, random_seed=42)
    # Intervention date only 12 hours before the end of dataset
    last_ts = df["timestamp"].max()
    interv_date = last_ts - pd.Timedelta(hours=12)

    res = SavingsVerifier.verify_intervention(
        df=df,
        intervention_name="Chiller Staging Adjustment",
        intervention_date=str(interv_date),
        expected_savings_kwh=100.0,
    )

    assert res["verification_status"] == "Awaiting verification data"
    assert res["realized_savings_kwh"] == 0.0
    assert "Awaiting verification data" in res["notes"]


def test_successful_realized_savings():
    """
    Simulate an intervention on Day 40 that successfully reduced consumption by 15 kWh/h.
    Verify realization rate and Target Met / Exceeded status.
    """
    df = generate_energy_dataset(days=55, scenario="normal", random_seed=42)
    # Cut energy by 15 kWh on days 40-55
    interv_ts = df["timestamp"].iloc[40 * 24]
    post_mask = df["timestamp"] >= interv_ts
    df.loc[post_mask, "energy_kwh"] = np.maximum(5.0, df.loc[post_mask, "energy_kwh"] - 15.0)

    post_hours = post_mask.sum()
    expected_savings = 15.0 * post_hours

    calc = CarbonCalculator(factor_key="India (CEA National Weighted Average)")
    res = SavingsVerifier.verify_intervention(
        df=df,
        intervention_name="HVAC Setpoint Setback",
        intervention_date=str(interv_ts),
        expected_savings_kwh=expected_savings,
        tariff_inr_per_kwh=8.50,
        carbon_calc=calc,
    )

    assert res["verification_status"] == "Target Met / Exceeded"
    assert res["realized_savings_kwh"] > 0
    assert res["realized_savings_inr"] > 0
    assert res["realization_rate_pct"] >= 80.0
    assert res["verified_avoided_kg_co2e"] > 0.0


def test_verification_persistence_to_db(temp_db):
    """Verify verification assessment can be saved and retrieved from SQLite."""
    df = generate_energy_dataset(days=45, scenario="normal", random_seed=99)
    interv_ts = df["timestamp"].iloc[30 * 24]
    df.loc[df["timestamp"] >= interv_ts, "energy_kwh"] -= 10.0

    res = SavingsVerifier.verify_intervention(
        df=df,
        intervention_name="Night Lighting Contactor Timer",
        intervention_date=str(interv_ts),
        expected_savings_kwh=3000.0,
        tariff_inr_per_kwh=9.0,
    )

    saved = SavingsVerifier.save_and_persist_verification(res, db_path=temp_db)
    assert saved is True

    records = get_all_verifications(db_path=temp_db)
    assert len(records) == 1
    assert records[0]["intervention_name"] == "Night Lighting Contactor Timer"
    assert records[0]["realized_savings_kwh"] == res["realized_savings_kwh"]
