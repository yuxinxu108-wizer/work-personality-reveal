import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.db import connect, initialize_database, to_json


EXPECTED_DIRECTION_KEYS = {
    "ux",
    "process",
    "growth",
    "content",
    "campaign",
    "community",
    "research",
    "strategy",
    "project",
}
ALLOWED_QUESTION_TYPES = {"scenario", "preference", "pressure", "calibration"}
ALLOWED_SOURCE_TYPES = {
    "official",
    "recruiting_platform",
    "manual_note",
    "school_public",
}
ALLOWED_SOURCE_QUALITIES = {"high", "medium", "low"}
ALLOWED_WEIGHT_VALUES = {-2, 1, 2}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_seed_data(
    directions: list[dict[str, Any]],
    questions: list[dict[str, Any]],
    jds: list[dict[str, Any]],
) -> None:
    if not isinstance(directions, list):
        raise ValueError("directions must be a list")
    if not isinstance(questions, list):
        raise ValueError("questions must be a list")
    if not isinstance(jds, list):
        raise ValueError("jds must be a list")

    direction_keys = [direction.get("key") for direction in directions]
    unique_direction_keys = set(direction_keys)
    if len(directions) != 9:
        raise ValueError(f"Expected exactly 9 direction records, got {len(directions)}")
    if len(unique_direction_keys) != len(direction_keys):
        raise ValueError("Direction keys must be unique")
    if unique_direction_keys != EXPECTED_DIRECTION_KEYS:
        missing = sorted(EXPECTED_DIRECTION_KEYS - unique_direction_keys)
        extra = sorted(unique_direction_keys - EXPECTED_DIRECTION_KEYS, key=str)
        raise ValueError(
            f"Direction keys must match expected keys; missing={missing}, extra={extra}"
        )
    for direction in directions:
        direction_key = direction.get("key", "<missing>")
        _require_keys(
            direction,
            {
                "key",
                "label",
                "short_label",
                "animal",
                "avatar_src",
                "plain_summary",
                "competency_definition",
                "typical_tasks",
                "common_capabilities",
                "suitable_roles",
                "risk_notes",
                "portfolio_guidance",
            },
            f"direction {direction_key}",
        )
        for text_field in (
            "key",
            "label",
            "short_label",
            "animal",
            "avatar_src",
            "plain_summary",
            "competency_definition",
            "portfolio_guidance",
        ):
            _require_non_empty_string(
                direction.get(text_field), f"{text_field} for direction {direction_key}"
            )
        for list_field in (
            "typical_tasks",
            "common_capabilities",
            "suitable_roles",
            "risk_notes",
        ):
            _require_non_empty_string_list(
                direction.get(list_field), f"{list_field} for direction {direction_key}"
            )

    question_ids: set[str] = set()
    option_ids: set[str] = set()
    for question in questions:
        _require_keys(
            question,
            {"id", "text", "question_type", "basis_notes", "related_jd_tasks", "options"},
            "question",
        )
        question_id = question.get("id")
        _require_non_empty_string(question_id, "question id")
        _require_non_empty_string(question.get("text"), f"text for {question_id}")
        _require_non_empty_string(
            question.get("basis_notes"), f"basis_notes for {question_id}"
        )
        if question_id in question_ids:
            raise ValueError(f"Duplicate question id: {question_id}")
        question_ids.add(question_id)

        question_type = question.get("question_type")
        if question_type not in ALLOWED_QUESTION_TYPES:
            raise ValueError(
                f"Invalid question_type for {question_id}: {question_type}"
            )

        _require_non_empty_string_list(
            question.get("related_jd_tasks"), f"related_jd_tasks for {question_id}"
        )
        options = question.get("options", [])
        if not 4 <= len(options) <= 6:
            raise ValueError(
                f"Question {question_id} must have 4-6 options, got {len(options)}"
            )

        for option in options:
            _require_keys(option, {"id", "text", "weights"}, f"option for {question_id}")
            option_id = option.get("id")
            _require_non_empty_string(option_id, "option id")
            _require_non_empty_string(option.get("text"), f"text for {option_id}")
            if option_id in option_ids:
                raise ValueError(f"Duplicate option id: {option_id}")
            option_ids.add(option_id)

            weights = option.get("weights", [])
            if not 1 <= len(weights) <= 2:
                raise ValueError(
                    f"Option {option_id} must have 1-2 weights, got {len(weights)}"
                )

            for weight in weights:
                direction = weight.get("direction")
                value = weight.get("value")
                if direction not in EXPECTED_DIRECTION_KEYS:
                    raise ValueError(
                        f"Unknown weight direction for option {option_id}: {direction}"
                    )
                if (
                    not isinstance(value, int)
                    or isinstance(value, bool)
                    or value not in ALLOWED_WEIGHT_VALUES
                ):
                    raise ValueError(
                        f"Invalid weight value for option {option_id}: {value}"
                    )

    jd_ids: set[str] = set()
    for jd in jds:
        _require_keys(
            jd,
            {
                "id",
                "company",
                "role_title",
                "role_category",
                "source_url",
                "source_type",
                "location",
                "employment_type",
                "raw_text",
                "responsibilities_text",
                "requirements_text",
                "collected_at",
                "annotation",
            },
            "jd",
        )
        jd_id = jd.get("id", "<missing>")
        _require_non_empty_string(jd_id, "jd id")
        if jd_id in jd_ids:
            raise ValueError(f"Duplicate jd id: {jd_id}")
        jd_ids.add(jd_id)
        for text_field in (
            "company",
            "role_title",
            "role_category",
            "source_url",
            "location",
            "employment_type",
            "raw_text",
            "responsibilities_text",
            "requirements_text",
        ):
            _require_non_empty_string(jd.get(text_field), f"{text_field} for JD {jd_id}")
        if "://" not in jd["source_url"]:
            raise ValueError(f"source_url for JD {jd_id} must include a URL scheme")
        try:
            date.fromisoformat(jd["collected_at"])
        except ValueError as exc:
            raise ValueError(
                f"collected_at for JD {jd_id} must use YYYY-MM-DD format"
            ) from exc

        source_type = jd.get("source_type")
        if source_type not in ALLOWED_SOURCE_TYPES:
            raise ValueError(f"Invalid source_type for JD {jd_id}: {source_type}")
        source_quality = jd.get("source_quality", "medium")
        if source_quality not in ALLOWED_SOURCE_QUALITIES:
            raise ValueError(
                f"Invalid source_quality for JD {jd_id}: {source_quality}"
            )

        annotation = jd.get("annotation", {})
        if not isinstance(annotation, dict):
            raise ValueError(f"annotation for JD {jd_id} must be an object")
        _require_keys(
            annotation,
            {
                "mapped_direction",
                "secondary_directions",
                "task_keywords",
                "capability_keywords",
                "tool_keywords",
                "jargon_terms",
                "notes",
            },
            f"annotation for JD {jd_id}",
        )
        mapped_direction = annotation.get("mapped_direction")
        if mapped_direction not in EXPECTED_DIRECTION_KEYS:
            raise ValueError(
                f"Invalid mapped_direction for JD {jd_id}: {mapped_direction}"
            )

        _require_list(annotation.get("secondary_directions"), f"secondary_directions for JD {jd_id}")
        for secondary_direction in annotation["secondary_directions"]:
            if secondary_direction not in EXPECTED_DIRECTION_KEYS:
                raise ValueError(
                    "Invalid secondary direction for "
                    f"JD {jd_id}: {secondary_direction}"
                )
        _require_non_empty_string_list(
            annotation.get("task_keywords"), f"task_keywords for JD {jd_id}"
        )
        _require_non_empty_string_list(
            annotation.get("capability_keywords"), f"capability_keywords for JD {jd_id}"
        )
        _require_non_empty_string_list(
            annotation.get("tool_keywords"), f"tool_keywords for JD {jd_id}"
        )
        _require_non_empty_string_list(
            annotation.get("jargon_terms"), f"jargon_terms for JD {jd_id}"
        )
        _require_non_empty_string(annotation.get("notes"), f"notes for JD {jd_id}")


