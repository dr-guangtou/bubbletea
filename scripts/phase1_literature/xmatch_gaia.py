"""Cross-match UCD candidates with Gaia DR3.

This script performs a spatial cross-match between the literature UCD
collection and Gaia DR3 using the NOIRLab Data Lab TAP service. It fetches
astrometric and photometric properties, including critical morphological
indicators like Astrometric Excess Noise (AEN).
"""

import logging
import time
from datetime import datetime
import pandas as pd
from typing import List, Dict, Optional
from pyvo.dal import tap
from scripts.config import LITERATURE_DB, LITERATURE_CATALOGS
from scripts.phase1_literature.ucd_database import get_db_connection

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# NOIRLab Data Lab TAP service
DATALAB_TAP_URL = "https://datalab.noirlab.edu/tap"

def get_objects_to_match(conn) -> List[Dict]:
    """Get objects from the database that need cross-matching."""
    query = "SELECT object_id, ra, dec FROM ucd_objects WHERE ra IS NOT NULL AND dec IS NOT NULL AND gaia_dr3_id IS NULL"
    df = pd.read_sql_query(query, conn)
    return df.to_dict('records')

def xmatch_gaia_datalab(objects: List[Dict], radius_arcsec: float = 1.0) -> pd.DataFrame:
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
    logger.info(f"Starting Gaia DR3 cross-match for {n_total} objects...")

    for i, obj in enumerate(objects):
        if (i + 1) % 50 == 0 or i == 0:
            logger.info(f"Progress: {i+1}/{n_total} ({(i+1)/n_total*100:.1f}%)")

        # ADQL query for a single object (box search for speed)
        # We fetch all the columns found in the migrated database
        adql = f"""
        SELECT
            source_id, ra, dec,
            phot_g_mean_mag, phot_bp_mean_mag, phot_rp_mean_mag,
            parallax, parallax_error, pmra, pmra_error, pmdec, pmdec_error,
            astrometric_excess_noise, astrometric_excess_noise_sig, ruwe,
            phot_g_n_obs, phot_bp_n_obs, phot_rp_n_obs,
            astrometric_matched_transits, astrometric_params_solved,
            classprob_dsc_combmod_galaxy, classprob_dsc_combmod_star,
            non_single_star, radial_velocity, radial_velocity_error,
            phot_g_mean_flux_over_error, phot_bp_mean_flux_over_error, phot_rp_mean_flux_over_error,
            phot_bp_rp_excess_factor,
            phot_variable_flag, ra_error, dec_error
        FROM gaia_dr3.gaia_source
        WHERE ra BETWEEN {obj['ra'] - radius_arcsec/3600} AND {obj['ra'] + radius_arcsec/3600}
          AND dec BETWEEN {obj['dec'] - radius_arcsec/3600} AND {obj['dec'] + radius_arcsec/3600}
        """

        try:
            job = service.run_sync(adql)
            res_table = job.to_table()

            if len(res_table) > 0:
                df_match = res_table.to_pandas()
                df_match['dist_arcsec'] = ((df_match['ra'] - obj['ra'])**2 +
                                          (df_match['dec'] - obj['dec'])**2)**0.5 * 3600

                closest = df_match.sort_values('dist_arcsec').iloc[0].to_dict()
                closest['object_id'] = obj['object_id']
                results.append(closest)
                # logger.info(f"Match found for {obj['object_id']}: dist={closest['dist_arcsec']:.2f} arcsec")
            else:
                pass
                # logger.warning(f"No match for {obj['object_id']} at {obj['ra']}, {obj['dec']}")

        except Exception as e:
            logger.warning(f"Error matching {obj['object_id']}: {e}")

        # Small delay to respect rate limits
        time.sleep(0.1)

    return pd.DataFrame(results)

