"""
EcoPilot AI: Synthetic & Simulated Energy Data Generator
Generates reproducible, realistic hourly electricity consumption datasets
with deterministic scenarios for hackathon demonstrations, and provides
robust CSV schema validation, data quality reporting, and audit trail extraction.
"""

from typing import Tuple, Optional, Dict, Any, List
import io
import numpy as np
import pandas as pd


# Building profiles with base parameters
BUILDING_PROFILES: Dict[str, Dict[str, Any]] = {
    "Academic Block A": {
        "base_load": 18.0,
        "peak_multiplier": 3.8,
        "peak_start": 8,
        "peak_end": 18,
        "weekend_factor": 0.35,
        "occupancy_weight": 25.0,
        "temp_weight": 1.2,
    },
    "Student Hostel B": {
        "base_load": 12.0,
        "peak_multiplier": 2.6,
        "peak_start": 17,
        "peak_end": 23,
        "weekend_factor": 0.85,
        "occupancy_weight": 18.0,
        "temp_weight": 0.9,
    },
    "Campus Dining Hall": {
        "base_load": 15.0,
        "peak_multiplier": 3.2,
        "peak_start": 7,
        "peak_end": 21,
        "weekend_factor": 0.70,
        "occupancy_weight": 22.0,
        "temp_weight": 1.5,
    },
    "Research Lab / Business": {
        "base_load": 28.0,
        "peak_multiplier": 2.2,
        "peak_start": 9,
        "peak_end": 19,
        "weekend_factor": 0.55,
        "occupancy_weight": 20.0,
        "temp_weight": 1.8,
    },
}

SCENARIOS = {
    "normal": "Normal Operations (Standard circadian schedule, expected variability)",
    "overnight_waste": "Excessive Overnight Consumption (HVAC/Lighting left on 22:00-06:00)",
    "sudden_spike": "Sudden Unexpected Spikes (Equipment malfunction / surging loads)",
}

MAX_ALLOWED_ROWS = 500000


