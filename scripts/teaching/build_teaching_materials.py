"""Build a self-contained local-file activity and a six-page printable PDF worksheet.

Inputs: versioned teaching packet, cached JPEGs, worksheet/background/tool Markdown,
and repository-native HTML/CSS/JavaScript assets. Outputs stay under docs/teaching/.
No network, catalog/database writes, web hosting, or student-answer access occurs.
"""

import base64
import hashlib
import html
import json
import logging
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlencode

import markdown
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    TEACHING_ASSETS_DIR,
    TEACHING_BUILD_REPORT,
    TEACHING_DIR,
    TEACHING_DOWNLOAD_DIR,
    TEACHING_PACKET,
    TEACHING_WORKSHEET_PDF,
)
from scripts.config import (
    teaching_previous_html as TEACHING_ACTIVITY_HTML,
)

logger = logging.getLogger(__name__)
review_fields = [
    {"key": "resolved", "label": "Visibly resolved"},
    {"key": "off_center", "label": "Off-center / possible mismatch"},
    {"key": "close_to_host_light", "label": "Close to host light"},
    {"key": "nearby_blend", "label": "Blend with a nearby source"},
    {"key": "too_faint", "label": "Too faint to assess"},
    {"key": "image_problem", "label": "Image problem / artifact"},
]
ink = colors.HexColor("#233c3a")
green = colors.HexColor("#126456")
paper = colors.HexColor("#f4f0e5")
styles = {
    "title": ParagraphStyle(
        "title", fontName="Times-Roman", fontSize=30, leading=33, textColor=ink, spaceAfter=14
    ),
    "heading": ParagraphStyle(
        "heading", fontName="Times-Roman", fontSize=20, leading=23, textColor=ink, spaceAfter=10
    ),
    "body": ParagraphStyle(
        "body", fontName="Helvetica", fontSize=10, leading=14, spaceAfter=8, textColor=ink
    ),
    "small": ParagraphStyle(
        "small", fontName="Helvetica", fontSize=8, leading=10, spaceAfter=5, textColor=ink
    ),
    "cell": ParagraphStyle("cell", fontName="Helvetica", fontSize=8.5, leading=11, textColor=ink),
    "center": ParagraphStyle(
        "center", fontName="Helvetica", fontSize=8, leading=10, alignment=TA_CENTER, textColor=ink
    ),
}


def paragraph(text: str, style: str = "body") -> Paragraph:
    """Normalize unsupported punctuation without losing scientific units or identifiers."""
    for character in ["\u2010", "\u2011", "\u2012", "\u2013", "\u2014", "\u2212"]:
        text = text.replace(character, "-")
    text = (
        text.replace("×", "x")
        .replace("↗", "")
        .replace("“", '"')
        .replace("”", '"')
        .replace("’", "'")
    )
    return Paragraph(html.escape(text), styles[style])


def table(rows: list[list[str]], widths: list[float]) -> Table:
    result = Table(
        [[paragraph(str(cell), "cell") for cell in row] for row in rows],
        colWidths=widths,
        hAlign="LEFT",
    )
    result.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), paper),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, -1), 0.35, colors.HexColor("#c9cfc1")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return result


def formatted(value: float | None, digits: int = 3) -> str:
    return "Not supplied" if value is None else f"{value:.{digits}f}"


def with_error(gaia: dict, field: str) -> str:
    return (
        "Not supplied"
        if gaia[field] is None
        else f"{gaia[field]:.3f} +/- {gaia[field + '_error']:.3f}"
    )


def questions_from_markdown() -> list[dict]:
    source = (TEACHING_DIR / "worksheet.md").read_text()
    matches = re.findall(
        r"^- \*\*(Q\d)\.\*\* (.*?)(?=\n- |\n## |\Z)", source, re.MULTILINE | re.DOTALL
    )
    questions = [
        {"key": key.lower(), "prompt": " ".join(text.replace("`", "").split())}
        for key, text in matches
    ]
    if [question["key"] for question in questions] != [f"q{index}" for index in range(1, 9)]:
        raise RuntimeError("Worksheet must define exactly Q1 through Q8")
    return questions


def offline_markdown(path: Path) -> str:
    """Keep optional online citations but remove repository-relative links from the file."""
    rendered = markdown.markdown(path.read_text(), extensions=["tables", "fenced_code"])
    return re.sub(r'<a href="(?!https?://)[^"]*">(.*?)</a>', r"\1", rendered, flags=re.DOTALL)


