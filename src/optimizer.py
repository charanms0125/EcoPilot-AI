"""
EcoPilot AI: Energy & Tariff Optimizer
Analyzes Time-of-Day (ToD) tariff rate structures, flexible load shifting,
and peak-demand shaving opportunities for campus and commercial facilities.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd


# Typical commercial / educational Time-of-Day (ToD) tariff structure in India
DEFAULT_TOD_SCHEDULE = {
    # Off-peak / Solar generation window: 10:00 to 16:00 and night 23:00 to 06:00
    "off_peak_tariff_inr": 5.50,
    # Normal hours: 06:00 to 10:00 and 16:00 to 18:00
    "normal_tariff_inr": 8.50,
    # Peak evening grid strain: 18:00 to 23:00
    "peak_tariff_inr": 12.50,
    "peak_hours": [18, 19, 20, 21, 22],
    "off_peak_hours": [23, 0, 1, 2, 3, 4, 5, 11, 12, 13, 14],
}

FLEXIBLE_LOAD_PROFILES = {
    "Overhead Water Tank Pumping": {
        "typical_kwh_per_cycle": 24.0,
        "duration_hours": 3,
        "default_active_hour": 19,  # Evening peak
        "recommended_shift_hour": 12,  # Solar surplus midday
        "description": "Shift water lifting pumps from evening peak grid to solar peak midday.",
    },
    "Hostel Laundry Operations": {
        "typical_kwh_per_cycle": 18.0,
        "duration_hours": 4,
        "default_active_hour": 20,
        "recommended_shift_hour": 14,
        "description": "Shift institutional washers and dryers to off-peak daytime slots.",
    },
    "Campus EV / Battery Fleet Charging": {
        "typical_kwh_per_cycle": 35.0,
        "duration_hours": 5,
        "default_active_hour": 18,
        "recommended_shift_hour": 1,
        "description": "Shift electric maintenance buggy & shuttle charging to midnight off-peak.",
    },
    "Central AC Pre-Cooling": {
        "typical_kwh_per_cycle": 20.0,
        "duration_hours": 2,
        "default_active_hour": 17,
        "recommended_shift_hour": 9,
        "description": "Pre-cool auditorium / lecture halls during normal rates before peak afternoon tariff.",
    },
}


def get_hourly_tariff(hour: int, tod_config: Optional[Dict[str, Any]] = None) -> float:
    """Return applicable tariff (₹/kWh) for a specific hour of day."""
    cfg = tod_config or DEFAULT_TOD_SCHEDULE
    if hour in cfg["peak_hours"]:
        return cfg["peak_tariff_inr"]
    elif hour in cfg["off_peak_hours"]:
        return cfg["off_peak_tariff_inr"]
    return cfg["normal_tariff_inr"]


def simulate_load_shifting(
    load_name: str,
    shift_kwh: float,
    current_hour: int,
    target_hour: int,
    days: int = 30,
    tod_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Simulate shifting a flexible electrical load from a high-tariff to a low-tariff window.

    Energy consumption remains net-neutral, but cost drops significantly due to differential pricing.
    """
    cfg = tod_config or DEFAULT_TOD_SCHEDULE

    if shift_kwh <= 0:
        raise ValueError("Shiftable load must be strictly positive (>0 kWh).")
    if not (0 <= current_hour <= 23 and 0 <= target_hour <= 23):
        raise ValueError("Hours must be between 0 and 23.")

    current_tariff = get_hourly_tariff(current_hour, cfg)
    target_tariff = get_hourly_tariff(target_hour, cfg)

    # Cost per cycle
    current_cost_per_cycle = shift_kwh * current_tariff
    target_cost_per_cycle = shift_kwh * target_tariff
    daily_saving_inr = current_cost_per_cycle - target_cost_per_cycle

    # Projected monthly / multi-day saving
    total_saving_inr = daily_saving_inr * days
    total_shifted_kwh = shift_kwh * days

    tariff_spread = current_tariff - target_tariff

    return {
        "load_name": load_name,
        "shift_kwh_per_cycle": round(shift_kwh, 2),
        "current_hour": current_hour,
        "current_hour_str": f"{current_hour:02d}:00",
        "current_tariff_inr": current_tariff,
        "target_hour": target_hour,
        "target_hour_str": f"{target_hour:02d}:00",
        "target_tariff_inr": target_tariff,
        "tariff_differential_inr": round(tariff_spread, 2),
        "days": days,
        "total_shifted_kwh": round(total_shifted_kwh, 2),
        "daily_saving_inr": round(daily_saving_inr, 2),
        "projected_savings_inr": round(total_saving_inr, 2),
        "is_profitable": daily_saving_inr > 0,
        "explanation": (
            f"Moving {shift_kwh:.1f} kWh of {load_name} from {current_hour:02d}:00 "
            f"(₹{current_tariff:.2f}/kWh) to {target_hour:02d}:00 (₹{target_tariff:.2f}/kWh) "
            f"saves ₹{tariff_spread:.2f}/kWh, generating ₹{total_saving_inr:.2f} over {days} days."
        ),
    }


def analyze_peak_demand_shaving(
    df: pd.DataFrame,
    contract_demand_kw: float = 75.0,
    penalty_rate_inr_per_kw: float = 450.0,
) -> Dict[str, Any]:
    """
    Detect hours exceeding registered contract demand threshold (kW or kWh/h)
    and estimate peak surcharge risk.
    """
    if "energy_kwh" not in df.columns:
        raise ValueError("DataFrame missing 'energy_kwh' column.")

    breaches = df[df["energy_kwh"] > contract_demand_kw].copy()
    num_breaches = len(breaches)
    max_draw = float(df["energy_kwh"].max())
    excess_peak_kw = max(0.0, max_draw - contract_demand_kw)

    estimated_penalty_inr = excess_peak_kw * penalty_rate_inr_per_kw

    return {
        "contract_demand_kw": contract_demand_kw,
        "max_draw_recorded_kw": round(max_draw, 2),
        "excess_peak_kw": round(excess_peak_kw, 2),
        "breach_hour_count": num_breaches,
        "penalty_rate_inr_per_kw": penalty_rate_inr_per_kw,
        "estimated_monthly_demand_penalty_inr": round(estimated_penalty_inr, 2),
        "risk_level": "High" if excess_peak_kw > 10 else ("Medium" if excess_peak_kw > 0 else "Low"),
    }
