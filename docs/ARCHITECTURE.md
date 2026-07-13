# 产品/运营实习证据向导架构设计

## 1. 架构目标

本架构支持新版 V0 主流程：

```text
Step 1 用户状态分流
→ Step 2 目标岗位理解
→ Step 3 用户经历收集
→ Step 4 AI 追问与证据匹配
→ Step 5 材料输出
```

设计目标：

- 复用现有 FastAPI、SQLite、JD 证据系统和测评能力。
- 把测评从主流程降级为“用户不知道方向时”的辅助入口。
- 新增一套“证据向导”领域模型，避免继续把逻辑塞进 assessment result。
- 保持 V0 可本地运行，不强依赖账号体系和生产数据库。
- AI 能力先通过清晰服务边界接入，支持 fixture/mock 输出，避免前端被模型不稳定性绑死。

## 2. 当前系统现状

### 2.1 技术栈

- 前端：静态 HTML/CSS/JavaScript，入口为 `frontend/index.html`。
- 后端：FastAPI，入口为 `backend/app/main.py`。
- 数据库：SQLite，本地路径默认 `data/app.db`。
- 数据访问：`backend/app/repositories/jd_repository.py`。
- 业务服务：
  - `assessment_service.py`
  - `evidence_service.py`
  - `action_plan_service.py`
  - JD 采集、审核、AI 标注相关服务
- AI：当前用户侧 AI 解释仍是占位接口。

### 2.2 已有核心表

已有表来自 `backend/app/db.py`：

- `directions`
- `questions`
- `question_options`
- `assessment_runs`
- `jd_sources`
- `jd_annotations`
- `jd_ai_annotations`

这些表继续保留，用作：

- 方向测评。
- 路径 C 的目标岗位发现。
- 路径 B 的聚合岗位画像。
- Step 2 的 JD 证据支撑。

## 3. 目标模块边界

### 3.1 Frontend Wizard

职责：

- 管理 5 步向导页面状态。
- 收集用户输入。
- 调用后端 API。
- 展示证据状态和材料输出。

不负责：

- 直接计算岗位画像。
- 直接拼接 AI prompt。
- 直接判断证据强弱。

### 3.2 Wizard API

职责：

- 创建向导会话。
- 保存用户当前路径和输入。
- 串联目标岗位、经历、追问、材料输出。

建议服务模块：

- `backend/app/services/wizard_service.py`

### 3.3 Role Intelligence

职责：

- 根据用户 JD、岗位选择、测评方向或经历反推结果，生成目标岗位画像。
- 输出岗位任务、能力要求、硬门槛、可包装机会。

建议服务模块：

- `backend/app/services/role_intelligence_service.py`

数据来源：

- 用户粘贴 JD。
- `directions`
- `jd_sources`
- `jd_annotations`
- `evidence_service.build_evidence_summary`

### 3.4 Experience Evidence

职责：

- 保存用户填写的经历事实。
- 将经历事实与目标岗位能力做匹配。
- 判断证据状态。
- 生成 3-5 个 AI 追问。

建议服务模块：

- `backend/app/services/evidence_match_service.py`

### 3.5 Material Generation

职责：

- 基于目标岗位、用户经历、追问回答和证据状态生成材料。
- 输出岗位能力匹配报告、作品集结构、简历 bullet、面试讲述提纲。
- 保留“真实原始版”和“求职优化版”的边界。

建议服务模块：

- `backend/app/services/material_service.py`

### 3.6 AI Gateway

职责：

- 统一封装 AI 调用。
- 支持 fixture/mock/provider 三种模式。
- 管理 prompt version。
- 对 AI 输出做结构校验。

建议服务模块：

- `backend/app/ai/gateway.py`
- `backend/app/ai/prompts.py`

不允许：

- 前端直接调用模型。
- 服务层直接散落拼接 prompt。
- AI 输出未经结构校验直接进入结果页。

## 4. 状态流转

### 4.1 主状态

```text
created
→ target_pending
→ target_analyzed
→ experience_collected
→ followup_requested
→ evidence_matched
→ material_generated
```

