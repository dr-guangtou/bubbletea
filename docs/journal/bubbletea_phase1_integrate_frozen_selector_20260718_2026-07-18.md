---
date: 2026-07-18
repo: bubbletea
branch: phase1_integrate_frozen_selector_20260718
tags:
  - journal
  - phase1
  - selector
  - phase4
---

## Progress

- Added `scripts/utils/point_source_selector.py` as the shared inference path for
  `point_source_logistic_model_v1`.
- Replaced the historical Phase IV Model C calculation and removed its excess-noise
  and proper-motion query prefilters.
- Restricted retrieval to the measured benchmark Gaia G-magnitude domain and added
  probability, decision, and selector-version fields to scored rows.
- Added a seven-check integration validator; stored development probabilities agree
  to `1.11e-16`, and all decisions match exactly.
- Updated `docs/SPEC.md`, `docs/todo.md`, and the Phase IV plan with the frozen
  integration contract and review evidence.

## Lessons Learned

- Selector parity includes the archive query denominator; upstream prefilters can
  silently create a different selection function even when the model is unchanged.
- A serialized model must be loaded only after its digest, version, and input-feature
  order have been verified.
- Live search execution must remain separate from selector integration while the
  background geometry and significance model are scientifically unresolved.

## Key Issues

- BT-005 remains open because the two-degree query cap does not cover the declared
  background annulus for the nearest hosts.
- BT-006 remains open because the pilot significance diagnostic omits background
  uncertainty and small-count calibration.
- The next task is a new-branch background-method design that compares valid local
  and off-target controls without running the legacy pilot as scientific evidence.
