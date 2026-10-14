# Necessary background: compact galaxies hidden among stars

[Course guide](README.md) · [Objects to investigate](target_shortlist.md) ·
[Instructor source checks](source_checks.md)

## Why look for ultra-compact dwarf galaxies?

Galaxies grow through interactions and mergers. Some of their history survives in
small stellar systems orbiting them. A compact object that looks unremarkable in
an image can therefore carry evidence about how a much larger galaxy assembled.
UCDs are interesting partly because their origin is not unique: some may be very
massive star clusters, while others may be galaxy centers left behind after their
outer stars were stripped away. Identifying the objects is the first step toward
testing those histories, not the final answer.

M60-UCD1 makes this question tangible. Detailed follow-up found a massive black
hole in this small stellar system, supporting an origin as the surviving center
of a larger galaxy. This result required spectroscopy and dynamical modeling;
students cannot infer a black hole from a Legacy Survey cutout or a Gaia fit
statistic. See [Seth et al. (2014)](https://arxiv.org/html/1409.4769).

There is also a lesson about how discoveries happen. Bright compact systems can
be overlooked when a survey labels them as stars or when a search assumes that
all interesting galaxies must look visibly extended. M59-UCD3 was found by
combining archival images and spectroscopy rather than accepting a single
catalog label. Its [discovery study](https://arxiv.org/html/1506.08828) is a useful
example of asking a new question of existing data.

In this short project we will not establish a new object's distance, formation
history, or UCD classification. We will learn to identify useful evidence, find
obvious alternative explanations, and recommend what should be checked next.

## 1. What kind of object are we looking for?

A foreground star belongs to the Milky Way. A globular cluster is a dense group of
stars. A UCD is a compact stellar system that can be larger or more luminous than
ordinary globular clusters, although the categories overlap. A host galaxy is the
larger galaxy with which a compact system may be physically associated. Being
near that galaxy on the sky does not prove association.

Some UCDs may be stripped galaxy nuclei: compact centers left behind after a
larger galaxy loses its outer stars. Do not teach that every UCD has this origin
or that a single size or brightness boundary settles the classification.

**Naming trap:** Gaia also uses “UCD” for **ultracool dwarfs**, very cool stellar
objects. Its `gold_sample_ucd` table is not a catalog of ultra-compact dwarf
galaxies. See the [Gaia table definition](https://gaia.aip.de/metadata/gaiadr3/gold_sample_ucd/).

## 2. A point-like image does not imply a single star

A telescope blurs a true point source into a small patch. That pattern is called
the **point-spread function**, or PSF. An object is *resolved* only when its own
spatial extent can be distinguished from this blur. Atmospheric seeing contributes
to the blur in ground-based images. Image pixel size and resolving power are not
the same thing.

At larger distance the same physical object subtends a smaller angle. Thus a
nearby UCD can look extended while a similar, more distant UCD looks like a star.
Compare against neighboring stars in the same image, not against images with
different seeing or display stretches. “Unresolved” is a valid observation, not a
rejection of a UCD.

Physical sizes and distances here use parsecs (pc), an astronomical distance unit;
one megaparsec (Mpc) is one million parsecs.

**Worked example:** the discovery paper gives M60-UCD1 a half-light radius of
24.2 pc, the radius enclosing half its measured light, at an adopted distance of
16.5 Mpc. The small-angle relation gives

```text
angular radius (arcseconds) = 206265 × radius (pc) / distance (pc)
                           = 206265 × 24.2 / 16,500,000
                           = 0.303 arcseconds, rounded
```

This is a half-light **radius**, not a diameter or the observed image width. A
ground-based image can therefore look nearly point-like without contradicting
the resolved measurements from better imaging. These literature inputs are from
[Strader et al. (2013)](https://arxiv.org/html/1307.7707).

## Why Gaia favors star-like objects - but does not see only stars

Gaia scanned the sky rather than taking ordinary large photographs for each
target. Its onboard software searched for compact concentrations of light and
allocated small detector regions, called **windows**, for measurements and
transmission to Earth. Rejecting very sharp detector events and broad diffuse
signals helped make autonomous detection practical. A smooth, faint galaxy disk
is therefore much less favored than a compact bright center or a UCD.

The software detects a light pattern, not the object's physical identity. A quasar,
compact galaxy, or galaxy nucleus can enter the catalog if it has a suitable
bright compact component. An extended object need not be perfectly point-like.
Gaia's ground processing can subsequently show departures from a stellar image
or motion model. That is the opportunity this project explores, but also the
reason blends and image problems must be considered. See
[de Bruijne et al. (2015)](https://arxiv.org/html/1502.00454) and the DR3
[extended-object summary](https://doi.org/10.1051/0004-6361/202243940).

### What is Gaia's spatial resolution?

Here spatial resolution means an **angular** separation on the sky, not a
physical length in parsecs. There is no single number that describes detection,
image sampling, resolving two sources, and final catalog completeness.

| Quantity | Useful numerical context | What it means |
| --- | --- | --- |
| Detector pixel sampling | 0.0589 arcsec along the scan; 0.1768 arcsec across it | Angular width of one detector pixel, not the resolving limit |
| Onboard equal-brightness pair resolution | About 0.23 arcsec along the scan and 0.70 arcsec across it in the detection study | Two equally bright point sources can be separated more easily in one direction; unequal brightness can require more separation |
| Published catalog pair completeness | EDR3 validation finds losses below about 1.5 arcsec, becoming severe below about 0.7 arcsec | The catalog does not contain every close pair that the optics could in principle distinguish |

“Along the scan” means the direction an object's image moves across Gaia's
detector; “across” is perpendicular to it. Different visits have different scan
directions. The pixel values are from the
[mission instrument description](https://arxiv.org/html/1609.04153), the detection
numbers from [de Bruijne et al.](https://arxiv.org/html/1502.00454), and the catalog
limits from [Fabricius et al. (2021), Section 2.3](https://arxiv.org/html/2012.06242).
The last result concerns EDR3; DR3 uses the EDR3 astrometric source solution. None
of these pair-separation numbers is a cutoff on UCD half-light radius.

**Positional precision is different:** repeated measurements can locate the center
of a blurred source much more precisely than the width of the blur. Very precise
positions do not mean Gaia resolves individual stars inside a distant UCD. Gaia
normally records their combined light as one source, if it detects that system.

## 3. Apparent brightness is not luminosity

Magnitude tells us how bright something appears in a particular filter. To infer
intrinsic brightness we need distance and, for precise work, extinction and
appropriate photometry. For negligible extinction,

```text
absolute magnitude = apparent magnitude − 5 log10(distance in pc / 10)
```

Use this as a concept, not a Gaia-only UCD definition. Gaia G, Legacy Survey g,
and literature V are different filters. Gaia's measurement of a slightly extended
object may also miss light compared with a total-light measurement. Do not insert
Gaia G into a published V-band classification threshold as though they were the
same measurement. An assumed host distance gives a conditional luminosity, not
independent proof that the source belongs to that host.

## 4. Parallax and proper motion are measurements with uncertainty

Astrometry means measuring positions and how they change. Parallax is the annual apparent positional shift associated with the Earth's
orbit. Proper motion is a change in sky position over time. Gaia reports parallax
in milliarcseconds (mas) and proper motion in mas per year; 1 arcsecond is 1000 mas.
Nearby stars can have measurable values; a distant compact galaxy is expected to
have values far below Gaia's practical precision.

The field `pmra` is the east-west component, including the cosine of declination
so it represents an angular motion on the sky, not simply the change in RA angle.
The field `pmdec` is the north-south component. Both are in mas per year.

For parallax, a useful warning measure is `abs(parallax) / parallax_error`.
A value near one is not convincing evidence for a nonzero parallax. Negative
measured parallaxes can arise from noise and calibration; they are not negative
physical distances. Do not invert an uncertain or negative parallax to estimate
the distance to a UCD.

For the live M60-UCD1 Gaia record, parallax is −0.079 ± 0.395 mas: its absolute
significance is 0.20. Its two proper-motion components are +0.420 ± 0.475 and
−0.547 ± 0.432 mas/year. These are consistent with no detected motion, not proof
of a galaxy. A distant star, QSO, compact background galaxy, or poor measurement
can also have no convincing detected motion.

A missing parallax or motion means Gaia did not supply that measurement. It does
not mean the measurement was exactly zero. The optional combined-motion calculation,
which includes the correlation between the two components, is in the
[instructor record](source_checks.md#optional-significance-calculation).

## 5. Gaia can notice a poor stellar fit

Gaia fits a model to its observations. A source's actual shape, a neighboring
source, orbital motion in a multiple-star system, or other measurement problems
can make a stellar model fit poorly. This is why unusual Gaia measurements can
help find non-stellar objects, but cannot identify UCDs by themselves.

| Field | Plain meaning | What it does not establish |
| --- | --- | --- |
| `ruwe` | Renormalized unit weight error: a normalized measure of the astrometric fit quality | A large value does not uniquely mean extension or a binary |
| `astrometric_excess_noise` | Additional angular scatter used to account for residuals in the astrometric fit, in mas | Not a direct size measurement |
| `astrometric_excess_noise_sig` | Gaia's internal significance statistic for that extra scatter | Not automatically a number of Gaussian standard deviations |
| `phot_bp_rp_excess_factor` | Ratio of summed BP and RP flux to G flux | Not a UCD probability or a universal pass/fail boundary |

These field definitions come from the official
[Gaia DR3 source data model](https://gea.esac.esa.int/archive/documentation/GDR3/Gaia_archive/chap_datamodel/sec_dm_main_source_catalogue/ssec_dm_gaia_source.html).
Further project definitions and limitations are in
[Gaia features](../methods/gaia_features.md). Leave the image-window diagnostics,
machine-learning details, and fit-solution codes to the instructor notes in this
short course.

## 6. Why compare G magnitude with flux excess?

The raw flux-excess factor is

```text
C = (I_BP + I_RP) / I_G
```

Here I means measured flux, not magnitude. BP and RP are Gaia's blue and red
photometric measurements and G is its broad-band measurement. Their response and
measurement regions differ. C is not expected to be exactly one for ordinary
stars; its normal distribution depends on color and measurement quality.

A G-versus-C diagram helps compare a target with the distribution of ordinary
sources. M60-UCD1 has C = 4.65, while the selected foreground comparison has
C = 1.22. That contrast is useful, but extension, crowding, bright host light,
and measurement problems can all affect C. Compare similar-color sources and
inspect images. Do not derive a universal threshold from these two examples or
confuse raw C with a color-corrected excess statistic.

## 7. Matching and provenance are part of the science

The nearest catalog row is not necessarily the intended object. Check the
coordinates, angular separation, image center, nearby alternatives, and coordinate
epoch, the date to which a position applies. A moving star can change position
between surveys. Keep Gaia's long source identifier as text so spreadsheet
rounding does not corrupt it.

*Provenance* means where a claim or measurement came from: the original paper,
table, survey release, source identifier, and matching method. An object name alone
can be ambiguous. Two papers calling an object “UCD1” need not refer to the same
coordinates. Preserve the original source rather than silently correcting it.

## 8. Separate observation, interpretation, and confirmation

- **Observation:** “The image is compact; no convincing motion is measured; the
  Gaia fit is poor; there is nearby host light.”
- **Interpretation:** “It is worth checking as a compact extragalactic candidate,
  but a blend or background source is still possible.”
- **Confirmation:** independent evidence, typically including spectroscopy for
  velocity/association and suitable imaging or other physical characterization.
  The precise classification can remain uncertain even with a measured velocity.

A quasar, also called a quasi-stellar object (QSO), is an active galactic nucleus
that can also appear point-like and have no
detectable motion. An H II region is gas ionized by young stars, often part of a
galaxy rather than an independent UCD. A non-single-star catalog records Gaia
evidence or solutions involving multiple stars. These are possible competing
explanations, not automatic ground truth from a catalog label.

For the class, the required conclusion is a defensible evidence record and a
follow-up recommendation. “Cannot tell from these data” can be the correct answer.
