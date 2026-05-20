"""
main.py
-------
Reads resume JSON and generates an ATS-friendly resume PDF.

If --input points to a PDF, the script extracts the text, asks OpenAI to
convert it into the structured resume JSON schema, writes that JSON to disk,
and then renders the PDF from the generated JSON.

Usage:
    python3 main.py
    python3 main.py --input data/input.json --output my_resume.pdf
    python3 main.py --input data/resume.pdf --json-output data/input.json
"""

import sys
import os
import json
import argparse
from pathlib import Path
from typing import Optional, Tuple

# Make sure imports resolve from project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle

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
from src.elements.resume_summary       import Summary
from src.elements.resume_languages     import Language
from src.elements.resume_awards        import Award
from src.elements.resume_volunteering  import Volunteering
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
            "PyMuPDF is required to extract text from PDF input. "
            "Install dependencies with `pip install -r requirements.txt`."
        ) from exc

    chunks = []
    with fitz.open(pdf_path) as document:
        for page in document:
            page_text = page.get_text("text").strip()
            if page_text:
                chunks.append(page_text)

    return "\n\n".join(chunks)


def strip_json_fences(text: str) -> str:
    import re
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else ""
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    # Remove trailing commas before } or ] (common OpenAI JSON mistake)
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
    return cleaned


def generate_resume_json_from_text(raw_text: str, output_json_path: str) -> dict:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError(
            "The openai package is required for PDF-to-JSON generation. "
            "Install dependencies with `pip install -r requirements.txt`."
        ) from exc

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set. Add it to your .env file.")

    client = OpenAI(api_key=api_key)
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    prompt = (
        "You are a senior ATS resume specialist and career coach with 20+ years of experience. "
        "Convert the following resume text into structured JSON using the schema below.\n\n"
        "SCHEMA:\n"
        "{\n"
        '  "personal": {"name": "", "title": "", "email": "", "phone": "", "location": "", "website": "", "website_text": "", "linkedin": "", "linkedin_text": ""},\n'
        '  "summary": "",\n'
        '  "skills": [{"title": "", "elements": []}],\n'
        '  "experience": [{"title": "", "company": "", "location": "", "start_date": "", "end_date": "", "description": []}],\n'
        '  "projects": [{"title": "", "description": [""], "link": "", "start_date": "", "end_date": ""}],\n'
        '  "education": [{"institution": "", "course": "", "location": "", "start_date": "", "end_date": ""}],\n'
        '  "certifications": [{"title": "", "link": ""}],\n'
        '  "awards": [{"title": "", "issuer": "", "date": "", "description": ""}],\n'
        '  "volunteering": [{"organization": "", "role": "", "location": "", "start_date": "", "end_date": "", "description": []}],\n'
        '  "languages": [{"name": "", "proficiency": ""}],\n'
        '  "achievements": [{"title": ""}]\n'
        "}\n\n"
        "ATS & QUALITY RULES — apply every single one:\n"
        "- NEVER invent, fabricate, or exaggerate any skill, tool, metric, or experience not in the original.\n"
        "- NEVER summarize, compress, or shorten any bullet point — preserve all original detail.\n"
        "- Rewrite every bullet to start with a strong action verb: Led, Built, Designed, Optimized, Delivered, Reduced, Increased, Implemented, Engineered, Automated. Never use 'Responsible for' or 'Worked on'.\n"
        "- If a bullet already contains a metric (%, $, numbers) — keep it exactly as-is.\n"
        "- If a bullet lacks a metric — rewrite it to be outcome-focused but DO NOT invent numbers.\n"
        "- Remove all filler words: proactive, passionate, team player, results-oriented, dynamic, hardworking, detail-oriented, go-getter.\n"
        "- No repetition — if the same tool or skill appears across multiple bullets, vary the framing.\n"
        "- Keep each bullet under 25 words, tight and scannable.\n"
        "- Summary: 2-3 sentences, factual, no buzzwords, demonstrates seniority and value. Never start with 'I am a passionate...'.\n"
        "- Skills: group by category, list tools/technologies exactly as they appear in the source.\n"
        "- Projects: split each feature or responsibility into its own bullet — never merge into one paragraph.\n"
        "- Dates: use consistent format 'Mon YYYY' (e.g. Jan 2023). Use 'Present' for current roles.\n"
        "- Use empty strings or empty arrays when a section has no data — never omit keys.\n"
        "- Return JSON only — no markdown fences, no commentary, no trailing commas.\n\n"
        f"RESUME TEXT:\n{raw_text}"
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You convert resume text into structured JSON."},
            {"role": "user",   "content": prompt},
        ],
    )

    response_text = response.choices[0].message.content or ""
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
    desc = data.get("description", [])
    if isinstance(desc, str):
        desc = [desc] if desc else []
    p.set_description(desc)
    p.set_link(data.get("link", ""))
    p.set_start_date(data.get("start_date", ""))
    p.set_end_date(data.get("end_date", ""))
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

def build_summary(text: str) -> Summary:
    s = Summary()
    s.set_text(text)
    return s

def build_language(data: dict) -> Language:
    l = Language()
    l.set_name(data["name"])
    l.set_proficiency(data.get("proficiency", ""))
    return l

