# First-stage host profile fixture

**Date:** 2026-08-11

**Script:** `scripts/phase3_background/freeze_first_stage_host_profiles.py`

**Command:**
`uv run python scripts/phase3_background/freeze_first_stage_host_profiles.py`

**Outputs:**

- `data/results/background/first_stage_host_profile_fixture_v1.csv`
- `data/results/background/first_stage_host_profile_fixture_v1.json`

## Purpose

This fixture defines the physical rings to retrieve before any large-radius Gaia
source count is inspected. It uses the five review galaxies that were already
selected from host identity, distance, and environment information alone.

Every host retains the same 14 rings with edges at 0, 5, 10, 15, 20, 25, 30, 40,
50, 75, 100, 150, 200, 300, and 600 kpc. The source-level output must also retain
continuous physical radius so these rings can be recombined without another Gaia
query.

## Temporary central treatment

The inner 0--50 kpc is labeled as a conservative contamination region for the first
stage. Its eight component rings remain in the output, but they are withheld from
UCD inference. Candidate boundaries at 20, 25, 30, 40, and 50 kpc may later be
compared using contamination behavior; they cannot be selected because one gives a
larger apparent UCD excess.

This 50 kpc choice is deliberately conservative and temporary. It is not a claim
that every galaxy has a 50 kpc visible body.

## Outer profile

Every requested profile reaches 600 kpc. No final outer signal boundary is selected
yet. The measured profile will be inspected first, and failed or incomplete outer
coverage will remain missing area rather than silently shortening the profile.

| Host | Distance (Mpc) | 50 kpc radius (deg) | 600 kpc radius (deg) | 600 kpc circle area (deg²) |
| --- | ---: | ---: | ---: | ---: |
| NGC 4698 | 23.933158 | 0.119699 | 1.436094 | 6.478776 |
| ESO 006-G001 | 2.700000 | 1.060912 | 12.528808 | 491.177142 |
| NGC 1316 | 19.769696 | 0.144908 | 1.738363 | 9.492875 |
| M60 | 16.657123 | 0.171985 | 2.062938 | 13.368272 |
| Arp 244 | 19.933481 | 0.143717 | 1.724089 | 9.337623 |

The nearby dwarf remains part of the fixed review set even though its requested sky
area is much larger. Geometry difficulty is not a scientific exclusion criterion.

## Galaxy-size-normalized view

The current host table contains no verified `R50`, the radius enclosing half of a
galaxy's light. Physical profiles therefore remain available, while the `R50`-
normalized view is explicitly unavailable. Once a provenance-bearing `R50` is
added, both views must be reported.

## First live benchmark

NGC 4698 is the first archive benchmark because it has the smallest 600 kpc angular
radius among the fixed review galaxies whose isolated-environment association is
resolved. This is a geometry-only choice and uses no Gaia source count.

All 16 fixture checks pass with zero archive queries. The next step is a count-only
600 kpc NGC 4698 benchmark before any full source retrieval.
