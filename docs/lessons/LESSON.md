# Lessons Learned - UCD Search Project

## 2026-07-14: Parse CDS fixed-width tables from their byte specification

**Lesson:** Whitespace splitting is unsafe for CDS fixed-width tables because
optional blank fields shift all later values without changing the apparent row.

**Context:** The multi-position Gaia audit initially split Fahrion table B1 rows
and encountered a shifted reference-code value before producing review results.

**Recommendation:** Parse columns using the published one-based byte ranges in
the VizieR `ReadMe`, and validate expected types before scientific comparison.

## 2026-07-14: Validate the documented direct script command

**Lesson:** A script that imports the repository's `scripts` namespace can pass
static checks but fail when invoked by its documented file path because Python
places the script directory, rather than the repository root, on `sys.path`.

**Context:** The one-target Gaia image-ambiguity audit failed before retrieval
when run with the required `uv run python scripts/phase1_literature/...` command.

**Recommendation:** Exercise the exact documented command during small-scale
validation and add a minimal repository-root bootstrap to standalone scripts that
use absolute project imports.

**Date:** 2026-03-27
**Project Duration:** ~11 days (Mar 16 - Mar 27, 2026)

---

## Executive Summary

This document captures key lessons learned during the UCD search project exploration phase. These insights should guide future work and prevent repeating mistakes.

---

## 1. Data Access & Infrastructure

### 1.1 Gaia TAP Queries

**Lesson:** Gaia archive has strict query limits requiring careful pagination.

- **Issue:** `OFFSET` pagination is NOT supported by Gaia TAP service
- **Solution:** Use `TOP` with iterative queries, or accept row limits and design queries to be selective
- **Best Practice:** Design queries to return < 50,000 rows per query; use ADQL `TOP` clause

**Lesson:** `astroquery.gaia` requires proper user authentication for large queries.

- **Issue:** Anonymous queries have stricter rate limits
- **Solution:** Configure `Gaia.login(user=..., password=...)` for production queries
- **Best Practice:** Use asynchronous queries (`upload_table`, `launch_job`) for large requests

### 1.2 Legacy Survey Cross-Match

**Lesson:** NOIRLab Data Lab provides the best access to Legacy Survey DR10.

- **Issue:** Legacy Survey not available on VizieR for cross-matching
- **Solution:** Use Data Lab TAP service with `q3c_join` for spatial matching
- **Best Practice:** Start with Data Lab for any Legacy Survey work

**Lesson:** Multiple cross-match methods were explored before finding optimal one.

- **Explored:** CDS XMatch, astroquery.vizier, NOIRLab Data Lab, direct HTTP requests
- **Final Choice:** Data Lab TAP with box search - best balance of speed and reliability
- **Recommendation:** Start with Data Lab for any Legacy Survey work

### 1.3 VizieR Catalog Ingestion

**Lesson:** VizieR table formats vary significantly across catalogs.

- **Issue:** Column names, units, and data types are not standardized
- **Solution:** Build flexible parsers that handle format conventions
- **Best Practice:** Always verify column names from the VizieR ReadMe before parsing

**Lesson:** VizieR download limits require chunking for large catalogs.

- **Solution:** Use `ROW_LIMIT` parameter or download via FTP for large catalogs
- **Best Practice:** Check catalog size before downloading; use async methods

---

## 2. Selection Criteria Development

### 2.1 AEN as Primary UCD Indicator

**Key Finding:** Astrometric Excess Noise (AEN) is the most reliable single indicator for UCD identification.

| Metric | UCDs | Background | Ratio |
|--------|------|------------|-------|
| Median AEN | 3.95 mas | 1.73 mas | 2.3x |
| 25th %ile | 3.42 mas | 1.00 mas | 3.4x |

**Lesson:** Color (BP-RP) does NOT distinguish UCDs from background.

- Both UCDs and background sources have BP-RP ~ 1.3 (old stellar populations)
- Use AEN and morphological classification instead

**Recommendation:** Consider raising AEN threshold from 0.5 mas to 2.0-3.0 mas for improved S/N.

### 2.2 Proper Motion Filtering

**Lesson:** Proper motion selection must balance completeness vs. purity.

- **Original:** Hard cut at PM < 2.92 mas/yr
- **Issue:** Some UCDs have uncertain PM measurements
- **Better:** Accept if PM is NULL OR PM_S/N ≤ 3.0 OR PM < 2.92 mas/yr

**Result:** Prioritize completeness over purity for initial candidate selection.

### 2.3 classprob_galaxy Reliability

**Lesson:** Gaia's `classprob_dsc_combi_galaxy` is statistically useful but unreliable for individual objects.

| Metric | UCDs | Background |
|--------|------|------------|
| Median | 0.95 | 0.00 |
| > 0.5 fraction | 72% | 12% |

**Recommendation:** Use as soft prior, NOT as hard cut.

---

## 3. Background Characterization

