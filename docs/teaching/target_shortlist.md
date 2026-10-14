# Teaching objects and provisional search hosts

**Checked:** 2026-10-12. Coordinates below are decimal degrees, ICRS. Gaia
positions are DR3 catalog positions; literature coordinates can differ slightly.

[Course guide](README.md) · [Concepts](concepts.md) · [Query and image checks](source_checks.md)

## 1. Known objects: start here

| Object and role | Gaia DR3 source identifier (text) | Gaia RA, Dec (degrees) | G; BP−RP; raw flux excess C |
| --- | --- | --- | --- |
| **M60-UCD1: main worked example** | `3927659910436411136` | 190.89985110, +11.53462982 | 18.115; 1.394; 4.654 |
| **M59-UCD3: brighter, cleaner-looking comparison** | `3928413763095214592` | 190.54602279, +11.64478881 | 17.850; 1.363; 6.135 |
| **M59cO: optional boundary-case compact system, with missing motion/parallax** | `3928425445406259456` | 190.48055767, +11.66771948 | 19.513; 1.373; 9.461 |
| NGC 4546-UCD1: optional, fainter comparison | `3681343123693230336` | 188.86962554, −3.78922730 | 20.012; 1.648; 14.027 |
| **Foreground comparison, selected by strong astrometry** | `3928418917055971968` | 190.64533820, +11.68032942 | 17.129; 1.114; 1.220 |

All Gaia numbers were retrieved live from ESA TAP, not inferred from a name. The
foreground comparison has parallax 0.788 ± 0.076 mas and proper motion components
+10.984 and −50.070 mas/year: persuasive foreground-star evidence. It is not a
spectroscopically checked classification or a perfectly color/magnitude-matched
control. M59cO and NGC 4546-UCD1 have no parallax/proper-motion solution in the
retrieved rows. Their missing measurements must not be entered as zero.

### Why retain M60-UCD1 as the main example?

