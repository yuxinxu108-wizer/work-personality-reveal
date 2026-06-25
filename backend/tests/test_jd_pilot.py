import csv
import json
import sqlite3
from pathlib import Path

import pytest

from backend.app.db import connect, initialize_database, to_json
from backend.app.repositories.jd_repository import JDRepository
from backend.app.services.jd_collection_service import (
    build_jd_id,
    normalize_collection_row,
)
from backend.app.services.jd_ai_annotation_service import (
    validate_ai_annotation_payload,
)
from backend.app.services.jd_review_service import REVIEW_COLUMNS, validate_review_row
from backend.app.services.evidence_service import build_evidence_summary
from scripts.run_jd_ai_annotation import (
    create_openai_payload,
    run_ai_annotation_from_fixture,
)
from scripts.import_collected_jds import import_collected_jds
from scripts.export_jd_review import export_jd_review
from scripts.import_reviewed_jds import import_reviewed_jds
from scripts.pilot_metrics import build_pilot_metrics


def initialize_test_db(db_path: Path) -> None:
    initialize_database(db_path)
    with connect(db_path) as conn:
        for direction_key, label in [
            ("growth", "Growth"),
            ("content", "Content"),
        ]:
            conn.execute(
                """
                INSERT OR IGNORE INTO directions (
                  key, label, short_label, animal, avatar_src, plain_summary,
                  competency_definition, typical_tasks, common_capabilities,
                  suitable_roles, risk_notes, portfolio_guidance
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    direction_key,
                    label,
                    label,
                    "none",
                    f"/avatars/{direction_key}.svg",
                    f"{label} work",
                    f"{label} competency",
                    to_json(["用户路径分析"]),
                    to_json(["数据整理"]),
                    to_json(["运营"]),
                    to_json(["需要复盘"]),
                    "Build a portfolio.",
                ),
            )


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def valid_collection_row() -> dict[str, str]:
    return {
        "source_url": "https://example.com/careers/growth-operator",
        "source_type": "official",
        "collected_at": "2026-05-29",
        "company": "Example Co",
        "role_title": "Growth Operator",
        "role_category": "operations",
        "location": "Shanghai",
        "employment_type": "full_time",
        "raw_text": "负责活动数据整理、用户路径分析和复盘",
        "responsibilities_text": "负责活动数据整理、用户路径分析和复盘",
        "requirements_text": "具备基础数据分析能力",
        "source_quality": "high",
        "collector_notes": "official careers page",
    }


def valid_ai_payload() -> dict[str, object]:
    return {
        "mapped_direction": "growth",
        "secondary_directions": ["campaign"],
        "confidence": 0.82,
        "task_keywords": ["活动数据整理", "用户路径分析", "增长实验"],
        "capability_keywords": ["数据分析", "复盘归因", "跨团队沟通"],
        "tool_keywords": ["Excel", "SQL"],
        "jargon_terms": ["转化率", "留存"],
        "evidence_quotes": [
            {"text": "负责活动数据整理", "supports": "task_keywords"},
            {"text": "用户路径分析", "supports": "capability_keywords"},
            {"text": "使用 Excel 和 SQL 跟踪转化率", "supports": "tool_keywords"},
            {"text": "复盘留存表现", "supports": "jargon_terms"},
        ],
        "reasoning_summary": "JD 重点围绕活动数据、用户路径和增长复盘，匹配 growth，campaign 作为辅助方向。",
        "needs_human_attention": False,
        "attention_reasons": [],
    }


def valid_ai_raw_text() -> str:
    return (
        "负责活动数据整理、用户路径分析和增长实验设计，使用 Excel 和 SQL 跟踪转化率，"
        "并且定期复盘留存表现，协同运营和产品团队优化活动节奏，沉淀活动看板，"
        "输出阶段性结论，支持后续渠道投放和用户触达策略。"
    )


def insert_source(
    conn: sqlite3.Connection,
    source_id: str,
    *,
    source_type: str = "official",
    source_quality: str = "medium",
) -> None:
    conn.execute(
        """
        INSERT INTO jd_sources (
          id, company, role_title, role_category, source_url, source_type,
          source_quality, collector_notes, raw_status, location, employment_type,
          raw_text, responsibilities_text, requirements_text, collected_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            source_id,
            "Example Co",
            f"Growth Operator {source_id}",
            "operations",
            f"https://example.com/jobs/{source_id}",
            source_type,
            source_quality,
            "",
            "reviewed",
            "Shanghai",
            "full_time",
            "负责活动数据整理、用户路径分析和复盘",
            "负责活动数据整理、用户路径分析和复盘",
            "具备基础数据分析能力",
            "2026-05-29",
        ),
    )


