"""Freeze the UCD reference host-association register.

Assign each of the 724 canonical reference objects one host-association state and,
where the evidence supports it, a resolved host name and adopted distance. This
register is an audited input to the visual review workbench; it never alters the
canonical literature database or object classifications.

Resolution policy (frozen by project-lead decisions on 2026-08-13):

- A single published galaxy name resolves to `verified_unique_host`.
- A published cluster or group name resolves to `published_environment_only`, and
  the cluster/group distance is adopted.
- A published galaxy pair ("X/Y") resolves to the named group because the two
  galaxies share a distance.
- An empty host field is resolved from the source publication's documented
  environment rather than left unknown.
- The 13 Voggel et al. 2020 "candidate stripped nuclei / luminous globular
  cluster" objects are excluded from the confirmed positive design reference.
"""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    CONFIRMED_UCD_DESIGN_REFERENCE_EXCLUSIONS,
    GALAXY_SAMPLE_CSV,
    HOST_ASSOCIATION_REGISTER,
    HOST_ASSOCIATION_REGISTER_CONTRACT,
    LITERATURE_REFERENCE_DB_V2,
    PROJECT_ROOT,
    UCD_LEGACY_REFERENCE_TARGETS,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase1_literature.build_validation_benchmark import connect_read_only

REGISTER_VERSION = "host_association_register_v1"

OUTPUT_CSV = HOST_ASSOCIATION_REGISTER
OUTPUT_CONTRACT = HOST_ASSOCIATION_REGISTER_CONTRACT
OUTPUT_EXCLUSIONS = CONFIRMED_UCD_DESIGN_REFERENCE_EXCLUSIONS

# Published host string -> (state, canonical host name).
HOST_STRING_RESOLUTION = {
    "M87": ("verified_unique_host", "M87"),
    "M87;Virgo cluster": ("verified_unique_host", "M87"),
    "M49": ("verified_unique_host", "M49"),
    "M59;Virgo cluster": ("verified_unique_host", "M59"),
    "M60": ("verified_unique_host", "M60"),
    "M85": ("verified_unique_host", "M85"),
    "Sombrero": ("verified_unique_host", "M104"),
    "NGC 3311": ("verified_unique_host", "NGC 3311"),
    "NGC 1399": ("verified_unique_host", "NGC 1399"),
    "NGC 4696": ("verified_unique_host", "NGC 4696"),
    "NGC 5128": ("verified_unique_host", "NGC 5128"),
    "NGC 4709": ("verified_unique_host", "NGC 4709"),
    "NGC 3923": ("verified_unique_host", "NGC 3923"),
    "NGC 4546": ("verified_unique_host", "NGC 4546"),
    "NGC 1336": ("verified_unique_host", "NGC 1336"),
    "Virgo cluster": ("published_environment_only", "Virgo cluster"),
    "Fornax cluster": ("published_environment_only", "Fornax cluster"),
    "NGC 1553/1549": ("published_environment_only", "Dorado group"),
    "NGC 1400/1407": ("published_environment_only", "NGC 1407 group"),
}

# Messier-name alias -> galaxy sample objname.
GALAXY_SAMPLE_ALIASES = {
    "M87": "MESSIER 087",
    "M49": "MESSIER 049",
    "M60": "MESSIER 060",
    "M59": "MESSIER 059",
    "M85": "MESSIER 085",
    "M104": "MESSIER 104",
}

# Group/cluster name -> (adopted_distance_mpc, distance_source).
CLUSTER_DISTANCES = {
    "Virgo cluster": (16.5, "Virgo cluster standard distance"),
    "Fornax cluster": (20.0, "Gregg 2009 / Saifollahi 2021 adopted cluster distance"),
    "Coma cluster": (100.0, "Chiboucas 2011 approximate cluster distance"),
    "Centaurus cluster": (43.0, "Mieske 2007 Centaurus cluster distance"),
}

# Group hosts whose distance comes from a member galaxy in the galaxy sample.
GROUP_MEMBER_DISTANCE = {
    "Dorado group": "NGC 1553",
    "NGC 1407 group": "NGC 1400",
}

# Verified hosts absent from the galaxy sample; source-level distances.
ABSENT_HOST_DISTANCES = {
    "NGC 5128": (3.8, "Voggel 2020 Centaurus A halo distance"),
    "NGC 3311": (50.7, "Misgeld 2011 Hydra I cluster distance"),
    "NGC 4696": (43.0, "Centaurus cluster distance (Mieske 2007)"),
    "NGC 4709": (43.0, "Centaurus cluster distance (Mieske 2007)"),
}

# Source publication -> environment for empty-host objects.
EMPTY_HOST_ENVIRONMENT = {
    "2009AJ....137..498G": ("published_environment_only", "Fornax cluster"),
    "2021MNRAS.504.3580S": ("published_environment_only", "Fornax cluster"),
    "2011ApJ...737...86C": ("published_environment_only", "Coma cluster"),
    "2020ApJ...899..140V": ("verified_unique_host", "NGC 5128"),
    "2019A&A...625A..50F": ("published_environment_only", "Virgo cluster"),
}

