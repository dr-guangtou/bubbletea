"""Plan, checkpoint, resume, and combine partitioned Gaia cone retrievals."""

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd
from pyvo.dal import tap


def file_sha256(path: Path) -> str:
    """Return the SHA-256 digest of a local file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def query_sha256(query: str) -> str:
    """Return the SHA-256 digest of an archive query."""
    return hashlib.sha256(query.encode()).hexdigest()


def write_json_atomic(path: Path, content: dict[str, object]) -> None:
    """Write JSON through a temporary file and replace the destination atomically."""
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8")
    temporary_path.replace(path)


@dataclass(frozen=True)
class AdaptiveStrip:
    """One planned declination range and its measured archive row count."""

    strip_id: str
    minimum_dec_deg: float
    maximum_dec_deg: float
    includes_maximum_dec: bool
    measured_source_count: int
    count_query_sha256: str
    is_leaf: bool

    def dec_predicate(self) -> str:
        """Return a disjoint declination-boundary predicate."""
        upper_operator = "<=" if self.includes_maximum_dec else "<"
        return (
            f"dec >= {self.minimum_dec_deg:.12f} AND "
            f"dec {upper_operator} {self.maximum_dec_deg:.12f}"
        )


def count_query(base_where: str, strip: AdaptiveStrip) -> str:
    """Return the archive row-count query for one strip."""
    return (
        "SELECT COUNT(*) AS source_count FROM gaia_dr3.gaia_source WHERE "
        f"{base_where} AND {strip.dec_predicate()}"
    )


def measure_strip_count(
    service: tap.TAPService, base_where: str, strip: AdaptiveStrip
) -> tuple[int, str]:
    """Measure and hash one strip's source count."""
    query = count_query(base_where, strip)
    source_count = int(
        service.run_sync(query, maxrec=10).to_table().to_pandas().iloc[0]["source_count"]
    )
    return source_count, query_sha256(query)


def plan_adaptive_strips(
    service: tap.TAPService,
    base_where: str,
    minimum_dec_deg: float,
    maximum_dec_deg: float,
    maximum_rows_per_strip: int,
    minimum_strip_height_deg: float = 1e-8,
) -> list[AdaptiveStrip]:
    """Recursively split ranges until every final strip fits the measured row limit."""
    if maximum_rows_per_strip <= 0:
        raise ValueError("Maximum rows per strip must be positive")
    planned: list[AdaptiveStrip] = []

    def visit(
        strip_id: str,
        minimum_dec: float,
        maximum_dec: float,
        includes_maximum: bool,
    ) -> int:
        provisional = AdaptiveStrip(
            strip_id,
            minimum_dec,
            maximum_dec,
            includes_maximum,
            0,
            "",
            False,
        )
        measured_count, count_hash = measure_strip_count(service, base_where, provisional)
        is_leaf = measured_count <= maximum_rows_per_strip
        current = AdaptiveStrip(
            strip_id,
            minimum_dec,
            maximum_dec,
            includes_maximum,
            measured_count,
            count_hash,
            is_leaf,
        )
        planned.append(current)
        if is_leaf:
            return measured_count
        if maximum_dec - minimum_dec <= minimum_strip_height_deg:
            raise RuntimeError("Measured row limit cannot be met at minimum strip height")
        midpoint_dec = (minimum_dec + maximum_dec) / 2
        lower_count = visit(f"{strip_id}0", minimum_dec, midpoint_dec, False)
        upper_count = visit(f"{strip_id}1", midpoint_dec, maximum_dec, includes_maximum)
        if lower_count + upper_count != measured_count:
            raise RuntimeError(
                f"Child counts {lower_count + upper_count} do not match parent {measured_count}"
            )
        return measured_count

    visit("r", minimum_dec_deg, maximum_dec_deg, True)
    return planned


def write_plan(path: Path, planned: list[AdaptiveStrip]) -> None:
    """Write a measured adaptive plan atomically."""
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    pd.DataFrame([asdict(strip) for strip in planned]).to_csv(temporary_path, index=False)
    temporary_path.replace(path)


def load_leaf_plan(path: Path) -> list[AdaptiveStrip]:
    """Load only final retrieval strips from a saved adaptive plan."""
    frame = pd.read_csv(path)
    leaves = frame.loc[frame["is_leaf"].astype(bool)]
    return [AdaptiveStrip(**record) for record in leaves.to_dict(orient="records")]