def prepare_ai_review_record(tmp_path: Path) -> tuple[Path, Path]:
    db_path = tmp_path / "app.db"
    fixture_path = tmp_path / "ai_annotations.json"
    initialize_test_db(db_path)
    with connect(db_path) as conn:
        insert_source(conn, "jd-review-1")
        conn.execute(
            """
            UPDATE jd_sources
            SET raw_status = 'collected', raw_text = ?, responsibilities_text = ?
            WHERE id = ?
            """,
            (valid_ai_raw_text(), valid_ai_raw_text(), "jd-review-1"),
        )
    fixture_path.write_text(
        json.dumps({"jd-review-1": valid_ai_payload()}, ensure_ascii=False),
        encoding="utf-8",
    )
    run_ai_annotation_from_fixture(db_path, fixture_path)
    return db_path, fixture_path


def _insert_annotation(
    conn: sqlite3.Connection,
    annotation_id: str,
    jd_id: str,
    *,
    review_status: str = "approved",
) -> None:
    conn.execute(
        """
        INSERT INTO jd_annotations (
          id, jd_id, mapped_direction, secondary_directions,
          task_keywords, capability_keywords, tool_keywords,
          jargon_terms, notes, review_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            annotation_id,
            jd_id,
            "growth",
            to_json([]),
            to_json(["用户路径分析"]),
            to_json(["数据整理"]),
            to_json(["Excel"]),
            to_json(["复盘"]),
            "pilot fixture",
            review_status,
        ),
    )


def insert_reviewed_annotation(
    conn: sqlite3.Connection,
    source_id: str,
    *,
    source_type: str = "official",
    source_quality: str = "medium",
    review_status: str = "approved",
    mapped_direction: str = "growth",
) -> None:
    insert_source(
        conn,
        source_id,
        source_type=source_type,
        source_quality=source_quality,
    )
    conn.execute(
        """
        INSERT INTO jd_annotations (
          id, jd_id, mapped_direction, secondary_directions,
          task_keywords, capability_keywords, tool_keywords,
          jargon_terms, notes, review_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"{source_id}_annotation",
            source_id,
            mapped_direction,
            to_json([]),
            to_json(["用户路径分析"]),
            to_json(["数据整理"]),
            to_json(["Excel"]),
            to_json(["复盘"]),
            "pilot fixture",
            review_status,
        ),
    )


def test_initialize_database_adds_pilot_columns_and_ai_table(tmp_path: Path):
    db_path = tmp_path / "app.db"
    initialize_database(db_path)

    with sqlite3.connect(db_path) as conn:
        source_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(jd_sources)")
        }
        annotation_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(jd_annotations)")
        }
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }

    assert {"source_quality", "collector_notes", "raw_status"}.issubset(
        source_columns
    )
    assert {
        "review_status",
        "review_notes",
        "reviewed_by",
        "reviewed_at",
    }.issubset(annotation_columns)
    assert "jd_ai_annotations" in tables


def test_source_type_accepts_school_public(tmp_path: Path):
    db_path = tmp_path / "app.db"
    initialize_test_db(db_path)

    with connect(db_path) as conn:
        insert_source(conn, "school_public_jd", source_type="school_public")
        source_type = conn.execute(
            "SELECT source_type FROM jd_sources WHERE id = ?",
            ("school_public_jd",),
        ).fetchone()["source_type"]

    assert source_type == "school_public"


def test_normalize_collection_row_requires_public_source_url():
    row = valid_collection_row()
    row["source_url"] = "internal-note"

    try:
        normalize_collection_row(row, row_number=2)
    except ValueError as exc:
        assert "row 2" in str(exc)
        assert "source_url" in str(exc)
    else:
        raise AssertionError("Expected invalid source_url to raise ValueError")


