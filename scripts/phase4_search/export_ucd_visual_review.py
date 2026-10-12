"""Generate the UCD visual review exports from the command line."""

import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import UCD_VISUAL_REVIEW_REVIEW_DB
from scripts.phase4_search.ucd_visual_review import schema
from scripts.phase4_search.ucd_visual_review.export import generate_exports


def main() -> None:
    """Generate all exports and print the summary counts."""
    connection = schema.connect(UCD_VISUAL_REVIEW_REVIEW_DB)
    summary = generate_exports(connection)
    connection.close()
    print(json.dumps(summary["counts"], indent=2))


if __name__ == "__main__":
    main()
