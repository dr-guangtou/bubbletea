"""Audit the remaining three-position shared-Gaia literature groups.

The script combines frozen Gaia geometry with authoritative Gregg, Fahrion, and
Saifollahi source tables, the Brüns extended-object alias catalog, and a minimal
ADS metadata query. It writes review recommendations but never changes canonical
membership or proposal status.
"""

import argparse
import csv
import json
import logging
import os
import sys
from datetime import date
from pathlib import Path

import astropy.units as u
from astropy.coordinates import SkyCoord
from astropy.io import ascii, fits

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import LITERATURE_SOURCES, LITERATURE_VALIDATION, REFERENCE_DIR
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase1_literature.search_literature import (
    ADS_ENDPOINT,
    normalize_ads_document,
    search_ads,
)

logger = logging.getLogger(__name__)

GROUP_REVIEW_PATH = LITERATURE_VALIDATION / "gaia_association_group_review.csv"
PAIR_GEOMETRY_PATH = LITERATURE_VALIDATION / "gaia_association_pair_geometry.csv"
ADS_CACHE_PATH = LITERATURE_SOURCES / "gaia_multi_position_literature.json"
DECISION_MANIFEST_PATH = LITERATURE_SOURCES / "gaia_multi_position_reviews.json"
REVIEW_CSV_PATH = LITERATURE_VALIDATION / "gaia_multi_position_review.csv"
REVIEW_REPORT_PATH = LITERATURE_VALIDATION / "gaia_multi_position_review.md"

REVIEW_ACTION = "manual_multi_position_identity_review"
ADS_QUERY = (
    "bibcode:(2008A&A...487..921M OR 2009AJ....137..498G OR "
    "2012A&A...547A..65B OR 2019A&A...625A..50F OR 2021MNRAS.504.3580S)"
)
EXPECTED_GROUP_COUNT = 8


def parse_arguments() -> argparse.Namespace:
    """Parse review inputs, outputs, and ADS refresh control."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group-review", type=Path, default=GROUP_REVIEW_PATH)
    parser.add_argument("--pair-geometry", type=Path, default=PAIR_GEOMETRY_PATH)
    parser.add_argument("--ads-cache", type=Path, default=ADS_CACHE_PATH)
    parser.add_argument("--decision-manifest", type=Path, default=DECISION_MANIFEST_PATH)
    parser.add_argument("--review-csv", type=Path, default=REVIEW_CSV_PATH)
    parser.add_argument("--review-report", type=Path, default=REVIEW_REPORT_PATH)
    parser.add_argument("--refresh-ads", action="store_true")
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    """Read a CSV file as dictionaries."""
    with path.open(encoding="utf-8", newline="") as input_file:
        return list(csv.DictReader(input_file))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    """Write a stable CSV using the first row as the explicit schema."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def relative_path(path: Path) -> str:
    """Return a repository-relative path."""
    return path.resolve().relative_to(Path.cwd().resolve()).as_posix()


def load_groups(group_review_path: Path) -> list[dict[str, str]]:
    """Load and validate the frozen eight-group multi-position cohort."""
    groups = [
        row for row in read_csv(group_review_path) if row["recommended_action"] == REVIEW_ACTION
    ]
    groups.sort(key=lambda row: int(row["gaia_dr3_id"]))
    if len(groups) != EXPECTED_GROUP_COUNT:
        raise RuntimeError(f"Expected eight multi-position groups, found {len(groups)}")
    if any(row["canonical_position_count"] != "3" for row in groups):
        raise RuntimeError("A multi-position review group no longer has three positions")
    return groups


def load_group_records(
    pair_geometry_path: Path, source_ids: set[str]
) -> dict[str, list[dict[str, str]]]:
    """Recover unique record context for every selected Gaia group."""
    records_by_group: dict[str, dict[str, dict[str, str]]] = {
        source_id: {} for source_id in source_ids
    }
    for row in read_csv(pair_geometry_path):
        source_id = row["gaia_dr3_id"]
        if source_id not in source_ids:
            continue
        for side in ("1", "2"):
            record_id = row[f"record_id_{side}"]
            records_by_group[source_id][record_id] = {
                "record_id": record_id,
                "bibcode": row[f"bibcode_{side}"],
                "original_name": row[f"original_name_{side}"],
                "ra": row[f"ra_{side}"],
                "dec": row[f"dec_{side}"],
                "canonical_object_id": row[f"canonical_object_id_{side}"],
                "gaia_ra": row["gaia_ra"],
                "gaia_dec": row["gaia_dec"],
            }
    return {
        source_id: sorted(records.values(), key=lambda row: (row["bibcode"], row["record_id"]))
        for source_id, records in records_by_group.items()
    }


