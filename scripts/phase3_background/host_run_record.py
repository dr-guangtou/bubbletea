"""Build permanent per-galaxy receipts for one declared analysis run."""

import hashlib
import json
import os
import re
from pathlib import Path
from uuid import uuid4


def canonical_json_text(content: dict[str, object]) -> str:
    """Return stable JSON text for hashing and exact-content comparison."""
    return json.dumps(content, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def content_sha256(content: dict[str, object]) -> str:
    """Return the stable SHA-256 identifier of JSON-compatible content."""
    return hashlib.sha256(canonical_json_text(content).encode()).hexdigest()


def run_identifier(configuration: dict[str, object]) -> str:
    """Return a stable identifier derived only from one run's declared configuration."""
    return f"run_{content_sha256(configuration)[:20]}"


def host_run_identifier(
    run_id: str, host_name: str, host_ra_deg: float, host_dec_deg: float
) -> str:
    """Return a stable identifier for one host within one declared run."""
    identity = {
        "run_id": run_id,
        "host_name": host_name,
        "host_ra_deg": host_ra_deg,
        "host_dec_deg": host_dec_deg,
    }
    return f"host_{content_sha256(identity)[:20]}"


def snake_case_name(value: str) -> str:
    """Return a filesystem-safe snake_case form of a host name."""
    normalized = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    if not normalized:
        raise ValueError("Host name must contain a letter or number")
    return normalized


def host_record_path(
    records_directory: Path, run_id: str, host_name: str, host_run_id: str
) -> Path:
    """Return the permanent path for one host receipt."""
    return records_directory / run_id / f"{snake_case_name(host_name)}_{host_run_id}.json"


def write_immutable_json(path: Path, content: dict[str, object]) -> str:
    """Create one JSON file atomically and refuse to replace different content."""
    formatted = json.dumps(content, indent=2, sort_keys=True) + "\n"
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if existing != formatted:
            raise FileExistsError(f"Refusing to overwrite a different run receipt: {path}")
        return "existing_identical"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    temporary_path.write_text(formatted, encoding="utf-8")
    try:
        os.link(temporary_path, path)
        return "created"
    except FileExistsError:
        existing = path.read_text(encoding="utf-8")
        if existing != formatted:
            raise FileExistsError(f"Refusing to overwrite a different run receipt: {path}")
        return "existing_identical"
    finally:
        temporary_path.unlink(missing_ok=True)
