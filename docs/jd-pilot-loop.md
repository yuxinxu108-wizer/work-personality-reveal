# JD Pilot Loop

This guide runs the 30-50 real public JD pilot before scaling to 300-500 records.

## 1. Collect Public JDs

Create a local pilot folder and start from the template:

```bash
mkdir -p data/pilot
cp data/templates/jd_collection_template.csv data/pilot/collected_jds.csv
```

Use `data/pilot/collected_jds.csv` for pilot collection.

Required fields:

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

Only collect public pages that do not require login. Do not use private communities, screenshots without links, or unverifiable text as real evidence.

## 2. Import Collected JDs

```bash
PYTHONPATH=. .venv/bin/python scripts/import_collected_jds.py --db data/app.db --csv data/pilot/collected_jds.csv
```

## 3. Create Internal AI Annotation Drafts

Fixture mode:

```bash
PYTHONPATH=. .venv/bin/python scripts/run_jd_ai_annotation.py --db data/app.db --provider fixture --fixture-json data/pilot/ai_annotation_fixture.json
```

Fixture mode requires `data/pilot/ai_annotation_fixture.json`, keyed by `jd_id`. Use it when model access is unavailable or when testing the review flow.

OpenAI mode:

```bash
PYTHONPATH=. .venv/bin/python scripts/run_jd_ai_annotation.py --db data/app.db --provider openai --model gpt-4.1-mini
```

This stage is internal only. It does not power user-facing AI answers.

## 4. Export Human Review CSV

```bash
PYTHONPATH=. .venv/bin/python scripts/export_jd_review.py --db data/app.db --csv data/pilot/review.csv
```

Human reviewers edit the `reviewed_*` columns and set `review_status` to one of:

- `approved`
- `needs_review`
- `rejected`

## 5. Import Reviewed Annotations

```bash
PYTHONPATH=. .venv/bin/python scripts/import_reviewed_jds.py --db data/app.db --csv data/pilot/review.csv
```

## 6. Check Pilot Metrics

```bash
PYTHONPATH=. .venv/bin/python scripts/pilot_metrics.py --db data/app.db
```

Pilot completion criteria:

- 30-50 collected JD records.
- At least 20 approved formal JD records.
- At least 6 approved directions covered.
- Every approved record has source URL, source type, source quality, direction annotation, task keywords, and capability keywords.

## Evidence Rule

The result page only uses formal evidence:

- approved review status
- high or medium source quality
- not `manual_note`
