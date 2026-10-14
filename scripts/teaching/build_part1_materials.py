"""Build the single-file Part I activity from real catalog data and cached images.

Inputs: v2 teaching packet, source assets, core reading, external DR11 JPEGs.
Outputs: student HTML and measured build report. The instructor key is never
embedded. Version 1 HTML is preserved separately on the first replacement.
"""

import base64
import hashlib
import json
import logging
import re
import shutil
import sys
import time
from pathlib import Path

import markdown
from astropy.coordinates import SkyCoord

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    TEACHING_ACTIVITY_HTML,
    TEACHING_ASSETS_DIR,
    teaching_part1_build_report,
    teaching_part1_downloads,
    teaching_part1_key,
    teaching_part1_packet,
    teaching_part1_reading,
    teaching_part1_reviews,
    teaching_part1_tool_guide,
    teaching_previous_html,
)

logger = logging.getLogger(__name__)
feature_definitions = [
    (
        "phot_g_mean_mag",
        "G magnitude",
        "G (mag)",
        "mag",
        "linear",
        False,
        "Mean apparent brightness in Gaia's broad G passband.",
    ),
    (
        "bp_rp",
        "BP−RP color",
        "BP−RP (mag)",
        "mag",
        "linear",
        False,
        "BP magnitude minus RP magnitude.",
    ),
    (
        "phot_bp_rp_excess_factor",
        "BP/RP flux excess",
        "(I_BP + I_RP) / I_G",
        "dimensionless",
        "log1p",
        False,
        "Sum of BP and RP mean fluxes divided by G mean flux.",
    ),
    (
        "absolute_parallax_significance",
        "Absolute-parallax significance",
        "|parallax| / error",
        "dimensionless",
        "log1p",
        False,
        "Absolute fitted parallax divided by its positive error.",
    ),
    (
        "proper_motion_significance",
        "Proper-motion significance",
        "Combined motion significance",
        "dimensionless",
        "log1p",
        False,
        "Two-component motion distance from zero in its correlated uncertainty coordinates.",
    ),
    (
        "astrometric_excess_noise",
        "Astrometric excess noise",
        "Excess noise (mas)",
        "mas",
        "log1p",
        True,
        "Additional per-observation angular noise in the astrometric solution.",
    ),
    (
        "ruwe",
        "RUWE",
        "RUWE",
        "dimensionless",
        "log1p",
        True,
        "Astrometric fit statistic normalized for magnitude and color.",
    ),
    (
        "astrometric_excess_noise_sig",
        "Excess-noise significance",
        "Excess-noise significance",
        "dimensionless",
        "log1p",
        True,
        "Gaia's reported significance statistic for excess noise.",
    ),
    (
        "ipd_frac_multi_peak",
        "IPD multi-peak fraction",
        "Multi-peak windows (%)",
        "%",
        "linear",
        True,
        "Percentage of successful image windows with more than one detected peak.",
    ),
    (
        "ipd_frac_odd_win",
        "IPD odd-window fraction",
        "Odd-window transits (%)",
        "%",
        "linear",
        True,
        "Percentage of successful image-measurement transits with truncated windows or multiple gates.",
    ),
]

scanning_diagram = """<div class="scan_lab">
<svg viewBox="0 0 600 280" role="img" aria-label="Illustrative scan directions across fixed sky sources and small readout windows">
<defs><pattern id="detector_grid" width="12" height="24" patternUnits="userSpaceOnUse"><path d="M 12 0 L 0 0 0 24" fill="none" stroke="#ccd4c8" stroke-width="1"/></pattern></defs>
<rect x="90" y="25" width="420" height="210" fill="url(#detector_grid)"/>
<g fill="#2b6156"><circle cx="200" cy="88" r="6"/><circle cx="300" cy="130" r="8"/><circle cx="406" cy="185" r="5"/></g>
<g id="scan_orientation"><rect x="273" y="91" width="54" height="78" fill="none" stroke="#ab5830" stroke-width="2"/><path d="M 120 130 H 475 M 462 120 L 475 130 462 140" fill="none" stroke="#176b56" stroke-width="3"/></g>
<text x="95" y="263" font-size="13" fill="#264f45">Fixed sky source positions</text><text x="342" y="263" font-size="13" fill="#9a4c29">Window / detector orientation</text>
</svg><div class="scan_controls"><label for="scan_visit">Illustrative visit</label><input id="scan_visit" type="range" min="1" max="6" step="1" value="1"><button id="scan_play" type="button" class="secondary">Play visits</button></div><p id="scan_visit_label" aria-live="polite"></p><p>Move the control to change the illustrative scan direction. The orange outline represents a readout window; it is not a source boundary. Positions, scale, window shape, visit count, and angles are schematic. Nothing moves automatically.</p></div>"""

