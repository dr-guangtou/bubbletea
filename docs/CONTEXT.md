# BubbleTea Project Context

**Reviewed:** 2026-07-14
**Purpose:** Scientific and operational context for continuing the project

## Project Identity

BubbleTea is an exploratory, reproducible astronomy research project, not a
software package. It investigates whether Gaia DR3 astrometry and photometry can
be used to find compact stellar systems around nearby galaxies, including
ultra-compact dwarf galaxies (UCDs) and luminous or extended globular clusters.

The primary target is the UCD population, not ordinary globular clusters. The
physical boundary between UCDs and globular clusters is understood to be fuzzy and
not perfectly physical. Operationally, BubbleTea should retain objects that Gaia
clearly reveals as extended and that are probably too luminous or too large to be
ordinary globular clusters. Ambiguous luminous or extended clusters may therefore
remain in the candidate sample, but the project should not broaden into a general
globular-cluster search.

The distance scope is sensitivity-driven. Within 25 Mpc, the project should seek a
more complete view of the Gaia-detectable UCD population. Between 25 and 50 Mpc,
it should retain only the most obvious UCD regime. Reliable luminosity and size
limits must be measured as functions of distance, Gaia photometric limits,
astrometric capability, and catalog uncertainties rather than assumed globally.

The central scientific motivation is to move beyond searches concentrated on
rich clusters and massive early-type galaxies. A credible sample in lower-density
environments would constrain whether UCDs are predominantly stripped galaxy
nuclei, unusually massive globular clusters, or a mixture of formation channels.

## Scientific Strategy

BubbleTea's scientific outputs have the following approved priority order:

1. Provide conclusive statistical evidence for or against an excess of extended
   but compact stellar systems, such as UCDs, around nearby galaxies relative to
   the background.
2. Test how the measured excess, including non-detections, correlates with host
   properties such as luminosity, color, environment, halo mass, and morphology.
3. Produce prominent candidate lists of previously unidentified UCDs around nearby
   systems, ranked primarily by the probability that each source is not a point
   source.

The first two objectives are population-level statistical analyses. Individual
candidate identification is valuable but must remain subordinate to a measurable,
reproducible selection function and background comparison.

The analysis is direction-neutral: all eligible galaxies count, and positive,
zero, and negative overdensities are retained. Null results are acceptable. A
3-sigma excess relative to the full background uncertainty in a defined radial
range is the initial standard for a reliable overdensity, subject to calibration
of the radial range and correction for any searched alternatives. Low-mass dwarf
galaxies provide useful false-positive checks, including for compact star-forming
and H II regions that require color or morphology rejection.

The required host variables for the primary correlation analysis are luminosity,
`R50` in a consistent band, and morphology. Optical color, environment, central
velocity dispersion, and other properties are optional when coverage is
sufficient. The current 2,155-galaxy table has complete K-band luminosity, only 200
base morphology values, and no `R50`; the separate HyperLEDA product contains 457
morphology values.
The luminosity band is flexible and should favor the most complete consistent
measurement; complete K-band luminosity is the current practical starting point.
Hosts missing `R50` or morphology remain in the Gaia overdensity analysis. The
missing fields should be recovered through careful literature and database
cross-matching and affect only correlations that require them.

The early search should retain a sequence of annuli. A final signal aperture may
be defined as `[M, N] x R50`, while a host-dependent inner mask excludes the main
galaxy body. Measured `R50` is preferred; a calibrated luminosity- or stellar-mass
to-`R50` relation may supply a temporary estimate. Example values such as
`2 x R50` are not fixed until validation, and physical-kpc profiles should remain
available beside normalized profiles.

The primary statistical sample and overdensity measurements use Gaia data alone.
External imaging is value-added: multi-band coverage can support SED and
color-color checks, while HST, Euclid, or other high-resolution imaging can test
morphology. Targeted imaging analysis may follow significant Gaia excesses, but
imaging availability must not alter the Gaia statistical selection.

