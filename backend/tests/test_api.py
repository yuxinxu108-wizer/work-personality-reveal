import sqlite3
import json
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.db import connect, initialize_database
from backend.app.main import app
from backend.app.repositories.jd_repository import JDRepository
from backend.app.services.assessment_service import (
    normalize_scores,
    score_answers,
    select_result,
)
from backend.app.services.evidence_service import build_evidence_summary
from scripts.import_jds import import_seed_data, validate_seed_data


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_initialize_database_creates_tables(tmp_path: Path):
    db_path = tmp_path / "app.db"
    initialize_database(db_path)

    with sqlite3.connect(db_path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }

    assert {
        "jd_sources",
        "jd_annotations",
        "directions",
        "questions",
        "question_options",
        "assessment_runs",
    }.issubset(tables)


def test_connect_enforces_foreign_keys(tmp_path: Path):
    db_path = tmp_path / "app.db"
    initialize_database(db_path)

    with connect(db_path) as conn:
        foreign_keys = conn.execute("PRAGMA foreign_keys").fetchone()[0]

    assert foreign_keys == 1


def test_foreign_keys_reject_orphan_rows(tmp_path: Path):
    db_path = tmp_path / "app.db"
    initialize_database(db_path)

    with connect(db_path) as conn:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO question_options (id, question_id, text, weights)
                VALUES ('orphan_option', 'missing_question', 'bad', '[]')
                """
            )


def test_direction_foreign_keys_reject_unknown_main_direction(tmp_path: Path):
    db_path = tmp_path / "app.db"
    initialize_database(db_path)

    with connect(db_path) as conn:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO assessment_runs (
                  id, answers_json, scores_json, main_direction, supporting_directions
                ) VALUES ('run_1', '{}', '{}', 'missing', '[]')
                """
            )


