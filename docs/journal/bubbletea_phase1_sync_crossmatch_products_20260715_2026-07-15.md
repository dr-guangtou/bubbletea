---
date: 2026-07-15
repo: bubbletea
branch: phase1_sync_crossmatch_products_20260715
tags:
  - journal
  - phase1
  - crossmatch
---

## Progress

- Completed BT-004 without modifying the legacy or v2 literature databases.
- Added `synchronize_crossmatch_products.py` with read-only canonical loading,
  exact Gaia source-ID retrieval, batched Legacy Survey cones, retries, complete
  audits, and a provenance manifest.
- Measured Legacy batches of 10, 50, and 200 targets; selected the measured
  50-target batch, while Gaia uses the measured 250-identifier batch.
- Retrieved all 962 unique Gaia sources and exported all 963 canonical Gaia
  associations represented by 1,097 provenance rows.
- Queried all 4,359 canonical positions against Legacy Survey DR10 and exported
  3,723 matches while retaining 636 no-match audit states.
- Added `validate_crossmatch_products.py`; all product, digest, count, radius,
  candidate-JSON, and shared-source checks pass.
- Preserved the 632-row Gaia and 917-row Legacy products unchanged and recorded
  their SHA-256 digests in the new manifest.

## Lessons Learned

- Canonical association counts differ legitimately from provenance-row counts:
  1,097 Gaia-bearing rows represent 963 canonical associations and 962 sources.
- The old Legacy export does not contain returned source coordinates or match
  separations and therefore cannot support spherical revalidation.
- Legacy matching contains material ambiguity: 620 targets have two or three
  in-radius candidates, and 220 selected sources are shared by multiple canonical
  targets.
- Repeated full retrievals returned identical per-batch candidate counts, while
  locally sorted great-circle selection keeps derived row order deterministic.

## Key Issues

- The one-arcsecond Gaia and two-arcsecond Legacy radii remain historical working
  parameters, not calibrated scientific thresholds.
- BT-014 and BT-015 are the remaining Stage 1 provenance/documentation tasks
  before building the labeled benchmark in BT-019.
