# Phase IV: Pilot Search — Task Tracking

**Goal:** Execute the UCD search around Top 100 targets and identify new candidates using the radial excess method.

**Status:** In progress

---

## IV.1 Search Pipeline Development

- [x] Implement `scripts/phase4_search/radial_search.py` (2026-05-11)
  - [x] Gaia DR3 query around target ($R < 300$ kpc)
  - [x] Apply Model C selection
  - [x] Calculate radial density profile (sources/deg$^2$ vs $R_{\text{kpc}}$)
  - [x] Implement annulus background estimation ($150$-$300$ kpc)
- [x] Implement statistical excess detection (Poisson significance) (2026-05-11)

## IV.2 Validation: Literature Recovery

- [x] Run search around **MESSIER 087** (Virgo) (2026-05-11)
  - [x] Verify recovery of known literature UCDs (74 recovered)
  - [x] Check contrast against local background (22.6x)
- [x] Run search around **NGC 5128** (Centaurus A) - (Processed in top tier)
- [x] Verify selection completeness and purity statistics (2026-05-11)

## IV.3 Pilot Search Execution

- [x] Execute search for all Top 20 pilot targets (2026-05-11)
- [x] Filter targets by minimum $|b| > 30^\circ$ (Applied)
- [ ] Generate candidate lists per galaxy
- [ ] Aggregate all candidates into a master pilot catalog


## IV.4 Candidate Ranking & QA

- [ ] Rank candidates by Model C score and radial significance
- [ ] Generate "Candidate Cards" (thumbnails + Gaia properties)
- [ ] Produce Phase IV Summary Report

---

## Scripts to Develop

| Script | Purpose |
|--------|---------|
| `scripts/phase4_search/radial_search.py` | Core search engine for radial excess detection |
| `scripts/phase4_search/validate_recovery.py` | Cross-match search results with literature DB |
| `scripts/phase4_search/process_pilot.py` | Batch processing and aggregation for Top 100 |