### 3.1 Galactic Latitude Dependence

**Critical Finding:** Background density varies by 10x with galactic latitude.

| \|b\| Range | Density (/deg²) | Std Dev |
|-------------|-----------------|---------|
| 20-30° | ~600 | 300 |
| 30-40° | ~230 | 94 |
| 40-50° | ~90 | 29 |
| 50-60° | ~85 | 10 |
| 60-70° | ~70 | 11 |
| 70-90° | ~60 | 19 |

**Lesson:** Local background estimation is ESSENTIAL for each target galaxy.

- Cannot use single global background estimate
- Must estimate from outer annulus around each galaxy (r > 150 kpc)

### 3.2 Nature of Background Sources

**Analysis:** Sources passing UCD selection are primarily:

| Component | Fraction | Cause |
|-----------|----------|-------|
| Binary stars | 50-60% | High AEN from orbital motion |
| Unresolved galaxies | 20-30% | Extended appearance |
| Poorly-fit stars | 10-20% | Near detection limits |

**Lesson:** Background contamination is unavoidable; focus on signal excess, not purity.

---

## 4. Radial Search Methodology

### 4.1 Validated Approach

1. Divide search area into concentric annuli (in kpc, not degrees)
2. Count candidates in each bin, normalize by area
3. Estimate background from outer annulus (r = 150-300 kpc)
4. Calculate excess and significance in inner bins

**Key Metric:** Contrast = Inner density / Background density

| Contrast | Interpretation |
|----------|----------------|
| > 10x | High-confidence detection |
| 2-10x | Detection |
| < 2x | Non-detection |

### 4.2 Angular Scale

**Lesson:** Always convert angular to physical scales using galaxy distance.

- Radial bins in kpc, not degrees
- Background annulus: 150-300 kpc
- Maximum search radius: ~300 kpc

---

## 5. Project Organization

### 5.1 Version Control

**Problem:** Many intermediate script versions created during exploration.

**Lesson:** Establish naming convention early:

- `script_v1.py`, `script_v2.py`, `script_v3.py` for versions
- Mark final clearly (`script_final.py` or just `script.py`)
- Archive intermediate versions promptly

**Recommendation:** Create `_archive/` subdirectory for obsolete scripts.

### 5.2 Documentation

**What worked well:**
- `notes/` directory with markdown files per analysis stage
- `manifest.json` for database statistics
- Clear schema documentation

**What could improve:**
- Session-level logs of decisions made
- Linking scripts to their outputs

### 5.3 Database Design

**Lesson:** SQLite is sufficient for ~1,500 objects.

**Design Principles:**
- Separate tables for sources, objects, photometry
- Full provenance tracking (source_id, date_added, added_by)
- JSON for flexible metadata

---

## 6. Technical Pitfalls

### 6.1 Coordinate Systems

**Issue:** Multiple coordinate systems across catalogs.

| System | Use Case |
|--------|----------|
| J2000 equatorial (RA, Dec) | Primary storage |
| Galactic (l, b) | Background estimation |
| Ecliptic | Occasionally encountered |

**Best Practice:** Store in J2000 equatorial, convert as needed.

### 6.2 Magnitude Systems

**Issue:** Vega vs. AB magnitudes.

| Survey | System |
|--------|--------|
| Gaia | Vega |
| Legacy Survey | AB (flux-based) |
| SDSS | AB |

**Best Practice:** Document magnitude system; convert to consistent system for analysis.

### 6.3 Cross-Match Radius

**Recommendation:** 1 arcsec is conservative but safe.

- Gaia astrometric precision: ~0.1 mas for bright sources
- Legacy Survey astrometry: ~0.1 arcsec
- UCD sizes: 0.1-0.5 arcsec at 15-20 Mpc

---

## 7. Collaboration Workflow

### 7.1 Agent-Human Interaction

**What worked:**
- Clear scientific questions from Dr. Guangtou
- Iterative refinement of criteria
- Regular check-ins on direction

**What improved:**
- Better astronomical context understanding
- More autonomous exploration within scope

### 7.2 Knowledge Persistence

**Issue:** Re-learning project context each session.

**Mitigation:**
- Comprehensive documentation
- `manifest.json` and `README.md` as quick-start
- Clear file naming conventions

---

## 8. Recommendations

### 8.1 Immediate

1. Confirm archival decisions with Dr. Guangtou
2. Create `_archive/` directories
3. Update README with current active scripts

### 8.2 Technical

1. Raise AEN threshold to 2.0-3.0 mas for better S/N
2. Implement local background estimation for all galaxies
3. Use classprob_galaxy as soft prior only

### 8.3 Organizational

1. Archive obsolete scripts promptly
2. Maintain session-level notes
3. Update manifest.json after major changes

## 2026-05-11: Morphology of Nearby Galaxies

