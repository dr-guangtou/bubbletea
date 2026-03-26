# `BubbleTea` - Search for fun compact galaxies using Gaia data 

This is a repo for a project that will utilize the Gaia and imaging survey data to search for Ultra-Compact Dwarf (UCD) galaxies and maybe other compact galaxies.

This project has been developed casually by other agents, and the results are in the `ucd_project` folder. Important files include: 
  - `README.md`
  - `PROJECT_REVIEW.md`
  - `LESSON.md`
  - `crossmatch_methods.md`
  - `ucd_collection_schema.md`

These past files include scripts to: 
  - Query the Gaia database
  - Query the Legacy database 
  - Fetching literature data for UCDs and other published targets
  - Fetching and/or processing nearby galaxy catalogs
  - Organizing literature or catalog data into a local database
  - Performing basic UCD candidate search, quality cut, and statistical analysis
  - Basic visualization.

**Note** that `/Users/shuang/data/` is a directory on my MacStudio in my office. If this link shows up, make a note of it, but do not change it.

The main scripts for searching and cross-matching can be accessed in the following way:

```python
cd ucd_project

# Run UCD search
python3 scripts/gaia_queries/radial_search_v2.py

# Cross-match with Legacy Survey
python3 scripts/legacy_survey/xmatch_legacy_survey.py
```
