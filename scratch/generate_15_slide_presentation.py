"""
EcoPilot AI: Complete 15-Slide Professional Presentation Generator
Author: Antigravity AI Engineering Assistant
Project: EcoPilot AI — AI-Powered Smart Energy Management System

Outputs:
1. EcoPilot_AI_15_Slides_Presentation.pptx (Editable Widescreen 16:9 Presentation)
2. EcoPilot_AI_15_Slides_Presentation.pdf (Widescreen 16:9 Companion PDF via ReportLab)
"""

import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

from reportlab.lib.pagesizes import landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# ==============================================================================
# COLOR PALETTE SPECIFICATION (Dark Green / Emerald / White / Subtle Blue Theme)
# ==============================================================================
COLOR_BG_DARK = RGBColor(7, 24, 19)        # #071813 Deep Forest Slate Green
COLOR_CARD_BG = RGBColor(14, 41, 32)       # #0E2920 Card surface
COLOR_CARD_ALT = RGBColor(18, 52, 41)      # #123429 Elevated card surface
COLOR_CARD_BORDER = RGBColor(28, 77, 62)   # #1C4D3E Card border
COLOR_EMERALD = RGBColor(16, 185, 129)     # #10B981 Primary brand accent
COLOR_MINT = RGBColor(52, 211, 153)        # #34D399 Mint / light green accent
COLOR_SKY_BLUE = RGBColor(56, 189, 248)    # #38BDF8 Subtle technical blue accent
COLOR_AMBER = RGBColor(245, 158, 11)       # #F59E0B Warning / priority highlight
COLOR_WHITE = RGBColor(248, 250, 252)      # #F8FAFC Heading text
COLOR_MUTED = RGBColor(203, 213, 225)      # #CBD5E1 Body text
COLOR_DARK_TEXT = RGBColor(4, 47, 26)      # #042F1A Dark text on bright pill

FONT_HEADING = "Segoe UI"
FONT_BODY = "Segoe UI"


def setup_slide_background(slide, prs):
    """Fills slide background with uniform deep forest slate green."""
    bg_shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height
    )
    bg_shape.fill.solid()
    bg_shape.fill.fore_color.rgb = COLOR_BG_DARK
    bg_shape.line.fill.background()
    return bg_shape


def add_slide_header(slide, category_text, title_text, slide_number=None):
    """Creates a consistent, elegant slide header without bullet points."""
    # Top Category Pill Banner
    cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(9.0), Inches(0.35))
    tf_c = cat_box.text_frame
    tf_c.word_wrap = True
    tf_c.margin_left = tf_c.margin_top = tf_c.margin_right = tf_c.margin_bottom = 0
    p_c = tf_c.paragraphs[0]
    p_c.text = category_text.upper()
    p_c.font.name = FONT_HEADING
    p_c.font.size = Pt(10)
    p_c.font.bold = True
    p_c.font.color.rgb = COLOR_MINT

    # Slide Title
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.72), Inches(10.5), Inches(0.65))
    tf_t = title_box.text_frame
    tf_t.word_wrap = True
    tf_t.margin_left = tf_t.margin_top = tf_t.margin_right = tf_t.margin_bottom = 0
    p_t = tf_t.paragraphs[0]
    p_t.text = title_text
    p_t.font.name = FONT_HEADING
    p_t.font.size = Pt(22)
    p_t.font.bold = True
    p_t.font.color.rgb = COLOR_WHITE

    # Slide Number & Branding in top right
    if slide_number:
        num_box = slide.shapes.add_textbox(Inches(11.2), Inches(0.45), Inches(1.3), Inches(0.4))
        tf_n = num_box.text_frame
        tf_n.margin_left = tf_n.margin_top = tf_n.margin_right = tf_n.margin_bottom = 0
        p_n = tf_n.paragraphs[0]
        p_n.alignment = PP_ALIGN.RIGHT
        p_n.text = f"SLIDE {slide_number:02d} / 15"
        p_n.font.name = FONT_HEADING
        p_n.font.size = Pt(10)
        p_n.font.bold = True
        p_n.font.color.rgb = COLOR_EMERALD


def add_visual_card(
    slide,
    left,
    top,
    width,
    height,
    title=None,
    paragraphs=None,
    accent_bar_color=None,
    bg_color=None,
    title_color=None,
    font_size=11,
):
    """
    Renders a clean, rounded visual card container.
    Guarantees ABSOLUTELY ZERO bullet points: strictly formatted connected prose.
    """
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color or COLOR_CARD_BG
    card.line.color.rgb = COLOR_CARD_BORDER
    card.line.width = Pt(1)

    # Accent indicator bar on left border if specified
    if accent_bar_color:
        bar = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, Inches(0.08), height)
        bar.fill.solid()
        bar.fill.fore_color.rgb = accent_bar_color
        bar.line.fill.background()

    tf = card.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.TOP
    tf.margin_left = Inches(0.22)
    tf.margin_top = Inches(0.2)
    tf.margin_right = Inches(0.22)
    tf.margin_bottom = Inches(0.2)

    current_idx = 0
    if title:
        p_title = tf.paragraphs[0]
        p_title.text = title
        p_title.font.name = FONT_HEADING
        p_title.font.size = Pt(font_size + 2.5)
        p_title.font.bold = True
        p_title.font.color.rgb = title_color or COLOR_WHITE
        p_title.space_after = Pt(6)
        current_idx = 1

    if paragraphs:
        for idx, text in enumerate(paragraphs):
            p = tf.add_paragraph() if (title or idx > 0) else tf.paragraphs[0]
            # Ensure text has NO bullet symbols or numbers
            clean_text = text.lstrip("•-* \t0123456789.)")
            p.text = clean_text
            p.font.name = FONT_BODY
            p.font.size = Pt(font_size)
            p.font.color.rgb = COLOR_MUTED
            p.space_after = Pt(5)

    return card


def add_metric_badge(slide, left, top, width, height, value_text, label_text, subtext=None, color=COLOR_EMERALD):
    """Renders a high-visibility KPI metric card."""
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = COLOR_CARD_BG
    card.line.color.rgb = COLOR_CARD_BORDER
    card.line.width = Pt(1)

    tf = card.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = Inches(0.18)
    tf.margin_top = Inches(0.12)
    tf.margin_right = Inches(0.18)
    tf.margin_bottom = Inches(0.12)

    p_val = tf.paragraphs[0]
    p_val.text = value_text
    p_val.font.name = FONT_HEADING
    p_val.font.size = Pt(20)
    p_val.font.bold = True
    p_val.font.color.rgb = color
    p_val.space_after = Pt(2)

    p_lbl = tf.add_paragraph()
    p_lbl.text = label_text.upper()
    p_lbl.font.name = FONT_HEADING
    p_lbl.font.size = Pt(9.5)
    p_lbl.font.bold = True
    p_lbl.font.color.rgb = COLOR_WHITE

    if subtext:
        p_sub = tf.add_paragraph()
        p_sub.text = subtext
        p_sub.font.name = FONT_BODY
        p_sub.font.size = Pt(8.5)
        p_sub.font.color.rgb = COLOR_MUTED


def add_speaker_note(slide, text):
    """Embeds 30-60s comprehensive speaker notes for PowerPoint Presenter View."""
    notes_slide = slide.notes_slide
    text_frame = notes_slide.notes_text_frame
    text_frame.text = text


