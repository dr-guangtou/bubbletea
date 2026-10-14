"""Retrieve a bounded Gaia/Legacy Survey teaching snapshot without scientific writes.

Inputs: data/teaching/targets_v1.json and explicit --execute permission.
Outputs: a small versioned teaching packet and external cached JPEGs/HTTP records.
Run a one-object --limit 1 acquisition before the complete six-object acquisition.
Requests are serial, rate-limited, and checkpointed; students never run this script.
"""

import argparse
import csv
import hashlib
import io
import json
import logging
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from PIL import Image

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import TEACHING_DOWNLOAD_DIR, TEACHING_PACKET, TEACHING_TARGETS

logger = logging.getLogger(__name__)
gaia_endpoint = "https://gea.esac.esa.int/tap-server/tap/sync"
image_endpoint = "https://www.legacysurvey.org/viewer/jpeg-cutout"
gaia_columns = (
    "source_id,ra,dec,ref_epoch,phot_g_mean_mag,bp_rp,parallax,parallax_error,"
    "pmra,pmra_error,pmdec,pmdec_error,pmra_pmdec_corr,astrometric_params_solved,"
    "ruwe,astrometric_excess_noise,astrometric_excess_noise_sig,phot_bp_rp_excess_factor"
)
image_scales = {"close": (128, 0.262), "context": (256, 0.8)}


def request_bytes(url: str) -> bytes:
    """Request serially with bounded retries and a short rate-limit backoff."""
    for attempt in range(3):
        time.sleep(2)
        try:
            with urlopen(
                Request(url, headers={"User-Agent": "BubbleTea-Teaching/1.0"}), timeout=25
            ) as response:
                return response.read()
        except HTTPError as error:
            if error.code not in {429, 500, 502, 503, 504} or attempt == 2:
                raise
            time.sleep(min(20, 5 * (attempt + 1)))
        except (URLError, TimeoutError):
            if attempt == 2:
                raise
            time.sleep(5)
    raise RuntimeError("Request attempts exhausted")


def read_gaia(targets: list[dict]) -> tuple[dict, dict]:
    """Keep original CSV bytes and identifiers as strings; null numbers stay null."""
    identifiers = [target["source_id"] for target in targets]
    if not all(len(identifier) == 19 and identifier.isdigit() for identifier in identifiers):
        raise ValueError("Invalid Gaia identifier in teaching definition")
    query = f"SELECT {gaia_columns} FROM gaiadr3.gaia_source WHERE source_id IN ({','.join(identifiers)})"
    url = (
        gaia_endpoint
        + "?"
        + urlencode({"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": query})
    )
    cache_name = "gaia_" + hashlib.sha256(query.encode()).hexdigest()[:16] + ".csv"
    path = TEACHING_DOWNLOAD_DIR / cache_name
    if not path.exists():
        path.write_bytes(request_bytes(url))
    rows = list(csv.DictReader(io.StringIO(path.read_text())))
    if {row["source_id"] for row in rows} != set(identifiers) or len(rows) != len(targets):
        raise RuntimeError("Gaia response does not contain exactly the requested sources")
    parsed = {}
    for row in rows:
        parsed[row["source_id"]] = {
            key: value if key == "source_id" else (float(value) if value else None)
            for key, value in row.items()
        }
    return parsed, {
        "endpoint": gaia_endpoint,
        "query": query,
        "csv_cache_file": cache_name,
        "csv_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "snapshot_date_utc": datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat(),
    }


def retrieve_image(target: dict, scale: str, gaia: dict) -> dict:
    """Record a validated download, including a reproducible URL and content hash."""
    size, pixel_scale = image_scales[scale]
    parameters = {
        "ra": gaia["ra"],
        "dec": gaia["dec"],
        "layer": "ls-dr11",
        "pixscale": pixel_scale,
        "size": size,
    }
    url = image_endpoint + "?" + urlencode(parameters)
    filename = f"{target['object_key']}_{scale}_ls_dr11.jpg"
    path = TEACHING_DOWNLOAD_DIR / filename
    if not path.exists():
        path.write_bytes(request_bytes(url))
    content = path.read_bytes()
    with Image.open(io.BytesIO(content)) as image:
        image.load()
        if image.format != "JPEG" or image.size != (size, size):
            raise RuntimeError(f"Invalid image response: {filename}")
        colors = image.convert("RGB").getcolors(size * size)
        unique_colors = len(colors)
    return {
        "cache_file": filename,
        "url": url,
        "layer": "ls-dr11",
        "size_pixels": size,
        "pixel_scale_arcsec": pixel_scale,
        "field_width_arcsec": size * pixel_scale,
        "unique_rgb_count": unique_colors,
        "content_status": "nonuniform" if unique_colors > 10 else "placeholder",
        "sha256": hashlib.sha256(content).hexdigest(),
        "retrieved_utc": datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat(),
        "visual_review_status": "pending",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--limit", type=int)
    arguments = parser.parse_args()
    if not arguments.execute:
        parser.error("Network access requires --execute")
    if arguments.limit is not None and not 1 <= arguments.limit <= 6:
        parser.error("--limit must be between 1 and 6")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    start = time.monotonic()
    definition = json.loads(TEACHING_TARGETS.read_text())
    targets = definition["objects"][: arguments.limit]
    TEACHING_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    gaia, retrieval = read_gaia(targets)
    packet = {
        "packet_version": definition["packet_version"],
        "selection_note": definition["selection_note"],
        "gaia_retrieval": retrieval,
        "objects": [],
    }
    for target in targets:
        source = gaia[target["source_id"]]
        record = dict(target, gaia=source, images={})
        for scale in image_scales:
            record["images"][scale] = retrieve_image(target, scale, source)
            logger.info(
                "Checked %s %s: %s",
                target["name"],
                scale,
                record["images"][scale]["content_status"],
            )
        record["external_catalog_checks"] = (
            "Not checked in this teaching packet; no negative inference permitted."
        )
        packet["objects"].append(record)
    packet["acquisition_seconds"] = time.monotonic() - start
    output = TEACHING_DOWNLOAD_DIR / "pilot_packet.json" if arguments.limit else TEACHING_PACKET
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(packet, indent=2) + "\n")
    logger.info(
        "Wrote %d objects in %.3f seconds to %s",
        len(targets),
        packet["acquisition_seconds"],
        output,
    )


if __name__ == "__main__":
    main()
