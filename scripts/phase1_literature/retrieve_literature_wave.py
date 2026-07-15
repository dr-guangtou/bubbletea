"""Retrieve approved literature PDFs and record source-package provenance.

The script uses one sequential connection, enforces the manifest request interval,
validates PDF and XLSX structure, and records all files and hashes. It never
changes database membership, object identity, or confirmation state.
"""

import argparse
import hashlib
import json
import logging
import sys
import time
import urllib.request
import zipfile
from datetime import date
from pathlib import Path
from xml.etree import ElementTree

from pypdf import PdfReader

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    LITERATURE_DISCOVERY,
    LITERATURE_SOURCES,
    LITERATURE_VALIDATION,
    REFERENCE_DIR,
)

logger = logging.getLogger(__name__)

DEFAULT_MANIFEST = LITERATURE_SOURCES / "literature_retrieval_wave1.json"
DEFAULT_DISCOVERY = LITERATURE_DISCOVERY / "literature_discovery_2026-07-15.json"
DEFAULT_REPORT = LITERATURE_VALIDATION / "literature_retrieval_wave1.json"
COMMIT_FILE_BOUNDARY_BYTES = 10 * 1024 * 1024


def parse_arguments() -> argparse.Namespace:
    """Parse retrieval controls."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--discovery", type=Path, default=DEFAULT_DISCOVERY)
    parser.add_argument("--reference-directory", type=Path, default=REFERENCE_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--bibcode", help="Retrieve only one approved publication")
    return parser.parse_args()


def sha256_bytes(content: bytes) -> str:
    """Calculate a SHA-256 digest."""
    return hashlib.sha256(content).hexdigest()


def load_json(path: Path) -> dict[str, object]:
    """Load one JSON document."""
    with path.open(encoding="utf-8") as input_file:
        return json.load(input_file)


def pdf_url(source: dict[str, object]) -> str:
    """Return the reviewed full-text URL for one source."""
    if source.get("arxiv_id"):
        return f"https://arxiv.org/pdf/{source['arxiv_id']}"
    return str(source["pdf_url"])


def retrieve_file(url: str, maximum_bytes: int) -> bytes:
    """Retrieve one file within the approved local size boundary."""
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": ("BubbleTea-UCD-Research/1.0 (https://github.com/dr-guangtou/bubbletea)")
        },
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        declared_length = response.headers.get("Content-Length")
        if declared_length is not None and int(declared_length) > maximum_bytes:
            raise ValueError(f"File exceeds approved local size boundary: {url}")
        content = response.read(maximum_bytes + 1)
    if len(content) > maximum_bytes:
        raise ValueError(f"File exceeds approved local size boundary: {url}")
    return content


def retrieve_pdf(url: str, maximum_bytes: int) -> bytes:
    """Retrieve one PDF within the approved local size boundary."""
    content = retrieve_file(url, maximum_bytes)
    if not content.startswith(b"%PDF-"):
        raise ValueError(f"Response is not a PDF: {url}")
    return content


def inspect_xlsx(path: Path) -> dict[str, object]:
    """Validate an unchanged XLSX package and list its worksheet names."""
    with zipfile.ZipFile(path) as archive:
        corrupt_member = archive.testzip()
        if corrupt_member is not None:
            raise ValueError(f"Corrupt XLSX member {corrupt_member}: {path}")
        members = set(archive.namelist())
        required_members = {"[Content_Types].xml", "xl/workbook.xml"}
        missing_members = sorted(required_members - members)
        if missing_members:
            raise ValueError(f"Missing XLSX members {missing_members}: {path}")
        workbook_root = ElementTree.fromstring(archive.read("xl/workbook.xml"))
        namespace = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        worksheet_names = [
            str(sheet.attrib["name"])
            for sheet in workbook_root.findall("main:sheets/main:sheet", namespace)
        ]
    return {
        "xlsx_member_count": len(members),
        "worksheet_count": len(worksheet_names),
        "worksheet_names": worksheet_names,
    }


def retrieve_supplementary_files(
    source: dict[str, object],
    folder: Path,
    maximum_bytes: int,
) -> list[dict[str, object]]:
    """Retrieve and validate explicitly approved supplementary files."""
    results = []
    for supplementary_file in source.get("supplementary_files", []):
        path = folder / str(supplementary_file["file_name"])
        if not path.exists():
            content = retrieve_file(str(supplementary_file["url"]), maximum_bytes)
            path.write_bytes(content)
        content = path.read_bytes()
        metadata = inspect_xlsx(path)
        results.append(
            {
                **supplementary_file,
                "retrieval_status": "complete",
                "byte_count": len(content),
                "sha256": sha256_bytes(content),
                **metadata,
            }
        )
    return results


def inspect_pdf(path: Path) -> dict[str, object]:
    """Validate a PDF and return structural metadata."""
    reader = PdfReader(path)
    page_count = len(reader.pages)
    if page_count <= 0:
        raise ValueError(f"PDF has no pages: {path}")
    first_page = reader.pages[0]
    width = float(first_page.mediabox.width)
    height = float(first_page.mediabox.height)
    return {
        "page_count": page_count,
        "pdf_header": reader.pdf_header,
        "first_page_width_points": width,
        "first_page_height_points": height,
    }


def folder_inventory(folder: Path) -> list[dict[str, object]]:
    """Hash every provenance file in one reference folder."""
    files = []
    for path in sorted(folder.iterdir()):
        if not path.is_file() or path.name == "README.md":
            continue
        byte_count = path.stat().st_size
        files.append(
            {
                "file_name": path.name,
                "byte_count": byte_count,
                "sha256": sha256_bytes(path.read_bytes()),
                "git_tracking_status": (
                    "eligible_by_size"
                    if byte_count <= COMMIT_FILE_BOUNDARY_BYTES
                    else "local_only_exceeds_10_mib"
                ),
            }
        )
    return files


def write_readme(
    folder: Path,
    source: dict[str, object],
    paper: dict[str, object],
    retrieval_url: str,
    files: list[dict[str, object]],
    supplementary_files: list[dict[str, object]],
) -> None:
    """Write a source-level provenance summary."""
    authors = "; ".join(str(author) for author in paper["authors"])
    file_rows = "\n".join(
        f"| `{item['file_name']}` | {item['byte_count']} | `{item['sha256']}` | "
        f"`{item['git_tracking_status']}` |"
        for item in files
    )
    arxiv_line = f"**arXiv:** `{source['arxiv_id']}`\n" if source.get("arxiv_id") else ""
    vizier_line = (
        f"**VizieR Catalog:** `{source['vizier_catalog']}`\n"
        if source.get("vizier_catalog")
        else "**VizieR Catalog:** No package found at the reviewed bibliographic root\n"
    )
    supplementary_lines = ""
    if supplementary_files:
        rows = "\n".join(
            f"| {item['source_label']} | `{item['file_name']}` | `{item['url']}` |"
            for item in supplementary_files
        )
        supplementary_lines = f"""
