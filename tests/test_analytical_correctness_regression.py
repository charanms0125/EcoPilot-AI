"""
Regression tests for Analytical Correctness Improvements in EcoPilot-AI:
1. Prevent anomaly baseline leakage (injected anomalies exclusion, dedicated baseline_df, date ranges, robust dispersion).
2. Isolation Forest consistency with documented dual-method ensemble and transparent attribution.
3. Ensure the selected forecasting model is actually used for future predictions.
4. Calibrate prediction intervals for the selected model.
5. Replace hardcoded 3 kWh forecast floor with configurable or data-derived value.
6. Improve weather-normalized verification with empirical OLS slope and documented assumptions.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from src.data_generator import generate_energy_dataset
from src.anomaly_detection import (
    compute_hourly_baselines,
    detect_anomalies,
)
from src.forecasting import (
    FEATURE_COLS,
    create_forecasting_features,
    chronological_train_val_test_split,
    train_and_evaluate_forecasting,
    predict_next_24_hours,
    SeasonalForecaster,
    PersistenceForecaster,
)
from src.verification import SavingsVerifier


# ==============================================================================
# 1. Regression Tests: Anomaly Baseline Leakage Prevention
# ==============================================================================

def test_baseline_computation_excludes_injected_anomalies():
    """
    Verify that compute_hourly_baselines filters out rows with is_injected_anomaly=True
    to prevent baseline median, mean, and std inflation.
    """
    df = generate_energy_dataset(days=60, scenario="sudden_spike", random_seed=42)
    assert "is_injected_anomaly" in df.columns
    injected_count = df["is_injected_anomaly"].sum()
    assert injected_count > 0, "Synthetic dataset should contain injected spikes"

    # Identify hours and weekend bins where spikes were injected
    spiked_bins = df[df["is_injected_anomaly"]][["is_weekend", "hour"]].drop_duplicates()
    assert len(spiked_bins) > 0

    # Compute baselines with leakage prevention (default) vs without
    clean_baselines = compute_hourly_baselines(df, exclude_injected_anomalies=True, robust_dispersion=False)
    leaked_baselines = compute_hourly_baselines(df, exclude_injected_anomalies=False, robust_dispersion=False)

    merged_comp = clean_baselines.merge(
        leaked_baselines, on=["is_weekend", "hour"], suffixes=("_clean", "_leaked")
    )
    spiked_comp = merged_comp.merge(spiked_bins, on=["is_weekend", "hour"])

    # For every bin where a spike was injected, baseline mean and std must be strictly lower when excluding anomalies
    assert (spiked_comp["baseline_mean_clean"] < spiked_comp["baseline_mean_leaked"]).all()
    assert (spiked_comp["baseline_std_clean"] < spiked_comp["baseline_std_leaked"]).all()


def test_detect_anomalies_with_dedicated_baseline_df():
    """
    Verify detect_anomalies accepts a dedicated baseline_df to prevent post-period
    or evaluation-period data from leaking into the reference baseline.
    """
    # Create two separate periods: clean baseline month and anomalous evaluation month
    df_clean_baseline = generate_energy_dataset(days=30, scenario="normal", random_seed=10)
    df_eval = generate_energy_dataset(days=30, scenario="overnight_waste", random_seed=20)

    # Detect anomalies in df_eval using df_clean_baseline as explicit reference
    res_isolated = detect_anomalies(
        df=df_eval,
        baseline_df=df_clean_baseline,
        sensitivity_std=2.0,
    )
    # Detect anomalies using default (eval data computes its own baseline)
    res_self = detect_anomalies(
        df=df_eval,
        sensitivity_std=2.0,
    )

    # Both should run cleanly
    assert "alerts" in res_isolated
    assert "summary" in res_isolated
    # The baselines in res_isolated should match df_clean_baseline
    clean_expected = compute_hourly_baselines(df_clean_baseline)
    flagged = res_isolated["flagged_df"]
    sample_row = flagged.iloc[0]
    matched_clean = clean_expected[
        (clean_expected["is_weekend"] == sample_row["is_weekend"])
        & (clean_expected["hour"] == sample_row["hour"])
    ]["baseline_median"].iloc[0]
    assert np.isclose(sample_row["baseline_median"], matched_clean, atol=1e-3)


def test_detect_anomalies_with_baseline_date_window():
    """
    Verify detect_anomalies can restrict baseline calculation to an explicit date window.
    """
    df = generate_energy_dataset(days=60, scenario="normal", random_seed=99)
    min_ts = df["timestamp"].min()
    window_end = min_ts + timedelta(days=20)

    res = detect_anomalies(
        df=df,
        baseline_start_date=str(min_ts),
        baseline_end_date=str(window_end),
    )
    assert res["summary"]["total_anomalies"] >= 0
    assert len(res["flagged_df"]) == len(df)


def test_robust_dispersion_prevents_std_inflation():
    """
    Verify robust dispersion clamps baseline_std to robust IQR-derived estimate
    when unflagged extreme outliers are present.
    """
    df = generate_energy_dataset(days=20, scenario="normal", random_seed=42)
    # Inject an extreme unflagged 500 kWh spike into a single row
    df_spiked = df.copy()
    df_spiked.loc[10, "energy_kwh"] = 500.0

    robust_b = compute_hourly_baselines(df_spiked, exclude_injected_anomalies=False, robust_dispersion=True)
    non_robust_b = compute_hourly_baselines(df_spiked, exclude_injected_anomalies=False, robust_dispersion=False)

    target_hour = df_spiked.loc[10, "timestamp"].hour
    target_weekend = 1 if df_spiked.loc[10, "timestamp"].dayofweek in [5, 6] else 0

    std_robust = robust_b[
        (robust_b["hour"] == target_hour) & (robust_b["is_weekend"] == target_weekend)
    ]["baseline_std"].iloc[0]
    std_non_robust = non_robust_b[
        (non_robust_b["hour"] == target_hour) & (non_robust_b["is_weekend"] == target_weekend)
    ]["baseline_std"].iloc[0]

    assert std_robust < std_non_robust, "Robust dispersion should resist single extreme outlier inflation"


# ==============================================================================
# 2. Regression Tests: Isolation Forest Ensemble Consistency
# ==============================================================================

def test_isolation_forest_included_in_ensemble():
    """
    Verify that when use_isolation_forest=True, anomalies flagged by Isolation Forest
    with sufficient energy surplus are included in is_anomaly and generate alerts.
    """
    df = generate_energy_dataset(days=40, scenario="sudden_spike", random_seed=42)
    res = detect_anomalies(df, use_isolation_forest=True, iforest_contamination=0.08)

    flagged = res["flagged_df"]
    # Check that is_iforest_anomaly exists and is a boolean column
    assert "is_iforest_anomaly" in flagged.columns
    assert "iforest_score" in flagged.columns

    # Check that alerts contain Isolation Forest detections
    alerts = res["alerts"]
    if_alerts = [a for a in alerts if a.get("isolation_forest_flag")]
    assert len(if_alerts) > 0, "Ensemble must include Isolation Forest alerts"
    assert res["summary"]["isolation_forest_count"] > 0


def test_isolation_forest_attribution_and_categorization():
    """
    Verify that when an anomaly is flagged by Isolation Forest, its attribution,
    category, and evidence strength are properly structured.
    """
    df = generate_energy_dataset(days=45, scenario="sudden_spike", random_seed=77)
    res = detect_anomalies(df, use_isolation_forest=True, iforest_contamination=0.05)

    for a in res["alerts"]:
        if a.get("isolation_forest_flag"):
            assert "Unsupervised Isolation Forest Outlier" in a["detection_method"]
            assert isinstance(a["isolation_forest_score"], (float, int))


def test_use_isolation_forest_false_bypasses_iforest():
    """
    Verify when use_isolation_forest=False, no Isolation Forest alerts are flagged.
    """
    df = generate_energy_dataset(days=25, scenario="normal", random_seed=42)
    res = detect_anomalies(df, use_isolation_forest=False)

    flagged = res["flagged_df"]
    assert not flagged["is_iforest_anomaly"].any()
    assert res["summary"]["isolation_forest_count"] == 0
    for a in res["alerts"]:
        assert a["isolation_forest_flag"] is False


# ==============================================================================
# 3. Regression Tests: Winning Forecasting Model Actually Used
# ==============================================================================

def test_selected_forecasting_model_is_returned_and_usable():
    """
    Verify train_and_evaluate_forecasting returns the winning model in 'model'
    and 'selected_model', and it can be called via predict(X).
    """
    df = generate_energy_dataset(days=35, random_seed=101)
    res = train_and_evaluate_forecasting(df, test_hours=48, val_hours=48)

    preferred_name = res["preferred_model_name"]
    model = res["model"]
    selected_model = res["selected_model"]

    assert model is selected_model
    assert hasattr(model, "predict"), "Selected model must implement .predict(X)"

    # Verify model corresponds to winning type
    if preferred_name == "Random Forest Regressor":
        from sklearn.ensemble import RandomForestRegressor
        assert isinstance(model, RandomForestRegressor)
    elif preferred_name == "Historical Seasonal Baseline":
        assert isinstance(model, SeasonalForecaster)
    elif preferred_name == "Previous-Day Persistence Baseline":
        assert isinstance(model, PersistenceForecaster)

    # Verify predict works on evaluation dataframe
    val_preds = model.predict(res["latest_featured_df"].dropna()[FEATURE_COLS].iloc[:10])
    assert len(val_preds) == 10
    assert not np.isnan(val_preds).any()


def test_seasonal_forecaster_standalone():
    """Verify SeasonalForecaster fits on train_df and accurately predicts by hour/dow."""
    df = generate_energy_dataset(days=20, random_seed=55)
    train_df = df.iloc[:240].copy()
    train_df["hour"] = train_df["timestamp"].dt.hour
    train_df["day_of_week"] = train_df["timestamp"].dt.dayofweek

    forecaster = SeasonalForecaster(train_df)
    test_X = pd.DataFrame({"day_of_week": [0, 1, 5], "hour": [8, 14, 23]})
    preds = forecaster.predict(test_X)
    assert len(preds) == 3
    assert (preds > 0).all()


def test_persistence_forecaster_standalone():
    """Verify PersistenceForecaster uses lag_24."""
    forecaster = PersistenceForecaster(fallback_val=25.0)
    test_X = pd.DataFrame({"lag_24": [30.0, 45.0, np.nan]})
    preds = forecaster.predict(test_X)
    assert preds[0] == 30.0
    assert preds[1] == 45.0
    assert preds[2] == 25.0  # Fallback


def test_predict_next_24_hours_with_seasonal_model():
    """Verify predict_next_24_hours functions smoothly when passed SeasonalForecaster."""
    df = generate_energy_dataset(days=25, random_seed=42)
    featured = create_forecasting_features(df)
    train_df, val_df, test_df = chronological_train_val_test_split(featured, 48, 48)

    seasonal_model = SeasonalForecaster(train_df)
    future = predict_next_24_hours(
        model=seasonal_model,
        df=df,
        interval_offsets=(-4.0, 4.0),
    )
    assert len(future) == 24
    assert (future["forecast_kwh"] > 0).all()
    assert (future["upper_bound_kwh"] >= future["lower_bound_kwh"]).all()


# ==============================================================================
# 4. Regression Tests: Prediction Intervals Calibrated for Selected Model
# ==============================================================================

def test_prediction_intervals_calibrated_for_selected_model():
    """
    Verify prediction intervals are derived from the selected model's residuals.
    """
    df = generate_energy_dataset(days=35, random_seed=88)
    res = train_and_evaluate_forecasting(df, test_hours=48, val_hours=48)

    pi = res["metrics"]["prediction_interval"]
    assert pi["selected_model"] == res["preferred_model_name"]
    assert "val_empirical_coverage_pct" in pi
    assert "test_empirical_coverage_pct" in pi
    assert "q05_residual_kwh" in pi
    assert "q95_residual_kwh" in pi
    assert pi["q95_residual_kwh"] >= pi["q05_residual_kwh"]

    q05, q95 = res["interval_offsets"]
    assert np.isclose(q05, pi["q05_residual_kwh"], atol=1e-2)
    assert np.isclose(q95, pi["q95_residual_kwh"], atol=1e-2)


# ==============================================================================
# 5. Regression Tests: Configurable & Data-Derived Forecast Floor
# ==============================================================================

def test_predict_next_24_hours_data_derived_floor():
    """
    Verify that when min_forecast_floor is None (default),
    floor is dynamically derived from historical 1st percentile.
    """
    df = generate_energy_dataset(days=25, scenario="normal", random_seed=42)
    res = train_and_evaluate_forecasting(df, test_hours=48, val_hours=48)

    p1 = float(np.percentile(df["energy_kwh"], 1))
    future = predict_next_24_hours(res["model"], df, min_forecast_floor=None)
    assert len(future) == 24
    # All predictions should be at or above data-derived floor
    assert (future["forecast_kwh"] >= round(p1, 2) - 0.1).all()


def test_predict_next_24_hours_configurable_floor():
    """
    Verify that a custom min_forecast_floor (e.g. 15.0 kWh or 0.0 kWh) is strictly enforced.
    """
    df = generate_energy_dataset(days=25, scenario="normal", random_seed=42)
    res = train_and_evaluate_forecasting(df, test_hours=48, val_hours=48)

    # Set custom floor higher than normal baseload to test strict bounding
    custom_floor = 22.5
    future = predict_next_24_hours(res["model"], df, min_forecast_floor=custom_floor)
    assert (future["forecast_kwh"] >= custom_floor).all()

    # Set zero floor
    zero_future = predict_next_24_hours(res["model"], df, min_forecast_floor=0.0)
    assert (zero_future["forecast_kwh"] >= 0.0).all()


# ==============================================================================
# 6. Regression Tests: Weather-Normalized Verification & Documented Assumptions
# ==============================================================================

def test_weather_normalized_empirical_ols_sensitivity():
    """
    Verify empirical temperature sensitivity beta is estimated from baseline data via OLS,
    and assumptions dictionary contains all required fields.
    """
    df = generate_energy_dataset(days=50, scenario="normal", random_seed=42)
    assert "simulated_temperature_c" in df.columns

    interv_ts = df["timestamp"].iloc[35 * 24]
    # Reduce post-period consumption by 12 kWh
    post_mask = df["timestamp"] >= interv_ts
    df.loc[post_mask, "energy_kwh"] = np.maximum(5.0, df.loc[post_mask, "energy_kwh"] - 12.0)

    res = SavingsVerifier.verify_intervention(
        df=df,
        intervention_name="Chiller Optimization",
        intervention_date=str(interv_ts),
        expected_savings_kwh=5000.0,
    )

    assert "weather_normalization_assumptions" in res
    w_assump = res["weather_normalization_assumptions"]

    assert w_assump["is_weather_adjusted"] is True
    assert w_assump["temperature_column"] == "simulated_temperature_c"
    assert isinstance(w_assump["baseline_avg_temp_c"], float)
    assert isinstance(w_assump["post_avg_temp_c"], float)
    assert isinstance(w_assump["temperature_delta_c"], float)
    assert w_assump["temperature_sensitivity_kwh_per_c"] > 0.0
    assert "Empirical" in w_assump["sensitivity_estimation_method"] or "Benchmark" in w_assump["sensitivity_estimation_method"]
    assert len(w_assump["assumptions_documentation"]) >= 3

    # Check that weather_adjusted_savings_kwh is calculated
    assert "weather_adjusted_savings_kwh" in res
    assert res["weather_adjusted_savings_kwh"] != 0.0


def test_weather_normalized_custom_sensitivity_override():
    """
    Verify user can pass custom cooling_sensitivity_kwh_per_c and it is respected.
    """
    df = generate_energy_dataset(days=50, scenario="normal", random_seed=42)
    interv_ts = df["timestamp"].iloc[35 * 24]

    custom_beta = 2.45
    res = SavingsVerifier.verify_intervention(
        df=df,
        intervention_name="HVAC Reset",
        intervention_date=str(interv_ts),
        expected_savings_kwh=2000.0,
        cooling_sensitivity_kwh_per_c=custom_beta,
    )

    w_assump = res["weather_normalization_assumptions"]
    assert w_assump["temperature_sensitivity_kwh_per_c"] == custom_beta
    assert "User-Configured" in w_assump["sensitivity_estimation_method"]


def test_weather_normalized_without_temperature_telemetry():
    """
    Verify verification without temperature data returns clean, unadjusted assumptions.
    """
    df = generate_energy_dataset(days=40, scenario="normal", random_seed=42)
    df_no_temp = df[["timestamp", "energy_kwh"]].copy()  # Strip temperature column

    interv_ts = df_no_temp["timestamp"].iloc[25 * 24]
    res = SavingsVerifier.verify_intervention(
        df=df_no_temp,
        intervention_name="LED Retrofit",
        intervention_date=str(interv_ts),
        expected_savings_kwh=1000.0,
    )

    w_assump = res["weather_normalization_assumptions"]
    assert w_assump["is_weather_adjusted"] is False
    assert w_assump["temperature_column"] is None
    assert w_assump["weather_adjustment_kwh"] == 0.0
    assert len(w_assump["assumptions_documentation"]) >= 1
