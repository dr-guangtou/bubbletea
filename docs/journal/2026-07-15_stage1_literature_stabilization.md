# Stage 1 Literature Stabilization

## What Was Done

- Closed the raw-row coverage gate by attaching 168 supporting rows to preserved
  objects as structural, velocity, or spectroscopic measurement evidence.
- Audited normalized hosts and distances. Corrected 27 Mieske Centaurus galaxy-
  cluster rows from the unsafe legacy 3.8 Mpc default to the source-stated 43 Mpc,
  retained the original values in immutable payloads, and kept the heterogeneous
  Fahrion compilation distance null.
- Corrected the Liu M87 derived normalization from the authoritative primary
  table: 92 rows retain `UCD=1`, 35 rows become `UCD=0`, all 127 receive the M87
  host label, and the source's 16.5 Mpc value remains scoped to that table.
- Completed the delegated object-level confirmation audit. Approved 1,316
  spectroscopic evidence rows from 12 source-defined cohorts under
  `confirmation_rules_v1`; recorded 57 Voggel comparison rows as reviewed non-
  promotions because their local table lacks qualifying confirmation evidence.
- Closed literature screening against the hashed 345-paper ADS corpus. All
  decisions are complete, 19 sources were retrieved, and eight optional retrievals
  have explicit deferral dispositions.

## Results

- The production v2 database contains 5,049 immutable literature records and
  4,359 canonical objects: 740 confirmed, 1,515 candidate, 2,082 rejected, and 22
  uncertain with subtype `reported_ucd_role_conflict`.
- M87UCD-29 is the newly exposed role conflict: Zhang, Ko, and Liu 2020 provide
  positive spectroscopic/UCD evidence, while Liu 2015 reports the same identity as
  `UCD=0`. Both sides remain preserved and the canonical classification is
  uncertain.
- Four coordinate-null Fahrion records remain pending identity reviews; they are
  provenance records without artificial positions and do not represent an open
  Stage 1 literature gate.
- All 180 legacy exact duplicate-coordinate groups are reproduced. The legacy
  database SHA-256 remains
  `d5a2890a10244d78c9be0b54852e8a6667c6ae766053698c450413a9f3ef1806`.
- The production v2 SHA-256 is
  `bb00860e1f39a4b7250a27d545eb5234e6612c1fd70d1ec6f3078658d825e05e`.
- `data/literature/validation/literature_reference_v2_validation.json` reports
  `passed`, no failures, and no open gates.

## Key Artifacts

- `data/literature/sources/supporting_source_row_links.json`
- `data/literature/sources/host_distance_reviews.json`
- `data/literature/sources/confirmation_evidence_reviews.json`
- `data/literature/sources/literature_screening_closure.json`
- `data/literature/validation/literature_reference_v2_validation.md`
- `data/literature/database/ucd_reference_v2.db`

## Decisions

- A source-reported confirmation label is not sufficient by itself. Promotion
  requires qualifying object-level evidence under the versioned ruleset.
- Source-wide distances are environmental context unless a source supports finer
  object- or host-specific normalization.
- Completing literature screening does not require ingesting every relevant
  ancillary paper. Deferred sources retain explicit scope and remain available
  for later enrichment.
- Selector changes remain separate from reference-data stabilization.

## Next Step

Begin the Stage 1 selector work by repairing spherical cross-match geometry and
ambiguity handling (`BT-007`), then synchronize Gaia and Legacy Survey exports
with the stabilized canonical database (`BT-004`) before calibrating one versioned
Gaia-only selector (`BT-002`).
