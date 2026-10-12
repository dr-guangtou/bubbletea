# Phase II: Target Galaxy Sample — Task Tracking

**Goal:** Define and prioritize the nearby galaxy sample (D < 50 Mpc) for the
UCD search pipeline.

**Status:** In progress

**Checkpoint (2026-10-12):** The inherited 2,155-host table is useful for development,
not a frozen final parent sample. Its May ranking and catalog are historical.
Consistent half-light radii, morphology, and parent-sample completeness remain
open (BT-020, BT-026, BT-027). See [current status](../current_status.md),
[validation stage 2](scientific_validation.md#stage-2-define-the-galaxy-samples),
and [roadmap](../PLAN.md).

---

## II.1 Sample Compilation

- [x] Migrate `galaxy_sample_ranked.csv` from legacy project (2026-03-27)
- [x] Verify sample distance range ($D \le 25$ Mpc, $N=2,155$) (2026-05-11)
- [x] Audit distance provenance and morphological completeness (2026-05-11)
- [x] Manual verification of coverage check for Top 10 galaxies (100% overlap) (2026-05-11)
- [x] Filter by galactic latitude ($|b| > 20^\circ$ applied in legacy build) (2026-05-11)

## II.2 Galaxy Properties

- [x] Collect total luminosities (K-band present for all 2,155 galaxies) (2026-05-11)
- [x] Fetch reliable morphology (Hubble type) from HyperLEDA for Top 500 galaxies (2026-05-11)
- [ ] Fill the remaining 75% morphological gap using PGC/NGC identifiers
- [x] Calculate physical scales (arcsec to kpc conversion factors available via distance) (2026-05-11)
- [x] Verify RA/Dec completeness (100% complete) (2026-05-11)

## II.3 Survey Coverage Check

- [ ] Overlap with Legacy Survey DR10 footprint
- [ ] Overlap with HSC-SSP footprint
- [ ] Identify high-priority targets with deep imaging

## II.4 Ranking and Prioritization

- [x] Define ranking metric (Luminosity, Distance, Coverage, LitBonus, FieldBonus) (2026-05-11)
- [x] Select Top 100 targets for Pilot Search (Phase IV) (2026-05-11)
- [x] Generate final target sample catalog (`pilot_sample_top100.csv`) (2026-05-11)

---

## Scripts to Develop

| Script | Purpose |
|--------|---------|
| `scripts/phase2_galaxy_sample/compile_sample.py` | Build unified sample from various catalogs |
| `scripts/phase2_galaxy_sample/coverage_check.py` | Check footprint overlap with imaging surveys |
| `scripts/phase2_galaxy_sample/rank_targets.py` | Rank galaxies for prioritized search |
