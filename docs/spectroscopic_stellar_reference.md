# Matched Spectroscopic Stellar Reference

**Date:** 2026-07-17  
**Status:** Development supplement complete; no selector threshold approved

## Definition and Naming

This reference contains objects with clean primary SDSS DR16 spectra classified
exactly as `STAR` (`scienceprimary = 1`, `zwarning = 0`) and linked to Gaia DR3 by
the NOIRLab 1.5-arcsecond cross-match table. It is called a **spectroscopic stellar
reference**, not a single-star sample. Stellar spectroscopy does not exclude
unresolved binaries, and absence from Gaia NSS would not prove physical singleness.

The reference supplements but does not modify `benchmark_v1`. Every one of the
3,857 benchmark Gaia identifiers was excluded in the archive query, so the new
reference is disjoint from both benchmark partitions and no validation identifier
was inspected.

## Parent and Matching Design

The complete archive count measured in ten exact `random_id` bins is 812,893
Gaia-linked clean stellar spectrum associations over the earlier audited
`14.0992 <= G <= 21.8186` interval. The operational pool uses the deterministic
`0 <= random_id < 10` interval and the current benchmark magnitude domain. After
nearest unique spectrum-to-Gaia association resolution, the external pool contains
79,369 unique sources.

Three unique controls were assigned to each of the 175 confirmed development UCDs.
Matching used only:

- Gaia `phot_g_mean_mag`;
- absolute Galactic latitude; and
- absolute barycentric-true-ecliptic latitude.

No parallax, proper motion, RUWE, astrometric excess noise, IPD, flux-excess, DSC,
candidate-membership, or NSS field was used to retrieve, filter, or match stars.
Those fields remain outcomes to be measured. The matched cohort contains 525 unique
stars, with median absolute target-control differences of 0.0810 mag, 1.3371
degrees, and 0.9590 degrees in the three matching variables. Maximum differences
remain larger and are preserved in the manifest; matching reduces but does not
remove the SDSS footprint and targeting selection functions.

## Development-Only Feature Result

The leading direction-adjusted univariate ROC AUC measurements are:

| Gaia feature | AUC | UCD direction | UCD coverage | Stellar coverage |
|---|---:|---|---:|---:|
| Astrometric-excess-noise significance | 0.961 | Higher | 100.0% | 100.0% |
| RUWE | 0.940 | Higher | 46.9% | 69.7% |
| BP/RP flux-excess factor | 0.940 | Higher | 100.0% | 98.7% |
| Astrometric excess noise | 0.934 | Higher | 100.0% | 100.0% |
| DSC galaxy probability | 0.917 | Higher | 100.0% | 99.8% |
| Proper-motion zero-significance | 0.879 | Lower | 46.9% | 69.7% |

The rejected legacy 70/30 and 60/30/10 rules retain 71/525 (13.5%) and 35/525
(6.7%) of these stars, respectively. These fractions diagnose the historical rules;
they do not approve either rule. In particular, stronger stellar rejection cannot
compensate for their previously measured loss of confirmed-UCD completeness.

The result fills the missing ordinary-stellar baseline while preserving three
limitations: SDSS spectroscopic targeting is non-random, the reference is not proof
of singleness, and the matching is only over observed magnitude and latitude
summaries. Performance must still be assessed alongside NSS, galaxy, QSO, H II, and
reported non-UCD cohorts rather than pooling all negatives.

## Reproducibility

- Builder: `scripts/phase1_literature/build_spectroscopic_stellar_reference.py`
- Analysis: `scripts/phase1_literature/analyze_spectroscopic_stellar_reference.py`
- Validator: `scripts/phase1_literature/validate_spectroscopic_stellar_reference.py`
- External pool: `$BUBBLETEA_EXTERNAL_DATA/bubbletea/stellar_reference/sdss_dr16/gaia_linked_clean_spectroscopic_stars_random_0_10_v2.fits`
- Matches: `data/literature/benchmarks/spectroscopic_stellar_reference_matches_v1.csv`
- Manifest: `data/literature/benchmarks/spectroscopic_stellar_reference_manifest_v1.json`
- Metrics: `data/literature/validation/spectroscopic_stellar_reference_feature_metrics_v1.csv`
- Summary: `data/literature/validation/spectroscopic_stellar_reference_summary_v1.json`
- Validation: `data/literature/validation/spectroscopic_stellar_reference_validation_v1.json`

The SDSS DR16 provenance is Ahumada et al. 2020,
`2020ApJS..249....3A`, DOI `10.3847/1538-4365/ab929e`.