def test_normalize_collection_row_accepts_complete_row():
    row = valid_collection_row()
    row["company"] = "  Example Co  "

    normalized = normalize_collection_row(row, row_number=2)

    assert normalized["id"] == build_jd_id(row["source_url"])
    assert normalized["company"] == "Example Co"
    assert normalized["raw_status"] == "collected"
    assert normalized["source_type"] == "official"
    assert normalized["source_quality"] == "high"


def test_import_collected_jds_inserts_sources(tmp_path: Path):
    db_path = tmp_path / "app.db"
    csv_path = tmp_path / "collected_jds.csv"
    row = valid_collection_row()
    write_csv(csv_path, [row])

    imported_count = import_collected_jds(db_path, csv_path)

    assert imported_count == 1
    with connect(db_path) as conn:
        source = conn.execute(
            "SELECT * FROM jd_sources WHERE id = ?",
            (build_jd_id(row["source_url"]),),
        ).fetchone()

    assert source["source_url"] == row["source_url"]
    assert source["company"] == row["company"]
    assert source["raw_status"] == "collected"


def test_import_collected_jds_does_not_overwrite_reviewed_sources(tmp_path: Path):
    db_path = tmp_path / "app.db"
    csv_path = tmp_path / "collected_jds.csv"
    row = valid_collection_row()
    source_id = build_jd_id(row["source_url"])
    initialize_database(db_path)
    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO jd_sources (
              id, company, role_title, role_category, source_url, source_type,
              source_quality, collector_notes, raw_status, location, employment_type,
              raw_text, responsibilities_text, requirements_text, collected_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_id,
                "Reviewed Co",
                "Reviewed Role",
                "operations",
                row["source_url"],
                "official",
                "high",
                "reviewed already",
                "reviewed",
                "Shanghai",
                "internship",
                "reviewed raw text",
                "reviewed responsibilities",
                "reviewed requirements",
                "2026-05-01",
            ),
        )

    updated_row = {**row, "company": "Changed Co", "raw_text": "changed raw text"}
    write_csv(csv_path, [updated_row])

    imported_count = import_collected_jds(db_path, csv_path)

    with connect(db_path) as conn:
        source = conn.execute(
            """
            SELECT company, raw_text, raw_status, collected_at
            FROM jd_sources
            WHERE id = ?
            """,
            (source_id,),
        ).fetchone()

    assert imported_count == 1
    assert source["company"] == "Reviewed Co"
    assert source["raw_text"] == "reviewed raw text"
    assert source["raw_status"] == "reviewed"
    assert source["collected_at"] == "2026-05-01"


def test_repository_lists_only_formal_approved_annotations(tmp_path: Path):
    db_path = tmp_path / "app.db"
    initialize_test_db(db_path)

    with connect(db_path) as conn:
        cases = [
            ("approved_high", "official", "high", "approved"),
            ("approved_medium", "recruiting_platform", "medium", "approved"),
            ("low_quality", "official", "low", "approved"),
            ("manual_note", "manual_note", "high", "approved"),
            ("needs_review", "official", "high", "needs_review"),
        ]
        for source_id, source_type, source_quality, review_status in cases:
            insert_source(
                conn,
                source_id,
                source_type=source_type,
                source_quality=source_quality,
            )
            _insert_annotation(
                conn,
                f"{source_id}_annotation",
                source_id,
                review_status=review_status,
            )

    repository = JDRepository(db_path)

    formal_annotations = repository.list_jd_annotations_for_direction("growth")
    all_annotations = repository.list_jd_annotations_for_direction(
        "growth",
        formal_only=False,
    )

    assert [item["role_title"] for item in formal_annotations] == [
        "Growth Operator approved_high",
        "Growth Operator approved_medium",
    ]
    assert {item["source_quality"] for item in formal_annotations} == {
        "high",
        "medium",
    }
    assert {item["review_status"] for item in formal_annotations} == {"approved"}
    assert len(all_annotations) == 5


def test_evidence_summary_uses_only_formal_reviewed_jds(tmp_path: Path):
    db_path = tmp_path / "app.db"
    initialize_test_db(db_path)

    with connect(db_path) as conn:
        cases = [
            ("approved_high", "official", "high", "approved"),
            ("low_quality", "official", "low", "approved"),
            ("manual_note", "manual_note", "high", "approved"),
            ("rejected", "official", "high", "rejected"),
        ]
        for source_id, source_type, source_quality, review_status in cases:
            insert_reviewed_annotation(
                conn,
                source_id,
                source_type=source_type,
                source_quality=source_quality,
                review_status=review_status,
            )

    summary = build_evidence_summary(JDRepository(db_path), "growth")

    assert summary["jd_count"] == 1
    assert summary["evidence_status"] == "limited"
    assert summary["representative_roles"] == ["Growth Operator approved_high"]
    assert summary["source_type_summary"] == {"official": 1}


