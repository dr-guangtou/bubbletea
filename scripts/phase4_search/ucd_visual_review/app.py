"""Flask application for the UCD visual review workbench."""

import json
import sys
from functools import cache
from pathlib import Path

from flask import Flask, abort, g, jsonify, request, send_file

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.config import (
    EXTERNAL_DATA_DIR,
    PROJECT_ROOT,
    UCD_VISUAL_REVIEW_BUNDLE_DIR,
    UCD_VISUAL_REVIEW_BUNDLE_INDEX,
    UCD_VISUAL_REVIEW_BUNDLE_MANIFEST,
    UCD_VISUAL_REVIEW_REVIEW_DB,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase4_search.ucd_visual_review import export as export_module
from scripts.phase4_search.ucd_visual_review import review_model, schema

BUNDLE_VERSION = "ucd_visual_review_bundle_v1"


def resolve_portable_path(path_text: str) -> Path:
    """Resolve a repository-relative or external-data portable path."""
    prefix = "$BUBBLETEA_EXTERNAL_DATA/"
    if path_text.startswith(prefix):
        return EXTERNAL_DATA_DIR / path_text.removeprefix(prefix)
    return Path(path_text)


def load_index() -> list[dict]:
    """Load the bundle index rows in a stable order with NaN sanitized to None."""
    import pandas as pd

    frame = pd.read_csv(
        UCD_VISUAL_REVIEW_BUNDLE_INDEX,
        dtype={"canonical_object_id": "string"},
        keep_default_na=False,
    )
    return frame.to_dict("records")


@cache
def load_object(canonical_object_id: str) -> dict:
    """Load one object document from the bundle."""
    path = UCD_VISUAL_REVIEW_BUNDLE_DIR / f"{canonical_object_id}.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def bundle_digest() -> str:
    """Return the recorded digest of the bundle index."""
    manifest = json.loads(UCD_VISUAL_REVIEW_BUNDLE_MANIFEST.read_text())
    return manifest["outputs"][
        str(UCD_VISUAL_REVIEW_BUNDLE_INDEX.relative_to(PROJECT_ROOT))
    ]


def verify_bundle() -> None:
    """Refuse to start if the bundle index digest does not match the manifest."""
    recorded = bundle_digest()
    current = calculate_sha256(UCD_VISUAL_REVIEW_BUNDLE_INDEX)
    if recorded != current:
        raise RuntimeError("Review bundle index digest mismatch; refusing to start")


def cohort_of(object_id: str) -> str:
    """Return the reference cohort for an object identifier."""
    document = load_object(object_id)
    return str(document.get("object", {}).get("reference_cohort", ""))


def get_db():
    """Return a per-request review database connection."""
    if "db" not in g:
        g.db = schema.connect(UCD_VISUAL_REVIEW_REVIEW_DB)
    return g.db


def create_app() -> Flask:
    """Build and configure the review workbench application."""
    verify_bundle()
    UCD_VISUAL_REVIEW_REVIEW_DB.parent.mkdir(parents=True, exist_ok=True)
    index = load_index()

    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False

    @app.teardown_appcontext
    def close_db(exception):  # noqa: ANN001, ARG001
        database = g.pop("db", None)
        if database is not None:
            database.close()

    @app.get("/")
    def home() -> str:
        return app.send_static_file("index.html")

    @app.get("/api/summary")
    def summary():
        state_map = schema.review_state_map(get_db())
        counts = {
            "total": len(index),
            "confirmed": sum(1 for row in index if row["reference_cohort"] == "confirmed_ucd"),
            "candidate": sum(
                1
                for row in index
                if row["reference_cohort"] == "saifollahi_high_probability_candidate"
            ),
            "reviewed_confirmed": 0,
            "reviewed_candidate": 0,
            "included_confirmed": 0,
        }
        for row in index:
            review = state_map.get(row["canonical_object_id"])
            cohort = row["reference_cohort"]
            if review and review_model.review_complete(review, cohort):
                if cohort == "confirmed_ucd":
                    counts["reviewed_confirmed"] += 1
                    if review["final_decision"] == "include":
                        counts["included_confirmed"] += 1
                else:
                    counts["reviewed_candidate"] += 1
        return jsonify(counts)

    @app.get("/api/objects")
    def objects():
        state_map = schema.review_state_map(get_db())
        rows = [dict(row) for row in index]
        cohort_filter = request.args.get("cohort")
        decision_filter = request.args.get("decision")
        review_filter = request.args.get("review_status")
        q = (request.args.get("q") or "").lower()
        if cohort_filter:
            rows = [row for row in rows if row["reference_cohort"] == cohort_filter]
        for row in rows:
            row["_review"] = state_map.get(row["canonical_object_id"])
            row["_complete"] = bool(
                row["_review"]
                and review_model.review_complete(row["_review"], row["reference_cohort"])
            )
        if review_filter == "complete":
            rows = [row for row in rows if row["_complete"]]
        elif review_filter == "incomplete":
            rows = [row for row in rows if row["_review"] and not row["_complete"]]
        elif review_filter == "not_started":
            rows = [row for row in rows if not row["_review"]]
        if decision_filter:
            rows = [
                row
                for row in rows
                if row["_review"] and row["_review"]["final_decision"] == decision_filter
            ]
        if q:
            rows = [
                row
                for row in rows
                if q in str(row["original_names"]).lower()
                or q in str(row["canonical_object_id"]).lower()
                or q in str(row["host_name"]).lower()
            ]
        sort = request.args.get("sort", "canonical_object_id")
        rows.sort(key=lambda row: str(row.get(sort) or ""))
        page = max(1, int(request.args.get("page", 1)))
        page_size = min(100, int(request.args.get("page_size", 50)))
        start = (page - 1) * page_size
        page_rows = rows[start : start + page_size]
        return jsonify(
            {
                "total": len(rows),
                "page": page,
                "page_size": page_size,
                "items": [
                    {
                        "canonical_object_id": row["canonical_object_id"],
                        "reference_cohort": row["reference_cohort"],
                        "classification_state": row["classification_state"],
                        "original_names": row["original_names"],
                        "host_name": row["host_name"],
                        "host_association_state": row["host_association_state"],
                        "design_reference_membership": row["design_reference_membership"],
                        "adopted_distance_mpc": row["adopted_distance_mpc"],
                        "review": row["_review"],
                        "complete": row["_complete"],
                    }
                    for row in page_rows
                ],
            }
        )

    @app.get("/api/objects/<canonical_object_id>")
    def object_detail(canonical_object_id: str):
        document = load_object(canonical_object_id)
        if not document:
            abort(404)
        document = dict(document)
        document["review"] = schema.current_review(get_db(), canonical_object_id)
        document["complete"] = bool(
            document["review"]
            and review_model.review_complete(
                document["review"], document["object"]["reference_cohort"]
            )
        )
        return jsonify(document)

    @app.get("/api/objects/<canonical_object_id>/history")
    def object_history(canonical_object_id: str):
        return jsonify(schema.history(get_db(), canonical_object_id))

    @app.get("/api/images/<canonical_object_id>/<scale>")
    def image(canonical_object_id: str, scale: str):
        if scale not in {"compact", "wide"}:
            abort(404)
        document = load_object(canonical_object_id)
        file_path = document.get("images", {}).get(scale, {}).get("file_path")
        if not file_path:
            abort(404)
        resolved = resolve_portable_path(file_path)
        if not resolved.exists():
            abort(404)
        return send_file(resolved, mimetype="image/jpeg")

    @app.post("/api/objects/<canonical_object_id>/reviews")
    def save_review(canonical_object_id: str):
        document = load_object(canonical_object_id)
        if not document:
            abort(404)
        payload = request.get_json(force=True) or {}
        cohort = str(document.get("object", {}).get("reference_cohort", ""))
        membership = str(document.get("host", {}).get("design_reference_membership", ""))
        if (
            membership == "excluded_stripped_nucleus_or_luminous_gc"
            and payload.get("final_decision") == "include"
        ):
            return jsonify({"errors": ["excluded object cannot be included"]}), 400
        errors = review_model.validate_review(payload, cohort)
        if errors:
            return jsonify({"errors": errors}), 400
        bundle_digest_value = bundle_digest()
        revision_id, conflict = schema.save_revision(
            get_db(),
            canonical_object_id,
            BUNDLE_VERSION,
            bundle_digest_value,
            payload,
        )
        if conflict:
            return jsonify({"error": conflict}), 409
        return jsonify({"revision_id": revision_id}), 201

    @app.post("/api/export")
    def export():
        summary = export_module.generate_exports(get_db())
        return jsonify(summary)

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5001, debug=False)
