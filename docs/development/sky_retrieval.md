# Random-sky field preparation and retrieval

**Consolidated:** 2026-10-12  
**Role:** Topic-organized development evidence, not a replacement for current scientific requirements.

[Science guide](../science_guide.md) · [Current status](../current_status.md) · [Documentation audit](documentation_audit.md)

## Current reading guidance

The count-blind 500-field grid, 12-field pilot, measured field conditions, and 398-field development retrieval are complete. Statements that the 102 reserved fields remain unopened are dated snapshots: their subsequent one-time evaluation is in background_measurements.md.

## Dated evidence

Each section below retains an original report's scientific content, measurements,
commands, and limitations. Status statements apply to that report's original date;
read the guidance above and current SPEC before following an old next step.

<a id="record-large_sky_field_grid"></a>

> Dated source record: `docs/large_sky_field_grid.md`. Superseded instructions are history, not current policy.

<!-- preserved_source_start: docs/large_sky_field_grid.md -->
## Fixed large-sky field grid

**Status:** Count-blind field identities and partition frozen
**Date:** 2026-07-19
**Issues:** BT-005, BT-009, BT-022

### Purpose

This grid replaces the inherited file of 500 unseeded random positions. It will be
used to measure how the density of sources passing the frozen selector changes
across the sky. It is separate from the galaxy-specific comparison regions used
for primary background subtraction.

No Gaia source count, selector probability, or passing-source density was read to
generate a coordinate or choose its partition. All 500 fields remain diagnostic;
none is approved as a scientific background.

### Why there are 500 fields and why the radius is 0.8 degree

The field count and radius preserve the scope of the inherited 500-field Phase III
experiment. They are not a new statistical power calculation and do not define the
real galaxy aperture.

Every field is a 0.8-degree-radius circle. Its exact spherical area is
2.010586633 square degrees. The earlier value 2.010619 is the flat-circle formula
`pi * radius^2`; 2.0 is a further approximation. The new workflow uses the
spherical area.

### How the positions are distributed

The existing galaxy catalog covers absolute Galactic latitude `|b| >= 20` degrees,
so the grid uses that same declared domain. It places 250 centers north and 250
south of the Milky Way plane.

Latitude is spaced uniformly in spherical area, not uniformly in degrees. In plain
language, each successive latitude represents the same amount of sky even though
lines of longitude converge toward a pole. Longitude advances by the fixed
golden angle, 137.507764 degrees. This is a standard deterministic spacing that
prevents successive points from lining up; it does not introduce randomness.

The measured absolute Galactic-latitude range is 20.080258–87.060276 degrees, and
the measured absolute ecliptic-latitude range is 0.098908–87.171146 degrees. The
minimum separation between any two centers is 6.429656 degrees, so the
0.8-degree-radius circles do not overlap.

### Development and held-back validation

A **sky block** is a broad fixed part of the sky used only for splitting this
experiment. It combines one 30-degree Galactic-longitude band with one of five
equal-sky-area absolute-Galactic-latitude bands and one Galactic hemisphere. All
fields in a block remain on the same side of the split.

The five latitude bands have edges at 20.000000, 28.269284, 37.244105, 47.460216,
60.273704, and 90.000000 degrees. Within each hemisphere/latitude combination, two
sky blocks are assigned to validation. Five of the ten combinations contribute a
third validation block. Stable hashes choose both the extra combinations and the
blocks, using positions and version strings only.

The frozen split contains:

| Partition | Sky blocks | Fields | Allowed use |
|---|---:|---:|---|
| Development | 95 | 398 | Measure field conditions, fit models, and choose rules |
| Validation | 25 | 102 | Remain unopened until the development model and evaluation rules are fixed |

Both partitions contain northern and southern fields, every equal-area Galactic-
latitude band, and every fixed 15-degree absolute-ecliptic-latitude band. The
minimum development-to-validation center separation is 6.429656 degrees.

Ecliptic latitude is only a sky-position indicator related to Gaia's scanning
pattern. It does not prove that two fields have similar Gaia coverage. Observation
counts, local depth, total source density, query completion, and usable area must
be measured later. Those measurements begin with development fields only.

### Known-environment flags