def test_evidence_summary_counts_latest_reviewed_jd_once(tmp_path: Path):
    db_path = tmp_path / "app.db"
    initialize_test_db(db_path)

    with connect(db_path) as conn:
        insert_source(conn, "duplicate-evidence", source_type="official", source_quality="high")
        for annotation_id, reviewed_at in [
            ("old-evidence", "2026-05-29"),
            ("new-evidence", "2026-05-30"),
        ]:
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
                    "duplicate-evidence",
                    "growth",
                    to_json([]),
                    to_json(["用户路径分析"]),
                    to_json(["数据整理"]),
                    to_json(["Excel"]),
                    to_json(["复盘"]),
                    "pilot fixture",
                    "approved",
                    "checked",
                    "tester",
                    reviewed_at,
                ),
            )

    summary = build_evidence_summary(JDRepository(db_path), "growth")

    assert summary["jd_count"] == 1
    assert summary["representative_roles"] == ["Growth Operator duplicate-evidence"]


def test_evidence_summary_ignores_old_approved_when_latest_review_rejected(
    tmp_path: Path,
):
    db_path = tmp_path / "app.db"
    initialize_test_db(db_path)

    with connect(db_path) as conn:
        insert_source(conn, "changed-review", source_type="official", source_quality="high")
        for annotation_id, review_status, reviewed_at in [
            ("old-approved", "approved", "2026-05-29"),
            ("new-rejected", "rejected", "2026-05-30"),
        ]:
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
                    "changed-review",
                    "growth",
                    to_json([]),
                    to_json(["用户路径分析"]),
                    to_json(["数据整理"]),
                    to_json(["Excel"]),
                    to_json(["复盘"]),
                    "pilot fixture",
                    review_status,
                    "checked",
                    "tester",
                    reviewed_at,
                ),
            )

    summary = build_evidence_summary(JDRepository(db_path), "growth")

    assert summary["jd_count"] == 0


def test_evidence_summary_uses_insert_order_for_same_day_reviews(tmp_path: Path):
    db_path = tmp_path / "app.db"
    initialize_test_db(db_path)

    with connect(db_path) as conn:
        insert_source(conn, "same-day-review", source_type="official", source_quality="high")
        for annotation_id, review_status in [
            ("z-old-approved", "approved"),
            ("a-new-rejected", "rejected"),
        ]:
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
                    "same-day-review",
                    "growth",
                    to_json([]),
                    to_json(["用户路径分析"]),
                    to_json(["数据整理"]),
                    to_json(["Excel"]),
                    to_json(["复盘"]),
                    "pilot fixture",
                    review_status,
                    "checked",
                    "tester",
                    "2026-05-30",
                ),
            )

    summary = build_evidence_summary(JDRepository(db_path), "growth")

    assert summary["jd_count"] == 0


def test_build_pilot_metrics_reports_collection_and_approval_counts(tmp_path: Path):
    db_path = tmp_path / "app.db"
    initialize_test_db(db_path)

    with connect(db_path) as conn:
        insert_reviewed_annotation(
            conn,
            "approved_growth",
            source_type="official",
            source_quality="high",
            review_status="approved",
            mapped_direction="growth",
        )
        insert_reviewed_annotation(
            conn,
            "needs_review_content",
            source_type="recruiting_platform",
            source_quality="medium",
            review_status="needs_review",
            mapped_direction="content",
        )

    metrics = build_pilot_metrics(db_path)

    assert metrics["collected_count"] == 2
    assert metrics["reviewed_annotation_count"] == 2
    assert metrics["approved_formal_count"] == 1
    assert metrics["covered_approved_directions"] == ["growth"]
    assert metrics["approved_direction_counts"] == {"growth": 1}
    assert metrics["status_counts"] == {"approved": 1, "needs_review": 1}
    assert metrics["pilot_collection_target_met"] is False
    assert metrics["pilot_minimum_approved_met"] is False
    assert metrics["pilot_minimum_direction_coverage_met"] is False


