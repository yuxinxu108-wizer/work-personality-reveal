import tempfile
import unittest
from pathlib import Path

from backend.app.db import connect, from_json, initialize_database, to_json
from backend.app.repositories.jd_repository import JDRepository


def seed_direction(db_path: Path):
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
                "ux",
                "用户体验型",
                "C 端产品",
                "小猫",
                "/assets/avatars/ux-cat.png",
                "关注用户体验",
                "体验问题定义",
                to_json(["体验走查"]),
                to_json(["用户视角"]),
                to_json(["C 端产品实习生"]),
                to_json(["避免只凭感觉"]),
                "做一个体验优化项目。",
            ),
        )


class AssessmentRunRepositoryTest(unittest.TestCase):
    def test_save_assessment_run_persists_replayable_result(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "app.db"
            initialize_database(db_path)
            seed_direction(db_path)
            repository = JDRepository(db_path)

            run_id = repository.save_assessment_run(
                answers={"q01": 0},
                scores={"ux": 100},
                main_direction="ux",
                supporting_directions=["growth"],
                confidence={
                    "level": "high",
                    "valid_answer_count": 25,
                    "total_question_count": 25,
                    "min_required_answer_count": 20,
                    "missing_required_answer_count": 0,
                    "reason": "答题完整度较高。",
                },
            )

            with connect(db_path) as conn:
                row = conn.execute(
                    "SELECT * FROM assessment_runs WHERE id = ?",
                    (run_id,),
                ).fetchone()

            self.assertTrue(run_id.startswith("run-"))
            self.assertEqual(row["main_direction"], "ux")
            self.assertEqual(row["confidence_level"], "high")
            self.assertEqual(row["valid_answer_count"], 25)
            self.assertEqual(from_json(row["answers_json"]), {"q01": 0})
            self.assertEqual(from_json(row["scores_json"]), {"ux": 100})
            self.assertEqual(from_json(row["supporting_directions"]), ["growth"])
            self.assertEqual(from_json(row["confidence_json"])["reason"], "答题完整度较高。")


if __name__ == "__main__":
    unittest.main()