The grid records whether each field intersects catalog geometry represented in the
current project:

- 142 fields intersect at least one circle with radius `2 R2t` around a represented
  Kourkchi-Tully group;
- 283 intersect at least one represented association circle with radius `R1t`;
- 47 contain the center of at least one galaxy in the 2,155-host project catalog;
  and
- 304 have one or more of these flags, while 196 have none.

These are sensitivity labels, not automatic exclusions. Earlier audits showed that
neither `2 R2t` nor `R1t` is a universal physical boundary, and excluding all
flagged fields would strongly change the sky coverage before its effect is tested.
The development analysis must report results both with the full diagnostic grid
and with declared environment-flag sensitivity subsets before any exclusion rule
is frozen.

### Validation result and artifacts

All 16 checks pass. They verify coordinate uniqueness, exact spherical area,
hemisphere and latitude coverage, whole-block partitioning, non-overlap, preserved
environment flags, absence of Gaia-count and selector columns, and unchanged host
and environment input row counts.

- `data/results/background/large_sky_field_grid_v1.csv`
- `data/results/background/large_sky_field_grid_v1.json`

Reproduce the count-blind grid without querying Gaia:

```bash
uv run python scripts/phase3_background/freeze_large_sky_field_grid.py
```
<!-- preserved_source_end: docs/large_sky_field_grid.md -->

<a id="record-large_sky_development_pilot"></a>

> Dated source record: `docs/large_sky_development_pilot.md`. Superseded instructions are history, not current policy.

<!-- preserved_source_start: docs/large_sky_development_pilot.md -->
## Frozen large-sky development pilot

**Status:** Field identities frozen before Gaia retrieval
**Date:** 2026-07-19
**Issues:** BT-009, BT-022

### Selection rule

The performance benchmark is `sky_field_0000`, the development field with the
smallest absolute Galactic latitude. `field_id` breaks an exact tie. This uses sky
position only and is intended to exercise a relatively demanding part of the
declared `|b| >= 20` degree domain.

The small pilot contains the benchmark and one stable-hash-selected development
field from each of the other nine combinations of Galactic hemisphere and
equal-area Galactic-latitude band. Those ten fields did not cover two of the six
fixed ecliptic-latitude bands, so the lowest-hash development field in each missing
band was added. The measured pilot therefore contains 12 fields.

The pilot includes both fields with and without count-blind catalog-environment
flags. Those flags remain labels for later sensitivity comparisons, not reasons to
delete a field.

### Isolation and allowed use

All 12 identities were written before any 0.8-degree grid field was queried. Every
field belongs to the 398-field development partition. None of the 102 held-back
validation identifiers is present.

Development fields may be used to benchmark retrieval, measure pre-selector Gaia
conditions, apply the frozen selector, and choose the eventual large-sky model.
Validation fields remain unopened until the model and its evaluation rules are
fixed.

All ten checks pass. They verify unique development identities, the benchmark
rule, complete Galactic and ecliptic coverage, representation of both environment-
flag states, and absence of Gaia-count and selector-result columns.

### Artifacts and reproduction

- `data/results/background/large_sky_development_pilot_fields_v1.csv`
- `data/results/background/large_sky_development_pilot_fields_v1.json`

```bash
uv run python scripts/phase3_background/freeze_large_sky_development_pilot.py
```
<!-- preserved_source_end: docs/large_sky_development_pilot.md -->

<a id="record-large_sky_development_retrieval"></a>

> Dated source record: `docs/large_sky_development_retrieval.md`. Superseded instructions are history, not current policy.

<!-- preserved_source_start: docs/large_sky_development_retrieval.md -->
## Large-sky development retrieval benchmark and pilot

**Status:** Single-field benchmark and 12-field development pilot complete
**Date:** 2026-07-19
**Issues:** BT-009, BT-022

### What was measured

All fields use the frozen 0.8-degree circles, exact spherical areas, 19 raw Gaia
columns, G-magnitude range, 5,000-row strip limit, selector version, and probability
threshold. Gaia was queried only for the 12 frozen development fields. None of the
102 held-back validation fields was queried or scored.

