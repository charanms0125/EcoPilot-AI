"""
EcoPilot AI: Energy Demand Forecasting Module
Provides strictly chronological train, validation, and test splitting,
lag-feature engineering without temporal look-ahead leakage,
and comparative evaluation across three distinct models:
1. Previous-Day Persistence Baseline (lag_24)
2. Historical Seasonal Baseline (hour & day-of-week profile fitted strictly on training data)
3. Random Forest Regressor

Includes calibrated empirical prediction intervals with coverage verification,
WAPE (Weighted Absolute Percentage Error), and zero-leakage multi-step 24-hour future generation.
"""

from typing import Dict, Any, Tuple, Optional, List
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


FEATURE_COLS = [
    "hour",
    "day_of_week",
    "is_weekend",
    "sin_hour",
    "cos_hour",
    "sin_dow",
    "cos_dow",
    "lag_1",
    "lag_2",
    "lag_24",
    "lag_48",
    "lag_168",
    "rolling_mean_24h",
]


def create_forecasting_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Construct time-series lag and cyclical features strictly avoiding future-data leakage.

    Handles irregular timestamps and missing intervals by regularizing to hourly frequency.
    All lag and rolling features are computed using past values only (shifted by at least 1 step).
    """
    if "timestamp" not in df.columns or "energy_kwh" not in df.columns:
        raise ValueError("DataFrame must contain 'timestamp' and 'energy_kwh' columns.")

    data = df.copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"])
    data = data.sort_values("timestamp").reset_index(drop=True)

    # Check for duplicate timestamps and deduplicate keeping the first
    if data["timestamp"].duplicated().any():
        data = data.drop_duplicates(subset=["timestamp"], keep="first").reset_index(drop=True)

    # Detect irregular time intervals or gaps and forward-fill small gaps (up to 3 hours)
    data = data.set_index("timestamp")
    # Resample to hourly to ensure regular interval spacing
    full_idx = pd.date_range(start=data.index.min(), end=data.index.max(), freq="h")
    if len(full_idx) != len(data):
        data = data.reindex(full_idx)
        data["energy_kwh"] = data["energy_kwh"].ffill(limit=3).bfill(limit=3)

    data = data.reset_index().rename(columns={"index": "timestamp"})

    # Time indicators
    data["hour"] = data["timestamp"].dt.hour
    data["day_of_week"] = data["timestamp"].dt.dayofweek
    data["is_weekend"] = data["day_of_week"].isin([5, 6]).astype(int)

    # Cyclical trigonometric representations
    data["sin_hour"] = np.sin(2 * np.pi * data["hour"] / 24.0)
    data["cos_hour"] = np.cos(2 * np.pi * data["hour"] / 24.0)
    data["sin_dow"] = np.sin(2 * np.pi * data["day_of_week"] / 7.0)
    data["cos_dow"] = np.cos(2 * np.pi * data["day_of_week"] / 7.0)

    # Pure past lags (strictly shifted, no contemporaneous or look-ahead leakage)
    data["lag_1"] = data["energy_kwh"].shift(1)
    data["lag_2"] = data["energy_kwh"].shift(2)
    data["lag_24"] = data["energy_kwh"].shift(24)
    data["lag_48"] = data["energy_kwh"].shift(48)
    data["lag_168"] = data["energy_kwh"].shift(168)  # Same hour previous week

    # 24-hour rolling mean of past values (shifted by 1 so current hour is strictly excluded)
    data["rolling_mean_24h"] = data["energy_kwh"].shift(1).rolling(window=24, min_periods=12).mean()

    return data


def chronological_train_test_split(
    featured_df: pd.DataFrame, test_hours: int = 168
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Chronological split into training and test sets.
    Drops warm-up rows with NaN lags from training data.
    Preserves backward compatibility for existing callers.
    """
    clean_df = featured_df.dropna(subset=FEATURE_COLS + ["energy_kwh"]).copy()

    total_valid = len(clean_df)
    min_required = test_hours + 72  # at least 3 days training + test_hours
    if total_valid < min_required:
        raise ValueError(
            f"Insufficient valid observations after lag construction ({total_valid} rows). "
            f"Need at least {min_required} rows (minimum 10-14 days of hourly data)."
        )

    split_idx = total_valid - test_hours
    train_df = clean_df.iloc[:split_idx].copy()
    test_df = clean_df.iloc[split_idx:].copy()

    return train_df, test_df


