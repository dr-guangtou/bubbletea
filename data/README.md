# Data Directory

This directory contains all data products for the BubbleTea project, organized by
their role in the research pipeline.

## Structure

```
data/
├── external/               # Large catalogs (gitignored, accessed via env var)
├── gaia_queries/           # Cached Gaia query results
├── galaxy_sample/          # Target galaxy sample
│   └── galaxy_sample_ranked.csv  # 2,155 galaxies ranked by priority
├── literature/             # UCD literature database and catalogs
│   ├── catalogs/           # Original and matched UCD catalogs
│   │   ├── all_ucds_gaia_matched.csv
│   │   ├── all_ucds_legacy_matched.csv
│   │   └── by_source/      # Per-paper CSV catalogs
│   ├── database/           # SQLite database for UCD compilation
│   │   └── ucd_collection.db
│   └── sources/            # Paper metadata and ingestion plans
│       ├── key_papers.json
│       └── vizier_inventory.json
└── results/                # Analysis results
    ├── background/         # Background density characterization
    ├── crossmatch/         # Candidate cross-match results
    └── radial_search/      # Radial profile excess detection results
```

## Provenance

| File/Directory | Source / Provenance |
|----------------|---------------------|
| `data/literature/database/ucd_collection.db` | Compiled from 6 literature sources (see `reference/summary.md`). |
| `data/literature/catalogs/by_source/` | Individual catalogs downloaded from VizieR or provided by authors. |
| `data/galaxy_sample/galaxy_sample_ranked.csv` | Unified sample from LVG, CF4, NED-LVS, and SGA-2020. |
| `data/literature/sources/` | Curated metadata mapping ADS bibcodes to VizieR IDs. |

## Verification Status

- **UCD Database**: Verified 2026-03-27. Row count: 1,542 objects from 6 sources.
- **Galaxy Sample**: Verified 2026-03-27. 2,155 candidate host galaxies (D < 50 Mpc).
- **Literature**: Matches `reference/summary.md`.