### 4.2 路径进入方式

#### 路径 A：用户有 JD

```text
created
→ submit_jd
→ target_analyzed
→ experience_collected
→ followup_requested
→ material_generated
```

#### 路径 B：用户有目标岗位但没有具体 JD

```text
created
→ select_role_family
→ target_analyzed
→ experience_collected
→ followup_requested
→ material_generated
```

#### 路径 C：用户不知道方向

```text
created
→ assessment_run
→ select_recommended_role
→ target_analyzed
→ experience_collected
→ followup_requested
→ material_generated
```

#### 路径 D：用户只想包装已有经历

```text
created
→ experience_collected
→ infer_candidate_roles
→ select_inferred_role
→ target_analyzed
→ followup_requested
→ material_generated
```

## 5. 数据模型

V0 可以先用 SQLite 表存储。若为了快速原型，也可以先将部分中间状态作为 JSON 存在会话表里，但接口结构必须保持稳定。

### 5.1 wizard_sessions

用途：记录一次用户材料生成向导。

字段：

- `id TEXT PRIMARY KEY`
- `entry_path TEXT NOT NULL`
- `status TEXT NOT NULL`
- `target_role_id TEXT`
- `assessment_run_id TEXT`
- `created_at TEXT NOT NULL`
- `updated_at TEXT NOT NULL`

`entry_path` 可选值：

- `has_jd`
- `has_target_role`
- `unknown_direction`
- `package_experience`

### 5.2 target_roles

用途：记录用户本次向导使用的目标岗位。

字段：

- `id TEXT PRIMARY KEY`
- `source_type TEXT NOT NULL`
- `role_title TEXT NOT NULL`
- `role_family TEXT NOT NULL`
- `raw_jd_text TEXT NOT NULL DEFAULT ''`
- `direction_key TEXT NOT NULL DEFAULT ''`
- `evidence_summary_json TEXT NOT NULL DEFAULT '{}'`
- `confidence_json TEXT NOT NULL DEFAULT '{}'`
- `created_at TEXT NOT NULL`

`source_type` 可选值：

- `user_jd`
- `role_family`
- `assessment`
- `experience_inferred`

### 5.3 jd_analyses

用途：保存 Step 2 的岗位理解结果。

字段：

- `id TEXT PRIMARY KEY`
- `session_id TEXT NOT NULL REFERENCES wizard_sessions(id)`
- `target_role_id TEXT NOT NULL REFERENCES target_roles(id)`
- `role_tasks_json TEXT NOT NULL`
- `capability_requirements_json TEXT NOT NULL`
- `hard_constraints_json TEXT NOT NULL`
- `portfolio_opportunities_json TEXT NOT NULL`
- `priority_capabilities_json TEXT NOT NULL`
- `source_trace_json TEXT NOT NULL DEFAULT '{}'`
- `created_at TEXT NOT NULL`

### 5.4 user_experiences

用途：保存 Step 3 的用户经历事实。

字段：

- `id TEXT PRIMARY KEY`
- `session_id TEXT NOT NULL REFERENCES wizard_sessions(id)`
- `name TEXT NOT NULL`
- `experience_type TEXT NOT NULL`
- `actions_text TEXT NOT NULL`
- `outputs_text TEXT NOT NULL`
- `evidence_assets_text TEXT NOT NULL DEFAULT ''`
- `created_at TEXT NOT NULL`
- `updated_at TEXT NOT NULL`

`experience_type` 可选值：

- `coursework`
- `campus_activity`
- `competition`
- `internship`
- `content_account`
- `research`
- `data_analysis`
- `other`

### 5.5 evidence_matches

用途：保存 Step 4 的能力匹配、证据状态和追问。

字段：

- `id TEXT PRIMARY KEY`
- `session_id TEXT NOT NULL REFERENCES wizard_sessions(id)`
- `experience_id TEXT NOT NULL REFERENCES user_experiences(id)`
- `matched_capabilities_json TEXT NOT NULL`
- `evidence_gaps_json TEXT NOT NULL`
- `followup_questions_json TEXT NOT NULL`
- `answers_json TEXT NOT NULL DEFAULT '{}'`
- `evidence_status_json TEXT NOT NULL`
- `created_at TEXT NOT NULL`
- `updated_at TEXT NOT NULL`

