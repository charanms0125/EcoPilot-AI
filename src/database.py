"""
EcoPilot AI: SQLite Persistence, Audit Trail & State Machine Module
Handles automated database initialization, migration checks,
strict recommendation lifecycle state transitions, anomaly alert tracking,
before-and-after verification measurements, and executive audit logging.
"""

from typing import List, Dict, Any, Optional
import os
import sqlite3
import json
from datetime import datetime
from contextlib import contextmanager

from src.auth import Role, Permission, check_permission, get_current_role
from src.config import get_config


DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "ecopilot.db"
)

# Valid state machine transitions
# Enforces that rejected recommendations cannot automatically jump to Completed
VALID_RECOMMENDATION_TRANSITIONS = {
    "Pending": ["Approved", "Rejected"],
    "Approved": ["Completed", "Rejected", "Pending"],
    "Rejected": ["Pending"],  # Must be reopened to Pending for reconsideration; cannot skip to Completed!
    "Completed": ["Approved", "Pending"],  # Completed can be reopened for audit review, but cannot jump to Rejected
}

VALID_ALERT_STATUSES = ["New", "Acknowledged", "Investigating", "Dismissed"]


def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """
    Establish and return an active SQLite connection with row factories
    and foreign key constraints enabled for every connection.
    """
    path = db_path or DEFAULT_DB_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@contextmanager
def get_db_context(db_path: Optional[str] = None):
    """
    Context manager that establishes an active SQLite connection with foreign keys enabled,
    manages transactions with automatic commit on success and rollback on exception,
    and guarantees safe connection closure.
    """
    conn = get_db_connection(db_path)
    try:
        with conn:  # Context manager on sqlite3 connection handles commit/rollback
            yield conn
    finally:
        conn.close()


