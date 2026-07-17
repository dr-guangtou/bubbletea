"""Validate shared frozen-selector parity and the Phase IV query contract."""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    LITERATURE_VALIDATION,
    SELECTOR_DEVELOPMENT_FEATURES,
    SPECTROSCOPIC_STELLAR_REFERENCE_MATCHES,
)
from scripts.phase4_search.radial_search import build_query
from scripts.utils.point_source_selector import (
    MODEL_FEATURES,
    RAW_GAIA_COLUMNS,
    load_frozen_selector,
)

PREDICTIONS = LITERATURE_VALIDATION / "point_source_logistic_development_predictions_v1.csv"
OUTPUT = LITERATURE_VALIDATION / "point_source_logistic_integration_validation_v1.json"


def main() -> None:
    """Require exact stored-probability parity and an unfiltered raw Gaia query."""
    expected = pd.read_csv(PREDICTIONS, dtype={"gaia_dr3_id": str})
    development = pd.read_csv(
        SELECTOR_DEVELOPMENT_FEATURES,
        dtype={"gaia_dr3_id": str},
    )
    development = development.loc[
        development["label_subtype"].isin(
            ["ucd_confirmed", "gaia_non_single_star", "spectroscopic_qso"]
        )
    ].copy()
    stars = pd.read_csv(SPECTROSCOPIC_STELLAR_REFERENCE_MATCHES, dtype={"source_id": str})
    rows = pd.concat([development, stars], ignore_index=True)
    selector = load_frozen_selector()
    actual = selector.score(rows)
    maximum_difference = float(
        np.max(np.abs(actual["point_source_logistic_probability"] - expected["probability"]))
    )
    query = build_query(10.0, -20.0, 0.1)
    checks = {
        "feature_contract": list(actual[MODEL_FEATURES].columns) == MODEL_FEATURES,
        "exact_probability_parity": maximum_difference <= 1e-15,
        "decision_parity": actual["point_source_logistic_selected"].tolist()
        == expected["selected"].astype(bool).tolist(),
        "version_recorded": actual["point_source_selector_version"]
        .eq(selector.model_version)
        .all(),
        "all_raw_columns_queried": all(column in query for column in RAW_GAIA_COLUMNS),
        "no_legacy_excess_noise_prefilter": "astrometric_excess_noise >" not in query,
        "no_legacy_proper_motion_prefilter": "SQRT(pmra" not in query,
    }
    checks = {name: bool(value) for name, value in checks.items()}
    report = {
        "integration_version": "point_source_logistic_integration_v1",
        "model_version": selector.model_version,
        "maximum_probability_difference": maximum_difference,
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if not all(checks.values()):
        raise RuntimeError(f"Frozen-selector integration validation failed: {checks}")


if __name__ == "__main__":
    main()