def test_build_pilot_metrics_uses_pilot_thresholds(tmp_path: Path):
    db_path = tmp_path / "app.db"
    initialize_test_db(db_path)
    directions = ["growth", "content", "campaign", "community", "research", "strategy"]

    with connect(db_path) as conn:
        for direction in directions:
            if direction == "growth":
                continue
            conn.execute(
                """
                INSERT OR IGNORE INTO directions (
                  key, label, short_label, animal, avatar_src, plain_summary,
                  competency_definition, typical_tasks, common_capabilities,
                  suitable_roles, risk_notes, portfolio_guidance
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    direction,
                    direction,
                    direction,
                    "none",
                    f"/avatars/{direction}.svg",
                    f"{direction} work",
                    f"{direction} competency",
                    to_json(["task"]),
                    to_json(["capability"]),
                    to_json(["intern"]),
                    to_json(["risk"]),
                    "Build a portfolio.",
                ),
            )
        for index in range(30):
            insert_reviewed_annotation(
                conn,
                f"approved_{index:02d}",
                source_type="official",
                source_quality="high",
                review_status="approved",
                mapped_direction=directions[index % len(directions)],
            )

    metrics = build_pilot_metrics(db_path)

    assert metrics["collected_count"] == 30
    assert metrics["approved_formal_count"] == 30
    assert len(metrics["covered_approved_directions"]) == 6
    assert metrics["pilot_collection_target_met"] is True
    assert metrics["pilot_minimum_approved_met"] is True
    assert metrics["pilot_minimum_direction_coverage_met"] is True


def test_build_pilot_metrics_rejects_oversized_pilot_collection(tmp_path: Path):
    db_path = tmp_path / "app.db"
    initialize_test_db(db_path)

    with connect(db_path) as conn:
        for index in range(51):
            insert_source(conn, f"source_{index:02d}")

    metrics = build_pilot_metrics(db_path)

    assert metrics["collected_count"] == 51
    assert metrics["pilot_collection_target_met"] is False


def test_build_pilot_metrics_accepts_upper_collection_boundary(tmp_path: Path):
    db_path = tmp_path / "app.db"
    initialize_test_db(db_path)

    with connect(db_path) as conn:
        for index in range(50):
            insert_source(conn, f"source_{index:02d}")

    metrics = build_pilot_metrics(db_path)

    assert metrics["collected_count"] == 50
    assert metrics["pilot_collection_target_met"] is True


def test_build_pilot_metrics_collected_count_excludes_manual_notes(tmp_path: Path):
    db_path = tmp_path / "app.db"
    initialize_test_db(db_path)

    with connect(db_path) as conn:
        for index in range(24):
            insert_source(conn, f"manual_{index:02d}", source_type="manual_note")
        for index in range(6):
            insert_source(conn, f"official_{index:02d}", source_type="official")

    metrics = build_pilot_metrics(db_path)

    assert metrics["collected_count"] == 6
    assert metrics["source_type_counts"] == {"manual_note": 24, "official": 6}
    assert metrics["pilot_collection_target_met"] is False


def test_build_pilot_metrics_approved_boundary(tmp_path: Path):
    db_path = tmp_path / "app.db"
    initialize_test_db(db_path)

    with connect(db_path) as conn:
        for index in range(20):
            insert_reviewed_annotation(
                conn,
                f"approved_{index:02d}",
                source_type="official",
                source_quality="high",
                review_status="approved",
                mapped_direction="growth",
            )

    metrics = build_pilot_metrics(db_path)
    assert metrics["approved_formal_count"] == 20
    assert metrics["pilot_minimum_approved_met"] is True

    db_path_19 = tmp_path / "app_19.db"
    initialize_test_db(db_path_19)
    with connect(db_path_19) as conn:
        for index in range(19):
            insert_reviewed_annotation(
                conn,
                f"approved_{index:02d}",
                source_type="official",
                source_quality="high",
                review_status="approved",
                mapped_direction="growth",
            )

    metrics_19 = build_pilot_metrics(db_path_19)
    assert metrics_19["approved_formal_count"] == 19
    assert metrics_19["pilot_minimum_approved_met"] is False


def test_build_pilot_metrics_direction_coverage_boundary(tmp_path: Path):
    directions = ["growth", "content", "campaign", "community", "research", "strategy"]
    db_path = tmp_path / "app.db"
    initialize_test_db(db_path)

    with connect(db_path) as conn:
        for direction in directions:
            conn.execute(
                """
                INSERT OR IGNORE INTO directions (
                  key, label, short_label, animal, avatar_src, plain_summary,
                  competency_definition, typical_tasks, common_capabilities,
                  suitable_roles, risk_notes, portfolio_guidance
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    direction,
                    direction,
                    direction,
                    "none",
                    f"/avatars/{direction}.svg",
                    f"{direction} work",
                    f"{direction} competency",
                    to_json(["task"]),
                    to_json(["capability"]),
                    to_json(["intern"]),
                    to_json(["risk"]),
                    "Build a portfolio.",
                ),
            )
        for index, direction in enumerate(directions):
            insert_reviewed_annotation(
                conn,
                f"approved_{index:02d}",
                source_type="official",
                source_quality="high",
                review_status="approved",
                mapped_direction=direction,
            )

    metrics = build_pilot_metrics(db_path)
    assert len(metrics["covered_approved_directions"]) == 6
    assert metrics["pilot_minimum_direction_coverage_met"] is True

    db_path_5 = tmp_path / "app_5.db"
    initialize_test_db(db_path_5)
    with connect(db_path_5) as conn:
        for direction in directions[:5]:
            conn.execute(
                """
                INSERT OR IGNORE INTO directions (
                  key, label, short_label, animal, avatar_src, plain_summary,
                  competency_definition, typical_tasks, common_capabilities,
                  suitable_roles, risk_notes, portfolio_guidance
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    direction,
                    direction,
                    direction,
                    "none",
                    f"/avatars/{direction}.svg",
                    f"{direction} work",
                    f"{direction} competency",
                    to_json(["task"]),
                    to_json(["capability"]),
                    to_json(["intern"]),
                    to_json(["risk"]),
                    "Build a portfolio.",
                ),
            )
        for index, direction in enumerate(directions[:5]):
            insert_reviewed_annotation(
                conn,
                f"approved_{index:02d}",
                source_type="official",
                source_quality="high",
                review_status="approved",
                mapped_direction=direction,
            )

    metrics_5 = build_pilot_metrics(db_path_5)
    assert len(metrics_5["covered_approved_directions"]) == 5
    assert metrics_5["pilot_minimum_direction_coverage_met"] is False


def test_build_pilot_metrics_counts_latest_reviewed_jd_once(tmp_path: Path):
    db_path = tmp_path / "app.db"
    initialize_test_db(db_path)
    with connect(db_path) as conn:
        insert_source(conn, "duplicate-reviewed")
        for annotation_id, reviewed_at in [
            ("old-review", "2026-05-29"),
            ("new-review", "2026-05-30"),
        ]:
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
                    "duplicate-reviewed",
                    "growth",
                    to_json([]),
                    to_json(["用户路径分析"]),
                    to_json(["数据整理"]),
                    to_json(["Excel"]),
                    to_json(["复盘"]),
                    "pilot fixture",
                    "approved",
                    "checked",
                    "tester",
                    reviewed_at,
                ),
            )

    metrics = build_pilot_metrics(db_path)

    assert metrics["reviewed_annotation_count"] == 1
    assert metrics["approved_formal_count"] == 1
    assert metrics["approved_direction_counts"] == {"growth": 1}


def test_build_pilot_metrics_uses_insert_order_for_same_day_reviews(tmp_path: Path):
    db_path = tmp_path / "app.db"
    initialize_test_db(db_path)
    with connect(db_path) as conn:
        insert_source(conn, "same-day-metrics", source_type="official", source_quality="high")
        for annotation_id, review_status in [
            ("z-old-approved", "approved"),
            ("a-new-rejected", "rejected"),
        ]:
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
                    "same-day-metrics",
                    "growth",
                    to_json([]),
                    to_json(["用户路径分析"]),
                    to_json(["数据整理"]),
                    to_json(["Excel"]),
                    to_json(["复盘"]),
                    "pilot fixture",
                    review_status,
                    "checked",
                    "tester",
                    "2026-05-30",
                ),
            )

    metrics = build_pilot_metrics(db_path)

    assert metrics["reviewed_annotation_count"] == 1
    assert metrics["approved_formal_count"] == 0
    assert metrics["status_counts"] == {"rejected": 1}


def test_build_pilot_metrics_reports_uninitialized_database(tmp_path: Path):
    db_path = tmp_path / "empty.db"
    db_path.touch()

    with pytest.raises(RuntimeError, match="not initialized"):
        build_pilot_metrics(db_path)


def test_validate_ai_annotation_payload_accepts_strict_json():
    raw_text = valid_ai_raw_text()
    payload = json.loads(json.dumps(valid_ai_payload(), ensure_ascii=False))

    normalized = validate_ai_annotation_payload(payload, raw_text=raw_text)

    assert normalized["mapped_direction"] == "growth"
    assert normalized["secondary_directions"] == ["campaign"]
    assert normalized["confidence"] == 0.82
    assert normalized["needs_human_attention"] is False
    assert normalized["attention_reasons"] == []


def test_validate_ai_annotation_payload_rejects_quote_not_in_jd():
    raw_text = valid_ai_raw_text()
    payload = valid_ai_payload()
    payload["evidence_quotes"] = [
        {"text": "不存在的原文片段", "supports": "task_keywords"}
    ]

    with pytest.raises(ValueError, match="evidence_quotes"):
        validate_ai_annotation_payload(payload, raw_text=raw_text)


def test_validate_ai_annotation_payload_marks_low_confidence_attention():
    raw_text = valid_ai_raw_text()
    payload = valid_ai_payload()
    payload["confidence"] = 0.64

    normalized = validate_ai_annotation_payload(payload, raw_text=raw_text)

    assert normalized["needs_human_attention"] is True
    assert "confidence_below_0.65" in normalized["attention_reasons"]


def test_validate_ai_annotation_payload_rejects_nan_confidence():
    raw_text = valid_ai_raw_text()
    payload = valid_ai_payload()
    payload["confidence"] = float("nan")

    with pytest.raises(ValueError, match="confidence"):
        validate_ai_annotation_payload(payload, raw_text=raw_text)


def test_openai_payload_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        create_openai_payload("prompt", model="gpt-4.1-mini")


def test_run_ai_annotation_from_fixture_saves_draft(tmp_path: Path):
    db_path = tmp_path / "app.db"
    fixture_path = tmp_path / "ai_annotations.json"
    raw_text = valid_ai_raw_text()
    initialize_test_db(db_path)
    with connect(db_path) as conn:
        insert_source(conn, "jd-ai-1")
        conn.execute(
            """
            UPDATE jd_sources
            SET raw_status = 'collected', raw_text = ?, responsibilities_text = ?
            WHERE id = ?
            """,
            (raw_text, raw_text, "jd-ai-1"),
        )
    fixture_path.write_text(
        json.dumps({"jd-ai-1": valid_ai_payload()}, ensure_ascii=False),
        encoding="utf-8",
    )

    saved_count = run_ai_annotation_from_fixture(
        db_path,
        fixture_path,
        model_name="fixture-test",
    )

    assert saved_count == 1
    with connect(db_path) as conn:
        source = conn.execute(
            "SELECT raw_status FROM jd_sources WHERE id = ?",
            ("jd-ai-1",),
        ).fetchone()
        draft = conn.execute(
            "SELECT * FROM jd_ai_annotations WHERE jd_id = ?",
            ("jd-ai-1",),
        ).fetchone()

    assert source["raw_status"] == "ai_annotated"
    assert draft["mapped_direction"] == "growth"
    assert json.loads(draft["secondary_directions"]) == ["campaign"]
    assert draft["confidence"] == 0.82
    assert draft["model_name"] == "fixture-test"
    assert draft["prompt_version"] == "jd-annotation-v1"


def test_run_ai_annotation_from_fixture_updates_existing_draft(tmp_path: Path):
    db_path = tmp_path / "app.db"
    fixture_path = tmp_path / "ai_annotations.json"
    raw_text = valid_ai_raw_text()
    initialize_test_db(db_path)
    with connect(db_path) as conn:
        insert_source(conn, "jd-ai-repeat")
        conn.execute(
            """
            UPDATE jd_sources
            SET raw_status = 'collected', raw_text = ?, responsibilities_text = ?
            WHERE id = ?
            """,
            (raw_text, raw_text, "jd-ai-repeat"),
        )

    fixture_path.write_text(
        json.dumps({"jd-ai-repeat": valid_ai_payload()}, ensure_ascii=False),
        encoding="utf-8",
    )
    first_count = run_ai_annotation_from_fixture(db_path, fixture_path)

    changed_payload = valid_ai_payload()
    changed_payload["confidence"] = 0.72
    changed_payload["reasoning_summary"] = "第二次标注更新了置信度。"
    fixture_path.write_text(
        json.dumps({"jd-ai-repeat": changed_payload}, ensure_ascii=False),
        encoding="utf-8",
    )
    second_count = run_ai_annotation_from_fixture(db_path, fixture_path)

    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT confidence, reasoning_summary
            FROM jd_ai_annotations
            WHERE jd_id = ?
            """,
            ("jd-ai-repeat",),
        ).fetchall()

    assert first_count == 1
    assert second_count == 1
    assert len(rows) == 1
    assert rows[0]["confidence"] == 0.72
    assert rows[0]["reasoning_summary"] == "第二次标注更新了置信度。"


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