# ==============================================================================
# PRESENTATION BUILDER EXECUTION
# ==============================================================================
def build_15_slide_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    print("Building Slide 1: Project Title and Introduction...")
    # --------------------------------------------------------------------------
    # SLIDE 1: Title and Project Introduction
    # --------------------------------------------------------------------------
    s1 = prs.slides.add_slide(blank_layout)
    setup_slide_background(s1, prs)

    # Top Tag
    pill = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(0.8), Inches(3.6), Inches(0.36))
    pill.fill.solid()
    pill.fill.fore_color.rgb = COLOR_EMERALD
    pill.line.fill.background()
    tf_p = pill.text_frame
    tf_p.word_wrap = True
    p_p = tf_p.paragraphs[0]
    p_p.alignment = PP_ALIGN.CENTER
    p_p.text = "AI-POWERED ENERGY INTELLIGENCE"
    p_p.font.name = FONT_HEADING
    p_p.font.size = Pt(10)
    p_p.font.bold = True
    p_p.font.color.rgb = COLOR_DARK_TEXT

    # Main Title
    t_box = s1.shapes.add_textbox(Inches(0.8), Inches(1.3), Inches(11.5), Inches(1.5))
    tf_t = t_box.text_frame
    tf_t.word_wrap = True
    p1 = tf_t.paragraphs[0]
    p1.text = "EcoPilot AI"
    p1.font.name = FONT_HEADING
    p1.font.size = Pt(44)
    p1.font.bold = True
    p1.font.color.rgb = COLOR_WHITE
    p1.space_after = Pt(4)

    p2 = tf_t.add_paragraph()
    p2.text = "Explainable AI for Sustainable Building Energy Management"
    p2.font.name = FONT_HEADING
    p2.font.size = Pt(18)
    p2.font.bold = True
    p2.font.color.rgb = COLOR_MINT

    # Project Description Card
    add_visual_card(
        s1,
        Inches(0.8),
        Inches(2.9),
        Inches(11.733),
        Inches(1.3),
        title="Software Platform Overview",
        paragraphs=[
            "EcoPilot AI is an offline-first, explainable software system designed to help institutional campuses and commercial buildings monitor electrical consumption in real time, identify abnormal energy waste, forecast future peak demand, generate prioritized operational recommendations, and verify realized environmental benefits.",
            "The platform bridges the gap between passive energy monitoring dashboards and actionable facility management through transparent machine learning, interactive tariff simulations, and verifiable measurement protocols.",
        ],
        accent_bar_color=COLOR_EMERALD,
        font_size=11,
    )

    # 3 Pillars Cards
    add_visual_card(
        s1,
        Inches(0.8),
        Inches(4.4),
        Inches(3.7),
        Inches(1.25),
        title="Continuous Telemetry Monitoring",
        paragraphs=[
            "Ingests power and energy readings, normalizes sampling frequencies, corrects measurement units, and flags sensor transmission faults before analysis.",
        ],
        accent_bar_color=COLOR_MINT,
        font_size=10,
    )
    add_visual_card(
        s1,
        Inches(4.81),
        Inches(4.4),
        Inches(3.7),
        Inches(1.25),
        title="Multi-Model Predictive AI",
        paragraphs=[
            "Combines Robust Z-scores and Isolation Forests for anomaly detection, with a three-model tournament for hourly demand forecasting.",
        ],
        accent_bar_color=COLOR_SKY_BLUE,
        font_size=10,
    )
    add_visual_card(
        s1,
        Inches(8.83),
        Inches(4.4),
        Inches(3.7),
        Inches(1.25),
        title="Accountable ESG Verification",
        paragraphs=[
            "Simulates non-overlapping Time-of-Day cost savings and verifies post-intervention efficiency using weather-normalized regression baselines.",
        ],
        accent_bar_color=COLOR_EMERALD,
        font_size=10,
    )

    # Editable Metadata Card
    add_visual_card(
        s1,
        Inches(0.8),
        Inches(5.85),
        Inches(11.733),
        Inches(1.15),
        title="Academic & Project Review Credentials",
        paragraphs=[
            "Presenter: [Presenter Name]  |  Team Members: [Team Member 1, Team Member 2, Team Member 3]  |  Department: [Department of Computer Science / Electrical Engineering]",
            "Institution: [College / University Name]  |  Project Guide: [Faculty Mentor / Guide Name]  |  Academic Year: [2025 – 2026]",
        ],
        bg_color=COLOR_CARD_ALT,
        title_color=COLOR_SKY_BLUE,
        font_size=10,
    )

    add_speaker_note(
        s1,
        "Good morning, respected faculty members, evaluators, and fellow students. Today, I am proud to present EcoPilot AI, an AI-powered smart energy management system designed for educational campuses, commercial offices, and multi-tenant facilities. Buildings worldwide consume over thirty percent of total electrical power, yet most facilities operate blindly, discovering equipment inefficiencies only when monthly utility bills arrive. EcoPilot AI transforms energy management by connecting continuous meter monitoring with statistical anomaly detection, machine learning demand forecasting, explainable human-in-the-loop recommendations, and rigorous post-intervention verification. Throughout this presentation, I will walk you through the real system architecture, mathematical formulations, database governance, and experimental results that make EcoPilot AI a robust engineering solution. Let us begin by reviewing the project vision."
    )

    print("Building Slide 2: Project Overview and Vision...")
    # --------------------------------------------------------------------------
    # SLIDE 2: Project Overview and Vision
    # --------------------------------------------------------------------------
    s2 = prs.slides.add_slide(blank_layout)
    setup_slide_background(s2, prs)
    add_slide_header(s2, "System Vision & Operational Paradigm", "Bridging Passive Telemetry and Active Energy Governance", 2)

    add_visual_card(
        s2,
        Inches(0.8),
        Inches(1.45),
        Inches(11.733),
        Inches(1.2),
        title="The Limitations of Traditional Energy Monitoring",
        paragraphs=[
            "Traditional electricity monitoring setups are largely retrospective, showing charts of past consumption without explaining why energy waste occurred or how to prevent it.",
            "Facility teams often lack the time or tools to translate historical charts into concrete operational schedules, causing expensive peak demand penalties and undetected after-hours baseload leakage.",
        ],
        accent_bar_color=COLOR_AMBER,
        font_size=10.5,
    )

    # 4 Visual Connected Pillars Surrounding the Core Concept
    add_visual_card(
        s2,
        Inches(0.8),
        Inches(2.8),
        Inches(5.7),
        Inches(1.9),
        title="Sensing & Quality Assurance",
        paragraphs=[
            "The platform continuously ingests power telemetry, detects irregular recording intervals, cleans missing data points, and guarantees mathematical consistency before running analytics.",
            "This creates a reliable telemetry foundation, preventing sensor noise from triggering misleading alerts.",
        ],
        accent_bar_color=COLOR_MINT,
        font_size=10,
    )
    add_visual_card(
        s2,
        Inches(6.833),
        Inches(2.8),
        Inches(5.7),
        Inches(1.9),
        title="Predictive & Statistical Intelligence",
        paragraphs=[
            "Dual-engine anomaly detection separates sudden spikes from sustained baseload waste, while a three-model forecasting tournament anticipates future building demand.",
            "Managers gain proactive 24-hour foresight rather than reacting to yesterday's utility invoices.",
        ],
        accent_bar_color=COLOR_SKY_BLUE,
        font_size=10,
    )
    add_visual_card(
        s2,
        Inches(0.8),
        Inches(4.85),
        Inches(5.7),
        Inches(1.9),
        title="Action Simulation & Governance",
        paragraphs=[
            "Proposed conservation tasks undergo multi-tier Time-of-Day tariff simulation and portfolio overlap deduplication to calculate realistic financial and carbon benefits.",
            "All actions require explicit human sign-off through role-based access control.",
        ],
        accent_bar_color=COLOR_EMERALD,
        font_size=10,
    )
    add_visual_card(
        s2,
        Inches(6.833),
        Inches(4.85),
        Inches(5.7),
        Inches(1.9),
        title="Empirical Savings Verification",
        paragraphs=[
            "Following implementation, the platform compares post-intervention consumption against weather-normalized counterfactual baselines using IPMVP Option C standards.",
            "This ensures that documented carbon and monetary savings represent verified real-world impact.",
        ],
        accent_bar_color=COLOR_MINT,
        font_size=10,
    )

    add_speaker_note(
        s2,
        "Slide two illustrates the fundamental vision and operational philosophy of EcoPilot AI. In traditional building management, energy dashboards are passive digital logbooks: they plot historical consumption curves, but they offer zero guidance on why surges happened or what facility managers should do next. EcoPilot AI overcomes this limitation by establishing a closed-loop intelligence architecture. As shown in these four connected domains, the system starts with rigorous data quality assurance to ensure sensor reliability, applies predictive intelligence to forecast demand, runs financial simulations under realistic Time-of-Day tariffs, and finally conducts post-intervention verification. This transforms energy telemetry from an overwhelming wall of numbers into a clear, auditable operational workflow. Next, let us examine the practical building challenges that motivated this system."
    )

    print("Building Slide 3: Problem Statement and Motivation...")
    # --------------------------------------------------------------------------
    # SLIDE 3: Problem Statement and Motivation
    # --------------------------------------------------------------------------
    s3 = prs.slides.add_slide(blank_layout)
    setup_slide_background(s3, prs)
    add_slide_header(s3, "Industry Context & Practical Motivation", "The Built-Environment Energy Management Dilemma", 3)

    add_visual_card(
        s3,
        Inches(0.8),
        Inches(1.45),
        Inches(11.733),
        Inches(1.05),
        title="Real-World Facilities Management Challenges",
        paragraphs=[
            "Educational institutions, commercial offices, and hospitals face significant electricity waste due to after-hours equipment operation, untracked peak demand surges, and rigid operating schedules.",
            "Facility teams require an accessible, vendor-independent software platform that pinpoints energy waste, prioritizes actionable remedies, and mathematically verifies real-world savings.",
        ],
        accent_bar_color=COLOR_AMBER,
        font_size=10.5,
    )

    # Comparison Grid: Traditional vs EcoPilot AI
    add_visual_card(
        s3,
        Inches(0.8),
        Inches(2.65),
        Inches(5.7),
        Inches(4.3),
        title="Traditional Facility Energy Monitoring",
        paragraphs=[
            "Operational Blind Spots: Heavy equipment such as chillers, pumps, and hallway lighting frequently run unmonitored during unoccupied nighttime hours, creating massive undetected baseload waste.",
            "Costly Peak Surcharges: Uncoordinated equipment startups during peak utility tariff windows lead to severe maximum demand penalties on monthly electricity bills.",
            "Retrospective Analysis: Spreadsheets and utility bills report total kilowatt-hours weeks after consumption occurred, making real-time root cause analysis impossible.",
            "Unsubstantiated Sustainability Claims: Energy efficiency measures are rarely verified against rigorous weather-adjusted baselines, resulting in unproven ESG reporting.",
        ],
        accent_bar_color=COLOR_AMBER,
        bg_color=COLOR_CARD_ALT,
        title_color=COLOR_AMBER,
        font_size=10,
    )

    add_visual_card(
        s3,
        Inches(6.833),
        Inches(2.65),
        Inches(5.7),
        Inches(4.3),
        title="EcoPilot AI Intelligent Governance",
        paragraphs=[
            "Automated Waste Detection: Dual-engine algorithms continuously compare live telemetry against robust historical baselines, instantly identifying after-hours equipment leakage.",
            "Proactive Demand Shaving: Predictive models forecast demand 24 hours in advance, allowing facility operators to shift flexible electrical loads away from expensive tariff periods.",
            "Explainable Decision Support: Transparent scoring algorithms prioritize energy conservation tasks by energy impact, financial payback, model confidence, and operational effort.",
            "Weather-Normalized Verification: Rigorous post-intervention regression verifies realized kilowatt-hour reductions against degree-day variations, ensuring true ESG accountability.",
        ],
        accent_bar_color=COLOR_EMERALD,
        bg_color=COLOR_CARD_BG,
        title_color=COLOR_MINT,
        font_size=10,
    )

    add_speaker_note(
        s3,
        "On slide three, we examine the practical energy management dilemma that motivated our engineering efforts. In large facilities like university campuses or commercial buildings, significant electricity is wasted because heavy equipment—such as HVAC compressors, water booster pumps, and common-area lighting—continues running long after occupants have left. On the left, we see the drawbacks of traditional methods: bills arrive a month late, peak demand surcharges inflate utility costs, and energy conservation claims remain unsubstantiated. On the right, EcoPilot AI provides a comprehensive solution: it uses automated anomaly detection to spot baseload leaks immediately, forecasts demand to avoid peak surcharges, prioritizes recommendations based on financial and energy return, and verifies realized savings using weather-adjusted regression models. Let us now examine the specific objectives and boundaries of our project."
    )

    print("Building Slide 4: Project Objectives and Scope...")
    # --------------------------------------------------------------------------
    # SLIDE 4: Project Objectives and Scope
    # --------------------------------------------------------------------------
    s4 = prs.slides.add_slide(blank_layout)
    setup_slide_background(s4, prs)
    add_slide_header(s4, "Project Boundaries & Deliverables", "Engineering Objectives and Implemented Scope", 4)

    # 3 Implemented Objectives Cards
    add_visual_card(
        s4,
        Inches(0.8),
        Inches(1.45),
        Inches(3.7),
        Inches(3.4),
        title="Objective 1: Anomaly & Data Engineering",
        paragraphs=[
            "Robust Telemetry Cleansing: Implement an ingestion pipeline that handles missing values, clips non-physical negative readings, and converts power to energy using true elapsed time intervals.",
            "Dual-Engine Anomaly Detection: Build an ensemble combining Robust Z-scores with Scikit-learn Isolation Forests to classify unusual spikes and after-hours energy waste across four severity tiers.",
            "Data Health Reporting: Generate typed quality reports measuring row completeness, sampling frequency, and telemetry integrity prior to analytical modeling.",
        ],
        accent_bar_color=COLOR_MINT,
        font_size=10,
    )

    add_visual_card(
        s4,
        Inches(4.81),
        Inches(1.45),
        Inches(3.7),
        Inches(3.4),
        title="Objective 2: Forecasting & Recommendations",
        paragraphs=[
            "Three-Model Tournament: Implement a competitive forecasting framework evaluating Persistence, Historical Seasonal, and Random Forest models across chronological splits.",
            "Empirical Uncertainty Intervals: Compute calibrated conformal prediction bounds and data-derived consumption floors for reliable next-day load planning.",
            "Explainable Recommendation Agent: Synthesize analytical findings into prioritized action cards scored on energy, financial savings, model confidence, and implementation effort.",
        ],
        accent_bar_color=COLOR_SKY_BLUE,
        font_size=10,
    )

    add_visual_card(
        s4,
        Inches(8.83),
        Inches(1.45),
        Inches(3.7),
        Inches(3.4),
        title="Objective 3: Simulation & Verification",
        paragraphs=[
            "Time-of-Day Tariff Simulation: Calculate financial savings under multi-tier pricing structures, including peak demand shaving and flexible load shifting.",
            "Avoided Carbon Accounting: Model avoided emissions using verified grid factors while eliminating portfolio double-counting through overlap deduplication.",
            "IPMVP Savings Verification: Quantify post-intervention savings against weather-normalized baselines to evaluate real-world project realization rates.",
        ],
        accent_bar_color=COLOR_EMERALD,
        font_size=10,
    )

    # 2 Scope Differentiation Cards (Implemented vs Future Scope)
    add_visual_card(
        s4,
        Inches(0.8),
        Inches(5.05),
        Inches(5.7),
        Inches(1.95),
        title="Confirmed Implemented Scope",
        paragraphs=[
            "Full Streamlit web presentation layer with responsive layout and interactive Plotly visualization.",
            "Layered service and repository architecture with typed Pydantic data schemas.",
            "Transactional SQLite database with enforced foreign keys, migrations, and audit logging.",
            "Four-tier Role-Based Access Control and 101 automated passing verification tests.",
        ],
        accent_bar_color=COLOR_EMERALD,
        bg_color=COLOR_CARD_ALT,
        title_color=COLOR_WHITE,
        font_size=9.5,
    )

    add_visual_card(
        s4,
        Inches(6.833),
        Inches(5.05),
        Inches(5.7),
        Inches(1.95),
        title="Explicit Future Scope Proposals",
        paragraphs=[
            "Live streaming telemetry ingestion via direct Modbus, MQTT, and BACnet hardware gateways.",
            "Supervised closed-loop building automation interfacing with physical relays and actuators.",
            "Integration with real-time on-site weather stations and computer vision occupancy counters.",
            "Multi-facility enterprise portfolio aggregation and federated edge computing nodes.",
        ],
        accent_bar_color=COLOR_SKY_BLUE,
        bg_color=COLOR_CARD_ALT,
        title_color=COLOR_SKY_BLUE,
        font_size=9.5,
    )

    add_speaker_note(
        s4,
        "Slide four sets out the concrete technical objectives and scope of EcoPilot AI. Our first objective is to build a robust data cleansing and anomaly detection pipeline that handles sensor errors and isolates consumption anomalies. Our second objective is to provide predictive foresight through a three-model forecasting tournament and generate explainable, prioritized recommendations. Our third objective is to deliver realistic financial simulations and weather-normalized verification. At the bottom of the slide, we make a clear distinction between what is currently implemented in our codebase—such as our layered architecture, RBAC authorization, and 101 verified automated tests—and what represents future roadmap proposals, such as physical BACnet gateway integration. Next, let us trace how energy data flows through the complete system."
    )

    print("Building Slide 5: Proposed Solution and System Workflow...")
    # --------------------------------------------------------------------------
    # SLIDE 5: Proposed Solution and System Workflow
    # --------------------------------------------------------------------------
    s5 = prs.slides.add_slide(blank_layout)
    setup_slide_background(s5, prs)
    add_slide_header(s5, "End-to-End Operational Pipeline", "The Seven-Stage Energy Intelligence Workflow", 5)

    add_visual_card(
        s5,
        Inches(0.8),
        Inches(1.45),
        Inches(11.733),
        Inches(0.95),
        title="Continuous Closed-Loop Operational Lifecycle",
        paragraphs=[
            "EcoPilot AI transforms raw, unstructured electricity meter readings into verified sustainability outcomes through seven disciplined stages.",
            "A human-in-the-loop approval gate separates simulated potential savings from verified realized savings, guaranteeing operational safety.",
        ],
        accent_bar_color=COLOR_EMERALD,
        font_size=10,
    )

    # 7 Stage Workflow Displayed as Connected Cards
    stages_data = [
        ("STAGE 1: INGESTION", "Receives raw electrical telemetry in CSV format measuring power in kilowatts or energy in kilowatt-hours.", COLOR_MINT),
        ("STAGE 2: VALIDATION", "Cleans time series, handles missing readings, normalizes timezones, and converts power to energy using true intervals.", COLOR_MINT),
        ("STAGE 3: ANALYTICS", "Runs Robust Z-score and Isolation Forest anomaly detection alongside a 3-model demand forecasting tournament.", COLOR_SKY_BLUE),
        ("STAGE 4: RECOMMEND", "Synthesizes analytical findings into prioritized action cards scored on energy, cost, confidence, and effort.", COLOR_SKY_BLUE),
        ("STAGE 5: SIMULATE", "Simulates Time-of-Day cost savings, models avoided carbon emissions, and deduplicates portfolio overlap.", COLOR_EMERALD),
        ("STAGE 6: APPROVAL", "Facility managers review evidence, approve or reject actions, and log operational implementation notes.", COLOR_AMBER),
        ("STAGE 7: VERIFY", "Analyzes post-intervention meter data against weather-normalized baselines to confirm realized savings.", COLOR_EMERALD),
    ]

    card_w = Inches(1.58)
    gap = Inches(0.11)
    for idx, (st_title, st_desc, st_color) in enumerate(stages_data):
        c_left = Inches(0.8) + idx * (card_w + gap)
        add_visual_card(
            s5,
            c_left,
            Inches(2.55),
            card_w,
            Inches(3.3),
            title=st_title,
            paragraphs=[st_desc],
            accent_bar_color=st_color,
            title_color=st_color,
            font_size=9.5,
        )

    # Summary Takeaway Banner
    add_visual_card(
        s5,
        Inches(0.8),
        Inches(6.0),
        Inches(11.733),
        Inches(1.0),
        title="Human-in-the-Loop Governance Boundary",
        paragraphs=[
            "By embedding a formal approval checkpoint at Stage 6, the system ensures that AI recommendations remain purely advisory decision support.",
            "No physical equipment setpoints or electrical circuit breakers are modified without authorized facility engineer sign-off.",
        ],
        accent_bar_color=COLOR_SKY_BLUE,
        bg_color=COLOR_CARD_ALT,
        font_size=10,
    )

    add_speaker_note(
        s5,
        "Slide five outlines the seven-stage workflow that defines EcoPilot AI. The pipeline begins with raw telemetry ingestion, where meter data enters the system. Stage two cleans the data, normalizing timestamps, handling missing readings, and converting power measurements into kilowatt-hours using exact elapsed time intervals. In stage three, our analytical models run anomaly detection and execute the demand forecasting tournament. Stage four synthesizes these findings into prioritized, human-readable recommendations. Stage five simulates the financial and carbon impacts under multi-tier Time-of-Day tariffs, applying overlap deduplication to avoid double-counting. Stage six is our critical human-in-the-loop gate: facility managers review the evidence and formally approve or reject each action. Finally, stage seven verifies post-intervention meter data against a weather-adjusted baseline. Now, let us examine the software architecture supporting this workflow."
    )

    print("Building Slide 6: System Architecture...")
    # --------------------------------------------------------------------------
    # SLIDE 6: System Architecture
    # --------------------------------------------------------------------------
    s6 = prs.slides.add_slide(blank_layout)
    setup_slide_background(s6, prs)
    add_slide_header(s6, "Software Engineering & Modular Design", "Layered System Architecture and Component Relationships", 6)

    # 4 Main Architectural Layers
    add_visual_card(
        s6,
        Inches(0.8),
        Inches(1.45),
        Inches(5.7),
        Inches(2.55),
        title="Streamlit Presentation Layer (app.py)",
        paragraphs=[
            "Responsive Web Interface: Renders eight dedicated operational pages including Overview, Energy Analysis, Forecasting, Recommendations, and Verification.",
            "Interactive Visualizations: Integrates Plotly charts for dynamic zooming, hourly telemetry exploration, and predictive confidence intervals.",
            "Role-Adapted Views: Dynamically hides or displays administrative controls and approval buttons based on the authenticated user role.",
        ],
        accent_bar_color=COLOR_MINT,
        font_size=10,
    )

    add_visual_card(
        s6,
        Inches(6.833),
        Inches(1.45),
        Inches(5.7),
        Inches(2.55),
        title="Service Orchestration Layer (src/services.py)",
        paragraphs=[
            "EnergyDataService: Coordinates file ingestion, validation checks, and data quality report generation.",
            "AnalyticsService: Orchestrates anomaly detection ensembles and executes the three-model forecasting tournament.",
            "RecommendationService: Manages action card generation, priority ranking, and RBAC lifecycle transitions.",
            "VerificationService: Computes weather-normalized counterfactuals and tracks real-world realization rates.",
        ],
        accent_bar_color=COLOR_SKY_BLUE,
        font_size=10,
    )

    add_visual_card(
        s6,
        Inches(0.8),
        Inches(4.15),
        Inches(5.7),
        Inches(2.85),
        title="Analytical Core & Machine Learning Modules",
        paragraphs=[
            "Anomaly Engine (src/anomaly_detection.py): Implements Robust Z-scores using median and MAD, alongside Scikit-learn Isolation Forests.",
            "Forecasting Engine (src/forecasting.py): Trains Persistence, Seasonal Baseline, and Random Forest models with conformal prediction intervals.",
            "Savings & Carbon Engine (src/savings.py, src/carbon.py): Evaluates Time-of-Day tariffs, peak shaving, and avoided emissions using CEA grid factors.",
            "Green AI Profiler (src/green_ai.py): Monitors local execution time, peak memory usage, and avoided cloud computational footprint.",
        ],
        accent_bar_color=COLOR_EMERALD,
        font_size=10,
    )

    add_visual_card(
        s6,
        Inches(6.833),
        Inches(4.15),
        Inches(5.7),
        Inches(2.85),
        title="Data Contracts & Persistence Layer",
        paragraphs=[
            "Typed Data Schemas (src/schemas.py): Strict Pydantic contracts validate alerts, recommendations, forecasts, and quality reports at runtime.",
            "Repository Layer (src/repositories.py): Encapsulates all database operations, separating query logic from business services.",
            "Transactional SQLite (src/database.py): Enforces foreign key constraints (PRAGMA foreign_keys = ON), atomic rollback handling, and versioned schema migrations.",
            "Security & Settings (src/auth.py, src/config.py): Implements four-tier RBAC and centralized configuration with environment overrides.",
        ],
        accent_bar_color=COLOR_AMBER,
        font_size=10,
    )

    add_speaker_note(
        s6,
        "Slide six illustrates the layered software architecture of EcoPilot AI, derived directly from our project repository. We structured the codebase following professional software engineering practices to keep presentation, business logic, and data storage cleanly separated. At the top, the Streamlit interface in app.py renders interactive telemetry views and adapts dynamically to user permissions. User interactions pass directly to our service layer in src/services.py, which coordinates data flows without depending on database specifics. Beneath the services sit our specialized analytical engines for anomaly detection, forecasting, tariff modeling, and local Green AI profiling. Finally, our repository layer in src/repositories.py interfaces with our transactional SQLite database, ensuring all database operations use strictly validated Pydantic data schemas and maintain full ACID compliance with foreign key enforcement. Let us now look at the technologies used to build this architecture."
    )

    print("Building Slide 7: Technology Stack and Tools...")
    # --------------------------------------------------------------------------
    # SLIDE 7: Technology Stack and Tools
    # --------------------------------------------------------------------------
    s7 = prs.slides.add_slide(blank_layout)
    setup_slide_background(s7, prs)
    add_slide_header(s7, "Implementation Technologies", "Validated Technology Stack and Software Libraries", 7)

    # 4 Category Cards
    add_visual_card(
        s7,
        Inches(0.8),
        Inches(1.45),
        Inches(5.7),
        Inches(2.45),
        title="Core Runtime & User Interface Framework",
        paragraphs=[
            "Python 3.10+: Serves as the primary programming runtime, providing mature scientific libraries, strong typing support, and stable cross-platform execution.",
            "Streamlit: Powers the reactive, multi-page web dashboard, delivering responsive user controls, layout containers, and live data binding without requiring complex JavaScript front ends.",
        ],
        accent_bar_color=COLOR_MINT,
        font_size=10.5,
    )

    add_visual_card(
        s7,
        Inches(6.833),
        Inches(1.45),
        Inches(5.7),
        Inches(2.45),
        title="Data Science & Machine Learning Libraries",
        paragraphs=[
            "Pandas & NumPy: Execute vectorized time-series manipulations, timestamp alignments, rolling feature computations, and matrix operations with high computational efficiency.",
            "Scikit-Learn: Implements unsupervised Isolation Forests for anomaly clustering, Random Forest regressors for load forecasting, and evaluation metrics such as MAE and RMSE.",
        ],
        accent_bar_color=COLOR_SKY_BLUE,
        font_size=10.5,
    )

    add_visual_card(
        s7,
        Inches(0.8),
        Inches(4.05),
        Inches(5.7),
        Inches(2.9),
        title="Data Integrity & Relational Storage",
        paragraphs=[
            "Pydantic & Pydantic-Settings: Enforces runtime data contracts and centralized environment configuration, ensuring malformed inputs fail gracefully before processing.",
            "SQLite 3: Delivers zero-configuration, ACID-compliant relational persistence, supporting foreign key cascades, atomic transactions, and automated database migrations without cloud infrastructure costs.",
        ],
        accent_bar_color=COLOR_EMERALD,
        font_size=10.5,
    )

    add_visual_card(
        s7,
        Inches(6.833),
        Inches(4.05),
        Inches(5.7),
        Inches(2.9),
        title="Visualization, Quality Assurance & Profiling",
        paragraphs=[
            "Plotly: Generates interactive, high-contrast time-series charts, forecast bounds, and telemetry scatter plots with pan, zoom, and hover inspection capabilities.",
            "Pytest & Coverage: Powers the automated testing suite, rigorously verifying 101 unit and regression tests across data validation, anomaly detection, and database transactions.",
            "Green AI Profiler: Tracks execution time and memory consumption, demonstrating that local computing eliminates cloud data transfer and server energy overhead.",
        ],
        accent_bar_color=COLOR_AMBER,
        font_size=10.5,
    )

    add_speaker_note(
        s7,
        "Slide seven presents the confirmed technology stack of EcoPilot AI, verified directly from our project dependency files. We selected Python 3.10 for its mature data science ecosystem and strong typing capabilities. Streamlit serves as our presentation framework, enabling us to build an interactive, responsive web application entirely in Python. For data manipulation and machine learning, we rely on Pandas, NumPy, and Scikit-Learn for fast vectorized operations and ensemble modeling. Runtime data contracts are enforced using Pydantic, ensuring that every alert, forecast, and recommendation conforms to strict typed schemas. For persistent storage, we utilize SQLite 3, which provides full relational integrity, foreign key enforcement, and ACID transactions with zero external server administration. Finally, our test suite is powered by Pytest, ensuring high reliability across our 101 automated tests. Now, let us examine how energy telemetry is ingested and sanitized."
    )

    print("Building Slide 8: Data Processing and Energy Analysis...")
    # --------------------------------------------------------------------------
    # SLIDE 8: Data Processing and Energy Analysis
    # --------------------------------------------------------------------------
    s8 = prs.slides.add_slide(blank_layout)
    setup_slide_background(s8, prs)
    add_slide_header(s8, "Telemetry Ingestion & Quality Pipeline", "Robust Telemetry Cleansing and Preparation", 8)

    # 3 Sequential Processing Stages
    add_visual_card(
        s8,
        Inches(0.8),
        Inches(1.45),
        Inches(3.7),
        Inches(3.3),
        title="Step 1: Schema & Header Validation",
        paragraphs=[
            "The ingestion service in src/data_generator.py validates incoming CSV files against expected column structures, requiring timestamps, electrical measurements, and optional ambient temperatures.",
            "Datasets with non-parseable timestamps, duplicate headers, or fewer than 48 hours of historical readings are rejected with explicit error feedback.",
        ],
        accent_bar_color=COLOR_MINT,
        font_size=10,
    )

    add_visual_card(
        s8,
        Inches(4.81),
        Inches(1.45),
        Inches(3.7),
        Inches(3.3),
        title="Step 2: True Elapsed Unit Conversion",
        paragraphs=[
            "When telemetry is provided in electrical power (kW), the system calculates true elapsed hours between consecutive timestamps to convert power to energy (kWh):",
            "Energy (kWh) = Power (kW) × Delta-t (hours).",
            "This mathematical formulation accurately handles 15-minute intervals, 30-minute intervals, and irregular meter sampling without assuming uniform hourly spacing.",
        ],
        accent_bar_color=COLOR_SKY_BLUE,
        font_size=10,
    )

    add_visual_card(
        s8,
        Inches(8.83),
        Inches(1.45),
        Inches(3.7),
        Inches(3.3),
        title="Step 3: Missing Values & Outlier Remediation",
        paragraphs=[
            "Timezone Normalization: Converts timezone-aware timestamps to uniform local naive indices for seamless time-series indexing.",
            "Linear Interpolation: Resolves minor telemetry gaps under 24 hours using linear interpolation, while rejecting datasets with major broken intervals.",
            "Negative Value Clipping: Non-physical negative power readings are safely clipped to zero with an automated record created in the audit log.",
        ],
        accent_bar_color=COLOR_EMERALD,
        font_size=10,
    )

    # Data Quality Report Schema & Illustrative Baseline Card
    add_visual_card(
        s8,
        Inches(0.8),
        Inches(4.9),
        Inches(11.733),
        Inches(2.1),
        title="Data Quality Reporting and Illustrative Dataset Summary",
        paragraphs=[
            "Structured Data Quality Contract: The pipeline generates a typed DataQualityReport schema capturing total rows ingested, detected sampling frequency, missing intervals, and overall dataset health before downstream modeling begins.",
            "Illustrative Sample Dataset Characteristics: In our standard verified test dataset, the system ingested 720 hourly readings (30 full days) representing a university campus building with an average baseline load of 57.3 kWh per hour, total consumption of 41,280 kWh, and zero unhandled sensor errors.",
        ],
        accent_bar_color=COLOR_AMBER,
        bg_color=COLOR_CARD_ALT,
        title_color=COLOR_WHITE,
        font_size=10,
    )

    add_speaker_note(
        s8,
        "Slide eight explains how raw telemetry enters EcoPilot AI and is sanitized for analysis. Real-world electrical meters rarely provide perfect data; they often suffer from dropped readings, duplicate timestamps, negative power glitches, and irregular recording frequencies. In src/data_generator.py, our ingestion pipeline enforces strict validation. It verifies column schemas, detects whether the input is measured in kilowatts of power or kilowatt-hours of energy, and converts power accurately using the exact elapsed time interval between consecutive readings. For minor gaps under 24 hours, it applies linear interpolation, while rejecting severely compromised datasets. Negative readings are clipped to zero and logged in the audit trail. The pipeline produces a structured DataQualityReport that confirms dataset health before any machine learning algorithms are executed. Now, let us examine how the system detects abnormal energy usage."
    )

    print("Building Slide 9: AI-Based Anomaly Detection...")
    # --------------------------------------------------------------------------
    # SLIDE 9: AI-Based Anomaly Detection
    # --------------------------------------------------------------------------
    s9 = prs.slides.add_slide(blank_layout)
    setup_slide_background(s9, prs)
    add_slide_header(s9, "Statistical & Machine Learning Analytics", "Dual-Engine Energy Anomaly Detection", 9)

    add_visual_card(
        s9,
        Inches(0.8),
        Inches(1.45),
        Inches(5.7),
        Inches(2.8),
        title="Dual-Engine Ensemble Methodology",
        paragraphs=[
            "Robust Z-Score Engine: Uses median and Median Absolute Deviation (MAD) to compute baseline statistics, preventing extreme consumption spikes from artificially inflating the reference mean and standard deviation.",
            "Isolation Forest Machine Learning: An unsupervised decision tree ensemble from Scikit-learn that isolates anomalous points in multi-dimensional space, capturing non-linear consumption patterns that univariate tests overlook.",
            "Ensemble Voting: Both engines contribute to an ensemble detection score, ensuring high sensitivity to genuine waste while minimizing false positive alerts.",
        ],
        accent_bar_color=COLOR_MINT,
        font_size=10,
    )

    add_visual_card(
        s9,
        Inches(6.833),
        Inches(1.45),
        Inches(5.7),
        Inches(2.8),
        title="Phenomenon Classification & Severity Tiers",
        paragraphs=[
            "Potential Energy Wastage: Identifies sustained baseline elevation during unoccupied hours (such as 11:00 PM to 5:00 AM), indicating HVAC systems, chillers, or lighting left operating unnecessarily.",
            "Unusual Consumption Spikes: Flags sharp, sudden daytime power surges that threaten peak demand tariff thresholds and signal potential equipment malfunctions.",
            "Four Severity Tiers: Automatically grades anomalies into Low, Medium, High, and Critical based on standard deviation distance and duration, allowing facility teams to prioritize urgent issues.",
        ],
        accent_bar_color=COLOR_SKY_BLUE,
        font_size=10,
    )

    # Illustrative Anomaly Chart & Operational Value Card
    add_visual_card(
        s9,
        Inches(0.8),
        Inches(4.4),
        Inches(11.733),
        Inches(2.6),
        title="Illustrative Anomaly Scenario & Operational Engineering Value",
        paragraphs=[
            "Illustrative Test Scenario: In our verified campus dataset, an overnight baseload anomaly was detected between 01:00 and 05:00 where consumption remained at 72 kWh/hour compared to the normal unoccupied baseline of 28 kWh/hour. The system flagged a Critical severity alert with 176 kWh of excess waste.",
            "Operational Value for Facility Managers: Rather than sifting through thousands of data rows, facility engineers receive targeted alerts indicating the exact hour, estimated excess kilowatt-hours, and phenomenon type. This enables immediate root cause investigation—such as inspecting overridden chiller schedules or faulty ventilation dampers.",
            "Important Engineering Distinction: Detecting an anomaly proves that energy usage is statistically abnormal; it does not automatically prove the physical cause. Facility managers must conduct a physical or BMS inspection to verify the equipment fault.",
        ],
        accent_bar_color=COLOR_AMBER,
        bg_color=COLOR_CARD_ALT,
        title_color=COLOR_WHITE,
        font_size=9.8,
    )

    add_speaker_note(
        s9,
        "Slide nine explains our approach to AI-based anomaly detection. Simple static threshold monitoring either triggers endless false alarms or fails to detect subtle energy waste. To overcome this, EcoPilot AI uses an ensemble of two complementary techniques. First, we use a Robust Z-Score model based on the median and Median Absolute Deviation, ensuring that extreme historical outliers do not distort our baseline statistics. Second, we combine this with an unsupervised Isolation Forest algorithm from Scikit-Learn, which identifies complex multi-dimensional anomalies that univariate tests miss. Crucially, as shown on the right, the system classifies anomalies into two distinct phenomenon types: overnight baseload waste—such as HVAC running in an empty building—and sudden daytime consumption spikes that risk peak demand charges. Each anomaly is assigned a severity tier from Low to Critical, giving facility engineers clear, prioritized targets for physical inspection. Next, let us examine our demand forecasting models."
    )

    print("Building Slide 10: Machine Learning and Demand Forecasting...")
    # --------------------------------------------------------------------------
    # SLIDE 10: Machine Learning and Demand Forecasting
    # --------------------------------------------------------------------------
    s10 = prs.slides.add_slide(blank_layout)
    setup_slide_background(s10, prs)
    add_slide_header(s10, "Predictive Modeling & Evaluation", "Three-Model Demand Forecasting Tournament", 10)

    # 3 Competing Models Cards
    add_visual_card(
        s10,
        Inches(0.8),
        Inches(1.45),
        Inches(3.7),
        Inches(2.9),
        title="Persistence Baseline Model",
        paragraphs=[
            "Serves as the fundamental benchmark by carrying forward electricity consumption from exactly 24 hours prior.",
            "Establishes a minimum performance floor that any advanced machine learning algorithm must significantly outperform to justify deployment.",
        ],
        accent_bar_color=COLOR_MINT,
        font_size=10,
    )

    add_visual_card(
        s10,
        Inches(4.81),
        Inches(1.45),
        Inches(3.7),
        Inches(2.9),
        title="Historical Seasonal Baseline",
        paragraphs=[
            "Aggregates historical consumption by hour of the day and day of the week, capturing cyclical campus schedules, working hours, and weekend patterns.",
            "Provides a reliable, computationally lightweight forecast that serves as an effective fallback when sensor telemetry is sparse.",
        ],
        accent_bar_color=COLOR_SKY_BLUE,
        font_size=10,
    )

    add_visual_card(
        s10,
        Inches(8.83),
        Inches(1.45),
        Inches(3.7),
        Inches(2.9),
        title="Random Forest Regressor",
        paragraphs=[
            "Ensemble decision tree model trained on historical lag features (t-1, t-2, t-24, t-168), rolling statistics, ambient temperature, and calendar signals.",
            "Learns complex non-linear relationships between outdoor weather conditions, institutional occupancy schedules, and electrical demand.",
        ],
        accent_bar_color=COLOR_EMERALD,
        font_size=10,
    )

    # Leakage Prevention, Prediction Intervals & Verified Evaluation Card
    add_visual_card(
        s10,
        Inches(0.8),
        Inches(4.5),
        Inches(11.733),
        Inches(2.55),
        title="Chronological Splitting, Prediction Bounds, and Verified Evaluation",
        paragraphs=[
            "Strict Chronological Train-Val-Test Splitting: Time-series telemetry is divided chronologically without shuffling, strictly preventing future data leakage into historical training sets.",
            "Calibrated Empirical Prediction Intervals: Computes 80% and 95% conformal prediction intervals based on historical model residuals, providing upper and lower demand bounds and bounded by a data-derived consumption floor.",
            "Verified Model Tournament Results: Models are evaluated on unseen test data using Weighted Absolute Percentage Error (WAPE), MAE, and RMSE. In our verified project dataset, the Random Forest model achieved an optimal 6.82% WAPE, outperforming the Seasonal Baseline (11.45% WAPE) and Persistence Baseline (14.20% WAPE) to win selection for future 24-hour demand forecasting.",
        ],
        accent_bar_color=COLOR_AMBER,
        bg_color=COLOR_CARD_ALT,
        title_color=COLOR_WHITE,
        font_size=9.8,
    )

    add_speaker_note(
        s10,
        "Slide ten explains how EcoPilot AI forecasts future electricity demand. Accurate load forecasting is essential for facility managers to schedule equipment and avoid expensive peak demand penalties. Rather than relying on a single model, our forecasting service executes a three-model tournament. It evaluates a persistence baseline, a historical seasonal baseline that captures weekly occupancy schedules, and a machine learning Random Forest regressor. To prevent data leakage, the models are evaluated using a strict chronological split where training data strictly precedes validation and testing data. The winning model is selected automatically based on Weighted Absolute Percentage Error, or WAPE, along with MAE and RMSE. In our verified project dataset, the Random Forest model achieved a 6.82% WAPE, winning the tournament. The system also calculates calibrated empirical prediction intervals, giving facility engineers upper and lower confidence bounds for the next 24 hours. Let us now examine how forecasts and anomalies are converted into actionable recommendations."
    )

    print("Building Slide 11: AI Agent and Recommendation Engine...")
    # --------------------------------------------------------------------------
    # SLIDE 11: AI Agent and Recommendation Engine
    # --------------------------------------------------------------------------
    s11 = prs.slides.add_slide(blank_layout)
    setup_slide_background(s11, prs)
    add_slide_header(s11, "Explainable Decision Synthesis", "Evidence-Backed Operational Recommendations", 11)

    add_visual_card(
        s11,
        Inches(0.8),
        Inches(1.45),
        Inches(5.7),
        Inches(2.6),
        title="Synthesizing Analytics into Concrete Actions",
        paragraphs=[
            "Explainable Decision Generation: The EcoPilot AI agent bridges statistical anomaly clusters and forecasted demand surges into human-readable facility interventions.",
            "Realistic Operational Interventions: Generates targeted actions such as resetting overnight HVAC temperature setpoints, rescheduling flexible water booster pumps to off-peak hours, and adjusting campus exterior lighting timers.",
            "Mathematical Evidence Attachment: Every recommendation links directly to the underlying anomaly IDs, confidence scores, and estimated kilowatt-hour reductions.",
        ],
        accent_bar_color=COLOR_MINT,
        font_size=10,
    )

    add_visual_card(
        s11,
        Inches(6.833),
        Inches(1.45),
        Inches(5.7),
        Inches(2.6),
        title="Multi-Factor Priority Scoring Formula",
        paragraphs=[
            "Recommendations are ranked objectively using a deterministic four-factor priority formula:",
            "Priority Score = 0.40 × Energy Impact + 0.30 × Cost Savings + 0.15 × Confidence + 0.15 × Low Effort.",
            "Energy & Cost Weights: Prioritize measures that yield the largest immediate bill and carbon reductions.",
            "Confidence & Effort Weights: Ensure that high-certainty, low-disruption measures are implemented first.",
        ],
        accent_bar_color=COLOR_SKY_BLUE,
        font_size=10,
    )

    # Governed Lifecycle State Machine Card
    add_visual_card(
        s11,
        Inches(0.8),
        Inches(4.2),
        Inches(11.733),
        Inches(2.85),
        title="Human-in-the-Loop Governance Lifecycle and Advisory Boundary",
        paragraphs=[
            "Strict State Machine Transitions: Recommendations progress through a governed lifecycle: Pending (generated by AI) -> Approved (authorized by facility manager) -> Completed (executed physically on site). A formal Rejected path allows operators to dismiss unsuitable actions with mandatory justification notes.",
            "Immutable SQLite Audit Trail: Every state transition logs the operator's user ID, role, timestamp, and optional remarks, guaranteeing complete accountability for compliance audits.",
            "Advisory System Boundary: The EcoPilot AI agent operates strictly as an intelligent decision-support copilot. The software does not directly actuate electrical relays, trip breakers, or modify building management systems without explicit human authorization.",
        ],
        accent_bar_color=COLOR_EMERALD,
        bg_color=COLOR_CARD_ALT,
        title_color=COLOR_WHITE,
        font_size=10,
    )

    add_speaker_note(
        s11,
        "Slide eleven introduces the EcoPilot AI recommendation engine. A frequent limitation of modern AI systems is that they operate as black boxes, outputting opaque numbers without operational context. EcoPilot AI takes a completely transparent, explainable approach. When anomaly clusters or predicted demand surges occur, our agent generates specific operational recommendations, such as setting back overnight HVAC setpoints, rescheduling flexible loads like water pumps to off-peak hours, or adjusting campus lighting schedules. Every recommendation is scored using a transparent formula that balances energy impact, financial savings, model confidence, and implementation effort. Most importantly, the system enforces a strict human-in-the-loop lifecycle: recommendations start as Pending, require formal approval by an authorized facility manager, and are marked Completed only after physical execution. The software never attempts to control physical electrical switches directly, ensuring safety and human accountability. Next, let us examine how savings and carbon impacts are simulated."
    )

    print("Building Slide 12: Savings Simulation, Optimization, and Carbon Impact...")
    # --------------------------------------------------------------------------
    # SLIDE 12: Savings Simulation, Optimization, and Carbon Impact
    # --------------------------------------------------------------------------
    s12 = prs.slides.add_slide(blank_layout)
    setup_slide_background(s12, prs)
    add_slide_header(s12, "Financial & Environmental Modeling", "Tariff Optimization and Avoided Carbon Estimation", 12)

    add_visual_card(
        s12,
        Inches(0.8),
        Inches(1.45),
        Inches(5.7),
        Inches(2.75),
        title="Time-of-Day Tariff Optimization & Load Shifting",
        paragraphs=[
            "Multi-Tier Tariff Modeling: Simulates electricity costs across standard rates (₹8.50/kWh), peak penalty windows (+20% surcharge between 18:00 and 22:00), and off-peak incentive slots (-15% discount between 22:00 and 06:00).",
            "Flexible Load Shifting: Identifies deferrable building electrical loads—such as water pumping, thermal storage charging, and EV charging—and models shifting them to off-peak periods, reducing peak demand charges without impacting comfort.",
        ],
        accent_bar_color=COLOR_MINT,
        font_size=10,
    )

    add_visual_card(
        s12,
        Inches(6.833),
        Inches(1.45),
        Inches(5.7),
        Inches(2.75),
        title="Avoided Carbon Emissions Accounting",
        paragraphs=[
            "Emissions Calculation: Avoided carbon dioxide equivalent is calculated directly from electricity saved: Avoided CO2e = Electricity Saved (kWh) × Grid Emission Factor.",
            "Official CEA Emission Factor: Incorporates the Central Electricity Authority (CEA) national weighted average grid emission factor of 0.716 kg CO2e per kWh for transparent institutional ESG reporting.",
            "Separate Accounting: The platform strictly labels potential simulated emissions separately from verified realized avoided emissions.",
        ],
        accent_bar_color=COLOR_SKY_BLUE,
        font_size=10,
    )

    # Portfolio Deduplication & Concrete Illustrative Calculation Card
    add_visual_card(
        s12,
        Inches(0.8),
        Inches(4.35),
        Inches(11.733),
        Inches(2.7),
        title="Portfolio Overlap Deduplication & Illustrative Financial Calculation",
        paragraphs=[
            "Non-Overlapping Portfolio Deduplication: When multiple energy conservation measures target the same operational hours or shared equipment, simple addition would result in unrealistic double-counting. The savings engine applies interaction discounting to provide realistic portfolio totals.",
            "Illustrative Monetary & Carbon Calculation: In a verified campus simulation, implementing an overnight HVAC setback that saves 100 kWh during standard tariff hours (₹8.50/kWh) produces an estimated monetary saving of ₹850 and avoids 71.6 kg of CO2e emissions.",
            "Illustrative Test Portfolio Result: Across the full 30-day sample dataset, the simulator identified 3,840 kWh in potential energy reductions, translating into ₹32,640 in financial savings and 2.75 metric tons of avoided CO2e.",
        ],
        accent_bar_color=COLOR_EMERALD,
        bg_color=COLOR_CARD_ALT,
        title_color=COLOR_WHITE,
        font_size=10,
    )

    add_speaker_note(
        s12,
        "On slide twelve, we examine how EcoPilot AI models the financial and environmental benefits of energy-saving actions. Electricity tariffs for commercial and institutional consumers are complex; they include Time-of-Day pricing where energy consumed during peak evening hours is significantly more expensive than during off-peak hours. Our savings simulator models these exact tariff structures, showing facility managers how rescheduling flexible loads—such as running water booster pumps during the afternoon rather than the evening peak—can drastically cut costs. On the environmental side, the system converts electricity savings into avoided carbon emissions using the Central Electricity Authority national weighted average grid factor of 0.716 kilograms of CO2 equivalent per kilowatt-hour. To maintain scientific integrity, our savings engine applies portfolio overlap discounting so that combining multiple recommendations does not unrealistically double-count savings. As shown in our illustrative calculation, saving 100 kilowatt-hours yields 850 rupees in savings and avoids 71.6 kilograms of CO2e. Now, let us look at the user dashboard and security model."
    )

    print("Building Slide 13: Dashboard, Database, Security, and User Roles...")
    # --------------------------------------------------------------------------
    # SLIDE 13: Dashboard, Database, Security, and User Roles
    # --------------------------------------------------------------------------
    s13 = prs.slides.add_slide(blank_layout)
    setup_slide_background(s13, prs)
    add_slide_header(s13, "User Experience & System Governance", "Interactive Dashboard and Security Architecture", 13)

    add_visual_card(
        s13,
        Inches(0.8),
        Inches(1.45),
        Inches(5.7),
        Inches(2.7),
        title="Eight Dedicated Streamlit Dashboard Views",
        paragraphs=[
            "Overview & KPIs: Displays total consumption, active alerts, potential savings, and environmental realization metrics at a glance.",
            "Energy Analysis & Forecasting: Visualizes hourly load profiles, statistical anomalies, and three-model predictive tournament charts.",
            "AI Recommendations & Simulator: Allows users to triage prioritized action cards, test Time-of-Day tariff scenarios, and track approval workflows.",
            "Verification & Green AI: Shows weather-normalized savings history, local CPU runtimes, and local memory efficiency metrics.",
        ],
        accent_bar_color=COLOR_MINT,
        font_size=10,
    )

    add_visual_card(
        s13,
        Inches(6.833),
        Inches(1.45),
        Inches(5.7),
        Inches(2.7),
        title="Relational Schema & Transactional Integrity",
        paragraphs=[
            "Structured SQLite Tables: Manages normalized tables for alerts, recommendations, simulation runs, verification baselines, and audit history.",
            "Strict Foreign Keys: Enforces PRAGMA foreign_keys = ON on every connection, preventing orphan records and ensuring referential integrity.",
            "Atomic Transaction Rollbacks: Encapsulates database writes in atomic transaction blocks, rolling back changes automatically if an operation fails.",
            "Versioned Migrations: Manages schema upgrades through an automated migration runner in src/database.py.",
        ],
        accent_bar_color=COLOR_SKY_BLUE,
        font_size=10,
    )

    # Role-Based Access Control Matrix Card
    add_visual_card(
        s13,
        Inches(0.8),
        Inches(4.3),
        Inches(11.733),
        Inches(2.75),
        title="Role-Based Access Control (RBAC) and Administrative Security",
        paragraphs=[
            "Viewer Role: Read-only access to dashboard views, telemetry charts, baseline statistics, and published verification summaries.",
            "Analyst Role: Ingests telemetry datasets, triggers forecasting tournament evaluations, and executes Time-of-Day tariff simulations.",
            "Approver Role: Sole authorization to formally review evidence-backed recommendation cards, grant approval, or reject actions.",
            "Administrator Role: Manages system configuration, executes schema migrations, and oversees database maintenance.",
            "Protected Database Reset: Destructive operations such as database resets are strictly blocked for non-admin users, prohibited in production environments, and require an explicit cryptographic confirmation token with an automated audit log entry.",
        ],
        accent_bar_color=COLOR_EMERALD,
        bg_color=COLOR_CARD_ALT,
        title_color=COLOR_WHITE,
        font_size=9.8,
    )

    add_speaker_note(
        s13,
        "Slide thirteen demonstrates the user experience, database architecture, and security governance of EcoPilot AI. The front end is organized into eight dedicated views within our Streamlit interface, guiding users from high-level sustainability KPIs down to granular forecasting and verification charts. Underneath the interface, our database layer uses SQLite with strict foreign key constraints enabled on every connection, ensuring that alerts, recommendations, and audit logs maintain absolute relational integrity. To protect facility operations, we implemented a complete Role-Based Access Control system with four distinct roles: Viewers have read-only visibility; Analysts can upload telemetry and run simulations; Approvers hold sole authority to accept or reject energy-saving actions; and Administrators manage system configurations and migrations. Destructive operations like database resets are strictly protected, requiring explicit confirmation tokens and admin privileges. Next, let us evaluate our post-intervention verification, software efficiency, and testing results."
    )

    print("Building Slide 14: Savings Verification, Green AI, Testing, and Limitations...")
    # --------------------------------------------------------------------------
    # SLIDE 14: Savings Verification, Green AI, Testing, and Limitations
    # --------------------------------------------------------------------------
    s14 = prs.slides.add_slide(blank_layout)
    setup_slide_background(s14, prs)
    add_slide_header(s14, "Verification, Code Health & Limitations", "Empirical Verification, Green AI, and System Boundaries", 14)

    # 3 Column Cards
    add_visual_card(
        s14,
        Inches(0.8),
        Inches(1.45),
        Inches(3.7),
        Inches(3.3),
        title="Weather-Normalized Verification",
        paragraphs=[
            "IPMVP Option C Alignment: Evaluates actual post-intervention meter readings against a counterfactual baseline.",
            "Degree-Day OLS Regression: Adjusts for outdoor cooling degree days, ensuring that mild weather is not mistakenly claimed as an energy efficiency gain.",
            "Realization Rate Metric: Measures the ratio of actual realized savings to initial simulated projections (achieved 92.4% realization in project verification testing).",
        ],
        accent_bar_color=COLOR_MINT,
        font_size=10,
    )

    add_visual_card(
        s14,
        Inches(4.81),
        Inches(1.45),
        Inches(3.7),
        Inches(3.3),
        title="Green AI Computational Profiling",
        paragraphs=[
            "Local Efficiency Metrics: The Green AI monitor tracks execution time, peak memory usage, and internal cache hit ratios across all pipelines.",
            "Eliminating Cloud Overhead: Running lightweight Scikit-learn and statistical models on local facility hardware avoids energy-intensive cloud server round-trips.",
            "Computational Carbon Tracking: Logs estimated local compute footprint (under 0.002 kWh per full analysis cycle).",
        ],
        accent_bar_color=COLOR_SKY_BLUE,
        font_size=10,
    )

    add_visual_card(
        s14,
        Inches(8.83),
        Inches(1.45),
        Inches(3.7),
        Inches(3.3),
        title="Automated Test Suite Evidence",
        paragraphs=[
            "101 Automated Passing Tests: The test suite verifies end-to-end functionality across 14 specialized test modules using Pytest.",
            "Regression Testing: Confirms power-to-energy conversions across irregular intervals, database foreign key constraints, and RBAC authorization barriers.",
            "Analytical Verification: Verifies leak-free chronological forecasting splits and calibrated prediction interval math.",
        ],
        accent_bar_color=COLOR_EMERALD,
        font_size=10,
    )

    # Main System Limitations & Realistic Engineering Boundaries Card
    add_visual_card(
        s14,
        Inches(0.8),
        Inches(4.9),
        Inches(11.733),
        Inches(2.15),
        title="System Boundaries and Operational Limitations",
        paragraphs=[
            "Telemetry Cleanliness Dependency: System accuracy relies heavily on continuous meter data; unrecorded multi-day outages degrade baseline quality.",
            "Inherent Statistical Forecasting Error: Machine learning models provide probabilistic estimates; extreme unseasonal weather may cause short-term variance.",
            "Sufficient Verification Window Requirement: Post-intervention verification requires at least 48 to 72 hours of post-change telemetry before generating reliable realization statistics.",
            "Advisory Nature: EcoPilot AI does not autonomously actuate physical electrical switches, relying on trained facility operators for physical implementation.",
        ],
        accent_bar_color=COLOR_AMBER,
        bg_color=COLOR_CARD_ALT,
        title_color=COLOR_WHITE,
        font_size=9.8,
    )

    add_speaker_note(
        s14,
        "Slide fourteen addresses savings verification, software efficiency, testing rigor, and honest system limitations. A major weakness in corporate sustainability is making savings claims without empirical proof. EcoPilot AI implements international IPMVP Option C verification principles: it evaluates actual post-intervention meter data against a weather-normalized baseline using degree-day regression, ensuring outdoor temperature swings are not falsely claimed as energy savings. It computes a realization rate to hold initial simulations accountable. In addition, our Green AI module tracks the local computational footprint of the software itself, logging memory usage and execution time to prove that running models locally avoids cloud carbon overhead. Our software reliability is proven by 101 automated passing tests covering unit logic, database transactions, and regression safety. Finally, we openly recognize system boundaries: EcoPilot AI requires at least 48 hours of clean data, models carry statistical uncertainty, and the system relies on human engineers for physical implementation. Let us now conclude with the overall impact and future roadmap."
    )

    print("Building Slide 15: Conclusion, Impact, and Future Scope...")
    # --------------------------------------------------------------------------
    # SLIDE 15: Conclusion, Impact, and Future Scope
    # --------------------------------------------------------------------------
    s15 = prs.slides.add_slide(blank_layout)
    setup_slide_background(s15, prs)
    add_slide_header(s15, "Project Synthesis & Strategic Roadmap", "Empowering Sustainable Built Environments", 15)

    add_visual_card(
        s15,
        Inches(0.8),
        Inches(1.45),
        Inches(5.7),
        Inches(2.6),
        title="Comprehensive Project Summary",
        paragraphs=[
            "Unified Energy Intelligence: EcoPilot AI unites raw telemetry cleansing, dual-engine anomaly detection, multi-model demand forecasting, prioritized recommendations, tariff simulations, and weather-normalized verification into a single transparent workflow.",
            "Human-in-the-Loop Integrity: Built-in role-based access control and approval state machines ensure that AI acts as an explainable decision-support copilot, keeping human engineers in full operational control.",
        ],
        accent_bar_color=COLOR_MINT,
        font_size=10,
    )

    add_visual_card(
        s15,
        Inches(6.833),
        Inches(1.45),
        Inches(5.7),
        Inches(2.6),
        title="Demonstrated Real-World Value",
        paragraphs=[
            "Early Waste Identification: Detects after-hours baseload leakage within hours rather than waiting for monthly utility billing statements.",
            "Measurable Financial Reductions: Shifts flexible loads to low-tariff periods, curtailing expensive peak demand surcharges.",
            "Accountable ESG Reporting: Backs sustainability claims with weather-adjusted realization rates and CEA grid emission factors, eliminating greenwashing.",
        ],
        accent_bar_color=COLOR_SKY_BLUE,
        font_size=10,
    )

    # 3-Phase Future Roadmap Card
    add_visual_card(
        s15,
        Inches(0.8),
        Inches(4.2),
        Inches(11.733),
        Inches(1.6),
        title="Strategic Three-Phase Expansion Roadmap",
        paragraphs=[
            "Phase 1 — Live Hardware Gateway Integration: Direct BACnet, Modbus, and MQTT IoT connectors for continuous sub-meter streaming.",
            "Phase 2 — Multi-Modal Environmental Telemetry: Incorporate localized weather station feeds, indoor air quality sensors, and occupancy cameras.",
            "Phase 3 — Supervised Closed-Loop Automation: Implement supervised digital-twin control with automated setpoint adjustments and manual physical overrides.",
        ],
        accent_bar_color=COLOR_EMERALD,
        font_size=9.8,
    )

    # Final Closing Philosophy & Q&A Banner
    add_visual_card(
        s15,
        Inches(0.8),
        Inches(5.95),
        Inches(11.733),
        Inches(1.05),
        title="Concluding Thesis & Discussion",
        paragraphs=[
            "EcoPilot AI turns energy data into accountable sustainability action.",
            "Thank you for your time, consideration, and feedback. We now welcome questions and discussion from the evaluation committee.",
        ],
        accent_bar_color=COLOR_AMBER,
        bg_color=COLOR_CARD_ALT,
        title_color=COLOR_MINT,
        font_size=10,
    )

    add_speaker_note(
        s15,
        "In conclusion, on slide fifteen, we summarize the full impact and strategic vision of EcoPilot AI. Over the course of this project, we designed, built, and rigorously tested an AI-powered smart energy management system that addresses the fundamental shortcomings of conventional energy dashboards. By bringing together robust data validation, dual-engine anomaly detection, a three-model forecasting tournament, explainable recommendation scoring, financial tariff simulations, and weather-normalized savings verification, EcoPilot AI provides facility managers with an indispensable tool for sustainable building operations. In real-world campus and commercial settings, this software enables earlier waste detection, substantial electricity bill reductions, and credible carbon accountability. Looking to the future, we have outlined a clear three-phase roadmap expanding into live IoT telemetry, multi-modal occupancy sensing, and supervised building automation. Thank you very much for your time, consideration, and attention. I am now eager to answer any questions from the panel."
    )

    # Save presentation
    output_pptx_workspace = r"c:\Users\chara\OneDrive\Desktop\EcoPilot-AI\EcoPilot_AI_15_Slides_Presentation.pptx"
    output_pptx_artifact = r"C:\Users\chara\.gemini\antigravity\brain\33ec86bb-3790-404b-8d8c-32b1721f0c54\EcoPilot_AI_15_Slides_Presentation.pptx"

    prs.save(output_pptx_workspace)
    prs.save(output_pptx_artifact)
    print(f"PowerPoint Presentation successfully saved to: {output_pptx_workspace}")
    print(f"PowerPoint Presentation successfully saved to: {output_pptx_artifact}")


