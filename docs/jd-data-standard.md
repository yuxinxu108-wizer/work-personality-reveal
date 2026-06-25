# JD Data Standard

Phase 1 uses manually curated JD samples. They are seed records for validating the assessment model and evidence summaries, not a complete labor-market dataset.

Required top-level fields:

- `id`
- `company`
- `role_title`
- `role_category`
- `source_url`
- `source_type`
- `location`
- `employment_type`
- `raw_text`
- `responsibilities_text`
- `requirements_text`
- `collected_at`
- `annotation`

Required annotation fields:

- `mapped_direction`
- `secondary_directions`
- `task_keywords`
- `capability_keywords`
- `tool_keywords`
- `jargon_terms`
- `notes`

Source type rules:

- `official`: company recruiting site
- `recruiting_platform`: third-party recruiting page
- `school_public`: public school career page or campus recruitment page
- `manual_note`: manually entered sample or temporary note

Data quality rules:

- Use `YYYY-MM-DD` for `collected_at`.
- `mapped_direction` and `secondary_directions` must use one of the 9 supported direction keys.
- Keyword arrays must contain non-empty strings.
- Do not use account passwords, private posts, logged-in-only social content, or copied private messages.
- Do not present `manual_note` records as real verified market coverage.

Current seed limitation:

The current `data/seeds/jd_seed.json` records are manual seed samples. They support local schema validation and product flow testing. Later data work should replace or supplement them with verified public JD records and keep the original source URL.

## Pilot Source And Review Rules

Formal evidence can only come from reviewed real public JD records.

Allowed `source_type` values:

- `official`: company official recruiting page.
- `recruiting_platform`: public recruiting platform page with complete JD text.
- `school_public`: public school career page or campus recruitment page.
- `manual_note`: temporary internal notes. These never count as formal market evidence.

Allowed `source_quality` values:

- `high`: official company recruiting page, official campus page, or public school career page.
- `medium`: public recruiting platform page with complete role details.
- `low`: incomplete, unstable, unclear, or weakly sourced JD.

Formal evidence filter:

- `review_status = approved`
- `source_quality` is `high` or `medium`
- `source_type` is not `manual_note`

Rejected and `needs_review` records stay in the database for audit, but they do not support result-page claims.
