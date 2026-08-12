"""Retrieve Gaia membership flags and Legacy Survey catalog rows for UCD references."""

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
    UCD_LEGACY_REFERENCE_CONTRACT,
    UCD_LEGACY_REFERENCE_GAIA_MEMBERSHIP,
    UCD_LEGACY_REFERENCE_MANIFEST,
    UCD_LEGACY_REFERENCE_TARGETS,
    UCD_LEGACY_REFERENCE_TRACTOR_AUDIT,
    UCD_LEGACY_REFERENCE_TRACTOR_MATCHES,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase3_background.benchmark_gaia_field_conditions import DATA_LAB_TAP_URL
from scripts.phase3_background.run_large_sky_development_scale import ArchiveTimeoutSession
from scripts.phase4_search.freeze_ucd_legacy_reference import CONTRACT_VERSION
from scripts.utils.crossmatch import build_datalab_cone_predicate

logger = logging.getLogger(__name__)

RETRIEVAL_VERSION = "ucd_legacy_reference_catalog_retrieval_v1"
GAIA_BATCH_SIZE = 100
TRACTOR_BATCH_SIZE = 40
TRACTOR_RADIUS_ARCSEC = 2.0
MAXIMUM_ATTEMPTS = 3
GAIA_COLUMNS = [
    "source_id",
    "in_qso_candidates",
    "in_galaxy_candidates",
    "non_single_star",
    "classprob_dsc_combmod_quasar",
    "classprob_dsc_combmod_galaxy",
    "classprob_dsc_combmod_star",
]
TRACTOR_COLUMNS = [
    "ls_id",
    "release",
    "brickname",
    "brickid",
    "objid",
    "brick_primary",
    "ra",
    "dec",
    "type",
    "maskbits",
    "fitbits",
    "ref_cat",
    "ref_id",
    "flux_g",
    "flux_r",
    "flux_i",
    "flux_z",
    "flux_w1",
    "flux_w2",
    "flux_ivar_g",
    "flux_ivar_r",
    "flux_ivar_i",
    "flux_ivar_z",
    "flux_ivar_w1",
    "flux_ivar_w2",
    "mw_transmission_g",
    "mw_transmission_r",
    "mw_transmission_i",
    "mw_transmission_z",
    "nobs_g",
    "nobs_r",
    "nobs_i",
    "nobs_z",
    "rchisq_g",
    "rchisq_r",
    "rchisq_i",
    "rchisq_z",
    "fracflux_g",
    "fracflux_r",
    "fracflux_i",
    "fracflux_z",
    "fracmasked_g",
    "fracmasked_r",
    "fracmasked_i",
    "fracmasked_z",
    "fracin_g",
    "fracin_r",
    "fracin_i",
    "fracin_z",
    "allmask_g",
    "allmask_r",
    "allmask_i",
    "allmask_z",
    "psfsize_g",
    "psfsize_r",
    "psfsize_i",
    "psfsize_z",
    "sersic",
    "sersic_ivar",
    "shape_r",
    "shape_r_ivar",
    "shape_e1",
    "shape_e1_ivar",
    "shape_e2",
    "shape_e2_ivar",
]


def parse_arguments() -> argparse.Namespace:
    """Require explicit permission for live catalog queries."""
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
            logger.warning("Catalog query attempt %d failed; retrying", attempt)
            time.sleep(2 ** (attempt - 1))
    raise AssertionError("Query retry loop ended unexpectedly")


def retrieve_gaia_membership(
    service: tap.TAPService, targets: pd.DataFrame
) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    """Test Gaia catalog membership only for exact unique identifiers."""
    testable = targets.loc[targets["gaia_identifier_count"].eq(1)].copy()
    frames = []
    records = []
    for batch_number, batch in enumerate(chunks(testable, GAIA_BATCH_SIZE), start=1):
        identifiers = sorted(batch["gaia_dr3_ids"].tolist(), key=int)
        query = (
            f"SELECT {', '.join(GAIA_COLUMNS)} FROM gaia_dr3.gaia_source WHERE "
            f"source_id IN ({','.join(identifiers)})"
        )
        started = perf_counter()
        result = run_query(service, query, len(identifiers) + 1)
        frames.append(result)
        records.append(
            {
                "batch_number": batch_number,
                "requested_identifier_count": len(identifiers),
                "returned_row_count": len(result),
                "seconds": perf_counter() - started,
                "query_sha256": hashlib.sha256(query.encode()).hexdigest(),
            }
        )
    returned = pd.concat(frames, ignore_index=True)
    returned["source_id"] = returned["source_id"].map(lambda value: str(int(value)))
    output = targets[
        [
            "canonical_object_id",
            "reference_cohort",
            "classification_state",
            "gaia_dr3_ids",
            "gaia_catalog_membership_testability",
        ]
    ].copy()
    output = output.merge(
        returned,
        left_on="gaia_dr3_ids",
        right_on="source_id",
        how="left",
        validate="m:1",
    )
    testable_mask = (
        output["gaia_identifier_count"].eq(1)
        if "gaia_identifier_count" in output
        else output["gaia_catalog_membership_testability"].eq(
            "testable_exact_unique_gaia_identifier"
        )
    )
    output["gaia_source_row_retrieved"] = output["source_id"].notna()
    output["gaia_membership_result_status"] = "not_testable_no_unique_gaia_identifier"
    output.loc[testable_mask, "gaia_membership_result_status"] = "exact_identifier_tested"
    for column in ("in_qso_candidates", "in_galaxy_candidates", "non_single_star"):
        output[column] = output[column].astype("Int64")
    return output, records


