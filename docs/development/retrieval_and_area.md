# Gaia retrieval, radial areas, and run records

**Consolidated:** 2026-10-12  
**Role:** Topic-organized development evidence, not a replacement for current scientific requirements.

[Science guide](../science_guide.md) · [Current status](../current_status.md) · [Documentation audit](documentation_audit.md)

## Current reading guidance

Strip-based retrieval, restart checks, exact spherical areas, and per-host run records are implemented. Small angular circles and controlled interrupted runs below are infrastructure tests, not scientific host profiles. The current Gaia policy applies no bright-star or ancillary-imaging area masks; successfully retrieved strips determine available area.

## Dated evidence

Each section below retains an original report's scientific content, measurements,
commands, and limitations. Status statements apply to that report's original date;
read the guidance above and current SPEC before following an old next step.

<a id="record-gaia_query_partition_validation"></a>

> Dated source record: `docs/gaia_query_partition_validation.md`. Superseded instructions are history, not current policy.

<!-- preserved_source_start: docs/gaia_query_partition_validation.md -->
## Gaia large-region query partition validation

**Status:** Bounded equivalence test passed; adaptive large-region retrieval pending
**Date:** 2026-07-18
**Gaia release reference:** `2023A&A...674A...1G`, DOI
`10.1051/0004-6361/202243940`

### Why the query is divided

Some nearby galaxies require sky coverage much larger than the inherited
two-degree limit. One very large archive request can exceed a service row limit or
fail partway through. The retrieval will therefore divide the requested galaxy-
centered circle into smaller horizontal sky strips and query them separately.

A horizontal sky strip is simply a range of declination, the north-south sky
coordinate. Every strip query still includes the exact original circular boundary.
The strips do not replace the circle with rectangles.

The lower edge of every strip is included. The upper edge is excluded except for
the final strip, which includes the circle's last edge. This rule assigns a source
lying exactly on a shared boundary to one and only one strip. Combining all strips
therefore reconstructs the complete circle without gaps or repeated boundary rows.

### Bounded live test

The validation queried a 0.2-degree-radius circle centered on NGC 4698 in two ways:

1. one complete-circle query used as the reference; and
2. four separate strips, each no taller than 0.1 degree.

Both methods used every Gaia DR3 catalog entry in the selector's allowed G-magnitude
range. The UCD selector and contaminant filters were not applied.

The complete circle returned 500 Gaia entries. The four strips returned 82, 154,
149, and 115 entries, also totaling 500. The combined strip result contains 500
unique Gaia source identifiers and matches the reference identifier set exactly:
zero entries are missing and zero are repeated. The run took 12.96 seconds.

All nine checks passed, including exact source-identifier equality, exact-circle
membership, one-time assignment of every synthetic strip-boundary point, correct
clipping of a synthetic circle at the north celestial pole, and absence of UCD
selector output.

### Real retrieval contract

The 0.1-degree strip height is a test value, not a production setting. For a real
host, the workflow will first count rows without downloading them. Any strip whose
measured count exceeds the declared safe retrieval size will be divided again. The
count, query status, retrieved row count, and source-identifier uniqueness must be
validated separately for every final strip.

After the strips are combined, the pipeline will calculate each source's exact
spherical separation from the galaxy once. It will then assign the source to the
exploratory radial rings locally. It will not query overlapping rings separately.

The production workflow must also checkpoint completed strips so a failed archive
request can resume without repeating successful downloads. A follow-up bounded test
now validates measured splitting, a controlled stop and restart, and recovery of a
deliberately damaged checkpoint; see
`docs/gaia_adaptive_retrieval_validation.md`. Neither test yet establishes a safe
production row limit for the full selector-input column set or service reliability
for a multi-degree nearby-galaxy retrieval.

### Artifacts and reproduction

- `data/results/background/gaia_query_partition_sources_v1.csv`
- `data/results/background/gaia_query_partition_strips_v1.csv`
- `data/results/background/gaia_query_partition_validation_v1.json`