It combines published physical characterization, a relatively bright Gaia record,
and unusual Gaia fit/flux measurements without significant measured motion.
[Strader et al. (2013)](https://arxiv.org/html/1307.7707) adopted 16.5 Mpc and
measured a 24.2 pc half-light radius. It is close to M60's light, so it also teaches
why context matters. The current DR11 cutout shows the compact source near its
center, a strong background gradient, and nearby green streaks. Do not interpret
those streaks as part of the UCD or present the image as artifact-free.

This is a known-object teaching exercise, not a claim that the frozen M60 host
search recovered this famous object. The discovery paper places it only 6.6 kpc
in projection from M60, inside the current conservative inner search exclusion.
It is not one of the two reliable controls counted in that outer-profile run.

M59-UCD3 is brighter in Gaia and its checked close-up is less dominated by host
background. Its discovery paper is
[Sandoval et al. (2015)](https://arxiv.org/abs/1506.08828). Use it alongside M60,
or as the first image if the class needs a cleaner-looking demonstration. Gaia
alone did not establish either object's physical nature.

| Object | Legacy Survey viewer, DR11 | Published/canonical evidence |
| --- | --- | --- |
| M60-UCD1 | [Viewer](https://www.legacysurvey.org/viewer?ra=190.89985109702346&dec=11.534629821482913&layer=ls-dr11&zoom=17) | Strader 2013; coordinate counterpart `canonical_315a636f7b7d54328e51ee79840622bb`, original name NGVS-UCD753 |
| M59-UCD3 | [Viewer](https://www.legacysurvey.org/viewer?ra=190.54602278774948&dec=11.644788807179935&layer=ls-dr11&zoom=17) | Sandoval 2015; `canonical_93ce39d50879542baaa8504b35ca6e2f` |
| M59cO | [Viewer](https://www.legacysurvey.org/viewer?ra=190.48055767488492&dec=11.667719481928792&layer=ls-dr11&zoom=17) | [Chilingarian & Mamon 2008](https://academic.oup.com/mnrasl/article/385/1/L83/1017524), between UCDs and compact ellipticals; `canonical_5a3facb9aecc5172a84fab77470ce757` |
| NGC 4546-UCD1 | [Viewer](https://www.legacysurvey.org/viewer?ra=188.86962553574625&dec=-3.7892273034273836&layer=ls-dr11&zoom=17) | [Norris & Kannappan 2011](https://arxiv.org/abs/1102.0001); `canonical_2926c0b4346e5f36afbf5546631a63a4` |
| Foreground comparison | [Viewer](https://www.legacysurvey.org/viewer?ra=190.6453381977382&dec=11.680329417651473&layer=ls-dr11&zoom=17) | Strong-astrometry selection in [source checks](source_checks.md); not a UCD |

Only the M60-UCD1 and M59-UCD3 close-up images were visually inspected in this
pass. Links for other examples are starting points, not certified usable images.
The coordinate counterpart for M60-UCD1 is in the canonical database but its
source row lacks a Gaia identifier. Do not assume that searching its common name
in the 724-object image bundle will find it; this teaching check has not modified
the database or its associations.

## 2. Published candidates for a small review exercise

Two relatively bright entries from the existing M60 recovery table are useful
**preparation seeds**, not a final classroom packet:

| Original name | Literature RA, Dec | Gaia source identifier | Recorded G | Current audited state |
| --- | --- | --- | --- | --- |
| J124352.42+112534.2 | 190.96841667, +11.42616667 | `3927645994742413056` | 19.376 | Candidate |
| J124524.02+110535.2 | 191.35008333, +11.09310000 | `3927574728348720512` | 19.660 | Candidate |

Source: [M60 recovery table](../../data/results/radial_search/m60_positive_control_known_recovery_v1.csv).
Canonical identifiers are `canonical_81deddc896515cea8ec786782a21d528` and
`canonical_d93f45b5a3c55ed386cb3c5b6e8fddee`. Their linked literature records have
different original status labels, but the approved database classification remains
candidate: no approved confirmation or rejection evidence. Retain the original
labels in provenance; do not teach either as a confirmed UCD.

Before assignment, the instructor must check the original publications and table
rows, Gaia match, image center, brightness, host context, external associations,
and DR11 image quality. Select additional varied examples from the existing
reference bundle, including clear and ambiguous appearances, rather than only
easy or attractive sources. Keep confirmed examples and candidates labeled
separately. This exercise is not a representative contamination-rate measurement.

## 3. Possible new search hosts: not yet an approved sample

The inherited nearby-galaxy pilot table supplies a first luminosity-ranked list.
K-band luminosity is useful as a rough indicator of stellar mass, not a measured
stellar mass. The following are plausible fields to investigate, **not certified
hosts with no published UCDs** and not the three most massive galaxies in the
nearby Universe.

| Host | RA, Dec (degrees) | Inherited distance (Mpc) | Inherited absolute K magnitude | Rationale and caveat |
| --- | --- | --- | --- | --- |
| **NGC 2974** (also NGC 2652) | 145.6387045, −3.6991485 | 22.428 | −25.499 | Luminous in the inherited table; in SLUGGS but not its UCD table. First practical field to audit; verify the unusually high luminosity against independent photometry/mass before calling it a top-mass host. |
| **NGC 1395** | 54.62447083, −23.02747222 | 24.277 | −25.032 | Rich published globular-cluster system, so scientifically interesting; group environment complicates membership. Published work did not identify a significant bright massive-cluster/UCD population, which is not a claim of none. |
| **NGC 4753** | 193.091951, −1.1996105 | 24.479 | −25.222 | Published study reported no UCD candidates under its criteria. Useful recovery/null-result exercise; existing negative evidence is a caveat for discovery yield, not proof the wider halo is empty. |

Distances and magnitudes are rounded values read from
[pilot_sample_top100.csv](../../data/galaxy_sample/pilot_sample_top100.csv), not newly
adopted distance measurements. Check distance-source consistency before luminosity
cuts: SLUGGS uses 20.9 Mpc for NGC 2974, for example, and the NGC 1395 study derives
21.1 Mpc from its cluster luminosity function. Different adopted distances change
inferred luminosity and projected separation.

### What the literature check actually establishes

- [Forbes et al. (2017), SLUGGS](https://arxiv.org/html/1701.04835), includes
  NGC 2974 but does not list it among its separately tabulated UCD hosts. This is
  bounded evidence, not an exhaustive absence claim.
- [Escudero et al. (2018)](https://academic.oup.com/mnras/article/474/4/4302/4662636)
  finds a rich NGC 1395 cluster system but no significant population of bright
  massive-cluster/UCD candidates in its color-magnitude analysis. The study's
  footprint and selection matter.
- [Caso et al. (2015)](https://arxiv.org/html/1508.07653), Section 3.1, reports no
  UCD candidates around NGC 4753 using its adopted magnitude/color criteria and
  studied fields. A Gaia search would test a different, explicitly limited sample.

Each has zero exact-host-label associations in our current canonical compilation;
that check is insufficient on its own. A counterexample is NGC 2768: it has zero
under this exact-label test but **does** have a published UCD in the SLUGGS table.
The script's hardcoded `is_lit_host` flag is therefore not an eligibility criterion.
The [source-check record](source_checks.md) gives the bounded ADS query and limits.

### Imaging and Gaia eligibility are still separate checks

The standard `ls-dr11` service returned nonzero g/r/z FITS pixels at the centers
of all three hosts, with nonuniform wider JPEGs also checked numerically for
NGC 2974 and NGC 4753. NGC 1395's first request was rate-limited, then succeeded
on a serial retry. These verify small center samples, not complete usable coverage
of any search annulus.
No host-specific HSC footprint has been verified. HSC is optional, and Subaru
imaging in a paper does not automatically mean HSC public-release coverage.

DR11 is a release, not a guarantee of new observations everywhere: the northern
part reuses DR9 reductions. See the official
[DR11 description](https://www.legacysurvey.org/dr11/description/) and
[HSC PDR3 coverage tools](https://hsc-release.mtk.nao.ac.jp/doc/index.php/available-data__pdr3/).

At these distances we cannot promise Gaia detects every real UCD. The actual
detections above verify specific luminous examples, not completeness for a host
population. Before selecting a class field, measure recovery of relevant known
objects, inspect magnitude/measurement availability, and verify the chosen radial
area's DR11 imaging. Preserve radial rings and exclude a justified inner galaxy
region; do not adopt the image cutout size as a search aperture.

**Recommendation:** M60-UCD1 and M59-UCD3 for the first session; a small published
candidate packet for student contributions; NGC 2974 as the first host to finish
auditing, NGC 1395 as an interesting alternative, and NGC 4753 as a useful
published-null comparison. Do not start a new-host class search until those
remaining checks pass.
