import tempfile
import unittest
from pathlib import Path

from backend.app.db import connect, initialize_database, to_json
from backend.app.repositories.jd_repository import JDRepository
from backend.app.services.jd_review_service import validate_review_row


BASE_REVIEW_ROW = {
    "jd_id": "jd-1",
    "source_url": "https://example.com/job",
    "company": "Example",
    "role_title": "用户研究实习生",
    "responsibilities_text": "负责用户研究、数据分析、项目推进",
    "requirements_text": "具备结构化思维、沟通协作、产品思维",
    "ai_annotation_id": "",
    "ai_mapped_direction": "research",
    "reviewed_mapped_direction": "research",
    "ai_secondary_directions": "",
    "reviewed_secondary_directions": "ux|strategy",
    "ai_task_keywords": "",
    "reviewed_task_keywords": "用户研究|数据分析|项目推进",
    "ai_capability_keywords": "",
    "reviewed_capability_keywords": "结构化思维|沟通协作|产品思维",
    "ai_tool_keywords": "",
    "reviewed_tool_keywords": "Excel",
    "ai_jargon_terms": "",
    "reviewed_jargon_terms": "NPS",
    "ai_confidence": "0.85",
    "needs_human_attention": "false",
    "review_status": "approved",
    "review_notes": "规则生成review；后续可人工抽查。",
    "reviewed_by": "codex_rule_review",
    "reviewed_at": "2026-06-25",
}


def insert_direction_and_source(db_path: Path):
    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO directions (
              key, label, short_label, animal, avatar_src, plain_summary,
              competency_definition, typical_tasks, common_capabilities,
              suitable_roles, risk_notes, portfolio_guidance
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "research",
                "用户研究型",
                "需求洞察",
                "小鹿",
                "/assets/avatars/research-deer.png",
                "理解真实用户",
                "用户研究",
                to_json(["用户访谈"]),
                to_json(["结构化思维"]),
                to_json(["用户研究实习生"]),
                to_json(["避免样本偏差"]),
                "做一次用户访谈项目。",
            ),
        )
        conn.execute(
            """
            INSERT INTO jd_sources (
              id, company, role_title, role_category, source_url, source_type,
              source_quality, collector_notes, raw_status, location,
              employment_type, raw_text, responsibilities_text,
              requirements_text, collected_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "jd-1",
                "Example",
                "用户研究实习生",
                "research",
                "https://example.com/job",
                "recruiting_platform",
                "medium",
                "",
                "reviewed",
                "上海",
                "internship",
                "负责用户研究、数据分析、项目推进",
                "负责用户研究、数据分析、项目推进",
                "具备结构化思维、沟通协作、产品思维",
                "2026-06-25",
            ),
        )


class ReviewLevelTest(unittest.TestCase):
    def test_legacy_rule_review_rows_are_not_strong_review(self):
        row = validate_review_row(BASE_REVIEW_ROW, row_number=2)

        self.assertEqual(row["review_level"], "rule_generated")

    def test_explicit_spot_checked_review_level_is_preserved(self):
        review_row = {**BASE_REVIEW_ROW, "review_level": "spot_checked"}

        row = validate_review_row(review_row, row_number=2)

        self.assertEqual(row["review_level"], "spot_checked")

    def test_repository_can_filter_strong_review_records(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "app.db"
            initialize_database(db_path)
            insert_direction_and_source(db_path)
            with connect(db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO jd_annotations (
                      id, jd_id, mapped_direction, secondary_directions,
                      task_keywords, capability_keywords, tool_keywords,
                      jargon_terms, notes, review_status, review_level
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "annotation-1",
                        "jd-1",
                        "research",
                        to_json([]),
                        to_json(["用户研究", "数据分析", "项目推进"]),
                        to_json(["结构化思维", "沟通协作", "产品思维"]),
                        to_json(["Excel"]),
                        to_json(["NPS"]),
                        "",
                        "approved",
                        "rule_generated",
                    ),
                )
            repository = JDRepository(db_path)

            weak_records = repository.list_jd_annotations_for_direction(
                "research",
                formal_only=True,
            )
            strong_records = repository.list_jd_annotations_for_direction(
                "research",
                formal_only=True,
                strong_review_only=True,
            )

            self.assertEqual(len(weak_records), 1)
            self.assertEqual(weak_records[0]["review_level"], "rule_generated")
            self.assertEqual(strong_records, [])

    def test_initialize_database_reclassifies_legacy_rule_reviews(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "app.db"
            initialize_database(db_path)
            insert_direction_and_source(db_path)
            with connect(db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO jd_annotations (
                      id, jd_id, mapped_direction, secondary_directions,
                      task_keywords, capability_keywords, tool_keywords,
                      jargon_terms, notes, review_status, review_level,
                      review_notes, reviewed_by, reviewed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "annotation-legacy",
                        "jd-1",
                        "research",
                        to_json([]),
                        to_json(["用户研究", "数据分析", "项目推进"]),
                        to_json(["结构化思维", "沟通协作", "产品思维"]),
                        to_json(["Excel"]),
                        to_json(["NPS"]),
                        "",
                        "approved",
                        "manual_reviewed",
                        "规则生成review；后续可人工抽查。",
                        "codex_rule_review",
                        "2026-06-25",
                    ),
                )

            initialize_database(db_path)

            with connect(db_path) as conn:
                review_level = conn.execute(
                    "SELECT review_level FROM jd_annotations WHERE id = ?",
                    ("annotation-legacy",),
                ).fetchone()["review_level"]

            self.assertEqual(review_level, "rule_generated")


if __name__ == "__main__":
    unittest.main()
