from reportlab.platypus import Paragraph
from src.constants.resume_constants import JOB_DETAILS_PARAGRAPH_STYLE
from src.constants import GARAMOND_SEMIBOLD


class Skill:
    def __init__(self, title="", elements=None):
        self.title    = title
        self.elements = elements or []

    def set_title(self, v: str):       self.title = v
    def set_elements(self, v: list):   self.elements = v
    def append_element(self, v: str):  self.elements.append(v)

    def get_table_element(self, running_row_index: list, table_styles: list) -> list:
        table = []
        items = ", ".join(e for e in self.elements if e)
        table.append([
            Paragraph(
                f"<font face='{GARAMOND_SEMIBOLD}'>{self.title}:</font> {items}",
                bulletText="•",
                style=JOB_DETAILS_PARAGRAPH_STYLE,
            )
        ])
        table_styles.append(("TOPPADDING",    (0, running_row_index[0]), (1, running_row_index[0]), 1))
        table_styles.append(("BOTTOMPADDING", (0, running_row_index[0]), (1, running_row_index[0]), 0))
        table_styles.append(("SPAN",          (0, running_row_index[0]), (1, running_row_index[0])))
        running_row_index[0] += 1
        return table
