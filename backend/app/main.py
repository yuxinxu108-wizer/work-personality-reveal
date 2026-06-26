import os
import sqlite3
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.app.repositories.jd_repository import JDRepository
from backend.app.schemas import AssessmentSubmitRequest
from backend.app.services.assessment_service import build_assessment_result
from backend.app.services.evidence_service import build_evidence_summary


app = FastAPI(title="JD Backed Assessment API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:5174",
        "http://localhost:5174",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def get_db_path() -> Path:
    return Path(os.environ.get("ASSESSMENT_DB_PATH", "data/app.db"))


def get_repository() -> JDRepository:
    return JDRepository(get_db_path())


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/directions")
def list_directions() -> list[dict[str, Any]]:
    return _read_database(get_repository().list_directions)


@app.get("/api/questions")
def list_questions() -> list[dict[str, Any]]:
    questions = _read_database(get_repository().list_questions)
    return [
        {
            "id": question["id"],
            "text": question["text"],
            "question_type": question["question_type"],
            "options": [
                {"id": option["id"], "text": option["text"]}
                for option in question["options"]
            ],
        }
        for question in questions
    ]


@app.post("/api/assessment/submit")
def submit_assessment(request: AssessmentSubmitRequest) -> dict[str, Any]:
    repository = get_repository()
    directions = _read_database(repository.list_directions)
    questions = _read_database(repository.list_questions)
    if not directions or not questions:
        raise HTTPException(
            status_code=503,
            detail="Assessment database is not seeded.",
        )

    selected = build_assessment_result(request.answers, questions, directions)
    if not selected["is_sufficient"]:
        raise HTTPException(
            status_code=422,
            detail=selected["confidence"]["reason"],
        )
    if not selected["main_direction"] or not selected["supporting_directions"]:
        raise HTTPException(
            status_code=503,
            detail="Assessment result could not be selected.",
        )

    main_direction = _read_database(
        repository.get_direction,
        selected["main_direction"],
    )
    support_key = selected["supporting_directions"][0]
    support_direction = _read_database(repository.get_direction, support_key)
    if main_direction is None or support_direction is None:
        raise HTTPException(
            status_code=503,
            detail="Assessment direction metadata is incomplete.",
        )
    evidence = _read_database(
        build_evidence_summary,
        repository,
        selected["main_direction"],
    )
    assessment_run_id = _read_database(
        repository.save_assessment_run,
        answers=request.answers,
        scores=selected["normalized_scores"],
        main_direction=selected["main_direction"],
        supporting_directions=selected["supporting_directions"],
        confidence=selected["confidence"],
    )

    return {
        "assessment_run_id": assessment_run_id,
        "main_direction": selected["main_direction"],
        "supporting_directions": selected["supporting_directions"],
        "scores": selected["normalized_scores"],
        "is_multi_sided": selected["is_multi_sided"],
        "confidence": selected["confidence"],
        "result_explanation": selected["result_explanation"],
        "result": {
            "title": main_direction["label"],
            "summary": main_direction["plain_summary"],
            "support_summary": support_direction["plain_summary"],
            "route_steps": [
                "先理解该方向在真实 JD 中的高频任务。",
                "用一个小项目证明你能完成这些任务。",
                "把项目表达成岗位关键词和可验证结果。",
            ],
            "action_plan": [],
            "portfolio_suggestion": main_direction["portfolio_guidance"],
        },
        "evidence": evidence,
    }


@app.get("/api/evidence/{direction_key}")
def direction_evidence(direction_key: str) -> dict[str, Any]:
    return _read_database(build_evidence_summary, get_repository(), direction_key)


@app.post("/api/ai/explain")
def ai_explain_placeholder() -> dict[str, object]:
    return {
        "available": False,
        "message": "AI explanation is reserved for a later phase.",
    }


def _read_database(function: Any, *args: Any, **kwargs: Any) -> Any:
    try:
        return function(*args, **kwargs)
    except sqlite3.Error as exc:
        raise HTTPException(
            status_code=503,
            detail="Assessment database is not initialized.",
        ) from exc
