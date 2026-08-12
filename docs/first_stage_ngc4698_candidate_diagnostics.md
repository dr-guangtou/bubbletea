# First-stage NGC 4698 candidate diagnostics

**Date:** 2026-08-12

**Script:** `scripts/phase3_background/plot_first_stage_host_candidates.py`

**Command:**
`BUBBLETEA_EXTERNAL_DATA=~/Dropbox/work/data uv run python scripts/phase3_background/plot_first_stage_host_candidates.py`

## Distance

The host catalog adopts a distance of 23.933158 Mpc for NGC 4698 from its
Cosmicflows-4 (`CF4`) entry. This is approximately 78.06 million light-years. It is
the distance used to convert every angular separation in this run to projected
kiloparsecs; this summary does not add an independent distance uncertainty.

## What is plotted

The location figure shows all 2,548 Gaia sources that remain after the frozen
point-source contamination selector. The full view reaches 600 kpc, and the second
panel enlarges the central 150 kpc. The gray central circle is the temporary
0--50 kpc contamination region. Point color is Gaia G magnitude, so lower numbers
are brighter objects.

The feature-space figure shows the nine measured inputs used by the frozen
selector:

- astrometric excess noise and its Gaia-reported significance;
- Gaia BP-RP color and the BP/RP flux-excess factor;
- renormalized unit weight error (`RUWE`), a measure of disagreement with Gaia's
  ordinary single-source astrometric fit;
- the percentages of image-processing windows with multiple peaks or nearby-window
  warnings;
- the significance of nonzero parallax and proper motion; and
- explicit feature availability, because the model also records when selected
  measurements are missing.

Gray points were rejected and blue points pass the frozen score threshold. The
scatter-panel display limits are the measured 0.5th and 99.5th percentiles only to
keep extreme archive values from compressing the visible distributions. No rows
are removed from counts or saved analysis outputs. Full feature definitions and
safeguards are in `docs/gaia_selector_features.md`.

## Are there prominent candidates?

There is no strong Gaia-only standout at this stage.

- The passing-source radial density is broadly flat beyond 50 kpc rather than
  forming a clear concentration around NGC 4698.
- Only 18 passing sources lie inside the temporary 50 kpc exclusion. There are 135
  between 50 and 150 kpc, but their density is consistent with the outer profile.
- Of the 2,548 passing sources, 2,421 (95.02%) lack Gaia's five-parameter
  astrometric solution. The corresponding fraction among rejected sources is
  16.31%. Missing astrometry is explicitly handled by the frozen model, but it
  means that many scores near one describe faint or structurally difficult Gaia
  measurements rather than uniquely convincing UCDs.
- Fifty-six passing Gaia entries have another passing entry within two arcseconds.
  Such close pairs merit source-level image review because blends, extended
  objects, and multiple Gaia detections can contribute.
- A high logistic score is not a calibrated probability that an object is a real
  UCD. It means only that its available Gaia measurements resemble the reliable
  UCD training examples more than the priority point-source contaminant examples.

Labels A--E make five examples easy to find in both figures. They were chosen by
transparent rules rather than a new scientific rank:

| Label | Reason shown | Radius (kpc) | G (mag) | Selector score | Initial reading |
| --- | --- | ---: | ---: | ---: | --- |
| A | Nearest passing source outside 50 kpc | 52.421 | 21.577 | 0.997375 | Faint; five-parameter astrometry unavailable |
| B | Highest score from 50--75 kpc | 55.930 | 21.478 | 0.999998 | Faint; five-parameter astrometry unavailable |
| C | Highest score from 75--100 kpc | 94.517 | 21.492 | 0.999995 | Faint; five-parameter astrometry unavailable |
| D | Highest score from 100--150 kpc | 146.761 | 21.544 | 0.999991 | Faint; five-parameter astrometry unavailable |
| E | Brightest passing source from 50--150 kpc | 127.149 | 16.233 | 0.974892 | Strong nonzero motion and parallax; not a clean UCD candidate |

Example E illustrates why a high score is insufficient: it has `RUWE = 13.123`,
proper-motion significance 48.468, and absolute-parallax significance 9.069. Those
measurements make a foreground star, blend, binary, or another poor-fit source more
plausible than a straightforward NGC 4698 UCD despite the fitted selector score.
Examples A--D instead owe much of their high score to strong excess noise combined
with missing five-parameter astrometry and require imaging before interpretation.

The exact coordinates and Gaia source identifiers for all five examples are stored
in `data/results/background/first_stage_ngc4698_candidate_review_v1.csv`. This table
is a plot-audit aid, not a follow-up priority list.

## Artifacts

- `figures/phase3/first_stage_ngc4698_candidate_locations.png`
- `figures/phase3/first_stage_ngc4698_candidate_locations.md`
- `figures/phase3/first_stage_ngc4698_selector_feature_spaces.png`
- `figures/phase3/first_stage_ngc4698_selector_feature_spaces.md`
- `data/results/background/first_stage_ngc4698_candidate_review_v1.csv`
- `data/results/background/first_stage_ngc4698_candidate_diagnostics_v1.json`

All seven diagnostic checks pass. No selector threshold, radial boundary, or
candidate-ranking rule was changed.
