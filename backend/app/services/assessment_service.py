from typing import Any


MIN_ANSWER_COVERAGE = 0.8


def build_assessment_result(
    answers: dict[str, int],
    questions: list[dict[str, Any]],
    directions: list[dict[str, Any]],
) -> dict[str, Any]:
    scores = score_answers(answers, questions, directions)
    selected = select_result(scores)
    valid_answer_count = count_valid_answers(answers, questions)
    total_question_count = len(questions)
    min_required_answer_count = min_required_answers(total_question_count)
    confidence = build_confidence_summary(
        selected,
        valid_answer_count=valid_answer_count,
        total_question_count=total_question_count,
        min_required_answer_count=min_required_answer_count,
    )
    selected["confidence"] = confidence
    selected["is_sufficient"] = confidence["level"] != "insufficient"
    selected["result_explanation"] = explain_result(selected, directions)
    return selected


def score_answers(
    answers: dict[str, int],
    questions: list[dict[str, Any]],
    directions: list[dict[str, Any]],
) -> dict[str, int]:
    scores = {direction["key"]: 0 for direction in directions}

    for question in questions:
        answer_index = answers.get(question["id"])
        if not _is_strict_int(answer_index):
            continue
        if answer_index < 0 or answer_index >= len(question["options"]):
            continue
        option = question["options"][answer_index]
        for weight in option["weights"]:
            direction = weight["direction"]
            value = weight["value"]
            if direction in scores and _is_strict_int(value):
                scores[direction] += value

    return scores


def count_valid_answers(
    answers: dict[str, int],
    questions: list[dict[str, Any]],
) -> int:
    count = 0
    for question in questions:
        answer_index = answers.get(question["id"])
        if not _is_strict_int(answer_index):
            continue
        if 0 <= answer_index < len(question["options"]):
            count += 1
    return count


def min_required_answers(total_question_count: int) -> int:
    if total_question_count <= 0:
        return 0
    return max(1, round(total_question_count * MIN_ANSWER_COVERAGE))


def normalize_scores(scores: dict[str, int]) -> dict[str, int]:
    if not scores:
        return {}
    values = list(scores.values())
    low = min(values)
    high = max(values)
    if high == low:
        return {key: 0 for key in scores}
    return {
        key: round(((value - low) / (high - low)) * 100)
        for key, value in scores.items()
    }


def build_confidence_summary(
    selected: dict[str, Any],
    *,
    valid_answer_count: int,
    total_question_count: int,
    min_required_answer_count: int,
) -> dict[str, Any]:
    missing_required = max(0, min_required_answer_count - valid_answer_count)
    if missing_required:
        level = "insufficient"
        reason = "有效答题数量不足，暂时不能生成稳定方向结论。"
    else:
        ranked = selected.get("ranked", [])
        top_gap = 0
        if len(ranked) >= 2:
            top_gap = ranked[0]["value"] - ranked[1]["value"]
        coverage = (
            valid_answer_count / total_question_count
            if total_question_count
            else 0
        )
        if coverage >= 0.9 and top_gap >= 4 and not selected.get("is_multi_sided"):
            level = "high"
            reason = "答题完整度较高，主方向和其他方向拉开了明显差距。"
        elif coverage >= MIN_ANSWER_COVERAGE and top_gap >= 2:
            level = "medium"
            reason = "答题数量达标，主方向有一定优势，但仍建议结合辅助方向验证。"
        else:
            level = "low"
            reason = "答题数量达标，但方向差距较小，结果更适合作为探索线索。"

    return {
        "level": level,
        "valid_answer_count": valid_answer_count,
        "total_question_count": total_question_count,
        "min_required_answer_count": min_required_answer_count,
        "missing_required_answer_count": missing_required,
        "reason": reason,
    }


def explain_result(
    selected: dict[str, Any],
    directions: list[dict[str, Any]],
) -> str:
    main_direction = selected.get("main_direction")
    direction_by_key = {direction["key"]: direction for direction in directions}
    main = direction_by_key.get(main_direction)
    if not main:
        return "当前答案还不足以生成稳定方向解释。"

    ranked = selected.get("ranked", [])
    if len(ranked) >= 2:
        gap = ranked[0]["value"] - ranked[1]["value"]
        return f"{main['label']}得分最高，领先第二方向 {gap} 分。"
    return f"{main['label']}得分最高。"


def select_result(scores: dict[str, int]) -> dict[str, Any]:
    ranked = [
        {"key": key, "value": value}
        for key, value in sorted(scores.items(), key=lambda item: item[1], reverse=True)
    ]
    if not ranked:
        return {
            "main_direction": None,
            "supporting_directions": [],
            "ranked": [],
            "normalized_scores": {},
            "is_multi_sided": False,
        }

    main = ranked[0]["key"]
    supporting = [ranked[1]["key"]] if len(ranked) > 1 else []
    if len(ranked) > 2:
        second = ranked[1]["value"]
        third = ranked[2]["value"]
        if third == second or abs(third - second) <= 1:
            supporting.append(ranked[2]["key"])

    top = ranked[0]["value"]
    is_multi_sided = False
    if len(ranked) >= 5:
        is_multi_sided = top - ranked[4]["value"] <= 3
    return {
        "main_direction": main,
        "supporting_directions": supporting[:2],
        "ranked": ranked,
        "normalized_scores": normalize_scores(scores),
        "is_multi_sided": is_multi_sided,
    }


def _is_strict_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)
