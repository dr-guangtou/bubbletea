---
date: 2026-08-12
repo: bubbletea
branch: phase3_calibrate_host_annuli_20260811
tags:
  - journal
  - phase3
  - gaia
  - host_profiles
---

## Progress

- Froze the first-stage host measurement design: concentric circular rings out to
  600 kiloparsecs, a conservative 15-kiloparsec central exclusion, verified Gaia
  retrieval coverage as the area denominator, and both local and random-field
  background comparisons.
- Retrieved and verified the complete NGC 4698 measurement area in six strips:
  23,811 Gaia sources over 6.478776 square degrees, of which 2,548 pass the frozen
  point-source selector; all 14 run checks passed.
- Produced the radial profile, sky-distribution, selection-parameter, and Gaia
  flux-excess quality-assurance figures with companion captions.
- Recorded that the visually reviewed bright example at RA 192.3120615 degrees,
  declination +8.7036833 degrees is a star despite passing the selector; it has
  strong nonzero-motion evidence and poor Gaia astrometric fit quality.
- Defined a bounded follow-up that preserves selector version 1 and measures a
  separate rule for rejecting sources whose parallax or proper motion is
  significantly inconsistent with zero.

## Lessons Learned

- A high selector probability does not guarantee that an individual source is an
  extragalactic point source; measured parallax and proper motion remain important
  evidence against a UCD interpretation.
- Gaia's blue-plus-red to broad-band flux ratio is useful quality-assurance context,
  but the literature reference boundary of 1.7 would not reject the confirmed
  stellar example and therefore should not be adopted as a BubbleTea cut.
- Most selected NGC 4698 entries lack the full astrometric measurements needed for
  a motion test, so missing astrometry must remain explicitly unknown rather than
  being treated as evidence of zero motion.

## Key Issues

- The 2,548 passing sources are not yet a scientifically clean UCD-candidate list;
  the frozen selector was designed as a broad first filter and retains at least one
  visually confirmed star.
- Any astrometric rejection boundary must be assessed against the full reliable-UCD
  sample and contaminant samples, not chosen to remove the single reviewed star or
  to change the NGC 4698 radial profile after seeing it.
- A future selector version 2 would require a separately specified validation
  sample and review protocol; this branch does not revise selector version 1.
- The next task is the bounded development-sample assessment of an astrometric
  contradiction rule, including the published three-standard-deviation reference.
