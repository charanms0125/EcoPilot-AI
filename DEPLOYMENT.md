# EcoPilot AI — Production Deployment & Operational Runbook

This guide covers operational best practices, architecture, configuration, database migrations, security policies, and production deployment procedures for EcoPilot AI.

---

## 1. System Architecture

EcoPilot AI employs a layered, service-oriented architecture designed for deterministic, verifiable, offline execution:

```
                           +----------------------------+
                           |  Streamlit Web Dashboard   |
                           |          (app.py)          |
                           +--------------+-------------+
                                          |
                      +-------------------+-------------------+
                      |                                       |
                      v                                       v
         +-------------------------+             +--------------------------+
         |      Service Layer      |             |   Role-Based Access      |
         |    (src/services.py)    |             |   Control (src/auth.py)  |
         +------------+------------+             +--------------------------+
                      |
         +------------+---------------------------------------+
         |            |                   |                   |
         v            v                   v                   v
+--------------+ +---------------+ +---------------+ +------------------+
| EnergyData-  | | Analytics-    | | Recommendation| | Verification-    |
| Service      | | Service       | | Service       | | Service          |
+-------+------+ +-------+-------+ +-------+-------+ +--------+---------+
        |                |                 |                  |
        +----------------+--------+--------+------------------+
                                  |
                                  v
                     +--------------------------+
                     |    Repository Layer      |
                     |  (src/repositories.py)   |
                     +------------+-------------+
                                  |
                                  v
                     +--------------------------+
                     |   SQLite WAL Database    |
                     |   (schema_migrations)    |
                     +--------------------------+
```

### Core Subsystems:
1. **Presentation (`app.py`):** Interactive Streamlit dashboard with 8 modular views.
2. **Services (`src/services.py`):** Encapsulates business logic, data validation, forecasting pipelines, and verification routines.
3. **Repositories (`src/repositories.py`):** Isolates SQLite data persistence and relational query logic with foreign key enforcement and transactional safety.
4. **Data Contract / Validation (`src/schemas.py`):** Strongly-typed Pydantic schemas validating inputs, outputs, telemetry quality, and audit logs.
5. **Authorization (`src/auth.py`):** Granular Role-Based Access Control (RBAC) with hierarchical privilege checks.
6. **Central Configuration (`src/config.py`):** Environment-driven settings with validation, profiles, and sensible defaults.
7. **Database Migrations (`src/database.py`):** Version-controlled schema migrations with atomic execution and transaction rollbacks.

---

## 2. Environment Profiles & Configuration

All application configuration is centralized in `src/config.py` and configurable via environment variables (`ECOPILOT_*`):

### Supported Profiles:
- **`development`** (default): Standard local development with SQLite foreign keys enabled and non-strict reset protections.
- **`test`**: Automated test suite environment.
- **`production`**: Strict production enforcement. In production:
  - Database reset operations are completely locked unless `ECOPILOT_ALLOW_DB_RESET=true` is explicitly set.
  - Reset requires administrative privileges and a verified token key (`ECOPILOT_RESET_CONFIRM_KEY`).
  - High anomaly detection sensitivity and audit trail integrity are enforced.

### Environment Variable Reference:

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `ECOPILOT_ENV` | String | `development` | Target environment profile (`development`, `test`, `production`). |
| `ECOPILOT_DB_PATH` | Path | `ecopilot.db` | Absolute or relative path to the SQLite persistence file. |
| `ECOPILOT_DEFAULT_TARIFF_INR` | Float | `8.50` | Commercial electricity tariff in INR per kWh. |
| `ECOPILOT_GRID_EMISSION_FACTOR` | String | `India (CEA National Weighted Average)` | Official reference factor for avoided CO2e calculations. |
| `ECOPILOT_DEFAULT_ANOMALY_SENSITIVITY_STD` | Float | `2.4` | Z-score threshold for anomaly sensitivity. |
| `ECOPILOT_ALLOW_DB_RESET` | Boolean | `false` | Production master kill-switch for database reset. |
| `ECOPILOT_RESET_CONFIRM_KEY` | String | `CONFIRM_RESET_DATA` | Secret passphrase required to initiate database reset. |
| `ECOPILOT_APP_HOST` | String | `0.0.0.0` | Binding host address for web server. |
| `ECOPILOT_APP_PORT` | Integer | `8501` | Listening port for web server. |

Example `.env` production file:
```ini
ECOPILOT_ENV=production
ECOPILOT_DB_PATH=/var/data/ecopilot/ecopilot_prod.db
ECOPILOT_DEFAULT_TARIFF_INR=8.50
ECOPILOT_GRID_EMISSION_FACTOR="India (CEA National Weighted Average)"
ECOPILOT_ALLOW_DB_RESET=false
ECOPILOT_RESET_CONFIRM_KEY="prod-secure-token-998822"
ECOPILOT_APP_HOST=0.0.0.0
ECOPILOT_APP_PORT=8501
```

