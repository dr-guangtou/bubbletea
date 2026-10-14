# Student worksheet: a star in disguise?

**Format:** One or two sessions, no coding.  
**Submit:** Your exported activity answers (JSON and readable text), or the completed
PDF. These are observations for instructor review, not UCD confirmations.

[Previous-version activity](ucd_investigation_v1.html) · [Previous-version PDF](ucd_worksheet.pdf) ·
[Background reading](concepts.md) · [Optional online tools](tool_guide.md)

## Before starting

This is the retained version 1 worksheet, not the current Part I activity.
Download `ucd_investigation_v1.html`, then open it in a desktop browser. No server,
installation, account, or internet connection is needed for the embedded data
and images. Save an email attachment before opening it; an email preview may not
run scripts. Optional archive/viewer links need internet. Use a student or group
identifier rather than unnecessary personal information.

Export answers before closing. Automatic browser storage may not work for local
files, private browsing, or restricted computers. An export is a normal download,
not an upload to the instructor. Submit it through the instructor's chosen channel.
To resume, open the same activity and import your own JSON answer file. Do not
edit the catalog data or use another student's answers as an independent review.

## A. Identify and compare

- **Q1.** Explain why searching for UCDs can tell us something about how galaxies
  grow. Give one possible origin, and one thing this exercise cannot establish.
- **Q2.** Inspect M60-UCD1 and the foreground comparison at the available image
  scales (both close and context in HTML; close only in the PDF).
  Record their exact Gaia identifiers and one visible similarity or difference.
  Is the image alone enough to separate a star from a UCD? Explain.
- **Q3.** Calculate `abs(parallax) / parallax_error` for both. State which has
  convincing foreground evidence and cite the motion measurements as well.
  Explain why no detected motion in M60-UCD1 does not confirm a UCD.

## B. Size, measurement, and selection

- **Q4.** M60-UCD1 has a published half-light radius of 24.2 pc at an adopted
  host distance of 16.5 Mpc. Calculate its angular half-light radius using
  `206265 × radius_pc / distance_pc`. Move the activity's distance slider to
  compare 5 and 50 Mpc. What changes, and what stays physically the same?
- **Q5.** Why is Gaia's 0.0589-arcsecond along-scan pixel size not a universal
  resolving limit? Explain angular resolution versus positional precision.
  Must a compact galaxy be perfectly point-like to be detected?
- **Q6.** Compare G and raw flux excess for the foreground star, M60-UCD1, and
  M59-UCD3. Give two alternative explanations for unusual flux excess or poor
  stellar fit. Why can six selected examples not establish a threshold or
  contamination rate?
- **Q7.** Inspect M59cO's catalog panel. Does its missing parallax mean zero
  parallax? What can and cannot be concluded about its motion?

## C. Published-candidate review

Review **candidate A, J124352.42+112534.2**, and
**candidate B, J124524.02+110535.2** independently.

1. Confirm the Gaia identifier and coordinates. Inspect the position marker and
   both image scales; the marker is not proof of a correct association.
2. Record resolved, off-center, close to host light, nearby blend, too faint to
   assess, and image-problem observations. Use **yes / no / uncertain / not
   assessable**, and do not force a judgment.
3. **R1:** Explain the image evidence. A bad Gaia fit alone cannot assign a blend
   or artifact flag. Color alone cannot establish a young cluster or H II region,
   gas ionized by young stars.
4. **R2:** Interpret the astrometry with values/errors or explicit missing values.
   External QSO, galaxy, and non-single-star associations are not checked in this
   packet; “not checked” is not “no match.”
5. Choose **retain for instructor review / possible contaminant / insufficient
   information**. **R3:** Give the reason and next evidence needed. This review
   does not change the research selector or confirm the object.

## D. Reflect and submit

- **Q8.** Identify one uncertainty or possible mismatch and the single most useful
  next observation or catalog check. Separate observation from interpretation.
- Check your identifier and both candidate records. Export JSON to resume or for
  instructor processing, and text for easy reading; alternatively print answers.
- Known controls and candidates remain separate; the six-object plot is not a
  population sample. No answers are sent automatically to a server.