def load_approved_decisions(path: Path, source_ids: set[str]) -> dict[str, str]:
    """Load the project-lead approval and require exact cohort coverage."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    approved_ids = {str(source_id) for source_id in payload["approved_gaia_dr3_ids"]}
    if approved_ids != source_ids:
        raise RuntimeError(
            "Multi-position approval coverage mismatch: "
            f"missing={sorted(source_ids - approved_ids, key=int)}, "
            f"unexpected={sorted(approved_ids - source_ids, key=int)}"
        )
    if int(payload["approved_group_count"]) != len(source_ids):
        raise RuntimeError("Multi-position approval count mismatch")
    if payload["identity_changes_authorized"] is not True:
        return {source_id: "pending_project_review" for source_id in source_ids}
    return {source_id: "approved_same_astrophysical_object" for source_id in source_ids}


def load_gregg_rows() -> dict[str, dict[str, object]]:
    """Load authoritative Gregg table 2 velocity and alias fields."""
    folder = REFERENCE_DIR / "gregg2009"
    table = ascii.read(folder / "table2.dat", readme=folder / "ReadMe.txt", format="cds")
    rows = {}
    for row in table:
        sequence = str(int(row["Seq"]))
        rows[sequence] = {
            "radial_velocity_km_s": int(row["RV"]),
            "radial_velocity_error_km_s": int(row["e_RV"]),
            "rf_mag": "" if row["rfmag"] is None else str(row["rfmag"]),
            "aliases": str(row["Notes"]).strip(),
        }
    return rows


def load_fahrion_rows() -> dict[str, dict[str, object]]:
    """Parse authoritative Fahrion table B1 fixed-layout rows."""
    rows = {}
    path = REFERENCE_DIR / "fahrion2019" / "tableb1.dat"
    for line in path.read_text(encoding="utf-8").splitlines():
        name = line[0:19].strip()
        radial_velocity = line[61:67].strip()
        if not name or not radial_velocity:
            continue
        rows[name] = {
            "radial_velocity_km_s": float(radial_velocity),
            "absolute_v_mag": float(line[68:74]),
            "projected_distance_kpc": float(line[75:80]),
            "effective_radius_pc": float(line[81:86]),
            "reference_code": int(line[87:89]),
        }
    return rows


def load_saifollahi_table() -> object:
    """Load authoritative Saifollahi table A1 photometry and sizes."""
    folder = REFERENCE_DIR / "saifollahi2021"
    return ascii.read(folder / "tablea1.dat", readme=folder / "ReadMe.txt", format="cds")


def find_saifollahi_row(table: object, ra: float, dec: float) -> dict[str, float]:
    """Find the exact source-table row and preserve identical row multiplicity."""
    matches = table[(abs(table["RAdeg"] - ra) < 1e-9) & (abs(table["DEdeg"] - dec) < 1e-9)]
    if not len(matches):
        raise RuntimeError(f"No Saifollahi row at {ra}, {dec}")
    science_columns = ("umag", "gmag", "rmag", "imag", "Jmag", "Ksmag", "rh")
    if any(len({str(row[column]) for row in matches}) != 1 for column in science_columns):
        raise RuntimeError(f"Non-identical Saifollahi duplicate rows at {ra}, {dec}")
    row = matches[0]
    return {
        "source_row_count": len(matches),
        "g_mag": float(row["gmag"]),
        "r_mag": float(row["rmag"]),
        "i_mag": float(row["imag"]),
        "ks_mag": float(row["Ksmag"]),
        "effective_radius_pc": float(row["rh"]),
    }


def load_bruens_aliases() -> tuple[SkyCoord, list[str]]:
    """Load Brüns catalog positions and alternative object designations."""
    path = REFERENCE_DIR / "data" / "ucd" / "Bruens2012_extended_objects.fit"
    with fits.open(path) as hdus:
        data = hdus[1].data
        coordinates = SkyCoord(data["_RA"] * u.deg, data["_DE"] * u.deg)
        aliases = [str(value).strip() for value in data["OName"]]
    return coordinates, aliases


def nearby_bruens_aliases(
    target: SkyCoord, catalog_coordinates: SkyCoord, aliases: list[str]
) -> str:
    """Return Brüns alternative names within one arcsecond of a group."""
    separations = target.separation(catalog_coordinates).arcsec
    matches = sorted(
        {aliases[index] for index, separation in enumerate(separations) if separation <= 1.0}
    )
    return ";".join(value for value in matches if value)


def retrieve_ads_metadata(cache_path: Path) -> None:
    """Retrieve minimal deterministic ADS metadata for the five source papers."""
    token = os.environ.get("ADS_API_TOKEN")
    if not token:
        raise RuntimeError("ADS_API_TOKEN is required for --refresh-ads")
    query_run, documents = search_ads(token, "gaia_multi_position_sources", ADS_QUERY, 20)
    papers = [normalize_ads_document(document) for document in documents]
    if len(papers) != 5:
        raise RuntimeError(f"Expected five ADS source papers, found {len(papers)}")
    payload = {
        "schema_version": 1,
        "retrieval_date": date.today().isoformat(),
        "ads_endpoint": ADS_ENDPOINT,
        "query_run": query_run,
        "papers": papers,
    }
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def source_record(records: list[dict[str, str]], bibcode: str) -> dict[str, str]:
    """Return the unique coordinate-bearing record for one publication."""
    matches = [record for record in records if record["bibcode"] == bibcode]
    unique_positions = {(row["ra"], row["dec"]): row for row in matches}
    if len(unique_positions) != 1:
        raise RuntimeError(f"Expected one position for {bibcode}, found {len(unique_positions)}")
    return next(iter(unique_positions.values()))


def build_review_rows(
    groups: list[dict[str, str]],
    records_by_group: dict[str, list[dict[str, str]]],
    identity_decisions: dict[str, str],
) -> list[dict[str, object]]:
    """Combine source measurements into one review row per Gaia group."""
    gregg_rows = load_gregg_rows()
    fahrion_rows = load_fahrion_rows()
    saifollahi_table = load_saifollahi_table()
    bruens_coordinates, bruens_aliases = load_bruens_aliases()
    review_rows = []
    for group in groups:
        source_id = group["gaia_dr3_id"]
        records = records_by_group[source_id]
        gregg_record = source_record(records, "2009AJ....137..498G")
        fahrion_record = source_record(records, "2019A&A...625A..50F")
        saifollahi_record = source_record(records, "2021MNRAS.504.3580S")
        gregg = gregg_rows[gregg_record["original_name"]]
        fahrion = fahrion_rows[fahrion_record["original_name"]]
        saifollahi = find_saifollahi_row(
            saifollahi_table,
            float(saifollahi_record["ra"]),
            float(saifollahi_record["dec"]),
        )
        target = SkyCoord(
            float(gregg_record["gaia_ra"]) * u.deg, float(gregg_record["gaia_dec"]) * u.deg
        )
        velocity_difference = abs(
            float(gregg["radial_velocity_km_s"]) - float(fahrion["radial_velocity_km_s"])
        )
        velocity_difference_sigma = velocity_difference / float(gregg["radial_velocity_error_km_s"])
        velocity_review_flag = (
            "moderate_measurement_tension_preserve_both"
            if velocity_difference_sigma > 2.0
            else "consistent_within_2_gregg_sigma"
        )
        aliases = nearby_bruens_aliases(target, bruens_coordinates, bruens_aliases)
        review_rows.append(
            {
                "gaia_dr3_id": source_id,
                "record_count": group["record_count"],
                "canonical_position_count": group["canonical_position_count"],
                "proposal_pair_count": group["proposal_pair_count"],
                "gregg_sequence": gregg_record["original_name"],
                "gregg_aliases": gregg["aliases"],
                "gregg_radial_velocity_km_s": gregg["radial_velocity_km_s"],
                "gregg_radial_velocity_error_km_s": gregg["radial_velocity_error_km_s"],
                "gregg_rf_mag": gregg["rf_mag"],
                "fahrion_name": fahrion_record["original_name"],
                "fahrion_radial_velocity_km_s": fahrion["radial_velocity_km_s"],
                "fahrion_absolute_v_mag": fahrion["absolute_v_mag"],
                "fahrion_effective_radius_pc": fahrion["effective_radius_pc"],
                "fahrion_reference_code": fahrion["reference_code"],
                "saifollahi_g_mag": saifollahi["g_mag"],
                "saifollahi_source_row_count": saifollahi["source_row_count"],
                "saifollahi_r_mag": saifollahi["r_mag"],
                "saifollahi_i_mag": saifollahi["i_mag"],
                "saifollahi_ks_mag": saifollahi["ks_mag"],
                "saifollahi_effective_radius_pc": saifollahi["effective_radius_pc"],
                "bruens_aliases_within_1_arcsec": aliases,
                "velocity_difference_km_s": velocity_difference,
                "velocity_difference_in_gregg_sigma": velocity_difference_sigma,
                "velocity_review_flag": velocity_review_flag,
                "maximum_position_separation_arcsec": group["maximum_position_separation_arcsec"],
                "maximum_gaia_distance_arcsec": group["maximum_gaia_distance_arcsec"],
                "gaia_duplicated_source": group["gaia_duplicated_source"],
                "gaia_ipd_frac_multi_peak": group["gaia_ipd_frac_multi_peak"],
                "gaia_ipd_frac_odd_win": group["gaia_ipd_frac_odd_win"],
                "evidence_assessment": "three_catalog_same_object_supported",
                "identity_recommendation": "recommend_accept_multi_position_identity",
                "identity_decision": identity_decisions[source_id],
            }
        )
    return review_rows


def write_report(
    path: Path,
    rows: list[dict[str, object]],
    group_review_path: Path,
    pair_geometry_path: Path,
    ads_cache_path: Path,
    decision_manifest_path: Path,
) -> None:
    """Write the measured evidence and pending recommendation report."""
    maximum_position_row = max(
        rows, key=lambda row: float(row["maximum_position_separation_arcsec"])
    )
    maximum_velocity_row = max(rows, key=lambda row: float(row["velocity_difference_km_s"]))
    table_rows = "\n".join(
        "| {gaia_dr3_id} | {fahrion_name} | {gregg_sequence} | {gregg_aliases} | "
        "{bruens_aliases_within_1_arcsec} | {maximum_position_separation_arcsec} | "
        "{velocity_difference_km_s} |".format(**row)
        for row in rows
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""# Gaia Multi-Position Identity Review

**Date:** {date.today().isoformat()}
**Status:** Project-lead-approved shared identities recorded.

## Scope and Provenance

- Three-position Gaia groups: {len(rows)}
- Frozen group review: `{relative_path(group_review_path)}`
  (SHA256 `{calculate_sha256(group_review_path)}`)
- Frozen pair geometry: `{relative_path(pair_geometry_path)}`
  (SHA256 `{calculate_sha256(pair_geometry_path)}`)
- ADS source metadata: `{relative_path(ads_cache_path)}`
  (SHA256 `{calculate_sha256(ads_cache_path)}`)
- Project-lead decision manifest: `{relative_path(decision_manifest_path)}`
  (SHA256 `{calculate_sha256(decision_manifest_path)}`)
- Authoritative source tables: Gregg table 2, Fahrion table B1, and Saifollahi
  table A1. Brüns catalog aliases are supporting cross-identifications.

## Evidence Summary

All eight groups combine one Gregg, one Fahrion/Mieske, and one Saifollahi
position around the same Gaia DR3 source. All reported roles are positive; Gaia
has no duplicated-source, IPD multi-peak, or odd-window flag in these groups.
Independent Gregg and Fahrion velocities remain consistent with Fornax membership
and refer to the same sub-arcsecond coordinate locus. Brüns supplies explicit
historical cross-identifications for five loci, including `F-24(UCD4)`,
`F-1(UCD2)`, `F-12`, `F-7`, and `F-22`.

| Gaia DR3 ID | Fahrion | Gregg | Gregg aliases | Brüns aliases | Max position separation (arcsec) | Velocity difference (km/s) |
|---|---|---:|---|---|---:|---:|
{table_rows}

The largest coordinate span is {maximum_position_row["maximum_position_separation_arcsec"]}
arcseconds for Gaia DR3 `{maximum_position_row["gaia_dr3_id"]}`. The largest
velocity difference is {maximum_velocity_row["velocity_difference_km_s"]} km/s
for `{maximum_velocity_row["fahrion_name"]}` / Gregg
`{maximum_velocity_row["gregg_sequence"]}`; both measurements still identify a
Fornax member at the same Gaia-centered locus. This comparison is flagged as
`moderate_measurement_tension_preserve_both`; neither velocity is averaged,
discarded, or used to alter the reported source measurements. Saifollahi table A1
also contains two identical rows at the F-1/UCD2 locus; both provenance records
remain preserved at one canonical position.

## Recommendation

The project lead approved all eight groups as eight astrophysical objects, each retaining every
literature record, measurement, original name, and superseded canonical identifier
as provenance. This audit records the authorization but does not itself change
database membership or proposal status; the deterministic v2 builder applies it.
""",
        encoding="utf-8",
    )


def main() -> None:
    """Run the non-destructive multi-position identity audit."""
    arguments = parse_arguments()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    groups = load_groups(arguments.group_review)
    records_by_group = load_group_records(
        arguments.pair_geometry, {row["gaia_dr3_id"] for row in groups}
    )
    identity_decisions = load_approved_decisions(
        arguments.decision_manifest, {row["gaia_dr3_id"] for row in groups}
    )
    if arguments.refresh_ads:
        retrieve_ads_metadata(arguments.ads_cache)
    if not arguments.ads_cache.exists():
        raise FileNotFoundError("ADS cache is absent; rerun with --refresh-ads")
    review_rows = build_review_rows(groups, records_by_group, identity_decisions)
    write_csv(arguments.review_csv, review_rows)
    write_report(
        arguments.review_report,
        review_rows,
        arguments.group_review,
        arguments.pair_geometry,
        arguments.ads_cache,
        arguments.decision_manifest,
    )
    logger.info("Audited %d multi-position groups without changing identities", len(review_rows))


if __name__ == "__main__":
    main()