def generate_energy_dataset(
    days: int = 60,
    building_category: str = "Academic Block A",
    scenario: str = "normal",
    random_seed: int = 42,
    start_date: str = "2026-08-01 00:00:00",
) -> pd.DataFrame:
    """
    Generate a deterministic synthetic hourly electricity dataset.

    Parameters:
    -----------
    days: int, default 60
        Number of days to simulate (minimum 60 recommended).
    building_category: str
        Category of building (determines load shape).
    scenario: str
        One of 'normal', 'overnight_waste', 'sudden_spike'.
    random_seed: int
        Random seed for exact reproducibility.
    start_date: str
        Start timestamp.

    Returns:
    --------
    pd.DataFrame with hourly timestamps, consumption, and simulated features.
    """
    rng = np.random.default_rng(random_seed)
    profile = BUILDING_PROFILES.get(building_category, BUILDING_PROFILES["Academic Block A"])

    total_hours = days * 24
    timestamps = pd.date_range(start=start_date, periods=total_hours, freq="h")

    df = pd.DataFrame({"timestamp": timestamps})
    df["hour"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.dayofweek
    df["day_name"] = df["timestamp"].dt.day_name()
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
    df["building_category"] = building_category
    df["is_synthetic"] = True

    # 1. Simulated Weather (Ambient Temperature in Celsius with circadian rhythm and seasonal drift)
    temp_circadian = np.sin((df["hour"] - 9) * 2 * np.pi / 24) * 5.0
    day_indices = np.arange(total_hours) / 24.0
    temp_seasonal = np.sin(day_indices * 2 * np.pi / 365) * 3.0
    temp_noise = rng.normal(0, 1.2, total_hours)
    df["simulated_temperature_c"] = np.round(27.0 + temp_circadian + temp_seasonal + temp_noise, 1)

    # 2. Simulated Occupancy Ratio (0.0 to 1.0)
    weekday_occ = np.clip(
        np.exp(-0.5 * ((df["hour"] - 13) / 3.5) ** 2) * 0.95 + rng.normal(0, 0.04, total_hours),
        0.05,
        1.0,
    )
    weekend_occ = np.clip(
        weekday_occ * profile["weekend_factor"] + rng.normal(0, 0.03, total_hours),
        0.02,
        0.6,
    )
    df["simulated_occupancy_ratio"] = np.where(df["is_weekend"] == 1, weekend_occ, weekday_occ)
    df["simulated_occupancy_ratio"] = np.round(np.clip(df["simulated_occupancy_ratio"], 0.0, 1.0), 2)

    # 3. Base Hourly Consumption Modeling
    base_load = profile["base_load"]

    # Active operational hours
    p_start, p_end = profile["peak_start"], profile["peak_end"]
    in_peak = (df["hour"] >= p_start) & (df["hour"] <= p_end)
    mid_peak = (p_start + p_end) / 2.0
    spread = (p_end - p_start) / 2.5
    bell_curve = np.exp(-0.5 * ((df["hour"] - mid_peak) / spread) ** 2)
    hour_factor = np.where(in_peak, bell_curve * (profile["peak_multiplier"] - 1.0), 0.1)

    # Weekend reduction
    weekend_reduction = np.where(df["is_weekend"] == 1, profile["weekend_factor"], 1.0)

    # Temperature cooling requirement (above 26°C, cooling kicks in)
    cooling_requirement = np.maximum(0, df["simulated_temperature_c"] - 26.0) * profile["temp_weight"]

    # Occupancy electricity driver
    occupancy_driver = df["simulated_occupancy_ratio"] * profile["occupancy_weight"]

    # Natural random noise
    noise = rng.normal(0, 1.5, total_hours)

    # Combine components
    energy_kwh = (
        base_load
        + (base_load * hour_factor * weekend_reduction)
        + (occupancy_driver * weekend_reduction)
        + cooling_requirement
        + noise
    )

    # Guarantee realistic positive bounds (never below baseline standby minimum)
    energy_kwh = np.maximum(profile["base_load"] * 0.6, energy_kwh)
    df["energy_kwh"] = np.round(energy_kwh, 2)

    # 4. Scenario Injections
    df["is_injected_anomaly"] = False
    df["anomaly_type"] = "None"
    df["scenario_name"] = scenario

    if scenario == "overnight_waste":
        # Inject continuous overnight waste (e.g., HVAC left running full blast overnight)
        overnight_mask = (
            (day_indices >= 40)
            & (day_indices <= 56)
            & ((df["hour"] >= 22) | (df["hour"] <= 5))
        )
        extra_waste = rng.uniform(11.5, 17.5, total_hours)
        df.loc[overnight_mask, "energy_kwh"] = np.round(
            df.loc[overnight_mask, "energy_kwh"] + extra_waste[overnight_mask], 2
        )
        df.loc[overnight_mask, "is_injected_anomaly"] = True
        df.loc[overnight_mask, "anomaly_type"] = "Overnight HVAC/Lighting Waste"

    elif scenario == "sudden_spike":
        # Inject several distinct sudden sharp equipment / surge spikes
        spike_hours = [
            (48 * 24 + 14, 45.0, "Substation Surge / Unmetered Compressor"),
            (51 * 24 + 10, 52.0, "Chiller Pump Malfunction"),
            (53 * 24 + 16, 38.0, "Heavy Equipment Overload"),
            (55 * 24 + 20, 42.0, "Unscheduled High-Draw Load"),
            (58 * 24 + 12, 50.0, "Faulty Capacitor Bank Draw"),
        ]
        for idx, spike_val, desc in spike_hours:
            if idx < total_hours:
                df.loc[idx, "energy_kwh"] = np.round(df.loc[idx, "energy_kwh"] + spike_val, 2)
                df.loc[idx, "is_injected_anomaly"] = True
                df.loc[idx, "anomaly_type"] = desc
                if idx + 1 < total_hours:
                    df.loc[idx + 1, "energy_kwh"] = np.round(df.loc[idx + 1, "energy_kwh"] + spike_val * 0.45, 2)
                    df.loc[idx + 1, "is_injected_anomaly"] = True
                    df.loc[idx + 1, "anomaly_type"] = f"{desc} (Cooldown)"

    return df


def generate_data_quality_report(
    raw_df: pd.DataFrame, cleaned_df: Optional[pd.DataFrame] = None, error_message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate an audit-grade data quality report for user inspection and export.
    Adheres strictly to DataQualityReportSchema.
    """
    report: Dict[str, Any] = {
        "timestamp_generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "raw_row_count": len(raw_df) if raw_df is not None else 0,
        "is_valid": cleaned_df is not None and error_message is None,
        "error_message": error_message,
        "health_score_pct": 100.0,
        "detected_timezone": "Naive (Local)",
        "sampling_frequency": "Hourly",
        "sampling_frequency_minutes": 60.0,
        "is_regular_interval": True,
        "irregular_intervals_detected": 0,
        "negative_values_found": 0,
        "negative_values_clipped": 0,
        "missing_values_imputed": 0,
        "duplicates_removed": 0,
        "issues_detected": [],
        "repairs_applied": [],
        "data_summary": {},
    }

    if raw_df is None or raw_df.empty:
        report["issues_detected"].append("Dataset contains 0 rows.")
        report["health_score_pct"] = 0.0
        return report

    report["columns_found"] = list(raw_df.columns)

    if cleaned_df is not None:
        report["cleaned_row_count"] = len(cleaned_df)
        report["date_range_start"] = str(cleaned_df["timestamp"].min())
        report["date_range_end"] = str(cleaned_df["timestamp"].max())
        report["total_hours_spanned"] = round(
            (cleaned_df["timestamp"].max() - cleaned_df["timestamp"].min()).total_seconds() / 3600.0, 1
        )
        report["data_summary"] = {
            "min_kwh": float(cleaned_df["energy_kwh"].min()),
            "max_kwh": float(cleaned_df["energy_kwh"].max()),
            "mean_kwh": round(float(cleaned_df["energy_kwh"].mean()), 2),
            "median_kwh": round(float(cleaned_df["energy_kwh"].median()), 2),
            "total_consumption_kwh": round(float(cleaned_df["energy_kwh"].sum()), 2),
        }
        report["power_vs_energy_note"] = (
            "Electricity consumption is processed as Energy (kWh = cumulative electrical energy). "
            "Power (kW) represents instantaneous electrical demand. For hourly interval data, 1 kW sustained for 1 hour = 1 kWh."
        )

        # Pull detailed audit attributes if populated by validator
        attrs = getattr(cleaned_df, "attrs", {})
        if attrs:
            report["detected_timezone"] = attrs.get("detected_timezone", report["detected_timezone"])
            report["sampling_frequency"] = attrs.get("sampling_frequency", report["sampling_frequency"])
            report["sampling_frequency_minutes"] = attrs.get("sampling_frequency_minutes", report["sampling_frequency_minutes"])
            report["is_regular_interval"] = attrs.get("is_regular_interval", report["is_regular_interval"])
            report["irregular_intervals_detected"] = attrs.get("irregular_intervals_detected", 0)
            report["negative_values_found"] = attrs.get("negative_values_found", 0)
            report["negative_values_clipped"] = attrs.get("negative_values_clipped", 0)
            report["missing_values_imputed"] = attrs.get("missing_values_imputed", 0)
            report["duplicates_removed"] = attrs.get("duplicates_removed", 0)

            # Build narrative issue and repair lists
            if report["duplicates_removed"] > 0:
                report["issues_detected"].append(f"Detected {report['duplicates_removed']} duplicate timestamps.")
                report["repairs_applied"].append(f"Removed {report['duplicates_removed']} duplicate timestamps (retained first occurrence).")

            if report["negative_values_found"] > 0:
                report["issues_detected"].append(f"Identified {report['negative_values_found']} negative energy readings (< 0 kWh).")
                report["repairs_applied"].append(f"Sanitized {report['negative_values_clipped']} negative values by clipping to 0.0 kWh standby minimum.")

            if report["missing_values_imputed"] > 0:
                report["issues_detected"].append(f"Found {report['missing_values_imputed']} missing or unreadable consumption intervals.")
                report["repairs_applied"].append(f"Imputed {report['missing_values_imputed']} missing intervals via linear interpolation and boundary fill.")

            if report["irregular_intervals_detected"] > 0:
                report["issues_detected"].append(
                    f"Observed {report['irregular_intervals_detected']} irregular interval deviations from nominal {report['sampling_frequency']} cadence."
                )

            # Compute Data Health Score (0-100%)
            raw_len = max(len(raw_df), 1)
            deductions = (
                (report["missing_values_imputed"] / raw_len) * 30.0
                + (report["negative_values_found"] / raw_len) * 20.0
                + (report["duplicates_removed"] / raw_len) * 15.0
                + (10.0 if not report["is_regular_interval"] else 0.0)
            )
            report["health_score_pct"] = round(max(0.0, min(100.0, 100.0 - deductions)), 1)

    return report


def validate_uploaded_csv(
    df: pd.DataFrame,
    resample_sub_hourly: bool = False,
) -> Tuple[bool, Optional[str], Optional[pd.DataFrame]]:
    """
    Validate and sanitize an uploaded energy consumption CSV.

    Enforces strict schema rules:
    - Rejects empty datasets and datasets > 500,000 rows.
    - Resolves timestamp column from tolerance list.
    - Handles and normalizes timezones (converts tz-aware to consistent tz-naive).
    - Resolves energy column (or power kW column with automatic integration).
    - Detects sampling frequency and flags irregular intervals.
    - Checks for duplicate timestamps and deduplicates.
    - Checks for invalid negative consumption and clips to zero (with audit tracking).
    - Checks for excessive missing gaps (> 24 consecutive hours).
    - Imputes minor missing gaps using linear interpolation.
    - Optionally regularizes sub-hourly telemetry to uniform hourly intervals.
    - Checks for minimum observation threshold (>= 48 hourly readings).
    - Enriches time features and attaches audit attributes.

    Returns:
    --------
    (is_valid: bool, error_message: Optional[str], cleaned_df: Optional[pd.DataFrame])
    """
    if df is None or df.empty:
        return False, "The uploaded CSV file is empty.", None

    if len(df) > MAX_ALLOWED_ROWS:
        return (
            False,
            f"File exceeds maximum allowed upload size: {len(df):,} rows found (maximum {MAX_ALLOWED_ROWS:,} supported).",
            None,
        )

    col_mapping = {}
    cols_lower = {str(c).strip().lower(): c for c in df.columns}

    # 1. Locate Timestamp Column
    ts_candidates = ["timestamp", "datetime", "date_time", "time", "date", "reading_time"]
    ts_col = None
    for cand in ts_candidates:
        if cand in cols_lower:
            ts_col = cols_lower[cand]
            break

    if not ts_col:
        return (
            False,
            f"Missing required timestamp column. Expected one of: {ts_candidates}. Found: {list(df.columns)}",
            None,
        )
    col_mapping[ts_col] = "timestamp"

    # 2. Locate Energy (kWh) or Power (kW) Column
    energy_candidates = [
        "energy_kwh",
        "kwh",
        "energy",
        "consumption_kwh",
        "consumption",
        "usage",
        "electricity_kwh",
        "active_energy_kwh",
    ]
    power_candidates = ["power_kw", "kw", "power", "active_power_kw", "demand_kw"]

    energy_col = None
    is_power_source = False

    for cand in energy_candidates:
        if cand in cols_lower:
            energy_col = cols_lower[cand]
            break

    if not energy_col:
        for cand in power_candidates:
            if cand in cols_lower:
                energy_col = cols_lower[cand]
                is_power_source = True
                break

    if not energy_col:
        return (
            False,
            f"Missing required energy consumption column. Expected energy (kWh) or power (kW). Found: {list(df.columns)}",
            None,
        )

    # 3. Rename and Extract
    cleaned = pd.DataFrame()
    cleaned["timestamp"] = df[ts_col].copy()
    cleaned["energy_kwh"] = df[energy_col].copy()

    # Optional columns: building_id, temperature, occupancy
    for opt_c in ["building", "building_id", "facility", "meter_id"]:
        if opt_c in cols_lower:
            cleaned["building_id"] = df[cols_lower[opt_c]].astype(str)
            break
    if "building_id" not in cleaned.columns:
        cleaned["building_id"] = "Uploaded Facility"

    for temp_c in ["temperature", "temp", "temp_c", "ambient_temp"]:
        if temp_c in cols_lower:
            cleaned["simulated_temperature_c"] = pd.to_numeric(df[cols_lower[temp_c]], errors="coerce")
            break
    if "simulated_temperature_c" not in cleaned.columns:
        cleaned["simulated_temperature_c"] = 28.0

    for occ_c in ["occupancy", "occupancy_ratio", "occ"]:
        if occ_c in cols_lower:
            cleaned["simulated_occupancy_ratio"] = pd.to_numeric(df[cols_lower[occ_c]], errors="coerce")
            break
    if "simulated_occupancy_ratio" not in cleaned.columns:
        cleaned["simulated_occupancy_ratio"] = 0.5

    # 4. Parse Timestamps & Handle Timezones
    try:
        cleaned["timestamp"] = pd.to_datetime(cleaned["timestamp"])
    except Exception as e:
        return False, f"Failed to parse timestamp column as datetime: {str(e)}", None

    detected_tz = "Naive (Local)"
    if hasattr(cleaned["timestamp"].dt, "tz") and cleaned["timestamp"].dt.tz is not None:
        detected_tz = str(cleaned["timestamp"].dt.tz)
        # Convert timezone-aware to timezone-naive local/UTC to prevent tz-naive vs tz-aware comparison errors
        cleaned["timestamp"] = cleaned["timestamp"].dt.tz_localize(None)

    if cleaned["timestamp"].isna().any():
        cleaned = cleaned.dropna(subset=["timestamp"]).reset_index(drop=True)
        if cleaned.empty:
            return False, "All timestamp values are invalid or unparseable.", None

    # Deduplicate Timestamps
    num_dups = 0
    if cleaned["timestamp"].duplicated().any():
        num_dups = int(cleaned["timestamp"].duplicated().sum())
        cleaned = cleaned.drop_duplicates(subset=["timestamp"], keep="first").reset_index(drop=True)

    # 5. Parse Numeric Energy
    cleaned["energy_kwh"] = pd.to_numeric(cleaned["energy_kwh"], errors="coerce")
    if cleaned["energy_kwh"].isna().all():
        return False, "All values in the consumption column are non-numeric or unreadable.", None

    # Ensure chronological sort before interval calculation and gap inspection
    cleaned = cleaned.sort_values("timestamp").reset_index(drop=True)

    # Sampling Frequency & Interval Analysis
    deltas_sec = cleaned["timestamp"].diff().dt.total_seconds().dropna()
    deltas_min = deltas_sec / 60.0

    if not deltas_min.empty:
        median_delta_min = float(deltas_min.median())
        mode_series = deltas_min.mode()
        mode_delta_min = float(mode_series.iloc[0]) if not mode_series.empty else median_delta_min
    else:
        median_delta_min = 60.0
        mode_delta_min = 60.0

    if 10.0 <= mode_delta_min <= 20.0:
        freq_label = "15-minute"
    elif 25.0 <= mode_delta_min <= 35.0:
        freq_label = "30-minute"
    elif 50.0 <= mode_delta_min <= 70.0:
        freq_label = "Hourly"
    elif 1300.0 <= mode_delta_min <= 1500.0:
        freq_label = "Daily"
    else:
        freq_label = f"{mode_delta_min:.0f}-minute"

    irregular_mask = (deltas_min < mode_delta_min * 0.85) | (deltas_min > mode_delta_min * 1.15)
    irregular_count = int(irregular_mask.sum())
    is_regular = irregular_count == 0

    # Power to Energy Conversion if source was kW
    if is_power_source:
        delta_hours = cleaned["timestamp"].diff().dt.total_seconds() / 3600.0
        delta_hours = delta_hours.bfill().fillna(1.0).clip(lower=0.0)
        cleaned["energy_kwh"] = cleaned["energy_kwh"] * delta_hours

    # 6. Check for Negative Values and Sanitize
    num_neg = int((cleaned["energy_kwh"] < 0).sum())
    if num_neg > 0:
        cleaned["energy_kwh"] = cleaned["energy_kwh"].clip(lower=0.0)

    # 7. Check Consecutive Missing Values Gap Limit
    consec_na = cleaned["energy_kwh"].isna().astype(int).groupby(cleaned["energy_kwh"].notna().cumsum()).sum()
    if (consec_na > 24).any():
        return (
            False,
            "Dataset contains an unacceptably large gap of consecutive missing values (>24 hours). "
            "Please provide a contiguous dataset for accurate baseline and forecasting analysis.",
            None,
        )

    num_missing = int(cleaned["energy_kwh"].isna().sum())
    if num_missing > 0:
        # Small missing values linear interpolation then forward/backward fill
        cleaned["energy_kwh"] = cleaned["energy_kwh"].interpolate(method="linear").ffill().bfill()

    # 8. Regularize Sub-Hourly Telemetry (e.g. 15-min or 30-min to Hourly)
    if resample_sub_hourly and mode_delta_min < 50.0 and len(cleaned) >= 8:
        agg_rules = {"energy_kwh": "sum"}
        if "simulated_temperature_c" in cleaned.columns:
            agg_rules["simulated_temperature_c"] = "mean"
        if "simulated_occupancy_ratio" in cleaned.columns:
            agg_rules["simulated_occupancy_ratio"] = "mean"
        if "building_id" in cleaned.columns:
            agg_rules["building_id"] = "first"

        resampled = (
            cleaned.set_index("timestamp")
            .resample("h")
            .agg(agg_rules)
            .dropna(subset=["energy_kwh"])
            .reset_index()
        )
        if len(resampled) >= 24:
            cleaned = resampled

    # 9. Minimum Length Check
    if len(cleaned) < 48:
        return (
            False,
            f"Insufficient observations: file contains only {len(cleaned)} rows. "
            "A minimum of 48 readings is required for baseline modeling.",
            None,
        )

    # 10. Enrich Time-Series Indicators
    cleaned["hour"] = cleaned["timestamp"].dt.hour
    cleaned["day_of_week"] = cleaned["timestamp"].dt.dayofweek
    cleaned["day_name"] = cleaned["timestamp"].dt.day_name()
    cleaned["is_weekend"] = cleaned["day_of_week"].isin([5, 6]).astype(int)
    cleaned["building_category"] = "User Uploaded Dataset"
    cleaned["is_synthetic"] = False
    cleaned["scenario_name"] = "Custom Upload"
    cleaned["is_injected_anomaly"] = False
    cleaned["anomaly_type"] = "None"

    # Attach audit attributes for quality report generation
    cleaned.attrs["detected_timezone"] = detected_tz
    cleaned.attrs["sampling_frequency"] = freq_label
    cleaned.attrs["sampling_frequency_minutes"] = round(mode_delta_min, 1)
    cleaned.attrs["is_regular_interval"] = is_regular
    cleaned.attrs["irregular_intervals_detected"] = irregular_count
    cleaned.attrs["negative_values_found"] = num_neg
    cleaned.attrs["negative_values_clipped"] = num_neg
    cleaned.attrs["missing_values_imputed"] = num_missing
    cleaned.attrs["duplicates_removed"] = num_dups

    return True, None, cleaned

    return True, None, cleaned


def get_sample_csv_content() -> str:
    """
    Generate downloadable sample CSV text adhering to expected EcoPilot schema.
    """
    dates = pd.date_range("2026-09-01 00:00:00", periods=72, freq="h")
    sample_data = []
    for d in dates:
        h = d.hour
        is_wknd = 1 if d.dayofweek in [5, 6] else 0
        base = 15.0 if not is_wknd else 10.0
        active = 20.0 * np.exp(-0.5 * ((h - 14) / 3.0) ** 2)
        kwh = round(base + active + np.random.uniform(0.5, 2.5), 2)
        temp = round(26.0 + 4.0 * np.sin((h - 8) * 2 * np.pi / 24), 1)
        sample_data.append(
            {
                "timestamp": d.strftime("%Y-%m-%d %H:%M:%S"),
                "energy_kwh": kwh,
                "building_id": "Campus-Block-A",
                "temperature_c": temp,
                "occupancy_ratio": round(0.1 + (0.8 * (active / 20.0)), 2),
            }
        )
    sample_df = pd.DataFrame(sample_data)
    csv_buf = io.StringIO()
    sample_df.to_csv(csv_buf, index=False)
    return csv_buf.getvalue()
