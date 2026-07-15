"""Audit held shared-Gaia identities with neighbor and image diagnostics.

The script selects the frozen two-position image-ambiguity cohort, retrieves
Gaia DR3 neighbors and Legacy Survey DR10 data/model/residual cutouts, and
writes provenance-complete review artifacts. It never changes the reference
database or accepts an identity decision.
"""

import argparse
import csv
import hashlib
import json
import logging
import math
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import astropy.units as u
import matplotlib.pyplot as plt
from astropy.coordinates import SkyCoord
from matplotlib.image import imread

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import LITERATURE_IMAGE_CUTOUTS, LITERATURE_SOURCES, LITERATURE_VALIDATION
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.utils.plotting import save_figure

logger = logging.getLogger(__name__)

GAIA_TAP_ENDPOINT = "https://datalab.noirlab.edu/tap/sync"
LEGACY_SURVEY_CUTOUT_ENDPOINT = "https://www.legacysurvey.org/viewer/jpeg-cutout"
GROUP_REVIEW_PATH = LITERATURE_VALIDATION / "gaia_association_group_review.csv"
PAIR_GEOMETRY_PATH = LITERATURE_VALIDATION / "gaia_association_pair_geometry.csv"
GAIA_NEIGHBOR_CACHE = LITERATURE_SOURCES / "gaia_dr3_image_ambiguity_neighbors.csv"
GAIA_NEIGHBOR_MANIFEST = LITERATURE_SOURCES / "gaia_dr3_image_ambiguity_neighbors.json"
CUTOUT_MANIFEST_CSV = LITERATURE_SOURCES / "legacy_survey_image_ambiguity_cutouts.csv"
CUTOUT_MANIFEST_JSON = LITERATURE_SOURCES / "legacy_survey_image_ambiguity_cutouts.json"
REVIEW_ANNOTATIONS = LITERATURE_SOURCES / "gaia_image_ambiguity_reviews.json"
REVIEW_CSV = LITERATURE_VALIDATION / "gaia_image_ambiguity_review.csv"
REVIEW_REPORT = LITERATURE_VALIDATION / "gaia_image_ambiguity_review.md"

REVIEW_ACTION = "manual_gaia_image_ambiguity_review"
NEIGHBOR_RADIUS_ARCSEC = 5.0
CUTOUT_PIXEL_SCALE_ARCSEC = 0.262
CUTOUT_SIZE_PIXELS = 128
CUTOUT_LAYERS = ("ls-dr10", "ls-dr10-model", "ls-dr10-resid")
SCRIPT_PATH = "scripts/phase1_literature/audit_gaia_image_ambiguity.py"
FULL_COMMAND = (
    "uv run python scripts/phase1_literature/audit_gaia_image_ambiguity.py "
    "--refresh-gaia-neighbors --refresh-cutouts"
)


