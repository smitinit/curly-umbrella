from reportlab.platypus import Paragraph
from src.constants.resume_constants import (
    PROJECT_PARAGRAPH_STYLE,
    COMPANY_HEADING_PARAGRAPH_STYLE,
    COMPANY_DURATION_PARAGRAPH_STYLE,
)
from src.constants import GARAMOND_SEMIBOLD


class Project:
    def __init__(self, title="", description=None, link="", start_date="", end_date=""):
        self.title       = title
        self.description = description or []
        self.link        = link
        self.start_date  = start_date
        self.end_date    = end_date

    def set_title(self, v: str):        self.title = v
    def set_description(self, v: list): self.description = v
    def set_link(self, v: str):         self.link = v
    def set_start_date(self, v: str):   self.start_date = v
    def set_end_date(self, v: str):     self.end_date = v

    def get_table_element(self, running_row_index: list, table_styles: list) -> list:
        table = []

        # Row 1: project title (left) | date range (right, optional)
        date_str = ""
        if self.start_date or self.end_date:
            date_str = f"{self.start_date} – {self.end_date}".strip(" –")

        title_text = self.title
        if self.link:
            title_text += f" <font size='9'><a href='{self.link}' color='blue'>{self.link}</a></font>"

        table.append([
            Paragraph(title_text, COMPANY_HEADING_PARAGRAPH_STYLE),
            Paragraph(date_str,   COMPANY_DURATION_PARAGRAPH_STYLE),
        ])
        table_styles.append(("TOPPADDING",    (0, running_row_index[0]), (1, running_row_index[0]), 5))
        table_styles.append(("BOTTOMPADDING", (0, running_row_index[0]), (1, running_row_index[0]), 1))
        running_row_index[0] += 1

        # Bullet rows
        for line in self.description:
            if not line:
                continue
            table.append([
                Paragraph(line, bulletText="•", style=PROJECT_PARAGRAPH_STYLE)
            ])
            table_styles.append(("TOPPADDING",    (0, running_row_index[0]), (1, running_row_index[0]), 1))
            table_styles.append(("BOTTOMPADDING", (0, running_row_index[0]), (1, running_row_index[0]), 0))
            table_styles.append(("SPAN",          (0, running_row_index[0]), (1, running_row_index[0])))
            running_row_index[0] += 1

        return table