# JD-Backed Assessment Platform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Phase 1 FastAPI + SQLite backend and migrate the quiz frontend to use data-backed API responses with JD evidence.

**Architecture:** Add a Python FastAPI backend that owns SQLite persistence, JD seed import, scoring, and evidence summaries. Keep the existing static frontend experience, but move it into `frontend/` and make it call backend APIs for questions and assessment results. Seed data remains manually curated JSON in Phase 1; AI is represented only by a placeholder endpoint and prompt documentation.

**Tech Stack:** Python 3, FastAPI, SQLite via Python `sqlite3`, pytest, vanilla HTML/CSS/JS, Node built-in tests for legacy scoring coverage.

---

## File Structure

- Create: `backend/requirements.txt`
  - Python runtime and test dependencies.
- Create: `backend/app/main.py`
  - FastAPI app and route registration.
- Create: `backend/app/db.py`
  - SQLite connection, schema initialization, JSON helpers.
- Create: `backend/app/schemas.py`
  - Pydantic request/response models.
- Create: `backend/app/repositories/jd_repository.py`
  - Database reads for JD, directions, questions, and evidence.
- Create: `backend/app/services/assessment_service.py`
  - Scoring and result selection.
- Create: `backend/app/services/evidence_service.py`
  - Evidence summary construction.
- Create: `backend/app/ai/prompts.py`
  - Future prompt template constants, no model calls.
- Create: `backend/app/ai/README.md`
  - AI placeholder documentation.
- Create: `backend/tests/test_api.py`
  - API and service tests.
- Create: `data/seeds/direction_definitions.json`
  - 9 direction definitions.
- Create: `data/seeds/question_bank.json`
  - 25 questions and weighted options.
- Create: `data/seeds/jd_seed.json`
  - First 20-30 manually curated JD samples.
- Create: `scripts/import_jds.py`
  - Imports seeds into SQLite.
- Create: `scripts/analyze_keywords.py`
  - Produces simple keyword frequency summaries.
- Create: `docs/jd-data-standard.md`
  - Rules for adding JD seed data.
- Create: `docs/direction-definitions.md`
  - Human-readable 9 direction definitions.
- Create: `frontend/`
  - Move/copy current static assets into a frontend folder.
- Create: `frontend/js/api.js`
  - API client helpers.
- Create: `frontend/js/app.js`
  - App state and event wiring.
- Create: `frontend/js/render.js`
  - DOM rendering helpers.
- Modify: root `package.json`
  - Keep Node tests and add a frontend localhost static server script.

## Task 1: Backend Tooling And Health API

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/main.py`
- Create: `backend/tests/test_api.py`

- [ ] **Step 1: Add backend dependencies**

Create `backend/requirements.txt`:

```text
fastapi==0.136.3
uvicorn==0.48.0
pytest==9.0.3
httpx==0.28.1
pydantic==2.13.4
```

- [ ] **Step 2: Write failing health test**

Create `backend/tests/test_api.py`:

```python
from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 3: Run test to verify failure**

Run:

```bash
PYTHONPATH=. pytest backend/tests/test_api.py -q
```

Expected: FAIL because `backend.app.main` does not exist.

- [ ] **Step 4: Create FastAPI app**

Create `backend/app/main.py`:

```python
from fastapi import FastAPI


app = FastAPI(title="JD Backed Assessment API")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 5: Add package markers**

Create empty files:

```text
backend/__init__.py
backend/app/__init__.py
backend/tests/__init__.py
```

- [ ] **Step 6: Run health test**

Run:

```bash
PYTHONPATH=. pytest backend/tests/test_api.py -q
```

Expected: PASS with `1 passed`.

- [ ] **Step 7: Commit backend skeleton**

Run:

```bash
git add backend
git commit -m "feat: add FastAPI backend skeleton"
```

Expected: commit succeeds.

## Task 2: SQLite Schema And Seed Import

**Files:**
- Create: `backend/app/db.py`
- Create: `data/seeds/direction_definitions.json`
- Create: `data/seeds/question_bank.json`
- Create: `data/seeds/jd_seed.json`
- Create: `scripts/import_jds.py`
- Modify: `backend/tests/test_api.py`

- [ ] **Step 1: Add schema/import tests**

Append to `backend/tests/test_api.py`:

```python
import sqlite3
from pathlib import Path