```bash
uv run python scripts/phase3_background/validate_gaia_query_partition.py
```
<!-- preserved_source_end: docs/gaia_query_partition_validation.md -->

<a id="record-gaia_adaptive_retrieval_validation"></a>

> Dated source record: `docs/gaia_adaptive_retrieval_validation.md`. Superseded instructions are history, not current policy.

<!-- preserved_source_start: docs/gaia_adaptive_retrieval_validation.md -->
## Adaptive and restartable Gaia retrieval validation

**Status:** Bounded split, stop, resume, and corruption-recovery test passed
**Date:** 2026-07-18
**Gaia release reference:** `2023A&A...674A...1G`, DOI
`10.1051/0004-6361/202243940`

### Plain-language workflow

Before downloading a large galaxy-centered region, the workflow asks the Gaia
archive only for the number of entries in that region. If the measured number is
larger than the declared safe size for one download, the north-south coordinate
range is divided in half and both halves are counted. This repeats until every
final sky strip is small enough.

A **checkpoint** is the saved source file for one completed strip plus a small
metadata file recording its expected row count, archive-query hash, retrieved row
count, and source-file hash. Both files are written through temporary files so an
interrupted write cannot masquerade as a completed download.

When a run restarts, every existing checkpoint is verified. A checkpoint is reused
only when its query, expected count, file hash, row count, and source identifiers
remain valid. Missing, incomplete, changed, or corrupted files are downloaded
again. Successfully verified files are not queried again.

### Bounded live validation

The validation uses the same 0.2-degree-radius NGC 4698 circle and 500-entry
reference as the earlier partition test. A test-only limit of 130 entries per strip
forces the workflow to measure and divide the circle adaptively. It creates six
final strips containing 82, 71, 83, 70, 79, and 115 entries.

The first retrieval is deliberately stopped after saving two strips. A new
retrieval instance then loads the saved plan, verifies and skips those two strips,
and downloads only the remaining four. The two original files retain exactly the
same hashes.

After that successful restart, the validation deliberately changes the final saved
strip. A third retrieval detects the hash mismatch, downloads only that damaged
strip again, and skips the five intact files. The final combined table contains 500
unique Gaia source identifiers and matches the independent reference exactly.

All 15 checks pass in 21.68 seconds. The validation queries only `source_id`, sky
position, and G magnitude; it does not apply the UCD selector.

### Production contract and remaining work

The 130-entry limit is intentionally small so the bounded test exercises splitting.
It is not a production archive limit. The production safe size must be measured
using the full set of Gaia columns required by the frozen selector. The reusable
retriever accepts that full column list; its query hash invalidates checkpoints if
the requested columns or any query condition changes.

A production run must preserve:

- the complete measured split plan before source retrieval begins;
- one atomic source and metadata checkpoint per final strip;
- explicit complete, incomplete, failed, and recovered states;
- exact source-identifier uniqueness after combination; and
- the immutable run configuration, Gaia release, selector input columns, query
  hashes, and output hashes.

A follow-up full-column benchmark directly measured 5,000 rows three times and
10,000 rows once. The 5,000-row results had identical source identifiers, query
times of 1.948628--1.976649 seconds, and serialized sizes of 1,027,468 bytes. The
provisional development checkpoint limit was therefore 5,000 rows. A subsequent
three-field test validates full-column restart behavior for one unsplit and two
split cases and freezes the 5,000-row per-strip limit for development and pilot
runs. The subsequent spherical area component maps verified completed strips to
each ring's successfully queried and missing area, then subtracts the union of
explicit masks. See `docs/radial_ring_area_accounting.md`.

### Artifacts and reproduction

- `data/results/background/gaia_adaptive_retrieval_plan_v1.csv`
- `data/results/background/gaia_adaptive_retrieval_sources_v1.csv`
- `data/results/background/gaia_adaptive_retrieval_validation_v1.json`

```bash
uv run python scripts/phase3_background/validate_adaptive_gaia_retrieval.py
```
<!-- preserved_source_end: docs/gaia_adaptive_retrieval_validation.md -->