**Lesson:** Do NOT use Legacy Survey object types (`REX`, `SER`, `DEV`, `EXP`) to characterize the morphology of nearby large galaxies ($D < 25\text{ Mpc}$).
**Context:** In the Legacy Survey's `tractor` processing, these nearby large galaxies are often "shredded" into many individual pieces rather than being represented by a single object. Consequently, the assigned morphological type of any one piece does not reflect the global morphology of the galaxy.
**Recommendation:** Use primary identifiers (NGC, IC, PGC) to retrieve reliable Hubble classifications and T-types from established databases like NED or HyperLEDA.

- AEN is the primary UCD discriminator
- Background varies 10x with galactic latitude
- Local background estimation is essential
- PM filtering must prioritize completeness

**Technical lessons:**
- Data Lab is best for Legacy Survey access
- VizieR formats vary - build flexible parsers
- SQLite is adequate for this scale

**Organizational lessons:**
- Version control and archival are essential
- Documentation pays dividends
- Clear naming conventions save time

## 2026-07-14: Validate documented script invocation

**Lesson:** A script that imports `scripts.config` does not resolve the repository
package when invoked by file path unless the repository root is on `PYTHONPATH`.
**Context:** The first literature-audit dry run failed before reading the database
because its documented direct-file command omitted `PYTHONPATH=.`.
**Recommendation:** Run and time the exact documented command on the smallest local
case before publishing it; use `PYTHONPATH=.` for the current direct-file pattern.

## 2026-07-14: Treat source metadata as evidence requiring verification

**Lesson:** A syntactically valid bibcode, source-wide distance, or confirmation
label can still describe the wrong paper, a heterogeneous compilation, or an
ingestion default rather than the object.
**Context:** ADS and VizieR checks corrected two legacy bibcodes, distinguished the
Centaurus galaxy cluster from Centaurus A, and exposed compilation-wide distances
and labels that were unsafe to normalize.
**Recommendation:** Preserve original values in immutable raw payloads, verify
bibliographic identifiers against authoritative services, and queue uncertain
normalized metadata for review rather than silently propagating it.

## 2026-07-14: Separate broad selection pools from positive references

**Lesson:** A catalog of objects considered during photometric selection is not
equivalent to a catalog of reported candidates or confirmed reference objects.
**Context:** Saifollahi et al. table A5 contains 1,155 classified UCD/GC selection
objects, while table A6 contains the final 44 unconfirmed UCD candidates and table
A1 reproduces 61 operational spectroscopic reference UCDs from a mixed sample.
**Recommendation:** Store broad selection pools separately, link final candidates
back to their source rows, and encode paper-specific reference criteria explicitly
without promoting reported confirmation automatically.

## 2026-07-14: Audit object labels below the table-title level

**Lesson:** A table described as UCD candidates can contain explicit non-UCD or
contaminant rows, while rows absent from direct source membership may already be
represented through a later literature compilation.
**Context:** The Liu M49 and M60 candidate tables contain 51 rows flagged as UCDs
and 28 rows explicitly flagged as non-UCDs. All 51 positive rows already have
sub-arcsecond v2 counterparts through existing provenance, whereas the 28
non-positive rows do not.
**Recommendation:** Join paired source tables, preserve object-level flags, and
measure exact and spherical overlap before changing canonical membership or
interpreting a table-wide role as a positive label.

## 2026-07-14: Omit unsupported optional reader arguments

**Lesson:** Passing `None` to an optional library argument is not always equivalent
to omitting that argument.
**Context:** The Astropy CDS reader expects `fill_values` to be iterable when the
keyword is present, so a shared table loader failed when it forwarded
`fill_values=None`.
**Recommendation:** Build optional keyword arguments explicitly and pass them only
when a concrete value is required; exercise both the default and specialized paths
in the small-scale check.

## 2026-07-14: Never use opaque identifier order as provenance routing

**Lesson:** A deterministic ordering can still encode the wrong relationship when
it has no scientific or provenance meaning.
**Context:** After adding multiple datasets per publication, unmatched raw files
fell back to UUID-sorted dataset order and attached legacy primary tables to new
supplemental datasets.
**Recommendation:** Route exact and paired tables explicitly, then use the declared
legacy-normalized dataset as the semantic fallback; audit the resulting file-to-
dataset row counts after every multi-table ingestion change.

## 2026-07-14: Run namespace-importing scripts as modules

**Lesson:** A standalone research script that imports from the repository's
`scripts` namespace is not directly executable by file path unless the project
root is added to Python's import path.
**Context:** Running `uv run python scripts/phase1_literature/build_reference_database.py`
failed before the build began because Python could not resolve `scripts.config`.
**Recommendation:** From the project root, run namespace-importing scripts with
`uv run python -m scripts.phase1_literature.<module_name>`, and keep imports
between phase scripts fully qualified under the same namespace.

## 2026-07-14: Inspect pre-commit scope before repository-wide runs

