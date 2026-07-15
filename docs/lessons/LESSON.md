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
