"""
EcoPilot AI: Complete 15-Slide Presentation Generator
Generates:
1. Editable Microsoft PowerPoint (.pptx) - 16:9 widescreen, custom theme, zero bullet points.
2. Companion High-Resolution PDF (.pdf) - 16:9 landscape using ReportLab.
"""

import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

# --- Color Palette Configuration ---
COLOR_BG_DARK = RGBColor(7, 24, 19)       # #071813 Deep Forest Slate Green
COLOR_CARD_BG = RGBColor(14, 41, 32)      # #0E2920 Card container
COLOR_CARD_BORDER = RGBColor(26, 74, 59)  # #1A4A3B Card border
COLOR_EMERALD = RGBColor(16, 185, 129)    # #10B981 Primary accent
COLOR_MINT = RGBColor(52, 211, 153)       # #34D399 Light green highlight
COLOR_SKY_BLUE = RGBColor(56, 189, 248)   # #38BDF8 Subtle blue accent
COLOR_AMBER = RGBColor(245, 158, 11)      # #F59E0B Warning/Highlight
COLOR_WHITE = RGBColor(248, 250, 252)     # #F8FAFC Heading text
COLOR_MUTED = RGBColor(203, 213, 225)     # #CBD5E1 Body text
COLOR_DARK_TEXT = RGBColor(4, 47, 26)     # #042F1A Dark text on light pill

def create_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]
    return prs, blank_layout

print("Script template ready")
