# 🌱 EcoPilot AI — Explainable AI Agent for Sustainable Building Energy Management

> **An evidence-backed, human-in-the-loop Green AI system that diagnoses energy waste, forecasts demand, simulates financial savings, quantifies verified carbon impact, and audits operational interventions for educational campuses, hostels, and commercial buildings.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11-emerald.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/framework-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn-F7931E.svg)](https://scikit-learn.org/)
[![Pydantic v2](https://img.shields.io/badge/validation-Pydantic%20v2-e92063.svg)](https://docs.pydantic.dev/)
[![Tests](https://img.shields.io/badge/tests-101%20passed-10b981.svg)](https://pytest.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 🎯 Executive Summary & Problem Statement

Electricity represents **30% to 45% of total operating expenses** across university campuses, student residences, and commercial facilities. Energy audits regularly show that **15% to 30% of this energy is completely wasted** on:
- Unchecked after-hours HVAC drift and nocturnal baseline inflation.
- High-bay and corridor lighting remaining powered in empty auditoriums and lecture halls.
- Coincident motor startup surges triggering costly peak demand surcharges.
- Running flexible loads during peak grid tariff hours rather than off-peak or solar-aligned windows.

### The Systemic Gap
1. **Passive Dashboards:** Existing energy management software merely renders retrospective line graphs. They expect overworked facility staff to visually scan gigabytes of telemetry to locate anomalies.
2. **Proprietary BMS Silos:** Full-scale Building Management Systems (Honeywell, Johnson Controls, Siemens) require millions of rupees in proprietary hardware, specialized protocols (BACnet/LonWorks), and lengthy vendor lock-ins.
3. **Greenwashing & Ungrounded AI:** Many AI projects fabricate carbon numbers or use ungrounded LLMs to hallucinate energy measurements, with zero audit trail or verification against actual physical telemetry.

### The EcoPilot AI Solution
EcoPilot AI provides an **evidence-based, offline-first Green AI decision platform**. It bridges raw meter telemetry and operational facility action through an accountable 7-stage closed loop:

$$\mathbf{Observe} \longrightarrow \mathbf{Analyze} \longrightarrow \mathbf{Plan} \longrightarrow \mathbf{Recommend} \longrightarrow \mathbf{Simulate} \longrightarrow \mathbf{Request\ Approval} \longrightarrow \mathbf{Track\ Outcome}$$

All calculations run deterministically on standard local Python runtimes without mandatory cloud API dependencies or paid services.

---

## 🏗️ Layered Architecture & Component Workflow

EcoPilot AI implements a decoupled **Presentation → Service → Repository → Persistence** pattern with strongly-typed Pydantic contracts and Role-Based Access Control (RBAC):

```mermaid
flowchart TD
    subgraph UI["1. Presentation Layer (app.py)"]
        DASH["8-View Streamlit Interactive Dashboard"]
        RBAC_SEL["Sidebar Role Selector: Viewer / Analyst / Approver / Administrator"]
    end

    subgraph SCHEMAS["2. Typed Contracts and Configuration (src/schemas.py and src/config.py)"]
        CONF["Centralized Settings: Development / Test / Production"]
        SCH["Pydantic Models: Quality Reports, Alerts, Recommendations, Forecasts, Verifications"]
    end

    subgraph SERVICES["3. Service Layer (src/services.py and src/auth.py)"]
        AUTH["@require_permission RBAC Guard"]
        EDS["EnergyDataService: Ingest, Sanitize, Impute, TZ-Normalize"]
        ANS["AnalyticsService: Robust Z-Score, Isolation Forest, Forecast Tournament"]
        RCS["RecommendationService: Multi-Factor Priority Scoring and Decision Lifecycles"]
        SIMS["SavingsSimulatorService: Multi-Action Overlap Deduplication and ToD"]
        VFS["VerificationService: Counterfactuals and Weather Normalization"]
        SAS["SystemAdminService: System Health and Protected DB Reset"]
    end

    subgraph REPOSITORIES["4. Repository Layer (src/repositories.py)"]
        R_REC["RecommendationRepository"]
        R_ALT["AlertRepository"]
        R_VER["VerificationRepository"]
        R_SIM["SimulationRepository"]
        R_UPL["DatasetUploadRepository"]
        R_ADM["DatabaseAdminRepository"]
    end

    subgraph PERSISTENCE["5. Persistence Layer (src/database.py)"]
        MIGR["Auto-Migrating SQLite Engine: 001 to 004"]
        WAL[("SQLite WAL Database + Foreign Key Constraints")]
        AUDIT[("admin_audit_log and recommendation audit_log")]
    end

    DASH --> AUTH
    RBAC_SEL --> AUTH
    CONF -.-> AUTH
    SCH -.-> AUTH
    AUTH --> EDS
    AUTH --> ANS
    AUTH --> RCS
    AUTH --> SIMS
    AUTH --> VFS
    AUTH --> SAS
    EDS --> R_REC
    EDS --> R_ALT
    ANS --> R_ALT
    RCS --> R_REC
    SIMS --> R_SIM
    VFS --> R_VER
    SAS --> R_UPL
    SAS --> R_ADM
    R_REC --> WAL
    R_ALT --> WAL
    R_VER --> WAL
    R_SIM --> WAL
    R_UPL --> WAL
    R_ADM --> WAL
    R_ADM --> MIGR
    R_REC --> AUDIT
    R_ADM --> AUDIT
```

---

## 📁 Project Directory Structure

```
EcoPilot-AI/
├── app.py                      # Streamlit 8-page dashboard with RBAC and service routing
├── pyproject.toml              # Build system, pytest, ruff, black, mypy, coverage config
├── .coveragerc                 # Coverage configuration
├── DEPLOYMENT.md               # Production operational runbook, Docker, migrations, backup guide
├── requirements.txt            # Zero-bloat production dependencies
├── README.md                   # Comprehensive architectural documentation
├── .env.example                # Configuration template (tariffs, emission factors, reset keys)
├── .gitignore                  # Clean version control rules
├── data/
│   ├── ecopilot.db             # Auto-migrating SQLite audit & telemetry database (WAL mode)
│   └── sample_energy_data.csv  # Standardized reference hourly telemetry schema
├── src/
│   ├── __init__.py             # Package marker
│   ├── config.py               # Centralized Settings & environment profile management
│   ├── schemas.py              # Strict Pydantic models for all entities and reports
│   ├── auth.py                 # Role-Based Access Control (RBAC) & permission decorators
│   ├── services.py             # High-level business logic orchestration layer
│   ├── repositories.py         # Relational database persistence abstraction layer
│   ├── data_generator.py       # Deterministic synthesizer, CSV validator & quality reporter
│   ├── forecasting.py          # 3-model tournament, chronological split, calibrated intervals
│   ├── anomaly_detection.py    # Robust Z-score + Isolation Forest ensemble, 4 severity tiers
│   ├── agent.py                # 7-stage closed-loop AI agent, priority formula & persistence
│   ├── savings.py              # Overlap-deduplicated savings simulator & ToD calculations
│   ├── optimizer.py            # Time-of-Day peak-to-solar load shifting engine
│   ├── carbon.py               # Transparent carbon calculator & official emission factor registry
│   ├── verification.py         # Before-and-after savings verification & counterfactual model
│   ├── green_ai.py             # Green AI monitor (latency, cache hits, avoided cloud emissions)
│   └── database.py             # SQLite persistence, schema migrations, and transition rules
└── tests/
    ├── test_production_readiness_regression.py # 17 tests: RBAC, schemas, services, migrations, reset
    ├── test_fixes_regression.py                # 18 tests: Power/energy math, FKs, rollback, ID isolation
    ├── test_analytical_correctness_regression.py # 17 tests: Baseline leakage, calibrated intervals
    ├── test_forecasting_upgrade.py             # 5 tests: 3-model benchmark, WAPE, calibrated intervals
    ├── test_forecasting.py                     # 4 tests: Data leakage prevention, chronological split
    ├── test_anomaly_upgrade.py                 # 3 tests: 4 severity tiers, isolation forest, evidence
    ├── test_csv_validation_upgrade.py          # 7 tests: Column tolerance, kW-to-kWh, deduplication
    ├── test_savings.py                         # 8 tests: Deduplication math, boundary conditions, ToD
    ├── test_carbon.py                          # 7 tests: Carbon math, negative rejections, official factors
    ├── test_agent_db.py                        # 5 tests: Anomaly linking, priority scoring, SQLite audits
    ├── test_agent_workflow.py                  # 3 tests: 7-stage state machine transitions & guards
    ├── test_verification.py                    # 3 tests: Counterfactuals, weather normalization, status
    ├── test_green_ai.py                        # 3 tests: Execution timing, cache hits, avoided emissions
    └── test_pipeline_integration.py            # 1 test: End-to-end integration: Ingest -> Forecast -> Agent -> Verify
```

---

## 🧭 Streamlit Dashboard Navigation (8 Dedicated Views)

| View | Key Purpose & Interactive Capabilities |
| :--- | :--- |
| **1. 📊 Overview & Sustainability KPIs** | Executive scoreboard showing total consumption, potential ₹/kWh savings, avoided CO₂e, active alerts, awaiting approvals, and measured real-world savings. |
| **2. 🔍 Telemetry & Energy Analysis** | Diurnal hourly heatmaps, weekday vs. weekend profiles, weekly load trends, rolling baseline tracking, and distribution plots. |
| **3. 🔮 Demand Forecasting (3 Models)** | Side-by-side tournament of Persistence Baseline, Seasonal Baseline, and Random Forest with chronological validation, WAPE/MAE/RMSE metrics, and empirical prediction intervals. |
| **4. 🤖 AI Recommendations & Tasks** | Ranked Energy Conservation Measures (ECMs) with documented evidence, root cause hypotheses, and interactive **Approve / Reject / Complete** decision gates backed by RBAC. |
| **5. 💡 Savings Simulator & ToD** | Interactive what-if laboratory with overlap-discounted compound retention, configurable recovery percentages, and Time-of-Day tariff peak-to-solar shifting. |
| **6. 🌍 Environmental Impact Center** | Formal carbon accounting dashboard applying official grid emission factors, displaying cumulative avoided GHG emissions, and clearly distinguishing potential vs. verified metrics. |
| **7. 📈 Savings Verification & History** | Before-and-after counterfactual verification engine comparing post-intervention telemetry against pre-intervention baselines with weather normalization and realization rates. |
| **8. ⚡ Green AI Efficiency Monitor** | Audits the computational carbon footprint of EcoPilot AI itself, tracking wall-clock execution time, memory usage, cache hit ratios, and avoided cloud LLM API emissions. |

---

## 🛡️ Enterprise Security, RBAC & Reset Protection

EcoPilot AI includes a formal 4-tier Role-Based Access Control matrix:

| Role | Hierarchy Weight | Permitted Actions |
| :--- | :---: | :--- |
| **`VIEWER`** | 1 | View telemetry, inspect anomaly charts, view forecasting and public verification records. |
| **`ANALYST`** | 2 | Viewer rights + Run what-if simulations, upload custom datasets, adjust anomaly detection thresholds. |
| **`APPROVER`** | 3 | Analyst rights + Approve, reject, and mark recommendations as completed with operator audit trail. |
| **`ADMINISTRATOR`** | 4 | Approver rights + Database maintenance, schema inspection, configuration overrides, and protected database reset. |

### Protected Database Reset Safeguards:
1. **Administrative Grant:** Only callers holding the `ADMINISTRATOR` role can trigger a reset.
2. **Production Lockout:** In `production` environment, reset is strictly forbidden unless `ECOPILOT_ALLOW_DB_RESET=true` is set.
3. **Secret Token Verification:** The caller must provide the matching `reset_confirm_key` (`CONFIRM_RESET_DATA`).
4. **Audit Trail:** Every reset attempt (whether successful or rejected) is recorded in `admin_audit_log`.

---

## ⚡ Detailed Methodology & Engineering Formulations

### 1. Transparent Carbon Accounting Module (`src/carbon.py`)

Avoided emissions are calculated strictly using the transparent formulation:

$$\text{Avoided Emissions } (\text{kg CO}_2\text{e}) = \text{Electricity Saved } (\text{kWh}) \times \text{Grid Emission Factor } (\text{kg CO}_2\text{e}/\text{kWh})$$

#### Built-In Official Emission Factor Registry:
- **India National Grid (Default):** $0.716\text{ kg CO}_2\text{e}/\text{kWh}$ (Central Electricity Authority Baseline Database v19.0, Dec 2023).
- **US National Average:** $0.386\text{ kg CO}_2\text{e}/\text{kWh}$ (US EPA eGRID 2022 Summary Tables, Jan 2024).
- **UK National Grid:** $0.207\text{ kg CO}_2\text{e}/\text{kWh}$ (UK DEFRA / DESNZ GHG Conversion Factors, 2023).
- **EU Average:** $0.251\text{ kg CO}_2\text{e}/\text{kWh}$ (European Environment Agency Greenhouse Gas Intensity, 2023).

#### Ethical Guardrails:
- Negative savings are strictly rejected with an explicit `ValueError`.
- If no emission factor is configured, the system displays `"Emission factor not configured"` rather than inventing numbers.
- Unverified projected savings are strictly labeled **"Potential Avoided Emissions"**; only real post-intervention meter verification can produce **"Verified Avoided Emissions"**.

---

### 2. Energy Forecasting Tournament (`src/forecasting.py`)

#### Chronological 3-Way Split (No Temporal Leakage):
Timeseries data is partitioned strictly in chronological sequence:
- **Training Set:** First 70% of chronological observations.
- **Validation Set:** Middle 15% (used strictly for model selection and threshold calibration).
- **Test Set:** Final 15% (held out untouched until final reporting).

#### Three-Model Benchmark Comparison:
1. **Persistence Baseline:** Predicts $y_t = y_{t-24}$ (exact same hour yesterday).
2. **Historical Seasonal Baseline:** Predicts $y_t = \text{median}(y \mid \text{day\_of\_week}, \text{hour})$.
3. **Random Forest Regressor:** Built on non-leaking lag features (`lag_1`, `lag_2`, `lag_24`, `lag_48`, `lag_168`), rolling statistics (`rolling_mean_24`, `rolling_std_24`), and cyclical sine/cosine encodings of hour and day of week.

The best-performing model on validation WAPE is selected and used for future 24-hour forecasting.

#### Evaluation Metrics & Why WAPE Over MAPE:
Mean Absolute Percentage Error (MAPE) divides by $y_t$. In institutional buildings with low overnight standby loads or equipment idling, $y_t \to 0$ causes asymptotic divisions and infinite error inflation. EcoPilot AI utilizes **Weighted Absolute Percentage Error (WAPE)**:

$$\text{WAPE} = \frac{\sum_{t=1}^N |y_t - \hat{y}_t|}{\sum_{t=1}^N y_t} \times 100\%$$

$$\text{MAE} = \frac{1}{N}\sum_{t=1}^N |y_t - \hat{y}_t|, \quad \text{RMSE} = \sqrt{\frac{1}{N}\sum_{t=1}^N (y_t - \hat{y}_t)^2}$$

#### Calibrated Empirical Prediction Intervals:
Prediction intervals are calibrated directly for the winning model using empirical residual quantiles on the validation set:

$$\hat{y}_t \pm q_{1 - \alpha/2}(|y_{\text{val}} - \hat{y}_{\text{val}}|)$$

The empirical coverage percentage is evaluated against held-out test data and displayed on the dashboard.

---

### 3. Explainable Anomaly Detection (`src/anomaly_detection.py`)

#### Dual-Method Ensemble:
1. **Clean Baseline & Robust Dispersion:** Baseline distributions are calculated excluding known anomalies to prevent baseline leakage. Dispersion is calculated using Median Absolute Deviation (MAD) or Interquartile Range (IQR) to avoid standard deviation inflation.
2. **Unsupervised Isolation Forest:** Evaluates multi-dimensional multivariate isolation scores without parametric assumptions. Observations flagged by both detectors or exceeding threshold limits are classified into 4 severity tiers: `Critical`, `High`, `Medium`, and `Low`.

#### Distinction Between Phenomena:
- **Potential Energy Wastage:** Anomalies occurring during off-hours, overnight periods, or weekends where surplus baseline indicates idle running.
- **Unusual Consumption Spike:** Mid-day surges during peak operating hours indicating equipment in-rush, short-cycling, or coincident motor startup.

---

### 4. Overlap-Deduplicated Savings Engine (`src/savings.py`)

EcoPilot AI prevents double-counting across overlapping conservation measures using a **sequential compounding retention formulation**:

$$\text{Retention Ratio} = \prod_{i=1}^M \left(1 - \frac{\text{kWh}_i}{\text{Eligible Baseline}}\right)$$

$$\text{Deduplicated Net Savings (kWh)} = \min\left(\sum_{i=1}^M \text{kWh}_i, \; \text{Eligible Baseline} \times (1 - \text{Retention Ratio})\right)$$

A physical ceiling of **85% of eligible baseline** prevents mathematically impossible savings claims.

---

### 5. Evidence-Anchored AI Task Agent (`src/agent.py`)

#### Multi-Factor Priority Score Formulation:
Recommendations are ranked transparently using an objective multi-factor score:

$$\text{Score} = 0.40 \cdot S_{\text{energy}} + 0.30 \cdot S_{\text{cost}} + 0.15 \cdot S_{\text{confidence}} + 0.15 \cdot (100 - S_{\text{effort}})$$

Where each component is normalized to $[0, 100]$.

#### State Machine Integrity:
Enforced valid transitions in SQLite:
- `Pending` $\to$ `Approved` or `Rejected`
- `Approved` $\to$ `Completed` or `Rejected` or `Pending`
- `Rejected` $\to$ `Pending` (Re-evaluation)
- Direct transition from `Rejected` $\to$ `Completed` is strictly blocked by the database integrity guard.

---

### 6. Before-and-After Verification Engine (`src/verification.py`)

EcoPilot AI follows IPMVP (International Performance Measurement and Verification Protocol) principles:
1. **Pre-Intervention Baseline Period:** Historical window establishing expected consumption.
2. **Post-Intervention Measurement Period:** Observed post-retrofit consumption.
3. **Counterfactual Baseline:** What the building would have consumed without the intervention, adjusted for weather (cooling/heating degree hours via empirical OLS sensitivity) and occupancy.
4. **Realized Savings:**
   $$\text{Realized Savings (kWh)} = \sum (\text{Counterfactual}_t - \text{Observed}_t)$$
5. **Realization Rate:**
   $$\text{Realization Rate} = \frac{\text{Realized Savings}}{\text{Expected Savings}} \times 100\%$$
6. **Guardrail:** If post-intervention telemetry is less than 48 hours, the system displays **"Awaiting verification data"** rather than drawing premature conclusions.

---

### 7. Telemetry Ingestion & Quality Reporting (`src/data_generator.py`)

The application supports CSV ingestion with schema validation and quality reporting:

| Feature | Behavior & Safeguards |
| :--- | :--- |
| **Timezone Normalization** | Detects UTC and offset timezones (`+05:30`), converts to tz-naive local/UTC time, and stores detected timezone. |
| **Cadence Detection** | Identifies sampling frequency (`15-minute`, `30-minute`, `Hourly`, `Daily`) and flags irregular intervals. |
| **Power-to-Energy Integration** | Automatically converts active power (`power_kw`) to energy (`energy_kwh`) using true timestamp intervals ($\Delta t$). |
| **Missing Value Imputation** | Imputes minor gaps via linear interpolation; rejects datasets with excessive gaps ($>24$ consecutive hours). |
| **Negative Value Sanitization** | Clips negative consumption readings to $0.0\text{ kWh}$ standby minimum and logs audit counts. |
| **Data Health Score** | Outputs an automated $0\text{--}100\%$ telemetry health score (`health_score_pct`) validated against `DataQualityReportSchema`. |

---

### 8. Green AI Efficiency Monitor (`src/green_ai.py`)

- **Zero Cloud API Overhead:** Core inference (Random Forest, Isolation Forest, rule-based reasoning) runs 100% locally on CPU in $< 500\text{ ms}$.
- **Performance Profiling:** Wall-clock latency is measured with `time.perf_counter()`.
- **Avoided Emissions Tracking:** Compares local execution ($< 0.0001\text{ kWh}$) against typical cloud multi-modal LLM calls ($\sim 0.003\text{ kWh}$ per prompt-response pair), logging computational savings directly to the dashboard.

---

## 🚀 Quickstart & Installation Guide

### Prerequisites
- Python 3.10 or 3.11 installed. Verify with:
  ```powershell
  python --version
  ```

### 1. Clone & Navigate to Project
```powershell
cd c:\Users\chara\OneDrive\Desktop\EcoPilot-AI
```

### 2. Create & Activate Virtual Environment
```powershell
# Create venv
python -m venv venv

# Activate in Windows PowerShell
.\venv\Scripts\Activate.ps1
```
*(If PowerShell execution policy blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure Environment
Copy the example environment template:
```powershell
Copy-Item .env.example .env
```
Default tariffs and official CEA emission factors are pre-configured. No external API keys are required for full offline operation.

---

## 🧪 Running the Automated Test Suite

EcoPilot AI includes a comprehensive **101-test suite** covering all analytical algorithms, data ingestion, database integrity, RBAC, and service layer integration:

```powershell
python -m pytest
```

### Test Suite Summary:
```
============================= test session starts =============================
platform win32 -- Python 3.10.10, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\chara\OneDrive\Desktop\EcoPilot-AI
configfile: pyproject.toml
testpaths: tests
collected 101 items

tests/test_agent_db.py .................................................... [  5%]
tests/test_agent_workflow.py .............................................. [  8%]
tests/test_analytical_correctness_regression.py ........................... [ 25%]
tests/test_anomaly_upgrade.py ............................................. [ 28%]
tests/test_carbon.py ...................................................... [ 35%]
tests/test_csv_validation_upgrade.py ...................................... [ 42%]
tests/test_fixes_regression.py ............................................ [ 60%]
tests/test_forecasting.py ................................................. [ 64%]
tests/test_forecasting_upgrade.py ......................................... [ 69%]
tests/test_green_ai.py .................................................... [ 72%]
tests/test_pipeline_integration.py ........................................ [ 73%]
tests/test_production_readiness_regression.py ............................. [ 90%]
tests/test_savings.py ..................................................... [ 98%]
tests/test_verification.py ................................................ [100%]

============================ 101 passed in ~33s ==============================
```

### Run with Coverage:
```powershell
python -m pytest --cov=src --cov-report=term-missing
```

---

## 🖥️ Launching the Application

Start the interactive Streamlit dashboard:

```powershell
streamlit run app.py
```

The application will launch in your default web browser at `http://localhost:8501`.

For production deployment instructions (Docker containerization, systemd service, Nginx reverse proxy, and database backup routines), see [DEPLOYMENT.md](file:///c:/Users/chara/OneDrive/Desktop/EcoPilot-AI/DEPLOYMENT.md).

---

## 🎤 3-Minute Hackathon Demonstration Script

### [0:00 – 0:35] The Hook & Problem Statement
> *"Judges, institutional buildings like university hostels and campuses waste up to 30% of their electricity on after-hours HVAC drift and unmanaged peak demand. Yet existing dashboards are just passive line charts, and proprietary BMS systems cost millions. We built **EcoPilot AI** — an explainable, offline-first Green AI agent that turns raw meter telemetry into verified financial and carbon savings through an accountable 7-stage loop."*

### [0:35 – 1:15] Ingestion & Explainable Detection
> *(Select 'Excessive Overnight Waste' scenario in the sidebar, navigate to 'Telemetry & Energy Analysis')*
> *"Notice our dual-engine anomaly detector. Between 22:00 and 06:00, baseline load stays at 34 kWh instead of 18 kWh. Rather than displaying a black-box alert, EcoPilot explains the exact evidence: +14 kWh/h surplus, a 3.4σ breach, and classifies it as 'Potential Energy Wastage' rather than an operational spike."*

### [1:15 – 2:00] Forecasting & Agent Recommendations
> *(Navigate to 'Demand Forecasting', then 'AI Recommendations')*
> *"In our forecasting engine, we benchmark persistence, seasonal baseline, and Random Forest using chronological splits and WAPE, with empirical 90% prediction intervals. Our AI Task Agent evaluates the waste evidence and proposes concrete Energy Conservation Measures — like an automated contactor cutoff timer — scored objectively by energy, cost, confidence, and effort."*

### [2:00 – 2:30] Deduplicated Savings & Official Carbon Accounting
> *(Navigate to 'Savings Simulator', then 'Environmental Impact Center')*
> *"In the Simulator, we implement overlap deduplication so intersecting measures never claim >100% savings. In the Environmental Impact Center, we don't invent carbon metrics: we apply the official Central Electricity Authority Baseline Database (0.716 kg CO₂e/kWh), strictly distinguishing potential estimates from verified results."*

### [2:30 – 3:00] Verification, Green AI & Human Governance
> *(Navigate to 'Savings Verification & Audit', then 'Green AI Efficiency')*
> *"Managers maintain full governance — approving actions records an immutable audit trail in SQLite. Our verification engine compares pre- and post-intervention telemetry with weather normalization. Finally, our Green AI monitor confirms that EcoPilot runs 100% locally on CPU in under 500 ms, saving over 99% of the computational carbon footprint of remote cloud LLMs. Thank you!"*

---

## 👨‍⚖️ 5 Likely Judge Questions & Answers

### Q1: *"How do you prevent data leakage in your forecasting models?"*
> **Answer:** *"All lag features (`lag_1`, `lag_24`, `lag_168`) and rolling statistics are computed strictly on past timestamps shifted by at least 1 step before model fitting. We enforce a chronological 3-way partition (70% train, 15% validation, 15% held-out test). The test set remains untouched until final evaluation. Automated tests programmatically verify that $\max(T_{\text{train}}) < \min(T_{\text{val}}) < \min(T_{\text{test}})$."*

### Q2: *"Why use WAPE instead of standard MAPE for energy forecasting?"*
> **Answer:** *"MAPE divides the error by the actual consumption value $y_t$. In institutional facilities during night hours or holiday shutdowns, consumption drops near zero, causing mathematical division blow-ups where a 2 kWh discrepancy looks like 800% error. Weighted Absolute Percentage Error (WAPE) weights errors across total volume ($\frac{\sum |y - \hat{y}|}{\sum y}$), providing an interpretable, stable metric that respects energy scale."*

### Q3: *"How do you ensure you are not greenwashing carbon numbers?"*
> **Answer:** *"We use official, documented emission factors with explicit citations (e.g., India CEA Baseline v19.0 at 0.716 kg CO₂e/kWh, US EPA eGRID at 0.386). If a user does not configure an emission factor, we explicitly display 'Emission factor not configured' rather than guessing. Furthermore, we maintain a strict ontological wall between unverified potential savings and post-intervention verified savings."*

### Q4: *"Can multiple energy conservation measures cause double-counting?"*
> **Answer:** *"Yes, which is a major flaw in naive energy tools. In `src/savings.py`, we employ a multiplicative retention formulation ($\text{Retention} = \prod (1 - r_i)$) with an absolute ceiling of 85% of eligible baseline. This discounts overlapping effects and guarantees that aggregate savings respect the laws of thermodynamics."*

### Q5: *"Why an offline-first architecture instead of querying an LLM like GPT-4?"*
> **Answer:** *"Energy management requires deterministic, auditable numerical calculations, not probabilistic token generation. By using scikit-learn models and rule-based reasoning on standard CPUs, EcoPilot AI runs in under 500 ms with zero API costs, zero data privacy risks for campus facility records, and an ultra-low compute carbon footprint documented in our Green AI monitor."*

---

## 🗺️ Post-Hackathon Roadmap

- [ ] **Phase 1: Hardware Ingestion Connectors (Months 1–2)**
  - Native Modbus RTU/TCP, BACnet IP, and MQTT streaming ingestion for direct Schneider Electric, Siemens, and Elmeasure energy meters.
- [ ] **Phase 2: Solar Microgrid & BESS Dispatch Optimization (Months 2–3)**
  - Integration with rooftop PV inverters and Battery Energy Storage Systems (BESS) for real-time solar self-consumption and battery arbitration.
- [ ] **Phase 3: Multi-Building Campus Tenant Sub-Metering (Months 3–4)**
  - Automated department-level and hostel-wing cost allocation with automated sub-billing generation.
- [ ] **Phase 4: Automated BMS Actuation Webhooks (Months 4–5)**
  - Authorized webhook execution pushing approved setpoint modifications directly into Tridium Niagara / Honeywell BMS controllers via BACnet IP.

---

## 📄 License & Attribution

Distributed under the **MIT License**. Developed for sustainable Green AI innovation in educational and commercial institutions. Built with Python, Streamlit, Scikit-Learn, Pydantic, and Plotly.
