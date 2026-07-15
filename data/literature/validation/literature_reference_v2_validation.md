# Literature Reference v2 Validation

**Date:** 2026-07-15
**Status:** `passed`
**Legacy database SHA-256:** `d5a2890a10244d78c9be0b54852e8a6667c6ae766053698c450413a9f3ef1806`
**Canonical export SHA-256:** `6821a94bed510acfb7f0afb0fc62ca4dcb0943ef1a17cd0e8daa673101609a06`

## Preserved Inputs and Outputs

| Measure | Count |
|---|---:|
| Publications | 30 |
| Datasets | 22 |
| Raw provenance files | 50 |
| Immutable literature records | 5049 |
| Separate selection-pool records | 2059 |
| Saifollahi broad selection-pool records | 1155 |
| Wittmann mixed compact-system pool records | 904 |
| Selection-pool links to final candidates | 44 |
| Approved Wave 1 object and comparison records | 2339 |
| Wave 1 source-reported UCD or possible-UCD rows | 855 |
| Wave 1 comparison or contaminant rows | 1484 |
| Registered Wave 1 VizieR files | 16 |
| Approved S999 non-anchor associations | 3 |
| Approved S999 identity evidence records | 1 |
| Ahn M59-UCD3 spatial-kinematic evidence records | 1 |
| Approved Wave 1 name-or-alias associations | 7 |
| Approved Wave 1 name-or-alias identity evidence | 7 |
| Records moved by approved Wave 1 multi-canonical identities | 28 |
| Approved Wave 1 multi-canonical identity groups | 12 |
| Records moved by delegated Wave 1 source identities | 238 |
| Approved delegated Wave 1 source identities | 80 |
| Supporting source rows linked as measurement evidence | 168 |
| Approved object-level spectroscopic evidence rows | 1316 |
| Reported-confirmed rows supported by approved evidence | 535 |
| Reported-confirmed rows reviewed without qualifying local evidence | 57 |
| ADS papers in the completed hashed screen | 345 |
| Approved literature retrievals | 19 |
| Explicitly scoped retrieval deferrals | 8 |
| Saifollahi spectroscopic reference UCD evidence rows | 61 |
| Approved Liu source associations | 51 |
| Approved Zhang/Fahrion S547 association | 1 |
| Approved Voggel source associations | 35 |
| Approved Voggel alias-chain associations | 1 |
| Approved identity evidence records | 1 |
| Pending Voggel manual association proposals | 0 |
| Coordinate-null provenance records without canonical objects | 4 |
| Canonical objects | 4359 |
| Exact duplicate-coordinate groups | 180 |
| Approved shared-Gaia identity groups | 116 |
| Approved three-position shared-Gaia identity groups | 8 |
| Approved ambiguous shared-Gaia close-pair evidence records | 2 |
| Approved supplemental name-and-position identity evidence | 1 |
| Literature records moved by approved Gaia associations | 128 |
| Retired canonical identifiers retained as aliases | 390 |
| Preserved F-6/Gregg 27 velocity-tension evidence | 1 |
| Preserved duplicate Saifollahi F-1/UCD2 source rows | 2 |
| Uncertain objects with reported UCD-role conflict subtype | 22 |
| Non-exact Gaia association proposals | 0 |
| Gaia source groups still under review | 0 |
| All open association proposals | 0 |
| Open review items | 4 |

The legacy audit remains 2108 rows and
180 exact duplicate-coordinate
groups. Additional canonical records come from authoritative Zhang, Dumont,
Saifollahi, Liu, Voggel, Ko, and Wave 1 tables. The broader Saifollahi and mixed
Wittmann pools remain separate from canonical positive references.

