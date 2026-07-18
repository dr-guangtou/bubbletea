# Adaptive and restartable Gaia retrieval validation

**Status:** Bounded split, stop, resume, and corruption-recovery test passed
**Date:** 2026-07-18
**Gaia release reference:** `2023A&A...674A...1G`, DOI
`10.1051/0004-6361/202243940`

## Plain-language workflow

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

## Bounded live validation

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

## Production contract and remaining work

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

Before a real multi-degree host run, the workflow still needs a measured safe row
and file-size limit using the full selector inputs, a bounded full-column restart
test, and integration with exact radial-ring area and masking calculations.

## Artifacts and reproduction

- `data/results/background/gaia_adaptive_retrieval_plan_v1.csv`
- `data/results/background/gaia_adaptive_retrieval_sources_v1.csv`
- `data/results/background/gaia_adaptive_retrieval_validation_v1.json`

```bash
uv run python scripts/phase3_background/validate_adaptive_gaia_retrieval.py
```