class AdaptiveGaiaRetriever:
    """Retrieve planned strips with verified on-disk checkpoints."""

    def __init__(
        self,
        service: tap.TAPService,
        base_where: str,
        checkpoint_directory: Path,
        source_columns: tuple[str, ...],
    ) -> None:
        required_columns = {"source_id", "ra", "dec"}
        if not required_columns.issubset(source_columns):
            raise ValueError("Source columns must include source_id, ra, and dec")
        if len(source_columns) != len(set(source_columns)):
            raise ValueError("Source columns must not contain duplicates")
        self.service = service
        self.base_where = base_where
        self.checkpoint_directory = checkpoint_directory
        self.source_columns = source_columns
        self.checkpoint_directory.mkdir(parents=True, exist_ok=True)

    def source_query(self, strip: AdaptiveStrip) -> str:
        """Return the source query for one final strip."""
        return (
            f"SELECT {', '.join(self.source_columns)} FROM gaia_dr3.gaia_source WHERE "
            f"{self.base_where} AND {strip.dec_predicate()}"
        )

    def checkpoint_paths(self, strip: AdaptiveStrip) -> tuple[Path, Path]:
        """Return the source and metadata checkpoint paths for one strip."""
        stem = f"strip_{strip.strip_id}"
        return (
            self.checkpoint_directory / f"{stem}.csv",
            self.checkpoint_directory / f"{stem}.json",
        )

    def checkpoint_valid(self, strip: AdaptiveStrip) -> bool:
        """Return whether one checkpoint matches its plan, query, rows, and hash."""
        source_path, metadata_path = self.checkpoint_paths(strip)
        if not source_path.exists() or not metadata_path.exists():
            return False
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            expected_query_hash = query_sha256(self.source_query(strip))
            if metadata.get("source_query_sha256") != expected_query_hash:
                return False
            if metadata.get("measured_source_count") != strip.measured_source_count:
                return False
            if metadata.get("source_file_sha256") != file_sha256(source_path):
                return False
            sources = pd.read_csv(source_path, dtype={"source_id": "int64"})
        except (OSError, ValueError, KeyError, json.JSONDecodeError, pd.errors.ParserError):
            return False
        return len(sources) == strip.measured_source_count and sources["source_id"].is_unique

    def retrieve_strip(self, strip: AdaptiveStrip) -> None:
        """Retrieve and atomically checkpoint one measured strip."""
        query = self.source_query(strip)
        sources = (
            self.service.run_sync(query, maxrec=strip.measured_source_count + 1)
            .to_table()
            .to_pandas()
        )
        if len(sources) != strip.measured_source_count:
            raise RuntimeError(
                f"Strip {strip.strip_id} expected {strip.measured_source_count} rows "
                f"but retrieved {len(sources)}"
            )
        if not sources["source_id"].is_unique:
            raise RuntimeError(f"Strip {strip.strip_id} contains repeated source identifiers")
        sources.insert(0, "adaptive_strip_id", strip.strip_id)
        source_path, metadata_path = self.checkpoint_paths(strip)
        temporary_source_path = source_path.with_suffix(source_path.suffix + ".tmp")
        sources.to_csv(temporary_source_path, index=False)
        metadata = {
            "strip_id": strip.strip_id,
            "measured_source_count": strip.measured_source_count,
            "retrieved_source_count": len(sources),
            "source_query_sha256": query_sha256(query),
            "source_file_sha256": file_sha256(temporary_source_path),
        }
        temporary_source_path.replace(source_path)
        write_json_atomic(metadata_path, metadata)

    def run(
        self,
        strips: list[AdaptiveStrip],
        maximum_new_retrievals: int | None = None,
    ) -> dict[str, object]:
        """Retrieve unfinished strips and report completed, new, and skipped work."""
        retrieved_strip_ids = []
        skipped_strip_ids = []
        for strip in strips:
            if self.checkpoint_valid(strip):
                skipped_strip_ids.append(strip.strip_id)
                continue
            if (
                maximum_new_retrievals is not None
                and len(retrieved_strip_ids) >= maximum_new_retrievals
            ):
                break
            self.retrieve_strip(strip)
            retrieved_strip_ids.append(strip.strip_id)
        completed_strip_ids = [strip.strip_id for strip in strips if self.checkpoint_valid(strip)]
        return {
            "retrieved_strip_ids": retrieved_strip_ids,
            "skipped_strip_ids": skipped_strip_ids,
            "completed_strip_ids": completed_strip_ids,
            "complete": len(completed_strip_ids) == len(strips),
        }

    def combine(self, strips: list[AdaptiveStrip]) -> pd.DataFrame:
        """Combine only complete, valid checkpoints and reject repeated sources."""
        if not all(self.checkpoint_valid(strip) for strip in strips):
            raise RuntimeError("Cannot combine an incomplete or invalid retrieval")
        frames = [
            pd.read_csv(self.checkpoint_paths(strip)[0], dtype={"source_id": "int64"})
            for strip in strips
        ]
        combined = pd.concat(frames, ignore_index=True)
        if not combined["source_id"].is_unique:
            raise RuntimeError("Combined retrieval contains repeated source identifiers")
        return combined
