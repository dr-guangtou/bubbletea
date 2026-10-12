"""Build a local HTML reading portal from repository Markdown, without scientific writes.

Inputs: Markdown guides, plans, reports, and provenance in the Git working tree.
Outputs: root index.html and mirrored site/ pages, assets, directory, and link report.
Run with --limit 5 for a small build before the complete build. No archive queries,
review-database access, source-file edits, or public deployment are performed.
"""

import argparse
import hashlib
import html
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit, urlunsplit

import markdown

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    DOCS_DIR,
    DOCUMENTATION_ASSETS_DIR,
    DOCUMENTATION_BUILD_REPORT,
    DOCUMENTATION_HOME,
    DOCUMENTATION_SITE_DIR,
    PROJECT_ROOT,
)

logger = logging.getLogger(__name__)

groups = (
    "Start here",
    "Plans and requirements",
    "Selection and reference",
    "Background and radial measurements",
    "Host and pilot work",
    "Research journals",
    "Data and provenance",
    "Figure captions",
    "Operating guides",
)

entry_paths = (
    "docs/current_status.md",
    "docs/documentation_guide.md",
    "docs/PLAN.md",
    "docs/SPEC.md",
    "docs/todo.md",
)


def relative_url(target: Path, output: Path) -> str:
    """Create a portable URL relative to an output page."""
    return quote(Path(os.path.relpath(target, output.parent)).as_posix(), safe="/")


def discover_sources(scope: str) -> list[Path]:
    """Use Git to exclude ignored, frozen, dependency, and generated material."""
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z", "*.md"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
    )
    sources = []
    for name in sorted(set(result.stdout.decode().split("\0")) - {""}):
        path = PROJECT_ROOT / name
        if not path.is_file() or not path.resolve().is_relative_to(PROJECT_ROOT):
            continue
        if path.is_relative_to(DOCUMENTATION_SITE_DIR) or name.startswith("ucd_project/"):
            continue
        if scope == "project" and len(path.relative_to(PROJECT_ROOT).parts) > 1:
            if not path.is_relative_to(DOCS_DIR):
                continue
        sources.append(path)
    return sources


def category(path: Path) -> str:
    """Separate current entry points from detailed evidence and historical records."""
    name = path.relative_to(PROJECT_ROOT).as_posix()
    if name in entry_paths or name in {"README.md", "docs/CONTEXT.md"}:
        return "Start here"
    if name.startswith("docs/plans/"):
        return "Plans and requirements"
    if name.startswith("docs/journal/"):
        return "Research journals"
    if name.startswith(("reference/", "data/")):
        return "Data and provenance"
    if name.startswith("figures/"):
        return "Figure captions"
    if any(word in path.stem for word in ("host", "m60", "ngc4698", "kourkchi")):
        return "Host and pilot work"
    if any(
        word in path.stem
        for word in (
            "background",
            "large_sky",
            "off_target",
            "radial",
            "gaia_query",
            "gaia_adaptive",
            "gaia_full",
        )
    ):
        return "Background and radial measurements"
    if name.startswith("docs/") and "lessons" not in name:
        return "Selection and reference"
    return "Operating guides"


def title_of(path: Path, source: str) -> str:
    """Read the first title, including underlined Markdown headings."""
    heading = re.search(r"^#\s+(.+)$", source, re.MULTILINE)
    title = heading.group(1) if heading else path.stem.replace("_", " ")
    return title.replace("`", "").replace("**", "")


def local_target(url: str, source: Path) -> tuple[Path, str] | None:
    """Resolve source-relative links, excluding external URLs and fragment-only links."""
    parsed = urlsplit(url)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None
    path = Path(unquote(parsed.path))
    target = path.resolve() if path.is_absolute() else (source.parent / path).resolve()
    if not target.is_relative_to(PROJECT_ROOT):
        return None
    return target, unquote(parsed.fragment)


