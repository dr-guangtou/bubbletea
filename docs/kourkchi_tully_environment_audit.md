# Kourkchi-Tully environment audit

**Date:** 2026-07-18
**Catalog:** VizieR `J/ApJ/843/16`
**Paper:** Kourkchi & Tully 2017, `2017ApJ...843...16K`

The raw ReadMe, group table, and member table are stored outside the repository
under `BUBBLETEA_EXTERNAL_DATA/bubbletea/environment_reference/kourkchi2017`.
Their SHA-256 digests and source identifiers are recorded in
`data/literature/sources/kourkchi_tully_2017_groups.json`.

The member table contains 15,004 unique PGC galaxies in 8,826 groups. A nearest
spherical audit against all 2,155 current BubbleTea hosts finds 1,794 hosts with a
catalog neighbor within 5 arcsec. Two hosts have two catalog galaxies inside that
radius and remain manual ambiguities. The other 1,792 unique associations are
accepted under `accepted_unique_spherical_5arcsec_v1`; 361 hosts remain unmatched.

The 5-arcsec identity radius is empirically checked rather than assumed. Eight
one-degree shifted control sets, spanning position angles in 45-degree steps,
contain 17,240 shifted host positions and produce zero matches within 5 arcsec.
The accepted real associations contain no repeated PGC identifier. Ten validation
checks pass.

Among the 1,792 accepted associations, the catalog roles are group member, group
principal, or isolated principal. These are catalog-derived environment evidence,
not permission to assign an inferential background. The two ambiguous and 361
unmatched hosts retain explicit non-accepted states. Catalog distance disagreement
is preserved as a diagnostic and does not invalidate an otherwise unique
sub-arcsecond identity; the project host distance and the group-catalog distance
have different provenance and uses.

Artifacts:

- `data/galaxy_sample/kourkchi_tully_environment_candidates_v1.csv`
- `data/results/background/kourkchi_tully_environment_audit_v1.json`
- `data/results/background/kourkchi_tully_environment_validation_v1.json`