Raw Gaia rows are stored as verified strip checkpoints outside the repository at
`~/Dropbox/work/data/bubbletea/gaia_large_sky_v1`. The repository retains measured
strip plans, compact field summaries, and provenance manifests.

A passing source is a search candidate selected by
`point_source_logistic_model_v1`; it is not a confirmed UCD.

### Single-field performance benchmark

`sky_field_0000` is the development field closest to the declared
`|b| = 20` degree boundary. It was chosen from position alone before its Gaia count
was known.

| Measurement | Result |
|---|---:|
| Gaia sources in the frozen magnitude range | 84,025 |
| Sources passing the frozen selector | 1,393 |
| Passing-source density per square degree | 692.832618 |
| Final retrieval strips | 26 |
| Largest strip | 4,982 rows |
| External checkpoint CSV bytes | 17,369,345 |
| Measured planning time | 87.086338 seconds |
| Measured retrieval time | 43.725160 seconds |
| Local selector time | 2.161201 seconds |
| Total measured time | 133.357677 seconds |

The run deliberately stopped after retrieving one strip. On resume, that strip was
verified and skipped, and the remaining 25 were downloaded. All 18 benchmark
safeguards pass. This confirms that the 5,000-row limit and persistent restart
mechanism work for a substantially denser 0.8-degree field.

### Twelve-field pilot result

| Field | Galactic latitude | Ecliptic latitude | Gaia sources | Passing candidates | Passing density per square degree |
|---|---:|---:|---:|---:|---:|
| `sky_field_0000` | 20.080258 | 4.592953 | 84,025 | 1,393 | 692.832618 |
| `sky_field_0067` | 31.310434 | -4.243134 | 11,911 | 960 | 477.472586 |
| `sky_field_0126` | 42.450885 | 48.038246 | 14,969 | 852 | 423.756920 |
| `sky_field_0151` | 47.795850 | -7.017217 | 7,002 | 481 | 239.233660 |
| `sky_field_0220` | 67.273333 | 29.317707 | 7,708 | 754 | 375.014927 |
| `sky_field_0275` | -24.150451 | -79.497819 | 24,779 | 812 | 403.862229 |
| `sky_field_0299` | -28.183708 | -46.372292 | 41,893 | 1,425 | 708.748370 |
| `sky_field_0302` | -28.698198 | -4.040004 | 40,952 | 1,081 | 537.654027 |
| `sky_field_0357` | -38.678626 | -7.318965 | 22,443 | 1,374 | 683.382639 |
| `sky_field_0429` | -54.532984 | -33.083639 | 5,779 | 696 | 346.167625 |
| `sky_field_0432` | -55.320275 | -60.348961 | 7,745 | 1,251 | 622.206464 |
| `sky_field_0483` | -73.052711 | -14.650003 | 6,198 | 504 | 250.673108 |

Together, the fields contain 275,404 Gaia sources and 11,583 passing candidates
over 24.127040 square degrees. The combined density is 480.083765 per square
degree, retained for count and area auditing only. Individual densities span
239.233660–708.748370, with a median of 450.614753.

The pilot used 83 final strips. Planning took 182.383724 seconds in total,
retrieval took 109.159825 seconds, and local scoring took 0.256445 seconds during
the batch run. The benchmark plan and all 26 benchmark checkpoints were reused
without another download. All nine aggregate safeguards pass.

### Interpretation and limits

The measured spread confirms that one latitude-only density value will not be
adequate. It does not yet show which combination of Galactic latitude, ecliptic
latitude, Gaia depth, observation counts, or environment flags best predicts the
passing-source density. The pilot was chosen for positional coverage rather than
statistical representativeness and is too small for the final model.

The four environment-flagged pilot fields are retained. Their combined result must
not be interpreted as an environment effect because the fields were not matched in
latitude or Gaia conditions. The full development analysis must measure those
conditions and use a declared comparison before deciding whether an environment
flag changes the model or sensitivity analysis.

### Artifacts and reproduction

- `data/results/background/large_sky_development_benchmark_plan_v1.csv`
- `data/results/background/large_sky_development_benchmark_summary_v1.csv`
- `data/results/background/large_sky_development_benchmark_v1.json`
- `data/results/background/large_sky_development_retrieval_plan_v1.csv`
- `data/results/background/large_sky_development_retrieval_summary_v1.csv`
- `data/results/background/large_sky_development_retrieval_v1.json`

