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
- [ ] Audit whether accepted group radii and masses provide conservative exclusion
  geometry for group members and principals.

## III.3 Frozen-selector background experiment

- [ ] Define spatial development and validation fields.
- [ ] Run one bounded target/control query and benchmark it.
- [ ] Recompute the random-field experiment with exact usable areas and the shared
  frozen selector.
- [ ] Calibrate matching tolerances and the conservative Galactic-latitude limit.

## Review

- The inherited 0.8-degree fields use an obsolete selector and divide by 2.0 square
  degrees rather than the exact circular area.
- The inherited Phase IV annulus can be absent under the two-degree cap and does not
  exclude the host or environment halo.
- The current host catalog lacks the verified size, halo, and environment fields
  required to finalize exclusion radii.
- The query-free fixture evaluates 20 symmetric candidates: 11 accepted and 9
  rejected, with a maximum Galactic-latitude mismatch of `7.11e-14` degrees.
