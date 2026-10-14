"""Assemble audited development-only teaching data and retrieve small DR11 cutouts.

Run with --prepare to assemble observations and a separate instructor key, then
--acquire --pilot for one example per class before --acquire for the full gallery.
Raw images stay in the configured external cache. No research file is modified.
"""

import argparse
import csv
import hashlib
import io
import json
import logging
import math
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlencode

import numpy as np
from astropy.coordinates import SkyCoord
from astropy.table import Table
from PIL import Image

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    CONFIRMED_UCD_DESIGN_REFERENCE_EXCLUSIONS,
    SELECTOR_DEVELOPMENT_FEATURES,
    SPECTROSCOPIC_STELLAR_REFERENCE_MANIFEST,
    STELLAR_REFERENCE_DIR,
    TEACHING_PACKET,
    UCD_LEGACY_REFERENCE_TARGETS,
    teaching_canonical_reference,
    teaching_part1_downloads,
    teaching_part1_key,
    teaching_part1_packet,
    teaching_part1_reviews,
    teaching_reliability_reviews,
)
from scripts.teaching.prepare_teaching_data import request_bytes

logger = logging.getLogger(__name__)
numeric_fields = [
    "ra",
    "dec",
    "phot_g_mean_mag",
    "phot_bp_mean_mag",
    "phot_rp_mean_mag",
    "phot_bp_rp_excess_factor",
    "astrometric_excess_noise",
    "astrometric_excess_noise_sig",
    "ruwe",
    "parallax",
    "parallax_error",
    "pmra",
    "pmra_error",
    "pmdec",
    "pmdec_error",
    "pmra_pmdec_corr",
    "ipd_frac_multi_peak",
    "ipd_frac_odd_win",
]
derived_fields = ["bp_rp", "absolute_parallax_significance", "proper_motion_significance"]
catalog_columns = ["source_id", *numeric_fields, *derived_fields, "reference_class"]
task1_ucd_ids = [
    "3530134298912051200",
    "4860297520297524864",
    "3907903846852100992",
    "3907716453134916352",
    "4860297554657264128",
    "3908713847620226176",
    "3907698826589168000",
    "3931736865191365760",
    "4860287422830497664",
    "3907710229727310208",
]
example_ucd_ids = ["3927659910436411136", "3928413763095214592", "3928425445406259456"]
unusable_gallery_ids = {
    "6088704213306329856",
    "6088703800989823360",
    "6088700605533772288",
    "6088704934861181312",
    "6088718300799198720",
    "6088701773764867328",
    "6088703354312975744",
    "377786422868114560",
    "909705654187349760",
    "3480892395785435904",
    "1080873260714189440",
}
insufficient_gallery_evidence_ids = {"2849268728502575616", "578546220918767872"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_csv(path):
    with path.open() as stream:
        return list(csv.DictReader(stream))


def number(value):
    if np.ma.is_masked(value):
        return None
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def identifier(value):
    result = value.decode() if isinstance(value, bytes) else str(value)
    if not result.isdigit() or not 1 <= len(result) <= 19:
        raise ValueError(f"Invalid exact identifier: {result}")
    return result


def spectrum_identifier(value):
    """Preserve the unsigned 64-bit SDSS bit pattern from a signed FITS integer."""
    result = int(value)
    return str(result if result >= 0 else result + 2**64)


def measurements(row):
    result = {field: number(row.get(field)) for field in numeric_fields}
    if result["phot_bp_mean_mag"] is not None and result["phot_rp_mean_mag"] is not None:
        result["bp_rp"] = result["phot_bp_mean_mag"] - result["phot_rp_mean_mag"]
    else:
        result["bp_rp"] = number(row.get("bp_rp"))
    parallax, error = result["parallax"], result["parallax_error"]
    result["absolute_parallax_significance"] = (
        abs(parallax) / error if parallax is not None and error is not None and error > 0 else None
    )
    motion = [
        result[key] for key in ["pmra", "pmdec", "pmra_error", "pmdec_error", "pmra_pmdec_corr"]
    ]
    result["proper_motion_significance"] = None
    if all(value is not None for value in motion):
        pmra, pmdec, error_ra, error_dec, correlation = motion
        if error_ra > 0 and error_dec > 0 and abs(correlation) < 1:
            u, v = pmra / error_ra, pmdec / error_dec
            result["proper_motion_significance"] = math.sqrt(
                max(0, (u * u + v * v - 2 * correlation * u * v) / (1 - correlation**2))
            )
    return result


def stable_order(source_id):
    return hashlib.sha256(f"bubbletea_part1_v2:{source_id}".encode()).hexdigest()


def write_json(path, value, compact=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            value,
            allow_nan=False,
            indent=None if compact else 2,
            separators=(",", ":") if compact else None,
        )
        + "\n"
    )


