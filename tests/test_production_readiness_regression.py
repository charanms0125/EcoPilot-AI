"""
Regression test suite for EcoPilot-AI Production Readiness Refactoring.
Validates:
1. CSV validation, quality reporting, and typed schema validation.
2. Timezone handling and normalization.
3. Sampling frequency and irregular interval detection.
4. Missing value interpolation and excessive gap rejection.
5. Negative value detection and clipping.
6. Centralized configuration with environment profile overrides.
7. Role-Based Access Control (RBAC) permissions, hierarchy, and context switching.
8. Protected database reset operations (role checks, token confirmation, audit logging).
9. Schema migrations runner and tracking.
10. Service and Repository layer contracts.
"""

import os
import pytest
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.config import Settings, Environment, get_config, set_config
from src.auth import (
    Role,
    Permission,
    get_role_permissions,
    has_minimum_role,
    check_permission,
    require_permission,
    get_current_role,
    set_current_role,
)
from src.schemas import (
    DataQualityReportSchema,
    AlertSchema,
    RecommendationSchema,
    ForecastMetricsSchema,
    VerificationResultSchema,
    AuditLogSchema,
)
from src.data_generator import (
    validate_uploaded_csv,
    generate_data_quality_report,
)
from src.database import (
    get_db_connection,
    get_db_context,
    init_db,
    run_migrations,
    get_applied_migrations,
    reset_database,
    reset_demo_db,
)
from src.repositories import (
    RecommendationRepository,
    AlertRepository,
    VerificationRepository,
    SimulationRepository,
    DatasetUploadRepository,
    DatabaseAdminRepository,
)
from src.services import (
    EnergyDataService,
    AnalyticsService,
    RecommendationService,
    SavingsSimulatorService,
    VerificationService,
    SystemAdminService,
)


@pytest.fixture
def temp_db_env(tmp_path, monkeypatch):
    """Sets up an isolated SQLite database and config for tests."""
    db_file = str(tmp_path / "test_readiness.db")
    monkeypatch.setenv("ECOPILOT_DB_PATH", db_file)
    monkeypatch.setenv("ECOPILOT_ENV", "test")
    monkeypatch.setenv("ECOPILOT_ALLOW_DB_RESET", "true")
    monkeypatch.setenv("ECOPILOT_RESET_CONFIRM_KEY", "TEST_CONFIRM_KEY")

    # Reset config singleton
    cfg = Settings(
        environment="test",
        db_path=db_file,
        allow_db_reset=True,
        reset_confirm_key="TEST_CONFIRM_KEY",
    )
    set_config(cfg)
    init_db(db_file)
    set_current_role(Role.ADMINISTRATOR)
    yield db_file


# ==============================================================================
# 1. TIMEZONE & SAMPLING FREQUENCY REGRESSION TESTS
# ==============================================================================

def test_timezone_normalization_tz_aware_to_tz_naive():
    """Verify that timezone-aware timestamps (e.g. UTC, Asia/Kolkata) are safely normalized to tz-naive."""
    # Create 60 hours of UTC timestamps
    ts_utc = pd.date_range("2026-03-01 00:00:00+00:00", periods=60, freq="h")
    df = pd.DataFrame({
        "timestamp": ts_utc,
        "energy_kwh": [35.0] * 60,
    })
    is_valid, err, cleaned = validate_uploaded_csv(df)
    assert is_valid is True, f"Validation failed: {err}"
    assert cleaned["timestamp"].dt.tz is None, "Timestamps should be normalized to tz-naive"
    assert cleaned.attrs.get("detected_timezone") == "UTC"

    # Verify quality report captures timezone
    report = generate_data_quality_report(df, cleaned, err)
    assert report["detected_timezone"] == "UTC"
    report_validated = DataQualityReportSchema(**report)
    assert report_validated.detected_timezone == "UTC"


