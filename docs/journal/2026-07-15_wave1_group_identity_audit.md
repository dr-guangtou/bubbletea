# Wave 1 Group Identity Audit

## What Was Done

- Added the read-only group audit
  `scripts/phase1_literature/audit_wave1_multi_canonical_groups.py`.
- Audited all 153 Wave 1 rows whose identifier evidence intersects multiple
  pre-Wave canonicals within one arcsecond.
- Preserved every identifier edge, nearby baseline contender, reported velocity,
  Gaia DR3 identifier, source role, coordinate, and current canonical identifier
  in deterministic CSV and JSON artifacts.
- Verified that two consecutive runs produce byte-identical artifacts.

## Results

- The 153 Wave rows form 91 connected groups involving 200 nearby pre-Wave
  canonical objects.
- Twelve groups contain 16 Wave rows and 24 pre-Wave canonicals with complete
  shared-identifier coverage, identical retained velocities, no distinct Gaia DR3
  identifiers, and no positive/negative role conflict. These groups are proposed
  for project-lead identity review.
- Seventy-four groups remain manual because one or more nearby baseline canonicals
  lack an identifier link.
- Five groups remain manual because their retained published velocities are not
  identical. This is conservative routing, not a claim that the objects conflict.

## Decisions

- Proximity is context only and never identity evidence.
- No numerical velocity threshold is introduced. Non-identical values remain for
  manual review until their source uncertainties and object histories are assessed.
- No production database identity, membership, classification, or confirmation
  state changes before project-lead approval.

## Review Artifacts

- `data/literature/validation/literature_wave1_multi_canonical_groups.md`
- `data/literature/validation/literature_wave1_multi_canonical_groups.csv`
- `data/literature/validation/literature_wave1_multi_canonical_members.csv`
- `data/literature/sources/literature_wave1_group_identity_proposals.json`

## Approved Implementation

The project lead approved all 12 proposed complete shared-identifier groups. The
builder now consolidates their 40 prior canonicals into 12 objects and preserves
all 28 superseded canonical identifiers as aliases. Twelve group-level identity
evidence records preserve the reviewed decisions.

The rebuilt v2 product contains 4,588 canonicals, 161 aliases, and 575 review
items. Candidate classifications decrease from 2,547 to 2,519 solely because the
28 duplicate candidate identities were consolidated; rejected and uncertain
counts remain unchanged. All 180 exact duplicate-coordinate groups and all 5,049
literature records remain preserved. A post-build audit retains 79 manual groups
covering 137 Wave rows and produces no new identity proposals.

## Next Step

The project lead delegated continued source-audit decisions. The five velocity
groups and 74 nearby-unlinked groups were therefore traced through the original
Liu 2015, Zhang 2015, Ko 2017, Fahrion 2019, Liu 2020, and Brodie 2011 records.

- Seventy-two identities use exact Liu 2015 NGVS keys and published `Other`
  aliases; the apparently unlinked coordinate-designated rows are catalog-lineage
  representations of the Zhang/Ko names.
- Brodie catalog `J/AJ/142/199` confirms S887, identifying Fahrion's S877 as a
  transcription error, and supplies H39168 at the T15886 position with the same
  velocity and size.
- H36612, VUCD5, VUCD7, and S5065 retain their different source velocities. Liu
  2020 explicitly defines its value as the adopted or weighted mean when multiple
  measurements exist, so the differences do not indicate separate objects.
- S547 and VUCD3 remain distinct objects. Only the Ko S547 row joins S547 and only
  Liu NGVS-UCD431 joins VUCD3; their shared unresolved Gaia source remains
  ambiguity evidence.

The 79 connected review groups close as 80 identities. The production builder
moves 238 records, stores 80 approved source-lineage evidence rows, and retains
all 229 newly superseded canonical identifiers as aliases. The deterministic v2
product contains 4,359 canonicals (2,290 candidate, 2,048 rejected, 21 uncertain),
390 aliases, and 493 review items. All 5,049 literature records and 180 exact
duplicate-coordinate groups remain preserved, and the post-build group audit has
zero remaining cases.

Those four Stage 1 gates were subsequently closed in
`docs/journal/2026-07-15_stage1_literature_stabilization.md`. The final
non-destructive validation passes with 4,359 canonicals classified as 740
confirmed, 1,515 candidate, 2,082 rejected, and 22 uncertain, with no open gates.