**Lesson:** A repository-wide auto-fixing hook can mutate frozen legacy notebooks
and unrelated phase scripts when its file exclusions do not match project policy.
**Context:** `pre-commit run --all-files` applied Ruff fixes and formatting to
unrelated tracked files before failing on known legacy findings; those hook-only
edits were immediately restored.
**Recommendation:** Audit hook include/exclude rules before an all-files run and
use targeted Ruff checks for scoped work until frozen and archived paths are
excluded from auto-fixing hooks.

## 2026-07-14: Recompute catalog distances on the sphere

**Lesson:** A nearest-neighbor identifier can be correct while its stored distance
is geometrically inconsistent.
**Context:** The legacy Gaia matcher ranked degree-space offsets without the
right-ascension cosine factor. Across 280 proposal endpoints, the largest measured
difference from an authoritative great-circle separation was 0.176110481759
arcseconds.
**Recommendation:** Use `SkyCoord.separation` for validation, preserve legacy
distances only as provenance, and assess shared-source identity separately from
Gaia blending and catalog-role conflicts.

## 2026-07-14: Apply review routing after proposal eligibility

**Lesson:** Repeated identifiers do not necessarily imply a non-exact association
proposal when every associated row has identical coordinates.
**Context:** A Gaia review-routing assertion initially ran before exact-coordinate
pairs were filtered and rejected an identifier that correctly had no proposal.
**Recommendation:** Construct the eligible non-exact pair set first, then require
review metadata only for groups that actually produce proposals.

## 2026-07-14: Validate relationships independently of a primary method label

**Lesson:** A one-to-many scientific relationship cannot always be reconstructed
from a single-valued association-method field after canonical groups are merged.
**Context:** Two exact-coordinate companion groups remained intact after approved
Gaia merging, but their moved rows correctly acquired the Gaia association method,
causing a method-filtered duplicate check to report false loss.
**Recommendation:** Validate exact-coordinate preservation directly from immutable
row coordinates and shared canonical membership, while treating the association
method as the reason for the latest non-exact merge.
## 2026-07-15: Run the builder smoke check after adding new digest logic

**Lesson:** A new Wave 1 package-digest path referenced `hashlib` before its import
was added; Ruff and the temporary-database smoke build caught the error before the
production v2 database was replaced.

**Context:** The literature builder recreates its output database, so new ingestion
paths must first target a disposable database even when prior builds are fast.

**Recommendation:** Run Ruff followed by a timed build to a temporary output path
after changing imports, package hashing, or ingestion orchestration, and only then
rebuild the configured v2 product.

## 2026-07-15: Do not probe a guessed SQLite path

**Lesson:** Opening a nonexistent path with the SQLite command-line client creates
an empty database even when the intended operation is read-only.

**Context:** A diagnostic schema query used a guessed v2 filename instead of the
configured `LITERATURE_REFERENCE_DB_V2` path and created a zero-byte ignored file.
The file was detected immediately, was never read by the audit, and was removed.

**Recommendation:** Resolve database paths from `scripts/config.py` before running
SQLite diagnostics, assert that the file exists, and use immutable or read-only
connection modes for inspection.

## 2026-07-15: Audit catalog lineage before treating a nearby row as unlinked

**Lesson:** A coordinate-designated record can retain its identity alias only in
an original table's secondary-name column, so normalized database names alone may
make a documented cross-identification appear absent.

**Context:** Seventy-two Wave 1 groups initially contained an "unreferenced" Liu or
Fahrion canonical. Liu 2015 table 3 preserved the Zhang/Ko identifier in `Other`,
and the exact NGVS catalog key connected the records without a positional rule.

**Recommendation:** Before routing a nearby canonical to manual ambiguity, inspect
source-specific alias columns and stable catalog keys across predecessor and
successor tables.

## 2026-07-15: Connected proximity groups can contain more than one identity

**Lesson:** A connected review component is not necessarily one astrophysical
object even when every member has an identifier edge.

**Context:** S547 and VUCD3 share an unresolved Gaia source and occur in one
sub-arcsecond component, but Fahrion preserves different positions, references,
magnitudes, and sizes. Source identifiers correctly split the component into two
identities.

**Recommendation:** Resolve identity at the identifier-edge subgroup level and
carry explicit retained-separate decisions through any group-level consolidation.

## 2026-07-15: Recheck authoritative flags even when row linkage is correct

**Lesson:** Correctly linking a supporting table does not prove that normalized
labels inherited from a legacy database match the authoritative primary table.

**Context:** Liu's 127 M87 rows were correctly paired with their structural and
velocity rows, but the legacy import had set all 127 to UCD. The authoritative
primary table contains 92 `UCD=1` and 35 `UCD=0` rows.

**Recommendation:** Validate identity, row role, and every selector-facing
normalized field as separate invariants against the authoritative source row.

## 2026-07-15: A reviewed confirmation can end in non-promotion

**Lesson:** Closing a confirmation review does not require promoting the object.