def test_sampling_frequency_detection():
    """Verify detection of 15-minute, 30-minute, and hourly cadences."""
    # 15-minute intervals
    df_15m = pd.DataFrame({
        "timestamp": pd.date_range("2026-01-01", periods=96, freq="15min"),
        "energy_kwh": [10.0] * 96,
    })
    is_valid, _, cleaned_15m = validate_uploaded_csv(df_15m)
    assert is_valid is True
    report_15m = generate_data_quality_report(df_15m, cleaned_15m)
    assert report_15m["sampling_frequency"] == "15-minute"

    # Hourly intervals
    df_1h = pd.DataFrame({
        "timestamp": pd.date_range("2026-01-01", periods=60, freq="h"),
        "energy_kwh": [40.0] * 60,
    })
    is_valid, _, cleaned_1h = validate_uploaded_csv(df_1h)
    assert is_valid is True
    report_1h = generate_data_quality_report(df_1h, cleaned_1h)
    assert report_1h["sampling_frequency"] == "Hourly"


def test_irregular_interval_flagging():
    """Verify irregular intervals are tracked and audited without crashing."""
    times = [datetime(2026, 1, 1, 0, 0)]
    np.random.seed(42)
    step_minutes = [15, 30, 60, 45, 15] * 12
    for m in step_minutes[:59]:
        times.append(times[-1] + timedelta(minutes=m))

    df = pd.DataFrame({
        "timestamp": times,
        "energy_kwh": [25.0] * len(times),
    })
    is_valid, _, cleaned = validate_uploaded_csv(df)
    assert is_valid is True
    report = generate_data_quality_report(df, cleaned)
    assert report["is_regular_interval"] is False
    assert report["irregular_intervals_detected"] > 0
    assert any("irregular" in issue.lower() for issue in report["issues_detected"])


# ==============================================================================
# 2. MISSING VALUES & NEGATIVE VALUES SANITIZATION
# ==============================================================================

def test_negative_values_clipping_and_audit():
    """Verify negative energy values are clipped to 0.0 and counted in the quality report."""
    vals = [25.0] * 60
    vals[5] = -12.5
    vals[15] = -3.0
    vals[25] = -0.1

    df = pd.DataFrame({
        "timestamp": pd.date_range("2026-02-01", periods=60, freq="h"),
        "energy_kwh": vals,
    })
    is_valid, _, cleaned = validate_uploaded_csv(df)
    assert is_valid is True
    assert (cleaned["energy_kwh"] >= 0.0).all()
    assert cleaned["energy_kwh"].iloc[5] == 0.0

    report = generate_data_quality_report(df, cleaned)
    assert report["negative_values_found"] == 3
    assert report["negative_values_clipped"] == 3
    assert report["health_score_pct"] < 100.0


def test_missing_values_linear_interpolation():
    """Verify minor missing value gaps are imputed with linear interpolation."""
    vals = [30.0] * 60
    vals[10] = np.nan
    vals[11] = np.nan

    df = pd.DataFrame({
        "timestamp": pd.date_range("2026-02-01", periods=60, freq="h"),
        "energy_kwh": vals,
    })
    is_valid, _, cleaned = validate_uploaded_csv(df)
    assert is_valid is True
    assert not cleaned["energy_kwh"].isna().any()
    assert cleaned["energy_kwh"].iloc[10] == 30.0

    report = generate_data_quality_report(df, cleaned)
    assert report["missing_values_imputed"] == 2


def test_excessive_gap_rejected():
    """Verify datasets with consecutive gaps > 24 hours are rejected."""
    vals = [30.0] * 80
    for i in range(10, 36):  # 26 consecutive missing hours
        vals[i] = np.nan

    df = pd.DataFrame({
        "timestamp": pd.date_range("2026-02-01", periods=80, freq="h"),
        "energy_kwh": vals,
    })
    is_valid, err, cleaned = validate_uploaded_csv(df)
    assert is_valid is False
    assert ">24 hours" in err


# ==============================================================================
# 3. CENTRALIZED CONFIGURATION TESTS
# ==============================================================================

def test_centralized_configuration_profiles(monkeypatch):
    """Verify Settings loads environment variables and parses types."""
    monkeypatch.setenv("ECOPILOT_ENV", "production")
    monkeypatch.setenv("ECOPILOT_DEFAULT_TARIFF_INR", "9.75")
    monkeypatch.setenv("ECOPILOT_ALLOW_DB_RESET", "false")

    cfg = Settings()
    assert cfg.env == Environment.PRODUCTION
    assert cfg.default_tariff_inr == 9.75
    assert cfg.allow_db_reset is False
    assert cfg.is_production is True


# ==============================================================================
# 4. ROLE-BASED ACCESS CONTROL (RBAC) TESTS
# ==============================================================================