<a id="record-gaia_full_selector_retrieval_benchmark"></a>

> Dated source record: `docs/gaia_full_selector_retrieval_benchmark.md`. Superseded instructions are history, not current policy.

<!-- preserved_source_start: docs/gaia_full_selector_retrieval_benchmark.md -->
## Full-selector-column Gaia retrieval benchmark

**Status:** Bounded benchmark passed; 5,000-row limit confirmed by multifield restart validation
**Date:** 2026-07-18
**Selector:** `point_source_logistic_model_v1`
**Gaia release reference:** `2023A&A...674A...1G`, DOI
`10.1051/0004-6361/202243940`

### Purpose

The restart test initially downloaded only four columns. A real search must download
all 19 Gaia columns required to calculate the frozen classifier's nine features.
This benchmark measures the archive time, local memory, serialized file size, and
classifier time for progressively larger full-column results.

The test uses a predeclared review host, ESO 006-G001, and a 0.5-degree-radius
performance-test circle. The circle contains 13,010 Gaia entries in the frozen
G-magnitude range. This field and radius measure retrieval behavior only; they do
not define the galaxy's scientific aperture or background.

### Measurements

| Requested rows | Repeat | Query seconds | Table memory (bytes) | CSV bytes | Classifier seconds | Python-traced peak bytes |
|---:|---:|---:|---:|---:|---:|---:|
| 100 | 0 | 1.534212 | 10,132 | 21,049 | 0.047920 | 5,289,258 |
| 500 | 0 | 1.688021 | 50,132 | 104,549 | 0.013902 | 1,229,038 |
| 1,000 | 0 | 1.585557 | 100,132 | 206,631 | 0.013612 | 2,783,334 |
| 2,500 | 0 | 2.118256 | 250,132 | 514,448 | 0.014471 | 5,815,883 |
| 5,000 | 0 | 1.967479 | 500,132 | 1,027,468 | 0.013912 | 11,409,998 |
| 10,000 | 0 | 2.627872 | 1,000,132 | 2,051,704 | 0.014861 | 13,217,268 |
| 5,000 | 1 | 1.976649 | 500,132 | 1,027,468 | 0.015364 | 11,407,446 |
| 5,000 | 2 | 1.948628 | 500,132 | 1,027,468 | 0.013794 | 11,407,752 |

“Table memory” is the measured pandas table size. “CSV bytes” is the measured size
after serializing that table. “Python-traced peak” covers Python-tracked allocations
during each query, serialization, and classification; it does not include every
possible native-library allocation. The process-wide peak resident memory reached
282,624,000 bytes by the end of the repeated sequence, but that value is cumulative
over the process and is not attributable to one query.

All requested rows and all 19 columns were returned. Source identifiers were unique
within every query, classifier probabilities were finite, and all three 5,000-row
runs returned the same identifier hash. All ten validation checks pass. The eight
queries took 17.719464 seconds in total.

The classifier was run only to verify that each retrieved table is usable. The
number passing the classifier is not used to choose the checkpoint size or any
scientific selection rule.

### Provisional limit

Use 5,000 rows as the provisional maximum for one development checkpoint. It was
measured successfully three times with identical identifiers and is half the
largest successful full-column test of 10,000 rows. This is a conservative project
setting, not a measured Gaia archive failure boundary.

A follow-up test now validates the limit in three fields with different measured
row counts and through complete full-column stop-and-resume behavior. The accepted
cases contain 2,991, 6,497, and 13,010 rows, produce one, two, and four strips, and
match independent identifier references exactly. The project therefore freezes
5,000 rows as the per-strip limit for development and pilot runs under the current
19-column contract. File sizes must still be recorded per checkpoint because null
patterns and numeric representations can change serialized size. See
`docs/gaia_full_column_multifield_validation.md`.

### Artifacts and reproduction

- `data/results/background/gaia_full_selector_retrieval_benchmark_v1.csv`
- `data/results/background/gaia_full_selector_retrieval_benchmark_v1.json`