def prepare(star_count):
    development = load_csv(SELECTOR_DEVELOPMENT_FEATURES)
    assert all(row["partition"] == "development" for row in development)
    atlas = {row["canonical_object_id"]: row for row in load_csv(UCD_LEGACY_REFERENCE_TARGETS)}
    canonical = {row["canonical_object_id"]: row for row in load_csv(teaching_canonical_reference)}
    source_exclusions = set(
        json.loads(CONFIRMED_UCD_DESIGN_REFERENCE_EXCLUSIONS.read_text())["canonical_object_ids"]
    )
    reliability = json.loads(teaching_reliability_reviews.read_text())["reviews"]
    unreliable = {
        row["canonical_object_id"]
        for row in reliability
        if row["training_treatment"] == "exclude_from_reliable_ucd_sample"
    }
    records, omitted = {}, []
    for row in development:
        source_id = identifier(row["gaia_dr3_id"])
        canonical_id = row["canonical_object_id"]
        reference_class = None
        if row["source_cohort"] == "sdss_dr16_qso":
            reference_class = "qso"
        elif row["source_cohort"] == "literature_ucd":
            if canonical_id in unreliable:
                omitted.append({"source_id": source_id, "reason": "reliability_review"})
                continue
            if canonical_id in source_exclusions or row["classification_state"] == "candidate":
                reference_class = "candidate"
            elif (
                row["classification_state"] == "confirmed"
                and row["primary_label_eligible"] == "True"
            ):
                reference_class = "ucd"
        if reference_class is None:
            continue
        current = canonical.get(canonical_id, {})
        if reference_class == "ucd" and current.get("classification_state") != "confirmed":
            raise ValueError(f"Current canonical state is not confirmed: {canonical_id}")
        if source_id in records:
            if records[source_id]["reference_class"] != reference_class:
                raise ValueError(f"Conflicting classes for {source_id}")
            raise ValueError(f"Duplicate teaching identity: {source_id}")
        names = atlas.get(canonical_id, {})
        coordinate_offset = None
        if names and names.get("adopted_ra") and names.get("adopted_dec"):
            coordinate_offset = float(
                SkyCoord(float(row["ra"]), float(row["dec"]), unit="deg")
                .separation(
                    SkyCoord(float(names["adopted_ra"]), float(names["adopted_dec"]), unit="deg")
                )
                .arcsec
            )
        records[source_id] = {
            "source_id": source_id,
            "gaia": measurements(row),
            "reference_class": reference_class,
            "name": names.get("original_names") or f"SDSS spectrum {row['source_object_id']}",
            "provenance": {
                "canonical_object_id": canonical_id,
                "publication_bibcode": row["publication_bibcode"],
                "catalog_id": row["catalog_id"],
                "source_row_locator": row["source_row_locator"],
                "source_detail": row["source_detail"],
                "label_basis": row["label_basis"],
                "host": names.get("host_galaxies", ""),
                "canonical_state": canonical.get(canonical_id, {}),
                "literature_position_offset_arcsec": coordinate_offset,
                "association_separation_arcsec": number(row["gaia_association_distance_arcsec"]),
                "source_status_exclusion_applied": canonical_id in source_exclusions,
            },
        }
    original_packet = json.loads(TEACHING_PACKET.read_text())
    for record in original_packet["objects"]:
        if record["source_id"] in example_ucd_ids:
            if record["source_id"] not in records:
                records[record["source_id"]] = {
                    "source_id": record["source_id"],
                    "gaia": measurements(record["gaia"]),
                    "reference_class": "ucd",
                    "name": record["name"],
                    "provenance": {
                        "literature": record["provenance"],
                        "paper_url": record["paper_url"],
                    },
                }
            records[record["source_id"]]["demonstration_context"] = {
                "host": record["host"],
                "distance_mpc": record["distance_mpc"],
                "distance_basis": record["distance_basis"],
                "paper_url": record["paper_url"],
                "name": record["name"],
                "reference_label": "Compact system: UCD / compact-elliptical boundary"
                if record["classification"] == "boundary_case"
                else "UCD",
                "note": "This system illustrates a physical classification boundary. Its unavailable Gaia astrometry is not zero motion."
                if record["classification"] == "boundary_case"
                else "",
            }
    stellar_manifest = json.loads(SPECTROSCOPIC_STELLAR_REFERENCE_MANIFEST.read_text())
    stellar_path = STELLAR_REFERENCE_DIR / stellar_manifest["external_pool"]
    if digest(stellar_path) != stellar_manifest["external_pool_sha256"]:
        raise ValueError("Stellar parent checksum no longer matches its provenance")
    stars = {}
    for table_row in Table.read(stellar_path):
        row = dict(zip(table_row.colnames, table_row, strict=True))
        source_id = identifier(row["source_id"])
        if str(row["spectroscopic_class"]) != "STAR":
            raise ValueError("Nonstellar class in spectroscopic stellar parent")
        if source_id in stars or source_id in records:
            raise ValueError(f"Duplicate or cross-class stellar identity: {source_id}")
        stars[source_id] = {
            "source_id": source_id,
            "gaia": measurements(row),
            "reference_class": "star",
            "name": f"SDSS spectrum {spectrum_identifier(row['specobjid'])}",
            "provenance": {
                "specobjid": spectrum_identifier(row["specobjid"]),
                "original_specobjid": str(row["specobjid"]),
                "subclass": str(row["subclass"]),
                "association_separation_arcsec": number(row["gaia_association_distance_arcsec"]),
                "label_basis": "SDSS DR16 primary spectrum STAR, zwarning=0; singleness not established",
            },
        }
    records.update(stars)
    reserved = set(example_ucd_ids + task1_ucd_ids)
    if not all(records[source_id]["reference_class"] == "ucd" for source_id in reserved):
        raise ValueError("Chosen UCD role includes an ineligible source")

    def matched_source(reference_class, magnitude):
        choices = [
            record
            for record in records.values()
            if record["reference_class"] == reference_class
            and record["source_id"] not in reserved
            and record["source_id"] not in unusable_gallery_ids
            and record["source_id"] not in insufficient_gallery_evidence_ids
            and abs(record["gaia"]["phot_g_mean_mag"] - magnitude) <= 0.12
            and -15 < record["gaia"]["dec"] < 65
            and (
                reference_class != "star"
                or (
                    record["gaia"]["proper_motion_significance"] is not None
                    and record["gaia"]["proper_motion_significance"] >= 4
                )
            )
        ]
        if not choices:
            raise ValueError(f"No comparable {reference_class} at G={magnitude}")
        choice = min(choices, key=lambda record: stable_order(record["source_id"]))
        reserved.add(choice["source_id"])
        return choice["source_id"]

    example_ids = list(example_ucd_ids)
    for reference_class in ["star", "qso"]:
        for magnitude in [18.3, 19.5]:
            example_ids.append(matched_source(reference_class, magnitude))
    task1_ids = list(task1_ucd_ids)
    for reference_class in ["star", "qso"]:
        for source_id in task1_ucd_ids:
            task1_ids.append(
                matched_source(reference_class, records[source_id]["gaia"]["phot_g_mean_mag"])
            )
    task1_ids.sort(
        key=lambda source_id: hashlib.sha256(
            f"presentation_order_v2:{source_id}".encode()
        ).hexdigest()
    )
    gallery = []
    key = {"version": "part1_reference_key_v2", "task1": {}, "examples": {}, "omitted": omitted}
    for role, identifiers in [("example", example_ids), ("task1", task1_ids)]:
        for index, source_id in enumerate(identifiers, 1):
            record = records[source_id]
            object_key = f"{role}_{index:02d}"
            evidence = {
                "source_id": source_id,
                "reference_class": record["reference_class"],
                "name": record["name"],
                "provenance": record["provenance"],
                "image_review": "pending",
                "evidence_audit": "pending",
            }
            key["task1" if role == "task1" else "examples"][object_key] = evidence
            item = {
                "object_key": object_key,
                "role": role,
                "source_id": source_id,
                "gaia": record["gaia"],
                "display_name": f"Object {index:02d}" if role == "task1" else record["name"],
                "images": {},
            }
            if role == "example":
                item["reference_class"] = record["reference_class"]
                item["context"] = record.get("demonstration_context", {})
            gallery.append(item)
    comparison = [
        record
        for record in records.values()
        if record["source_id"] not in reserved and record["reference_class"] != "star"
    ]
    minimum_g = min(record["gaia"]["phot_g_mean_mag"] for record in comparison)
    maximum_g = max(record["gaia"]["phot_g_mean_mag"] for record in comparison)
    eligible_stars = [
        record
        for record in stars.values()
        if record["source_id"] not in reserved
        and minimum_g <= record["gaia"]["phot_g_mean_mag"] <= maximum_g
    ]
    sampled_stars = sorted(eligible_stars, key=lambda record: stable_order(record["source_id"]))[
        :star_count
    ]
    comparison += sampled_stars
    comparison.sort(key=lambda record: stable_order(record["source_id"]))
    counts = dict(Counter(record["reference_class"] for record in comparison))
    key["task2_nonstellar_provenance"] = {
        record["source_id"]: record["provenance"]
        for record in comparison
        if record["reference_class"] != "star"
    }
    key["source_inputs"] = {
        str(path): digest(path)
        for path in [
            SELECTOR_DEVELOPMENT_FEATURES,
            CONFIRMED_UCD_DESIGN_REFERENCE_EXCLUSIONS,
            teaching_reliability_reviews,
            UCD_LEGACY_REFERENCE_TARGETS,
            teaching_canonical_reference,
            SPECTROSCOPIC_STELLAR_REFERENCE_MANIFEST,
            stellar_path,
            TEACHING_PACKET,
        ]
    }
    key["sampling"] = {
        "seed_prefix": "bubbletea_part1_v2:",
        "star_parent_count": len(stars),
        "eligible_star_count": len(eligible_stars),
        "requested_star_count": star_count,
        "magnitude_interval": [minimum_g, maximum_g],
        "task2_counts": counts,
        "validation_features_inspected": False,
        "gallery_image_exclusions": sorted(unusable_gallery_ids),
        "gallery_evidence_exclusions": sorted(insufficient_gallery_evidence_ids),
        "gallery_star_curation": "For introductory image/classification cards only, require the two-component proper-motion significance to be at least 4. This is not a one-dimensional four-sigma probability. Task 2 stars have no astrometric cut.",
        "notes": "Development sources plus benchmark-excluded stellar parent; no selector cuts on stars. Labeled M60 example reused from already-public v1 only.",
    }
    packet = {
        "activity_version": "bubbletea_part1_v2",
        "prepared_utc": datetime.now(UTC).isoformat(),
        "gallery": gallery,
        "catalog_columns": catalog_columns,
        "catalog_rows": [
            [
                record["source_id"],
                *[record["gaia"][field] for field in numeric_fields + derived_fields],
                record["reference_class"],
            ]
            for record in comparison
        ],
        "sampling": {
            name: value
            for name, value in key["sampling"].items()
            if not name.startswith("gallery_")
        },
        "reference_key_sha256": None,
    }
    write_json(teaching_part1_key, key)
    packet["reference_key_sha256"] = digest(teaching_part1_key)
    write_json(teaching_part1_packet, packet, compact=True)
    logger.info(
        "Prepared %d gallery objects and %s catalog rows; packet %d bytes",
        len(gallery),
        counts,
        teaching_part1_packet.stat().st_size,
    )