Calibration of the Gaia-only non-point-source probability remains open. The
reference design should preserve uncertainty in the mixed confirmed/candidate UCD
sample and compare it with spectroscopic QSOs and compact galaxies, Gaia binary
stars, and compact star-forming or H II regions over the relevant magnitude range.
For now, Gaia `BP-RP`, or another validated Gaia-native color combination, is the
only approved route for rejecting obviously very blue star-forming or H II
contaminants in the primary statistical selector; exact thresholds require
validation.

1. Compile literature compact stellar systems as a reference sample.
2. Characterize their Gaia detection rate and observable distributions.
3. Define a nearby host-galaxy sample and prioritize targets.
4. Measure the sky density of Gaia sources that mimic the reference population.
5. Search for a radial excess around each galaxy relative to a local background.
6. Rank individual candidates and validate them with imaging, morphology, and
   spectroscopy before drawing population-level conclusions.

The core observable is Gaia astrometric excess noise (AEN). A compact stellar
system can be marginally resolved by Gaia and therefore fit poorly by the
single-source astrometric model. AEN is useful statistically but is not unique to
UCDs: binaries, crowded or poorly measured stars, and compact background galaxies
also produce elevated values. The project must therefore measure an excess over a
local control population rather than interpret every selected source as a UCD.

The inherited baseline criteria from Voggel et al. (2020) are approximately:

- Gaia G magnitude from 16 to 21 mag.
- BP-RP color from 0.8 to 1.8 mag.
- AEN above 0.5 mas, or a probabilistic score based on AEN significance and the
  BP/RP flux-excess factor.
- Permissive proper-motion rejection: retain a source when proper motion is
  missing, statistically insignificant, or below 2.92 mas/yr.
- Search in physical radius and estimate contamination locally.

Background estimation should be deliberately redundant. Large-area averages and
off-target circular or annular controls should be compared. Controls must match or
model Galactic latitude, lie beyond a conservative buffered upper bound on the
host's `R200c` inferred from luminosity or size relations, and avoid other nearby
galaxies. Differences among valid background methods are part of the scientific
uncertainty rather than an implementation nuisance.

The final host sample should apply a conservative absolute Galactic-latitude cut.
Its value must be measured by testing the canonical selection across latitude and
identifying where Milky Way background density and variance prevent meaningful UCD
constraints. The inherited 20-degree and 30-degree limits are exploratory only.
No sensitivity threshold is known in advance; defining it from neutral background
and sensitivity measurements is part of the research rather than a value to assume.

The first-stage analysis treats group, cluster, and isolated galaxies with the same
host-centered procedure and does not use environment to select methods. Known
dense systems within 50 Mpc should be flagged for later analysis. Their local and
global background estimates must both be examined because a local control may
contain a genuine group or cluster compact-system population.

Overlapping search regions are processed independently in the first round, so one
Gaia source may contribute to multiple host measurements. All source-host links
must be retained and flagged as dependent; a later probabilistic model may assign
host-membership probabilities.

Host overdensity may eventually act as contextual evidence that an individual
candidate is real, but this remains an untested suspicion. Gaia-only source
evidence and host-level excess must remain separate in first-round outputs to avoid
circularly using candidates to create an excess and then using that excess to boost
the same candidates.

The project may conclude with candidates; individual confirmation is not mandatory.
The confirmation standard is intentionally high: space-based high-resolution
imaging showing UCD-like resolved structure, or spectroscopy giving a redshift or
velocity consistent with the associated nearby system. Gaia extendedness and
overdensity alone never constitute confirmation.

The per-galaxy excess response variable is also open. Raw background-subtracted
counts, area densities, and host-normalized quantities should be compared broadly
using calibration, controls, simulations, and analogous methods from other fields.
It must not be chosen because it produces the strongest desired correlation.

