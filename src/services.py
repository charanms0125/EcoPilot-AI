"""
EcoPilot AI: Service Layer (Business Logic Orchestration)
Orchestrates domain operations across data ingestion, analytics, recommendations,
simulations, verification, and administrative lifecycle workflows.
Decouples Streamlit dashboard rendering from computational and transactional logic.
"""

from typing import List, Dict, Any, Optional, Tuple, Union
import io
import pandas as pd
import numpy as np

from src.data_generator import (
    generate_energy_dataset,
    validate_uploaded_csv,
    generate_data_quality_report,
    get_sample_csv_content,
    BUILDING_PROFILES,
    SCENARIOS,
)
from src.anomaly_detection import detect_anomalies
from src.forecasting import (
    train_and_evaluate_forecasting,
    predict_next_24_hours,
)
from src.agent import EcoPilotAgent
from src.savings import SavingsEngine
from src.optimizer import (
    simulate_load_shifting,
    analyze_peak_demand_shaving,
    DEFAULT_TOD_SCHEDULE,
    FLEXIBLE_LOAD_PROFILES,
)
from src.carbon import CarbonCalculator, DEFAULT_FACTOR_KEY
from src.verification import SavingsVerifier
from src.repositories import (
    RecommendationRepository,
    AlertRepository,
    VerificationRepository,
    SimulationRepository,
    DatasetUploadRepository,
    DatabaseAdminRepository,
)
from src.auth import Role, Permission, check_permission, require_permission, get_current_role
from src.config import get_config