def test_import_reviewed_jds_updates_existing_final_annotation(tmp_path: Path) -> None:
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
    rows[0]["review_notes"] = "first review"
    rows[0]["reviewed_by"] = "tester"
    rows[0]["reviewed_at"] = "2026-05-29"
    write_csv(export_path, rows)
    first_imported = import_reviewed_jds(db_path, export_path)

    rows[0]["review_notes"] = "updated review"
    rows[0]["reviewed_at"] = "2026-05-30"
    write_csv(export_path, rows)
    second_imported = import_reviewed_jds(db_path, export_path)

    with connect(db_path) as conn:
        annotations = conn.execute(
            """
            SELECT review_notes, reviewed_at
            FROM jd_annotations
            WHERE jd_id = ?
            """,
            ("jd-review-1",),
        ).fetchall()

    assert first_imported == 1
    assert second_imported == 1
    assert len(annotations) == 1
    assert annotations[0]["review_notes"] == "updated review"
    assert annotations[0]["reviewed_at"] == "2026-05-30"


def test_export_jd_review_uses_latest_ai_draft_per_jd(tmp_path: Path) -> None:
    db_path, _ = prepare_ai_review_record(tmp_path)
    export_path = tmp_path / "review.csv"
    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO jd_ai_annotations (
              id, jd_id, mapped_direction, secondary_directions, confidence,
              task_keywords, capability_keywords, tool_keywords, jargon_terms,
              evidence_quotes, reasoning_summary, needs_human_attention,
              attention_reasons, model_name, prompt_version, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "ai-newer",
                "jd-review-1",
                "growth",
                to_json(["campaign"]),
                0.91,
                to_json(["更新任务1", "更新任务2", "更新任务3"]),
                to_json(["更新能力1", "更新能力2", "更新能力3"]),
                to_json(["Excel"]),
                to_json(["复盘"]),
                to_json([{"text": "负责活动数据整理", "supports": "task_keywords"}]),
                "newer draft",
                0,
                to_json([]),
                "fixture-newer",
                "jd-annotation-v1",
                "2999-01-01 00:00:00",
            ),
        )

    exported = export_jd_review(db_path, export_path)

    with export_path.open("r", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))

    assert exported == 1
    assert len(rows) == 1
    assert rows[0]["ai_annotation_id"] == "ai-newer"


def test_validate_review_row_requires_approved_reviewer_and_date() -> None:
    row = {column: "" for column in REVIEW_COLUMNS}
    row.update(
        {
            "jd_id": "jd-review-1",
            "ai_annotation_id": "ai-review-1",
            "ai_mapped_direction": "growth",
            "reviewed_mapped_direction": "growth",
            "reviewed_secondary_directions": "campaign",
            "reviewed_task_keywords": "数据复盘|路径分析|效果对比",
            "reviewed_capability_keywords": "指标意识|假设验证|表格能力",
            "review_status": "approved",
        }
    )

    with pytest.raises(ValueError, match="reviewed_by"):
        validate_review_row(row, row_number=2)

    row["reviewed_by"] = "tester"
    with pytest.raises(ValueError, match="reviewed_at"):
        validate_review_row(row, row_number=2)
