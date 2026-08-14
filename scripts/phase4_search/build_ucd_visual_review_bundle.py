"""Build the compact, application-ready review-input bundle.

Assemble one JSON object per canonical reference object from the frozen target,
host, image, Gaia, Legacy Survey, and external-catalog products. The web server
reads only this bundle; it never scans large FITS files or queries remote services
during review. One JSON file is written per object, plus a repository-tracked index
and manifest.
"""

import json
import sqlite3
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    HOST_ASSOCIATION_REGISTER,
    LITERATURE_REFERENCE_DB_V2,
    PROJECT_ROOT,
    UCD_LEGACY_REFERENCE_CUTOUT_MANIFEST,
    UCD_LEGACY_REFERENCE_GAIA_MEMBERSHIP,
    UCD_LEGACY_REFERENCE_TARGETS,
    UCD_LEGACY_REFERENCE_TRACTOR_MATCHES,
    UCD_VISUAL_REVIEW_BUNDLE_DIR,
    UCD_VISUAL_REVIEW_BUNDLE_INDEX,
    UCD_VISUAL_REVIEW_BUNDLE_MANIFEST,
    UCD_VISUAL_REVIEW_EXTERNAL_ASSOCIATIONS,
    UCD_VISUAL_REVIEW_GAIA_NEIGHBORS,
    UCD_VISUAL_REVIEW_WIDE_CUTOUT_MANIFEST,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256

BUNDLE_VERSION = "ucd_visual_review_bundle_v1"

FAHRION_TABLE = PROJECT_ROOT / "reference" / "fahrion2019" / "tableb1.dat"

# Fahrion et al. 2019 table B1 reference numbers -> discovery bibcodes (ReadMe note 1).
FAHRION_REF_BIBCODE = {
    0: "2019A&A...625A..50F",
    1: "2008A&A...487..921M",
    2: "2011AJ....142..199B",
    3: "2015ApJ...812...34L",
    4: "2011MNRAS.414..739N",
    5: "2003IAUJD...6E..18M",
    6: "2017MNRAS.468.4513M",
    7: "2007AJ....133.1722E",
    8: "2007A&A...472..111M",
    9: "2009A&A...498..705M",
    10: "2011MNRAS.414.3699M",
    11: "2004A&A...416..917G",
    12: "2015ApJ...808L..32S",
    13: "2016MNRAS.456..617J",
}


def safe(value: object) -> object:
    """Return a JSON-safe scalar, replacing NaN with None."""
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    if isinstance(value, (int, float, str, bool)):
        return value
    return str(value)


def row_to_dict(row: pd.Series) -> dict:
    """Convert a DataFrame row to a JSON-safe dict with NaN replaced by None."""
    return {str(key): safe(value) for key, value in row.items()}


def legacy_viewer_url(ra: float, dec: float) -> str:
    """Legacy Survey viewer centered on a coordinate."""
    return (
        f"https://www.legacysurvey.org/viewer/?ra={ra}&dec={dec}"
        f"&layer=ls-dr10&zoom=14"
    )


def gaia_archive_url(source_id: str) -> str:
    """Gaia Archive source page for a source identifier."""
    return f"https://gea.esac.esa.int/archive/?json={source_id}"


def simbad_url(ra: float, dec: float) -> str:
    """SIMBAD coordinate search."""
    return f"https://simbad.cds.unistra.fr/simbad/sim-coo?Coord={ra}+{dec}&Radius=2&Radius.unit=arcsec"


def ned_url(ra: float, dec: float) -> str:
    """NED near-position search."""
    return (
        "https://ned.ipac.caltech.edu/conesearch?"
        f"search_type=Near+Position+Search&ra={ra}&dec={dec}&radius=2"
    )


def ads_url(bibcode: str) -> str:
    """ADS abstract page for a bibcode."""
    return f"https://ui.adsabs.harvard.edu/abs/{bibcode}/abstract"


def build_links(core: dict) -> dict:
    """Build external link templates for an object."""
    ra = core["adopted_ra"]
    dec = core["adopted_dec"]
    links = {
        "legacy_viewer": legacy_viewer_url(ra, dec),
        "simbad": simbad_url(ra, dec),
        "ned": ned_url(ra, dec),
    }
    bibcodes = [
        code for code in str(core.get("publication_bibcodes") or "").split(";") if code
    ]
    links["ads"] = [ads_url(code) for code in bibcodes]
    gaia_ids = [code for code in str(core.get("gaia_dr3_ids") or "").split(";") if code]
    links["gaia_archive"] = [gaia_archive_url(code) for code in gaia_ids]
    return links


