"""Render English/Chinese student introductions from their Markdown sources.

Inputs: course introduction Markdown and configured TrueType fonts.
Outputs: matching three-page PDFs and a build/validation report in docs/teaching.
Requires uv's teaching extra and Poppler for rendering and font checks. Font
locations can be overridden with BUBBLETEA_TEACHING_FONT and
BUBBLETEA_TEACHING_BOLD_FONT; students need neither fonts nor this build script.
"""

import hashlib
import html
import json
import logging
import re
import subprocess
import sys
import xml.etree.ElementTree as xml_tree
from pathlib import Path

import markdown
from pypdf import PdfReader
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    PROJECT_ROOT,
    TEACHING_ACTIVITY_HTML,
    teaching_introduction_bold_font,
    teaching_introduction_bold_font_index,
    teaching_introduction_font,
    teaching_introduction_pdfs,
    teaching_introduction_preview,
    teaching_introduction_report,
    teaching_introduction_sources,
)

logger = logging.getLogger(__name__)
ink = HexColor("#213c34")
teal = HexColor("#126456")
muted = HexColor("#52645d")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inline_markup(node):
    """Convert only supported Markdown inline markup to ReportLab paragraphs."""
    result = html.escape(node.text or "")
    for child in node:
        inner = inline_markup(child)
        if child.tag == "strong":
            result += f"<b>{inner}</b>"
        elif child.tag == "em":
            result += f"<i>{inner}</i>"
        elif child.tag == "code":
            result += f'<font color="#126456">{inner}</font>'
        elif child.tag == "a":
            target = child.attrib["href"]
            if not target.startswith("https://"):
                raise ValueError(f"Introduction links must be portable HTTPS links: {target}")
            result += (
                f'<a href="{html.escape(target, quote=True)}" color="#126456"><u>{inner}</u></a>'
            )
        else:
            raise ValueError(f"Unsupported inline Markdown: {child.tag}")
        result += html.escape(child.tail or "")
    return result


def draw_page(canvas, document):
    canvas.saveState()
    width, height = A4
    canvas.setFillColor(teal)
    canvas.rect(44, height - 32, 32, 3, fill=1, stroke=0)
    canvas.setFont("course_bold", 8)
    canvas.drawString(86, height - 32, "BUBBLETEA / PART I / PROJECT INTRODUCTION")
    canvas.setStrokeColor(HexColor("#d7ded7"))
    canvas.line(44, 43, width - 44, 43)
    canvas.setFillColor(muted)
    canvas.setFont("course_text", 8)
    canvas.drawString(44, 29, "Gaia DR3 + Legacy Survey DR11 / 2026-10-14")
    canvas.drawRightString(width - 44, 29, f"{document.page} / 3")
    canvas.restoreState()


