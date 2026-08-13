# Phase IV: Pilot Search — Task Tracking

**Goal:** Execute the UCD search around Top 100 targets and identify new candidates using the radial excess method.

**Status:** In progress

---

## IV.1 Search Pipeline Development

- [x] Integrate `point_source_logistic_model_v1` as the single shared Gaia selector
  with exact feature, missing-value, threshold, and version parity; validate locally
  before any live pilot query (completed 2026-07-18)

- [x] Implement `scripts/phase4_search/radial_search.py` (2026-05-11)
  - [x] Gaia DR3 query around target ($R < 300$ kpc)
  - [x] Replace historical Model C with the frozen v1 selector (2026-07-18)
  - [x] Calculate radial density profile (sources/deg$^2$ vs $R_{\text{kpc}}$)
  - [x] Implement annulus background estimation ($150$-$300$ kpc)
- [x] Implement statistical excess detection (Poisson significance) (2026-05-11)

## IV.2 Validation: Literature Recovery

- [x] Run search around **MESSIER 087** (Virgo) (2026-05-11)
  - [x] Verify recovery of known literature UCDs (74 recovered)
  - [x] Check contrast against local background (22.6x)
- [x] Run search around **NGC 5128** (Centaurus A) - (Processed in top tier)
- [x] Verify selection completeness and purity statistics (2026-05-11)
- [ ] Run the M60 positive control using the unchanged selector and frozen 0--600
  kpc rings (started 2026-08-12)
  - [x] Freeze the count-blind design and known-object recovery table (2026-08-12).
  - [x] Measure one aggregate Gaia source count for the raw retrieval workload:
    45,402 sources in the frozen magnitude range (2026-08-12).
  - [x] Verify compact Legacy Survey DR10 three-color cutouts using the two reliable
    confirmed M60 UCDs (2026-08-12).
  - [x] Freeze explicit visual-review columns: color alone cannot label a compact
    star-forming region, incomplete catalog coverage is not negative evidence, and
    blend or image-problem flags require visual inspection (2026-08-12).
  - [x] Retrieve all 45,402 magnitude-limited Gaia rows in verified strips, apply the
    unchanged selector locally, and preserve the 14-ring profile; 4,920 sources pass
    selector version 1 (2026-08-12).
  - [x] Recover both reliable UCD controls and all nine literature candidates with a
    unique Gaia identifier; keep 18 objects without a unique identifier explicitly
    not testable by exact identifier (2026-08-12).
  - [x] Freeze a representative 400-source contamination-audit sample separately
    from the known controls and promising-candidate shortlist before visual
    inspection (2026-08-12).
  - [x] Retrieve and verify all 400 compact Legacy Survey cutouts and create four
    blinded radial-zone contact sheets; keep every visual field not reviewed
    (2026-08-12).
  - [x] Plot G magnitude against raw BP/RP flux-excess factor for the complete
    selector-retained population and frozen audit sample in all four radial zones
    (2026-08-12).
  - [x] Build an empirical Legacy Survey appearance and photometry reference for 680
    confirmed UCDs and 44 Saifollahi high-probability candidates (2026-08-12).
    - [x] Freeze the two provenance-defined cohorts before inspecting catalog or
      imaging outcomes (2026-08-12).
    - [x] Record compact three-color cutouts or explicit unavailable outcomes and
      create an eight-page atlas of 707 non-placeholder images (2026-08-12).
    - [x] Test Gaia NSS, galaxy-candidate, and QSO-candidate membership by exact Gaia
      identifier where possible (2026-08-12).
    - [x] Retrieve auditable Legacy Survey DR10 Tractor matches with photometry,
      quality flags, model type, and available shape measurements (2026-08-12).
    - [x] Document the measurements and interpretation limits in plain language
      (2026-08-12).
  - [ ] Keep possible contaminants as review flags; do not remove them from the
    selector-v1 radial profile during this first pass.

## IV.3 Pilot Search Execution

- [x] Execute search for all Top 20 pilot targets (2026-05-11)
- [x] Filter targets by minimum $|b| > 30^\circ$ (Applied)
- [ ] Generate candidate lists per galaxy
- [ ] Aggregate all candidates into a master pilot catalog


## IV.4 Candidate Ranking & QA

- [ ] Rank candidates by frozen v1 probability and radial significance
- [ ] Generate "Candidate Cards" (thumbnails + Gaia properties)
- [ ] Produce Phase IV Summary Report

## Review — 2026-07-18 frozen-selector integration

- Shared inference reproduces all stored development probabilities and decisions.
- The Gaia query retains the full measured magnitude-domain denominator and removes
  the two legacy astrometric prefilters.
- No live scientific pilot was run because BT-005 background coverage and BT-006
  significance calibration remain open.

---

## Scripts to Develop

| Script | Purpose |
|--------|---------|
| `scripts/phase4_search/radial_search.py` | Core search engine for radial excess detection |
| `scripts/phase4_search/validate_recovery.py` | Cross-match search results with literature DB |
| `scripts/phase4_search/process_pilot.py` | Batch processing and aggregation for Top 100 |
