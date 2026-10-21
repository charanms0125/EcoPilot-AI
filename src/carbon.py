"""
EcoPilot AI: Transparent Carbon Calculator & Environmental Impact Module
Computes potential and verified avoided greenhouse gas (GHG) emissions
using strictly documented, official grid emission factors.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime


# Official, peer-reviewed grid emission factor references
OFFICIAL_EMISSION_FACTORS: Dict[str, Dict[str, Any]] = {
    "India (CEA National Weighted Average)": {
        "factor_kg_co2e_per_kwh": 0.716,
        "region": "India (National Grid)",
        "source": "Central Electricity Authority (CEA), CO2 Baseline Database for the Indian Power Sector, User Guide Version 19.0 (2024)",
        "effective_date": "2024-03-31",
        "units": "kg CO2e / kWh",
        "scope": "Scope 2 (Indirect emissions from purchased grid electricity)",
        "notes": "Includes thermal, hydro, nuclear, and grid-connected renewable generation weighted average.",
    },
    "India (CEA Renewable Energy Excluded - Thermal Dominant)": {
        "factor_kg_co2e_per_kwh": 0.912,
        "region": "India (Thermal Generation Baseline)",
        "source": "Central Electricity Authority (CEA), Baseline Database v19.0, Thermal Generation Weighted Average (2024)",
        "effective_date": "2024-03-31",
        "units": "kg CO2e / kWh",
        "scope": "Scope 2 (Operating Margin)",
        "notes": "Reflects marginal thermal generation avoided during peak conservation windows.",
    },
    "United States (EPA eGRID National Average)": {
        "factor_kg_co2e_per_kwh": 0.386,
        "region": "United States (National)",
        "source": "US Environmental Protection Agency (EPA), eGRID2022 Summary Tables (Released 2024)",
        "effective_date": "2024-01-30",
        "units": "kg CO2e / kWh",
        "scope": "Scope 2",
        "notes": "US national annual average grid gross output emission rate.",
    },
    "United Kingdom (DESNZ / DEFRA National Grid)": {
        "factor_kg_co2e_per_kwh": 0.207,
        "region": "United Kingdom (Great Britain)",
        "source": "UK Department for Energy Security and Net Zero (DESNZ) / DEFRA Greenhouse Gas Conversion Factors (2023)",
        "effective_date": "2023-06-07",
        "units": "kg CO2e / kWh",
        "scope": "Scope 2",
        "notes": "UK grid electricity transmission and distribution average factor.",
    },
    "European Union (EEA Average)": {
        "factor_kg_co2e_per_kwh": 0.251,
        "region": "European Union (EU-27)",
        "source": "European Environment Agency (EEA), Greenhouse Gas Emission Intensity of Electricity Generation in Europe (2023)",
        "effective_date": "2023-11-15",
        "units": "kg CO2e / kWh",
        "scope": "Scope 2",
        "notes": "EU-27 consumption-weighted electricity emission intensity.",
    },
}

DEFAULT_FACTOR_KEY = "India (CEA National Weighted Average)"


class CarbonCalculator:
    """
    Transparent, verifiable carbon accounting engine for energy conservation.
    Enforces strict mathematical bounds and clear separation between
    potential estimated savings and verified real-world outcomes.
    """

    def __init__(
        self,
        factor_key: Optional[str] = DEFAULT_FACTOR_KEY,
        custom_factor: Optional[float] = None,
        custom_source: Optional[str] = None,
        custom_region: Optional[str] = None,
        custom_effective_date: Optional[str] = None,
    ):
        """
        Initialize the carbon calculator with a documented grid emission factor.
        """
        self.is_configured = False
        self.factor_kg_co2e_per_kwh: Optional[float] = None
        self.source: str = "Emission factor not configured"
        self.region: str = "Not Specified"
        self.effective_date: str = "Unknown"
        self.units: str = "kg CO2e / kWh"
        self.scope: str = "Scope 2"
        self.notes: str = ""

        if custom_factor is not None:
            if custom_factor <= 0:
                raise ValueError(
                    f"Custom emission factor must be strictly positive (> 0). Provided: {custom_factor}"
                )
            if not custom_source:
                raise ValueError("A documented official source citation is required for custom emission factors.")
            self.factor_kg_co2e_per_kwh = float(custom_factor)
            self.source = custom_source
            self.region = custom_region or "Custom Region"
            self.effective_date = custom_effective_date or datetime.now().strftime("%Y-%m-%d")
            self.is_configured = True
            self.notes = "Custom user-configured emission factor with documented source."
        elif factor_key and factor_key in OFFICIAL_EMISSION_FACTORS:
            ref = OFFICIAL_EMISSION_FACTORS[factor_key]
            self.factor_kg_co2e_per_kwh = float(ref["factor_kg_co2e_per_kwh"])
            self.source = ref["source"]
            self.region = ref["region"]
            self.effective_date = ref["effective_date"]
            self.units = ref["units"]
            self.scope = ref["scope"]
            self.notes = ref["notes"]
            self.is_configured = True
        elif factor_key is None or factor_key == "Not Configured":
            self.is_configured = False
        else:
            raise ValueError(
                f"Unknown emission factor key: '{factor_key}'. "
                f"Available references: {list(OFFICIAL_EMISSION_FACTORS.keys())}"
            )

    def calculate_avoided_emissions(
        self,
        electricity_saved_kwh: float,
        is_verified: bool = False,
        intervention_name: str = "Energy Conservation Intervention",
    ) -> Dict[str, Any]:
        """
        Calculate avoided emissions using the official standard formula:
            avoided_emissions_kg_co2e = electricity_saved_kwh * grid_emission_factor_kg_co2e_per_kwh

        Parameters:
        -----------
        electricity_saved_kwh: float
            Electricity reduction volume (kWh). Must be >= 0.
        is_verified: bool, default False
            True only if computed from physical sub-meter verification.
        intervention_name: str
            Label of the efficiency measure.

        Returns:
        --------
        Dict with carbon metrics, source citations, and clear verification status labels.
        """
        if electricity_saved_kwh < 0:
            raise ValueError(
                f"Electricity saved cannot be negative. Provided: {electricity_saved_kwh} kWh. "
                "Negative values indicate increased consumption, which must be handled through baseline comparison."
            )

        if not self.is_configured or self.factor_kg_co2e_per_kwh is None:
            return {
                "is_configured": False,
                "status_label": "Emission factor not configured",
                "avoided_emissions_kg_co2e": None,
                "avoided_emissions_tonnes_co2e": None,
                "electricity_saved_kwh": round(float(electricity_saved_kwh), 2),
                "factor_kg_co2e_per_kwh": None,
                "source": "Emission factor not configured",
                "region": "Not Configured",
                "effective_date": "N/A",
                "is_verified": False,
                "message": (
                    "Emission factor not configured. To calculate avoided greenhouse gas emissions, "
                    "please select an official grid emission factor from the configuration settings."
                ),
                "assumptions": ["No official emission factor currently configured."],
                "limitations": ["Environmental impact cannot be quantified without verified grid intensity."],
            }

        avoided_kg = round(float(electricity_saved_kwh * self.factor_kg_co2e_per_kwh), 2)
        avoided_tonnes = round(avoided_kg / 1000.0, 4)

        status_label = (
            "Verified Avoided Emissions (Measured Sub-Meter)"
            if is_verified
            else "Potential Avoided Emissions (Estimated Model)"
        )

        assumptions = [
            f"Grid emission factor of {self.factor_kg_co2e_per_kwh:.3f} kg CO2e/kWh applied uniformly.",
            f"Factor Source: {self.source}.",
            f"Geographic Region: {self.region} (Reporting Date: {self.effective_date}).",
            "Electricity reduction translates directly to marginal grid thermal displacement.",
        ]

        limitations = [
            "Does not account for hourly marginal grid variability unless dynamic ToD emission factor is configured.",
            (
                "Result is an unverified model estimate subject to post-implementation audit."
                if not is_verified
                else "Realized avoided emissions verified via before-and-after baseline tracking."
            ),
        ]

        # Tangible environmental equivalence benchmarks (strictly grounded in EPA formulas)
        # 1 mature tree absorbs ~21.77 kg CO2/year (EPA GHG Equivalencies Calculator)
        tree_years_equivalent = round(avoided_kg / 21.77, 1) if avoided_kg > 0 else 0.0
        # 1 passenger car emits ~0.192 kg CO2/km (EPA average passenger vehicle)
        km_driven_equivalent = round(avoided_kg / 0.192, 1) if avoided_kg > 0 else 0.0

        return {
            "is_configured": True,
            "intervention_name": intervention_name,
            "status_label": status_label,
            "is_verified": is_verified,
            "electricity_saved_kwh": round(float(electricity_saved_kwh), 2),
            "factor_kg_co2e_per_kwh": self.factor_kg_co2e_per_kwh,
            "avoided_emissions_kg_co2e": avoided_kg,
            "avoided_emissions_tonnes_co2e": avoided_tonnes,
            "units_factor": self.units,
            "units_emissions": "kg CO2e",
            "source": self.source,
            "region": self.region,
            "effective_date": self.effective_date,
            "scope": self.scope,
            "equivalencies": {
                "tree_seedlings_grown_for_10_years": tree_years_equivalent,
                "avoided_passenger_car_km": km_driven_equivalent,
            },
            "assumptions": assumptions,
            "limitations": limitations,
        }

    @staticmethod
    def get_available_factors() -> List[str]:
        """Return list of supported official emission factor keys."""
        return list(OFFICIAL_EMISSION_FACTORS.keys())

    @staticmethod
    def get_factor_metadata(factor_key: str) -> Optional[Dict[str, Any]]:
        """Return complete metadata for a specific emission factor key."""
        return OFFICIAL_EMISSION_FACTORS.get(factor_key)
