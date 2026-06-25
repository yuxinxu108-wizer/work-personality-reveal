# Real JD Pilot Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the 30-50 real public JD pilot loop: collect CSV JD records, create internal AI annotation drafts, export/import human review, and make assessment evidence use only reviewed real-market data.

**Architecture:** Keep the current FastAPI + SQLite + static frontend architecture. Add a data pipeline around the existing `jd_sources` and `jd_annotations` tables: collected JD source records, AI draft annotations, reviewed final annotations, formal evidence filtering, and pilot metrics scripts.

**Tech Stack:** Python 3, FastAPI, SQLite, pytest, CSV/JSON standard library, existing frontend JavaScript.

---

## Scope

This plan implements the approved 30-50 JD pilot loop only.

Included:

- CSV collection template for public JD records.
- Import validation for collected JDs.
- SQLite schema support for source quality, source review status, AI draft annotations, and human-reviewed final annotations.
- Internal AI annotation interface and strict JSON validation.
- CSV export/import loop for human review.
- Evidence summaries that only count approved real JD records.
- Pilot metrics command showing collection, approval, source, and direction coverage.
- Documentation for how to run the pilot.

Not included:

- User-facing AI chat.
- Resume upload or resume rewrite.
- Login.
- Admin review UI.
- Automated crawling.
- Full 300-500 JD collection.
- Production deployment.

## File Structure

- Modify `backend/app/db.py`: add schema fields/tables and lightweight migrations.
- Modify `backend/app/repositories/jd_repository.py`: add insert/list helpers for collected JDs, AI drafts, reviewed annotations, and formal evidence filters.
- Modify `backend/app/services/evidence_service.py`: filter evidence to approved, high/medium, non-`manual_note` records.
- Create `backend/app/services/jd_collection_service.py`: validate and normalize collection CSV rows.
- Create `backend/app/services/jd_ai_annotation_service.py`: validate AI annotation JSON and build model prompts.
- Create `backend/app/services/jd_review_service.py`: build review CSV rows and import reviewed annotations.
- Create `backend/tests/test_jd_pilot.py`: focused tests for pilot schema, collection import, AI annotation validation, review import, evidence filtering, and metrics.
- Modify `scripts/import_jds.py`: allow `school_public`, source quality defaults, and reviewed annotation defaults for existing seed data.
- Create `scripts/import_collected_jds.py`: import pilot collection CSV into SQLite.
- Create `scripts/run_jd_ai_annotation.py`: run internal annotation drafts through OpenAI or a fixture file.
- Create `scripts/export_jd_review.py`: export AI drafts for human review.
- Create `scripts/import_reviewed_jds.py`: import corrected review CSV into final annotations.
- Create `scripts/pilot_metrics.py`: print pilot readiness counts.
- Create `data/templates/jd_collection_template.csv`: collection template with required headers and one example row.
- Create `data/templates/jd_review_template.csv`: documented review headers for human reviewers.
- Modify `docs/jd-data-standard.md`: update source/review/evidence rules.
- Create `docs/jd-pilot-loop.md`: operational guide for the pilot.
- Modify `README.md`: add pilot commands and localhost notes.

---

### Task 1: Schema And Repository Support For Pilot Data

**Files:**
- Modify: `backend/app/db.py`
- Modify: `backend/app/repositories/jd_repository.py`
- Modify: `scripts/import_jds.py`
- Test: `backend/tests/test_jd_pilot.py`

- [ ] **Step 1: Write failing schema and repository tests**

Create `backend/tests/test_jd_pilot.py` with these tests:

```python
from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.app.db import connect, initialize_database, to_json
from backend.app.repositories.jd_repository import JDRepository


DIRECTION_KEYS = {
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


def initialize_test_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "pilot.db"
    initialize_database(db_path)
    with connect(db_path) as conn:
        for key in DIRECTION_KEYS:
            conn.execute(
                """
                INSERT INTO directions (
                  key, label, short_label, animal, avatar_src, plain_summary,
                  competency_definition, typical_tasks, common_capabilities,
                  suitable_roles, risk_notes, portfolio_guidance
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    key,
                    f"{key} label",
                    key,
                    "animal",
                    f"/assets/{key}.png",
                    f"{key} summary",
                    f"{key} competency",
                    to_json([f"{key} task"]),
                    to_json([f"{key} capability"]),
                    to_json([f"{key} intern"]),
                    to_json([f"{key} risk"]),
                    f"{key} portfolio",
                ),
            )
    return db_path


def insert_source(
    db_path: Path,
    jd_id: str,
    *,
    source_type: str = "official",
    source_quality: str = "high",
) -> None:
    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO jd_sources (
              id, company, role_title, role_category, source_url, source_type,
              source_quality, collector_notes, raw_status, location,
              employment_type, raw_text, responsibilities_text,
              requirements_text, collected_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                jd_id,
                "示例公司",
                "产品运营实习生",
                "互联网实习",
                f"https://example.com/jobs/{jd_id}",
                source_type,
                source_quality,
                "公开页面采集",
                "collected",
                "上海",
                "internship",
                "负责活动数据整理、用户路径分析和复盘，也负责用户反馈整理、数据复盘和活动支持，要求沟通清楚。",
                "负责活动数据整理、用户路径分析和复盘，也负责用户反馈整理、数据复盘和活动支持。",
                "要求沟通清楚，能使用表格整理信息。",
                "2026-05-29",
            ),
        )


def test_initialize_database_adds_pilot_columns_and_ai_table(tmp_path: Path) -> None:
    db_path = initialize_test_db(tmp_path)

    with connect(db_path) as conn:
        source_columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(jd_sources)")
        }
        annotation_columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(jd_annotations)")
        }
        ai_table = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
            ("jd_ai_annotations",),
        ).fetchone()

    assert {"source_quality", "collector_notes", "raw_status"} <= source_columns
    assert {"review_status", "review_notes", "reviewed_by", "reviewed_at"} <= annotation_columns
    assert ai_table is not None


def test_source_type_accepts_school_public(tmp_path: Path) -> None:
    db_path = initialize_test_db(tmp_path)

    insert_source(db_path, "jd-school", source_type="school_public")

    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT source_type FROM jd_sources WHERE id = ?",
            ("jd-school",),
        ).fetchone()

    assert row["source_type"] == "school_public"


def test_repository_lists_only_formal_approved_annotations(tmp_path: Path) -> None:
    db_path = initialize_test_db(tmp_path)
    insert_source(db_path, "official-approved", source_type="official", source_quality="high")
    insert_source(db_path, "manual-approved", source_type="manual_note", source_quality="high")
    insert_source(db_path, "official-rejected", source_type="official", source_quality="high")
    insert_source(db_path, "low-approved", source_type="official", source_quality="low")

    with connect(db_path) as conn:
        rows = [
            ("ann-1", "official-approved", "approved"),
            ("ann-2", "manual-approved", "approved"),
            ("ann-3", "official-rejected", "rejected"),
            ("ann-4", "low-approved", "approved"),
        ]
        for annotation_id, jd_id, status in rows:
            conn.execute(
                """
                INSERT INTO jd_annotations (
                  id, jd_id, mapped_direction, secondary_directions,
                  task_keywords, capability_keywords, tool_keywords,
                  jargon_terms, notes, review_status, review_notes,
                  reviewed_by, reviewed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    annotation_id,
                    jd_id,
                    "growth",
                    json.dumps(["campaign"], ensure_ascii=False),
                    json.dumps(["数据复盘", "路径分析", "效果对比"], ensure_ascii=False),
                    json.dumps(["指标意识", "假设验证", "表格能力"], ensure_ascii=False),
                    json.dumps(["Excel"], ensure_ascii=False),
                    json.dumps(["转化"], ensure_ascii=False),
                    "reviewed",
                    status,
                    "human checked",
                    "reviewer-a",
                    "2026-05-29",
                ),
            )

    repository = JDRepository(db_path)

    formal = repository.list_jd_annotations_for_direction("growth", formal_only=True)
    all_annotations = repository.list_jd_annotations_for_direction("growth", formal_only=False)

    assert [annotation["role_title"] for annotation in formal] == ["产品运营实习生"]
    assert len(all_annotations) == 4
```

