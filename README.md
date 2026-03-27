# BubbleTea

Searching for Ultra-Compact Dwarf (UCD) galaxies and other compact stellar systems
in the nearby universe using Gaia DR3 astrometry and imaging survey photometry.

## Scientific Goal

Perform a systematic search for UCDs around nearby galaxies (D < 50 Mpc) by
exploiting Gaia's astrometric excess noise (AEN) as a morphological discriminator.
Cross-match candidates with Legacy Survey DR10, HSC, and other imaging data to
characterize their photometric and structural properties.

## Method

1. **AEN-based selection**: UCDs appear as marginally resolved sources in Gaia,
   producing elevated astrometric excess noise (AEN > 0.5 mas) compared to stars.
2. **Radial profile analysis**: Search in concentric annuli around target galaxies,
   subtract local background, identify statistically significant excesses.
3. **Multi-wavelength cross-match**: Confirm candidates using Legacy Survey morphology,
   colors, and (where available) spectroscopic data.

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
uv run python scripts/phase1_literature/analyze_gaia_properties.py
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

## Key Results from Pilot Study

- **1,542 known UCDs** compiled from 6 literature sources
- **59% Gaia DR3 match rate** for known UCDs
- **Background density** varies 10x with galactic latitude (60/deg^2 at |b|>70 to 600/deg^2 at |b|<30)
- **7 galaxies** show high-contrast (>10x) UCD signal excess in pilot search
- **AEN is the primary discriminator** — color (BP-RP) alone does not separate UCDs from background