---

## 3. Database Migrations Guide

The database management subsystem automatically tracks and applies schema migrations in sequence:

### Migration Registry:
- **`001_initial_schema`**: Base tables (`recommendations`, `audit_log`, `simulations`, `anomalies`, `verifications`, `dataset_uploads`).
- **`002_facility_and_run_attribution`**: Multi-facility and run-scoped isolation columns (`run_id`, `facility_name`).
- **`003_performance_indexes`**: Targeted composite indexes on `facility_name`, `status`, `created_at`, `timestamp`.
- **`004_security_audit_logging`**: Enterprise administrative audit logging (`admin_audit_log`) with role, action, target, and status.

### Running Migrations:
Migrations execute automatically on application startup via `init_db()`. To inspect or execute migrations programmatically:

```python
from src.database import run_migrations, get_applied_migrations

# Run pending migrations
run_migrations()

# Check applied migrations
migrations = get_applied_migrations()
for m in migrations:
    print(f"Applied: {m['version']} - {m['name']} at {m['applied_at']}")
```

### Safety & Transaction Isolation:
- SQLite `PRAGMA foreign_keys = ON;` is enforced on every connection.
- SQLite `PRAGMA journal_mode = WAL;` (Write-Ahead Logging) is enabled for high concurrency.
- Migrations run in an atomic transaction; any failure triggers an immediate rollback.

---

## 4. Role-Based Access Control (RBAC)

EcoPilot AI enforces a 4-tier hierarchical access model:

| Role | Hierarchy Weight | Allowed Capabilities |
| :--- | :---: | :--- |
| **`VIEWER`** | 1 | Read telemetry, inspect anomaly charts, view forecasting and public verification history. |
| **`ANALYST`** | 2 | All Viewer capabilities + Run what-if simulations, adjust sensitivity parameters, upload datasets, and archive simulation outcomes. |
| **`APPROVER`** | 3 | All Analyst capabilities + Approve, reject, and mark recommendations as completed with operator audit trail. |
| **`ADMINISTRATOR`** | 4 | All Approver capabilities + Full database maintenance, configuration overrides, and protected database reset. |

### Enforcing Authorization in Services:
Services annotate critical business operations with the `@require_permission` decorator or call `check_permission()`:

```python
from src.auth import require_permission, Permission

@require_permission(Permission.EXECUTE_RECOMMENDATION)
def approve_recommendation(rec_id: str, operator: str, note: str):
    # Only Approver and Administrator can execute
    ...
```

---

## 5. Production Hardening & Operational Runbook

### Protected Database Reset
Accidental data deletion is prevented through multiple independent safeguards:
1. **Role Check:** Must hold `ADMINISTRATOR` role.
2. **Environment Protection:** If `ECOPILOT_ENV=production`, reset is blocked unless `ECOPILOT_ALLOW_DB_RESET=true` is set in the environment.
3. **Secret Token Verification:** The caller must supply the matching `confirmation_key`.
4. **Audit Logging:** Every attempt (successful or rejected) is recorded in `admin_audit_log`.

### Automated Backup Procedure:
Before executing manual schema upgrades or major server maintenance, snapshot the SQLite database file:

```bash
# SQLite online safe backup
sqlite3 /var/data/ecopilot/ecopilot_prod.db ".backup '/var/backups/ecopilot_$(date +%Y%m%d_%H%M%S).db'"
```

---

## 6. Docker & Container Deployment

### Production Dockerfile:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency requirements
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Copy application source
COPY . .

# Set production environment defaults
ENV ECOPILOT_ENV=production
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ENABLE_CORS=false
ENV STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=true

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

EXPOSE 8501

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Running with Docker Compose:
```yaml
version: '3.8'

services:
  ecopilot:
    build: .
    container_name: ecopilot-ai
    restart: unless-stopped
    ports:
      - "8501:8501"
    environment:
      - ECOPILOT_ENV=production
      - ECOPILOT_DB_PATH=/data/ecopilot.db
      - ECOPILOT_ALLOW_DB_RESET=false
    volumes:
      - ecopilot-data:/data

volumes:
  ecopilot-data:
```

---

## 7. Quality Assurance & Continuous Testing

Run the test suite, linting, formatting, and coverage checks:

```bash
# Run all tests
python -m pytest

# Run with test coverage
python -m pytest --cov=src --cov-report=term-missing

# Linting with Ruff
ruff check src/

# Formatting check with Black
black --check src/ app.py
```