def parse_arguments() -> argparse.Namespace:
    """Parse audit inputs, refresh controls, and optional sample limit."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group-review", type=Path, default=GROUP_REVIEW_PATH)
    parser.add_argument("--pair-geometry", type=Path, default=PAIR_GEOMETRY_PATH)
    parser.add_argument("--gaia-cache", type=Path, default=GAIA_NEIGHBOR_CACHE)
    parser.add_argument("--gaia-manifest", type=Path, default=GAIA_NEIGHBOR_MANIFEST)
    parser.add_argument("--cutout-directory", type=Path, default=LITERATURE_IMAGE_CUTOUTS)
    parser.add_argument("--cutout-manifest-csv", type=Path, default=CUTOUT_MANIFEST_CSV)
    parser.add_argument("--cutout-manifest-json", type=Path, default=CUTOUT_MANIFEST_JSON)
    parser.add_argument("--review-annotations", type=Path, default=REVIEW_ANNOTATIONS)
    parser.add_argument("--review-csv", type=Path, default=REVIEW_CSV)
    parser.add_argument("--review-report", type=Path, default=REVIEW_REPORT)
    parser.add_argument("--refresh-gaia-neighbors", action="store_true")
    parser.add_argument("--refresh-cutouts", action="store_true")
    parser.add_argument(
        "--limit",
        type=int,
        help="Process the first N source IDs for a measured small-scale validation run.",
    )
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    """Read a CSV file as dictionaries."""
    with path.open(encoding="utf-8", newline="") as input_file:
        return list(csv.DictReader(input_file))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    """Write stable CSV output with an explicit schema."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def relative_path(path: Path) -> str:
    """Return a repository-relative path where possible."""
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def load_review_targets(
    group_review_path: Path, pair_geometry_path: Path, limit: int | None
) -> list[dict[str, object]]:
    """Load the frozen 23-group image-ambiguity cohort and pair context."""
    selected_groups = {
        row["gaia_dr3_id"]: row
        for row in read_csv(group_review_path)
        if row["recommended_action"] == REVIEW_ACTION
    }
    selected_pairs = [
        row for row in read_csv(pair_geometry_path) if row["gaia_dr3_id"] in selected_groups
    ]
    pairs_by_source: dict[str, list[dict[str, str]]] = {}
    for row in selected_pairs:
        pairs_by_source.setdefault(row["gaia_dr3_id"], []).append(row)

    source_ids = sorted(selected_groups, key=int)
    if limit is not None:
        if limit < 1:
            raise ValueError("--limit must be at least one")
        source_ids = source_ids[:limit]
    targets = []
    for source_id in source_ids:
        pair_rows = pairs_by_source.get(source_id, [])
        if len(pair_rows) != 1:
            raise RuntimeError(
                f"Expected one pair for held group {source_id}, found {len(pair_rows)}"
            )
        group = selected_groups[source_id]
        pair = pair_rows[0]
        if group["canonical_position_count"] != "2":
            raise RuntimeError(f"Held image group is not two-position: {source_id}")
        targets.append({"group": group, "pair": pair})
    if limit is None and len(targets) != 23:
        raise RuntimeError(f"Expected frozen cohort of 23 groups, found {len(targets)}")
    return targets


def build_gaia_neighbor_query(targets: list[dict[str, object]]) -> str:
    """Build a deterministic union-of-boxes query around target Gaia coordinates."""
    clauses = []
    for target in targets:
        pair = target["pair"]
        ra = float(pair["gaia_ra"])
        dec = float(pair["gaia_dec"])
        dec_half_width = NEIGHBOR_RADIUS_ARCSEC / 3600.0
        ra_half_width = dec_half_width / math.cos(math.radians(dec))
        clauses.append(
            f"(ra BETWEEN {ra - ra_half_width:.12f} AND {ra + ra_half_width:.12f} "
            f"AND dec BETWEEN {dec - dec_half_width:.12f} AND {dec + dec_half_width:.12f})"
        )
    where_clause = "\n    OR ".join(clauses)
    return f"""SELECT
    source_id, ra, dec, phot_g_mean_mag, phot_bp_mean_mag, phot_rp_mean_mag,
    duplicated_source, ipd_frac_multi_peak, ipd_frac_odd_win, ruwe
FROM gaia_dr3.gaia_source
WHERE {where_clause}
ORDER BY source_id"""


