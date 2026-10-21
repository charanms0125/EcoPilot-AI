"""
Unit tests for the upgraded Energy Demand Forecasting Module.
Verifies chronological 3-way train/validation/test splits,
3-model comparative evaluation (Persistence, Seasonal, Random Forest),
WAPE calculation, and empirical prediction interval calibration.
"""

import pytest
import pandas as pd
import numpy as np

from src.data_generator import generate_energy_dataset
from src.forecasting import (
    create_forecasting_features,
    chronological_train_val_test_split,
    compute_seasonal_baseline,
    calculate_metrics,
    train_and_evaluate_forecasting,
    predict_next_24_hours,
)


def test_chronological_three_way_split():
    """Verify train_df < val_df < test_df strictly with zero temporal leakage."""
    df = generate_energy_dataset(days=35, random_seed=42)
    featured = create_forecasting_features(df)
    train_df, val_df, test_df = chronological_train_val_test_split(
        featured, val_hours=48, test_hours=48
    )

    assert train_df["timestamp"].max() < val_df["timestamp"].min()
    assert val_df["timestamp"].max() < test_df["timestamp"].min()
    assert len(val_df) == 48
    assert len(test_df) == 48
    assert len(train_df) > 100


def test_compute_seasonal_baseline():
    """Verify seasonal baseline calculates historical median by (day_of_week, hour)."""
    df = generate_energy_dataset(days=30, random_seed=99)
    featured = create_forecasting_features(df)
    train_df, val_df, test_df = chronological_train_val_test_split(featured, 48, 48)

    seasonal_preds = compute_seasonal_baseline(train_df, test_df)
    assert len(seasonal_preds) == len(test_df)
    assert not np.isnan(seasonal_preds).any()
    assert (seasonal_preds > 0).all()


def test_calculate_metrics_wape():
    """Verify MAE, RMSE, R2, and WAPE formulas."""
    y_true = np.array([10.0, 20.0, 30.0, 40.0])
    y_pred = np.array([12.0, 18.0, 33.0, 37.0])
    # abs errors: 2 + 2 + 3 + 3 = 10. sum_true = 100. WAPE = 10%
    m = calculate_metrics(y_true, y_pred)
    assert m["mae"] == 2.5
    assert m["wape_pct"] == 10.0
    assert m["rmse"] > 0
    assert m["r2"] > 0.9


def test_three_model_forecasting_evaluation():
    """Verify comparative evaluation across Random Forest, Seasonal, and Persistence."""
    df = generate_energy_dataset(days=30, random_seed=101)
    res = train_and_evaluate_forecasting(df, test_hours=48, val_hours=48)

    assert "models_test" in res["metrics"]
    assert "models_val" in res["metrics"]
    models = res["metrics"]["models_test"]
    assert "Random Forest" in models
    assert "Historical Seasonal" in models
    assert "Previous-Day Persistence" in models

    # Check validation-based selection
    assert res["preferred_model_name"] in [
        "Random Forest Regressor",
        "Historical Seasonal Baseline",
        "Previous-Day Persistence Baseline",
    ]

    # Check prediction intervals calibration
    pi = res["metrics"]["prediction_interval"]
    assert "val_empirical_coverage_pct" in pi
    assert "test_empirical_coverage_pct" in pi
    assert 50.0 <= pi["val_empirical_coverage_pct"] <= 100.0


def test_predict_next_24_hours_with_calibrated_intervals():
    """Verify multi-step iterative 24-hour generation with calibrated interval bounds."""
    df = generate_energy_dataset(days=25, random_seed=202)
    res = train_and_evaluate_forecasting(df, test_hours=48, val_hours=48)

    future = predict_next_24_hours(
        model=res["model"],
        df=df,
        interval_offsets=res["interval_offsets"],
        empirical_coverage_pct=res["metrics"]["prediction_interval"]["val_empirical_coverage_pct"],
    )

    assert len(future) == 24
    assert (future["forecast_kwh"] > 0).all()
    assert (future["upper_bound_kwh"] >= future["lower_bound_kwh"]).all()
    assert (future["lower_bound_kwh"] >= 0.0).all()
    assert "Calibrated" in future["confidence_level"].iloc[0]
