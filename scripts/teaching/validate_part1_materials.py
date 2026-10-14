"""Validate the complete offline Part I lesson, real data, and grading round trips.

Inputs: frozen v2 packet/key and generated HTML. Uses installed Chrome on macOS;
network is disabled and no real student work is loaded. Temporary screenshots
and synthetic submissions live under tmp/teaching/part1. Scientific inputs are
checked read-only against their original hashes.
"""

import copy
import hashlib
import json
import logging
import math
import platform
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
from astropy.coordinates import SkyCoord
from playwright.sync_api import sync_playwright

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    CONFIRMED_UCD_DESIGN_REFERENCE_EXCLUSIONS,
    TEACHING_ACTIVITY_HTML,
    teaching_part1_key,
    teaching_part1_packet,
    teaching_part1_preview,
    teaching_part1_reviews,
    teaching_part1_selection_trial,
    teaching_part1_validation_report,
    teaching_reliability_reviews,
)
from scripts.teaching.check_part1_answers import check_answers, score_rules

logger = logging.getLogger(__name__)


def validate_review_fixes(browser, check):
    """Exercise review findings with synthetic work in a separate offline browser."""
    context = browser.new_context(offline=True, viewport={"width": 1440, "height": 900})
    page = context.new_page()
    page.goto(TEACHING_ACTIVITY_HTML.as_uri())
    page.fill("#student_identifier", "original_student")
    page.fill("#evidence_note", "Original evidence must survive rejected imports.")
    page.click("#evaluate")
    original = page.evaluate("() => copy(state)")
    saved = page.evaluate("() => localStorage.getItem(storage_key)")

    def import_data(value):
        page.evaluate("() => by_id('import_error').textContent = ''")
        page.set_input_files(
            "#import_file",
            {
                "name": "review_fixture.json",
                "mimeType": "application/json",
                "buffer": json.dumps(value).encode(),
            },
        )
        page.wait_for_function(
            "() => by_id('import_error').textContent.startsWith('Import rejected')"
        )

    for version in ["bubbletea_answers_v3", "bubbletea_answers_v2"]:
        bad = copy.deepcopy(original)
        bad["student_identifier"] = "replacement_student"
        bad["task2_attempts"][0]["attempt_id"] = ["attempt_0001"]
        bad["schema_version"] = version
        if version.endswith("v2"):
            del bad["task2_final_selection"], bad["imported_v2_final_rules"]
            del bad["task2_attempts"][0]["metrics"]["f1"]
            bad["task2_final_rules"] = {
                "recovery_attempt_id": "",
                "purity_attempt_id": "",
                "recovery_explanation": "",
                "purity_explanation": "",
            }
        import_data(bad)
        check(
            page.evaluate("() => copy(state)") == original
            and page.input_value("#student_identifier") == "original_student"
            and page.evaluate("() => localStorage.getItem(storage_key)") == saved,
            f"Array attempt ID rejected without changing memory, UI, or storage: {version}",
        )

    candidate = copy.deepcopy(original)
    candidate["student_identifier"] = "replacement_student"
    first = next(iter(candidate["task1_responses"]))
    candidate["task1_responses"][first]["evidence_note"] = "Replacement evidence"
    page.evaluate("""() => {
      const original_render = render_history;
      render_history = () => {render_history = original_render; throw new Error('Injected render failure');};
    }""")
    import_data(candidate)
    check(
        page.evaluate("() => copy(state)") == original
        and page.input_value("#student_identifier") == "original_student"
        and page.input_value("#evidence_note")
        == original["task1_responses"][first]["evidence_note"]
        and page.evaluate("() => localStorage.getItem(storage_key)") == saved
        and page.locator("#history_rows tr").count() == 1
        and page.evaluate("() => selected_mask.reduce((total, value) => total + value, 0)")
        == original["task2_attempts"][0]["counts"]["total_selected"],
        "Import rollback restores memory, form, history, plot mask, and storage after rendering fails",
    )

    page.evaluate("""() => {
      state.draft_rules=blank_rules();
      state.draft_rules.phot_g_mean_mag={enabled:true,minimum:null,maximum:19};
      sync_rule_controls(); evaluate_selection();
    }""")
    counts = page.evaluate("() => copy(state.task2_attempts.at(-1).counts)")
    for incomplete in ["-", "1e"]:
        control = page.locator("#phot_g_mean_mag_maximum")
        control.fill("")
        control.press_sequentially(incomplete)
        check(
            control.evaluate("input => input.validity.badInput"),
            f"Native invalid-input fixture: {incomplete}",
        )
        control.blur()
        check(
            control.input_value() == "19"
            and "previous boundary was kept" in page.locator("#rule_error").inner_text(),
            f"Invalid number retains visible previous bound and explains correction: {incomplete}",
        )
        page.click("#evaluate")
        check(
            page.evaluate("() => copy(state.task2_attempts.at(-1).counts)") == counts,
            f"Malformed number cannot broaden the evaluated selection: {incomplete}",
        )
    control.fill("")
    control.blur()
    check(
        page.evaluate("() => state.draft_rules.phot_g_mean_mag.maximum === null"),
        "Intentionally blank number remains an unbounded cut",
    )

    endpoints = page.evaluate("""() => features.map(field => {
      state.draft_rules=blank_rules(); sync_rule_controls();
      by_id(`enable_${field.key}`).click();
      for (const [bound, position] of [['minimum', '0'], ['maximum', '1000']]) {
        const slider=by_id(`${field.key}_${bound}_slider`);
        slider.value=position; slider.dispatchEvent(new Event('input', {bubbles:true}));
      }
      const rule=state.draft_rules[field.key];
      return {key:field.key, exact:rule.minimum===field.minimum && rule.maximum===field.maximum,
        selected:compute_selection(state.draft_rules,'exclude',false).counts.total_selected,
        available:rows.filter(row => row[columns[field.key]] !== null).length};
    })""")
    for result in endpoints:
        check(
            result["exact"] and result["selected"] == result["available"],
            f"Slider handlers preserve both exact endpoints and all available rows: {result['key']}",
        )

    page.evaluate("""() => {
      state.draft_rules=blank_rules(); evaluate_selection();
      const plot=plots[0], rect=plot.canvas.getBoundingClientRect(), point=plot.points[0];
      plot.canvas.dispatchEvent(new MouseEvent('mousemove', {
        clientX:rect.left+point[0]*rect.width/800, clientY:rect.top+point[1]*rect.height/500}));
    }""")
    check(
        page.locator("#plot_hover").inner_text().endswith(" · selected"),
        "Hover fixture describes a selected source",
    )
    page.evaluate("""() => {
      state.draft_rules.phot_g_mean_mag={enabled:true,minimum:-1,maximum:0}; evaluate_selection();
    }""")
    check(
        page.locator("#plot_hover").inner_text().startswith("Hover over a point"),
        "New evaluation clears stale hover selection text",
    )
    page.evaluate(
        "() => {by_id('plot_hover').textContent='stale selected'; apply_import(empty_state());}"
    )
    check(
        page.locator("#plot_hover").inner_text().startswith("Hover over a point"),
        "Import without evaluated results clears hover text",
    )
    check(
        page.evaluate("""() => [...by_id('catalog_table').children].every((tr,index) => {
      const fields=['source_id','phot_g_mean_mag','bp_rp','phot_bp_rp_excess_factor',
        'astrometric_excess_noise','absolute_parallax_significance','proper_motion_significance'];
      return tr.children.length===fields.length && fields.every((field,column) =>
        tr.children[column].textContent===(field==='source_id' ? rows[index][0] : format(rows[index][columns[field]])));
    })"""),
        "Accessible table includes every plotted measurement, with correct row alignment",
    )
    check(
        "Excess noise (mas)" in page.locator(".record_browser thead").text_content(),
        "Accessible excess-noise header includes its units",
    )
    check(
        "[NAME]_[STUDENT_ID].json" in page.locator("#submission_instructions").inner_text()
        and "网络学堂" in page.locator("#submission_instructions").inner_text(),
        "Student submission instructions include required filename and destination",
    )
    context.close()


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    started = time.perf_counter()
    checks = []

    def check(condition, name):
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    content = teaching_part1_packet.read_bytes()
    packet = json.loads(content)
    packet_digest = hashlib.sha256(content).hexdigest()
    key = json.loads(teaching_part1_key.read_text())
    trial = json.loads(teaching_part1_selection_trial.read_text())
    check(
        trial["packet_sha256"] == packet_digest,
        "Range-cut trial uses the unchanged teaching packet",
    )
    reviews = json.loads(teaching_part1_reviews.read_text())
    check(
        packet["reference_key_sha256"]
        == hashlib.sha256(teaching_part1_key.read_bytes()).hexdigest()
        and key["review_record_sha256"]
        == hashlib.sha256(teaching_part1_reviews.read_bytes()).hexdigest(),
        "Reference key and explicit teaching reviews match their recorded digests",
    )
    columns = {name: index for index, name in enumerate(packet["catalog_columns"])}
    rows = packet["catalog_rows"]
    check(
        TEACHING_ACTIVITY_HTML.stat().st_size < 10_000_000,
        "Single HTML remains below 10,000,000 bytes",
    )
    source_ids = [row[0] for row in rows]
    check(
        all(isinstance(value, str) and value.isdigit() for value in source_ids),
        "All catalog Gaia IDs remain exact strings",
    )
    check(len(set(source_ids)) == len(rows), "No duplicate Task 2 Gaia identifiers")
    gallery_ids = [record["source_id"] for record in packet["gallery"]]
    check(
        len(set(gallery_ids)) == len(gallery_ids) and not set(gallery_ids) & set(source_ids),
        "Examples, Task 1, and Task 2 have disjoint unique identities",
    )
    check(
        Counter(row[columns["reference_class"]] for row in rows)
        == packet["sampling"]["task2_counts"],
        "Catalog class totals reproduce exactly",
    )
    check(
        Counter(record["reference_class"] for record in key["task1"].values())
        == {"ucd": 10, "star": 10, "qso": 10},
        "Instructor reference key has the intended Task 1 composition",
    )
    check(
        all(
            "reference_class" not in record
            and "provenance" not in record
            and "context" not in record
            for record in packet["gallery"]
            if record["role"] == "task1"
        ),
        "Task 1 observations do not include instructor-only labels or provenance",
    )
    exclusions = set(
        json.loads(CONFIRMED_UCD_DESIGN_REFERENCE_EXCLUSIONS.read_text())["canonical_object_ids"]
    )
    unreliable = {
        record["canonical_object_id"]
        for record in json.loads(teaching_reliability_reviews.read_text())["reviews"]
    }
    labels = {row[0]: row[columns["reference_class"]] for row in rows}
    for source_id, provenance in key["task2_nonstellar_provenance"].items():
        canonical_id = provenance["canonical_object_id"]
        check(canonical_id not in unreliable, f"Reliability exclusions respected for {source_id}")
        if canonical_id in exclusions:
            check(
                labels[source_id] == "candidate",
                f"Later source-status exclusion remains unscored for {source_id}",
            )
    for path, expected in key["source_inputs"].items():
        check(
            hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected,
            f"Scientific input unchanged: {Path(path).name}",
        )
    for record in packet["gallery"]:
        review = reviews["objects"][record["source_id"]]
        check(
            review["status"] == "suitable_for_instructor_review"
            and all(
                review["image_sha256"][scale] == image["sha256"]
                for scale, image in record["images"].items()
            ),
            f"Explicit visual notes match the inspected images: {record['object_key']}",
        )
        check(
            set(record["images"]) == {"close", "context"}
            and all(image["content_status"] == "nonuniform" for image in record["images"].values()),
            f"Both image transports/content checks pass: {record['object_key']}",
        )
    for row in rows:
        parallax, error = row[columns["parallax"]], row[columns["parallax_error"]]
        expected = (
            abs(parallax) / error
            if parallax is not None and error is not None and error > 0
            else None
        )
        check(
            row[columns["absolute_parallax_significance"]] == expected,
            f"Parallax significance reproduces: {row[0]}",
        )
        motion = [
            row[columns[name]]
            for name in ["pmra", "pmdec", "pmra_error", "pmdec_error", "pmra_pmdec_corr"]
        ]
        observed = row[columns["proper_motion_significance"]]
        if (
            all(value is not None for value in motion)
            and motion[2] > 0
            and motion[3] > 0
            and abs(motion[4]) < 1
        ):
            vector = np.array(motion[:2])
            error_ra, error_dec, correlation = motion[2:]
            covariance = np.array(
                [
                    [error_ra**2, correlation * error_ra * error_dec],
                    [correlation * error_ra * error_dec, error_dec**2],
                ]
            )
            expected = math.sqrt(max(0, float(vector @ np.linalg.solve(covariance, vector))))
            check(
                math.isclose(observed, expected, rel_tol=1e-10, abs_tol=1e-10),
                f"Covariance-based motion significance reproduces: {row[0]}",
            )
        else:
            check(observed is None, f"Unavailable motion stays null: {row[0]}")
    teaching_part1_preview.mkdir(parents=True, exist_ok=True)
    errors, remote_requests = [], []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=True)
        validate_review_fixes(browser, check)
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
            page.title().startswith("A Galaxy in Disguise"), "Offline local-file title and startup"
        )
        check(
            page.locator("#task1_navigation button").count() == 30,
            "Thirty Task 1 navigation buttons",
        )
        check(page.locator("#example_navigation button").count() == 7, "Seven labeled examples")
        check(page.locator("#plots canvas").count() == 4, "Four native canvas plots")
        check(
            page.evaluate(
                "() => [...document.querySelectorAll('a[href]')].filter(link => /^https?:/.test(link.getAttribute('href'))).every(link => link.target === '_blank' && link.rel.includes('noopener') && link.rel.includes('noreferrer'))"
            ),
            "Every external link opens safely in a new tab",
        )
        check(
            not page.locator("#online_guide").evaluate("item => item.open")
            and page.locator("#online_guide a").count() >= 8,
            "Detailed online guide is included and folded by default",
        )
        check(
            page.locator("math").count() == 3
            and page.locator(".reading table td")
            .first.evaluate("item => getComputedStyle(item).fontFamily")
            .endswith("sans-serif"),
            "Native offline equations and sans-serif measurement definitions are present",
        )
        page.locator("#distance_slider").fill("5")
        nearby_size = page.locator("#size_ruler line").first.evaluate(
            "item => Number(item.getAttribute('x2')) - Number(item.getAttribute('x1'))"
        )
        page.locator("#distance_slider").fill("50")
        distant_size = page.locator("#size_ruler line").first.evaluate(
            "item => Number(item.getAttribute('x2')) - Number(item.getAttribute('x1'))"
        )
        check(
            math.isclose(nearby_size / distant_size, 10),
            "Tenfold distance reduces the illustrated angular diameter tenfold",
        )
        page.locator("#distance_slider").fill("16.5")
        page.locator("#distance_slider").focus()
        page.keyboard.press("ArrowRight")
        check(
            page.locator("#distance_value").inner_text() == "17.0",
            "Angular-size control works with the keyboard",
        )
        page.locator("#distance_slider").fill("16.5")
        check(
            page.locator("#task3 textarea").count() == 1
            and page.locator("#task3 details").count() == 0,
            "One membership question with no hint panel",
        )
        check(
            page.evaluate(
                "() => state.task2_attempts.length === 0 && !Object.values(state.draft_rules).some(rule => rule.enabled)"
            ),
            "No preloaded cuts or automatic answer feedback",
        )
        for name, record in [("best_in_grid", trial["best_in_grid"]), *trial["controls"].items()]:
            measured = page.evaluate(
                "rules => {const result=compute_selection(rules || blank_rules(),'exclude',false);return {counts:result.counts,metrics:result.metrics};}",
                record.get("rules"),
            )
            check(
                measured == {key: record[key] for key in ["counts", "metrics"]},
                f"Browser independently reproduces bounded-trial/control result: {name}",
            )
        check(
            trial["controls"]["select_everything"]["metrics"]["f1"]
            < trial["best_in_grid"]["metrics"]["f1"]
            and trial["controls"]["select_one_known_ucd"]["metrics"]["f1"]
            < trial["best_in_grid"]["metrics"]["f1"]
            and trial["controls"]["select_nothing"]["metrics"]
            == {"purity": None, "completeness": 0, "f1": 0},
            "All/one/empty controls do not earn a high combined score",
        )
        for record in packet["gallery"]:
            container = "#task1_navigation" if record["role"] == "task1" else "#example_navigation"
            view = "#task1_view" if record["role"] == "task1" else "#example_view"
            page.locator(f'{container} button[data-object_key="{record["object_key"]}"]').click()
            page.wait_for_function(
                "selector => Array.from(document.querySelectorAll(selector + ' img')).every(image => image.complete && image.naturalWidth > 0)",
                arg=view,
            )
            check(
                page.locator(view + " img").count() == 2,
                f"Both gallery images decode offline: {record['object_key']}",
            )
            check(
                record["source_id"] in page.locator(view).inner_text(),
                f"Exact gallery source identifier rendered: {record['object_key']}",
            )
            sky = SkyCoord(
                record["gaia"]["ra"], record["gaia"]["dec"], unit="deg", frame="icrs"
            ).galactic
            galactic = page.evaluate(
                "key => packet.gallery.find(object => object.object_key === key).galactic_coordinates",
                record["object_key"],
            )
            check(
                math.isclose(galactic["longitude_deg"], sky.l.deg, abs_tol=1e-10)
                and math.isclose(galactic["latitude_deg"], sky.b.deg, abs_tol=1e-10)
                and "Galactic longitude" in page.locator(view).inner_text()
                and "Galactic latitude" in page.locator(view).inner_text(),
                f"Galactic coordinates reproduce and are displayed: {record['object_key']}",
            )
            if record["role"] == "task1":
                check(
                    "Reference class:" not in page.locator(view).inner_text(),
                    f"No Task 1 reference label displayed: {record['object_key']}",
                )
        page.locator("#task1_navigation button").first.click()
        page.locator("#classification label").filter(
            has=page.locator('input[value="uncertain"]')
        ).click()
        check(
            "1 / 30 classifications" in page.locator("#task1_progress").inner_text(),
            "Classification alone completes a Task 1 object",
        )
        page.locator("#confidence label").filter(has=page.locator('input[value="low"]')).click()
        page.locator("#evidence_basis label").filter(
            has=page.locator('input[value="supplied_observations"]')
        ).click()
        injection = '<img src=x onerror="window.injected=true"> Evidence is uncertain.'
        page.fill("#evidence_note", injection)
        page.fill("#student_identifier", "validation_only")
        check(
            page.locator("#student_identifier").locator("..").inner_text() == "Student ID"
            and "Student ID: validation_only" in page.evaluate("readable_report()")
            and "Student/group:" not in page.evaluate("readable_report()"),
            "Submission field and readable report ask only for the individual Student ID",
        )
        page.fill(
            "#membership_answer",
            "Independent student response placeholder for validation; no model answer supplied.",
        )
        page.select_option("#llm_used", "yes")
        page.fill("#llm_disclosure", "Validation fixture; no real student data.")
        check(
            page.evaluate(
                "() => state.task1_responses[task1_objects[0].object_key].classification === 'uncertain'"
            ),
            "Uncertain is recorded distinctly from unanswered",
        )
        page.click("#evaluate")
        scenarios = [
            ({}, "keep"),
            ({"phot_g_mean_mag": {"enabled": True, "minimum": -1, "maximum": 0}}, "exclude"),
            (
                {"proper_motion_significance": {"enabled": True, "minimum": None, "maximum": 3}},
                "keep",
            ),
            (
                {"proper_motion_significance": {"enabled": True, "minimum": None, "maximum": 3}},
                "exclude",
            ),
            (
                {
                    "phot_bp_rp_excess_factor": {"enabled": True, "minimum": 2, "maximum": None},
                    "phot_g_mean_mag": {"enabled": True, "minimum": 18, "maximum": 21},
                },
                "keep",
            ),
        ]
        for overrides, missing_policy in scenarios:
            browser_result = page.evaluate(
                "([overrides, policy]) => {state.draft_rules = Object.assign(blank_rules(), overrides); state.draft_missing_policy=policy; sync_rule_controls(); evaluate_selection(); return state.task2_attempts.at(-1);}",
                [overrides, missing_policy],
            )
            independent = score_rules(packet, browser_result["rules"], missing_policy)
            check(
                independent["counts"] == browser_result["counts"]
                and independent["metrics"] == browser_result["metrics"],
                f"Independent scoring matches browser: {len(checks)}",
            )
        boundary = rows[0][columns["phot_g_mean_mag"]]
        exact_result = page.evaluate(
            "bound => {const rules=blank_rules();rules.phot_g_mean_mag={enabled:true,minimum:bound,maximum:bound};return compute_selection(rules, 'exclude', false);}",
            boundary,
        )
        check(
            exact_result["counts"]["total_selected"]
            == sum(row[columns["phot_g_mean_mag"]] == boundary for row in rows),
            "Equal lower/upper boundaries include exactly matching measured values",
        )
        previous_history = page.evaluate("() => copy(state.task2_attempts)")
        page.click("#reset_rules")
        check(
            page.evaluate("() => !Object.values(state.draft_rules).some(rule => rule.enabled)")
            and page.evaluate("() => copy(state.task2_attempts)") == previous_history,
            "Reset disables draft cuts without destroying evaluated history",
        )
        page.locator("#history_rows button").last.click()
        check(
            page.evaluate(
                "() => JSON.stringify(state.draft_rules) === JSON.stringify(state.task2_attempts.at(-1).rules)"
            ),
            "An earlier attempt can restore its rules without adding an evaluation",
        )
        point = page.evaluate("() => plots[0].points[0].slice(0,2)")
        canvas = page.locator("#plots canvas").first
        canvas.scroll_into_view_if_needed()
        box = canvas.bounding_box()
        page.mouse.move(
            box["x"] + point[0] * box["width"] / 800, box["y"] + point[1] * box["height"] / 500
        )
        check(
            page.locator("#plot_hover").inner_text().startswith("Gaia "),
            "Hover identifies a plotted source without revealing its reference class",
        )
        page.click("#scan_play")
        check(
            page.evaluate("() => scan_timer !== null"),
            "Scanning illustration starts only on request",
        )
        page.click("#scan_play")
        check(page.evaluate("() => scan_timer === null"), "Scanning illustration can be paused")
        page.evaluate(
            "() => {state.draft_rules=blank_rules(); state.draft_rules.phot_g_mean_mag={enabled:true,minimum:20,maximum:21};sync_rule_controls();}"
        )
        previous_maximum = page.evaluate("() => state.draft_rules.phot_g_mean_mag.maximum")
        page.fill("#phot_g_mean_mag_maximum", "19")
        page.locator("#phot_g_mean_mag_maximum").blur()
        check(
            page.evaluate("() => state.draft_rules.phot_g_mean_mag.maximum") == previous_maximum
            and "not saved" in page.locator("#rule_error").inner_text(),
            "Reversed numeric intervals cannot corrupt saved drafts",
        )
        page.select_option("#final_attempt", "attempt_0006")
        page.fill("#why_it_works", "Validation rationale for one final selection.")
        page.fill("#how_to_improve", "Validation discussion of improvements.")
        before = page.evaluate("() => copy(state)")
        with page.expect_download() as event:
            page.click("#export_json")
        answers_path = teaching_part1_preview / "validation_answers.json"
        event.value.save_as(answers_path)
        exported = json.loads(answers_path.read_text())
        check(exported == before, "JSON download preserves the entire answer state")
        graded = check_answers(exported, packet, packet_digest, key)
        check(
            graded["valid"] and len(graded["task1_instructor_review"]) == 30,
            "Independent instructor checker accepts export and leaves evidence for manual review",
        )
        with page.expect_download() as event:
            page.click("#export_text")
        report_path = teaching_part1_preview / "validation_report.txt"
        event.value.save_as(report_path)
        check(
            injection in report_path.read_text() and "TASK 3" in report_path.read_text(),
            "Readable export contains literal evidence, rules, and membership response",
        )
        page.fill("#evidence_note", "Changed after export")
        page.set_input_files("#import_file", answers_path)
        page.wait_for_function(
            "() => document.getElementById('save_status').textContent.includes('Answers restored')"
        )
        check(page.evaluate("() => copy(state)") == exported, "Full export/import round trip")
        check(
            page.evaluate("() => typeof window.injected === 'undefined'"),
            "Imported text cannot execute markup",
        )
        bad_cases = []
        bad = copy.deepcopy(exported)
        bad["packet_sha256"] = "0" * 64
        bad_cases.append(bad)
        bad = copy.deepcopy(exported)
        bad["schema_version"] = "ucd_answers_v1"
        bad_cases.append(bad)
        bad = copy.deepcopy(exported)
        bad["task2_attempts"][0]["counts"]["star"] += 1
        bad_cases.append(bad)
        bad = copy.deepcopy(exported)
        first = next(iter(bad["task1_responses"]))
        bad["task1_responses"][first]["source_id"] = int(bad["task1_responses"][first]["source_id"])
        bad_cases.append(bad)
        bad = copy.deepcopy(exported)
        bad["task2_final_selection"]["attempt_id"] = "attempt_9999"
        bad_cases.append(bad)
        bad = copy.deepcopy(exported)
        bad["task2_attempts"][0]["metrics"]["f1"] += 0.1
        bad_cases.append(bad)
        bad = copy.deepcopy(exported)
        bad["draft_rules"]["phot_g_mean_mag"] = {"enabled": True, "minimum": 21, "maximum": 18}
        bad_cases.append(bad)
        bad = copy.deepcopy(exported)
        bad["task2_attempts"].append(copy.deepcopy(bad["task2_attempts"][0]))
        bad_cases.append(bad)
        for index, bad in enumerate(bad_cases):
            bad_path = teaching_part1_preview / f"invalid_answers_{index}.json"
            bad_path.write_text(json.dumps(bad))
            page.evaluate("() => document.getElementById('import_error').textContent = ''")
            page.set_input_files("#import_file", bad_path)
            page.wait_for_function(
                "() => document.getElementById('import_error').textContent.startsWith('Import rejected')"
            )
            check(
                page.evaluate("() => copy(state)") == exported,
                f"Rejected invalid import retains current work: {index}",
            )
            try:
                check_answers(bad, packet, packet_digest, key)
            except ValueError:
                check(True, f"Instructor checker rejects same invalid submission: {index}")
            else:
                raise AssertionError(f"Instructor checker accepted invalid submission {index}")
        old = copy.deepcopy(exported)
        old["schema_version"] = "bubbletea_answers_v2"
        del old["task2_final_selection"], old["imported_v2_final_rules"]
        old["task2_final_rules"] = {
            "recovery_attempt_id": "attempt_0001",
            "purity_attempt_id": "attempt_0006",
            "recovery_explanation": "An earlier recovery choice.",
            "purity_explanation": injection,
        }
        for attempt in old["task2_attempts"]:
            del attempt["metrics"]["f1"]
        old_path = teaching_part1_preview / "older_version_2_answers.json"
        old_path.write_text(json.dumps(old))
        page.set_input_files("#import_file", old_path)
        page.wait_for_function("() => state.imported_v2_final_rules !== null")
        upgraded = page.evaluate("() => copy(state)")
        check(
            upgraded["task1_responses"] == exported["task1_responses"]
            and upgraded["task2_attempts"] == exported["task2_attempts"]
            and upgraded["imported_v2_final_rules"] == old["task2_final_rules"]
            and upgraded["task2_final_selection"]
            == {"attempt_id": "", "why_it_works": "", "how_to_improve": ""},
            "Version 2 import retains responses, attempts, and old choices; requires a new single final selection",
        )
        check(
            check_answers(old, packet, packet_digest, key)["preserved_version_2_choices"]
            == old["task2_final_rules"],
            "Instructor checker accepts and preserves a valid older submission",
        )
        old_bad = copy.deepcopy(old)
        old_bad["task2_attempts"][0]["metrics"]["purity"] += 0.1
        old_bad_path = teaching_part1_preview / "invalid_older_answers.json"
        old_bad_path.write_text(json.dumps(old_bad))
        page.set_input_files("#import_file", old_bad_path)
        page.wait_for_function(
            "() => document.getElementById('import_error').textContent.startsWith('Import rejected')"
        )
        check(
            page.evaluate("() => copy(state)") == upgraded,
            "Invalid older scores cannot replace the current draft",
        )
        try:
            check_answers(old_bad, packet, packet_digest, key)
        except ValueError:
            check(True, "Instructor checker rejects invalid older scores")
        else:
            raise AssertionError("Invalid older scores were accepted")
        page.set_input_files("#import_file", answers_path)
        page.wait_for_function("() => state.imported_v2_final_rules === null")
        page.screenshot(path=str(teaching_part1_preview / "desktop.png"), full_page=True)
        page.locator(".hero").screenshot(path=str(teaching_part1_preview / "hero.png"))
        page.locator("#task1_view").screenshot(path=str(teaching_part1_preview / "object_view.png"))
        page.locator(".plot_workspace").screenshot(path=str(teaching_part1_preview / "plots.png"))
        page.locator(".scan_lab").screenshot(path=str(teaching_part1_preview / "scan.png"))
        page.locator(".size_lab").screenshot(path=str(teaching_part1_preview / "size.png"))
        page.locator(".reading table").screenshot(
            path=str(teaching_part1_preview / "definitions.png")
        )
        page.locator(".response_panel").screenshot(
            path=str(teaching_part1_preview / "classification.png")
        )
        page.locator(".final_selection").screenshot(
            path=str(teaching_part1_preview / "final_selection.png")
        )
        mathematics = page.locator("details").filter(
            has=page.locator("summary", has_text="Optional mathematics")
        )
        mathematics.locator("summary").click()
        mathematics.screenshot(path=str(teaching_part1_preview / "mathematics.png"))
        check(
            mathematics.locator("math").first.bounding_box()["height"] > 25,
            "Native fractions occupy rendered equation height",
        )
        mathematics.locator("summary").click()
        page.locator("#task3").screenshot(path=str(teaching_part1_preview / "membership.png"))
        page.set_viewport_size({"width": 390, "height": 844})
        check(
            page.evaluate("() => document.documentElement.scrollWidth <= window.innerWidth + 1"),
            "Narrow layout has no document-level horizontal overflow",
        )
        page.locator("#task1_view").screenshot(
            path=str(teaching_part1_preview / "narrow_object.png")
        )
        page.locator("#submission").screenshot(
            path=str(teaching_part1_preview / "narrow_submission.png")
        )
        page.keyboard.press("Tab")
        check(
            page.evaluate("() => document.activeElement !== document.body"),
            "Keyboard focus reaches controls",
        )
        layout_measurements = []
        for width, height in [
            (1440, 900),
            (1366, 768),
            (1100, 620),
            (900, 600),
            (820, 740),
            (390, 844),
        ]:
            layout_context = browser.new_context(
                offline=True, viewport={"width": width, "height": height}, reduced_motion="reduce"
            )
            layout_page = layout_context.new_page()
            layout_page.on("pageerror", lambda error: errors.append(str(error)))
            layout_page.goto(TEACHING_ACTIVITY_HTML.as_uri())
            layout_page.locator("#task1_review").evaluate(
                "item => item.scrollIntoView({block:'start',behavior:'instant'})"
            )
            check(
                layout_page.locator("#task1_properties table").count() == 2
                and layout_page.locator("#task1_properties tr").count() == 15
                and layout_page.locator("#classification input").count() == 4,
                f"Compact layout retains all 15 measurements and four classes: {width}x{height}",
            )
            first_images = layout_page.locator("#task1_images img").evaluate_all(
                "items => items.map(item => item.src)"
            )
            evidence = f"Layout test at {width} by {height}; not student work."

            def check_images_visible(action):
                visible = layout_page.evaluate("""() => {
                    const navigation_bottom=document.querySelector('.chapter_nav').getBoundingClientRect().bottom;
                    return [...document.querySelectorAll('#task1_images img')].every(item => {
                        const box=item.getBoundingClientRect();
                        return box.top>=navigation_bottom && box.bottom<=innerHeight && box.left>=0 && box.right<=innerWidth;
                    });
                }""")
                check(visible, f"Both complete images visible while {action}: {width}x{height}")

            if width > 820:
                tables = [
                    table.bounding_box()
                    for table in layout_page.locator("#task1_properties table").all()
                ]
                check(
                    abs(tables[0]["y"] - tables[1]["y"]) < 1 and tables[1]["x"] > tables[0]["x"],
                    f"Measurements occupy two side-by-side columns: {width}x{height}",
                )
            layout_page.locator("#classification label").filter(
                has=layout_page.locator('input[value="uncertain"]')
            ).click()
            if width > 820:
                check_images_visible("classifying")
            layout_page.fill("#evidence_note", evidence)
            if width > 820:
                check_images_visible("writing evidence")
            layout_page.locator("#next_object").scroll_into_view_if_needed()
            if width > 820:
                check_images_visible("using Next object")
            layout_page.click("#next_object")
            check(
                layout_page.evaluate("current_object") == "task1_02"
                and layout_page.locator("#evidence_note").input_value() == ""
                and layout_page.locator("#task1_images img").evaluate_all(
                    "items => items.map(item => item.src)"
                )
                != first_images
                and "Object 02" in layout_page.locator("#response_object").text_content(),
                f"Next updates images and response identity without carrying answers forward: {width}x{height}",
            )
            if width > 820:
                check_images_visible("reviewing the next object")
                check(
                    layout_page.locator("#classification").bounding_box()["y"] > 45,
                    f"Next returns classification to view: {width}x{height}",
                )
            layout_page.click("#previous_object")
            check(
                layout_page.locator("#evidence_note").input_value() == evidence
                and layout_page.locator(
                    'input[name="classification"][value="uncertain"]'
                ).is_checked(),
                f"Previous restores the original classification and evidence: {width}x{height}",
            )
            check(
                layout_page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"),
                f"No layout overflow: {width}x{height}",
            )
            if width <= 820:
                image_box = layout_page.locator("#task1_images").bounding_box()
                response_box = layout_page.locator(".response_panel").bounding_box()
                check(
                    image_box["y"] + image_box["height"] <= response_box["y"],
                    f"Narrow layout stacks images before answers without overlap: {width}x{height}",
                )
            layout_measurements.append(
                {
                    "width": width,
                    "height": height,
                    "side_by_side": width > 820,
                    "image_visibility_checks": width > 820,
                }
            )
            layout_page.screenshot(
                path=str(teaching_part1_preview / f"task1_layout_{width}_{height}.png")
            )
            layout_context.close()
        denied = browser.new_context(offline=True, accept_downloads=True, reduced_motion="reduce")
        denied.add_init_script(
            "Object.defineProperty(window, 'localStorage', {get(){throw new Error('Storage disabled for validation');}})"
        )
        blocked_page = denied.new_page()
        blocked_page.goto(TEACHING_ACTIVITY_HTML.as_uri())
        check(
            "unavailable" in blocked_page.locator("#save_status").inner_text(),
            "Blocked storage has an explicit warning",
        )
        check(
            blocked_page.evaluate(
                "() => scan_timer === null && matchMedia('(prefers-reduced-motion: reduce)').matches"
            ),
            "Reduced-motion mode starts with no animation",
        )
        blocked_page.fill("#student_identifier", "storage_denied")
        with blocked_page.expect_download() as event:
            blocked_page.click("#export_json")
        event.value.save_as(teaching_part1_preview / "storage_denied_answers.json")
        check(
            json.loads((teaching_part1_preview / "storage_denied_answers.json").read_text())[
                "student_identifier"
            ]
            == "storage_denied",
            "Answers remain exportable with browser storage denied",
        )
        timed_context = browser.new_context(offline=True, viewport={"width": 1440, "height": 1000})
        timed_page = timed_context.new_page()
        session = timed_context.new_cdp_session(timed_page)
        session.send("Emulation.setCPUThrottlingRate", {"rate": 4})
        initial = time.perf_counter()
        timed_page.goto(TEACHING_ACTIVITY_HTML.as_uri())
        timed_page.wait_for_function(
            "() => document.querySelectorAll('#plots canvas').length === 4"
        )
        startup_seconds = time.perf_counter() - initial
        timings = []
        for _ in range(6):
            timings.append(
                timed_page.evaluate(
                    "() => new Promise(resolve => {const start=performance.now();evaluate_selection();requestAnimationFrame(()=>requestAnimationFrame(()=>resolve(performance.now()-start)));})"
                )
            )
        evaluation_median_ms = statistics.median(timings[1:])
        check(startup_seconds < 5, "Throttled complete-page startup below 5 seconds")
        check(
            evaluation_median_ms < 300,
            "Throttled evaluation plus two animation frames below 300 ms",
        )
        check(
            not remote_requests and not errors, "No mandatory remote requests or JavaScript errors"
        )
        browser_version = browser.version
        browser.close()
    report = {
        "activity_version": packet["activity_version"],
        "packet_sha256": packet_digest,
        "passed": len(checks),
        "check_categories": "data integrity, every derived astrometry value, offline gallery, independent scoring, imports, storage, keyboard/narrow UI, full-page performance",
        "browser": browser_version,
        "platform": platform.platform(),
        "cpu_throttle": 4,
        "startup_seconds": startup_seconds,
        "evaluation_and_frames_median_ms": evaluation_median_ms,
        "evaluation_trials_ms": timings,
        "task1_layout_viewports": layout_measurements,
        "mandatory_remote_requests": remote_requests,
        "javascript_errors": errors,
        "elapsed_seconds": time.perf_counter() - started,
        "limitations": [
            "Windows and other browsers not tested",
            "Final pedagogical assessment belongs to the instructor",
            "Visual source review recorded separately from automated image checks",
        ],
    }
    teaching_part1_validation_report.write_text(json.dumps(report, indent=2) + "\n")
    logger.info(
        "Passed %d checks; throttled startup %.3f s, evaluation+frames median %.1f ms",
        len(checks),
        startup_seconds,
        evaluation_median_ms,
    )


if __name__ == "__main__":
    main()
