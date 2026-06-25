import unittest

from backend.app.services.assessment_service import build_assessment_result


DIRECTIONS = [
    {"key": "ux", "label": "用户体验型"},
    {"key": "growth", "label": "数据增长型"},
    {"key": "content", "label": "内容表达型"},
]

QUESTIONS = [
    {
        "id": f"q{index:02d}",
        "options": [
            {
                "weights": [
                    {"direction": "ux", "value": 2},
                    {"direction": "growth", "value": 1},
                ]
            },
            {
                "weights": [
                    {"direction": "content", "value": 2},
                    {"direction": "growth", "value": 1},
                ]
            },
        ],
    }
    for index in range(1, 26)
]


class AssessmentConfidenceTest(unittest.TestCase):
    def test_empty_answers_are_insufficient_for_a_product_result(self):
        result = build_assessment_result({}, QUESTIONS, DIRECTIONS)

        self.assertFalse(result["is_sufficient"])
        self.assertEqual(result["confidence"]["level"], "insufficient")
        self.assertEqual(result["confidence"]["valid_answer_count"], 0)
        self.assertEqual(result["confidence"]["min_required_answer_count"], 20)
        self.assertGreater(result["confidence"]["missing_required_answer_count"], 0)

    def test_complete_answers_include_confidence_and_explanation(self):
        answers = {question["id"]: 0 for question in QUESTIONS}

        result = build_assessment_result(answers, QUESTIONS, DIRECTIONS)

        self.assertTrue(result["is_sufficient"])
        self.assertEqual(result["main_direction"], "ux")
        self.assertEqual(result["confidence"]["valid_answer_count"], 25)
        self.assertEqual(result["confidence"]["total_question_count"], 25)
        self.assertIn(result["confidence"]["level"], {"high", "medium", "low"})
        self.assertIn("用户体验型", result["result_explanation"])


if __name__ == "__main__":
    unittest.main()
