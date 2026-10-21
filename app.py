"""
EcoPilot AI: An Explainable AI Agent for Sustainable Building Energy Management
Main Streamlit Application Dashboard

Architecture:
- 7-Stage Closed-Loop Conservation Workflow:
  OBSERVE -> ANALYZE -> PLAN -> RECOMMEND -> SIMULATE -> REQUEST APPROVAL -> TRACK OUTCOME
- Evidence-backed AI agent with persistent SQLite audit trails
- 8 Modular Dashboard Views:
  1. 📊 Overview
  2. 🔍 Energy Analysis
  3. 🔮 Forecasting
  4. 🤖 AI Recommendations
  5. 💡 Savings Simulator
  6. 🌍 Environmental Impact (Dedicated Center)
  7. 📈 Verification and History
  8. ⚡ Green AI Efficiency
"""

import os
import io
import time
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Internal core modules
from src.data_generator import (
    generate_energy_dataset,
    validate_uploaded_csv,
    generate_data_quality_report,
    get_sample_csv_content,
    BUILDING_PROFILES,
    SCENARIOS,
)
from src.forecasting import (
    train_and_evaluate_forecasting,
    predict_next_24_hours,
)
from src.anomaly_detection import detect_anomalies
from src.agent import EcoPilotAgent
from src.savings import SavingsEngine
from src.carbon import CarbonCalculator, OFFICIAL_EMISSION_FACTORS, DEFAULT_FACTOR_KEY
from src.verification import SavingsVerifier
from src.green_ai import GreenAIMonitor
from src.optimizer import (
    simulate_load_shifting,
    analyze_peak_demand_shaving,
    DEFAULT_TOD_SCHEDULE,
    FLEXIBLE_LOAD_PROFILES,
)
from src.database import (
    init_db,
    get_all_recommendations,
    update_recommendation_status,
    get_audit_trail,
    save_simulation,
    get_all_simulations,
    get_all_alerts,
    update_alert_status,
    get_all_verifications,
    log_dataset_upload,
    reset_demo_db,
)
from src.config import get_config
from src.auth import Role, set_current_role, get_current_role, get_role_permissions
from src.services import (
    EnergyDataService,
    AnalyticsService,
    RecommendationService,
    SavingsSimulatorService,
    VerificationService,
    SystemAdminService,
)
from src.repositories import (
    RecommendationRepository,
    AlertRepository,
    VerificationRepository,
    SimulationRepository,
    DatasetUploadRepository,
    DatabaseAdminRepository,
)


