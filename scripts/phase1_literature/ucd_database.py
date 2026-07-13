"""Database utilities and schema for the UCD literature collection.

This module provides the SQLite database schema and utility functions for
managing the known UCD population reference dataset.
"""

import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import logging
from scripts.config import LITERATURE_DB

# Set up logging
logger = logging.getLogger(__name__)

def get_db_connection(db_path: Path = LITERATURE_DB) -> sqlite3.Connection:
    """Get a connection to the SQLite database.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        A sqlite3.Connection object.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_database(db_path: Path = LITERATURE_DB):
    """Initialize the database with the schema if it doesn't exist.

    Args:
        db_path: Path to the SQLite database file.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = get_db_connection(db_path)

    # Sources table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS ucd_sources (
            source_id TEXT PRIMARY KEY,
            bibcode TEXT,
            title TEXT,
            authors TEXT,
            journal TEXT,
            year INTEGER,
            volume TEXT,
            pages TEXT,
            doi TEXT,
            vizier_id TEXT,
            survey_name TEXT,
            notes TEXT,
            n_objects INTEGER,
            date_added TEXT,
            last_modified TEXT
        )
    ''')

    # Objects table (with all columns found in the migrated database)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS ucd_objects (
            object_id TEXT PRIMARY KEY,
            original_name TEXT,
            source_id TEXT,
            ra REAL,
            dec REAL,
            g_mag REAL,
            r_mag REAL,
            i_mag REAL,
            z_mag REAL,
            radial_velocity REAL,
            radial_velocity_err REAL,
            re_arcsec REAL,
            re_pc REAL,
            distance_mpc REAL,
            stellar_mass REAL,
            confirmation_status TEXT,
            is_ucd INTEGER DEFAULT 1,
            notes TEXT,
            date_added TEXT,
            last_modified TEXT,

            -- Gaia DR3 cross-match columns
            gaia_dr3_id TEXT,
            gaia_g_mag REAL,
            gaia_bp_mag REAL,
            gaia_rp_mag REAL,
            gaia_parallax REAL,
            gaia_parallax_err REAL,
            gaia_pmra REAL,
            gaia_pmra_err REAL,
            gaia_pmdec REAL,
            gaia_pmdec_err REAL,
            gaia_xmatch_dist REAL,
            gaia_aen REAL,
            gaia_aen_sig REAL,
            gaia_ruwe REAL,
            gaia_matched_transits INTEGER,
            gaia_params_solved INTEGER,
            gaia_g_snr REAL,
            gaia_bp_snr REAL,
            gaia_rp_snr REAL,
            gaia_g_n_obs INTEGER,
            gaia_bp_n_obs INTEGER,
            gaia_rp_n_obs INTEGER,
            gaia_bp_rp REAL,
            gaia_bp_g REAL,
            gaia_prob_galaxy REAL,
            gaia_prob_star REAL,
            gaia_variable_flag TEXT,
            gaia_non_single_star INTEGER,
            gaia_radial_velocity REAL,
            gaia_radial_velocity_err REAL,
            gaia_sigma5d_max REAL,
            gaia_ra_error REAL,
            gaia_dec_error REAL,
            gaia_br_excess REAL,

            -- Legacy Survey DR10 cross-match columns
            ls_dr10_id TEXT,
            ls_type TEXT,
            ls_flux_g REAL,
            ls_flux_r REAL,
            ls_flux_i REAL,
            ls_flux_z REAL,
            ls_g_mag REAL,
            ls_r_mag REAL,
            ls_i_mag REAL,
            ls_z_mag REAL,
            ls_xmatch_dist REAL,

            -- Host and ancillary info
            host_cluster TEXT,
            host_galaxy TEXT,
            distance_err_mpc REAL,
            redshift REAL,

            FOREIGN KEY (source_id) REFERENCES ucd_sources(source_id)
        )
    ''')

    # Create indices
    conn.execute('CREATE INDEX IF NOT EXISTS idx_objects_ra ON ucd_objects(ra)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_objects_dec ON ucd_objects(dec)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_objects_source ON ucd_objects(source_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_objects_ucd ON ucd_objects(is_ucd)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_objects_gaia ON ucd_objects(gaia_dr3_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_objects_ls ON ucd_objects(ls_dr10_id)')

    conn.commit()
    conn.close()
    logger.info(f"Database initialized at {db_path}")