def load_indexed(path: Path, key: str) -> dict[str, list[dict]]:
    """Load a CSV and group its rows by a key column."""
    if not path.exists():
        return {}
    frame = pd.read_csv(path, dtype={"canonical_object_id": "string"})
    grouped: dict[str, list[dict]] = {}
    for row in frame.to_dict("records"):
        grouped.setdefault(str(row[key]), []).append(row_to_dict(pd.Series(row)))
    return grouped


def parse_tableb1_refs() -> list[int]:
    """Parse the Fahrion 2019 table B1 discovery-reference column."""
    refs = []
    for line in FAHRION_TABLE.read_text().splitlines():
        stripped = line.rstrip()
        if stripped:
            refs.append(int(stripped[-2:]))
    return refs


def discovery_map(targets: pd.DataFrame) -> dict[str, dict]:
    """Determine the earliest discovery bibcode per reference object.

    For objects sourced only from the Fahrion 2019 compilation, the true discovery
    is read from that table's reference column rather than the compilation year.
    """
    connection = sqlite3.connect(LITERATURE_REFERENCE_DB_V2)
    connection.row_factory = sqlite3.Row
    query = """
        SELECT co.canonical_object_id, p.bibcode, p.publication_year, p.title
        FROM canonical_objects AS co
        JOIN object_record_associations AS ora
          ON ora.canonical_object_id = co.canonical_object_id
         AND ora.association_status = 'accepted'
        JOIN literature_records AS lr USING (record_id)
        JOIN datasets AS d USING (dataset_id)
        JOIN publications AS p USING (publication_id)
    """
    object_bibcodes: dict[str, list[tuple[int | None, str]]] = defaultdict(list)
    bibcode_title: dict[str, tuple[int, str]] = {}
    for row in connection.execute(query):
        object_bibcodes[row["canonical_object_id"]].append(
            (row["publication_year"], row["bibcode"])
        )
        bibcode_title[row["bibcode"]] = (row["publication_year"] or 0, row["title"] or "")
    connection.close()

    fahrion_refs = parse_tableb1_refs()
    discovery: dict[str, dict] = {}
    for _, target in targets.iterrows():
        object_id = str(target["canonical_object_id"])
        rows = object_bibcodes.get(object_id, [])
        bibcodes = {bibcode for _, bibcode in rows}
        if bibcodes == {"2019A&A...625A..50F"}:
            locator = str(target["source_row_locators"] or "").split(";")[0]
            suffix = int(locator.rsplit("_", 1)[-1])
            bibcode = FAHRION_REF_BIBCODE.get(fahrion_refs[suffix], "2019A&A...625A..50F")
        else:
            _, bibcode = min(rows, key=lambda pair: (pair[0] or 9999, pair[1]))
        year, title = bibcode_title.get(bibcode, (int(bibcode[:4]), ""))
        discovery[object_id] = {
            "bibcode": bibcode,
            "year": year,
            "title": title,
            "ads_url": ads_url(bibcode),
        }
    return discovery


