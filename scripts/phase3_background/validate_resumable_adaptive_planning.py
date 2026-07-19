"""Validate that interrupted adaptive planning resumes from saved count nodes."""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter
from unittest.mock import patch

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import GAIA_RESUMABLE_PLANNING_VALIDATION
from scripts.phase3_background.adaptive_gaia_retrieval import (
    AdaptiveStrip,
    count_query,
    plan_adaptive_strips,
    query_sha256,
)

VALIDATION_VERSION = "gaia_resumable_planning_validation_v1"


class ControlledPlanningStop(RuntimeError):
    """Stop the first synthetic planning pass after saved progress exists."""


def main() -> None:
    """Interrupt and resume one deterministic synthetic adaptive plan."""
    started = perf_counter()
    counts = {"r": 12, "r0": 4, "r1": 8, "r10": 3, "r11": 5}
    first_pass_counted_ids = []
    second_pass_counted_ids = []

    def first_measure(service: object, base_where: str, strip: AdaptiveStrip) -> tuple[int, str]:
        del service
        first_pass_counted_ids.append(strip.strip_id)
        if strip.strip_id == "r10":
            raise ControlledPlanningStop("controlled stop before the fourth count")
        query = count_query(base_where, strip)
        return counts[strip.strip_id], query_sha256(query)

    def second_measure(service: object, base_where: str, strip: AdaptiveStrip) -> tuple[int, str]:
        del service
        second_pass_counted_ids.append(strip.strip_id)
        query = count_query(base_where, strip)
        return counts[strip.strip_id], query_sha256(query)

    with TemporaryDirectory() as temporary_directory:
        progress_path = Path(temporary_directory) / "measured_plan.csv"
        controlled_stop_observed = False
        try:
            with patch(
                "scripts.phase3_background.adaptive_gaia_retrieval.measure_strip_count",
                side_effect=first_measure,
            ):
                plan_adaptive_strips(
                    object(),
                    "synthetic_where",
                    0.0,
                    1.0,
                    5,
                    progress_path=progress_path,
                )
        except ControlledPlanningStop:
            controlled_stop_observed = True
        saved_node_count_after_stop = sum(1 for _ in progress_path.read_text().splitlines()) - 1
        with patch(
            "scripts.phase3_background.adaptive_gaia_retrieval.measure_strip_count",
            side_effect=second_measure,
        ):
            completed_plan = plan_adaptive_strips(
                object(),
                "synthetic_where",
                0.0,
                1.0,
                5,
                progress_path=progress_path,
            )
        final_saved_node_count = sum(1 for _ in progress_path.read_text().splitlines()) - 1
    leaf_counts = [node.measured_source_count for node in completed_plan if node.is_leaf]
    checks = {
        "controlled_stop_observed": controlled_stop_observed,
        "three_nodes_saved_before_stop": saved_node_count_after_stop == 3,
        "first_pass_reached_only_expected_nodes": first_pass_counted_ids
        == ["r", "r0", "r1", "r10"],
        "restart_counted_only_missing_nodes": second_pass_counted_ids == ["r10", "r11"],
        "completed_plan_has_five_nodes": len(completed_plan) == 5,
        "final_progress_has_five_nodes": final_saved_node_count == 5,
        "leaf_counts_conserve_root": sum(leaf_counts) == completed_plan[0].measured_source_count,
        "all_leaf_counts_within_limit": max(leaf_counts) <= 5,
    }
    checks = {name: bool(value) for name, value in checks.items()}
    report = {
        "validation_version": VALIDATION_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "plain_language_result": (
            "The interrupted first pass saved three completed count nodes. The restart "
            "reused them and queried only the two missing nodes."
        ),
        "archive_queries_executed": 0,
        "elapsed_seconds": perf_counter() - started,
        "first_pass_counted_ids": first_pass_counted_ids,
        "second_pass_counted_ids": second_pass_counted_ids,
        "saved_node_count_after_stop": saved_node_count_after_stop,
        "final_saved_node_count": final_saved_node_count,
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    GAIA_RESUMABLE_PLANNING_VALIDATION.write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"Resumable planning validation failed: {checks}")


if __name__ == "__main__":
    main()