def build_pdf(language, source, destination):
    text = source.read_text()
    sections = text.split("<!-- pagebreak -->")
    if len(sections) != 3:
        raise ValueError("Each introduction must define three intentional page sections")
    wrap = "CJK" if language == "zh" else None
    body = ParagraphStyle(
        "body",
        fontName="course_text",
        fontSize=10.5,
        leading=15.1,
        textColor=ink,
        spaceAfter=8,
        wordWrap=wrap,
        alignment=TA_LEFT,
    )
    styles = {
        "p": body,
        "h1": ParagraphStyle(
            "title",
            parent=body,
            fontName="course_bold",
            fontSize=28,
            leading=34,
            spaceAfter=9,
            textColor=teal,
            keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "heading",
            parent=body,
            fontName="course_bold",
            fontSize=16,
            leading=21,
            spaceBefore=10,
            spaceAfter=9,
            keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "subheading",
            parent=body,
            fontName="course_bold",
            fontSize=12,
            leading=17,
            spaceBefore=9,
            spaceAfter=7,
            keepWithNext=True,
        ),
        "li": ParagraphStyle("list", parent=body, leftIndent=12, firstLineIndent=-12, spaceAfter=6),
    }
    story = []
    source_plain = []
    for section_index, section in enumerate(sections):
        root = xml_tree.fromstring(f"<document>{markdown.markdown(section)}</document>")
        plain = "".join(root.itertext())
        source_plain.append(plain)
        for font_name in ("course_text", "course_bold"):
            available = pdfmetrics.getFont(font_name).face.charToGlyph
            missing = sorted(
                {char for char in plain if not char.isspace() and ord(char) not in available}
            )
            if missing:
                raise ValueError(f"{font_name} is missing required glyphs: {missing}")
        for node in root:
            if node.tag in styles:
                story.append(Paragraph(inline_markup(node), styles[node.tag]))
            elif node.tag in ("ul", "ol"):
                for index, item in enumerate(node, 1):
                    marker = f"{index}." if node.tag == "ol" else "-"
                    story.append(Paragraph(f"<b>{marker}</b> {inline_markup(item)}", styles["li"]))
                story.append(Spacer(1, 3))
            else:
                raise ValueError(f"Unsupported Markdown block: {node.tag}")
        if section_index < 2:
            story.append(PageBreak())
    document = SimpleDocTemplate(
        str(destination),
        pagesize=A4,
        rightMargin=44,
        leftMargin=44,
        topMargin=51,
        bottomMargin=57,
        title=text.splitlines()[0].removeprefix("# ") + " | Project Introduction",
        author="BubbleTea teaching project",
        lang="zh-CN" if language == "zh" else "en",
        initialFontName="course_text",
        invariant=1,
    )
    document.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
    reader = PdfReader(destination)
    if len(reader.pages) != 3:
        raise ValueError(f"Expected 3 pages; got {len(reader.pages)} for {language}")
    page_lengths = []
    for index, (page, expected) in enumerate(zip(reader.pages, source_plain, strict=True)):
        normalized = re.sub(r"\s+", "", page.extract_text())
        expected = re.sub(r"\s+", "", expected)
        # List markers and page furniture are added by the renderer. Verify each
        # source text segment in order without relying on identical PDF line breaks.
        position = 0
        for character in expected:
            position = normalized.find(character, position)
            if position < 0:
                raise ValueError(f"Missing or reordered source text on {language} page {index + 1}")
            position += 1
        page_lengths.append(len(normalized))
    fonts = subprocess.run(
        ["pdffonts", str(destination)], check=True, text=True, capture_output=True
    ).stdout
    font_rows = fonts.splitlines()[2:]
    if not font_rows or any(line.split()[-5:-2] != ["yes", "yes", "yes"] for line in font_rows):
        raise ValueError(f"All fonts must be embedded/subset with Unicode maps:\n{fonts}")
    prefix = teaching_introduction_preview / f"project_introduction_{language}"
    subprocess.run(
        ["pdftoppm", "-scale-to", "1400", "-png", str(destination), str(prefix)], check=True
    )
    return {
        "source": str(source.relative_to(PROJECT_ROOT)),
        "source_sha256": digest(source),
        "pdf": str(destination.relative_to(PROJECT_ROOT)),
        "pdf_sha256": digest(destination),
        "pdf_bytes": destination.stat().st_size,
        "pages": len(reader.pages),
        "extracted_page_characters": page_lengths,
        "source_text_preserved_in_order": True,
        "font_report": fonts,
        "preview_prefix": str(prefix.relative_to(PROJECT_ROOT)),
    }


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    teaching_introduction_preview.mkdir(parents=True, exist_ok=True)
    for name, path in (
        ("course_text", teaching_introduction_font),
        ("course_bold", teaching_introduction_bold_font),
    ):
        if not path.is_file():
            raise FileNotFoundError(f"Configure a Unicode TrueType font for {name}: {path}")
        index = teaching_introduction_bold_font_index if name == "course_bold" else 0
        pdfmetrics.registerFont(TTFont(name, str(path), subfontIndex=index))
    pdfmetrics.registerFontFamily(
        "course_text",
        normal="course_text",
        bold="course_bold",
        italic="course_text",
        boldItalic="course_bold",
    )
    report = {
        "classroom_html_sha256": digest(TEACHING_ACTIVITY_HTML),
        "fonts": [
            {"name": path.name, "sha256": digest(path)}
            for path in (teaching_introduction_font, teaching_introduction_bold_font)
        ],
        "documents": {},
        "visual_review": "Rendered PNGs require human/agent inspection; not asserted by this script.",
    }
    for language, source in teaching_introduction_sources.items():
        report["documents"][language] = build_pdf(
            language, source, teaching_introduction_pdfs[language]
        )
        logger.info("Built and rendered %s introduction: 3 pages", language)
    teaching_introduction_report.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
