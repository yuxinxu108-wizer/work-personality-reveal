import math
from typing import Any


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

PROMPT_VERSION = "jd-annotation-v1"

REQUIRED_FIELDS = {
    "mapped_direction",
    "secondary_directions",
    "confidence",
    "task_keywords",
    "capability_keywords",
    "tool_keywords",
    "jargon_terms",
    "evidence_quotes",
    "reasoning_summary",
    "needs_human_attention",
    "attention_reasons",
}

EVIDENCE_SUPPORTS = {
    "task_keywords",
    "capability_keywords",
    "tool_keywords",
    "jargon_terms",
}


def validate_ai_annotation_payload(
    payload: dict[str, Any],
    *,
    raw_text: str,
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")

    missing_fields = sorted(REQUIRED_FIELDS - set(payload))
    if missing_fields:
        raise ValueError(f"payload missing required fields: {', '.join(missing_fields)}")

    mapped_direction = _require_text(payload["mapped_direction"], "mapped_direction")
    if mapped_direction not in EXPECTED_DIRECTION_KEYS:
        raise ValueError("mapped_direction must be a known direction key")

    secondary_directions = _require_string_list(
        payload["secondary_directions"],
        "secondary_directions",
        min_items=0,
        max_items=2,
    )
    invalid_secondary = [
        direction
        for direction in secondary_directions
        if direction not in EXPECTED_DIRECTION_KEYS
    ]
    if invalid_secondary:
        raise ValueError("secondary_directions must contain known direction keys")

    confidence = payload["confidence"]
    if isinstance(confidence, bool) or not isinstance(confidence, int | float):
        raise ValueError("confidence must be a number between 0 and 1")
    confidence = float(confidence)
    if not math.isfinite(confidence) or confidence < 0 or confidence > 1:
        raise ValueError("confidence must be a number between 0 and 1")

    task_keywords = _require_string_list(
        payload["task_keywords"],
        "task_keywords",
        min_items=3,
        max_items=8,
    )
    capability_keywords = _require_string_list(
        payload["capability_keywords"],
        "capability_keywords",
        min_items=3,
        max_items=8,
    )
    tool_keywords = _require_string_list(
        payload["tool_keywords"],
        "tool_keywords",
        min_items=0,
        max_items=6,
    )
    jargon_terms = _require_string_list(
        payload["jargon_terms"],
        "jargon_terms",
        min_items=0,
        max_items=8,
    )

    evidence_quotes = _validate_evidence_quotes(payload["evidence_quotes"], raw_text)
    reasoning_summary = _require_text(
        payload["reasoning_summary"],
        "reasoning_summary",
    )

    if not isinstance(payload["needs_human_attention"], bool):
        raise ValueError("needs_human_attention must be a boolean")
    needs_human_attention = payload["needs_human_attention"]
    attention_reasons = _require_string_list(
        payload["attention_reasons"],
        "attention_reasons",
        min_items=0,
        max_items=8,
    )

    if confidence < 0.65:
        needs_human_attention = True
        attention_reasons = _append_unique(
            attention_reasons,
            "confidence_below_0.65",
            "attention_reasons",
        )
    if len(raw_text.strip()) < 80:
        needs_human_attention = True
        attention_reasons = _append_unique(
            attention_reasons,
            "jd_text_too_short",
            "attention_reasons",
        )

    return {
        "mapped_direction": mapped_direction,
        "secondary_directions": secondary_directions,
        "confidence": confidence,
        "task_keywords": task_keywords,
        "capability_keywords": capability_keywords,
        "tool_keywords": tool_keywords,
        "jargon_terms": jargon_terms,
        "evidence_quotes": evidence_quotes,
        "reasoning_summary": reasoning_summary,
        "needs_human_attention": needs_human_attention,
        "attention_reasons": attention_reasons,
    }


def build_annotation_prompt(
    jd: dict[str, Any],
    directions: list[dict[str, Any]],
) -> str:
    direction_lines = []
    for direction in directions:
        direction_lines.append(
            "\n".join(
                [
                    f"- key: {direction.get('key', '')}",
                    f"  label: {direction.get('label', '')}",
                    f"  summary: {direction.get('plain_summary', '')}",
                    f"  competency: {direction.get('competency_definition', '')}",
                    f"  typical_tasks: {direction.get('typical_tasks', [])}",
                    f"  common_capabilities: {direction.get('common_capabilities', [])}",
                ]
            )
        )

    jd_lines = [
        f"id: {jd.get('id', '')}",
        f"company: {jd.get('company', '')}",
        f"role_title: {jd.get('role_title', '')}",
        f"role_category: {jd.get('role_category', '')}",
        f"location: {jd.get('location', '')}",
        f"employment_type: {jd.get('employment_type', '')}",
        f"source_type: {jd.get('source_type', '')}",
        f"source_quality: {jd.get('source_quality', '')}",
        f"raw_text: {jd.get('raw_text', '')}",
        f"responsibilities_text: {jd.get('responsibilities_text', '')}",
        f"requirements_text: {jd.get('requirements_text', '')}",
    ]

    return (
        "你是内部 JD 方向标注助手，只为研究和数据整理生成标注草稿。\n"
        "请严格输出一个 JSON object，不要输出 Markdown、注释或额外文字。\n"
        "禁止给用户职业建议，禁止编造 JD 中不存在的来源、事实、工具或引用。\n"
        "evidence_quotes[].text 必须逐字来自 JD 字段原文。\n"
        "JSON 字段必须包含：mapped_direction, secondary_directions, confidence, "
        "task_keywords, capability_keywords, tool_keywords, jargon_terms, "
        "evidence_quotes, reasoning_summary, needs_human_attention, attention_reasons。\n"
        "字段约束：mapped_direction 使用一个方向 key；secondary_directions 最多 2 个；"
        "confidence 为 0 到 1；task_keywords 和 capability_keywords 各 3-8 个；"
        "tool_keywords 0-6 个；jargon_terms 0-8 个；"
        "evidence_quotes[].supports 只能是 task_keywords, capability_keywords, "
        "tool_keywords, jargon_terms。\n\n"
        "方向定义：\n"
        f"{chr(10).join(direction_lines)}\n\n"
        "JD 字段：\n"
        f"{chr(10).join(jd_lines)}"
    )


def _require_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a non-empty string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be a non-empty string")
    return normalized


def _require_string_list(
    value: Any,
    field_name: str,
    *,
    min_items: int,
    max_items: int,
) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    if len(value) < min_items or len(value) > max_items:
        raise ValueError(
            f"{field_name} must contain between {min_items} and {max_items} items"
        )

    normalized = []
    for index, item in enumerate(value):
        try:
            normalized.append(_require_text(item, f"{field_name}[{index}]"))
        except ValueError as exc:
            raise ValueError(f"{field_name} must contain non-empty strings") from exc
    return normalized


def _validate_evidence_quotes(value: Any, raw_text: str) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise ValueError("evidence_quotes must be a list")

    normalized = []
    for index, quote in enumerate(value):
        if not isinstance(quote, dict):
            raise ValueError("evidence_quotes must contain objects")
        text = _require_text(quote.get("text"), f"evidence_quotes[{index}].text")
        supports = _require_text(
            quote.get("supports"),
            f"evidence_quotes[{index}].supports",
        )
        if text not in raw_text:
            raise ValueError("evidence_quotes text must appear in raw_text")
        if supports not in EVIDENCE_SUPPORTS:
            raise ValueError(
                "evidence_quotes supports must be task_keywords, "
                "capability_keywords, tool_keywords, or jargon_terms"
            )
        normalized.append({"text": text, "supports": supports})
    return normalized


def _append_unique(items: list[str], item: str, field_name: str) -> list[str]:
    if item in items:
        return items
    if len(items) >= 8:
        raise ValueError(f"{field_name} must contain at most 8 items")
    return [*items, item]