def _require_keys(record: Any, keys: set[str], label: str) -> None:
    if not isinstance(record, dict):
        raise ValueError(f"{label} must be an object")
    missing = sorted(keys - set(record))
    if missing:
        raise ValueError(f"{label} is missing required keys: {', '.join(missing)}")


def _require_non_empty_string(value: Any, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")


def _require_non_empty_list(value: Any, label: str) -> None:
    _require_list(value, label)
    if not value:
        raise ValueError(f"{label} must be a non-empty list")


def _require_list(value: Any, label: str) -> None:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list")


def _require_non_empty_string_list(value: Any, label: str) -> None:
    _require_non_empty_list(value, label)
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{label}[{index}] must be a non-empty string")


def import_seed_data(db_path: Path, seed_dir: Path) -> None:
    initialize_database(db_path)
    directions = load_json(seed_dir / "direction_definitions.json")
    questions = load_json(seed_dir / "question_bank.json")
    jds = load_json(seed_dir / "jd_seed.json")
    validate_seed_data(directions, questions, jds)

    with connect(db_path) as conn:
        conn.execute("DELETE FROM question_options")
        conn.execute("DELETE FROM questions")
        conn.execute("DELETE FROM jd_annotations")
        conn.execute("DELETE FROM jd_sources")
        conn.execute("DELETE FROM directions")

        for direction in directions:
            conn.execute(
                """
                INSERT INTO directions (
                  key, label, short_label, animal, avatar_src, plain_summary,
                  competency_definition, typical_tasks, common_capabilities,
                  suitable_roles, risk_notes, portfolio_guidance
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    direction["key"],
                    direction["label"],
                    direction["short_label"],
                    direction["animal"],
                    direction["avatar_src"],
                    direction["plain_summary"],
                    direction["competency_definition"],
                    to_json(direction["typical_tasks"]),
                    to_json(direction["common_capabilities"]),
                    to_json(direction["suitable_roles"]),
                    to_json(direction["risk_notes"]),
                    direction["portfolio_guidance"],
                ),
            )

        for question in questions:
            conn.execute(
                """
                INSERT INTO questions (
                  id, text, question_type, basis_notes, related_jd_tasks
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    question["id"],
                    question["text"],
                    question["question_type"],
                    question["basis_notes"],
                    to_json(question["related_jd_tasks"]),
                ),
            )
            for option in question["options"]:
                conn.execute(
                    """
                    INSERT INTO question_options (id, question_id, text, weights)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        option["id"],
                        question["id"],
                        option["text"],
                        to_json(option["weights"]),
                    ),
                )

        for jd in jds:
            conn.execute(
                """
                INSERT INTO jd_sources (
                  id, company, role_title, role_category, source_url, source_type,
                  source_quality, collector_notes, raw_status, location,
                  employment_type, raw_text, responsibilities_text,
                  requirements_text, collected_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    jd["id"],
                    jd["company"],
                    jd["role_title"],
                    jd["role_category"],
                    jd["source_url"],
                    jd["source_type"],
                    jd.get("source_quality", "medium"),
                    jd.get("collector_notes", ""),
                    jd.get("raw_status", "reviewed"),
                    jd["location"],
                    jd["employment_type"],
                    jd["raw_text"],
                    jd["responsibilities_text"],
                    jd["requirements_text"],
                    jd["collected_at"],
                ),
            )
            annotation = jd["annotation"]
            conn.execute(
                """
                INSERT INTO jd_annotations (
                  id, jd_id, mapped_direction, secondary_directions,
                  task_keywords, capability_keywords, tool_keywords,
                  jargon_terms, notes, review_status, review_notes,
                  reviewed_by, reviewed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"{jd['id']}_annotation",
                    jd["id"],
                    annotation["mapped_direction"],
                    to_json(annotation["secondary_directions"]),
                    to_json(annotation["task_keywords"]),
                    to_json(annotation["capability_keywords"]),
                    to_json(annotation["tool_keywords"]),
                    to_json(annotation["jargon_terms"]),
                    annotation["notes"],
                    annotation.get("review_status", "approved"),
                    annotation.get("review_notes", "seed data"),
                    annotation.get("reviewed_by", "seed"),
                    annotation.get("reviewed_at", jd["collected_at"]),
                ),
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/app.db")
    parser.add_argument("--seed-dir", default="data/seeds")
    args = parser.parse_args()
    import_seed_data(Path(args.db), Path(args.seed_dir))


if __name__ == "__main__":
    main()