def main() -> None:
    """Assemble one JSON object per reference object plus index and manifest."""
    targets = pd.read_csv(UCD_LEGACY_REFERENCE_TARGETS, dtype={"gaia_dr3_ids": "string"})
    host_register = pd.read_csv(HOST_ASSOCIATION_REGISTER, dtype={"canonical_object_id": "string"})
    compact_images = load_indexed(UCD_LEGACY_REFERENCE_CUTOUT_MANIFEST, "canonical_object_id")
    wide_images = load_indexed(UCD_VISUAL_REVIEW_WIDE_CUTOUT_MANIFEST, "canonical_object_id")
    tractor = load_indexed(UCD_LEGACY_REFERENCE_TRACTOR_MATCHES, "canonical_object_id")
    gaia_membership = load_indexed(
        UCD_LEGACY_REFERENCE_GAIA_MEMBERSHIP, "canonical_object_id"
    )
    gaia_neighbors = load_indexed(UCD_VISUAL_REVIEW_GAIA_NEIGHBORS, "canonical_object_id")
    external = load_indexed(UCD_VISUAL_REVIEW_EXTERNAL_ASSOCIATIONS, "canonical_object_id")

    host_by_id = {
        str(row["canonical_object_id"]): row_to_dict(row)
        for row in host_register.to_dict("records")
    }
    discovery_by_id = discovery_map(targets)

    UCD_VISUAL_REVIEW_BUNDLE_DIR.mkdir(parents=True, exist_ok=True)
    index_rows = []
    for _, target in targets.iterrows():
        object_id = str(target["canonical_object_id"])
        core = row_to_dict(target)
        host = host_by_id.get(object_id, {})

        # Separate accepted-identifier evidence from positional neighbors.
        neighbors = gaia_neighbors.get(object_id, [])
        accepted = [row for row in neighbors if row.get("match_basis") == "accepted_identifier"]
        positional = [row for row in neighbors if row.get("match_basis") == "positional_neighbor"]
        membership = gaia_membership.get(object_id, [])

        document = {
            "canonical_object_id": object_id,
            "object": core,
            "host": host,
            "images": {
                "compact": compact_images.get(object_id, [{}])[0],
                "wide": wide_images.get(object_id, [{}])[0],
            },
            "gaia": {
                "accepted_membership": membership[0] if membership else None,
                "accepted_sources": accepted,
                "positional_neighbors": positional,
            },
            "legacy_survey": tractor.get(object_id, []),
            "external_catalogs": external.get(object_id, []),
            "discovery": discovery_by_id.get(object_id, {}),
            "links": build_links(core),
        }
        path = UCD_VISUAL_REVIEW_BUNDLE_DIR / f"{object_id}.json"
        path.write_text(json.dumps(document, sort_keys=True), encoding="utf-8")

        index_rows.append(
            {
                "canonical_object_id": object_id,
                "reference_cohort": core.get("reference_cohort"),
                "classification_state": core.get("classification_state"),
                "original_names": core.get("original_names"),
                "host_name": host.get("host_name"),
                "host_association_state": host.get("host_association_state"),
                "design_reference_membership": host.get("design_reference_membership"),
                "adopted_distance_mpc": host.get("adopted_distance_mpc"),
                "adopted_ra": core.get("adopted_ra"),
                "adopted_dec": core.get("adopted_dec"),
            }
        )

    index = pd.DataFrame(index_rows)
    index.to_csv(UCD_VISUAL_REVIEW_BUNDLE_INDEX, index=False)

    manifest = {
        "bundle_version": BUNDLE_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "bundle_complete",
        "object_count": len(index),
        "bundle_directory": str(
            UCD_VISUAL_REVIEW_BUNDLE_DIR.relative_to(UCD_VISUAL_REVIEW_BUNDLE_DIR.parents[2])
        ),
        "inputs": {
            str(UCD_LEGACY_REFERENCE_TARGETS.relative_to(PROJECT_ROOT)): calculate_sha256(
                UCD_LEGACY_REFERENCE_TARGETS
            ),
            str(HOST_ASSOCIATION_REGISTER.relative_to(PROJECT_ROOT)): calculate_sha256(
                HOST_ASSOCIATION_REGISTER
            ),
            str(UCD_LEGACY_REFERENCE_CUTOUT_MANIFEST.relative_to(PROJECT_ROOT)): calculate_sha256(
                UCD_LEGACY_REFERENCE_CUTOUT_MANIFEST
            ),
            str(UCD_VISUAL_REVIEW_WIDE_CUTOUT_MANIFEST.relative_to(PROJECT_ROOT)): calculate_sha256(
                UCD_VISUAL_REVIEW_WIDE_CUTOUT_MANIFEST
            ),
            str(UCD_LEGACY_REFERENCE_TRACTOR_MATCHES.relative_to(PROJECT_ROOT)): calculate_sha256(
                UCD_LEGACY_REFERENCE_TRACTOR_MATCHES
            ),
            str(UCD_LEGACY_REFERENCE_GAIA_MEMBERSHIP.relative_to(PROJECT_ROOT)): calculate_sha256(
                UCD_LEGACY_REFERENCE_GAIA_MEMBERSHIP
            ),
            str(UCD_VISUAL_REVIEW_GAIA_NEIGHBORS.relative_to(PROJECT_ROOT)): calculate_sha256(
                UCD_VISUAL_REVIEW_GAIA_NEIGHBORS
            ),
            str(UCD_VISUAL_REVIEW_EXTERNAL_ASSOCIATIONS.relative_to(PROJECT_ROOT)): calculate_sha256(
                UCD_VISUAL_REVIEW_EXTERNAL_ASSOCIATIONS
            ),
        },
        "outputs": {
            str(UCD_VISUAL_REVIEW_BUNDLE_INDEX.relative_to(PROJECT_ROOT)): calculate_sha256(
                UCD_VISUAL_REVIEW_BUNDLE_INDEX
            ),
        },
    }
    UCD_VISUAL_REVIEW_BUNDLE_MANIFEST.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
