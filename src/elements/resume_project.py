from reportlab.platypus import Paragraph
from src.constants.resume_constants import PROJECT_PARAGRAPH_STYLE
from src.constants import GARAMOND_SEMIBOLD


class Project:
    def __init__(self, title="", description="", link=""):
        self.title       = title
        self.description = description
        self.link        = link

    def set_title(self, v: str):       self.title = v
    def set_description(self, v: str): self.description = v
    def set_link(self, v: str):        self.link = v

    def get_table_element(self, running_row_index: list, table_styles: list) -> list:
        table = []
        link_part = f" {self.link}" if self.link else ""
        table.append([
            Paragraph(
                f"<font face='{GARAMOND_SEMIBOLD}'>{self.title}:</font> {self.description}{link_part}",
                bulletText="•",
                style=PROJECT_PARAGRAPH_STYLE,
            )
        ])
        table_styles.append(("TOPPADDING",    (0, running_row_index[0]), (1, running_row_index[0]), 1))
        table_styles.append(("BOTTOMPADDING", (0, running_row_index[0]), (1, running_row_index[0]), 0))
        table_styles.append(("SPAN",          (0, running_row_index[0]), (1, running_row_index[0])))
        running_row_index[0] += 1
        return table