The final correlation analysis should use a lower-luminosity-limited volume where
the host catalog is measured to be close to complete; greater than 80 percent is an
example target, not yet a fixed threshold. The entire valid host sample should also
be shown to reveal system diversity, but it is descriptive or exploratory when not
selection-complete. The ranked Top-100 is only a development pilot.
The parent census should come from a published nearby-galaxy catalog with an
explicit completeness analysis, such as catalogs developed for gravitational-wave
counterpart searches or dark-siren cosmology. The current merged table cannot
establish its own completeness without that external selection function.
Where a parent selection function is public, it should be applied and verified
directly; secondary catalogs may enrich properties without changing the parent
sample denominator silently.

Gaia scan-pattern variation may affect spatial resolution and compact-source
sensitivity. The first stage may assume sufficient uniformity, but the final
analysis must test residual candidate density and extendedness against available
Gaia coverage, astrometric-quality, and scan-law-related sky patterns.

## Repository Evolution

The frozen `ucd_project/` tree contains the exploratory predecessor. Its principal
results were a 1,542-entry literature database, a 2,155-galaxy target sample, a
50-field background experiment, and radial searches around a small set of hosts.
The active repository reorganizes that work into reproducible phases and rewrites
scripts on demand rather than copying the legacy scripts wholesale.

The formal reorganization and Stage 1 literature stabilization are now preserved
in feature and merge commits. Canonical data products retain manifests and file
digests; historical exploratory outputs remain labeled rather than silently
replaced.

## Verified Current State

The legacy and exploratory values below were measured directly on 2026-07-14;
canonical literature and cross-match values were remeasured on 2026-07-16.

| Component | Verified state |
|---|---|
| Immutable legacy literature database | 2,108 rows from 9 sources |
| Canonical v2 reference database | 5,049 records, 4,359 canonical objects |
| Canonical classifications | 740 confirmed, 1,515 candidate, 2,082 rejected, 22 uncertain |
| Rows flagged as UCDs | 2,064 |
| Gaia-matched database rows | 1,097 |
| Legacy-matched database rows | 0 |
| Exact distinct coordinate pairs | 1,928 |
| Exact duplicate-coordinate groups | 180 |
| Canonical Gaia product | 963 associations, 962 unique Gaia DR3 sources |
| Canonical Legacy Survey product | 3,723 matches plus 636 audited no-matches |
| Historical matched CSVs | 632 Gaia rows and 917 Legacy rows; hashed but superseded |
| Galaxy sample | 2,155 galaxies, 2.586-25.000 Mpc |
| Legacy Survey coverage checks | 500 galaxies queried; 499 returned coverage |
| HyperLEDA morphology | 457 of 2,155 galaxies have a retrieved type |
| Pilot target table | 100 galaxies; 14 literature hosts; 7 proxy cluster members |
| Background experiment | 500 successful Gaia fields |
| Current radial-search summary | 17 galaxies |
| Candidate files | 18 files, 18,552 rows, 17,995 unique Gaia source IDs |
| Figures | 10 PNG files, each with a companion Markdown caption |

The database includes candidates as well as confirmed systems. Only the 377 rows
from the Voggel/Fahrion 2019 compilation are currently marked `confirmed`; the
remaining sources are marked `candidate`. Counts must not be described as counts
of unique confirmed UCDs.

## Work Completed by Phase

### Phase I: Literature Reference Sample

- Expanded the database from 1,542 rows in 6 sources to 2,108 rows in 9 sources.
- Added ingestion, SQLite management, Gaia cross-match, Legacy Survey cross-match,
  redundancy-check, property-analysis, and selection-model scripts.
- Populated 1,097 database rows with Gaia data.
- Generated eight Phase I diagnostic figures.
- Compared a constant AEN model, an inverse-distance threshold, and a
  probabilistic score based on AEN significance and BP/RP flux excess.

The literature reference database and canonical cross-match products are now
non-destructively validated and synchronized. Selector calibration remains open.
The destructive redundancy script remains prohibited because exact-coordinate
groups are preserved as provenance-bearing many-to-one associations.

