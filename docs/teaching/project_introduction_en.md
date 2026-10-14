# A Galaxy in Disguise

**Project Introduction | BubbleTea, Part I | Observational Astronomy**

## Why look for a galaxy that resembles a star?

An ultra-compact dwarf galaxy (UCD) is a compact stellar system near the boundary
between very massive star clusters and small galaxies. Its light comes from many
stars, but at a large distance it can resemble a single star in an image. Some
UCDs may be the surviving centers of larger galaxies stripped by gravitational
interactions; others may have formed as unusually massive star clusters. Their
origins are part of the research question, not settled by their name.

These small objects can reveal a much larger history. Detailed observations of
M60-UCD1 found a massive black hole, supporting an origin in a larger galaxy.
The evidence went far beyond its appearance in a photograph.
[Seth et al. (2014)](https://arxiv.org/abs/1409.4769)

The UCD census remains incomplete. Much of the search effort has concentrated
on galaxy clusters and groups. Could less-studied massive galaxies host
overlooked UCDs? How common are they around disk galaxies, or in less crowded
environments? These are motivations for this semester's project, not a promise
that any particular galaxy will contain a detectable UCD or that we will make a
new discovery. The HTML lesson provides examples and further reading.

## Two complementary views of the sky

**Gaia** repeatedly scanned the sky, recording positions, brightnesses, colors,
parallaxes, and proper motions. It detected compact concentrations of light,
not only objects already known to be stars. Compact galaxies and quasars can
therefore also have Gaia records. Small detector pixels, the ability to separate
two sources, and precision in measuring a position are different concepts.
[ESA: Gaia](https://www.esa.int/Science_Exploration/Space_Science/Gaia)

**Legacy Survey images** provide a complementary view of an object's appearance
and surroundings. Atmospheric and instrumental blur can make a small object
look point-like. The same physical object also looks smaller at greater
distance. A color picture is a display, not a substitute for measured fluxes or
colors. This activity combines saved Gaia DR3 records and Legacy Survey DR11
images. [Legacy Survey DR11](https://www.legacysurvey.org/dr11/description/)

## Getting started

Save `ucd_investigation.html` to your computer and open it in a desktop browser,
not an email or course-platform preview. All required data, images, and
interactive tools are inside that one file. No coding, installation, account,
local server, or internet connection is required for the core tasks. Optional
online exploration requires internet access.

Begin with the background, illustrations, measurement definitions, and labeled
examples. The core reading is designed for about 30 minutes; allow additional
time for the investigation. This is **Part I** of a semester project. Searching
for new candidates comes later; it is not a requirement of this assignment.

<!-- pagebreak -->

## Your investigation

The aim is to connect observations with physical interpretations, test a
selection rule on real data, and explain both its usefulness and its limits.
Use the examples to develop your own reasoning rather than seek a perfect
shortcut. Definitions and optional tool instructions are available in the HTML.

### Task 1 | Classify 30 objects

Inspect each object's close and wider images, Gaia measurements, and available
links. Choose **UCD, star, QSO (quasar), or uncertain** for every object. Only the
classification is required. Confidence, evidence used, a short explanation, and
external citations are optional but useful records of your reasoning. You can
revisit and change your choices; the activity does not reveal the answers.

Read values together with their uncertainties. “Not supplied” is not zero.
Distinguish what the observations show from what you infer. If you consult an
online catalog, check that you are looking at the same source. The expandable
guide explains Gaia Archive, Legacy Survey, and Aladin exploration; online
checks are optional, not extra required deliverables.

### Task 2 | Design and improve a selection rule

Explore the interactive plots of **21,118 real catalog objects** in a deliberately
star-rich sample. Enable measurement ranges, adjust their limits, and decide
how to handle missing measurements. Every enabled condition must be satisfied.
Press **Evaluate selection** to record a trial and see its selected objects and
scores; changing a slider alone does not evaluate a new trial.

- **Completeness:** the fraction of reference UCDs recovered by your rule.
- **Purity:** among selected objects with secure reference classes, the fraction
  that are UCDs rather than stars or QSOs.
- **F1:** a combined score, the harmonic mean of purity and completeness. Try to
  improve it while inspecting the counts and the two component scores.

Unconfirmed candidates are counted separately and do not enter these scores.
The sample is constructed for teaching: scores after repeated tuning do not
establish performance in a new sky field. A high score does not confirm an
individual candidate as a UCD. Perfect separation is not the expectation.

Try different rules, compare the recorded attempts, then choose **one evaluated
attempt** as your final selection. Complete both explanations in the page:

- Why do you think this works?
- How do you think this selection can be improved?

### Task 3 | Establishing membership

Answer the following question in the page. Your response will provide a
starting point for Part II:

**You find a possible UCD close to a massive galaxy on the sky. How would you
investigate whether it is physically associated with that galaxy?**

<!-- pagebreak -->

## What to deliver

Submit **one JSON answer file** exported from the HTML activity. It contains your
Student ID, the 30 Task 1 responses, Task 2 trial history and final selection
with both explanations, the Task 3 answer, and your brief LLM-use disclosure.
There is no separate report, screenshot collection, code, or discovery claim
required for Part I. The optional TXT export is for convenient reading and
does not replace the JSON submission.

### Save, check, and submit

1. Under **Keep a record**, enter your **Student ID**. Complete the LLM-use
   declaration. If you used an LLM, briefly say how it helped and what you verified.
2. Check that all 30 objects have a classification, one evaluated Task 2 attempt
   is chosen as final, both selection explanations are filled in, and Task 3
   has an answer. “Uncertain” is a valid classification, not a blank response.
3. Click **Download answers · JSON**. Find the downloaded file and rename it to
   **`[NAME]_[STUDENT_ID].json`**. Replace NAME with your name and STUDENT_ID
   with your student ID; remove the square brackets and retain `.json`.
4. Upload that JSON file to **网络学堂 (Tsinghua Online Classroom)** in the
   assignment specified by your instructor. Check that the upload succeeded.
   Follow the course announcement for the deadline.
5. Keep a local copy of your final JSON and the exact HTML used to create it.

The webpage asks only for Student ID; your name belongs in the submission
filename. On systems that hide file extensions, avoid accidentally adding
`.json` twice. Downloading the file does **not** upload it to 网络学堂.

### Keep your work safe

Download JSON early and after important changes, even if your work is
incomplete. Browser draft storage is convenient but not a dependable backup;
moving the HTML or changing browsers may make the draft unavailable. The
downloaded HTML itself does not acquire your answers.

To continue later, open the same HTML and choose your saved JSON under
**Resume from a saved JSON file**. Import replaces the current answers, so
export any work you want to retain first. Renaming the JSON does not alter its
contents. Do not edit the JSON by hand. After further changes, download a new
JSON and submit that final version, not an earlier draft.

### Responsible use of LLMs

LLM assistance is allowed and encouraged when used thoughtfully. It can help
explain a concept, organize an investigation, or suggest checks, but its
confident wording is not observational evidence. Verify factual claims against
the supplied measurements and reliable sources. Your submitted choices and
explanations should reflect what you actually checked. Provide a brief
disclosure; no private chat transcript is requested.

**The goal:** a reproducible record of your decisions, a tested selection rule,
and a thoughtful question about physical association. Those are the foundations
for the next stage of the project.