- [ ] **Step 2: Run the failing tests**

Run:

```bash
PYTHONPATH=. .venv/bin/python -m pytest backend/tests/test_jd_pilot.py -q
```

Expected: fails because `source_quality`, `collector_notes`, `raw_status`, `jd_ai_annotations`, `review_status`, and `formal_only` do not exist yet.

- [ ] **Step 3: Update `backend/app/db.py` schema**

Modify `SCHEMA_SQL` so `jd_sources`, `jd_annotations`, and the new `jd_ai_annotations` definitions are:

```python
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS jd_sources (
  id TEXT PRIMARY KEY,
  company TEXT NOT NULL,
  role_title TEXT NOT NULL,
  role_category TEXT NOT NULL,
  source_url TEXT NOT NULL,
  source_type TEXT NOT NULL CHECK (
    source_type IN ('official', 'recruiting_platform', 'school_public', 'manual_note')
  ),
  source_quality TEXT NOT NULL DEFAULT 'medium' CHECK (
    source_quality IN ('high', 'medium', 'low')
  ),
  collector_notes TEXT NOT NULL DEFAULT '',
  raw_status TEXT NOT NULL DEFAULT 'collected' CHECK (
    raw_status IN ('collected', 'ai_annotated', 'reviewed')
  ),
  location TEXT NOT NULL,
  employment_type TEXT NOT NULL,
  raw_text TEXT NOT NULL,
  responsibilities_text TEXT NOT NULL,
  requirements_text TEXT NOT NULL,
  collected_at TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS jd_ai_annotations (
  id TEXT PRIMARY KEY,
  jd_id TEXT NOT NULL REFERENCES jd_sources(id),
  mapped_direction TEXT NOT NULL REFERENCES directions(key),
  secondary_directions TEXT NOT NULL,
  confidence REAL NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
  task_keywords TEXT NOT NULL,
  capability_keywords TEXT NOT NULL,
  tool_keywords TEXT NOT NULL,
  jargon_terms TEXT NOT NULL,
  evidence_quotes TEXT NOT NULL,
  reasoning_summary TEXT NOT NULL,
  needs_human_attention INTEGER NOT NULL CHECK (needs_human_attention IN (0, 1)),
  attention_reasons TEXT NOT NULL,
  model_name TEXT NOT NULL,
  prompt_version TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS jd_annotations (
  id TEXT PRIMARY KEY,
  jd_id TEXT NOT NULL REFERENCES jd_sources(id),
  ai_annotation_id TEXT REFERENCES jd_ai_annotations(id),
  mapped_direction TEXT NOT NULL REFERENCES directions(key),
  secondary_directions TEXT NOT NULL,
  task_keywords TEXT NOT NULL,
  capability_keywords TEXT NOT NULL,
  tool_keywords TEXT NOT NULL,
  jargon_terms TEXT NOT NULL,
  notes TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'approved' CHECK (
    review_status IN ('approved', 'needs_review', 'rejected')
  ),
  review_notes TEXT NOT NULL DEFAULT '',
  reviewed_by TEXT NOT NULL DEFAULT '',
  reviewed_at TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS directions (
  key TEXT PRIMARY KEY,
  label TEXT NOT NULL,
  short_label TEXT NOT NULL,
  animal TEXT NOT NULL,
  avatar_src TEXT NOT NULL,
  plain_summary TEXT NOT NULL,
  competency_definition TEXT NOT NULL,
  typical_tasks TEXT NOT NULL,
  common_capabilities TEXT NOT NULL,
  suitable_roles TEXT NOT NULL,
  risk_notes TEXT NOT NULL,
  portfolio_guidance TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS questions (
  id TEXT PRIMARY KEY,
  text TEXT NOT NULL,
  question_type TEXT NOT NULL CHECK (
    question_type IN ('scenario', 'preference', 'pressure', 'calibration')
  ),
  basis_notes TEXT NOT NULL,
  related_jd_tasks TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS question_options (
  id TEXT PRIMARY KEY,
  question_id TEXT NOT NULL REFERENCES questions(id),
  text TEXT NOT NULL,
  weights TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS assessment_runs (
  id TEXT PRIMARY KEY,
  answers_json TEXT NOT NULL,
  scores_json TEXT NOT NULL,
  main_direction TEXT NOT NULL REFERENCES directions(key),
  supporting_directions TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""
```

Add migration helpers after `_migrate_direction_foreign_keys(conn)`:

```python
        _migrate_pilot_columns(conn)
        _migrate_jd_sources_source_type_check(conn)
```

Add this function:

```python
def _migrate_pilot_columns(conn: sqlite3.Connection) -> None:
    _add_column_if_missing(
        conn,
        "jd_sources",
        "source_quality",
        "TEXT NOT NULL DEFAULT 'medium'",
    )
    _add_column_if_missing(
        conn,
        "jd_sources",
        "collector_notes",
        "TEXT NOT NULL DEFAULT ''",
    )
    _add_column_if_missing(
        conn,
        "jd_sources",
        "raw_status",
        "TEXT NOT NULL DEFAULT 'collected'",
    )
    _add_column_if_missing(
        conn,
        "jd_annotations",
        "ai_annotation_id",
        "TEXT REFERENCES jd_ai_annotations(id)",
    )
    _add_column_if_missing(
        conn,
        "jd_annotations",
        "review_status",
        "TEXT NOT NULL DEFAULT 'approved'",
    )
    _add_column_if_missing(
        conn,
        "jd_annotations",
        "review_notes",
        "TEXT NOT NULL DEFAULT ''",
    )
    _add_column_if_missing(
        conn,
        "jd_annotations",
        "reviewed_by",
        "TEXT NOT NULL DEFAULT ''",
    )
    _add_column_if_missing(
        conn,
        "jd_annotations",
        "reviewed_at",
        "TEXT NOT NULL DEFAULT ''",
    )
```

Add these helpers:

```python
def _add_column_if_missing(
    conn: sqlite3.Connection,
    table: str,
    column: str,
    definition: str,
) -> None:
    if not _table_exists(conn, table):
        return
    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
```

Add this rebuild function so older local databases with the old `source_type` CHECK constraint can accept `school_public`:

```python
def _migrate_jd_sources_source_type_check(conn: sqlite3.Connection) -> None:
    if not _table_exists(conn, "jd_sources"):
        return
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = ?",
        ("jd_sources",),
    ).fetchone()
    if row and "school_public" in row["sql"]:
        return

    columns = [row["name"] for row in conn.execute("PRAGMA table_info(jd_sources)")]
    conn.execute("ALTER TABLE jd_sources RENAME TO jd_sources_old")
    conn.execute(
        """
        CREATE TABLE jd_sources (
          id TEXT PRIMARY KEY,
          company TEXT NOT NULL,
          role_title TEXT NOT NULL,
          role_category TEXT NOT NULL,
          source_url TEXT NOT NULL,
          source_type TEXT NOT NULL CHECK (
            source_type IN ('official', 'recruiting_platform', 'school_public', 'manual_note')
          ),
          source_quality TEXT NOT NULL DEFAULT 'medium' CHECK (
            source_quality IN ('high', 'medium', 'low')
          ),
          collector_notes TEXT NOT NULL DEFAULT '',
          raw_status TEXT NOT NULL DEFAULT 'collected' CHECK (
            raw_status IN ('collected', 'ai_annotated', 'reviewed')
          ),
          location TEXT NOT NULL,
          employment_type TEXT NOT NULL,
          raw_text TEXT NOT NULL,
          responsibilities_text TEXT NOT NULL,
          requirements_text TEXT NOT NULL,
          collected_at TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    column_names = ", ".join(columns)
    conn.execute(
        f"INSERT INTO jd_sources ({column_names}) "
        f"SELECT {column_names} FROM jd_sources_old"
    )
    conn.execute("DROP TABLE jd_sources_old")
```

Update `MIGRATED_TABLES_SQL["jd_annotations"]` to match the new `jd_annotations` definition.

- [ ] **Step 4: Update `JDRepository.list_jd_annotations_for_direction`**

Modify the method in `backend/app/repositories/jd_repository.py`:

```python
    def list_jd_annotations_for_direction(
        self,
        direction_key: str,
        *,
        formal_only: bool = True,
    ) -> list[dict[str, Any]]:
        where_clauses = ["ja.mapped_direction = ?"]
        params: list[Any] = [direction_key]
        if formal_only:
            where_clauses.extend(
                [
                    "ja.review_status = 'approved'",
                    "js.source_quality IN ('high', 'medium')",
                    "js.source_type != 'manual_note'",
                ]
            )
        where_sql = " AND ".join(where_clauses)
        with connect(self.db_path) as conn:
            rows = conn.execute(
                f"""
                SELECT
                  js.company,
                  js.role_title,
                  js.source_type,
                  js.source_quality,
                  ja.review_status,
                  ja.*
                FROM jd_annotations ja
                JOIN jd_sources js ON js.id = ja.jd_id
                WHERE {where_sql}
                ORDER BY js.id, ja.id
                """,
                params,
            ).fetchall()

        return [
            {
                "company": row["company"],
                "role_title": row["role_title"],
                "source_type": row["source_type"],
                "source_quality": row["source_quality"],
                "review_status": row["review_status"],
                "task_keywords": from_json(row["task_keywords"]),
                "capability_keywords": from_json(row["capability_keywords"]),
                "secondary_directions": from_json(row["secondary_directions"]),
            }
            for row in rows
        ]
```

- [ ] **Step 5: Update seed import validation defaults**

Modify `scripts/import_jds.py`:

```python
ALLOWED_SOURCE_TYPES = {"official", "recruiting_platform", "school_public", "manual_note"}
ALLOWED_SOURCE_QUALITIES = {"high", "medium", "low"}
```

In JD validation, after `source_type` validation, add:

```python
        source_quality = jd.get("source_quality", "medium")
        if source_quality not in ALLOWED_SOURCE_QUALITIES:
            raise ValueError(f"Invalid source_quality for JD {jd_id}: {source_quality}")
```

When inserting into `jd_sources`, include the new columns and defaults:

```python
                    jd.get("source_quality", "medium"),
                    jd.get("collector_notes", ""),
                    jd.get("raw_status", "reviewed"),
```

When inserting into `jd_annotations`, include:

```python
                    annotation.get("review_status", "approved"),
                    annotation.get("review_notes", "seed data"),
                    annotation.get("reviewed_by", "seed"),
                    annotation.get("reviewed_at", jd["collected_at"]),
```

- [ ] **Step 6: Run tests**

Run:

```bash
PYTHONPATH=. .venv/bin/python -m pytest backend/tests/test_jd_pilot.py backend/tests/test_api.py -q
```

Expected: pilot tests pass; if an existing API test expects manual seed evidence to count as formal evidence, update that assertion to expect `jd_count >= 0` and add a separate test with approved non-`manual_note` evidence.

- [ ] **Step 7: Commit**

```bash
git add backend/app/db.py backend/app/repositories/jd_repository.py backend/tests/test_jd_pilot.py scripts/import_jds.py
git commit -m "feat: add JD pilot schema"
```

---

### Task 2: Collection CSV Template And Importer

**Files:**
- Create: `data/templates/jd_collection_template.csv`
- Create: `backend/app/services/jd_collection_service.py`
- Create: `scripts/import_collected_jds.py`
- Test: `backend/tests/test_jd_pilot.py`

- [ ] **Step 1: Add failing collection import tests**

Append to `backend/tests/test_jd_pilot.py`:

```python
import csv

from backend.app.services.jd_collection_service import (
    REQUIRED_COLLECTION_COLUMNS,
    normalize_collection_row,
)


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def valid_collection_row() -> dict[str, str]:
    return {
        "source_url": "https://example.com/jobs/growth-intern",
        "source_type": "recruiting_platform",
        "collected_at": "2026-05-29",
        "company": "示例公司",
        "role_title": "增长运营实习生",
        "role_category": "运营",
        "location": "上海",
        "employment_type": "internship",
        "raw_text": "负责活动数据整理、用户路径分析和复盘。",
        "responsibilities_text": "负责活动数据整理、用户路径分析和复盘。",
        "requirements_text": "要求沟通清楚，会使用 Excel。",
        "source_quality": "medium",
        "collector_notes": "公开招聘平台页面",
    }


def test_normalize_collection_row_requires_public_source_url() -> None:
    row = valid_collection_row()
    row["source_url"] = "example.com/no-scheme"

    with pytest.raises(ValueError, match="source_url"):
        normalize_collection_row(row, row_number=2)


def test_normalize_collection_row_accepts_complete_row() -> None:
    normalized = normalize_collection_row(valid_collection_row(), row_number=2)

    assert normalized["id"].startswith("jd-")
    assert normalized["source_type"] == "recruiting_platform"
    assert normalized["source_quality"] == "medium"
    assert normalized["raw_status"] == "collected"
    assert set(REQUIRED_COLLECTION_COLUMNS) <= set(valid_collection_row().keys())
```

- [ ] **Step 2: Run failing tests**

Run:

```bash
PYTHONPATH=. .venv/bin/python -m pytest backend/tests/test_jd_pilot.py::test_normalize_collection_row_requires_public_source_url backend/tests/test_jd_pilot.py::test_normalize_collection_row_accepts_complete_row -q
```

Expected: fails because `jd_collection_service.py` does not exist.

- [ ] **Step 3: Create `backend/app/services/jd_collection_service.py`**

```python
from __future__ import annotations

import hashlib
from datetime import date


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

ALLOWED_SOURCE_TYPES = {"official", "recruiting_platform", "school_public", "manual_note"}
ALLOWED_SOURCE_QUALITIES = {"high", "medium", "low"}


def normalize_collection_row(row: dict[str, str], *, row_number: int) -> dict[str, str]:
    missing = [
        column
        for column in REQUIRED_COLLECTION_COLUMNS
        if column not in row or not row[column].strip()
    ]
    if missing:
        raise ValueError(f"Row {row_number} missing required columns: {', '.join(missing)}")

    normalized = {column: row[column].strip() for column in REQUIRED_COLLECTION_COLUMNS}
    if "://" not in normalized["source_url"]:
        raise ValueError(f"Row {row_number} source_url must include a URL scheme")
    if normalized["source_type"] not in ALLOWED_SOURCE_TYPES:
        raise ValueError(f"Row {row_number} invalid source_type: {normalized['source_type']}")
    if normalized["source_quality"] not in ALLOWED_SOURCE_QUALITIES:
        raise ValueError(
            f"Row {row_number} invalid source_quality: {normalized['source_quality']}"
        )
    try:
        date.fromisoformat(normalized["collected_at"])
    except ValueError as exc:
        raise ValueError(
            f"Row {row_number} collected_at must use YYYY-MM-DD format"
        ) from exc

    normalized["id"] = build_jd_id(normalized["source_url"])
    normalized["raw_status"] = "collected"
    return normalized


def build_jd_id(source_url: str) -> str:
    digest = hashlib.sha1(source_url.encode("utf-8")).hexdigest()[:12]
    return f"jd-{digest}"
```

- [ ] **Step 4: Create collection template**

Create `data/templates/jd_collection_template.csv`:

```csv
source_url,source_type,collected_at,company,role_title,role_category,location,employment_type,raw_text,responsibilities_text,requirements_text,source_quality,collector_notes
https://example.com/jobs/product-ops-intern,recruiting_platform,2026-05-29,示例公司,产品运营实习生,运营,上海,internship,负责用户反馈整理、活动支持和数据复盘。要求沟通清楚，会用表格整理信息。,负责用户反馈整理、活动支持和数据复盘。,要求沟通清楚，会用表格整理信息。,medium,示例行，正式采集时替换为真实公开 JD
```

- [ ] **Step 5: Create `scripts/import_collected_jds.py`**

