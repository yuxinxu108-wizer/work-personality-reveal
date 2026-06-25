from pathlib import Path
from typing import Any
import uuid

from backend.app.db import connect, from_json, to_json


class JDRepository:
    def __init__(self, db_path: Path | str):
        self.db_path = Path(db_path)

    def list_directions(self) -> list[dict[str, Any]]:
        with connect(self.db_path) as conn:
            rows = conn.execute("SELECT * FROM directions ORDER BY key").fetchall()
        return [self._direction_from_row(row) for row in rows]

    def get_direction(self, key: str) -> dict[str, Any] | None:
        with connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM directions WHERE key = ?",
                (key,),
            ).fetchone()
        return self._direction_from_row(row) if row else None

    def list_questions(self) -> list[dict[str, Any]]:
        with connect(self.db_path) as conn:
            questions = conn.execute("SELECT * FROM questions ORDER BY id").fetchall()
            options = conn.execute(
                "SELECT * FROM question_options ORDER BY id"
            ).fetchall()

        options_by_question: dict[str, list[dict[str, Any]]] = {}
        for option in options:
            options_by_question.setdefault(option["question_id"], []).append(
                {
                    "id": option["id"],
                    "text": option["text"],
                    "weights": from_json(option["weights"]),
                }
            )

        return [
            {
                "id": question["id"],
                "text": question["text"],
                "question_type": question["question_type"],
                "basis_notes": question["basis_notes"],
                "related_jd_tasks": from_json(question["related_jd_tasks"]),
                "options": options_by_question.get(question["id"], []),
            }
            for question in questions
        ]

    def save_assessment_run(
        self,
        *,
        answers: dict[str, int],
        scores: dict[str, int],
        main_direction: str,
        supporting_directions: list[str],
        confidence: dict[str, Any],
    ) -> str:
        run_id = f"run-{uuid.uuid4().hex[:12]}"
        with connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO assessment_runs (
                  id, answers_json, scores_json, main_direction,
                  supporting_directions, confidence_level, confidence_json,
                  valid_answer_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    to_json(answers),
                    to_json(scores),
                    main_direction,
                    to_json(supporting_directions),
                    confidence.get("level", ""),
                    to_json(confidence),
                    confidence.get("valid_answer_count", 0),
                ),
            )
        return run_id

    def list_jd_annotations_for_direction(
        self,
        direction_key: str,
        *,
        formal_only: bool = True,
    ) -> list[dict[str, Any]]:
        formal_filter = ""
        params: tuple[Any, ...] = (direction_key,)
        if formal_only:
            formal_filter = """
                AND ja.review_status = 'approved'
                AND js.source_quality IN ('high', 'medium')
                AND js.source_type != 'manual_note'
                AND ja.id = (
                  SELECT latest.id
                  FROM jd_annotations latest
                  WHERE latest.jd_id = ja.jd_id
                  ORDER BY latest.reviewed_at DESC, latest.rowid DESC
                  LIMIT 1
                )
            """

        with connect(self.db_path) as conn:
            rows = conn.execute(
                f"""
                SELECT
                  js.company, js.role_title, js.source_type, js.source_quality,
                  js.collected_at, ja.*
                FROM jd_annotations ja
                JOIN jd_sources js ON js.id = ja.jd_id
                WHERE ja.mapped_direction = ?
                {formal_filter}
                ORDER BY js.id, ja.id
                """,
                params,
            ).fetchall()

        return [
            {
                "company": row["company"],
                "role_title": row["role_title"],
                "source_type": row["source_type"],
                "source_quality": row["source_quality"],
                "collected_at": row["collected_at"],
                "review_status": row["review_status"],
                "task_keywords": from_json(row["task_keywords"]),
                "capability_keywords": from_json(row["capability_keywords"]),
                "tool_keywords": from_json(row["tool_keywords"]),
                "jargon_terms": from_json(row["jargon_terms"]),
                "secondary_directions": from_json(row["secondary_directions"]),
            }
            for row in rows
        ]

    def _direction_from_row(self, row: Any) -> dict[str, Any]:
        return {
            "key": row["key"],
            "label": row["label"],
            "short_label": row["short_label"],
            "animal": row["animal"],
            "avatar_src": row["avatar_src"],
            "plain_summary": row["plain_summary"],
            "competency_definition": row["competency_definition"],
            "typical_tasks": from_json(row["typical_tasks"]),
            "common_capabilities": from_json(row["common_capabilities"]),
            "suitable_roles": from_json(row["suitable_roles"]),
            "risk_notes": from_json(row["risk_notes"]),
            "portfolio_guidance": row["portfolio_guidance"],
        }
