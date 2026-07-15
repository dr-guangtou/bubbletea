---
date: 2026-07-15
repo: bubbletea
branch: phase1_stabilize_literature_20260714
tags:
  - journal
  - phase1
  - literature
  - provenance
---

## Progress

- Recorded project-lead approval for all eight three-position shared-Gaia identities in `data/literature/sources/gaia_multi_position_reviews.json`.
- Generalized the v2 builder to merge approved two- or three-position groups while retaining every retired canonical identifier as an alias.
- Preserved the F-6/Gregg 27 velocity tension and both identical Saifollahi F-1/UCD2 source rows as explicit provenance.
- Closed the shared-Gaia proposal queue: 116 approved identity groups, 126 moved record associations, 125 aliases, and zero proposals remain.
- Measured 2,315 canonical objects: 1,726 candidate, 575 rejected, and 14 uncertain; 584 review items remain.
- Reproduced all 180 legacy exact duplicate-coordinate groups and kept four coordinate-null records unassociated.
- Ran two clean build-and-validation cycles in 0.94/0.24 and 0.86/0.24 seconds.
- Both cycles produced database SHA-256 `d9978289cc74b47660d352397d17e47c1935a13eee4f1b240ef33320d15f05bb` and canonical export SHA-256 `7457a3482ec1057a41e8a86f9435cbe05b23ccd83d6ee1c2bd1cc0fd3bb197ca`.
- Confirmed the legacy database SHA-256 remained `d5a2890a10244d78c9be0b54852e8a6667c6ae766053698c450413a9f3ef1806`.
- Added a ninth ADS query targeting 2015-2026 UCD titles and expanded the discovery union from 300 to 345 papers.
- Screened the exact metadata corpus with SHA-256 `54619aad14b33d82ff9408d7da7db0190d2f14709673c0b7a4e4fcf702788f79`: 5 already ingested, 313 context-only, and 27 proposed for retrieval.
- Retrieved the approved high-priority Wave 1 cohort: 19 PDFs, 365 pages, and
  90,501,988 bytes, with all PDFs structurally valid and first pages visually
  checked.
- Retrieved five authoritative VizieR packages containing 11 tables and 4,535
  preserved rows; 4,426 rows have direct or explicitly linked coordinates.
- Preserved four Nature publisher source-data workbooks byte-for-byte and recorded
  their source URLs, hashes, package integrity, and worksheet inventories.
- Measured Wave 1 overlap without changing v2: 16 exact-coordinate rows, 1,315
  within one arcsecond, 28 within five arcseconds, 3,067 beyond five arcseconds,
  and 109 non-object spatial bins.
- Identified two existing S999 canonicals separated by 0.277550692557 arcseconds;
  both remain separate pending explicit identity review.
- Recorded project-lead approval of the five-part Wave 1 treatment and rebuilt v2
  with 855 unconfirmed positive rows, 1,484 negative comparison rows, and a
  separate 904-row Wittmann mixed compact-system pool.
- Attached all 109 Ahn spatial-kinematic bins to M59-UCD3 as one supporting
  evidence dataset rather than independent objects.
- Consolidated four Zhang, Fahrion, Ko, and Liu S999 rows under the Gaia-bearing
  Fahrion position while retaining the prior Zhang canonical identifier as an
  alias and preserving every coordinate and velocity measurement.
- Preserved four exact Ko GC/UCD table conflicts as
  `uncertain / reported_ucd_role_conflict` rather than selecting either label.
- Rebuilt and validated twice in 1.28/0.41 and 1.22/0.40 seconds. Both cycles
  produced database SHA-256
  `6e3811c5eb45898c2fd5aa896374822758c69f664f6d513ba8bd9b1cfee1a8a7`
  and canonical export SHA-256
  `6d16fdbcf036791b9cf49a27d1470212c6c5098d13bdc783242de89f56b2975b`.
- Measured 5,049 literature records, 2,059 pool records, 4,623 canonicals, 126
  retained aliases, and 587 review items; the legacy database hash remains
  `d5a2890a10244d78c9be0b54852e8a6667c6ae766053698c450413a9f3ef1806`.
- Audited 2,324 remaining Wave 1 rows against 2,314 pre-Wave canonical identities
  using direct names and published aliases before positional context. Seven rows
  form a high-confidence proposed association cohort at 0.007032699785 to
  0.136000985070 arcseconds; all seven targets and source rows are candidates.
- Routed 175 match pairs from 153 Wave rows to manual group review because more
  than one baseline canonical lies within one arcsecond. Rejected four distant
  identifier collisions rather than treating reused names as identities.
- Implemented project-lead approval for the seven-row high-confidence cohort.
  Seven Wave rows now share six pre-Wave candidate identities, with seven approved
  name-or-alias evidence records and seven retired Wave canonical identifiers
  preserved as aliases.
- Rebuilt and validated twice in 1.29/0.41 and 1.27/0.41 seconds. Both cycles
  produced database SHA-256
  `15ddd262ef12e2f62b6353266a9e5c08fe48a19a38ff52e7e70d7824d48e27f4`
  and canonical export SHA-256
  `140a8b2bbccf8ae255d6bd6bab8fe026357c2e076e1d74b462f862c8fcf82cc6`.
- Measured 4,616 canonical objects: 2,547 candidate, 2,051 rejected, and 18
  uncertain. The database retains 133 canonical aliases and 587 review items.

## Lessons Learned

- Identity consolidation must support a declared number of unique source positions rather than assuming every reviewed Gaia group is a pair.
- Duplicate source rows and discordant measurements are provenance to retain, even when the corresponding positional identities are approved.
- Citation-led discovery alone missed seven relevant 2015-2018 object studies; a targeted title query is required for recall.
- Source tables must be routed by scientific row role before association: positive
  UCD rows, mixed compact-system compilations, comparison rows, and spatial bins
  cannot share one automatic ingestion rule.

## Key Issues

- Stage 1 still has raw-row, host-distance, confirmation-evidence, and new-literature screening gates.
- Non-exact Wave 1 positional overlaps other than S999 remain separate identities;
  the audit is not a general one-arcsecond association rule.
- Object-level confirmation evidence remains to be reviewed, including the
  retrieved PDF-only Wave 1 sources, before selector labels can be frozen.
- The 153 multi-canonical cases require a separate group-level audit; none was
  changed by the seven-row approval.