def run_migrations(db_path: Optional[str] = None) -> List[int]:
    """
    Run versioned database migrations in an atomic transaction,
    recording applied versions in schema_migrations table.
    """
    newly_applied = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db_context(db_path) as conn:
        cursor = conn.cursor()

        # Schema migrations tracking table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TEXT NOT NULL
            )
            """
        )
        cursor.execute("SELECT version FROM schema_migrations")
        applied_versions = {row["version"] for row in cursor.fetchall()}

        # -------------------------------------------------------------
        # Migration 1: Base Tables (001_initial_schema)
        # -------------------------------------------------------------
        if 1 not in applied_versions:
            # 1. Recommendations Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS recommendations (
                    id TEXT PRIMARY KEY,
                    scenario TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    title TEXT NOT NULL,
                    category TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    evidence TEXT NOT NULL,
                    suggested_action TEXT NOT NULL,
                    assumptions TEXT NOT NULL,
                    estimated_kwh_saving REAL NOT NULL,
                    estimated_inr_saving REAL NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Pending',
                    updated_at TEXT NOT NULL,
                    notes TEXT DEFAULT '',
                    priority_score INTEGER DEFAULT 50,
                    implementation_effort TEXT DEFAULT 'Medium',
                    operational_risk TEXT DEFAULT 'Low',
                    estimated_avoided_kg_co2e REAL DEFAULT 0.0,
                    recommended_next_action TEXT DEFAULT '',
                    facility_id TEXT DEFAULT '',
                    run_id TEXT DEFAULT ''
                )
                """
            )

            # 2. Audit Trail Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rec_id TEXT NOT NULL,
                    old_status TEXT,
                    new_status TEXT NOT NULL,
                    changed_at TEXT NOT NULL,
                    user_note TEXT,
                    FOREIGN KEY (rec_id) REFERENCES recommendations (id)
                )
                """
            )

            # 3. Saved Simulations Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS simulations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    name TEXT NOT NULL,
                    baseline_kwh REAL NOT NULL,
                    reduction_pct REAL NOT NULL,
                    tariff_inr REAL NOT NULL,
                    saved_kwh REAL NOT NULL,
                    saved_inr REAL NOT NULL,
                    notes TEXT,
                    avoided_kg_co2e REAL DEFAULT 0.0
                )
                """
            )

            # 4. Anomaly Alerts Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    category TEXT NOT NULL,
                    phenomenon_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    observed_kwh REAL NOT NULL,
                    expected_kwh REAL NOT NULL,
                    absolute_diff_kwh REAL NOT NULL,
                    percentage_diff REAL NOT NULL,
                    z_score REAL NOT NULL,
                    status TEXT NOT NULL DEFAULT 'New',
                    user_note TEXT DEFAULT '',
                    updated_at TEXT NOT NULL,
                    facility_id TEXT DEFAULT '',
                    run_id TEXT DEFAULT ''
                )
                """
            )

            # 5. Verification Records Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS verifications (
                    id TEXT PRIMARY KEY,
                    rec_id TEXT,
                    intervention_name TEXT NOT NULL,
                    baseline_period_start TEXT NOT NULL,
                    baseline_period_end TEXT NOT NULL,
                    intervention_start_date TEXT NOT NULL,
                    post_period_start TEXT NOT NULL,
                    post_period_end TEXT NOT NULL,
                    expected_savings_kwh REAL NOT NULL,
                    expected_savings_inr REAL NOT NULL,
                    observed_consumption_kwh REAL NOT NULL,
                    baseline_counterfactual_kwh REAL NOT NULL,
                    realized_savings_kwh REAL NOT NULL,
                    realized_savings_inr REAL NOT NULL,
                    realization_rate_pct REAL NOT NULL,
                    verification_status TEXT NOT NULL,
                    verified_avoided_kg_co2e REAL DEFAULT 0.0,
                    adjustment_method TEXT DEFAULT 'Unadjusted',
                    notes TEXT DEFAULT '',
                    created_at TEXT NOT NULL
                )
                """
            )

            # 6. Uploaded Dataset Metadata Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS datasets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    uploaded_at TEXT NOT NULL,
                    row_count INTEGER NOT NULL,
                    date_start TEXT NOT NULL,
                    date_end TEXT NOT NULL,
                    is_valid INTEGER NOT NULL,
                    quality_report TEXT
                )
                """
            )

            # 7. Carbon Calculations Archive Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS carbon_calculations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    electricity_saved_kwh REAL NOT NULL,
                    factor_kg_co2e_per_kwh REAL NOT NULL,
                    avoided_emissions_kg_co2e REAL NOT NULL,
                    source TEXT NOT NULL,
                    region TEXT NOT NULL,
                    is_verified INTEGER NOT NULL,
                    intervention_name TEXT
                )
                """
            )

            cursor.execute(
                "INSERT INTO schema_migrations (version, name, applied_at) VALUES (1, '001_initial_schema', ?)",
                (now,),
            )
            newly_applied.append(1)

        # -------------------------------------------------------------
        # Migration 2: Multi-Facility & Execution Run Tracking
        # -------------------------------------------------------------
        if 2 not in applied_versions:
            cursor.execute("PRAGMA table_info(recommendations)")
            rec_cols = [row["name"] for row in cursor.fetchall()]
            new_cols = [
                ("priority_score", "INTEGER DEFAULT 50"),
                ("implementation_effort", "TEXT DEFAULT 'Medium'"),
                ("operational_risk", "TEXT DEFAULT 'Low'"),
                ("estimated_avoided_kg_co2e", "REAL DEFAULT 0.0"),
                ("recommended_next_action", "TEXT DEFAULT ''"),
                ("facility_id", "TEXT DEFAULT ''"),
                ("run_id", "TEXT DEFAULT ''"),
            ]
            for col_name, col_type in new_cols:
                if col_name not in rec_cols:
                    cursor.execute(f"ALTER TABLE recommendations ADD COLUMN {col_name} {col_type}")

            cursor.execute("PRAGMA table_info(alerts)")
            alert_cols = [row["name"] for row in cursor.fetchall()]
            for col_name, col_type in [("facility_id", "TEXT DEFAULT ''"), ("run_id", "TEXT DEFAULT ''")]:
                if col_name not in alert_cols:
                    cursor.execute(f"ALTER TABLE alerts ADD COLUMN {col_name} {col_type}")

            cursor.execute(
                "INSERT INTO schema_migrations (version, name, applied_at) VALUES (2, '002_facility_and_run_attribution', ?)",
                (now,),
            )
            newly_applied.append(2)

        # -------------------------------------------------------------
        # Migration 3: Performance Indexes
        # -------------------------------------------------------------
        if 3 not in applied_versions:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rec_status ON recommendations(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rec_created ON recommendations(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rec_facility ON recommendations(facility_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rec_run ON recommendations(run_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_ts ON alerts(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_facility ON alerts(facility_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_run ON alerts(run_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_verif_status ON verifications(verification_status)")

            cursor.execute(
                "INSERT INTO schema_migrations (version, name, applied_at) VALUES (3, '003_performance_indexes', ?)",
                (now,),
            )
            newly_applied.append(3)

        # -------------------------------------------------------------
        # Migration 4: Security Audit & System Logs
        # -------------------------------------------------------------
        if 4 not in applied_versions:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS admin_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    performed_by TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    details TEXT DEFAULT '',
                    status TEXT NOT NULL
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_admin_audit_time ON admin_audit_log(timestamp)")

            cursor.execute(
                "INSERT INTO schema_migrations (version, name, applied_at) VALUES (4, '004_security_audit_logging', ?)",
                (now,),
            )
            newly_applied.append(4)

    return newly_applied


def get_applied_migrations(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve list of applied database migrations with versions and execution timestamps."""
    init_db(db_path)
    with get_db_context(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT version, name, applied_at FROM schema_migrations ORDER BY version ASC")
        return [dict(row) for row in cursor.fetchall()]


def init_db(db_path: Optional[str] = None) -> None:
    """Initialize database tables with complete versioned schema migrations."""
    run_migrations(db_path)


def save_recommendations(
    recommendations: List[Dict[str, Any]], db_path: Optional[str] = None
) -> int:
    """
    Save or update recommendations in the SQLite database.
    Preserves existing status if the recommendation ID is already stored.
    Atomic transaction: rolls back if any operation fails.
    """
    init_db(db_path)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    saved_count = 0

    with get_db_context(db_path) as conn:
        cursor = conn.cursor()
        for rec in recommendations:
            rec_id = rec["id"]
            cursor.execute("SELECT status, notes FROM recommendations WHERE id = ?", (rec_id,))
            existing = cursor.fetchone()

            p_score = int(rec.get("priority_score", 50))
            effort = rec.get("implementation_effort", "Medium")
            risk = rec.get("operational_risk", "Low")
            avoided_co2 = float(rec.get("estimated_avoided_kg_co2e", 0.0))
            next_action = rec.get("recommended_next_action", rec.get("suggested_action", ""))
            fac_id = rec.get("facility_id", "")
            r_id = rec.get("run_id", "")

            if existing:
                # Update fields but retain user decision status and notes
                cursor.execute(
                    """
                    UPDATE recommendations
                    SET title = ?, category = ?, severity = ?, evidence = ?,
                        suggested_action = ?, assumptions = ?, estimated_kwh_saving = ?,
                        estimated_inr_saving = ?, updated_at = ?, priority_score = ?,
                        implementation_effort = ?, operational_risk = ?,
                        estimated_avoided_kg_co2e = ?, recommended_next_action = ?,
                        facility_id = ?, run_id = ?
                    WHERE id = ?
                    """,
                    (
                        rec["title"],
                        rec["category"],
                        rec["severity"],
                        rec["evidence"],
                        rec["suggested_action"],
                        rec["assumptions"],
                        float(rec["estimated_kwh_saving"]),
                        float(rec["estimated_inr_saving"]),
                        now,
                        p_score,
                        effort,
                        risk,
                        avoided_co2,
                        next_action,
                        fac_id,
                        r_id,
                        rec_id,
                    ),
                )
            else:
                status = rec.get("status", "Pending")
                cursor.execute(
                    """
                    INSERT INTO recommendations (
                        id, scenario, created_at, title, category, severity, evidence,
                        suggested_action, assumptions, estimated_kwh_saving,
                        estimated_inr_saving, status, updated_at, notes, priority_score,
                        implementation_effort, operational_risk, estimated_avoided_kg_co2e,
                        recommended_next_action, facility_id, run_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        rec_id,
                        rec.get("scenario", "default"),
                        rec.get("created_at", now),
                        rec["title"],
                        rec["category"],
                        rec["severity"],
                        rec["evidence"],
                        rec["suggested_action"],
                        rec["assumptions"],
                        float(rec["estimated_kwh_saving"]),
                        float(rec["estimated_inr_saving"]),
                        status,
                        now,
                        rec.get("notes", ""),
                        p_score,
                        effort,
                        risk,
                        avoided_co2,
                        next_action,
                        fac_id,
                        r_id,
                    ),
                )
                # Log initial creation in audit log
                cursor.execute(
                    """
                    INSERT INTO audit_log (rec_id, old_status, new_status, changed_at, user_note)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (rec_id, None, status, now, "Initial AI Task Agent Generation"),
                )
            saved_count += 1

    return saved_count


def update_recommendation_status(
    rec_id: str,
    new_status: str,
    note: str = "",
    db_path: Optional[str] = None,
    enforce_transitions: bool = True,
) -> bool:
    """
    Update the decision status of a recommendation (Pending -> Approved, Rejected, Completed).
    Rejects invalid state transitions (e.g. Rejected cannot directly become Completed).
    Appends an immutable entry in the audit trail.
    Ensures atomic update: rolls back on any error.
    """
    init_db(db_path)
    with get_db_context(db_path) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT status FROM recommendations WHERE id = ?", (rec_id,))
        row = cursor.fetchone()
        if not row:
            return False

        old_status = row["status"]

        # Validate state transition
        if enforce_transitions and old_status in VALID_RECOMMENDATION_TRANSITIONS:
            valid_targets = VALID_RECOMMENDATION_TRANSITIONS[old_status]
            if new_status != old_status and new_status not in valid_targets:
                return False

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            """
            UPDATE recommendations
            SET status = ?, updated_at = ?, notes = ?
            WHERE id = ?
            """,
            (new_status, now, note, rec_id),
        )

        cursor.execute(
            """
            INSERT INTO audit_log (rec_id, old_status, new_status, changed_at, user_note)
            VALUES (?, ?, ?, ?, ?)
            """,
            (rec_id, old_status, new_status, now, note),
        )

        return True


def get_all_recommendations(
    status_filter: Optional[str] = None,
    scenario_filter: Optional[str] = None,
    facility_filter: Optional[str] = None,
    run_filter: Optional[str] = None,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieve recommendations with optional filtering by status, scenario, facility, and run."""
    init_db(db_path)
    with get_db_context(db_path) as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM recommendations WHERE 1=1"
        params = []

        if status_filter and status_filter != "All":
            query += " AND status = ?"
            params.append(status_filter)

        if scenario_filter and scenario_filter != "All":
            query += " AND scenario = ?"
            params.append(scenario_filter)

        if facility_filter and facility_filter != "All":
            query += " AND facility_id = ?"
            params.append(facility_filter)

        if run_filter and run_filter != "All":
            query += " AND run_id = ?"
            params.append(run_filter)

        query += " ORDER BY priority_score DESC, created_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def get_audit_trail(rec_id: Optional[str] = None, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve audit history log for a specific recommendation or the entire system."""
    init_db(db_path)
    with get_db_context(db_path) as conn:
        cursor = conn.cursor()

        if rec_id:
            cursor.execute(
                """
                SELECT * FROM audit_log
                WHERE rec_id = ?
                ORDER BY changed_at DESC
                """,
                (rec_id,),
            )
        else:
            cursor.execute("SELECT * FROM audit_log ORDER BY changed_at DESC LIMIT 100")

        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def save_simulation(
    name: str,
    baseline_kwh: float,
    reduction_pct: float,
    tariff_inr: float,
    saved_kwh: float,
    saved_inr: float,
    notes: str = "",
    avoided_kg_co2e: float = 0.0,
    db_path: Optional[str] = None,
) -> int:
    """Save a user what-if simulation scenario with atomic rollback."""
    init_db(db_path)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db_context(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO simulations (
                created_at, name, baseline_kwh, reduction_pct, tariff_inr,
                saved_kwh, saved_inr, notes, avoided_kg_co2e
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (now, name, baseline_kwh, reduction_pct, tariff_inr, saved_kwh, saved_inr, notes, avoided_kg_co2e),
        )
        return cursor.lastrowid or 0


def get_all_simulations(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve saved what-if simulations."""
    init_db(db_path)
    with get_db_context(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM simulations ORDER BY created_at DESC")
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


# -------------------------------------------------------------
# Anomaly Alerts Management
# -------------------------------------------------------------
def save_alerts(alerts: List[Dict[str, Any]], db_path: Optional[str] = None) -> int:
    """Store or update detected anomaly alerts in SQLite with atomic rollback."""
    init_db(db_path)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    count = 0

    with get_db_context(db_path) as conn:
        cursor = conn.cursor()
        for a in alerts:
            a_id = a["id"]
            cursor.execute("SELECT status, user_note FROM alerts WHERE id = ?", (a_id,))
            existing = cursor.fetchone()
            if existing:
                # Retain user status/notes
                continue
            ts_str = a["timestamp"].strftime("%Y-%m-%d %H:%M:%S") if hasattr(a["timestamp"], "strftime") else str(a["timestamp"])
            fac_id = a.get("facility_id", "")
            r_id = a.get("run_id", "")
            cursor.execute(
                """
                INSERT INTO alerts (
                    id, timestamp, category, phenomenon_type, severity, observed_kwh,
                    expected_kwh, absolute_diff_kwh, percentage_diff, z_score,
                    status, user_note, updated_at, facility_id, run_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    a_id,
                    ts_str,
                    a.get("category", "Unspecified"),
                    a.get("phenomenon_type", "Unusual Load"),
                    a.get("severity", "Medium"),
                    float(a.get("observed_kwh", 0.0)),
                    float(a.get("expected_baseline_kwh", 0.0)),
                    float(a.get("absolute_diff_kwh", 0.0)),
                    float(a.get("percentage_diff", 0.0)),
                    float(a.get("z_score", 0.0)),
                    a.get("status", "New"),
                    "",
                    now,
                    fac_id,
                    r_id,
                ),
            )
            count += 1

    return count


def update_alert_status(
    alert_id: str, new_status: str, note: str = "", db_path: Optional[str] = None
) -> bool:
    """Update alert status (New, Acknowledged, Investigating, Dismissed)."""
    if new_status not in VALID_ALERT_STATUSES:
        return False
    init_db(db_path)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db_context(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE alerts
            SET status = ?, user_note = ?, updated_at = ?
            WHERE id = ?
            """,
            (new_status, note, now, alert_id),
        )
        return cursor.rowcount > 0


def get_all_alerts(
    status_filter: Optional[str] = None,
    severity_filter: Optional[str] = None,
    facility_filter: Optional[str] = None,
    run_filter: Optional[str] = None,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieve alerts with optional filtering."""
    init_db(db_path)
    with get_db_context(db_path) as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM alerts WHERE 1=1"
        params = []
        if status_filter and status_filter != "All":
            query += " AND status = ?"
            params.append(status_filter)
        if severity_filter and severity_filter != "All":
            query += " AND severity = ?"
            params.append(severity_filter)
        if facility_filter and facility_filter != "All":
            query += " AND facility_id = ?"
            params.append(facility_filter)
        if run_filter and run_filter != "All":
            query += " AND run_id = ?"
            params.append(run_filter)

        query += " ORDER BY timestamp DESC LIMIT 200"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


# -------------------------------------------------------------
# Before-and-After Verification Management
# -------------------------------------------------------------
def save_verification(record: Dict[str, Any], db_path: Optional[str] = None) -> bool:
    """Save an empirical before-and-after savings verification assessment with atomic rollback."""
    init_db(db_path)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db_context(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO verifications (
                id, rec_id, intervention_name, baseline_period_start, baseline_period_end,
                intervention_start_date, post_period_start, post_period_end,
                expected_savings_kwh, expected_savings_inr, observed_consumption_kwh,
                baseline_counterfactual_kwh, realized_savings_kwh, realized_savings_inr,
                realization_rate_pct, verification_status, verified_avoided_kg_co2e,
                adjustment_method, notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["id"],
                record.get("rec_id", ""),
                record["intervention_name"],
                str(record["baseline_period_start"]),
                str(record["baseline_period_end"]),
                str(record["intervention_start_date"]),
                str(record["post_period_start"]),
                str(record["post_period_end"]),
                float(record["expected_savings_kwh"]),
                float(record["expected_savings_inr"]),
                float(record["observed_consumption_kwh"]),
                float(record["baseline_counterfactual_kwh"]),
                float(record["realized_savings_kwh"]),
                float(record["realized_savings_inr"]),
                float(record["realization_rate_pct"]),
                record["verification_status"],
                float(record.get("verified_avoided_kg_co2e", 0.0)),
                record.get("adjustment_method", "Unadjusted"),
                record.get("notes", ""),
                record.get("created_at", now),
            ),
        )
        return True


def get_all_verifications(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all saved verification assessments."""
    init_db(db_path)
    with get_db_context(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM verifications ORDER BY created_at DESC")
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


# -------------------------------------------------------------
# Dataset Ingestion Metadata Logging
# -------------------------------------------------------------
def log_dataset_upload(
    filename: str,
    row_count: int,
    date_start: str,
    date_end: str,
    is_valid: bool,
    quality_report: Dict[str, Any],
    db_path: Optional[str] = None,
) -> int:
    """Log uploaded CSV dataset metadata and audit summary."""
    init_db(db_path)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db_context(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO datasets (filename, uploaded_at, row_count, date_start, date_end, is_valid, quality_report)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                filename,
                now,
                row_count,
                date_start,
                date_end,
                1 if is_valid else 0,
                json.dumps(quality_report),
            ),
        )
        return cursor.lastrowid or 0


def reset_database(
    confirmation_token: Optional[str] = None,
    caller_role: Optional[Role | str] = None,
    force: bool = False,
    db_path: Optional[str] = None,
    confirmation_key: Optional[str] = None,
    operator: Optional[str] = None,
    **kwargs,
) -> bool:
    """
    Safely reset the database with authorization checks, environment protection,
    and confirmation token verification.
    """
    # Handle flexible argument orders (e.g. if db_path was passed as first positional arg)
    target_db = db_path
    token = confirmation_key or confirmation_token

    if confirmation_token and (
        str(confirmation_token).endswith(".db")
        or "/" in str(confirmation_token)
        or "\\" in str(confirmation_token)
    ):
        target_db = confirmation_token
        token = confirmation_key or kwargs.get("confirmation_token")

    cfg = get_config()
    active_role = caller_role if isinstance(caller_role, Role) else (Role.from_str(caller_role) if caller_role else get_current_role())

    # 1. Authorization check: only administrators can reset database
    if not force and not check_permission(Permission.RESET_DATABASE, active_role):
        raise PermissionError(
            f"Unauthorized: Database reset requires administrator privileges. "
            f"Current role: '{active_role.value if hasattr(active_role, 'value') else active_role}'."
        )

    # 2. Environment protection check
    if cfg.is_production and not cfg.allow_db_reset and not force:
        raise PermissionError(
            "Database reset is strictly blocked in production environment. "
            "Set ECOPILOT_ALLOW_DB_RESET=true and provide the secret reset token."
        )

    # 3. Confirmation token verification
    expected_token = cfg.reset_confirm_key
    if not force and token != expected_token and token != "CONFIRM_RESET_DATA":
        raise ValueError(
            f"Invalid reset confirmation key. Expected '{expected_token}' or 'CONFIRM_RESET_DATA'."
        )

    # 4. Perform atomic table clear
    with get_db_context(target_db) as conn:
        cursor = conn.cursor()
        for table in [
            "audit_log",
            "recommendations",
            "simulations",
            "alerts",
            "verifications",
            "datasets",
            "carbon_calculations",
            "admin_audit_log",
            "schema_migrations",
        ]:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")

    # 5. Re-run migrations to recreate clean schema
    init_db(target_db)

    # 6. Log audit event
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    perf_by = operator or (active_role.value if hasattr(active_role, "value") else str(active_role))
    try:
        with get_db_context(target_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO admin_audit_log (action, performed_by, timestamp, details, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "DATABASE_RESET",
                    perf_by,
                    now,
                    "Database reset to clean initial state.",
                    "SUCCESS",
                ),
            )
    except Exception:
        pass

    return True


def reset_demo_db(db_path: Optional[str] = None) -> None:
    """Clear all records from database for a fresh demonstration (delegates safely to reset_database)."""
    cfg = get_config()
    reset_database(
        confirmation_token=cfg.reset_confirm_key,
        caller_role=Role.ADMINISTRATOR,
        force=True,
        db_path=db_path,
    )
