# Data Directory — Provenance Manifest

**Last updated:** 2026-03-27

## Overview

This directory contains all data products for the BubbleTea project. Large binary
files (FITS, SQLite databases) are gitignored. Small CSV and JSON files are tracked.

## Directory Structure

```
data/
├── external/           # Large catalogs via BUBBLETEA_EXTERNAL_DATA env var
├── literature/
│   ├── database/       # UCD SQLite database
│   ├── catalogs/       # CSV catalogs (by_source, merged)
│   └── sources/        # Paper metadata (JSON)
├── galaxy_sample/      # Target galaxy sample
├── gaia_queries/       # Cached Gaia query results
└── results/            # Analysis outputs
```

## File Provenance

### literature/database/ucd_collection.db

SQLite database containing 1,542 known UCDs from 6 literature sources.
- **Created by:** `ucd_project/scripts/ucd_database/ingest_improved.py` (legacy)
- **To be recreated by:** `scripts/phase1_literature/fetch_vizier_catalog.py`
- **Sources:** See `literature/sources/vizier_inventory.json` for catalog IDs

### literature/catalogs/by_source/

Per-paper CSV files with UCD coordinates and properties.

| File pattern | Source | Objects |
|-------------|--------|---------|
| `2020ApJ...899..140W*.csv` | Voggel et al. 2020 | 632 |
| `2021MNRAS.504.3580S*.csv` | Saifollahi et al. 2021 | 105 |
| `2015ApJ...812...34L*.csv` | Liu et al. 2015 | ~100 |
| `2015ApJ...802...30Z*.csv` | Zhang et al. 2015 | ~50 |
| `2011A&A...531A...4M*.csv` | Misgeld et al. 2011 | ~100 |
| `2011ApJ...737...86C*.csv` | Chiboucas et al. 2011 | ~50 |

### literature/sources/

- `key_papers.json` — Priority-ranked list of key UCD papers
- `vizier_inventory.json` — VizieR catalog IDs for each source

### galaxy_sample/galaxy_sample_ranked.csv

Unified galaxy sample (2,155 galaxies, D < 25 Mpc) ranked by K-band luminosity.
- **Created by:** `ucd_project/scripts/galaxy_sample/` (legacy)
- **Sources:** LVG, CF4, NED-LVS, SGA-2020 catalogs
- **Columns:** name, ra, dec, distance_mpc, galactic_b, k_mag, log_lk, tier

## External Data

Large catalog files not stored in the repo. Set the `BUBBLETEA_EXTERNAL_DATA`
environment variable to the directory containing:

- `NED-LVS_current.fits` — NED Local Volume Sample
- `SGA-2020.fits` — Siena Galaxy Atlas
- `CF4_parsed.csv` — Cosmicflows-4 distances
- `LVG_parsed.csv` — Local Volume Galaxies catalog
