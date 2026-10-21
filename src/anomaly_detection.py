"""
EcoPilot AI: Explainable Anomaly Detection Engine
Transparent statistical baseline modeling, multi-tier severity categorization,
distinct separation of Unusual Consumption vs. Potential Wastage vs. Confirmed Savings,
and Scikit-learn Isolation Forest integration with explicit ethical guardrails.
"""

from typing import List, Dict, Any, Optional
import re
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


def _sanitize_id_token(val: Optional[str], default: str = "") -> str:
    """Sanitize string token into safe uppercase alphanumeric-hyphen slug."""
    if not val:
        return default
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", str(val).strip()).strip("-").upper()
    return cleaned[:24] if cleaned else default


def compute_hourly_baselines(
    df: pd.DataFrame,
    exclude_injected_anomalies: bool = True,
    robust_dispersion: bool = True,
) -> pd.DataFrame:
    """
    Compute transparent historical baseline metrics grouped by (hour, is_weekend).
    Calculates median, mean, standard deviation, 25th, and 75th percentiles.
    Prevents baseline leakage by excluding contaminated / injected anomaly rows.
    """
    data = df.copy()
    if "is_weekend" not in data.columns and "timestamp" in data.columns:
        data["is_weekend"] = pd.to_datetime(data["timestamp"]).dt.dayofweek.isin([5, 6]).astype(int)
    if "hour" not in data.columns and "timestamp" in data.columns:
        data["hour"] = pd.to_datetime(data["timestamp"]).dt.hour

    # Prevent baseline leakage by filtering out known/injected anomalies when available
    calc_data = data
    if exclude_injected_anomalies:
        clean_mask = pd.Series(True, index=data.index)
        if "is_injected_anomaly" in data.columns:
            clean_mask = clean_mask & (~data["is_injected_anomaly"].fillna(False).astype(bool))
        if "is_anomaly" in data.columns:
            clean_mask = clean_mask & (~data["is_anomaly"].fillna(False).astype(bool))

        # Only subset if at least some clean rows exist
        if clean_mask.sum() > 0:
            calc_data = data[clean_mask]

    grouped = calc_data.groupby(["is_weekend", "hour"])["energy_kwh"].agg(
        baseline_median="median",
        baseline_mean="mean",
        baseline_std="std",
        q25=lambda x: np.percentile(x, 25),
        q75=lambda x: np.percentile(x, 75),
    ).reset_index()

    # Fallback for any missing bins if calc_data dropped all rows of that bin
    if len(grouped) < 48 and len(data) > 0:
        full_grouped = data.groupby(["is_weekend", "hour"])["energy_kwh"].agg(
            baseline_median="median",
            baseline_mean="mean",
            baseline_std="std",
            q25=lambda x: np.percentile(x, 25),
            q75=lambda x: np.percentile(x, 75),
        ).reset_index()
        grouped = full_grouped.merge(grouped, on=["is_weekend", "hour"], how="left", suffixes=("_full", ""))
        for col in ["baseline_median", "baseline_mean", "baseline_std", "q25", "q75"]:
            grouped[col] = grouped[col].fillna(grouped[f"{col}_full"])
        grouped = grouped[["is_weekend", "hour", "baseline_median", "baseline_mean", "baseline_std", "q25", "q75"]]

    grouped["baseline_iqr"] = grouped["q75"] - grouped["q25"]

    # Robust dispersion: protect against baseline std inflation from unflagged extreme outliers
    if robust_dispersion:
        # For a normal distribution, IQR ~ 1.349 * sigma
        robust_std = grouped["baseline_iqr"] / 1.349
        grouped["baseline_std"] = np.where(
            (robust_std > 0.05) & (grouped["baseline_std"] > 1.5 * robust_std),
            robust_std,
            grouped["baseline_std"],
        )

    # Fill any zero std to avoid division by zero
    grouped["baseline_std"] = grouped["baseline_std"].replace(0, 1.0).fillna(1.0)
    grouped["baseline_iqr"] = grouped["baseline_iqr"].replace(0, 1.0).fillna(1.0)

    return grouped


