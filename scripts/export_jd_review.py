from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.db import connect, from_json
from backend.app.services.jd_review_service import REVIEW_COLUMNS


def export_jd_review(db_path: Path | str, csv_path: Path | str) -> int:
    csv_path = Path(csv_path)
    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT
              js.id AS jd_id,
              js.source_url,
              js.company,
              js.role_title,
              js.responsibilities_text,
              js.requirements_text,
              ai.id AS ai_annotation_id,
              ai.mapped_direction AS ai_mapped_direction,
              ai.secondary_directions AS ai_secondary_directions,
              ai.task_keywords AS ai_task_keywords,
              ai.capability_keywords AS ai_capability_keywords,
              ai.tool_keywords AS ai_tool_keywords,
              ai.jargon_terms AS ai_jargon_terms,
              ai.confidence AS ai_confidence,
              ai.needs_human_attention
            FROM jd_sources js
            JOIN jd_ai_annotations ai ON ai.jd_id = js.id
            WHERE js.raw_status = 'ai_annotated'
              AND ai.id = (
                SELECT latest_ai.id
                FROM jd_ai_annotations latest_ai
                WHERE latest_ai.jd_id = js.id
                ORDER BY latest_ai.created_at DESC, latest_ai.id DESC
                LIMIT 1
              )
            ORDER BY js.id, ai.created_at DESC
            """
        ).fetchall()

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=REVIEW_COLUMNS)
        writer.writeheader()
        for row in rows:
            secondary_directions = "|".join(from_json(row["ai_secondary_directions"]))
            task_keywords = "|".join(from_json(row["ai_task_keywords"]))
            capability_keywords = "|".join(from_json(row["ai_capability_keywords"]))
            tool_keywords = "|".join(from_json(row["ai_tool_keywords"]))
            jargon_terms = "|".join(from_json(row["ai_jargon_terms"]))
            writer.writerow(
                {
                    "jd_id": row["jd_id"],
                    "source_url": row["source_url"],
                    "company": row["company"],
                    "role_title": row["role_title"],
                    "responsibilities_text": row["responsibilities_text"],
                    "requirements_text": row["requirements_text"],
                    "ai_annotation_id": row["ai_annotation_id"],
                    "ai_mapped_direction": row["ai_mapped_direction"],
                    "reviewed_mapped_direction": row["ai_mapped_direction"],
                    "ai_secondary_directions": secondary_directions,
                    "reviewed_secondary_directions": secondary_directions,
                    "ai_task_keywords": task_keywords,
                    "reviewed_task_keywords": task_keywords,
                    "ai_capability_keywords": capability_keywords,
                    "reviewed_capability_keywords": capability_keywords,
                    "ai_tool_keywords": tool_keywords,
                    "reviewed_tool_keywords": tool_keywords,
                    "ai_jargon_terms": jargon_terms,
                    "reviewed_jargon_terms": jargon_terms,
                    "ai_confidence": row["ai_confidence"],
                    "needs_human_attention": bool(row["needs_human_attention"]),
                    "review_status": "needs_review",
                    "review_notes": "",
                    "reviewed_by": "",
                    "reviewed_at": "",
                }
            )
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export AI JD annotations for human review.")
    parser.add_argument("--db", required=True, type=Path)
    parser.add_argument("--csv", required=True, type=Path)
    args = parser.parse_args()

    count = export_jd_review(args.db, args.csv)
    print(f"Exported {count} rows to {args.csv}")


if __name__ == "__main__":
    main()
