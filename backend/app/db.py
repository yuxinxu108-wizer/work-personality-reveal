import json
import sqlite3
from pathlib import Path
from typing import Any


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS jd_sources (
  id TEXT PRIMARY KEY,
  company TEXT NOT NULL,
  role_title TEXT NOT NULL,
  role_category TEXT NOT NULL,
  source_url TEXT NOT NULL,
  source_type TEXT NOT NULL CHECK (
    source_type IN ('official', 'recruiting_platform', 'manual_note', 'school_public')
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
  review_level TEXT NOT NULL DEFAULT 'manual_reviewed' CHECK (
    review_level IN ('rule_generated', 'manual_reviewed', 'spot_checked')
  ),
  review_notes TEXT NOT NULL DEFAULT '',
  reviewed_by TEXT NOT NULL DEFAULT '',
  reviewed_at TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS jd_ai_annotations (
  id TEXT PRIMARY KEY,
  jd_id TEXT NOT NULL REFERENCES jd_sources(id),
  mapped_direction TEXT NOT NULL,
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
  confidence_level TEXT NOT NULL DEFAULT '',
  confidence_json TEXT NOT NULL DEFAULT '{}',
  valid_answer_count INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

MIGRATED_TABLES_SQL = {
    "jd_sources": """
    CREATE TABLE jd_sources (
      id TEXT PRIMARY KEY,
      company TEXT NOT NULL,
      role_title TEXT NOT NULL,
      role_category TEXT NOT NULL,
      source_url TEXT NOT NULL,
      source_type TEXT NOT NULL CHECK (
        source_type IN (
          'official', 'recruiting_platform', 'manual_note', 'school_public'
        )
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
    """,
    "jd_annotations": """
    CREATE TABLE jd_annotations (
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
      review_level TEXT NOT NULL DEFAULT 'manual_reviewed' CHECK (
        review_level IN ('rule_generated', 'manual_reviewed', 'spot_checked')
      ),
      review_notes TEXT NOT NULL DEFAULT '',
      reviewed_by TEXT NOT NULL DEFAULT '',
      reviewed_at TEXT NOT NULL DEFAULT ''
    );
    """,
    "assessment_runs": """
    CREATE TABLE assessment_runs (
      id TEXT PRIMARY KEY,
      answers_json TEXT NOT NULL,
      scores_json TEXT NOT NULL,
      main_direction TEXT NOT NULL REFERENCES directions(key),
      supporting_directions TEXT NOT NULL,
      confidence_level TEXT NOT NULL DEFAULT '',
      confidence_json TEXT NOT NULL DEFAULT '{}',
      valid_answer_count INTEGER NOT NULL DEFAULT 0,
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """,
}


def connect(db_path: Path | str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database(db_path: Path | str) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as conn:
        conn.executescript(SCHEMA_SQL)
        _migrate_pilot_columns(conn)
        _migrate_review_levels(conn)
        _migrate_jd_sources_source_type_check(conn)
        _migrate_jd_annotations_review_status_check(conn)
        _migrate_direction_foreign_keys(conn)


def to_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def from_json(value: str) -> Any:
    return json.loads(value)


def _migrate_direction_foreign_keys(conn: sqlite3.Connection) -> None:
    if not _table_has_fk(conn, "jd_annotations", "directions", "mapped_direction"):
        _rebuild_table_with_current_schema(conn, "jd_annotations")
    if not _table_has_fk(conn, "assessment_runs", "directions", "main_direction"):
        _rebuild_table_with_current_schema(conn, "assessment_runs")


def _migrate_pilot_columns(conn: sqlite3.Connection) -> None:
    _add_column_if_missing(
        conn,
        "jd_sources",
        "source_quality",
        """
        source_quality TEXT NOT NULL DEFAULT 'medium'
        CHECK (source_quality IN ('high', 'medium', 'low'))
        """,
    )
    _add_column_if_missing(
        conn,
        "jd_sources",
        "collector_notes",
        "collector_notes TEXT NOT NULL DEFAULT ''",
    )
    _add_column_if_missing(
        conn,
        "jd_sources",
        "raw_status",
        """
        raw_status TEXT NOT NULL DEFAULT 'collected'
        CHECK (raw_status IN ('collected', 'ai_annotated', 'reviewed'))
        """,
    )
    _add_column_if_missing(
        conn,
        "jd_annotations",
        "ai_annotation_id",
        "ai_annotation_id TEXT REFERENCES jd_ai_annotations(id)",
    )
    _add_column_if_missing(
        conn,
        "jd_annotations",
        "review_status",
        """
        review_status TEXT NOT NULL DEFAULT 'approved'
        CHECK (review_status IN ('approved', 'needs_review', 'rejected'))
        """,
    )
    _add_column_if_missing(
        conn,
        "jd_annotations",
        "review_notes",
        "review_notes TEXT NOT NULL DEFAULT ''",
    )
    _add_column_if_missing(
        conn,
        "jd_annotations",
        "review_level",
        """
        review_level TEXT NOT NULL DEFAULT 'manual_reviewed'
        CHECK (review_level IN ('rule_generated', 'manual_reviewed', 'spot_checked'))
        """,
    )
    _add_column_if_missing(
        conn,
        "jd_annotations",
        "reviewed_by",
        "reviewed_by TEXT NOT NULL DEFAULT ''",
    )
    _add_column_if_missing(
        conn,
        "jd_annotations",
        "reviewed_at",
        "reviewed_at TEXT NOT NULL DEFAULT ''",
    )
    _add_column_if_missing(
        conn,
        "assessment_runs",
        "confidence_level",
        "confidence_level TEXT NOT NULL DEFAULT ''",
    )
    _add_column_if_missing(
        conn,
        "assessment_runs",
        "confidence_json",
        "confidence_json TEXT NOT NULL DEFAULT '{}'",
    )
    _add_column_if_missing(
        conn,
        "assessment_runs",
        "valid_answer_count",
        "valid_answer_count INTEGER NOT NULL DEFAULT 0",
    )


def _migrate_review_levels(conn: sqlite3.Connection) -> None:
    if not _table_exists(conn, "jd_annotations"):
        return
    columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(jd_annotations)")
    }
    required_columns = {"review_level", "reviewed_by", "review_notes"}
    if not required_columns.issubset(columns):
        return
    conn.execute(
        """
        UPDATE jd_annotations
        SET review_level = 'rule_generated'
        WHERE review_level = 'manual_reviewed'
          AND (
            reviewed_by = 'codex_rule_review'
            OR review_notes LIKE '%规则生成%'
          )
        """
    )


def _add_column_if_missing(
    conn: sqlite3.Connection, table: str, column: str, definition: str
) -> None:
    columns = {
        row["name"]
        for row in conn.execute(f"PRAGMA table_info({table})")
    }
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {definition}")


def _migrate_jd_sources_source_type_check(conn: sqlite3.Connection) -> None:
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'jd_sources'"
    ).fetchone()
    if row is None or "school_public" in row["sql"]:
        return

    _rebuild_table_with_current_schema(conn, "jd_sources")


def _migrate_jd_annotations_review_status_check(conn: sqlite3.Connection) -> None:
    if not _table_exists(conn, "jd_annotations"):
        return
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'jd_annotations'"
    ).fetchone()
    if row is None or "needs_review" in row["sql"]:
        return

    _rebuild_table_with_current_schema(conn, "jd_annotations")


def _table_has_fk(
    conn: sqlite3.Connection, table: str, referenced_table: str, from_column: str
) -> bool:
    if not _table_exists(conn, table):
        return True
    return any(
        row["table"] == referenced_table and row["from"] == from_column
        for row in conn.execute(f"PRAGMA foreign_key_list({table})")
    )


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table,),
    ).fetchone()
    return row is not None


