# Phase III: Background Characterization — Task Tracking

**Goal:** Measure the spatially varying density of sources passing the frozen Gaia
selector and provide valid host-specific controls.

**Status:** Design review

## III.1 Control design

- [x] Audit the inherited random-field, annulus, and legacy background methods
  (2026-07-18).
- [x] Draft the three-layer background design and permanent failure-state rules
  (2026-07-18).
- [x] Approve paired off-target controls as primary, with a valid local annulus and
  large-field model as robustness methods (2026-07-18).
- [x] Block inferential background assignment for unresolved group or cluster
  environments while retaining exploratory profiles (2026-07-18).
- [x] Permit a conservative K-luminosity-based upper `R200c` proxy for isolated
  centrals in the geometry fixture only (2026-07-18).

## III.2 Geometry validation

- [x] Build the five-case geometry-only fixture (2026-07-18).
- [x] Validate spherical aperture areas, halo exclusion, neighboring-halo screening,
  and explicit unavailable states; all nine checks pass (2026-07-18).
- [ ] Freeze control-candidate generation before inspecting selected-source counts.

## III.2a Environment reference

- [x] Stage Kourkchi-Tully 2017 member and group tables outside the repository with
  source identifiers and SHA-256 provenance (2026-07-18).
- [x] Audit all 2,155 hosts and accept 1,792 unique associations within the
  shift-calibrated 5-arcsec rule; preserve 2 ambiguities and 361 unmatched hosts
  (2026-07-18).
- [x] Audit whether accepted group `R2t` and association `R1t` provide conservative
  exclusion geometry; neither is a universal one-radius solution (2026-07-18).
- [ ] Approve separate exclusion treatment for isolated principals, ordinary groups,
  and rich groups or clusters.

## III.3 Frozen-selector background experiment

- [ ] Define spatial development and validation fields.
- [x] Select a deterministic five-host review set without using Gaia source counts
  (2026-07-18).
- [x] Run one bounded target/two-comparison field-condition query without applying
  the selector; all six checks pass in 11.19 seconds (2026-07-18).
- [x] Extend pre-selector measurements to all five review hosts using 13 frozen
  patches; all nine checks pass in 46.93 seconds, and no patch is approved as a
  scientific background (2026-07-18).
- [ ] Recompute the random-field experiment with exact usable areas and the shared
  frozen selector.
- [ ] Calibrate matching tolerances and the conservative Galactic-latitude limit.

## III.4 Interface with the real host measurement

- [x] Confirm that the 0.1-degree field-condition circles are query benchmarks only
  and do not define the real host aperture (2026-07-18).
- [x] Require concentric circular annuli for the real radial profile and a separately
  calibrated central exclusion for galaxy substructure and H II contamination
  (2026-07-18).
- [ ] Define the exploratory physical-kpc annuli and host-size-normalized annuli
  under BT-021 before a real host search.
- [ ] Calibrate the central exclusion and final radial signal region under BT-021.

Progress, 2026-07-18:

- [x] Audit the count-blind angular geometry for all 2,155 hosts; all seven checks
  pass, and no `R50` field is currently available.
- [x] Define a recombinable exploratory physical-ring view while preserving
  continuous source radius; the displayed edges are not final boundaries.
- [x] Remove the inherited two-degree cap from the design requirement: a 600 kpc
  diagnostic radius exceeds two degrees for 1,018 hosts.
- [ ] Acquire provenance-bearing `R50` measurements under BT-020 before calibrating
  the normalized central exclusion.
- [ ] Implement and validate tiled retrieval and exact per-ring usable areas.

## Review

- The inherited 0.8-degree fields use an obsolete selector and divide by 2.0 square
  degrees rather than the exact circular area.
- The inherited Phase IV annulus can be absent under the two-degree cap and does not
  exclude the host or environment halo.
- The current host catalog lacks the verified size, halo, and environment fields
  required to finalize exclusion radii.
- The query-free fixture evaluates 20 symmetric candidates: 11 accepted and 9
  rejected, with a maximum Galactic-latitude mismatch of `7.11e-14` degrees.
- `1.5 R2t`, `2 R2t`, and `3 R2t` enclose 91.73%, 97.73%, and 99.77% of accepted
  group members, while one association `R1t` encloses 86.41% of usable members;
  no universal safety factor is frozen.
- The first live-archive test found 121, 100, and 122 Gaia sources in three equal
  patches at exactly the same Galactic latitude. Gaia coverage and total source
  density must therefore be measured, but three patches cannot set a tolerance.
- The five-host review shows larger field-condition variation for the two group
  cases. Total Gaia density is partly signal-sensitive near a target and cannot be
  used as a rigid matching requirement.
