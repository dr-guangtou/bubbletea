"""Search ADS and optionally arXiv for evidence-first UCD literature.

The script records exact query strings, pagination, raw metadata, curated screening
overrides, and access status. ADS is authoritative for publication identity. arXiv
is an optional discovery fallback and is queried once per run with a single
connection, respecting its public API policy.
"""

import argparse
import csv
import hashlib
import json
import logging
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as element_tree
from collections import Counter
from datetime import date
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import LITERATURE_DISCOVERY, LITERATURE_SOURCES

logger = logging.getLogger(__name__)

ADS_ENDPOINT = "https://api.adsabs.harvard.edu/v1/search/query"
ARXIV_ENDPOINT = "https://export.arxiv.org/api/query"
ADS_FIELDS = "bibcode,title,author,year,doi,identifier,abstract,citation_count,property"
SCREENING_OVERRIDES = LITERATURE_SOURCES / "literature_screening_overrides.json"
ADS_QUERIES = {
    "priority_seed_records": (
        "bibcode:(2015ApJ...802...30Z OR 2022ApJ...929..147D OR "
        "2023Natur.623..296W OR 2023MNRAS.526L.136P OR "
        "2023ApJ...954..206W OR 2025ApJ...988....1P OR "
        "2026ApJS..285...27W OR 2026A&A...708A.172M)"
    ),
    "recent_object_data": (
        'year:[2021 TO 2026] AND abs:"ultracompact dwarf galaxies" '
        "AND property:refereed AND database:astronomy"
    ),
    "recent_catalogs_and_spectroscopy": (
        "year:[2021 TO 2026] AND abs:(UCD AND "
        "(catalog OR sample OR spectroscopic OR morphology)) "
        "AND property:refereed AND database:astronomy"
    ),
    "citations_voggel_2020": "reference:2020ApJ...899..140V",
    "citations_fahrion_2019": "reference:2019A&A...625A..50F",
    "citations_zhang_2015": "reference:2015ApJ...802...30Z",
    "citations_dumont_2022": "reference:2022ApJ...929..147D",
    "citations_wang_2023": "reference:2023Natur.623..296W",
    "targeted_ucd_titles_2015_2026": (
        'year:[2015 TO 2026] AND (((title:ultracompact OR title:"ultra-compact") '
        "AND title:dwarf) OR title:UCD) AND property:refereed AND database:astronomy "
        "NOT title:(blue OR ultracool OR ultrafaint OR white)"
    ),
}