# The 13 Voggel 2020 candidate stripped-nucleus / luminous-GC objects.
EXCLUDED_VOGGEL_OBJECTS = {
    "canonical_00ae5b07b9cf5390ba173953832e14ec",
    "canonical_17804c7e74715d6ca3fe50787946d8de",
    "canonical_1db589dfa6de50a68f2551e19e22fd16",
    "canonical_1f25198096e95827a5aecdc802d30d79",
    "canonical_44ad081b22cc542a9505c1efb27ec836",
    "canonical_4a18b7fcd0b95832b2b2565874a33f5a",
    "canonical_60fa53999c875aba803f200901f0e863",
    "canonical_7cf56b44d12b50f9a7817b60a01acfef",
    "canonical_906cad5350875a2ca12a432e141e726f",
    "canonical_a55569533f1f597d80cbcc6afa5c7ee0",
    "canonical_b41649ef486152a888f26dcb5fc7439c",
    "canonical_d103508dbc135c0a9bade3b5055ceee7",
    "canonical_fe9a542f1d9f5a13ac4185e2be17e940",
}

EXCLUSION_REASON = (
    "Voggel 2020 candidate stripped nucleus or luminous globular cluster; "
    "source reports candidate status, not confirmed UCD"
)


def load_galaxy_sample() -> pd.DataFrame:
    """Load the ranked galaxy sample indexed by objname."""
    sample = pd.read_csv(GALAXY_SAMPLE_CSV, dtype={"objname": "string"})
    return sample.set_index("objname")


def load_empty_host_bibcodes() -> dict[str, set[str]]:
    """Map each empty-host object to its contributing bibcodes."""
    query = """
        SELECT co.canonical_object_id, p.bibcode
        FROM canonical_objects AS co
        JOIN object_record_associations AS ora
          ON ora.canonical_object_id = co.canonical_object_id
         AND ora.association_status = 'accepted'
        JOIN literature_records AS lr USING (record_id)
        JOIN datasets AS d USING (dataset_id)
        JOIN publications AS p USING (publication_id)
    """
    with connect_read_only(LITERATURE_REFERENCE_DB_V2) as connection:
        pairs = pd.read_sql_query(query, connection)
    mapping: dict[str, set[str]] = {}
    for canonical_object_id, bibcode in pairs.itertuples(index=False):
        mapping.setdefault(canonical_object_id, set()).add(bibcode)
    return mapping


def resolve_host(row: pd.Series, bibcodes: set[str]) -> dict:
    """Resolve one object's host state and host name."""
    host_string = row["host_galaxies"]
    if pd.isna(host_string):
        host_string = ""
    else:
        host_string = str(host_string).strip()
    if host_string:
        state, host_name = HOST_STRING_RESOLUTION[host_string]
        return {"host_association_state": state, "host_name": host_name}

    # Empty host: resolve from source publication environment.
    for bibcode in bibcodes:
        if bibcode in EMPTY_HOST_ENVIRONMENT:
            state, host_name = EMPTY_HOST_ENVIRONMENT[bibcode]
            return {"host_association_state": state, "host_name": host_name}
    return {"host_association_state": "host_unavailable", "host_name": None}


def host_measurements(host_name: str, galaxy_sample: pd.DataFrame) -> dict:
    """Attach coordinates, distance, and luminosity for a resolved host."""
    result = {
        "host_ra": None,
        "host_dec": None,
        "host_table_row": None,
        "adopted_distance_mpc": None,
        "distance_source": None,
        "M_Ks": None,
        "log_L_K": None,
    }
    lookup_name = GALAXY_SAMPLE_ALIASES.get(host_name, host_name)
    if lookup_name in galaxy_sample.index:
        row = galaxy_sample.loc[lookup_name]
        result.update(
            host_ra=float(row["ra"]),
            host_dec=float(row["dec"]),
            host_table_row=lookup_name,
            adopted_distance_mpc=float(row["dist_best"]),
            distance_source=str(row["dist_source"]),
            M_Ks=float(row["M_Ks"]) if pd.notna(row["M_Ks"]) else None,
            log_L_K=float(row["log_L_K"]) if pd.notna(row["log_L_K"]) else None,
        )
        return result

    # Group host whose distance comes from a member galaxy.
    member = GROUP_MEMBER_DISTANCE.get(host_name)
    if member and member in galaxy_sample.index:
        row = galaxy_sample.loc[member]
        result.update(
            adopted_distance_mpc=float(row["dist_best"]),
            distance_source=f"group member {member} ({row['dist_source']})",
        )
        return result

    # Cluster distance or absent-host source-level distance.
    if host_name in CLUSTER_DISTANCES:
        distance, source = CLUSTER_DISTANCES[host_name]
        result.update(adopted_distance_mpc=distance, distance_source=source)
    elif host_name in ABSENT_HOST_DISTANCES:
        distance, source = ABSENT_HOST_DISTANCES[host_name]
        result.update(adopted_distance_mpc=distance, distance_source=source)
    return result


