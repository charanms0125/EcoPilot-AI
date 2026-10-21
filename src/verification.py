"""
EcoPilot AI: Before-and-After Savings Verification Engine
Computes empirical realized savings by comparing post-intervention telemetry
against pre-intervention baselines, with optional weather/occupancy adjustments,
strict insufficient-data states, and causal humility disclaimers.
"""

from typing import Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime

from src.carbon import CarbonCalculator
from src.database import save_verification, get_all_verifications


def _fmt_ts(val) -> str:
    """Safely format timestamp to string without crashing on NaT or non-datetime objects."""
    if pd.notna(val) and hasattr(val, "strftime"):
        return val.strftime("%Y-%m-%d %H:%M")
    elif pd.notna(val):
        return str(val)
    return "N/A"


class SavingsVerifier:
    """
    Evaluates real-world energy and cost reductions achieved after an intervention.
    Enforces clear conceptual separation between:
    1. Detected Potential Waste (historical anomalies)
    2. Estimated Potential Savings (model projections)
    3. Verified Realized Savings (sub-meter or interval before-and-after tracking)
    """

    MIN_POST_HOURS: int = 48  # Minimum 2 days of post-intervention telemetry required

    @staticmethod
    def verify_intervention(
        df: pd.DataFrame,
        intervention_name: str,
        intervention_date: str,
        baseline_start_date: Optional[str] = None,
        baseline_end_date: Optional[str] = None,
        post_start_date: Optional[str] = None,
        post_end_date: Optional[str] = None,
        expected_savings_kwh: float = 0.0,
        tariff_inr_per_kwh: float = 8.50,
        carbon_calc: Optional[CarbonCalculator] = None,
        rec_id: Optional[str] = None,
        notes: str = "",
        cooling_sensitivity_kwh_per_c: Optional[float] = None,
        weather_col: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute before-and-after verification analysis.

        Parameters:
        -----------
        df: pd.DataFrame
            Full dataset with 'timestamp' and 'energy_kwh'.
        intervention_name: str
            Name/title of the conservation measure.
        intervention_date: str
            Date or timestamp when intervention took effect.
        baseline_start_date, baseline_end_date: Optional[str]
            Date range for baseline reference period. Defaults to 14 days before intervention.
        post_start_date, post_end_date: Optional[str]
            Date range for evaluation. Defaults to available data after intervention.
        expected_savings_kwh: float
            Original ex-ante projected savings.
        tariff_inr_per_kwh: float
            Applicable electricity tariff (₹/kWh).
        carbon_calc: Optional[CarbonCalculator]
            Configured carbon calculator instance.

        Returns:
        --------
        Dict with realized savings, realization rate, counterfactual models, and verification status.
        """
        if df is None or not isinstance(df, pd.DataFrame):
            raise ValueError("Input must be a valid pandas DataFrame.")

        if "timestamp" not in df.columns or "energy_kwh" not in df.columns:
            raise ValueError("DataFrame must contain 'timestamp' and 'energy_kwh' columns.")

        v_id = f"VERIF-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        if df.empty:
            return {
                "id": v_id,
                "rec_id": rec_id or "",
                "intervention_name": intervention_name,
                "intervention_start_date": str(intervention_date),
                "baseline_period_start": "N/A",
                "baseline_period_end": "N/A",
                "post_period_start": "N/A",
                "post_period_end": "N/A",
                "baseline_hours": 0,
                "post_hours": 0,
                "expected_savings_kwh": round(float(expected_savings_kwh), 2),
                "expected_savings_inr": round(float(expected_savings_kwh * tariff_inr_per_kwh), 2),
                "observed_consumption_kwh": 0.0,
                "baseline_counterfactual_kwh": 0.0,
                "realized_savings_kwh": 0.0,
                "realized_savings_inr": 0.0,
                "weather_adjusted_savings_kwh": 0.0,
                "realization_rate_pct": 0.0,
                "verification_status": "Insufficient data",
                "verified_avoided_kg_co2e": 0.0,
                "adjustment_method": "None (Empty Telemetry)",
                "tariff_inr_per_kwh": tariff_inr_per_kwh,
                "notes": notes or "No telemetry data provided for verification.",
                "disclaimers": [
                    "Insufficient data: empty dataset provided.",
                    "No savings claims can be verified without operational records.",
                ],
                "weather_normalization_assumptions": {
                    "is_weather_adjusted": False,
                    "temperature_column": None,
                    "baseline_avg_temp_c": None,
                    "post_avg_temp_c": None,
                    "temperature_delta_c": 0.0,
                    "temperature_sensitivity_kwh_per_c": 0.0,
                    "sensitivity_estimation_method": "None (Empty Telemetry)",
                    "weather_adjustment_kwh": 0.0,
                    "assumptions_documentation": [
                        "Insufficient data to perform weather normalization.",
                    ],
                },
            }

        data = df.copy()
        data["timestamp"] = pd.to_datetime(data["timestamp"])
        data = data.sort_values("timestamp").reset_index(drop=True)

        interv_ts = pd.to_datetime(intervention_date)

        # Baseline Period
        if baseline_start_date and baseline_end_date:
            b_mask = (data["timestamp"] >= pd.to_datetime(baseline_start_date)) & (
                data["timestamp"] <= pd.to_datetime(baseline_end_date)
            )
        else:
            # Default: 14 days immediately preceding intervention
            b_mask = (data["timestamp"] >= (interv_ts - pd.Timedelta(days=14))) & (
                data["timestamp"] < interv_ts
            )

        baseline_df = data[b_mask].copy()

        # Post-Intervention Period
        if post_start_date and post_end_date:
            p_mask = (data["timestamp"] >= pd.to_datetime(post_start_date)) & (
                data["timestamp"] <= pd.to_datetime(post_end_date)
            )
        else:
            p_mask = data["timestamp"] >= interv_ts

        post_df = data[p_mask].copy()

        # Handle Insufficient or Empty Data Gracefully
        post_hours = len(post_df)
        baseline_hours = len(baseline_df)

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Check for Empty Baseline
        if baseline_hours == 0 or baseline_df.empty:
            return {
                "id": v_id,
                "rec_id": rec_id or "",
                "intervention_name": intervention_name,
                "intervention_start_date": _fmt_ts(interv_ts),
                "baseline_period_start": "N/A",
                "baseline_period_end": "N/A",
                "post_period_start": _fmt_ts(post_df["timestamp"].min()) if not post_df.empty else "N/A",
                "post_period_end": _fmt_ts(post_df["timestamp"].max()) if not post_df.empty else "N/A",
                "baseline_hours": 0,
                "post_hours": post_hours,
                "expected_savings_kwh": round(float(expected_savings_kwh), 2),
                "expected_savings_inr": round(float(expected_savings_kwh * tariff_inr_per_kwh), 2),
                "observed_consumption_kwh": round(float(post_df["energy_kwh"].sum()), 2) if not post_df.empty else 0.0,
                "baseline_counterfactual_kwh": 0.0,
                "realized_savings_kwh": 0.0,
                "realized_savings_inr": 0.0,
                "weather_adjusted_savings_kwh": 0.0,
                "realization_rate_pct": 0.0,
                "verification_status": "Insufficient baseline data",
                "verified_avoided_kg_co2e": 0.0,
                "adjustment_method": "None (Insufficient Baseline Telemetry)",
                "tariff_inr_per_kwh": tariff_inr_per_kwh,
                "notes": notes or "Insufficient baseline telemetry: No baseline reference data available for specified period.",
                "disclaimers": [
                    "Insufficient baseline data: no pre-intervention telemetry available.",
                    "No savings claims can be verified without baseline operational records.",
                ],
                "weather_normalization_assumptions": {
                    "is_weather_adjusted": False,
                    "temperature_column": None,
                    "baseline_avg_temp_c": None,
                    "post_avg_temp_c": None,
                    "temperature_delta_c": 0.0,
                    "temperature_sensitivity_kwh_per_c": 0.0,
                    "sensitivity_estimation_method": "None (Insufficient Baseline Telemetry)",
                    "weather_adjustment_kwh": 0.0,
                    "assumptions_documentation": [
                        "Insufficient baseline telemetry to model weather normalization.",
                    ],
                },
            }

        # 2. Check for Empty or Insufficient Post-Intervention Data
        if post_hours < SavingsVerifier.MIN_POST_HOURS:
            return {
                "id": v_id,
                "rec_id": rec_id or "",
                "intervention_name": intervention_name,
                "intervention_start_date": _fmt_ts(interv_ts),
                "baseline_period_start": _fmt_ts(baseline_df["timestamp"].min()) if not baseline_df.empty else "N/A",
                "baseline_period_end": _fmt_ts(baseline_df["timestamp"].max()) if not baseline_df.empty else "N/A",
                "post_period_start": _fmt_ts(post_df["timestamp"].min()) if not post_df.empty else "N/A",
                "post_period_end": _fmt_ts(post_df["timestamp"].max()) if not post_df.empty else "N/A",
                "baseline_hours": baseline_hours,
                "post_hours": post_hours,
                "expected_savings_kwh": round(float(expected_savings_kwh), 2),
                "expected_savings_inr": round(float(expected_savings_kwh * tariff_inr_per_kwh), 2),
                "observed_consumption_kwh": round(float(post_df["energy_kwh"].sum()), 2) if not post_df.empty else 0.0,
                "baseline_counterfactual_kwh": 0.0,
                "realized_savings_kwh": 0.0,
                "realized_savings_inr": 0.0,
                "weather_adjusted_savings_kwh": 0.0,
                "realization_rate_pct": 0.0,
                "verification_status": "Awaiting verification data",
                "verified_avoided_kg_co2e": 0.0,
                "adjustment_method": "None (Insufficient Telemetry)",
                "tariff_inr_per_kwh": tariff_inr_per_kwh,
                "notes": notes or (
                    f"Awaiting verification data: only {post_hours} hours of post-intervention telemetry recorded. "
                    f"A minimum of {SavingsVerifier.MIN_POST_HOURS} hours is required for statistical confidence."
                ),
                "disclaimers": [
                    "Awaiting verification data: insufficient post-intervention hours.",
                    "No savings claims can be verified until sufficient operational records accrue.",
                ],
                "weather_normalization_assumptions": {
                    "is_weather_adjusted": False,
                    "temperature_column": None,
                    "baseline_avg_temp_c": None,
                    "post_avg_temp_c": None,
                    "temperature_delta_c": 0.0,
                    "temperature_sensitivity_kwh_per_c": 0.0,
                    "sensitivity_estimation_method": "None (Insufficient Telemetry)",
                    "weather_adjustment_kwh": 0.0,
                    "assumptions_documentation": [
                        "Insufficient post-intervention telemetry to model weather normalization.",
                    ],
                },
            }

        # 1. Unadjusted Before-and-After Counterfactual
        # Compute baseline profile grouped by (is_weekend, hour) to control for circadian & weekend shifts
        if "is_weekend" not in baseline_df.columns:
            baseline_df["is_weekend"] = baseline_df["timestamp"].dt.dayofweek.isin([5, 6]).astype(int)
        if "hour" not in baseline_df.columns:
            baseline_df["hour"] = baseline_df["timestamp"].dt.hour

        if "is_weekend" not in post_df.columns:
            post_df["is_weekend"] = post_df["timestamp"].dt.dayofweek.isin([5, 6]).astype(int)
        if "hour" not in post_df.columns:
            post_df["hour"] = post_df["timestamp"].dt.hour

        hourly_b_profile = (
            baseline_df.groupby(["is_weekend", "hour"])["energy_kwh"]
            .mean()
            .reset_index()
            .rename(columns={"energy_kwh": "baseline_expected_hour_kwh"})
        )

        merged_post = post_df.merge(hourly_b_profile, on=["is_weekend", "hour"], how="left")
        # Fallback to general baseline mean if specific hour combination missing
        global_b_mean = float(baseline_df["energy_kwh"].mean())
        merged_post["baseline_expected_hour_kwh"] = merged_post["baseline_expected_hour_kwh"].fillna(global_b_mean)

        baseline_counterfactual_kwh = float(merged_post["baseline_expected_hour_kwh"].sum())
        observed_post_kwh = float(merged_post["energy_kwh"].sum())

        realized_kwh = round(baseline_counterfactual_kwh - observed_post_kwh, 2)
        realized_inr = round(realized_kwh * tariff_inr_per_kwh, 2)

        # Realization Rate: realized savings vs. expected ex-ante savings
        if expected_savings_kwh > 0:
            realization_rate = round((realized_kwh / expected_savings_kwh) * 100.0, 1)
        else:
            realization_rate = 100.0 if realized_kwh > 0 else 0.0

        # Categorize Verification Status
        if realized_kwh >= expected_savings_kwh * 0.9 and realized_kwh > 0:
            status = "Target Met / Exceeded"
        elif realized_kwh > 0:
            status = "Partial Savings Realized (Underperforming Target)"
        else:
            status = "No Savings Detected / Consumption Increased"

        # 2. Weather & Occupancy Adjusted Counterfactual (when features available)
        # Identify temperature column if present
        t_col = None
        if weather_col and weather_col in baseline_df.columns and weather_col in post_df.columns:
            t_col = weather_col
        else:
            for candidate in ["simulated_temperature_c", "temperature_c", "temperature", "temp_c", "ambient_temp"]:
                if candidate in baseline_df.columns and candidate in post_df.columns:
                    t_col = candidate
                    break

        adjustment_method = "Hour-of-Week Profile Counterfactual"
        adjusted_savings_kwh = realized_kwh

        if t_col:
            b_temp = float(baseline_df[t_col].mean())
            p_temp = float(post_df[t_col].mean())
            temp_delta = p_temp - b_temp

            # Derive empirical temperature sensitivity beta (kWh / °C)
            if cooling_sensitivity_kwh_per_c is not None:
                beta_temp = float(cooling_sensitivity_kwh_per_c)
                beta_source = "User-Configured Sensitivity"
            else:
                # Estimate empirical slope from baseline telemetry via OLS: Cov(T, E) / Var(T)
                var_t = float(np.var(baseline_df[t_col]))
                if var_t > 0.05 and len(baseline_df) >= 24:
                    cov_te = float(np.cov(baseline_df[t_col], baseline_df["energy_kwh"])[0, 1])
                    empirical_beta = cov_te / var_t
                    # Sensible bounds for cooling load sensitivity
                    if empirical_beta > 0.05:
                        beta_temp = round(float(empirical_beta), 3)
                        beta_source = f"Empirical Baseline OLS Regression ({t_col})"
                    else:
                        beta_temp = 1.2
                        beta_source = "Standard Benchmark Fallback (1.2 kWh/°C)"
                else:
                    beta_temp = 1.2
                    beta_source = "Standard Benchmark Fallback (Low Baseline Temp Variance)"

            weather_adjustment_kwh = round(float(temp_delta * beta_temp * post_hours), 2)
            adjusted_savings_kwh = round(realized_kwh + weather_adjustment_kwh, 2)
            adjustment_method = f"Weather-Normalized ({beta_source}: {beta_temp:.2f} kWh/°C delta)"

            weather_assumptions = {
                "is_weather_adjusted": True,
                "temperature_column": t_col,
                "baseline_avg_temp_c": round(b_temp, 2),
                "post_avg_temp_c": round(p_temp, 2),
                "temperature_delta_c": round(temp_delta, 2),
                "temperature_sensitivity_kwh_per_c": beta_temp,
                "sensitivity_estimation_method": beta_source,
                "weather_adjustment_kwh": weather_adjustment_kwh,
                "assumptions_documentation": [
                    f"Post-intervention period was on average {abs(temp_delta):.2f}°C "
                    f"{'warmer' if temp_delta >= 0 else 'cooler'} than the baseline reference period.",
                    f"Thermal response rate of {beta_temp:.2f} kWh/°C derived via {beta_source}.",
                    "Assumes static building thermal envelope and linear cooling degree drift across evaluation period.",
                    "Weather adjustment is applied to the counterfactual to isolate intervention effect from ambient weather drift.",
                ],
            }
        else:
            weather_assumptions = {
                "is_weather_adjusted": False,
                "temperature_column": None,
                "baseline_avg_temp_c": None,
                "post_avg_temp_c": None,
                "temperature_delta_c": 0.0,
                "temperature_sensitivity_kwh_per_c": 0.0,
                "sensitivity_estimation_method": "None (No temperature telemetry)",
                "weather_adjustment_kwh": 0.0,
                "assumptions_documentation": [
                    "No temperature telemetry detected; unadjusted hour-of-week profile counterfactual applied.",
                    "Assumes ambient weather conditions during post-intervention period were comparable to baseline.",
                ],
            }

        # 3. Verified Carbon Emissions
        verified_co2_kg = 0.0
        if carbon_calc and carbon_calc.is_configured and realized_kwh > 0:
            c_res = carbon_calc.calculate_avoided_emissions(
                electricity_saved_kwh=realized_kwh,
                is_verified=True,
                intervention_name=intervention_name,
            )
            verified_co2_kg = c_res["avoided_emissions_kg_co2e"] or 0.0

        result = {
            "id": v_id,
            "rec_id": rec_id or "",
            "intervention_name": intervention_name,
            "intervention_start_date": _fmt_ts(interv_ts),
            "baseline_period_start": _fmt_ts(baseline_df["timestamp"].min()),
            "baseline_period_end": _fmt_ts(baseline_df["timestamp"].max()),
            "post_period_start": _fmt_ts(post_df["timestamp"].min()),
            "post_period_end": _fmt_ts(post_df["timestamp"].max()),
            "baseline_hours": baseline_hours,
            "post_hours": post_hours,
            "expected_savings_kwh": round(float(expected_savings_kwh), 2),
            "expected_savings_inr": round(float(expected_savings_kwh * tariff_inr_per_kwh), 2),
            "observed_consumption_kwh": round(observed_post_kwh, 2),
            "baseline_counterfactual_kwh": round(baseline_counterfactual_kwh, 2),
            "realized_savings_kwh": realized_kwh,
            "realized_savings_inr": realized_inr,
            "weather_adjusted_savings_kwh": adjusted_savings_kwh,
            "weather_normalization_assumptions": weather_assumptions,
            "realization_rate_pct": realization_rate,
            "verification_status": status,
            "verified_avoided_kg_co2e": verified_co2_kg,
            "adjustment_method": adjustment_method,
            "tariff_inr_per_kwh": tariff_inr_per_kwh,
            "notes": notes or f"Realized savings verified over {post_hours} hours with {adjustment_method}.",
            "disclaimers": [
                "Realized savings represent interval counterfactual differences.",
                "Uncontrolled before-and-after tracking does not establish absolute causal proof without sub-metered circuit isolation.",
                "Weather and operational shifts have been modeled where features permit.",
            ],
        }

        return result

    @staticmethod
    def save_and_persist_verification(
        verification_result: Dict[str, Any], db_path: Optional[str] = None
    ) -> bool:
        """Persist verification assessment into SQLite database."""
        return save_verification(verification_result, db_path)

    @staticmethod
    def get_historical_verifications(db_path: Optional[str] = None):
        """Retrieve historical verification records."""
        return get_all_verifications(db_path)
