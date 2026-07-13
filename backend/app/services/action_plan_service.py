from typing import Any


def build_action_plan(
    main_direction: dict[str, Any],
    support_direction: dict[str, Any],
    evidence: dict[str, Any],
) -> list[dict[str, Any]]:
    main_label = main_direction["label"]
    main_short = main_direction["short_label"]
    support_short = support_direction["short_label"]
    main_tasks = _first_items(main_direction.get("typical_tasks", []), 4)
    main_capabilities = _first_items(main_direction.get("common_capabilities", []), 4)
    evidence_tasks = _first_items(evidence.get("high_frequency_tasks", []), 4)
    evidence_capabilities = _first_items(
        evidence.get("high_frequency_capabilities", []), 4
    )
    resume_keywords = _first_items(evidence.get("resume_keywords", []), 4)

    primary_task = _pick(evidence_tasks, 0, _pick(main_tasks, 0, "岗位任务拆解"))
    secondary_task = _pick(evidence_tasks, 1, _pick(main_tasks, 1, primary_task))
    third_task = _pick(evidence_tasks, 2, _pick(main_tasks, 2, secondary_task))
    primary_capability = _pick(
        evidence_capabilities,
        0,
        _pick(main_capabilities, 0, "结构化表达"),
    )
    portfolio_guidance = main_direction.get("portfolio_guidance", "完成一个可展示的小项目。")

    return [
        {
            "label": "Day 1",
            "title": f"拆解 {main_short} 的真实 JD 要求",
            "goal": f"把 {main_label} 从抽象方向变成可执行的岗位任务清单。",
            "tasks": [
                f"阅读 5-8 条目标岗位 JD，标出反复出现的任务，例如 {primary_task}、{secondary_task}。",
                f"把任务分成输入、动作、产出三列，明确哪些是你现在能做的，哪些需要补齐。",
                f"整理一份 {main_short} 岗位词表，至少包含 10 个任务词和 10 个能力词。",
            ],
            "deliverable": f"{main_short} JD 任务拆解表",
            "resume_sentence": f"基于真实 JD 拆解 {main_short} 岗位任务，识别 {primary_task} 等高频要求。",
            "jd_keywords": _unique([primary_task, secondary_task, *resume_keywords]),
        },
        {
            "label": "Day 2",
            "title": f"选择一个能证明 {primary_capability} 的作品集题目",
            "goal": "确定一个 7 天内能完成、能被面试官快速看懂的小项目。",
            "tasks": [
                f"从自己的校园、社群、内容或求职场景里选一个真实问题，优先贴近 {primary_task}。",
                f"用一句话写清楚项目目标：为谁解决什么问题，用什么指标判断结果。",
                f"把辅助方向 {support_short} 作为加分点，设计一个可展示的表达或运营动作。",
            ],
            "deliverable": "作品集项目选题卡",
            "resume_sentence": f"围绕 {primary_task} 设计可验证项目目标，并结合 {support_short} 做展示强化。",
            "jd_keywords": _unique([primary_task, primary_capability, support_short]),
        },
        {
            "label": "Day 3",
            "title": "收集证据并建立问题判断",
            "goal": "让项目不是凭感觉，而是有观察、数据或访谈证据支撑。",
            "tasks": [
                "收集至少 10 条用户反馈、行为数据、竞品案例或公开资料。",
                f"用表格记录现象、可能原因、影响程度，突出 {secondary_task}。",
                "把证据压缩成 3 个关键发现，每个发现都配一条原始证据。",
            ],
            "deliverable": "证据整理表和 3 条关键发现",
            "resume_sentence": f"通过资料整理和证据归纳，定位影响 {secondary_task} 的关键问题。",
            "jd_keywords": _unique([secondary_task, "证据归纳", primary_capability]),
        },
        {
            "label": "Day 4",
            "title": f"设计解决方案和 {third_task} 路径",
            "goal": "把发现转成可执行方案，而不是只停留在分析。",
            "tasks": [
                "针对 3 个关键发现分别写出解决动作、预期效果和执行成本。",
                f"画出用户或业务路径，标记 {third_task} 发生的位置。",
                "选出一个优先级最高的方案，说明为什么先做它。",
            ],
            "deliverable": "方案优先级表和路径图",
            "resume_sentence": f"基于路径分析设计改进方案，明确 {third_task} 的优先级和落地点。",
            "jd_keywords": _unique([third_task, "路径分析", "优先级判断"]),
        },
        {
            "label": "Day 5",
            "title": "做出可展示的最小版本",
            "goal": "产出一个别人能打开、能理解、能评价的项目版本。",
            "tasks": [
                "完成一版原型、表格、内容样稿、活动方案或分析报告。",
                f"在作品里明确展示 {primary_task}、{secondary_task} 和你的判断过程。",
                "请 2-3 个同学试看，记录他们不理解或觉得不可信的地方。",
            ],
            "deliverable": "最小可展示作品",
            "resume_sentence": f"独立完成可展示方案，覆盖 {primary_task} 与 {secondary_task} 等核心任务。",
            "jd_keywords": _unique([primary_task, secondary_task, "作品集"]),
        },
        {
            "label": "Day 6",
            "title": "复盘效果并补强简历表达",
            "goal": "把项目从“做过”升级成“有过程、有结果、有反思”。",
            "tasks": [
                "根据试看反馈修改作品，至少补齐 3 个表达不清或证据不足的位置。",
                "写出项目前后对比：问题是什么、你做了什么、结果或预期变化是什么。",
                f"用 JD 语言重写项目描述，突出 {primary_capability} 和 {support_short} 加分点。",
            ],
            "deliverable": "项目复盘页和简历项目描述",
            "resume_sentence": f"复盘项目效果并沉淀简历表达，突出 {primary_capability}、{support_short} 和结果意识。",
            "jd_keywords": _unique([primary_capability, support_short, *resume_keywords]),
        },
        {
            "label": "Day 7",
            "title": "整理投递包并建立下一轮迭代",
            "goal": "把作品、简历和投递关键词连成一个可持续迭代的求职材料包。",
            "tasks": [
                "把项目整理成 1 页作品集摘要：背景、目标、过程、结果、反思。",
                f"围绕 {main_short} 搜索 20 个岗位，记录 JD 中是否出现 {primary_task}、{secondary_task}。",
                f"根据搜索结果决定下一轮补强方向：继续深挖 {main_short}，或加入 {support_short} 作为差异化定位。",
            ],
            "deliverable": "作品集摘要、简历项目段落、投递关键词表",
            "resume_sentence": f"完成 {main_short} 方向作品集摘要，并基于 JD 关键词持续迭代投递材料。",
            "jd_keywords": _unique([main_short, primary_task, secondary_task, support_short]),
        },
    ]


def _first_items(values: list[str], limit: int) -> list[str]:
    return [value for value in values if value][:limit]


def _pick(values: list[str], index: int, fallback: str) -> str:
    if index < len(values):
        return values[index]
    return fallback


def _unique(values: list[str]) -> list[str]:
    unique_values = []
    for value in values:
        if value and value not in unique_values:
            unique_values.append(value)
    return unique_values[:6]
