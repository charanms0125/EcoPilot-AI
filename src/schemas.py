"""
EcoPilot AI: Strongly-Typed Domain Schemas
Defines strict Pydantic models for data quality reports, anomaly alerts,
prioritized recommendations, forecasts, and savings verifications.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class BaseDomainModel(BaseModel):
    """Base class for EcoPilot domain schemas with serialization helpers."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to standard Python dictionary."""
        return self.model_dump()


# ==============================================================================
# 1. Telemetry Ingestion & Data Quality Schemas
# ==============================================================================

class DataSummarySchema(BaseDomainModel):
    """Statistical summary of validated telemetry consumption."""

    min_kwh: float = Field(default=0.0, description="Minimum observed hourly consumption in kWh.")
    max_kwh: float = Field(default=0.0, description="Maximum observed hourly consumption in kWh.")
    mean_kwh: float = Field(default=0.0, description="Mean hourly consumption in kWh.")
    median_kwh: float = Field(default=0.0, description="Median hourly consumption in kWh.")
    total_consumption_kwh: float = Field(default=0.0, description="Sum of all consumption in kWh.")


class DataQualityReportSchema(BaseDomainModel):
    """Comprehensive data quality audit report for telemetry ingestion."""

    timestamp_generated: str = Field(description="ISO timestamp when quality audit was executed.")
    raw_row_count: int = Field(default=0, description="Number of rows in original uploaded file.")
    cleaned_row_count: int = Field(default=0, description="Number of validated rows after cleansing.")
    is_valid: bool = Field(default=True, description="Whether the dataset satisfies operational criteria.")
    error_message: Optional[str] = Field(default=None, description="Detailed error description if invalid.")
    health_score_pct: float = Field(default=100.0, description="Overall telemetry data health score (0-100%).")
    detected_timezone: str = Field(default="Naive (Local)", description="Detected timezone representation.")
    sampling_frequency: str = Field(default="Hourly", description="Detected mode telemetry frequency.")
    sampling_frequency_minutes: float = Field(default=60.0, description="Median delta between readings in minutes.")
    is_regular_interval: bool = Field(default=True, description="Whether telemetry intervals are uniformly spaced.")
    irregular_intervals_detected: int = Field(default=0, description="Count of timestamps deviating from mode frequency.")
    negative_values_found: int = Field(default=0, description="Count of negative readings identified.")
    negative_values_clipped: int = Field(default=0, description="Count of negative readings sanitized to zero.")
    missing_values_imputed: int = Field(default=0, description="Count of NaN readings imputed.")
    duplicates_removed: int = Field(default=0, description="Count of duplicate timestamps dropped.")
    total_hours_spanned: float = Field(default=0.0, description="Total hours between min and max timestamp.")
    date_range_start: Optional[str] = Field(default=None, description="Starting timestamp of valid range.")
    date_range_end: Optional[str] = Field(default=None, description="Ending timestamp of valid range.")
    columns_found: List[str] = Field(default_factory=list, description="Original headers detected in upload.")
    issues_detected: List[str] = Field(default_factory=list, description="List of quality defects observed.")
    repairs_applied: List[str] = Field(default_factory=list, description="List of automated corrections applied.")
    data_summary: Dict[str, Any] = Field(default_factory=dict, description="Basic summary metrics.")


# ==============================================================================
# 2. Anomaly Detection Schemas
# ==============================================================================

class AlertSchema(BaseDomainModel):
    """Individual explainable energy anomaly alert."""

    id: str = Field(description="Unique collision-proof alert identifier.")
    facility_id: str = Field(default="", description="Facility or building identifier.")
    run_id: str = Field(default="", description="Execution run identifier.")
    timestamp: Any = Field(description="Timestamp of anomalous observation.")
    timestamp_str: str = Field(description="Human-readable timestamp string.")
    hour: int = Field(description="Hour of day (0-23).")
    day_name: str = Field(description="Day of week name.")
    observed_kwh: float = Field(description="Observed energy consumption in kWh.")
    expected_baseline_kwh: float = Field(description="Expected median baseline in kWh.")
    absolute_diff_kwh: float = Field(description="Absolute surplus above baseline in kWh.")
    percentage_diff: float = Field(description="Percentage surplus above baseline.")
    z_score: float = Field(description="Standard deviation deviation score.")
    severity: str = Field(description="Severity tier: Critical, High, Medium, Low.")
    phenomenon_type: str = Field(description="Distinction: Potential Wastage vs Unusual Consumption.")
    category: str = Field(description="Operational category (e.g., Overnight Baseload Shift).")
    detection_method: str = Field(description="Detectors flagging this anomaly.")
    confidence_score: float = Field(description="Multi-detector confidence score (0.0 to 1.0).")
    confidence_label: str = Field(description="Confidence rating: High, Medium, Tentative.")
    evidence_strength: str = Field(description="Narrative explanation of evidence strength.")
    rule_explanation: str = Field(description="Transparent rule and threshold explanation.")
    investigation_hypothesis: str = Field(description="Root cause hypothesis for facility audit.")
    recommended_investigation: str = Field(description="Actionable physical audit checklist.")
    isolation_forest_flag: bool = Field(default=False, description="Whether flagged by Isolation Forest.")
    isolation_forest_score: float = Field(default=0.0, description="Isolation Forest decision score.")
    status: str = Field(default="New", description="Workflow status: New, Acknowledged, Investigating, Resolved.")
    ml_disclaimer: str = Field(default="", description="Ethical machine learning guardrail disclaimer.")


