# BubbleTea

Searching for Ultra-Compact Dwarf (UCD) galaxies and other compact stellar systems
in the nearby universe using Gaia DR3 astrometry and imaging survey photometry.

## Scientific Goal

Perform a systematic Gaia-only search for UCD candidates around nearby galaxies.
Gaia evidence of non-point-like structure is combined with host-centered excess
statistics; external imaging and spectroscopy are value-added characterization,
not inputs to the primary population selection.

## Method

1. **Gaia-only source model**: Calibrate a versioned non-point-source probability
   from Gaia observables; no final numerical threshold has been approved.
2. **Host-centered statistics**: Measure positive, null, and negative excesses
   against validated local or control-field backgrounds.
3. **Value-added characterization**: Use Legacy Survey and other external data to
   describe covered subsets without changing Gaia statistical membership.

## Project Phases

| Phase | Description | Status |
|-------|-------------|--------|
| **I** | Literature UCDs: fetch, organize, cross-match, characterize Gaia properties | Active |
| **Ib** | Ancillary data collection (DESI, multi-wavelength) | Planned |
| **II** | Target galaxy sample definition and prioritization (D < 50 Mpc) | Planned |
| **III** | Background density characterization (galactic latitude dependence) | Planned |
| **IV** | Pilot search around confirmed UCD hosts + high-priority targets | Planned |
| **V** | Cross-match candidates with imaging and spectroscopic data | Planned |
| **VI** | Statistical analysis, discussion, and future perspectives | Planned |

See `docs/PLAN.md` for the full plan and `docs/plans/` for per-phase task tracking.

## Quick Start

```bash
# Install dependencies
uv sync

# Set up pre-commit hooks
pre-commit install

# Set external data path (large catalogs not in repo)
export BUBBLETEA_EXTERNAL_DATA=/path/to/your/data

# Run a script
PYTHONPATH=. uv run python scripts/phase1_literature/analyze_gaia_properties.py
```

## Repository Structure

```
bubbletea/
├── scripts/               # Python scripts organized by phase
│   ├── config.py          # Central path configuration
│   ├── utils/             # Shared utilities (plotting, cross-match)
│   ├── phase1_literature/ # Phase I: literature UCD compilation
│   ├── phase2_galaxy_sample/
│   ├── phase3_background/
│   ├── phase4_search/
│   ├── phase5_crossmatch/
│   └── phase6_analysis/
├── data/                  # Data products (large files gitignored)
│   ├── literature/        # UCD literature database and catalogs
│   ├── galaxy_sample/     # Target galaxy sample
│   ├── gaia_queries/      # Cached Gaia query results
│   └── results/           # Analysis results
├── figures/               # Figures organized by phase (each with .md caption)
├── reference/             # Literature: PDF + original data per paper
├── docs/                  # Plans, journal, lessons
│   ├── PLAN.md            # Master plan
│   ├── plans/             # Per-phase task tracking
│   ├── journal/           # Research journal entries
│   └── lessons/           # Lessons learned
├── notebooks/             # Analysis notebooks
└── ucd_project/           # Legacy code (frozen reference, gitignored)
```

## Data Provenance

All data in this project is traceable to its original source. Each entry in the
literature database records the ADS bibcode, DOI, and VizieR catalog ID. The
`reference/` directory contains a folder per paper with the PDF and original data
files. See `reference/summary.md` for the literature tracking table.

## Key References

- Voggel et al. (2020), ApJ 899, 140 — Gaia-based UCD selection methodology
- Wang et al. (2023), ApJ 954, 206 — Gaia GC search around M31
- Saifollahi et al. (2021), MNRAS 504, 3580 — Fornax UCD sample

## Validated Reference State

- **5,049 literature records** from 14 record-contributing publications are
  preserved in the non-destructive v2 database, which registers 30 publication
  provenance packages in total.
- **4,359 canonical objects** are classified as 740 confirmed, 1,515 candidate,
  2,082 rejected, and 22 uncertain under `confirmation_rules_v1`.
- **963 canonical Gaia associations** represent 962 unique Gaia DR3 sources.
- **3,723 Legacy Survey DR10 matches** are retained as value-added enrichment;
  complete audits include all 4,359 canonical targets.
- Historical pilot thresholds, match rates, and host contrasts remain exploratory
  until the unified selector and background model are validated.

The generated counts and validation state are recorded in
`data/literature/validation/project_status_counts.json`.
