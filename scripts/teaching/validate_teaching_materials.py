"""Check the offline teaching file in installed Chrome and inspect PDF structure.

Inputs: generated HTML/PDF and the frozen teaching packet. No external network
requests or live student files are used. Outputs: a small validation report and
temporary browser screenshots/download fixtures; no scientific data writes.
"""

import hashlib
import json
import logging
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright
from pypdf import PdfReader

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    TEACHING_BROWSER_PREVIEW_DIR,
    TEACHING_PACKET,
    TEACHING_VALIDATION_REPORT,
    TEACHING_WORKSHEET_PDF,
)
from scripts.config import (
    teaching_previous_html as TEACHING_ACTIVITY_HTML,
)

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    packet = json.loads(TEACHING_PACKET.read_text())
    checks = []

    def check(condition: bool, description: str) -> None:
        if not condition:
            raise AssertionError(description)
        checks.append(description)

    pdf = PdfReader(TEACHING_WORKSHEET_PDF)
    check(len(pdf.pages) == 6, "PDF has six pages")
    text = "\n".join(page.extract_text() for page in pdf.pages)
    check(all(f"Q{index}." in text for index in range(1, 9)), "PDF has Q1-Q8")
    check(
        all(record["source_id"] in text for record in packet["objects"]),
        "PDF preserves all six exact Gaia identifiers",
    )
    check("\u25a0" not in text, "PDF text contains no unsupported-glyph black squares")
    check("Not supplied" in text, "PDF explicitly preserves missing measurements")
    TEACHING_BROWSER_PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    remote_requests = []
    errors = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(
            offline=True, accept_downloads=True, viewport={"width": 1440, "height": 1000}
        )
        page = context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on(
            "request",
            lambda request: (
                remote_requests.append(request.url)
                if request.url.startswith(("http:", "https:"))
                else None
            ),
        )
        page.goto(TEACHING_ACTIVITY_HTML.as_uri())
        check(
            page.title().startswith("A star in disguise?"),
            "HTML opens directly as file:// with network offline",
        )
        check(
            page.locator("#object_navigation button").count() == 6,
            "Six object navigation buttons load",
        )
        check(page.locator("#questions textarea").count() == 8, "HTML has Q1-Q8 response fields")
        check(
            page.locator("#comparison_plot circle").count() == 6,
            "G-versus-excess plot contains exactly six selected examples",
        )
        page.screenshot(path=str(TEACHING_BROWSER_PREVIEW_DIR / "desktop.png"), full_page=True)
        for selector, filename in [
            (".hero", "opening.png"),
            (".size_lab", "size.png"),
            (".plot_section", "plot.png"),
        ]:
            page.locator(selector).screenshot(path=str(TEACHING_BROWSER_PREVIEW_DIR / filename))
        page.locator("#investigation").screenshot(
            path=str(TEACHING_BROWSER_PREVIEW_DIR / "inspection.png")
        )
        for record in packet["objects"]:
            page.get_by_role("button", name=record["name"], exact=True).click()
            check(
                record["source_id"] in page.locator("#source_identifier").inner_text(),
                f"Exact string identifier rendered for {record['object_key']}",
            )
            page.wait_for_function(
                "() => Array.from(document.querySelectorAll('#images img')).every(image => image.complete && image.naturalWidth > 0)"
            )
            check(
                page.locator("#images img").count() == 2,
                f"Both embedded images load offline for {record['object_key']}",
            )
            if record["object_key"] == "m59co":
                check(
                    page.locator("#catalog_rows").inner_text().count("Not supplied") == 4,
                    "M59cO parallax, both motion components and RUWE are missing, not zero",
                )
        page.locator("#show_marker").uncheck()
        check(
            not page.locator(".position_marker").first.is_visible(),
            "Catalog position marker can be hidden",
        )
        page.locator("#show_marker").check()
        page.locator("#distance_slider").fill("50")
        check(
            "0.100 arcsec" in page.locator("#angular_value").inner_text(),
            "Distance slider calculates angular radius at 50 Mpc",
        )
        page.locator("#distance_slider").fill("16.5")
        check(
            "0.303 arcsec" in page.locator("#angular_value").inner_text(),
            "Distance slider reproduces published-input angular radius",
        )
        page.locator("#comparison_plot circle[aria-label='Inspect M59cO']").focus()
        page.keyboard.press("Enter")
        check(
            page.locator("#object_name").inner_text() == "M59cO",
            "Plot point supports keyboard selection",
        )
        page.locator("#student_identifier").fill("qa_group")
        page.locator("#q1").fill("Independent test response: evidence is not confirmation.")
        candidate = next(
            record for record in packet["objects"] if record["object_key"] == "candidate_a"
        )
        page.get_by_role("button", name=candidate["name"], exact=True).click()
        page.locator("#flag_resolved").select_option("uncertain")
        page.locator("#r1").fill("QA test only, not an astronomical classification.")
        page.get_by_role("button", name="M60-UCD1", exact=True).click()
        page.get_by_role("button", name=candidate["name"], exact=True).click()
        check(
            page.locator("#r1").input_value().startswith("QA test only"),
            "Review survives switching objects",
        )
        check(
            page.locator("#flag_resolved").input_value() == "uncertain",
            "Four-state visual uncertainty survives switching",
        )
        with page.expect_download() as download_info:
            page.locator("#export_json").click()
        download_path = TEACHING_BROWSER_PREVIEW_DIR / "qa_answers.json"
        download_info.value.save_as(download_path)
        answer_file = json.loads(download_path.read_text())
        check(
            all(
                isinstance(review["source_id"], str) and len(review["source_id"]) == 19
                for review in answer_file["reviews"].values()
            ),
            "Downloaded answers preserve exact Gaia IDs as text",
        )
        check(
            answer_file["packet_sha256"]
            == hashlib.sha256(TEACHING_PACKET.read_bytes()).hexdigest(),
            "Answer download records exact teaching snapshot digest",
        )
        page.locator("#q1").fill("Changed test response")
        page.locator("#import_answers").set_input_files(download_path)
        page.wait_for_function(
            "() => document.getElementById('save_status').textContent.startsWith('Answers imported')"
        )
        check(
            page.locator("#q1").input_value() == answer_file["answers"]["q1"],
            "JSON export/import round trip restores answers",
        )

        def import_fixture(value: dict) -> None:
            page.locator("#import_answers").set_input_files(
                {
                    "name": "fixture.json",
                    "mimeType": "application/json",
                    "buffer": json.dumps(value).encode(),
                }
            )

        invalid = json.loads(json.dumps(answer_file))
        invalid["reviews"]["candidate_a"]["source_id"] = int(candidate["source_id"])
        import_fixture(invalid)
        page.wait_for_function(
            "() => document.getElementById('save_status').textContent.startsWith('Import rejected')"
        )
        check(
            page.locator("#q1").input_value() == answer_file["answers"]["q1"],
            "Numeric source-ID import is rejected without discarding answers",
        )
        invalid = dict(answer_file, packet_sha256="wrong_packet")
        import_fixture(invalid)
        page.wait_for_function(
            "() => document.getElementById('save_status').textContent.startsWith('Import rejected')"
        )
        check(
            "exact teaching packet" in page.locator("#save_status").inner_text(),
            "Wrong snapshot digest is rejected",
        )
        malicious = json.loads(json.dumps(answer_file))
        malicious["answers"]["q1"] = (
            '<img src="https://invalid.example/x" onerror="window.injected=true">'
        )
        import_fixture(malicious)
        page.wait_for_function(
            "() => document.getElementById('save_status').textContent.startsWith('Answers imported')"
        )
        check(
            page.locator("#q1").input_value() == malicious["answers"]["q1"]
            and page.locator("#questions img").count() == 0,
            "Imported HTML-like text is displayed as text, not executable markup",
        )
        with page.expect_download() as download_info:
            page.locator("#export_text").click()
        text_path = TEACHING_BROWSER_PREVIEW_DIR / "qa_answers.txt"
        download_info.value.save_as(text_path)
        check(
            "Q8." in text_path.read_text() and candidate["source_id"] in text_path.read_text(),
            "Readable report includes questions, reviews, and exact IDs",
        )
        page.evaluate("window.dispatchEvent(new Event('beforeprint'))")
        check(
            "Q8." in page.locator("#print_summary").text_content(),
            "Print report includes current answers",
        )
        page.set_viewport_size({"width": 390, "height": 844})
        check(
            page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"),
            "Narrow layout has no horizontal page overflow",
        )
        page.get_by_role("button", name="M60-UCD1", exact=True).click()
        page.locator("#investigation").screenshot(
            path=str(TEACHING_BROWSER_PREVIEW_DIR / "narrow.png")
        )
        check(not remote_requests, "Core offline activity attempts no HTTP or HTTPS requests")
        check(not errors, "No browser JavaScript exceptions")
        blocked = browser.new_context(offline=True, accept_downloads=True)
        blocked.add_init_script(
            "Object.defineProperty(window,'localStorage',{get(){throw new Error('Storage blocked')}})"
        )
        blocked_page = blocked.new_page()
        blocked_page.goto(TEACHING_ACTIVITY_HTML.as_uri())
        blocked_page.locator("#q1").fill("Storage-denied test")
        check(
            "storage unavailable" in blocked_page.locator("#save_status").inner_text(),
            "Blocked local storage produces an explicit warning",
        )
        with blocked_page.expect_download():
            blocked_page.locator("#export_json").click()
        check(True, "JSON export still works when browser storage is blocked")
        browser_version = browser.version
        browser.close()
    report = {
        "passed": True,
        "checks_passed": len(checks),
        "checks": checks,
        "browser": f"Installed Chrome {browser_version}, headless on macOS",
        "offline": True,
        "pdf_visual_review": "Automated structure checks only; see docs/teaching/instructor_notes.md for the separately recorded six-page visual inspection.",
        "html_sha256": hashlib.sha256(TEACHING_ACTIVITY_HTML.read_bytes()).hexdigest(),
        "pdf_sha256": hashlib.sha256(TEACHING_WORKSHEET_PDF.read_bytes()).hexdigest(),
    }
    TEACHING_VALIDATION_REPORT.write_text(json.dumps(report, indent=2) + "\n")
    logger.info("Passed %d offline browser and PDF checks", len(checks))


if __name__ == "__main__":
    main()