### Phase II: Host-Galaxy Sample

- Audited a 2,155-galaxy sample assembled from LVG, Cosmicflows-4, NED-LVS, and
  SGA-2020, with complete coordinates, distances, and K-band luminosities.
- Queried Legacy Survey coverage for the top 500 rows.
- Retrieved HyperLEDA morphology for 457 galaxies.
- Ranked the covered subset and wrote a Top-100 pilot table.

The ranking is provisional. The environment flag uses rough sky circles around
Virgo and Fornax, not group or cluster membership, so the reported field fraction
is not a defensible environmental classification. Coverage has not been tested for
the remaining 1,655 galaxies or for the full 300 kpc search aperture.

### Phase III: Background Characterization

- Generated 500 random positions with absolute Galactic latitude above 20 degrees.
- Completed all 500 Gaia queries in circular fields of radius 0.8 degrees.
- Fitted the stored densities with
  `density = 10950.5 * exp(-abs(b) / 10.407) + 417.7` sources per square degree.
- Confirmed a strong Galactic-latitude trend and substantial field-to-field
  scatter, supporting local rather than global background estimation.

The numerical model applies only to the exact Phase III query and selection. Its
high-latitude floor is about 418 per square degree, substantially higher than the
legacy experiment because the selection changed. It is not a universal UCD-mimic
background model.

### Phase IV: Pilot Radial Search

- Implemented a Gaia query, permissive proper-motion filter, probabilistic score,
  physical radial bins, and an outer-annulus background calculation.
- Produced a current summary for 17 galaxies and candidate files for 18.
- Recovered strong central excesses around established rich systems including M87,
  M60, NGC 1399, and NGC 1316.
- The largest stored central significance is for M87, with a contrast of 22.64 and
  the script's reported significance of 42.18.

These results establish that the pipeline detects dense compact-source systems,
but they do not yet establish new UCD discoveries. Candidate-level validation,
selection-function measurement, and robust significance calculations remain open.

## Critical Method Consistency Issue

`Model C` does not currently denote one reproducible selection function:

- Phase I uses `0.7 * probability_aen + 0.3 * probability_bp_rp_excess > 0.5`.
- Phase III uses the same score after G, AEN, and AEN-significance prefilters, but
  applies neither the Phase IV color term nor its proper-motion filter.
- Phase IV uses `0.6 * probability_aen + 0.3 * probability_bp_rp_excess +
  0.1 * color_in_range > 0.5` after a different prefilter that includes proper
  motion.

Consequently, literature completeness, random-field background density, and pilot
candidate density are not measurements of the same selection function. The
criteria must be frozen in one shared implementation before further scaling.

## Other Scientific and Reproducibility Risks

The persistent issue register is `docs/todo.md`. Its issue identifiers should be
used in plans, journals, and commits when resolving the findings below.

- The Phase I model comparison measures recovery of literature entries but does
  not jointly measure purity or false-positive rate on a matched control sample.
- BT-007 replaced the rectangular Gaia and Legacy matching with NOIRLab Q3C cones,
  independent great-circle radius enforcement, and ambiguity diagnostics. BT-004
  generated canonical products with complete 4,359-target audits: 963 canonical
  Gaia associations and 3,723 Legacy Survey matches; 620 Legacy targets have more
  than one in-radius candidate and remain explicitly ambiguous.
- Phase III divides counts by 2.0 square degrees, while a 0.8-degree circle has an
  area of 2.010619 square degrees. This is a measured 0.531 percent normalization
  difference and is easy to correct once the selection is frozen.
- The Phase IV 2-degree query cap reaches only 129.2 kpc at 3.7 Mpc. M81 and
  NGC 253 therefore have no data in the declared 150-300 kpc background annulus;
  their stored background densities are zero and their contrasts are undefined.
- Three intended Top-20 eligible targets are absent from the current summary:
  M49, M59, and NGC 1097. A stale M49 candidate/profile pair remains on disk.
