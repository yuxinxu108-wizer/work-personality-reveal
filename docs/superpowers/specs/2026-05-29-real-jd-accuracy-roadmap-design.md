# Real JD Accuracy Roadmap Design

## Goal

Move the internship direction test from a runnable MVP to a practical, data-backed tool that can be used by students looking for internet internships.

The project is considered basically complete when results are explainable through real public JD data, not manually invented examples. The system should help users understand suitable directions, searchable roles, portfolio ideas, and capability gaps with evidence from reviewed JD records.

## Target Product Standard

This is a practical tool, not a research-grade recommender system.

Success means:

- Real public JD data supports direction definitions, question basis, and result explanations.
- Users can see why a result was selected.
- Suggestions are actionable for internship search, portfolio building, and skill improvement.
- Most users find the result useful and reasonable.
- Limitations are documented honestly.

## Data Scale

The full MVP target is 300-500 real public JD records.

Coverage rule:

- Each of the 9 directions must have at least 30 approved JD records.
- Popular directions may have more records.
- Smaller directions still need enough evidence to avoid weak or unsupported results.
- The result page should show how many approved JD records support the selected direction.

Before scaling to 300-500 records, the next stage will run a 30-50 JD pilot loop.

## Pilot Loop

The pilot loop proves that the data and review process works before large-scale collection.

Pilot completion criteria:

- 30-50 real public JD records are collected.
- At least 6 directions are covered; 9 directions is preferred.
- Each JD has source URL, collection date, company, role title, responsibilities, and requirements.
- Each JD receives AI initial annotation.
- Each JD receives human review.
- Each JD ends with `approved`, `needs_review`, or `rejected`.
- Only approved JD records enter evidence summaries.
- The team can identify which questions, directions, or result explanations need adjustment.

## Source Rules

Allowed sources:

- Company official recruiting pages
- Public recruiting platform pages
- Public school career pages or public campus recruitment pages
- Public JD text that does not require login

Disallowed sources:

- Private social posts
- WeChat groups, private communities, or friends-only posts
- Login-only pages
- Screenshots without source links
- Very old or unverifiable postings
- Non-internship roles unless they strongly clarify entry-level direction definitions

Source type values:

- `official`
- `recruiting_platform`
- `school_public`
- `manual_note`

`manual_note` can be used for temporary notes, but it must not count as real market evidence.

## CSV Collection Template

Pilot collection will use CSV before building an admin review UI.

Required columns:

- `source_url`
- `source_type`
- `collected_at`
- `company`
- `role_title`
- `role_category`
- `location`
- `employment_type`
- `raw_text`
- `responsibilities_text`
- `requirements_text`
- `source_quality`
- `collector_notes`

`source_quality` values:

- `high`: company official recruiting page, official campus page, or public school career page
- `medium`: public recruiting platform page with complete role details
- `low`: incomplete, unstable, or unclear source

Only `high` and `medium` records should be eligible for approved evidence in the pilot.

## AI Initial Annotation

The first model integration should support internal JD annotation only. It should not expose user-facing AI answers yet.

Input per JD:

- role title
- company
- responsibilities text
- requirements text
- raw JD text
- current 9 direction definitions

Output must be strict JSON:

```json
{
  "mapped_direction": "growth",
  "secondary_directions": ["campaign"],
  "confidence": 0.82,
  "task_keywords": ["数据复盘", "路径分析", "效果对比"],
  "capability_keywords": ["指标意识", "假设验证", "表格能力"],
  "tool_keywords": ["Excel", "SQL"],
  "jargon_terms": ["转化", "留存", "复盘"],
  "evidence_quotes": [
    {
      "text": "负责活动数据分析和效果复盘",
      "supports": "task_keywords"
    }
  ],
  "reasoning_summary": "该 JD 高频出现数据分析、效果复盘和路径优化，因此主方向更接近数据增长型。",
  "needs_human_attention": false,
  "attention_reasons": []
}
```

Rules:

- `mapped_direction` must be one of the 9 supported direction keys.
- `secondary_directions` may contain at most 2 directions.
- `confidence` must be between 0 and 1.
- `task_keywords` and `capability_keywords` should each contain 3-8 items.
- `tool_keywords` may contain 0-6 items.
- `jargon_terms` may contain 0-8 items.
- `evidence_quotes` must come from the JD text.
- The AI must not invent sources, skills, or JD requirements.
- The AI must not generate user career advice in this internal annotation step.