def load_packet() -> dict:
    packet = json.loads(TEACHING_PACKET.read_text())
    packet["packet_sha256"] = hashlib.sha256(TEACHING_PACKET.read_bytes()).hexdigest()
    packet["questions"] = questions_from_markdown()
    packet["review_fields"] = review_fields
    if len(packet["objects"]) != 6:
        raise RuntimeError("The classroom packet must contain six checked identifiers")
    for record in packet["objects"]:
        if not isinstance(record["source_id"], str) or len(record["source_id"]) != 19:
            raise RuntimeError("Gaia identifiers must remain exact strings")
        record["viewer_url"] = "https://www.legacysurvey.org/viewer?" + urlencode(
            {
                "ra": record["gaia"]["ra"],
                "dec": record["gaia"]["dec"],
                "layer": "ls-dr11",
                "zoom": 17,
            }
        )
        for image in record["images"].values():
            path = (TEACHING_DOWNLOAD_DIR / image["cache_file"]).resolve()
            if not path.is_relative_to(TEACHING_DOWNLOAD_DIR.resolve()):
                raise RuntimeError("Image path escaped configured teaching cache")
            content = path.read_bytes()
            if hashlib.sha256(content).hexdigest() != image["sha256"]:
                raise RuntimeError(f"Image digest mismatch: {path.name}")
            image["data_url"] = "data:image/jpeg;base64," + base64.b64encode(content).decode()
    return packet


def build_html(packet: dict) -> None:
    template = (TEACHING_ASSETS_DIR / "activity.html").read_text()
    substitutions = {
        "__STYLE__": (TEACHING_ASSETS_DIR / "activity.css").read_text(),
        "__SCRIPT__": (TEACHING_ASSETS_DIR / "activity.js").read_text(),
        "__BACKGROUND__": offline_markdown(TEACHING_DIR / "concepts.md"),
        "__GUIDE__": offline_markdown(TEACHING_DIR / "tool_guide.md"),
        "__PACKET__": json.dumps(packet, ensure_ascii=True).replace("</", "<\\/"),
    }
    for marker, content in substitutions.items():
        template = template.replace(marker, content)
    if any(marker in template for marker in substitutions):
        raise RuntimeError("Unresolved HTML template marker")
    TEACHING_ACTIVITY_HTML.write_text(template)


