from reportlab.platypus import Paragraph
from src.constants.resume_constants import (
    COMPANY_HEADING_PARAGRAPH_STYLE,
    COMPANY_DURATION_PARAGRAPH_STYLE,
    COMPANY_TITLE_PARAGRAPH_STYLE,
    COMPANY_LOCATION_PARAGRAPH_STYLE,
    JOB_DETAILS_PARAGRAPH_STYLE,
)


class Experience:
    def __init__(self, company="", title="", location="", start_date="", end_date="", description=None):
        self.company     = company
        self.title       = title
        self.location    = location
        self.start_date  = start_date
        self.end_date    = end_date
        self.description = description or []

    def set_company(self, company: str):       self.company = company
    def set_title(self, title: str):           self.title = title
    def set_location(self, location: str):     self.location = location
    def set_start_date(self, date: str):       self.start_date = date
    def set_end_date(self, date: str):         self.end_date = date
    def set_description(self, desc: list):     self.description = desc
    def append_description(self, item: str):   self.description.append(item)

    def get_table_element(self, running_row_index: list, table_styles: list) -> list:
        table = []

        # Row 1: company name (left) | date range (right)
        table.append([
            Paragraph(self.company, COMPANY_HEADING_PARAGRAPH_STYLE),
            Paragraph(f"{self.start_date} – {self.end_date}", COMPANY_DURATION_PARAGRAPH_STYLE),
        ])
        table_styles.append(("TOPPADDING",    (0, running_row_index[0]), (1, running_row_index[0]), 5))
        table_styles.append(("BOTTOMPADDING", (0, running_row_index[0]), (1, running_row_index[0]), 1))
        running_row_index[0] += 1

        # Row 2: job title (left) | location (right)
        table.append([
            Paragraph(self.title, COMPANY_TITLE_PARAGRAPH_STYLE),
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