def main() -> None:
    """Write the register, contract, and exclusions decision."""
    targets = pd.read_csv(UCD_LEGACY_REFERENCE_TARGETS, dtype={"canonical_object_id": "string"})
    galaxy_sample = load_galaxy_sample()
    empty_host_bibcodes = load_empty_host_bibcodes()

    rows = []
    for _, target in targets.iterrows():
        canonical_object_id = target["canonical_object_id"]
        resolved = resolve_host(target, empty_host_bibcodes.get(canonical_object_id, set()))
        measurements = host_measurements(resolved["host_name"], galaxy_sample)

        excluded = canonical_object_id in EXCLUDED_VOGGEL_OBJECTS
        if target["reference_cohort"] == "saifollahi_high_probability_candidate":
            membership = "candidate_saifollahi"
        elif excluded:
            membership = "excluded_stripped_nucleus_or_luminous_gc"
        else:
            membership = "include"

        rows.append(
            {
                "canonical_object_id": canonical_object_id,
                "reference_cohort": target["reference_cohort"],
                "host_association_state": resolved["host_association_state"],
                "host_name": resolved["host_name"],
                "design_reference_membership": membership,
                "exclusion_reason": EXCLUSION_REASON if excluded else None,
                **measurements,
            }
        )

    register = pd.DataFrame(rows)
    register = register.sort_values("canonical_object_id").reset_index(drop=True)

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    register.to_csv(OUTPUT_CSV, index=False)

    # Validation checks.
    checks = {
        "row_count_is_724": len(register) == 724,
        "states_are_allowed": register["host_association_state"].isin(
            {"verified_unique_host", "published_environment_only", "host_unavailable"}
        ).all(),
        "memberships_are_allowed": register["design_reference_membership"].isin(
            {"include", "candidate_saifollahi", "excluded_stripped_nucleus_or_luminous_gc"}
        ).all(),
        "no_host_unavailable_remains": (register["host_association_state"] != "host_unavailable").all(),
        "excluded_count_is_13": (register["design_reference_membership"] == "excluded_stripped_nucleus_or_luminous_gc").sum() == 13,
        "saifollahi_candidates_are_separate": (
            register.loc[
                register["reference_cohort"] == "saifollahi_high_probability_candidate",
                "design_reference_membership",
            ]
            == "candidate_saifollahi"
        ).all(),
        "saifollahi_never_in_confirmed_design_reference": (
            register.loc[
                register["reference_cohort"] == "saifollahi_high_probability_candidate",
                "design_reference_membership",
            ]
            != "include"
        ).all(),
    }
    checks = {name: bool(value) for name, value in checks.items()}

    contract = {
        "contract_version": REGISTER_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "approved_by_project_lead_2026-08-13",
        "plain_language_scope": (
            "Assign one host-association state and resolved host per canonical "
            "reference object under the project-lead host policy of 2026-08-13."
        ),
        "cohort_counts": register["reference_cohort"].value_counts().to_dict(),
        "host_state_counts": register["host_association_state"].value_counts().to_dict(),
        "membership_counts": register["design_reference_membership"].value_counts().to_dict(),
        "output": {
            "path": str(OUTPUT_CSV.relative_to(PROJECT_ROOT)),
            "sha256": calculate_sha256(OUTPUT_CSV),
        },
        "inputs": {
            str(UCD_LEGACY_REFERENCE_TARGETS.relative_to(PROJECT_ROOT)): calculate_sha256(
                UCD_LEGACY_REFERENCE_TARGETS
            ),
            str(GALAXY_SAMPLE_CSV.relative_to(PROJECT_ROOT)): calculate_sha256(GALAXY_SAMPLE_CSV),
            str(LITERATURE_REFERENCE_DB_V2.relative_to(PROJECT_ROOT)): calculate_sha256(
                LITERATURE_REFERENCE_DB_V2
            ),
        },
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    OUTPUT_CONTRACT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_CONTRACT.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")

    exclusions = {
        "decision_version": "confirmed_ucd_design_reference_exclusions_v1",
        "decided_at_utc": datetime.now(UTC).isoformat(),
        "decided_by": "project_lead_2026-08-13",
        "reason": EXCLUSION_REASON,
        "evidence": {
            "catalog_title": (
                "A Gaia-based Catalog of Candidate Stripped Nuclei and Luminous "
                "Globular Clusters in the Halo of Centaurus A"
            ),
            "publication_bibcode": "2020ApJ...899..140V",
            "source_reported_confirmation_status": "candidate",
            "original_name": "null (no published name)",
        },
        "canonical_object_ids": sorted(EXCLUDED_VOGGEL_OBJECTS),
        "count": len(EXCLUDED_VOGGEL_OBJECTS),
    }
    OUTPUT_EXCLUSIONS.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_EXCLUSIONS.write_text(json.dumps(exclusions, indent=2) + "\n", encoding="utf-8")

    if not all(checks.values()):
        raise RuntimeError(f"Host-association register freeze failed: {checks}")


if __name__ == "__main__":
    main()
