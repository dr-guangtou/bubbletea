"""Cross-match UCD candidates with Legacy Survey DR10.

This script performs a spatial cross-match between the literature UCD
collection and Legacy Survey DR10 using the NOIRLab Data Lab TAP service.
It retrieves morphological types and g, r, i, z photometry.
"""

import logging
import time
import math
import pandas as pd
from typing import List, Dict, Optional
from pyvo.dal import tap
from datetime import datetime
from scripts.config import LITERATURE_DB, LITERATURE_CATALOGS
from scripts.phase1_literature.ucd_database import get_db_connection

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# NOIRLab Data Lab TAP service
DATALAB_TAP_URL = "https://datalab.noirlab.edu/tap"

def flux_to_mag(flux: float) -> Optional[float]:
    """Convert Legacy Survey flux (nanomaggies) to AB magnitude.

    Legacy Survey uses a zero point of 22.5.
    """
    if flux is None or flux <= 0:
        return None
    try:
        return 22.5 - 2.5 * math.log10(flux)
    except (ValueError, TypeError):
        return None

def get_objects_to_match(conn) -> List[Dict]:
    """Get objects from the database that need cross-matching."""
    query = "SELECT object_id, ra, dec FROM ucd_objects WHERE ra IS NOT NULL AND dec IS NOT NULL"
    df = pd.read_sql_query(query, conn)
    return df.to_dict('records')

def xmatch_legacy_datalab(objects: List[Dict], radius_arcsec: float = 2.0) -> pd.DataFrame:
    """Perform cross-match using NOIRLab Data Lab TAP.

    Args:
        objects: List of objects with ra, dec, object_id.
        radius_arcsec: Match radius in arcseconds.

    Returns:
        DataFrame with cross-match results.
    """
    service = tap.TAPService(DATALAB_TAP_URL)
    results = []

    n_total = len(objects)
    logger.info(f"Starting Legacy Survey DR10 cross-match for {n_total} objects...")

    start_time = time.time()

    for i, obj in enumerate(objects):
        if (i + 1) % 50 == 0 or i == 0:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            eta = (n_total - i - 1) / rate / 60 if rate > 0 else 0
            logger.info(f"Progress: {i+1}/{n_total} ({(i+1)/n_total*100:.1f}%) - ETA: {eta:.1f} min")

        # ADQL query for a single object
        radius_deg = radius_arcsec / 3600.0
        adql = f"""
        SELECT
            ls_id, ra, dec, type,
            flux_g, flux_r, flux_i, flux_z
        FROM ls_dr10.tractor
        WHERE ra BETWEEN {obj['ra'] - radius_deg} AND {obj['ra'] + radius_deg}
          AND dec BETWEEN {obj['dec'] - radius_deg} AND {obj['dec'] + radius_deg}
        """

        try:
            job = service.run_sync(adql)
            res_table = job.to_table()

            if len(res_table) > 0:
                df_match = res_table.to_pandas()
                # Calculate angular distance
                df_match['dist_arcsec'] = ((df_match['ra'] - obj['ra'])**2 +
                                          (df_match['dec'] - obj['dec'])**2)**0.5 * 3600

                # Keep closest match within radius
                closest = df_match.sort_values('dist_arcsec').iloc[0].to_dict()
                closest['object_id'] = obj['object_id']
                results.append(closest)

        except Exception as e:
            logger.warning(f"Error matching {obj['object_id']}: {e}")

        # Small delay to respect rate limits
        time.sleep(0.1)

    return pd.DataFrame(results)

def update_db_with_legacy(conn, df_ls: pd.DataFrame):
    """Update the ucd_objects table with Legacy Survey results."""

    n_updated = 0
    now = datetime.now().isoformat()

    for _, row in df_ls.iterrows():
        obj_id = row['object_id']

        # Convert fluxes to magnitudes
        g_mag = flux_to_mag(row.get('flux_g'))
        r_mag = flux_to_mag(row.get('flux_r'))
        i_mag = flux_to_mag(row.get('flux_i'))
        z_mag = flux_to_mag(row.get('flux_z'))

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

        conn.execute(sql, (
            str(row.get('ls_id')),
            str(row.get('type')),
            row.get('flux_g'),
            row.get('flux_r'),
            row.get('flux_i'),
            row.get('flux_z'),
            g_mag, r_mag, i_mag, z_mag,
            row.get('dist_arcsec'),
            now,
            obj_id
        ))
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
    df_ls = xmatch_legacy_datalab(objects)

    if not df_ls.empty:
        update_db_with_legacy(conn, df_ls)

        # Save results to CSV for provenance
        csv_path = LITERATURE_CATALOGS / "all_ucds_legacy_matched.csv"
        df_ls.to_csv(csv_path, index=False)
        logger.info(f"Exported Legacy Survey matches to {csv_path}")

    conn.close()

if __name__ == "__main__":
    main()
