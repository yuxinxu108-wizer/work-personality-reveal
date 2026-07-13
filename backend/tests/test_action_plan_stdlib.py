import unittest

from backend.app.services.action_plan_service import build_action_plan


MAIN_DIRECTION = {
    "key": "growth",
    "label": "数据增长型",
    "short_label": "增长运营",
    "plain_summary": "观察每一步有多少人留下来，用数字判断哪里最值得先改。",
    "typical_tasks": ["数据复盘", "路径分析", "效果对比", "增长实验设计"],
    "common_capabilities": ["指标意识", "表格能力", "假设验证", "结果复盘"],
    "portfolio_guidance": "分析一个报名或关注路径的流失问题，提出可验证的改进方案。",
}

SUPPORT_DIRECTION = {
    "key": "content",
    "label": "内容表达型",
    "short_label": "内容运营",
    "plain_summary": "把信息整理成用户愿意点开、看懂、收藏或转发的内容。",
    "typical_tasks": ["选题策划", "标题优化", "内容排期", "内容数据复盘"],
    "common_capabilities": ["表达能力", "热点敏感", "内容结构", "平台理解"],
    "portfolio_guidance": "搭建一个面向大学生求职的内容账号方案。",
}

EVIDENCE = {
    "high_frequency_tasks": ["用户路径分析", "数据复盘", "转化漏斗"],
    "high_frequency_capabilities": ["数据分析", "结构化思维", "沟通协作"],
    "resume_keywords": ["数据分析", "复盘归因"],
    "evidence_confidence": {"level": "medium"},
}


class ActionPlanTest(unittest.TestCase):
    def test_builds_detailed_7_day_plan_from_direction_and_jd_evidence(self):
        plan = build_action_plan(MAIN_DIRECTION, SUPPORT_DIRECTION, EVIDENCE)

        self.assertEqual(len(plan), 7)
        self.assertEqual(plan[0]["label"], "Day 1")
        for day in plan:
            self.assertTrue(day["title"])
            self.assertTrue(day["goal"])
            self.assertGreaterEqual(len(day["tasks"]), 3)
            self.assertTrue(day["deliverable"])
            self.assertTrue(day["resume_sentence"])
            self.assertIn("jd_keywords", day)

        joined = " ".join(
            [day["title"] for day in plan]
            + [task for day in plan for task in day["tasks"]]
        )
        self.assertIn("用户路径分析", joined)
        self.assertIn("内容运营", joined)
        self.assertIn("转化漏斗", joined)


if __name__ == "__main__":
    unittest.main()
