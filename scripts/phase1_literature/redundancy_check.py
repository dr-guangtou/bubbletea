"""Identify and remove redundant UCD objects across different literature sources.

Performs a spatial cross-match (0.5 arcsec) between all objects in the
database and removes duplicates, prioritizing data from more recent
publications.
"""

import logging
import pandas as pd
import numpy as np
from astropy.coordinates import SkyCoord
import astropy.units as u
from scripts.config import LITERATURE_DB
from scripts.phase1_literature.ucd_database import get_db_connection

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def perform_redundancy_check(radius_arcsec: float = 1.5):
    """Identify and remove duplicates in the ucd_objects table."""
    conn = get_db_connection()

    # Load all objects with their source year
    query = """
        SELECT o.object_id, o.ra, o.dec, s.year, o.source_id
        FROM ucd_objects o
        JOIN ucd_sources s ON o.source_id = s.source_id
        WHERE o.ra IS NOT NULL AND o.dec IS NOT NULL
    """
    df = pd.read_sql_query(query, conn)

    if df.empty:
        logger.info("No objects found to check.")
        conn.close()
        return

    logger.info(f"Total objects to check: {len(df)}")

    # Sort by year (descending) so we keep the most recent ones
    # For same year, sort by source_id to be deterministic
    df = df.sort_values(['year', 'source_id', 'object_id'], ascending=[False, True, True]).reset_index(drop=True)

    coords = SkyCoord(ra=df['ra'].values*u.deg, dec=df['dec'].values*u.deg)

    # Identify duplicates
    to_remove = []

    # match_to_catalog_sky returns the closest match in the second catalog for each object in the first
    # We compare the catalog against itself. For each object, the closest match will be itself (distance 0).
    # We want the second closest match.

    # A simpler way for small catalogs:
    idx_self, idx_other, d2d, _ = coords.search_around_sky(coords, radius_arcsec * u.arcsec)

    # Filter out self-matches
    mask = idx_self != idx_other
    idx_self = idx_self[mask]
    idx_other = idx_other[mask]

    # Now we have pairs of indices (i, j) that are within radius
    # Because we sorted df, if i < j, i is more "recent" or preferred over j.
    # We want to remove j.

    for i, j in zip(idx_self, idx_other):
        if i < j:
            to_remove.append(df.iloc[j]['object_id'])

    to_remove = sorted(list(set(to_remove)))

    logger.info(f"Found {len(to_remove)} redundant objects to remove.")

    if to_remove:
        # Perform removal
        cursor = conn.cursor()
        # Use chunks to avoid too many variables in SQL
        chunk_size = 500
        for i in range(0, len(to_remove), chunk_size):
            chunk = to_remove[i:i + chunk_size]
            placeholders = ', '.join(['?' for _ in chunk])
            cursor.execute(f"DELETE FROM ucd_objects WHERE object_id IN ({placeholders})", chunk)

        conn.commit()
        logger.info(f"Successfully removed {len(to_remove)} objects.")

    conn.close()

if __name__ == "__main__":
    perform_redundancy_check()
