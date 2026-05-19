from reportlab.platypus import Paragraph
from src.constants.resume_constants import SECTION_PARAGRAPH_STYLE, append_section_table_style


class Section:
    def __init__(self, heading: str, elements=None):
        self.heading  = heading
        self.elements = elements or []

    def set_elements(self, elements: list): self.elements = elements
    def add_element(self, element):         self.elements.append(element)

    def get_section_table(self, running_row_index: list, table_styles: list) -> list:
        section_table = []

        # Section heading row with underline
        section_table.append([Paragraph(self.heading, SECTION_PARAGRAPH_STYLE)])
        append_section_table_style(table_styles, running_row_index)
        running_row_index[0] += 1

        # All elements under this section
        for element in self.elements:
            for row in element.get_table_element(running_row_index, table_styles):
                section_table.append(row)

        return section_table
