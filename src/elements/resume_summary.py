from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from src.constants import GARAMOND_REGULAR

SUMMARY_PARAGRAPH_STYLE = ParagraphStyle(
    "summary_paragraph",
    fontName=GARAMOND_REGULAR,
    fontSize=10,
    leading=13,
    leftIndent=0,
    alignment=TA_JUSTIFY,
)


class Summary:
    def __init__(self, text=""):
        self.text = text

    def set_text(self, v: str): self.text = v

    def get_table_element(self, running_row_index: list, table_styles: list) -> list:
        table = []
        table.append([
            Paragraph(self.text, style=SUMMARY_PARAGRAPH_STYLE)
        ])
        table_styles.append(("TOPPADDING",    (0, running_row_index[0]), (1, running_row_index[0]), 2))
        table_styles.append(("BOTTOMPADDING", (0, running_row_index[0]), (1, running_row_index[0]), 2))
        table_styles.append(("SPAN",          (0, running_row_index[0]), (1, running_row_index[0])))
        running_row_index[0] += 1
        return table