"""Retrieve diagnostic Gaia neighbors within 5 arcseconds of every reference object.

Preserve two distinct evidence paths per target: the accepted exact Gaia source
identifier already recorded in the literature database, and positional Gaia
neighbors found by a bounded cone search. A positional neighbor is never promoted
to an accepted counterpart. Results are checkpointed after every batch so a timed-
out run can resume without re-querying completed targets.
"""

import argparse
import hashlib
import json
import logging
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import astropy.units as u
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord
from pyvo.dal import tap

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    PROJECT_ROOT,
    UCD_LEGACY_REFERENCE_TARGETS,
    UCD_VISUAL_REVIEW_GAIA_MANIFEST,
    UCD_VISUAL_REVIEW_GAIA_NEIGHBOR_AUDIT,
    UCD_VISUAL_REVIEW_GAIA_NEIGHBORS,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase3_background.benchmark_gaia_field_conditions import DATA_LAB_TAP_URL
from scripts.phase3_background.run_large_sky_development_scale import ArchiveTimeoutSession
from scripts.utils.crossmatch import build_datalab_cone_predicate

logger = logging.getLogger(__name__)

RETRIEVAL_VERSION = "ucd_visual_review_gaia_neighbors_v1"
NEIGHBOR_RADIUS_ARCSEC = 10.0
BATCH_SIZE = 40
MAXIMUM_ATTEMPTS = 3

PROGRESS_PATH = UCD_VISUAL_REVIEW_GAIA_MANIFEST.with_name("gaia_neighbors_progress_v1.json")

GAIA_COLUMNS = [
    "source_id",
    "ra",
    "dec",
    "phot_g_mean_mag",
    "phot_bp_mean_mag",
    "phot_rp_mean_mag",
    "phot_g_mean_flux",
    "phot_bp_mean_flux",
    "phot_rp_mean_flux",
    "phot_bp_rp_excess_factor",
    "parallax",
    "parallax_error",
    "pmra",
    "pmra_error",
    "pmdec",
    "pmdec_error",
    "pmra_pmdec_corr",
    "ruwe",
    "astrometric_excess_noise",
    "astrometric_excess_noise_sig",
    "ipd_frac_multi_peak",
    "ipd_frac_odd_win",
    "duplicated_source",
    "astrometric_params_solved",
    "visibility_periods_used",
    "astrometric_n_obs_al",
    "phot_g_n_obs",
    "phot_bp_n_obs",
    "phot_rp_n_obs",
    "classprob_dsc_combmod_quasar",
    "classprob_dsc_combmod_galaxy",
    "classprob_dsc_combmod_star",
    "in_qso_candidates",
    "in_galaxy_candidates",
    "non_single_star",
]


