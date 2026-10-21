"""
EcoPilot AI: Centralized Configuration Management
Provides typed application settings with environment variable overrides,
strict validation, and environment profiles (development, test, production).
"""

from enum import Enum
from typing import Optional
import os
from pathlib import Path
from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Application-wide configuration parameters."""

    model_config = SettingsConfigDict(
        env_prefix="ECOPILOT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Runtime Environment
    environment: str = Field(
        default="development",
        validation_alias=AliasChoices("environment", "env", "ecopilot_environment", "ecopilot_env"),
        description="Runtime environment: development, test, production",
    )

    @property
    def env(self) -> Environment:
        val = self.environment.lower().strip()
        if "prod" in val:
            return Environment.PRODUCTION
        elif "test" in val:
            return Environment.TEST
        return Environment.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        return self.env == Environment.PRODUCTION

    # Database Configuration
    db_path: str = Field(
        default="data/ecopilot.db",
        validation_alias=AliasChoices("db_path", "ecopilot_db_path"),
        description="Path to primary SQLite database file.",
    )

    # Energy & Tariff Parameters
    default_tariff_inr_per_kwh: float = Field(
        default=8.50,
        validation_alias=AliasChoices(
            "default_tariff_inr_per_kwh",
            "default_tariff_inr",
            "tariff",
            "ecopilot_default_tariff_inr_per_kwh",
            "ecopilot_default_tariff_inr",
            "ecopilot_tariff",
        ),
        description="Default electricity tariff in INR per kWh.",
    )

    @property
    def default_tariff_inr(self) -> float:
        return self.default_tariff_inr_per_kwh

    default_carbon_factor_key: str = Field(
        default="India (CEA National Weighted Average)",
        validation_alias=AliasChoices(
            "default_carbon_factor_key",
            "grid_emission_factor",
            "ecopilot_grid_emission_factor",
            "ecopilot_default_carbon_factor_key",
        ),
        description="Default emission factor key for avoided emissions calculations.",
    )

    @property
    def grid_emission_factor(self) -> str:
        return self.default_carbon_factor_key

    # Telemetry Ingestion & Quality Thresholds
    max_allowed_upload_rows: int = Field(
        default=500000,
        description="Maximum allowed rows in uploaded CSV telemetry files.",
    )
    max_consecutive_missing_hours: int = Field(
        default=24,
        description="Maximum contiguous missing hours permitted before rejecting a dataset.",
    )
    min_required_reading_hours: int = Field(
        default=48,
        description="Minimum hours required for baseline and anomaly detection.",
    )

    # Anomaly Detection Defaults
    default_anomaly_sensitivity_std: float = Field(
        default=2.4,
        validation_alias=AliasChoices(
            "default_anomaly_sensitivity_std",
            "anomaly_sensitivity_std",
            "ecopilot_default_anomaly_sensitivity_std",
            "ecopilot_anomaly_sensitivity_std",
        ),
        description="Z-score sensitivity multiplier for anomaly thresholding.",
    )
    default_min_absolute_diff_kwh: float = Field(
        default=6.0,
        description="Minimum absolute surplus kWh required to trigger an anomaly alert.",
    )

    # Forecasting Engine Defaults
    forecast_test_hours: int = Field(default=72, description="Test split duration in hours.")
    forecast_val_hours: int = Field(default=48, description="Validation split duration in hours.")
    forecast_random_state: int = Field(default=42, description="Random seed for model training.")

    # Security & Role-Based Access Control
    default_role: str = Field(
        default="administrator",
        description="Default active session role (viewer, analyst, approver, administrator).",
    )
    allow_db_reset: bool = Field(
        default=False,
        validation_alias=AliasChoices("allow_db_reset", "ecopilot_allow_db_reset"),
        description="Whether destructive database reset operations are permitted in this environment.",
    )
    reset_confirm_key: str = Field(
        default="CONFIRM_RESET_DATA",
        validation_alias=AliasChoices("reset_confirm_key", "ecopilot_reset_confirm_key", "confirmation_key"),
        description="Required safety token string to authorize database reset operations.",
    )


_SETTINGS_INSTANCE: Optional[Settings] = None


def get_config(reload: bool = False) -> Settings:
    """
    Retrieve or initialize the singleton application settings instance.
    Pass reload=True to force re-reading from environment variables.
    """
    global _SETTINGS_INSTANCE
    if _SETTINGS_INSTANCE is None or reload:
        # Check fallback ECOPILOT_DB_PATH
        env_db = os.getenv("ECOPILOT_DB_PATH")
        env_tariff = os.getenv("ECOPILOT_TARIFF")

        kwargs = {}
        if env_db:
            kwargs["db_path"] = env_db
        if env_tariff:
            try:
                kwargs["default_tariff_inr_per_kwh"] = float(env_tariff)
            except ValueError:
                pass

        _SETTINGS_INSTANCE = Settings(**kwargs)
    return _SETTINGS_INSTANCE


def set_config(settings: Settings) -> None:
    """Set or override the active configuration instance (e.g. for testing)."""
    global _SETTINGS_INSTANCE
    _SETTINGS_INSTANCE = settings
