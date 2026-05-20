from reportlab.platypus import Paragraph
from src.constants.resume_constants import JOB_DETAILS_PARAGRAPH_STYLE
from src.constants import GARAMOND_SEMIBOLD


class Language:
    def __init__(self, name="", proficiency=""):
        self.name        = name
        self.proficiency = proficiency

    def set_name(self, v: str):        self.name = v
    def set_proficiency(self, v: str): self.proficiency = v

    def get_table_element(self, running_row_index: list, table_styles: list) -> list:
        table = []
        proficiency_part = f": {self.proficiency}" if self.proficiency else ""
        table.append([
            Paragraph(
                f"<font face='{GARAMOND_SEMIBOLD}'>{self.name}</font>{proficiency_part}",
                bulletText="•",
                style=JOB_DETAILS_PARAGRAPH_STYLE,
            )
        ])
        table_styles.append(("TOPPADDING",    (0, running_row_index[0]), (1, running_row_index[0]), 1))
        table_styles.append(("BOTTOMPADDING", (0, running_row_index[0]), (1, running_row_index[0]), 0))
        table_styles.append(("SPAN",          (0, running_row_index[0]), (1, running_row_index[0])))
        running_row_index[0] += 1
        return table