```python
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.db import connect, initialize_database
from backend.app.services.jd_collection_service import normalize_collection_row


def import_collected_jds(db_path: Path, csv_path: Path) -> int:
    initialize_database(db_path)
    imported = 0
    with csv_path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        rows = [
            normalize_collection_row(row, row_number=index)
            for index, row in enumerate(reader, start=2)
        ]

    with connect(db_path) as conn:
        for row in rows:
            conn.execute(
                """
                INSERT INTO jd_sources (
                  id, company, role_title, role_category, source_url, source_type,
                  source_quality, collector_notes, raw_status, location,
                  employment_type, raw_text, responsibilities_text,
                  requirements_text, collected_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                  company = excluded.company,
                  role_title = excluded.role_title,
                  role_category = excluded.role_category,
                  source_type = excluded.source_type,
                  source_quality = excluded.source_quality,
                  collector_notes = excluded.collector_notes,
                  raw_status = excluded.raw_status,
                  location = excluded.location,
                  employment_type = excluded.employment_type,
                  raw_text = excluded.raw_text,
                  responsibilities_text = excluded.responsibilities_text,
                  requirements_text = excluded.requirements_text,
                  collected_at = excluded.collected_at
                """,
                (
                    row["id"],
                    row["company"],
                    row["role_title"],
                    row["role_category"],
                    row["source_url"],
                    row["source_type"],
                    row["source_quality"],
                    row["collector_notes"],
                    row["raw_status"],
                    row["location"],
                    row["employment_type"],
                    row["raw_text"],
                    row["responsibilities_text"],
                    row["requirements_text"],
                    row["collected_at"],
                ),
            )
            imported += 1
    return imported


def main() -> None:
    parser = argparse.ArgumentParser(description="Import collected public JD CSV rows.")
    parser.add_argument("--db", required=True, type=Path)
    parser.add_argument("--csv", required=True, type=Path)
    args = parser.parse_args()

    count = import_collected_jds(args.db, args.csv)
    print(f"Imported {count} collected JD records into {args.db}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Add importer integration test**

Append to `backend/tests/test_jd_pilot.py`:

```python
from scripts.import_collected_jds import import_collected_jds


def test_import_collected_jds_inserts_sources(tmp_path: Path) -> None:
    db_path = initialize_test_db(tmp_path)
    csv_path = tmp_path / "collected.csv"
    write_csv(csv_path, [valid_collection_row()])

    imported = import_collected_jds(db_path, csv_path)

    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT role_title, source_quality, raw_status FROM jd_sources"
        ).fetchone()

    assert imported == 1
    assert row["role_title"] == "增长运营实习生"
    assert row["source_quality"] == "medium"
    assert row["raw_status"] == "collected"
```

- [ ] **Step 7: Run tests**

```bash
PYTHONPATH=. .venv/bin/python -m pytest backend/tests/test_jd_pilot.py -q
```

Expected: all pilot tests pass.

- [ ] **Step 8: Commit**

```bash
git add data/templates/jd_collection_template.csv backend/app/services/jd_collection_service.py scripts/import_collected_jds.py backend/tests/test_jd_pilot.py
git commit -m "feat: import collected JD CSV"
```

---

### Task 3: Internal AI Annotation Draft Validation

**Files:**
- Create: `backend/app/services/jd_ai_annotation_service.py`
- Modify: `backend/requirements.txt`
- Create: `scripts/run_jd_ai_annotation.py`
- Test: `backend/tests/test_jd_pilot.py`

- [ ] **Step 1: Add failing annotation validation tests**

Append to `backend/tests/test_jd_pilot.py`:

```python
from backend.app.services.jd_ai_annotation_service import (
    validate_ai_annotation_payload,
)


def valid_ai_payload() -> dict[str, object]:
    return {
        "mapped_direction": "growth",
        "secondary_directions": ["campaign"],
        "confidence": 0.82,
        "task_keywords": ["数据复盘", "路径分析", "效果对比"],
        "capability_keywords": ["指标意识", "假设验证", "表格能力"],
        "tool_keywords": ["Excel", "SQL"],
        "jargon_terms": ["转化", "留存", "复盘"],
        "evidence_quotes": [
            {
                "text": "负责活动数据整理、用户路径分析和复盘",
                "supports": "task_keywords",
            }
        ],
        "reasoning_summary": "该 JD 高频出现数据整理、路径分析和效果复盘。",
        "needs_human_attention": False,
        "attention_reasons": [],
    }


def test_validate_ai_annotation_payload_accepts_strict_json() -> None:
    raw_text = "负责活动数据整理、用户路径分析和复盘。要求沟通清楚。"

    payload = validate_ai_annotation_payload(valid_ai_payload(), raw_text=raw_text)

    assert payload["mapped_direction"] == "growth"
    assert payload["confidence"] == 0.82
    assert payload["needs_human_attention"] is False


def test_validate_ai_annotation_payload_rejects_quote_not_in_jd() -> None:
    payload = valid_ai_payload()
    payload["evidence_quotes"] = [
        {"text": "这句话没有出现在 JD 里", "supports": "task_keywords"}
    ]

    with pytest.raises(ValueError, match="evidence_quotes"):
        validate_ai_annotation_payload(payload, raw_text="负责活动数据整理。")


def test_validate_ai_annotation_payload_marks_low_confidence_attention() -> None:
    payload = valid_ai_payload()
    payload["confidence"] = 0.4
    payload["needs_human_attention"] = False

    normalized = validate_ai_annotation_payload(
        payload,
        raw_text="负责活动数据整理、用户路径分析和复盘。",
    )

    assert normalized["needs_human_attention"] is True
    assert "confidence_below_0.65" in normalized["attention_reasons"]


def test_openai_payload_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.run_jd_ai_annotation import create_openai_payload

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        create_openai_payload("prompt", model="gpt-4.1-mini")
```

- [ ] **Step 2: Run failing tests**

```bash
PYTHONPATH=. .venv/bin/python -m pytest backend/tests/test_jd_pilot.py::test_validate_ai_annotation_payload_accepts_strict_json backend/tests/test_jd_pilot.py::test_validate_ai_annotation_payload_rejects_quote_not_in_jd backend/tests/test_jd_pilot.py::test_validate_ai_annotation_payload_marks_low_confidence_attention -q
```

Expected: fails because `jd_ai_annotation_service.py` and `create_openai_payload` do not exist.

- [ ] **Step 3: Create `backend/app/services/jd_ai_annotation_service.py`**

```python
from __future__ import annotations

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


def validate_ai_annotation_payload(
    payload: dict[str, Any],
    *,
    raw_text: str,
) -> dict[str, Any]:
    required = {
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
    missing = sorted(required - set(payload))
    if missing:
        raise ValueError(f"AI annotation missing fields: {', '.join(missing)}")

    mapped_direction = payload["mapped_direction"]
    if mapped_direction not in EXPECTED_DIRECTION_KEYS:
        raise ValueError(f"Invalid mapped_direction: {mapped_direction}")

    secondary_directions = _require_string_list(
        payload["secondary_directions"],
        "secondary_directions",
        min_items=0,
        max_items=2,
    )
    for direction in secondary_directions:
        if direction not in EXPECTED_DIRECTION_KEYS:
            raise ValueError(f"Invalid secondary direction: {direction}")

    confidence = payload["confidence"]
    if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
        raise ValueError("confidence must be a number between 0 and 1")
    if confidence < 0 or confidence > 1:
        raise ValueError("confidence must be a number between 0 and 1")

    evidence_quotes = payload["evidence_quotes"]
    if not isinstance(evidence_quotes, list):
        raise ValueError("evidence_quotes must be a list")
    for quote in evidence_quotes:
        if not isinstance(quote, dict):
            raise ValueError("evidence_quotes entries must be objects")
        text = quote.get("text")
        supports = quote.get("supports")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("evidence_quotes text must be non-empty")
        if text.strip() not in raw_text:
            raise ValueError(f"evidence_quotes text not found in JD text: {text}")
        if supports not in {"task_keywords", "capability_keywords", "tool_keywords", "jargon_terms"}:
            raise ValueError(f"Invalid evidence_quotes supports value: {supports}")

    attention_reasons = _require_string_list(
        payload["attention_reasons"],
        "attention_reasons",
        min_items=0,
        max_items=8,
    )
    needs_human_attention = bool(payload["needs_human_attention"])
    if confidence < 0.65 and "confidence_below_0.65" not in attention_reasons:
        attention_reasons.append("confidence_below_0.65")
        needs_human_attention = True
    if len(raw_text.strip()) < 80 and "jd_text_too_short" not in attention_reasons:
        attention_reasons.append("jd_text_too_short")
        needs_human_attention = True

    return {
        "mapped_direction": mapped_direction,
        "secondary_directions": secondary_directions,
        "confidence": float(confidence),
        "task_keywords": _require_string_list(payload["task_keywords"], "task_keywords", min_items=3, max_items=8),
        "capability_keywords": _require_string_list(payload["capability_keywords"], "capability_keywords", min_items=3, max_items=8),
        "tool_keywords": _require_string_list(payload["tool_keywords"], "tool_keywords", min_items=0, max_items=6),
        "jargon_terms": _require_string_list(payload["jargon_terms"], "jargon_terms", min_items=0, max_items=8),
        "evidence_quotes": evidence_quotes,
        "reasoning_summary": _require_text(payload["reasoning_summary"], "reasoning_summary"),
        "needs_human_attention": needs_human_attention,
        "attention_reasons": attention_reasons,
    }


def build_annotation_prompt(jd: dict[str, Any], directions: list[dict[str, Any]]) -> str:
    direction_lines = [
        f"- {direction['key']}: {direction['label']}。{direction['competency_definition']}"
        for direction in directions
    ]
    return "\n".join(
        [
            "你是互联网实习 JD 标注助手。只输出严格 JSON，不输出解释性正文。",
            "任务：根据 JD 内容标注主方向、辅助方向、任务关键词、能力关键词、工具词、黑话词和证据句。",
            "禁止：不要生成用户职业建议，不要编造 JD 没有出现的要求，不要编造来源。",
            "方向定义：",
            *direction_lines,
            "JD：",
            f"公司：{jd['company']}",
            f"岗位：{jd['role_title']}",
            f"职责：{jd['responsibilities_text']}",
            f"要求：{jd['requirements_text']}",
            f"原文：{jd['raw_text']}",
            "输出 JSON 字段：mapped_direction, secondary_directions, confidence, task_keywords, capability_keywords, tool_keywords, jargon_terms, evidence_quotes, reasoning_summary, needs_human_attention, attention_reasons。",
        ]
    )


def _require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _require_string_list(
    value: Any,
    field: str,
    *,
    min_items: int,
    max_items: int,
) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    if not min_items <= len(value) <= max_items:
        raise ValueError(f"{field} must contain {min_items}-{max_items} items")
    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field} must contain non-empty strings")
        normalized.append(item.strip())
    return normalized
