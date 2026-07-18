"""Apply the frozen Gaia point-source logistic selector with exact feature parity."""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from scripts.config import POINT_SOURCE_LOGISTIC_MODEL, POINT_SOURCE_LOGISTIC_MODEL_MANIFEST

SELECTOR_VERSION = "point_source_logistic_model_v1"
MINIMUM_G_MAGNITUDE = 11.26291847229004
MAXIMUM_G_MAGNITUDE = 21.75798797607422
RAW_GAIA_COLUMNS = [
    "source_id",
    "ra",
    "dec",
    "phot_g_mean_mag",
    "phot_bp_mean_mag",
    "phot_rp_mean_mag",
    "phot_bp_rp_excess_factor",
    "astrometric_excess_noise",
    "astrometric_excess_noise_sig",
    "parallax",
    "parallax_error",
    "pmra",
    "pmra_error",
    "pmdec",
    "pmdec_error",
    "pmra_pmdec_corr",
    "ruwe",
    "ipd_frac_multi_peak",
    "ipd_frac_odd_win",
]
MODEL_FEATURES = [
    "log1p_astrometric_excess_noise",
    "log1p_astrometric_excess_noise_sig",
    "phot_bp_rp_excess_factor",
    "bp_rp",
    "log_ruwe",
    "log1p_ipd_frac_multi_peak",
    "log1p_ipd_frac_odd_win",
    "log1p_absolute_parallax_zero_significance",
    "log1p_proper_motion_zero_significance",
]


@dataclass(frozen=True)
class FrozenPointSourceSelector:
    """Loaded model, threshold, and immutable version metadata."""

    model: object
    threshold: float
    model_version: str

    def score(self, rows: pd.DataFrame) -> pd.DataFrame:
        """Return all input rows with frozen probabilities and decisions."""
        scored = add_model_features(rows)
        scored["point_source_logistic_probability"] = self.model.predict_proba(
            scored[MODEL_FEATURES]
        )[:, 1]
        scored["point_source_logistic_selected"] = scored["point_source_logistic_probability"].ge(
            self.threshold
        )
        scored["point_source_selector_version"] = self.model_version
        return scored


def add_model_features(rows: pd.DataFrame) -> pd.DataFrame:
    """Derive the frozen nine-feature contract while preserving null values."""
    rows = rows.copy()
    rows["bp_rp"] = rows["phot_bp_mean_mag"] - rows["phot_rp_mean_mag"]
    rows["absolute_parallax_zero_significance"] = rows["parallax"].abs() / rows[
        "parallax_error"
    ].where(rows["parallax_error"].gt(0))
    standardized_pmra = rows["pmra"] / rows["pmra_error"]
    standardized_pmdec = rows["pmdec"] / rows["pmdec_error"]
    correlation = rows["pmra_pmdec_corr"]
    valid_motion = (
        rows["pmra_error"].gt(0)
        & rows["pmdec_error"].gt(0)
        & np.isfinite(standardized_pmra)
        & np.isfinite(standardized_pmdec)
        & np.isfinite(correlation)
        & correlation.abs().lt(1)
    )
    squared_significance = (
        np.square(standardized_pmra)
        + np.square(standardized_pmdec)
        - 2 * correlation * standardized_pmra * standardized_pmdec
    ) / (1 - np.square(correlation))
    rows["proper_motion_zero_significance"] = np.sqrt(
        squared_significance.clip(lower=0).where(valid_motion)
    )
    rows["log1p_astrometric_excess_noise"] = np.log1p(
        rows["astrometric_excess_noise"].clip(lower=0)
    )
    rows["log1p_astrometric_excess_noise_sig"] = np.log1p(
        rows["astrometric_excess_noise_sig"].clip(lower=0)
    )
    rows["log_ruwe"] = np.log(rows["ruwe"].where(rows["ruwe"].gt(0)))
    for source in [
        "ipd_frac_multi_peak",
        "ipd_frac_odd_win",
        "absolute_parallax_zero_significance",
        "proper_motion_zero_significance",
    ]:
        rows[f"log1p_{source}"] = np.log1p(rows[source].clip(lower=0))
    return rows


def load_frozen_selector(
    model_path: Path = POINT_SOURCE_LOGISTIC_MODEL,
    manifest_path: Path = POINT_SOURCE_LOGISTIC_MODEL_MANIFEST,
) -> FrozenPointSourceSelector:
    """Load v1 only after verifying its version, feature contract, and digest."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    checks = {
        "model_version": manifest["model_version"] == SELECTOR_VERSION,
        "input_features": manifest["input_features"] == MODEL_FEATURES,
        "model_digest": manifest["artifacts"]["model_sha256"]
        == hashlib.sha256(model_path.read_bytes()).hexdigest(),
    }
    if not all(checks.values()):
        raise RuntimeError(f"Frozen point-source selector contract failed: {checks}")
    return FrozenPointSourceSelector(
        model=joblib.load(model_path),
        threshold=float(manifest["threshold"]),
        model_version=manifest["model_version"],
    )
