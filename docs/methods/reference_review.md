# UCD reference review: scope, evidence, and decisions

[Science guide](../science_guide.md) · [Current status](../current_status.md) ·
[Detailed tool specification](../plans/ucd_visual_review_tool.md)

## What is being reviewed

The fixed image-reference list contains 680 literature-confirmed UCDs and 44
Saifollahi high-probability candidates. This is not the complete literature
database. The candidate group always remains separate from the confirmed group.

The tool combines literature provenance, Gaia measurements and neighbors, host
distance and context, Legacy Survey images and fitted catalog measurements,
external-catalog associations, and manual source-identification proposals.
The [application README](../../scripts/phase4_search/ucd_visual_review/README.md)
contains the launch command and local storage description.

## Images and associations are not physical classifications

A readable cutout can be a survey placeholder. A target can be off-center or have
an ambiguous nearest catalog source. A Legacy Survey point-source fit does not
prove an object is a star; an extended fit does not prove it is an unrelated galaxy.
Apparent resolution depends on distance as well as image quality.

The original image-reference Tractor search used 2 arcseconds. The later workbench
expanded Gaia and Legacy Survey neighbor searches to 10 arcseconds, and limits
Legacy matches to r < 23, to help inspect displaced literature coordinates.
These settings belong to different retrieval versions. Keep both records rather
than silently replacing the older measurement.

Gaia galaxy- or QSO-candidate membership is a review warning, not spectroscopic
confirmation of contamination. Gaia non-single-star membership records a multiple-
source solution; a missing match is not proof of physical singleness. Always keep
the exact Gaia identifier as a string.

## How to record a judgment

- Record whether an image is usable and whether the source appears resolved,
  off-center, close to host light, too faint to judge, blended, affected by an image
  problem, or consistent with a star-forming region or young cluster.
- Color alone cannot assign the star-forming-region flag; require catalog or visual
  evidence. Missing or incomplete catalogs provide unknown evidence.
- Blend and image-problem flags require visual inspection. Gaia quality measurements
  can prioritize inspection but do not assign those flags.
- Use `include`, `exclude`, or `hold`, keeping reasons and uncertainty. Candidate
  `include` means retain for follow-up, never promote to confirmed.
- Store coordinate/counterpart corrections as proposals. Gaia identifies the
  coordinate reference; a selected Legacy source identifies the photometry reference.
  Do not edit the canonical database during visual review.

The clean positive design reference contains only eligible confirmed objects with
completed include decisions. It is separate from the candidate follow-up pool.
Saved revisions retain history; exports connect decisions to their original inputs.

## Current limits and next measurement

The workbench is implemented; zero saved local revisions were found in the
October 12 restart audit. No visual-cleanliness claim follows from software
completion. Review a varied pilot, then the full reference, before measuring
real-field contamination in M60's independent representative 400-source sample.

See [reference preparation](../development/reference_imaging.md),
[August 19 implementation checkpoint](../journal/2026-08-19_ucd_visual_review_workbench.md),
and [host profiles](../development/host_pilot_profiles.md) for evidence.
