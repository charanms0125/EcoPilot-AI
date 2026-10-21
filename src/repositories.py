"""
EcoPilot AI: Repository Layer (Data Access Layer)
Encapsulates all SQLite persistence and retrieval logic, isolating database
queries from presentation views and service orchestrators.
"""

from typing import List, Dict, Any, Optional
import json
from src.database import (
    get_db_context,
    init_db,
    save_recommendations as db_save_recommendations,
    get_all_recommendations as db_get_all_recommendations,
    update_recommendation_status as db_update_recommendation_status,
    get_audit_trail as db_get_audit_trail,
    save_alerts as db_save_alerts,
    get_all_alerts as db_get_all_alerts,
    update_alert_status as db_update_alert_status,
    save_verification as db_save_verification,
    get_all_verifications as db_get_all_verifications,
    save_simulation as db_save_simulation,
    get_all_simulations as db_get_all_simulations,
    log_dataset_upload as db_log_dataset_upload,
    reset_database as db_reset_database,
    get_applied_migrations as db_get_applied_migrations,
)
from src.auth import Role, Permission, check_permission, get_current_role


class RecommendationRepository:
    """Repository for energy conservation recommendations and audit trails."""

    @staticmethod
    def get_all(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
        return db_get_all_recommendations(db_path)

    @staticmethod
    def get_by_id(rec_id: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        init_db(db_path)
        with get_db_context(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM recommendations WHERE id = ?", (rec_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def save_all(recommendations: List[Dict[str, Any]], db_path: Optional[str] = None) -> int:
        return db_save_recommendations(recommendations, db_path)

    @staticmethod
    def upsert(rec: Dict[str, Any], db_path: Optional[str] = None) -> int:
        return db_save_recommendations([rec], db_path)

    @staticmethod
    def update_status(
        rec_id: str,
        new_status: str,
        user_note: str = "",
        caller_role: Optional[Role | str] = None,
        db_path: Optional[str] = None,
    ) -> bool:
        active_role = caller_role if isinstance(caller_role, Role) else (Role.from_str(caller_role) if caller_role else get_current_role())

        # Role-based authorization for state changes
        if new_status in ["Approved", "Rejected"]:
            if not check_permission(Permission.APPROVE_RECOMMENDATION, active_role):
                raise PermissionError(f"Role '{active_role.value}' cannot authorize or reject recommendations.")
        elif new_status == "Completed":
            if not check_permission(Permission.COMPLETE_ACTION, active_role):
                raise PermissionError(f"Role '{active_role.value}' cannot mark recommendations as completed.")

        return db_update_recommendation_status(rec_id, new_status, user_note, db_path)

    @staticmethod
    def get_audit_trail(rec_id: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
        return db_get_audit_trail(rec_id, db_path)


class AlertRepository:
    """Repository for explainable anomaly alerts."""

    @staticmethod
    def get_all(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
        return db_get_all_alerts(db_path)

    @staticmethod
    def save_all(alerts: List[Dict[str, Any]], db_path: Optional[str] = None) -> int:
        return db_save_alerts(alerts, db_path)

    @staticmethod
    def update_status(
        alert_id: str,
        new_status: str,
        user_note: str = "",
        caller_role: Optional[Role | str] = None,
        db_path: Optional[str] = None,
    ) -> bool:
        active_role = caller_role if isinstance(caller_role, Role) else (Role.from_str(caller_role) if caller_role else get_current_role())
        if not check_permission(Permission.UPDATE_ALERT_STATUS, active_role):
            raise PermissionError(f"Role '{active_role.value}' cannot update anomaly alert triage status.")
        return db_update_alert_status(alert_id, new_status, user_note, db_path)


class VerificationRepository:
    """Repository for realized savings before-and-after verification assessments."""

    @staticmethod
    def get_all(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
        return db_get_all_verifications(db_path)

    @staticmethod
    def save(verification_record: Dict[str, Any], db_path: Optional[str] = None) -> bool:
        return db_save_verification(verification_record, db_path)


class SimulationRepository:
    """Repository for tariff arbitrage and load shifting simulations."""

    @staticmethod
    def get_all(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
        return db_get_all_simulations(db_path)

    @staticmethod
    def save(simulation_record: Dict[str, Any], db_path: Optional[str] = None) -> int:
        return db_save_simulation(
            name=simulation_record.get("name", "Simulation"),
            baseline_kwh=float(simulation_record.get("baseline_kwh", 0.0)),
            reduction_pct=float(simulation_record.get("reduction_pct", 0.0)),
            tariff_inr=float(simulation_record.get("tariff_inr", 8.50)),
            saved_kwh=float(simulation_record.get("saved_kwh", 0.0)),
            saved_inr=float(simulation_record.get("saved_inr", 0.0)),
            notes=simulation_record.get("notes", ""),
            avoided_kg_co2e=float(simulation_record.get("avoided_kg_co2e", 0.0)),
            db_path=db_path,
        )


class DatasetUploadRepository:
    """Repository for telemetry upload history and data quality reports."""

    @staticmethod
    def log_upload(
        filename: str,
        row_count: int,
        date_start: str,
        date_end: str,
        is_valid: bool,
        quality_report: Dict[str, Any],
        db_path: Optional[str] = None,
    ) -> int:
        return db_log_dataset_upload(
            filename=filename,
            row_count=row_count,
            date_start=date_start,
            date_end=date_end,
            is_valid=is_valid,
            quality_report=quality_report,
            db_path=db_path,
        )

    @staticmethod
    def get_all(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
        init_db(db_path)
        with get_db_context(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM datasets ORDER BY id DESC")
            records = []
            for row in cursor.fetchall():
                d = dict(row)
                if d.get("quality_report"):
                    try:
                        d["quality_report"] = json.loads(d["quality_report"])
                    except Exception:
                        pass
                records.append(d)
            return records


class DatabaseAdminRepository:
    """Repository for administrative maintenance, migrations, and health checks."""

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
        return db_reset_database(
            confirmation_token=confirmation_token,
            caller_role=caller_role,
            force=force,
            db_path=db_path,
            confirmation_key=confirmation_key,
            operator=operator,
            **kwargs,
        )

    @staticmethod
    def get_admin_audit_logs(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
        init_db(db_path)
        with get_db_context(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM admin_audit_log ORDER BY id DESC")
            records = []
            for r in cursor.fetchall():
                d = dict(r)
                d["operator"] = d.get("performed_by", "")
                records.append(d)
            return records

    @staticmethod
    def get_applied_migrations(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
        return db_get_applied_migrations(db_path)

    @staticmethod
    def get_table_counts(db_path: Optional[str] = None) -> Dict[str, int]:
        init_db(db_path)
        counts = {}
        with get_db_context(db_path) as conn:
            cursor = conn.cursor()
            tables = [
                "recommendations",
                "alerts",
                "verifications",
                "simulations",
                "datasets",
                "audit_log",
                "carbon_calculations",
            ]
            for t in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) as cnt FROM {t}")
                    counts[t] = cursor.fetchone()["cnt"]
                except Exception:
                    counts[t] = 0
        return counts
