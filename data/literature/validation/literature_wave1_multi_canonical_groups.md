# Literature Wave 1 Multi-Canonical Group Audit

**Status:** `complete_no_new_proposals`
**Reference database SHA-256:** `bb00860e1f39a4b7250a27d545eb5234e6612c1fd70d1ec6f3078658d825e05e`

This read-only audit groups the Wave 1 rows whose identifier evidence intersects
multiple pre-Wave canonical objects within one arcsecond. Every nearby baseline
canonical is retained in the review group. Position alone never supports a merge.

## Coverage

| Measure | Count |
|---|---:|
| Connected review groups | 0 |
| Wave 1 rows | 0 |
| Pre-Wave canonical objects | 0 |
| Proposed merge groups | 0 |
| Wave 1 rows in proposed groups | 0 |
| Pre-Wave canonicals in proposed groups | 0 |
| Current canonicals in proposed groups | 0 |

## Routing

| Recommendation | Groups |
|---|---:|


Groups with distinct Gaia DR3 identifiers are explicitly retained separately.
Groups with an unreferenced nearby canonical or non-identical reported velocities
remain manual. A proposed merge requires identifier coverage for every baseline
canonical and no Gaia conflict; reported positive/negative conflicts are routed to
the existing uncertain role-conflict treatment.

## Proposed Groups

| Group | Shared identifier | Wave rows | Baseline canonicals | Recommendation | UCD roles | Velocity spread, km/s | Maximum separation, arcsec |
|---|---|---:|---:|---|---|---:|---:|


The companion membership CSV preserves every record, identifier link, velocity,
Gaia identifier, and separation used for review. No identity or classification
was changed by this audit. Previously approved groups already associated with a
pre-Wave canonical are excluded from this remaining-case report.