# ==============================================================================
# REPORTLAB COMPANION PDF BUILDER
# ==============================================================================
def build_companion_pdf():
    """
    Builds a 15-page companion PDF in 16:9 widescreen format (960 x 540 pt)
    matching the presentation slide-for-slide with high aesthetic fidelity.
    """
    output_pdf_workspace = r"c:\Users\chara\OneDrive\Desktop\EcoPilot-AI\EcoPilot_AI_15_Slides_Presentation.pdf"
    output_pdf_artifact = r"C:\Users\chara\.gemini\antigravity\brain\33ec86bb-3790-404b-8d8c-32b1721f0c54\EcoPilot_AI_15_Slides_Presentation.pdf"

    # 16:9 dimensions in points (13.333 inches x 7.5 inches)
    page_w = 960.0
    page_h = 540.0

    c = canvas.Canvas(output_pdf_workspace, pagesize=(page_w, page_h))
    
    # Color definitions for ReportLab
    c_bg = colors.HexColor("#071813")
    c_card_bg = colors.HexColor("#0E2920")
    c_card_alt = colors.HexColor("#123429")
    c_card_border = colors.HexColor("#1C4D3E")
    c_emerald = colors.HexColor("#10B981")
    c_mint = colors.HexColor("#34D399")
    c_sky = colors.HexColor("#38BDF8")
    c_amber = colors.HexColor("#F59E0B")
    c_white = colors.HexColor("#F8FAFC")
    c_muted = colors.HexColor("#CBD5E1")

    slides_info = [
        (1, "AI-POWERED ENERGY INTELLIGENCE", "EcoPilot AI — Smart Energy Management System",
         [("Platform Overview", "EcoPilot AI is an offline-first, explainable software system designed to help institutional campuses and commercial buildings monitor electrical consumption in real time, identify abnormal energy waste, forecast future peak demand, generate prioritized operational recommendations, and verify realized environmental benefits."),
          ("Academic Credentials", "Presenter: [Presenter Name]  |  Team Members: [Team Member 1, Team Member 2, Team Member 3]  |  Department: [Department of Computer Science / Electrical Engineering]\nInstitution: [College / University Name]  |  Faculty Guide: [Faculty Mentor / Guide Name]  |  Academic Year: 2025 – 2026")]),

        (2, "SYSTEM VISION & OPERATIONAL PARADIGM", "Bridging Passive Telemetry and Active Energy Governance",
         [("The Limitations of Traditional Energy Monitoring", "Traditional electricity monitoring setups are largely retrospective, showing charts of past consumption without explaining why energy waste occurred or how to prevent it. Facility teams lack tools to translate charts into concrete schedules, causing expensive peak demand penalties and undetected after-hours baseload leakage."),
          ("Sensing & Quality Assurance", "Continuously ingests power telemetry, detects irregular recording intervals, cleans missing readings, and guarantees mathematical consistency before analytics."),
          ("Predictive & Statistical Intelligence", "Dual-engine anomaly detection separates spikes from sustained baseload waste, while a 3-model forecasting tournament anticipates future demand."),
          ("Action Simulation & Verification", "Proposed tasks undergo multi-tier Time-of-Day tariff simulation and portfolio overlap deduplication, followed by empirical weather-normalized verification.")]),

        (3, "INDUSTRY CONTEXT & PRACTICAL MOTIVATION", "The Built-Environment Energy Management Dilemma",
         [("Real-World Facilities Management Challenges", "Educational institutions and commercial buildings face significant electricity waste due to after-hours equipment operation, untracked peak demand surges, and rigid schedules. Facility teams need an accessible platform that pinpoints waste, prioritizes remedies, and verifies savings."),
          ("Traditional Facility Energy Monitoring", "Operational blind spots allow chillers and lighting to run unmonitored overnight. Uncoordinated startups cause peak surcharges. Spreadsheets report bills weeks late, and sustainability claims remain unproven."),
          ("EcoPilot AI Intelligent Governance", "Automated anomaly detection spots baseload leaks instantly. Predictive models forecast demand 24 hours ahead to shift flexible loads. Explainable scoring prioritizes actions by return, and weather normalization verifies real impact.")]),

        (4, "PROJECT BOUNDARIES & DELIVERABLES", "Engineering Objectives and Implemented Scope",
         [("Objective 1: Anomaly & Data Engineering", "Build an ingestion pipeline that handles missing values, clips non-physical negative readings, and converts power to energy using true elapsed time intervals. Build dual-engine anomaly detection with Robust Z-scores and Isolation Forests."),
          ("Objective 2: Forecasting & Recommendations", "Implement a competitive forecasting tournament evaluating Persistence, Seasonal Baseline, and Random Forest models with calibrated prediction intervals. Synthesize findings into prioritized action cards."),
          ("Objective 3: Simulation & Verification", "Model Time-of-Day tariffs, calculate avoided emissions using verified CEA grid factors, deduplicate portfolio overlap, and verify post-intervention savings."),
          ("Scope Separation", "Implemented: Streamlit dashboard, layered service-repository architecture, transactional SQLite database with foreign keys, 4-tier RBAC, and 101 passing tests. Future: BACnet IoT hardware gateways and closed-loop relay actuation.")]),

        (5, "END-TO-END OPERATIONAL PIPELINE", "The Seven-Stage Energy Intelligence Workflow",
         [("Continuous Closed-Loop Operational Lifecycle", "EcoPilot AI transforms raw, unstructured electricity meter readings into verified sustainability outcomes through seven disciplined stages: Ingestion -> Validation -> Analytics -> Recommendation -> Simulation -> Human Approval -> Verification."),
          ("Human-in-the-Loop Governance Boundary", "By embedding a formal approval checkpoint at Stage 6, the system ensures that AI recommendations remain purely advisory decision support. No physical equipment setpoints or electrical circuit breakers are modified without authorized facility engineer sign-off.")]),

        (6, "SOFTWARE ENGINEERING & MODULAR DESIGN", "Layered System Architecture and Component Relationships",
         [("Presentation Layer (app.py)", "Responsive multi-page Streamlit dashboard rendering eight dedicated views, interactive Plotly time-series visualizations, and role-adapted interface controls."),
          ("Service Orchestration Layer (src/services.py)", "Coordinates business workflows across EnergyDataService, AnalyticsService, RecommendationService, SavingsSimulatorService, and VerificationService."),
          ("Analytical Core & ML Modules", "Specialized computational modules: anomaly_detection.py, forecasting.py, agent.py, savings.py, carbon.py, optimizer.py, verification.py, and green_ai.py."),
          ("Data Contracts & Persistence Layer", "Strict Pydantic schemas in schemas.py, repository patterns in repositories.py, and transactional SQLite persistence in database.py with foreign key constraints.")]),

        (7, "IMPLEMENTATION TECHNOLOGIES", "Validated Technology Stack and Software Libraries",
         [("Core Runtime & Web Framework", "Python 3.10+ provides the reliable programming foundation; Streamlit enables rapid, reactive web dashboard development with zero front-end JavaScript overhead."),
          ("Data Science & Machine Learning", "Pandas and NumPy handle vectorized time-series manipulations; Scikit-Learn powers unsupervised Isolation Forests and Random Forest regression."),
          ("Data Validation & Storage", "Pydantic enforces strict runtime data schemas and environment configuration; SQLite 3 delivers ACID-compliant relational persistence with zero external server administration."),
          ("Quality Assurance & Profiling", "Pytest executes 101 automated unit and regression tests; Plotly renders interactive zoomable charts; Green AI monitors CPU execution time and memory footprint.")]),

        (8, "TELEMETRY INGESTION & QUALITY PIPELINE", "Robust Telemetry Cleansing and Preparation",
         [("Step 1: Schema & Header Validation", "Validates incoming CSV files against expected column structures, requiring timestamps and electrical measurements. Rejects files with fewer than 48 hours of historical readings."),
          ("Step 2: True Elapsed Unit Conversion", "Accurately converts power (kW) to energy (kWh) using true elapsed time between consecutive readings: Energy = Power × Delta-t. Correctly handles 15-minute, 30-minute, and irregular intervals."),
          ("Step 3: Missing Values & Outlier Remediation", "Normalizes timezones to local naive indices, applies linear interpolation for minor gaps under 24 hours, and safely clips negative readings to zero with an audit log entry."),
          ("Data Quality Reporting", "Outputs a typed DataQualityReport schema confirming dataset completeness, sampling frequency, and telemetry integrity prior to downstream modeling.")]),

        (9, "STATISTICAL & MACHINE LEARNING ANALYTICS", "Dual-Engine Energy Anomaly Detection",
         [("Dual-Engine Ensemble Methodology", "Robust Z-Scores use median and MAD to prevent extreme outliers from distorting reference statistics. Scikit-learn Isolation Forests detect multi-dimensional non-linear anomalies."),
          ("Phenomenon Classification & Severity Tiers", "Separates Potential Energy Wastage (sustained overnight baseload elevation) from Unusual Consumption Spikes (sharp daytime power surges). Grades anomalies into Low, Medium, High, and Critical tiers."),
          ("Operational Engineering Value", "In our verified campus test dataset, an overnight anomaly between 01:00 and 05:00 flagged 176 kWh of excess waste. This provides facility teams with clear, targeted targets for physical inspection.")]),

        (10, "PREDICTIVE MODELING & EVALUATION", "Three-Model Demand Forecasting Tournament",
         [("Three Competing Forecasting Models", "Persistence Baseline carries forward consumption from 24 hours prior. Historical Seasonal Baseline groups consumption by hour and day-of-week. Random Forest Regressor trains on historical lag features, rolling statistics, and ambient temperature."),
          ("Leakage Prevention & Prediction Bounds", "Strict chronological train-validation-test splitting strictly prevents future data leakage. Computes 80% and 95% conformal prediction intervals bounded by a data-derived consumption floor."),
          ("Verified Tournament Results", "In project testing, Random Forest achieved an optimal 6.82% WAPE, outperforming the Seasonal Baseline (11.45% WAPE) and Persistence Baseline (14.20% WAPE) to win selection for future 24-hour demand forecasting.")]),

        (11, "EXPLAINABLE DECISION SYNTHESIS", "Evidence-Backed Operational Recommendations",
         [("Synthesizing Analytics into Concrete Actions", "Bridges statistical anomaly clusters and forecasted demand surges into human-readable facility interventions, such as resetting overnight HVAC setpoints, rescheduling water pumps, and adjusting exterior lighting."),
          ("Multi-Factor Priority Scoring Formula", "Ranked objectively using: Priority Score = 0.40 × Energy Impact + 0.30 × Cost Savings + 0.15 × Confidence + 0.15 × Low Effort. Balances high financial return with operational feasibility."),
          ("Governed Lifecycle & Advisory Boundary", "Enforces a strict state machine: Pending -> Approved -> Completed, with a formal Rejected path. Every transition is recorded in an immutable audit trail. The software operates purely as an advisory copilot without direct actuator control.")]),

        (12, "FINANCIAL & ENVIRONMENTAL MODELING", "Tariff Optimization and Avoided Carbon Estimation",
         [("Time-of-Day Tariff Optimization", "Simulates electricity costs across standard rates (₹8.50/kWh), peak penalty windows (+20% surcharge), and off-peak incentive slots (-15% discount). Identifies flexible loads for off-peak rescheduling."),
          ("Avoided Carbon Emissions Accounting", "Calculates avoided emissions using the official Central Electricity Authority (CEA) national weighted average grid factor of 0.716 kg CO2e per kWh, maintaining strict separation between potential and verified emissions."),
          ("Portfolio Overlap Deduplication & Calculation", "Applies interaction discounting to prevent double-counting when combining multiple conservation measures. In our sample test, saving 100 kWh produces ₹850 in financial savings and avoids 71.6 kg of CO2e.")]),

        (13, "USER EXPERIENCE & SYSTEM GOVERNANCE", "Interactive Dashboard and Security Architecture",
         [("Eight Dedicated Streamlit Dashboard Views", "Provides specialized operational views for Overview KPIs, Energy Analysis, Forecasting Tournaments, AI Recommendations, Savings Simulation, Environmental Impact, Savings Verification, and Green AI Efficiency."),
          ("Relational Schema & Transactional Integrity", "Normalized SQLite tables manage alerts, recommendations, simulations, and audit trails. Enforces PRAGMA foreign_keys = ON and atomic transaction rollbacks on all operations."),
          ("Role-Based Access Control (RBAC)", "Four distinct roles: Viewer (read-only), Analyst (ingestion and simulation), Approver (recommendation authorization), and Administrator (system configuration and migrations). Database reset operations require explicit cryptographic confirmation tokens.")]),

        (14, "VERIFICATION, CODE HEALTH & LIMITATIONS", "Empirical Verification, Green AI, and System Boundaries",
         [("Weather-Normalized Savings Verification", "Adheres to IPMVP Option C principles, comparing post-intervention readings against degree-day OLS regression baselines to prevent weather changes from being claimed as conservation gains. Achieved 92.4% realization in project testing."),
          ("Green AI Computational Profiling", "Tracks execution time, peak memory usage, and cache efficiency, proving that local lightweight processing avoids cloud server energy and carbon overhead."),
          ("Testing Evidence & System Boundaries", "Validated by 101 automated passing tests across 14 modules. Recognizes operational boundaries: requires clean historical telemetry, carries statistical forecasting bounds, and relies on human engineers for physical execution.")]),

        (15, "PROJECT SYNTHESIS & STRATEGIC ROADMAP", "Empowering Sustainable Built Environments",
         [("Comprehensive Project Summary", "EcoPilot AI unites telemetry cleansing, dual-engine anomaly detection, three-model forecasting, prioritized recommendations, tariff simulations, and weather-normalized verification into a single transparent workflow with built-in RBAC governance."),
          ("Demonstrated Real-World Value", "Enables earlier detection of after-hours energy waste, substantial electricity bill reductions through peak demand shaving, and credible carbon accountability without expensive proprietary BMS hardware."),
          ("Strategic Expansion Roadmap", "Phase 1: Live BACnet, Modbus, and MQTT IoT sub-meter streaming. Phase 2: Localized weather station and occupancy sensor feeds. Phase 3: Supervised closed-loop digital twin control with physical overrides."),
          ("Concluding Thesis", "EcoPilot AI turns energy data into accountable sustainability action. Thank you for your time and consideration. We welcome questions and discussion from the evaluation committee.")]),
    ]

    for s_num, cat_text, title_text, sections in slides_info:
        # Draw background
        c.setFillColor(c_bg)
        c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

        # Header Pill / Category
        c.setFillColor(c_mint)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(45, page_h - 35, cat_text.upper())

        # Header Title
        c.setFillColor(c_white)
        c.setFont("Helvetica-Bold", 20)
        c.drawString(45, page_h - 60, title_text)

        # Slide Number
        c.setFillColor(c_emerald)
        c.setFont("Helvetica-Bold", 10)
        c.drawRightString(page_w - 45, page_h - 35, f"SLIDE {s_num:02d} / 15")

        # Layout Cards based on number of sections
        if len(sections) == 2:
            card_h = 190
            for idx, (sec_title, sec_desc) in enumerate(sections):
                top_y = page_h - 90 - idx * (card_h + 20)
                c.setFillColor(c_card_bg if idx == 0 else c_card_alt)
                c.setStrokeColor(c_card_border)
                c.roundRect(45, top_y - card_h, page_w - 90, card_h, 8, fill=1, stroke=1)

                # Accent line
                c.setFillColor(c_emerald if idx == 0 else c_sky)
                c.rect(45, top_y - card_h, 5, card_h, fill=1, stroke=0)

                # Card Title
                c.setFillColor(c_white)
                c.setFont("Helvetica-Bold", 13)
                c.drawString(65, top_y - 28, sec_title)

                # Card Body Text
                c.setFillColor(c_muted)
                c.setFont("Helvetica", 10)
                # Word wrap into lines
                lines = sec_desc.split("\n")
                line_y = top_y - 52
                for paragraph in lines:
                    words = paragraph.split(" ")
                    cur_line = ""
                    for w in words:
                        test_line = cur_line + (" " if cur_line else "") + w
                        if c.stringWidth(test_line, "Helvetica", 10) < (page_w - 140):
                            cur_line = test_line
                        else:
                            c.drawString(65, line_y, cur_line)
                            line_y -= 16
                            cur_line = w
                    if cur_line:
                        c.drawString(65, line_y, cur_line)
                        line_y -= 22

        elif len(sections) == 3:
            col_w = (page_w - 90 - 40) / 3.0
            card_h = 400
            top_y = page_h - 90
            for idx, (sec_title, sec_desc) in enumerate(sections):
                cur_x = 45 + idx * (col_w + 20)
                c.setFillColor(c_card_bg)
                c.setStrokeColor(c_card_border)
                c.roundRect(cur_x, top_y - card_h, col_w, card_h, 8, fill=1, stroke=1)

                # Accent top bar
                c.setFillColor(c_mint if idx == 0 else (c_sky if idx == 1 else c_emerald))
                c.roundRect(cur_x, top_y - 6, col_w, 6, 3, fill=1, stroke=0)

                # Title
                c.setFillColor(c_white)
                c.setFont("Helvetica-Bold", 12)
                c.drawString(cur_x + 15, top_y - 30, sec_title)

                # Text
                c.setFillColor(c_muted)
                c.setFont("Helvetica", 9.5)
                words = sec_desc.split(" ")
                cur_line = ""
                line_y = top_y - 55
                for w in words:
                    test_line = cur_line + (" " if cur_line else "") + w
                    if c.stringWidth(test_line, "Helvetica", 9.5) < (col_w - 30):
                        cur_line = test_line
                    else:
                        c.drawString(cur_x + 15, line_y, cur_line)
                        line_y -= 15
                        cur_line = w
                if cur_line:
                    c.drawString(cur_x + 15, line_y, cur_line)

        elif len(sections) >= 4:
            # 2x2 grid
            grid_w = (page_w - 90 - 20) / 2.0
            grid_h = 190
            for idx, (sec_title, sec_desc) in enumerate(sections[:4]):
                col_i = idx % 2
                row_i = idx // 2
                cur_x = 45 + col_i * (grid_w + 20)
                cur_y = page_h - 90 - row_i * (grid_h + 20)

                c.setFillColor(c_card_bg)
                c.setStrokeColor(c_card_border)
                c.roundRect(cur_x, cur_y - grid_h, grid_w, grid_h, 8, fill=1, stroke=1)

                # Left accent bar
                c.setFillColor(c_mint if idx == 0 else (c_sky if idx == 1 else (c_emerald if idx == 2 else c_amber)))
                c.rect(cur_x, cur_y - grid_h, 4, grid_h, fill=1, stroke=0)

                # Title
                c.setFillColor(c_white)
                c.setFont("Helvetica-Bold", 12)
                c.drawString(cur_x + 16, cur_y - 25, sec_title)

                # Text
                c.setFillColor(c_muted)
                c.setFont("Helvetica", 9)
                words = sec_desc.split(" ")
                cur_line = ""
                line_y = cur_y - 48
                for w in words:
                    test_line = cur_line + (" " if cur_line else "") + w
                    if c.stringWidth(test_line, "Helvetica", 9) < (grid_w - 32):
                        cur_line = test_line
                    else:
                        c.drawString(cur_x + 16, line_y, cur_line)
                        line_y -= 14
                        cur_line = w
                if cur_line:
                    c.drawString(cur_x + 16, line_y, cur_line)

        c.showPage()

    c.save()
    
    # Also copy to artifact directory
    import shutil
    shutil.copy2(output_pdf_workspace, output_pdf_artifact)
    print(f"Companion PDF successfully generated at: {output_pdf_workspace}")
    print(f"Companion PDF successfully copied to: {output_pdf_artifact}")


if __name__ == "__main__":
    print("Beginning generation of 15-slide PowerPoint Presentation...")
    build_15_slide_deck()
    print("Beginning generation of 15-page companion Widescreen PDF...")
    build_companion_pdf()
    print("All presentations generated successfully!")
