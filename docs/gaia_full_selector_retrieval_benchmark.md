# Full-selector-column Gaia retrieval benchmark

**Status:** Bounded benchmark passed; 5,000-row limit confirmed by multifield restart validation
**Date:** 2026-07-18
**Selector:** `point_source_logistic_model_v1`
**Gaia release reference:** `2023A&A...674A...1G`, DOI
`10.1051/0004-6361/202243940`

## Purpose

The restart test initially downloaded only four columns. A real search must download
all 19 Gaia columns required to calculate the frozen classifier's nine features.
This benchmark measures the archive time, local memory, serialized file size, and
classifier time for progressively larger full-column results.

The test uses a predeclared review host, ESO 006-G001, and a 0.5-degree-radius
performance-test circle. The circle contains 13,010 Gaia entries in the frozen
G-magnitude range. This field and radius measure retrieval behavior only; they do
not define the galaxy's scientific aperture or background.

## Measurements

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

## Provisional limit

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

## Artifacts and reproduction

- `data/results/background/gaia_full_selector_retrieval_benchmark_v1.csv`
- `data/results/background/gaia_full_selector_retrieval_benchmark_v1.json`

```bash
uv run python scripts/phase3_background/benchmark_full_selector_retrieval.py
```