def parse_arguments() -> argparse.Namespace:
    """Parse search controls."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-directory", type=Path, default=LITERATURE_DISCOVERY)
    parser.add_argument("--screening-overrides", type=Path, default=SCREENING_OVERRIDES)
    parser.add_argument("--rows-per-page", type=int, default=50)
    parser.add_argument("--include-arxiv", action="store_true")
    return parser.parse_args()


def request_json(url: str, headers: dict[str, str], attempts: int = 4) -> dict[str, object]:
    """Request JSON with bounded retry for rate limits and service errors."""
    for attempt in range(attempts):
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code != 429 and error.code < 500:
                raise
            if attempt == attempts - 1:
                raise
            retry_after = error.headers.get("Retry-After")
            delay_seconds = float(retry_after) if retry_after else 2 ** (attempt + 1)
            time.sleep(delay_seconds)
    raise RuntimeError("Unreachable retry state")


def search_ads(
    token: str, query_name: str, query: str, rows_per_page: int
) -> tuple[dict[str, object], list[dict[str, object]]]:
    """Retrieve every page of one deterministic ADS query."""
    start = 0
    documents = []
    num_found = None
    page_count = 0
    headers = {"Authorization": f"Bearer {token}"}
    while num_found is None or start < num_found:
        parameters = urllib.parse.urlencode(
            {
                "q": query,
                "fl": ADS_FIELDS,
                "rows": rows_per_page,
                "start": start,
                "sort": "bibcode asc",
            }
        )
        response = request_json(f"{ADS_ENDPOINT}?{parameters}", headers)
        response_data = response["response"]
        if num_found is None:
            num_found = int(response_data["numFound"])
        page_documents = response_data["docs"]
        documents.extend(page_documents)
        page_count += 1
        if not page_documents:
            break
        start += len(page_documents)
    if num_found is None or len(documents) != num_found:
        raise RuntimeError(
            f"ADS pagination incomplete for {query_name}: {len(documents)} of {num_found}"
        )
    return (
        {
            "query_name": query_name,
            "query": query,
            "num_found": num_found,
            "page_count": page_count,
            "rows_per_page": rows_per_page,
            "fields": ADS_FIELDS.split(","),
            "sort": "bibcode asc",
        },
        documents,
    )


def parse_arxiv_entry(entry: element_tree.Element) -> dict[str, object]:
    """Convert one Atom entry to discovery metadata."""
    atom = "{http://www.w3.org/2005/Atom}"
    identifier = (entry.findtext(f"{atom}id") or "").rsplit("/", maxsplit=1)[-1]
    return {
        "arxiv_id": identifier,
        "title": " ".join((entry.findtext(f"{atom}title") or "").split()),
        "abstract": " ".join((entry.findtext(f"{atom}summary") or "").split()),
        "published": entry.findtext(f"{atom}published"),
        "updated": entry.findtext(f"{atom}updated"),
        "authors": [author.findtext(f"{atom}name") for author in entry.findall(f"{atom}author")],
    }


def search_arxiv() -> dict[str, object]:
    """Run one policy-compliant arXiv discovery request."""
    query = 'all:"ultracompact dwarf" OR all:"ultra-compact dwarf"'
    parameters = urllib.parse.urlencode(
        {
            "search_query": query,
            "start": 0,
            "max_results": 100,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
    )
    headers = {
        "User-Agent": "BubbleTea-UCD-Research/1.0 (https://github.com/dr-guangtou/bubbletea)"
    }
    request = urllib.request.Request(f"{ARXIV_ENDPOINT}?{parameters}", headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        root = element_tree.parse(response).getroot()
    atom = "{http://www.w3.org/2005/Atom}"
    open_search = "{http://a9.com/-/spec/opensearch/1.1/}"
    return {
        "query": query,
        "total_results": int(root.findtext(f"{open_search}totalResults") or 0),
        "request_count": 1,
        "minimum_request_interval_seconds": 3,
        "results": [parse_arxiv_entry(entry) for entry in root.findall(f"{atom}entry")],
    }


def load_overrides(path: Path) -> dict[str, object]:
    """Load reviewed screening decisions."""
    with path.open(encoding="utf-8") as input_file:
        return json.load(input_file)


def screening_corpus_sha256(papers: list[dict[str, object]]) -> str:
    """Hash the exact normalized ADS metadata reviewed by the project."""
    payload = json.dumps(papers, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def normalize_ads_document(document: dict[str, object]) -> dict[str, object]:
    """Normalize ADS list-valued metadata for stable output."""
    return {
        "bibcode": document["bibcode"],
        "title": (document.get("title") or [""])[0],
        "authors": document.get("author") or [],
        "year": int(document["year"]),
        "doi": (document.get("doi") or [None])[0],
        "identifiers": document.get("identifier") or [],
        "abstract": document.get("abstract"),
        "citation_count": int(document.get("citation_count") or 0),
        "properties": sorted(document.get("property") or []),
    }


def suggested_category(paper: dict[str, object]) -> str:
    """Suggest a screening category without making a scientific inclusion decision."""
    text = f"{paper['title']} {paper.get('abstract') or ''}".lower()
    if "ultracompact dwarf" in text or "ultra-compact dwarf" in text:
        return "pending_object_data_screening"
    return "pending_context_screening"


def build_screening_rows(
    papers: list[dict[str, object]], manifest: dict[str, object]
) -> list[dict[str, object]]:
    """Build a deterministic literature review queue."""
    overrides = manifest["papers"]
    reviewed_corpus = screening_corpus_sha256(papers) == manifest.get("screened_corpus_sha256")
    default_reviewed_result = manifest.get("default_reviewed_result", {})
    rows = []
    for paper in papers:
        override = overrides.get(str(paper["bibcode"]), {})
        if not override and reviewed_corpus:
            override = default_reviewed_result
        rows.append(
            {
                "bibcode": paper["bibcode"],
                "year": paper["year"],
                "title": paper["title"],
                "first_author": paper["authors"][0] if paper["authors"] else None,
                "doi": paper["doi"],
                "has_ads_data_property": int("DATA" in paper["properties"]),
                "category": override.get("category", suggested_category(paper)),
                "priority": override.get("priority", "unreviewed"),
                "decision": override.get("decision", "pending_screening"),
                "reason": override.get("reason", "Manual screening required"),
                "data_access_status": override.get("data_access_status", "not_checked"),
            }
        )
    return rows


def write_screening_report(
    path: Path,
    rows: list[dict[str, object]],
    corpus_sha256: str,
) -> None:
    """Write a concise report of the completed metadata screening."""
    decision_counts = Counter(str(row["decision"]) for row in rows)
    category_counts = Counter(str(row["category"]) for row in rows)
    pending_count = decision_counts.get("pending_screening", 0)
    retrieval_rows = [row for row in rows if row["decision"] == "retrieve_data"]
    decision_lines = "\n".join(
        f"| `{decision}` | {count} |" for decision, count in sorted(decision_counts.items())
    )
    category_lines = "\n".join(
        f"| `{category}` | {count} |" for category, count in sorted(category_counts.items())
    )
    retrieval_lines = "\n".join(
        f"| `{row['bibcode']}` | {row['priority']} | {row['category']} | "
        f"{row['data_access_status']} | {row['reason']} |"
        for row in retrieval_rows
    )
    report = f"""# Literature Discovery Screening

