"""Fetch UCD catalogs from VizieR and ingest into the literature database.

This script uses astroquery to download catalogs from VizieR, applies
specialized parsing for known formats, and stores the results in the
local SQLite database.
"""

import logging
from typing import Dict, Optional, List
import pandas as pd
import numpy as np
from astropy.table import Table
from astropy.coordinates import SkyCoord
import astropy.units as u
from astroquery.vizier import Vizier
from scripts.config import LITERATURE_DB, LITERATURE_CATALOGS
from scripts.phase1_literature.ucd_database import get_db_connection, add_source, add_objects, init_database

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Vizier
vizier = Vizier(columns=["*"], row_limit=-1)

def parse_coords(df: pd.DataFrame) -> pd.DataFrame:
    """Parse coordinates from RA and Dec columns that might be in HMS/DMS format."""
    if 'ra' not in df.columns or 'dec' not in df.columns:
        return df

    # Clean strings: strip whitespace and replace empty/all-space with NaN
    df['ra'] = df['ra'].astype(str).str.strip().replace('', np.nan)
    df['dec'] = df['dec'].astype(str).str.strip().replace('', np.nan)

    # Drop rows with null ra/dec to avoid SkyCoord errors
    df = df.dropna(subset=['ra', 'dec'])

    if df.empty:
        return df

    # Check if they look like numbers
    try:
        df['ra'] = df['ra'].astype(float)
        df['dec'] = df['dec'].astype(float)
        return df
    except (ValueError, TypeError):
        # Continue to HMS/DMS parsing
        pass

    logger.info(f"Parsing HMS/DMS coordinates for {len(df)} rows...")
    try:
        # Some VizieR tables use ' ' as separator, some use ':'
        # SkyCoord handles both usually, but let's be safe
        coords = SkyCoord(ra=df['ra'], dec=df['dec'], unit=(u.hourangle, u.deg))
        df['ra'] = coords.ra.deg
        df['dec'] = coords.dec.deg
    except Exception as e:
        logger.warning(f"Error parsing coordinates: {e}")
        # Try a more desperate approach if needed, but usually SkyCoord is robust enough

    return df

def fetch_vizier_catalog(vizier_id: str) -> Optional[Table]:
    """Fetch a catalog from VizieR by its ID.

    Args:
        vizier_id: The VizieR catalog ID (e.g., 'J/ApJ/899/140').

    Returns:
        An astropy Table or None if not found.
    """
    logger.info(f"Fetching VizieR catalog: {vizier_id}")
    try:
        catalogs = vizier.get_catalogs(vizier_id)
        if not catalogs:
            logger.warning(f"No catalogs found for ID: {vizier_id}")
            return None
        table = catalogs[0]
        logger.info(f"Columns in {vizier_id}: {table.colnames}")
        return table
    except Exception as e:
        logger.error(f"Error fetching VizieR catalog {vizier_id}: {e}")
        return None

def process_wang2020(table: Table) -> pd.DataFrame:
    """Specialized processing for Wang et al. 2020 (J/ApJ/899/140)."""
    df = table.to_pandas()
    mapping = {
        'RAJ2000': 'ra',
        'DEJ2000': 'dec',
        'Gmag': 'g_mag',
        'BP-RP': 'gaia_bp_rp',
        'AEN': 'gaia_aen',
        'Gaia': 'gaia_dr3_id'
    }
    rename_dict = {k: v for k, v in mapping.items() if k in df.columns}
    df = df.rename(columns=rename_dict)
    df = parse_coords(df)
    df['is_ucd'] = 1
    df['confirmation_status'] = 'candidate'
    return df

def process_fornax_saifollahi2021(table: Table) -> pd.DataFrame:
    """Specialized processing for Saifollahi et al. 2021 (J/MNRAS/504/3580)."""
    df = table.to_pandas()
    mapping = {
        'RAJ2000': 'ra',
        'DEJ2000': 'dec',
        'gmag': 'g_mag',
        'rmag': 'r_mag',
        'imag': 'i_mag',
        'rh': 're_pc'
    }
    rename_dict = {k: v for k, v in mapping.items() if k in df.columns}
    df = df.rename(columns=rename_dict)
    df = parse_coords(df)
    if 're_pc' in df.columns:
        df['is_ucd'] = df['re_pc'].apply(lambda x: 1 if x >= 10 else 0)
    else:
        df['is_ucd'] = 1
    df['confirmation_status'] = 'candidate'
    return df

def process_centaurus_mieske2007(table: Table) -> pd.DataFrame:
    """Specialized processing for Mieske et al. 2007 (J/A+A/472/111)."""
    df = table.to_pandas()
    mapping = {
        'RAJ2000': 'ra',
        'DEJ2000': 'dec',
        'V0mag': 'v_mag',
        'CCOS': 'original_name'
    }
    rename_dict = {k: v for k, v in mapping.items() if k in df.columns}
    df = df.rename(columns=rename_dict)
    df = parse_coords(df)
    df['is_ucd'] = 1
    df['confirmation_status'] = 'candidate'
    return df

def process_abell_blakeslee2008(table: Table) -> pd.DataFrame:
    """Specialized processing for Blakeslee & Barber DeGraaff 2008 (J/AJ/136/2295)."""
    df = table.to_pandas()
    mapping = {
        'RAJ2000': 'ra',
        'DEJ2000': 'dec',
        'Imag': 'i_mag',
        '[BD2008]': 'original_name'
    }
    rename_dict = {k: v for k, v in mapping.items() if k in df.columns}
    df = df.rename(columns=rename_dict)
    df = parse_coords(df)
    df['is_ucd'] = 1
    df['confirmation_status'] = 'candidate'
    df['notes'] = 'z=0.034, negative test baseline'
    return df

