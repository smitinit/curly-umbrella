from reportlab.platypus import Paragraph
from src.constants.resume_constants import JOB_DETAILS_PARAGRAPH_STYLE


class Certification:
    def __init__(self, title="", link=""):
        self.title = title
        self.link  = link

    def set_title(self, v: str): self.title = v
    def set_link(self, v: str):  self.link = v

    def get_table_element(self, running_row_index: list, table_styles: list) -> list:
        table = []
        link_part = f" {self.link}" if self.link else ""
        table.append([
            Paragraph(f"{self.title}{link_part}", bulletText="•", style=JOB_DETAILS_PARAGRAPH_STYLE)
        ])
        table_styles.append(("TOPPADDING",    (0, running_row_index[0]), (1, running_row_index[0]), 1))
        table_styles.append(("BOTTOMPADDING", (0, running_row_index[0]), (1, running_row_index[0]), 0))
        table_styles.append(("SPAN",          (0, running_row_index[0]), (1, running_row_index[0])))
        running_row_index[0] += 1
        return table
