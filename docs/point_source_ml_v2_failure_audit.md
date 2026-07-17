# Benchmark-v2 persistent UCD failure audit

**Date:** 2026-07-18  
**Scope:** Seven confirmed UCDs missed in all ten development-only logistic repeats  
**Validation partition:** Sealed and uninspected

## Result

The seven failures are not one homogeneous class. All seven retain approved
spectroscopic membership evidence, so this audit does not recommend changing their
UCD classifications. Four Gaia associations are nevertheless unsafe as positive
training examples because the matched Gaia source has highly significant proper
motion. The remaining three are plausible hard UCD examples at `G > 20` and should
remain in development.

| Literature object | Gaia DR3 source | G | Literature-to-Gaia offset | Proper-motion zero-significance | Assessment |
|---|---:|---:|---:|---:|---|
| NGC 1400_1 | 5107392559411455616 | 19.571 | 0.466 arcsec | 14.31 | Suspect foreground superposition or wrong Gaia association |
| NGC1400_2 | 5107470379920956160 | 19.049 | 0.392 arcsec | 44.87 | Suspect foreground superposition or wrong Gaia association |
| Dorado2 | 4778649573525185024 | 19.825 | 0.741 arcsec | 9.91 | Suspect foreground superposition or wrong Gaia association |
| Saifollahi A1 row 32 | 4860354282585368064 | 20.338 | 0.121 arcsec | 11.67 | Suspect foreground superposition despite close positional match |
| Saifollahi A1 row 36 | 4860213682535953792 | 20.456 | 0.112 arcsec | 0.27 | Plausible hard UCD; faint and blue |
| Saifollahi A1 row 39 | 4860359470905910656 | 20.575 | 0.301 arcsec | 0.56 | Plausible hard UCD; faint and moderately extended in Gaia |
| Saifollahi A1 row 59 | 4860293126545559424 | 20.351 | 0.270 arcsec | 2.80 | Plausible hard UCD; resolved-size evidence and Gaia excess noise |

The proper-motion significance uses the full Gaia two-dimensional covariance, not
the two components independently. The four suspect associations have significance
between 9.91 and 44.87, whereas the other three range from 0.27 to 2.80. The three
Fahrion objects have nonzero published velocities. The four Saifollahi objects are
members of the spectroscopic A1 reference sample and have published half-light
radii of 15.2, 5.6, 9.9, and 13.2 pc, respectively. Thus, the conflict is between
the confirmed literature object and the Gaia association, not evidence that the
literature object itself is a foreground star.

## Approved treatment

Retain all seven canonical objects as confirmed UCDs. Mark the four high-motion Gaia
links as `suspect_foreground_superposition_or_wrong_gaia_association` and exclude
those links from selector training until image/epoch-aware association review is
complete. Do not relabel the underlying UCDs. Keep the other three as intentional
hard positive examples. The project lead approved this treatment on 2026-07-18.
The five-case evidence register, including rejected B409, is
`data/literature/sources/ucd_reliability_reviews.json`.

Benchmark v3 implements the decision non-destructively. It retains all 3,857 rows
and changes no published classification or partition assignment, but makes the four
conflicted links ineligible for reliable training. Development then contains 146
reliable confirmed UCDs and 438 rematched stars. Ten-repeat logistic recall is
93.84--96.58% (median 94.18%) and macro priority retention is 3.61--4.00% (median
3.78%). All stability gates pass, although nine reliable UCDs are now persistent
misses and all 50 fits still choose boundary `C = 3.0`.
