# Initial Scientific Validation Plan

**Created:** 2026-07-14
**Status:** Ready for execution after initial scientific-definition interview
**Specification:** `docs/SPEC.md`
**Issue register:** `docs/todo.md`

## Goal

Establish a reproducible Gaia-only selection and statistical validation framework
before expanding the UCD search to a final galaxy sample. Preserve null and
negative results, quantify sensitivity, and separate population inference from
value-added candidate characterization.

## Stage 1: Stabilize Reference Data

- [ ] Reconcile literature rows, unique objects, source associations, confirmation
  tiers, and the 180 exact duplicate-coordinate groups (`BT-003`, `BT-028`).
- [ ] Repair spherical cross-match geometry and ambiguity handling (`BT-007`).
- [ ] Synchronize the Gaia and Legacy Survey exports with the canonical database
  (`BT-004`).
- [ ] Complete per-paper provenance packages and reconcile documentation counts
  (`BT-014`, `BT-015`).
- [ ] Build the labeled UCD and contaminant benchmark with fixed validation
  partitions (`BT-019`).

**Gate:** A non-destructive validation report reproduces all canonical counts and
every benchmark label retains provenance and uncertainty.

## Stage 2: Define the Galaxy Samples

- [ ] Review published nearby-galaxy censuses with public completeness analyses,
  including multi-messenger and dark-siren catalogs (`BT-027`).
- [ ] Select and verify a parent selection function without changing its denominator
  during catalog enrichment (`BT-027`).
- [ ] Retrieve consistent `R50` and morphology values with provenance and quality
  indicators (`BT-020`).
- [ ] Calibrate the conservative Galactic-latitude eligibility limit (`BT-022`).
- [ ] Freeze the near-complete primary sample and the broader valid diversity sample
  (`BT-026`).

**Gate:** The primary and diversity samples can be regenerated from documented
inputs, and every exclusion has a recorded reason.

## Stage 3: Calibrate One Gaia-Only Selector

- [ ] Compare Gaia extendedness features and color combinations on the fixed
  benchmark without treating uncertain UCD candidates as certain labels
  (`BT-002`, `BT-019`).
- [ ] Measure selection behavior across magnitude, distance, inferred luminosity,
  inferred size, Galactic latitude, and Gaia uncertainty properties (`BT-002`).
- [ ] Freeze one versioned selector used identically for literature, control fields,
  and host searches (`BT-002`, `BT-017`).
- [ ] Add fast deterministic validation scripts for selector parity and null handling
  (`BT-018`).

**Gate:** The selector has measured completeness and contamination behavior over a
declared applicability domain and one implementation produces all selections.

## Stage 4: Validate Background and Radial Statistics

- [ ] Recompute background behavior with the canonical selector and exact usable
  areas (`BT-009`).
- [ ] Compare large-field, off-target circular, and off-target annular backgrounds
  matched in Galactic latitude and screened for nearby halos (`BT-005`).
- [ ] Calibrate exploratory physical and `R50`-normalized annuli, including the
  central exclusion and trial factors (`BT-021`).
- [ ] Define and calibrate the full overdensity uncertainty and provisional 3-sigma
  evidence standard (`BT-006`).
- [ ] Compare per-galaxy excess metrics without selecting the strongest correlation
  (`BT-025`).

**Gate:** Known hosts, low-mass controls, nearby angular-cap cases, and blank fields
produce calibrated positive, zero, and negative measurements without special-case
code paths.

## Stage 5: Run an Auditable Pilot

- [ ] Implement immutable run metadata, target status, failure recording, and safe
  resume behavior (`BT-010`).
- [ ] Run a deliberately small validation set before any larger remote query.
- [ ] Build a source-level catalog with one-to-many host associations (`BT-011`).
- [ ] Validate literature recovery and candidate indexing (`BT-008`).
- [ ] Preserve Gaia-only candidate evidence separately from host context (`BT-024`).
- [ ] Record external imaging and spectroscopy only as value-added evidence
  (`BT-013`, `BT-028`).

**Gate:** A repeated pilot run produces the same versioned products, complete
failure accounting, and no stale files from another run.

## Stage 6: Population Analysis and Final Systematics

- [ ] Include every eligible host measurement, including zero and negative excess,
  in the appropriate population products.
- [ ] Quantify correlations in the primary near-complete sample and depict diversity
  in the broader valid sample.
- [ ] Flag known groups and clusters, compare local and global backgrounds, and
  perform dedicated secondary analysis (`BT-012`).
- [ ] Develop probabilistic host association only after independent first-stage
  measurements are stable (`BT-023`).
- [ ] Test Gaia scanning-pattern systematics and apply a model, uncertainty term, or
  quality mask only if measurements require it (`BT-029`).
- [ ] Pass Ruff and pre-commit without changing scientific behavior (`BT-016`).

**Gate:** Final claims state the selection domain, sample selection function,
background method sensitivity, trial handling, and remaining systematic limits.

## Small-Scale Validation Rule

Before each full execution, run the smallest representative local fixture or query
that exercises the same code path. Measure its runtime and output rather than
estimating either. Local deterministic checks should complete within the project
mandate's sub-minute validation window; remote archive latency must be measured and
recorded separately before scaling.

## Review

- [x] The plan follows the approved scientific priority order.
- [x] Population inference remains Gaia-only.
- [x] Candidate confirmation is optional and value-added.
- [x] Null and negative results remain valid outputs.
- [x] Full execution is blocked by explicit validation gates rather than an
  estimated schedule.
