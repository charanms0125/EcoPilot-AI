"""
EcoPilot AI: Savings Calculation & What-If Simulation Engine
Provides rigorous input-validated formulas for energy and financial savings,
overlap-safe portfolio calculations, and transparent assumption tracking.
"""

from typing import Dict, Any, List, Optional
import numpy as np


class SavingsEngine:
    """
    Mathematical calculation engine for energy and financial savings.
    Enforces strict physical constraints and prevents unrealistic claims.
    """

    DEFAULT_TARIFF_INR: float = 8.50  # Typical commercial/institutional tariff in India (₹/kWh)

    @staticmethod
    def calculate_single_saving(
        baseline_eligible_kwh: float,
        reduction_percentage: float,
        tariff_inr_per_kwh: float,
        action_name: str = "Proposed Energy Efficiency Action",
        hours_active: int = 1,
        verified: bool = False,
    ) -> Dict[str, Any]:
        """
        Calculate energy and cost savings for a single conservation measure.

        Formula:
            reduction_fraction = reduction_percentage / 100.0
            energy_saved_kwh = baseline_eligible_kwh * reduction_fraction
            cost_savings_inr = energy_saved_kwh * tariff_inr_per_kwh

        Validations:
        - baseline_eligible_kwh must be non-negative.
        - reduction_percentage must be between 0.0 and 100.0%.
        - tariff_inr_per_kwh must be strictly positive (> 0).
        """
        # 1. Input Validations
        if baseline_eligible_kwh < 0:
            raise ValueError(f"Baseline consumption cannot be negative. Provided: {baseline_eligible_kwh}")

        if reduction_percentage < 0.0 or reduction_percentage > 100.0:
            raise ValueError(
                f"Reduction percentage must be between 0.0% and 100.0%. Provided: {reduction_percentage}%"
            )

        if tariff_inr_per_kwh <= 0:
            raise ValueError(
                f"Electricity tariff must be strictly positive (> 0 ₹/kWh). Provided: {tariff_inr_per_kwh}"
            )

        # 2. Computations
        reduction_fraction = reduction_percentage / 100.0
        energy_saved_kwh = baseline_eligible_kwh * reduction_fraction
        proposed_consumption_kwh = baseline_eligible_kwh - energy_saved_kwh

        baseline_cost_inr = baseline_eligible_kwh * tariff_inr_per_kwh
        proposed_cost_inr = proposed_consumption_kwh * tariff_inr_per_kwh
        cost_savings_inr = energy_saved_kwh * tariff_inr_per_kwh

        return {
            "action_name": action_name,
            "baseline_consumption_kwh": round(float(baseline_eligible_kwh), 2),
            "baseline_cost_inr": round(float(baseline_cost_inr), 2),
            "proposed_consumption_kwh": round(float(proposed_consumption_kwh), 2),
            "proposed_cost_inr": round(float(proposed_cost_inr), 2),
            "energy_saved_kwh": round(float(energy_saved_kwh), 2),
            "cost_savings_inr": round(float(cost_savings_inr), 2),
            "reduction_percentage": round(float(reduction_percentage), 1),
            "tariff_inr_per_kwh": round(float(tariff_inr_per_kwh), 2),
            "hours_active": hours_active,
            "status": "Verified Savings" if verified else "Estimated Savings",
            "assumptions": [
                f"Constant electricity tariff of ₹{tariff_inr_per_kwh:.2f}/kWh applied over active duration.",
                f"Action achieves projected {reduction_percentage:.1f}% reduction on eligible slice.",
                "Non-energy comfort standards and baseline operational safety limits are maintained.",
                "Savings represent estimates until sub-meter post-implementation verification.",
            ],
            "limitations": [
                "Does not account for peak demand surcharge penalties or power factor incentives unless explicitly configured.",
                "Realized savings depend on occupant compliance and maintenance of setpoint schedules.",
            ],
        }

    @staticmethod
    def calculate_portfolio_savings(
        recommendations: List[Dict[str, Any]],
        overall_baseline_kwh: float,
        tariff_inr_per_kwh: float,
    ) -> Dict[str, Any]:
        """
        Calculate cumulative savings across multiple actions accounting for overlapping effects.

        Never directly sums percentage reductions to prevent impossible (>100%) or double-counted claims.
        Uses sequential compounding / diminishing marginal baseline reduction:
            Effective combined reduction = 1 - product(1 - reduction_fraction_i)
        Caps total combined energy saved at the total eligible baseline.
        """
        if not recommendations:
            return {
                "total_actions": 0,
                "raw_sum_kwh": 0.0,
                "deduplicated_saved_kwh": 0.0,
                "deduplicated_saved_inr": 0.0,
                "effective_reduction_pct": 0.0,
                "overlap_correction_kwh": 0.0,
                "note": "No active recommendations to simulate.",
            }

        if overall_baseline_kwh < 0:
            raise ValueError("Overall baseline consumption cannot be negative.")
        if tariff_inr_per_kwh <= 0:
            raise ValueError("Tariff must be positive.")

        # Compute raw independent sum
        raw_kwh = sum(r.get("estimated_kwh_saving", 0.0) for r in recommendations)

        # Multiplicative interaction model to prevent double-counting
        # E.g. Action A reduces 20%, Action B reduces 15%. Combined reduction is 1 - (1-0.2)*(1-0.15) = 32% (not 35%)
        retention = 1.0
        for r in recommendations:
            # If recommendation specifies individual percentage or estimate
            est_kwh = r.get("estimated_kwh_saving", 0.0)
            if overall_baseline_kwh > 0 and est_kwh > 0:
                frac = min(est_kwh / overall_baseline_kwh, 0.9)
                retention *= (1.0 - frac)

        combined_reduction_fraction = min(1.0 - retention, 0.85)  # Cap at realistic 85% maximum conservation
        deduplicated_kwh = min(raw_kwh, overall_baseline_kwh * combined_reduction_fraction)
        deduplicated_kwh = round(float(deduplicated_kwh), 2)
        overlap_correction = max(0.0, round(float(raw_kwh - deduplicated_kwh), 2))
        deduplicated_inr = round(float(deduplicated_kwh * tariff_inr_per_kwh), 2)

        effective_pct = (
            (deduplicated_kwh / overall_baseline_kwh) * 100.0 if overall_baseline_kwh > 0 else 0.0
        )

        return {
            "total_actions": len(recommendations),
            "overall_baseline_kwh": round(float(overall_baseline_kwh), 2),
            "raw_sum_kwh": round(float(raw_kwh), 2),
            "deduplicated_saved_kwh": deduplicated_kwh,
            "deduplicated_saved_inr": deduplicated_inr,
            "effective_reduction_pct": round(float(effective_pct), 1),
            "overlap_correction_kwh": overlap_correction,
            "tariff_inr_per_kwh": round(float(tariff_inr_per_kwh), 2),
            "note": "Multiplicative overlap discounting applied to prevent double counting.",
        }
