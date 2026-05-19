"""
main.py
-------
Reads resume JSON and generates an ATS-friendly resume PDF.

If --input points to a PDF, the script extracts the text, asks OpenAI to
convert it into the structured resume JSON schema, writes that JSON to disk,
and then renders the PDF from the generated JSON.

Usage:
    cd src/
    python3 main.py
    python3 main.py --input data/input.json --output my_resume.pdf
    python3 main.py --input data/resume.pdf --json-output data/input.json
"""

import sys
import os
import json
import argparse
import base64
from pathlib import Path
from typing import Optional, Tuple

# Make sure imports resolve from src/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer

from src.constants import FULL_COLUMN_WIDTH
from src.constants.resume_constants import (
    RESUME_ELEMENTS_ORDER,
    NAME_PARAGRAPH_STYLE,
    TITLE_PARAGRAPH_STYLE,
    CONTACT_PARAGRAPH_STYLE,
    append_section_table_style,
)

from src.elements.resume_experience    import Experience
from src.elements.resume_education     import Education
from src.elements.resume_skill         import Skill
from src.elements.resume_project       import Project
from src.elements.resume_achievement   import Achievement
from src.elements.resume_certification import Certification
from src.sections.resume_section       import Section


def resolve_path(path_value: str, base_dir: str) -> str:
    if os.path.isabs(path_value):
        return os.path.normpath(path_value)
    return os.path.normpath(os.path.join(base_dir, path_value))


def extract_pdf_text(pdf_path: str) -> str:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError(
            "PyMuPDF is required to extract text from PDF input. Install dependencies with `pip install -r requirements.txt`."
        ) from exc

    chunks = []
    with fitz.open(pdf_path) as document:
        for page in document:
            page_text = page.get_text("text").strip()
            if page_text:
                chunks.append(page_text)

    return "\n\n".join(chunks)


def strip_json_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else ""
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
    return cleaned.strip()


def generate_resume_json_from_text(raw_text: str, output_json_path: str) -> dict:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError(
            "The openai package is required for PDF-to-JSON generation. Install dependencies with `pip install -r requirements.txt`."
        ) from exc

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set. Add it to your .env file.")

    client = OpenAI(api_key=api_key)
    model = os.environ.get("OPENAI_MODEL", "gpt-5.4-mini")

    prompt = (
        "Convert the following resume text into valid JSON for this schema:\n"
        "{\n"
        '  "personal": {"name": "", "title": "", "email": "", "phone": "", "location": "", "website": "", "website_text": "", "linkedin": "", "linkedin_text": ""},\n'
        '  "skills": [{"title": "", "elements": []}],\n'
        '  "projects": [{"title": "", "description": "", "link": ""}],\n'
        '  "experience": [{"title": "", "company": "", "location": "", "start_date": "", "end_date": "", "description": []}],\n'
        '  "education": [{"institution": "", "course": "", "location": "", "start_date": "", "end_date": ""}],\n'
        '  "achievements": [{"title": ""}],\n'
        '  "certifications": [{"title": "", "link": ""}]\n'
        "}\n\n"
        "Rules:\n"
        "- Return JSON only, no markdown fences or commentary.\n"
        "- Preserve the original meaning and dates where possible.\n"
        "- Use empty strings or empty arrays when information is missing.\n"
        "- If the PDF contains multiple sections, infer the best matching section for each item.\n\n"
        f"Resume text:\n{raw_text}"
    )

    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": "You convert resume text into structured JSON."},
            {"role": "user", "content": prompt},
        ],
    )

    response_text = getattr(response, "output_text", "") or ""
    if not response_text:
        raise RuntimeError("OpenAI returned an empty response while generating resume JSON.")

    data = json.loads(strip_json_fences(response_text))

    with open(output_json_path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)

    return data


def load_resume_data(input_path: str, json_output_path: Optional[str] = None) -> Tuple[dict, Optional[str]]:
    if input_path.lower().endswith(".pdf"):
        raw_text = extract_pdf_text(input_path)
        if not raw_text:
            raise RuntimeError(f"No extractable text was found in PDF: {input_path}")

        generated_json_path = json_output_path or str(Path(input_path).with_suffix(".json"))
        data = generate_resume_json_from_text(raw_text, generated_json_path)
        return data, generated_json_path

    with open(input_path, "r", encoding="utf-8") as handle:
        return json.load(handle), None


# ── Builders ──────────────────────────────────────────────────────────────────

def build_experience(data: dict) -> Experience:
    e = Experience()
    e.set_company(data["company"])
    e.set_title(data["title"])
    e.set_location(data["location"])
    e.set_start_date(data["start_date"])
    e.set_end_date(data["end_date"])
    e.set_description(data["description"])
    return e

def build_education(data: dict) -> Education:
    e = Education()
    e.set_institution(data["institution"])
    e.set_course(data["course"])
    e.set_location(data["location"])
    e.set_start_date(data["start_date"])
    e.set_end_date(data["end_date"])
    return e

def build_skill(data: dict) -> Skill:
    s = Skill()
    s.set_title(data["title"])
    s.set_elements(data["elements"])
    return s

