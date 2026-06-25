# JD-Backed Assessment Platform Design

## Context

The current project is a static internship direction quiz. It has a polished front-end experience, 25 questions, 9 result directions, weighted scoring, result guidance, jargon explanations, and animal avatar artwork.

The next phase changes the project from a static quiz into a data-backed assessment product. The goal is to make questions and result profiles traceable to real internship job descriptions instead of relying only on intuition.

## Product Goal

Build a JD-backed internship direction assessment system.

The product should help beginner students understand which internet internship direction they should try first, and explain the recommendation using structured evidence from real job descriptions.

## Phase 1 Scope

Phase 1 is a data-backed MVP.

Included:

- Add a Python FastAPI backend.
- Add a SQLite database.
- Define a JD data model.
- Import 20-30 manually curated JD samples first.
- Build scripts for importing JD seed data into SQLite.
- Define the 9 assessment directions with clearer competency definitions.
- Connect questions and result explanations to direction definitions and JD evidence.
- Expose API endpoints for directions, questions, assessment submission, and result evidence.
- Refactor the front end enough to read from the API instead of hardcoded static data.
- Show medium-depth evidence on the result page:
  - JD sample count for the result direction.
  - high-frequency tasks.
  - high-frequency capability requirements.
  - representative role titles.
  - source type summary.
- Add AI module placeholders and prompt templates only.

Excluded:

- No real AI model call in Phase 1.
- No resume upload or resume editing.
- No login, accounts, or user history.
- No admin management UI.
- No automatic large-scale JD crawler.
- No PostgreSQL deployment.
- No production hosting.

## Architecture

Use this structure:

```text
intern-direction-test/
  frontend/
    index.html
    styles.css
    js/
      api.js
      app.js
      render.js
      scoring-client.js
    assets/
      avatars/
  backend/
    app/
      main.py
      db.py
      models.py
      schemas.py
      repositories/
        jd_repository.py
        assessment_repository.py
      services/
        assessment_service.py
        evidence_service.py
        keyword_service.py
      ai/
        prompts.py
        README.md
    tests/
  data/
    seeds/
      jd_seed.json
      direction_definitions.json
      question_bank.json
    app.db
  scripts/
    import_jds.py
    analyze_keywords.py
  docs/
    jd-data-standard.md
    direction-definitions.md
```

The current root-level static files can stay during migration, but the target structure should separate `frontend/`, `backend/`, `data/`, and `scripts/`.

## Why FastAPI

FastAPI is the backend API framework. It will receive requests from the front end, query SQLite, run assessment logic, and return JSON.

Reasons:

- Python is better for the upcoming JD text processing, keyword analysis, prompt preparation, and future AI work.
- FastAPI is lightweight and quick for API development.
- FastAPI provides automatic API docs, useful while the API is changing.
- It keeps future AI integration straightforward without forcing a rewrite.

## Why SQLite

SQLite is the Phase 1 database. It is a local `.db` file, not a separate database server.

Reasons:

- More structured and queryable than JSON.
- Easier to filter by role type, source type, company, direction, and keywords.
- Good enough for 20-120 JD samples.
- Much lighter than PostgreSQL for this local MVP.
- Can later migrate to PostgreSQL if the project becomes multi-user or hosted.

## Data Model

### `jd_sources`

Stores each job description sample.

Fields:

- `id`
- `company`
- `role_title`
- `role_category`
- `source_url`
- `source_type`
  - `official`
  - `recruiting_platform`
  - `manual_note`
- `location`
- `employment_type`
- `raw_text`
- `responsibilities_text`
- `requirements_text`
- `collected_at`
- `created_at`

### `jd_annotations`

Stores structured labels and extracted information for a JD.

Fields:

- `id`
- `jd_id`
- `mapped_direction`
- `secondary_directions`
- `task_keywords`
- `capability_keywords`
- `tool_keywords`
- `jargon_terms`
- `notes`

JSON text fields are acceptable in SQLite for Phase 1.

### `directions`

Stores the 9 assessment directions.

Fields:

- `key`
- `label`
- `short_label`
- `animal`
- `avatar_src`
- `plain_summary`
- `competency_definition`
- `typical_tasks`
- `common_capabilities`
- `suitable_roles`
- `risk_notes`
- `portfolio_guidance`

The 9 direction keys remain:

- `ux`
- `process`
- `growth`
- `content`
- `campaign`
- `community`
- `research`
- `strategy`
- `project`

### `questions`

Stores assessment questions.

Fields:

- `id`
- `text`
- `question_type`
  - `scenario`
  - `preference`
  - `pressure`
  - `calibration`
- `basis_notes`
- `related_jd_tasks`

### `question_options`

Stores answer options and scoring weights.

Fields:

- `id`
- `question_id`
- `text`
- `weights`

`weights` can be JSON in Phase 1:

```json
[
  { "direction": "research", "value": 2 },
  { "direction": "campaign", "value": 1 }
]
```

### `assessment_runs`

Optional in Phase 1. If implemented, stores anonymous submissions for local testing.

Fields:

- `id`
- `answers_json`
- `scores_json`
- `main_direction`
- `supporting_directions`
- `created_at`

No personal user data should be stored in Phase 1.

## JD Seed Workflow

Phase 1 starts with 20-30 high-quality manually curated JD samples.

Workflow:

1. Manually collect JD information from official recruiting pages where possible.
2. Use recruiting platform pages only when official pages are unavailable or dynamic.
3. Record source type clearly.
4. Save structured samples in `data/seeds/jd_seed.json`.
5. Run `scripts/import_jds.py` to load samples into SQLite.
6. Run `scripts/analyze_keywords.py` to summarize high-frequency task and capability terms.
7. Use the summary to revise direction definitions, questions, and result profiles.

No account credentials, private social accounts, or scraped logged-in content should be used.

## Backend API

### `GET /api/health`

Returns service status.

### `GET /api/directions`

Returns the 9 directions and their competency definitions.

### `GET /api/questions`

Returns active questions and options. It should not expose internal scoring rationale more than needed by the client.

### `POST /api/assessment/submit`

Request:

```json
{
  "answers": {
    "q01": 1,
    "q02": 0
  }
}
```

Response:

```json
{
  "main_direction": "content",
  "supporting_directions": ["growth"],
  "scores": {
    "content": 100,
    "growth": 82
  },
  "result": {
    "title": "内容表达型",
    "summary": "...",
    "route_steps": [],
    "action_plan": [],
    "portfolio_suggestion": "..."
  },
  "evidence": {
    "jd_count": 18,
    "high_frequency_tasks": [],
    "high_frequency_capabilities": [],
    "representative_roles": [],
    "source_type_summary": {
      "official": 10,
      "recruiting_platform": 8
    }
  }
}
```

### `GET /api/evidence/{direction_key}`

Returns medium-depth evidence for one direction:

- JD count.
- high-frequency tasks.
- high-frequency capabilities.
- representative roles.
- source type summary.

It should not expose every source link in Phase 1.

### `POST /api/ai/explain`

Placeholder only in Phase 1.

Returns:

```json
{
  "available": false,
  "message": "AI explanation is reserved for a later phase."
}
```

## Assessment Logic

The backend owns assessment scoring in Phase 1.

Rules:

- The client sends answers.
- The backend computes raw scores.
- The backend selects one main direction.
- The backend selects one supporting direction by default.
- If supporting directions are tied or extremely close, return at most two.
- If many top scores are close, return a multi-sided note while still recommending one main path.

Question options must be traceable to:

- a behavior tendency,
- one or two direction weights,
- related JD task/capability evidence,
- a short internal basis note.

## Frontend Changes

Keep the current visual direction and user flow:

- home screen,
- quiz screen,
- loading state,
- result screen.

Change the data flow:

- `GET /api/questions` replaces hardcoded question data.
- `POST /api/assessment/submit` replaces client-only scoring.
- result evidence is rendered from backend response.
- existing animal avatars remain front-end assets.

The front end should show medium evidence on the result page:

- "该方向参考了 X 条 JD"
- high-frequency tasks,
- high-frequency capabilities,
- representative role titles,
- source type summary.

If the API is unavailable during local development, the frontend may show a clear error state. It should not silently fall back to old hardcoded data without telling the user.

## AI Placeholder

Create `backend/app/ai/` with:

- `prompts.py`
- `README.md`

It should document future prompt inputs:

- user answers,
- score distribution,
- main/supporting directions,
- JD evidence,
- portfolio suggestion,
- target role if provided.

No real model call is implemented in Phase 1. If a user asks for AI behavior before it exists, the app should clearly say it is not available yet.

## Testing

Backend tests:

- database initialization works,
- JD seed import works,
- directions can be loaded,
- questions can be loaded,
- assessment scoring returns expected main/supporting directions,
- evidence summary returns expected fields,
- AI placeholder returns `available: false`.

Frontend checks:

- page loads from localhost,
- questions render from API,
- full quiz submission works,
- result page renders evidence,
- API unavailable state is visible,
- existing avatar assets still render.

Data checks:

- every JD has source type,
- every JD has role category,
- every annotated JD maps to at least one direction,
- every active question has at least 4 options,
- every option has valid direction weights,
- every result direction has evidence text.

## Phase 2 Notes

Future phases may add:

- AI result explanation,
- AI follow-up questions,
- resume rewriting,
- user-uploaded target JD matching,
- admin page for JD annotation,
- larger semi-automated JD collection,
- PostgreSQL if hosted or multi-user.

These are intentionally out of Phase 1.