from backend.app.db import initialize_database
from scripts.import_jds import import_seed_data


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
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
PYTHONPATH=. pytest backend/tests/test_api.py -q
```

Expected: FAIL because `backend.app.db` and `scripts.import_jds` do not exist.

- [ ] **Step 3: Implement SQLite schema**

Create `backend/app/db.py`:

```python
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
  source_type TEXT NOT NULL,
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
  mapped_direction TEXT NOT NULL,
  secondary_directions TEXT NOT NULL,
  task_keywords TEXT NOT NULL,
  capability_keywords TEXT NOT NULL,
  tool_keywords TEXT NOT NULL,
  jargon_terms TEXT NOT NULL,
  notes TEXT NOT NULL
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
  question_type TEXT NOT NULL,
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
  main_direction TEXT NOT NULL,
  supporting_directions TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def connect(db_path: Path | str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database(db_path: Path | str) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as conn:
        conn.executescript(SCHEMA_SQL)


def to_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def from_json(value: str) -> Any:
    return json.loads(value)
```

- [ ] **Step 4: Create direction seed file**

Create `data/seeds/direction_definitions.json` with 9 records. Use this exact shape for every record:

```json
[
  {
    "key": "ux",
    "label": "用户体验型",
    "short_label": "C 端产品",
    "animal": "小猫",
    "avatar_src": "./assets/avatars/ux-cat.png",
    "plain_summary": "适合从真实使用场景里发现问题，把功能改得更顺手、更容易理解。",
    "competency_definition": "关注用户完成任务时的路径、理解成本、情绪反馈和体验阻力。",
    "typical_tasks": ["体验走查", "用户反馈整理", "竞品功能拆解", "原型优化"],
    "common_capabilities": ["用户视角", "细节观察", "问题表达", "基础原型"],
    "suitable_roles": ["C 端产品实习生", "用户体验产品实习生", "用户研究实习生"],
    "risk_notes": ["容易只停留在主观感受，需要补充证据和优先级判断。"],
    "portfolio_guidance": "做一个常用 App 的体验优化项目，展示问题发现、证据和改版方案。"
  },
  {
    "key": "process",
    "label": "业务流程型",
    "short_label": "B 端产品",
    "animal": "小海狸",
    "avatar_src": "./assets/avatars/process-beaver.png",
    "plain_summary": "适合梳理角色、规则和步骤，把复杂协作变成更清楚的流程。",
    "competency_definition": "关注业务角色、状态流转、权限规则、异常处理和协作效率。",
    "typical_tasks": ["流程图梳理", "后台需求整理", "规则设计", "异常场景补充"],
    "common_capabilities": ["结构化思维", "流程意识", "规则表达", "耐心拆解"],
    "suitable_roles": ["B 端产品实习生", "后台产品实习生", "平台运营实习生"],
    "risk_notes": ["容易表达抽象，需要结合具体业务场景说明价值。"],
    "portfolio_guidance": "设计一个校园事务线上处理流程，展示角色、状态和异常处理。"
  },
  {
    "key": "growth",
    "label": "数据增长型",
    "short_label": "增长运营",
    "animal": "小狐狸",
    "avatar_src": "./assets/avatars/growth-fox.png",
    "plain_summary": "适合观察每一步有多少人留下来，用数字判断哪里最值得先改。",
    "competency_definition": "关注指标变化、关键路径、转化、留存和实验验证。",
    "typical_tasks": ["数据复盘", "路径分析", "效果对比", "增长实验设计"],
    "common_capabilities": ["指标意识", "表格能力", "假设验证", "结果复盘"],
    "suitable_roles": ["增长产品实习生", "增长运营实习生", "数据运营实习生"],
    "risk_notes": ["容易只看数字，需要补充用户原因和业务背景。"],
    "portfolio_guidance": "分析一个报名或关注路径的流失问题，提出可验证的改进方案。"
  },
  {
    "key": "content",
    "label": "内容表达型",
    "short_label": "内容运营",
    "animal": "小鹦鹉",
    "avatar_src": "./assets/avatars/content-parrot.png",
    "plain_summary": "适合把信息整理成用户愿意点开、看懂、收藏或转发的内容。",
    "competency_definition": "关注选题、文案、平台表达、内容结构和传播反馈。",
    "typical_tasks": ["选题策划", "标题优化", "内容排期", "内容数据复盘"],
    "common_capabilities": ["表达能力", "热点敏感", "内容结构", "平台理解"],
    "suitable_roles": ["内容运营实习生", "新媒体运营实习生", "内容产品实习生"],
    "risk_notes": ["容易凭感觉判断内容好坏，需要补数据反馈。"],
    "portfolio_guidance": "搭建一个面向大学生求职的内容账号方案，展示选题、样稿和复盘指标。"
  },
  {
    "key": "campaign",
    "label": "活动转化型",
    "short_label": "活动运营",
    "animal": "小兔子",
    "avatar_src": "./assets/avatars/campaign-rabbit.png",
    "plain_summary": "适合把目标变成具体活动，让更多人愿意参与并完成关键动作。",
    "competency_definition": "关注活动目标、参与路径、触达节奏、资源协调和结果复盘。",
    "typical_tasks": ["活动策划", "报名提升", "物料准备", "活动复盘"],
    "common_capabilities": ["执行力", "转化意识", "协调能力", "风险预案"],
    "suitable_roles": ["活动运营实习生", "校园运营实习生", "营销运营实习生"],
    "risk_notes": ["容易只写创意，需要补完整路径、资源和复盘指标。"],
    "portfolio_guidance": "策划一场线上打卡或资料领取活动，展示目标、路径、执行和复盘。"
  },
  {
    "key": "community",
    "label": "社群关系型",
    "short_label": "用户运营",
    "animal": "小水獭",
    "avatar_src": "./assets/avatars/community-otter.png",
    "plain_summary": "适合维护用户关系，让用户愿意留下来、互动起来、持续参与。",
    "competency_definition": "关注用户关系、社群氛围、互动机制、召回和长期留存。",
    "typical_tasks": ["社群维护", "用户互动", "用户召回", "活动通知"],
    "common_capabilities": ["沟通耐心", "氛围观察", "用户陪伴", "机制设计"],
    "suitable_roles": ["社群运营实习生", "用户运营实习生", "私域运营实习生"],
    "risk_notes": ["容易变成日常闲聊，需要沉淀机制和指标。"],
    "portfolio_guidance": "设计一个求职互助社群运营方案，展示入群、互动、召回和留存设计。"
  },
  {
    "key": "research",
    "label": "用户研究型",
    "short_label": "需求洞察",
    "animal": "小鹿",
    "avatar_src": "./assets/avatars/research-deer.png",
    "plain_summary": "适合通过聊天、观察和整理反馈，弄清楚真实用户到底需要什么。",
    "competency_definition": "关注用户访谈、问卷、反馈归纳、需求洞察和问题验证。",
    "typical_tasks": ["用户访谈", "问卷整理", "反馈归类", "洞察报告"],
    "common_capabilities": ["共情能力", "提问能力", "归纳能力", "客观记录"],
    "suitable_roles": ["用户研究实习生", "产品调研实习生", "用户运营实习生"],
    "risk_notes": ["容易只收集故事，需要把反馈归纳成可行动的问题。"],
    "portfolio_guidance": "完成一次小型用户访谈项目，展示问题设计、访谈记录和洞察结论。"
  },
  {
    "key": "strategy",
    "label": "商业分析型",
    "short_label": "策略运营",
    "animal": "小猫头鹰",
    "avatar_src": "./assets/avatars/strategy-owl.png",
    "plain_summary": "适合把目标、资源、竞品和结果放在一起看，判断下一步怎么做更划算。",
    "competency_definition": "关注业务目标、竞品对比、优先级判断、商业模式和策略取舍。",
    "typical_tasks": ["竞品分析", "策略拆解", "优先级判断", "业务复盘"],
    "common_capabilities": ["逻辑判断", "全局视角", "信息整合", "结构化表达"],
    "suitable_roles": ["策略运营实习生", "商业分析实习生", "策略产品实习生"],
    "risk_notes": ["容易停留在宏观判断，需要补数据和落地动作。"],
    "portfolio_guidance": "做一个竞品和机会判断分析项目，展示判断框架和行动建议。"
  },
  {
    "key": "project",
    "label": "项目推进型",
    "short_label": "执行推进",
    "animal": "小边牧",
    "avatar_src": "./assets/avatars/project-border-collie.png",
    "plain_summary": "适合把目标拆成计划，协调不同人和资源，保证事情按时落地。",
    "competency_definition": "关注排期、分工、风险、跨方沟通和交付质量。",
    "typical_tasks": ["项目排期", "进度跟进", "跨方协调", "风险预案"],
    "common_capabilities": ["责任心", "推进力", "沟通协调", "节奏管理"],
    "suitable_roles": ["项目运营实习生", "产品运营实习生", "活动运营实习生"],
    "risk_notes": ["容易只做执行，需要补目标判断和复盘表达。"],
    "portfolio_guidance": "推进一个从计划到复盘的小项目，展示排期、协调和结果。"
  }
]
```

- [ ] **Step 5: Create question seed file**

Create `data/seeds/question_bank.json` by converting the current 25-question content from `data.js` into this shape:

```json
[
  {
    "id": "q01",
    "text": "社团招新海报发出去后，报名人数很少。你最想先做什么？",
    "question_type": "scenario",
    "basis_notes": "测试用户面对低报名问题时更倾向先做用户访谈、路径数据、内容表达、体验流程还是项目推进。",
    "related_jd_tasks": ["用户反馈", "数据复盘", "活动策划", "内容优化"],
    "options": [
      {
        "id": "q01_a1",
        "text": "找几个没报名的同学问问，他们卡在了哪里",
        "weights": [
          { "direction": "research", "value": 2 },
          { "direction": "campaign", "value": 1 }
        ]
      }
    ]
  }
]
```

All 25 questions must be included. Each question must have 4-6 options. Each option must have 1-2 weights.

- [ ] **Step 6: Create JD seed file**

Create `data/seeds/jd_seed.json` with at least 20 records. Each record must use this shape:

```json
[
  {
    "id": "jd_001",
    "company": "样例公司",
    "role_title": "产品运营实习生",
    "role_category": "产品运营",
    "source_url": "manual://seed/jd_001",
    "source_type": "manual_note",
    "location": "不限",
    "employment_type": "实习",
    "raw_text": "负责用户反馈整理、活动执行、数据复盘等工作。",
    "responsibilities_text": "负责用户反馈整理、活动执行、数据复盘。",
    "requirements_text": "具备沟通能力、数据意识和执行力。",
    "collected_at": "2026-05-28",
    "annotation": {
      "mapped_direction": "campaign",
      "secondary_directions": ["growth", "community"],
      "task_keywords": ["活动执行", "用户反馈", "数据复盘"],
      "capability_keywords": ["沟通能力", "数据意识", "执行力"],
      "tool_keywords": ["Excel"],
      "jargon_terms": ["复盘", "转化"],
      "notes": "Seed record for schema validation."
    }
  }
]
```

The 20 records must cover all 9 directions at least once.

- [ ] **Step 7: Implement import script**

Create `scripts/import_jds.py`:

```python
import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any

from backend.app.db import initialize_database, to_json


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def import_seed_data(db_path: Path, seed_dir: Path) -> None:
    initialize_database(db_path)
    directions = load_json(seed_dir / "direction_definitions.json")
    questions = load_json(seed_dir / "question_bank.json")
    jds = load_json(seed_dir / "jd_seed.json")

    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM question_options")
        conn.execute("DELETE FROM questions")
        conn.execute("DELETE FROM jd_annotations")
        conn.execute("DELETE FROM jd_sources")
        conn.execute("DELETE FROM directions")

        for direction in directions:
            conn.execute(
                """
                INSERT INTO directions (
                  key, label, short_label, animal, avatar_src, plain_summary,
                  competency_definition, typical_tasks, common_capabilities,
                  suitable_roles, risk_notes, portfolio_guidance
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    direction["key"],
                    direction["label"],
                    direction["short_label"],
                    direction["animal"],
                    direction["avatar_src"],
                    direction["plain_summary"],
                    direction["competency_definition"],
                    to_json(direction["typical_tasks"]),
                    to_json(direction["common_capabilities"]),
                    to_json(direction["suitable_roles"]),
                    to_json(direction["risk_notes"]),
                    direction["portfolio_guidance"],
                ),
            )

        for question in questions:
            conn.execute(
                """
                INSERT INTO questions (
                  id, text, question_type, basis_notes, related_jd_tasks
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    question["id"],
                    question["text"],
                    question["question_type"],
                    question["basis_notes"],
                    to_json(question["related_jd_tasks"]),
                ),
            )
            for option in question["options"]:
                conn.execute(
                    """
                    INSERT INTO question_options (id, question_id, text, weights)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        option["id"],
                        question["id"],
                        option["text"],
                        to_json(option["weights"]),
                    ),
                )

        for jd in jds:
            conn.execute(
                """
                INSERT INTO jd_sources (
                  id, company, role_title, role_category, source_url, source_type,
                  location, employment_type, raw_text, responsibilities_text,
                  requirements_text, collected_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    jd["id"],
                    jd["company"],
                    jd["role_title"],
                    jd["role_category"],
                    jd["source_url"],
                    jd["source_type"],
                    jd["location"],
                    jd["employment_type"],
                    jd["raw_text"],
                    jd["responsibilities_text"],
                    jd["requirements_text"],
                    jd["collected_at"],
                ),
            )
            annotation = jd["annotation"]
            conn.execute(
                """
                INSERT INTO jd_annotations (
                  id, jd_id, mapped_direction, secondary_directions,
                  task_keywords, capability_keywords, tool_keywords,
                  jargon_terms, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"{jd['id']}_annotation",
                    jd["id"],
                    annotation["mapped_direction"],
                    to_json(annotation["secondary_directions"]),
                    to_json(annotation["task_keywords"]),
                    to_json(annotation["capability_keywords"]),
                    to_json(annotation["tool_keywords"]),
                    to_json(annotation["jargon_terms"]),
                    annotation["notes"],
                ),
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/app.db")
    parser.add_argument("--seed-dir", default="data/seeds")
    args = parser.parse_args()
    import_seed_data(Path(args.db), Path(args.seed_dir))


if __name__ == "__main__":
    main()
```

- [ ] **Step 8: Run import tests**

Run:

```bash
PYTHONPATH=. pytest backend/tests/test_api.py -q
```

Expected: PASS with 3 tests.

- [ ] **Step 9: Commit schema and seeds**

Run:

```bash
git add backend/app/db.py backend/tests/test_api.py data/seeds scripts/import_jds.py
git commit -m "feat: add SQLite seed import"
```

Expected: commit succeeds.

## Task 3: Repository Layer And Evidence Summary

**Files:**
- Create: `backend/app/repositories/jd_repository.py`
- Create: `backend/app/services/evidence_service.py`
- Create: `scripts/analyze_keywords.py`
- Modify: `backend/tests/test_api.py`

- [ ] **Step 1: Add repository/evidence tests**

Append:

```python
from backend.app.repositories.jd_repository import JDRepository
from backend.app.services.evidence_service import build_evidence_summary


def test_repository_loads_directions_questions_and_evidence(tmp_path: Path):
    db_path = tmp_path / "app.db"
    initialize_database(db_path)
    import_seed_data(db_path, Path("data/seeds"))
    repository = JDRepository(db_path)

    assert len(repository.list_directions()) == 9
    assert len(repository.list_questions()) == 25

    evidence = build_evidence_summary(repository, "growth")
    assert evidence["jd_count"] >= 1
    assert evidence["high_frequency_tasks"]
    assert evidence["high_frequency_capabilities"]
    assert evidence["representative_roles"]
    assert evidence["source_type_summary"]
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
PYTHONPATH=. pytest backend/tests/test_api.py -q
```

Expected: FAIL because repository and evidence service do not exist.

- [ ] **Step 3: Implement repository**

Create `backend/app/repositories/jd_repository.py`:

```python
from collections import Counter
from pathlib import Path
from typing import Any

from backend.app.db import connect, from_json


class JDRepository:
    def __init__(self, db_path: Path | str):
        self.db_path = Path(db_path)

    def list_directions(self) -> list[dict[str, Any]]:
        with connect(self.db_path) as conn:
            rows = conn.execute("SELECT * FROM directions ORDER BY key").fetchall()
        return [self._direction_from_row(row) for row in rows]

    def get_direction(self, key: str) -> dict[str, Any] | None:
        with connect(self.db_path) as conn:
            row = conn.execute("SELECT * FROM directions WHERE key = ?", (key,)).fetchone()
        return self._direction_from_row(row) if row else None

    def list_questions(self) -> list[dict[str, Any]]:
        with connect(self.db_path) as conn:
            questions = conn.execute("SELECT * FROM questions ORDER BY id").fetchall()
            options = conn.execute("SELECT * FROM question_options ORDER BY id").fetchall()

        options_by_question: dict[str, list[dict[str, Any]]] = {}
        for option in options:
            options_by_question.setdefault(option["question_id"], []).append(
                {
                    "id": option["id"],
                    "text": option["text"],
                    "weights": from_json(option["weights"]),
                }
            )

        return [
            {
                "id": question["id"],
                "text": question["text"],
                "question_type": question["question_type"],
                "basis_notes": question["basis_notes"],
                "related_jd_tasks": from_json(question["related_jd_tasks"]),
                "options": options_by_question.get(question["id"], []),
            }
            for question in questions
        ]

    def list_jd_annotations_for_direction(self, direction_key: str) -> list[dict[str, Any]]:
        with connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT js.company, js.role_title, js.source_type, ja.*
                FROM jd_annotations ja
                JOIN jd_sources js ON js.id = ja.jd_id
                WHERE ja.mapped_direction = ?
                """,
                (direction_key,),
            ).fetchall()

        return [
            {
                "company": row["company"],
                "role_title": row["role_title"],
                "source_type": row["source_type"],
                "task_keywords": from_json(row["task_keywords"]),
                "capability_keywords": from_json(row["capability_keywords"]),
                "secondary_directions": from_json(row["secondary_directions"]),
            }
            for row in rows
        ]

    def _direction_from_row(self, row: Any) -> dict[str, Any]:
        return {
            "key": row["key"],
            "label": row["label"],
            "short_label": row["short_label"],
            "animal": row["animal"],
            "avatar_src": row["avatar_src"],
            "plain_summary": row["plain_summary"],
            "competency_definition": row["competency_definition"],
            "typical_tasks": from_json(row["typical_tasks"]),
            "common_capabilities": from_json(row["common_capabilities"]),
            "suitable_roles": from_json(row["suitable_roles"]),
            "risk_notes": from_json(row["risk_notes"]),
            "portfolio_guidance": row["portfolio_guidance"],
        }
```

- [ ] **Step 4: Implement evidence service**

Create `backend/app/services/evidence_service.py`:

```python
from collections import Counter
from typing import Any

from backend.app.repositories.jd_repository import JDRepository


def most_common(values: list[str], limit: int = 6) -> list[str]:
    return [value for value, _ in Counter(values).most_common(limit)]


def build_evidence_summary(
    repository: JDRepository,
    direction_key: str,
) -> dict[str, Any]:
    annotations = repository.list_jd_annotations_for_direction(direction_key)
    task_values = [
        keyword
        for annotation in annotations
        for keyword in annotation["task_keywords"]
    ]
    capability_values = [
        keyword
        for annotation in annotations
        for keyword in annotation["capability_keywords"]
    ]
    source_counts = Counter(annotation["source_type"] for annotation in annotations)

    return {
        "jd_count": len(annotations),
        "high_frequency_tasks": most_common(task_values),
        "high_frequency_capabilities": most_common(capability_values),
        "representative_roles": most_common(
            [annotation["role_title"] for annotation in annotations],
            limit=5,
        ),
        "source_type_summary": dict(source_counts),
    }
```

- [ ] **Step 5: Implement keyword analysis script**

Create `scripts/analyze_keywords.py`:

```python
import argparse
import json
from pathlib import Path

from backend.app.repositories.jd_repository import JDRepository
from backend.app.services.evidence_service import build_evidence_summary


def analyze(db_path: Path) -> dict[str, object]:
    repository = JDRepository(db_path)
    return {
        direction["key"]: build_evidence_summary(repository, direction["key"])
        for direction in repository.list_directions()
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/app.db")
    args = parser.parse_args()
    print(json.dumps(analyze(Path(args.db)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run tests**

Run:

```bash
PYTHONPATH=. pytest backend/tests/test_api.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit repository/evidence layer**

Run:

```bash
git add backend/app/repositories backend/app/services scripts/analyze_keywords.py backend/tests/test_api.py
git commit -m "feat: add JD evidence repository"
```

Expected: commit succeeds.

## Task 4: Assessment Service

**Files:**
- Create: `backend/app/services/assessment_service.py`
- Modify: `backend/tests/test_api.py`

- [ ] **Step 1: Add assessment service tests**

Append:

```python
from backend.app.services.assessment_service import score_answers, select_result


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
    assert set(scores.keys()) == {direction["key"] for direction in repository.list_directions()}
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
PYTHONPATH=. pytest backend/tests/test_api.py -q
```

Expected: FAIL because assessment service does not exist.

- [ ] **Step 3: Implement assessment service**

Create `backend/app/services/assessment_service.py`:

```python
from typing import Any


def score_answers(
    answers: dict[str, int],
    questions: list[dict[str, Any]],
    directions: list[dict[str, Any]],
) -> dict[str, int]:
    scores = {direction["key"]: 0 for direction in directions}

    for question in questions:
        answer_index = answers.get(question["id"])
        if not isinstance(answer_index, int):
            continue
        if answer_index < 0 or answer_index >= len(question["options"]):
            continue
        option = question["options"][answer_index]
        for weight in option["weights"]:
            direction = weight["direction"]
            value = weight["value"]
            if direction in scores and isinstance(value, int):
                scores[direction] += value

    return scores


def normalize_scores(scores: dict[str, int]) -> dict[str, int]:
    if not scores:
        return {}
    values = list(scores.values())
    low = min(values)
    high = max(values)
    if high == low:
        return {key: 0 for key in scores}
    return {
        key: round(((value - low) / (high - low)) * 100)
        for key, value in scores.items()
    }


def select_result(scores: dict[str, int]) -> dict[str, Any]:
    ranked = [
        {"key": key, "value": value}
        for key, value in sorted(scores.items(), key=lambda item: item[1], reverse=True)
    ]
    main = ranked[0]["key"]
    supporting = [ranked[1]["key"]]
    if len(ranked) > 2:
        second = ranked[1]["value"]
        third = ranked[2]["value"]
        if third == second or abs(third - second) <= 1:
            supporting.append(ranked[2]["key"])

    top = ranked[0]["value"]
    fifth = ranked[4]["value"] if len(ranked) > 4 else top
    return {
        "main_direction": main,
        "supporting_directions": supporting[:2],
        "ranked": ranked,
        "normalized_scores": normalize_scores(scores),
        "is_multi_sided": top - fifth <= 3,
    }
```

- [ ] **Step 4: Run tests**

Run:

```bash
PYTHONPATH=. pytest backend/tests/test_api.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit assessment service**

Run:

```bash
git add backend/app/services/assessment_service.py backend/tests/test_api.py
git commit -m "feat: add backend assessment scoring"
```

Expected: commit succeeds.

## Task 5: API Endpoints

**Files:**
- Create: `backend/app/schemas.py`
- Modify: `backend/app/main.py`
- Modify: `backend/tests/test_api.py`

- [ ] **Step 1: Add API endpoint tests**

Append:

```python
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
    assert payload["main_direction"]
    assert payload["supporting_directions"]
    assert payload["evidence"]["jd_count"] >= 1


def test_ai_placeholder():
    response = client.post("/api/ai/explain", json={})
    assert response.status_code == 200
    assert response.json()["available"] is False
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
PYTHONPATH=. pytest backend/tests/test_api.py -q
```

Expected: FAIL because endpoints do not exist.

- [ ] **Step 3: Add schemas**

Create `backend/app/schemas.py`:

```python
from pydantic import BaseModel


class AssessmentSubmitRequest(BaseModel):
    answers: dict[str, int]
```

- [ ] **Step 4: Implement API endpoints**

Replace `backend/app/main.py` with:

```python
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI

from backend.app.repositories.jd_repository import JDRepository
from backend.app.schemas import AssessmentSubmitRequest
from backend.app.services.assessment_service import score_answers, select_result
from backend.app.services.evidence_service import build_evidence_summary


app = FastAPI(title="JD Backed Assessment API")


def get_db_path() -> Path:
    return Path(os.environ.get("ASSESSMENT_DB_PATH", "data/app.db"))


def get_repository() -> JDRepository:
    return JDRepository(get_db_path())


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/directions")
def list_directions() -> list[dict[str, Any]]:
    return get_repository().list_directions()


@app.get("/api/questions")
def list_questions() -> list[dict[str, Any]]:
    questions = get_repository().list_questions()
    public_questions = []
    for question in questions:
        public_questions.append(
            {
                "id": question["id"],
                "text": question["text"],
                "question_type": question["question_type"],
                "options": [
                    {"id": option["id"], "text": option["text"]}
                    for option in question["options"]
                ],
            }
        )
    return public_questions


@app.post("/api/assessment/submit")
def submit_assessment(request: AssessmentSubmitRequest) -> dict[str, Any]:
    repository = get_repository()
    directions = repository.list_directions()
    questions = repository.list_questions()
    scores = score_answers(request.answers, questions, directions)
    selected = select_result(scores)
    main_direction = repository.get_direction(selected["main_direction"])
    support_key = selected["supporting_directions"][0]
    support_direction = repository.get_direction(support_key)
    evidence = build_evidence_summary(repository, selected["main_direction"])

    return {
        "main_direction": selected["main_direction"],
        "supporting_directions": selected["supporting_directions"],
        "scores": selected["normalized_scores"],
        "is_multi_sided": selected["is_multi_sided"],
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
    return build_evidence_summary(get_repository(), direction_key)


@app.post("/api/ai/explain")
def ai_explain_placeholder() -> dict[str, object]:
    return {
        "available": False,
        "message": "AI explanation is reserved for a later phase.",
    }
```

- [ ] **Step 5: Run tests**

Run:

```bash
PYTHONPATH=. pytest backend/tests/test_api.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit API endpoints**

Run:

```bash
git add backend/app/main.py backend/app/schemas.py backend/tests/test_api.py
git commit -m "feat: expose assessment API"
```

Expected: commit succeeds.

## Task 6: AI Placeholder Documentation

**Files:**
- Create: `backend/app/ai/prompts.py`
- Create: `backend/app/ai/README.md`
- Create: `backend/app/ai/__init__.py`

- [ ] **Step 1: Add prompt template module**

Create `backend/app/ai/prompts.py`:

```python
RESULT_EXPLANATION_PROMPT_TEMPLATE = """
You are helping a beginner student understand an internet internship direction result.

Inputs:
- User answers: {answers}
- Score distribution: {scores}
- Main direction: {main_direction}
- Supporting directions: {supporting_directions}
- JD evidence: {jd_evidence}
- Portfolio suggestion: {portfolio_suggestion}

Task:
Explain the result using the JD evidence. Do not invent sources. Keep the tone practical and beginner-friendly.
"""
```

- [ ] **Step 2: Add AI README**

Create `backend/app/ai/README.md`:

```markdown
# User-Facing AI Placeholder

User-facing AI answers remain a placeholder and do not call a model.

Future user-facing AI inputs:

- user answers
- score distribution
- main and supporting directions
- JD evidence summary
- portfolio suggestion
- optional target role or target JD

Rules for future implementation:

- Do not invent JD sources.
- Use retrieved JD evidence as grounding.
- Explain jargon in beginner-friendly language.
- Keep resume rewriting out of Phase 1.
```

- [ ] **Step 3: Add package marker**

Create empty `backend/app/ai/__init__.py`.

- [ ] **Step 4: Commit AI placeholder**

Run:

```bash
git add backend/app/ai
git commit -m "docs: add AI placeholder"
```

Expected: commit succeeds.

## Task 7: Frontend Migration To API

**Files:**
- Create: `frontend/index.html`
- Create: `frontend/styles.css`
- Create: `frontend/assets/avatars/*`
- Create: `frontend/js/api.js`
- Create: `frontend/js/app.js`
- Create: `frontend/js/render.js`
- Modify: root `package.json`

- [ ] **Step 1: Copy current frontend assets**

Copy current static files into `frontend/`:

```bash
mkdir -p frontend/js frontend/assets
cp index.html frontend/index.html
cp styles.css frontend/styles.css
cp -R assets/avatars frontend/assets/avatars
```

- [ ] **Step 2: Create API client**

Create `frontend/js/api.js`:

```js
const API_BASE = "http://127.0.0.1:8000";

export async function fetchDirections() {
  const response = await fetch(`${API_BASE}/api/directions`);
  if (!response.ok) throw new Error("方向接口暂时不可用");
  return response.json();
}

export async function fetchQuestions() {
  const response = await fetch(`${API_BASE}/api/questions`);
  if (!response.ok) throw new Error("题目接口暂时不可用");
  return response.json();
}

export async function submitAssessment(answers) {
  const response = await fetch(`${API_BASE}/api/assessment/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answers })
  });
  if (!response.ok) throw new Error("测评接口暂时不可用");
  return response.json();
}
```

- [ ] **Step 3: Create render helpers**

Create `frontend/js/render.js` with exported helpers:

```js
export function setText(id, value) {
  document.getElementById(id).textContent = value;
}

export function clear(node) {
  node.textContent = "";
}

export function renderApiError(message) {
  const optionsList = document.getElementById("optionsList");
  optionsList.textContent = message;
}
```

- [ ] **Step 4: Create app entry**

Create `frontend/js/app.js`:

```js
import { fetchDirections, fetchQuestions, submitAssessment } from "./api.js";
import { clear, renderApiError, setText } from "./render.js";

let directions = {};
let questions = [];
let currentIndex = 0;
let answersByQuestionId = {};
let latestResult = null;
let advanceTimer = null;

const screens = {
  home: document.getElementById("home"),
  quiz: document.getElementById("quiz"),
  loading: document.getElementById("loading"),
  result: document.getElementById("result")
};

const questionMeta = document.getElementById("questionMeta");
const progressBar = document.getElementById("progressBar");
const questionText = document.getElementById("questionText");
const optionsList = document.getElementById("optionsList");
const prevBtn = document.getElementById("prevBtn");

function showScreen(name) {
  Object.values(screens).forEach((screen) => {
    screen.classList.toggle("is-active", screen === screens[name]);
  });
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function clearAdvanceTimer() {
  if (!advanceTimer) return;
  window.clearTimeout(advanceTimer);
  advanceTimer = null;
}

async function loadInitialData() {
  const [directionList, questionList] = await Promise.all([
    fetchDirections(),
    fetchQuestions()
  ]);
  directions = Object.fromEntries(directionList.map((direction) => [direction.key, direction]));
  questions = questionList;
}

function renderQuestion() {
  const question = questions[currentIndex];
  if (!question) {
    renderApiError("题目暂时不可用，请确认后端服务已启动。");
    return;
  }

  const selectedAnswer = answersByQuestionId[question.id];
  questionMeta.textContent = `第 ${currentIndex + 1} / ${questions.length} 题`;
  progressBar.style.width = `${((currentIndex + 1) / questions.length) * 100}%`;
  questionText.textContent = question.text;
  prevBtn.disabled = currentIndex === 0;
  clear(optionsList);

  question.options.forEach((option, optionIndex) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "option-btn";
    button.textContent = option.text;
    button.classList.toggle("is-selected", selectedAnswer === optionIndex);
    button.addEventListener("click", () => selectAnswer(question.id, optionIndex));
    optionsList.appendChild(button);
  });
}

function selectAnswer(questionId, optionIndex) {
  clearAdvanceTimer();
  answersByQuestionId[questionId] = optionIndex;
  renderQuestion();
  advanceTimer = window.setTimeout(async () => {
    advanceTimer = null;
    if (currentIndex < questions.length - 1) {
      currentIndex += 1;
      renderQuestion();
      return;
    }
    await showLoadingThenResult();
  }, 180);
}

async function showLoadingThenResult() {
  showScreen("loading");
  latestResult = await submitAssessment(answersByQuestionId);
  renderResult(latestResult);
  showScreen("result");
}

function renderResult(payload) {
  const direction = directions[payload.main_direction];
  renderAvatar(direction);
  setText("resultTitle", payload.result.title);
  setText("resultSummary", payload.result.summary);
  setText(
    "multiNote",
    payload.is_multi_sided
      ? "你的结果比较多面，建议先用一个小项目验证主方向，再把辅助方向做成加分点。"
      : "你的主方向比较清晰，可以先围绕这个方向做作品集和投递关键词准备。"
  );
  setText("projectIdea", payload.result.portfolio_suggestion);
  renderSupporting(payload.supporting_directions);
  renderScoreBars(payload.scores);
  renderRouteSteps(payload.result.route_steps);
  renderEvidence(payload.evidence);
}

function renderAvatar(direction) {
  const avatar = document.getElementById("avatarBadge");
  clear(avatar);
  const sticker = document.createElement("div");
  sticker.className = `animal-sticker animal-${direction.key}`;
  const image = document.createElement("img");
  image.src = direction.avatar_src.replace("./assets", "./assets");
  image.alt = "";
  image.className = "avatar-image";
  sticker.appendChild(image);
  avatar.appendChild(sticker);
}

function renderSupporting(keys) {
  const container = document.getElementById("supportingDirections");
  clear(container);
  keys.forEach((key) => {
    const direction = directions[key];
    const item = document.createElement("article");
    item.className = "support-item";
    const title = document.createElement("h3");
    const summary = document.createElement("p");
    title.textContent = direction.label;
    summary.textContent = direction.plain_summary;
    item.append(title, summary);
    container.appendChild(item);
  });
}

function renderScoreBars(scores) {
  const container = document.getElementById("scoreBars");
  clear(container);
  Object.entries(scores)
    .sort((a, b) => b[1] - a[1])
    .forEach(([key, value]) => {
      const row = document.createElement("div");
      const label = document.createElement("span");
      const track = document.createElement("div");
      const fill = document.createElement("div");
      const number = document.createElement("strong");
      row.className = "score-row";
      label.textContent = directions[key].short_label;
      track.className = "score-track";
      fill.className = "score-fill";
      fill.style.width = `${value}%`;
      number.textContent = String(value);
      track.appendChild(fill);
      row.append(label, track, number);
      container.appendChild(row);
    });
}

function renderRouteSteps(steps) {
  const container = document.getElementById("routeSteps");
  clear(container);
  steps.forEach((step, index) => {
    const item = document.createElement("article");
    const title = document.createElement("h3");
    const body = document.createElement("p");
    title.textContent = `第 ${index + 1} 步`;
    body.textContent = step;
    item.append(title, body);
    container.appendChild(item);
  });
}

function renderEvidence(evidence) {
  const keywords = document.getElementById("applicationKeywords");
  const jobs = document.getElementById("productJobs");
  const ops = document.getElementById("operationJobs");
  clear(keywords);
  clear(jobs);
  clear(ops);

  [`参考 ${evidence.jd_count} 条 JD`, ...evidence.high_frequency_capabilities].forEach((text) => {
    const chip = document.createElement("span");
    chip.textContent = text;
    keywords.appendChild(chip);
  });

  evidence.high_frequency_tasks.forEach((task) => {
    const item = document.createElement("li");
    item.textContent = task;
    jobs.appendChild(item);
  });

  evidence.representative_roles.forEach((role) => {
    const item = document.createElement("li");
    item.textContent = role;
    ops.appendChild(item);
  });
}

async function startQuiz() {
  try {
    if (!questions.length) await loadInitialData();
    currentIndex = 0;
    answersByQuestionId = {};
    latestResult = null;
    renderQuestion();
    showScreen("quiz");
  } catch (error) {
    showScreen("quiz");
    renderApiError(error.message);
  }
}

document.getElementById("startBtn").addEventListener("click", startQuiz);
document.getElementById("backHomeBtn").addEventListener("click", () => showScreen("home"));
prevBtn.addEventListener("click", () => {
  clearAdvanceTimer();
  if (currentIndex === 0) return;
  currentIndex -= 1;
  renderQuestion();
});
document.getElementById("restartBtn").addEventListener("click", startQuiz);
document.getElementById("copyBtn").addEventListener("click", async () => {
  if (!latestResult) return;
  const text = `我的实习方向定位：${latestResult.result.title}\n${latestResult.result.summary}\n作品集建议：${latestResult.result.portfolio_suggestion}`;
  try {
    await navigator.clipboard.writeText(text);
  } catch (error) {
    window.prompt("复制失败，可以手动复制这段摘要：", text);
  }
});
```

This first API-backed frontend does not need to preserve the old local jargon modal. Jargon can be restored in a later frontend polish task after evidence rendering is stable.

- [ ] **Step 5: Update frontend script tags**

In `frontend/index.html`, replace old script tags with:

```html
<script type="module" src="./js/app.js"></script>
```

- [ ] **Step 6: Add static server script**

Modify root `package.json` scripts:

```json
{
  "scripts": {
    "test": "node --test",
    "frontend": "python3 -m http.server 5173 --bind 127.0.0.1 --directory frontend"
  }
}
```

- [ ] **Step 7: Manual check**

Run backend:

```bash
PYTHONPATH=. python scripts/import_jds.py --db data/app.db --seed-dir data/seeds
PYTHONPATH=. uvicorn backend.app.main:app --reload
```

Run frontend in another terminal:

```bash
npm run frontend
```

Open:

```text
http://127.0.0.1:5173/
```

Expected:

- page loads,
- questions come from API,
- submitting quiz returns result,
- evidence summary appears on result page.

- [ ] **Step 8: Commit frontend migration**

Run:

```bash
git add frontend package.json
git commit -m "feat: migrate frontend to assessment API"
```

Expected: commit succeeds.

## Task 8: Documentation And Final Verification

**Files:**
- Create: `docs/jd-data-standard.md`
- Create: `docs/direction-definitions.md`
- Modify if needed: `README.md`

- [ ] **Step 1: Add JD data standard**

Create `docs/jd-data-standard.md`:

```markdown
# JD Data Standard

Phase 1 uses manually curated JD samples.

Required fields:

- company
- role_title
- role_category
- source_url
- source_type
- responsibilities_text
- requirements_text
- annotation.mapped_direction
- annotation.task_keywords
- annotation.capability_keywords

Source type rules:

- `official`: company recruiting site
- `recruiting_platform`: third-party recruiting page
- `manual_note`: manually entered sample or temporary note

Do not use account passwords, private posts, or logged-in-only social content.
```

- [ ] **Step 2: Add direction definitions doc**

Create `docs/direction-definitions.md` by summarizing the 9 records from `data/seeds/direction_definitions.json`.

- [ ] **Step 3: Run full verification**

Run:

```bash
npm test
PYTHONPATH=. pytest backend/tests/test_api.py -q
PYTHONPATH=. python scripts/import_jds.py --db data/app.db --seed-dir data/seeds
PYTHONPATH=. python scripts/analyze_keywords.py --db data/app.db
```

Expected:

- Node tests pass.
- Backend tests pass.
- Import script exits 0.
- Keyword analysis prints JSON with 9 direction keys.

- [ ] **Step 4: Commit docs/final polish**

Run:

```bash
git add docs data/app.db
git commit -m "docs: document JD-backed assessment MVP"
```

Expected: commit succeeds if files changed.

## Self-Review

- Spec coverage: The plan covers FastAPI, SQLite, seed import, JD model, direction definitions, question bank, scoring API, evidence API, AI placeholder, frontend API migration, and documentation.
- Deliberate exclusions: no real AI calls, no resume upload, no login, no admin UI, no crawler, no PostgreSQL, no production deployment.
- Risk: Task 2 includes large JSON seed files. The implementer should prioritize correct structure and all 9 direction coverage over perfect JD realism; real JD quality can improve in later data iterations.
- Risk: Task 7 is the broadest task. If it becomes too large during execution, split it into frontend copy/setup, API client, result rendering, and localhost integration subtasks before coding further.