证据状态枚举：

- `strong`
- `needs_support`
- `not_recommended`

### 5.6 material_outputs

用途：保存 Step 5 的最终材料。

字段：

- `id TEXT PRIMARY KEY`
- `session_id TEXT NOT NULL REFERENCES wizard_sessions(id)`
- `role_match_report_json TEXT NOT NULL`
- `portfolio_structure_json TEXT NOT NULL`
- `resume_bullets_json TEXT NOT NULL`
- `interview_outline_json TEXT NOT NULL`
- `evidence_status_json TEXT NOT NULL`
- `created_at TEXT NOT NULL`
- `updated_at TEXT NOT NULL`

## 6. API 设计

### 6.1 当前保留接口

继续保留：

- `GET /api/health`
- `GET /api/directions`
- `GET /api/questions`
- `POST /api/assessment/submit`
- `GET /api/evidence/{direction_key}`

### 6.2 新增向导接口

#### 创建向导会话

```text
POST /api/wizard/sessions
```

请求：

```json
{
  "entry_path": "has_jd"
}
```

响应：

```json
{
  "session_id": "wiz-xxx",
  "status": "created",
  "next_step": "target_input"
}
```

#### 路径 A：提交 JD

```text
POST /api/wizard/{session_id}/target/jd
```

请求：

```json
{
  "raw_jd_text": "...",
  "company": "",
  "role_title": "",
  "city": "",
  "source": ""
}
```

响应：`JDAnalysis`

#### 路径 B：选择目标岗位

```text
POST /api/wizard/{session_id}/target/role-family
```

请求：

```json
{
  "role_family": "content_operations",
  "filters": {
    "city": "",
    "industry": ""
  }
}
```

响应：`JDAnalysis`

#### 路径 C：使用测评结果

```text
POST /api/wizard/{session_id}/target/assessment
```

请求：

```json
{
  "assessment_run_id": "run-xxx",
  "direction_key": "content_expression"
}
```

响应：`JDAnalysis`

#### 路径 D：先提交经历

```text
POST /api/wizard/{session_id}/experience-first
```

请求：`UserExperienceInput`

响应：

```json
{
  "experience_id": "exp-xxx",
  "candidate_roles": [
    {
      "role_family": "content_operations",
      "reason": "..."
    }
  ]
}
```

#### 提交经历

```text
POST /api/wizard/{session_id}/experiences
```

请求：`UserExperienceInput`

响应：

```json
{
  "experience_id": "exp-xxx",
  "next_step": "evidence_followup"
}
```

#### 生成追问

```text
POST /api/wizard/{session_id}/evidence/followup
```

响应：

```json
{
  "match_id": "match-xxx",
  "matched_capabilities": [],
  "evidence_gaps": [],
  "followup_questions": []
}
```

#### 提交追问回答

```text
POST /api/wizard/{session_id}/evidence/answers
```

请求：

```json
{
  "match_id": "match-xxx",
  "answers": {
    "q1": "..."
  }
}
```

响应：更新后的 `EvidenceMatch`

#### 生成材料

```text
POST /api/wizard/{session_id}/materials
```

响应：`MaterialOutput`

## 7. Pydantic Schema 边界

建议新增到 `backend/app/schemas.py` 或拆到 `backend/app/schemas/wizard.py`。

核心 schema：

- `WizardSessionCreateRequest`
- `WizardSessionResponse`
- `JDTargetRequest`
- `RoleFamilyTargetRequest`
- `AssessmentTargetRequest`
- `UserExperienceInput`
- `CandidateRole`
- `JDAnalysisResponse`
- `EvidenceFollowupResponse`
- `EvidenceAnswersRequest`
- `MaterialOutputResponse`

所有请求默认 `extra="forbid"`，避免前端把未定义字段悄悄传入。