def build_award(data: dict) -> Award:
    a = Award()
    a.set_title(data["title"])
    a.set_issuer(data.get("issuer", ""))
    a.set_date(data.get("date", ""))
    a.set_description(data.get("description", ""))
    return a

def build_volunteering(data: dict) -> Volunteering:
    v = Volunteering()
    v.set_organization(data["organization"])
    v.set_role(data["role"])
    v.set_location(data.get("location", ""))
    v.set_start_date(data.get("start_date", ""))
    v.set_end_date(data.get("end_date", ""))
    v.set_description(data.get("description", []))
    return v


def build_resume_pdf(data: dict, output: str) -> None:
    personal = data.get("personal", {})
    name     = personal.get("name", "Resume")

    email        = personal.get("email", "")
    phone        = personal.get("phone", "")
    location     = personal.get("location", "")
    website      = personal.get("website", "")
    website_txt  = personal.get("website_text", website)
    linkedin     = personal.get("linkedin", "")
    linkedin_txt = personal.get("linkedin_text", linkedin)

    contact_parts = []
    if email:    contact_parts.append(email)
    if phone:    contact_parts.append(phone)
    if location: contact_parts.append(location)
    if website:  contact_parts.append(f"<a href='{website}' color='blue'>{website_txt}</a>")
    if linkedin: contact_parts.append(f"<a href='{linkedin}' color='blue'>{linkedin_txt}</a>")
    contact_line = " | ".join(contact_parts)

    resume_data    = {}
    table          = []
    table_styles   = []
    running_row_index = [0]

    table_styles += [
        ("ALIGN",        (0, 0), (0, -1), "LEFT"),
        ("ALIGN",        (1, 0), (1, -1), "RIGHT"),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]

    # ── Header ────────────────────────────────────────────────────────────────
    table.append([Paragraph(name, NAME_PARAGRAPH_STYLE)])
    table_styles.append(("SPAN",          (0, running_row_index[0]), (1, running_row_index[0])))
    table_styles.append(("BOTTOMPADDING", (0, running_row_index[0]), (1, running_row_index[0]), 1))
    table_styles.append(("TOPPADDING",    (0, running_row_index[0]), (1, running_row_index[0]), 0))
    running_row_index[0] += 1

    job_title = personal.get("title", "")
    if job_title:
        table.append([Paragraph(job_title, TITLE_PARAGRAPH_STYLE)])
        table_styles.append(("SPAN",          (0, running_row_index[0]), (1, running_row_index[0])))
        table_styles.append(("BOTTOMPADDING", (0, running_row_index[0]), (1, running_row_index[0]), 1))
        table_styles.append(("TOPPADDING",    (0, running_row_index[0]), (1, running_row_index[0]), 0))
        running_row_index[0] += 1

    table.append([Paragraph(contact_line, CONTACT_PARAGRAPH_STYLE)])
    table_styles.append(("SPAN",          (0, running_row_index[0]), (1, running_row_index[0])))
    table_styles.append(("BOTTOMPADDING", (0, running_row_index[0]), (1, running_row_index[0]), 4))
    table_styles.append(("TOPPADDING",    (0, running_row_index[0]), (1, running_row_index[0]), 0))
    running_row_index[0] += 1

    # ── Summary (single item, not a list) ─────────────────────────────────────
    summary_text = data.get("summary", "")
    if summary_text:
        resume_data["summary"] = Section("Summary", [build_summary(summary_text)])

    # ── List-based sections ───────────────────────────────────────────────────
    list_builders = {
        "experience":    (data.get("experience",    []), build_experience),
        "education":     (data.get("education",     []), build_education),
        "skills":        (data.get("skills",        []), build_skill),
        "projects":      (data.get("projects",      []), build_project),
        "certifications":(data.get("certifications",[]), build_certification),
        "awards":        (data.get("awards",        []), build_award),
        "volunteering":  (data.get("volunteering",  []), build_volunteering),
        "languages":     (data.get("languages",     []), build_language),
        "achievements":  (data.get("achievements",  []), build_achievement),
    }

    for key, (items, builder) in list_builders.items():
        if items:
            resume_data[key] = Section(key.capitalize(), [builder(item) for item in items])

    # ── Render in order ───────────────────────────────────────────────────────
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


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate an ATS-friendly resume PDF from JSON or PDF input.")
    script_dir    = os.path.dirname(os.path.abspath(__file__))
    default_input = os.path.join(script_dir, "data", "input.json")
    parser.add_argument("--input",       default=default_input, help="Path to input JSON or PDF")
    parser.add_argument("--json-output", default="",            help="Where to write generated JSON when the input is a PDF")
    parser.add_argument("--output",      default="",            help="Output PDF path")
    args = parser.parse_args()

    input_path       = resolve_path(args.input, os.getcwd())
    json_output_path = resolve_path(args.json_output, os.getcwd()) if args.json_output else None

    data, generated_json_path = load_resume_data(input_path, json_output_path)
    personal = data.get("personal", {})
    name     = personal.get("name", "Resume")
    output   = args.output or f"{name.lower().replace(' ', '_')}_resume.pdf"

    build_resume_pdf(data, output)
    print(f"✓ Resume saved: {output}")
    if generated_json_path:
        print(f"✓ Generated JSON saved: {generated_json_path}")


if __name__ == "__main__":
    main()