def test_rbac_role_hierarchy_and_permissions():
    """Verify hierarchical inheritance: Administrator > Approver > Analyst > Viewer."""
    assert has_minimum_role(required_role=Role.VIEWER, current_role=Role.ADMINISTRATOR) is True
    assert has_minimum_role(required_role=Role.ANALYST, current_role=Role.APPROVER) is True
    assert has_minimum_role(required_role=Role.ANALYST, current_role=Role.VIEWER) is False
    assert has_minimum_role(required_role=Role.APPROVER, current_role=Role.ANALYST) is False

    viewer_perms = get_role_permissions(Role.VIEWER)
    analyst_perms = get_role_permissions(Role.ANALYST)
    approver_perms = get_role_permissions(Role.APPROVER)
    admin_perms = get_role_permissions(Role.ADMINISTRATOR)

    assert Permission.VIEW_TELEMETRY in viewer_perms
    assert Permission.EXECUTE_SIMULATION not in viewer_perms
    assert Permission.EXECUTE_SIMULATION in analyst_perms
    assert Permission.EXECUTE_RECOMMENDATION not in analyst_perms
    assert Permission.EXECUTE_RECOMMENDATION in approver_perms
    assert Permission.SYSTEM_RESET in admin_perms
    assert Permission.SYSTEM_RESET not in approver_perms


def test_permission_decorator_enforcement():
    """Verify @require_permission blocks execution when active role lacks privilege."""
    @require_permission(Permission.SYSTEM_RESET)
    def admin_action():
        return "success"

    set_current_role(Role.VIEWER)
    with pytest.raises(PermissionError) as exc_info:
        admin_action()
    assert "Access Denied" in str(exc_info.value)

    set_current_role(Role.ADMINISTRATOR)
    assert admin_action() == "success"


# ==============================================================================
# 5. PROTECTED DATABASE RESET TESTS
# ==============================================================================

def test_protected_reset_blocked_for_non_admin(temp_db_env):
    """Verify reset_database raises PermissionError for Viewer and Analyst roles."""
    set_current_role(Role.ANALYST)
    with pytest.raises(PermissionError) as exc_info:
        reset_database(temp_db_env, confirmation_key="TEST_CONFIRM_KEY")
    assert "administrator privileges" in str(exc_info.value).lower() or "unauthorized" in str(exc_info.value).lower()


def test_protected_reset_requires_confirmation_token(temp_db_env):
    """Verify reset_database rejects invalid confirmation token."""
    set_current_role(Role.ADMINISTRATOR)
    with pytest.raises(ValueError) as exc_info:
        reset_database(temp_db_env, confirmation_key="WRONG_TOKEN")
    assert "Invalid reset confirmation key" in str(exc_info.value)


def test_protected_reset_blocked_in_production(temp_db_env, monkeypatch):
    """Verify reset is rejected in production if ECOPILOT_ALLOW_DB_RESET is false."""
    monkeypatch.setenv("ECOPILOT_ENV", "production")
    monkeypatch.setenv("ECOPILOT_ALLOW_DB_RESET", "false")
    cfg = Settings(environment="production", allow_db_reset=False, reset_confirm_key="SEC_KEY")
    set_config(cfg)

    set_current_role(Role.ADMINISTRATOR)
    with pytest.raises(PermissionError) as exc_info:
        reset_database(temp_db_env, confirmation_key="SEC_KEY")
    assert "Database reset is strictly blocked in production" in str(exc_info.value)


def test_protected_reset_success_and_audit_trail(temp_db_env):
    """Verify successful reset creates an entry in admin_audit_log."""
    set_current_role(Role.ADMINISTRATOR)
    res = reset_database(temp_db_env, confirmation_key="TEST_CONFIRM_KEY", operator="Lead Architect")
    assert res is True

    logs = DatabaseAdminRepository.get_admin_audit_logs(temp_db_env)
    assert len(logs) >= 1
    latest = logs[0]
    assert latest["action"] == "DATABASE_RESET"
    assert latest["operator"] == "Lead Architect"
    assert latest["status"] == "SUCCESS"


# ==============================================================================
# 6. MIGRATION RUNNER & SCHEMA TRACKING TESTS
# ==============================================================================