def tractor_query(batch: pd.DataFrame) -> str:
    """Build one union of coordinate cones for the fixed target batch."""
    predicates = [
        f"({build_datalab_cone_predicate(row.adopted_ra, row.adopted_dec, TRACTOR_RADIUS_ARCSEC)})"
        for row in batch.itertuples(index=False)
    ]
    return f"SELECT {', '.join(TRACTOR_COLUMNS)} FROM ls_dr10.tractor WHERE " + " OR ".join(
        predicates
    )


def derived_photometry(row: dict[str, object]) -> dict[str, object]:
    """Derive observed and extinction-corrected magnitudes only for valid fluxes."""
    output: dict[str, object] = {}
    for band in ("g", "r", "i", "z", "w1", "w2"):
        flux = float(row[f"flux_{band}"])
        inverse_variance = float(row[f"flux_ivar_{band}"])
        valid = (
            np.isfinite(flux)
            and flux > 0
            and np.isfinite(inverse_variance)
            and inverse_variance > 0
        )
        output[f"valid_{band}_photometry"] = bool(valid)
        output[f"mag_{band}"] = float(22.5 - 2.5 * np.log10(flux)) if valid else np.nan
        if band in {"g", "r", "i", "z"}:
            transmission = float(row[f"mw_transmission_{band}"])
            corrected_flux = flux / transmission if valid and 0 < transmission <= 1 else np.nan
            output[f"dered_mag_{band}"] = (
                float(22.5 - 2.5 * np.log10(corrected_flux))
                if np.isfinite(corrected_flux) and corrected_flux > 0
                else np.nan
            )
    return output


def retrieve_tractor(
    service: tap.TAPService, targets: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, list[dict[str, object]]]:
    """Retrieve and retain every positional association within two arcseconds."""
    association_rows = []
    audit_rows = []
    query_records = []
    for batch_number, batch in enumerate(chunks(targets, TRACTOR_BATCH_SIZE), start=1):
        query = tractor_query(batch)
        started = perf_counter()
        candidates = run_query(service, query, maxrec=100000)
        candidates["ls_id"] = candidates["ls_id"].map(lambda value: str(int(value)))
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
            if candidate_coordinates is None:
                matches = candidates.copy()
            else:
                coordinate = SkyCoord(target["adopted_ra"] * u.deg, target["adopted_dec"] * u.deg)
                distances = coordinate.separation(candidate_coordinates).arcsec
                matches = candidates.loc[distances <= TRACTOR_RADIUS_ARCSEC].copy()
                matches["dist_arcsec"] = distances[distances <= TRACTOR_RADIUS_ARCSEC]
                matches = matches.sort_values(["dist_arcsec", "ls_id"], kind="mergesort")
            match_count = len(matches)
            audit_rows.append(
                {
                    "canonical_object_id": target["canonical_object_id"],
                    "reference_cohort": target["reference_cohort"],
                    "classification_state": target["classification_state"],
                    "target_ra": target["adopted_ra"],
                    "target_dec": target["adopted_dec"],
                    "query_radius_arcsec": TRACTOR_RADIUS_ARCSEC,
                    "match_status": "matched" if match_count else "no_match",
                    "match_count_within_radius": match_count,
                    "nearest_dist_arcsec": float(matches.iloc[0]["dist_arcsec"])
                    if match_count
                    else np.nan,
                    "second_nearest_dist_arcsec": float(matches.iloc[1]["dist_arcsec"])
                    if match_count > 1
                    else np.nan,
                    "ambiguous_match": match_count > 1,
                    "selected_closest_ls_id": matches.iloc[0]["ls_id"] if match_count else "",
                }
            )
            for association_rank, (_, match) in enumerate(matches.iterrows(), start=1):
                source = match.to_dict()
                association_rows.append(
                    {
                        "canonical_object_id": target["canonical_object_id"],
                        "reference_cohort": target["reference_cohort"],
                        "classification_state": target["classification_state"],
                        "target_ra": target["adopted_ra"],
                        "target_dec": target["adopted_dec"],
                        "association_rank": association_rank,
                        "selected_closest_match": association_rank == 1,
                        **source,
                        **derived_photometry(source),
                    }
                )
        logger.info(
            "Tractor batch %d of %d complete",
            batch_number,
            len(chunks(targets, TRACTOR_BATCH_SIZE)),
        )
    return pd.DataFrame(association_rows), pd.DataFrame(audit_rows), query_records


