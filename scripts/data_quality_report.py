from __future__ import annotations

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

from backend.app.db import connect, initialize_database


DEFAULT_MIN_RECOMMENDED_JD_COUNT = 30


def build_data_quality_report(
    db_path: Path | str,
    *,
    min_recommended_jd_count: int = DEFAULT_MIN_RECOMMENDED_JD_COUNT,
) -> dict[str, Any]:
    try:
        initialize_database(db_path)
        with connect(db_path) as conn:
            directions = conn.execute(
                """
                SELECT key, label
                FROM directions
                ORDER BY key
                """
            ).fetchall()
            rows = conn.execute(
                """
                SELECT
                  ja.mapped_direction,
                  ja.review_status,
                  ja.review_level,
                  js.source_type,
                  js.source_quality,
                  js.collected_at
                FROM jd_annotations ja
                JOIN jd_sources js ON js.id = ja.jd_id
                WHERE ja.id = (
                  SELECT latest.id
                  FROM jd_annotations latest
                  WHERE latest.jd_id = ja.jd_id
                  ORDER BY latest.reviewed_at DESC, latest.rowid DESC
                  LIMIT 1
                )
                  AND ja.review_status = 'approved'
                  AND js.source_quality IN ('high', 'medium')
                  AND js.source_type != 'manual_note'
                ORDER BY ja.mapped_direction, js.id
                """
            ).fetchall()
    except sqlite3.Error as exc:
        raise RuntimeError(
            f"Database is not initialized for data quality report: {db_path}"
        ) from exc

    rows_by_direction: dict[str, list[Any]] = {}
    for row in rows:
        rows_by_direction.setdefault(row["mapped_direction"], []).append(row)

    direction_reports = [
        _build_direction_report(
            direction["key"],
            direction["label"],
            rows_by_direction.get(direction["key"], []),
            min_recommended_jd_count=min_recommended_jd_count,
        )
        for direction in directions
    ]

    total_formal_count = sum(row["formal_jd_count"] for row in direction_reports)
    total_strong_review_count = sum(
        row["strong_review_jd_count"] for row in direction_reports
    )

    return {
        "total_direction_count": len(direction_reports),
        "total_formal_jd_count": total_formal_count,
        "total_strong_review_jd_count": total_strong_review_count,
        "min_recommended_jd_count": min_recommended_jd_count,
        "directions": direction_reports,
    }


def _build_direction_report(
    direction_key: str,
    direction_label: str,
    rows: list[Any],
    *,
    min_recommended_jd_count: int,
) -> dict[str, Any]:
    formal_jd_count = len(rows)
    review_level_counts = Counter(
        row["review_level"] or "manual_reviewed" for row in rows
    )
    source_quality_counts = Counter(row["source_quality"] for row in rows)
    source_type_counts = Counter(row["source_type"] for row in rows)
    strong_review_jd_count = sum(
        1
        for row in rows
        if (row["review_level"] or "manual_reviewed")
        in {"manual_reviewed", "spot_checked"}
    )
    latest_dates = [row["collected_at"] for row in rows if row["collected_at"]]

    return {
        "direction_key": direction_key,
        "direction_label": direction_label,
        "formal_jd_count": formal_jd_count,
        "strong_review_jd_count": strong_review_jd_count,
        "coverage_status": _coverage_status(
            formal_jd_count,
            min_recommended_jd_count=min_recommended_jd_count,
        ),
        "review_level_summary": dict(sorted(review_level_counts.items())),
        "source_quality_summary": dict(sorted(source_quality_counts.items())),
        "source_type_summary": dict(sorted(source_type_counts.items())),
        "latest_collected_at": max(latest_dates) if latest_dates else "",
    }


def _coverage_status(
    formal_jd_count: int,
    *,
    min_recommended_jd_count: int,
) -> str:
    if formal_jd_count == 0:
        return "no_evidence"
    if formal_jd_count < min_recommended_jd_count:
        return "low_sample"
    return "target_met"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build product data quality report.")
    parser.add_argument("--db", default="data/app.db")
    parser.add_argument(
        "--min-recommended-jd-count",
        default=DEFAULT_MIN_RECOMMENDED_JD_COUNT,
        type=int,
    )
    args = parser.parse_args()

    try:
        report = build_data_quality_report(
            Path(args.db),
            min_recommended_jd_count=args.min_recommended_jd_count,
        )
    except RuntimeError as exc:
        raise SystemExit(f"Cannot build data quality report: {exc}") from exc

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
