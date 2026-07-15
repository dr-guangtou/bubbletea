"""Cross-match UCD candidates with Legacy Survey DR10.

This script performs a spatial cross-match between the literature UCD
collection and Legacy Survey DR10 using the NOIRLab Data Lab TAP service.
It retrieves morphological types and g, r, i, z photometry.
"""

import logging
import math
import time
from datetime import datetime
from typing import Any

import pandas as pd
from pyvo.dal import tap

from scripts.config import LEGACY_CROSSMATCH_AUDIT, LEGACY_CROSSMATCH_EXPORT
from scripts.phase1_literature.ucd_database import get_db_connection
from scripts.utils.crossmatch import build_datalab_cone_predicate, select_spherical_match

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# NOIRLab Data Lab TAP service
DATALAB_TAP_URL = "https://datalab.noirlab.edu/tap"


def flux_to_mag(flux: float) -> float | None:
    """Convert Legacy Survey flux (nanomaggies) to AB magnitude.

    Legacy Survey uses a zero point of 22.5.
    """
    if flux is None or flux <= 0:
        return None
    try:
        return 22.5 - 2.5 * math.log10(flux)
    except (ValueError, TypeError):
        return None


def get_objects_to_match(conn) -> list[dict[str, Any]]:
    """Get objects from the database that need cross-matching."""
    query = "SELECT object_id, ra, dec FROM ucd_objects WHERE ra IS NOT NULL AND dec IS NOT NULL"
    df = pd.read_sql_query(query, conn)
    return df.to_dict("records")


def build_legacy_query(ra: float, dec: float, radius_arcsec: float) -> str:
    """Build a Legacy Survey DR10 service-side cone query."""
    cone_predicate = build_datalab_cone_predicate(ra, dec, radius_arcsec)
    return f"""
        SELECT
            ls_id, ra, dec, type,
            flux_g, flux_r, flux_i, flux_z
        FROM ls_dr10.tractor
        WHERE {cone_predicate}
    """


def xmatch_legacy_datalab(
    objects: list[dict[str, Any]], radius_arcsec: float = 2.0
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Perform cross-match using NOIRLab Data Lab TAP.

    Args:
        objects: List of objects with ra, dec, object_id.
        radius_arcsec: Match radius in arcseconds.

    Returns:
        Matched rows and a complete per-object audit table.
    """
    service = tap.TAPService(DATALAB_TAP_URL)
    results = []
    audit_rows = []

    n_total = len(objects)
    logger.info(f"Starting Legacy Survey DR10 cross-match for {n_total} objects...")

    start_time = time.time()

    for i, obj in enumerate(objects):
        if (i + 1) % 50 == 0 or i == 0:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            eta = (n_total - i - 1) / rate / 60 if rate > 0 else 0
            logger.info(
                f"Progress: {i + 1}/{n_total} ({(i + 1) / n_total * 100:.1f}%) - ETA: {eta:.1f} min"
            )

        audit_row = {
            "object_id": obj["object_id"],
            "target_ra": obj["ra"],
            "target_dec": obj["dec"],
            "query_radius_arcsec": radius_arcsec,
        }

        try:
            job = service.run_sync(build_legacy_query(obj["ra"], obj["dec"], radius_arcsec))
            res_table = job.to_table()
            closest, diagnostics = select_spherical_match(
                res_table.to_pandas(),
                obj["ra"],
                obj["dec"],
                radius_arcsec,
                "ls_id",
            )
            audit_row.update(diagnostics)
            audit_row["match_status"] = "matched" if closest is not None else "no_match"
            audit_row["query_error_message"] = None
            if closest is not None:
                closest.update(diagnostics)
                closest["object_id"] = obj["object_id"]
                closest["target_ra"] = obj["ra"]
                closest["target_dec"] = obj["dec"]
                results.append(closest)

        except Exception as error:  # noqa: BLE001
            logger.warning("Error matching %s: %s", obj["object_id"], error)
            audit_row.update(
                {
                    "match_status": "query_error",
                    "query_error_message": str(error),
                    "match_count_within_radius": None,
                    "nearest_dist_arcsec": None,
                    "second_nearest_dist_arcsec": None,
                    "nearest_neighbor_gap_arcsec": None,
                    "ambiguous_match": None,
                    "candidate_matches_json": None,
                }
            )

        audit_rows.append(audit_row)

        # Small delay to respect rate limits
        time.sleep(0.1)

    return pd.DataFrame(results), pd.DataFrame(audit_rows)


def update_db_with_legacy(conn, df_ls: pd.DataFrame):
    """Update the ucd_objects table with Legacy Survey results."""

    n_updated = 0
    now = datetime.now().isoformat()

    for _, row in df_ls.iterrows():
        obj_id = row["object_id"]

        # Convert fluxes to magnitudes
        g_mag = flux_to_mag(row.get("flux_g"))
        r_mag = flux_to_mag(row.get("flux_r"))
        i_mag = flux_to_mag(row.get("flux_i"))
        z_mag = flux_to_mag(row.get("flux_z"))

        sql = """
        UPDATE ucd_objects SET
            ls_dr10_id = ?,
            ls_type = ?,
            ls_flux_g = ?,
            ls_flux_r = ?,
            ls_flux_i = ?,
            ls_flux_z = ?,
            ls_g_mag = ?,
            ls_r_mag = ?,
            ls_i_mag = ?,
            ls_z_mag = ?,
            ls_xmatch_dist = ?,
            last_modified = ?
        WHERE object_id = ?
        """

        conn.execute(
            sql,
            (
                str(row.get("ls_id")),
                str(row.get("type")),
                row.get("flux_g"),
                row.get("flux_r"),
                row.get("flux_i"),
                row.get("flux_z"),
                g_mag,
                r_mag,
                i_mag,
                z_mag,
                row.get("dist_arcsec"),
                now,
                obj_id,
            ),
        )
        n_updated += 1

    conn.commit()
    logger.info(f"Updated {n_updated} objects in database with Legacy Survey data.")


def main():
    conn = get_db_connection()
    objects = get_objects_to_match(conn)

    if not objects:
        logger.info("No objects found in database to match.")
        return

    # Run cross-match
    df_ls, df_audit = xmatch_legacy_datalab(objects)

    if not df_ls.empty:
        update_db_with_legacy(conn, df_ls)

        df_ls.to_csv(LEGACY_CROSSMATCH_EXPORT, index=False)
        logger.info("Exported Legacy Survey matches to %s", LEGACY_CROSSMATCH_EXPORT)

    LEGACY_CROSSMATCH_AUDIT.parent.mkdir(parents=True, exist_ok=True)
    df_audit.to_csv(LEGACY_CROSSMATCH_AUDIT, index=False)
    logger.info("Exported Legacy cross-match audit to %s", LEGACY_CROSSMATCH_AUDIT)

    conn.close()


if __name__ == "__main__":
    main()