```

- [ ] **Step 4: Create `scripts/run_jd_ai_annotation.py`**

This script supports OpenAI mode for internal AI annotation and fixture mode for tests or offline runs. The real model call is internal-only and never exposed to users.

```python
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.db import connect, initialize_database, to_json
from backend.app.services.jd_ai_annotation_service import (
    PROMPT_VERSION,
    build_annotation_prompt,
    validate_ai_annotation_payload,
)


def create_openai_payload(prompt: str, *, model: str) -> dict[str, object]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required for OpenAI annotation mode")
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError(
            "The openai package is required for OpenAI annotation mode. "
            "Install backend requirements first."
        ) from exc

    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=model,
        input=prompt,
    )
    text = response.output_text
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"OpenAI response was not valid JSON: {text}") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError("OpenAI annotation response must be a JSON object")
    return parsed


def run_ai_annotation(
    db_path: Path,
    *,
    fixture_path: Path | None,
    provider: str,
    model_name: str = "fixture",
) -> int:
    initialize_database(db_path)
    fixture_payloads: dict[str, object] = {}
    if provider not in {"fixture", "openai"}:
        raise ValueError("provider must be fixture or openai")
    if provider == "fixture":
        if fixture_path is None:
            raise ValueError("fixture_path is required for fixture provider")
        loaded = json.loads(fixture_path.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            raise ValueError("Fixture must be an object keyed by jd_id")
        fixture_payloads = loaded

    saved = 0
    with connect(db_path) as conn:
        directions = [
            dict(row)
            for row in conn.execute("SELECT * FROM directions ORDER BY key").fetchall()
        ]
        rows = conn.execute(
            """
            SELECT * FROM jd_sources
            WHERE raw_status IN ('collected', 'ai_annotated')
            ORDER BY id
            """
        ).fetchall()
        for row in rows:
            if provider == "fixture":
                if row["id"] not in fixture_payloads:
                    continue
                raw_payload = fixture_payloads[row["id"]]
            else:
                prompt = build_annotation_prompt(dict(row), directions)
                raw_payload = create_openai_payload(prompt, model=model_name)
            if not isinstance(raw_payload, dict):
                raise ValueError("Annotation payload must be a JSON object")
            payload = validate_ai_annotation_payload(
                raw_payload,
                raw_text=row["raw_text"],
            )
            annotation_id = f"ai-{uuid.uuid4().hex[:12]}"
            conn.execute(
                """
                INSERT INTO jd_ai_annotations (
                  id, jd_id, mapped_direction, secondary_directions,
                  confidence, task_keywords, capability_keywords,
                  tool_keywords, jargon_terms, evidence_quotes,
                  reasoning_summary, needs_human_attention,
                  attention_reasons, model_name, prompt_version
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    annotation_id,
                    row["id"],
                    payload["mapped_direction"],
                    to_json(payload["secondary_directions"]),
                    payload["confidence"],
                    to_json(payload["task_keywords"]),
                    to_json(payload["capability_keywords"]),
                    to_json(payload["tool_keywords"]),
                    to_json(payload["jargon_terms"]),
                    to_json(payload["evidence_quotes"]),
                    payload["reasoning_summary"],
                    1 if payload["needs_human_attention"] else 0,
                    to_json(payload["attention_reasons"]),
                    model_name,
                    PROMPT_VERSION,
                ),
            )
            conn.execute(
                "UPDATE jd_sources SET raw_status = 'ai_annotated' WHERE id = ?",
                (row["id"],),
            )
            saved += 1
    return saved


def run_ai_annotation_from_fixture(
    db_path: Path,
    fixture_path: Path,
    *,
    model_name: str = "fixture",
) -> int:
    return run_ai_annotation(
        db_path,
        fixture_path=fixture_path,
        provider="fixture",
        model_name=model_name,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Create internal AI JD annotation drafts.")
    parser.add_argument("--db", required=True, type=Path)
    parser.add_argument("--provider", choices=["fixture", "openai"], default="fixture")
    parser.add_argument("--fixture-json", type=Path)
    parser.add_argument("--model", default="gpt-4.1-mini")
    args = parser.parse_args()

    count = run_ai_annotation(
        args.db,
        fixture_path=args.fixture_json,
        provider=args.provider,
        model_name=args.model if args.provider == "openai" else "fixture",
    )
    print(f"Saved {count} AI annotation drafts")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Add OpenAI dependency**

Append this line to `backend/requirements.txt`:

```text
openai>=1.99.0,<3.0.0
```

Then install backend dependencies if the local virtualenv does not already have the package:

```bash
.venv/bin/python -m pip install -r backend/requirements.txt
```

Expected: dependencies install successfully. If network access is unavailable, keep the code and tests committed; OpenAI mode will fail clearly with the import error until dependencies are installed.

- [ ] **Step 6: Add fixture script integration test**

Append to `backend/tests/test_jd_pilot.py`:

```python
from scripts.run_jd_ai_annotation import run_ai_annotation_from_fixture


def test_run_ai_annotation_from_fixture_saves_draft(tmp_path: Path) -> None:
    db_path = initialize_test_db(tmp_path)
    insert_source(db_path, "jd-ai-1")
    fixture_path = tmp_path / "ai.json"
    fixture_path.write_text(
        json.dumps({"jd-ai-1": valid_ai_payload()}, ensure_ascii=False),
        encoding="utf-8",
    )

    saved = run_ai_annotation_from_fixture(db_path, fixture_path)

    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT mapped_direction, model_name FROM jd_ai_annotations"
        ).fetchone()
        status = conn.execute(
            "SELECT raw_status FROM jd_sources WHERE id = ?",
            ("jd-ai-1",),
        ).fetchone()

    assert saved == 1
    assert row["mapped_direction"] == "growth"
    assert row["model_name"] == "fixture"
    assert status["raw_status"] == "ai_annotated"
```

- [ ] **Step 7: Run tests**

```bash
PYTHONPATH=. .venv/bin/python -m pytest backend/tests/test_jd_pilot.py -q
```

Expected: all pilot tests pass.

- [ ] **Step 8: Commit**

```bash
git add backend/app/services/jd_ai_annotation_service.py scripts/run_jd_ai_annotation.py backend/requirements.txt backend/tests/test_jd_pilot.py
git commit -m "feat: add internal JD annotation drafts"
```

---

### Task 4: Human Review Export And Import

**Files:**
- Create: `data/templates/jd_review_template.csv`
- Create: `backend/app/services/jd_review_service.py`
- Create: `scripts/export_jd_review.py`
- Create: `scripts/import_reviewed_jds.py`
- Test: `backend/tests/test_jd_pilot.py`

- [ ] **Step 1: Add failing review flow tests**

Append to `backend/tests/test_jd_pilot.py`:

```python
from backend.app.services.jd_review_service import REVIEW_COLUMNS
from scripts.export_jd_review import export_jd_review
from scripts.import_reviewed_jds import import_reviewed_jds


def prepare_ai_review_record(tmp_path: Path) -> tuple[Path, Path]:
    db_path = initialize_test_db(tmp_path)
    insert_source(db_path, "jd-review-1")
    fixture_path = tmp_path / "ai.json"
    fixture_path.write_text(
        json.dumps({"jd-review-1": valid_ai_payload()}, ensure_ascii=False),
        encoding="utf-8",
    )
    run_ai_annotation_from_fixture(db_path, fixture_path)
    return db_path, fixture_path


def test_export_jd_review_contains_required_columns(tmp_path: Path) -> None:
    db_path, _ = prepare_ai_review_record(tmp_path)
    export_path = tmp_path / "review.csv"

    exported = export_jd_review(db_path, export_path)

    with export_path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    assert exported == 1
    assert reader.fieldnames == REVIEW_COLUMNS
    assert rows[0]["jd_id"] == "jd-review-1"
    assert rows[0]["ai_mapped_direction"] == "growth"
    assert rows[0]["review_status"] == "needs_review"


def test_import_reviewed_jds_writes_final_annotation(tmp_path: Path) -> None:
    db_path, _ = prepare_ai_review_record(tmp_path)
    export_path = tmp_path / "review.csv"
    export_jd_review(db_path, export_path)

    with export_path.open("r", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    rows[0]["reviewed_mapped_direction"] = "growth"
    rows[0]["reviewed_secondary_directions"] = "campaign"
    rows[0]["reviewed_task_keywords"] = "数据复盘|路径分析|效果对比"
    rows[0]["reviewed_capability_keywords"] = "指标意识|假设验证|表格能力"
    rows[0]["reviewed_tool_keywords"] = "Excel|SQL"
    rows[0]["reviewed_jargon_terms"] = "转化|留存|复盘"
    rows[0]["review_status"] = "approved"
    rows[0]["review_notes"] = "人工确认方向合理"
    rows[0]["reviewed_by"] = "tester"
    rows[0]["reviewed_at"] = "2026-05-29"
    write_csv(export_path, rows)

    imported = import_reviewed_jds(db_path, export_path)

    with connect(db_path) as conn:
        annotation = conn.execute(
            "SELECT mapped_direction, review_status, reviewed_by FROM jd_annotations"
        ).fetchone()
        source = conn.execute(
            "SELECT raw_status FROM jd_sources WHERE id = ?",
            ("jd-review-1",),
        ).fetchone()

    assert imported == 1
    assert annotation["mapped_direction"] == "growth"
    assert annotation["review_status"] == "approved"
    assert annotation["reviewed_by"] == "tester"
    assert source["raw_status"] == "reviewed"
```

- [ ] **Step 2: Run failing tests**

```bash
PYTHONPATH=. .venv/bin/python -m pytest backend/tests/test_jd_pilot.py::test_export_jd_review_contains_required_columns backend/tests/test_jd_pilot.py::test_import_reviewed_jds_writes_final_annotation -q
```

Expected: fails because review service and scripts do not exist.

- [ ] **Step 3: Create `backend/app/services/jd_review_service.py`**

```python
from __future__ import annotations

from datetime import date
from typing import Any


REVIEW_COLUMNS = [
    "jd_id",
    "source_url",
    "company",
    "role_title",
    "responsibilities_text",
    "requirements_text",
    "ai_annotation_id",
    "ai_mapped_direction",
    "reviewed_mapped_direction",
    "ai_secondary_directions",
    "reviewed_secondary_directions",
    "ai_task_keywords",
    "reviewed_task_keywords",
    "ai_capability_keywords",
    "reviewed_capability_keywords",
    "ai_tool_keywords",
    "reviewed_tool_keywords",
    "ai_jargon_terms",
    "reviewed_jargon_terms",
    "ai_confidence",
    "needs_human_attention",
    "review_status",
    "review_notes",
    "reviewed_by",
    "reviewed_at",
]

REVIEW_STATUSES = {"approved", "needs_review", "rejected"}
DIRECTION_KEYS = {
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


def split_pipe_list(value: str) -> list[str]:
    if not value.strip():
        return []
    return [item.strip() for item in value.split("|") if item.strip()]


def validate_review_row(row: dict[str, str], *, row_number: int) -> dict[str, Any]:
    missing = [column for column in REVIEW_COLUMNS if column not in row]
    if missing:
        raise ValueError(f"Review row {row_number} missing columns: {', '.join(missing)}")

    status = row["review_status"].strip()
    if status not in REVIEW_STATUSES:
        raise ValueError(f"Review row {row_number} invalid review_status: {status}")

    mapped_direction = row["reviewed_mapped_direction"].strip()
    if status == "approved" and mapped_direction not in DIRECTION_KEYS:
        raise ValueError(
            f"Review row {row_number} approved records need valid reviewed_mapped_direction"
        )
    if status != "approved" and not mapped_direction:
        mapped_direction = row["ai_mapped_direction"].strip()

    secondary = split_pipe_list(row["reviewed_secondary_directions"])
    if len(secondary) > 2:
        raise ValueError(f"Review row {row_number} may have at most 2 secondary directions")
    for direction in secondary:
        if direction not in DIRECTION_KEYS:
            raise ValueError(f"Review row {row_number} invalid secondary direction: {direction}")

    task_keywords = split_pipe_list(row["reviewed_task_keywords"])
    capability_keywords = split_pipe_list(row["reviewed_capability_keywords"])
    if status == "approved" and len(task_keywords) < 3:
        raise ValueError(f"Review row {row_number} approved records need 3 task keywords")
    if status == "approved" and len(capability_keywords) < 3:
        raise ValueError(
            f"Review row {row_number} approved records need 3 capability keywords"
        )

    reviewed_at = row["reviewed_at"].strip()
    if reviewed_at:
        try:
            date.fromisoformat(reviewed_at)
        except ValueError as exc:
            raise ValueError(
                f"Review row {row_number} reviewed_at must use YYYY-MM-DD format"
            ) from exc

    return {
        "jd_id": row["jd_id"].strip(),
        "ai_annotation_id": row["ai_annotation_id"].strip() or None,
        "mapped_direction": mapped_direction,
        "secondary_directions": secondary,
        "task_keywords": task_keywords,
        "capability_keywords": capability_keywords,
        "tool_keywords": split_pipe_list(row["reviewed_tool_keywords"]),
        "jargon_terms": split_pipe_list(row["reviewed_jargon_terms"]),
        "review_status": status,
        "review_notes": row["review_notes"].strip(),
        "reviewed_by": row["reviewed_by"].strip(),
        "reviewed_at": reviewed_at,
    }
```

- [ ] **Step 4: Create review export script**

Create `scripts/export_jd_review.py`:

```python
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.db import connect, from_json
from backend.app.services.jd_review_service import REVIEW_COLUMNS


def export_jd_review(db_path: Path, csv_path: Path) -> int:
    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT
              js.id AS jd_id,
              js.source_url,
              js.company,
              js.role_title,
              js.responsibilities_text,
              js.requirements_text,
              ai.id AS ai_annotation_id,
              ai.mapped_direction AS ai_mapped_direction,
              ai.secondary_directions AS ai_secondary_directions,
              ai.task_keywords AS ai_task_keywords,
              ai.capability_keywords AS ai_capability_keywords,
              ai.tool_keywords AS ai_tool_keywords,
              ai.jargon_terms AS ai_jargon_terms,
              ai.confidence AS ai_confidence,
              ai.needs_human_attention
            FROM jd_sources js
            JOIN jd_ai_annotations ai ON ai.jd_id = js.id
            WHERE js.raw_status = 'ai_annotated'
            ORDER BY js.id, ai.created_at DESC
            """
        ).fetchall()

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=REVIEW_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "jd_id": row["jd_id"],
                    "source_url": row["source_url"],
                    "company": row["company"],
                    "role_title": row["role_title"],
                    "responsibilities_text": row["responsibilities_text"],
                    "requirements_text": row["requirements_text"],
                    "ai_annotation_id": row["ai_annotation_id"],
                    "ai_mapped_direction": row["ai_mapped_direction"],
                    "reviewed_mapped_direction": row["ai_mapped_direction"],
                    "ai_secondary_directions": "|".join(from_json(row["ai_secondary_directions"])),
                    "reviewed_secondary_directions": "|".join(from_json(row["ai_secondary_directions"])),
                    "ai_task_keywords": "|".join(from_json(row["ai_task_keywords"])),
                    "reviewed_task_keywords": "|".join(from_json(row["ai_task_keywords"])),
                    "ai_capability_keywords": "|".join(from_json(row["ai_capability_keywords"])),
                    "reviewed_capability_keywords": "|".join(from_json(row["ai_capability_keywords"])),
                    "ai_tool_keywords": "|".join(from_json(row["ai_tool_keywords"])),
                    "reviewed_tool_keywords": "|".join(from_json(row["ai_tool_keywords"])),
                    "ai_jargon_terms": "|".join(from_json(row["ai_jargon_terms"])),
                    "reviewed_jargon_terms": "|".join(from_json(row["ai_jargon_terms"])),
                    "ai_confidence": row["ai_confidence"],
                    "needs_human_attention": bool(row["needs_human_attention"]),
                    "review_status": "needs_review",
                    "review_notes": "",
                    "reviewed_by": "",
                    "reviewed_at": "",
                }
            )
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export AI JD annotations for human review.")
    parser.add_argument("--db", required=True, type=Path)
    parser.add_argument("--csv", required=True, type=Path)
    args = parser.parse_args()

    count = export_jd_review(args.db, args.csv)
    print(f"Exported {count} rows to {args.csv}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Create review import script**

Create `scripts/import_reviewed_jds.py`:

```python
from __future__ import annotations

import argparse
import csv
import sys
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.db import connect, initialize_database, to_json
from backend.app.services.jd_review_service import validate_review_row


def import_reviewed_jds(db_path: Path, csv_path: Path) -> int:
    initialize_database(db_path)
    with csv_path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        rows = [
            validate_review_row(row, row_number=index)
            for index, row in enumerate(reader, start=2)
        ]

    imported = 0
    with connect(db_path) as conn:
        for row in rows:
            annotation_id = f"review-{uuid.uuid4().hex[:12]}"
            conn.execute(
                """
                INSERT INTO jd_annotations (
                  id, jd_id, ai_annotation_id, mapped_direction,
                  secondary_directions, task_keywords, capability_keywords,
                  tool_keywords, jargon_terms, notes, review_status,
                  review_notes, reviewed_by, reviewed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    annotation_id,
                    row["jd_id"],
                    row["ai_annotation_id"],
                    row["mapped_direction"],
                    to_json(row["secondary_directions"]),
                    to_json(row["task_keywords"]),
                    to_json(row["capability_keywords"]),
                    to_json(row["tool_keywords"]),
                    to_json(row["jargon_terms"]),
                    row["review_notes"],
                    row["review_status"],
                    row["review_notes"],
                    row["reviewed_by"],
                    row["reviewed_at"],
                ),
            )
            conn.execute(
                "UPDATE jd_sources SET raw_status = 'reviewed' WHERE id = ?",
                (row["jd_id"],),
            )
            imported += 1
    return imported


def main() -> None:
    parser = argparse.ArgumentParser(description="Import human-reviewed JD annotations.")
    parser.add_argument("--db", required=True, type=Path)
    parser.add_argument("--csv", required=True, type=Path)
    args = parser.parse_args()

    count = import_reviewed_jds(args.db, args.csv)
    print(f"Imported {count} reviewed JD annotations")


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Create `data/templates/jd_review_template.csv`**

```csv
jd_id,source_url,company,role_title,responsibilities_text,requirements_text,ai_annotation_id,ai_mapped_direction,reviewed_mapped_direction,ai_secondary_directions,reviewed_secondary_directions,ai_task_keywords,reviewed_task_keywords,ai_capability_keywords,reviewed_capability_keywords,ai_tool_keywords,reviewed_tool_keywords,ai_jargon_terms,reviewed_jargon_terms,ai_confidence,needs_human_attention,review_status,review_notes,reviewed_by,reviewed_at
jd-example,https://example.com/jobs/product-ops-intern,示例公司,产品运营实习生,负责用户反馈整理和活动数据复盘。,要求沟通清楚，会用表格整理信息。,ai-example,growth,growth,campaign,campaign,数据复盘|路径分析|效果对比,数据复盘|路径分析|效果对比,指标意识|假设验证|表格能力,指标意识|假设验证|表格能力,Excel,Excel,转化|复盘,转化|复盘,0.82,false,approved,示例行，正式审核时替换为真实判断,reviewer,2026-05-29
```

- [ ] **Step 7: Run tests**

```bash
PYTHONPATH=. .venv/bin/python -m pytest backend/tests/test_jd_pilot.py -q
```

Expected: all pilot tests pass.

- [ ] **Step 8: Commit**

```bash
git add data/templates/jd_review_template.csv backend/app/services/jd_review_service.py scripts/export_jd_review.py scripts/import_reviewed_jds.py backend/tests/test_jd_pilot.py
git commit -m "feat: add JD review CSV loop"
```

---

### Task 5: Formal Evidence Filtering And Pilot Metrics

**Files:**
- Modify: `backend/app/services/evidence_service.py`
- Create: `scripts/pilot_metrics.py`
- Test: `backend/tests/test_jd_pilot.py`

- [ ] **Step 1: Add failing evidence and metrics tests**

Append to `backend/tests/test_jd_pilot.py`:

```python
from backend.app.services.evidence_service import build_evidence_summary
from scripts.pilot_metrics import build_pilot_metrics


def insert_reviewed_annotation(
    db_path: Path,
    jd_id: str,
    *,
    source_type: str,
    source_quality: str,
    review_status: str,
    direction: str = "growth",
) -> None:
    insert_source(db_path, jd_id, source_type=source_type, source_quality=source_quality)
    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO jd_annotations (
              id, jd_id, mapped_direction, secondary_directions,
              task_keywords, capability_keywords, tool_keywords,
              jargon_terms, notes, review_status, review_notes,
              reviewed_by, reviewed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"ann-{jd_id}",
                jd_id,
                direction,
                json.dumps(["campaign"], ensure_ascii=False),
                json.dumps(["数据复盘", "路径分析", "效果对比"], ensure_ascii=False),
                json.dumps(["指标意识", "假设验证", "表格能力"], ensure_ascii=False),
                json.dumps(["Excel"], ensure_ascii=False),
                json.dumps(["转化"], ensure_ascii=False),
                "reviewed",
                review_status,
                "checked",
                "tester",
                "2026-05-29",
            ),
        )


