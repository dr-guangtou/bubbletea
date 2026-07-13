"""Execute radial UCD search using Model C selection and local background.

Performs concentric annulus queries around target galaxies, applies
probabilistic Model C selection, and identifies statistical excesses
relative to the local background (150-300 kpc).
"""

import logging
import time
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from astroquery.gaia import Gaia
from astropy.coordinates import SkyCoord
from astropy import units as u
from scipy.stats import norm
from scripts.config import GALAXY_SAMPLE_DIR, RADIAL_SEARCH_RESULTS_DIR

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
RADIAL_BINS_KPC = [0, 10, 20, 30, 40, 50, 60, 80, 100, 125, 150, 175, 200, 225, 250, 275, 300]
BG_ANNULUS_R_IN = 150  # kpc
MAX_RADIUS_DEG = 2.0   # Cap search at 2 degrees
MAX_ROWS = 100000
RATE_LIMIT = 1.0

def compute_radius_deg(distance_mpc: float, radius_kpc: float) -> float:
    """Convert physical radius (kpc) to angular radius (deg)."""
    arcsec_per_kpc = 206265.0 / (distance_mpc * 1000.0)
    return radius_kpc * arcsec_per_kpc / 3600.0

def build_query(ra: float, dec: float, radius_deg: float) -> str:
    """Build ADQL query for Gaia sources around a target."""
    return f"""
    SELECT
        source_id, ra, dec,
        phot_g_mean_mag, phot_bp_mean_mag, phot_rp_mean_mag,
        phot_bp_mean_mag - phot_rp_mean_mag AS bp_rp,
        astrometric_excess_noise, astrometric_excess_noise_sig,
        phot_bp_rp_excess_factor,
        pmra, pmra_error, pmdec, pmdec_error,
        ruwe, classprob_dsc_combmod_galaxy
    FROM gaiadr3.gaia_source
    WHERE 1 = CONTAINS(
        POINT('ICRS', ra, dec),
        CIRCLE('ICRS', {ra}, {dec}, {radius_deg})
    )
    AND phot_g_mean_mag BETWEEN 16 AND 21
    AND astrometric_excess_noise > 0.3
    AND (
        (pmra IS NULL OR pmdec IS NULL)
        OR
        (SQRT(pmra*pmra + pmdec*pmdec) /
         SQRT(pmra_error*pmra_error + pmdec_error*pmdec_error) <= 3.0)
        OR
        (SQRT(pmra*pmra + pmdec*pmdec) < 2.92)
    )
    """

