# Off-target control experiments

**Consolidated:** 2026-10-12  
**Role:** Topic-organized development evidence, not a replacement for current scientific requirements.

[Science guide](../science_guide.md) · [Current status](../current_status.md) · [Documentation audit](documentation_audit.md)

## Current reading guidance

These small comparison fields tested field matching, source retrieval, and counting uncertainty. They were never approved as final scientific backgrounds. The complete 500-field experiment is recorded separately in background_measurements.md; a valid host-specific comparison remains separate work.

## Dated evidence

Each section below retains an original report's scientific content, measurements,
commands, and limitations. Status statements apply to that report's original date;
read the guidance above and current SPEC before following an old next step.

<a id="record-background_field_conditions_benchmark"></a>

> Dated source record: `docs/background_field_conditions_benchmark.md`. Superseded instructions are history, not current policy.

<!-- preserved_source_start: docs/background_field_conditions_benchmark.md -->
## Gaia field-condition benchmark

**Status:** Bounded diagnostic completed; matching rules not yet fixed  
**Date:** 2026-07-18  
**Host:** NGC 4698  
**Gaia release reference:** `2023A&A...674A...1G`, DOI
`10.1051/0004-6361/202243940`  
**Artifacts:**
`data/results/background/background_review_hosts_v1.csv`,
`data/results/background/background_review_hosts_v1.json`,
`data/results/background/background_field_conditions_benchmark_v1.csv` and
`data/results/background/background_field_conditions_benchmark_v1.json`

### Question

Does placing comparison patches at exactly the same Galactic latitude as a target
also make their Gaia coverage and total Gaia source density effectively identical?

This benchmark does not apply the UCD selector and does not count UCD candidates.
The reported source counts include every Gaia DR3 catalog entry inside the circle
with G magnitude between 11.262918 and 21.757988. No parallax, proper-motion,
binary-star, QSO, morphology, or UCD-classifier filter is applied. It measures only
field properties that can be chosen before seeing a possible galaxy excess.

### Test

The test uses a circular patch of radius 0.1 degree centered on NGC 4698 and two
same-size comparison patches placed east and west of it. All three patch centers
have the same Galactic latitude, 71.345091 degrees. The comparison-patch separation
and the group-radius multiplier are temporary test values, not approved scientific
rules.

The 0.1-degree radius was selected only to make the first live archive query small
and fast. It is not a proposed scientific search radius. The real galaxy
measurement will use multiple concentric circular rings, retain a radial profile,
and omit a calibrated central galaxy region from UCD inference.

The script measures:

- the number and sky density of all Gaia sources in the selector's allowed G
  magnitude range, before applying the selector;
- the average number of visibility periods and matched astrometric transits;
- ecliptic latitude; and
- `M10`, the median G magnitude of Gaia sources with no more than ten matched
  astrometric transits in the patch. Here `M10` is used only as a local Gaia-depth
  indicator: a brighter value usually means shallower coverage.

### Measured result

| Patch | Gaia sources | Sources per square degree | Mean visibility periods | Mean matched transits | M10 (G magnitude) |
|---|---:|---:|---:|---:|---:|
| NGC 4698 target | 121 | 3851.55 | 15.98 | 39.12 | 21.187 |
| West comparison | 100 | 3183.10 | 12.07 | 37.97 | 21.093 |
| East comparison | 122 | 3883.38 | 14.46 | 35.92 | 21.102 |

All six validation checks passed. The three patches had positive measured area,
complete retrieval of the low-transit sample, no missing values in either
observation-count column, and no UCD-selector output in the query contract. The
complete run took 11.19 seconds on 2026-07-18.

### Interpretation

Matching Galactic latitude alone did not make the three fields identical. The west
comparison contained 100 Gaia sources, versus 121 and 122 in the target and east
patches, and it had fewer visibility periods on average. The three `M10` values
were much closer, spanning 0.094 magnitude.