def test_evidence_summary_uses_only_formal_reviewed_jds(tmp_path: Path) -> None:
    db_path = initialize_test_db(tmp_path)
    insert_reviewed_annotation(
        db_path,
        "formal",
        source_type="official",
        source_quality="high",
        review_status="approved",
    )
    insert_reviewed_annotation(
        db_path,
        "manual",
        source_type="manual_note",
        source_quality="high",
        review_status="approved",
    )
    insert_reviewed_annotation(
        db_path,
        "low-quality",
        source_type="official",
        source_quality="low",
        review_status="approved",
    )
    insert_reviewed_annotation(
        db_path,
        "rejected",
        source_type="official",
        source_quality="high",
        review_status="rejected",
    )

    summary = build_evidence_summary(JDRepository(db_path), "growth")

    assert summary["jd_count"] == 1
    assert summary["source_type_summary"] == {"official": 1}
    assert "数据复盘" in summary["high_frequency_tasks"]


def test_build_pilot_metrics_reports_collection_and_approval_counts(tmp_path: Path) -> None:
    db_path = initialize_test_db(tmp_path)
    insert_reviewed_annotation(
        db_path,
        "formal",
        source_type="official",
        source_quality="high",
        review_status="approved",
        direction="growth",
    )
    insert_reviewed_annotation(
        db_path,
        "needs-review",
        source_type="recruiting_platform",
        source_quality="medium",
        review_status="needs_review",
        direction="content",
    )

    metrics = build_pilot_metrics(db_path)

    assert metrics["collected_count"] == 2
    assert metrics["approved_formal_count"] == 1
    assert metrics["covered_approved_directions"] == ["growth"]
    assert metrics["status_counts"] == {"approved": 1, "needs_review": 1}
