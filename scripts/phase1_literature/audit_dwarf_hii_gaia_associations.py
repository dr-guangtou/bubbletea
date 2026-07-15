"""Measure van Zee dwarf-galaxy H II-to-Gaia separations against controls."""

import argparse
import hashlib
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
from pyvo.dal import tap

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    DWARF_HII_GAIA_ASSOCIATION_CALIBRATION,
    DWARF_HII_GAIA_ASSOCIATION_CANDIDATES,
    LITERATURE_REFERENCE_DB_V2,
)
from scripts.phase1_literature.audit_hii_gaia_associations import (
    CALIBRATION_RADII_ARCSEC,
    CONTROL_OFFSETS_ARCSEC,
    build_candidates,
    displaced_coordinates,
    field_geometry,
    nearest_distances,
    retrieve_gaia_field,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase1_literature.build_validation_benchmark import (
    VIZIER_TAP_URL,
    build_literature_benchmark_rows,
    serialize_path,
)

logger = logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    """Parse output paths and bounded smoke-run controls."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-database", type=Path, default=LITERATURE_REFERENCE_DB_V2)
    parser.add_argument("--candidates", type=Path, default=DWARF_HII_GAIA_ASSOCIATION_CANDIDATES)
    parser.add_argument("--calibration", type=Path, default=DWARF_HII_GAIA_ASSOCIATION_CALIBRATION)
    parser.add_argument("--limit-galaxies", type=int)
    return parser.parse_args()


def retrieve_regions() -> tuple[pd.DataFrame, str]:
    """Retrieve and consolidate repeated spectra of the same H II position."""
    query = '''SELECT "Galaxy", "Slit", "EW", "NS", "Halpha", "F(Hbeta)",
                      "_RA", "_DE", "recno"
               FROM "J/ApJ/636/214/table3"
               ORDER BY "Galaxy", "Slit", "EW", "NS"'''
    service = tap.TAPService(VIZIER_TAP_URL)
    raw = service.run_sync(query, maxrec=100).to_table().to_pandas()
    raw = raw.rename(columns={"Galaxy": "galaxy", "_RA": "hii_ra", "_DE": "hii_dec"})
    rows = []
    for (galaxy, hii_ra, hii_dec), group in raw.groupby(["galaxy", "hii_ra", "hii_dec"], sort=True):
        rows.append(
            {
                "galaxy": galaxy,
                "hii_ra": hii_ra,
                "hii_dec": hii_dec,
                "source_record_numbers": ";".join(
                    str(int(value)) for value in sorted(group["recno"])
                ),
                "slit_measurements": ";".join(
                    f"{row.Slit}:{int(row.EW)}:{int(row.NS)}" for row in group.itertuples()
                ),
                "spectroscopic_measurement_count": len(group),
                "maximum_halpha_to_hbeta": float(group["Halpha"].max()),
                "maximum_hbeta_flux_1e18_w_m2": float(group["F(Hbeta)"].max()),
            }
        )
    return pd.DataFrame(rows), query


def main() -> None:
    """Run the dwarf H II separation-control audit without changing labels."""
    arguments = parse_arguments()
    if arguments.limit_galaxies is not None and arguments.limit_galaxies <= 0:
        raise ValueError("--limit-galaxies must be positive")
    literature_rows = build_literature_benchmark_rows(arguments.reference_database)
    minimum_g = float(literature_rows["phot_g_mean_mag"].min())
    maximum_g = float(literature_rows["phot_g_mean_mag"].max())
    regions, source_query = retrieve_regions()
    galaxies = sorted(regions["galaxy"].unique())
    if arguments.limit_galaxies is not None:
        galaxies = galaxies[: arguments.limit_galaxies]
        regions = regions.loc[regions["galaxy"].isin(galaxies)].copy()

    candidate_frames = []
    gaia_queries = []
    real_distances: list[float] = []
    control_distances: list[float] = []
    field_counts = []
    for galaxy in galaxies:
        galaxy_regions = regions.loc[regions["galaxy"] == galaxy].copy()
        center_ra, center_dec, radius_arcsec = field_geometry(galaxy_regions)
        sources, query = retrieve_gaia_field(
            galaxy, center_ra, center_dec, radius_arcsec, minimum_g, maximum_g
        )
        gaia_queries.append({"galaxy": galaxy, "query": query})
        candidates = build_candidates(galaxy_regions, sources)
        candidate_frames.append(candidates)
        field_real = candidates["nearest_distance_arcsec"].to_numpy()
        real_distances.extend(field_real.tolist())
        field_controls: list[float] = []
        for ra_offset, dec_offset in CONTROL_OFFSETS_ARCSEC:
            control_ra, control_dec = displaced_coordinates(galaxy_regions, ra_offset, dec_offset)
            _, distances = nearest_distances(control_ra, control_dec, sources)
            control_distances.extend(distances.tolist())
            field_controls.extend(distances.tolist())
        control_array = np.asarray(field_controls)
        field_counts.append(
            {
                "galaxy": galaxy,
                "hii_region_count": len(galaxy_regions),
                "gaia_source_count": len(sources),
                "cumulative_separation_counts": [
                    {
                        "radius_arcsec": radius,
                        "real_match_count": int(np.sum(field_real <= radius)),
                        "control_match_mean_per_offset": float(
                            np.sum(control_array <= radius) / len(CONTROL_OFFSETS_ARCSEC)
                        ),
                    }
                    for radius in CALIBRATION_RADII_ARCSEC
                ],
            }
        )

    candidates = pd.concat(candidate_frames, ignore_index=True)
    candidates["gaia_dr3_id"] = candidates["source_id"].map(
        lambda value: str(int(value)) if not pd.isna(value) else None
    )
    candidates["association_status"] = "exploratory_not_approved"
    candidates["publication_bibcode"] = "2006ApJ...636..214V"
    candidates["catalog_id"] = "J/ApJ/636/214/table3"
    candidates["source_row_locator"] = candidates["source_record_numbers"].map(
        lambda value: f"recno={value}"
    )
    arguments.candidates.parent.mkdir(parents=True, exist_ok=True)
    candidates.to_csv(arguments.candidates, index=False)

    real_array = np.asarray(real_distances)
    control_array = np.asarray(control_distances)
    cumulative = []
    for radius in CALIBRATION_RADII_ARCSEC:
        real_count = int(np.sum(real_array <= radius))
        control_mean = float(np.sum(control_array <= radius) / len(CONTROL_OFFSETS_ARCSEC))
        selected = candidates.loc[candidates["nearest_distance_arcsec"] <= radius]
        unique_sources = int(selected["gaia_dr3_id"].nunique())
        excess = real_count - control_mean
        cumulative.append(
            {
                "radius_arcsec": radius,
                "real_match_count": real_count,
                "unique_gaia_source_count": unique_sources,
                "repeated_source_assignment_count": real_count - unique_sources,
                "control_match_mean_per_offset": control_mean,
                "estimated_excess_count": excess,
                "estimated_excess_fraction": excess / real_count if real_count else None,
            }
        )
    report = {
        "generated_utc": datetime.now(UTC).isoformat(),
        "status": "exploratory_not_approved",
        "publication_bibcode": "2006ApJ...636..214V",
        "doi": "10.1086/498017",
        "catalog_id": "J/ApJ/636/214/table3",
        "smoke_limit_galaxies": arguments.limit_galaxies,
        "magnitude_domain": [minimum_g, maximum_g],
        "magnitude_domain_source": serialize_path(arguments.reference_database),
        "coordinate_note": "CDS positions derived from published galaxy centers and integer arcsecond slit offsets",
        "control_offsets_arcsec": CONTROL_OFFSETS_ARCSEC,
        "source_query": source_query,
        "gaia_queries": gaia_queries,
        "query_sha256": hashlib.sha256(
            json.dumps([source_query, gaia_queries], sort_keys=True).encode()
        ).hexdigest(),
        "field_counts": field_counts,
        "cumulative_separation_counts": cumulative,
        "candidate_output": serialize_path(arguments.candidates),
        "candidate_output_sha256": calculate_sha256(arguments.candidates),
    }
    arguments.calibration.parent.mkdir(parents=True, exist_ok=True)
    arguments.calibration.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    logger.info("Wrote %d unique dwarf H II positions", len(candidates))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
