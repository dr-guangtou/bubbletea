# UCD Visual Review Workbench — built and frozen for production

**Date:** 2026-08-19
**Scope:** Phase IV — interactive review tool for the UCD reference (680 confirmed + 44 Saifollahi candidates)

## What was done

Built the full data-preparation and application pipeline specified in
`docs/plans/ucd_visual_review_tool.md`:

- **Host-association register** — 724 objects resolved to `verified_unique_host`
  (411), `published_environment_only` (313), `host_unavailable` (0). 13 Voggel 2020
  "candidate stripped-nucleus / luminous-GC" objects excluded from the confirmed
  design reference. Cluster/group hosts adopt the cluster distance.
- **Retrievals** — wide (67″) Legacy Survey cutouts (707 + 17 placeholders skipped),
  10″ Gaia neighbors, external-catalog associations (SDSS/Quaia/morphology/NSS),
  all with versioned manifests + SHA-256 digests.
- **Review-input bundle** — one JSON per object + index + manifest.
- **Flask workbench** — append-only review DB, local API, image-dominant UI with
  two-scale images, match markers, source identification, and coordinate correction.

## Decisions made (project lead)

- Cross-match radii: Legacy Survey and Gaia neighbors both **10″** (was 2″/5″) to
  recover off-center literature coordinates.
- Legacy Survey matches filtered to **r < 23.0**.
- Decision flags **unified** to `include` / `exclude` / `hold` for both confirmed
  UCDs and candidates; candidate `include` = "keep in follow-up pool", never a
  promotion to confirmed.
- Gaia source = coordinate reference; Legacy source = photometry reference;
  `reference_quality` (`both`/`gaia_only`/`legacy_only`/`none`) is informational only.
- Discovery paper recorded per object (earliest year, or Fahrion `tableb1.dat` ref
  for Fahrion-only objects).

## Current state

- Production version frozen: bundle `ucd_visual_review_bundle_v1`, schema
  `review_schema_v1`, unified decision model.
- Review DB **reset** (empty); exports regenerated clean.
- "Pilot only" list filter defaults to off (full 724 objects).
- `validate_api.py` passes 15/15; all scripts ruff-clean.

## Next steps

1. Run the full source-by-source assessment of all 724 objects.
2. Export periodically (`scripts/phase4_search/export_ucd_visual_review.py`) and
   commit the versioned artifacts.
3. After review: derive the clean positive design reference (confirmed `include`)
   for designing Gaia + Legacy Survey selection rules.