This is only one target and two comparison patches. It shows why Gaia coverage and
total source density should be measured rather than assumed, but it cannot tell us
which diagnostic is most useful or set an acceptable mismatch. Those decisions
require a larger count-blind development sample and later validation against the
frozen selector on spatially separate fields.

### Reproduction

```bash
uv run python scripts/phase3_background/build_background_review_hosts.py
uv run python scripts/phase3_background/benchmark_gaia_field_conditions.py
```
<!-- preserved_source_end: docs/background_field_conditions_benchmark.md -->

<a id="record-background_review_field_conditions"></a>

> Dated source record: `docs/background_review_field_conditions.md`. Superseded instructions are history, not current policy.

<!-- preserved_source_start: docs/background_review_field_conditions.md -->
## Five-host Gaia field-condition review

**Status:** Diagnostic measurements completed; no scientific background field approved
**Date:** 2026-07-18
**Gaia release reference:** `2023A&A...674A...1G`, DOI
`10.1051/0004-6361/202243940`

### Purpose

This review asks whether temporary same-Galactic-latitude comparison circles have
similar Gaia coverage and total source density across five different nearby-galaxy
settings. “Before selection” means that these measurements are made before applying
the UCD classifier. No UCD-candidate count is used to choose or approve a field.

The five target galaxies are NGC 4698, the nearby ESO 006-G001, the group main
galaxy NGC 1316, the group member M60, and the unresolved-environment case Arp 244.

### Temporary geometry

In this document, a **galaxy-centered test circle** is a 0.1-degree-radius circle
centered on the named galaxy. Earlier summaries called this the “target patch.” A
**comparison test circle** is an equal-size circle moved away from the galaxy while
remaining at the same Galactic latitude. Earlier summaries called these
“diagnostic patches.” They are measured to test the method; they are not yet
approved for subtracting contamination from the galaxy measurement.

The 0.1-degree radius was chosen only for a bounded archive-query test. It is not
the real galaxy measurement aperture. At the catalog distances used here, this
angle corresponds to a projected radius of 4.712394 kpc for ESO 006-G001 and
41.771283 kpc for NGC 4698. The real measurement must instead preserve a series of
concentric circular rings in physical and host-size-normalized radius. A calibrated
inner circular region will be omitted from UCD inference because galaxy
substructure, compact star-forming regions, and H II regions can dominate it.

For the four galaxies with accepted Kourkchi-Tully catalog associations, two
comparison test circles were placed east and west at exactly the galaxy's Galactic
latitude. Their temporary separation uses twice the catalog's estimated
collapsed-group radius, followed by a 1.2 center-separation multiplier. These are
test values, not approved halo boundaries.

For group cases, each comparison test circle was also checked against a circle
centered on the catalog's group main galaxy. All four group test circles clear that
temporary boundary, but this does not make them valid scientific backgrounds. Arp
244 has no accepted environment association, so only its galaxy-centered circle
was measured. We did not create off-galaxy comparison coordinates from an
unverified group center or group size. That is what the earlier phrase “no invented
comparison” meant; it did not mean that any observed data were fabricated.

### Quantities measured

- **Total Gaia source count and density:** every Gaia DR3 catalog entry inside the
  circle whose G magnitude lies between 11.262918 and 21.757988. No parallax,
  proper-motion, binary-star, QSO, morphology, or UCD-classifier filter is applied.
  These counts are therefore expected to be dominated by ordinary Milky Way stars.
- **Visibility periods:** separated groups of Gaia observations contributing to a
  source. The table reports the average within each patch.
- **Matched astrometric transits:** individual Gaia passages associated with a
  source's astrometric processing. The table reports the patch average.
- **`M10`:** the median G magnitude of Gaia entries with no more than ten matched
  astrometric transits and a reported G magnitude. Unlike the total-count column,
  this depth calculation is not restricted to the classifier's G-magnitude range.
  It is a local Gaia-depth indicator; a brighter value generally indicates
  shallower coverage.

### Measured result