def build_project(data: dict) -> Project:
    p = Project()
    p.set_title(data["title"])
    p.set_description(data["description"])
    p.set_link(data.get("link", ""))
    return p

def build_achievement(data: dict) -> Achievement:
    a = Achievement()
    a.set_title(data["title"])
    return a

def build_certification(data: dict) -> Certification:
    c = Certification()
    c.set_title(data["title"])
    c.set_link(data.get("link", ""))
    return c


def build_resume_pdf(data: dict, output: str) -> None:
    personal = data.get("personal", {})
    name = personal.get("name", "Resume")

    email = personal.get("email", "")
    phone = personal.get("phone", "")
    location = personal.get("location", "")
    website = personal.get("website", "")
    website_txt = personal.get("website_text", website)
    linkedin = personal.get("linkedin", "")
    linkedin_txt = personal.get("linkedin_text", linkedin)

    contact_parts = []
    if email:
        contact_parts.append(email)
    if phone:
        contact_parts.append(phone)
    if location:
        contact_parts.append(location)
    if website:
        contact_parts.append(f"<a href='{website}' color='blue'>{website_txt}</a>")
    if linkedin:
        contact_parts.append(f"<a href='{linkedin}' color='blue'>{linkedin_txt}</a>")
    contact_line = " | ".join(contact_parts)

    resume_data = {}
    table = []
    table_styles = []
    running_row_index = [0]

    table_styles += [
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]

    table.append([Paragraph(name, NAME_PARAGRAPH_STYLE)])
    table_styles.append(("SPAN", (0, running_row_index[0]), (1, running_row_index[0])))
    table_styles.append(("BOTTOMPADDING", (0, running_row_index[0]), (1, running_row_index[0]), 1))
    table_styles.append(("TOPPADDING", (0, running_row_index[0]), (1, running_row_index[0]), 0))
    running_row_index[0] += 1

    job_title = personal.get("title", "")
    if job_title:
        table.append([Paragraph(job_title, TITLE_PARAGRAPH_STYLE)])
        table_styles.append(("SPAN", (0, running_row_index[0]), (1, running_row_index[0])))
        table_styles.append(("BOTTOMPADDING", (0, running_row_index[0]), (1, running_row_index[0]), 1))
        table_styles.append(("TOPPADDING", (0, running_row_index[0]), (1, running_row_index[0]), 0))
        running_row_index[0] += 1

    table.append([Paragraph(contact_line, CONTACT_PARAGRAPH_STYLE)])
    table_styles.append(("SPAN", (0, running_row_index[0]), (1, running_row_index[0])))
    table_styles.append(("BOTTOMPADDING", (0, running_row_index[0]), (1, running_row_index[0]), 4))
    table_styles.append(("TOPPADDING", (0, running_row_index[0]), (1, running_row_index[0]), 0))
    running_row_index[0] += 1

    builders = {
        "experience": (data.get("experience", []), build_experience),
        "education": (data.get("education", []), build_education),
        "skills": (data.get("skills", []), build_skill),
        "projects": (data.get("projects", []), build_project),
        "achievements": (data.get("achievements", []), build_achievement),
        "certifications": (data.get("certifications", []), build_certification),
    }

    for key, (items, builder) in builders.items():
        if items:
            elements = [builder(item) for item in items]
            resume_data[key] = Section(key.capitalize(), elements)

    for key in RESUME_ELEMENTS_ORDER:
        if key in resume_data:
            for row in resume_data[key].get_section_table(running_row_index, table_styles):
                table.append(row)

    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
        topMargin=0.3 * inch,
        bottomMargin=0.2 * inch,
        title=f"Resume – {name}",
        author=name,
    )

    main_table = Table(
        table,
        colWidths=[FULL_COLUMN_WIDTH * 0.70, FULL_COLUMN_WIDTH * 0.30],
        spaceBefore=0,
        spaceAfter=0,
    )
    main_table.setStyle(TableStyle(table_styles))

    doc.build([main_table])


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate an ATS-friendly resume PDF from JSON or PDF input.")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_input = os.path.join(script_dir, "data", "input.json")
    parser.add_argument("--input",  default=default_input, help="Path to input JSON or PDF")
    parser.add_argument("--json-output", default="", help="Where to write generated JSON when the input is a PDF")
    parser.add_argument("--output", default="", help="Output PDF path")
    args = parser.parse_args()

    input_path = resolve_path(args.input, os.getcwd())
    json_output_path = resolve_path(args.json_output, os.getcwd()) if args.json_output else None

    # Load data from JSON directly, or generate it from a PDF first.
    data, generated_json_path = load_resume_data(input_path, json_output_path)
    personal = data.get("personal", {})
    name = personal.get("name", "Resume")
    output = args.output or f"{name.lower().replace(' ', '_')}_resume.pdf"

    build_resume_pdf(data, output)
    print(f"✓ Resume saved: {output}")
    if generated_json_path:
        print(f"✓ Generated JSON saved: {generated_json_path}")


if __name__ == "__main__":
    main()
