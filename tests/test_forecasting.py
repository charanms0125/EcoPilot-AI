"""
Unit tests for the Energy Forecasting Module.
Verifies lag feature creation without data leakage, chronological splitting,
error handling for insufficient data, and baseline comparison.
"""

import pytest
import pandas as pd
import numpy as np

from src.data_generator import generate_energy_dataset
from src.forecasting import (
    create_forecasting_features,
    chronological_train_test_split,
    train_and_evaluate_forecasting,
    predict_next_24_hours,
)


def test_lag_construction_no_future_leakage():
    """
    Verify lag_1, lag_2, and lag_24 at step t are strictly derived from past values
    and have no contemporaneous or look-ahead leakage.
    """
    df = generate_energy_dataset(days=15, random_seed=123)
    featured = create_forecasting_features(df)

    # Check lag_1 matches previous row's energy_kwh exactly
    for i in range(1, 20):
        expected_lag_1 = df["energy_kwh"].iloc[i - 1]
        actual_lag_1 = featured["lag_1"].iloc[i]
        assert actual_lag_1 == expected_lag_1, f"Mismatch at row {i}: {actual_lag_1} != {expected_lag_1}"

    # Check lag_24 matches 24 rows prior
    for i in range(24, 40):
        expected_lag_24 = df["energy_kwh"].iloc[i - 24]
        actual_lag_24 = featured["lag_24"].iloc[i]
        assert actual_lag_24 == expected_lag_24, f"Lag 24 mismatch at row {i}"


def test_chronological_split_strict_ordering():
    """Verify train set strictly precedes test set with zero temporal overlap."""
    df = generate_energy_dataset(days=20, random_seed=42)
    featured = create_forecasting_features(df)
    train_df, test_df = chronological_train_test_split(featured, test_hours=48)

    max_train_ts = train_df["timestamp"].max()
    min_test_ts = test_df["timestamp"].min()

    assert max_train_ts < min_test_ts, "Temporal leakage: Train timestamps overlap with test set!"
    assert len(test_df) == 48


def test_insufficient_data_error_handling():
    """Verify ValueError is raised when dataset is too small for time-series lags."""
    tiny_df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-01", periods=20, freq="h"),
            "energy_kwh": np.random.uniform(10, 50, 20),
        }
    )

    with pytest.raises(ValueError, match="At least 240 hourly readings"):
        train_and_evaluate_forecasting(tiny_df)


def test_forecasting_evaluation_and_future_prediction():
    """Verify model training, test metrics, and 24-hour future generation."""
    df = generate_energy_dataset(days=25, random_seed=99)
    result = train_and_evaluate_forecasting(df, test_hours=48)

    metrics = result["metrics"]
    assert "rf_mae" in metrics
    assert "baseline_mae" in metrics
    assert metrics["rf_mae"] > 0
    assert metrics["rf_rmse"] > 0
    assert metrics["test_size"] == 48

    # Generate 24 hours of predictions
    future = predict_next_24_hours(result["model"], df, test_rmse=metrics["rf_rmse"])
    assert len(future) == 24
    assert (future["forecast_kwh"] > 0).all()
    assert (future["upper_bound_kwh"] >= future["lower_bound_kwh"]).all()
    assert future["timestamp"].iloc[0] == df["timestamp"].iloc[-1] + pd.Timedelta(hours=1)