```

- [ ] **Step 2: Run failing tests**

```bash
PYTHONPATH=. .venv/bin/python -m pytest backend/tests/test_jd_pilot.py::test_evidence_summary_uses_only_formal_reviewed_jds backend/tests/test_jd_pilot.py::test_build_pilot_metrics_reports_collection_and_approval_counts -q
```

Expected: metrics script does not exist, or evidence still counts non-formal records.

- [ ] **Step 3: Update `backend/app/services/evidence_service.py`**

Keep the service small. It should rely on repository formal filtering:

```python
from collections import Counter
from typing import Any

from backend.app.repositories.jd_repository import JDRepository


def most_common(values: list[str], limit: int = 6) -> list[str]:
    return [value for value, _ in Counter(values).most_common(limit)]


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
    source_counts = Counter(annotation["source_type"] for annotation in annotations)

    return {
        "jd_count": len(annotations),
        "high_frequency_tasks": most_common(task_values),
        "high_frequency_capabilities": most_common(capability_values),
        "representative_roles": most_common(
            [annotation["role_title"] for annotation in annotations],
            limit=5,
        ),
        "source_type_summary": dict(source_counts),
        "evidence_status": "limited" if len(annotations) < 30 else "target_met",
    }
```

- [ ] **Step 4: Create `scripts/pilot_metrics.py`**

```python
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.db import connect