**Context:** Voggel's 57 previously confirmed comparison rows carry Gaia
photometry in the local table but not the spectroscopy or resolved morphology
required by `confirmation_rules_v1`. They remain candidates with an explicit
reviewed-insufficient-evidence decision.

**Recommendation:** Represent approval, non-promotion, and unresolved review as
distinct evidence states so absence of local qualifying evidence is not confused
with either rejection or unfinished work.

## 2026-07-15: Validate catalog-service geometry against the live endpoint

**Lesson:** Standards-compliant ADQL geometry syntax is not necessarily supported
by a service that exposes a TAP endpoint.

**Context:** NOIRLab Data Lab rejected `CONTAINS(POINT, CIRCLE)` with a PostgreSQL
function error. Its supported `Q3C_RADIAL_QUERY` cone predicate succeeded for both
Gaia DR3 and Legacy Survey DR10. Independent local great-circle filtering remains
necessary to enforce the requested radius and make the behavior testable.

**Recommendation:** Test one bounded live cone per service before scaling a
cross-match, use the service's documented spatial predicate, and always verify the
returned candidates with a local spherical calculation.

## 2026-07-15: Separate provenance-row counts from canonical association counts

**Lesson:** Repeated literature rows carrying one catalog identifier must not be
counted as missing matches after those rows are consolidated into canonical
objects.

**Context:** The legacy database contained 1,097 Gaia-bearing rows, but the
stabilized model resolves them to 963 canonical associations and 962 unique Gaia
sources. The old 917-row Legacy export lacked returned source coordinates and
separations, so its geometry could not be revalidated or promoted.

**Recommendation:** Report record, canonical-association, and unique-source counts
separately; hash historical products; and regenerate canonical enrichments with a
complete target audit and explicit shared-source diagnostics.

## 2026-07-16: Do not use `path` as a zsh loop variable

**Lesson:** In zsh, parameter names are case-insensitive, so assigning the loop
variable `path` shadows the executable-search `PATH` array.

**Context:** A read-only README comparison loop assigned `path` and then could not
find `sed`. The command failed before reading or changing any file.

**Recommendation:** Use specific names such as `file_path` in zsh loops and avoid
shell special parameters even when their capitalization differs.

## 2026-07-16: Generate current counts and label historical inventories

**Lesson:** A dated plan or inventory should remain an honest historical artifact,
but it must not appear to be the current source of truth after the data model
changes.

**Context:** Project summaries still cited the 1,542-row exploratory database and
two metadata JSON files retained pending decisions that had since been closed.

**Recommendation:** Generate headline counts from canonical products, link current
documents to that artifact, and mark superseded inventories explicitly instead of
silently rewriting their historical entries.

## 2026-07-16: Calibrate catalog associations by source geometry

**Lesson:** One angular radius is not defensible for catalogs with different
coordinate construction and source morphology.

**Context:** PHANGS-MUSE region centroids supported a 0.3-arcsecond Gaia radius,
while van Zee dwarf-galaxy positions derived from galaxy centers and integer-
arcsecond slit offsets required a separately measured 3.0-arcsecond radius.

**Recommendation:** Measure real and displaced-control separation curves for each
source catalog, record the coordinate construction, and never transfer an
association radius between catalogs without calibration.

## 2026-07-16: Consolidate benchmark labels at the Gaia-source level

**Lesson:** Multiple legitimate catalog positions can select one Gaia source even
when the catalog rows represent separate observations.

**Context:** Two UGC 3647 slit positions produced 13 accepted van Zee associations
but only 12 unique Gaia sources. A release validation check caught the duplicate
before selector work began.

**Recommendation:** Enforce one benchmark row per Gaia source while retaining all
contributing source-row locators, measurements, and association separations in
the row-level provenance.

## 2026-07-16: Interpret discrimination together with feature coverage

**Lesson:** A strong conditional AUC does not justify a hard cut when the feature
is missing preferentially for the target class.

**Context:** Proper-motion and absolute-parallax zero-significance reached
development AUC values above 0.84 but were present for only 82 of 175 confirmed
UCDs. Extended sources frequently lack five-parameter astrometry.

**Recommendation:** Report target and contaminant coverage beside every metric,
preserve missing astrometry as an allowed selector state, and reject hard cuts
that silently remove sources without the measurement.

## 2026-07-16: Uncertain positives can reverse feature priorities

**Lesson:** Candidate labels can change which Gaia diagnostics appear most useful
even when every source association is correct.

**Context:** Adding the uncertain UCD-candidate cohort raised IPD multi-peak and
RUWE discrimination while weakening proper-motion separation. Many candidates
have high-motion or poor-fit properties absent from the confirmed cohort.

**Recommendation:** Calibrate primary score terms on confirmed positives, retain
candidates only as declared sensitivity rows, and present both rankings before
freezing a selector.

## 2026-07-16: Normalize generated validation details before JSON serialization