class link_rewriter(HTMLParser):
    """Rewrite Markdown links while preserving code and trusted source HTML."""

    def __init__(self, source: Path, output: Path, page_map: dict[Path, Path]):
        super().__init__(convert_charrefs=False)
        self.source = source
        self.output = output
        self.page_map = page_map
        self.parts = []
        self.references = set()
        self.unavailable = []

    def handle_starttag(self, tag, attributes):
        rewritten = []
        missing = False
        for name, value in attributes:
            if name in {"href", "src"} and value:
                resolved = local_target(value, self.source)
                if resolved:
                    target, fragment = resolved
                    if not target.exists():
                        missing = True
                        self.unavailable.append(
                            {"source": str(self.source.relative_to(PROJECT_ROOT)), "url": value}
                        )
                    if target in self.page_map:
                        self.references.add(target)
                    destination = self.page_map.get(target, target)
                    parsed = urlsplit(value)
                    value = urlunsplit(
                        (
                            "",
                            "",
                            relative_url(destination, self.output),
                            parsed.query,
                            quote(fragment, safe="-_.:"),
                        )
                    )
            rewritten.append((name, value))
        if missing:
            rewritten.append(("data_unavailable", "true"))
            rewritten.append(
                ("title", "Unavailable repository file; retained from source documentation")
            )
        attributes_text = "".join(
            f" {name}" if value is None else f' {name}="{html.escape(value, quote=True)}"'
            for name, value in rewritten
        )
        self.parts.append(f"<{tag}{attributes_text}>")

    def handle_startendtag(self, tag, attributes):
        self.handle_starttag(tag, attributes)

    def handle_endtag(self, tag):
        self.parts.append(f"</{tag}>")

    def handle_data(self, data):
        self.parts.append(data)

    def handle_entityref(self, name):
        self.parts.append(f"&{name};")

    def handle_charref(self, name):
        self.parts.append(f"&#{name};")

    def handle_comment(self, data):
        self.parts.append(f"<!--{data}-->")


def render(source: str) -> tuple[str, str]:
    """Render readable Markdown with tables, code, contents, and task checkboxes."""
    renderer = markdown.Markdown(extensions=["tables", "fenced_code", "toc", "sane_lists"])
    body = renderer.convert(source)
    body = re.sub(
        r"(<li>\s*(?:<p>)?)\[([ xX])\]\s",
        lambda match: (
            match[1] + '<input type="checkbox" disabled aria-label="Task complete" checked> '
            if match[2].lower() == "x"
            else match[1] + '<input type="checkbox" disabled aria-label="Task pending"> '
        ),
        body,
    )
    return body, renderer.toc


def rewrite(body: str, source: Path, output: Path, page_map: dict) -> link_rewriter:
    parser = link_rewriter(source, output, page_map)
    parser.feed(body)
    return parser


def page_shell(title: str, body: str, output: Path) -> str:
    """Wrap content in a shared accessible offline shell."""
    home = relative_url(DOCUMENTATION_HOME, output)
    directory = relative_url(DOCUMENTATION_SITE_DIR / "directory.html", output)
    style = relative_url(DOCUMENTATION_SITE_DIR / "assets" / "style.css", output)
    script = relative_url(DOCUMENTATION_SITE_DIR / "assets" / "navigation.js", output)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="BubbleTea: a reproducible search for ultra-compact dwarf galaxies. Research documentation and evidence.">
