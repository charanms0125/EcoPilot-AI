"""
Unit tests for the Carbon Calculator module.
Verifies emissions formulas, input validation, official factor metadata,
and strict labeling between potential vs verified emissions.
"""

import pytest
from src.carbon import CarbonCalculator, OFFICIAL_EMISSION_FACTORS


def test_standard_avoided_emissions():
    """Verify emissions formula using official India CEA factor (0.716 kg CO2e/kWh)."""
    calc = CarbonCalculator(factor_key="India (CEA National Weighted Average)")
    res = calc.calculate_avoided_emissions(electricity_saved_kwh=1000.0, is_verified=False)

    assert res["is_configured"] is True
    assert res["electricity_saved_kwh"] == 1000.0
    assert res["factor_kg_co2e_per_kwh"] == 0.716
    assert res["avoided_emissions_kg_co2e"] == 716.0
    assert res["avoided_emissions_tonnes_co2e"] == 0.716
    assert "Potential Avoided Emissions" in res["status_label"]
    assert res["is_verified"] is False
    assert "Central Electricity Authority" in res["source"]


def test_verified_avoided_emissions_label():
    """Verify that when is_verified=True, status label explicitly states Verified."""
    calc = CarbonCalculator(factor_key="India (CEA National Weighted Average)")
    res = calc.calculate_avoided_emissions(electricity_saved_kwh=500.0, is_verified=True)

    assert res["is_verified"] is True
    assert "Verified Avoided Emissions" in res["status_label"]
    assert res["avoided_emissions_kg_co2e"] == 358.0


def test_unconfigured_emission_factor():
    """Verify clean fallback when emission factor is not configured."""
    calc = CarbonCalculator(factor_key="Not Configured")
    res = calc.calculate_avoided_emissions(electricity_saved_kwh=500.0)

    assert res["is_configured"] is False
    assert res["status_label"] == "Emission factor not configured"
    assert res["avoided_emissions_kg_co2e"] is None
    assert "Emission factor not configured" in res["message"]


def test_negative_electricity_saved_raises_error():
    """Negative energy savings must be rejected with ValueError."""
    calc = CarbonCalculator(factor_key="India (CEA National Weighted Average)")
    with pytest.raises(ValueError, match="cannot be negative"):
        calc.calculate_avoided_emissions(electricity_saved_kwh=-100.0)


def test_zero_electricity_saved():
    """Zero energy savings produces zero emissions avoided without error."""
    calc = CarbonCalculator(factor_key="India (CEA National Weighted Average)")
    res = calc.calculate_avoided_emissions(electricity_saved_kwh=0.0)
    assert res["avoided_emissions_kg_co2e"] == 0.0
    assert res["avoided_emissions_tonnes_co2e"] == 0.0


def test_custom_emission_factor():
    """Verify custom factor requires documented source and positive value."""
    calc = CarbonCalculator(
        custom_factor=0.55,
        custom_source="State Pollution Control Board Grid Study 2024",
        custom_region="Regional State Grid",
    )
    res = calc.calculate_avoided_emissions(electricity_saved_kwh=200.0)
    assert res["factor_kg_co2e_per_kwh"] == 0.55
    assert res["avoided_emissions_kg_co2e"] == 110.0
    assert "State Pollution Control Board" in res["source"]

    # Negative custom factor must raise ValueError
    with pytest.raises(ValueError, match="strictly positive"):
        CarbonCalculator(custom_factor=-0.2, custom_source="Test")

    # Missing source citation must raise ValueError
    with pytest.raises(ValueError, match="documented official source citation"):
        CarbonCalculator(custom_factor=0.5, custom_source="")


def test_unknown_factor_key_raises_error():
    """Invalid factor key must raise ValueError."""
    with pytest.raises(ValueError, match="Unknown emission factor key"):
        CarbonCalculator(factor_key="NonExistentGrid")
