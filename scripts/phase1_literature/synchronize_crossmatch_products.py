"""Build canonical Gaia DR3 and Legacy Survey DR10 cross-match products.

The script reads the stabilized v2 database without modifying it. Gaia rows are
retrieved by provenance-bearing source ID. Legacy rows are retrieved with batched
service-side cones and independently filtered with great-circle separations.
"""

import argparse
import hashlib
import json
import logging
import sqlite3
import time
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

import astropy.units as u
import pandas as pd
from astropy.coordinates import SkyCoord
from pyvo.dal import tap

from scripts.config import (
    CANONICAL_CROSSMATCH_MANIFEST,
    CANONICAL_GAIA_CROSSMATCH_AUDIT,
    CANONICAL_GAIA_CROSSMATCH_EXPORT,
    CANONICAL_LEGACY_CROSSMATCH_AUDIT,
    CANONICAL_LEGACY_CROSSMATCH_EXPORT,
    GAIA_CROSSMATCH_EXPORT,
    LEGACY_CROSSMATCH_EXPORT,
    LITERATURE_REFERENCE_DB_V2,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase1_literature.xmatch_gaia import DATALAB_TAP_URL
from scripts.phase1_literature.xmatch_legacy_survey import flux_to_mag
from scripts.utils.crossmatch import build_datalab_cone_predicate, select_spherical_match

logger = logging.getLogger(__name__)

GAIA_RADIUS_ARCSEC = 1.0
LEGACY_RADIUS_ARCSEC = 2.0
GAIA_IDENTIFIER_BATCH_SIZE = 250
LEGACY_TARGET_BATCH_SIZE = 50
MAX_QUERY_ATTEMPTS = 3

GAIA_COLUMNS = [
    "source_id",
    "ra",
    "dec",
    "phot_g_mean_mag",
    "phot_bp_mean_mag",
    "phot_rp_mean_mag",
    "parallax",
    "parallax_error",
    "pmra",
    "pmra_error",
    "pmdec",
    "pmdec_error",
    "astrometric_excess_noise",
    "astrometric_excess_noise_sig",
    "ruwe",
    "ipd_frac_multi_peak",
    "ipd_frac_odd_win",
    "duplicated_source",
]
LEGACY_COLUMNS = ["ls_id", "ra", "dec", "type", "flux_g", "flux_r", "flux_i", "flux_z"]


def parse_arguments() -> argparse.Namespace:
    """Parse database, output, and bounded-validation options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-database", type=Path, default=LITERATURE_REFERENCE_DB_V2)
    parser.add_argument("--gaia-output", type=Path, default=CANONICAL_GAIA_CROSSMATCH_EXPORT)
    parser.add_argument("--gaia-audit", type=Path, default=CANONICAL_GAIA_CROSSMATCH_AUDIT)
    parser.add_argument("--legacy-output", type=Path, default=CANONICAL_LEGACY_CROSSMATCH_EXPORT)
    parser.add_argument("--legacy-audit", type=Path, default=CANONICAL_LEGACY_CROSSMATCH_AUDIT)
    parser.add_argument("--manifest", type=Path, default=CANONICAL_CROSSMATCH_MANIFEST)
    parser.add_argument(
        "--limit",
        type=int,
        help="Process only the first N canonical objects for a measured smoke run.",
    )
    return parser.parse_args()


def connect_read_only(path: Path) -> sqlite3.Connection:
    """Open an existing SQLite database without allowing writes."""
    if not path.is_file():
        raise FileNotFoundError(path)
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def load_canonical_targets(
    connection: sqlite3.Connection, limit: int | None = None
) -> pd.DataFrame:
    """Load one deterministic row per positioned canonical object."""
    query = """
        SELECT
            c.canonical_object_id,
            c.adopted_ra AS target_ra,
            c.adopted_dec AS target_dec,
            cl.classification_state,
            cl.classification_subtype,
            GROUP_CONCAT(DISTINCT r.gaia_dr3_id) AS gaia_dr3_id
        FROM canonical_objects c
        JOIN object_classifications cl USING (canonical_object_id)
        JOIN object_record_associations a USING (canonical_object_id)
        JOIN literature_records r USING (record_id)
        WHERE c.adopted_ra IS NOT NULL AND c.adopted_dec IS NOT NULL
        GROUP BY c.canonical_object_id
        ORDER BY c.canonical_object_id
    """
    targets = pd.read_sql_query(query, connection)
    if targets["gaia_dr3_id"].dropna().str.contains(",", regex=False).any():
        raise RuntimeError("A canonical object has more than one Gaia DR3 source ID")
    if limit is not None:
        if limit <= 0:
            raise ValueError("--limit must be positive")
        targets = targets.head(limit).copy()
    return targets


def chunked_rows(frame: pd.DataFrame, size: int) -> list[pd.DataFrame]:
    """Split a table into deterministic non-empty batches."""
    return [frame.iloc[start : start + size] for start in range(0, len(frame), size)]


def run_query(service: tap.TAPService, query: str, maxrec: int) -> pd.DataFrame:
    """Run one bounded query with retries for transient service failures."""
    for attempt in range(1, MAX_QUERY_ATTEMPTS + 1):
        try:
            return service.run_sync(query, maxrec=maxrec).to_table().to_pandas()
        except Exception:  # noqa: BLE001
            if attempt == MAX_QUERY_ATTEMPTS:
                raise
            logger.warning("Catalog query attempt %d failed; retrying", attempt)
            time.sleep(1.0)
    raise RuntimeError("Catalog query retry loop ended unexpectedly")


def build_gaia_identifier_query(source_ids: list[str]) -> str:
    """Build one exact Gaia DR3 source-identifier query."""
    identifiers = ",".join(sorted(source_ids, key=int))
    return (
        f"SELECT {', '.join(GAIA_COLUMNS)} FROM gaia_dr3.gaia_source "
        f"WHERE source_id IN ({identifiers})"
    )


def retrieve_gaia_sources(
    service: tap.TAPService, source_ids: list[str]
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Retrieve all unique canonical Gaia identifiers in measured-size batches."""
    frames = []
    query_records = []
    identifier_frame = pd.DataFrame({"source_id": sorted(set(source_ids), key=int)})
    for batch_number, batch in enumerate(
        chunked_rows(identifier_frame, GAIA_IDENTIFIER_BATCH_SIZE), start=1
    ):
        identifiers = batch["source_id"].tolist()
        query = build_gaia_identifier_query(identifiers)
        started = perf_counter()
        result = run_query(service, query, len(identifiers) + 10)
        elapsed_seconds = perf_counter() - started
        frames.append(result)
        query_records.append(
            {
                "batch_number": batch_number,
                "requested_identifier_count": len(identifiers),
                "returned_row_count": len(result),
                "elapsed_seconds": elapsed_seconds,
                "query_sha256": hashlib.sha256(query.encode("utf-8")).hexdigest(),
            }
        )
        logger.info(
            "Gaia batch %d: requested %d, returned %d",
            batch_number,
            len(identifiers),
            len(result),
        )
    sources = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=GAIA_COLUMNS)
    sources["source_id"] = sources["source_id"].map(lambda value: str(int(value)))
    if sources["source_id"].duplicated().any():
        raise RuntimeError("Gaia service returned duplicate source identifiers")
    return sources, query_records


