---
date: 2026-07-16
repo: bubbletea
branch: phase1_reconcile_provenance_docs_20260716
tags:
  - journal
  - phase1
  - provenance
  - documentation
---

## Progress

- Completed BT-014 without restructuring any `reference/` directory.
- Verified one approved reference folder for each of 30 v2 publications plus the
  separate Wang 2023 methodology package.
- Added DOI and explicit PDF-access status to nine older VizieR packages; 21
  registered packages retain local PDFs and nine document nonlocal access.
- Added missing digest entries for Mieske table 2, Gregg table 3, the Saifollahi
  image list, Voggel FITS conversions, the Voggel PDF, and Wang methodology files.
- Generated `project_status_counts.json` directly from the v2 database and
  synchronized canonical cross-match products.
- Reconciled current headline counts in the project README, master plan, context,
  data README, reference summary, and Phase I tracker.
- Marked `key_papers.json` and `vizier_inventory.json` as superseded historical
  plans with links to their authoritative replacements.
- Passed 277 package, digest, inventory-status, and documentation-count checks.
- Revalidated all 277 checks after project-lead review and received approval to
  close the branch on 2026-07-16.

## Lessons Learned

- A complete provenance package may document DOI-based paper access when no local
  PDF is retained, but the absence must be explicit.
- Physical package inventory found three valid raw files that were present on disk
  but absent from their package README tables.
- Generated count artifacts prevent summaries from mixing provenance rows,
  canonical objects, and unique external-catalog sources.

## Key Issues

- Four coordinate-null Fahrion records remain explicit identity reviews; they do
  not block the completed Stage 1 reference gate.
- The next Stage 1 task is BT-019: build the labeled UCD and contaminant benchmark
  with fixed validation partitions and provenance-bearing uncertainty labels.
