# Literature Reference Collection

**Last update:** 2026-07-14

The legacy database is an immutable provenance input, not a canonical confirmed-UCD
catalog. It contains 2,108 literature rows from 9 database sources. The
non-destructive v2 rebuild adds the missing 97-row Zhang et al. M87 table and the
321-row Dumont et al. NGC 5128 target table. It also separates the Saifollahi et
al. broad 1,155-object selection pool from 61 operational spectroscopic reference
UCDs and 44 final unconfirmed candidates. The approved Liu, Voggel, Fahrion, and
shared-Gaia treatments yield 2,710 preserved literature records and 2,354
canonical objects, with four unresolved records intentionally lacking a canonical
association.

## Current Source Packages

| Bibcode | Region or role | Screening use |
|---|---|---|
| `2007A&A...472..111M` | Centaurus galaxy cluster | Nearby reference data; distance review pending |
| `2008AJ....136.2295B` | Abell S0740 | Distant sensitivity data |
| `2009AJ....137..498G` | Fornax | Nearby reference data |
| `2011A&A...531A...4M` | Hydra I | Distant sensitivity data |
| `2011ApJ...737...86C` | Coma | Distant sensitivity data |
| `2015ApJ...802...30Z` | M87 spectroscopy | Nearby confirmation evidence; review pending |
| `2015ApJ...812...34L` | Virgo | Nearby reference data |
| `2019A&A...625A..50F` | FCC 47 plus compilation table | Nearby reference data; heterogeneous distances |
| `2020ApJ...899..140V` | Centaurus A Gaia candidates | Nearby candidate data |
| `2021MNRAS.504.3580S` | Fornax | Nearby reference data |
| `2022ApJ...929..147D` | Centaurus A spectroscopy and dynamics | Nearby candidate and supporting evidence |

Each source package under `reference/` contains a provenance README and retrieved
machine-readable files. The Wang et al. 2023 folder is a separate M31 globular
cluster methodology paper and is not one of the object-level v2 source datasets.

## Validation State

The v2 structural checks pass, but selectors remain blocked by the explicit review
gates in `data/literature/validation/literature_reference_v2_validation.md`. In
particular, no reported source-wide confirmation is automatically accepted. The
180 exact duplicate-coordinate groups are retained through many-to-one source
associations.
The approved Gaia cohorts merge 72 clean and 14 reported-role-conflict
two-position groups and retain every retired canonical identifier as an alias.
The 14 role-conflict objects have the classification
`uncertain / reported_ucd_role_conflict`. The remaining 49 pair proposals cover
31 Gaia groups requiring image-ambiguity or multi-position review.

For Saifollahi et al., table A5 is retained in a separate selection-pool table and
does not contribute canonical positive references; table A6 contributes 44
candidate records linked back to their A5 provenance rows.

The v2 build also retains 51 Liu UCD candidates as approved associations to
existing Fahrion objects, 28 Liu non-UCD comparison records, and 57 Voggel
reference records. Of the Voggel rows, 34 have approved associations within one
arcsecond, T17-1596 has an approved alias-chain association to Fahrion
HHH86-C15 at 1.37 arcseconds, and 22 create new reference objects. Four Fahrion rows
without published coordinates remain provenance records with identity reviews but
no canonical objects.

The reproducible literature search and screening worksheet are in
`data/literature/discovery/`. Bibliographic corrections retain the old identifiers
as aliases in v2.
