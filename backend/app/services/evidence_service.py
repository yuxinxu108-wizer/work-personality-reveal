from collections import Counter
from typing import Any

from backend.app.repositories.jd_repository import JDRepository


EXCLUDED_HARD_REQUIREMENT_HINTS = (
    "每周",
    "实习",
    "到岗",
    "毕业",
    "本科",
    "硕士",
    "202",
    "个月",
    "天",
)
MIN_RECOMMENDED_JD_COUNT = 30
MIN_USABLE_JD_COUNT = 10


def most_common(values: list[str], limit: int = 6) -> list[str]:
    return [value for value, _ in Counter(values).most_common(limit)]


def filter_hard_requirements(values: list[str], limit: int = 8) -> list[str]:
    filtered = [
        value
        for value in values
        if value and not any(hint in value for hint in EXCLUDED_HARD_REQUIREMENT_HINTS)
    ]
    return most_common(filtered, limit=limit)


def build_evidence_confidence(jd_count: int) -> dict[str, Any]:
    if jd_count == 0:
        level = "none"
        message = "当前方向暂无可用于展示的正式 JD 证据。"
    elif jd_count < MIN_USABLE_JD_COUNT:
        level = "low"
        message = "当前方向 JD 样本较少，结论适合作为初步参考。"
    elif jd_count < MIN_RECOMMENDED_JD_COUNT:
        level = "medium"
        message = "当前方向已有一定 JD 样本，仍建议继续补充数据。"
    else:
        level = "high"
        message = "当前方向 JD 样本已达到建议阈值，结论稳定度较高。"
    return {
        "level": level,
        "sample_count": jd_count,
        "min_recommended_jd_count": MIN_RECOMMENDED_JD_COUNT,
        "message": message,
    }


def build_evidence_summary(
    repository: JDRepository,
    direction_key: str,
) -> dict[str, Any]:
    annotations = repository.list_jd_annotations_for_direction(
        direction_key,
        formal_only=True,
    )
    task_values = [
        keyword
        for annotation in annotations
        for keyword in annotation["task_keywords"]
    ]
    capability_values = [
        keyword
        for annotation in annotations
        for keyword in annotation["capability_keywords"]
    ]
    tool_values = [
        keyword
        for annotation in annotations
        for keyword in annotation["tool_keywords"]
    ]
    jargon_values = [
        keyword
        for annotation in annotations
        for keyword in annotation["jargon_terms"]
    ]
    source_counts = Counter(annotation["source_type"] for annotation in annotations)
    source_quality_counts = Counter(
        annotation["source_quality"] for annotation in annotations
    )
    review_level_counts = Counter(
        annotation.get("review_level", "manual_reviewed")
        for annotation in annotations
    )
    strong_review_jd_count = sum(
        1
        for annotation in annotations
        if annotation.get("review_level", "manual_reviewed")
        in {"manual_reviewed", "spot_checked"}
    )
    collected_dates = [
        annotation["collected_at"]
        for annotation in annotations
        if annotation.get("collected_at")
    ]
    representative_roles = most_common(
        [annotation["role_title"] for annotation in annotations],
        limit=6,
    )

    jd_count = len(annotations)

    return {
        "jd_count": jd_count,
        "evidence_status": "limited" if jd_count < 30 else "target_met",
        "recommended_roles": representative_roles,
        "representative_roles": representative_roles,
        "high_frequency_tasks": most_common(task_values),
        "high_frequency_capabilities": most_common(capability_values),
        "high_frequency_tools": most_common(tool_values),
        "hard_requirements": filter_hard_requirements(tool_values + jargon_values),
        "resume_keywords": most_common(capability_values),
        "source_type_summary": dict(source_counts),
        "source_quality_summary": dict(source_quality_counts),
        "review_level_summary": dict(review_level_counts),
        "strong_review_jd_count": strong_review_jd_count,
        "latest_collected_at": max(collected_dates) if collected_dates else "",
        "evidence_confidence": build_evidence_confidence(jd_count),
    }
