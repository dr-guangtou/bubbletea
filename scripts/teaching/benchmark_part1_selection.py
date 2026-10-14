"""Measure achievable classroom range-cut scores without changing reference data.

Inputs: the frozen Part I teaching packet. Output: an instructor-only JSON report.
Run --pilot to test a small subset of the threshold combinations first. The full
grid is deliberately bounded; it is not a global optimum or held-out research
validation. Every cut uses a field exposed in the student range controls.
"""

import argparse
import hashlib
import itertools
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
from sklearn.metrics import f1_score

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import teaching_part1_packet, teaching_part1_selection_trial
from scripts.teaching.check_part1_answers import feature_keys, score_rules

logger = logging.getLogger(__name__)


def blank_rules():
    return {name: {"enabled": False, "minimum": None, "maximum": None} for name in feature_keys}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pilot", action="store_true", help="Check 16 combinations; do not write a report"
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    started = time.perf_counter()
    content = teaching_part1_packet.read_bytes()
    packet = json.loads(content)
    columns = {name: index for index, name in enumerate(packet["catalog_columns"])}
    rows = packet["catalog_rows"]
    labels = np.array([row[columns["reference_class"]] for row in rows])
    positive = labels == "ucd"
    known = labels != "candidate"
    positive_count = int(positive.sum())
    grid = {
        "phot_bp_rp_excess_factor": (
            "minimum",
            [None, 1.2, 1.4, 1.6, 1.8, 2, 2.2, 2.5, 3, 3.5, 4, 5],
        ),
        "proper_motion_significance": ("maximum", [None, 2, 3, 4, 5, 7, 10, 15, 20]),
        "astrometric_excess_noise": ("minimum", [None, 0.5, 1, 2, 3, 5, 10]),
        "phot_g_mean_mag": ("maximum", [None, 19, 20, 20.5, 21, 21.5]),
    }
    if args.pilot:
        grid = {name: (direction, values[:2]) for name, (direction, values) in grid.items()}
    masks = {}
    for name, (direction, boundaries) in grid.items():
        values = np.array(
            [row[columns[name]] if row[columns[name]] is not None else np.nan for row in rows]
        )
        for boundary in boundaries:
            masks[name, boundary] = (
                np.ones(len(rows), dtype=bool)
                if boundary is None
                else (values >= boundary if direction == "minimum" else values <= boundary)
            )
    best, evaluated = None, 0
    for boundaries in itertools.product(*(values for _, values in grid.values())):
        selected = np.logical_and.reduce(
            [masks[name, boundary] for name, boundary in zip(grid, boundaries, strict=True)]
        )
        true_positive = int(np.count_nonzero(selected & positive))
        selected_known = int(np.count_nonzero(selected & known))
        score = 2 * true_positive / (positive_count + selected_known)
        active = sum(boundary is not None for boundary in boundaries)
        comparison = (score, -active, true_positive)
        if best is None or comparison > best["comparison"]:
            best = {"comparison": comparison, "boundaries": boundaries, "selected": selected}
        evaluated += 1
    rules = blank_rules()
    for name, boundary in zip(grid, best["boundaries"], strict=True):
        if boundary is not None:
            rules[name]["enabled"] = True
            rules[name][grid[name][0]] = boundary
    result = score_rules(packet, rules, "exclude")
    independent_f1 = f1_score(positive[known], best["selected"][known], zero_division=0)
    if not np.isclose(independent_f1, result["metrics"]["f1"], atol=1e-14, rtol=0):
        raise AssertionError("Independent F1 implementations disagree")
    all_result = score_rules(packet, blank_rules(), "keep")
    empty_rules = blank_rules()
    empty_rules["phot_g_mean_mag"] = {"enabled": True, "minimum": -1, "maximum": 0}
    empty_result = score_rules(packet, empty_rules, "exclude")
    one_rules = blank_rules()
    for row in rows:
        value = row[columns["phot_g_mean_mag"]]
        if (
            row[columns["reference_class"]] == "ucd"
            and sum(other[columns["phot_g_mean_mag"]] == value for other in rows) == 1
        ):
            one_rules["phot_g_mean_mag"] = {"enabled": True, "minimum": value, "maximum": value}
            break
    else:
        raise AssertionError("No unique positive magnitude for the one-object control")
    one_result = score_rules(packet, one_rules, "exclude")
    if one_result["counts"]["total_selected"] != 1 or one_result["counts"]["ucd"] != 1:
        raise AssertionError("The one-object control did not select exactly one UCD")
    elapsed = time.perf_counter() - started
    report = {
        "packet_sha256": hashlib.sha256(content).hexdigest(),
        "task2_counts": packet["sampling"]["task2_counts"],
        "scope": "Fixed teaching sample; optimization and evaluation on the same objects. Not a global optimum, held-out test, or real-sky purity estimate.",
        "grid": grid,
        "combinations_tested": evaluated,
        "missing_policy": "exclude",
        "best_in_grid": {"rules": rules, **result},
        "independent_sklearn_f1": float(independent_f1),
        "controls": {
            "select_everything": all_result,
            "select_nothing": {"rules": empty_rules, **empty_result},
            "select_one_known_ucd": {"rules": one_rules, **one_result},
        },
        "runtime_seconds": elapsed,
        "grading_note": "Keep thresholds instructor-only. Do not require this particular solution or claim it is best possible. Review explanations as well as metrics.",
    }
    logger.info(
        "%s combinations in %.3f s: F1 %.6f, purity %.6f, completeness %.6f; counts %s",
        evaluated,
        elapsed,
        result["metrics"]["f1"],
        result["metrics"]["purity"],
        result["metrics"]["completeness"],
        result["counts"],
    )
    if not args.pilot:
        teaching_part1_selection_trial.parent.mkdir(parents=True, exist_ok=True)
        teaching_part1_selection_trial.write_text(
            json.dumps(report, indent=2, allow_nan=False) + "\n"
        )
        logger.info("Wrote %s", teaching_part1_selection_trial)


if __name__ == "__main__":
    main()