```bash
BUBBLETEA_EXTERNAL_DATA="$HOME/Dropbox/work/data" \
  uv run python scripts/phase3_background/benchmark_large_sky_development_retrieval.py

BUBBLETEA_EXTERNAL_DATA="$HOME/Dropbox/work/data" \
  uv run python scripts/phase3_background/run_large_sky_development_retrieval.py
```
<!-- preserved_source_end: docs/large_sky_development_retrieval.md -->

<a id="record-large_sky_development_field_conditions"></a>

> Dated source record: `docs/large_sky_development_field_conditions.md`. Superseded instructions are history, not current policy.

<!-- preserved_source_start: docs/large_sky_development_field_conditions.md -->
## Large-sky development field conditions

**Date:** 2026-07-19

**Scope:** The 12 frozen development pilot fields only

**Script:** `scripts/phase3_background/measure_large_sky_development_field_conditions.py`

**Outputs:** `data/results/background/large_sky_development_field_conditions_v1.csv`
and its JSON provenance record

### Purpose

These measurements describe the Gaia catalog in each field before the UCD selector
is applied. They test whether variations in Gaia coverage, depth, or total catalog
density help predict how many sources pass the selector. They do not decide whether
a field is a valid scientific background.

### Measurements in plain language

- **Total Gaia source density:** all Gaia sources in the selector's allowed G-magnitude
  range, divided by the exact queried area. It can reflect Milky Way source density,
  crowding, and real astrophysical populations as well as survey behavior. It is not
  a pure observing-condition measurement and cannot become a rigid host-to-control
  matching cut.
- **Mean visibility periods:** the average number of groups of Gaia observations
  separated in time. It describes how often sources in the field were observed on
  distinct occasions.
- **Mean matched transits:** the average number of Gaia focal-plane crossings that
  were associated with a catalog source. It is a second description of observation
  frequency.
- **M10:** the median G magnitude of sources with no more than ten matched transits.
  A fainter value generally indicates that such sparsely observed sources reach
  fainter magnitudes. M10 is a local depth indicator, not a selector cut.

The archive service overflowed when it summed the two integer observation-count
columns directly. The final procedure therefore retrieves each field's compact
source identifier and observation counts, verifies that the retrieval is complete
and unique, and calculates both means locally. The total count is independently
measured and must also equal the count from the existing 19-column retrieval.

### Measured result

All 12 development fields pass all 12 safeguards. The complete run took
66.501269 seconds. The measured ranges are:

| Measurement | Minimum | Maximum |
| --- | ---: | ---: |
| Total Gaia sources per square degree | 2,874.285496 | 41,791.285489 |
| Mean visibility periods | 12.437076 | 24.246461 |
| Mean matched transits | 19.192643 | 56.199413 |
| M10, G magnitude | 20.894909 | 21.158578 |

The full-column and compact pre-selector retrievals have identical source counts
in every field. None of the 102 held-back validation fields was queried or scored.

Three additional field descriptions were calculated later from the verified raw
checkpoints: the 10th percentile, median, and 90th percentile of all G magnitudes
inside the frozen magnitude range. All nine checks pass, all source counts and
identifier fingerprints match the original retrieval, and no archive query was
needed. See `docs/large_sky_development_scale.md`.

### Interpretation limit

The fields were selected to cover sky position, not to estimate correlations
precisely. Their ranges show that the candidate predictors vary enough to test in
the 398-field development experiment. Associations seen among only these 12 fields
must not select a predictor, model, threshold, or scientific background.
<!-- preserved_source_end: docs/large_sky_development_field_conditions.md -->

<a id="record-large_sky_development_scale"></a>

> Dated source record: `docs/large_sky_development_scale.md`. Superseded instructions are history, not current policy.

<!-- preserved_source_start: docs/large_sky_development_scale.md -->
## Large-sky development continuation

**Date:** 2026-07-19

**Scripts:**
`scripts/phase3_background/derive_large_sky_development_g_magnitude_summaries.py`
and `scripts/phase3_background/run_large_sky_development_scale.py`

