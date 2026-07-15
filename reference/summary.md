# Literature Reference Collection

**Last update:** 2026-07-16

The legacy database is an immutable provenance input, not a canonical confirmed-UCD
catalog. It contains 2,108 literature rows from 9 database sources. The
non-destructive v2 rebuild adds the missing 97-row Zhang et al. M87 table and the
321-row Dumont et al. NGC 5128 target table. It also separates the Saifollahi et
al. broad 1,155-object selection pool from 61 operational spectroscopic reference
UCDs and 44 final unconfirmed candidates. The approved Liu, Voggel, Fahrion, and
shared-Gaia and Wave 1 treatments yield 5,049 preserved literature records from
14 record-contributing publications and 4,359 canonical objects, with four
unresolved records intentionally lacking a canonical association. The database
registers 30 publication provenance packages in total. The canonical
classifications are 740 confirmed, 1,515 candidate, 2,082 rejected, and 22
uncertain.

## Object-Level Dataset Packages

| Bibcode | Region or role | Screening use |
|---|---|---|
| `2007A&A...472..111M` | Centaurus galaxy cluster | Nearby reference data; source distance corrected to 43 Mpc |
| `2008AJ....136.2295B` | Abell S0740 | Distant sensitivity data |
| `2009AJ....137..498G` | Fornax | Nearby reference data |
| `2011A&A...531A...4M` | Hydra I | Distant sensitivity data |
| `2011ApJ...737...86C` | Coma | Distant sensitivity data |
| `2015ApJ...802...30Z` | M87 spectroscopy | Approved object-level confirmation evidence |
| `2015ApJ...812...34L` | Virgo | Nearby reference data |
| `2019A&A...625A..50F` | FCC 47 plus compilation table | Nearby reference data; heterogeneous distances |
| `2020ApJ...899..140V` | Centaurus A Gaia candidates | Nearby candidate data |
| `2021MNRAS.504.3580S` | Fornax | Nearby reference data |
| `2022ApJ...929..147D` | Centaurus A spectroscopy and dynamics | Nearby candidate and supporting evidence |

The v2 database registers 30 publication packages: the object-level datasets
above plus approved Wave 1 reference and confirmation sources. Every registered
publication has a provenance README, bibliographic identifiers, a local PDF or
documented access status, and original machine-readable files or an explicit
no-package status. The Wang et al. 2023 folder is a separate M31 globular-cluster
methodology package, bringing the tracked reference-folder total to 31.

## Validation State

The v2 structural checks pass with no open Stage 1 gates. No reported source-wide
confirmation is automatically accepted, and the 180 exact duplicate-coordinate
groups are retained through many-to-one source associations.
The approved Gaia cohorts merge 72 clean and 14 reported-role-conflict
two-position groups and retain every retired canonical identifier as an alias.
The 14 role-conflict objects have the classification
`uncertain / reported_ucd_role_conflict`. No shared-Gaia association proposal
remains open.

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
as aliases in v2. Generated headline counts and package checks are in
`data/literature/validation/project_status_counts.json` and
`data/literature/validation/provenance_documentation_validation.json`.