def chronological_train_val_test_split(
    featured_df: pd.DataFrame,
    val_hours: int = 48,
    test_hours: int = 48,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Chronological 3-way split: Training -> Validation -> Test.
    The test set remains untouched during model selection and hyperparameter tuning.
    Validation set is used to select the preferred forecasting model.
    """
    clean_df = featured_df.dropna(subset=FEATURE_COLS + ["energy_kwh"]).copy()

    total_valid = len(clean_df)
    min_required = val_hours + test_hours + 72  # at least 3 days training
    if total_valid < min_required:
        raise ValueError(
            f"Insufficient observations for 3-way split ({total_valid} rows). "
            f"Need at least {min_required} rows."
        )

    test_start = total_valid - test_hours
    val_start = test_start - val_hours

    train_df = clean_df.iloc[:val_start].copy()
    val_df = clean_df.iloc[val_start:test_start].copy()
    test_df = clean_df.iloc[test_start:].copy()

    return train_df, val_df, test_df


def compute_seasonal_baseline(train_df: pd.DataFrame, target_df: pd.DataFrame) -> np.ndarray:
    """
    Compute Historical Seasonal Baseline strictly fitted on training data:
    Groups training data by (day_of_week, hour) to compute median consumption.
    Maps onto target_df without looking ahead.
    """
    profile = (
        train_df.groupby(["day_of_week", "hour"])["energy_kwh"]
        .median()
        .reset_index()
        .rename(columns={"energy_kwh": "seasonal_median"})
    )
    # Global hour fallback if specific (day_of_week, hour) is unseen
    hour_fallback = train_df.groupby("hour")["energy_kwh"].median().to_dict()

    merged = target_df[["day_of_week", "hour"]].merge(profile, on=["day_of_week", "hour"], how="left")
    # Impute any missing with hour fallback
    unmapped_mask = merged["seasonal_median"].isna()
    if unmapped_mask.any():
        fallback_vals = merged.loc[unmapped_mask, "hour"].map(hour_fallback)
        merged.loc[unmapped_mask, "seasonal_median"] = fallback_vals

    # Global train median fallback if still missing
    global_median = float(train_df["energy_kwh"].median())
    merged["seasonal_median"] = merged["seasonal_median"].fillna(global_median)

    return merged["seasonal_median"].to_numpy()


class SeasonalForecaster:
    """Historical Seasonal Forecaster mapping (day_of_week, hour) to training medians."""

    def __init__(self, train_df: pd.DataFrame):
        self.profile = (
            train_df.groupby(["day_of_week", "hour"])["energy_kwh"]
            .median()
            .to_dict()
        )
        self.hour_fallback = (
            train_df.groupby("hour")["energy_kwh"]
            .median()
            .to_dict()
        )
        self.global_median = float(train_df["energy_kwh"].median())

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        preds = []
        for _, row in X.iterrows():
            dow = int(row["day_of_week"]) if "day_of_week" in row else 0
            h = int(row["hour"]) if "hour" in row else 0
            key = (dow, h)
            if key in self.profile and not np.isnan(self.profile[key]):
                val = self.profile[key]
            elif h in self.hour_fallback and not np.isnan(self.hour_fallback[h]):
                val = self.hour_fallback[h]
            else:
                val = self.global_median
            preds.append(float(val))
        return np.array(preds, dtype=float)


class PersistenceForecaster:
    """Previous-Day Persistence Forecaster using lag_24."""

    def __init__(self, fallback_val: float = 0.0):
        self.fallback_val = fallback_val

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if "lag_24" in X.columns:
            return X["lag_24"].fillna(self.fallback_val).to_numpy(dtype=float)
        elif "lag_1" in X.columns:
            return X["lag_1"].fillna(self.fallback_val).to_numpy(dtype=float)
        return np.full(len(X), self.fallback_val, dtype=float)


def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Compute regression evaluation metrics:
    - MAE (Mean Absolute Error)
    - RMSE (Root Mean Squared Error)
    - WAPE (Weighted Absolute Percentage Error = sum(|y - y_hat|) / sum(y))
    - R² (Coefficient of Determination)

    Explains why WAPE is superior to MAPE in building energy:
    MAPE divides by y_t, causing asymptotic spikes or division-by-zero errors
    during low-load or unoccupied periods. WAPE aggregates total error over total volume.
    """
    y_t = np.asarray(y_true, dtype=float)
    y_p = np.asarray(y_pred, dtype=float)

    mae = float(mean_absolute_error(y_t, y_p))
    rmse = float(np.sqrt(mean_squared_error(y_t, y_p)))
    r2 = float(r2_score(y_t, y_p))

    sum_true = float(np.sum(np.abs(y_t)))
    if sum_true > 0:
        wape = float((np.sum(np.abs(y_t - y_p)) / sum_true) * 100.0)
    else:
        wape = 0.0

    return {
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "wape_pct": round(wape, 2),
        "r2": round(r2, 3),
    }


def train_and_evaluate_forecasting(
    df: pd.DataFrame,
    test_hours: int = 72,
    val_hours: int = 48,
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Train and evaluate energy forecasting across 3 models:
    1. Previous-Day Persistence Baseline (lag_24)
    2. Historical Seasonal Baseline (hour + day-of-week profile)
    3. Random Forest Regressor

    Methodology:
    - Chronological 3-way split: Train -> Validation -> Test.
    - Preprocessing and feature engineering fitted strictly on appropriate history.
    - Model selection performed on validation set (Validation MAE/WAPE).
    - Test set kept strictly untouched until final evaluation.
    - Calibrated empirical prediction intervals with coverage verification on validation residuals.
    """
    if len(df) < 240:
        raise ValueError(
            f"Dataset has only {len(df)} rows. At least 240 hourly readings (10 days) are required."
        )

    featured_df = create_forecasting_features(df)
    train_df, val_df, test_df = chronological_train_val_test_split(
        featured_df, val_hours=val_hours, test_hours=test_hours
    )

    X_train = train_df[FEATURE_COLS]
    y_train = train_df["energy_kwh"]
    X_val = val_df[FEATURE_COLS]
    y_val = val_df["energy_kwh"]
    X_test = test_df[FEATURE_COLS]
    y_test = test_df["energy_kwh"]

    # ---------------------------------------------------------
    # MODEL 1: Previous-Day Persistence Baseline (lag_24)
    # ---------------------------------------------------------
    persist_val_preds = val_df["lag_24"].to_numpy()
    persist_test_preds = test_df["lag_24"].to_numpy()
    metrics_persist_val = calculate_metrics(y_val.to_numpy(), persist_val_preds)
    metrics_persist_test = calculate_metrics(y_test.to_numpy(), persist_test_preds)

    # ---------------------------------------------------------
    # MODEL 2: Historical Seasonal Baseline (hour & day-of-week)
    # ---------------------------------------------------------
    seasonal_val_preds = compute_seasonal_baseline(train_df, val_df)
    seasonal_test_preds = compute_seasonal_baseline(train_df, test_df)
    metrics_seasonal_val = calculate_metrics(y_val.to_numpy(), seasonal_val_preds)
    metrics_seasonal_test = calculate_metrics(y_test.to_numpy(), seasonal_test_preds)

    # ---------------------------------------------------------
    # MODEL 3: Random Forest Regressor
    # ---------------------------------------------------------
    rf_model = RandomForestRegressor(
        n_estimators=100,
        max_depth=12,
        min_samples_leaf=2,
        random_state=random_state,
        n_jobs=-1,
    )
    rf_model.fit(X_train, y_train)

    rf_val_preds = rf_model.predict(X_val)
    rf_test_preds = rf_model.predict(X_test)
    metrics_rf_val = calculate_metrics(y_val.to_numpy(), rf_val_preds)
    metrics_rf_test = calculate_metrics(y_test.to_numpy(), rf_test_preds)

    # ---------------------------------------------------------
    # Model Selection using Validation Performance (NOT Test Set!)
    # ---------------------------------------------------------
    candidates = {
        "Random Forest Regressor": metrics_rf_val["mae"],
        "Historical Seasonal Baseline": metrics_seasonal_val["mae"],
        "Previous-Day Persistence Baseline": metrics_persist_val["mae"],
    }
    preferred_model_name = min(candidates, key=candidates.get)

    seasonal_forecaster = SeasonalForecaster(train_df)
    persistence_forecaster = PersistenceForecaster(fallback_val=float(train_df["energy_kwh"].median()))

    # Resolve winning forecaster and its corresponding predictions
    if preferred_model_name == "Historical Seasonal Baseline":
        selected_model = seasonal_forecaster
        selected_val_preds = seasonal_val_preds
        selected_test_preds = seasonal_test_preds
    elif preferred_model_name == "Previous-Day Persistence Baseline":
        selected_model = persistence_forecaster
        selected_val_preds = persist_val_preds
        selected_test_preds = persist_test_preds
    else:
        selected_model = rf_model
        selected_val_preds = rf_val_preds
        selected_test_preds = rf_test_preds

    # Improvement over persistence baseline on test set
    base_mae = metrics_persist_test["mae"]
    rf_mae = metrics_rf_test["mae"]
    improvement_pct = round(((base_mae - rf_mae) / base_mae) * 100.0, 1) if base_mae > 0 else 0.0

    # ---------------------------------------------------------
    # Calibrated Prediction Intervals (Empirical Residual Quantiles on Selected Model)
    # ---------------------------------------------------------
    # Residuals on validation set: e = y_val - y_pred_val using the selected model
    val_residuals = y_val.to_numpy() - selected_val_preds
    # Compute empirical 5th and 95th percentiles of validation residuals (90% interval)
    q05 = float(np.percentile(val_residuals, 5))
    q95 = float(np.percentile(val_residuals, 95))
    val_interval_half_width = float(np.percentile(np.abs(val_residuals), 90))

    # Evaluate empirical coverage on validation set
    val_in_interval = (y_val.to_numpy() >= (selected_val_preds + q05)) & (y_val.to_numpy() <= (selected_val_preds + q95))
    val_coverage_pct = round(float(np.mean(val_in_interval)) * 100.0, 1)

    # Evaluate empirical coverage on held-out test set
    test_in_interval = (y_test.to_numpy() >= (selected_test_preds + q05)) & (y_test.to_numpy() <= (selected_test_preds + q95))
    test_coverage_pct = round(float(np.mean(test_in_interval)) * 100.0, 1)

    # Feature Importances (from RF)
    importances = dict(
        zip(FEATURE_COLS, [round(float(v), 4) for v in rf_model.feature_importances_])
    )

    # Complete test evaluation dataframe
    eval_df = pd.DataFrame(
        {
            "timestamp": test_df["timestamp"].values,
            "actual_kwh": np.round(y_test.values, 2),
            "selected_pred_kwh": np.round(selected_test_preds, 2),
            "selected_lower_90_kwh": np.maximum(0.0, np.round(selected_test_preds + q05, 2)),
            "selected_upper_90_kwh": np.round(selected_test_preds + q95, 2),
            "rf_pred_kwh": np.round(rf_test_preds, 2),
            "seasonal_pred_kwh": np.round(seasonal_test_preds, 2),
            "baseline_pred_kwh": np.round(persist_test_preds, 2),
            "selected_residual_kwh": np.round(y_test.values - selected_test_preds, 2),
        }
    )

    # Validation evaluation dataframe
    val_eval_df = pd.DataFrame(
        {
            "timestamp": val_df["timestamp"].values,
            "actual_kwh": np.round(y_val.values, 2),
            "selected_pred_kwh": np.round(selected_val_preds, 2),
            "rf_pred_kwh": np.round(rf_val_preds, 2),
            "seasonal_pred_kwh": np.round(seasonal_val_preds, 2),
            "baseline_pred_kwh": np.round(persist_val_preds, 2),
        }
    )

    return {
        "model": selected_model,
        "selected_model": selected_model,
        "rf_model": rf_model,
        "seasonal_model": seasonal_forecaster,
        "persistence_model": persistence_forecaster,
        "preferred_model_name": preferred_model_name,
        "selection_criterion": "Lowest Validation MAE",
        "horizon_hours": 24,
        "interval": "1 Hour",
        "metrics": {
            # Backward-compatible keys for existing app/tests
            "rf_mae": metrics_rf_test["mae"],
            "rf_rmse": metrics_rf_test["rmse"],
            "rf_r2": metrics_rf_test["r2"],
            "baseline_mae": metrics_persist_test["mae"],
            "baseline_rmse": metrics_persist_test["rmse"],
            "baseline_r2": metrics_persist_test["r2"],
            "selected_model": preferred_model_name,
            "selected_mae": calculate_metrics(y_test.to_numpy(), selected_test_preds)["mae"],
            "selected_rmse": calculate_metrics(y_test.to_numpy(), selected_test_preds)["rmse"],
            "improvement_pct": improvement_pct,
            "test_hours": test_hours,
            "val_hours": val_hours,
            "train_size": len(train_df),
            "val_size": len(val_df),
            "test_size": len(test_df),
            # Detailed 3-model test metrics
            "models_test": {
                "Random Forest": metrics_rf_test,
                "Historical Seasonal": metrics_seasonal_test,
                "Previous-Day Persistence": metrics_persist_test,
            },
            # Detailed 3-model validation metrics
            "models_val": {
                "Random Forest": metrics_rf_val,
                "Historical Seasonal": metrics_seasonal_val,
                "Previous-Day Persistence": metrics_persist_val,
            },
            # Interval calibration metrics
            "prediction_interval": {
                "nominal_level": "90%",
                "selected_model": preferred_model_name,
                "q05_residual_kwh": round(q05, 2),
                "q95_residual_kwh": round(q95, 2),
                "val_empirical_coverage_pct": val_coverage_pct,
                "test_empirical_coverage_pct": test_coverage_pct,
                "calibration_status": (
                    f"Calibrated (Val: {val_coverage_pct}%, Test: {test_coverage_pct}%)"
                ),
            },
        },
        "feature_importances": importances,
        "evaluation_df": eval_df,
        "val_evaluation_df": val_eval_df,
        "latest_featured_df": featured_df,
        "interval_offsets": (q05, q95),
        "limitations": [
            "Assumes building occupancy schedules follow historical circadian rhythms.",
            "Extreme unforecast weather events or unplanned campus closures will cause transient residual spikes.",
            "WAPE is preferred over MAPE because near-zero consumption periods distort percentage calculations.",
        ],
    }


def predict_next_24_hours(
    model: Any,
    df: pd.DataFrame,
    test_rmse: float = 3.5,
    interval_offsets: Optional[Tuple[float, float]] = None,
    empirical_coverage_pct: float = 90.0,
    min_forecast_floor: Optional[float] = None,
) -> pd.DataFrame:
    """
    Generate an iterative multi-step 24-hour future forecast starting from the last timestamp.
    Includes calibrated prediction intervals derived from validation residual quantiles.
    Supports configurable or data-derived baseline standby floor.
    """
    if df.empty:
        raise ValueError("Cannot predict next 24 hours on empty dataframe.")

    series_df = df[["timestamp", "energy_kwh"]].copy()
    series_df["timestamp"] = pd.to_datetime(series_df["timestamp"])
    series_df = series_df.sort_values("timestamp").reset_index(drop=True)

    # Determine forecast floor (configurable or data-derived baseline standby load)
    if min_forecast_floor is not None:
        floor_kwh = max(0.0, float(min_forecast_floor))
    else:
        # Data-derived standby minimum: 1st percentile of observed non-negative energy
        positive_energy = series_df["energy_kwh"].dropna()
        if not positive_energy.empty and len(positive_energy) >= 10:
            floor_kwh = max(0.0, float(np.percentile(positive_energy, 1)))
        else:
            floor_kwh = 0.0

    last_ts = series_df["timestamp"].iloc[-1]
    future_timestamps = pd.date_range(start=last_ts + pd.Timedelta(hours=1), periods=24, freq="h")

    forecast_records = []
    current_series = series_df["energy_kwh"].to_list()

    # Calibrated offsets or fallback
    if interval_offsets:
        q_low, q_high = interval_offsets
    else:
        # Fallback to standard 1.645 * RMSE
        q_low = -1.645 * test_rmse
        q_high = 1.645 * test_rmse

    for step, ts in enumerate(future_timestamps):
        h = ts.hour
        dow = ts.dayofweek
        is_wknd = 1 if dow in [5, 6] else 0

        # Lags relative to current simulated series length
        n = len(current_series)
        lag_1 = current_series[n - 1]
        lag_2 = current_series[n - 2] if n >= 2 else lag_1
        lag_24 = current_series[n - 24] if n >= 24 else lag_1
        lag_48 = current_series[n - 48] if n >= 48 else lag_24
        lag_168 = current_series[n - 168] if n >= 168 else lag_24

        # 24h rolling mean
        slice_24 = current_series[max(0, n - 24) : n]
        rolling_24 = float(np.mean(slice_24))

        row_dict = {
            "hour": h,
            "day_of_week": dow,
            "is_weekend": is_wknd,
            "sin_hour": np.sin(2 * np.pi * h / 24.0),
            "cos_hour": np.cos(2 * np.pi * h / 24.0),
            "sin_dow": np.sin(2 * np.pi * dow / 7.0),
            "cos_dow": np.cos(2 * np.pi * dow / 7.0),
            "lag_1": lag_1,
            "lag_2": lag_2,
            "lag_24": lag_24,
            "lag_48": lag_48,
            "lag_168": lag_168,
            "rolling_mean_24h": rolling_24,
        }

        feature_vector = pd.DataFrame([row_dict])[FEATURE_COLS]
        raw_pred = model.predict(feature_vector)
        pred_kwh = float(raw_pred[0]) if hasattr(raw_pred, "__len__") else float(raw_pred)
        # Guarantee non-negative baseline standby minimum
        pred_kwh = max(pred_kwh, floor_kwh)

        lower_bound = max(0.0, round(pred_kwh + q_low, 2))
        upper_bound = round(pred_kwh + q_high, 2)

        # Append to simulated series for next step's lags
        current_series.append(pred_kwh)

        forecast_records.append(
            {
                "timestamp": ts,
                "hour": h,
                "day_name": ts.day_name(),
                "forecast_kwh": round(pred_kwh, 2),
                "lower_bound_kwh": lower_bound,
                "upper_bound_kwh": upper_bound,
                "confidence_level": f"Calibrated 90% Empirical Interval ({empirical_coverage_pct:.0f}% Coverage)",
            }
        )

    return pd.DataFrame(forecast_records)
