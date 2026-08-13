# UCD Visual Review Workbench

A localhost, single-user Flask application for source-by-source visual review of the
UCD reference (680 confirmed UCDs + 44 Saifollahi high-probability candidates).

## Run

```bash
BUBBLETEA_EXTERNAL_DATA=~/Dropbox/work/data \
  uv run python -m scripts.phase4_search.ucd_visual_review.app
```

Then open <http://127.0.0.1:5001> in a browser.

The server refuses to start if the review-input bundle's recorded digest does not
match the files on disk. Review state is stored in an append-only SQLite database
under `$BUBBLETEA_EXTERNAL_DATA/bubbletea/ucd_visual_review_v1/reviews/`.

## Structure

- `app.py` — Flask routes (summary, objects, detail, history, images, save, export).
- `schema.py` — append-only review revision storage.
- `review_model.py` — the four-state visual observations, decisions, and validation.
- `validate_api.py` — deterministic API checks against the frozen bundle.
- `static/` — vanilla HTML, CSS, and JavaScript frontend.

## Specification

`docs/plans/ucd_visual_review_tool.md`