def apply_model_c(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the probabilistic Model C selection."""
    if df.empty:
        return df
    prob_aen = norm.cdf(df['astrometric_excess_noise_sig'] - 2.0)
    prob_br = (df['phot_bp_rp_excess_factor'] - 1.2) / 0.5
    prob_br = np.clip(prob_br, 0, 1)
    prob_color = ((df['bp_rp'] >= 0.8) & (df['bp_rp'] <= 1.8)).astype(float)
    df['model_c_score'] = (prob_aen * 0.6 + prob_br * 0.3 + prob_color * 0.1)
    return df[df['model_c_score'] > 0.5].copy()

def compute_radial_bins(df: pd.DataFrame, galaxy_ra: float, galaxy_dec: float,
                        distance_mpc: float, bins_kpc: List[float]) -> Tuple[pd.DataFrame, np.ndarray]:
    """Compute radial bin statistics."""
    if df.empty:
        return pd.DataFrame(), np.array([])
    galaxy_coord = SkyCoord(ra=galaxy_ra*u.deg, dec=galaxy_dec*u.deg)
    cand_coords = SkyCoord(ra=df['ra'].values*u.deg, dec=df['dec'].values*u.deg)
    separations_deg = galaxy_coord.separation(cand_coords).deg
    kpc_per_deg = distance_mpc * 1000.0 * np.pi / 180.0
    separations_kpc = separations_deg * kpc_per_deg

    results = []
    for i in range(len(bins_kpc) - 1):
        r_in, r_out = bins_kpc[i], bins_kpc[i+1]
        mask = (separations_kpc >= r_in) & (separations_kpc < r_out)
        n = int(mask.sum())
        r_in_deg = compute_radius_deg(distance_mpc, r_in)
        r_out_deg = compute_radius_deg(distance_mpc, r_out)
        area_deg2 = np.pi * (r_out_deg**2 - r_in_deg**2)
        density = n / area_deg2 if area_deg2 > 0 else 0
        density_err = np.sqrt(n) / area_deg2 if n > 0 else (1.0 / area_deg2 if area_deg2 > 0 else 0)
        results.append({
            'r_in_kpc': r_in, 'r_out_kpc': r_out,
            'r_mid_kpc': (r_in + r_out) / 2,
            'area_deg2': area_deg2,
            'n_candidates': n,
            'density': density,
            'density_err': density_err
        })
    return pd.DataFrame(results), separations_kpc

def search_around_galaxy(target: Dict) -> Optional[Dict]:
    """Perform radial search for a single target galaxy."""
    name = target['objname']
    ra, dec, dist = target['ra'], target['dec'], target['dist_best']
    logger.info(f"Searching around {name} (D={dist:.1f} Mpc)...")
    radius_deg = min(compute_radius_deg(dist, 300), MAX_RADIUS_DEG)

    try:
        query = build_query(ra, dec, radius_deg)
        job = Gaia.launch_job_async(query)
        result = job.get_results()
        if len(result) == 0:
            return None
        df_raw = result.to_pandas()
        df_cand = apply_model_c(df_raw)
        radial_df, separations_kpc = compute_radial_bins(df_cand, ra, dec, dist, RADIAL_BINS_KPC)
        if radial_df.empty:
            return None

        bg_bins = radial_df[radial_df['r_in_kpc'] >= BG_ANNULUS_R_IN]
        total_bg_objects = bg_bins['n_candidates'].sum()
        total_bg_area = bg_bins['area_deg2'].sum()
        bg_density = total_bg_objects / total_bg_area if total_bg_area > 0 else 0

        central = radial_df[radial_df['r_out_kpc'] <= 20]
        n_central = central['n_candidates'].sum()
        area_central = central['area_deg2'].sum()
        central_density = n_central / area_central if area_central > 0 else 0

        expected_central = bg_density * area_central
        excess_central = n_central - expected_central
        significance = excess_central / np.sqrt(expected_central) if expected_central > 0 else 0
        contrast = central_density / bg_density if bg_density > 0 else np.nan

        safe_name = name.replace(' ', '_')
        radial_df.to_csv(RADIAL_SEARCH_RESULTS_DIR / f"{safe_name}_radial_profile.csv", index=False)
        df_cand['radius_kpc'] = separations_kpc
        df_cand.to_csv(RADIAL_SEARCH_RESULTS_DIR / f"{safe_name}_candidates.csv", index=False)

        return {
            'objname': name,
            'dist_mpc': dist,
            'glat': target.get('glat'),
            'n_candidates': len(df_cand),
            'bg_density': bg_density,
            'central_density': central_density,
            'contrast': contrast,
            'excess_central': excess_central,
            'significance': significance
        }
    except Exception as e:
        logger.error(f"  Error searching {name}: {e}")
        return None

def main(n_limit: Optional[int] = None, min_glat: float = 30.0):
    pilot_path = GALAXY_SAMPLE_DIR / "pilot_sample_top100.csv"
    if not pilot_path.exists():
        logger.error(f"Pilot sample not found: {pilot_path}")
        return

    df_pilot = pd.read_csv(pilot_path)
    df_pilot = df_pilot[df_pilot['glat'].abs() >= min_glat]
    if n_limit:
        df_pilot = df_pilot.head(n_limit)

    RADIAL_SEARCH_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    summary_results = []
    for _, row in df_pilot.iterrows():
        res = search_around_galaxy(row.to_dict())
        if res:
            summary_results.append(res)
        time.sleep(RATE_LIMIT)

    if summary_results:
        summary_df = pd.DataFrame(summary_results)
        output_path = RADIAL_SEARCH_RESULTS_DIR / "pilot_search_summary.csv"
        summary_df.sort_values('significance', ascending=False).to_csv(output_path, index=False)
        logger.info(f"Pilot search complete. Summary saved to {output_path}")

if __name__ == "__main__":
    # Start with top 20 to be safe before full run
    main(n_limit=20)
