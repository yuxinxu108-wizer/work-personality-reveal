from __future__ import annotations

import argparse
import csv
import sys
import uuid
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.db import connect, initialize_database, to_json
from backend.app.services.jd_review_service import validate_review_row


def import_reviewed_jds(db_path: Path | str, csv_path: Path | str) -> int:
    initialize_database(db_path)
    with Path(csv_path).open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        rows = [
            validate_review_row(row, row_number=index)
            for index, row in enumerate(reader, start=2)
        ]

    imported = 0
    with connect(db_path) as conn:
        for row in rows:
            existing = conn.execute(
                """
                SELECT id
                FROM jd_annotations
                WHERE jd_id = ?
                  AND (
                    ai_annotation_id = ?
                    OR (ai_annotation_id IS NULL AND ? IS NULL)
                  )
                ORDER BY id
                LIMIT 1
                """,
                (
                    row["jd_id"],
                    row["ai_annotation_id"],
                    row["ai_annotation_id"],
                ),
            ).fetchone()
            annotation_id = existing["id"] if existing else f"review-{uuid.uuid4().hex[:12]}"
            conn.execute(
                """
                INSERT INTO jd_annotations (
                  id, jd_id, ai_annotation_id, mapped_direction,
                  secondary_directions, task_keywords, capability_keywords,
                  tool_keywords, jargon_terms, notes, review_status,
                  review_level, review_notes, reviewed_by, reviewed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                  mapped_direction = excluded.mapped_direction,
                  secondary_directions = excluded.secondary_directions,
                  task_keywords = excluded.task_keywords,
                  capability_keywords = excluded.capability_keywords,
                  tool_keywords = excluded.tool_keywords,
                  jargon_terms = excluded.jargon_terms,
                  notes = excluded.notes,
                  review_status = excluded.review_status,
                  review_level = excluded.review_level,
                  review_notes = excluded.review_notes,
                  reviewed_by = excluded.reviewed_by,
                  reviewed_at = excluded.reviewed_at
                """,
                (
                    annotation_id,
                    row["jd_id"],
                    row["ai_annotation_id"],
                    row["mapped_direction"],
                    to_json(row["secondary_directions"]),
                    to_json(row["task_keywords"]),
                    to_json(row["capability_keywords"]),
                    to_json(row["tool_keywords"]),
                    to_json(row["jargon_terms"]),
                    row["review_notes"],
                    row["review_status"],
                    row["review_level"],
                    row["review_notes"],
                    row["reviewed_by"],
                    row["reviewed_at"],
                ),
            )
            conn.execute(
                "UPDATE jd_sources SET raw_status = 'reviewed' WHERE id = ?",
                (row["jd_id"],),
            )
            imported += 1
    return imported


def main() -> None:
    parser = argparse.ArgumentParser(description="Import human-reviewed JD annotations.")
    parser.add_argument("--db", required=True, type=Path)
    parser.add_argument("--csv", required=True, type=Path)
    args = parser.parse_args()

    count = import_reviewed_jds(args.db, args.csv)
    print(f"Imported {count} reviewed JD annotations")


if __name__ == "__main__":
    main()
