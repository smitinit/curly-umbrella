from src.constants import GARAMOND_REGULAR, GARAMOND_BOLD, GARAMOND_SEMIBOLD, GARAMOND_ITALIC
from reportlab.lib.enums import TA_RIGHT, TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors

# ── Section order in the final PDF ────────────────────────────────────────────
RESUME_ELEMENTS_ORDER = [
    "summary",
    "skills",
    "experience",
    "projects",
    "education",
    "certifications",
    "awards",
    "volunteering",
    "languages",
    "achievements",
]

# ── Paragraph styles ───────────────────────────────────────────────────────────
NAME_PARAGRAPH_STYLE = ParagraphStyle(
    "name_paragraph",
    fontName=GARAMOND_BOLD,
    fontSize=20,
    leading=24,
    alignment=TA_LEFT,
)

TITLE_PARAGRAPH_STYLE = ParagraphStyle(
    "title_paragraph",
    fontName=GARAMOND_ITALIC,
    fontSize=13,
    leading=16,
    alignment=TA_LEFT,
    textColor=colors.HexColor("#444444"),
)

CONTACT_PARAGRAPH_STYLE = ParagraphStyle(
    "contact_paragraph",
    fontName=GARAMOND_REGULAR,
    fontSize=11,
    leading=14,
    alignment=TA_LEFT,
)

SECTION_PARAGRAPH_STYLE = ParagraphStyle(
    "section_paragraph",
    fontName=GARAMOND_BOLD,
    fontSize=12,
    leading=14,
    textTransform="uppercase",
    spaceAfter=2,
)

COMPANY_HEADING_PARAGRAPH_STYLE = ParagraphStyle(
    "company_heading_paragraph",
    fontName=GARAMOND_SEMIBOLD,
    fontSize=11,
    leading=14,
)

COMPANY_TITLE_PARAGRAPH_STYLE = ParagraphStyle(
    "company_title_paragraph",
    fontName=GARAMOND_ITALIC,
    fontSize=10,
    leading=13,
)

COMPANY_DURATION_PARAGRAPH_STYLE = ParagraphStyle(
    "company_duration_paragraph",
    fontName=GARAMOND_SEMIBOLD,
    fontSize=11,
    leading=14,
    alignment=TA_RIGHT,
)

COMPANY_LOCATION_PARAGRAPH_STYLE = ParagraphStyle(
    "company_location_paragraph",
    fontName=GARAMOND_ITALIC,
    fontSize=10,
    leading=13,
    alignment=TA_RIGHT,
)

JOB_DETAILS_PARAGRAPH_STYLE = ParagraphStyle(
   "job_details_paragraph",
    fontName=GARAMOND_REGULAR,
    fontSize=10,
    leading=13,
    leftIndent=14,
    bulletIndent=4,
    alignment=TA_JUSTIFY,
)

PROJECT_PARAGRAPH_STYLE = ParagraphStyle(
    "project_paragraph",
    fontName=GARAMOND_REGULAR,
    fontSize=10,
    leading=13,
    leftIndent=14,
    bulletIndent=4,
    alignment=TA_JUSTIFY,
)


def append_section_table_style(table_styles: list, running_row_index: list) -> None:
    """Add a divider line below the section heading row."""
    table_styles.append(("TOPPADDING",  (0, running_row_index[0]), (1, running_row_index[0]), 6))
    table_styles.append(("BOTTOMPADDING", (0, running_row_index[0]), (1, running_row_index[0]), 4))
    table_styles.append(("LINEBELOW",   (0, running_row_index[0]), (-1, running_row_index[0]), 0.8, colors.black))