def _rebuild_table_with_current_schema(conn: sqlite3.Connection, table: str) -> None:
    old_columns = [
        row["name"]
        for row in conn.execute(f"PRAGMA table_info({table})")
    ]
    foreign_keys_enabled = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    conn.commit()
    try:
        conn.execute("PRAGMA foreign_keys = OFF")
        conn.execute("PRAGMA legacy_alter_table = ON")
        conn.execute(f"ALTER TABLE {table} RENAME TO {table}_old")
        conn.execute(MIGRATED_TABLES_SQL[table])
        new_columns = {
            row["name"]
            for row in conn.execute(f"PRAGMA table_info({table})")
        }
        copy_columns = [column for column in old_columns if column in new_columns]
        column_names = ", ".join(copy_columns)
        select_columns = ", ".join(
            _select_expression_for_migrated_column(table, column)
            for column in copy_columns
        )
        conn.execute(
            f"INSERT INTO {table} ({column_names}) "
            f"SELECT {select_columns} FROM {table}_old"
        )
        conn.execute(f"DROP TABLE {table}_old")
        conn.commit()
    finally:
        conn.execute("PRAGMA legacy_alter_table = OFF")
        if foreign_keys_enabled:
            conn.execute("PRAGMA foreign_keys = ON")


def _select_expression_for_migrated_column(table: str, column: str) -> str:
    if table == "jd_annotations" and column == "review_status":
        return (
            "CASE review_status "
            "WHEN 'pending' THEN 'needs_review' "
            "ELSE review_status END"
        )
    return column
