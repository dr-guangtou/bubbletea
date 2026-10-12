"""Check documentation rendering fixtures, source coverage, digests, and generated links.

Read-only checks of the generated portal plus in-memory Markdown fixtures. Run
after build_documentation.py; no scientific data or review database is opened.
"""

import hashlib
import json
import logging
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    DOCS_DIR,
    DOCUMENTATION_BUILD_REPORT,
    DOCUMENTATION_HOME,
    DOCUMENTATION_SITE_DIR,
    PROJECT_ROOT,
)
from scripts.documentation.build_documentation import (
    discover_sources,
    page_inspector,
    render,
    rewrite,
    validate_pages,
)

logger = logging.getLogger(__name__)


def main():
    checks = []

    def require(condition, message):
        if not condition:
            raise RuntimeError(message)
        checks.append(message)

    rendered, contents = render(
        "# Example\n\n## Repeated\n\n## Repeated\n\n"
        "| A | B |\n| --- | --- |\n| 1 | 2 |\n\n"
        "```python\ngaia_source_id = '1234567890123456789'\n```\n\n"
        "- [x] Done\n- [ ] Pending\n\n"
        "The radius is $R < 50$ kpc.\n"
    )
    require("<table>" in rendered, "Markdown tables render")
    require('<code class="language-python">' in rendered, "Fenced code renders")
    require('type="checkbox"' in rendered and "checked" in rendered, "Task lists render")
    require("1234567890123456789" in rendered, "Gaia identifier text is unchanged")
    require("$R &lt; 50$" in rendered, "Scientific source notation stays readable")
    parser = page_inspector()
    parser.feed(rendered)
    require(
        len(parser.identifiers) == len(set(parser.identifiers)),
        "Repeated headings get unique identifiers",
    )
    require("#repeated_1" in contents, "Contents follows repeated headings")

    source = DOCS_DIR / "documentation_guide.md"
    output = DOCUMENTATION_SITE_DIR / "docs" / "documentation_guide.html"
    target = DOCS_DIR / "PLAN.md"
    page_map = {target: DOCUMENTATION_SITE_DIR / "docs" / "PLAN.html"}
    fixture = '<a href="PLAN.md?view=full#phases">Roadmap</a><a href="https://example.org/paper">Paper</a><a href="#local">Local</a><a href="../reference/summary.md">Sources</a><img src="hsc_example.png"><code>PLAN.md</code>'
    rewritten = rewrite(fixture, source, output, page_map)
    text = "".join(rewritten.parts)
    require(
        'href="PLAN.html?view=full#phases"' in text, "Rendered links preserve queries and fragments"
    )
    require('href="https://example.org/paper"' in text, "External links are unchanged")
    require('href="#local"' in text, "Same-page links are unchanged")
    require(
        'href="../../reference/summary.md"' in text, "Supporting Markdown remains source-linked"
    )
    require(
        'src="../../docs/hsc_example.png"' in text,
        "Images resolve against original source location",
    )
    require("<code>PLAN.md</code>" in text, "Code is not rewritten as a link")
    require(target in rewritten.references, "Backlink targets are collected")
    missing = rewrite(
        '<a href="missing_documentation_fixture.md">Missing</a>', source, output, page_map
    )
    require(
        bool(missing.unavailable) and "data_unavailable" in "".join(missing.parts),
        "Unavailable source links remain explicit",
    )

    report = json.loads(DOCUMENTATION_BUILD_REPORT.read_text(encoding="utf-8"))
    sources = discover_sources(report["scope"])
    expected = {str(path.relative_to(PROJECT_ROOT)) for path in sources}
    require(report["pilot_limit"] is None, "Full build, not pilot, is being validated")
    require(set(report["source_sha256"]) == expected, "Every selected source is covered")
    for name, digest in report["source_sha256"].items():
        require(
            hashlib.sha256((PROJECT_ROOT / name).read_bytes()).hexdigest() == digest,
            f"Source digest matches: {name}",
        )
    outputs = [DOCUMENTATION_HOME, DOCUMENTATION_SITE_DIR / "directory.html"]
    outputs.extend(
        DOCUMENTATION_SITE_DIR / path.relative_to(PROJECT_ROOT).with_suffix(".html")
        for path in sources
    )
    require(all(path.is_file() for path in outputs), "All source views and entry pages exist")
    failures, warnings = validate_pages(outputs)
    require(not failures, "Generated local navigation has no broken destinations")
    require(warnings == report["unresolved_source_fragments"], "Source-fragment warnings reproduce")
    require(
        not report["generated_navigation_failures"],
        "Build report has no generated navigation failures",
    )
    logger.info("All %s checks passed for %s source documents", len(checks), len(sources))
    logger.info(
        "Historical warnings retained: %s unavailable links, %s fragments",
        len(report["unavailable_source_links"]),
        len(warnings),
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