# --- Page Configuration ---
st.set_page_config(
    page_title="EcoPilot AI — Sustainable Building Energy Agent",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom Styling: Deep Navy / Emerald Sustainability Theme ---
CUSTOM_CSS = """
<style>
    /* Global styles */
    .stApp {
        background: radial-gradient(circle at 10% 10%, #0d1829 0%, #070d18 100%);
        color: #e2e8f0;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Headers & typography */
    h1, h2, h3, h4, h5, h6 {
        color: #f8fafc;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    
    /* Metrics & Cards */
    .metric-card {
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px 18px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
        backdrop-filter: blur(10px);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        border-color: rgba(16, 185, 129, 0.4);
        transform: translateY(-2px);
    }
    .metric-label {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #94a3b8;
        font-weight: 600;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 1.75rem;
        font-weight: 800;
        color: #ffffff;
        line-height: 1.2;
    }
    .metric-sub {
        font-size: 0.78rem;
        color: #10b981;
        margin-top: 6px;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    
    /* Badges */
    .badge-critical {
        background: rgba(220, 38, 38, 0.25);
        color: #fca5a5;
        border: 1px solid rgba(220, 38, 38, 0.5);
        border-radius: 6px;
        padding: 2px 8px;
        font-size: 0.75rem;
        font-weight: 700;
    }
    .badge-high {
        background: rgba(239, 68, 68, 0.18);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.4);
        border-radius: 6px;
        padding: 2px 8px;
        font-size: 0.75rem;
        font-weight: 700;
    }
    .badge-medium {
        background: rgba(245, 158, 11, 0.18);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.4);
        border-radius: 6px;
        padding: 2px 8px;
        font-size: 0.75rem;
        font-weight: 700;
    }
    .badge-low {
        background: rgba(59, 130, 246, 0.18);
        color: #60a5fa;
        border: 1px solid rgba(59, 130, 246, 0.4);
        border-radius: 6px;
        padding: 2px 8px;
        font-size: 0.75rem;
        font-weight: 700;
    }
    .badge-pending {
        background: rgba(234, 179, 8, 0.18);
        color: #facc15;
        border: 1px solid rgba(234, 179, 8, 0.4);
        border-radius: 6px;
        padding: 2px 8px;
        font-size: 0.75rem;
        font-weight: 700;
    }
    .badge-approved {
        background: rgba(16, 185, 129, 0.18);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.4);
        border-radius: 6px;
        padding: 2px 8px;
        font-size: 0.75rem;
        font-weight: 700;
    }
    .badge-completed {
        background: rgba(6, 182, 212, 0.18);
        color: #22d3ee;
        border: 1px solid rgba(6, 182, 212, 0.4);
        border-radius: 6px;
        padding: 2px 8px;
        font-size: 0.75rem;
        font-weight: 700;
    }
    .badge-rejected {
        background: rgba(148, 163, 184, 0.18);
        color: #94a3b8;
        border: 1px solid rgba(148, 163, 184, 0.4);
        border-radius: 6px;
        padding: 2px 8px;
        font-size: 0.75rem;
        font-weight: 700;
    }

    /* Workflow indicator bar */
    .workflow-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid rgba(16, 185, 129, 0.25);
        border-radius: 10px;
        padding: 12px 18px;
        margin-bottom: 24px;
        overflow-x: auto;
    }
    .wf-step {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 3px;
        min-width: 90px;
    }
    .wf-step-num {
        font-size: 0.72rem;
        font-weight: 800;
        background: #10b981;
        color: #042f1a;
        width: 22px;
        height: 22px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .wf-step-title {
        font-size: 0.8rem;
        font-weight: 700;
        color: #f1f5f9;
    }
    .wf-arrow {
        color: #64748b;
        font-size: 1.0rem;
        font-weight: 700;
    }
    
    /* Recommendation card */
    .rec-card {
        background: rgba(15, 23, 42, 0.75);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-left: 4px solid #10b981;
        border-radius: 10px;
        padding: 18px 20px;
        margin-bottom: 16px;
    }
    .rec-card-critical { border-left-color: #dc2626; }
    .rec-card-high { border-left-color: #ef4444; }
    .rec-card-medium { border-left-color: #f59e0b; }
    .rec-card-low { border-left-color: #3b82f6; }

    /* Concept separation banner */
    .concept-banner {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        gap: 12px;
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 20px;
    }
    .concept-item {
        border-left: 3px solid #64748b;
        padding-left: 10px;
    }
    .concept-title {
        font-size: 0.75rem;
        text-transform: uppercase;
        font-weight: 700;
        letter-spacing: 0.05em;
    }
    .concept-desc {
        font-size: 0.78rem;
        color: #cbd5e1;
        margin-top: 3px;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Plotly dark theme configuration
PLOTLY_DARK_TEMPLATE = "plotly_dark"
PLOTLY_LAYOUT_DEFAULTS = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(11, 19, 34, 0.0)",
    plot_bgcolor="rgba(15, 23, 42, 0.4)",
    font=dict(family="Inter, sans-serif", color="#cbd5e1"),
    margin=dict(l=40, r=20, t=40, b=40),
    xaxis=dict(gridcolor="rgba(255, 255, 255, 0.06)", showgrid=True),
    yaxis=dict(gridcolor="rgba(255, 255, 255, 0.06)", showgrid=True),
)

# Auto-initialize database and centralized configuration
init_db()
app_config = get_config()
green_monitor = GreenAIMonitor.get_instance()


# --- Navigation Options ---
PAGE_OPTIONS = [
    "📊 Overview",
    "🔍 Energy Analysis",
    "🔮 Forecasting",
    "🤖 AI Recommendations",
    "💡 Savings Simulator",
    "🌍 Environmental Impact",
    "📈 Verification and History",
    "⚡ Green AI Efficiency",
]

# --- Sidebar Controls ---
st.sidebar.markdown(
    """
    <div style='display: flex; align-items: center; gap: 10px; margin-bottom: 12px;'>
        <span style='font-size: 2rem;'>🌱</span>
        <div>
            <h2 style='margin: 0; font-size: 1.35rem; color: #10b981;'>EcoPilot AI</h2>
            <p style='margin: 0; font-size: 0.75rem; color: #94a3b8;'>AI for Sustainable Buildings</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

selected_page = st.sidebar.radio("Navigation", PAGE_OPTIONS, index=0)

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Scenario & Facility Config")

# Demo Scenario Selector
SCENARIO_DISPLAY = {
    "overnight_waste": "🔴 Excessive Overnight Waste (Demo)",
    "sudden_spike": "⚡ Sudden Surge Spikes (Demo)",
    "normal": "🟢 Normal Operations (Baseline)",
    "custom_csv": "📁 Upload Custom CSV Data",
}

selected_scenario_key = st.sidebar.selectbox(
    "Select Demo Scenario:",
    options=list(SCENARIO_DISPLAY.keys()),
    format_func=lambda k: SCENARIO_DISPLAY[k],
    index=0,
    help="Switch between reproducible operational scenarios to evaluate how the agent detects, explains, and acts.",
)

# Facility Category
building_options = list(BUILDING_PROFILES.keys())
selected_building = st.sidebar.selectbox(
    "Facility / Building Archetype:",
    options=building_options,
    index=0,
)

# Electricity Tariff
tariff_inr = st.sidebar.number_input(
    "Electricity Tariff (₹/kWh):",
    min_value=1.0,
    max_value=30.0,
    value=8.50,
    step=0.25,
    help="Typical commercial/campus electricity tariff in India ranges from ₹7.50 to ₹11.00/kWh.",
)

# Grid Emission Factor Configuration
st.sidebar.markdown("---")
st.sidebar.subheader("🌍 Grid Emission Factor")
emission_factor_options = list(OFFICIAL_EMISSION_FACTORS.keys()) + ["Not Configured", "Custom Emission Factor"]
selected_factor_key = st.sidebar.selectbox(
    "Official Emission Reference:",
    options=emission_factor_options,
    index=0,
    help="Select an official, documented grid emission factor for avoided GHG calculations.",
)

custom_factor_val = None
custom_factor_source = None
if selected_factor_key == "Custom Emission Factor":
    custom_factor_val = st.sidebar.number_input(
        "Custom Factor (kg CO2e/kWh):", min_value=0.01, max_value=2.0, value=0.716, step=0.01
    )
    custom_factor_source = st.sidebar.text_input(
        "Source Citation (Required):", value="Institutional Microgrid Assessment 2024"
    )

# Initialize Carbon Calculator
carbon_calc = CarbonCalculator(
    factor_key=selected_factor_key if selected_factor_key != "Custom Emission Factor" else None,
    custom_factor=custom_factor_val,
    custom_source=custom_factor_source,
)

# Anomaly Sensitivity Threshold
st.sidebar.markdown("---")
st.sidebar.subheader("⚠️ Detection Tuning")
sensitivity_std = st.sidebar.slider(
    "Anomaly Sensitivity (Z-score σ):",
    min_value=1.5,
    max_value=4.0,
    value=2.4,
    step=0.1,
    help="Lower standard deviations flag subtle deviations; higher values flag only severe anomalies.",
)

# Downloadable Sample CSV in Sidebar
sample_csv_text = get_sample_csv_content()
st.sidebar.download_button(
    label="📥 Download Sample CSV Schema",
    data=sample_csv_text,
    file_name="ecopilot_sample_energy_data.csv",
    mime="text/csv",
    help="Download a clean, pre-formatted hourly energy CSV to test custom upload.",
)

# --- Role-Based Access Control (RBAC) ---
st.sidebar.markdown("---")
st.sidebar.subheader("👤 User Role & Access")
role_options = [r.value for r in Role]
selected_role_str = st.sidebar.selectbox(
    "Active User Role:",
    options=role_options,
    index=role_options.index(Role.ANALYST.value),
    help="Role-Based Access Control: Viewer (Read-only), Analyst (Simulate/Analyze), Approver (Approve/Reject Actions), Administrator (Full Access & DB Reset)."
)
active_role = Role(selected_role_str)
set_current_role(active_role)
st.sidebar.caption(f"Active Role: **{active_role.value}** | Env: **{app_config.env.value.upper()}**")

# Reset Demo DB Button (Protected by RBAC & Confirmation Key)
if st.sidebar.button("🔄 Reset Decision & Verification Log"):
    try:
        SystemAdminService.reset_database(confirmation_key=app_config.reset_confirm_key, force=True)
        st.sidebar.success("Database history reset to clean state.")
        st.rerun()
    except PermissionError as pe:
        st.sidebar.error(f"Action Restricted: {str(pe)}")
    except Exception as e:
        st.sidebar.error(f"Reset Failed: {str(e)}")

st.sidebar.caption(
    "🌱 **EcoPilot AI Core Framework:**<br>"
    "Evidence-backed AI Agent for Sustainable Building Energy Management.<br>"
    "100% Offline Local Inference | Zero Paid API Dependencies",
    unsafe_allow_html=True,
)


# --- Data Acquisition Logic ---
uploaded_file = None
quality_report = None

if selected_scenario_key == "custom_csv":
    st.sidebar.markdown("### Upload Custom Energy Data")
    uploaded_file = st.sidebar.file_uploader(
        "Upload hourly energy CSV:",
        type=["csv"],
        help="Requires timestamp and energy_kwh (or power_kw) columns.",
    )

if selected_scenario_key == "custom_csv" and uploaded_file is not None:
    try:
        raw_df = pd.read_csv(uploaded_file)
        is_valid, err_msg, df_active, quality_report = EnergyDataService.load_and_validate_csv(
            file_content_or_df=raw_df,
            filename=uploaded_file.name,
            record_upload_log=True,
        )
        if not is_valid:
            st.error(f"CSV Validation Error: {err_msg}")
            st.json(quality_report)
            st.stop()
        health_pct = quality_report.get("health_score_pct", 100.0) if quality_report else 100.0
        st.sidebar.success(f"Loaded {len(df_active)} records successfully (Health: {health_pct}%).")
    except Exception as e:
        st.error(f"Failed to read CSV: {str(e)}")
        st.stop()
else:
    # Use synthetic deterministic scenario via EnergyDataService
    active_scenario_name = "normal" if selected_scenario_key == "custom_csv" else selected_scenario_key
    with green_monitor.time_task("Generate Scenario Data", "Synthetic Energy Synthesizer"):
        df_active = EnergyDataService.get_or_generate_dataset(
            days=60,
            building_category=selected_building,
            scenario=active_scenario_name,
            random_seed=42,
        )


# --- Execute Core Analytics & Reasoning ---
# 1. Anomaly Detection
with green_monitor.time_task("Anomaly Detection", "Z-Score + Isolation Forest"):
    anomaly_results = detect_anomalies(
        df=df_active,
        sensitivity_std=sensitivity_std,
        min_absolute_diff_kwh=6.0,
        use_isolation_forest=True,
    )

# 2. Forecasting Engine
try:
    with green_monitor.time_task("Energy Forecasting", "Random Forest + Seasonal + Persistence"):
        fcst_results = train_and_evaluate_forecasting(df_active, test_hours=72, val_hours=48)
        future_24h_df = predict_next_24_hours(
            model=fcst_results["model"],
            df=df_active,
            test_rmse=fcst_results["metrics"]["rf_rmse"],
            interval_offsets=fcst_results["interval_offsets"],
            empirical_coverage_pct=fcst_results["metrics"]["prediction_interval"]["val_empirical_coverage_pct"],
        )
except Exception as e:
    fcst_results = None
    future_24h_df = None
    st.warning(f"Forecasting note: {str(e)}")

# 3. AI Task Agent Synthesis
with green_monitor.time_task("AI Task Agent Reasoning", "EcoPilotAgent Reasoning Engine"):
    agent = EcoPilotAgent(
        tariff_inr_per_kwh=tariff_inr,
        carbon_factor_key=selected_factor_key if selected_factor_key != "Custom Emission Factor" else None,
        custom_carbon_factor=custom_factor_val,
        custom_carbon_source=custom_factor_source,
    )
    active_recommendations = agent.analyze_and_generate_recommendations(
        anomaly_results=anomaly_results,
        forecast_results=fcst_results,
        scenario_name=selected_scenario_key,
        building_category=selected_building,
    )

# 4. Multi-Action Portfolio Savings Calculation (Accounting for overlap)
total_consumption_kwh = float(df_active["energy_kwh"].sum())
total_bill_inr = total_consumption_kwh * tariff_inr

portfolio_savings = SavingsEngine.calculate_portfolio_savings(
    recommendations=active_recommendations,
    overall_baseline_kwh=total_consumption_kwh,
    tariff_inr_per_kwh=tariff_inr,
)

# 5. Avoided Emissions from Portfolio Savings
avoided_co2_res = carbon_calc.calculate_avoided_emissions(
    electricity_saved_kwh=portfolio_savings["deduplicated_saved_kwh"],
    is_verified=False,
    intervention_name="EcoPilot Recommendations Portfolio",
)

# 6. Retrieve Verified Savings if Recorded in DB
historical_verifs = get_all_verifications()
total_verified_kwh = sum(v["realized_savings_kwh"] for v in historical_verifs if v["realized_savings_kwh"] > 0)
total_verified_inr = sum(v["realized_savings_inr"] for v in historical_verifs if v["realized_savings_inr"] > 0)
total_verified_co2 = sum(v.get("verified_avoided_kg_co2e", 0.0) for v in historical_verifs)


# --- Workflow Top Banner ---
st.markdown(
    """
    <div class='workflow-container'>
        <div class='wf-step'>
            <div class='wf-step-num'>1</div>
            <div class='wf-step-title'>OBSERVE</div>
            <span style='font-size: 0.7rem; color: #94a3b8;'>Hourly Telemetry</span>
        </div>
        <div class='wf-arrow'>→</div>
        <div class='wf-step'>
            <div class='wf-step-num'>2</div>
            <div class='wf-step-title'>ANALYZE</div>
            <span style='font-size: 0.7rem; color: #94a3b8;'>Z-Score & IsoForest</span>
        </div>
        <div class='wf-arrow'>→</div>
        <div class='wf-step'>
            <div class='wf-step-num'>3</div>
            <div class='wf-step-title'>PLAN</div>
            <span style='font-size: 0.7rem; color: #94a3b8;'>Group Waste Drivers</span>
        </div>
        <div class='wf-arrow'>→</div>
        <div class='wf-step'>
            <div class='wf-step-num'>4</div>
            <div class='wf-step-title'>RECOMMEND</div>
            <span style='font-size: 0.7rem; color: #94a3b8;'>Prioritized Tasks</span>
        </div>
        <div class='wf-arrow'>→</div>
        <div class='wf-step'>
            <div class='wf-step-num'>5</div>
            <div class='wf-step-title'>SIMULATE</div>
            <span style='font-size: 0.7rem; color: #94a3b8;'>Overlap-Safe ₹ & CO2</span>
        </div>
        <div class='wf-arrow'>→</div>
        <div class='wf-step'>
            <div class='wf-step-num'>6</div>
            <div class='wf-step-title'>APPROVE</div>
            <span style='font-size: 0.7rem; color: #94a3b8;'>Human Operator</span>
        </div>
        <div class='wf-arrow'>→</div>
        <div class='wf-step'>
            <div class='wf-step-num'>7</div>
            <div class='wf-step-title'>TRACK</div>
            <span style='font-size: 0.7rem; color: #94a3b8;'>Sub-Meter Verify</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ==============================================================================
# PAGE 1: OVERVIEW
# ==============================================================================
if selected_page == "📊 Overview":
    st.markdown(
        f"### Facility Overview: <span style='color: #10b981;'>{selected_building}</span>",
        unsafe_allow_html=True,
    )
    st.caption(
        f"Active Scenario: **{SCENARIO_DISPLAY.get(selected_scenario_key, selected_scenario_key)}** | "
        f"Readings: {len(df_active)} hourly records (60 days) | Tariff: ₹{tariff_inr:.2f}/kWh | "
        f"Grid Factor: **{carbon_calc.factor_kg_co2e_per_kwh if carbon_calc.is_configured else 'Not Configured'} kg CO2e/kWh**"
    )

    # Conceptual Separation Banner
    st.markdown(
        """
        <div class='concept-banner'>
            <div class='concept-item' style='border-left-color: #ef4444;'>
                <div class='concept-title' style='color: #ef4444;'>1. Detected Potential Waste</div>
                <div class='concept-desc'>Historical telemetry deviating above baseline (e.g. overnight HVAC running while empty). An anomaly is a hypothesis, not proof of waste.</div>
            </div>
            <div class='concept-item' style='border-left-color: #f59e0b;'>
                <div class='concept-title' style='color: #f59e0b;'>2. Estimated Potential Savings</div>
                <div class='concept-desc'>Model projections assuming approved interventions achieve conservative reduction targets with overlap deduplication.</div>
            </div>
            <div class='concept-item' style='border-left-color: #10b981;'>
                <div class='concept-title' style='color: #10b981;'>3. Verified Realized Savings</div>
                <div class='concept-desc'>Empirical counterfactual savings measured from follow-up sub-meter data after physical implementation.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Top KPI Metrics Row
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    with kpi1:
        st.markdown(
            f"""
            <div class='metric-card'>
                <div class='metric-label'>Total Consumption</div>
                <div class='metric-value'>{total_consumption_kwh:,.0f} <span style='font-size: 0.9rem;'>kWh</span></div>
                <div class='metric-sub'>60 Days Telemetry</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with kpi2:
        st.markdown(
            f"""
            <div class='metric-card'>
                <div class='metric-label'>Est. Electricity Bill</div>
                <div class='metric-value'>₹{total_bill_inr:,.0f}</div>
                <div class='metric-sub'>@ ₹{tariff_inr:.2f}/kWh</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with kpi3:
        pot_kwh = portfolio_savings["deduplicated_saved_kwh"]
        pot_inr = portfolio_savings["deduplicated_saved_inr"]
        st.markdown(
            f"""
            <div class='metric-card' style='border-color: rgba(16, 185, 129, 0.4);'>
                <div class='metric-label' style='color: #34d399;'>Potential Savings</div>
                <div class='metric-value' style='color: #34d399;'>₹{pot_inr:,.0f}</div>
                <div class='metric-sub' style='color: #34d399;'>{pot_kwh:,.0f} kWh ({portfolio_savings['effective_reduction_pct']}%)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with kpi4:
        if avoided_co2_res["is_configured"]:
            co2_kg = avoided_co2_res["avoided_emissions_kg_co2e"]
            st.markdown(
                f"""
                <div class='metric-card' style='border-color: rgba(56, 189, 248, 0.4);'>
                    <div class='metric-label' style='color: #38bdf8;'>Avoided GHG Emissions</div>
                    <div class='metric-value' style='color: #38bdf8;'>{co2_kg:,.0f} <span style='font-size: 0.9rem;'>kg</span></div>
                    <div class='metric-sub' style='color: #38bdf8;'>{avoided_co2_res['avoided_emissions_tonnes_co2e']:.2f} tonnes CO2e</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class='metric-card'>
                    <div class='metric-label'>Avoided Emissions</div>
                    <div class='metric-value' style='font-size: 1.1rem; color: #94a3b8;'>Not Configured</div>
                    <div class='metric-sub' style='color: #94a3b8;'>Select grid factor</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    with kpi5:
        pending_count = sum(1 for r in active_recommendations if r["status"] == "Pending")
        high_anom = anomaly_results["summary"]["critical_severity"] + anomaly_results["summary"]["high_severity"]
        st.markdown(
            f"""
            <div class='metric-card'>
                <div class='metric-label'>Awaiting Review</div>
                <div class='metric-value'>{pending_count} <span style='font-size: 0.9rem;'>tasks</span></div>
                <div class='metric-sub' style='color: {"#ef4444" if high_anom > 0 else "#f59e0b"};'>
                    {high_anom} High/Crit Alerts
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Main Visuals: Historical Timeline & Priority Action Cards
    col_chart, col_side = st.columns([2.2, 1.0])

    with col_chart:
        st.subheader("📈 Electricity Demand & Anomaly Telemetry")
        
        # Plot last 14 days
        last_14_days_mask = df_active["timestamp"] >= (df_active["timestamp"].max() - pd.Timedelta(days=14))
        df_sub = df_active[last_14_days_mask].copy()

        fig_main = go.Figure()
        # Normal consumption line
        fig_main.add_trace(
            go.Scatter(
                x=df_sub["timestamp"],
                y=df_sub["energy_kwh"],
                mode="lines",
                name="Hourly Electricity Demand (kWh)",
                line=dict(color="#10b981", width=2),
                hovertemplate="%{x|%b %d, %H:00}<br><b>%{y:.1f} kWh</b><extra></extra>",
            )
        )

        # Flagged anomalies overlay
        merged_flags = anomaly_results["flagged_df"]
        anom_sub = merged_flags[
            (merged_flags["timestamp"] >= df_sub["timestamp"].min()) & (merged_flags["is_anomaly"])
        ]
        if not anom_sub.empty:
            fig_main.add_trace(
                go.Scatter(
                    x=anom_sub["timestamp"],
                    y=anom_sub["energy_kwh"],
                    mode="markers",
                    name="Anomaly Alert",
                    marker=dict(
                        color="#ef4444",
                        size=8,
                        symbol="circle-open-dot",
                        line=dict(width=2, color="#ef4444"),
                    ),
                    hovertemplate="<b>ANOMALY DETECTED</b><br>%{x|%b %d, %H:00}<br>Observed: %{y:.1f} kWh<extra></extra>",
                )
            )

        # Historical baseline curve
        fig_main.add_trace(
            go.Scatter(
                x=df_sub["timestamp"],
                y=merged_flags.loc[df_sub.index, "baseline_median"],
                mode="lines",
                name="Historical Median Baseline",
                line=dict(color="#64748b", width=1.5, dash="dot"),
                hovertemplate="Median Baseline: %{y:.1f} kWh<extra></extra>",
            )
        )

        fig_main.update_layout(
            **PLOTLY_LAYOUT_DEFAULTS,
            height=380,
            title="Recent 14-Day Consumption Timeline with Statistical Baseline",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_main, use_container_width=True)

    with col_side:
        st.subheader("🔔 Priority Action Items")
        st.caption("AI Task Agent ranked recommendations based on impact:")
        
        if active_recommendations:
            for rec in active_recommendations[:3]:
                sev_badge = f"badge-{rec['severity'].lower()}"
                status_badge = f"badge-{rec['status'].lower()}"
                
                st.markdown(
                    f"""
                    <div class='rec-card rec-card-{rec['severity'].lower()}'>
                        <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;'>
                            <span class='{sev_badge}'>{rec['severity']} Priority (Score {rec['priority_score']})</span>
                            <span class='{status_badge}'>{rec['status']}</span>
                        </div>
                        <div style='font-size: 0.95rem; font-weight: 700; color: #f8fafc; margin-bottom: 4px;'>
                            {rec['title']}
                        </div>
                        <div style='font-size: 0.8rem; color: #94a3b8; margin-bottom: 8px;'>
                            Est. Impact: <strong style='color: #10b981;'>₹{rec['estimated_inr_saving']:,.0f}</strong> 
                            ({rec['estimated_kwh_saving']:.0f} kWh)
                        </div>
                        <div style='font-size: 0.78rem; color: #cbd5e1; line-height: 1.3;'>
                            {rec['suggested_action'][:120]}...
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No active anomalies detected in current scenario. Baseline efficiency is nominal.")

    # Verified Realized Savings Summary Bar if Available
    if historical_verifs:
        st.markdown(
            f"""
            <div style='background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 8px; padding: 12px 18px; margin-top: 15px;'>
                <strong style='color: #34d399;'>🏆 Verified Real-World Achievements (Sub-Meter Logging):</strong>
                {len(historical_verifs)} intervention(s) verified to date. Realized: <strong>{total_verified_kwh:,.1f} kWh</strong> 
                (₹{total_verified_inr:,.0f} saved | {total_verified_co2:,.1f} kg CO2e verified avoided).
            </div>
            """,
            unsafe_allow_html=True,
        )


# ==============================================================================
# PAGE 2: ENERGY ANALYSIS
# ==============================================================================
elif selected_page == "🔍 Energy Analysis":
    st.markdown("### 🔍 Electricity Consumption & Temporal Load Profiling")
    st.caption("Multi-timescale analysis: Daily consumption, weekly patterns, monthly trends, and circadian heatmaps.")

    tab_daily, tab_weekly, tab_monthly, tab_heatmap = st.tabs(
        ["📅 Daily Breakdown", "📊 Weekly Profile", "🗓️ Monthly Trends", "🔥 Circadian Heatmap"]
    )

    with tab_daily:
        daily_df = df_active.set_index("timestamp").resample("D")["energy_kwh"].agg(
            total_kwh="sum", peak_kwh="max", avg_kwh="mean"
        ).reset_index()
        daily_df["7d_moving_avg"] = daily_df["total_kwh"].rolling(window=7, min_periods=1).mean()

        fig_daily = go.Figure()
        fig_daily.add_trace(
            go.Bar(
                x=daily_df["timestamp"],
                y=daily_df["total_kwh"],
                name="Daily Total (kWh)",
                marker_color="#10b981",
                opacity=0.8,
            )
        )
        fig_daily.add_trace(
            go.Scatter(
                x=daily_df["timestamp"],
                y=daily_df["7d_moving_avg"],
                name="7-Day Rolling Trend",
                line=dict(color="#f59e0b", width=2.5),
            )
        )
        fig_daily.update_layout(
            **PLOTLY_LAYOUT_DEFAULTS,
            height=380,
            title="Daily Electricity Demand with 7-Day Moving Trend",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_daily, use_container_width=True)

    with tab_weekly:
        df_active["week_num"] = df_active["timestamp"].dt.isocalendar().week
        weekly_df = df_active.groupby(["week_num", "day_name"])["energy_kwh"].sum().reset_index()
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        fig_box = px.box(
            df_active,
            x="day_name",
            y="energy_kwh",
            category_orders={"day_name": day_order},
            color="is_weekend",
            color_discrete_map={0: "#10b981", 1: "#64748b"},
            title="Hourly Electricity Dispersion Across Days of the Week",
        )
        fig_box.update_layout(**PLOTLY_LAYOUT_DEFAULTS, height=380, showlegend=False)
        st.plotly_chart(fig_box, use_container_width=True)
        st.caption("Notice the distinct drop in median consumption during weekends compared to academic/office weekdays.")

    with tab_monthly:
        monthly_df = df_active.set_index("timestamp").resample("ME")["energy_kwh"].sum().reset_index()
        monthly_df["month_str"] = monthly_df["timestamp"].dt.strftime("%B %Y")
        monthly_df["bill_inr"] = monthly_df["energy_kwh"] * tariff_inr

        fig_monthly = px.bar(
            monthly_df,
            x="month_str",
            y="energy_kwh",
            text="energy_kwh",
            color="energy_kwh",
            color_continuous_scale="Greens",
            title="Monthly Aggregate Electricity Volume (kWh)",
        )
        fig_monthly.update_traces(texttemplate="%{text:,.0f} kWh", textposition="outside")
        fig_monthly.update_layout(**PLOTLY_LAYOUT_DEFAULTS, height=360, coloraxis_showscale=False)
        st.plotly_chart(fig_monthly, use_container_width=True)

    with tab_heatmap:
        pivot_heat = df_active.pivot_table(
            index="day_name",
            columns="hour",
            values="energy_kwh",
            aggfunc="mean",
        ).reindex(day_order)

        fig_heat = px.imshow(
            pivot_heat,
            labels=dict(x="Hour of Day (24h)", y="Day of Week", color="Avg kWh"),
            x=list(range(24)),
            y=day_order,
            color_continuous_scale="Viridis",
            title="Average Hourly Energy Intensity Matrix (Heatmap)",
            aspect="auto",
        )
        fig_heat.update_layout(**PLOTLY_LAYOUT_DEFAULTS, height=380)
        st.plotly_chart(fig_heat, use_container_width=True)


# ==============================================================================
# PAGE 3: FORECASTING
# ==============================================================================
elif selected_page == "🔮 Forecasting":
    st.markdown("### 🔮 Multi-Baseline Energy Demand Forecasting")
    st.caption(
        "Chronological time-series prediction comparing Random Forest Regressor "
        "against Historical Seasonal and Previous-Day Naive Baselines on held-out test data."
    )

    if fcst_results is None:
        st.error("Forecasting model could not be initialized due to insufficient data (< 240 hourly readings).")
    else:
        metrics = fcst_results["metrics"]

        # Metric comparison cards
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(
                f"""
                <div class='metric-card'>
                    <div class='metric-label'>Random Forest MAE</div>
                    <div class='metric-value' style='color: #10b981;'>{metrics['rf_mae']} <span style='font-size: 1rem;'>kWh</span></div>
                    <div class='metric-sub'>WAPE: {metrics['models_test']['Random Forest']['wape_pct']}% | R²: {metrics['rf_r2']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with m2:
            st.markdown(
                f"""
                <div class='metric-card'>
                    <div class='metric-label'>Seasonal Baseline MAE</div>
                    <div class='metric-value' style='color: #94a3b8;'>{metrics['models_test']['Historical Seasonal']['mae']} <span style='font-size: 1rem;'>kWh</span></div>
                    <div class='metric-sub' style='color: #94a3b8;'>WAPE: {metrics['models_test']['Historical Seasonal']['wape_pct']}%</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with m3:
            st.markdown(
                f"""
                <div class='metric-card'>
                    <div class='metric-label'>Persistence Baseline MAE</div>
                    <div class='metric-value' style='color: #94a3b8;'>{metrics['baseline_mae']} <span style='font-size: 1rem;'>kWh</span></div>
                    <div class='metric-sub' style='color: #94a3b8;'>WAPE: {metrics['models_test']['Previous-Day Persistence']['wape_pct']}%</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with m4:
            st.markdown(
                f"""
                <div class='metric-card' style='border-color: rgba(56, 189, 248, 0.4);'>
                    <div class='metric-label' style='color: #38bdf8;'>Preferred Model</div>
                    <div class='metric-value' style='font-size: 1.25rem; color: #38bdf8;'>{fcst_results['preferred_model_name'][:20]}</div>
                    <div class='metric-sub' style='color: #38bdf8;'>Selected via Validation MAE</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Tabbed Views: Held-out Test Evaluation vs Next 24h Future Forecast
        tab_eval, tab_future, tab_comp, tab_feat = st.tabs(
            ["📊 Held-Out Test Evaluation", "🔮 Next 24-Hour Future Forecast", "⚖️ 3-Model Comparison Table", "🧠 Feature Importance"]
        )

        with tab_eval:
            eval_df = fcst_results["evaluation_df"]
            fig_eval = go.Figure()
            fig_eval.add_trace(
                go.Scatter(
                    x=eval_df["timestamp"],
                    y=eval_df["actual_kwh"],
                    mode="lines",
                    name="Actual Consumption (kWh)",
                    line=dict(color="#f8fafc", width=2.2),
                )
            )
            fig_eval.add_trace(
                go.Scatter(
                    x=eval_df["timestamp"],
                    y=eval_df["rf_pred_kwh"],
                    mode="lines",
                    name="Random Forest Prediction",
                    line=dict(color="#10b981", width=2),
                )
            )
            fig_eval.add_trace(
                go.Scatter(
                    x=eval_df["timestamp"],
                    y=eval_df["seasonal_pred_kwh"],
                    mode="lines",
                    name="Historical Seasonal Profile",
                    line=dict(color="#38bdf8", width=1.5, dash="dash"),
                )
            )
            fig_eval.add_trace(
                go.Scatter(
                    x=eval_df["timestamp"],
                    y=eval_df["baseline_pred_kwh"],
                    mode="lines",
                    name="Previous-Day Persistence",
                    line=dict(color="#64748b", width=1.5, dash="dot"),
                )
            )
            fig_eval.update_layout(
                **PLOTLY_LAYOUT_DEFAULTS,
                height=400,
                title="Held-Out Test Set: Actual vs. 3 Model Predictions (72 Hours)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig_eval, use_container_width=True)

            st.caption(
                "💡 **WAPE vs. MAPE Transparency:** In building energy modeling, MAPE (Mean Absolute Percentage Error) "
                "divides by actual load $y_t$. When overnight standby load drops near zero, MAPE explodes to mathematically "
                "distorted values. **WAPE (Weighted Absolute Percentage Error)** aggregates total absolute error over total volume, "
                "giving a stable, robust percentage accuracy metric."
            )

        with tab_future:
            if future_24h_df is not None:
                fig_fut = go.Figure()

                # Upper bound
                fig_fut.add_trace(
                    go.Scatter(
                        x=future_24h_df["timestamp"],
                        y=future_24h_df["upper_bound_kwh"],
                        mode="lines",
                        line=dict(width=0),
                        showlegend=False,
                        hoverinfo="skip",
                    )
                )
                # Lower bound with shading
                fig_fut.add_trace(
                    go.Scatter(
                        x=future_24h_df["timestamp"],
                        y=future_24h_df["lower_bound_kwh"],
                        mode="lines",
                        line=dict(width=0),
                        fill="tonexty",
                        fillcolor="rgba(16, 185, 129, 0.15)",
                        name="Calibrated 90% Empirical Interval",
                    )
                )
                # Central prediction
                fig_fut.add_trace(
                    go.Scatter(
                        x=future_24h_df["timestamp"],
                        y=future_24h_df["forecast_kwh"],
                        mode="lines+markers",
                        name="Forecasted Consumption (kWh)",
                        line=dict(color="#10b981", width=2.5),
                        marker=dict(size=6, color="#10b981"),
                        hovertemplate="%{x|%a %H:00}<br><b>Forecast: %{y:.1f} kWh</b><extra></extra>",
                    )
                )

                fig_fut.update_layout(
                    **PLOTLY_LAYOUT_DEFAULTS,
                    height=380,
                    title="Next 24-Hour Projected Demand Envelope with Calibrated Empirical Interval",
                )
                st.plotly_chart(fig_fut, use_container_width=True)

                pi_meta = metrics["prediction_interval"]
                st.info(
                    f"🛡️ **Empirical Calibration Verification:** Prediction interval bounds are computed from validation residual quantiles "
                    f"($q_{{05}} = {pi_meta['q05_residual_kwh']}$ kWh, $q_{{95}} = {pi_meta['q95_residual_kwh']}$ kWh). "
                    f"Empirical validation coverage: **{pi_meta['val_empirical_coverage_pct']}%** | Test coverage: **{pi_meta['test_empirical_coverage_pct']}%**."
                )

                # Future forecast table
                with st.expander("🔍 View Next 24-Hour Hourly Forecast Table"):
                    display_fut = future_24h_df[
                        ["timestamp", "hour", "day_name", "forecast_kwh", "lower_bound_kwh", "upper_bound_kwh"]
                    ].copy()
                    display_fut["timestamp"] = display_fut["timestamp"].dt.strftime("%Y-%m-%d %H:%M")
                    st.dataframe(display_fut, use_container_width=True)

        with tab_comp:
            st.subheader("Benchmark Comparison on Chronological Held-Out Test Set")
            comp_data = []
            for m_name, m_dict in metrics["models_test"].items():
                val_m = metrics["models_val"].get(m_name, {})
                comp_data.append(
                    {
                        "Model": m_name,
                        "Validation MAE (kWh)": val_m.get("mae", 0.0),
                        "Test MAE (kWh)": m_dict["mae"],
                        "Test RMSE (kWh)": m_dict["rmse"],
                        "Test WAPE (%)": f"{m_dict['wape_pct']}%",
                        "Test R² Score": m_dict["r2"],
                    }
                )
            st.dataframe(pd.DataFrame(comp_data), use_container_width=True)

        with tab_feat:
            importances = fcst_results["feature_importances"]
            feat_df = (
                pd.DataFrame(list(importances.items()), columns=["Feature", "Importance"])
                .sort_values("Importance", ascending=True)
            )
            fig_feat = px.bar(
                feat_df,
                x="Importance",
                y="Feature",
                orientation="h",
                color="Importance",
                color_continuous_scale="Greens",
                title="Random Forest Feature Importance Weights",
            )
            fig_feat.update_layout(**PLOTLY_LAYOUT_DEFAULTS, height=380, coloraxis_showscale=False)
            st.plotly_chart(fig_feat, use_container_width=True)


# ==============================================================================
# PAGE 4: AI RECOMMENDATIONS
# ==============================================================================
elif selected_page == "🤖 AI Recommendations":
    st.markdown("### 🤖 Evidence-Backed AI Task Agent")
    st.caption(
        "Synthesizes detected telemetry into prioritized conservation tasks. "
        "Allows facility directors to approve, reject, or complete actions with an immutable SQLite audit trail."
    )

    st.markdown(
        """
        <div style='background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 8px; padding: 12px 18px; margin-bottom: 20px;'>
            <div style='font-size: 0.85rem; color: #f1f5f9; font-weight: 600;'>
                🛡️ Human-in-the-Loop Operational Guardrail:
            </div>
            <div style='font-size: 0.78rem; color: #94a3b8;'>
                Approval confirms the managerial decision to schedule maintenance or setpoint adjustments. 
                The agent never switches physical hardware autonomously. State machine strictly enforces valid lifecycle transitions.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Display Recommendations with interactive controls via RecommendationService
    db_recs = RecommendationService.get_recommendations(scenario_filter=selected_scenario_key)
    if not db_recs:
        db_recs = active_recommendations

    if db_recs:
        for idx, rec in enumerate(db_recs):
            rec_id = rec["id"]
            current_status = rec["status"]
            sev_class = rec["severity"].lower()

            st.markdown(
                f"""
                <div class='rec-card rec-card-{sev_class}'>
                    <div style='display: flex; justify-content: space-between; align-items: flex-start;'>
                        <div>
                            <span class='badge-{sev_class}'>{rec['severity']} Priority (Score {rec.get('priority_score', 50)})</span>
                            <span class='badge-{current_status.lower()}' style='margin-left: 6px;'>{current_status}</span>
                            <span style='font-size: 0.75rem; color: #64748b; margin-left: 10px;'>ID: {rec_id}</span>
                            <h4 style='margin: 8px 0 4px 0; color: #ffffff;'>{rec['title']}</h4>
                            <div style='font-size: 0.85rem; color: #10b981; font-weight: 600;'>
                                Potential Saving: ₹{rec['estimated_inr_saving']:,.0f} ({rec['estimated_kwh_saving']:.0f} kWh)
                                {' | Avoided: ' + str(round(rec['estimated_avoided_kg_co2e'], 1)) + ' kg CO2e' if rec.get('estimated_avoided_kg_co2e') else ''}
                            </div>
                        </div>
                    </div>
                    <div style='margin-top: 10px; font-size: 0.85rem; color: #e2e8f0; line-height: 1.4;'>
                        <strong>Recommended Action:</strong> {rec['suggested_action']}
                    </div>
                    <div style='margin-top: 6px; font-size: 0.82rem; color: #38bdf8;'>
                        <strong>Next Step:</strong> {rec.get('recommended_next_action', 'Review sub-panel schedules.')}
                    </div>
                    <div style='margin-top: 8px; font-size: 0.8rem; color: #94a3b8;'>
                        <strong>Evidence Anchor:</strong> {rec['evidence']}
                    </div>
                    <div style='margin-top: 6px; font-size: 0.78rem; color: #94a3b8;'>
                        <strong>Explicit Assumptions:</strong> {rec['assumptions']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Interactive action button controls
            col_b1, col_b2, col_b3, col_b4 = st.columns([1.2, 1.2, 1.4, 2.5])
            with col_b1:
                if st.button(f"✅ Approve", key=f"app_{rec_id}", disabled=(current_status == "Approved")):
                    try:
                        RecommendationService.approve_recommendation(
                            rec_id=rec_id,
                            operator=f"Operator ({active_role.value})",
                            note="Approved in dashboard",
                        )
                        st.toast(f"Approved {rec_id}!")
                        st.rerun()
                    except PermissionError as pe:
                        st.error(f"Action Restricted: {str(pe)}")
            with col_b2:
                if st.button(f"❌ Reject", key=f"rej_{rec_id}", disabled=(current_status == "Rejected")):
                    try:
                        RecommendationService.reject_recommendation(
                            rec_id=rec_id,
                            operator=f"Operator ({active_role.value})",
                            note="Rejected by operator",
                        )
                        st.toast(f"Rejected {rec_id}!")
                        st.rerun()
                    except PermissionError as pe:
                        st.error(f"Action Restricted: {str(pe)}")
            with col_b3:
                if st.button(f"🏆 Mark Complete", key=f"cmp_{rec_id}", disabled=(current_status == "Completed")):
                    try:
                        RecommendationService.complete_recommendation(
                            rec_id=rec_id,
                            operator=f"Operator ({active_role.value})",
                            note="Implementation verified on site",
                        )
                        st.toast(f"Marked {rec_id} as Completed!")
                        st.rerun()
                    except PermissionError as pe:
                        st.error(f"Action Restricted: {str(pe)}")
            with col_b4:
                if rec.get("notes"):
                    st.caption(f"Operator Note: *{rec['notes']}*")

            st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin: 15px 0;'>", unsafe_allow_html=True)
    else:
        st.info("No recommendations found for this scenario.")


# ==============================================================================
# PAGE 5: SAVINGS SIMULATOR
# ==============================================================================
elif selected_page == "💡 Savings Simulator":
    st.markdown("### 💡 Interactive Energy & Financial Savings Simulator")
    st.caption(
        "Model what-if conservation scenarios with explicit physical constraints, "
        "Time-of-Day (ToD) tariff arbitrage, and portfolio overlap deduplication."
    )

    tab_single, tab_tod, tab_overlap = st.tabs(
        ["🎯 Single Action What-If", "⏱️ Time-of-Day Load Shifting", "🧩 Multi-Action Overlap Resolver"]
    )

    with tab_single:
        st.subheader("Single Measure Conservation Simulation")
        col_s1, col_s2 = st.columns([1, 1.2])

        with col_s1:
            sim_baseline = st.number_input(
                "Eligible Baseline Energy (kWh):",
                min_value=10.0,
                max_value=500000.0,
                value=float(min(total_consumption_kwh, 15000.0)),
                step=500.0,
                help="The volume of baseline electricity consumption eligible for this specific conservation measure.",
            )
            sim_reduction_pct = st.slider(
                "Proposed Reduction Percentage (%):",
                min_value=0.0,
                max_value=60.0,
                value=20.0,
                step=1.0,
                help="Conservative target reduction percentage (typically 10% - 30% for building efficiency).",
            )
            sim_tariff = st.number_input(
                "Electricity Tariff (₹/kWh):",
                min_value=1.0,
                max_value=30.0,
                value=tariff_inr,
                step=0.25,
            )
            sim_action_name = st.text_input(
                "Measure Name / Description:",
                value="Nighttime Auxiliary HVAC Setback & Timer Control",
            )

            try:
                sim_res = SavingsEngine.calculate_single_saving(
                    baseline_eligible_kwh=sim_baseline,
                    reduction_percentage=sim_reduction_pct,
                    tariff_inr_per_kwh=sim_tariff,
                    action_name=sim_action_name,
                )
            except Exception as e:
                st.error(f"Simulation calculation error: {str(e)}")
                sim_res = None

        with col_s2:
            if sim_res:
                sim_co2 = carbon_calc.calculate_avoided_emissions(sim_res["energy_saved_kwh"])
                st.markdown(
                    f"""
                    <div style='background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 12px; padding: 20px;'>
                        <h4 style='color: #10b981; margin-top: 0;'>Projected Conservation Outcomes</h4>
                        <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-top: 15px;'>
                            <div>
                                <div class='metric-label'>Energy Saved</div>
                                <div style='font-size: 1.5rem; font-weight: 800; color: #ffffff;'>
                                    {sim_res['energy_saved_kwh']:,.1f} <span style='font-size: 0.9rem;'>kWh</span>
                                </div>
                                <div style='font-size: 0.78rem; color: #10b981;'>{sim_res['reduction_percentage']}% of eligible load</div>
                            </div>
                            <div>
                                <div class='metric-label'>Rupees Saved</div>
                                <div style='font-size: 1.5rem; font-weight: 800; color: #34d399;'>
                                    ₹{sim_res['cost_savings_inr']:,.0f}
                                </div>
                                <div style='font-size: 0.78rem; color: #34d399;'>@ ₹{sim_res['tariff_inr_per_kwh']:.2f}/kWh</div>
                            </div>
                            <div>
                                <div class='metric-label'>Avoided Emissions</div>
                                <div style='font-size: 1.25rem; font-weight: 700; color: #38bdf8;'>
                                    {sim_co2['avoided_emissions_kg_co2e'] or 0.0:,.1f} <span style='font-size: 0.85rem;'>kg CO2e</span>
                                </div>
                            </div>
                            <div>
                                <div class='metric-label'>Proposed Post-Action Cost</div>
                                <div style='font-size: 1.25rem; font-weight: 700; color: #ffffff;'>
                                    ₹{sim_res['proposed_cost_inr']:,.0f}
                                </div>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if st.button("💾 Archive Simulation to History", key="save_sim_btn"):
                    try:
                        SavingsSimulatorService.archive_simulation(
                            name=sim_action_name,
                            baseline_kwh=sim_res["baseline_consumption_kwh"],
                            reduction_pct=sim_res["reduction_percentage"],
                            tariff_inr=sim_res["tariff_inr_per_kwh"],
                            saved_kwh=sim_res["energy_saved_kwh"],
                            saved_inr=sim_res["cost_savings_inr"],
                            avoided_kg_co2e=sim_co2["avoided_emissions_kg_co2e"] or 0.0,
                        )
                        st.success("Simulation parameters and outcomes archived to SQLite database!")
                    except PermissionError as pe:
                        st.error(f"Action Restricted: {str(pe)}")

        if sim_res:
            st.markdown("#### Before vs. After Consumption Comparison")
            fig_bar = go.Figure(
                data=[
                    go.Bar(
                        name="Baseline vs. Proposed",
                        x=["Current Baseline", "Projected Reduction", "Proposed Consumption"],
                        y=[
                            sim_res["baseline_consumption_kwh"],
                            -sim_res["energy_saved_kwh"],
                            sim_res["proposed_consumption_kwh"],
                        ],
                        marker_color=["#64748b", "#ef4444", "#10b981"],
                        text=[
                            f"{sim_res['baseline_consumption_kwh']:,.0f} kWh",
                            f"-{sim_res['energy_saved_kwh']:,.0f} kWh",
                            f"{sim_res['proposed_consumption_kwh']:,.0f} kWh",
                        ],
                        textposition="auto",
                    )
                ]
            )
            fig_bar.update_layout(**PLOTLY_LAYOUT_DEFAULTS, height=280)
            st.plotly_chart(fig_bar, use_container_width=True)

    with tab_tod:
        st.subheader("Time-of-Day (ToD) Flexible Load Rescheduling")
        st.caption(
            "Shift discretionary high-energy loads from high-cost peak hours to low-cost off-peak/solar windows. "
            "Total energy remains net-neutral, but bill drops dramatically."
        )

        load_type = st.selectbox(
            "Select Discretionary Load Type:",
            list(FLEXIBLE_LOAD_PROFILES.keys()),
            index=0,
        )
        l_prof = FLEXIBLE_LOAD_PROFILES[load_type]

        col_t1, col_t2 = st.columns([1, 1])
        with col_t1:
            load_kwh = st.number_input(
                "Load Energy per Cycle (kWh):",
                min_value=1.0,
                max_value=200.0,
                value=float(l_prof["typical_kwh_per_cycle"]),
            )
            from_h = st.slider("Current Active Hour (24h):", 0, 23, l_prof["default_active_hour"])
            to_h = st.slider("Target Shift Hour (24h):", 0, 23, l_prof["recommended_shift_hour"])
            shift_days = st.number_input("Operating Days per Month:", min_value=1, max_value=31, value=30)

        with col_t2:
            tod_res = simulate_load_shifting(
                load_name=load_type,
                shift_kwh=load_kwh,
                current_hour=from_h,
                target_hour=to_h,
                days=shift_days,
            )
            st.markdown(
                f"""
                <div style='background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 12px; padding: 18px;'>
                    <h4 style='color: #38bdf8; margin-top: 0;'>ToD Tariff Optimization Results</h4>
                    <p style='font-size: 0.85rem; color: #cbd5e1;'>{tod_res['explanation']}</p>
                    <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 10px;'>
                        <div>
                            <div class='metric-label'>Daily Saving</div>
                            <div style='font-size: 1.4rem; font-weight: 700; color: #ffffff;'>
                                ₹{tod_res['daily_saving_inr']:,.2f}
                            </div>
                        </div>
                        <div>
                            <div class='metric-label'>Monthly Saving</div>
                            <div style='font-size: 1.4rem; font-weight: 700; color: #38bdf8;'>
                                ₹{tod_res['projected_savings_inr']:,.2f}
                            </div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.warning(
            "⚠️ **Carbon Disclosure:** Shifting electricity consumption between hours saves money via tariff arbitrage, "
            "but does **not** automatically reduce carbon emissions unless the destination hour has documented lower "
            "marginal grid emission factors (e.g. midday solar surplus vs evening coal peaking)."
        )

    with tab_overlap:
        st.subheader("Multi-Recommendation Overlap & Double-Counting Guardrail")
        st.caption(
            "When combining multiple recommendations (e.g., thermostat setback AND lighting schedule), "
            "naive addition overestimates savings. EcoPilot applies sequential retention compounding."
        )

        st.json(portfolio_savings)
        st.info(
            f"Note: Raw unadjusted sum was {portfolio_savings['raw_sum_kwh']:.1f} kWh, but after overlap discounting, "
            f"realistic achievable savings are {portfolio_savings['deduplicated_saved_kwh']:.1f} kWh "
            f"(deduplicating {portfolio_savings['overlap_correction_kwh']:.1f} kWh of potential double counting)."
        )


# ==============================================================================
# PAGE 6: ENVIRONMENTAL IMPACT (DEDICATED FEATURE ONE)
# ==============================================================================
elif selected_page == "🌍 Environmental Impact":
    st.markdown("### 🌍 Environmental Impact Center")
    st.caption(
        "Quantifies the carbon and greenhouse gas (GHG) consequences of electricity consumption "
        "and potential energy-saving interventions using strictly documented official grid emission factors."
    )

    # 1. Top Environmental Impact KPIs
    e_kpi1, e_kpi2, e_kpi3, e_kpi4, e_kpi5 = st.columns(5)
    with e_kpi1:
        st.markdown(
            f"""
            <div class='metric-card'>
                <div class='metric-label'>Total Consumption</div>
                <div class='metric-value'>{total_consumption_kwh:,.0f} <span style='font-size: 0.9rem;'>kWh</span></div>
                <div class='metric-sub'>Baseline electricity</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with e_kpi2:
        st.markdown(
            f"""
            <div class='metric-card'>
                <div class='metric-label'>Potential Electricity Saved</div>
                <div class='metric-value' style='color: #10b981;'>{portfolio_savings['deduplicated_saved_kwh']:,.0f} <span style='font-size: 0.9rem;'>kWh</span></div>
                <div class='metric-sub'>Deduplicated portfolio</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with e_kpi3:
        st.markdown(
            f"""
            <div class='metric-card'>
                <div class='metric-label'>Estimated Cost Savings</div>
                <div class='metric-value' style='color: #34d399;'>₹{portfolio_savings['deduplicated_saved_inr']:,.0f}</div>
                <div class='metric-sub'>@ ₹{tariff_inr:.2f}/kWh</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with e_kpi4:
        if avoided_co2_res["is_configured"]:
            st.markdown(
                f"""
                <div class='metric-card' style='border-color: rgba(56, 189, 248, 0.4);'>
                    <div class='metric-label' style='color: #38bdf8;'>Avoided GHG Emissions</div>
                    <div class='metric-value' style='color: #38bdf8;'>{avoided_co2_res['avoided_emissions_kg_co2e']:,.0f} <span style='font-size: 0.9rem;'>kg</span></div>
                    <div class='metric-sub' style='color: #38bdf8;'>{avoided_co2_res['avoided_emissions_tonnes_co2e']:.2f} t CO2e</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class='metric-card'>
                    <div class='metric-label'>Avoided Emissions</div>
                    <div class='metric-value' style='font-size: 1.1rem; color: #94a3b8;'>Not Configured</div>
                    <div class='metric-sub' style='color: #94a3b8;'>Select grid factor</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    with e_kpi5:
        st.markdown(
            f"""
            <div class='metric-card'>
                <div class='metric-label'>Verified Realized Savings</div>
                <div class='metric-value' style='color: #22d3ee;'>{total_verified_kwh:,.0f} <span style='font-size: 0.9rem;'>kWh</span></div>
                <div class='metric-sub' style='color: #22d3ee;'>{len(historical_verifs)} verified log(s)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. Configured Emission Factor Source Metadata Box
    if carbon_calc.is_configured:
        st.markdown(
            f"""
            <div style='background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 10px; padding: 14px 18px; margin-bottom: 20px;'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <span style='font-size: 0.85rem; font-weight: 700; color: #38bdf8;'>Applicable Grid Emission Factor:</span>
                        <strong style='font-size: 1.1rem; color: #ffffff; margin-left: 8px;'>{carbon_calc.factor_kg_co2e_per_kwh} {carbon_calc.units}</strong>
                    </div>
                    <span class='badge-approved'>Scope 2 Documented</span>
                </div>
                <div style='font-size: 0.78rem; color: #94a3b8; margin-top: 6px;'>
                    <strong>Official Source:</strong> {carbon_calc.source}<br>
                    <strong>Geographic Region:</strong> {carbon_calc.region} | <strong>Effective Reporting Date:</strong> {carbon_calc.effective_date}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.warning(
            "⚠️ **Emission factor not configured.** To calculate potential or verified avoided emissions, "
            "please select a documented grid emission factor in the sidebar configuration."
        )

    # 3. Interactive Multi-Timescale Environmental Visualizations
    st.subheader("📊 Interactive Sustainability Visualizations")
    tab_co2_time, tab_recs_co2, tab_eq = st.tabs(
        ["📈 Cumulative Avoided GHG Timeline", "🧩 Avoided Emissions by Intervention", "🌳 Tangible Equivalencies"]
    )

    with tab_co2_time:
        # Build cumulative daily avoided emissions simulation
        daily_kwh = df_active.set_index("timestamp").resample("D")["energy_kwh"].sum().reset_index()
        # If recommendations applied, daily savings modeled proportionally
        daily_pct_reduction = (portfolio_savings["effective_reduction_pct"] / 100.0) if portfolio_savings["effective_reduction_pct"] > 0 else 0.0
        daily_kwh["saved_kwh"] = daily_kwh["energy_kwh"] * daily_pct_reduction
        
        factor = carbon_calc.factor_kg_co2e_per_kwh if carbon_calc.is_configured else 0.0
        daily_kwh["daily_avoided_kg"] = daily_kwh["saved_kwh"] * factor
        daily_kwh["cum_avoided_kg"] = daily_kwh["daily_avoided_kg"].cumsum()

        fig_co2 = go.Figure()
        fig_co2.add_trace(
            go.Scatter(
                x=daily_kwh["timestamp"],
                y=daily_kwh["cum_avoided_kg"],
                mode="lines",
                name="Cumulative Avoided CO2e (kg)",
                line=dict(color="#38bdf8", width=2.5),
                fill="tozeroy",
                fillcolor="rgba(56, 189, 248, 0.1)",
            )
        )
        fig_co2.update_layout(
            **PLOTLY_LAYOUT_DEFAULTS,
            height=360,
            title=f"Projected Cumulative Avoided GHG Emissions over 60 Days ({factor:.3f} kg CO2e/kWh)",
            yaxis_title="Avoided kg CO2e",
        )
        st.plotly_chart(fig_co2, use_container_width=True)

    with tab_recs_co2:
        if active_recommendations:
            rec_names = [r["title"][:30] + "..." for r in active_recommendations]
            rec_kwhs = [r["estimated_kwh_saving"] for r in active_recommendations]
            rec_co2s = [r.get("estimated_avoided_kg_co2e", 0.0) for r in active_recommendations]

            fig_rec_co2 = go.Figure(
                data=[
                    go.Bar(
                        name="Avoided CO2e (kg)",
                        x=rec_names,
                        y=rec_co2s,
                        marker_color="#38bdf8",
                        text=[f"{v:,.0f} kg" for v in rec_co2s],
                        textposition="auto",
                    )
                ]
            )
            fig_rec_co2.update_layout(
                **PLOTLY_LAYOUT_DEFAULTS,
                height=340,
                title="Potential Avoided GHG Emissions by Proposed Intervention",
            )
            st.plotly_chart(fig_rec_co2, use_container_width=True)

    with tab_eq:
        if avoided_co2_res["is_configured"]:
            eq = avoided_co2_res["equivalencies"]
            col_eq1, col_eq2 = st.columns(2)
            with col_eq1:
                st.markdown(
                    f"""
                    <div class='metric-card' style='text-align: center; padding: 24px;'>
                        <div style='font-size: 2.5rem;'>🌳</div>
                        <div class='metric-value' style='color: #10b981; margin: 10px 0;'>{eq['tree_seedlings_grown_for_10_years']:,.0f}</div>
                        <div class='metric-label'>Mature Tree Seedling Equivalents</div>
                        <div style='font-size: 0.78rem; color: #94a3b8; margin-top: 6px;'>
                            Carbon sequestered by tree seedlings grown for 10 years (US EPA GHG Factor: ~21.77 kg CO2/tree/yr)
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col_eq2:
                st.markdown(
                    f"""
                    <div class='metric-card' style='text-align: center; padding: 24px;'>
                        <div style='font-size: 2.5rem;'>🚗</div>
                        <div class='metric-value' style='color: #38bdf8; margin: 10px 0;'>{eq['avoided_passenger_car_km']:,.0f} <span style='font-size: 1rem;'>km</span></div>
                        <div class='metric-label'>Passenger Vehicle Kilometers Avoided</div>
                        <div style='font-size: 0.78rem; color: #94a3b8; margin-top: 6px;'>
                            Emissions avoided equivalent to typical gasoline passenger vehicle travel (EPA: ~0.192 kg CO2/km)
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# ==============================================================================
# PAGE 7: VERIFICATION AND HISTORY
# ==============================================================================
elif selected_page == "📈 Verification and History":
    st.markdown("### 📈 Before-and-After Verification & Decision Audit")
    st.caption("Rigorous counterfactual measurement of realized savings, SQLite audit trail, and executive reporting.")

    tab_verify, tab_history, tab_audit, tab_report = st.tabs(
        ["🔬 Savings Verification Lab", "📋 Recommendation Decisions", "🛡️ SQLite Audit Log", "📄 Executive Audit Summary"]
    )

    with tab_verify:
        st.subheader("Before-and-After Intervention Verification")
        st.caption(
            "Compares observed post-intervention electricity demand against pre-intervention hourly baseline counterfactuals. "
            "Distinguishes unadjusted vs. weather-normalized impact."
        )

        col_v1, col_v2 = st.columns([1, 1.2])

        with col_v1:
            st.markdown("##### 1. Define Intervention Parameters")
            v_name = st.selectbox(
                "Select Target Intervention:",
                [r["title"] for r in active_recommendations] + ["Custom Energy Conservation Measure"],
            )

            # Date selector
            min_ts = df_active["timestamp"].min().date()
            max_ts = df_active["timestamp"].max().date()
            default_interv_date = min_ts + timedelta(days=40)

            v_date = st.date_input(
                "Intervention Start Date:",
                value=default_interv_date,
                min_value=min_ts,
                max_value=max_ts,
            )

            v_expected_kwh = st.number_input(
                "Expected Savings Target (kWh):",
                min_value=10.0,
                max_value=50000.0,
                value=1200.0,
                step=100.0,
            )

            v_notes = st.text_input("Intervention Log Notes:", value="Sub-panel timer installed on central chiller.")

            # Run verification
            try:
                verif_output = SavingsVerifier.verify_intervention(
                    df=df_active,
                    intervention_name=v_name,
                    intervention_date=str(v_date),
                    expected_savings_kwh=v_expected_kwh,
                    tariff_inr_per_kwh=tariff_inr,
                    carbon_calc=carbon_calc,
                    notes=v_notes,
                )
            except Exception as e:
                st.error(f"Verification execution error: {str(e)}")
                verif_output = None

        with col_v2:
            if verif_output:
                st.markdown("##### 2. Realized Verification Results")
                status_color = "#10b981" if "Target Met" in verif_output["verification_status"] else "#f59e0b"
                
                st.markdown(
                    f"""
                    <div style='background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(255, 255, 255, 0.1); border-left: 4px solid {status_color}; border-radius: 10px; padding: 18px;'>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <h4 style='margin: 0; color: #ffffff;'>{verif_output["intervention_name"][:35]}</h4>
                            <span class='badge-approved' style='color: {status_color}; border-color: {status_color};'>
                                {verif_output["verification_status"]}
                            </span>
                        </div>
                        <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 14px;'>
                            <div>
                                <div class='metric-label'>Realized Savings</div>
                                <div style='font-size: 1.5rem; font-weight: 800; color: #ffffff;'>
                                    {verif_output['realized_savings_kwh']:,.1f} <span style='font-size: 0.85rem;'>kWh</span>
                                </div>
                                <div style='font-size: 0.78rem; color: #10b981;'>₹{verif_output['realized_savings_inr']:,.0f} saved</div>
                            </div>
                            <div>
                                <div class='metric-label'>Realization Rate</div>
                                <div style='font-size: 1.5rem; font-weight: 800; color: {status_color};'>
                                    {verif_output['realization_rate_pct']}%
                                </div>
                                <div style='font-size: 0.78rem; color: #94a3b8;'>of {verif_output['expected_savings_kwh']:,.0f} kWh target</div>
                            </div>
                            <div>
                                <div class='metric-label'>Post-Telemetry Duration</div>
                                <div style='font-size: 1.1rem; font-weight: 700; color: #cbd5e1;'>
                                    {verif_output['post_hours']} hours
                                </div>
                            </div>
                            <div>
                                <div class='metric-label'>Verified Avoided CO2e</div>
                                <div style='font-size: 1.1rem; font-weight: 700; color: #38bdf8;'>
                                    {verif_output['verified_avoided_kg_co2e']:,.1f} kg
                                </div>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if st.button("💾 Archive Verification Record to SQLite", key="save_verif_btn"):
                    try:
                        VerificationService.save_verification(verif_output)
                        st.success("Verification record successfully persisted to database!")
                        st.rerun()
                    except PermissionError as pe:
                        st.error(f"Action Restricted: {str(pe)}")

        # Historical verifications log
        st.markdown("---")
        st.subheader("📜 Historical Verified Interventions Log")
        all_v = VerificationService.get_all_verifications()
        if all_v:
            st.dataframe(pd.DataFrame(all_v), use_container_width=True)
        else:
            st.info("No verified intervention records archived yet. Run the verification above to archive your first audit.")

    with tab_history:
        st.subheader("Recommendation Action Lifecycle")
        filter_status = st.selectbox(
            "Filter History by Status:",
            ["All", "Pending", "Approved", "Rejected", "Completed"],
            index=0,
        )
        history_records = RecommendationService.get_recommendations(status_filter=filter_status)

        if history_records:
            hist_df = pd.DataFrame(history_records)[
                ["id", "scenario", "title", "severity", "status", "estimated_inr_saving", "estimated_kwh_saving", "priority_score", "updated_at"]
            ]
            st.dataframe(hist_df, use_container_width=True)

            csv_buffer = io.StringIO()
            hist_df.to_csv(csv_buffer, index=False)
            st.download_button(
                label="📥 Export Decision History to CSV",
                data=csv_buffer.getvalue(),
                file_name=f"ecopilot_decisions_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )
        else:
            st.info("No records match the selected status filter.")

    with tab_audit:
        st.subheader("System Event & Decision Audit Trail")
        st.caption("Captures every status change with exact timestamp and user remarks.")
        audit_trail = get_audit_trail()
        if audit_trail:
            st.dataframe(pd.DataFrame(audit_trail), use_container_width=True)
        else:
            st.info("No audit entries recorded yet.")

    with tab_report:
        st.subheader("Downloadable Executive Energy Audit Summary")
        factor_str = f"{carbon_calc.factor_kg_co2e_per_kwh} kg CO2e/kWh ({carbon_calc.source})" if carbon_calc.is_configured else "Emission factor not configured"
        report_text = f"""# ECOPILOT AI — EXECUTIVE ENERGY CONSERVATION AUDIT
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Target Facility: {selected_building}
Scenario Evaluated: {selected_scenario_key}
Active Grid Tariff: ₹{tariff_inr:.2f} / kWh
Grid Emission Factor: {factor_str}

## 1. CONSUMPTION BASELINE
- Total Recorded Electricity Demand: {total_consumption_kwh:,.1f} kWh
- Total Baseline Electricity Expense: ₹{total_bill_inr:,.2f}
- Hourly Time-Series Observations: {len(df_active)} hours (60 days)

## 2. ANOMALY DETECTION FINDINGS
- Total Anomalies Detected: {anomaly_results['summary']['total_anomalies']}
- Critical Severity Events: {anomaly_results['summary']['critical_severity']}
- High Severity Events: {anomaly_results['summary']['high_severity']}
- Nocturnal Baseload Waste (22:00 - 06:00): {anomaly_results['summary']['overnight_waste_count']} hours
- Total Documented Excess Energy Waste: {anomaly_results['summary']['total_excess_kwh']:,.1f} kWh
- Financial Exposure to Documented Waste: ₹{(anomaly_results['summary']['total_excess_kwh'] * tariff_inr):,.2f}

## 3. RECOMMENDED CONSERVATION MEASURES
Total Synthesized Actionable Measures: {len(active_recommendations)}
Deduplicated Potential Energy Savings: {portfolio_savings['deduplicated_saved_kwh']:,.1f} kWh ({portfolio_savings['effective_reduction_pct']}%)
Deduplicated Potential Financial Savings: ₹{portfolio_savings['deduplicated_saved_inr']:,.2f}
Potential Avoided GHG Emissions: {avoided_co2_res['avoided_emissions_kg_co2e'] or 0.0:,.1f} kg CO2e

## 4. VERIFIED OUTCOMES (SUB-METER LOGGING)
Verified Realized Energy Savings: {total_verified_kwh:,.1f} kWh
Verified Financial Savings: ₹{total_verified_inr:,.2f}
Verified Avoided GHG Emissions: {total_verified_co2:,.1f} kg CO2e

## 5. ASSUMPTIONS & LIMITATIONS
1. Baseline readings and temperatures follow simulated facility operating hours for demonstration.
2. Savings are conservative projections based on mathematical models and portfolio overlap deduplication.
3. Central Electricity Authority (CEA) of India Scope 2 weighted average grid baseline applied when configured.
4. Final verified savings require post-implementation sub-meter data logging.
"""
        st.text_area("Audit Report Preview:", value=report_text, height=300)
        st.download_button(
            label="📄 Download Executive Audit Report (.txt)",
            data=report_text,
            file_name=f"ecopilot_audit_report_{selected_building.replace(' ', '_')}.txt",
            mime="text/plain",
        )


# ==============================================================================
# PAGE 8: GREEN AI EFFICIENCY
# ==============================================================================
elif selected_page == "⚡ Green AI Efficiency":
    st.markdown("### ⚡ Green AI Efficiency Monitor")
    st.caption(
        "Software telemetry tracking computational latency, cache hits, avoided redundant recomputations, "
        "and architectural efficiency compared against naive cloud LLM pipelines."
    )

    metrics_summary = green_monitor.get_metrics_summary()
    pipeline_comp = green_monitor.get_pipeline_comparison()

    # Top KPI cards
    g1, g2, g3, g4 = st.columns(4)
    with g1:
        st.markdown(
            f"""
            <div class='metric-card'>
                <div class='metric-label'>Total Measured Compute</div>
                <div class='metric-value' style='color: #10b981;'>{metrics_summary['total_measured_execution_ms']} <span style='font-size: 1rem;'>ms</span></div>
                <div class='metric-sub'>{metrics_summary['total_logged_tasks']} tasks profiled</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with g2:
        st.markdown(
            f"""
            <div class='metric-card'>
                <div class='metric-label'>Cache Hits</div>
                <div class='metric-value' style='color: #38bdf8;'>{metrics_summary['cache_hits']}</div>
                <div class='metric-sub'>{metrics_summary['avoided_duplicate_operations']} avoided re-runs</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with g3:
        st.markdown(
            f"""
            <div class='metric-card'>
                <div class='metric-label'>Remote API Calls</div>
                <div class='metric-value' style='color: #a78bfa;'>{metrics_summary['cloud_api_calls_incurred']}</div>
                <div class='metric-sub'>100% On-Premise Local</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with g4:
        st.markdown(
            f"""
            <div class='metric-card' style='border-color: rgba(16, 185, 129, 0.4);'>
                <div class='metric-label' style='color: #34d399;'>Architecture Speedup</div>
                <div class='metric-value' style='color: #34d399;'>{pipeline_comp['comparison_metrics']['latency_speedup']}</div>
                <div class='metric-sub' style='color: #34d399;'>vs Cloud LLM Prompting</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Comparative Architecture Table
    st.subheader("⚖️ Architectural Efficiency: EcoPilot Local Edge vs. Cloud LLM Baseline")
    col_arc1, col_arc2 = st.columns(2)

    with col_arc1:
        st.markdown(
            f"""
            <div style='background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 10px; padding: 18px;'>
                <h4 style='color: #10b981; margin-top: 0;'>🌱 EcoPilot AI (Local Edge Architecture)</h4>
                <ul style='font-size: 0.85rem; color: #cbd5e1; line-height: 1.7;'>
                    <li><strong>Execution Mode:</strong> {pipeline_comp['ecopilot_local_architecture']['execution_mode']}</li>
                    <li><strong>Execution Time:</strong> {pipeline_comp['ecopilot_local_architecture']['total_latency_ms']} ms</li>
                    <li><strong>Remote API Calls:</strong> {pipeline_comp['ecopilot_local_architecture']['api_calls']}</li>
                    <li><strong>Tokens Billed:</strong> {pipeline_comp['ecopilot_local_architecture']['tokens_consumed']}</li>
                    <li><strong>Offline Capability:</strong> 100% Fully Functional Offline</li>
                    <li><strong>Financial API Cost:</strong> $0.00 / month</li>
                    <li><strong>Data Privacy:</strong> 100% Facility Data Stays On-Premise</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_arc2:
        st.markdown(
            f"""
            <div style='background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 10px; padding: 18px;'>
                <h4 style='color: #ef4444; margin-top: 0;'>☁️ Naive Cloud LLM Baseline</h4>
                <ul style='font-size: 0.85rem; color: #cbd5e1; line-height: 1.7;'>
                    <li><strong>Execution Mode:</strong> {pipeline_comp['unoptimized_cloud_llm_baseline']['execution_mode']}</li>
                    <li><strong>Execution Time:</strong> ~{pipeline_comp['unoptimized_cloud_llm_baseline']['estimated_latency_ms']:,.0f} ms (network + generation)</li>
                    <li><strong>Remote API Calls:</strong> ~{pipeline_comp['unoptimized_cloud_llm_baseline']['estimated_api_calls']} per session</li>
                    <li><strong>Tokens Billed:</strong> ~{pipeline_comp['unoptimized_cloud_llm_baseline']['estimated_tokens']:,} tokens</li>
                    <li><strong>Offline Capability:</strong> Fails without active internet & paid API keys</li>
                    <li><strong>Financial API Cost:</strong> {pipeline_comp['unoptimized_cloud_llm_baseline']['financial_api_cost_usd']}</li>
                    <li><strong>Data Privacy:</strong> Raw campus load curves transmitted to third-party cloud</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Transparency Disclaimers
    st.info(
        "🛡️ **Green AI Transparency & Ethical Disclaimers:**<br>"
        "1. Latency figures reflect actual measured Python wall-clock execution time on this hardware.<br>"
        "2. Direct physical GPU wattage and data center carbon emissions are **not** fabricated because physical "
        "hardware power meters are unavailable.<br>"
        "3. Local edge inference guarantees zero recurring cloud API billing and zero transmission of sensitive facility telemetry.",
        icon="ℹ️",
    )
