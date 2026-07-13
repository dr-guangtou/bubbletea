# Lessons Learned - UCD Search Project

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