**Screening corpus SHA-256:** `{corpus_sha256}`
**Papers screened:** {len(rows)}
**Pending decisions:** {pending_count}

This is a title-and-abstract metadata screen of the exact hashed ADS corpus. It
does not ingest a source, approve object identity, or promote confirmation state.

## Decisions

| Decision | Papers |
|---|---:|
{decision_lines}

## Categories

| Category | Papers |
|---|---:|
{category_lines}

## Proposed Retrieval Cohort

| Bibcode | Priority | Category | Access status | Reason |
|---|---|---|---|---|
{retrieval_lines}

The proposed cohort requires project-lead review before source retrieval or v2
membership changes. Context-only papers remain discoverable in the screening CSV.
"""
    path.write_text(report, encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    """Write a screening table."""
    with path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    """Execute the reproducible discovery workflow."""
    arguments = parse_arguments()
    token = os.environ.get("ADS_API_TOKEN")
    if not token:
        raise RuntimeError("ADS_API_TOKEN is required")
    if arguments.rows_per_page <= 0:
        raise ValueError("rows-per-page must be positive")

    arguments.output_directory.mkdir(parents=True, exist_ok=True)
    query_runs = []
    papers_by_bibcode = {}
    for query_name, query in ADS_QUERIES.items():
        query_run, documents = search_ads(token, query_name, query, arguments.rows_per_page)
        query_runs.append(query_run)
        for document in documents:
            paper = normalize_ads_document(document)
            papers_by_bibcode[str(paper["bibcode"])] = paper
        logger.info("ADS query %s returned %d records", query_name, len(documents))

    papers = [papers_by_bibcode[bibcode] for bibcode in sorted(papers_by_bibcode)]
    screening_manifest = load_overrides(arguments.screening_overrides)
    screening_rows = build_screening_rows(papers, screening_manifest)
    corpus_sha256 = screening_corpus_sha256(papers)
    retrieval_date = date.today().isoformat()
    discovery = {
        "retrieval_date": retrieval_date,
        "ads_endpoint": ADS_ENDPOINT,
        "query_runs": query_runs,
        "unique_paper_count": len(papers),
        "papers": papers,
        "arxiv": search_arxiv() if arguments.include_arxiv else {"status": "not_requested"},
    }
    with (arguments.output_directory / f"literature_discovery_{retrieval_date}.json").open(
        "w", encoding="utf-8"
    ) as output_file:
        json.dump(discovery, output_file, indent=2, sort_keys=True)
        output_file.write("\n")
    write_csv(
        arguments.output_directory / f"literature_screening_{retrieval_date}.csv",
        screening_rows,
    )
    write_screening_report(
        arguments.output_directory / f"literature_screening_{retrieval_date}.md",
        screening_rows,
        corpus_sha256,
    )
    logger.info("Recorded %d unique ADS papers", len(papers))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