## Publisher Source Data

| Publisher label | Local file | Source URL |
|---|---|---|
{rows}

The XLSX packages are preserved byte-for-byte. ZIP and required workbook XML
members were validated without modifying or re-exporting the workbooks.
"""
    content = f"""# {paper["title"]}

**Authors:** {authors}
**ADS Bibcode:** `{source["bibcode"]}`
**DOI:** `{source["doi"]}`
{arxiv_line}{vizier_line}**Retrieval Date:** {date.today().isoformat()}
**PDF Source:** `{retrieval_url}`
**Screening Category:** `{source["screening_category"]}`

## Files

| File | Bytes | SHA-256 | Git size status |
|---|---:|---|---|
{file_rows}

These are provenance inputs. Retrieval does not approve catalog membership,
object identity, or confirmation evidence. Machine-readable tables are preferred
over PDF extraction whenever both exist.
{supplementary_lines}
"""
    (folder / "README.md").write_text(content, encoding="utf-8")


def main() -> None:
    """Retrieve approved PDFs sequentially and write a deterministic report."""
    arguments = parse_arguments()
    manifest = load_json(arguments.manifest)
    discovery = load_json(arguments.discovery)
    papers = {str(paper["bibcode"]): paper for paper in discovery["papers"]}
    sources = list(manifest["sources"])
    if arguments.bibcode:
        sources = [source for source in sources if source["bibcode"] == arguments.bibcode]
        if not sources:
            raise ValueError(f"Bibcode is not approved in the manifest: {arguments.bibcode}")

    interval_seconds = float(manifest["minimum_request_interval_seconds"])
    maximum_bytes = int(manifest["maximum_pdf_bytes"])
    maximum_supplementary_bytes = int(manifest["maximum_supplementary_file_bytes"])
    results = []
    last_request_time = None
    for source in sources:
        bibcode = str(source["bibcode"])
        if bibcode not in papers:
            raise ValueError(f"Approved bibcode is absent from discovery metadata: {bibcode}")
        folder = arguments.reference_directory / str(source["reference_folder"])
        folder.mkdir(parents=True, exist_ok=True)
        output_path = folder / f"{source['reference_folder']}.pdf"
        retrieval_url = pdf_url(source)
        try:
            if output_path.exists():
                content = output_path.read_bytes()
            else:
                if last_request_time is not None:
                    remaining_interval = interval_seconds - (time.monotonic() - last_request_time)
                    if remaining_interval > 0:
                        time.sleep(remaining_interval)
                last_request_time = time.monotonic()
                content = retrieve_pdf(retrieval_url, maximum_bytes)
                output_path.write_bytes(content)
            pdf_metadata = inspect_pdf(output_path)
            supplementary_files = retrieve_supplementary_files(
                source, folder, maximum_supplementary_bytes
            )
            files = folder_inventory(folder)
            write_readme(
                folder,
                source,
                papers[bibcode],
                retrieval_url,
                files,
                supplementary_files,
            )
            results.append(
                {
                    **source,
                    "retrieval_status": "complete",
                    "pdf_url": retrieval_url,
                    "pdf_file": output_path.name,
                    "pdf_byte_count": len(content),
                    "pdf_sha256": sha256_bytes(content),
                    **pdf_metadata,
                    "supplementary_files": supplementary_files,
                    "files": files,
                }
            )
            logger.info("complete %s", bibcode)
        except Exception as error:
            logger.error("Failed %s: %s", bibcode, error)
            results.append(
                {
                    **source,
                    "retrieval_status": "failed",
                    "pdf_url": retrieval_url,
                    "error": str(error),
                    "files": folder_inventory(folder),
                }
            )

    arguments.report.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "retrieval_date": date.today().isoformat(),
        "approval_date": manifest["approval_date"],
        "approval_scope": manifest["approval_scope"],
        "minimum_request_interval_seconds": interval_seconds,
        "sources": results,
    }
    arguments.report.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    failures = [result for result in results if result["retrieval_status"] == "failed"]
    if failures:
        raise RuntimeError(f"Literature retrieval failed for {len(failures)} sources")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