def acquire(pilot):
    packet = json.loads(teaching_part1_packet.read_text())
    teaching_part1_downloads.mkdir(parents=True, exist_ok=True)
    chosen = packet["gallery"]
    if pilot:
        chosen = [
            next(row for row in chosen if row.get("reference_class") == value)
            for value in ["ucd", "star", "qso"]
        ]
    for item in chosen:
        for scale, size, pixel_scale in [("close", 160, 0.262), ("context", 256, 0.8)]:
            url = "https://www.legacysurvey.org/viewer/jpeg-cutout?" + urlencode(
                {
                    "ra": item["gaia"]["ra"],
                    "dec": item["gaia"]["dec"],
                    "layer": "ls-dr11",
                    "size": size,
                    "pixscale": pixel_scale,
                }
            )
            path = teaching_part1_downloads / f"{item['source_id']}_{scale}_ls_dr11.jpg"
            try:
                if not path.exists():
                    content = request_bytes(url)
                    with Image.open(io.BytesIO(content)) as image:
                        image.load()
                        if image.format != "JPEG" or image.size != (size, size):
                            raise ValueError("Not the requested JPEG dimensions")
                    path.write_bytes(content)
                with Image.open(path) as image:
                    colors = len(image.convert("RGB").getcolors(size * size))
                item["images"][scale] = {
                    "cache_file": path.name,
                    "url": url,
                    "sha256": digest(path),
                    "layer": "ls-dr11",
                    "size_pixels": size,
                    "pixel_scale_arcsec": pixel_scale,
                    "field_width_arcsec": size * pixel_scale,
                    "unique_rgb_count": colors,
                    "content_status": "nonuniform" if colors > 10 else "placeholder",
                    "retrieved_utc": datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat(),
                }
                logger.info(
                    "%s %s: %s", item["object_key"], scale, item["images"][scale]["content_status"]
                )
            except Exception as error:
                item["images"][scale] = {
                    "content_status": "failed",
                    "url": url,
                    "reason": str(error),
                }
                logger.warning("%s %s: %s", item["object_key"], scale, error)
            write_json(teaching_part1_packet, packet, compact=True)
    logger.info("Acquisition checkpoint saved; visual review is still a separate required step")