def get_objects_summary(db_path: Path = LITERATURE_DB) -> Dict:
    """Get a summary of objects in the database.

    Returns:
        A dictionary with counts and summaries.
    """
    conn = get_db_connection(db_path)

    summary = {}

    # Total objects
    summary['total_objects'] = conn.execute("SELECT COUNT(*) FROM ucd_objects").fetchone()[0]

    # UCD vs non-UCD
    summary['n_ucds'] = conn.execute("SELECT COUNT(*) FROM ucd_objects WHERE is_ucd = 1").fetchone()[0]

    # Cross-match status
    summary['n_gaia_matches'] = conn.execute("SELECT COUNT(*) FROM ucd_objects WHERE gaia_dr3_id IS NOT NULL").fetchone()[0]
    summary['n_ls_matches'] = conn.execute("SELECT COUNT(*) FROM ucd_objects WHERE ls_dr10_id IS NOT NULL").fetchone()[0]

    # By source
    df_sources = pd.read_sql_query('''
        SELECT s.source_id, s.bibcode, s.year, COUNT(o.object_id) as n
        FROM ucd_sources s
        LEFT JOIN ucd_objects o ON s.source_id = o.source_id
        GROUP BY s.source_id
        ORDER BY n DESC
    ''', conn)
    summary['by_source'] = df_sources

    conn.close()
    return summary

def add_source(conn: sqlite3.Connection, source_data: Dict):
    """Add a new source to the database.

    Args:
        conn: sqlite3.Connection.
        source_data: Dictionary of source fields.
    """
    now = datetime.now().isoformat()
    source_data['date_added'] = source_data.get('date_added', now)
    source_data['last_modified'] = now

    columns = list(source_data.keys())
    placeholders = ', '.join(['?' for _ in columns])
    sql = f"INSERT OR REPLACE INTO ucd_sources ({', '.join(columns)}) VALUES ({placeholders})"

    conn.execute(sql, [source_data.get(c) for c in columns])
    conn.commit()

def add_objects(conn: sqlite3.Connection, objects_df: pd.DataFrame, source_id: str):
    """Add objects from a DataFrame to the database.

    Args:
        conn: sqlite3.Connection.
        objects_df: DataFrame of objects.
        source_id: The source_id to associate these objects with.
    """
    now = datetime.now().isoformat()

    # Columns expected in the database
    cursor = conn.execute("PRAGMA table_info(ucd_objects)")
    db_cols = [row[1] for row in cursor.fetchall()]

    n_added = 0
    for i, row in objects_df.iterrows():
        # Only take columns that exist in the DB
        row_dict = row.to_dict()
        row_dict['source_id'] = source_id

        # Ensure object_id is set
        if 'object_id' not in row_dict or pd.isna(row_dict['object_id']):
            # Create a simple unique ID based on source and index
            row_dict['object_id'] = f"{source_id}_{i:04d}"

        row_dict['date_added'] = row_dict.get('date_added', now)
        row_dict['last_modified'] = now

        filtered_data = {k: v for k, v in row_dict.items() if k in db_cols}

        columns = list(filtered_data.keys())
        placeholders = ', '.join(['?' for _ in columns])
        sql = f"INSERT OR REPLACE INTO ucd_objects ({', '.join(columns)}) VALUES ({placeholders})"

        conn.execute(sql, [filtered_data.get(c) for c in columns])
        n_added += 1

    conn.commit()
    logger.info(f"Added/Updated {n_added} objects for source {source_id}")

if __name__ == "__main__":
    # If run directly, show summary
    init_database()
    summary = get_objects_summary()
    print(f"Total Objects: {summary['total_objects']}")
    print(f"UCDs: {summary['n_ucds']}")
    print(f"Gaia matches: {summary['n_gaia_matches']}")
    print(f"LS matches: {summary['n_ls_matches']}")
    print("\nBy Source:")
    print(summary['by_source'].to_string(index=False))