**Lesson:** Passing scientific checks can still fail artifact creation when a
diagnostic detail contains NumPy scalar types.

**Context:** The selector-development validator reached report writing with no
failed invariant, then `json.dumps` rejected `numpy.int64` values returned by a
Pandas uniqueness operation.

**Recommendation:** Convert Pandas and NumPy diagnostic scalars to native Python
types when assembling machine-readable validation reports.

## 2026-07-16: Run repository diagnostics through uv

**Lesson:** A system Python process can lack project dependencies even when the
locked project environment is complete.

**Context:** One read-only selector-summary command invoked `python` directly and
failed to import `pyvo`; rerunning the same command through `uv run python`
succeeded without changing dependencies or data.

**Recommendation:** Use `uv run` for scripts and ad hoc Python diagnostics, not
only for formal pipeline commands.

## 2026-07-16: Name Gaia diagnostics by their actual units and null hypothesis

**Lesson:** Archive column names and convenient “significance” labels can hide
scientifically important definitions.

**Context:** Gaia's `ipd_frac_multi_peak` and `ipd_frac_odd_win` are integer
percentages from 0 to 100, not unit fractions. The initial proper-motion
diagnostic also treated the two components as independent even though Gaia
publishes `pmra_pmdec_corr`.

**Recommendation:** Document every selector feature with its unit, equation,
physical non-uniqueness, null behavior, and official data-model reference. Use
the Gaia covariance submatrix for vector zero-significance tests.

## 2026-07-17: Verify the numerical domain of archive sampling fields

**Lesson:** A numeric interval does not imply a sampling fraction unless the
field's complete domain is measured and recorded.

**Context:** The SDSS benchmark query used `0.0 <= random_id < 0.1`. Prose called
this a 10% slice, but the measured SDSS field spans 0 to 100, making it a 0.1%
engineering slice. The exact query and selected rows remained reproducible, but
the interpretation was wrong.

**Recommendation:** Record sampling-field domains, interval widths, and derived
fractions together; validate them before using cohort size to support a scientific
claim.

## 2026-07-17: Separate truth, stress, and density roles for large catalogs

**Lesson:** A very large catalog can improve coverage while weakening validation
if it was constructed from the same features being tested.

**Context:** Gaia DR3 galaxy and QSO candidate catalogs contain millions of rows
and directly represent real search failure modes, but their classifications use
Gaia features. Spectroscopic SDSS labels are more independent, Gaia morphology
galaxies are better stress cases, and Quaia's selection function is useful for
spatial-null tests.

**Recommendation:** Assign each external catalog one declared role—independent
calibration, failure-mode stress, or density/null analysis—and never use raw
catalog size as a class prior or evidence of independent selector accuracy.

## 2026-07-17: Retrieve contaminants before applying selector prefilters

**Lesson:** An archive-side selector prefilter makes contaminant acceptance
impossible to measure because rejected objects never enter the audit artifact.

**Context:** The inherited radial search queried only sources passing provisional
astrometric and proper-motion cuts. The morphology-galaxy stress test instead
retrieved every Sersic-fit source and then found that both historical selectors
accepted the same 714 of 814 galaxies.

**Recommendation:** Retrieve the complete declared contaminant cohort first, store
every row, and evaluate versioned selectors locally with selected and rejected
counts both retained.

## 2026-07-17: Compact-galaxy failure modes include missing astrometry

**Lesson:** A high galaxy rejection rate cannot be assumed from proper-motion or
RUWE diagnostics when most Gaia morphology galaxies lack those measurements.

**Context:** Astrometric excess noise and IPD percentages were complete in the
three-host morphology fixture, but RUWE and covariance-aware proper-motion
significance covered only 11.9%. Both historical selectors still accepted 87.7%.

**Recommendation:** Treat missing five-parameter astrometry as an explicit state,
measure galaxy acceptance within that state, and add morphology-sensitive evidence
that does not impose a hard astrometry-availability requirement on UCDs.

## 2026-07-17: Combined density can conceal paired field variation

**Lesson:** A larger combined count does not establish a host-centered excess when
matched field differences are heterogeneous.

**Context:** Twelve host fields had a combined morphology-galaxy density of 42.22
per square degree versus 31.68 in controls, but only eight paired differences were
positive, the two-sided sign-test p-value was 0.3877, and one control was empty.

**Recommendation:** Preserve paired field results, report robust paired tests, and
do not promote an area-weighted combined ratio to a clustering detection.

## 2026-07-17: Empty groups and exact interval bounds require explicit handling

**Lesson:** Valid zero-count fields and floating-point confidence-interval endpoints
must be supported by both analysis and plotting paths.

**Context:** All 24 queries completed, but the first figure attempt failed because a
Wilson upper bound at one differed by floating-point roundoff and produced a tiny
negative display error. Reuse validation also initially expected every field name
in a source table even though a valid zero-row control has no source rows.