| Host | Circle | Gaia entries in the stated G range | Entries per square degree | Mean visibility periods | Mean matched transits | M10 |
|---|---|---:|---:|---:|---:|---:|
| NGC 4698 | Target | 121 | 3851.55 | 15.98 | 39.12 | 21.187 |
| NGC 4698 | West test | 100 | 3183.10 | 12.07 | 37.97 | 21.093 |
| NGC 4698 | East test | 122 | 3883.38 | 14.46 | 35.92 | 21.102 |
| ESO 006-G001 | Target | 530 | 16870.43 | 23.55 | 33.55 | 21.018 |
| ESO 006-G001 | West test | 460 | 14642.26 | 21.17 | 28.54 | 20.913 |
| ESO 006-G001 | East test | 584 | 18589.30 | 24.85 | 35.07 | 21.001 |
| NGC 1316 | Target | 136 | 4329.02 | 23.05 | 37.38 | 21.213 |
| NGC 1316 | West diagnostic | 110 | 3501.41 | 26.65 | 56.51 | 21.129 |
| NGC 1316 | East diagnostic | 81 | 2578.31 | 24.69 | 40.88 | 21.631 |
| M60 | Target | 289 | 9199.16 | 9.96 | 35.94 | 21.384 |
| M60 | West diagnostic | 59 | 1878.03 | 12.64 | 21.32 | 20.886 |
| M60 | East diagnostic | 130 | 4138.03 | 15.58 | 33.87 | 21.049 |
| Arp 244 | Target only | 330 | 10504.23 | 11.82 | 21.14 | 21.134 |

The complete run took 46.93 seconds. All nine validation checks passed: all frozen
positions were measured, retrievals were complete, required observation values
were present, every patch had positive area, the queries contained no selector
output, and no test patch was marked as an approved scientific background.

### Interpretation

The two one-galaxy catalog cases have comparatively small `M10` ranges across their
three patches: 0.094 magnitude for NGC 4698 and 0.105 magnitude for ESO 006-G001.
The group cases have larger ranges: 0.503 magnitude for NGC 1316 and 0.498 magnitude
for M60. The average observation counts also vary substantially within some sets.
This confirms that exact Galactic-latitude matching does not guarantee similar Gaia
coverage.

Total Gaia density needs more careful treatment. M60's target patch contains 289
Gaia sources, while its test patches contain 59 and 130. The target patch may
contain real sources associated with M60 or the Virgo environment, not merely a
different level of Gaia crowding or completeness. Therefore total Gaia density is
a useful diagnostic but cannot be required to match the target rigidly: doing so
could reject genuine host-associated populations before the UCD selector is even
applied.

The next calibration should learn how field properties predict selected-source
density from comparison fields that are not centered on target galaxies. It should
then test that relationship on spatially separate comparison fields. Target
overdensities must not be used to choose the matching tolerances.

### Artifacts and reproduction

- `data/results/background/background_review_field_positions_v1.csv`
- `data/results/background/background_review_field_positions_v1.json`
- `data/results/background/background_review_field_conditions_v1.csv`
- `data/results/background/background_review_field_conditions_v1.json`

```bash
uv run python scripts/phase3_background/build_background_review_field_positions.py
uv run python scripts/phase3_background/measure_background_review_field_conditions.py
```
<!-- preserved_source_end: docs/background_review_field_conditions.md -->

<a id="record-off_target_field_split"></a>

> Dated source record: `docs/off_target_field_split.md`. Superseded instructions are history, not current policy.

<!-- preserved_source_start: docs/off_target_field_split.md -->
## Off-target development and validation fields

**Status:** Bounded diagnostic split frozen
**Date:** 2026-07-18
**Issues:** BT-005, BT-009

### Plain-language definitions

An **off-target field** here is one of the existing 0.1-degree test circles placed
away from a review galaxy. These circles were created to test background methods;
they are not the real galaxy measurement rings.

- **Development fields** may be used to choose or adjust the background method.
- **Validation fields** are held back until those choices are fixed. They then test
  whether the method works in different sky regions.
- **Excluded fields** are the five galaxy-centered test circles. They are not part
  of this off-target split.