distance_diagram = """<section class="size_lab" aria-labelledby="size_heading">
<p class="eyebrow">Try a change in distance</p><h3 id="size_heading">Same system. Different apparent size.</h3>
<p>Keep M60-UCD1's published half-light radius fixed at <strong>24.2 pc</strong> and move it hypothetically farther away. A half-light radius encloses half the light; it is not the full width of the image. <a href="https://arxiv.org/abs/1307.7707">Discovery study and size measurement</a>.</p>
<label for="distance_slider">Hypothetical distance: <output id="distance_value">16.5</output> Mpc</label>
<input id="distance_slider" type="range" min="5" max="50" step="0.5" value="16.5">
<p id="angular_value" aria-live="polite"></p>
<svg id="size_ruler" viewBox="0 0 650 255" role="img" aria-label="Angular scale ruler comparing a hypothetical half-light diameter with detector sampling and equal-brightness pair separations"></svg>
<p class="small">This changes angular size only: it does not simulate a blurred image, fading light, or whether Gaia would detect the object. Detector pixels, pair separation, and a system's half-light diameter describe different things; neither reference bar is a cutoff on UCD radius. The comparison values are explained and sourced immediately above.</p></section>"""


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    started = time.perf_counter()
    original = teaching_part1_packet.read_bytes()
    packet = json.loads(original)
    key = json.loads(teaching_part1_key.read_text())
    reviews = json.loads(teaching_part1_reviews.read_text())
    review_digest = hashlib.sha256(teaching_part1_reviews.read_bytes()).hexdigest()
    if (
        packet["reference_key_sha256"]
        != hashlib.sha256(teaching_part1_key.read_bytes()).hexdigest()
        or key.get("review_record_sha256") != review_digest
        or any(
            record.get("image_review") == "pending" or record.get("evidence_audit") == "pending"
            for role in ["examples", "task1"]
            for record in key[role].values()
        )
    ):
        raise ValueError("The teaching image/evidence review is absent or out of date")
    packet["packet_sha256"] = hashlib.sha256(original).hexdigest()
    packet.pop("reference_key_sha256", None)
    features = []
    for key, label, short_label, unit, scale, advanced, definition in feature_definitions:
        column = packet["catalog_columns"].index(key)
        values = [row[column] for row in packet["catalog_rows"] if row[column] is not None]
        if not values or (scale == "log1p" and min(values) < 0):
            raise ValueError(f"Cannot build the measured domain for {key}")
        features.append(
            {
                "key": key,
                "label": label,
                "short_label": short_label,
                "unit": unit,
                "scale": scale,
                "advanced": advanced,
                "definition": definition,
                "minimum": min(values),
                "maximum": max(values),
                "missing_count": len(packet["catalog_rows"]) - len(values),
            }
        )
    packet["features"] = features
    image_count, missing_images = 0, []
    for object_record in packet["gallery"]:
        galactic = SkyCoord(
            object_record["gaia"]["ra"], object_record["gaia"]["dec"], unit="deg", frame="icrs"
        ).galactic
        object_record["galactic_coordinates"] = {
            "longitude_deg": float(galactic.l.deg),
            "latitude_deg": float(galactic.b.deg),
            "basis": "Astropy ICRS-to-Galactic transformation of the saved Gaia DR3 position",
        }
        review = reviews["objects"][object_record["source_id"]]
        if object_record["role"] == "task1" and any(
            key in object_record for key in ["reference_class", "provenance", "context"]
        ):
            raise ValueError("Task 1 object contains a reference-label disclosure field")
        for scale in ["close", "context"]:
            image_record = object_record["images"].get(scale)
            if not image_record or image_record["content_status"] != "nonuniform":
                missing_images.append(f"{object_record['object_key']}:{scale}")
                continue
            path = teaching_part1_downloads / image_record["cache_file"]
            if review["image_sha256"][scale] != image_record["sha256"]:
                raise ValueError(f"Image changed after visual review: {object_record['source_id']}")
            content = path.read_bytes()
            if hashlib.sha256(content).hexdigest() != image_record["sha256"]:
                raise ValueError(f"Image hash mismatch: {path.name}")
            image_record["data_url"] = (
                "data:image/jpeg;base64," + base64.b64encode(content).decode()
            )
            image_record.pop("cache_file", None)
            image_count += 1
    reading = (
        teaching_part1_reading.read_text()
        .replace("<!-- scanning_diagram -->", scanning_diagram)
        .replace("<!-- distance_diagram -->", distance_diagram)
    )
    if missing_images:
        raise ValueError(f"Reviewed gallery images are unavailable: {missing_images}")
    rendered = markdown.markdown(reading, extensions=["tables", "fenced_code", "sane_lists"])
    guide = markdown.markdown(
        teaching_part1_tool_guide.read_text(), extensions=["tables", "sane_lists"]
    )
    guide = guide.replace('href="ucd_investigation.html"', 'href="#top"')
    rendered = rendered.replace(
        "<!-- detailed_tool_guide -->",
        f'<details id="online_guide"><summary>Detailed steps: Gaia Archive, Visualization, Aladin, and Legacy Survey</summary><div class="tool_guide">{guide}</div></details>',
    )
    template = (TEACHING_ASSETS_DIR / "part1.html").read_text()
    style = (TEACHING_ASSETS_DIR / "part1.css").read_text()
    script = (TEACHING_ASSETS_DIR / "part1.js").read_text()
    hero = packet["gallery"][0]["images"].get("close", {})
    hero_image = (
        f'<img src="{hero["data_url"]}" alt="Saved Legacy Survey DR11 image of M60-UCD1">'
        if hero.get("data_url")
        else "Image unavailable"
    )
    for token, replacement in {
        "__STYLE__": style,
        "__SCRIPT__": script,
        "__READING__": rendered,
        "__HERO_IMAGE__": hero_image,
        "__HERO_WIDTH__": str(hero.get("field_width_arcsec", "unavailable")),
        "__PACKET__": json.dumps(packet, separators=(",", ":"), allow_nan=False).replace(
            "<", "\\u003c"
        ),
    }.items():
        template = template.replace(token, replacement)
    if re.search(r"__[A-Z_]+__", template):
        raise ValueError("Unresolved template placeholder")
    template = re.sub(
        r'<a\s+([^>]*href="https?://[^>]+)>',
        lambda match: (
            "<a "
            + re.sub(r'\s+(?:target|rel)="[^"]*"', "", match.group(1))
            + ' target="_blank" rel="noopener noreferrer">'
        ),
        template,
    )
    size = len(template.encode())
    if size >= 10_000_000:
        raise ValueError(
            f"HTML is {size} bytes; reduce the deterministic star allocation before publishing"
        )
    if TEACHING_ACTIVITY_HTML.exists() and not teaching_previous_html.exists():
        if "A star in disguise?" in TEACHING_ACTIVITY_HTML.read_text():
            shutil.copyfile(TEACHING_ACTIVITY_HTML, teaching_previous_html)
    TEACHING_ACTIVITY_HTML.write_text(template)
    report = {
        "activity_version": packet["activity_version"],
        "packet_sha256": packet["packet_sha256"],
        "html_bytes": size,
        "html_sha256": hashlib.sha256(template.encode()).hexdigest(),
        "embedded_images": image_count,
        "image_review_sha256": review_digest,
        "missing_images": missing_images,
        "catalog_counts": packet["sampling"]["task2_counts"],
        "catalog_rows": len(packet["catalog_rows"]),
        "gallery_objects": len(packet["gallery"]),
        "core_reading_words": len(re.findall(r"\b\w+\b", reading)),
        "features": features,
        "build_seconds": time.perf_counter() - started,
        "status": "built; see the validation report and dated classroom handoff in the course guide",
    }
    teaching_part1_build_report.write_text(json.dumps(report, indent=2) + "\n")
    logger.info(
        "Built %d bytes, %d images, %d missing images, %d catalog rows in %.3f s",
        size,
        image_count,
        len(missing_images),
        len(packet["catalog_rows"]),
        report["build_seconds"],
    )


if __name__ == "__main__":
    main()