def update_db_with_gaia(conn, df_gaia: pd.DataFrame):
    """Update the ucd_objects table with Gaia results."""
    # Map Data Lab columns to our DB columns
    mapping = {
        'source_id': 'gaia_dr3_id',
        'phot_g_mean_mag': 'gaia_g_mag',
        'phot_bp_mean_mag': 'gaia_bp_mag',
        'phot_rp_mean_mag': 'gaia_rp_mag',
        'parallax': 'gaia_parallax',
        'parallax_error': 'gaia_parallax_err',
        'pmra': 'gaia_pmra',
        'pmra_error': 'gaia_pmra_err',
        'pmdec': 'gaia_pmdec',
        'pmdec_error': 'gaia_pmdec_err',
        'dist_arcsec': 'gaia_xmatch_dist',
        'astrometric_excess_noise': 'gaia_aen',
        'astrometric_excess_noise_sig': 'gaia_aen_sig',
        'ruwe': 'gaia_ruwe',
        'astrometric_matched_transits': 'gaia_matched_transits',
        'astrometric_params_solved': 'gaia_params_solved',
        'phot_g_mean_flux_over_error': 'gaia_g_snr',
        'phot_bp_mean_flux_over_error': 'gaia_bp_snr',
        'phot_rp_mean_flux_over_error': 'gaia_rp_snr',
        'phot_g_n_obs': 'gaia_g_n_obs',
        'phot_bp_n_obs': 'gaia_bp_n_obs',
        'phot_rp_n_obs': 'gaia_rp_n_obs',
        'classprob_dsc_combmod_galaxy': 'gaia_prob_galaxy',
        'classprob_dsc_combmod_star': 'gaia_prob_star',
        'phot_variable_flag': 'gaia_variable_flag',
        'non_single_star': 'gaia_non_single_star',
        'radial_velocity': 'gaia_radial_velocity',
        'radial_velocity_error': 'gaia_radial_velocity_err',
        'ra_error': 'gaia_ra_error',
        'dec_error': 'gaia_dec_error',
        'phot_bp_rp_excess_factor': 'gaia_br_excess'
    }

    df_update = df_gaia.rename(columns=mapping)

    # Calculate additional columns
    if 'gaia_bp_mag' in df_update.columns and 'gaia_rp_mag' in df_update.columns:
        df_update['gaia_bp_rp'] = df_update['gaia_bp_mag'] - df_update['gaia_rp_mag']
    if 'gaia_bp_mag' in df_update.columns and 'gaia_g_mag' in df_update.columns:
        df_update['gaia_bp_g'] = df_update['gaia_bp_mag'] - df_update['gaia_g_mag']

    n_updated = 0
    for _, row in df_update.iterrows():
        row_dict = row.to_dict()
        obj_id = row_dict.pop('object_id')

        # Build UPDATE query
        update_data = {k: v for k, v in row_dict.items() if k.startswith('gaia_')}
        if not update_data:
            continue

        cols = [f"{k} = ?" for k in update_data.keys()]
        vals = list(update_data.values())

        sql = f"UPDATE ucd_objects SET {', '.join(cols)}, last_modified = ? WHERE object_id = ?"
        vals.extend([datetime.now().isoformat(), obj_id])

        conn.execute(sql, vals)
        n_updated += 1

    conn.commit()
    logger.info(f"Updated {n_updated} objects in database.")

def main():
    conn = get_db_connection()
    objects = get_objects_to_match(conn)

    if not objects:
        logger.info("No objects found in database to match.")
        return

    # For testing or re-running, we might want to filter only those without matches
    # But for verification, we can run all
    df_gaia = xmatch_gaia_datalab(objects)

    if not df_gaia.empty:
        update_db_with_gaia(conn, df_gaia)

        # Save results to CSV for provenance
        csv_path = LITERATURE_CATALOGS / "all_ucds_gaia_matched.csv"
        df_gaia.to_csv(csv_path, index=False)
        logger.info(f"Exported Gaia matches to {csv_path}")

    conn.close()

if __name__ == "__main__":
    main()