“Held back” is a procedural rule: selector results from validation fields must not
be used to choose cuts, matching tolerances, or model settings.

### Frozen assignment

The split identifier is `split_04329736d47c538b7aa0`.

| Partition | Host system | Environment case | Galactic latitude | Fields |
|---|---|---|---:|---|
| Development | NGC 4698 | Isolated principal in the group catalog | +71.345091° | west, east |
| Development | NGC 1316 | Main galaxy of a cataloged group | −56.690166° | west, east |
| Validation | ESO 006-G001 | Isolated principal in the group catalog | −25.222591° | west, east |
| Validation | M60 | Member of a cataloged group | +74.317758° | west, east |

Both off-target circles generated from one host remain in the same partition. This
prevents closely related east/west measurements from appearing on opposite sides of
the method test. Each partition contains one isolated case, one grouped case, one
positive Galactic latitude, and one negative Galactic latitude.

The smallest measured center-to-center separation between a development circle and
a validation circle is 11.949376 degrees. The test-circle diameter is 0.2 degree,
so no development circle overlaps a validation circle.

### What was not used

The assignment script reads only the previously frozen field positions and their
host, environment, and sky coordinates. It does not read the field-condition table,
Gaia source counts, source densities, or frozen-selector results.

Pre-selector field-condition measurements already exist for these positions and
have been discussed previously. They were not inputs to this assignment. No
selected-source count has been calculated or inspected for this split.

### Important limitation

These eight circles form a small first experiment, not a final survey-wide
validation sample. All still have
`eligible_for_scientific_background = false`. The split allows the canonical
selector experiment to test procedure and leakage control; it does not approve any
circle as the background for a real galaxy or calibrate a final Galactic-latitude
limit.

### Artifacts and reproduction

- `data/results/background/off_target_field_split_v1.csv`
- `data/results/background/off_target_field_split_v1.json`

```bash
uv run python scripts/phase3_background/freeze_off_target_field_split.py
```
<!-- preserved_source_end: docs/off_target_field_split.md -->

<a id="record-off_target_development_selector"></a>

> Dated source record: `docs/off_target_development_selector.md`. Superseded instructions are history, not current policy.

<!-- preserved_source_start: docs/off_target_development_selector.md -->
## Frozen-selector results for off-target development fields

**Status:** Development fields measured; validation selector results remain unopened
**Date:** 2026-07-18
**Issues:** BT-005, BT-009

### What was done

The four frozen development circles were queried for all 19 Gaia columns required
by `point_source_logistic_model_v1`. The selector was then applied locally, using
its frozen probability threshold of `0.8277833628791744`.

A source that **passes the frozen selector** has a model probability at or above
that threshold. It is a search candidate, not a confirmed UCD. These small circles
measure the selector's off-target behavior and cannot establish an astrophysical
background by themselves.

### Measured development results

Each circle has a 0.1-degree radius and an exact spherical area of 0.031416 square
degree. Gaia usable area equals queried area, with no imaging masks.

| Field | Host system | Gaia sources | Sources passing selector | Passing-source density per square degree |
|---|---|---:|---:|---:|
| `1:east` | NGC 1316 | 81 | 18 | 572.957941 |
| `1:west` | NGC 1316 | 110 | 8 | 254.647974 |
| `58:east` | NGC 4698 | 122 | 12 | 381.971960 |
| `58:west` | NGC 4698 | 100 | 6 | 190.985980 |

The four fields contain 413 Gaia sources in total; 44 pass the selector over a
combined usable area of 0.125664 square degree. The observed field-to-field
difference must be tested explicitly; four fields from only two host systems do not
by themselves show that one common density is invalid. No matching tolerance or
final background model is selected by this measurement alone.

### Validation isolation

The held-back identifiers are `2115:east`, `2115:west`, `4:east`, and `4:west`.
The script checks these identifiers before every query and again in both output
tables. None was queried or summarized.

Pre-selector observing-condition measurements already exist for those sky
positions. “Unopened” here specifically means that no frozen-selector probability,
decision, or selected-source count has been produced for the held-back fields.

