from reportlab.platypus import Paragraph
from src.constants.resume_constants import (
    COMPANY_HEADING_PARAGRAPH_STYLE,
    COMPANY_DURATION_PARAGRAPH_STYLE,
    COMPANY_TITLE_PARAGRAPH_STYLE,
    COMPANY_LOCATION_PARAGRAPH_STYLE,
)


class Education:
    def __init__(self, institution="", course="", location="", start_date="", end_date=""):
        self.institution = institution
        self.course      = course
        self.location    = location
        self.start_date  = start_date
        self.end_date    = end_date

    def set_institution(self, v: str): self.institution = v
    def set_course(self, v: str):      self.course = v
    def set_location(self, v: str):    self.location = v
    def set_start_date(self, v: str):  self.start_date = v
    def set_end_date(self, v: str):    self.end_date = v

    def get_table_element(self, running_row_index: list, table_styles: list) -> list:
        table = []

        table.append([
            Paragraph(self.institution, COMPANY_HEADING_PARAGRAPH_STYLE),
            Paragraph(f"{self.start_date} – {self.end_date}", COMPANY_DURATION_PARAGRAPH_STYLE),
        ])
        table_styles.append(("TOPPADDING",    (0, running_row_index[0]), (1, running_row_index[0]), 5))
        table_styles.append(("BOTTOMPADDING", (0, running_row_index[0]), (1, running_row_index[0]), 1))
        running_row_index[0] += 1

        table.append([
            Paragraph(self.course, COMPANY_TITLE_PARAGRAPH_STYLE),
            Paragraph(self.location, COMPANY_LOCATION_PARAGRAPH_STYLE),
        ])
        table_styles.append(("TOPPADDING",    (0, running_row_index[0]), (1, running_row_index[0]), 1))
        table_styles.append(("BOTTOMPADDING", (0, running_row_index[0]), (1, running_row_index[0]), 3))
        running_row_index[0] += 1

        return table
