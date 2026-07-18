# Phase III: Background Characterization — Task Tracking

**Goal:** Measure the spatially varying density of sources passing the frozen Gaia
selector and provide valid host-specific controls.

**Status:** Design review

## III.1 Control design

- [x] Audit the inherited random-field, annulus, and legacy background methods
  (2026-07-18).
- [x] Draft the three-layer background design and permanent failure-state rules
  (2026-07-18).
- [ ] Approve the primary/control-method hierarchy.
- [ ] Approve treatment of unresolved group and cluster environments.
- [ ] Approve the first halo-exclusion-radius proxy.

## III.2 Geometry validation

- [ ] Build the five-case geometry-only fixture.
- [ ] Validate spherical aperture areas, halo exclusion, neighboring-halo screening,
  and explicit unavailable states.
- [ ] Freeze control-candidate generation before inspecting selected-source counts.

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