### Validation result

All 18 checks pass in 10.560200 seconds. They verify:

- exactly the four frozen development fields were queried;
- the four held-back identifiers and their frozen host-role assignments are intact;
- no held-back field appears in a query or output;
- measured and retrieved row counts agree;
- all 19 raw Gaia columns and selector outputs are present;
- source identifiers are unique and have recorded fingerprints;
- probabilities are finite and use the frozen selector version;
- summary counts match the saved source decisions; and
- Gaia queried and usable areas agree, with zero missing or masked area.

### Artifacts and reproduction

- `data/results/background/off_target_development_selector_sources_v1.csv`
- `data/results/background/off_target_development_selector_summary_v1.csv`
- `data/results/background/off_target_development_selector_v1.json`

Reproduction deliberately re-queries only development fields:

```bash
uv run python scripts/phase3_background/run_off_target_development_selector.py
```
<!-- preserved_source_end: docs/off_target_development_selector.md -->

<a id="record-off_target_development_summary"></a>

> Dated source record: `docs/off_target_development_summary.md`. Superseded instructions are history, not current policy.

<!-- preserved_source_start: docs/off_target_development_summary.md -->
## Frozen development summary rules

**Status:** Summary procedure frozen before validation
**Date:** 2026-07-18
**Issues:** BT-005, BT-009

### What is frozen

The development results will be summarized at three levels:

1. Keep each of the four fields as a separate measurement.
2. Combine east and west fields only when they come from the same host system.
3. Show one all-development total for description only, not as a universal
   background density.

The frozen selector threshold remains `0.8277833628791744`. It will not be changed
after seeing these counts. No development field is promoted to an approved
scientific background.

### Small-count ranges in plain language

When only a few sources are counted, repeating an equivalent measurement can
produce a different count by chance. A Poisson model is the standard simple model
for that random counting variation when events are independent and have one average
rate over a fixed area.

For every field and combined row, the table records 68% and 95% exact central
Poisson ranges. These give ranges of average counts compatible with the observed
small count under that simple model. The corresponding density ranges divide the
count ranges by the exact usable area.

The percentage describes repeated use of the procedure: under the Poisson model,
ranges constructed this way include the true average rate at least that percentage
of the time over many equivalent experiments. It is not the probability that one
particular displayed range contains the true value.

These ranges do **not** include real differences among sky fields, correlated
sources, changes in Gaia observing conditions, or uncertainty in the selector.
They are therefore counting-only ranges, not the final background uncertainty.

### Host-pair and overall summaries

| Summary | Passing sources | Usable area (square degrees) | Density per square degree | 68% counting-only range | 95% counting-only range |
|---|---:|---:|---:|---:|---:|
| NGC 1316 east + west | 26 | 0.062832 | 413.802957 | 333.564113–511.396270 | 270.309830–606.317208 |
| NGC 4698 east + west | 18 | 0.062832 | 286.478970 | 219.901362–370.724732 | 169.785594–452.760282 |
| All development fields, descriptive only | 44 | 0.125664 | 350.140964 | 297.819151–410.960003 | 254.412960–470.047901 |

The all-development value is not a claim that every sky field has the same
background. It is retained so count and area totals can be audited.

### Validation boundary

The four held-back validation identifiers do not appear in the input or output.
When validation is opened, the same seven-row structure, confidence levels,
selector threshold, and host-pair rule must be used. Validation results cannot be
used to rewrite this development summary procedure.

All 16 checks pass. They verify field preservation, east/west pairing, count and
area conservation, interval ordering, zero-count support, unchanged selector
threshold, and continued absence of validation fields.

### Artifacts and reproduction

- `data/results/background/off_target_development_frozen_summary_v1.csv`
- `data/results/background/off_target_development_frozen_summary_v1.json`

```bash
uv run python scripts/phase3_background/freeze_off_target_development_summary.py
```
<!-- preserved_source_end: docs/off_target_development_summary.md -->

<a id="record-off_target_validation_selector"></a>