### What was added

The 12 pilot development fields include three fixed descriptions of their
Gaia G-magnitude distributions:

- the magnitude below which 10% of the field's sources lie;
- the median magnitude;
- the magnitude below which 90% of the field's sources lie.

These are calculated from already downloaded sources. The definitions were fixed
before the remaining development fields are measured. They describe each entire
field and are not cuts applied to individual sources.

The continuation script combines four operations for every new development field:

1. divide the circular Gaia request into measured, non-overlapping strips;
2. save and verify the 19 columns required by the frozen source selector;
3. apply that selector locally and count the passing sources;
4. measure the pre-selector field conditions and calculate all fixed magnitude
   summaries.

After a field finishes, its raw files, measured strip plan, hashes, checks, and
plain field summary are written outside the repository under the configured
external-data directory. A later run checks that record and the saved file hashes
before treating the field as complete. An interrupted field reuses valid strips and
continues from the unfinished work.

### Safety rules

- Only rows marked `development` in the frozen grid may be processed.
- The 102 held-back validation identifiers are never placed in the processing list.
- The default command permits zero new remote fields. Starting remote work requires
  an explicit nonnegative `--maximum-new-fields` value.
- Processing order is a reproducible hash of the run version and field identifier.
  It uses no Gaia count, selector result, or host excess.
- A field with incomplete or invalid files is not represented as a zero count.
- This step measures inputs only. It fits no sky-background model and approves no
  field as a scientific background.

### Measured validation

The local magnitude calculation read all 12 completed fields in 1.416442 seconds,
made zero archive queries, and passed all nine safeguards. Every field's source
count and source-identifier fingerprint match the original retrieval.

The continuation first completed a zero-query dry run, importing the 12 existing
fields and passing all 14 run safeguards. It then processed exactly one new field,
`sky_field_0167`, selected by the fixed count-blind order:

- 9,095 Gaia sources in two verified strips;
- 540 sources pass the frozen selector;
- total density 4,523.555389 sources per square degree;
- selected density 268.578330 sources per square degree;
- complete field processing in 13.655484 seconds;
- all ten field checks and all 14 run checks pass.

A subsequent zero-query restart retained 13 completed development fields, started
no new field, and finished its state check in 0.005078 seconds.

Continued bounded runs completed all 398 development fields. Together they contain
8,001,113 Gaia sources, of which 403,920 pass the frozen selector, over
800.213480 square degrees. The external raw checkpoints contain 2,356 final strips
and 1,640,878,040 CSV bytes. Total Gaia density spans 2,401.289216--618,195.694388
sources per square degree; passing-source density spans
99.970823--37,714.863283 per square degree. These are measured ranges, not
projections from the pilot.

One unusually dense field, `sky_field_0317`, contains 1,242,936 Gaia sources and
75,829 passing sources in 386 final strips. Its adaptive planning repeatedly met
the fixed time ceiling. The planner now saves every completed count measurement,
checks its query and geometry before reuse, and resumes from that point. A local
stop-and-restart test passed all eight safeguards without an archive query. The
live field then resumed across bounded attempts until it completed; earlier failed
attempts remain as permanent external records and are not converted to zero.

The workflow retains a 180-second ceiling for each archive request and a 300-second
ceiling for each complete field attempt. Failed fields are deferred by default so
they cannot consume the first slot of every later batch, and retrying them requires
the explicit `--retry-failed-fields` option. All 17 aggregate safeguards pass. A
final zero-work run verified all 398 external field records, made no new field
attempt, and finished in 0.025172 seconds. All 102 validation fields remain
unopened.

### Interpretation

This validates the complete development measurement, failure preservation, bounded
waiting, planning and retrieval restarts, and local aggregate verification. The six
frozen models were subsequently compared, then reassigned to a secondary diagnostic
role after review. The primary large-sky reference now uses the directly measured
density distribution of development fields in the same broad
absolute-Galactic-latitude band. See
`docs/large_sky_direct_background_comparison.md`. No individual field is thereby
approved as a scientific background, and all 102 large-sky validation fields remain
unopened.
<!-- preserved_source_end: docs/large_sky_development_scale.md -->