Approved Liu and Voggel associations retain distinct literature records while
linking them to existing canonical objects. Four coordinate-null Fahrion rows are
preserved as unresolved provenance records without creating artificial positions.
The T17-1596 Voggel row is linked to Fahrion HHH86-C15 through the published
Taylor GC0218 and Woodley HHH86-C15 alias chain; its 1.37-arcsec coordinate
offset remains recorded on the accepted association.
The approved Gaia cohorts merge 72 clean, 14 reported-role-conflict, 22
image-reviewed two-position, and eight literature-reviewed three-position groups
while retaining every superseded canonical identifier as an alias. The 14
role-conflict objects remain explicitly uncertain. The F-6/Gregg 27 velocity
tension is retained as reviewed evidence, and both identical Saifollahi source
rows in the F-1/UCD2 identity are preserved as separate provenance records.
Zhang and Fahrion S547 records are consolidated through approved name-and-position
evidence, while S547 and VUCD3 remain separate canonical objects sharing explicit
ambiguous unresolved-Gaia evidence. No shared-Gaia identity proposals remain.
The approved Wave 1 treatment preserves 855 positive and 1,484 comparison rows
without promoting confirmation or applying a general non-exact matching radius.
Four exact Ko UCD/GC role conflicts remain explicitly uncertain. The Zhang,
Fahrion, Ko, and Liu representations of S999 are consolidated under the
Gaia-bearing Fahrion position while retaining the prior Zhang canonical identifier
as an alias. The 109 Ahn spatial bins are attached to M59-UCD3 as one supporting
measurement dataset rather than 109 objects.
Seven additional Wave 1 rows are associated with six pre-Wave candidate
identities through direct names or source-published aliases. Each reviewed target
was the unique nearest baseline canonical within one arcsecond, and no general
positional matching radius was introduced. All seven superseded Wave canonical
identifiers remain aliases; classifications are unchanged apart from the expected
reduction in duplicate candidate objects.
Twelve additional multi-canonical groups are consolidated through complete shared-
identifier coverage, identical retained velocities, consistent reported roles,
and no distinct-Gaia conflict. Their 16 Wave rows and 24 pre-Wave canonicals now
form 12 objects, and all 28 superseded canonical identifiers remain aliases. The
other 79 reviewed groups were left unchanged at that review gate.
The delegated source audit closes those 79 groups as 80 identities. Seventy-two
use exact Liu 2015 catalog keys and published aliases, two use Brodie catalog
evidence, four preserve differing independent or weighted velocity measurements,
and the S547/VUCD3 close pair is split into its two previously reviewed distinct
objects. All 229 superseded canonical identifiers remain aliases, every reported
velocity remains immutable source evidence, and no positional identity rule is
introduced.
The raw-row coverage gate is closed. All 168 rows in the three tables previously
classified as intentionally supporting rather than object-defining are attached
to preserved objects as measurement evidence: 27 Chiboucas structural rows, 127
Liu structural-and-velocity rows, and 14 Voggel spectroscopic rows. These links do
not authorize identity, classification, or confirmation changes.
The host-distance gate is also closed. Mieske's 27 Centaurus-cluster rows now use
the source-stated 43 Mpc instead of the incorrect legacy 3.8 Mpc Centaurus A
default, while all original values remain in immutable raw payloads. Fahrion's
heterogeneous 381-row compilation retains its published per-row host labels but
no blanket normalized distance. Liu's 127 M87, 50 M49, and 29 M60 rows now carry
explicit table-specific host labels, and the 16.5 Mpc legacy value remains scoped
to the M87 table. Other retained distances are documented as source-adopted or
approximate environmental context, not independent object-level measurements.
The confirmation gate is closed under `confirmation_rules_v1`. The delegated
audit approves 1,316 spectroscopic evidence rows across 12 source-defined cohorts,
which resolve to 740 confirmed canonical objects after identity consolidation.
The 57 Voggel previously confirmed comparison rows remain candidates because the
local table does not carry qualifying object-level spectroscopy or resolved-
structure evidence. Twenty-two reviewed positive/negative role conflicts remain
uncertain, including M87UCD-29; no source label or measurement is discarded.
The new-literature screening gate is closed against the same-day hashed ADS
corpus of 345 papers. All title-and-abstract decisions are complete, 19 sources
were retrieved in the approved Wave 1 cohort, and eight remaining retrieval
candidates have explicit ancillary, incremental, mixed-distance, or distant-
sensitivity dispositions. Deferral does not classify those papers as irrelevant;
it prevents optional enrichment from blocking the Stage 1 benchmark.

## Conservative Classifications

| State | Canonical objects |
|---|---:|
| `candidate` | 1515 |
| `confirmed` | 740 |
| `rejected` | 2082 |
| `uncertain` | 22 |

No reported confirmation is promoted automatically. Every promotion requires an
approved evidence review under `confirmation_rules_v1`.

## Dataset Authority

| Status | Datasets |
|---|---:|
| `authoritative_candidate_table` | 1 |
| `authoritative_coordinate_null_supplement` | 1 |
| `authoritative_mixed_candidate_comparison_table` | 2 |
| `authoritative_reference_table` | 1 |
| `authoritative_selection_pool` | 1 |
| `authoritative_vizier_package` | 5 |
| `normalized_records_linked_to_raw_package` | 11 |

## Open Stage 1 Gates

- None.

All Stage 1 literature-stabilization gates are closed. Selector changes remain a
separate reviewed task. The legacy database was opened read-only and the
destructive redundancy script was not used.
