import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.db import connect


MINIMUM_COLLECTION_TARGET = 30
MAXIMUM_COLLECTION_TARGET = 50
MINIMUM_APPROVED = 20
MINIMUM_DIRECTION_COVERAGE = 6


def build_pilot_metrics(db_path: Path) -> dict[str, Any]:
    try:
        with connect(db_path) as conn:
            source_rows = conn.execute(
                """
                SELECT source_type, source_quality
                FROM jd_sources
                ORDER BY id
                """
            ).fetchall()
            annotation_rows = conn.execute(
                """
                SELECT
                  ja.jd_id,
                  ja.mapped_direction,
                  ja.review_status,
                  js.source_type,
                  js.source_quality
                FROM jd_annotations ja
                JOIN jd_sources js ON js.id = ja.jd_id
                WHERE ja.id = (
                  SELECT latest.id
                  FROM jd_annotations latest
                  WHERE latest.jd_id = ja.jd_id
                  ORDER BY latest.reviewed_at DESC, latest.rowid DESC
                  LIMIT 1
                )
                ORDER BY js.id, ja.id
                """
            ).fetchall()
    except sqlite3.Error as exc:
        raise RuntimeError(
            f"Database is not initialized for pilot metrics: {db_path}. "
            "Run scripts/import_jds.py --db data/app.db --seed-dir data/seeds "
            "or import collected JD records first."
        ) from exc

    status_counts = Counter(row["review_status"] for row in annotation_rows)
    source_type_counts = Counter(row["source_type"] for row in source_rows)
    source_quality_counts = Counter(row["source_quality"] for row in source_rows)
    real_public_source_rows = [
        row for row in source_rows if row["source_type"] != "manual_note"
    ]

    approved_formal_rows = [
        row
        for row in annotation_rows
        if row["review_status"] == "approved"
        and row["source_quality"] in {"high", "medium"}
        and row["source_type"] != "manual_note"
    ]
    approved_direction_counts = Counter(
        row["mapped_direction"] for row in approved_formal_rows
    )
    covered_approved_directions = sorted(approved_direction_counts)

    return {
        "collected_count": len(real_public_source_rows),
        "reviewed_annotation_count": len(annotation_rows),
        "approved_formal_count": len(approved_formal_rows),
        "covered_approved_directions": covered_approved_directions,
        "approved_direction_counts": dict(sorted(approved_direction_counts.items())),
        "status_counts": dict(sorted(status_counts.items())),
        "source_type_counts": dict(sorted(source_type_counts.items())),
        "source_quality_counts": dict(sorted(source_quality_counts.items())),
        "pilot_collection_target_met": (
            MINIMUM_COLLECTION_TARGET
            <= len(real_public_source_rows)
            <= MAXIMUM_COLLECTION_TARGET
        ),
        "pilot_minimum_approved_met": len(approved_formal_rows) >= MINIMUM_APPROVED,
        "pilot_minimum_direction_coverage_met": (
            len(covered_approved_directions) >= MINIMUM_DIRECTION_COVERAGE
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/app.db")
    args = parser.parse_args()

    try:
        metrics = build_pilot_metrics(Path(args.db))
        print(json.dumps(metrics, ensure_ascii=False, indent=2))
    except RuntimeError as exc:
        raise SystemExit(f"Cannot build pilot metrics: {exc}") from exc


if __name__ == "__main__":
    main()