**Recommendation:** Clip derived display-error lengths at zero, retain zero-count
fields in field-level tables, and validate source-field membership against nonempty
query records rather than the complete field design.

## 2026-07-17: A morphology candidate catalog is neither truth nor a parent sample

**Lesson:** Successful Gaia Sersic fitting identifies a useful extended-source
stress population but does not establish that every row is a background galaxy.

**Context:** Gaia DR3 `galaxy_candidates` can in principle contain UCDs, H II
regions, nuclei, and other compact sources. Requiring its morphology fit would also
exclude unresolved UCDs. A blind-safe exact match found 0/175 confirmed development
UCDs, 1/569 uncertain UCD candidates, and 0/127 development H II regions in the
914,837-source Sersic-fit subset.

**Recommendation:** Select the Gaia UCD parent sample independently of morphology-
catalog membership. Use Sersic radius, index, uncertainty, and fit quality only as
supplementary exclusion evidence calibrated against independent imaging, and keep
validation identifiers blind until the policy is frozen.

## 2026-07-17: Spectroscopic star does not mean physically single star

**Lesson:** An externally classified stellar spectrum supplies a useful ordinary-
star label, but neither that label nor absence from Gaia NSS establishes singleness.

**Context:** A deterministic SDSS DR16 pool produced 525 unique stars matched 3:1
to confirmed development UCDs in G and sky latitudes. Expanding the pool from 1% to
10% of the measured `random_id` domain reduced the median absolute G mismatch from
0.539 to 0.081 mag; using signed ecliptic latitude had also encoded the SDSS
footprint rather than Gaia scan similarity.

**Recommendation:** Name the cohort by the evidence actually available, match on
absolute ecliptic latitude when controlling broad Gaia scanning geometry, preserve
the measured balance diagnostics, and keep Gaia NSS as a separate failure mode.

## 2026-07-17: Optimize contaminant cohorts equally, not by their row counts

**Lesson:** A pooled false-positive fraction silently gives the largest reference
cohort the greatest scientific importance.

**Context:** The approved Stage 3 priority treats ordinary stars, NSS/binaries, and
QSOs as separate point-source failure modes. Equal-cohort calibration found a 90.3%
confirmed-UCD operating point with 6.48%, 0.00%, and 4.71% retention in those three
cohorts, respectively. The same core retains most galaxies and H II regions, which
are intentionally assigned secondary imaging and color/morphology treatments.

**Recommendation:** Optimize and report the macro-average across declared priority
cohorts, retain every cohort-specific result, and never let catalog availability or
sample size become an implicit scientific weight.

## 2026-07-17: Nested thresholds expose selector instability

**Lesson:** Meeting a pooled development recall target does not guarantee stable
completeness across spatially grouped folds.

**Context:** Regularized logistic regression reached 93.7% pooled confirmed-UCD
recall with 4.02% equal-cohort point-source retention, but fold-specific recall
ranged from 81.8% to 100%. Shallow boosting retained fewer contaminants yet missed
the recall target and was still less stable. Fold-local preprocessing and threshold
selection prevented training-set calibration from hiding this variation.

**Recommendation:** Require repeated grouped nested-CV stability, inspect simple-
model coefficients and failure cases, and report stratified completeness before
freezing one selector for withheld validation.

## 2026-07-17: Normalize NumPy diagnostics before JSON output

**Lesson:** A validation computation can pass logically and still fail while
writing its report when diagnostic details contain NumPy scalar types.

**Context:** The first ML-comparison validation run reached report serialization,
where an outer-fold diagnostic contained `numpy.int64`, which the standard JSON
encoder does not accept.

**Recommendation:** Convert NumPy scalar diagnostics through a strict serializer
when writing machine-readable validation reports, then rerun the full validator.

## 2026-07-17: Invoke project tools through uv

**Lesson:** Project development executables are available through the locked uv
environment and may not exist on the interactive shell path.

**Context:** A direct `pre-commit` invocation failed because the executable was not
globally installed; `uv run pre-commit` used the declared project environment and
ran successfully.

**Recommendation:** Prefix all project Python tools, including pre-commit, with
`uv run` so execution uses the reproducible locked environment.

## 2026-07-17: Sync development groups before running repository hooks

**Lesson:** A default locked uv sync can remove tools that are declared only in
optional development extras.

**Context:** `uv sync --locked` reproduced the default environment but removed
Ruff and pre-commit before the targeted hook run. No source or scientific artifact
changed, but the check could not start until the development groups were restored.

**Recommendation:** Use `uv sync --locked --all-extras` when preparing the full
repository-development environment, then run hooks through `uv run`.

## 2026-07-17: Stable pooled recall can coexist with localized failures

**Lesson:** Repeated cross-validation can stabilize the global estimate without
eliminating spatial, magnitude, or source-specific completeness failures.

