from __future__ import annotations

from datetime import date
from typing import Any


REVIEW_COLUMNS = [
    "jd_id",
    "source_url",
    "company",
    "role_title",
    "responsibilities_text",
    "requirements_text",
    "ai_annotation_id",
    "ai_mapped_direction",
    "reviewed_mapped_direction",
    "ai_secondary_directions",
    "reviewed_secondary_directions",
    "ai_task_keywords",
    "reviewed_task_keywords",
    "ai_capability_keywords",
    "reviewed_capability_keywords",
    "ai_tool_keywords",
    "reviewed_tool_keywords",
    "ai_jargon_terms",
    "reviewed_jargon_terms",
    "ai_confidence",
    "needs_human_attention",
    "review_status",
    "review_notes",
    "reviewed_by",
    "reviewed_at",
]

REVIEW_STATUSES = {"approved", "needs_review", "rejected"}

DIRECTION_KEYS = {
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


def split_pipe_list(value: str) -> list[str]:
    if not value.strip():
        return []
    return [item.strip() for item in value.split("|") if item.strip()]


def validate_review_row(row: dict[str, str], *, row_number: int) -> dict[str, Any]:
    missing = [column for column in REVIEW_COLUMNS if column not in row]
    if missing:
        raise ValueError(f"Review row {row_number} missing columns: {', '.join(missing)}")

    status = row["review_status"].strip()
    if status not in REVIEW_STATUSES:
        raise ValueError(f"Review row {row_number} invalid review_status: {status}")

    mapped_direction = row["reviewed_mapped_direction"].strip()
    if status == "approved" and mapped_direction not in DIRECTION_KEYS:
        raise ValueError(
            f"Review row {row_number} approved records need valid reviewed_mapped_direction"
        )
    if status != "approved" and not mapped_direction:
        mapped_direction = row["ai_mapped_direction"].strip()

    secondary = split_pipe_list(row["reviewed_secondary_directions"])
    if len(secondary) > 2:
        raise ValueError(f"Review row {row_number} may have at most 2 secondary directions")
    invalid_secondary = [direction for direction in secondary if direction not in DIRECTION_KEYS]
    if invalid_secondary:
        raise ValueError(
            f"Review row {row_number} invalid secondary direction: {invalid_secondary[0]}"
        )

    task_keywords = split_pipe_list(row["reviewed_task_keywords"])
    capability_keywords = split_pipe_list(row["reviewed_capability_keywords"])
    if status == "approved" and len(task_keywords) < 3:
        raise ValueError(f"Review row {row_number} approved records need 3 task keywords")
    if status == "approved" and len(capability_keywords) < 3:
        raise ValueError(
            f"Review row {row_number} approved records need 3 capability keywords"
        )

    reviewed_at = row["reviewed_at"].strip()
    reviewed_by = row["reviewed_by"].strip()
    if status == "approved" and not reviewed_by:
        raise ValueError(f"Review row {row_number} approved records need reviewed_by")
    if status == "approved" and not reviewed_at:
        raise ValueError(f"Review row {row_number} approved records need reviewed_at")
    if reviewed_at:
        try:
            date.fromisoformat(reviewed_at)
        except ValueError as exc:
            raise ValueError(
                f"Review row {row_number} reviewed_at must use YYYY-MM-DD format"
            ) from exc

    return {
        "jd_id": row["jd_id"].strip(),
        "ai_annotation_id": row["ai_annotation_id"].strip() or None,
        "mapped_direction": mapped_direction,
        "secondary_directions": secondary,
        "task_keywords": task_keywords,
        "capability_keywords": capability_keywords,
        "tool_keywords": split_pipe_list(row["reviewed_tool_keywords"]),
        "jargon_terms": split_pipe_list(row["reviewed_jargon_terms"]),
        "review_status": status,
        "review_notes": row["review_notes"].strip(),
        "reviewed_by": reviewed_by,
        "reviewed_at": reviewed_at,
    }
