# Point-source astrometric rejection assessment, version 1

## Question

Can a simple Gaia motion rule remove additional stars and QSOs after the frozen
point-source selector, without losing too many reliable ultra-compact dwarfs
(UCDs)?

Here, **astrometric significance** means how far a measured parallax or proper
motion lies from zero after accounting for its reported uncertainty. A distant UCD
should have effectively zero parallax and proper motion, so a large value can be
evidence for a foreground star. However, Gaia can also report misleading motion for
a barely resolved source whose changing image shape shifts its measured center.

The tested second rule uses the larger available value from:

- absolute parallax divided by its uncertainty; and
- the two-dimensional proper-motion distance from zero, including the reported
  correlation between the two proper-motion components.

A source is rejected only when that value is strictly above the trial boundary. If
one measurement is missing, the other can still be used. If both are missing, the
rule does not reject the source.

## Scope and safeguards

The contract in
`data/literature/sources/point_source_astrometric_rejection_assessment_v1.json`
was committed before the measurements were calculated. The analysis uses only the
benchmark-v3 development sample and the ordinary-star development supplement. It
applies `point_source_logistic_model_v1` and its frozen threshold first. It does not
inspect validation data, change selector version 1, use the NGC 4698 star to choose
a boundary, or select a new operating point automatically.

The measured sample contains 146 reliable UCDs, 438 ordinary spectroscopic stars,
1,125 Gaia non-single stars, and 403 spectroscopic QSOs. Galaxies and H II regions
are reported as secondary checks. At least one usable motion measurement exists for
69/146 UCDs, 306/438 ordinary stars, 1,125/1,125 non-single stars, and 321/403 QSOs.

## Measured result

| Treatment | Reliable UCDs passing | Ordinary stars passing | Gaia non-single stars passing | QSOs passing | Equal-weight priority-contaminant fraction |
| --- | ---: | ---: | ---: | ---: | ---: |
| Selector version 1 alone | 135/146 (92.47%) | 13/438 (2.97%) | 0/1,125 (0.00%) | 8/403 (1.99%) | 1.651% |
| 3-standard-deviation reference | 131/146 (89.73%) | 12/438 (2.74%) | 0/1,125 (0.00%) | 7/403 (1.74%) | 1.492% |
| First measured boundary retaining at least 90% of all UCDs: 7.0397 | 132/146 (90.41%) | 13/438 (2.97%) | 0/1,125 (0.00%) | 8/403 (1.99%) | 1.651% |

The 3-standard-deviation reference removes four UCDs that selector version 1 had
retained, while removing one retained ordinary star and one retained QSO. At every
measured boundary that preserves the historical goal of at least 90% reliable-UCD
retention, the priority-contaminant fraction is unchanged from selector version 1.
The full 1,885-boundary curve is preserved in
`data/literature/validation/point_source_astrometric_rejection_curve_v1.csv`.

Five reliable UCD associations exceed 3 standard deviations. All five are from the
Voggel et al. (2020) NGC 5128 catalog (`2020ApJ...899..140V`) and retain the
project's high-confidence spectroscopic classification. Four pass selector version
1 and would be newly removed at the 3-standard-deviation reference; one is already
below the selector threshold. Their Gaia identifiers, coordinates, source rows,
selector scores, and motion measurements are preserved in
`data/literature/validation/point_source_astrometric_rejection_ucd_review_v1.csv`.
This shared origin makes extended-source astrometric corruption a plausible
explanation and does not provide evidence that their published UCD classifications
are wrong.

## Recommendation for review

Do not add a universal hard astrometric rejection boundary to the shared selector.
In this development sample it cannot improve priority-contaminant rejection while
maintaining the project's 90% UCD-retention goal. Preserve parallax and
proper-motion significance as explicit warning flags instead: a high value should
trigger individual imaging and literature review, as the NGC 4698 stellar example
demonstrates, but should not by itself erase a source from the candidate list.

The project lead should review
`figures/phase1/point_source_astrometric_rejection_tradeoff_v1.png` and approve or
reject this no-hard-boundary recommendation before the shared selection workflow is
changed.