def build_pdf(packet: dict) -> None:
    width = A4[0] - 32 * mm
    document = SimpleDocTemplate(
        str(TEACHING_WORKSHEET_PDF),
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=21 * mm,
        bottomMargin=18 * mm,
        title="A star in disguise? - Student worksheet",
        author="BubbleTea observational astronomy",
    )
    story = []
    lookup = {record["object_key"]: record for record in packet["objects"]}
    questions = {question["key"]: question["prompt"] for question in packet["questions"]}

    def answer_space(lines: int = 2) -> None:
        blank = Table([[""] for _ in range(lines)], colWidths=[width], rowHeights=16)
        blank.setStyle(
            TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#bdc6bc"))])
        )
        story.extend([blank, Spacer(1, 7)])

    def question(key: str, lines: int = 2) -> None:
        story.append(paragraph(f"{key.upper()}. {questions[key]}"))
        answer_space(lines)

    def photo(record: dict, scale: str, size: float) -> Image | Paragraph:
        image = record["images"][scale]
        if image["content_status"] != "nonuniform":
            return paragraph("Image unavailable / placeholder response", "small")
        return Image(str(TEACHING_DOWNLOAD_DIR / image["cache_file"]), width=size, height=size)

    story.extend(
        [
            paragraph("A star in disguise?", "title"),
            paragraph("OBSERVATIONAL ASTRONOMY / STUDENT FIELD NOTEBOOK", "small"),
            paragraph("Student / group: ____________________   Date: ______________"),
            paragraph("A compact dot can preserve the history of a larger galaxy.", "heading"),
        ]
    )
    story.append(
        paragraph(
            "Ultra-compact dwarf galaxies (UCDs) are compact stellar systems with a fuzzy boundary against massive star clusters. Some may be galaxy centers left behind after outer stars were stripped away. Comparing their properties helps us study how galaxies grow. M60-UCD1 even hosts a massive black hole discovered through detailed follow-up [1,2]; this worksheet cannot establish a black hole or confirm a new UCD."
        )
    )
    story.append(paragraph("Why Gaia can record non-stars", "heading"))
    story.append(
        paragraph(
            "Gaia scanned the sky and selected compact concentrations of light for small measurement windows. This favors star-like light patterns, not necessarily individual stars: compact galaxies, bright galaxy centers, and quasars (active galaxy centers) can be detected too. Diffuse light is less favored. Departures from a stellar image or motion fit are clues, but can also arise from blends or measurement problems [3]."
        )
    )
    story.append(
        table(
            [
                ["Do not confuse", "Numerical context and meaning"],
                [
                    "Pixel sampling",
                    "0.0589 arcsec along scan; 0.1768 arcsec across. Pixel size is not resolving power [4].",
                ],
                [
                    "Onboard pair resolution",
                    "About 0.23 arcsec along and 0.70 arcsec across for equal-brightness pairs in the detection study. Not a UCD-radius cutoff [3].",
                ],
                [
                    "Catalog completeness",
                    "EDR3 pair losses start below about 1.5 arcsec, becoming severe below 0.7 arcsec. DR3 uses the EDR3 astrometric solution [5].",
                ],
                [
                    "Positional precision",
                    "A source center can be measured more precisely than its blurred image width. This does not resolve its individual stars.",
                ],
            ],
            [120, width - 120],
        )
    )
    story.extend(
        [
            Spacer(1, 10),
            paragraph("Your job", "heading"),
            paragraph(
                "Compare known objects, review two published candidates, and record what you see and cannot tell. A compact image, no detected motion, or high flux excess alone never confirms a UCD. Missing astrometry is not zero. The Gaia acronym UCD can also mean an ultracool stellar dwarf - a different topic."
            ),
            paragraph(
                "Use the companion HTML offline, or complete this PDF on paper. Optional online practice is on page 6. No code or website is required. References are on page 6.",
                "small",
            ),
            PageBreak(),
        ]
    )

    story.append(paragraph("01 / Identify and compare", "heading"))
    controls = [lookup[key] for key in ["m60_ucd1", "m59_ucd3", "foreground_star"]]
    tiles = Table(
        [
            [photo(record, "close", 105) for record in controls],
            [paragraph(record["name"], "center") for record in controls],
        ],
        colWidths=[width / 3] * 3,
    )
    story.extend(
        [
            tiles,
            paragraph(
                "DR11 close cutouts: 33.536 arcsec square each, 0.262 arcsec/pixel. Centers are requested Gaia coordinates; images have no drawn marker. The HTML also supplies wider context; paper-only reviewers should note that missing context.",
                "small",
            ),
        ]
    )
    rows = [
        ["Gaia DR3", *[record["name"] for record in controls]],
        ["Source ID (text)", *[record["source_id"] for record in controls]],
    ]
    for label, field in [
        ("G magnitude", "phot_g_mean_mag"),
        ("BP-RP", "bp_rp"),
        ("Raw flux excess C", "phot_bp_rp_excess_factor"),
    ]:
        rows.append([label, *[formatted(record["gaia"][field]) for record in controls]])
    for label, field in [
        ("Parallax (mas)", "parallax"),
        ("pmra (mas/year)", "pmra"),
        ("pmdec (mas/year)", "pmdec"),
    ]:
        rows.append([label, *[with_error(record["gaia"], field) for record in controls]])
    story.extend(
        [
            table(rows, [103] + [(width - 103) / 3] * 3),
            paragraph(
                "Parallax is an annual apparent shift; proper motion is a drift across the sky. One milliarcsecond (mas) = 0.001 arcsec. pmra includes the cosine of declination; pmdec is north-south motion. Values are measurement +/- uncertainty; negative parallax can arise from noise, and missing is not zero.",
                "small",
            ),
            Spacer(1, 4),
        ]
    )
    for key in ["q1", "q2", "q3"]:
        question(key, 1)
    story.append(PageBreak())

    story.append(paragraph("02 / Size and uncertainty", "heading"))
    story.append(
        paragraph(
            "Small-angle relation: angular radius (arcsec) = 206265 x radius (pc) / distance (pc). Sizes/distances use parsecs (pc); one megaparsec (Mpc) is 1,000,000 pc. The result is a half-light radius, not a diameter or measured image width. On paper, calculate the 5 and 50 Mpc examples instead of moving the slider."
        )
    )
    question("q4", 3)
    question("q5", 3)
    story.append(
        paragraph(
            "Raw excess C = (I_BP + I_RP) / I_G, using blue, red, and broad-band fluxes, not magnitudes. Renormalized unit weight error (RUWE) measures astrometric fit quality; excess noise is additional angular scatter, not size. High values can have several causes. These six examples are deliberately selected."
        )
    )
    question("q6", 3)
    missing = lookup["m59co"]
    story.append(
        table(
            [
                ["M59cO - compact-system boundary case", "Saved Gaia DR3 record"],
                ["Source ID", missing["source_id"]],
                ["RA, Dec (degrees)", f"{missing['gaia']['ra']:.8f}, {missing['gaia']['dec']:.8f}"],
                ["Parallax / proper motion / RUWE", "Not supplied / Not supplied / Not supplied"],
            ],
            [width / 2] * 2,
        )
    )
    question("q7", 2)
    story.append(PageBreak())

    for index, key in enumerate(["candidate_a", "candidate_b"], start=3):
        record = lookup[key]
        story.extend(
            [
                paragraph(
                    f"0{index} / Published candidate {'A' if key.endswith('a') else 'B'}", "heading"
                ),
                paragraph(record["name"]),
                paragraph(
                    f"Gaia ID {record['source_id']} / RA {record['gaia']['ra']:.8f}, Dec {record['gaia']['dec']:.8f} deg",
                    "small",
                ),
            ]
        )
        tiles = Table(
            [
                [photo(record, "close", 142), photo(record, "context", 142)],
                [
                    paragraph("Close: 33.536 arcsec square", "center"),
                    paragraph("Context: 204.800 arcsec square", "center"),
                ],
            ],
            colWidths=[width / 2] * 2,
        )
        story.extend(
            [
                tiles,
                paragraph(
                    "Legacy Survey DR11; close 0.262 arcsec/pixel, context 0.8 arcsec/pixel. Both centered on Gaia position, not proof of a correct match. Inspect the unmarked image center; the HTML also offers a marker.",
                    "small",
                ),
            ]
        )
        gaia = record["gaia"]
        story.append(
            table(
                [
                    ["Saved Gaia DR3", "Value"],
                    [
                        "G / BP-RP / raw excess C",
                        f"{formatted(gaia['phot_g_mean_mag'])} / {formatted(gaia['bp_rp'])} / {formatted(gaia['phot_bp_rp_excess_factor'])}",
                    ],
                    ["Parallax (mas)", with_error(gaia, "parallax")],
                    [
                        "pmra / pmdec (mas/year)",
                        f"{with_error(gaia, 'pmra')} / {with_error(gaia, 'pmdec')}",
                    ],
                    [
                        "RUWE / excess noise (mas)",
                        f"{formatted(gaia['ruwe'])} / {formatted(gaia['astrometric_excess_noise'])}",
                    ],
                ],
                [width * 0.4, width * 0.6],
            )
        )
        story.append(
            paragraph(
                "Flags: Y=yes / N=no / U=uncertain / NA=not assessable. Circle one for each.",
                "small",
            )
        )
        story.append(
            table(
                [[field["label"], "Y     N     U     NA"] for field in review_fields],
                [width * 0.6, width * 0.4],
            )
        )
        for label in [
            "R1. Image evidence and uncertainty",
            "R2. Astrometry and alternative explanations",
            "R3. Recommendation reason and next evidence",
        ]:
            story.append(paragraph(label, "small"))
            answer_space(1)
        story.append(
            paragraph(
                "Recommendation: retain for instructor review / possible contaminant / insufficient information",
                "small",
            )
        )
        story.append(
            paragraph(
                "Published candidate, not confirmed. Liu 2015 table6.dat [6]; inherited comparison Fahrion 2019 [7]. Original labels differ; approved reference state is candidate. Assumed M60 distance is conditional. External quasar, galaxy, and non-single-star memberships are not checked. Color alone cannot identify a young cluster or H II region (gas ionized by young stars).",
                "small",
            )
        )
        story.append(PageBreak())

    story.append(paragraph("05 / Reflect, explore, submit", "heading"))
    question("q8", 3)
    story.append(paragraph("Optional online steps - no code", "heading"))
    for text in [
        "Gaia Archive: open gea.esac.esa.int/archive/; select DR3 and object/position search. Use the exact source ID if supported, otherwise the supplied decimal-degree position and a 5 arcsec matching radius. Check the exact returned ID, values, errors, and units. Do not turn missing fields into zero.",
        "Gaia Visualization: use its sky view for context and supported plots. Exact object identification may require the Archive or Aladin. The built-in HTML comparison plot is the required plot; a parallax-based stellar 3D view cannot give a UCD distance.",
        "Aladin Desktop: install the version for your operating system from CDS. Enter the coordinates; load an optical image and Gaia DR3 catalog I/355/gaiadr3 from VizieR. Select the matching table row and toggle catalog symbols. Record the image survey/release and consider image epoch for moving stars.",
        "Legacy Survey: use each object's viewer link in the HTML; confirm the DR11 image layer, not model/residual. Inspect close and wider views, coordinates, scale, host light, and defects. A blank tile is unavailable imaging; RGB display colors are not calibrated colors.",
    ]:
        story.append(paragraph(text, "small"))
    story.append(
        paragraph(
            "Live GUI labels vary and were not fully tested. The full step-by-step guide is embedded in the HTML. Core work is offline. No Windows rehearsal or student installation is required.",
            "small",
        )
    )
    story.append(paragraph("Submission checklist", "heading"))
    story.append(
        paragraph(
            "Record your identifier; answer Q1-Q8 and both candidate reviews; distinguish observations from interpretation. Export JSON to resume and text to read/submit, or submit this PDF. Export before closing: local browser storage is best-effort. Nothing uploads automatically, and student reviews never become confirmed/training labels without instructor adjudication.",
            "small",
        )
    )
    references = [
        ("1", "Strader et al. 2013 / M60-UCD1", "https://arxiv.org/abs/1307.7707"),
        ("2", "Seth et al. 2014 / M60-UCD1 black hole", "https://arxiv.org/abs/1409.4769"),
        ("3", "de Bruijne et al. 2015 / onboard detection", "https://arxiv.org/abs/1502.00454"),
        ("4", "Gaia Collaboration 2016 / mission instrument", "https://arxiv.org/abs/1609.04153"),
        ("5", "Fabricius et al. 2021 / EDR3 validation", "https://arxiv.org/abs/2012.06242"),
        (
            "6",
            "Liu et al. 2015 / published candidates",
            "https://doi.org/10.1088/0004-637X/812/1/34",
        ),
        (
            "7",
            "Fahrion et al. 2019 / comparative compilation",
            "https://doi.org/10.1051/0004-6361/201834941",
        ),
        ("8", "Sandoval et al. 2015 / M59-UCD3", "https://arxiv.org/abs/1506.08828"),
    ]
    story.append(paragraph("References and provenance", "heading"))
    for number, label, url in references:
        story.append(
            Paragraph(
                f'[{number}] {html.escape(label)}: <link href="{html.escape(url)}" color="#126456">{html.escape(url)}</link>',
                styles["small"],
            )
        )

    def footer(canvas, document) -> None:
        canvas.saveState()
        canvas.setFillColor(ink)
        canvas.setFont("Helvetica", 8)
        canvas.drawString(
            16 * mm, A4[1] - 13 * mm, "BUBBLETEA / A STAR IN DISGUISE? / STUDENT WORKSHEET"
        )
        canvas.setStrokeColor(colors.HexColor("#c9cfc1"))
        canvas.line(16 * mm, 15 * mm, A4[0] - 16 * mm, 15 * mm)
        canvas.setFont("Helvetica", 6.5)
        canvas.drawString(
            16 * mm,
            11 * mm,
            "ESA Gaia DR3 / Images: Legacy Surveys / D. Lang (Perimeter Institute) / DR11",
        )
        canvas.drawString(
            16 * mm,
            8 * mm,
            f"Snapshot {packet['gaia_retrieval']['snapshot_date_utc'][:10]} UTC / {packet['packet_sha256'][:12]}",
        )
        canvas.drawRightString(A4[0] - 16 * mm, 8 * mm, f"{document.page} / 6")
        canvas.restoreState()

    document.build(story, onFirstPage=footer, onLaterPages=footer)
    if len(PdfReader(TEACHING_WORKSHEET_PDF).pages) != 6:
        raise RuntimeError("Worksheet overflowed its intended six-page layout; render and adjust")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    start = time.monotonic()
    packet = load_packet()
    build_html(packet)
    build_pdf(packet)
    report = {
        "packet_version": packet["packet_version"],
        "packet_sha256": packet["packet_sha256"],
        "object_count": len(packet["objects"]),
        "embedded_image_count": sum(len(record["images"]) for record in packet["objects"]),
        "pdf_page_count": len(PdfReader(TEACHING_WORKSHEET_PDF).pages),
        "html_bytes": TEACHING_ACTIVITY_HTML.stat().st_size,
        "pdf_bytes": TEACHING_WORKSHEET_PDF.stat().st_size,
        "build_seconds": time.monotonic() - start,
        "source_sha256": {
            str(path.relative_to(TEACHING_DIR.parent.parent)): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in [
                TEACHING_PACKET,
                Path(__file__),
                *TEACHING_ASSETS_DIR.iterdir(),
                TEACHING_DIR / "worksheet.md",
                TEACHING_DIR / "concepts.md",
                TEACHING_DIR / "tool_guide.md",
            ]
            if path.is_file()
        },
    }
    TEACHING_BUILD_REPORT.write_text(json.dumps(report, indent=2) + "\n")
    logger.info(
        "Built %d objects, %d embedded images, %d PDF pages in %.3f seconds",
        report["object_count"],
        report["embedded_image_count"],
        report["pdf_page_count"],
        report["build_seconds"],
    )


if __name__ == "__main__":
    main()
