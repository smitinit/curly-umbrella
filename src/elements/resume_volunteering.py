from reportlab.platypus import Paragraph
from src.constants.resume_constants import (
    COMPANY_HEADING_PARAGRAPH_STYLE,
    COMPANY_DURATION_PARAGRAPH_STYLE,
    COMPANY_TITLE_PARAGRAPH_STYLE,
    COMPANY_LOCATION_PARAGRAPH_STYLE,
    JOB_DETAILS_PARAGRAPH_STYLE,
)


class Volunteering:
    def __init__(self, organization="", role="", location="", start_date="", end_date="", description=None):
        self.organization = organization
        self.role         = role
        self.location     = location
        self.start_date   = start_date
        self.end_date     = end_date
        self.description  = description or []

    def set_organization(self, v: str):  self.organization = v
    def set_role(self, v: str):          self.role = v
    def set_location(self, v: str):      self.location = v
    def set_start_date(self, v: str):    self.start_date = v
    def set_end_date(self, v: str):      self.end_date = v
    def set_description(self, v: list):  self.description = v
    def append_description(self, v: str): self.description.append(v)

    def get_table_element(self, running_row_index: list, table_styles: list) -> list:
        table = []

        # Row 1: organization (left) | date range (right)
        table.append([
            Paragraph(self.organization, COMPANY_HEADING_PARAGRAPH_STYLE),
            Paragraph(f"{self.start_date} – {self.end_date}", COMPANY_DURATION_PARAGRAPH_STYLE),
        ])
        table_styles.append(("TOPPADDING",    (0, running_row_index[0]), (1, running_row_index[0]), 5))
        table_styles.append(("BOTTOMPADDING", (0, running_row_index[0]), (1, running_row_index[0]), 1))
        running_row_index[0] += 1

        # Row 2: role (left) | location (right)
        table.append([
            Paragraph(self.role,     COMPANY_TITLE_PARAGRAPH_STYLE),
            Paragraph(self.location, COMPANY_LOCATION_PARAGRAPH_STYLE),
        ])
        table_styles.append(("TOPPADDING",    (0, running_row_index[0]), (1, running_row_index[0]), 1))
        table_styles.append(("BOTTOMPADDING", (0, running_row_index[0]), (1, running_row_index[0]), 2))
        running_row_index[0] += 1

        # Bullet rows
        for line in self.description:
            table.append([
                Paragraph(line, bulletText="•", style=JOB_DETAILS_PARAGRAPH_STYLE)
            ])
            table_styles.append(("TOPPADDING",    (0, running_row_index[0]), (1, running_row_index[0]), 1))
            table_styles.append(("BOTTOMPADDING", (0, running_row_index[0]), (1, running_row_index[0]), 0))
            table_styles.append(("SPAN",          (0, running_row_index[0]), (1, running_row_index[0])))
            running_row_index[0] += 1

        return table