def process_fornax_gregg2009(table: Table) -> pd.DataFrame:
    """Specialized processing for Gregg et al. 2009 (J/AJ/137/498)."""
    df = table.to_pandas()
    mapping = {
        'RAJ2000': 'ra',
        'DEJ2000': 'dec',
        'rfmag': 'r_mag',
        'bJmag': 'b_mag',
        'Seq': 'original_name'
    }
    rename_dict = {k: v for k, v in mapping.items() if k in df.columns}
    df = df.rename(columns=rename_dict)
    df = parse_coords(df)
    df['is_ucd'] = 1
    df['confirmation_status'] = 'candidate'
    return df

def process_compilation_voggel2019(table: Table) -> pd.DataFrame:
    """Specialized processing for Voggel/Fahrion et al. 2019 (J/A+A/625/A50)."""
    df = table.to_pandas()
    mapping = {
        'RAJ2000': 'ra',
        'DEJ2000': 'dec',
        'Name': 'original_name',
        'Host': 'host_galaxy'
    }
    rename_dict = {k: v for k, v in mapping.items() if k in df.columns}
    df = df.rename(columns=rename_dict)
    df = parse_coords(df)
    df['is_ucd'] = 1
    df['confirmation_status'] = 'confirmed' # Compilation of literature UCDs
    return df

def ingest_all_verified():
    """Ingest all verified catalogs into the database."""
    init_database()
    conn = get_db_connection()

    catalogs_to_ingest = [
        {
            "source_id": "2020ApJ...899..140W",
            "vizier_id": "J/ApJ/899/140",
            "title": "The Nature of Ultra-compact Dwarfs Revealed by Gaia",
            "authors": "Wang, L. et al.",
            "year": 2020,
            "processor": process_wang2020,
            "distance": 3.8
        },
        {
            "source_id": "2021MNRAS.504.3580S",
            "vizier_id": "J/MNRAS/504/3580",
            "title": "Ultra-compact dwarfs beyond the centre of the Fornax galaxy cluster",
            "authors": "Saifollahi, T. et al.",
            "year": 2021,
            "processor": process_fornax_saifollahi2021,
            "distance": 20.0
        },
        {
            "source_id": "2007A&A...472..111M",
            "vizier_id": "J/A+A/472/111/table1",
            "title": "A search for ultra-compact dwarf galaxies in the Centaurus galaxy cluster",
            "authors": "Mieske, S. et al.",
            "year": 2007,
            "processor": process_centaurus_mieske2007,
            "distance": 3.8
        },
        {
            "source_id": "2008AJ....136.2295B",
            "vizier_id": "J/AJ/136/2295",
            "title": "Ultra-Compact Dwarf Candidates Near the Lensing Galaxy in Abell S0740",
            "authors": "Blakeslee & Barber DeGraaff",
            "year": 2008,
            "processor": process_abell_blakeslee2008,
            "distance": 150.0 # z=0.034
        },
        {
            "source_id": "2009AJ....137..498G",
            "vizier_id": "J/AJ/137/498/table2",
            "title": "A Large Population of Ultra-Compact Dwarfs and Bright Intracluster Globulars in the Fornax Cluster",
            "authors": "Gregg et al.",
            "year": 2009,
            "processor": process_fornax_gregg2009,
            "distance": 20.0
        },
        {
            "source_id": "2019A&A...625A..50V",
            "vizier_id": "J/A+A/625/A50",
            "title": "Ultra compact dwarf galaxies catalog",
            "authors": "Voggel, K.T. et al.",
            "year": 2019,
            "processor": process_compilation_voggel2019,
            "distance": 20.0 # Most are Virgo/Fornax
        },
        {
            "source_id": "2015ApJ...812...34L",
            "vizier_id": "J/ApJ/812/34",
            "title": "NGVS X. UCD candidates in M87/M49/M60",
            "authors": "Liu, C. et al.",
            "year": 2015,
            "processor": process_fornax_saifollahi2021,
            "distance": 16.5
        },
        {
            "source_id": "2011A&A...531A...4M",
            "vizier_id": "J/A+A/531/A4",
            "title": "UCDs in Hydra I cluster",
            "authors": "Misgeld, I. et al.",
            "year": 2011,
            "processor": process_wang2020,
            "distance": 50.7
        },
        {
            "source_id": "2011ApJ...737...86C",
            "vizier_id": "J/ApJ/737/86",
            "title": "Near-infrared Properties of UCDs in Coma",
            "authors": "Chiboucas, K. et al.",
            "year": 2011,
            "processor": process_wang2020,
            "distance": 100.0
        }
    ]

    for cat in catalogs_to_ingest:
        source_id = cat['source_id']
        table = fetch_vizier_catalog(cat['vizier_id'])
        if table:
            df = cat['processor'](table)

            # Add source metadata
            add_source(conn, {
                'source_id': source_id,
                'bibcode': source_id,
                'title': cat['title'],
                'authors': cat['authors'],
                'year': cat['year'],
                'vizier_id': cat['vizier_id']
            })

            # Add objects
            if 'distance' in cat:
                df['distance_mpc'] = cat['distance']
            add_objects(conn, df, source_id)

            # Export to CSV for provenance
            csv_path = LITERATURE_CATALOGS / "by_source" / f"{source_id}.csv"
            df.to_csv(csv_path, index=False)
            logger.info(f"Exported {len(df)} objects to {csv_path}")

    conn.close()

if __name__ == "__main__":
    # Example: Ingest just the primary catalogs
    ingest_all_verified()