Low confidence rules:

- `confidence < 0.65`
- JD text is too short
- role title and responsibilities conflict
- direction is ambiguous
- more than 2 plausible secondary directions appear

Any of these should set `needs_human_attention = true`.

## Human Review

The pilot will use exported CSV or JSON for human review.

Review flow:

1. Import collected JD records.
2. Run AI initial annotation.
3. Export AI annotations for review.
4. Human reviewer corrects directions, keywords, notes, and status.
5. Import reviewed annotations.
6. Only approved records enter evidence summaries.

Review columns:

- `jd_id`
- `source_url`
- `company`
- `role_title`
- `responsibilities_text`
- `requirements_text`
- `ai_mapped_direction`
- `reviewed_mapped_direction`
- `ai_secondary_directions`
- `reviewed_secondary_directions`
- `ai_task_keywords`
- `reviewed_task_keywords`
- `ai_capability_keywords`
- `reviewed_capability_keywords`
- `ai_tool_keywords`
- `reviewed_tool_keywords`
- `ai_jargon_terms`
- `reviewed_jargon_terms`
- `ai_confidence`
- `needs_human_attention`
- `review_status`
- `review_notes`
- `reviewed_by`
- `reviewed_at`

`review_status` values:

- `approved`
- `needs_review`
- `rejected`

Approval rules:

- Source is public and traceable.
- JD text is complete enough.
- Main direction can be justified from responsibilities or requirements.
- At least 3 task keywords are present.
- At least 3 capability keywords are present.
- Keywords are grounded in JD text.
- Human reviewer confirms the mapping is reasonable.

Rejected records must not enter formal evidence summaries.

## Evidence Rules

Evidence summaries may only use records where:

- `review_status = approved`
- `source_quality` is `high` or `medium`
- `source_type` is not `manual_note`

Evidence summaries should expose:

- approved JD count
- high-frequency tasks
- high-frequency capabilities
- representative roles
- source type summary
- optional tool and jargon summaries

Result pages should avoid unsupported claims. If a direction has too little approved evidence, the UI should say that evidence is still limited.

## Accuracy Metrics

Data quality metrics:

- Pilot: 30-50 collected JD records.
- Pilot: at least 20 approved JD records.
- Pilot: at least 6 directions covered.
- Full MVP: 300-500 collected JD records.
- Full MVP: every direction has at least 30 approved JD records.
- Full MVP: every approved JD has source URL, date, source type, direction annotation, task keywords, and capability keywords.

Assessment stability metrics:

- Every direction has JD evidence.
- Every question maps to at least 2-3 real JD task patterns.
- Options avoid obvious direction labels.
- Similar answer behavior produces stable direction outcomes.
- Different directions can produce meaningfully different score profiles.

User feedback metrics:

- Pilot: 10-15 real users test the quiz.
- Full MVP: 30-50 real users provide feedback.
- At least 70% say the result is basically accurate or useful.
- At least 70% say suggestions are actionable.
- Main or supporting direction matches user self-reported interest, application target, or experience at least 60% of the time.
- Inaccurate feedback is categorized and used to revise questions or result explanations.

## User-Side AI Scope

User-facing AI should not be opened in this next stage.

The backend may keep a placeholder endpoint and may add shared AI infrastructure, but the real model call should first support internal JD annotation. User-side AI explanation can be considered after approved evidence is reliable.

Future user-facing AI rules:

- Use approved JD evidence only.
- Do not invent sources.
- Do not make absolute career claims.
- Explain uncertainty.
- Avoid resume or private data handling until privacy and storage rules are designed.

## Completion Definition

The project can be called basically complete when:

1. It has 300-500 real public JD records.
2. Every direction has at least 30 approved JD records.
3. The result page shows evidence count for the selected direction.
4. Direction analysis, role keywords, and portfolio suggestions are traceable to approved JD evidence.
5. Every question has a documented JD evidence basis.
6. User feedback reaches the target usefulness and direction-match metrics.
7. Documentation explains data sources, annotation process, limitations, and exclusions.
8. User-facing AI, if enabled later, is grounded only in approved evidence.

## Out Of Scope For This Stage

- User-facing AI chat
- Resume upload or resume rewriting
- Login
- Admin review UI
- Automated crawlers
- Production deployment
- Claims of academic-grade recommendation accuracy
