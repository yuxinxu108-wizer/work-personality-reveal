import tempfile
import unittest
from pathlib import Path

from backend.app.db import connect, initialize_database, to_json
from scripts.data_quality_report import build_data_quality_report


DIRECTIONS = [
    ("ux", "用户体验型"),
    ("process", "业务流程型"),
    ("growth", "数据增长型"),
]


def seed_direction(conn, key, label):
    conn.execute(
        """
        INSERT INTO directions (
          key, label, short_label, animal, avatar_src, plain_summary,
          competency_definition, typical_tasks, common_capabilities,
          suitable_roles, risk_notes, portfolio_guidance
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            key,
            label,
            label,
            "none",
            f"/assets/{key}.png",
            f"{label} summary",
            f"{label} competency",
            to_json(["任务"]),
            to_json(["能力"]),
            to_json(["岗位"]),
            to_json(["风险"]),
            "作品集建议",
        ),
    )


def seed_jd(conn, index, direction, *, review_level="manual_reviewed"):
    jd_id = f"jd-{index}"
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
            jd_id,
            "Example",
            f"{direction} 实习生",
            direction,
            f"https://example.com/{jd_id}",
            "recruiting_platform",
            "medium",
            "",
            "reviewed",
            "上海",
            "internship",
            "负责用户研究、数据分析、项目推进",
            "负责用户研究、数据分析、项目推进",
            "具备结构化思维、沟通协作、产品思维",
            f"2026-06-{10 + index:02d}",
        ),
    )
    conn.execute(
        """
        INSERT INTO jd_annotations (
          id, jd_id, mapped_direction, secondary_directions,
          task_keywords, capability_keywords, tool_keywords, jargon_terms,
          notes, review_status, review_level
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"annotation-{index}",
            jd_id,
            direction,
            to_json([]),
            to_json(["用户研究", "数据分析", "项目推进"]),
            to_json(["结构化思维", "沟通协作", "产品思维"]),
            to_json(["Excel"]),
            to_json(["NPS"]),
            "",
            "approved",
            review_level,
        ),
    )


class DataQualityReportTest(unittest.TestCase):
    def test_report_lists_every_direction_and_flags_low_sample_coverage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "app.db"
            initialize_database(db_path)
            with connect(db_path) as conn:
                for key, label in DIRECTIONS:
                    seed_direction(conn, key, label)
                seed_jd(conn, 1, "ux", review_level="rule_generated")
                seed_jd(conn, 2, "ux", review_level="manual_reviewed")
                for index in range(3, 33):
                    seed_jd(conn, index, "growth", review_level="spot_checked")

            report = build_data_quality_report(db_path, min_recommended_jd_count=30)

        self.assertEqual(report["total_direction_count"], 3)
        self.assertEqual([row["direction_key"] for row in report["directions"]], [
            "growth",
            "process",
            "ux",
        ])
        ux = next(row for row in report["directions"] if row["direction_key"] == "ux")
        process = next(row for row in report["directions"] if row["direction_key"] == "process")
        growth = next(row for row in report["directions"] if row["direction_key"] == "growth")

        self.assertEqual(ux["formal_jd_count"], 2)
        self.assertEqual(ux["strong_review_jd_count"], 1)
        self.assertEqual(ux["review_level_summary"], {
            "manual_reviewed": 1,
            "rule_generated": 1,
        })
        self.assertEqual(ux["coverage_status"], "low_sample")
        self.assertEqual(process["coverage_status"], "no_evidence")
        self.assertEqual(growth["coverage_status"], "target_met")
        self.assertEqual(growth["latest_collected_at"], "2026-06-42")


if __name__ == "__main__":
    unittest.main()