**Context:** Ten grouped nested-CV repeats produced a narrow 93.1--95.4% pooled UCD
recall range, while individual folds reached as low as 81.8%. Eleven UCDs were
persistently missed, several in shared HEALPix groups, and fixed-bin recall fell to
85--88% in some populated magnitude or latitude strata.

**Recommendation:** Treat repeated pooled stability as a gate to source-level
review, not permission to skip it. Preserve failure identities, report stratum
counts, and audit provenance and Gaia associations before selector freezing.

## 2026-07-17: Logistic coefficient signs are diagnostics, not causes

**Lesson:** Stable standardized logistic coefficients show that model direction is
reproducible, but correlated measurements prevent causal feature interpretation.

**Context:** All nine measurement coefficients retained the same sign in 50 fitted
outer models. Astrometric excess noise carried the largest positive coefficient,
while parallax and proper-motion significance were consistently negative.

**Recommendation:** Report the preprocessing scale, missing indicators, coefficient
range, and sign agreement. Do not call coefficient magnitude physical importance
or use it alone to justify a scientific cut.

## 2026-07-17: Unanimous boundary selection does not enclose an optimum

**Lesson:** Repeatedly choosing the same hyperparameter is not evidence of an
interior optimum when that value lies at the edge of the tested grid.

**Context:** All 50 logistic outer fits selected `C = 3.0`, the least-regularized
value available. The choice is stable within the declared grid, but weaker
regularization was never compared.

**Recommendation:** Run a bounded grid extension until performance plateaus or an
interior choice is enclosed, without changing the validation partition or choosing
the extension from validation behavior.

## 2026-07-17: A numeric zero can be a missing-value sentinel

**Lesson:** A machine-readable numeric value is not automatically a physical
measurement; catalog conventions and astrophysical plausibility must both be
checked before promoting it to confirmation evidence.

**Context:** Fahrion table B1 contains `RV = 0.0` for 68 of 377 coordinate-bearing
rows. The confirmation review incorrectly stated that every row supplies a radial
velocity, placing 30 zero-RV objects in the confirmed development benchmark. The
bright B409 row then matched a Gaia source with 77.9-sigma parallax and large proper
motion, exposing the error during classifier failure review.

**Recommendation:** Treat Fahrion `RV = 0.0` as unavailable velocity evidence,
re-audit affected objects for independent confirmation and foreground Gaia
superpositions, preserve the original rows and decisions, and rebuild every
downstream benchmark artifact before selector freezing.

## 2026-07-17: Validate CDS reader compatibility before relying on it

**Lesson:** A valid CDS archive README is not guaranteed to be parsed successfully
by every Astropy CDS-reader version.

**Context:** The first corrected Fahrion audit attempted to read table B1 through
its authoritative README, but the installed Astropy reader did not recognize the
file declaration. The fixed-width radial-velocity field is explicitly defined at
bytes 62--67 and the table has a validated 381-row count.

**Recommendation:** When a CDS reader rejects an otherwise validated package, parse
only the required documented fixed-width field, assert the complete row count, and
retain the original README and file hashes as provenance.

## 2026-07-17: Patch repeated approval blocks with exact function context

**Lesson:** A short patch context can modify the wrong occurrence when a build file
contains several similar approval-status and evidence-insertion blocks.

**Context:** The first B409 evidence patch changed the Wave-1 approval status instead
of the confirmation-review status and placed the existing positive-evidence insert
inside the new rejection branch. The safety gate stopped the rebuild with an empty
temporary target database before any completed artifact was accepted.

**Recommendation:** Anchor patches on function names and inspect the complete edited
control-flow block before rebuilding; treat any interrupted generated database as
invalid and rebuild it from immutable inputs rather than using it.

## 2026-07-17: Correct labels through versioned migrations

**Lesson:** An evidence correction should not overwrite a benchmark that already
anchors documented analyses, even when every observational feature is unchanged.

**Context:** Correcting the Fahrion zero-velocity policy changed 26 Gaia-linked
literature labels but did not change source identity, Gaia measurements, spatial
groups, or the sealed partition assignment. Requerying Gaia would add unnecessary
external variability, while overwriting benchmark v1 would erase the provenance of
the superseded selector results.

**Recommendation:** Preserve the old benchmark, create a new evidence version through
a deterministic field-limited migration, hash both inputs and outputs, and recompute
all downstream training artifacts under the new version before model approval.

## 2026-07-18: Boundary chasing is not hyperparameter calibration

**Lesson:** Repeatedly enlarging a regularization grid does not establish a defensible
finite optimum when cross-validation continues selecting its weakest-regularized edge.

**Context:** The logistic grid was extended from `C = 3` to 100 and then 3000. Four
of five outer folds selected the upper boundary in both tests, while fold recall
remained variable.

**Recommendation:** Stop geometric boundary chasing. Compare weakly regularized and
explicitly unregularized fits for coefficient and prediction convergence, then use
stability and scientific interpretability to define the final model policy.
