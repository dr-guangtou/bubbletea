"""Validate the immutable one-time point-source validation evaluation."""

import json
import sys
from pathlib import Path

import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import LITERATURE_SOURCES, LITERATURE_VALIDATION
from scripts.phase1_literature.audit_reference_data import calculate_sha256

AUTHORIZATION = LITERATURE_SOURCES / "point_source_validation_authorization_v1.json"
PREDICTIONS = LITERATURE_VALIDATION / "point_source_logistic_validation_predictions_v1.csv"
FEATURES = LITERATURE_VALIDATION / "gaia_selector_validation_features_v1.csv"
SUMMARY = LITERATURE_VALIDATION / "point_source_logistic_validation_summary_v1.json"
OUTPUT = LITERATURE_VALIDATION / "point_source_logistic_validation_validation_v1.json"


def main() -> None:
    """Reproduce frozen metrics and verify authorization and artifact contracts."""
    authorization = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    rows = pd.read_csv(PREDICTIONS, dtype={"gaia_dr3_id": str})
    features = pd.read_csv(FEATURES, dtype={"gaia_dr3_id": str})
    confirmed = rows["label_subtype"].eq("ucd_confirmed") & rows["primary_label_eligible"]
    nss = rows["label_subtype"].eq("gaia_non_single_star")
    qso = rows["label_subtype"].eq("spectroscopic_qso")
    reproduced_recall = float(rows.loc[confirmed, "selected"].mean())
    reproduced_priority_retention = float(
        (rows.loc[nss, "selected"].mean() + rows.loc[qso, "selected"].mean()) / 2.0
    )
    checks = {
        "authorization_approved": authorization["authorization_status"]
        == "approved_by_project_lead",
        "retuning_prohibited": authorization["retuning_after_evaluation"] == "prohibited",
        "authorization_digest": summary["inputs"]["authorization_sha256"]
        == calculate_sha256(AUTHORIZATION),
        "prediction_digest": summary["predictions_sha256"] == calculate_sha256(PREDICTIONS),
        "validation_row_count": len(rows) == 721,
        "unique_gaia_identifiers": rows["gaia_dr3_id"].is_unique,
        "validation_partition_only": set(features["partition"]) == {"validation"},
        "feature_prediction_identity_parity": rows["benchmark_id"].tolist()
        == features["benchmark_id"].tolist(),
        "reliable_ucd_count": int(confirmed.sum()) == 23,
        "reliable_ucd_recall_reproduced": reproduced_recall
        == summary["primary_metrics"]["reliable_ucd_recall"],
        "priority_retention_reproduced": reproduced_priority_retention
        == summary["primary_metrics"]["macro_available_priority_retention"],
        "frozen_model_contract": summary["regularization_c"] == 1000.0
        and summary["threshold"] == 0.8277833628791744,
        "evaluation_closed": summary["evaluation_status"]
        == "one_time_frozen_validation_complete_no_retuning_authorized",
    }
    checks = {name: bool(passed) for name, passed in checks.items()}
    report = {
        "evaluation_version": summary["evaluation_version"],
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "failed_count": len(checks) - sum(checks.values()),
        "reproduced_reliable_ucd_recall": reproduced_recall,
        "reproduced_macro_available_priority_retention": reproduced_priority_retention,
        "checks": checks,
    }
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if not all(checks.values()):
        raise RuntimeError(f"Frozen validation verification failed: {checks}")


if __name__ == "__main__":
    main()
