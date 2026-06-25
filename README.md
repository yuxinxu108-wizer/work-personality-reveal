# Intern Direction Test

JD-backed internship direction assessment MVP for Chinese internet internship roles.

The current product includes:

- FastAPI backend
- SQLite local database
- 25-question assessment
- 9 internship directions
- JD evidence summaries
- Static frontend served from `frontend/`
- 148 条 BOSS JD in `data/pilot/collected_jds.csv`
- Human-review CSV workflow in `data/pilot/review.csv`

User-facing AI explanation remains a placeholder. Internal JD annotation can run through fixture data or OpenAI mode for the pilot data workflow.

## Current Project Entry

The formal frontend entry is:

`frontend/index.html`

The formal backend entry is:

`backend/app/main.py`

Root-level `data.js` and `scoring.js` are retained for legacy scoring tests. Do not treat them as the current product frontend.

## Setup

Create the Python environment and install backend dependencies:

```bash
npm run setup
```

This creates `.venv` and installs `backend/requirements.txt`.

## Run Locally

Start the backend:

```bash
npm run backend
```

Start the frontend in a separate terminal:

```bash
npm run frontend
```

Open:

```text
http://127.0.0.1:5174/
```

## Database

`data/app.db` is the local SQLite database used by the app.

To seed the manual baseline records without touching the pilot CSV files:

```bash
npm run db:seed
```

The pilot data lives in:

- `data/pilot/collected_jds.csv`: 148 条 BOSS JD prepared for import
- `data/pilot/review.csv`: reviewed annotation CSV used by the pilot import flow

The current pilot review file was generated from cleaned BOSS JD data and should still be sampled manually before being treated as strong market evidence.

## Real JD Pilot Loop

The app separates manually seeded examples from formal market evidence. Manual seed records support local schema validation and product flow testing; formal market evidence should come from reviewed real public JD records.

Run the pilot pipeline:

```bash
PYTHONPATH=. .venv/bin/python scripts/import_collected_jds.py --db data/app.db --csv data/pilot/collected_jds.csv
PYTHONPATH=. .venv/bin/python scripts/run_jd_ai_annotation.py --db data/app.db --provider fixture --fixture-json data/pilot/ai_annotation_fixture.json
PYTHONPATH=. .venv/bin/python scripts/export_jd_review.py --db data/app.db --csv data/pilot/review.csv
PYTHONPATH=. .venv/bin/python scripts/import_reviewed_jds.py --db data/app.db --csv data/pilot/review.csv
PYTHONPATH=. .venv/bin/python scripts/pilot_metrics.py --db data/app.db
```

Use fixture mode when model access is unavailable or when testing the review flow.

## Verify

Run frontend and Node scoring tests:

```bash
npm test
```

Run backend tests:

```bash
npm run backend:test
```

Run the full local verification suite:

```bash
npm run verify
```

If backend tests report that `pytest` is unavailable, run:

```bash
npm run setup
```

## Notes

- `data/app.db` is generated locally and ignored by git.
- `data/pilot` contains the current real JD import files.
- Resume upload, real user-facing AI explanation, login, admin UI, and production deployment are outside the current MVP.