def angular_separation_arcsec(
    target_ra: float, target_dec: float, source_ra: float, source_dec: float
) -> float:
    """Calculate one authoritative great-circle separation."""
    target = SkyCoord(target_ra * u.deg, target_dec * u.deg)
    source = SkyCoord(source_ra * u.deg, source_dec * u.deg)
    return float(target.separation(source).arcsec)


def build_gaia_products(
    targets: pd.DataFrame, sources: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build the canonical Gaia association export and complete target audit."""
    source_by_identifier = sources.set_index("source_id", drop=False)
    matched_rows = []
    audit_rows = []
    for target in targets.to_dict("records"):
        source_id_value = target["gaia_dr3_id"]
        base = {
            "canonical_object_id": target["canonical_object_id"],
            "target_ra": target["target_ra"],
            "target_dec": target["target_dec"],
            "classification_state": target["classification_state"],
            "classification_subtype": target["classification_subtype"],
            "query_radius_arcsec": GAIA_RADIUS_ARCSEC,
            "association_method": "canonical_literature_gaia_dr3_id",
        }
        if pd.isna(source_id_value):
            audit_rows.append(
                {
                    **base,
                    "gaia_dr3_id": None,
                    "match_status": "no_canonical_gaia_id",
                    "dist_arcsec": None,
                    "within_query_radius": None,
                    "match_quality": "not_queried",
                }
            )
            continue
        source_id = str(source_id_value)
        if source_id not in source_by_identifier.index:
            audit_rows.append(
                {
                    **base,
                    "gaia_dr3_id": source_id,
                    "match_status": "source_id_not_returned",
                    "dist_arcsec": None,
                    "within_query_radius": None,
                    "match_quality": "query_failure",
                }
            )
            continue
        source = source_by_identifier.loc[source_id].to_dict()
        distance = angular_separation_arcsec(
            target["target_ra"], target["target_dec"], source["ra"], source["dec"]
        )
        within_radius = distance <= GAIA_RADIUS_ARCSEC
        row = {
            **base,
            **source,
            "gaia_dr3_id": source_id,
            "dist_arcsec": distance,
            "within_query_radius": within_radius,
            "match_quality": "within_radius" if within_radius else "outside_radius_retained",
            "match_status": "matched_by_source_id",
        }
        matched_rows.append(row)
        audit_rows.append(row)
    return pd.DataFrame(matched_rows), pd.DataFrame(audit_rows)


def build_legacy_batch_query(targets: pd.DataFrame) -> str:
    """Build one measured-size union of Legacy Survey cone predicates."""
    predicates = [
        f"({build_datalab_cone_predicate(row.target_ra, row.target_dec, LEGACY_RADIUS_ARCSEC)})"
        for row in targets.itertuples(index=False)
    ]
    return f"SELECT {', '.join(LEGACY_COLUMNS)} FROM ls_dr10.tractor WHERE " + " OR ".join(
        predicates
    )


def build_legacy_products(
    service: tap.TAPService, targets: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, list[dict[str, Any]]]:
    """Query, select, and audit Legacy Survey matches for every target."""
    matched_rows = []
    audit_rows = []
    query_records = []
    for batch_number, batch in enumerate(chunked_rows(targets, LEGACY_TARGET_BATCH_SIZE), start=1):
        query = build_legacy_batch_query(batch)
        started = perf_counter()
        candidates = run_query(service, query, 100000)
        elapsed_seconds = perf_counter() - started
        query_records.append(
            {
                "batch_number": batch_number,
                "target_count": len(batch),
                "returned_candidate_count": len(candidates),
                "elapsed_seconds": elapsed_seconds,
                "query_sha256": hashlib.sha256(query.encode("utf-8")).hexdigest(),
            }
        )
        for target in batch.to_dict("records"):
            selected, diagnostics = select_spherical_match(
                candidates,
                target["target_ra"],
                target["target_dec"],
                LEGACY_RADIUS_ARCSEC,
                "ls_id",
            )
            base = {
                "canonical_object_id": target["canonical_object_id"],
                "target_ra": target["target_ra"],
                "target_dec": target["target_dec"],
                "classification_state": target["classification_state"],
                "classification_subtype": target["classification_subtype"],
                **diagnostics,
            }
            if selected is None:
                audit_rows.append({**base, "match_status": "no_match"})
                continue
            row = {**base, **selected, "match_status": "matched"}
            for band in ("g", "r", "i", "z"):
                row[f"{band}_mag"] = flux_to_mag(row[f"flux_{band}"])
            matched_rows.append(row)
            audit_rows.append(row)
        logger.info(
            "Legacy batch %d: targets %d, candidates %d",
            batch_number,
            len(batch),
            len(candidates),
        )
    matched = pd.DataFrame(matched_rows)
    audit = pd.DataFrame(audit_rows)
    if not matched.empty:
        source_keys = matched["ls_id"].map(lambda value: str(int(value)))
        source_counts = source_keys.value_counts()
        matched["selected_source_canonical_count"] = source_keys.map(source_counts)
        matched["shared_selected_source"] = matched["selected_source_canonical_count"] > 1
        diagnostics = matched.set_index("canonical_object_id")[
            ["selected_source_canonical_count", "shared_selected_source"]
        ]
        audit["selected_source_canonical_count"] = audit["canonical_object_id"].map(
            diagnostics["selected_source_canonical_count"]
        )
        audit["shared_selected_source"] = (
            audit["canonical_object_id"].map(diagnostics["shared_selected_source"]).fillna(False)
        )
    return matched, audit, query_records


def write_csv(path: Path, frame: pd.DataFrame) -> None:
    """Write a deterministic CSV, including its header when it has no rows."""
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def file_summary(path: Path) -> dict[str, Any]:
    """Summarize one generated or historical product by path, rows, and digest."""
    try:
        display_path = path.relative_to(Path.cwd()).as_posix()
    except ValueError:
        display_path = path.as_posix()
    return {
        "path": display_path,
        "row_count": len(pd.read_csv(path)),
        "sha256": calculate_sha256(path),
    }


def main() -> None:
    """Synchronize both catalog products and record their exact provenance."""
    arguments = parse_arguments()
    retrieval_started_at = datetime.now(UTC).isoformat()
    with connect_read_only(arguments.reference_database) as connection:
        targets = load_canonical_targets(connection, arguments.limit)
    service = tap.TAPService(DATALAB_TAP_URL)

    source_ids = targets["gaia_dr3_id"].dropna().astype(str).tolist()
    gaia_sources, gaia_queries = retrieve_gaia_sources(service, source_ids)
    gaia_matches, gaia_audit = build_gaia_products(targets, gaia_sources)
    legacy_matches, legacy_audit, legacy_queries = build_legacy_products(service, targets)

    write_csv(arguments.gaia_output, gaia_matches)
    write_csv(arguments.gaia_audit, gaia_audit)
    write_csv(arguments.legacy_output, legacy_matches)
    write_csv(arguments.legacy_audit, legacy_audit)

    manifest = {
        "schema_version": 1,
        "retrieval_started_at_utc": retrieval_started_at,
        "retrieval_completed_at_utc": datetime.now(UTC).isoformat(),
        "service": "NOIRLab Astro Data Lab TAP",
        "endpoint": DATALAB_TAP_URL,
        "script": "scripts/phase1_literature/synchronize_crossmatch_products.py",
        "command": (
            "PYTHONPATH=. uv run python "
            "scripts/phase1_literature/synchronize_crossmatch_products.py"
        ),
        "reference_database": {
            "path": arguments.reference_database.relative_to(Path.cwd()).as_posix(),
            "sha256": calculate_sha256(arguments.reference_database),
            "canonical_target_count": len(targets),
        },
        "gaia": {
            "catalog_release": "Gaia DR3",
            "table": "gaia_dr3.gaia_source",
            "association_method": "canonical literature Gaia DR3 source ID",
            "diagnostic_radius_arcsec": GAIA_RADIUS_ARCSEC,
            "identifier_batch_size": GAIA_IDENTIFIER_BATCH_SIZE,
            "query_batches": gaia_queries,
            "matched_export": file_summary(arguments.gaia_output),
            "target_audit": file_summary(arguments.gaia_audit),
        },
        "legacy_survey": {
            "catalog_release": "Legacy Survey DR10",
            "table": "ls_dr10.tractor",
            "match_radius_arcsec": LEGACY_RADIUS_ARCSEC,
            "target_batch_size": LEGACY_TARGET_BATCH_SIZE,
            "query_batches": legacy_queries,
            "matched_export": file_summary(arguments.legacy_output),
            "target_audit": file_summary(arguments.legacy_audit),
        },
        "superseded_historical_exports": [
            file_summary(GAIA_CROSSMATCH_EXPORT),
            file_summary(LEGACY_CROSSMATCH_EXPORT),
        ],
        "limited_smoke_run": arguments.limit is not None,
    }
    arguments.manifest.parent.mkdir(parents=True, exist_ok=True)
    arguments.manifest.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    logger.info("Wrote canonical cross-match manifest to %s", arguments.manifest)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