class AnomalySummarySchema(BaseDomainModel):
    """Aggregate summary of anomaly detection execution."""

    total_anomalies: int = Field(default=0, description="Total count of anomalies detected.")
    critical_severity: int = Field(default=0, description="Count of Critical severity alerts.")
    high_severity: int = Field(default=0, description="Count of High severity alerts.")
    medium_severity: int = Field(default=0, description="Count of Medium severity alerts.")
    low_severity: int = Field(default=0, description="Count of Low severity alerts.")
    overnight_waste_count: int = Field(default=0, description="Count of off-hours baseload anomalies.")
    isolation_forest_count: int = Field(default=0, description="Count of anomalies confirmed by Isolation Forest.")
    potential_waste_kwh: float = Field(default=0.0, description="Total kWh attributed to potential wastage.")
    total_excess_kwh: float = Field(default=0.0, description="Total surplus kWh across all anomalies.")


# ==============================================================================
# 3. Energy Forecasting Schemas
# ==============================================================================

class ForecastRecordSchema(BaseDomainModel):
    """Hourly forecast prediction record."""

    timestamp: Any = Field(description="Forecast timestamp.")
    hour: int = Field(description="Hour of day (0-23).")
    day_name: str = Field(description="Day of week name.")
    forecast_kwh: float = Field(description="Predicted energy consumption in kWh.")
    lower_bound_kwh: float = Field(description="Calibrated lower empirical confidence bound.")
    upper_bound_kwh: float = Field(description="Calibrated upper empirical confidence bound.")
    confidence_level: str = Field(description="Confidence interval description and nominal coverage.")


class ForecastMetricsSchema(BaseDomainModel):
    """Evaluation metrics for energy forecasting model."""

    selected_model: str = Field(description="Winning model chosen based on lowest validation MAE.")
    selected_mae: float = Field(default=0.0, description="Test MAE of winning model.")
    selected_rmse: float = Field(default=0.0, description="Test RMSE of winning model.")
    rf_mae: float = Field(default=0.0, description="Random Forest test MAE.")
    rf_rmse: float = Field(default=0.0, description="Random Forest test RMSE.")
    rf_r2: float = Field(default=0.0, description="Random Forest test R².")
    baseline_mae: float = Field(default=0.0, description="Previous-day persistence test MAE.")
    improvement_pct: float = Field(default=0.0, description="Percentage MAE improvement over persistence.")
    prediction_interval: Dict[str, Any] = Field(default_factory=dict, description="Calibrated interval metrics.")


class ForecastResultSchema(BaseDomainModel):
    """Complete output package of the forecasting pipeline."""

    preferred_model_name: str = Field(description="Winning forecasting model.")
    selection_criterion: str = Field(default="Lowest Validation MAE")
    horizon_hours: int = Field(default=24)
    interval: str = Field(default="1 Hour")
    metrics: Dict[str, Any] = Field(default_factory=dict)
    feature_importances: Dict[str, float] = Field(default_factory=dict)
    interval_offsets: tuple = Field(default=(-5.0, 5.0))
    limitations: List[str] = Field(default_factory=list)


# ==============================================================================
# 4. Recommendation & Decision Lifecycle Schemas
# ==============================================================================

class RecommendationSchema(BaseDomainModel):
    """Actionable energy conservation measure recommendation."""

    id: str = Field(description="Unique recommendation ID.")
    scenario: str = Field(default="general", description="Scenario trigger name.")
    created_at: str = Field(description="Creation ISO timestamp.")
    title: str = Field(description="Clear title of the conservation measure.")
    category: str = Field(description="System category (HVAC, Lighting, Baseload, Tariff).")
    severity: str = Field(default="Medium", description="Severity or impact tier.")
    evidence: str = Field(description="Empirical telemetry evidence supporting this measure.")
    suggested_action: str = Field(description="Physical step-by-step implementation guide.")
    assumptions: str = Field(description="Operational and thermal assumptions made.")
    estimated_kwh_saving: float = Field(description="Projected annual energy reduction in kWh.")
    estimated_inr_saving: float = Field(description="Projected annual financial reduction in INR.")
    status: str = Field(default="Pending", description="Lifecycle state: Pending, Approved, In Progress, Completed, Rejected.")
    updated_at: str = Field(description="Last update timestamp.")
    notes: str = Field(default="", description="Operator or auditor notes.")
    priority_score: int = Field(default=50, description="Deterministic priority score (0-100).")
    implementation_effort: str = Field(default="Medium", description="Effort level: Low, Medium, High.")
    operational_risk: str = Field(default="Low", description="Risk to occupant comfort or process continuity.")
    estimated_avoided_kg_co2e: float = Field(default=0.0, description="Projected avoided greenhouse gas emissions.")
    recommended_next_action: str = Field(default="", description="Immediate next action for facilities team.")
    facility_id: str = Field(default="", description="Associated facility identifier.")
    run_id: str = Field(default="", description="Associated execution run ID.")


