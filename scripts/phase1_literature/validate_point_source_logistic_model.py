"""Validate serialization, parity, provenance, and blind safety of the final model."""

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    LITERATURE_VALIDATION,
    SELECTOR_DEVELOPMENT_FEATURES,
    SPECTROSCOPIC_STELLAR_REFERENCE_MATCHES,
    VALIDATION_BENCHMARK,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase1_literature.compare_point_source_ml import MODEL_FEATURES, load_cohorts

MODEL = LITERATURE_VALIDATION / "point_source_logistic_model_v1.joblib"
MANIFEST = LITERATURE_VALIDATION / "point_source_logistic_model_v1.json"
PREDICTIONS = LITERATURE_VALIDATION / "point_source_logistic_development_predictions_v1.csv"
OUTPUT = LITERATURE_VALIDATION / "point_source_logistic_model_validation_v1.json"


def main() -> None:
    """Reload the model and verify exact development prediction parity."""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    predictions = pd.read_csv(PREDICTIONS, dtype={"gaia_dr3_id": str})
    rows = load_cohorts(SELECTOR_DEVELOPMENT_FEATURES, SPECTROSCOPIC_STELLAR_REFERENCE_MATCHES)
    rows = rows.loc[rows["fit_role"].eq("model_fit")].reset_index(drop=True)
    benchmark = pd.read_csv(VALIDATION_BENCHMARK, dtype={"gaia_dr3_id": str})
    validation_ids = set(benchmark.loc[benchmark["partition"].eq("validation"), "gaia_dr3_id"])
    model = joblib.load(MODEL)
    reloaded_probabilities = model.predict_proba(rows[MODEL_FEATURES])[:, 1]
    maximum_probability_difference = float(
        np.max(np.abs(reloaded_probabilities - predictions["probability"].to_numpy()))
    )
    checks = {
        "model_digest": manifest["artifacts"]["model_sha256"] == calculate_sha256(MODEL),
        "prediction_digest": manifest["artifacts"]["predictions_sha256"]
        == calculate_sha256(PREDICTIONS),
        "row_identity_parity": predictions["row_id"].tolist() == rows["row_id"].tolist(),
        "exact_prediction_parity": maximum_probability_difference <= 1e-15,
        "threshold_parity": predictions["selected"].to_numpy().astype(bool).tolist()
        == (reloaded_probabilities >= manifest["threshold"]).tolist(),
        "no_validation_gaia_identifier_in_fit": not set(rows["gaia_dr3_id"]).intersection(
            validation_ids
        ),
        "feature_contract": manifest["input_features"] == MODEL_FEATURES,
        "validation_partition_not_inspected": manifest["validation_partition_inspected"] is False,
    }
    checks = {name: bool(passed) for name, passed in checks.items()}
    report = {
        "model_version": manifest["model_version"],
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "failed_count": len(checks) - sum(checks.values()),
        "maximum_probability_difference": maximum_probability_difference,
        "checks": checks,
    }
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if not all(checks.values()):
        raise RuntimeError(f"Final model validation failed: {checks}")


if __name__ == "__main__":
    main()