- Candidate catalogs overlap: 557 Gaia sources occur in more than one host file.
  A master catalog needs explicit host-association and duplicate policies.
- Recovery validation matches each host file against the entire literature
  database and has an index-direction error when labeling unmatched candidates.
  Its recovery and new-candidate counts are not yet reliable.
- Central significance is calculated as `(observed - expected) / sqrt(expected)`
  without propagating uncertainty in the locally estimated background. The
  reported values are ranking diagnostics, not final detection significances.
- Only `reference/voggel2020/` and `reference/wang2023/` follow the current
  paper-folder provenance convention. Seven ingested literature sources lack the
  required per-paper reference package.
- `README.md`, `docs/PLAN.md`, `data/README.md`, `reference/summary.md`, and phase
  trackers contain conflicting sample sizes and phase statuses.
- All 23 active Python files parse, but Ruff reports 397 violations. The current
  scripts have not passed the configured pre-commit gate.
- `docs/SPEC.md`, required by the repository instructions as the architectural
  source of truth, is absent.

## Guardrails for Future Work

- Do not call a selector `Model C` without recording its exact version and terms.
- Do not describe database rows as unique or confirmed systems unless duplicate
  associations and confirmation labels have been applied explicitly.
- Do not interpret Gaia-selected sources as UCDs. Gaia identifies extended-source
  candidates; imaging and spectroscopy are required for astrophysical
  classification.
- Do not optimize the pipeline for recovery of ordinary globular clusters. The
  primary target is UCDs, with ambiguous objects retained only where extension and
  exceptional luminosity or size make a UCD interpretation plausible.
- Do not compare completeness, contamination, or density values produced by
  different selection functions.
- Do not report a zero local background when the required control area was not
  observed.
- Do not describe a radial excess as a discovery until recovery, null statistics,
  host association, and ancillary-data checks have been validated.
- Do not scale a query or pilot run until the same workflow succeeds on a small,
  measured validation set.

## Recommended Next Step

Do not run the full Top-100 search yet. The next research milestone should be a
small, measured validation cycle that makes the selection function and statistical
interpretation reproducible:

1. Interview the project lead to define the intended scientific sample: UCDs only,
   UCDs plus extended globular clusters, or a broader compact-stellar-system class;
   define confirmation labels, distance range, and the role of environment.
2. Create `docs/SPEC.md` from those decisions, including one canonical selection
   function, cross-match geometry, background estimator, significance method, and
   required provenance fields.
3. Reconcile the literature database non-destructively: source counts, duplicate
   groups, confirmation status, Gaia and Legacy exports, and per-paper provenance.
4. Implement the canonical selection once in a shared utility and use it in the
   literature, random-field, and radial-search analyses.
5. Validate on a deliberately small set: one rich known host such as M87, one
   low-signal control, and one nearby target that exercises the angular-radius cap.
6. Measure literature recovery and control-field contamination with the same code,
   then choose thresholds from completeness-purity tradeoffs rather than recovery
   alone.
7. Only after that validation, rerun the pilot, aggregate a host-aware master
   candidate catalog, and begin imaging and spectroscopic characterization.

## Key Entry Points

- Project overview: `README.md`
- Master phase plan: `docs/PLAN.md`
- Scientific source of truth: `docs/SPEC.md`
- Current journals: `docs/journal/`
- Lessons: `docs/lessons/LESSON.md`
- Cross-phase issue register: `docs/todo.md`
- Initial validation plan: `docs/plans/scientific_validation.md`
- Literature database utilities: `scripts/phase1_literature/ucd_database.py`
- Selection experiment: `scripts/phase1_literature/distance_selection.py`
- Background experiment: `scripts/phase3_background/`
- Pilot search: `scripts/phase4_search/radial_search.py`
- Recovery validation: `scripts/phase4_search/validate_recovery.py`
- Central paths: `scripts/config.py`
- Frozen exploratory project: `ucd_project/`