```bash
uv run python scripts/phase3_background/benchmark_full_selector_retrieval.py
```
<!-- preserved_source_end: docs/gaia_full_selector_retrieval_benchmark.md -->

<a id="record-gaia_full_column_multifield_validation"></a>

> Dated source record: `docs/gaia_full_column_multifield_validation.md`. Superseded instructions are history, not current policy.

<!-- preserved_source_start: docs/gaia_full_column_multifield_validation.md -->
## Multi-field full-column Gaia retrieval validation

**Status:** 5,000-row per-strip retrieval limit validated for development and pilot use
**Date:** 2026-07-18
**Selector:** `point_source_logistic_model_v1`
**Gaia release reference:** `2023A&A...674A...1G`, DOI
`10.1051/0004-6361/202243940`

### Purpose

This test checks whether the adaptive stop-and-restart workflow works with all 19
Gaia columns required by the frozen classifier in fields with different measured
source densities. It uses the previously measured 5,000-row limit for each saved
sky strip.

The circles are performance-test regions, not scientific galaxy apertures. NGC
4698 and ESO 006-G001 use 0.5-degree radii. M60 uses 0.75 degree so the intermediate-
density case contains enough rows to exercise splitting.

### Preserved failed test

The first run used 0.5 degree for all three fields. It measured 2,991 rows for NGC
4698, 3,098 for M60, and 13,010 for ESO 006-G001. Only ESO 006-G001 required
splitting, so the predeclared requirement that at least two fields exercise restart
behavior failed. All identity and column checks passed, but that run was not
accepted.

The requirement was not weakened. The M60 performance-test radius was expanded to
0.75 degree, while NGC 4698 was retained as the below-limit case and ESO 006-G001
as the higher-density case. This geometry change affects only retrieval validation
and cannot define a scientific search radius.

### Accepted measurements

| Field | Test radius (degrees) | Gaia rows | Final strips | Largest strip | Saved CSV bytes | Largest saved strip (bytes) | Elapsed seconds |
|---|---:|---:|---:|---:|---:|---:|---:|
| NGC 4698 | 0.50 | 2,991 | 1 | 2,991 | 581,964 | 581,964 | 5.556552 |
| M60 | 0.75 | 6,497 | 2 | 3,326 | 1,255,861 | 639,072 | 8.158222 |
| ESO 006-G001 | 0.50 | 13,010 | 4 | 4,123 | 2,723,286 | 859,723 | 15.873899 |

The fields contain 22,498 Gaia rows in total and produce seven final strips. Every
strip remains below 5,000 rows. The two split fields deliberately stop after their
first saved strip; fresh retrieval instances verify and skip that strip, download
only unfinished strips, and complete successfully. NGC 4698 completes as one strip
without unnecessary splitting.

For every field, the combined full-column rows are unique and their source-
identifier hash exactly matches an independent complete-circle identifier query.
All required classifier columns are present and all classifier probabilities are
finite. The selected-source counts are validation outputs only and are not used for
an astrophysical decision. All 13 checks pass in 29.589341 seconds.

### Decision

Freeze 5,000 rows as the maximum for one saved Gaia retrieval strip in development
and pilot runs using the current 19-column contract. This value is supported by:

- three repeated 5,000-row full-column benchmarks with identical identifiers;
- a successful 10,000-row full-column stress test;
- one unsplit and two split multifield cases;
- controlled full-column stop-and-restart behavior; and
- exact independent source-identifier agreement in all three fields.

This limit controls one archive response, not the total size of a galaxy run.
Multi-degree hosts may require many strips. Every strip must still record its actual
row count, file bytes, query hash, file hash, and completion state. Changing the
Gaia column contract, archive, or data release requires a new benchmark.

### Artifacts and reproduction

- `data/results/background/gaia_full_column_multifield_retrieval_v1.csv`
- `data/results/background/gaia_full_column_multifield_plan_v1.csv`
- `data/results/background/gaia_full_column_multifield_validation_v1.json`