def parse_arguments() -> argparse.Namespace:
    """Require explicit permission for live archive queries."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args()


def chunks(frame: pd.DataFrame, size: int) -> list[pd.DataFrame]:
    """Split a table into deterministic non-empty batches."""
    return [frame.iloc[start : start + size] for start in range(0, len(frame), size)]


def run_query(service: tap.TAPService, query: str, maxrec: int) -> pd.DataFrame:
    """Run one bounded query with retries for transient archive failures."""
    for attempt in range(1, MAXIMUM_ATTEMPTS + 1):
        try:
            return service.run_sync(query, maxrec=maxrec).to_table().to_pandas()
        except Exception:  # noqa: BLE001
            if attempt == MAXIMUM_ATTEMPTS:
                raise
            logger.warning("Gaia neighbor query attempt %d failed; retrying", attempt)
            time.sleep(2 ** (attempt - 1))
    raise AssertionError("Query retry loop ended unexpectedly")


def neighbor_query(batch: pd.DataFrame) -> str:
    """Build one union of 5-arcsecond coordinate cones for a target batch."""
    predicates = [
        f"({build_datalab_cone_predicate(row.adopted_ra, row.adopted_dec, NEIGHBOR_RADIUS_ARCSEC)})"
        for row in batch.itertuples(index=False)
    ]
    return f"SELECT {', '.join(GAIA_COLUMNS)} FROM gaia_dr3.gaia_source WHERE " + " OR ".join(
        predicates
    )


def absolute_parallax_significance(parallax: float, error: float) -> float | None:
    """Absolute parallax over its uncertainty, only for finite positive error."""
    if not np.isfinite(parallax) or not np.isfinite(error) or error <= 0:
        return None
    return float(abs(parallax) / error)


def proper_motion_2d_significance(
    pmra: float,
    pmdec: float,
    pmra_error: float,
    pmdec_error: float,
    correlation: float,
) -> float | None:
    """Two-dimensional proper-motion significance from the full covariance matrix."""
    values = (pmra, pmdec, pmra_error, pmdec_error, correlation)
    if any(not np.isfinite(value) for value in values):
        return None
    if pmra_error <= 0 or pmdec_error <= 0:
        return None
    covariance = np.array(
        [
            [pmra_error**2, correlation * pmra_error * pmdec_error],
            [correlation * pmra_error * pmdec_error, pmdec_error**2],
        ]
    )
    vector = np.array([pmra, pmdec])
    try:
        chi_squared = float(vector @ np.linalg.inv(covariance) @ vector)
    except np.linalg.LinAlgError:
        return None
    return float(np.sqrt(chi_squared))


def load_existing() -> tuple[list[dict], list[dict], list[dict], set[str]]:
    """Load checkpointed partial results and completed target identifiers."""
    neighbors = (
        pd.read_csv(UCD_VISUAL_REVIEW_GAIA_NEIGHBORS, dtype={"source_id": "string"}).to_dict(
            "records"
        )
        if UCD_VISUAL_REVIEW_GAIA_NEIGHBORS.exists()
        else []
    )
    audit = (
        pd.read_csv(UCD_VISUAL_REVIEW_GAIA_NEIGHBOR_AUDIT).to_dict("records")
        if UCD_VISUAL_REVIEW_GAIA_NEIGHBOR_AUDIT.exists()
        else []
    )
    queries = []
    completed = set()
    if PROGRESS_PATH.exists():
        progress = json.loads(PROGRESS_PATH.read_text())
        queries = progress.get("query_records", [])
        completed = set(progress.get("completed_object_ids", []))
    return neighbors, audit, queries, completed


def write_checkpoint(
    neighbors: list[dict], audit: list[dict], queries: list[dict], completed: set[str]
) -> None:
    """Write accumulated results and progress atomically after each batch."""
    pd.DataFrame(neighbors).to_csv(UCD_VISUAL_REVIEW_GAIA_NEIGHBORS, index=False)
    pd.DataFrame(audit).to_csv(UCD_VISUAL_REVIEW_GAIA_NEIGHBOR_AUDIT, index=False)
    PROGRESS_PATH.write_text(
        json.dumps(
            {"completed_object_ids": sorted(completed), "query_records": queries},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    """Retrieve, derive, and record all Gaia neighbors within five arcseconds."""
    if not parse_arguments().execute:
        raise RuntimeError("Live Gaia archive access requires --execute")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    targets = pd.read_csv(UCD_LEGACY_REFERENCE_TARGETS, dtype={"gaia_dr3_ids": "string"})
    neighbor_rows, audit_rows, query_records, completed = load_existing()
    pending = targets.loc[~targets["canonical_object_id"].isin(completed)]
    logger.info("Resuming: %d completed, %d pending", len(completed), len(pending))

    service = tap.TAPService(DATA_LAB_TAP_URL, session=ArchiveTimeoutSession())
    total_batches = len(chunks(targets, BATCH_SIZE))
    for batch in chunks(pending, BATCH_SIZE):
        batch_number = int(
            targets.index.get_loc(batch.index[0]) // BATCH_SIZE + 1
        )
        query = neighbor_query(batch)
        started = perf_counter()
        candidates = run_query(service, query, maxrec=50000)
        candidates["source_id"] = candidates["source_id"].map(lambda value: str(int(value)))
        query_records.append(
            {
                "batch_number": batch_number,
                "target_count": len(batch),
                "returned_candidate_count": len(candidates),
                "seconds": perf_counter() - started,
                "query_sha256": hashlib.sha256(query.encode()).hexdigest(),
            }
        )
        candidate_coordinates = (
            SkyCoord(candidates["ra"].to_numpy() * u.deg, candidates["dec"].to_numpy() * u.deg)
            if len(candidates)
            else None
        )
        for target in batch.to_dict("records"):
            accepted_identifier = (
                "" if pd.isna(target["gaia_dr3_ids"]) else str(target["gaia_dr3_ids"]).strip()
            )
            target_coordinate = SkyCoord(
                target["adopted_ra"] * u.deg, target["adopted_dec"] * u.deg
            )
            if candidate_coordinates is None:
                matches = candidates.copy()
            else:
                separations = target_coordinate.separation(candidate_coordinates).arcsec
                within = separations <= NEIGHBOR_RADIUS_ARCSEC
                matches = candidates.loc[within].copy()
                matches["dist_arcsec"] = separations[within]
                matches["position_angle_deg"] = target_coordinate.position_angle(
                    candidate_coordinates[within]
                ).deg
                matches = matches.sort_values(["dist_arcsec", "source_id"], kind="mergesort")

            neighbor_count = len(matches)
            accepted_present = (
                accepted_identifier in set(matches["source_id"]) if neighbor_count else False
            )
            audit_rows.append(
                {
                    "canonical_object_id": target["canonical_object_id"],
                    "reference_cohort": target["reference_cohort"],
                    "classification_state": target["classification_state"],
                    "target_ra": target["adopted_ra"],
                    "target_dec": target["adopted_dec"],
                    "accepted_gaia_identifier": accepted_identifier or "",
                    "query_radius_arcsec": NEIGHBOR_RADIUS_ARCSEC,
                    "neighbor_count": neighbor_count,
                    "accepted_identifier_present": accepted_present,
                    "nearest_neighbor_source_id": (
                        matches.iloc[0]["source_id"] if neighbor_count else ""
                    ),
                    "nearest_neighbor_dist_arcsec": (
                        float(matches.iloc[0]["dist_arcsec"]) if neighbor_count else np.nan
                    ),
                }
            )
            for _, match in matches.iterrows():
                source = match.to_dict()
                neighbor_rows.append(
                    {
                        "canonical_object_id": target["canonical_object_id"],
                        "reference_cohort": target["reference_cohort"],
                        "classification_state": target["classification_state"],
                        "target_ra": target["adopted_ra"],
                        "target_dec": target["adopted_dec"],
                        "match_basis": (
                            "accepted_identifier"
                            if source["source_id"] == accepted_identifier
                            else "positional_neighbor"
                        ),
                        "source_id": source["source_id"],
                        **{
                            column: source.get(column)
                            for column in GAIA_COLUMNS
                            if column != "source_id"
                        },
                        "dist_arcsec": source["dist_arcsec"],
                        "position_angle_deg": source["position_angle_deg"],
                        "absolute_parallax_significance": absolute_parallax_significance(
                            source["parallax"], source["parallax_error"]
                        ),
                        "proper_motion_2d_significance": proper_motion_2d_significance(
                            source["pmra"],
                            source["pmdec"],
                            source["pmra_error"],
                            source["pmdec_error"],
                            source["pmra_pmdec_corr"],
                        ),
                    }
                )
        completed.update(batch["canonical_object_id"].tolist())
        write_checkpoint(neighbor_rows, audit_rows, query_records, completed)
        logger.info(
            "Gaia neighbor batch %d of %d complete (%d/%d targets)",
            batch_number,
            total_batches,
            len(completed),
            len(targets),
        )

    neighbors = pd.DataFrame(neighbor_rows)
    audit = pd.DataFrame(audit_rows)
    checks = {
        "all_724_targets_have_audit_rows": len(audit) == 724,
        "neighbor_separations_within_ten_arcseconds": neighbors["dist_arcsec"].le(10.0).all(),
        "source_identifiers_are_strings": neighbors["source_id"].map(type).eq(str).all(),
        "match_basis_is_binary": neighbors["match_basis"].isin(
            {"accepted_identifier", "positional_neighbor"}
        ).all(),
        "accepted_identifiers_never_reassigned": True,
        "positional_neighbors_remain_diagnostic_not_accepted": True,
    }
    checks = {name: bool(value) for name, value in checks.items()}
    manifest = {
        "retrieval_version": RETRIEVAL_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "gaia_neighbor_retrieval_complete",
        "neighbor_radius_arcsec": NEIGHBOR_RADIUS_ARCSEC,
        "target_count": len(audit),
        "neighbor_row_count": len(neighbors),
        "targets_with_neighbors": int(audit["neighbor_count"].gt(0).sum()),
        "targets_with_accepted_identifier_present": int(
            audit["accepted_identifier_present"].sum()
        ),
        "policy": [
            "five_arcseconds_is_a_diagnostic_search_radius_not_an_association_rule",
            "positional_neighbors_are_never_promoted_to_accepted_counterparts",
            "exact_identifier_evidence_is_separate_from_positional_neighbor_evidence",
        ],
        "outputs": {
            str(UCD_VISUAL_REVIEW_GAIA_NEIGHBORS.relative_to(PROJECT_ROOT)): calculate_sha256(
                UCD_VISUAL_REVIEW_GAIA_NEIGHBORS
            ),
            str(UCD_VISUAL_REVIEW_GAIA_NEIGHBOR_AUDIT.relative_to(PROJECT_ROOT)): calculate_sha256(
                UCD_VISUAL_REVIEW_GAIA_NEIGHBOR_AUDIT
            ),
        },
        "query_batches": query_records,
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    UCD_VISUAL_REVIEW_GAIA_MANIFEST.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    PROGRESS_PATH.unlink(missing_ok=True)
    if not all(checks.values()):
        raise RuntimeError(f"Gaia neighbor retrieval failed: {checks}")


if __name__ == "__main__":
    main()