## 8. AI 服务边界

### 8.1 AI 模式

V0 支持三种模式：

- `fixture`：固定样例输出，用于开发和测试。
- `mock`：规则生成的本地输出，用于无模型环境。
- `provider`：真实模型调用，用于后续接入。

环境变量：

```text
AI_PROVIDER_MODE=fixture|mock|provider
```

### 8.2 AI 任务

AI 只负责以下任务：

- 单条 JD 拆解。
- 目标岗位画像补全。
- 经历到能力的匹配。
- 追问生成。
- 材料生成。

AI 不负责：

- 判断用户一定适合某岗位。
- 编造用户没有提供的指标。
- 把硬门槛改写成可包装能力。
- 绕过证据状态标注。

### 8.3 Prompt 版本

每类 AI 任务都需要记录 prompt version：

- `jd_analysis_v1`
- `role_profile_v1`
- `experience_match_v1`
- `followup_questions_v1`
- `material_output_v1`

AI 输出必须是结构化 JSON，并通过 schema 校验后才能返回前端。

## 9. Frontend 状态设计

前端维护一个 wizard state：

```text
sessionId
entryPath
currentStep
targetRole
jdAnalysis
experience
evidenceMatch
materialOutput
errors
loading
```

页面导航不应该依赖 DOM 隐藏多个旧 section 的临时方式长期扩展。V0 可继续静态前端，但建议将页面渲染拆成明确函数：

- `renderHome`
- `renderEntryRouting`
- `renderJdInput`
- `renderRoleFamilySelection`
- `renderAssessmentBridge`
- `renderExperienceInput`
- `renderTargetAnalysis`
- `renderEvidenceFollowup`
- `renderMaterialOutput`

## 10. 错误与空状态

### JD 输入不足

返回 422：

```json
{
  "detail": "JD 内容不足，无法判断岗位要求。"
}
```

前端提示用户补充完整 JD，或改选目标岗位方向。

### 聚合 JD 证据不足

接口仍返回岗位画像，但证据置信度为 `low`。

前端必须提示：

> 当前岗位样本较少，结论适合作为初步参考。

### 经历信息不足

Step 4 不直接生成材料，先返回追问。

### AI 输出校验失败

后端返回 503，并提示：

> AI 输出暂时无法使用，请稍后重试或切换到规则模式。

## 11. 测试策略

### 单元测试

需要覆盖：

- 路径 A JD 输入校验。
- 路径 B 岗位画像生成。
- 路径 C assessment run 到 target role 的转换。
- 路径 D experience-first 候选岗位推断。
- 证据状态枚举。
- 追问生成数量和结构。
- 材料输出结构。

### API 测试

需要覆盖完整主链路：

```text
create session
→ submit target
→ submit experience
→ generate followup
→ submit answers
→ generate materials
```

### 前端测试

当前项目已有 Node 测试。后续至少补：

- 页面路由状态测试。
- 结果页文案结构测试。
- 项目卫生测试，确保正式入口仍是 `frontend/index.html`。

## 12. 风险与决策

### 12.1 不立即引入账号体系

V0 可以用 session ID 支撑单次流程。账号、长期材料库、跨设备保存放到 V1。

### 12.2 不实时接入小红书/知乎搜索

外部案例先做后台研究库，不作为用户实时主流程依赖。

原因：

- 噪声高。
- 合规风险高。
- 输出不稳定。
- 难以测试。

### 12.3 不做完整项目工作台

V0 只生成经历包装和材料输出，不承诺平台内完成完整项目。

### 12.4 保留 SQLite

当前项目仍处于本地 MVP 阶段。SQLite 足够支撑 V0 验证；生产化再评估迁移。

## 13. 后续实施顺序

1. 创建 `TODO.md`，把开发拆成小任务。
2. 先实现数据 schema 和服务层 fixture。
3. 再实现 API。
4. 再改前端页面。
5. 最后接入真实 AI provider。

每次实现只做一个 TODO，并同步更新 PRD、DESIGN、ARCHITECTURE。
