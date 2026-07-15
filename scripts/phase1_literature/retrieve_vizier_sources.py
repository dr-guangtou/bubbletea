"""Retrieve original VizieR ReadMe and machine-readable tables with provenance.

Downloads are limited to files below the repository's 10 MiB commit boundary.
Every retrieved file is hashed and recorded. Existing reference folders are never
renamed or deleted.
"""

import argparse
import hashlib
import json
import logging
import re
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import LITERATURE_SOURCES, LITERATURE_VALIDATION, REFERENCE_DIR

logger = logging.getLogger(__name__)

CDS_ROOT = "https://cdsarc.cds.unistra.fr/ftp"
MAXIMUM_FILE_BYTES = 10 * 1024 * 1024
RETRIEVAL_MANIFEST = LITERATURE_SOURCES / "vizier_retrieval_manifest.json"
DATA_FILE_PATTERN = re.compile(r"^\s*([A-Za-z0-9_.-]+\.dat(?:\.gz)?)\s+", re.MULTILINE)


def parse_arguments() -> argparse.Namespace:
    """Parse manifest and output paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=RETRIEVAL_MANIFEST)
    parser.add_argument("--reference-directory", type=Path, default=REFERENCE_DIR)
    parser.add_argument(
        "--report", type=Path, default=LITERATURE_VALIDATION / "vizier_retrieval.json"
    )
    parser.add_argument("--bibcode", help="Retrieve only one configured bibcode")
    return parser.parse_args()


def sha256_bytes(content: bytes) -> str:
    """Hash downloaded content."""
    return hashlib.sha256(content).hexdigest()


def retrieve(url: str) -> tuple[bytes, int | None]:
    """Retrieve one file and enforce the repository size boundary."""
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "BubbleTea-UCD-Research/1.0"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        content_length = response.headers.get("Content-Length")
        declared_bytes = int(content_length) if content_length is not None else None
        if declared_bytes is not None and declared_bytes > MAXIMUM_FILE_BYTES:
            raise ValueError(f"Remote file exceeds 10 MiB boundary: {url}")
        content = response.read(MAXIMUM_FILE_BYTES + 1)
    if len(content) > MAXIMUM_FILE_BYTES:
        raise ValueError(f"Downloaded file exceeds 10 MiB boundary: {url}")
    return content, declared_bytes


def provenance_readme(source: dict[str, str], files: list[dict[str, object]]) -> str:
    """Generate a concise provenance README for a retrieved catalog package."""
    file_rows = "\n".join(
        f"| `{item['file_name']}` | {item['byte_count']} | `{item['sha256']}` |" for item in files
    )
    return f"""# {source["bibcode"]}

**ADS Bibcode:** `{source["bibcode"]}`
**VizieR Catalog:** `{source["catalog_root"]}`
**Retrieval Date:** {date.today().isoformat()}
**Retrieval Base:** `{CDS_ROOT}/{source["catalog_root"]}/`

## Files

| File | Bytes | SHA-256 |
|---|---:|---|
{file_rows}

The files in this directory are original VizieR archive products. The generated
hashes and archive paths are the provenance authority for subsequent ingestion.
No scientific classification is inferred from catalog membership alone.
"""


def retrieve_source(source: dict[str, str], reference_directory: Path) -> dict[str, object]:
    """Retrieve one catalog package and return its manifest entry."""
    folder = reference_directory / source["reference_folder"]
    folder.mkdir(parents=True, exist_ok=True)
    base_url = f"{CDS_ROOT}/{source['catalog_root']}"
    readme_content, _ = retrieve(f"{base_url}/ReadMe")
    readme_text = readme_content.decode("utf-8", errors="replace")
    file_names = source.get("files") or sorted(set(DATA_FILE_PATTERN.findall(readme_text)))
    retrieved_files = []

    readme_path = folder / "ReadMe.txt"
    readme_path.write_bytes(readme_content)
    retrieved_files.append(
        {
            "file_name": readme_path.name,
            "byte_count": len(readme_content),
            "sha256": sha256_bytes(readme_content),
            "source_url": f"{base_url}/ReadMe",
        }
    )
    for file_name in file_names:
        source_url = f"{base_url}/{file_name}"
        output_file_name = file_name
        try:
            content, declared_bytes = retrieve(source_url)
        except urllib.error.HTTPError as error:
            if error.code != 404 or file_name.endswith(".gz"):
                raise
            output_file_name = f"{file_name}.gz"
            source_url = f"{base_url}/{output_file_name}"
            content, declared_bytes = retrieve(source_url)
        output_path = folder / output_file_name
        output_path.write_bytes(content)
        retrieved_files.append(
            {
                "file_name": output_file_name,
                "byte_count": len(content),
                "declared_bytes": declared_bytes,
                "sha256": sha256_bytes(content),
                "source_url": source_url,
            }
        )
    readme_markdown = folder / "README.md"
    if not readme_markdown.exists() or source["reference_folder"] != "voggel2020":
        readme_markdown.write_text(
            provenance_readme(source, retrieved_files),
            encoding="utf-8",
        )
    return {
        **source,
        "retrieval_status": "complete",
        "files": retrieved_files,
    }


def main() -> None:
    """Retrieve every configured VizieR package sequentially."""
    arguments = parse_arguments()
    with arguments.manifest.open(encoding="utf-8") as input_file:
        sources = json.load(input_file)["sources"]
    if arguments.bibcode:
        sources = [source for source in sources if source["bibcode"] == arguments.bibcode]
        if not sources:
            raise ValueError(f"Bibcode is not configured: {arguments.bibcode}")
    results = []
    for source in sources:
        logger.info("Retrieving %s", source["catalog_root"])
        try:
            results.append(retrieve_source(source, arguments.reference_directory))
        except Exception as error:
            logger.error("Failed to retrieve %s: %s", source["catalog_root"], error)
            results.append(
                {
                    **source,
                    "retrieval_status": "failed",
                    "error": str(error),
                    "files": [],
                }
            )
    arguments.report.parent.mkdir(parents=True, exist_ok=True)
    with arguments.report.open("w", encoding="utf-8") as output_file:
        json.dump(
            {
                "retrieval_date": date.today().isoformat(),
                "cds_root": CDS_ROOT,
                "sources": results,
            },
            output_file,
            indent=2,
            sort_keys=True,
        )
        output_file.write("\n")
    failed_sources = [source for source in results if source["retrieval_status"] != "complete"]
    if failed_sources:
        raise RuntimeError(f"VizieR retrieval failed for {len(failed_sources)} sources")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