def retrieve_gaia_neighbors(
    targets: list[dict[str, object]], cache_path: Path, manifest_path: Path
) -> None:
    """Retrieve Gaia box candidates and record exact query provenance."""
    query = build_gaia_neighbor_query(targets)
    request_body = urlencode(
        {"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": query}
    ).encode("utf-8")
    request = Request(GAIA_TAP_ENDPOINT, data=request_body, method="POST")
    with urlopen(request, timeout=120) as response:  # noqa: S310
        response_bytes = response.read()
    if not response_bytes.startswith(b"source_id"):
        raise RuntimeError(response_bytes[:500].decode("utf-8", errors="replace"))
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(response_bytes)
    rows = read_csv(cache_path)
    returned_ids = {row["source_id"] for row in rows}
    missing_targets = sorted(
        {str(target["pair"]["gaia_dr3_id"]) for target in targets} - returned_ids,
        key=int,
    )
    if missing_targets:
        raise RuntimeError(f"Gaia neighborhood retrieval omitted targets: {missing_targets}")
    manifest = {
        "schema_version": 1,
        "retrieval_date": date.today().isoformat(),
        "service": "NOIRLab Astro Data Lab TAP",
        "endpoint": GAIA_TAP_ENDPOINT,
        "table": "gaia_dr3.gaia_source",
        "diagnostic_radius_arcsec": NEIGHBOR_RADIUS_ARCSEC,
        "query_geometry": "RA/Dec boxes followed by exact local spherical filtering",
        "query": query,
        "query_sha256": hashlib.sha256(query.encode("utf-8")).hexdigest(),
        "target_count": len(targets),
        "raw_union_row_count": len(rows),
        "csv_path": relative_path(cache_path),
        "csv_sha256": calculate_sha256(cache_path),
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def associate_neighbors(
    targets: list[dict[str, object]], raw_neighbors: list[dict[str, str]]
) -> dict[str, list[dict[str, object]]]:
    """Apply the exact five-arcsecond spherical aperture to raw box rows."""
    neighbor_coordinates = SkyCoord(
        [float(row["ra"]) for row in raw_neighbors] * u.deg,
        [float(row["dec"]) for row in raw_neighbors] * u.deg,
    )
    associations = {}
    for target in targets:
        pair = target["pair"]
        target_coordinate = SkyCoord(
            float(pair["gaia_ra"]) * u.deg, float(pair["gaia_dec"]) * u.deg
        )
        separations = target_coordinate.separation(neighbor_coordinates).arcsec
        rows = []
        for raw_row, separation in zip(raw_neighbors, separations, strict=True):
            if separation <= NEIGHBOR_RADIUS_ARCSEC:
                rows.append({**raw_row, "separation_arcsec": float(separation)})
        rows.sort(key=lambda row: (float(row["separation_arcsec"]), int(row["source_id"])))
        source_id = str(pair["gaia_dr3_id"])
        if source_id not in {row["source_id"] for row in rows}:
            raise RuntimeError(f"Exact spherical filtering omitted target {source_id}")
        associations[source_id] = rows
    return associations


def cutout_url(ra: float, dec: float, layer: str) -> str:
    """Build an exact Legacy Survey DR10 JPEG cutout URL."""
    parameters = urlencode(
        {
            "ra": f"{ra:.12f}",
            "dec": f"{dec:.12f}",
            "pixscale": f"{CUTOUT_PIXEL_SCALE_ARCSEC:.3f}",
            "width": CUTOUT_SIZE_PIXELS,
            "height": CUTOUT_SIZE_PIXELS,
            "layer": layer,
        }
    )
    return f"{LEGACY_SURVEY_CUTOUT_ENDPOINT}?{parameters}"


def retrieve_cutouts(
    targets: list[dict[str, object]], cutout_directory: Path
) -> list[dict[str, object]]:
    """Retrieve all data/model/residual JPEGs and return file provenance rows."""
    cutout_directory.mkdir(parents=True, exist_ok=True)
    manifest_rows = []
    for target in targets:
        pair = target["pair"]
        source_id = str(pair["gaia_dr3_id"])
        ra = float(pair["gaia_ra"])
        dec = float(pair["gaia_dec"])
        for layer in CUTOUT_LAYERS:
            url = cutout_url(ra, dec, layer)
            request = Request(url, headers={"User-Agent": "BubbleTea-literature-audit/1.0"})
            with urlopen(request, timeout=120) as response:  # noqa: S310
                response_bytes = response.read()
                content_type = response.headers.get("Content-Type", "")
            if not response_bytes.startswith(b"\xff\xd8"):
                raise RuntimeError(f"Cutout retrieval did not return JPEG for {source_id} {layer}")
            output_path = cutout_directory / f"{source_id}_{layer}.jpg"
            output_path.write_bytes(response_bytes)
            manifest_rows.append(
                {
                    "gaia_dr3_id": source_id,
                    "gaia_ra": f"{ra:.12f}",
                    "gaia_dec": f"{dec:.12f}",
                    "layer": layer,
                    "pixel_scale_arcsec": CUTOUT_PIXEL_SCALE_ARCSEC,
                    "width_pixels": CUTOUT_SIZE_PIXELS,
                    "height_pixels": CUTOUT_SIZE_PIXELS,
                    "url": url,
                    "content_type": content_type,
                    "byte_count": len(response_bytes),
                    "file_path": relative_path(output_path),
                    "sha256": hashlib.sha256(response_bytes).hexdigest(),
                }
            )
    return manifest_rows


def load_cutout_manifest(path: Path, targets: list[dict[str, object]]) -> list[dict[str, str]]:
    """Load cached cutout provenance and require every target-layer combination."""
    rows = read_csv(path)
    expected = {
        (str(target["pair"]["gaia_dr3_id"]), layer) for target in targets for layer in CUTOUT_LAYERS
    }
    available = {(row["gaia_dr3_id"], row["layer"]) for row in rows}
    missing = sorted(expected - available)
    if missing:
        raise RuntimeError(f"Cutout manifest is missing target layers: {missing}")
    return [row for row in rows if (row["gaia_dr3_id"], row["layer"]) in expected]


def write_cutout_manifests(
    csv_path: Path,
    json_path: Path,
    rows: list[dict[str, object]],
    group_review_path: Path,
) -> None:
    """Write row-level and collection-level Legacy Survey provenance."""
    fieldnames = [
        "gaia_dr3_id",
        "gaia_ra",
        "gaia_dec",
        "layer",
        "pixel_scale_arcsec",
        "width_pixels",
        "height_pixels",
        "url",
        "content_type",
        "byte_count",
        "file_path",
        "sha256",
    ]
    write_csv(csv_path, rows, fieldnames)
    manifest = {
        "schema_version": 1,
        "retrieval_date": date.today().isoformat(),
        "service": "Legacy Survey Viewer cutout service",
        "endpoint": LEGACY_SURVEY_CUTOUT_ENDPOINT,
        "survey_layer": "Legacy Surveys DR10",
        "layers": list(CUTOUT_LAYERS),
        "pixel_scale_arcsec": CUTOUT_PIXEL_SCALE_ARCSEC,
        "width_pixels": CUTOUT_SIZE_PIXELS,
        "height_pixels": CUTOUT_SIZE_PIXELS,
        "target_count": len({str(row["gaia_dr3_id"]) for row in rows}),
        "file_count": len(rows),
        "csv_path": relative_path(csv_path),
        "csv_sha256": calculate_sha256(csv_path),
        "cohort_source_path": relative_path(group_review_path),
        "cohort_source_sha256": calculate_sha256(group_review_path),
        "scientific_limit": (
            "JPEG cutouts are image diagnostics only; they do not establish DR10 "
            "maskbit or catalog-quality status."
        ),
    }
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def optional_float(value: str) -> float | None:
    """Convert a possibly blank or NaN CSV value to a finite float."""
    if not value:
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def load_review_annotations(
    path: Path, targets: list[dict[str, object]]
) -> dict[str, dict[str, str]]:
    """Load reproducible visual recommendations and require cohort coverage."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    shared_rationale = str(payload["shared_identity_rationale"])
    annotations = {
        str(source_id): {
            "image_review": "single_centered_source_both_positions_overlay",
            "identity_recommendation": "recommend_accept_shared_identity",
            "review_rationale": shared_rationale,
        }
        for source_id in payload["recommended_shared_identity_source_ids"]
    }
    for row in payload["recommended_separate_objects"]:
        annotations[str(row["gaia_dr3_id"])] = {
            "image_review": "unresolved_close_pair_at_gaia_resolution",
            "identity_recommendation": str(row["recommendation"]),
            "review_rationale": str(row["rationale"]),
        }
    target_ids = {str(target["pair"]["gaia_dr3_id"]) for target in targets}
    annotation_ids = set(annotations)
    missing_ids = target_ids - annotation_ids
    unexpected_ids = annotation_ids - target_ids if len(targets) == 23 else set()
    if missing_ids or unexpected_ids:
        raise RuntimeError(
            "Review annotation coverage mismatch: "
            f"missing={sorted(missing_ids, key=int)}, "
            f"unexpected={sorted(unexpected_ids, key=int)}"
        )
    decision_by_recommendation = {
        "recommend_accept_shared_identity": "approved_same_astrophysical_object",
        "recommend_retain_separate_shared_gaia_source": (
            "approved_retain_separate_shared_gaia_source"
        ),
    }
    if payload["identity_changes_authorized"] is True:
        for annotation in annotations.values():
            annotation["identity_decision"] = decision_by_recommendation[
                annotation["identity_recommendation"]
            ]
    else:
        for annotation in annotations.values():
            annotation["identity_decision"] = "pending_project_review"
    return {source_id: annotations[source_id] for source_id in target_ids}


def build_review_rows(
    targets: list[dict[str, object]],
    neighbor_associations: dict[str, list[dict[str, object]]],
    cutout_rows: list[dict[str, str]],
    review_annotations: dict[str, dict[str, str]],
) -> list[dict[str, object]]:
    """Summarize measured neighborhood evidence without accepting identities."""
    cutouts = {(row["gaia_dr3_id"], row["layer"]): row for row in cutout_rows}
    review_rows = []
    for target in targets:
        group = target["group"]
        pair = target["pair"]
        source_id = str(pair["gaia_dr3_id"])
        annotation = review_annotations[source_id]
        neighbors = neighbor_associations[source_id]
        competitors = [row for row in neighbors if row["source_id"] != source_id]
        target_g_mag = optional_float(
            next(row for row in neighbors if row["source_id"] == source_id)["phot_g_mean_mag"]
        )
        nearest = competitors[0] if competitors else None
        nearest_g_mag = optional_float(str(nearest["phot_g_mean_mag"])) if nearest else None
        delta_g_mag = (
            nearest_g_mag - target_g_mag
            if nearest_g_mag is not None and target_g_mag is not None
            else None
        )
        evidence_summary = (
            "competing_gaia_source_within_2_arcsec"
            if any(float(row["separation_arcsec"]) <= 2.0 for row in competitors)
            else "no_competing_gaia_source_within_2_arcsec"
        )
        review_rows.append(
            {
                "gaia_dr3_id": source_id,
                "source_context": group["source_context"],
                "bibcodes": group["bibcodes"],
                "original_name_1": pair["original_name_1"],
                "original_name_2": pair["original_name_2"],
                "ra_1": pair["ra_1"],
                "dec_1": pair["dec_1"],
                "ra_2": pair["ra_2"],
                "dec_2": pair["dec_2"],
                "literature_position_separation_arcsec": pair["separation_arcsec"],
                "gaia_ra": pair["gaia_ra"],
                "gaia_dec": pair["gaia_dec"],
                "gaia_g_mag": pair["gaia_g_mag"],
                "gaia_duplicated_source": pair["gaia_duplicated_source"],
                "gaia_ipd_frac_multi_peak": pair["gaia_ipd_frac_multi_peak"],
                "gaia_ipd_frac_odd_win": pair["gaia_ipd_frac_odd_win"],
                "gaia_ruwe": pair["gaia_ruwe"],
                "gaia_distance_1_arcsec": pair["gaia_distance_1_arcsec"],
                "gaia_distance_2_arcsec": pair["gaia_distance_2_arcsec"],
                "gaia_neighbor_count_within_1_arcsec": sum(
                    float(row["separation_arcsec"]) <= 1.0 for row in competitors
                ),
                "gaia_neighbor_count_within_2_arcsec": sum(
                    float(row["separation_arcsec"]) <= 2.0 for row in competitors
                ),
                "gaia_neighbor_count_within_5_arcsec": len(competitors),
                "nearest_competing_gaia_id": nearest["source_id"] if nearest else "",
                "nearest_competing_gaia_separation_arcsec": (
                    f"{float(nearest['separation_arcsec']):.12f}" if nearest else ""
                ),
                "nearest_competing_gaia_g_mag": nearest_g_mag if nearest_g_mag is not None else "",
                "nearest_competing_gaia_delta_g_mag": delta_g_mag
                if delta_g_mag is not None
                else "",
                "data_cutout_path": cutouts[(source_id, "ls-dr10")]["file_path"],
                "data_cutout_sha256": cutouts[(source_id, "ls-dr10")]["sha256"],
                "model_cutout_path": cutouts[(source_id, "ls-dr10-model")]["file_path"],
                "model_cutout_sha256": cutouts[(source_id, "ls-dr10-model")]["sha256"],
                "residual_cutout_path": cutouts[(source_id, "ls-dr10-resid")]["file_path"],
                "residual_cutout_sha256": cutouts[(source_id, "ls-dr10-resid")]["sha256"],
                "neighborhood_evidence": evidence_summary,
                "image_review": annotation["image_review"],
                "identity_recommendation": annotation["identity_recommendation"],
                "review_rationale": annotation["review_rationale"],
                "identity_decision": annotation["identity_decision"],
            }
        )
    return review_rows


def marker_position(
    ra: float, dec: float, center_ra: float, center_dec: float
) -> tuple[float, float]:
    """Convert a small sky offset to cutout pixels, with east to the left."""
    delta_ra_arcsec = (ra - center_ra) * math.cos(math.radians(center_dec)) * 3600.0
    delta_dec_arcsec = (dec - center_dec) * 3600.0
    center = (CUTOUT_SIZE_PIXELS - 1) / 2.0
    return (
        center - delta_ra_arcsec / CUTOUT_PIXEL_SCALE_ARCSEC,
        center + delta_dec_arcsec / CUTOUT_PIXEL_SCALE_ARCSEC,
    )


def render_montage(
    rows: list[dict[str, object]],
    cutout_rows: list[dict[str, str]],
    name: str,
    title: str,
    command: str,
) -> None:
    """Render aligned DR10 data/model/residual rows with literature markers."""
    cutouts = {(row["gaia_dr3_id"], row["layer"]): Path(row["file_path"]) for row in cutout_rows}
    figure, axes = plt.subplots(
        len(rows), 3, figsize=(9.0, max(4.0, 2.6 * len(rows))), squeeze=False
    )
    layer_titles = ("DR10 data", "DR10 model", "DR10 residual")
    for row_index, row in enumerate(rows):
        source_id = str(row["gaia_dr3_id"])
        for column_index, layer in enumerate(CUTOUT_LAYERS):
            axis = axes[row_index][column_index]
            axis.imshow(imread(cutouts[(source_id, layer)]), origin="upper")
            axis.set_xticks([])
            axis.set_yticks([])
            if row_index == 0:
                axis.set_title(layer_titles[column_index], fontsize=9)
            for marker_index, color in ((1, "#00e5ff"), (2, "#ff4fd8")):
                x, y = marker_position(
                    float(row[f"ra_{marker_index}"]),
                    float(row[f"dec_{marker_index}"]),
                    float(row["gaia_ra"]),
                    float(row["gaia_dec"]),
                )
                axis.scatter(
                    [x],
                    [y],
                    s=42,
                    facecolors="none",
                    edgecolors=color,
                    linewidths=1.2,
                )
            center = (CUTOUT_SIZE_PIXELS - 1) / 2.0
            axis.scatter([center], [center], marker="+", s=45, color="#ffe066", linewidths=1.0)
        names = " / ".join(
            value or "unnamed"
            for value in (str(row["original_name_1"]), str(row["original_name_2"]))
        )
        axes[row_index][0].set_ylabel(
            f"{source_id}\n{names}\n"
            f"dup={row['gaia_duplicated_source']} multi={row['gaia_ipd_frac_multi_peak']} "
            f"odd={row['gaia_ipd_frac_odd_win']}",
            fontsize=6.5,
            rotation=0,
            ha="right",
            va="center",
            labelpad=5,
        )
    figure.suptitle(title, fontsize=12, y=0.997)
    figure.subplots_adjust(
        left=0.25, right=0.995, top=0.965, bottom=0.005, hspace=0.08, wspace=0.03
    )
    save_figure(
        figure,
        name,
        phase=1,
        script_path=SCRIPT_PATH,
        command=command,
        data_source=(
            "Gaia DR3 neighborhood cache and Legacy Surveys DR10 JPEG data/model/residual cutouts"
        ),
        description=(
            "Each row is centered on the authoritative Gaia DR3 position (yellow plus). "
            "The two preserved literature positions are cyan and magenta circles. The "
            "5-arcsecond Gaia neighborhood is diagnostic, not an identity radius. JPEG "
            "cutouts are visual diagnostics and do not establish DR10 maskbit or catalog "
            "quality status."
        ),
        title=title,
    )
    plt.close(figure)


def write_review_report(
    path: Path,
    review_rows: list[dict[str, object]],
    group_review_path: Path,
    pair_geometry_path: Path,
    review_annotations_path: Path,
) -> None:
    """Write the audit boundary and measured neighborhood summary."""
    contexts = Counter(str(row["source_context"]) for row in review_rows)
    within_one = sum(int(row["gaia_neighbor_count_within_1_arcsec"]) > 0 for row in review_rows)
    within_two = sum(int(row["gaia_neighbor_count_within_2_arcsec"]) > 0 for row in review_rows)
    within_five = sum(int(row["gaia_neighbor_count_within_5_arcsec"]) > 0 for row in review_rows)
    recommendations = Counter(str(row["identity_recommendation"]) for row in review_rows)
    context_lines = "\n".join(f"- `{key}`: {value}" for key, value in sorted(contexts.items()))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""# Gaia Image-Ambiguity Review

**Date:** {date.today().isoformat()}
**Status:** Project-lead-approved split treatment recorded.

## Scope

- Held two-position groups audited: {len(review_rows)}
{context_lines}
- Frozen group-review input: `{relative_path(group_review_path)}`
  (SHA256 `{calculate_sha256(group_review_path)}`)
- Frozen pair-geometry input: `{relative_path(pair_geometry_path)}`
  (SHA256 `{calculate_sha256(pair_geometry_path)}`)
- Review annotations: `{relative_path(review_annotations_path)}`
  (SHA256 `{calculate_sha256(review_annotations_path)}`)

## Measured Gaia Neighborhoods

- Groups with a competing Gaia DR3 source within 1 arcsecond: {within_one}
- Groups with a competing Gaia DR3 source within 2 arcseconds: {within_two}
- Groups with a competing Gaia DR3 source within 5 arcseconds: {within_five}

The 5-arcsecond aperture is a diagnostic neighborhood, not an association or
identity radius. The TAP request uses conservative coordinate boxes, followed by
an exact local spherical-separation filter.

## Imaging Boundary

Legacy Survey DR10 data, model, and residual JPEG cutouts are centered on the
authoritative Gaia coordinate. They are diagnostic views only. The viewer JPEGs
do not establish DR10 `maskbits`, catalog measurement quality, or an astrophysical
identity by themselves; DR10 known issues and bitmask definitions must be checked
before using Legacy Survey measurements in scientific selection.

## Decision State

The project lead approved accepting {recommendations["recommend_accept_shared_identity"]}
shared identities and retaining {recommendations["recommend_retain_separate_shared_gaia_source"]} close pair as a separate pair of
canonical objects sharing ambiguous Gaia evidence. This audit artifact records
the authorization but does not itself modify the database; the deterministic v2
builder applies the approved treatment.
""",
        encoding="utf-8",
    )