def test_migration_runner_applies_and_tracks(temp_db_env):
    """Verify run_migrations creates schema_migrations and logs applied versions."""
    run_migrations(temp_db_env)
    applied = get_applied_migrations(temp_db_env)
    applied_versions = [m["version"] for m in applied]

    assert 1 in applied_versions  # 001_initial_schema
    assert 2 in applied_versions  # 002_facility_and_run_attribution
    assert 3 in applied_versions  # 003_performance_indexes
    assert 4 in applied_versions  # 004_security_audit_logging

    # Re-running migrations should be idempotent
    run_migrations(temp_db_env)
    applied_after = get_applied_migrations(temp_db_env)
    assert len(applied_after) == len(applied)


# ==============================================================================
# 7. SERVICE & REPOSITORY LAYER INTEGRATION TESTS
# ==============================================================================

def test_energy_data_service_load_and_validate(temp_db_env):
    """Verify EnergyDataService processes valid CSV, logs upload, and returns typed quality report."""
    df = pd.DataFrame({
        "timestamp": pd.date_range("2026-01-01", periods=60, freq="h"),
        "energy_kwh": [30.0] * 60,
    })
    is_valid, err, cleaned, report = EnergyDataService.load_and_validate_csv(
        file_content_or_df=df,
        filename="test_upload.csv",
        record_upload_log=True,
        db_path=temp_db_env,
    )
    assert is_valid is True
    assert err is None
    assert len(cleaned) == 60
    assert report["health_score_pct"] == 100.0

    uploads = DatasetUploadRepository.get_all(temp_db_env)
    assert len(uploads) >= 1
    assert uploads[0]["filename"] == "test_upload.csv"


def test_recommendation_service_rbac_lifecycle(temp_db_env):
    """Verify RecommendationService enforces RBAC when approving and rejecting actions."""
    # Seed a recommendation via repository
    rec_data = {
        "id": "REC-TEST-001",
        "scenario": "normal",
        "title": "Optimize Chiller Setpoint",
        "category": "HVAC",
        "severity": "Medium",
        "priority_score": 65,
        "estimated_kwh_saving": 120.0,
        "estimated_inr_saving": 1020.0,
        "suggested_action": "Raise chilled water temperature by 1 C",
        "evidence": "Observed constant baseline",
        "assumptions": "Linear chiller COP",
        "status": "Pending",
        "facility_name": "Test Facility",
        "run_id": "RUN-001",
    }
    RecommendationRepository.upsert(rec_data, db_path=temp_db_env)

    # 1. Viewer cannot approve
    set_current_role(Role.VIEWER)
    with pytest.raises(PermissionError):
        RecommendationService.approve_recommendation("REC-TEST-001", operator="Viewer Operator", db_path=temp_db_env)

    # 2. Analyst cannot approve
    set_current_role(Role.ANALYST)
    with pytest.raises(PermissionError):
        RecommendationService.approve_recommendation("REC-TEST-001", operator="Analyst Operator", db_path=temp_db_env)

    # 3. Approver CAN approve
    set_current_role(Role.APPROVER)
    success = RecommendationService.approve_recommendation("REC-TEST-001", operator="Approver Operator", note="Approved for schedule", db_path=temp_db_env)
    assert success is True

    rec = RecommendationRepository.get_by_id("REC-TEST-001", db_path=temp_db_env)
    assert rec["status"] == "Approved"


def test_savings_simulator_service_rbac(temp_db_env):
    """Verify SavingsSimulatorService requires EXECUTE_SIMULATION permission."""
    set_current_role(Role.VIEWER)
    with pytest.raises(PermissionError):
        SavingsSimulatorService.archive_simulation(
            name="Chiller Optimization",
            baseline_kwh=1000.0,
            reduction_pct=10.0,
            tariff_inr=8.50,
            saved_kwh=100.0,
            saved_inr=850.0,
            avoided_kg_co2e=71.6,
            db_path=temp_db_env,
        )

    set_current_role(Role.ANALYST)
    sim_id = SavingsSimulatorService.archive_simulation(
        name="Chiller Optimization",
        baseline_kwh=1000.0,
        reduction_pct=10.0,
        tariff_inr=8.50,
        saved_kwh=100.0,
        saved_inr=850.0,
        avoided_kg_co2e=71.6,
        db_path=temp_db_env,
    )
    assert sim_id is not None
    sims = SimulationRepository.get_all(db_path=temp_db_env)
    assert len(sims) >= 1