```bash
uv run python scripts/phase3_background/validate_full_column_multifield_retrieval.py
```
<!-- preserved_source_end: docs/gaia_full_column_multifield_validation.md -->

<a id="record-radial_ring_area_accounting"></a>

> Dated source record: `docs/radial_ring_area_accounting.md`. Superseded instructions are history, not current policy.

<!-- preserved_source_start: docs/radial_ring_area_accounting.md -->
## Radial-ring area accounting

**Status:** Spherical area component validated; Gaia no-mask policy fixed
**Date:** 2026-07-18
**Issues:** BT-005, BT-010, BT-021

### Plain-language definitions

Each radial ring now carries five separate areas:

- **Requested area:** the entire ring that the measurement asked for.
- **Successfully queried area:** the part covered by retrieval strips whose saved
  files passed all completion and integrity checks.
- **Missing area:** the requested part without a verified completed strip.
- **Masked area:** the union of explicitly unusable regions inside the successfully
  queried area. Overlapping masks are counted once, not once per mask.
- **Usable area:** successfully queried area minus masked area. This is the
  denominator for a source density.

An interrupted query therefore produces a positive missing area rather than a
false zero source density. A complete query can still have less usable area than
requested area if an authoritative mask removes part of the sky.

The central galaxy exclusion is a different concept. It marks inner rings as
diagnostic-only for the scientific analysis; it does not pretend that those rings
were missing from the archive or geometrically unusable.

For the Gaia measurement, masked area is always zero. Bright-star, dust, and
ancillary-imaging masks are not applied. Therefore Gaia usable area equals
successfully queried area. Crowding, observation counts, or dust may still be
recorded as diagnostics, but they do not remove Gaia sky area.

### Spherical calculation

The requested area is the analytic area between two circles on a sphere. Retrieval
strips and circular masks are intersected with each ring on the sphere, including
right-ascension wraparound and polar geometry. The intersections are integrated to
an internal absolute tolerance of `1e-13` steradian and validated to `1e-8` square
degree. Here, "exact area" means spherical rather than a flat-sky approximation,
with the numerical integration error recorded in every row.

Each mask must have an identifier, center, angular radius, reason, and provenance.
The area code forms the union of all masks before subtraction, so overlapping masks
cannot remove the same sky twice.

### Bounded validation

The measured retrieval plans for NGC 4698, M60, and ESO 006-G001 were divided into
four test rings each. A controlled M60 case retains only one of its two completed
strips. These are fractions of the archive performance-test circles, not physical-
kiloparsec rings or approved scientific apertures.

For all three completed retrievals, the successfully queried area reproduces the
requested spherical area. The largest ring-level difference is
`1.873002e-12` square degree, and the four rings for each host sum to the analytic
circle area within `1.110223e-16` square degree.

Under the Gaia policy, the complete M60 fixture has `1.767121` square degrees both
successfully queried and usable. The controlled one-of-two-strip state has
`0.884062` square degree both successfully queried and usable, while `0.883059`
square degree remains explicitly missing.

Two overlapping circular masks were then placed in the M60 fixture. They are
explicitly labeled `synthetic_fixture_not_survey_coverage`; they are not real Gaia,
bright-star, dust, or imaging masks. The complete fixture contains
`1.767121` square degrees of requested and successfully queried area. The union of
the two masks removes `0.039362` square degree, leaving `1.727758` square degrees
usable. A controlled partial state with only one of two retrieval strips complete
records `0.884062` square degree queried and `0.883059` square degree missing.

All 18 predeclared checks pass in `0.216274` seconds. They cover completed and
partial retrievals, area identities, overlapping-mask union, non-negative areas,
polar geometry, central-ring disposition, retrieval-plan counts, the Gaia no-mask
policy, and the synthetic-mask provenance warning. The output contains 24 ring
records.

### Boundary between Gaia and ancillary imaging

