"""
Unit tests for the Savings Calculation & What-If Simulation Engine.
Verifies formulas, boundary constraints, input validation, and portfolio overlap discounting.
"""

import pytest
from src.savings import SavingsEngine


def test_standard_savings_calculation():
    """Verify single saving formula under normal valid parameters."""
    res = SavingsEngine.calculate_single_saving(
        baseline_eligible_kwh=1000.0,
        reduction_percentage=20.0,
        tariff_inr_per_kwh=8.50,
        action_name="HVAC Setpoint Optimization",
    )
    assert res["energy_saved_kwh"] == 200.0
    assert res["cost_savings_inr"] == 1700.0  # 200 * 8.5
    assert res["proposed_consumption_kwh"] == 800.0
    assert res["proposed_cost_inr"] == 6800.0  # 800 * 8.5
    assert res["reduction_percentage"] == 20.0
    assert res["status"] == "Estimated Savings"
    assert len(res["assumptions"]) > 0


def test_zero_reduction():
    """Verify zero percent reduction yields zero savings without errors."""
    res = SavingsEngine.calculate_single_saving(
        baseline_eligible_kwh=500.0,
        reduction_percentage=0.0,
        tariff_inr_per_kwh=10.0,
    )
    assert res["energy_saved_kwh"] == 0.0
    assert res["cost_savings_inr"] == 0.0
    assert res["proposed_consumption_kwh"] == 500.0


def test_hundred_percent_reduction():
    """Verify 100% reduction eliminates consumption without negative values."""
    res = SavingsEngine.calculate_single_saving(
        baseline_eligible_kwh=300.0,
        reduction_percentage=100.0,
        tariff_inr_per_kwh=7.50,
    )
    assert res["energy_saved_kwh"] == 300.0
    assert res["proposed_consumption_kwh"] == 0.0
    assert res["cost_savings_inr"] == 2250.0


def test_negative_baseline_raises_error():
    """Negative baseline consumption must be rejected with ValueError."""
    with pytest.raises(ValueError, match="cannot be negative"):
        SavingsEngine.calculate_single_saving(
            baseline_eligible_kwh=-50.0,
            reduction_percentage=10.0,
            tariff_inr_per_kwh=8.50,
        )


def test_impossible_percentage_raises_error():
    """Reduction > 100% or < 0% must be rejected with ValueError."""
    with pytest.raises(ValueError, match="between 0.0% and 100.0%"):
        SavingsEngine.calculate_single_saving(
            baseline_eligible_kwh=100.0,
            reduction_percentage=125.0,
            tariff_inr_per_kwh=8.50,
        )

    with pytest.raises(ValueError, match="between 0.0% and 100.0%"):
        SavingsEngine.calculate_single_saving(
            baseline_eligible_kwh=100.0,
            reduction_percentage=-15.0,
            tariff_inr_per_kwh=8.50,
        )


def test_zero_or_negative_tariff_raises_error():
    """Tariff <= 0 must be rejected with ValueError to prevent division by zero or invalid accounting."""
    with pytest.raises(ValueError, match="strictly positive"):
        SavingsEngine.calculate_single_saving(
            baseline_eligible_kwh=100.0,
            reduction_percentage=10.0,
            tariff_inr_per_kwh=0.0,
        )

    with pytest.raises(ValueError, match="strictly positive"):
        SavingsEngine.calculate_single_saving(
            baseline_eligible_kwh=100.0,
            reduction_percentage=10.0,
            tariff_inr_per_kwh=-5.0,
        )


def test_portfolio_overlap_discounting():
    """
    Ensure multiple recommendations are not simply added naively if they exceed baseline,
    and multiplicative compounding prevents double counting.
    """
    recs = [
        {"estimated_kwh_saving": 300.0},
        {"estimated_kwh_saving": 250.0},
        {"estimated_kwh_saving": 200.0},
    ]
    baseline = 800.0
    tariff = 8.0

    res = SavingsEngine.calculate_portfolio_savings(recs, baseline, tariff)

    # Raw sum is 750 kWh
    assert res["raw_sum_kwh"] == 750.0
    # Deduplicated must be <= raw sum and strictly capped at baseline * 0.85
    assert res["deduplicated_saved_kwh"] < res["raw_sum_kwh"]
    assert res["deduplicated_saved_kwh"] <= baseline * 0.85
    assert res["overlap_correction_kwh"] > 0
    assert res["deduplicated_saved_inr"] == round(res["deduplicated_saved_kwh"] * tariff, 2)


def test_empty_portfolio():
    """Verify empty recommendation list returns clean zeroed metrics without crashing."""
    res = SavingsEngine.calculate_portfolio_savings([], 500.0, 8.5)
    assert res["total_actions"] == 0
    assert res["deduplicated_saved_kwh"] == 0.0
    assert res["deduplicated_saved_inr"] == 0.0
