"""Fit and serialize the approved point-source logistic model on development data."""

import json
import sys
from pathlib import Path

import joblib

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    LITERATURE_VALIDATION,
    SELECTOR_DEVELOPMENT_FEATURES,
    SPECTROSCOPIC_STELLAR_REFERENCE_MATCHES,
)
from scripts.phase1_literature.analyze_logistic_regularization_convergence import (
    build_logistic_model,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase1_literature.compare_point_source_ml import (
    MODEL_FEATURES,
    equal_cohort_weights,
    load_cohorts,
    macro_priority_retention,
)

POLICY_PATH = Path("data/literature/sources/point_source_logistic_policy_v1.json")
MODEL_OUTPUT = LITERATURE_VALIDATION / "point_source_logistic_model_v1.joblib"
MODEL_MANIFEST_OUTPUT = LITERATURE_VALIDATION / "point_source_logistic_model_v1.json"
PREDICTIONS_OUTPUT = LITERATURE_VALIDATION / "point_source_logistic_development_predictions_v1.csv"


def main() -> None:
    """Fit the frozen policy and export transparent model artifacts."""
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    if (
        policy["approval_status"] != "approved_by_project_lead"
        or policy["regularization"]["status"] != "frozen"
        or policy["threshold"]["status"] != "frozen"
        or policy["validation_partition"]["status"] != "sealed_and_uninspected"
    ):
        raise RuntimeError("Point-source model policy is not fully approved")
    rows = load_cohorts(SELECTOR_DEVELOPMENT_FEATURES, SPECTROSCOPIC_STELLAR_REFERENCE_MATCHES)
    rows = rows.loc[rows["fit_role"].eq("model_fit")].reset_index(drop=True)
    regularization_c = float(policy["regularization"]["regularization_c"])
    threshold = float(policy["threshold"]["value"])
    model = build_logistic_model(regularization_c)
    model.fit(
        rows[MODEL_FEATURES],
        rows["target"],
        model__sample_weight=equal_cohort_weights(rows),
    )
    probabilities = model.predict_proba(rows[MODEL_FEATURES])[:, 1]
    selected = probabilities >= threshold
    predictions = rows[["row_id", "gaia_dr3_id", "ml_group", "ml_cohort", "target"]].copy()
    predictions["probability"] = probabilities
    predictions["selected"] = selected
    predictions.to_csv(PREDICTIONS_OUTPUT, index=False)

    MODEL_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_OUTPUT)
    preprocessing = model.named_steps["preprocessing"]
    feature_pipeline = preprocessing.named_transformers_["features"]
    imputer = feature_pipeline.named_steps["imputer"]
    scaler = feature_pipeline.named_steps["scale"]
    estimator = model.named_steps["model"]
    transformed_features = preprocessing.get_feature_names_out().tolist()
    positive = rows["target"].eq(1).to_numpy()
    manifest = {
        "model_version": "point_source_logistic_model_v1",
        "fit_scope": "benchmark_v3_development_model_fit_rows_only",
        "validation_partition_inspected": False,
        "policy": str(POLICY_PATH),
        "policy_sha256": calculate_sha256(POLICY_PATH),
        "regularization_c": regularization_c,
        "threshold": threshold,
        "input_features": MODEL_FEATURES,
        "transformed_features": transformed_features,
        "imputer_statistics": {
            feature: float(value)
            for feature, value in zip(MODEL_FEATURES, imputer.statistics_, strict=True)
        },
        "missing_indicator_input_indices": imputer.indicator_.features_.astype(int).tolist(),
        "scaler_mean": {
            feature: float(value)
            for feature, value in zip(transformed_features, scaler.mean_, strict=True)
        },
        "scaler_scale": {
            feature: float(value)
            for feature, value in zip(transformed_features, scaler.scale_, strict=True)
        },
        "coefficients": {
            feature: float(value)
            for feature, value in zip(transformed_features, estimator.coef_[0], strict=True)
        },
        "intercept": float(estimator.intercept_[0]),
        "counts": {
            "fit_rows": len(rows),
            "reliable_ucds": int(positive.sum()),
            "priority_contaminants": int((~positive).sum()),
        },
        "development_apparent_metrics": {
            "reliable_ucd_recall": float(selected[positive].mean()),
            "macro_priority_retention": macro_priority_retention(rows, selected),
        },
        "inputs": {
            "development_features_sha256": calculate_sha256(SELECTOR_DEVELOPMENT_FEATURES),
            "stellar_matches_sha256": calculate_sha256(SPECTROSCOPIC_STELLAR_REFERENCE_MATCHES),
        },
        "artifacts": {
            "model": str(MODEL_OUTPUT),
            "model_sha256": calculate_sha256(MODEL_OUTPUT),
            "predictions": str(PREDICTIONS_OUTPUT),
            "predictions_sha256": calculate_sha256(PREDICTIONS_OUTPUT),
        },
        "decision_status": "final_development_model_fitted_validation_still_sealed",
    }
    MODEL_MANIFEST_OUTPUT.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