def build_pilot_metrics(db_path: Path) -> dict[str, Any]:
    with connect(db_path) as conn:
        sources = conn.execute(
            "SELECT id, source_type, source_quality, raw_status FROM jd_sources"
        ).fetchall()
        annotations = conn.execute(
            """
            SELECT
              ja.mapped_direction,
              ja.review_status,
              js.source_type,
              js.source_quality
            FROM jd_annotations ja
            JOIN jd_sources js ON js.id = ja.jd_id
            """
        ).fetchall()

    status_counts = Counter(row["review_status"] for row in annotations)
    source_counts = Counter(row["source_type"] for row in sources)
    quality_counts = Counter(row["source_quality"] for row in sources)
    approved_formal = [
        row
        for row in annotations
        if row["review_status"] == "approved"
        and row["source_quality"] in {"high", "medium"}
        and row["source_type"] != "manual_note"
    ]
    approved_direction_counts = Counter(row["mapped_direction"] for row in approved_formal)

    return {
        "collected_count": len(sources),
        "reviewed_annotation_count": len(annotations),
        "approved_formal_count": len(approved_formal),
        "covered_approved_directions": sorted(approved_direction_counts),
        "approved_direction_counts": dict(sorted(approved_direction_counts.items())),
        "status_counts": dict(sorted(status_counts.items())),
        "source_type_counts": dict(sorted(source_counts.items())),
        "source_quality_counts": dict(sorted(quality_counts.items())),
        "pilot_collection_target_met": 30 <= len(sources) <= 50,
        "pilot_minimum_approved_met": len(approved_formal) >= 20,
        "pilot_minimum_direction_coverage_met": len(approved_direction_counts) >= 6,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Print JD pilot readiness metrics.")
    parser.add_argument("--db", required=True, type=Path)
    args = parser.parse_args()

    print(json.dumps(build_pilot_metrics(args.db), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run tests**

```bash
PYTHONPATH=. .venv/bin/python -m pytest backend/tests/test_jd_pilot.py backend/tests/test_api.py -q
```

Expected: tests pass. If frontend/API schema tests do not know `evidence_status`, assert the existing keys still exist and add an assertion for `evidence_status`.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/evidence_service.py scripts/pilot_metrics.py backend/tests/test_jd_pilot.py backend/tests/test_api.py
git commit -m "feat: filter reviewed JD evidence"
```

---

### Task 6: Documentation And End-To-End Pilot Smoke Test

**Files:**
- Modify: `docs/jd-data-standard.md`
- Create: `docs/jd-pilot-loop.md`
- Modify: `README.md`

- [ ] **Step 1: Update `docs/jd-data-standard.md`**

Add a section named `Pilot Source And Review Rules`:

```markdown
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
```

- [ ] **Step 2: Create `docs/jd-pilot-loop.md`**

```markdown
# JD Pilot Loop

This guide runs the 30-50 real public JD pilot before scaling to 300-500 records.

## 1. Collect Public JDs

Use `data/templates/jd_collection_template.csv`.

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
```

- [ ] **Step 3: Update `README.md`**

Add a `Real JD Pilot Loop` section:

```markdown
## Real JD Pilot Loop

The app now separates manually seeded examples from formal market evidence.

Run the pilot pipeline:

```bash
PYTHONPATH=. .venv/bin/python scripts/import_collected_jds.py --db data/app.db --csv data/pilot/collected_jds.csv
PYTHONPATH=. .venv/bin/python scripts/run_jd_ai_annotation.py --db data/app.db --provider fixture --fixture-json data/pilot/ai_annotation_fixture.json
PYTHONPATH=. .venv/bin/python scripts/export_jd_review.py --db data/app.db --csv data/pilot/review.csv
PYTHONPATH=. .venv/bin/python scripts/import_reviewed_jds.py --db data/app.db --csv data/pilot/review.csv
PYTHONPATH=. .venv/bin/python scripts/pilot_metrics.py --db data/app.db
```

Frontend preview:

```bash
npm run frontend
```

Open `http://127.0.0.1:5174/`.
```

- [ ] **Step 4: Run full verification**

```bash
npm test
PYTHONPATH=. .venv/bin/python -m pytest backend/tests/test_api.py backend/tests/test_jd_pilot.py -q
.venv/bin/python scripts/import_jds.py --db data/app.db --seed-dir data/seeds
.venv/bin/python scripts/pilot_metrics.py --db data/app.db
```

Expected:

- `npm test` passes.
- Backend pytest passes.
- Seed import completes.
- Pilot metrics prints JSON. With only manual seed data, `approved_formal_count` may be `0`; that is correct because `manual_note` is not formal market evidence.

- [ ] **Step 5: Commit**

```bash
git add docs/jd-data-standard.md docs/jd-pilot-loop.md README.md
git commit -m "docs: document JD pilot loop"
```

---

## Execution Notes

- Do not open user-facing AI chat in this plan. The AI annotation script is internal data work only.
- Do not upload resumes or add resume rewrite features in this plan.
- If real model access is not configured, use fixture mode and fail clearly for real-provider mode.
- Do not count `manual_note` records as formal evidence.
- Keep localhost frontend at `http://127.0.0.1:5174/` when running the current frontend package script.
- After the pilot loop is implemented, the next product decision is whether to collect 300-500 JDs or first rewrite questions/results based on the pilot evidence.

## Final Verification Checklist

- [ ] `PYTHONPATH=. .venv/bin/python -m pytest backend/tests/test_api.py backend/tests/test_jd_pilot.py -q`
- [ ] `npm test`
- [ ] `.venv/bin/python scripts/import_jds.py --db data/app.db --seed-dir data/seeds`
- [ ] `.venv/bin/python scripts/pilot_metrics.py --db data/app.db`
- [ ] Confirm `manual_note` seed records do not count as formal evidence.
- [ ] Confirm review CSV can be exported and imported with approved records.
- [ ] Confirm result evidence summaries expose formal approved JD counts only.