> Dated source record: `docs/off_target_validation_selector.md`. Superseded instructions are history, not current policy.

<!-- preserved_source_start: docs/off_target_validation_selector.md -->
## Held-back off-target validation result

**Status:** One-time held-back check complete; no field approved as a scientific background
**Date:** 2026-07-19
**Issues:** BT-005, BT-009

### What was tested

The four off-target circles kept out of development were opened after the selector
and summary rules were fixed. The run used the same 19 Gaia columns, G-magnitude
range, selector version, probability threshold, 0.1-degree circle, usable-area
definition, east/west host pairing, and counting-only ranges used for development.
No setting was changed after the validation counts became visible.

Here, **validation** means a one-time check on circles whose selector
probabilities, decisions, and passing-source counts were not used to choose the
procedure. Earlier measurements of total Gaia source density and observing
conditions at these positions were allowed and remain separate.

A source that passes the selector is a retained search candidate, not a confirmed
UCD. These circles are diagnostic measurements and are not approved backgrounds
for a host-galaxy measurement.

### Field results

Each circle has an exact spherical area of 0.031416 square degree. For this Gaia
measurement, usable area equals successfully queried area; no bright-star, dust,
or ancillary-imaging masks are applied.

| Field | Related host | Gaia sources | Sources passing selector | Passing-source density per square degree |
|---|---|---:|---:|---:|
| `2115:east` | ESO 006-G001 | 584 | 16 | 509.295947 |
| `2115:west` | ESO 006-G001 | 460 | 19 | 604.788937 |
| `4:east` | M60 | 130 | 14 | 445.633954 |
| `4:west` | M60 | 59 | 3 | 95.492990 |

The four fields contain 1,233 Gaia sources. Fifty-two pass the selector over
0.125664 square degree, giving a descriptive combined density of 413.802957 per
square degree.

### Frozen summaries

East and west are combined only within the same related host. The ranges below
describe random variation in small independent counts under a Poisson model. They
do not include real differences among sky fields, correlated sources, Gaia
observing-condition differences, or selector uncertainty.

| Summary | Passing sources | Density per square degree | 68% counting-only range | 95% counting-only range |
|---|---:|---:|---:|---:|
| ESO 006-G001 east + west | 35 | 557.042442 | 463.798777–667.425658 | 388.000471–774.711191 |
| M60 east + west | 17 | 270.563472 | 205.896317–352.952862 | 157.613193–433.198328 |
| All validation fields, descriptive only | 52 | 413.802957 | 356.892019–479.163152 | 309.047841–542.647524 |

### Comparison with development

The combined validation density is 1.181818 times the combined development
density of 350.140964 per square degree. It falls outside the development 68%
counting-only range but inside the development 95% range. This is a description,
not a rule that the result must pass.

Individual development fields span 190.985980–572.957941 per square degree, while
validation fields span 95.492990–604.788937. Development host pairs span
286.478970–413.802957, while validation host pairs span 270.563472–557.042442.
Both pairs of ranges overlap.

The result supports the limited claim that the fixed procedure can be executed on
untouched fields without an obvious incompatible total density. It also shows
large field-to-field variation. Four validation circles from two host systems are
therefore too few and too small to define a survey-wide background model, matching
tolerance, or Galactic-latitude limit.

### Safeguards and artifacts

All 24 safeguards pass. They verify the frozen field identities, exclusion of all
development fields from validation queries and outputs, complete retrieval,
unchanged selector and area rules, count and area conservation, the fixed
seven-row summary structure, unchanged development files, and the explicitly
descriptive status of every comparison.

- `data/results/background/off_target_validation_selector_sources_v1.csv`
- `data/results/background/off_target_validation_selector_summary_v1.csv`
- `data/results/background/off_target_validation_frozen_summary_v1.csv`
- `data/results/background/off_target_validation_selector_v1.json`

The recorded run took 12.439364 seconds:

```bash
uv run python scripts/phase3_background/run_off_target_validation_selector.py
```
<!-- preserved_source_end: docs/off_target_validation_selector.md -->


