import argparse
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.db import connect, to_json
from backend.app.services.jd_ai_annotation_service import (
    PROMPT_VERSION,
    build_annotation_prompt,
    validate_ai_annotation_payload,
)


def create_openai_payload(prompt: str, *, model: str) -> dict[str, Any]:
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required for OpenAI annotation mode")

    from openai import OpenAI

    client = OpenAI()
    response = client.responses.create(model=model, input=prompt)
    payload = json.loads(response.output_text)
    if not isinstance(payload, dict):
        raise ValueError("OpenAI response must be a JSON object")
    return payload


def run_ai_annotation(
    db_path: Path | str,
    *,
    fixture_path: Path | str | None,
    provider: str,
    model_name: str = "fixture",
) -> int:
    if provider not in {"fixture", "openai"}:
        raise ValueError("provider must be fixture or openai")
    if provider == "fixture" and fixture_path is None:
        raise ValueError("fixture_path is required for fixture provider")

    fixtures = _load_fixtures(fixture_path) if provider == "fixture" else {}
    saved_count = 0

    with connect(db_path) as conn:
        directions = [
            dict(row)
            for row in conn.execute("SELECT * FROM directions ORDER BY key").fetchall()
        ]
        sources = [
            dict(row)
            for row in conn.execute(
                """
                SELECT *
                FROM jd_sources
                WHERE raw_status IN ('collected', 'ai_annotated')
                ORDER BY id
                """
            ).fetchall()
        ]

        for source in sources:
            jd_id = source["id"]
            if provider == "fixture":
                if jd_id not in fixtures:
                    continue
                payload = fixtures[jd_id]
            else:
                prompt = build_annotation_prompt(source, directions)
                payload = create_openai_payload(prompt, model=model_name)

            normalized = validate_ai_annotation_payload(
                payload,
                raw_text=source["raw_text"],
            )
            _insert_ai_annotation(conn, jd_id, normalized, model_name)
            conn.execute(
                "UPDATE jd_sources SET raw_status = 'ai_annotated' WHERE id = ?",
                (jd_id,),
            )
            saved_count += 1

    return saved_count


def run_ai_annotation_from_fixture(
    db_path: Path | str,
    fixture_path: Path | str,
    *,
    model_name: str = "fixture",
) -> int:
    return run_ai_annotation(
        db_path,
        fixture_path=fixture_path,
        provider="fixture",
        model_name=model_name,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Create internal JD AI annotation drafts.")
    parser.add_argument("--db", required=True, type=Path)
    parser.add_argument("--provider", choices=["fixture", "openai"], required=True)
    parser.add_argument("--fixture-json", type=Path)
    parser.add_argument("--model", default="gpt-4.1-mini")
    args = parser.parse_args()

    count = run_ai_annotation(
        args.db,
        fixture_path=args.fixture_json,
        provider=args.provider,
        model_name=args.model,
    )
    print(f"Saved {count} AI annotation drafts")


def _load_fixtures(fixture_path: Path | str | None) -> dict[str, Any]:
    if fixture_path is None:
        raise ValueError("fixture_path is required")
    with Path(fixture_path).open(encoding="utf-8") as fixture_file:
        fixtures = json.load(fixture_file)
    if not isinstance(fixtures, dict):
        raise ValueError("fixture JSON must be keyed by jd_id")
    return fixtures


def _insert_ai_annotation(
    conn,
    jd_id: str,
    annotation: dict[str, Any],
    model_name: str,
) -> None:
    existing = conn.execute(
        """
        SELECT id
        FROM jd_ai_annotations
        WHERE jd_id = ?
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """,
        (jd_id,),
    ).fetchone()
    annotation_id = existing["id"] if existing else str(uuid.uuid4())
    conn.execute(
        """
        INSERT INTO jd_ai_annotations (
          id, jd_id, mapped_direction, secondary_directions, confidence,
          task_keywords, capability_keywords, tool_keywords, jargon_terms,
          evidence_quotes, reasoning_summary, needs_human_attention,
          attention_reasons, model_name, prompt_version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          mapped_direction = excluded.mapped_direction,
          secondary_directions = excluded.secondary_directions,
          confidence = excluded.confidence,
          task_keywords = excluded.task_keywords,
          capability_keywords = excluded.capability_keywords,
          tool_keywords = excluded.tool_keywords,
          jargon_terms = excluded.jargon_terms,
          evidence_quotes = excluded.evidence_quotes,
          reasoning_summary = excluded.reasoning_summary,
          needs_human_attention = excluded.needs_human_attention,
          attention_reasons = excluded.attention_reasons,
          model_name = excluded.model_name,
          prompt_version = excluded.prompt_version
        """,
        (
            annotation_id,
            jd_id,
            annotation["mapped_direction"],
            to_json(annotation["secondary_directions"]),
            annotation["confidence"],
            to_json(annotation["task_keywords"]),
            to_json(annotation["capability_keywords"]),
            to_json(annotation["tool_keywords"]),
            to_json(annotation["jargon_terms"]),
            to_json(annotation["evidence_quotes"]),
            annotation["reasoning_summary"],
            1 if annotation["needs_human_attention"] else 0,
            to_json(annotation["attention_reasons"]),
            model_name,
            PROMPT_VERSION,
        ),
    )


if __name__ == "__main__":
    main()