class AuditLogSchema(BaseDomainModel):
    """Audit log entry capturing state transitions."""

    id: Optional[int] = Field(default=None, description="Audit entry ID.")
    rec_id: str = Field(description="Associated recommendation ID.")
    old_status: Optional[str] = Field(default=None, description="Previous lifecycle state.")
    new_status: str = Field(description="New lifecycle state.")
    changed_at: str = Field(description="Transition timestamp.")
    user_note: Optional[str] = Field(default=None, description="User or operator reasoning for transition.")


# ==============================================================================
# 5. Before-and-After Verification Schemas
# ==============================================================================

class WeatherNormalizationAssumptionsSchema(BaseDomainModel):
    """Documented weather normalization assumptions and coefficients."""

    is_weather_adjusted: bool = Field(default=False, description="Whether thermal normalization was applied.")
    temperature_column: Optional[str] = Field(default=None, description="Detected ambient temperature column.")
    baseline_avg_temp_c: Optional[float] = Field(default=None, description="Pre-intervention mean temperature.")
    post_avg_temp_c: Optional[float] = Field(default=None, description="Post-intervention mean temperature.")
    temperature_delta_c: float = Field(default=0.0, description="Ambient temperature change in °C.")
    temperature_sensitivity_kwh_per_c: float = Field(default=0.0, description="Thermal cooling load response coefficient.")
    sensitivity_estimation_method: str = Field(default="None", description="OLS regression, benchmark, or user-configured.")
    weather_adjustment_kwh: float = Field(default=0.0, description="Total weather adjustment added to counterfactual.")
    assumptions_documentation: List[str] = Field(default_factory=list, description="Narrative list of documented assumptions.")


class VerificationResultSchema(BaseDomainModel):
    """Complete before-and-after realized savings verification evaluation."""

    id: str = Field(description="Unique verification record identifier.")
    rec_id: str = Field(default="", description="Linked recommendation identifier.")
    intervention_name: str = Field(description="Title of conservation measure evaluated.")
    intervention_start_date: str = Field(description="Intervention start timestamp.")
    baseline_period_start: str = Field(description="Baseline start timestamp.")
    baseline_period_end: str = Field(description="Baseline end timestamp.")
    post_period_start: str = Field(description="Evaluation post period start timestamp.")
    post_period_end: str = Field(description="Evaluation post period end timestamp.")
    baseline_hours: int = Field(description="Count of baseline observation hours.")
    post_hours: int = Field(description="Count of post-intervention observation hours.")
    expected_savings_kwh: float = Field(description="Original ex-ante projected savings in kWh.")
    expected_savings_inr: float = Field(description="Original ex-ante projected savings in INR.")
    observed_consumption_kwh: float = Field(description="Actual post-period consumption measured.")
    baseline_counterfactual_kwh: float = Field(description="Expected consumption if no intervention had occurred.")
    realized_savings_kwh: float = Field(description="Realized energy savings in kWh.")
    realized_savings_inr: float = Field(description="Realized cost savings in INR.")
    weather_adjusted_savings_kwh: float = Field(description="Weather-normalized realized savings in kWh.")
    realization_rate_pct: float = Field(description="Realization percentage vs ex-ante target.")
    verification_status: str = Field(description="Status: Target Met / Exceeded, Partial Savings, Insufficient data, etc.")
    verified_avoided_kg_co2e: float = Field(default=0.0, description="Verified avoided greenhouse gas emissions.")
    adjustment_method: str = Field(description="Counterfactual modeling methodology.")
    tariff_inr_per_kwh: float = Field(default=8.50, description="Applied tariff rate.")
    notes: str = Field(default="", description="Verification notes.")
    disclaimers: List[str] = Field(default_factory=list, description="Causal humility and sensor disclaimers.")
    weather_normalization_assumptions: WeatherNormalizationAssumptionsSchema = Field(
        default_factory=WeatherNormalizationAssumptionsSchema,
        description="Detailed assumptions metadata.",
    )