class EnergyDataService:
    """Service handling telemetry validation, quality inspection, and synthetic synthesis."""

    @staticmethod
    def load_and_validate_csv(
        file_or_df: Optional[Union[pd.DataFrame, io.BytesIO, io.StringIO, str]] = None,
        filename: str = "uploaded_file.csv",
        db_path: Optional[str] = None,
        resample_sub_hourly: bool = False,
        file_content_or_df: Optional[Union[pd.DataFrame, io.BytesIO, io.StringIO, str]] = None,
        record_upload_log: bool = True,
        **kwargs,
    ) -> Tuple[bool, Optional[str], Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Ingest, validate, sanitize, and audit an uploaded telemetry CSV.
        Logs upload audit record into SQLite repository if valid.
        """
        target_input = file_or_df if file_or_df is not None else file_content_or_df
        try:
            if isinstance(target_input, pd.DataFrame):
                raw_df = target_input
            else:
                raw_df = pd.read_csv(target_input)
        except Exception as e:
            err = f"Failed to parse CSV file: {str(e)}"
            empty_df = pd.DataFrame()
            report = generate_data_quality_report(empty_df, None, err)
            return False, err, None, report

        is_valid, err_msg, cleaned_df = validate_uploaded_csv(raw_df, resample_sub_hourly=resample_sub_hourly)
        quality_report = generate_data_quality_report(raw_df, cleaned_df, err_msg)

        if is_valid and cleaned_df is not None and record_upload_log:
            try:
                DatasetUploadRepository.log_upload(
                    filename=filename,
                    row_count=len(cleaned_df),
                    date_start=str(cleaned_df["timestamp"].min()),
                    date_end=str(cleaned_df["timestamp"].max()),
                    is_valid=True,
                    quality_report=quality_report,
                    db_path=db_path,
                )
            except Exception:
                pass

        return is_valid, err_msg, cleaned_df, quality_report

    @classmethod
    def get_or_generate_dataset(
        cls,
        scenario: str = "normal",
        scenario_name: Optional[str] = None,
        building_category: str = "Academic / Lecture Hall Complex",
        days: int = 60,
        random_seed: int = 42,
    ) -> pd.DataFrame:
        scen = scenario_name or scenario
        return cls.generate_scenario_dataset(
            scenario_name=scen,
            building_category=building_category,
            days=days,
            random_seed=random_seed,
        )

    @staticmethod
    def generate_scenario_dataset(
        scenario_name: str = "normal",
        building_category: str = "Academic / Lecture Hall Complex",
        days: int = 60,
        random_seed: int = 42,
    ) -> pd.DataFrame:
        """Synthesize deterministic telemetry dataset matching scenario profile."""
        return generate_energy_dataset(
            days=days,
            building_category=building_category,
            scenario=scenario_name,
            random_seed=random_seed,
        )

    @staticmethod
    def get_sample_csv() -> str:
        """Retrieve pre-formatted downloadable sample CSV schema."""
        return get_sample_csv_content()


class AnalyticsService:
    """Service orchestrating explainable anomaly detection and multi-model energy forecasting."""

    @staticmethod
    def run_anomaly_detection(
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
        persist_alerts: bool = True,
        db_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute anomaly detection and optionally persist alerts to repository."""
        results = detect_anomalies(
            df=df,
            sensitivity_std=sensitivity_std,
            min_absolute_diff_kwh=min_absolute_diff_kwh,
            use_isolation_forest=use_isolation_forest,
            iforest_contamination=iforest_contamination,
            facility_id=facility_id,
            run_id=run_id,
            baseline_df=baseline_df,
            baseline_start_date=baseline_start_date,
            baseline_end_date=baseline_end_date,
        )

        if persist_alerts and results.get("alerts"):
            try:
                AlertRepository.save_all(results["alerts"], db_path=db_path)
            except Exception:
                pass

        return results

    @staticmethod
    def run_forecasting_pipeline(
        df: pd.DataFrame,
        test_hours: int = 72,
        val_hours: int = 48,
        random_state: int = 42,
    ) -> Dict[str, Any]:
        """Execute multi-model chronological forecasting evaluation."""
        return train_and_evaluate_forecasting(
            df=df,
            test_hours=test_hours,
            val_hours=val_hours,
            random_state=random_state,
        )

    @staticmethod
    def generate_24h_forecast(
        model: Any,
        df: pd.DataFrame,
        test_rmse: float = 3.5,
        interval_offsets: Optional[Tuple[float, float]] = None,
        empirical_coverage_pct: float = 90.0,
        min_forecast_floor: Optional[float] = None,
    ) -> pd.DataFrame:
        """Generate multi-step 24-hour future forecast starting from last timestamp."""
        return predict_next_24_hours(
            model=model,
            df=df,
            test_rmse=test_rmse,
            interval_offsets=interval_offsets,
            empirical_coverage_pct=empirical_coverage_pct,
            min_forecast_floor=min_forecast_floor,
        )


class RecommendationService:
    """Service governing AI recommendation synthesis, prioritization, and lifecycle state machine."""

    @staticmethod
    def generate_recommendations(
        agent: EcoPilotAgent,
        anomaly_results: Dict[str, Any],
        forecast_results: Optional[Dict[str, Any]] = None,
        scenario_name: str = "general",
        building_category: str = "Academic / Lecture Hall Complex",
        persist: bool = True,
        db_path: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Synthesize prioritized, evidence-backed recommendations."""
        recs = agent.analyze_and_generate_recommendations(
            anomaly_results=anomaly_results,
            forecast_results=forecast_results,
            scenario_name=scenario_name,
            building_category=building_category,
        )
        if persist and recs:
            try:
                RecommendationRepository.save_all(recs, db_path=db_path)
            except Exception:
                pass
        return recs

    @staticmethod
    def approve_recommendation(
        rec_id: str,
        note: str = "Approved in dashboard",
        caller_role: Optional[Role | str] = None,
        db_path: Optional[str] = None,
        operator: Optional[str] = None,
        notes: Optional[str] = None,
        **kwargs,
    ) -> bool:
        """Authorize an energy conservation measure (requires Approver or Administrator role)."""
        final_note = notes or note
        if operator and "by" not in final_note:
            final_note = f"{final_note} (by {operator})"
        return RecommendationRepository.update_status(
            rec_id=rec_id,
            new_status="Approved",
            user_note=final_note,
            caller_role=caller_role,
            db_path=db_path,
        )

    @staticmethod
    def reject_recommendation(
        rec_id: str,
        note: str = "Rejected by operator",
        caller_role: Optional[Role | str] = None,
        db_path: Optional[str] = None,
        operator: Optional[str] = None,
        notes: Optional[str] = None,
        **kwargs,
    ) -> bool:
        """Reject an energy conservation measure (requires Approver or Administrator role)."""
        final_note = notes or note
        if operator and "by" not in final_note:
            final_note = f"{final_note} (by {operator})"
        return RecommendationRepository.update_status(
            rec_id=rec_id,
            new_status="Rejected",
            user_note=final_note,
            caller_role=caller_role,
            db_path=db_path,
        )

    @staticmethod
    def complete_recommendation(
        rec_id: str,
        note: str = "Implementation verified on site",
        caller_role: Optional[Role | str] = None,
        db_path: Optional[str] = None,
        operator: Optional[str] = None,
        notes: Optional[str] = None,
        **kwargs,
    ) -> bool:
        """Mark an implemented measure as Completed (requires Approver or Administrator role)."""
        final_note = notes or note
        if operator and "by" not in final_note:
            final_note = f"{final_note} (by {operator})"
        return RecommendationRepository.update_status(
            rec_id=rec_id,
            new_status="Completed",
            user_note=final_note,
            caller_role=caller_role,
            db_path=db_path,
        )

    @staticmethod
    def get_all_recommendations(
        status_filter: Optional[str] = None,
        scenario_filter: Optional[str] = None,
        facility_filter: Optional[str] = None,
        db_path: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve stored recommendations with optional filters."""
        all_recs = RecommendationRepository.get_all(db_path=db_path)
        filtered = all_recs
        if status_filter and status_filter != "All":
            filtered = [r for r in filtered if r.get("status") == status_filter]
        if scenario_filter and scenario_filter != "All":
            filtered = [r for r in filtered if r.get("scenario") == scenario_filter]
        if facility_filter and facility_filter != "All":
            filtered = [r for r in filtered if r.get("facility_id") == facility_filter]
        return filtered

    get_recommendations = get_all_recommendations

    @staticmethod
    def get_audit_trail(rec_id: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve chronological state transition audit trail for a recommendation."""
        return RecommendationRepository.get_audit_trail(rec_id, db_path=db_path)


class SavingsSimulatorService:
    """Service evaluating multi-measure portfolio compounding, peak shaving, and load shifting."""

    @staticmethod
    def calculate_portfolio_savings(
        recommendations: List[Dict[str, Any]],
        overall_baseline_kwh: float,
        tariff_inr_per_kwh: float = 8.50,
    ) -> Dict[str, Any]:
        """Compute deduplicated portfolio savings avoiding double-counting."""
        return SavingsEngine.calculate_portfolio_savings(
            recommendations=recommendations,
            overall_baseline_kwh=overall_baseline_kwh,
            tariff_inr_per_kwh=tariff_inr_per_kwh,
        )

    @staticmethod
    def run_load_shifting_simulation(
        df: pd.DataFrame,
        shift_percentage: float = 20.0,
        peak_hours: Optional[List[int]] = None,
        off_peak_hours: Optional[List[int]] = None,
        tariff_schedule: Optional[Dict[str, Any]] = None,
        persist: bool = True,
        simulation_name: str = "Interactive Load Shifting Scenario",
        notes: str = "",
        db_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Simulate demand shifting from on-peak to off-peak tariff periods."""
        results = simulate_load_shifting(
            df=df,
            shift_percentage=shift_percentage,
            peak_hours=peak_hours,
            off_peak_hours=off_peak_hours,
            tariff_schedule=tariff_schedule,
        )
        if persist:
            try:
                sim_record = {
                    "name": simulation_name,
                    "baseline_kwh": results.get("original_peak_kwh", 0.0),
                    "reduction_pct": shift_percentage,
                    "tariff_inr": tariff_schedule.get("peak", 11.50) if tariff_schedule else 11.50,
                    "saved_kwh": results.get("shifted_kwh", 0.0),
                    "saved_inr": results.get("cost_savings_inr", 0.0),
                    "notes": notes or f"Shifted {shift_percentage}% of flexible load.",
                    "avoided_kg_co2e": results.get("avoided_kg_co2e", 0.0),
                }
                SimulationRepository.save(sim_record, db_path=db_path)
            except Exception:
                pass
        return results

    @staticmethod
    def run_peak_demand_shaving(
        df: pd.DataFrame,
        target_reduction_pct: float = 15.0,
        demand_charge_inr_per_kva: float = 450.0,
        power_factor: float = 0.90,
    ) -> Dict[str, Any]:
        """Simulate monthly contract demand charge reduction via peak shaving."""
        return analyze_peak_demand_shaving(
            df=df,
            target_reduction_pct=target_reduction_pct,
            demand_charge_inr_per_kva=demand_charge_inr_per_kva,
            power_factor=power_factor,
        )

    @staticmethod
    @require_permission(Permission.RUN_SIMULATION)
    def archive_simulation(
        name: str,
        baseline_kwh: float,
        reduction_pct: float,
        tariff_inr: float,
        saved_kwh: float,
        saved_inr: float,
        avoided_kg_co2e: float = 0.0,
        notes: str = "",
        db_path: Optional[str] = None,
    ) -> int:
        """Archive a completed simulation outcome to persistent SQLite repository."""
        sim_record = {
            "name": name,
            "baseline_kwh": baseline_kwh,
            "reduction_pct": reduction_pct,
            "tariff_inr": tariff_inr,
            "saved_kwh": saved_kwh,
            "saved_inr": saved_inr,
            "avoided_kg_co2e": avoided_kg_co2e,
            "notes": notes,
        }
        return SimulationRepository.save(sim_record, db_path=db_path)


class VerificationService:
    """Service evaluating empirical realized before-and-after savings."""

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
        persist: bool = True,
        db_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute before-and-after verification with empirical weather normalization."""
        res = SavingsVerifier.verify_intervention(
            df=df,
            intervention_name=intervention_name,
            intervention_date=intervention_date,
            baseline_start_date=baseline_start_date,
            baseline_end_date=baseline_end_date,
            post_start_date=post_start_date,
            post_end_date=post_end_date,
            expected_savings_kwh=expected_savings_kwh,
            tariff_inr_per_kwh=tariff_inr_per_kwh,
            carbon_calc=carbon_calc,
            rec_id=rec_id,
            notes=notes,
            cooling_sensitivity_kwh_per_c=cooling_sensitivity_kwh_per_c,
            weather_col=weather_col,
        )
        if persist and res.get("verification_status") != "Insufficient data":
            try:
                VerificationRepository.save(res, db_path=db_path)
            except Exception:
                pass
        return res

    @staticmethod
    def get_historical_verifications(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve historical verification records."""
        return VerificationRepository.get_all(db_path=db_path)

    @staticmethod
    @require_permission(Permission.SAVE_VERIFICATION)
    def save_verification(
        verification_data: Dict[str, Any],
        db_path: Optional[str] = None,
    ) -> int:
        """Persist a verified intervention record to database."""
        return VerificationRepository.save(verification_data, db_path=db_path)

    get_all_verifications = get_historical_verifications


class SystemAdminService:
    """Service handling system maintenance, migration tracking, and protected database resets."""

    @staticmethod
    def get_system_health(db_path: Optional[str] = None) -> Dict[str, Any]:
        """Retrieve database counts, applied migration status, and runtime environment settings."""
        cfg = get_config()
        counts = DatabaseAdminRepository.get_table_counts(db_path)
        migrations = DatabaseAdminRepository.get_applied_migrations(db_path)

        return {
            "environment": cfg.environment,
            "database_path": db_path or cfg.db_path,
            "table_record_counts": counts,
            "applied_migrations_count": len(migrations),
            "applied_migrations": migrations,
            "active_role": get_current_role().value,
            "allow_db_reset": cfg.allow_db_reset,
        }

    @staticmethod
    def reset_database(
        confirmation_token: Optional[str] = None,
        caller_role: Optional[Role | str] = None,
        force: bool = False,
        db_path: Optional[str] = None,
        confirmation_key: Optional[str] = None,
        operator: Optional[str] = None,
        **kwargs,
    ) -> bool:
        """Execute protected database reset with authorization and safety guards."""
        return DatabaseAdminRepository.reset_database(
            confirmation_token=confirmation_token,
            caller_role=caller_role,
            force=force,
            db_path=db_path,
            confirmation_key=confirmation_key,
            operator=operator,
            **kwargs,
        )