def main() -> None:
    """Execute both frozen catalog retrievals and write checked outputs."""
    if not parse_arguments().execute:
        raise RuntimeError("Live catalog access requires --execute")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    contract = json.loads(UCD_LEGACY_REFERENCE_CONTRACT.read_text())
    if contract["contract_version"] != CONTRACT_VERSION:
        raise RuntimeError("UCD Legacy reference contract is not expected")
    if calculate_sha256(UCD_LEGACY_REFERENCE_TARGETS) != contract["target_output"]["sha256"]:
        raise RuntimeError("UCD Legacy reference targets differ from the frozen digest")
    targets = pd.read_csv(UCD_LEGACY_REFERENCE_TARGETS, dtype={"gaia_dr3_ids": str})
    service = tap.TAPService(DATA_LAB_TAP_URL, session=ArchiveTimeoutSession())
    gaia, gaia_queries = retrieve_gaia_membership(service, targets)
    tractor, tractor_audit, tractor_queries = retrieve_tractor(service, targets)
    gaia.to_csv(UCD_LEGACY_REFERENCE_GAIA_MEMBERSHIP, index=False)
    tractor.to_csv(UCD_LEGACY_REFERENCE_TRACTOR_MATCHES, index=False)
    tractor_audit.to_csv(UCD_LEGACY_REFERENCE_TRACTOR_AUDIT, index=False)
    testable = gaia["gaia_membership_result_status"].eq("exact_identifier_tested")
    checks = {
        "all_724_targets_have_gaia_status": len(gaia) == len(targets) == 724,
        "exactly_175_gaia_identifiers_tested": int(testable.sum()) == 175,
        "all_testable_gaia_rows_retrieved": gaia.loc[testable, "gaia_source_row_retrieved"].all(),
        "all_targets_have_tractor_audit_rows": len(tractor_audit) == 724,
        "all_tractor_associations_are_within_two_arcseconds": tractor["dist_arcsec"].le(2.0).all(),
        "closest_match_is_unique_per_matched_target": tractor.loc[
            tractor["selected_closest_match"]
        ]["canonical_object_id"].is_unique,
        "all_associations_have_portable_string_identifiers": tractor["ls_id"]
        .map(type)
        .eq(str)
        .all(),
        "catalog_flags_are_evidence_not_rejections": True,
        "tractor_types_are_measurements_not_truth_labels": True,
    }
    checks = {name: bool(value) for name, value in checks.items()}
    manifest = {
        "retrieval_version": RETRIEVAL_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "catalog_retrieval_complete_images_pending",
        "gaia_membership": {
            "method": "exact_unique_gaia_dr3_source_identifier",
            "testable_count": int(testable.sum()),
            "qso_candidate_membership_count": int(
                gaia.loc[testable, "in_qso_candidates"].fillna(0).sum()
            ),
            "galaxy_candidate_membership_count": int(
                gaia.loc[testable, "in_galaxy_candidates"].fillna(0).sum()
            ),
            "non_single_star_membership_count": int(
                gaia.loc[testable, "non_single_star"].fillna(0).sum()
            ),
            "query_batches": gaia_queries,
        },
        "legacy_tractor": {
            "method": "all positional associations within 2 arcseconds",
            "target_count": len(targets),
            "matched_target_count": int(tractor_audit["match_status"].eq("matched").sum()),
            "no_match_target_count": int(tractor_audit["match_status"].eq("no_match").sum()),
            "ambiguous_target_count": int(tractor_audit["ambiguous_match"].sum()),
            "association_row_count": len(tractor),
            "closest_type_counts": tractor.loc[tractor["selected_closest_match"], "type"]
            .value_counts()
            .to_dict(),
            "query_batches": tractor_queries,
        },
        "outputs": {
            str(UCD_LEGACY_REFERENCE_GAIA_MEMBERSHIP.relative_to(PROJECT_ROOT)): calculate_sha256(
                UCD_LEGACY_REFERENCE_GAIA_MEMBERSHIP
            ),
            str(UCD_LEGACY_REFERENCE_TRACTOR_MATCHES.relative_to(PROJECT_ROOT)): calculate_sha256(
                UCD_LEGACY_REFERENCE_TRACTOR_MATCHES
            ),
            str(UCD_LEGACY_REFERENCE_TRACTOR_AUDIT.relative_to(PROJECT_ROOT)): calculate_sha256(
                UCD_LEGACY_REFERENCE_TRACTOR_AUDIT
            ),
        },
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    UCD_LEGACY_REFERENCE_MANIFEST.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"UCD Legacy catalog retrieval failed: {checks}")


if __name__ == "__main__":
    main()
