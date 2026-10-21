"""
Unit tests for the upgraded CSV Data Validation and Ingestion Pipeline.
Verifies column tolerance, power (kW) to energy (kWh) conversion, duplicate timestamp
handling, negative value sanitization, row limits, and sample CSV export.
"""

import pytest
import pandas as pd
import numpy as np

from src.data_generator import (
    validate_uploaded_csv,
    generate_data_quality_report,
    get_sample_csv_content,
)


def test_valid_csv_standard():
    """Verify standard valid CSV with timestamp and energy_kwh."""
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-01", periods=100, freq="h"),
            "energy_kwh": [25.0] * 100,
        }
    )
    is_valid, err, cleaned = validate_uploaded_csv(df)
    assert is_valid is True
    assert err is None
    assert len(cleaned) == 100


def test_power_kw_to_energy_kwh_conversion():
    """Verify CSV with power_kw is successfully converted to energy_kwh."""
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2026-02-01", periods=60, freq="h"),
            "power_kw": [45.5] * 60,
        }
    )
    is_valid, err, cleaned = validate_uploaded_csv(df)
    assert is_valid is True
    assert "energy_kwh" in cleaned.columns
    assert cleaned["energy_kwh"].iloc[0] == 45.5


def test_duplicate_timestamps_deduplicated():
    """Verify duplicate timestamps are resolved by keeping first occurrence."""
    dates = pd.date_range("2026-03-01", periods=50, freq="h").tolist()
    # Add 5 duplicates
    dates.extend(dates[:5])
    df = pd.DataFrame({"timestamp": dates, "energy_kwh": [30.0] * len(dates)})
    is_valid, err, cleaned = validate_uploaded_csv(df)
    assert is_valid is True
    assert len(cleaned) == 50


def test_negative_values_clipped_to_zero():
    """Verify negative energy readings are clipped to 0.0 with warning preserved."""
    vals = [20.0] * 50
    vals[10] = -15.0
    vals[25] = -4.0
    df = pd.DataFrame({"timestamp": pd.date_range("2026-04-01", periods=50, freq="h"), "energy_kwh": vals})
    is_valid, err, cleaned = validate_uploaded_csv(df)
    assert is_valid is True
    assert (cleaned["energy_kwh"] >= 0.0).all()
    assert cleaned["energy_kwh"].iloc[10] == 0.0


def test_insufficient_history_rejected():
    """Verify datasets with < 48 hours are rejected."""
    df = pd.DataFrame({"timestamp": pd.date_range("2026-05-01", periods=24, freq="h"), "energy_kwh": [20.0] * 24})
    is_valid, err, cleaned = validate_uploaded_csv(df)
    assert is_valid is False
    assert "minimum of 48" in err.lower()


def test_sample_csv_generation():
    """Verify sample CSV content is valid CSV with expected columns."""
    csv_text = get_sample_csv_content()
    assert "timestamp" in csv_text
    assert "energy_kwh" in csv_text
    df_read = pd.read_csv(pd.io.common.StringIO(csv_text))
    is_valid, err, cleaned = validate_uploaded_csv(df_read)
    assert is_valid is True
    assert len(cleaned) >= 48


def test_data_quality_report():
    """Verify structured data quality report generation."""
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-06-01", periods=60, freq="h"),
            "energy_kwh": np.random.uniform(15, 45, 60),
        }
    )
    is_valid, err, cleaned = validate_uploaded_csv(df)
    report = generate_data_quality_report(df, cleaned, err)
    assert report["is_valid"] is True
    assert "data_summary" in report
    assert "power_vs_energy_note" in report