<title>{html.escape(title)} · BubbleTea</title><link rel="stylesheet" href="{style}">
<script src="{script}" defer></script></head><body>
<a class="skip_link" href="#main">Skip to content</a>
<header class="masthead"><a class="brand" href="{home}"><span class="brand_mark" aria-hidden="true">◉</span> BubbleTea <span class="brand_note">research notebook</span></a>
<nav aria-label="Main navigation"><a href="{home}">Overview</a><a href="{directory}">All documents</a></nav></header>
<main id="main">{body}</main>
<footer>BubbleTea · Observational astronomy · Markdown is the editable source.<br>
Local reading portal, not the source-review application or a final scientific catalog.</footer>
</body></html>"""


class page_inspector(HTMLParser):
    """Collect local destinations and heading identifiers for build validation."""

    def __init__(self):
        super().__init__()
        self.identifiers = []
        self.links = []

    def handle_starttag(self, tag, attributes):
        attributes = dict(attributes)
        if attributes.get("id"):
            self.identifiers.append(attributes["id"])
        if attributes.get("data_unavailable"):
            return
        for attribute in ("href", "src"):
            if attributes.get(attribute):
                self.links.append(attributes[attribute])


def validate_pages(outputs: list[Path]) -> tuple[list[dict], list[dict]]:
    """Fail broken generated navigation; report old source-fragment issues separately."""
    inspections = {}
    failures = []
    source_warnings = []
    for output in outputs:
        parser = page_inspector()
        parser.feed(output.read_text(encoding="utf-8"))
        if len(parser.identifiers) != len(set(parser.identifiers)):
            failures.append(
                {
                    "page": str(output.relative_to(PROJECT_ROOT)),
                    "problem": "duplicate HTML identifiers",
                }
            )
        inspections[output.resolve()] = parser
    for output, parser in inspections.items():
        for url in parser.links:
            parsed = urlsplit(url)
            if parsed.scheme or parsed.netloc:
                continue
            target = (output.parent / unquote(parsed.path)).resolve() if parsed.path else output
            if not target.exists():
                failures.append({"page": str(output.relative_to(PROJECT_ROOT)), "url": url})
            elif parsed.fragment and target in inspections:
                if unquote(parsed.fragment) not in inspections[target].identifiers:
                    source_warnings.append(
                        {
                            "page": str(output.relative_to(PROJECT_ROOT)),
                            "url": url,
                            "problem": "unresolved historical/source fragment",
                        }
                    )
    return failures, source_warnings


def build(scope: str, limit: int | None) -> dict:
    """Build pages from a stable source list and validate generated local links."""
    started = time.perf_counter()
    for output in (DOCUMENTATION_SITE_DIR, DOCUMENTATION_HOME):
        if not output.resolve().is_relative_to(PROJECT_ROOT):
            raise RuntimeError("Documentation output must remain inside the repository")
    sources = discover_sources(scope)
    if limit:
        first = [PROJECT_ROOT / name for name in entry_paths if PROJECT_ROOT / name in sources]
        sources = (first + [path for path in sources if path not in first])[:limit]
    page_map = {
        source: DOCUMENTATION_SITE_DIR / source.relative_to(PROJECT_ROOT).with_suffix(".html")
        for source in sources
    }
    titles = {source: title_of(source, source.read_text(encoding="utf-8")) for source in sources}
    bodies = {}
    backlinks = defaultdict(set)
    unavailable = []
    DOCUMENTATION_SITE_DIR.mkdir(parents=True, exist_ok=True)
    assets = DOCUMENTATION_SITE_DIR / "assets"
    assets.mkdir(exist_ok=True)
    for name in ("style.css", "navigation.js"):
        shutil.copyfile(DOCUMENTATION_ASSETS_DIR / name, assets / name)
    for source, output in page_map.items():
        body, contents = render(source.read_text(encoding="utf-8"))
        parsed = rewrite(body, source, output, page_map)
        bodies[source] = ("".join(parsed.parts), contents)
        unavailable.extend(parsed.unavailable)
        for target in parsed.references - {source}:
            backlinks[target].add(source)

    def document_links(paths, output):
        return "".join(
            f'<li><a href="{relative_url(page_map[path], output)}">{html.escape(titles[path])}</a></li>'
            for path in paths
            if path in page_map
        )

    outputs = []
    for source, output in page_map.items():
        body, contents = bodies[source]
        group = category(source)
        historical = (
            group == "Research journals"
            or source.name == "handover.md"
            or source.name == "CONTEXT.md"
        )
        notice = (
            '<p class="notice">Historical record. Read the dated current-status page before treating this as today’s operating state.</p>'
            if historical
            else ""
        )
        core = [PROJECT_ROOT / name for name in entry_paths if PROJECT_ROOT / name != source]
        related = [path for path in sources if path != source and category(path) == group][:6]
        cited = sorted(backlinks[source])
        side = f'<aside class="page_sidebar"><p class="eyebrow">On this page</p>{contents}<details><summary>Research navigation</summary><ul>{document_links(core, output)}</ul></details><details><summary>Related reading</summary><ul>{document_links(related, output)}</ul></details>'
        if cited:
            side += f"<details><summary>Linked from ({len(cited)})</summary><ul>{document_links(cited, output)}</ul></details>"
        side += "</aside>"
        source_link = relative_url(source, output)
        page = f'<div class="document_layout"><article class="document"><div class="document_meta"><span>{html.escape(group)}</span><a href="{source_link}">Markdown source ↗</a></div>{notice}{body}</article>{side}</div>'
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(page_shell(titles[source], page, output), encoding="utf-8")
        outputs.append(output)

    directory = DOCUMENTATION_SITE_DIR / "directory.html"
    directory_body = f'<section class="directory"><p class="eyebrow">The reading room</p><h1>Every document.<br>One place to begin.</h1><p>{len(sources)} Markdown documents, organized by their role. Journals preserve history; the current-status page explains where we stopped.</p><label class="search_label" for="document_search">Find a title or repository path</label><input id="document_search" type="search" placeholder="Try M60, Gaia features, or provenance…" autocomplete="off"><p id="search_count" role="status" aria-live="polite"></p>'
    for group in groups:
        selected = [path for path in sources if category(path) == group]
        if not selected:
            continue
        directory_body += f'<section class="document_group"><h2>{group} <span>{len(selected):02d}</span></h2><ul class="document_list">'
        for path in selected:
            name = path.relative_to(PROJECT_ROOT).as_posix()
            searchable = html.escape(f"{titles[path]} {name}".lower(), quote=True)
            directory_body += f'<li data_search="{searchable}"><a href="{relative_url(page_map[path], directory)}">{html.escape(titles[path])}</a><small>{html.escape(name)}</small></li>'
        directory_body += "</ul></section>"
    directory_body += "</section>"
    directory.write_text(
        page_shell("Document directory", directory_body, directory), encoding="utf-8"
    )
    outputs.append(directory)

    home = DOCUMENTATION_HOME
    home_body = """<section class="hero"><div><p class="eyebrow">A nearby-universe research notebook</p><h1>Small galaxies.<br><em>Careful evidence.</em></h1><p class="hero_description">Searching for ultra-compact dwarf galaxies with Gaia—and keeping the selection, the background, and the uncertainty in view.</p>"""
    home_body += f'<a class="primary_link" href="{relative_url(page_map.get(DOCS_DIR / "current_status.md", DOCS_DIR / "current_status.md"), home)}">Read the current status <span aria-hidden="true">↗</span></a></div>'
    home_body += """<aside class="checkpoint"><p class="eyebrow">Restart checkpoint · 12 October 2026</p><div class="orbit" aria-hidden="true"><span></span></div><h2>Review the reference.<br>Then measure contamination.</h2><p>The inspection tool is built. Source-by-source assessment is the next research step, not a completed result.</p><p class="small_note">Latest research journal: 19 August 2026.<br>These are dated checkpoints, not live counters.</p></aside></section>"""
    sections = (
        (
            "01",
            "Where the project stands",
            "docs/current_status.md",
            ["What has been completed", "Where work stopped"],
        ),
        ("02", "The science roadmap", "docs/PLAN.md", ["Immediate sequence", "Phases"]),
        ("03", "Inside the repository", "README.md", ["Repository Structure"]),
        (
            "04",
            "How the documents connect",
            "docs/documentation_guide.md",
            ["One purpose per document", "How these documents connect"],
        ),
    )
    for number, heading, name, selected_sections in sections:
        source = PROJECT_ROOT / name
        source_text = source.read_text(encoding="utf-8")
        excerpt = ""
        for section_name in selected_sections:
            found = re.search(
                rf"^## {re.escape(section_name)}\s*\n(.*?)(?=^## |\Z)",
                source_text,
                re.MULTILINE | re.DOTALL,
            )
            if found:
                excerpt += f"### {section_name}\n\n{found.group(1)}\n"
        rendered, _ = render(excerpt)
        parsed = rewrite(rendered, source, home, page_map)
        unavailable.extend(parsed.unavailable)
        destination = page_map.get(source, source)
        home_body += f'<section class="overview_section"><div class="section_heading"><span class="section_number">{number}</span><h2>{heading}</h2><a href="{relative_url(destination, home)}">Source document ↗</a></div><div class="overview_content">{"".join(parsed.parts)}</div></section>'
    home_body += f'<section class="next_step"><p class="eyebrow">Next: observational astronomy in the classroom</p><h2>A teaching project, with its own brief.</h2><p>This portal organizes the research record. Student-facing lessons, exercises, and datasets come next, after the audience and learning goals are agreed.</p><a href="{relative_url(directory, home)}">Browse all {len(sources)} documents ↗</a></section>'
    home.write_text(page_shell("Research overview", home_body, home), encoding="utf-8")
    outputs.append(home)
    failures, warnings = validate_pages(outputs)
    report = {
        "scope": scope,
        "pilot_limit": limit,
        "source_count": len(sources),
        "html_page_count": len(outputs),
        "source_sha256": {
            str(path.relative_to(PROJECT_ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sources
        },
        "unavailable_source_links": unavailable,
        "unresolved_source_fragments": warnings,
        "generated_navigation_failures": failures,
        "elapsed_seconds": round(time.perf_counter() - started, 6),
        "html_bytes": sum(path.stat().st_size for path in outputs),
    }
    DOCUMENTATION_BUILD_REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    logger.info(
        "Built %s source documents into %s HTML pages in %.3f s (%s bytes)",
        len(sources),
        len(outputs),
        report["elapsed_seconds"],
        report["html_bytes"],
    )
    logger.info(
        "Source warnings: %s unavailable links, %s fragments", len(unavailable), len(warnings)
    )
    if failures:
        raise RuntimeError(
            f"Generated navigation failed {len(failures)} checks; see {DOCUMENTATION_BUILD_REPORT}"
        )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scope",
        choices=("project", "all"),
        default="project",
        help="Root + docs (default), or all repository Markdown when explicitly requested.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Positive small-build source limit; does not delete existing pages.",
    )
    arguments = parser.parse_args()
    if arguments.limit is not None and arguments.limit < 1:
        parser.error("--limit must be positive")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    build(arguments.scope, arguments.limit)


if __name__ == "__main__":
    main()