def apply_reviews():
    """Attach explicit visual/evidence notes only to the exact inspected image bytes."""
    packet = json.loads(teaching_part1_packet.read_text())
    key = json.loads(teaching_part1_key.read_text())
    reviews = json.loads(teaching_part1_reviews.read_text())
    if set(reviews["objects"]) != {record["source_id"] for record in packet["gallery"]}:
        raise ValueError("Review identities differ from the current gallery")
    for record in packet["gallery"]:
        review = reviews["objects"][record["source_id"]]
        if review["status"] != "suitable_for_instructor_review":
            raise ValueError(f"Unaccepted teaching image: {record['source_id']}")
        for scale in ["close", "context"]:
            expected = review["image_sha256"][scale]
            image = record["images"][scale]
            if expected != image["sha256"] or expected != digest(
                teaching_part1_downloads / image["cache_file"]
            ):
                raise ValueError(f"Reviewed image changed: {record['source_id']} {scale}")
        reference = key["examples" if record["role"] == "example" else "task1"][
            record["object_key"]
        ]
        if reference["source_id"] != record["source_id"]:
            raise ValueError("Reference key does not match observations")
        reference["image_review"] = review["image_note"]
        reference["evidence_audit"] = review["evidence_note"]
        reference["manual_grading_required"] = True
    key["review_record_sha256"] = digest(teaching_part1_reviews)
    key["instructor_approval"] = "pending"
    key["grading_policy"] = reviews["grading_policy"]
    packet["sampling"] = {
        name: value for name, value in key["sampling"].items() if not name.startswith("gallery_")
    }
    write_json(teaching_part1_key, key)
    packet["reference_key_sha256"] = digest(teaching_part1_key)
    write_json(teaching_part1_packet, packet, compact=True)
    logger.info(
        "Attached %d explicit teaching reviews; instructor approval remains pending",
        len(reviews["objects"]),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--acquire", action="store_true")
    parser.add_argument("--review", action="store_true")
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--star-count", type=int, default=20000)
    args = parser.parse_args()
    if sum([args.prepare, args.acquire, args.review]) != 1 or args.star_count < 1:
        parser.error("Choose one of --prepare / --acquire / --review and a positive star count")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    if args.prepare:
        prepare(args.star_count)
    elif args.acquire:
        acquire(args.pilot)
    else:
        apply_reviews()


if __name__ == "__main__":
    main()