def detect_anomalies(
    df: pd.DataFrame,
    sensitivity_std: float = 2.4,
    min_absolute_diff_kwh: float = 6.0,
    use_isolation_forest: bool = True,
    iforest_contamination: float = 0.03,
    facility_id: Optional[str] = None,
    run_id: Optional[str] = None,
    baseline_df: Optional[pd.DataFrame] = None,
    baseline_start_date: Optional[str] = None,
    baseline_end_date: Optional[str] = None,
    exclude_injected_anomalies: bool = True,
) -> Dict[str, Any]:
    """
    Detect energy consumption anomalies, distinguish unusual load from potential waste,
    and categorize into 4 transparent severity levels (Critical, High, Medium, Low).

    Parameters:
    -----------
    df: pd.DataFrame
        Energy dataframe with 'timestamp', 'energy_kwh', and optional time indicators.
    sensitivity_std: float, default 2.4
        Z-score multiplier threshold.
    min_absolute_diff_kwh: float, default 6.0
        Minimum kWh surplus above baseline required to trigger an alert.
    use_isolation_forest: bool, default True
        Whether to fit an Isolation Forest and correlate with statistical alerts.
    iforest_contamination: float
        Estimated fraction of anomalies for Isolation Forest.
    facility_id: Optional[str], default None
        Unique facility identifier to prevent alert ID collisions across facilities.
    run_id: Optional[str], default None
        Execution run identifier to prevent alert ID collisions across runs.
    baseline_df: Optional[pd.DataFrame], default None
        Dedicated reference baseline dataframe to prevent baseline contamination/leakage.
    baseline_start_date, baseline_end_date: Optional[str], default None
        Explicit date range for historical baseline calculation to prevent data leakage.
    exclude_injected_anomalies: bool, default True
        Whether to exclude injected or known anomaly rows from baseline statistics.

    Returns:
    --------
    Dict containing:
    - 'alerts': list of structured alert dicts with hypotheses and confidence ratings
    - 'flagged_df': original dataframe enriched with anomaly flags and baselines
    - 'summary': dictionary with counts by severity, phenomenon type, and excess kWh
    """
    data = df.copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"])
    if "hour" not in data.columns:
        data["hour"] = data["timestamp"].dt.hour
    if "is_weekend" not in data.columns:
        data["is_weekend"] = data["timestamp"].dt.dayofweek.isin([5, 6]).astype(int)

    # Resolve default facility from argument or dataframe attributes/columns
    default_facility = facility_id
    if not default_facility:
        for opt_col in ["facility_id", "building_id", "facility", "building_category", "building"]:
            if opt_col in data.columns and not data[opt_col].isna().all():
                default_facility = str(data[opt_col].iloc[0])
                break

    # 1. Merge Historical Baselines (preventing leakage from evaluation period or injected anomalies)
    if baseline_df is not None and not baseline_df.empty:
        baseline_source = baseline_df.copy()
        if "timestamp" in baseline_source.columns:
            baseline_source["timestamp"] = pd.to_datetime(baseline_source["timestamp"])
    elif baseline_start_date or baseline_end_date:
        b_mask = pd.Series(True, index=data.index)
        if baseline_start_date:
            b_mask = b_mask & (data["timestamp"] >= pd.to_datetime(baseline_start_date))
        if baseline_end_date:
            b_mask = b_mask & (data["timestamp"] <= pd.to_datetime(baseline_end_date))
        baseline_source = data[b_mask].copy()
    else:
        baseline_source = data.copy()

    baselines = compute_hourly_baselines(
        baseline_source,
        exclude_injected_anomalies=exclude_injected_anomalies,
    )
    merged = data.merge(baselines, on=["is_weekend", "hour"], how="left")

    # 2. Transparent Statistical Differences
    merged["abs_diff_kwh"] = merged["energy_kwh"] - merged["baseline_median"]
    merged["pct_diff"] = np.where(
        merged["baseline_median"] > 0,
        (merged["abs_diff_kwh"] / merged["baseline_median"]) * 100.0,
        0.0,
    )
    merged["z_score"] = merged["abs_diff_kwh"] / merged["baseline_std"]

    # 3. Rule Flag: Standard High Consumption Statistical Anomaly
    # Combines Z-score threshold and IQR rule (deviation > 1.5 * IQR) as documented in ensemble
    iqr_anomaly_mask = merged["abs_diff_kwh"] >= (1.5 * merged["baseline_iqr"])
    stat_mask = (
        ((merged["z_score"] >= sensitivity_std) | iqr_anomaly_mask)
        & (merged["abs_diff_kwh"] >= min_absolute_diff_kwh)
    )
    merged["is_stat_anomaly"] = stat_mask

    # 4. Rule Flag: Overnight Baseload Waste (Hours 22:00 to 06:00)
    overnight_hours = (merged["hour"] >= 22) | (merged["hour"] <= 5)
    overnight_mask = (
        overnight_hours
        & (merged["z_score"] >= max(1.8, sensitivity_std - 0.5))
        & (merged["abs_diff_kwh"] >= max(5.0, min_absolute_diff_kwh * 0.75))
    )
    merged["is_overnight_waste"] = overnight_mask

    # 5. Isolation Forest Unsupervised Outlier Detection (Optional)
    merged["is_iforest_anomaly"] = False
    merged["iforest_score"] = 0.0
    if use_isolation_forest and len(merged) >= 96:
        feature_matrix = merged[
            ["energy_kwh", "hour", "is_weekend", "abs_diff_kwh", "z_score"]
        ].fillna(0)
        iso = IsolationForest(
            contamination=iforest_contamination,
            random_state=42,
            n_estimators=100,
        )
        iso_preds = iso.fit_predict(feature_matrix)
        merged["is_iforest_anomaly"] = (iso_preds == -1)
        merged["iforest_score"] = np.round(iso.decision_function(feature_matrix), 3)

    # 6. Combined Anomaly Flag: Consistent Dual-Method Ensemble
    # Ensembles statistical z-score/IQR rules, nocturnal boundary rules, and Isolation Forest
    if use_isolation_forest:
        iforest_ensemble_mask = merged["is_iforest_anomaly"] & (
            (merged["abs_diff_kwh"] >= max(2.0, min_absolute_diff_kwh * 0.5))
            | (merged["z_score"] >= 1.5)
        )
        merged["is_anomaly"] = (
            merged["is_stat_anomaly"] | merged["is_overnight_waste"] | iforest_ensemble_mask
        )
    else:
        merged["is_anomaly"] = merged["is_stat_anomaly"] | merged["is_overnight_waste"]

    # 7. Build Detailed Explainable Alerts
    alerts: List[Dict[str, Any]] = []
    anomaly_indices = merged[merged["is_anomaly"]].index

    for idx in anomaly_indices:
        row = merged.loc[idx]
        ts = row["timestamp"]
        observed = float(row["energy_kwh"])
        baseline = float(row["baseline_median"])
        abs_diff = round(float(row["abs_diff_kwh"]), 2)
        pct_diff = round(float(row["pct_diff"]), 1)
        z_sc = round(float(row["z_score"]), 2)
        h = int(row["hour"])
        is_stat = bool(row["is_stat_anomaly"])
        is_ovn = bool(row["is_overnight_waste"])
        is_if = bool(row["is_iforest_anomaly"])
        if_score = float(row["iforest_score"])

        # Determine Severity across 4 distinct levels
        # Critical: severe spike or extreme deviation
        if abs_diff >= 45.0 or pct_diff >= 140.0 or z_sc >= 4.2:
            severity = "Critical"
        elif abs_diff >= 25.0 or pct_diff >= 85.0 or z_sc >= 3.2:
            severity = "High"
        elif abs_diff >= 12.0 or pct_diff >= 45.0 or z_sc >= 2.2:
            severity = "Medium"
        else:
            severity = "Low"

        # Distinguish: Potential Energy Wastage vs Unusual Consumption vs Multi-dimensional Outlier
        if is_ovn:
            phenomenon_type = "Potential Energy Wastage"
            category = "Overnight Baseload Shift"
            rule_explanation = (
                f"Observed {observed:.1f} kWh during low-occupancy hour {h:02d}:00 exceeded "
                f"the typical nocturnal baseline of {baseline:.1f} kWh by +{abs_diff:.1f} kWh (+{pct_diff:.1f}%). "
                f"Statistical deviation: {z_sc}σ above historical median."
            )
            hypothesis = (
                "Hypothesis: Central ventilation, auxiliary split AC units, water pumps, "
                "or high-bay illumination left running outside operating schedule. "
                "Action: Physical audit of overnight building control schedule and smart timer interlocks."
            )
            investigation_steps = [
                "1. Check facility sub-panel meters for active circuits after 22:00.",
                "2. Verify whether occupancy sensors in lecture halls and corridors are functioning.",
                "3. Inspect central chiller/AHU setback schedule.",
            ]
        elif is_stat:
            category = "Peak / Unexpected Daytime Spike"
            # Spike during daytime could be unusual load (valid campus event) or equipment issue
            if abs_diff >= 35.0:
                phenomenon_type = "Unusual Consumption Spike / Equipment In-Rush"
            else:
                phenomenon_type = "Unusual Operational Load"
            rule_explanation = (
                f"Observed {observed:.1f} kWh at hour {h:02d}:00 exceeded the expected "
                f"median of {baseline:.1f} kWh by +{abs_diff:.1f} kWh (+{pct_diff:.1f}%). "
                f"Surpassed sensitivity threshold of {sensitivity_std}σ (z-score: {z_sc}σ)."
            )
            hypothesis = (
                "Hypothesis: Concurrent operation of high-draw appliances, heavy workshop/lab equipment, "
                "or mechanical compressor short-cycling without proper sequence interlocking. "
                "Recommend verifying sub-meter logs and equipment cycle times."
            )
            investigation_steps = [
                "1. Review workshop, lab, or commercial kitchen schedule for coincident high-draw tasks.",
                "2. Check HVAC compressor staging delay timers (prevent simultaneous motor in-rush).",
                "3. Review maximum demand indicator (kVA) to prevent contractual utility penalties.",
            ]
        elif is_if:
            category = "Multivariate Density Outlier"
            phenomenon_type = "Unsupervised Pattern Anomaly"
            rule_explanation = (
                f"Identified as topological density outlier by Isolation Forest (score: {if_score:.3f}). "
                f"Observed {observed:.1f} kWh at hour {h:02d}:00 deviated from median baseline of {baseline:.1f} kWh "
                f"(+{abs_diff:.1f} kWh, {z_sc}σ)."
            )
            hypothesis = (
                "Hypothesis: Irregular multi-dimensional operational signature (abnormal energy/hour/weekend interaction). "
                "Verify sub-meter logs and equipment cycle schedules."
            )
            investigation_steps = [
                "1. Inspect equipment schedule during this hour.",
                "2. Compare against typical multi-variate profile.",
                "3. Verify sensor telemetry accuracy.",
            ]
        else:
            category = "Peak / Unexpected Daytime Spike"
            phenomenon_type = "Unusual Operational Load"
            rule_explanation = (
                f"Observed {observed:.1f} kWh at hour {h:02d}:00 exceeded the expected "
                f"median of {baseline:.1f} kWh by +{abs_diff:.1f} kWh (+{pct_diff:.1f}%)."
            )
            hypothesis = "Hypothesis: Multi-signal ensemble detection."
            investigation_steps = ["1. Review sub-meter logs for this interval."]

        # Multi-detector method attribution
        methods = []
        if is_stat:
            methods.append("Statistical Median Z-Score")
        if is_ovn:
            methods.append("Nocturnal Schedule Boundary Rule")
        if is_if:
            methods.append("Unsupervised Isolation Forest Outlier")
        if not methods:
            methods.append("Statistical Median Z-Score")
        detection_method_str = " + ".join(methods)

        # Confidence / Evidence-strength score (0.0 to 1.0)
        # Higher score when Z-score is high, excess kWh is large, and Isolation Forest concurs
        base_confidence = min(0.65 + (max(0.0, z_sc) / 10.0), 0.85)
        if is_if:
            base_confidence = min(1.0, base_confidence + 0.12)
        confidence_score = round(base_confidence, 2)

        if confidence_score >= 0.85:
            confidence_label = "High Confidence"
            evidence_strength = (
                f"Strong multi-signal convergence ({confidence_score * 100:.0f}%): "
                f"Z-Score deviation of {z_sc}σ reinforced by {detection_method_str}."
            )
        elif confidence_score >= 0.70:
            confidence_label = "Medium Confidence"
            evidence_strength = (
                f"Moderate evidence ({confidence_score * 100:.0f}%): "
                f"Noticeable +{abs_diff:.1f} kWh breach above historical dispersion (Z-Score: {z_sc}σ)."
            )
        else:
            confidence_label = "Tentative Signal"
            evidence_strength = (
                f"Preliminary indication ({confidence_score * 100:.0f}%): "
                f"Exceeds minimum trigger, but may represent normal operational variance (Z-Score: {z_sc}σ)."
            )

        if is_if and (is_stat or is_ovn):
            rule_explanation += f" Confirmed as geometric outlier by Isolation Forest (score: {if_score})."

        # Determine unique, collision-proof alert ID across facilities and runs
        row_facility = (
            facility_id
            or row.get("facility_id")
            or row.get("building_id")
            or row.get("facility")
            or row.get("building_category")
            or default_facility
        )
        facility_tag = _sanitize_id_token(row_facility)
        run_tag = _sanitize_id_token(run_id)

        id_parts = ["ALT"]
        if facility_tag:
            id_parts.append(facility_tag)
        if run_tag:
            id_parts.append(run_tag)
        id_parts.append(ts.strftime("%Y%m%d%H%M"))
        alert_id = "-".join(id_parts)

        alerts.append(
            {
                "id": alert_id,
                "facility_id": str(row_facility) if row_facility else "",
                "run_id": str(run_id) if run_id else "",
                "timestamp": ts,
                "timestamp_str": ts.strftime("%Y-%m-%d %H:%M"),
                "hour": h,
                "day_name": ts.day_name(),
                "observed_kwh": observed,
                "expected_baseline_kwh": baseline,
                "absolute_diff_kwh": abs_diff,
                "percentage_diff": pct_diff,
                "z_score": z_sc,
                "severity": severity,
                "phenomenon_type": phenomenon_type,
                "category": category,
                "detection_method": detection_method_str,
                "confidence_score": confidence_score,
                "confidence_label": confidence_label,
                "evidence_strength": evidence_strength,
                "rule_explanation": rule_explanation,
                "investigation_hypothesis": hypothesis,
                "recommended_investigation": "\n".join(investigation_steps),
                "isolation_forest_flag": is_if,
                "isolation_forest_score": if_score,
                "status": "New",
                "ml_disclaimer": (
                    "Note: The Isolation Forest outlier score measures topological density distance in feature space, "
                    "NOT a physical probability of machine failure. Physical equipment diagnosis requires direct sensor logs."
                ),
            }
        )

    # Sort alerts in reverse chronological order
    alerts = sorted(alerts, key=lambda a: a["timestamp"], reverse=True)

    summary = {
        "total_anomalies": len(alerts),
        "critical_severity": sum(1 for a in alerts if a["severity"] == "Critical"),
        "high_severity": sum(1 for a in alerts if a["severity"] == "High"),
        "medium_severity": sum(1 for a in alerts if a["severity"] == "Medium"),
        "low_severity": sum(1 for a in alerts if a["severity"] == "Low"),
        "overnight_waste_count": sum(1 for a in alerts if a["category"] == "Overnight Baseload Shift"),
        "isolation_forest_count": sum(1 for a in alerts if a.get("isolation_forest_flag")),
        "potential_waste_kwh": round(
            sum(a["absolute_diff_kwh"] for a in alerts if a["phenomenon_type"] == "Potential Energy Wastage"),
            1,
        ),
        "total_excess_kwh": round(sum(a["absolute_diff_kwh"] for a in alerts), 1),
    }

    return {
        "alerts": alerts,
        "flagged_df": merged,
        "summary": summary,
    }