Real Gaia host densities must not use the synthetic fixture masks. The generic mask
intersection remains available only as tested geometry for a future data product
that explicitly requires masks. Any later ancillary-imaging measurement has its own
coverage and quality policy; it does not change the Gaia denominator.

### Artifacts and reproduction

- `data/results/background/radial_ring_area_accounting_validation_v1.csv`
- `data/results/background/radial_ring_area_accounting_validation_v1.json`

```bash
uv run python scripts/phase3_background/validate_radial_ring_area_accounting.py
```
<!-- preserved_source_end: docs/radial_ring_area_accounting.md -->

<a id="record-host_run_records"></a>

> Dated source record: `docs/host_run_records.md`. Superseded instructions are history, not current policy.

<!-- preserved_source_start: docs/host_run_records.md -->
## Per-galaxy analysis receipts

**Status:** Receipt format and non-overwrite behavior validated
**Date:** 2026-07-18
**Issue:** BT-010

### What one receipt is

A receipt is one JSON file describing what happened when one galaxy was processed
under one declared analysis configuration. It records:

- the galaxy name and sky position;
- whether its work completed, stopped partway, or failed;
- which retrieval strips have verified saved files;
- the expected and retrieved Gaia row counts;
- the Gaia source-identifier checksums;
- the radial-ring requested, queried, missing, and usable areas;
- any failure in ordinary English; and
- the configuration checksum and time inherited from the source retrieval.

A checksum is a short digital fingerprint of content. If the content changes, its
checksum changes. The receipt index stores each receipt file's checksum so later
validation can detect an accidental edit.

### Why receipts are never overwritten

The run identifier is calculated from the declared configuration and exact input
file checksums. The per-galaxy identifier combines that run identifier with the
galaxy identity. Therefore rerunning identical inputs finds the same receipt, while
changed inputs or settings produce a different run identifier and a new receipt
path.

Writing is atomic: other code sees either no receipt or the complete receipt, never
a half-written file. If the destination already contains identical content, it is
reused. If it contains different content, the write fails rather than replacing the
earlier result. The validation also exercises concurrent-safe file creation.

### Bounded results

The three completed performance fields share run identifier
`run_be3271012ea314b4a512`.

| Galaxy | Status | Completed strips | Gaia rows | Requested area (square degrees) | Missing area (square degrees) | Usable area (square degrees) |
|---|---|---:|---:|---:|---:|---:|
| NGC 4698 | complete | 1 of 1 | 2,991 | 0.785393 | 0.000000 | 0.785393 |
| M60 | complete | 2 of 2 | 6,497 | 1.767121 | 0.000000 | 1.767121 |
| ESO 006-G001 | complete | 4 of 4 | 13,010 | 0.785393 | 0.000000 | 0.785393 |

The tiny stored missing values in completed rows are below the declared numerical
area tolerance and display as zero in this summary.

A separate controlled M60 receipt uses run identifier
`run_0462fc307c338f11120f`. It represents one of two strips complete, records
`0.884062` square degree as queried and usable, preserves `0.883059` square degree
as missing, and states: "Only one of two required sky strips has a verified file."
It is a failure-handling fixture, not a scientific M60 result.

All 18 checks pass in `0.014978` seconds. The checks cover stable identifiers,
identical rerun reuse, rejection of changed content, absence of temporary files,
receipt checksums, embedded configuration and query fingerprints, Gaia area
identities, complete-run source counts and identifiers, plain-language failure
recording, and separation of complete and controlled partial runs.

### Current boundary

These receipts describe the existing archive performance circles and four
fractional test rings. They are not real physical-kiloparsec search receipts. The
same format can be used for real hosts after the exploratory physical ring request
and central scientific exclusion are declared.

### Artifacts and reproduction

- `data/results/background/host_run_records_v1/`
- `data/results/background/host_run_record_index_v1.csv`
- `data/results/background/host_run_record_validation_v1.json`

```bash
uv run python scripts/phase3_background/validate_host_run_records.py
```
<!-- preserved_source_end: docs/host_run_records.md -->


