# Science guide: what we measure and what the evidence means

[Current status](current_status.md) · [Roadmap](PLAN.md) · [Scientific requirements](SPEC.md)

## The project in one paragraph

BubbleTea searches Gaia for compact stellar systems around nearby galaxies,
especially ultra-compact dwarf galaxies (UCDs). These can be brighter or larger
than ordinary globular clusters while remaining barely resolved in survey images.
The primary question is whether a reproducibly selected population shows an excess
around a galaxy relative to unrelated foreground and background sources. A passing
source, a catalog label, and an excess are three different kinds of evidence;
none alone confirms a new UCD.

## 1. Establish a reliable reference

Published records are associated with distinct objects without discarding their
source provenance or uncertain classifications. The full database and the smaller
visual-review reference have different scopes. Literature-confirmed objects can
still have incorrect classifications or incorrect Gaia counterparts, so reference
review records evidence rather than treating every published label as infallible.

Read the [review rules and available evidence](methods/reference_review.md),
[reference-image preparation](development/reference_imaging.md), and the
[workbench specification](plans/ucd_visual_review_tool.md).

## 2. Select sources using Gaia alone

The baseline is a frozen logistic-regression selector: a statistical rule combining
nine Gaia measurements, with explicit handling of missing values. “Frozen” means
its inputs, fitted parameters, and selection threshold are fixed so the reference,
random fields, and galaxy profiles use the same rule. Its output is a selection
score, not a calibrated probability of physical UCD identity.

Removing ordinary stars, non-single or binary stars, and QSOs is the first priority.
Extended galaxies are secondary and can require ancillary imaging. H II regions
and young clusters need separate evidence; blue color alone cannot assign a visual
star-forming-region flag.

- [Gaia features, significance calculations, and ROC AUC](methods/gaia_features.md)
  explain the measurements and diagnostic plots in plain language with Gaia references.
- [Contaminant samples](methods/contaminant_samples.md) explain how each comparison
  population was assembled and how its selection could bias performance estimates.
- [Extragalactic catalogs](methods/extragalactic_catalogs.md) explain why candidate
  membership is not a truth label or a universal veto.
- [Selector development and independent validation](development/selector_experiments.md)
  retain the measurements, rejected alternatives, and frozen version-1 implementation.

Balanced benchmark contaminant fractions do not predict purity in real fields.
The real-field contamination rate must be measured with representative samples,
not inferred from an intentionally selected collection of known objects.

## 3. Measure a radial profile, not just one count

Keep every source's separation from the host and summarize it in concentric circular
annuli, meaning rings sharing the same center. Where a verified half-light radius
is available, also express separations relative to that galaxy size. Preserve the
physical-kiloparsec profile when size information is missing.

The inner galaxy region is set aside for UCD inference because galaxy light,
substructure, compact young clusters, and H II regions can dominate. The first-stage
0--50 kpc exclusion and 600 kpc retrieval reach are conservative working geometry,
not final universal scientific limits. Gaia area comes from verified completed
retrieval strips, not external-imaging masks.

Read [radial definitions and limits](methods/radial_measurements.md),
[retrieval and area checks](development/retrieval_and_area.md), and
[NGC 4698/M60 measured profiles](development/host_pilot_profiles.md).

## 4. Measure unrelated sources directly

The primary large-sky comparison is a distribution of measured selected-source
densities in random fields at similar Galactic latitude. Its median, mean, and
central ranges preserve real variation among fields. A fitted sky-density model is
only a diagnostic; it does not replace an available measurement.

A valid local outer annulus must be reported alongside the random-field comparison,
including their difference and ratio. A region inside the relevant galaxy or group
population cannot simply be called background. Missing or invalid coverage means
unavailable evidence, not a density of zero.

Read [background comparisons and reserved-field validation](development/background_measurements.md),
[small off-target experiments](development/off_target_controls.md), and
[environment and geometry history](development/background_geometry.md).
The final host-specific background treatment and complete excess uncertainty
remain open; measured profiles are not automatically significant detections.

## 5. Review images without changing the frozen experiment

Legacy Survey images and catalog fits help identify counterparts, learn what UCDs
look like at different distances, and flag possible contamination. Their
availability must not redefine Gaia's statistical sample or usable area.
During the first M60 pass, possible contaminants are flags, not automatic removals.

The next research action is reference review, followed by the representative M60
contamination sample. A clean reference can support a separately validated future
selector; it does not retroactively alter frozen validation results.

## Where detailed records belong

This page is the scientific reading map. SPEC owns approved requirements; current
status owns the dated restart summary. Permanent definitions are in `methods/`.
Development experiments, benchmarks, failures, and reproducibility details are
in topic-organized `development/` records. Journals preserve dated sessions.
The [documentation guide](documentation_guide.md) explains these responsibilities;
the [consolidation audit](development/documentation_audit.md) maps retired documents.
