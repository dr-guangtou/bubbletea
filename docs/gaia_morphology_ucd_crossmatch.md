# Gaia Morphology Membership and UCD Cross-Match

**Date:** 2026-07-17  
**Status:** Development-partition measurement complete; validation partition remains blind

## Scientific Role of the Catalog

The project shorthand “Gaia morphology catalog” means the 914,837 Gaia DR3
`galaxy_candidates` sources with a published Sérsic fit (`radius_sersic IS NOT
NULL`). These are **galaxy candidates with fitted profiles**, not a uniformly
spectroscopically confirmed galaxy sample. Candidate membership can include other
compact or extended objects, potentially including UCDs and H II regions.

The catalog has two approved uses:

1. measure the sky density and Gaia-selector behavior of Gaia-detected
   extragalactic or extended-source candidates; and
2. provide supplementary morphology evidence for individual search candidates.

It must not define the parent sample for the UCD search. Requiring a successful
Sérsic fit would exclude unresolved and barely resolved UCDs for which Gaia does not
publish such a fit. The Gaia-only parent sample must be selected independently of
`galaxy_candidates` membership and Sérsic-fit availability.

## Host-Field Density Caveat

The higher combined density of morphology candidates in the 12 host fields than in
the 12 controls cannot be attributed entirely to unrelated background galaxies.
Some candidates near the hosts could be genuine host-associated compact stellar
systems, H II regions, galaxy nuclei, or other extended sources. Together with the
inconclusive paired statistics and the catalog's non-uniform selection function,
this prevents interpreting the measured density difference as either a background-
galaxy clustering signal or a UCD overdensity.

The defensible quantity is the density of **Gaia DR3 galaxy candidates with
successful Sérsic fits**, conditional on the Gaia detection and morphology
pipelines.

## Blind-Safe Exact Cross-Match

The exact Gaia DR3 source-ID cross-match was restricted to the benchmark development
partition. The 721 validation rows, including 24 confirmed UCDs, remain uninspected
until the Gaia-only selector and morphology-use policy are frozen.

| Development cohort | Tested | Sérsic-catalog matches |
|---|---:|---:|
| High-confidence confirmed UCDs | 175 | 0 |
| Uncertain literature UCD candidates | 569 | 1 |
| PHANGS and dwarf-host H II regions | 127 | 0 |
| Clean SDSS spectroscopic galaxies | 638 | 75 |

The absence of confirmed-UCD matches in the development partition supports the
decision not to require morphology-catalog membership. It does not establish zero
coverage for all confirmed UCDs because the 24 validation UCDs remain blind.

The one matched literature UCD candidate is
`canonical_fc98f8ba01545cc0a4e7ae8663ccdedb` (Gaia DR3
`6088221630780081536`). It has `radius_sersic = 2601.639 mas`, `n_sersic =
3.7763`, and `flags_sersic = 6`, meaning an elliptical profile was reported as
well fitted. This is useful galaxy-like evidence for reviewing that uncertain
candidate, but one candidate and zero confirmed matches cannot calibrate a Sérsic
rejection threshold.

## Interpreting the Sérsic Parameters

- `radius_sersic` is the fitted major-axis effective radius in milliarcseconds.
  A clearly large angular radius can support rejection of an object expected to be
  unresolved at its host distance, but it must be interpreted with its uncertainty,
  quality flag, magnitude, Gaia windowing, and the host-distance hypothesis.
- `n_sersic` measures profile concentration. A high value is not, by itself, proof
  of contamination: compact spheroids and bright galaxy cores can have concentrated
  profiles, and Gaia often measures only a galaxy's inner region.
- `flags_sersic` records fit configuration and quality. Values 6 and 8 are the
  well-fitted elliptical and circular cases; other values can indicate nearby-source
  interference, failed convergence, or parameters reaching fit-domain limits.

No hard cut on radius or Sérsic index is approved. The next calibration must compare
these parameters with independent, higher-resolution optical or space-based image
modeling. That imaging can ultimately distinguish unresolved or barely resolved UCDs
from background galaxies, bright nuclei, and other extended contaminants, but it
remains value-added validation rather than a requirement for Gaia statistical-sample
membership.

## Reproducibility

- Script: `scripts/phase1_literature/crossmatch_gaia_morphology_benchmark.py`
- Command: `BUBBLETEA_EXTERNAL_DATA=~/Dropbox/work/data uv run python scripts/phase1_literature/crossmatch_gaia_morphology_benchmark.py`
- Cross-match rows: `data/literature/validation/gaia_morphology_benchmark_crossmatch.csv`
- Manifest: `data/literature/validation/gaia_morphology_benchmark_crossmatch_manifest.json`
- Validator: `scripts/phase1_literature/validate_gaia_morphology_benchmark_crossmatch.py`
- Validation: `data/literature/validation/gaia_morphology_benchmark_crossmatch_validation.json`

Primary references are Gaia Collaboration, *Gaia Data Release 3: The extragalactic
content*, `2023A&A...674A..41G`, DOI `10.1051/0004-6361/202243232`, and Ducourant
et al., *Gaia Data Release 3: Surface brightness profiles of galaxies and host
galaxies of quasars*, `2023A&A...674A..11D`, DOI
`10.1051/0004-6361/202243798`.
