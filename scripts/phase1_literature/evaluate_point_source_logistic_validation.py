"""Apply the frozen point-source model once to the authorized validation partition."""

import json
import sys
from pathlib import Path

import joblib
import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import LITERATURE_SOURCES, LITERATURE_VALIDATION
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase1_literature.compare_point_source_ml import MODEL_FEATURES, add_model_features

AUTHORIZATION = LITERATURE_SOURCES / "point_source_validation_authorization_v1.json"
FEATURES = LITERATURE_VALIDATION / "gaia_selector_validation_features_v1.csv"
FEATURE_MANIFEST = LITERATURE_VALIDATION / "gaia_selector_validation_features_v1_manifest.json"
MODEL = LITERATURE_VALIDATION / "point_source_logistic_model_v1.joblib"
MODEL_MANIFEST = LITERATURE_VALIDATION / "point_source_logistic_model_v1.json"
PREDICTIONS_OUTPUT = LITERATURE_VALIDATION / "point_source_logistic_validation_predictions_v1.csv"
SUMMARY_OUTPUT = LITERATURE_VALIDATION / "point_source_logistic_validation_summary_v1.json"


def main() -> None:
    """Evaluate frozen probabilities and report predeclared cohort metrics."""
    authorization = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
    model_manifest = json.loads(MODEL_MANIFEST.read_text(encoding="utf-8"))
    feature_manifest = json.loads(FEATURE_MANIFEST.read_text(encoding="utf-8"))
    if authorization["threshold"] != model_manifest["threshold"]:
        raise RuntimeError("Authorized and serialized thresholds differ")
    if feature_manifest["authorization_sha256"] != calculate_sha256(AUTHORIZATION):
        raise RuntimeError("Validation features do not match the authorization")
    rows = pd.read_csv(FEATURES, dtype={"gaia_dr3_id": str})
    rows = add_model_features(rows)
    model = joblib.load(MODEL)
    probability = model.predict_proba(rows[MODEL_FEATURES])[:, 1]
    selected = probability >= float(model_manifest["threshold"])
    predictions = rows[
        [
            "benchmark_id",
            "gaia_dr3_id",
            "source_cohort",
            "label",
            "label_subtype",
            "confidence_tier",
            "primary_label_eligible",
            "sensitivity_label_eligible",
            "partition_group",
        ]
    ].copy()
    predictions["probability"] = probability
    predictions["selected"] = selected
    predictions.to_csv(PREDICTIONS_OUTPUT, index=False)

    cohort_metrics = {}
    for subtype, group in predictions.groupby("label_subtype", sort=True):
        cohort_metrics[str(subtype)] = {
            "row_count": len(group),
            "selected_count": int(group["selected"].sum()),
            "selected_fraction": float(group["selected"].mean()),
        }
    reliable_ucds = (
        predictions["label_subtype"].eq("ucd_confirmed") & predictions["primary_label_eligible"]
    )
    priority_subtypes = ["gaia_non_single_star", "spectroscopic_qso"]
    priority_fractions = [
        float(predictions.loc[predictions["label_subtype"].eq(subtype), "selected"].mean())
        for subtype in priority_subtypes
        if predictions["label_subtype"].eq(subtype).any()
    ]
    summary = {
        "evaluation_version": "point_source_logistic_validation_v1",
        "evaluation_status": "one_time_frozen_validation_complete_no_retuning_authorized",
        "model_version": model_manifest["model_version"],
        "regularization_c": model_manifest["regularization_c"],
        "threshold": model_manifest["threshold"],
        "counts": {"validation_rows": len(predictions), "reliable_ucds": int(reliable_ucds.sum())},
        "primary_metrics": {
            "reliable_ucd_recall": float(predictions.loc[reliable_ucds, "selected"].mean()),
            "macro_available_priority_retention": float(
                sum(priority_fractions) / len(priority_fractions)
            ),
        },
        "cohort_metrics": cohort_metrics,
        "inputs": {
            "authorization_sha256": calculate_sha256(AUTHORIZATION),
            "features_sha256": calculate_sha256(FEATURES),
            "feature_manifest_sha256": calculate_sha256(FEATURE_MANIFEST),
            "model_sha256": calculate_sha256(MODEL),
            "model_manifest_sha256": calculate_sha256(MODEL_MANIFEST),
        },
        "predictions_sha256": calculate_sha256(PREDICTIONS_OUTPUT),
        "future_policy": "no_retuning; any model change requires a new independent validation cohort",
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