def main() -> None:
    """Run the non-destructive Gaia-neighbor and image audit."""
    arguments = parse_arguments()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    targets = load_review_targets(arguments.group_review, arguments.pair_geometry, arguments.limit)
    review_annotations = load_review_annotations(arguments.review_annotations, targets)

    if arguments.refresh_gaia_neighbors:
        retrieve_gaia_neighbors(targets, arguments.gaia_cache, arguments.gaia_manifest)
    if not arguments.gaia_cache.exists():
        raise FileNotFoundError(
            "Gaia neighbor cache is absent; rerun with --refresh-gaia-neighbors"
        )
    raw_neighbors = read_csv(arguments.gaia_cache)
    neighbor_associations = associate_neighbors(targets, raw_neighbors)

    if arguments.refresh_cutouts:
        cutout_rows = retrieve_cutouts(targets, arguments.cutout_directory)
        write_cutout_manifests(
            arguments.cutout_manifest_csv,
            arguments.cutout_manifest_json,
            cutout_rows,
            arguments.group_review,
        )
    else:
        if not arguments.cutout_manifest_csv.exists():
            raise FileNotFoundError("Cutout manifest is absent; rerun with --refresh-cutouts")
        cutout_rows = load_cutout_manifest(arguments.cutout_manifest_csv, targets)

    review_rows = build_review_rows(targets, neighbor_associations, cutout_rows, review_annotations)
    review_fieldnames = list(review_rows[0])
    write_csv(arguments.review_csv, review_rows, review_fieldnames)
    write_review_report(
        arguments.review_report,
        review_rows,
        arguments.group_review,
        arguments.pair_geometry,
        arguments.review_annotations,
    )

    command = (
        FULL_COMMAND if arguments.limit is None else f"{FULL_COMMAND} --limit {arguments.limit}"
    )
    m87_rows = [
        row for row in review_rows if row["source_context"] == "liu_m87_and_fahrion_compilation"
    ]
    other_rows = [
        row for row in review_rows if row["source_context"] != "liu_m87_and_fahrion_compilation"
    ]
    if m87_rows:
        render_montage(
            m87_rows,
            cutout_rows,
            "gaia_image_ambiguity_m87",
            "Held shared-Gaia identities: M87 literature positions",
            command,
        )
    if other_rows:
        render_montage(
            other_rows,
            cutout_rows,
            "gaia_image_ambiguity_other",
            "Held shared-Gaia identities: other literature positions",
            command,
        )
    logger.info(
        "Audited %d held image-ambiguity groups without changing identities", len(review_rows)
    )


if __name__ == "__main__":
    main()
