import unittest

from backend.app.services.evidence_service import build_evidence_summary


class FakeRepository:
    def __init__(self, annotations):
        self.annotations = annotations

    def list_jd_annotations_for_direction(self, direction_key, *, formal_only=True):
        return self.annotations


def annotation(index, *, source_quality="medium", collected_at="2026-06-25"):
    return {
        "role_title": f"产品运营实习生 {index}",
        "source_type": "recruiting_platform",
        "source_quality": source_quality,
        "collected_at": collected_at,
        "review_level": "manual_reviewed",
        "task_keywords": ["用户研究", "数据分析", "项目推进"],
        "capability_keywords": ["结构化思维", "沟通协作", "产品思维"],
        "tool_keywords": ["Excel"],
        "jargon_terms": ["转化率"],
        "secondary_directions": [],
    }


class EvidenceConfidenceTest(unittest.TestCase):
    def test_no_evidence_reports_none_confidence(self):
        summary = build_evidence_summary(FakeRepository([]), "ux")

        self.assertEqual(summary["evidence_confidence"]["level"], "none")
        self.assertEqual(summary["evidence_confidence"]["sample_count"], 0)
        self.assertEqual(summary["evidence_confidence"]["min_recommended_jd_count"], 30)

    def test_low_sample_count_reports_limited_confidence(self):
        summary = build_evidence_summary(
            FakeRepository([annotation(index) for index in range(7)]),
            "ux",
        )

        self.assertEqual(summary["evidence_confidence"]["level"], "low")
        self.assertIn("样本较少", summary["evidence_confidence"]["message"])

    def test_target_sample_count_reports_high_confidence(self):
        summary = build_evidence_summary(
            FakeRepository([annotation(index, source_quality="high") for index in range(30)]),
            "strategy",
        )

        self.assertEqual(summary["evidence_confidence"]["level"], "high")
        self.assertEqual(summary["source_quality_summary"], {"high": 30})
        self.assertEqual(summary["latest_collected_at"], "2026-06-25")

    def test_review_level_summary_counts_strong_and_rule_generated_records(self):
        records = [
            annotation(1),
            {**annotation(2), "review_level": "rule_generated"},
            {**annotation(3), "review_level": "spot_checked"},
        ]

        summary = build_evidence_summary(FakeRepository(records), "strategy")

        self.assertEqual(summary["review_level_summary"], {
            "manual_reviewed": 1,
            "rule_generated": 1,
            "spot_checked": 1,
        })
        self.assertEqual(summary["strong_review_jd_count"], 2)


if __name__ == "__main__":
    unittest.main()
