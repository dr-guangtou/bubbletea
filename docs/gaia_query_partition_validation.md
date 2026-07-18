# Gaia large-region query partition validation

**Status:** Bounded equivalence test passed; adaptive large-region retrieval pending
**Date:** 2026-07-18
**Gaia release reference:** `2023A&A...674A...1G`, DOI
`10.1051/0004-6361/202243940`

## Why the query is divided

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

## Bounded live test

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

## Real retrieval contract

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

## Artifacts and reproduction

- `data/results/background/gaia_query_partition_sources_v1.csv`
- `data/results/background/gaia_query_partition_strips_v1.csv`
- `data/results/background/gaia_query_partition_validation_v1.json`

```bash
uv run python scripts/phase3_background/validate_gaia_query_partition.py
```