def test_initialize_database_migrates_existing_direction_foreign_keys(tmp_path: Path):
    db_path = tmp_path / "app.db"
    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE jd_sources (
              id TEXT PRIMARY KEY,
              company TEXT NOT NULL,
              role_title TEXT NOT NULL,
              role_category TEXT NOT NULL,
              source_url TEXT NOT NULL,
              source_type TEXT NOT NULL,
              location TEXT NOT NULL,
              employment_type TEXT NOT NULL,
              raw_text TEXT NOT NULL,
              responsibilities_text TEXT NOT NULL,
              requirements_text TEXT NOT NULL,
              collected_at TEXT NOT NULL,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE directions (
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
            CREATE TABLE jd_annotations (
              id TEXT PRIMARY KEY,
              jd_id TEXT NOT NULL REFERENCES jd_sources(id),
              mapped_direction TEXT NOT NULL,
              secondary_directions TEXT NOT NULL,
              task_keywords TEXT NOT NULL,
              capability_keywords TEXT NOT NULL,
              tool_keywords TEXT NOT NULL,
              jargon_terms TEXT NOT NULL,
              notes TEXT NOT NULL
            );
            CREATE TABLE assessment_runs (
              id TEXT PRIMARY KEY,
              answers_json TEXT NOT NULL,
              scores_json TEXT NOT NULL,
              main_direction TEXT NOT NULL,
              supporting_directions TEXT NOT NULL,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

    initialize_database(db_path)

    with connect(db_path) as conn:
        jd_annotation_fks = {
            (row["table"], row["from"])
            for row in conn.execute("PRAGMA foreign_key_list(jd_annotations)")
        }
        assessment_run_fks = {
            (row["table"], row["from"])
            for row in conn.execute("PRAGMA foreign_key_list(assessment_runs)")
        }

    assert ("directions", "mapped_direction") in jd_annotation_fks
    assert ("directions", "main_direction") in assessment_run_fks


def test_import_seed_data_loads_core_records(tmp_path: Path):
    db_path = tmp_path / "app.db"
    initialize_database(db_path)
    import_seed_data(db_path, Path("data/seeds"))

    with sqlite3.connect(db_path) as conn:
        direction_count = conn.execute("SELECT COUNT(*) FROM directions").fetchone()[0]
        question_count = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
        option_count = conn.execute("SELECT COUNT(*) FROM question_options").fetchone()[0]
        jd_count = conn.execute("SELECT COUNT(*) FROM jd_sources").fetchone()[0]

    assert direction_count == 9
    assert question_count == 25
    assert option_count >= 100
    assert jd_count >= 20


def test_import_seed_data_is_idempotent(tmp_path: Path):
    db_path = tmp_path / "app.db"
    seed_dir = Path("data/seeds")
    initialize_database(db_path)

    import_seed_data(db_path, seed_dir)
    import_seed_data(db_path, seed_dir)

    with sqlite3.connect(db_path) as conn:
        counts = {
            table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in (
                "directions",
                "questions",
                "question_options",
                "jd_sources",
                "jd_annotations",
            )
        }

    assert counts == {
        "directions": 9,
        "questions": 25,
        "question_options": 125,
        "jd_sources": 24,
        "jd_annotations": 24,
    }


def test_validate_seed_data_rejects_invalid_question_type():
    directions, questions, jds = _load_valid_seed_data()
    questions[0]["question_type"] = "unknown"

    with pytest.raises(ValueError, match="question_type"):
        validate_seed_data(directions, questions, jds)


def test_validate_seed_data_rejects_blank_question_text():
    directions, questions, jds = _load_valid_seed_data()
    questions[0]["text"] = " "

    with pytest.raises(ValueError, match="text for q01"):
        validate_seed_data(directions, questions, jds)


def test_validate_seed_data_rejects_unknown_weight_direction():
    directions, questions, jds = _load_valid_seed_data()
    questions[0]["options"][0]["weights"][0]["direction"] = "unknown"

    with pytest.raises(ValueError, match="weight direction"):
        validate_seed_data(directions, questions, jds)


def test_validate_seed_data_rejects_blank_option_text():
    directions, questions, jds = _load_valid_seed_data()
    questions[0]["options"][0]["text"] = ""

    with pytest.raises(ValueError, match="text for q01_a1"):
        validate_seed_data(directions, questions, jds)


def test_validate_seed_data_rejects_duplicate_jd_ids():
    directions, questions, jds = _load_valid_seed_data()
    jds[1]["id"] = jds[0]["id"]

    with pytest.raises(ValueError, match="Duplicate jd id"):
        validate_seed_data(directions, questions, jds)


def test_validate_seed_data_rejects_bad_jd_date():
    directions, questions, jds = _load_valid_seed_data()
    jds[0]["collected_at"] = "2026/05/28"

    with pytest.raises(ValueError, match="collected_at"):
        validate_seed_data(directions, questions, jds)


def test_validate_seed_data_rejects_empty_direction_metadata():
    directions, questions, jds = _load_valid_seed_data()
    directions[0]["typical_tasks"] = []

    with pytest.raises(ValueError, match="typical_tasks"):
        validate_seed_data(directions, questions, jds)


def test_validate_seed_data_rejects_non_list_secondary_directions():
    directions, questions, jds = _load_valid_seed_data()
    jds[0]["annotation"]["secondary_directions"] = ""

    with pytest.raises(ValueError, match="secondary_directions"):
        validate_seed_data(directions, questions, jds)


def test_validate_seed_data_rejects_non_string_keyword_items():
    directions, questions, jds = _load_valid_seed_data()
    jds[0]["annotation"]["task_keywords"] = [123]

    with pytest.raises(ValueError, match="task_keywords"):
        validate_seed_data(directions, questions, jds)


def test_validate_seed_data_rejects_bad_source_type():
    directions, questions, jds = _load_valid_seed_data()
    jds[0]["source_type"] = "blog"

    with pytest.raises(ValueError, match="source_type"):
        validate_seed_data(directions, questions, jds)


def test_validate_seed_data_rejects_bad_source_url():
    directions, questions, jds = _load_valid_seed_data()
    jds[0]["source_url"] = "manual-seed-jd-001"

    with pytest.raises(ValueError, match="source_url"):
        validate_seed_data(directions, questions, jds)


def test_validate_seed_data_rejects_bad_weight_value():
    directions, questions, jds = _load_valid_seed_data()
    questions[0]["options"][0]["weights"][0]["value"] = 3

    with pytest.raises(ValueError, match="weight value"):
        validate_seed_data(directions, questions, jds)


def test_validate_seed_data_rejects_bool_weight_value():
    directions, questions, jds = _load_valid_seed_data()
    questions[0]["options"][0]["weights"][0]["value"] = True

    with pytest.raises(ValueError, match="weight value"):
        validate_seed_data(directions, questions, jds)


def test_import_seed_data_rejects_invalid_seed_without_mutating_db(tmp_path: Path):
    db_path = tmp_path / "app.db"
    seed_dir = Path("data/seeds")
    bad_seed_dir = tmp_path / "bad-seeds"
    bad_seed_dir.mkdir()

    for filename in (
        "direction_definitions.json",
        "question_bank.json",
        "jd_seed.json",
    ):
        (bad_seed_dir / filename).write_text(
            (seed_dir / filename).read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    import_seed_data(db_path, seed_dir)
    before_counts = _core_counts(db_path)

    bad_questions = json.loads(
        (bad_seed_dir / "question_bank.json").read_text(encoding="utf-8")
    )
    bad_questions[0]["options"][0]["weights"][0]["direction"] = "missing"
    (bad_seed_dir / "question_bank.json").write_text(
        json.dumps(bad_questions, ensure_ascii=False),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="weight direction"):
        import_seed_data(db_path, bad_seed_dir)

    assert _core_counts(db_path) == before_counts


def test_repository_loads_directions_questions_and_evidence(tmp_path: Path):
    db_path = tmp_path / "app.db"
    initialize_database(db_path)
    import_seed_data(db_path, Path("data/seeds"))
    repository = JDRepository(db_path)

    assert len(repository.list_directions()) == 9
    assert len(repository.list_questions()) == 25

    evidence = build_evidence_summary(repository, "growth")
    assert evidence == {
        "jd_count": 0,
        "evidence_status": "limited",
        "recommended_roles": [],
        "representative_roles": [],
        "high_frequency_tasks": [],
        "high_frequency_capabilities": [],
        "high_frequency_tools": [],
        "hard_requirements": [],
        "resume_keywords": [],
        "source_type_summary": {},
        "source_quality_summary": {},
        "review_level_summary": {},
        "strong_review_jd_count": 0,
        "latest_collected_at": "",
        "evidence_confidence": {
            "level": "none",
            "sample_count": 0,
            "min_recommended_jd_count": 30,
            "message": "当前方向暂无可用于展示的正式 JD 证据。",
        },
    }


def test_evidence_summary_handles_unknown_direction(tmp_path: Path):
    db_path = tmp_path / "app.db"
    initialize_database(db_path)
    import_seed_data(db_path, Path("data/seeds"))
    repository = JDRepository(db_path)

    evidence = build_evidence_summary(repository, "unknown")

    assert evidence == {
        "jd_count": 0,
        "evidence_status": "limited",
        "recommended_roles": [],
        "representative_roles": [],
        "high_frequency_tasks": [],
        "high_frequency_capabilities": [],
        "high_frequency_tools": [],
        "hard_requirements": [],
        "resume_keywords": [],
        "source_type_summary": {},
        "source_quality_summary": {},
        "review_level_summary": {},
        "strong_review_jd_count": 0,
        "latest_collected_at": "",
        "evidence_confidence": {
            "level": "none",
            "sample_count": 0,
            "min_recommended_jd_count": 30,
            "message": "当前方向暂无可用于展示的正式 JD 证据。",
        },
    }


def test_analyze_keywords_script_runs_without_pythonpath(tmp_path: Path):
    db_path = tmp_path / "app.db"
    initialize_database(db_path)
    import_seed_data(db_path, Path("data/seeds"))

    result = subprocess.run(
        [
            sys.executable,
            "scripts/analyze_keywords.py",
            "--db",
            str(db_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["growth"]["jd_count"] == 0


def test_analyze_keywords_script_reports_uninitialized_db(tmp_path: Path):
    db_path = tmp_path / "empty.db"
    db_path.touch()

    result = subprocess.run(
        [
            sys.executable,
            "scripts/analyze_keywords.py",
            "--db",
            str(db_path),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "Database is not initialized" in result.stderr


def test_import_jds_script_runs_without_pythonpath(tmp_path: Path):
    db_path = tmp_path / "script-app.db"

    subprocess.run(
        [
            sys.executable,
            "scripts/import_jds.py",
            "--db",
            str(db_path),
            "--seed-dir",
            "data/seeds",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    with sqlite3.connect(db_path) as conn:
        direction_count = conn.execute("SELECT COUNT(*) FROM directions").fetchone()[0]

    assert direction_count == 9


def test_assessment_service_scores_and_selects_result(tmp_path: Path):
    db_path = tmp_path / "app.db"
    initialize_database(db_path)
    import_seed_data(db_path, Path("data/seeds"))
    repository = JDRepository(db_path)
    questions = repository.list_questions()
    answers = {question["id"]: 0 for question in questions}

    scores = score_answers(answers, questions, repository.list_directions())
    result = select_result(scores)

    assert result["main_direction"]
    assert 1 <= len(result["supporting_directions"]) <= 2
    assert len(result["ranked"]) == 9
    assert set(scores.keys()) == {
        direction["key"] for direction in repository.list_directions()
    }


def test_assessment_service_ignores_invalid_answers(tmp_path: Path):
    db_path = tmp_path / "app.db"
    initialize_database(db_path)
    import_seed_data(db_path, Path("data/seeds"))
    repository = JDRepository(db_path)
    directions = repository.list_directions()
    questions = repository.list_questions()
    answers = {
        questions[0]["id"]: -1,
        questions[1]["id"]: 99,
        questions[2]["id"]: "0",
        questions[3]["id"]: True,
    }

    assert score_answers(answers, questions, directions) == {
        direction["key"]: 0 for direction in directions
    }


def test_assessment_service_normalizes_empty_and_flat_scores():
    assert normalize_scores({}) == {}
    assert normalize_scores({"ux": 2, "growth": 2}) == {"ux": 0, "growth": 0}


def test_assessment_service_rejects_bool_weight_values():
    directions = [{"key": "ux"}]
    questions = [
        {
            "id": "q01",
            "options": [
                {
                    "weights": [
                        {"direction": "ux", "value": True},
                    ]
                }
            ],
        }
    ]

    assert score_answers({"q01": 0}, questions, directions) == {"ux": 0}


def test_assessment_service_selects_empty_and_small_results():
    assert select_result({}) == {
        "main_direction": None,
        "supporting_directions": [],
        "ranked": [],
        "normalized_scores": {},
        "is_multi_sided": False,
    }
    assert select_result({"ux": 4})["is_multi_sided"] is False
    two_direction = select_result({"ux": 4, "growth": 3})
    assert two_direction["main_direction"] == "ux"
    assert two_direction["supporting_directions"] == ["growth"]
    assert two_direction["is_multi_sided"] is False


def test_assessment_service_supports_negative_weights_and_support_ties():
    directions = [{"key": "ux"}, {"key": "growth"}, {"key": "content"}]
    questions = [
        {
            "id": "q01",
            "options": [
                {
                    "weights": [
                        {"direction": "ux", "value": 2},
                        {"direction": "content", "value": -2},
                    ]
                }
            ],
        }
    ]

    assert score_answers({"q01": 0}, questions, directions) == {
        "ux": 2,
        "growth": 0,
        "content": -2,
    }

    result = select_result({"ux": 5, "growth": 3, "content": 2})
    assert result["supporting_directions"] == ["growth", "content"]


def test_api_returns_directions_questions_and_assessment(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "app.db"
    initialize_database(db_path)
    import_seed_data(db_path, Path("data/seeds"))
    monkeypatch.setenv("ASSESSMENT_DB_PATH", str(db_path))

    response = client.get("/api/directions")
    assert response.status_code == 200
    assert len(response.json()) == 9

    questions_response = client.get("/api/questions")
    assert questions_response.status_code == 200
    questions = questions_response.json()
    assert len(questions) == 25
    assert "weights" not in questions[0]["options"][0]

    answers = {question["id"]: 0 for question in questions}
    submit_response = client.post("/api/assessment/submit", json={"answers": answers})
    assert submit_response.status_code == 200
    payload = submit_response.json()
    assert payload["assessment_run_id"].startswith("run-")
    assert payload["main_direction"]
    assert payload["supporting_directions"]
    assert payload["confidence"]["level"] in {"high", "medium", "low"}
    assert payload["confidence"]["valid_answer_count"] == 25
    assert payload["result_explanation"]
    action_plan = payload["result"]["action_plan"]
    assert len(action_plan) == 7
    assert {
        "label",
        "title",
        "goal",
        "tasks",
        "deliverable",
        "resume_sentence",
        "jd_keywords",
    }.issubset(action_plan[0])
    assert len(action_plan[0]["tasks"]) >= 3
    assert payload["evidence"]["jd_count"] == 0


def test_api_allows_frontend_cors_origin(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "app.db"
    initialize_database(db_path)
    import_seed_data(db_path, Path("data/seeds"))
    monkeypatch.setenv("ASSESSMENT_DB_PATH", str(db_path))

    response = client.options(
        "/api/questions",
        headers={
            "Origin": "http://127.0.0.1:5174",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5174"


def test_api_questions_do_not_expose_scoring_data(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "app.db"
    initialize_database(db_path)
    import_seed_data(db_path, Path("data/seeds"))
    monkeypatch.setenv("ASSESSMENT_DB_PATH", str(db_path))

    response = client.get("/api/questions")

    assert response.status_code == 200
    question = response.json()[0]
    assert "basis_notes" not in question
    assert "related_jd_tasks" not in question
    assert "weights" not in question["options"][0]


def test_api_returns_direction_evidence(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "app.db"
    initialize_database(db_path)
    import_seed_data(db_path, Path("data/seeds"))
    monkeypatch.setenv("ASSESSMENT_DB_PATH", str(db_path))

    response = client.get("/api/evidence/growth")

    assert response.status_code == 200
    assert response.json()["jd_count"] == 0


def test_api_submit_rejects_insufficient_answers(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "app.db"
    initialize_database(db_path)
    import_seed_data(db_path, Path("data/seeds"))
    monkeypatch.setenv("ASSESSMENT_DB_PATH", str(db_path))

    response = client.post("/api/assessment/submit", json={"answers": {}})

    assert response.status_code == 422
    assert "有效答题数量不足" in response.json()["detail"]


def test_api_rejects_coerced_answer_types(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "app.db"
    initialize_database(db_path)
    import_seed_data(db_path, Path("data/seeds"))
    monkeypatch.setenv("ASSESSMENT_DB_PATH", str(db_path))

    string_response = client.post(
        "/api/assessment/submit",
        json={"answers": {"q01": "0"}},
    )
    bool_response = client.post(
        "/api/assessment/submit",
        json={"answers": {"q01": True}},
    )
    extra_response = client.post(
        "/api/assessment/submit",
        json={"answers": {"q01": 0}, "extra": "nope"},
    )

    assert string_response.status_code == 422
    assert bool_response.status_code == 422
    assert extra_response.status_code == 422


def test_api_reports_uninitialized_database(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "empty.db"
    db_path.touch()
    monkeypatch.setenv("ASSESSMENT_DB_PATH", str(db_path))

    response = client.get("/api/directions")

    assert response.status_code == 503
    assert response.json()["detail"] == "Assessment database is not initialized."


def test_api_submit_reports_unseeded_database(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "app.db"
    initialize_database(db_path)
    monkeypatch.setenv("ASSESSMENT_DB_PATH", str(db_path))

    response = client.post("/api/assessment/submit", json={"answers": {}})

    assert response.status_code == 503
    assert response.json()["detail"] == "Assessment database is not seeded."


def test_ai_placeholder():
    response = client.post("/api/ai/explain", json={})
    assert response.status_code == 200
    assert response.json()["available"] is False


def _load_valid_seed_data():
    seed_dir = Path("data/seeds")
    directions = json.loads(
        (seed_dir / "direction_definitions.json").read_text(encoding="utf-8")
    )
    questions = json.loads(
        (seed_dir / "question_bank.json").read_text(encoding="utf-8")
    )
    jds = json.loads((seed_dir / "jd_seed.json").read_text(encoding="utf-8"))
    return directions, questions, jds


def _core_counts(db_path: Path) -> dict[str, int]:
    with sqlite3.connect(db_path) as conn:
        return {
            table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in (
                "directions",
                "questions",
                "question_options",
                "jd_sources",
                "jd_annotations",
            )
        }
