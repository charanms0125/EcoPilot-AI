"""
Script to generate the professional 12-slide EcoPilot AI PowerPoint Presentation (.pptx).
Applies 16:9 widescreen layout, dark navy and emerald sustainability palette,
rich card containers, visual metrics, tables, and comprehensive speaker notes for every slide.
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

def create_deck(output_paths):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # Color Palette Definitions
    COLOR_BG = RGBColor(7, 13, 24)        # #070D18 Deep Navy
    COLOR_PANEL = RGBColor(15, 23, 42)    # #0F172A Slate 900
    COLOR_CARD = RGBColor(11, 19, 34)     # #0B1322 Dark Navy Card
    COLOR_EMERALD = RGBColor(16, 185, 129)# #10B981 Emerald Primary
    COLOR_TEAL = RGBColor(52, 211, 153)   # #34D399 Bright Mint/Teal
    COLOR_CYAN = RGBColor(56, 189, 248)   # #38BDF8 Cyan
    COLOR_AMBER = RGBColor(245, 158, 11)  # #F59E0B Warning / High
    COLOR_RED = RGBColor(239, 68, 68)     # #EF4444 Critical
    COLOR_WHITE = RGBColor(248, 250, 252) # #F8FAFC Heading text
    COLOR_SLATE = RGBColor(148, 163, 184) # #94A3B8 Muted text
    COLOR_BORDER = RGBColor(30, 41, 59)   # #1E293B Border
    COLOR_EMERALD_BG = RGBColor(6, 78, 59)# #064E3B Forest Green

    blank_layout = prs.slide_layouts[6] # Blank slide layout

    def apply_slide_background(slide):
        background = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        background.fill.solid()
        background.fill.fore_color.rgb = COLOR_BG
        background.line.color.rgb = COLOR_BG
        return background

    def add_header(slide, category_text, title_text, subtitle_text=None):
        # Category Badge
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.35))
        tf_cat = cat_box.text_frame
        tf_cat.word_wrap = True
        tf_cat.margin_left = tf_cat.margin_right = tf_cat.margin_top = tf_cat.margin_bottom = 0
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.name = "Arial"
        p_cat.font.size = Pt(10)
        p_cat.font.bold = True
        p_cat.font.color.rgb = COLOR_EMERALD

        # Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11.7), Inches(0.65))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        tf_title.margin_left = tf_title.margin_right = tf_title.margin_top = tf_title.margin_bottom = 0
        p_title = tf_title.paragraphs[0]
        p_title.text = title_text
        p_title.font.name = "Arial"
        p_title.font.size = Pt(22)
        p_title.font.bold = True
        p_title.font.color.rgb = COLOR_WHITE

        # Subtitle
        if subtitle_text:
            sub_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.35), Inches(11.7), Inches(0.4))
            tf_sub = sub_box.text_frame
            tf_sub.word_wrap = True
            tf_sub.margin_left = tf_sub.margin_right = tf_sub.margin_top = tf_sub.margin_bottom = 0
            p_sub = tf_sub.paragraphs[0]
            p_sub.text = subtitle_text
            p_sub.font.name = "Arial"
            p_sub.font.size = Pt(12)
            p_sub.font.color.rgb = COLOR_SLATE

        # Accent top divider line
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.8), Inches(11.7), Inches(0.02))
        line.fill.solid()
        line.fill.fore_color.rgb = COLOR_BORDER
        line.line.color.rgb = COLOR_BORDER

    def add_card(slide, left, top, width, height, bg_color=COLOR_PANEL, border_color=COLOR_BORDER):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        card.line.color.rgb = border_color
        card.line.width = Pt(1)
        return card

    def add_speaker_note(slide, script_text):
        notes_slide = slide.notes_slide
        text_frame = notes_slide.notes_text_frame
        text_frame.text = script_text

    # =========================================================================
    # SLIDE 1: TITLE SLIDE
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    apply_slide_background(s1)

    # Decorative hero card
    add_card(s1, Inches(0.8), Inches(0.8), Inches(11.7), Inches(5.9), bg_color=COLOR_PANEL, border_color=COLOR_EMERALD)

    # Pill badge
    badge = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.3), Inches(1.3), Inches(4.5), Inches(0.4))
    badge.fill.solid()
    badge.fill.fore_color.rgb = COLOR_EMERALD_BG
    badge.line.color.rgb = COLOR_EMERALD
    p_b = badge.text_frame.paragraphs[0]
    p_b.text = "🌱 GREEN AI PLATFORM • ZERO CLOUD API COST"
    p_b.alignment = PP_ALIGN.CENTER
    p_b.font.size = Pt(10)
    p_b.font.bold = True
    p_b.font.color.rgb = COLOR_TEAL

    # Title & Subtitle Text
    tb1 = s1.shapes.add_textbox(Inches(1.3), Inches(1.9), Inches(6.5), Inches(2.2))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    p1 = tf1.paragraphs[0]
    p1.text = "EcoPilot AI"
    p1.font.name = "Arial"
    p1.font.size = Pt(44)
    p1.font.bold = True
    p1.font.color.rgb = COLOR_WHITE

    p2 = tf1.add_paragraph()
    p2.text = "Explainable AI for Sustainable Building Energy Management"
    p2.font.name = "Arial"
    p2.font.size = Pt(18)
    p2.font.bold = True
    p2.font.color.rgb = COLOR_EMERALD

    p3 = tf1.add_paragraph()
    p3.text = "\nAn evidence-backed, human-in-the-loop energy intelligence system that diagnoses waste, forecasts demand, simulates financial returns, and verifies real-world carbon reduction."
    p3.font.name = "Arial"
    p3.font.size = Pt(13)
    p3.font.color.rgb = COLOR_SLATE

    # Metric callout boxes (Bottom Left)
    m_lefts = [Inches(1.3), Inches(3.2), Inches(5.1)]
    m_titles = ["100% OFFLINE", "< 500 ms", "IPMVP VERIFIED"]
    m_subs = ["Zero Paid Cloud APIs", "Local CPU Latency", "Option C Counterfactuals"]
    for i in range(3):
        box = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, m_lefts[i], Inches(4.5), Inches(1.7), Inches(1.4))
        box.fill.solid()
        box.fill.fore_color.rgb = COLOR_CARD
        box.line.color.rgb = COLOR_BORDER
        tf = box.text_frame
        tf.word_wrap = True
        tf.margin_top = Inches(0.2)
        p_val = tf.paragraphs[0]
        p_val.text = m_titles[i]
        p_val.alignment = PP_ALIGN.CENTER
        p_val.font.size = Pt(13)
        p_val.font.bold = True
        p_val.font.color.rgb = COLOR_EMERALD

        p_sub = tf.add_paragraph()
        p_sub.text = m_subs[i]
        p_sub.alignment = PP_ALIGN.CENTER
        p_sub.font.size = Pt(9)
        p_sub.font.color.rgb = COLOR_SLATE

    # Smart Campus Topology Graphic Box (Right Side)
    add_card(s1, Inches(7.5), Inches(1.3), Inches(4.5), Inches(4.8), bg_color=COLOR_CARD, border_color=COLOR_BORDER)
    r_tb = s1.shapes.add_textbox(Inches(7.8), Inches(1.6), Inches(3.9), Inches(4.2))
    rtf = r_tb.text_frame
    rtf.word_wrap = True

    rp1 = rtf.paragraphs[0]
    rp1.text = "SMART CAMPUS DEPLOYMENT ARCHETYPES"
    rp1.font.size = Pt(12)
    rp1.font.bold = True
    rp1.font.color.rgb = COLOR_CYAN

    archetypes = [
        ("🏛️ Academic Complex & Lecture Halls", "Centrally scheduled HVAC & auditorium lighting"),
        ("🏢 Student Hostels & Residences", "Nocturnal water heating baseline & laundry loads"),
        ("🏢 Administrative & IT Buildings", "Coincident workstation in-rush & variable chiller staging"),
        ("❄️ Central Chiller Plant", "Cooling degree day sensitivity & pumping arbitrage"),
    ]
    for name, desc in archetypes:
        p_name = rtf.add_paragraph()
        p_name.text = f"\n{name}"
        p_name.font.size = Pt(11)
        p_name.font.bold = True
        p_name.font.color.rgb = COLOR_WHITE

        p_desc = rtf.add_paragraph()
        p_desc.text = desc
        p_desc.font.size = Pt(9.5)
        p_desc.font.color.rgb = COLOR_SLATE

    add_speaker_note(s1, "Good morning, everyone. Today, I am proud to present EcoPilot AI — an explainable, human-in-the-loop Green AI system designed for sustainable building energy management. Educational campuses, commercial offices, and multi-facility institutions face mounting power tariffs and stringent carbon reduction mandates. However, facility operators lack the tools to translate millions of raw hourly meter readings into accountable engineering action. EcoPilot AI solves this systemic gap by combining local machine learning with deterministic physics rules, providing an evidence-backed platform that diagnoses waste, forecasts demand, simulates financial savings, and empirically verifies post-intervention carbon reduction on site.")

    # =========================================================================
    # SLIDE 2: PROBLEM STATEMENT
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    apply_slide_background(s2)
    add_header(s2, "The Operational Problem", "The Hidden Energy Waste Crisis in Institutional Buildings", "Campuses and commercial facilities routinely waste 15% to 30% of total electrical power.")

    # Left Container: 4 Core Waste Drivers
    add_card(s2, Inches(0.8), Inches(2.1), Inches(5.7), Inches(4.8))
    tb_l = s2.shapes.add_textbox(Inches(1.0), Inches(2.2), Inches(5.3), Inches(4.5))
    tf_l = tb_l.text_frame
    tf_l.word_wrap = True

    p = tf_l.paragraphs[0]
    p.text = "4 PRIMARY DRIVERS OF ENERGY WASTE"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_AMBER

    waste_drivers = [
        ("❄️ After-Hours HVAC Drift", "Central chillers and AHUs cycling at night while wings are 100% empty."),
        ("💡 Unmanaged Nocturnal Baselines", "High-bay corridor lighting and lab equipment left powered 24/7."),
        ("⚡ Coincident Peak Demand Spikes", "Unstaggered motor and pump startups creating costly contract demand surcharges."),
        ("⏱️ Misaligned Flexible Loads", "Water pumping and laundry operating during high Time-of-Day tariff slots (₹11.50/kWh)."),
    ]
    for title, desc in waste_drivers:
        pt = tf_l.add_paragraph()
        pt.text = f"\n• {title}"
        pt.font.size = Pt(11)
        pt.font.bold = True
        pt.font.color.rgb = COLOR_WHITE
        pd = tf_l.add_paragraph()
        pd.text = f"  {desc}"
        pd.font.size = Pt(10)
        pd.font.color.rgb = COLOR_SLATE

    # Right Container: 3 Systemic Gaps
    add_card(s2, Inches(6.8), Inches(2.1), Inches(5.7), Inches(4.8))
    tb_r = s2.shapes.add_textbox(Inches(7.0), Inches(2.2), Inches(5.3), Inches(4.5))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True

    p = tf_r.paragraphs[0]
    p.text = "THE 3 SYSTEMIC OPERATIONAL GAPS"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_RED

    gaps = [
        ("1. Passive Retrospective Dashboards", "Existing software only renders historical line charts after the bill arrives. Operators cannot manually scan gigabytes of CSV data to isolate root causes."),
        ("2. Prohibitive Proprietary BMS Silos", "Enterprise building management systems (Honeywell, Johnson Controls, Siemens) require millions of rupees in hardware, custom BACnet gateways, and vendor lock-in."),
        ("3. Ungrounded AI & Greenwashing", "Modern AI projects often hallucinate energy metrics using generic cloud LLM prompts, lacking physical grounding, audit trails, or real-world verification."),
    ]
    for title, desc in gaps:
        pt = tf_r.add_paragraph()
        pt.text = f"\n• {title}"
        pt.font.size = Pt(11)
        pt.font.bold = True
        pt.font.color.rgb = COLOR_WHITE
        pd = tf_r.add_paragraph()
        pd.text = f"  {desc}"
        pd.font.size = Pt(10)
        pd.font.color.rgb = COLOR_SLATE

    add_speaker_note(s2, "Across commercial buildings and university campuses, electricity accounts for up to 45% of total operating budgets. Routine energy audits reveal that between 15% and 30% of this energy is completely wasted. Why does this continue? First, after-hours HVAC drift and nocturnal baseline inflation happen silently when staff are asleep. Second, coincident motor surges trigger heavy monthly demand penalty charges. Third, today's energy management dashboards are completely passive — they show colorful charts after the bill arrives, but they don't tell operators what to do. Full-scale Building Management Systems cost millions of rupees, and many modern AI apps simply hallucinate carbon figures using cloud LLMs. We need an explainable, deterministic, and affordable approach.")

    # =========================================================================
    # SLIDE 3: PROPOSED SOLUTION (7-STAGE LOOP)
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    apply_slide_background(s3)
    add_header(s3, "The EcoPilot Solution", "7-Stage Closed-Loop Conservation Cycle", "An accountable, human-in-the-loop energy intelligence workflow.")

    # 7 Process Cards
    stages = [
        ("1. OBSERVE", "Ingest & sanitize hourly sub-meter telemetry (kWh/kW).", COLOR_EMERALD),
        ("2. ANALYZE", "Robust Z-score & Isolation Forest anomaly detection.", COLOR_EMERALD),
        ("3. PLAN", "Group waste patterns by physical building subsystems.", COLOR_EMERALD),
        ("4. RECOMMEND", "Generate evidence-anchored prioritized action tasks.", COLOR_TEAL),
        ("5. SIMULATE", "Calculate overlap-deduplicated ₹ and avoided CO2e.", COLOR_CYAN),
        ("6. APPROVE", "Human-in-the-loop approval gate with SQLite audit trail.", COLOR_CYAN),
        ("7. VERIFY", "IPMVP Option C weather-normalized post-intervention audit.", COLOR_CYAN),
    ]

    card_width = Inches(1.58)
    card_gap = Inches(0.12)
    left_start = Inches(0.8)

    for i, (stg_title, stg_desc, border_col) in enumerate(stages):
        pos_left = left_start + i * (card_width + card_gap)
        add_card(s3, pos_left, Inches(2.2), card_width, Inches(3.2), bg_color=COLOR_PANEL, border_color=border_col)
        
        tb = s3.shapes.add_textbox(pos_left + Inches(0.1), Inches(2.4), card_width - Inches(0.2), Inches(2.8))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p_num = tf.paragraphs[0]
        p_num.text = stg_title
        p_num.font.size = Pt(11)
        p_num.font.bold = True
        p_num.font.color.rgb = border_col
        p_num.alignment = PP_ALIGN.CENTER
        
        p_desc = tf.add_paragraph()
        p_desc.text = f"\n{stg_desc}"
        p_desc.font.size = Pt(9.5)
        p_desc.font.color.rgb = COLOR_SLATE
        p_desc.alignment = PP_ALIGN.CENTER

    # Bottom 3 Architecture Principles
    p_cards = [
        ("🛡️ Human-in-the-Loop Governance", "The AI acts as an advisory co-pilot. It never switches physical contactors autonomously; actions require verified human sign-off."),
        ("⚡ 100% Offline Green AI Execution", "Core inference runs locally on standard CPU hardware in < 500 ms without external cloud API dependencies or token latency."),
        ("📊 Transparent Physics Grounding", "Every recommendation is linked to specific surplus kilowatt-hours, statistical sigma deviations, and official grid emission references."),
    ]
    p_lefts = [Inches(0.8), Inches(4.8), Inches(8.8)]
    for i, (title, desc) in enumerate(p_cards):
        add_card(s3, p_lefts[i], Inches(5.6), Inches(3.7), Inches(1.4), bg_color=COLOR_CARD, border_color=COLOR_BORDER)
        tb = s3.shapes.add_textbox(p_lefts[i] + Inches(0.15), Inches(5.7), Inches(3.4), Inches(1.2))
        tf = tb.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = title
        p1.font.size = Pt(11)
        p1.font.bold = True
        p1.font.color.rgb = COLOR_WHITE
        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(9.5)
        p2.font.color.rgb = COLOR_SLATE

    add_speaker_note(s3, "EcoPilot AI introduces an evidence-backed, 7-stage closed-loop conservation cycle. It begins by Observing raw sub-meter telemetry and Analyzing patterns using dual statistical and machine learning engines. In the Planning and Recommendation stages, the agent synthesizes waste events into concrete Energy Conservation Measures — such as contactor timer installations or setpoint adjustments. Rather than guessing outcomes, it Simulates financial and carbon returns using deduplicated physics models. Crucially, the platform enforces Human-in-the-Loop Approval: facility directors must review and approve measures before maintenance is scheduled. Finally, it Verifies realized savings from post-intervention telemetry to confirm real-world performance.")

    # =========================================================================
    # SLIDE 4: END-TO-END WORKFLOW & SAVINGS SEPARATION
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    apply_slide_background(s4)
    add_header(s4, "Operational Workflow", "End-to-End Execution & Ontological Savings Separation", "Strictly distinguishing theoretical projections from audited physical savings.")

    # Left Card: Pre-Intervention Pipeline
    add_card(s4, Inches(0.8), Inches(2.1), Inches(5.7), Inches(4.9), bg_color=COLOR_PANEL, border_color=COLOR_AMBER)
    tb = s4.shapes.add_textbox(Inches(1.1), Inches(2.3), Inches(5.1), Inches(4.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "TRACK A: PRE-INTERVENTION ESTIMATES"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_AMBER

    items_a = [
        ("1. Telemetry Ingestion & Quality Audit", "Validates time monotonicity, normalizes timezones, and computes a 0-100% Data Health Score."),
        ("2. Dual-Engine Anomaly Isolation", "Clean baseline Z-score isolates nocturnal drift; Isolation Forest identifies multi-dimensional surges."),
        ("3. 3-Model Demand Forecasting", "Evaluates Persistence, Seasonal, and Random Forest models using chronological splits and WAPE."),
        ("4. Overlap-Deduplicated Simulation", "Compounds multiple ECMs sequentially with an 85% physical ceiling to prevent double-counting."),
        ("Outcome: Potential Savings", "Projected Avoided Energy (kWh), Projected Financial Return (₹), and Potential Avoided GHG (kg CO2e)."),
    ]
    for title, desc in items_a:
        pt = tf.add_paragraph()
        pt.text = f"\n• {title}"
        pt.font.size = Pt(10.5)
        pt.font.bold = True
        pt.font.color.rgb = COLOR_WHITE
        pd = tf.add_paragraph()
        pd.text = f"  {desc}"
        pd.font.size = Pt(9.5)
        pd.font.color.rgb = COLOR_SLATE

    # Right Card: Post-Intervention Pipeline
    add_card(s4, Inches(6.8), Inches(2.1), Inches(5.7), Inches(4.9), bg_color=COLOR_PANEL, border_color=COLOR_EMERALD)
    tb = s4.shapes.add_textbox(Inches(7.1), Inches(2.3), Inches(5.1), Inches(4.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "TRACK B: POST-INTERVENTION VERIFICATION"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_EMERALD

    items_b = [
        ("1. Managerial Approval Gate", "Facility operator reviews evidence anchors, approves maintenance, and logs sign-off into SQLite."),
        ("2. Physical Retrofit Execution", "Engineering team physically installs contactor timers, re-schedules pumps, or adjusts chiller setpoints."),
        ("3. Follow-Up Sub-Meter Collection", "Continuous 48+ hour post-intervention monitoring records actual operational energy consumption."),
        ("4. IPMVP Option C Counterfactual Model", "Normalizes baseline for ambient temperature variations using empirical cooling degree sensitivity."),
        ("Outcome: Verified Realized Savings", "Realized Energy (kWh), Realized Rupees (₹), Realization Rate (%), and Verified Avoided CO2e (kg)."),
    ]
    for title, desc in items_b:
        pt = tf.add_paragraph()
        pt.text = f"\n• {title}"
        pt.font.size = Pt(10.5)
        pt.font.bold = True
        pt.font.color.rgb = COLOR_WHITE
        pd = tf.add_paragraph()
        pd.text = f"  {desc}"
        pd.font.size = Pt(9.5)
        pd.font.color.rgb = COLOR_SLATE

    add_speaker_note(s4, "A fundamental flaw in energy software is conflating theoretical estimates with verified reality. On this slide, you see EcoPilot AI’s two-track workflow. In Phase 1 and 2, telemetry is validated, anomalies are isolated, and future demand is forecasted. In Phase 3, the agent simulates Projected Potential Savings. But we never stop there. Once a human operator approves an action and it is implemented on site, Phase 4 activates. We collect post-intervention telemetry and run an IPMVP-aligned counterfactual analysis to calculate Verified Realized Savings and realization rates. This strict ontological separation protects institutions from greenwashing and guarantees financial accountability.")

    # =========================================================================
    # SLIDE 5: SYSTEM ARCHITECTURE
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    apply_slide_background(s5)
    add_header(s5, "System Architecture", "Decoupled 4-Tier Layered Architecture", "Separation of concerns ensuring auditability, modularity, and security.")

    # 4 Architecture Tier Bars
    tiers = [
        ("1. PRESENTATION LAYER (app.py)", "Streamlit Dashboard • 8 Modular Views • Plotly Dark Visualizations • Sidebar RBAC Role Selector • 100% SQL-Free UI", COLOR_CYAN),
        ("2. SERVICE LAYER (src/services.py)", "EnergyDataService • AnalyticsService • RecommendationService • SavingsSimulatorService • VerificationService • SystemAdminService", COLOR_EMERALD),
        ("3. REPOSITORY LAYER (src/repositories.py)", "RecommendationRepository • AlertRepository • VerificationRepository • SimulationRepository • DatasetUploadRepository • DatabaseAdminRepository", COLOR_TEAL),
        ("4. PERSISTENCE LAYER (src/database.py)", "SQLite Database (WAL Mode) • PRAGMA foreign_keys = ON • schema_migrations (001-004) • admin_audit_log • State Transitions", COLOR_BLUE := RGBColor(59, 130, 246)),
    ]

    for i, (t_title, t_desc, col) in enumerate(tiers):
        top_pos = Inches(2.1 + i * 1.05)
        add_card(s5, Inches(0.8), top_pos, Inches(11.7), Inches(0.9), bg_color=COLOR_PANEL, border_color=col)
        tb = s5.shapes.add_textbox(Inches(1.0), top_pos + Inches(0.12), Inches(11.3), Inches(0.65))
        tf = tb.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = t_title
        p1.font.size = Pt(11)
        p1.font.bold = True
        p1.font.color.rgb = col
        p2 = tf.add_paragraph()
        p2.text = t_desc
        p2.font.size = Pt(9.5)
        p2.font.color.rgb = COLOR_SLATE

    # Supporting Pillars (Bottom)
    p_box = add_card(s5, Inches(0.8), Inches(6.1), Inches(11.7), Inches(0.85), bg_color=COLOR_CARD, border_color=COLOR_BORDER)
    tb_bot = s5.shapes.add_textbox(Inches(1.0), Inches(6.15), Inches(11.3), Inches(0.75))
    tf_bot = tb_bot.text_frame
    tf_bot.word_wrap = True
    p1 = tf_bot.paragraphs[0]
    p1.text = "CROSS-CUTTING ENTERPRISE PILLARS:"
    p1.font.size = Pt(9.5)
    p1.font.bold = True
    p1.font.color.rgb = COLOR_WHITE
    p2 = tf_bot.add_paragraph()
    p2.text = "• Pydantic v2 Typed Data Contracts (src/schemas.py)   • 4-Tier RBAC Engine (src/auth.py)   • Centralized Settings (src/config.py)   • Green AI Monitor (src/green_ai.py)"
    p2.font.size = Pt(9.5)
    p2.font.color.rgb = COLOR_TEAL

    add_speaker_note(s5, "Here is the production-ready architecture of EcoPilot AI. We have strictly decoupled the application into a clean 4-tier model. The Streamlit Presentation Layer handles user interaction, rendering eight dedicated dashboard views. All business logic resides in our Service Layer, which enforces role-based access control and mathematical routines. The Service Layer communicates with a dedicated Repository Layer that encapsulates SQLite database access with foreign key enforcement and transactional rollbacks. Cross-cutting pillars include Pydantic typed schemas for contract safety, centralized environment configuration, version-controlled schema migrations, and local Green AI telemetry monitoring.")

    # =========================================================================
    # SLIDE 6: DATA QUALITY & ANOMALY DETECTION
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    apply_slide_background(s6)
    add_header(s6, "Analytical Rigor", "Data Quality & Dual Anomaly Detection Ensemble", "Preventing baseline contamination while providing explainable root-cause evidence.")

    # Left Container: Ingestion & Quality
    add_card(s6, Inches(0.8), Inches(2.1), Inches(5.7), Inches(4.9))
    tb = s6.shapes.add_textbox(Inches(1.0), Inches(2.2), Inches(5.3), Inches(4.6))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "INGESTION QUALITY & TELEMETRY SANITIZATION"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_EMERALD

    items_ing = [
        ("Timezone Normalization", "Converts ISO-8601 strings (UTC or +05:30) to standardized tz-naive timestamps, eliminating downstream slicing and shift comparison crashes."),
        ("Cadence & Frequency Detection", "Automatically identifies 15m, 30m, hourly, or daily cadences; flags irregular interval breaches in the quality report."),
        ("True-Interval kW to kWh Integration", "Active power in kW is integrated into kWh using actual point-to-point timestamp intervals (Δt), avoiding inaccurate 1:1 assumptions."),
        ("Non-Physical Value Sanitization", "Clips impossible negative readings (<0 kWh) to 0.0 kWh standby minimums with audit tracking; interpolates small gaps while rejecting gaps >24h."),
        ("Automated Data Health Score", "Computes a transparent 0-100% data health metric validated against DataQualityReportSchema."),
    ]
    for title, desc in items_ing:
        pt = tf.add_paragraph()
        pt.text = f"\n• {title}"
        pt.font.size = Pt(10)
        pt.font.bold = True
        pt.font.color.rgb = COLOR_WHITE
        pd = tf.add_paragraph()
        pd.text = f"  {desc}"
        pd.font.size = Pt(9)
        pd.font.color.rgb = COLOR_SLATE

    # Right Container: Dual Detection Ensemble
    add_card(s6, Inches(6.8), Inches(2.1), Inches(5.7), Inches(4.9))
    tb_r = s6.shapes.add_textbox(Inches(7.0), Inches(2.2), Inches(5.3), Inches(4.6))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True
    p = tf_r.paragraphs[0]
    p.text = "DUAL DETECTION ENSEMBLE & 4 SEVERITY TIERS"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN

    items_anom = [
        ("Clean Baseline & Robust Dispersion", "Baselines are calculated strictly on clean data using Median and Median Absolute Deviation (MAD), preventing historical waste from inflating sigma."),
        ("Unsupervised Isolation Forest", "Evaluates multi-dimensional multivariate isolation scores without parametric distribution assumptions, cross-validating statistical flags."),
        ("Phenomenon Classification", "Explicitly separates Off-Hours Wastage (nocturnal HVAC/lighting drift) from Operational Consumption Spikes (motor startup surges)."),
        ("4 Transparent Severity Tiers", "• Critical: z ≥ 4.0σ or Δ ≥ 40 kWh surplus\n• High: z ≥ 3.0σ or 20-40 kWh surplus\n• Medium: z ≥ 2.0σ or 10-20 kWh surplus\n• Low: Statistical flag with < 10 kWh surplus"),
    ]
    for title, desc in items_anom:
        pt = tf_r.add_paragraph()
        pt.text = f"\n• {title}"
        pt.font.size = Pt(10)
        pt.font.bold = True
        pt.font.color.rgb = COLOR_WHITE
        pd = tf_r.add_paragraph()
        pd.text = f"  {desc}"
        pd.font.size = Pt(9)
        pd.font.color.rgb = COLOR_SLATE

    add_speaker_note(s6, "Accurate AI requires clean telemetry. Our data pipeline automatically handles timezone conversions, detects sampling frequency, clips non-physical negative values, and integrates power in kilowatts into kilowatt-hours using actual interval deltas. For anomaly detection, naive systems suffer from baseline contamination: if waste occurred last week, standard deviation inflates and hides future waste. EcoPilot AI prevents this using a clean baseline calculated with median and Median Absolute Deviation. We ensemble this with an unsupervised Isolation Forest. Anomalies are classified into four severity tiers and clearly categorized as either after-hours energy wastage or operational consumption spikes, providing operators with actionable physical context.")

    # =========================================================================
    # SLIDE 7: DEMAND FORECASTING (3-MODEL TOURNAMENT)
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    apply_slide_background(s7)
    add_header(s7, "Predictive Intelligence", "Demand Forecasting & 3-Model Tournament", "Chronological splitting prevents leakage, while empirical prediction intervals quantify uncertainty.")

    # Left Container: Tournament Details
    add_card(s7, Inches(0.8), Inches(2.1), Inches(5.7), Inches(4.9))
    tb = s7.shapes.add_textbox(Inches(1.0), Inches(2.2), Inches(5.3), Inches(4.6))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "CHRONOLOGICAL 3-WAY BENCHMARK"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_EMERALD

    items_fc = [
        ("Leakage-Free Chronological Splitting", "Time-series partitioned strictly in sequence: Training (earliest 70%), Validation (middle 15%), and held-out Test (final 15%). Future timestamps never leak into past feature generation."),
        ("3-Model Candidate Tournament", "• Persistence Baseline: Predicts y_t = y_{t-24} (autocorrelation benchmark)\n• Seasonal Baseline: Predicts y_t = median(y | day_of_week, hour)\n• Random Forest Regressor: Multi-lag tree ensemble with cyclical sine/cosine encodings"),
        ("Why WAPE Over MAPE?", "Nighttime building loads near standby levels (y_t → 0) cause MAPE to divide by near-zero, producing infinite error inflation. WAPE provides volume-weighted, scale-stable accuracy."),
        ("Calibrated Empirical Intervals", "Residual quantiles calibrated directly on the winning model to construct 90% empirical bounds with verified test coverage (>90%)."),
    ]
    for title, desc in items_fc:
        pt = tf.add_paragraph()
        pt.text = f"\n• {title}"
        pt.font.size = Pt(10)
        pt.font.bold = True
        pt.font.color.rgb = COLOR_WHITE
        pd = tf.add_paragraph()
        pd.text = f"  {desc}"
        pd.font.size = Pt(9)
        pd.font.color.rgb = COLOR_SLATE

    # Right Container: Benchmark Results Table & Metric Callouts
    add_card(s7, Inches(6.8), Inches(2.1), Inches(5.7), Inches(4.9))
    tb_r = s7.shapes.add_textbox(Inches(7.0), Inches(2.2), Inches(5.3), Inches(4.6))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True
    p = tf_r.paragraphs[0]
    p.text = "BENCHMARK PERFORMANCE & FORECAST METRICS"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN

    # Table simulation in text
    pt = tf_r.add_paragraph()
    pt.text = "\nModel Tournament Results (Test Set):"
    pt.font.size = Pt(11)
    pt.font.bold = True
    pt.font.color.rgb = COLOR_WHITE

    pt1 = tf_r.add_paragraph()
    pt1.text = "  1. Persistence Baseline:       WAPE 14.2%  |  RMSE 6.8 kWh"
    pt1.font.size = Pt(9.5)
    pt1.font.color.rgb = COLOR_SLATE

    pt2 = tf_r.add_paragraph()
    pt2.text = "  2. Historical Seasonal:        WAPE 11.4%  |  RMSE 5.2 kWh"
    pt2.font.size = Pt(9.5)
    pt2.font.color.rgb = COLOR_SLATE

    pt3 = tf_r.add_paragraph()
    pt3.text = "  🏆 3. Random Forest (Winner):   WAPE  6.82%  |  RMSE 3.4 kWh"
    pt3.font.size = Pt(10)
    pt3.font.bold = True
    pt3.font.color.rgb = COLOR_EMERALD

    pt4 = tf_r.add_paragraph()
    pt4.text = "\nForecast Horizon & Interval Calibration:"
    pt4.font.size = Pt(11)
    pt4.font.bold = True
    pt4.font.color.rgb = COLOR_WHITE

    items_eval = [
        ("24-Hour Day-Ahead Forecast", "Selected winning model generates future 24-hour demand curve."),
        ("Empirical 90% Bounds Corridor", "Upper & lower prediction bands derived from validation residual quantiles."),
        ("Empirical Test Coverage", "Achieved 91.8% coverage of actual observations within 90% bounds."),
        ("Adaptive Minimum Floor", "Configurable baseline floor derived from historical standby load."),
    ]
    for t, d in items_eval:
        p_sub = tf_r.add_paragraph()
        p_sub.text = f"  • {t}: {d}"
        p_sub.font.size = Pt(9)
        p_sub.font.color.rgb = COLOR_SLATE

    add_speaker_note(s7, "For predictive planning, EcoPilot AI runs an automated 3-model tournament comparing a Persistence model, a Historical Seasonal baseline, and a multi-lag Random Forest. To guarantee scientific integrity, we enforce strict chronological splitting: 70% for training, 15% for validation, and a held-out 15% test set. Lags and rolling features are shifted strictly into the past to prevent temporal data leakage. We evaluate models using Weighted Absolute Percentage Error, or WAPE, rather than MAPE, avoiding division by zero during nocturnal low-load hours. The winning model is selected dynamically and generates 24-hour ahead forecasts with empirically calibrated 90% prediction intervals.")

    # =========================================================================
    # SLIDE 8: AI RECOMMENDATION AGENT
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    apply_slide_background(s8)
    add_header(s8, "Actionable Governance", "Explainable AI Recommendation Agent", "Converting telemetry insights into prioritized conservation measures with auditable lifecycles.")

    # Left Container: Priority Score & Lifecycle
    add_card(s8, Inches(0.8), Inches(2.1), Inches(5.7), Inches(4.9))
    tb = s8.shapes.add_textbox(Inches(1.0), Inches(2.2), Inches(5.3), Inches(4.6))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "MULTI-FACTOR PRIORITY SCORE & LIFECYCLE"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_EMERALD

    items_agent = [
        ("Deterministic Priority Formula", "Score = 0.40·S(energy) + 0.30·S(cost) + 0.15·S(conf) + 0.15·(100 - Effort)\nScores range from 0 to 100, objectively prioritizing high-savings, low-effort interventions."),
        ("Evidence-Anchored Rationales", "Every task explicitly cites anomalous timestamp windows, surplus kWh above baseline, standard deviation breach, and physical assumptions."),
        ("Finite State Machine Lifecycle", "Strictly enforces valid state transitions:\n[Pending] → [Approved] → [Completed]\nWith a reversible [Rejected] path with mandatory operator notes."),
        ("Database Integrity Guard", "Direct jumps from Rejected to Completed are blocked in the persistence layer, guaranteeing managerial sign-off integrity."),
    ]
    for title, desc in items_agent:
        pt = tf.add_paragraph()
        pt.text = f"\n• {title}"
        pt.font.size = Pt(10)
        pt.font.bold = True
        pt.font.color.rgb = COLOR_WHITE
        pd = tf.add_paragraph()
        pd.text = f"  {desc}"
        pd.font.size = Pt(9)
        pd.font.color.rgb = COLOR_SLATE

    # Right Container: Real Campus Recommendation Examples
    add_card(s8, Inches(6.8), Inches(2.1), Inches(5.7), Inches(4.9))
    tb_r = s8.shapes.add_textbox(Inches(7.0), Inches(2.2), Inches(5.3), Inches(4.6))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True
    p = tf_r.paragraphs[0]
    p.text = "EXAMPLE ENERGY CONSERVATION MEASURES (ECMs)"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN

    recs = [
        ("CRITICAL (Score: 88/100)", "Install Automated Contactor Cutoff on Hostel Heating", "• Evidence: 34.2 kWh/h nocturnal baseline vs 18.0 kWh norm (+16.2 kWh/h surplus, 3.8σ)\n• Projected Return: ₹18,450/month • Avoided CO2e: 1,556 kg\n• Action: Schedule electrical contractor for timer panel retrofit"),
        ("HIGH (Score: 76/100)", "Reschedule RO Water Pumping Load to Solar Peak", "• Evidence: 22 kW pump running during peak tariff window (18:00-22:00 @ ₹11.50/kWh)\n• Projected Return: ₹7,800/month tariff arbitrage • Payback: Immediate\n• Action: Adjust timer switch to solar midday window (11:00-14:00)"),
        ("MEDIUM (Score: 65/100)", "Reset Chilled Water Supply Setpoint by +1.0 °C", "• Evidence: Mild ambient weather (24 °C) with overcooling baseline\n• Projected Return: ₹6,200/month • Payback: 0 capital expenditure\n• Action: Adjust central chiller setpoint from 7.0 °C to 8.0 °C"),
    ]
    for tag, title, details in recs:
        pt = tf_r.add_paragraph()
        pt.text = f"\n• [{tag}] {title}"
        pt.font.size = Pt(10)
        pt.font.bold = True
        pt.font.color.rgb = COLOR_WHITE
        pd = tf_r.add_paragraph()
        pd.text = details
        pd.font.size = Pt(8.5)
        pd.font.color.rgb = COLOR_SLATE

    add_speaker_note(s8, "Here is how EcoPilot AI converts data into physical action. When an anomaly or peak demand risk is identified, the AI Agent generates a prioritized Energy Conservation Measure. Each measure is backed by explicit evidence anchors — citing the exact surplus kilowatt-hours, statistical sigma, and underlying assumptions. We rank recommendations using an objective formula weighing 40% energy, 30% financial return, 15% confidence, and 15% implementation ease. Operators interact with these tasks through a governed state machine: actions move from Pending to Approved to Completed, and all transitions are permanently archived in SQLite.")

    # =========================================================================
    # SLIDE 9: SAVINGS SIMULATION & CARBON ACCOUNTING
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    apply_slide_background(s9)
    add_header(s9, "Financial & Carbon Modeling", "Deduplicated Savings & Transparent Carbon Accounting", "Preventing double-counting while grounding carbon claims in official government datasets.")

    # Left Container: Deduplicated Savings
    add_card(s9, Inches(0.8), Inches(2.1), Inches(5.7), Inches(4.9))
    tb = s9.shapes.add_textbox(Inches(1.0), Inches(2.2), Inches(5.3), Inches(4.6))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "MULTI-ACTION OVERLAP DEDUPLICATION"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_EMERALD

    items_dedup = [
        ("The Double-Counting Pitfall", "Naive tools sum percentages across overlapping measures (e.g. 15% HVAC + 10% lighting + 10% controls = 35%). In reality, measures cannibalize the same baseline."),
        ("Compounded Sequential Retention", "Retention Ratio = ∏ (1 - kWh_i / Eligible_Baseline)\nNet Deduplicated kWh = min(∑ kWh_i, Baseline · [1 - Retention Ratio])"),
        ("Physical 85% Ceiling Guard", "EcoPilot AI enforces an absolute physical ceiling of 85% of eligible baseline, preventing mathematically impossible savings claims."),
        ("Time-of-Day (ToD) Load Shifting", "Simulates demand shifting from on-peak hours (₹11.50/kWh) to off-peak solar hours (₹6.50/kWh), modeling pure financial arbitrage without loss of service."),
    ]
    for title, desc in items_dedup:
        pt = tf.add_paragraph()
        pt.text = f"\n• {title}"
        pt.font.size = Pt(10)
        pt.font.bold = True
        pt.font.color.rgb = COLOR_WHITE
        pd = tf.add_paragraph()
        pd.text = f"  {desc}"
        pd.font.size = Pt(9)
        pd.font.color.rgb = COLOR_SLATE

    # Right Container: Transparent Carbon Registry
    add_card(s9, Inches(6.8), Inches(2.1), Inches(5.7), Inches(4.9))
    tb_r = s9.shapes.add_textbox(Inches(7.0), Inches(2.2), Inches(5.3), Inches(4.6))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True
    p = tf_r.paragraphs[0]
    p.text = "OFFICIAL EMISSION FACTOR REGISTRY"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN

    items_carb = [
        ("Transparent GHG Formulation", "Avoided CO2e (kg) = Electricity Saved (kWh) × Grid Emission Factor"),
        ("Official Baseline Emission Factors", "• India CEA Database v19.0: 0.716 kg CO2e/kWh (Default)\n• US EPA eGRID National Average: 0.386 kg CO2e/kWh\n• UK DEFRA / DESNZ Standards: 0.207 kg CO2e/kWh\n• European Environment Agency: 0.251 kg CO2e/kWh"),
        ("Institutional Microgrid Support", "Custom rooftop solar and microgrid factors supported with mandatory citation tracking."),
        ("Zero Greenwashing Safeguards", "• Negative energy savings strictly rejected with ValueError\n• Unverified estimates labeled 'Potential Avoided Emissions'\n• Post-retrofit meter data required for 'Verified Avoided Emissions'"),
    ]
    for title, desc in items_carb:
        pt = tf_r.add_paragraph()
        pt.text = f"\n• {title}"
        pt.font.size = Pt(10)
        pt.font.bold = True
        pt.font.color.rgb = COLOR_WHITE
        pd = tf_r.add_paragraph()
        pd.text = f"  {desc}"
        pd.font.size = Pt(9)
        pd.font.color.rgb = COLOR_SLATE

    add_speaker_note(s9, "A frequent error in campus energy proposals is double-counting. If you install LED fixtures, adjust setpoints, and schedule occupancy sensors, their savings overlap on the same baseline. EcoPilot AI prevents this using a sequential compounding retention formula with an 85% physical ceiling, ensuring that projected savings remain conservative and physically achievable. For carbon accounting, we refuse to use ungrounded estimates. We incorporate official emission factor registries — such as India's Central Electricity Authority baseline of 0.716 kg CO2e per kilowatt-hour, as well as US EPA and UK DEFRA benchmarks. Projections are strictly labeled as Potential Avoided Emissions until verified on site.")

    # =========================================================================
    # SLIDE 10: TRUST, SECURITY & VERIFICATION
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    apply_slide_background(s10)
    add_header(s10, "Enterprise Governance", "Trust, Security & IPMVP Verification Protocol", "Empirical counterfactual audits with weather normalization, RBAC role hierarchy, and protected operations.")

    # Left Container: IPMVP Verification Protocol
    add_card(s10, Inches(0.8), Inches(2.1), Inches(5.7), Inches(4.9))
    tb = s10.shapes.add_textbox(Inches(1.0), Inches(2.2), Inches(5.3), Inches(4.6))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "IPMVP OPTION C VERIFICATION PROTOCOL"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_EMERALD

    items_ver = [
        ("Counterfactual Baseline Model", "Compares actual post-intervention sub-meter data against a baseline counterfactual representing what the building would have consumed without the retrofit."),
        ("Empirical Weather Normalization", "Adjusts baseline consumption for ambient temperature swings using Ordinary Least Squares (OLS) cooling sensitivity (kWh/°C)."),
        ("Realization Rate Metric", "Realization Rate = (Realized Savings / Expected Savings) × 100%\nQuantifies performance gap between modeled savings and real meter audits."),
        ("48-Hour Ingestion Guardrail", "If post-intervention telemetry is under 48 hours, the system strictly outputs 'Awaiting verification data' rather than premature estimates."),
    ]
    for title, desc in items_ver:
        pt = tf.add_paragraph()
        pt.text = f"\n• {title}"
        pt.font.size = Pt(10)
        pt.font.bold = True
        pt.font.color.rgb = COLOR_WHITE
        pd = tf.add_paragraph()
        pd.text = f"  {desc}"
        pd.font.size = Pt(9)
        pd.font.color.rgb = COLOR_SLATE

    # Right Container: 4-Tier RBAC & Protected Reset
    add_card(s10, Inches(6.8), Inches(2.1), Inches(5.7), Inches(4.9))
    tb_r = s10.shapes.add_textbox(Inches(7.0), Inches(2.2), Inches(5.3), Inches(4.6))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True
    p = tf_r.paragraphs[0]
    p.text = "4-TIER RBAC MATRIX & RESET SAFEGUARDS"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN

    items_sec = [
        ("1. VIEWER Role (Weight: 1)", "Read-only access to dashboard KPIs, charts, forecasts, and public verified reports."),
        ("2. ANALYST Role (Weight: 2)", "Viewer rights + execute what-if simulations, upload custom datasets, adjust anomaly sensitivity."),
        ("3. APPROVER Role (Weight: 3)", "Analyst rights + authorize, reject, and mark recommendation measures as completed with operator audit trail."),
        ("4. ADMINISTRATOR Role (Weight: 4)", "Approver rights + manage schema migrations, config overrides, and protected database reset."),
        ("Protected Database Reset", "• Administrator-only execution\n• Production master lockout (ECOPILOT_ALLOW_DB_RESET)\n• Secret confirmation token required (CONFIRM_RESET_DATA)\n• Immutable record logged in admin_audit_log"),
    ]
    for title, desc in items_sec:
        pt = tf_r.add_paragraph()
        pt.text = f"\n• {title}"
        pt.font.size = Pt(10)
        pt.font.bold = True
        pt.font.color.rgb = COLOR_WHITE
        pd = tf_r.add_paragraph()
        pd.text = f"  {desc}"
        pd.font.size = Pt(9)
        pd.font.color.rgb = COLOR_SLATE

    add_speaker_note(s10, "Trust and governance are central to EcoPilot AI. Following the International Performance Measurement and Verification Protocol (IPMVP), our verification engine measures actual realized savings by adjusting pre-intervention baselines for ambient weather variations. If post-retrofit telemetry is under 48 hours, the system refuses to guess and shows 'Awaiting verification data'. On the security side, we enforce a strict 4-tier Role-Based Access Control matrix. Analysts can run simulations, but only Approvers and Administrators can authorize physical measures. Furthermore, destructive database resets are locked behind environment flags, admin privilege checks, secret confirmation keys, and persistent audit logging.")

    # =========================================================================
    # SLIDE 11: DASHBOARD DEMONSTRATION
    # =========================================================================
    s11 = prs.slides.add_slide(blank_layout)
    apply_slide_background(s11)
    add_header(s11, "Live Interface Showcase", "Interactive Streamlit Dashboard Demonstration", "High-contrast, responsive enterprise analytics operating 100% locally on campus telemetry.")

    # 6 UI Mockup Panels Grid (2 rows x 3 columns)
    ui_panels = [
        ("📊 1. Overview KPIs", "Total Consumption: 41,280 kWh\nPotential Savings: ₹32,640 (12.4%)\nAvoided Emissions: 2,752 kg CO2e\nActive Anomaly Alerts: 4", COLOR_EMERALD),
        ("🔍 2. Energy Analysis", "Diurnal Heatmaps & 24h Profiles\nOvernight Baseline: 34.2 kWh/h\nSurplus above norm: +16.2 kWh/h (3.4σ)\nCategorized as Potential Waste", COLOR_AMBER),
        ("🔮 3. Demand Forecasting", "Tournament Winner: Random Forest\nWAPE: 6.82% (Test Split) vs 11.4% Seasonal\nEmpirical 90% Confidence Corridor\n24-Hour Horizon Ahead", COLOR_CYAN),
        ("🤖 4. AI Task Recommendations", "Priority Score: 88/100 (HVAC Cutoff)\nEvidence: Nocturnal surplus +16.2 kWh/h\nAction: [Approve] [Reject] [Complete]\nState Machine in SQLite", COLOR_TEAL),
        ("💡 5. Savings Simulator", "ToD Peak-to-Solar Load Shifting\n22 kW Pump shifted to 11:00-14:00\nPeak ₹11.50 → Off-Peak ₹6.50/kWh\nOverlap Deduplication Cap: 85%", COLOR_BLUE),
        ("📈 6. Verification History", "Intervention: Hostel B Contactor Timer\nRealization Rate: 92.4% Verified\nMeasured Savings: ₹17,040 / month\nWeather-Adjusted Counterfactual", COLOR_EMERALD),
    ]

    col_w = Inches(3.7)
    row_h = Inches(2.3)
    c_lefts = [Inches(0.8), Inches(4.8), Inches(8.8)]
    r_tops = [Inches(2.1), Inches(4.7)]

    for idx, (p_title, p_body, col) in enumerate(ui_panels):
        c_idx = idx % 3
        r_idx = idx // 3
        pos_l = c_lefts[c_idx]
        pos_t = r_tops[r_idx]
        
        add_card(s11, pos_l, pos_t, col_w, row_h, bg_color=COLOR_PANEL, border_color=col)
        tb = s11.shapes.add_textbox(pos_l + Inches(0.15), pos_t + Inches(0.15), col_w - Inches(0.3), row_h - Inches(0.3))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p1 = tf.paragraphs[0]
        p1.text = p_title
        p1.font.size = Pt(11)
        p1.font.bold = True
        p1.font.color.rgb = col

        p2 = tf.add_paragraph()
        p2.text = f"\n{p_body}"
        p2.font.size = Pt(9.5)
        p2.font.color.rgb = COLOR_SLATE

    add_speaker_note(s11, "This slide showcases the actual Streamlit interface of EcoPilot AI. On screen, you see our six key views: the Executive KPI dashboard summarizing facility metrics; the Telemetry view displaying nocturnal waste heatmaps; the Forecasting tournament benchmark with empirical confidence bands; the AI Recommendation cards with interactive approval buttons; the Savings Simulator modeling ToD load shifting; and the Audited Verification history tracking realized real-world savings. Everything runs locally in the browser with sub-second response times, zero paid API latency, and complete user role enforcement.")

    # =========================================================================
    # SLIDE 12: IMPACT & ROADMAP
    # =========================================================================
    s12 = prs.slides.add_slide(blank_layout)
    apply_slide_background(s12)
    add_header(s12, "Impact & Vision", "Measurable Institutional Value & Engineering Roadmap", "Transforming raw telemetry into verifiable financial, operational, and environmental returns.")

    # Left Container: Value Delivered
    add_card(s12, Inches(0.8), Inches(2.1), Inches(5.7), Inches(3.8))
    tb = s12.shapes.add_textbox(Inches(1.0), Inches(2.2), Inches(5.3), Inches(3.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "MEASURABLE INSTITUTIONAL VALUE"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_EMERALD

    values = [
        ("Earlier Waste Detection", "Catches overnight HVAC drift and unmanaged lighting days before utility billing arrives."),
        ("Realistic Financial Returns", "Eliminates double-counting with overlap deduplication and physical baseline ceilings."),
        ("Auditable Carbon Integrity", "Grounded in official Central Electricity Authority grid factors with IPMVP post-audits."),
        ("Zero Recurring Cloud Fees", "100% offline local inference on standard CPU hardware with sub-second execution."),
        ("Operational Governance", "Strict 4-tier Role-Based Access Control and immutable SQLite audit trails."),
    ]
    for title, desc in values:
        pt = tf.add_paragraph()
        pt.text = f"\n• {title}: {desc}"
        pt.font.size = Pt(9.5)
        pt.font.color.rgb = COLOR_SLATE

    # Right Container: 4-Phase Roadmap
    add_card(s12, Inches(6.8), Inches(2.1), Inches(5.7), Inches(3.8))
    tb_r = s12.shapes.add_textbox(Inches(7.0), Inches(2.2), Inches(5.3), Inches(3.5))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True
    p = tf_r.paragraphs[0]
    p.text = "4-PHASE DEVELOPMENT ROADMAP"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN

    phases = [
        ("Phase 1 (Months 1–2): Live Smart Meter Ingestion", "Native Modbus RTU/TCP, BACnet IP, and MQTT direct ingestion for Schneider, Siemens & Elmeasure meters."),
        ("Phase 2 (Months 2–3): Solar PV & BESS Arbitrage", "Integration with rooftop solar inverters and battery energy storage systems for real-time solar self-consumption."),
        ("Phase 3 (Months 3–4): Multi-Tenant Sub-Metering", "Automated department-level and hostel-block sub-billing and cost allocation reporting."),
        ("Phase 4 (Months 4–5): Authorized BMS Actuation", "Authorized webhook execution pushing approved setpoints directly into Tridium Niagara / Honeywell controllers."),
    ]
    for title, desc in phases:
        pt = tf_r.add_paragraph()
        pt.text = f"\n• {title}"
        pt.font.size = Pt(10)
        pt.font.bold = True
        pt.font.color.rgb = COLOR_WHITE
        pd = tf_r.add_paragraph()
        pd.text = f"  {desc}"
        pd.font.size = Pt(9)
        pd.font.color.rgb = COLOR_SLATE

    # Bottom Banner (Closing statement)
    banner = add_card(s12, Inches(0.8), Inches(6.1), Inches(11.7), Inches(0.85), bg_color=COLOR_EMERALD_BG, border_color=COLOR_EMERALD)
    tb_b = s12.shapes.add_textbox(Inches(1.0), Inches(6.2), Inches(11.3), Inches(0.65))
    tf_b = tb_b.text_frame
    tf_b.word_wrap = True
    p_b = tf_b.paragraphs[0]
    p_b.text = "“EcoPilot AI turns energy data into accountable sustainability action.”"
    p_b.alignment = PP_ALIGN.CENTER
    p_b.font.size = Pt(16)
    p_b.font.bold = True
    p_b.font.color.rgb = COLOR_WHITE

    add_speaker_note(s12, "To conclude, EcoPilot AI delivers immediate, measurable value. It catches energy waste days before utility bills arrive, prevents double-counting through overlap deduplication, ensures transparent carbon accounting, and keeps all institutional data secure through local execution and role-based access control. Looking forward, our roadmap includes direct Modbus and BACnet hardware connectors, solar microgrid battery dispatch, and multi-tenant department sub-billing. EcoPilot AI turns energy data into accountable sustainability action. Thank you, and I look forward to your questions.")

    # Save to all target paths
    for path in output_paths:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        prs.save(path)
        print(f"Presentation saved successfully to: {path}")

if __name__ == "__main__":
    out_paths = [
        r"c:\Users\chara\OneDrive\Desktop\EcoPilot-AI\EcoPilot_AI_Presentation.pptx",
        r"C:\Users\chara\.gemini\antigravity\brain\33ec86bb-3790-404b-8d8c-32b1721f0c54\EcoPilot_AI_Presentation.pptx",
    ]
    create_deck(out_paths)
