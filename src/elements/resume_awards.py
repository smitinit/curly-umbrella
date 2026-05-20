from reportlab.platypus import Paragraph
from src.constants.resume_constants import (
    COMPANY_HEADING_PARAGRAPH_STYLE,
    COMPANY_DURATION_PARAGRAPH_STYLE,
    JOB_DETAILS_PARAGRAPH_STYLE,
)


class Award:
    def __init__(self, title="", issuer="", date="", description=""):
        self.title       = title
        self.issuer      = issuer
        self.date        = date
        self.description = description

    def set_title(self, v: str):       self.title = v
    def set_issuer(self, v: str):      self.issuer = v
    def set_date(self, v: str):        self.date = v
    def set_description(self, v: str): self.description = v

    def get_table_element(self, running_row_index: list, table_styles: list) -> list:
        table = []

        # Row 1: award title (left) | date (right)
        table.append([
            Paragraph(self.title,  COMPANY_HEADING_PARAGRAPH_STYLE),
            Paragraph(self.date,   COMPANY_DURATION_PARAGRAPH_STYLE),
        ])
        table_styles.append(("TOPPADDING",    (0, running_row_index[0]), (1, running_row_index[0]), 5))
        table_styles.append(("BOTTOMPADDING", (0, running_row_index[0]), (1, running_row_index[0]), 1))
        running_row_index[0] += 1

        # Row 2: issuer (optional)
        if self.issuer:
            table.append([
                Paragraph(self.issuer, JOB_DETAILS_PARAGRAPH_STYLE)
            ])
            table_styles.append(("TOPPADDING",    (0, running_row_index[0]), (1, running_row_index[0]), 1))
            table_styles.append(("BOTTOMPADDING", (0, running_row_index[0]), (1, running_row_index[0]), 1))
            table_styles.append(("SPAN",          (0, running_row_index[0]), (1, running_row_index[0])))
            running_row_index[0] += 1

        # Row 3: description (optional)
        if self.description:
            table.append([
                Paragraph(self.description, bulletText="•", style=JOB_DETAILS_PARAGRAPH_STYLE)
            ])
            table_styles.append(("TOPPADDING",    (0, running_row_index[0]), (1, running_row_index[0]), 1))
            table_styles.append(("BOTTOMPADDING", (0, running_row_index[0]), (1, running_row_index[0]), 0))
            table_styles.append(("SPAN",          (0, running_row_index[0]), (1, running_row_index[0])))
            running_row_index[0] += 1

        return table