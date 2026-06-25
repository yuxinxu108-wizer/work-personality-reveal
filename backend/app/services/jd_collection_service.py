import hashlib
from datetime import datetime
from typing import Any


REQUIRED_COLLECTION_COLUMNS = [
    "source_url",
    "source_type",
    "collected_at",
    "company",
    "role_title",
    "role_category",
    "location",
    "employment_type",
    "raw_text",
    "responsibilities_text",
    "requirements_text",
    "source_quality",
    "collector_notes",
]
ALLOWED_SOURCE_TYPES = {
    "official",
    "recruiting_platform",
    "school_public",
    "manual_note",
}
ALLOWED_SOURCE_QUALITIES = {"high", "medium", "low"}


def build_jd_id(source_url: str) -> str:
    digest = hashlib.sha1(source_url.encode("utf-8")).hexdigest()[:12]
    return f"jd-{digest}"


def normalize_collection_row(
    row: dict[str, Any],
    *,
    row_number: int,
) -> dict[str, str]:
    normalized = {}
    for column in REQUIRED_COLLECTION_COLUMNS:
        value = row.get(column)
        if value is None or str(value).strip() == "":
            raise ValueError(f"row {row_number}: missing required column {column}")
        normalized[column] = str(value).strip()

    if "://" not in normalized["source_url"]:
        raise ValueError(f"row {row_number}: source_url must be a public URL")

    if normalized["source_type"] not in ALLOWED_SOURCE_TYPES:
        raise ValueError(f"row {row_number}: invalid source_type")

    if normalized["source_quality"] not in ALLOWED_SOURCE_QUALITIES:
        raise ValueError(f"row {row_number}: invalid source_quality")

    try:
        datetime.strptime(normalized["collected_at"], "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(
            f"row {row_number}: collected_at must be YYYY-MM-DD"
        ) from exc

    normalized["id"] = build_jd_id(normalized["source_url"])
    normalized["raw_status"] = "collected"
    return normalized
