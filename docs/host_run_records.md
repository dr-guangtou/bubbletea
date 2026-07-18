# Per-galaxy analysis receipts

**Status:** Receipt format and non-overwrite behavior validated
**Date:** 2026-07-18
**Issue:** BT-010

## What one receipt is

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

## Why receipts are never overwritten

The run identifier is calculated from the declared configuration and exact input
file checksums. The per-galaxy identifier combines that run identifier with the
galaxy identity. Therefore rerunning identical inputs finds the same receipt, while
changed inputs or settings produce a different run identifier and a new receipt
path.

Writing is atomic: other code sees either no receipt or the complete receipt, never
a half-written file. If the destination already contains identical content, it is
reused. If it contains different content, the write fails rather than replacing the
earlier result. The validation also exercises concurrent-safe file creation.

## Bounded results

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

## Current boundary

These receipts describe the existing archive performance circles and four
fractional test rings. They are not real physical-kiloparsec search receipts. The
same format can be used for real hosts after the exploratory physical ring request
and central scientific exclusion are declared.

## Artifacts and reproduction

- `data/results/background/host_run_records_v1/`
- `data/results/background/host_run_record_index_v1.csv`
- `data/results/background/host_run_record_validation_v1.json`

```bash
uv run python scripts/phase3_background/validate_host_run_records.py
```
