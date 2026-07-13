# 产品/运营实习证据向导 TODO

本清单从 `docs/product-prd.md`、`docs/DESIGN.md` 和 `docs/ARCHITECTURE.md` 生成。执行时一次只做一个 TODO；每次代码变更后同步更新相关文档。

## 当前原则

- 先做可本地验证的 V0，不引入账号体系。
- 先用 fixture/mock 输出跑通完整链路，再接真实 AI provider。
- 保留现有测评和 JD 证据能力，不破坏当前测试。
- 前端正式入口仍是 `frontend/index.html`。
- 每个任务都必须有明确验证命令。

## Phase 0：文档与基线

- [x] 更新 `docs/product-prd.md` 为新版产品/运营实习证据向导 PRD。
- [x] 新增 `docs/DESIGN.md`，固化首页、路径 A/B/C/D、Step 2-5 和输出状态。
- [x] 新增 `docs/ARCHITECTURE.md`，定义数据模型、API、AI 边界和状态流转。
- [ ] 运行当前基线验证，记录开始实现前的测试状态。
  - 验证：`npm test`
  - 验证：`npm run backend:test`

## Phase 1：后端数据模型与 schema

- [ ] 新增向导相关 Pydantic schema。
  - 文件：`backend/app/schemas.py` 或 `backend/app/schemas/wizard.py`
  - 包含：`WizardSessionCreateRequest`、`JDTargetRequest`、`RoleFamilyTargetRequest`、`AssessmentTargetRequest`、`UserExperienceInput`、`EvidenceAnswersRequest`
  - 验证：新增/更新 schema 单元测试，运行 `npm run backend:test`

- [ ] 在 SQLite schema 中加入向导表。
  - 文件：`backend/app/db.py`
  - 表：`wizard_sessions`、`target_roles`、`jd_analyses`、`user_experiences`、`evidence_matches`、`material_outputs`
  - 要求：支持已有数据库迁移，不破坏旧表
  - 验证：`npm run backend:test`

- [ ] 新增向导 repository。
  - 文件：`backend/app/repositories/wizard_repository.py`
  - 能力：创建 session、保存 target role、保存 JD analysis、保存 experience、保存 evidence match、保存 material output
  - 验证：新增 repository 测试，运行 `npm run backend:test`

## Phase 2：后端服务层 fixture/mock

- [ ] 新增 `wizard_service.py`。
  - 负责：创建会话、推进状态、校验路径流转
  - 验证：覆盖四种 entry path 的状态测试，运行 `npm run backend:test`

- [ ] 新增 `role_intelligence_service.py`。
  - 路径 A：从用户 JD 生成结构化岗位理解 fixture
  - 路径 B/C：基于现有 direction/JD evidence 生成聚合岗位画像
  - 路径 D：根据经历生成候选岗位方向 fixture
  - 验证：覆盖 A/B/C/D 输入，运行 `npm run backend:test`

- [ ] 新增 `evidence_match_service.py`。
  - 负责：经历事实到岗位能力的匹配、证据缺口、3-5 个追问、证据状态
  - 验证：追问数量、字段结构、证据状态枚举测试，运行 `npm run backend:test`

- [ ] 新增 `material_service.py`。
  - 负责：岗位能力匹配报告、作品集结构、简历 bullet、面试讲述提纲
  - 要求：同时输出真实原始版和求职优化版；不得生成无证据表达
  - 验证：输出结构测试，运行 `npm run backend:test`

- [ ] 新增 AI gateway 边界。
  - 文件：`backend/app/ai/gateway.py`、`backend/app/ai/prompts.py`
  - 模式：`fixture`、`mock`、`provider`
  - V0 先实现 fixture/mock，不接真实 provider
  - 验证：模式选择和结构校验测试，运行 `npm run backend:test`

## Phase 3：后端 API

- [ ] 新增创建向导会话 API。
  - 接口：`POST /api/wizard/sessions`
  - 验证：API 测试，运行 `npm run backend:test`

- [ ] 新增路径 A JD 提交 API。
  - 接口：`POST /api/wizard/{session_id}/target/jd`
  - 验证：正常 JD、空 JD、文本过短测试，运行 `npm run backend:test`

- [ ] 新增路径 B 岗位方向选择 API。
  - 接口：`POST /api/wizard/{session_id}/target/role-family`
  - 验证：可生成聚合岗位画像，运行 `npm run backend:test`

- [ ] 新增路径 C 测评结果转目标岗位 API。
  - 接口：`POST /api/wizard/{session_id}/target/assessment`
  - 验证：assessment_run_id 可关联 target role，运行 `npm run backend:test`

- [ ] 新增路径 D 经历优先 API。
  - 接口：`POST /api/wizard/{session_id}/experience-first`
  - 验证：无目标岗位时返回候选方向，运行 `npm run backend:test`

- [ ] 新增经历提交 API。
  - 接口：`POST /api/wizard/{session_id}/experiences`
  - 验证：字段校验和 session 状态更新，运行 `npm run backend:test`

- [ ] 新增证据追问 API。
  - 接口：`POST /api/wizard/{session_id}/evidence/followup`
  - 验证：返回 matched capabilities、gaps、questions，运行 `npm run backend:test`

- [ ] 新增追问回答 API。
  - 接口：`POST /api/wizard/{session_id}/evidence/answers`
  - 验证：回答后证据状态更新，运行 `npm run backend:test`

- [ ] 新增材料生成 API。
  - 接口：`POST /api/wizard/{session_id}/materials`
  - 验证：完整输出四块材料，运行 `npm run backend:test`

## Phase 4：前端信息架构与页面

- [ ] 重做首页首屏。
  - 文件：`frontend/index.html`、`frontend/styles.css`、`frontend/js/app.js`
  - 内容：新版主标题、副标题、开始准备、测评辅助入口
  - 验证：`npm test`

- [ ] 实现 Step 1 用户状态分流页。
  - 四个入口：有 JD、有目标岗位、不知道方向、只想包装经历
  - 验证：`npm test`

- [ ] 实现路径 A JD 粘贴页。
  - 包含：JD 粘贴框、可选字段、错误提示
  - 验证：`npm test`

- [ ] 实现路径 B 目标岗位选择页。
  - 包含：产品/运营岗位方向、岗位卡片、已有 JD 证据数量
  - 验证：`npm test`

- [ ] 改造路径 C 测评结果页。
  - 将测评结果转为“使用这个方向作为目标岗位”
  - 保留现有测评能力
  - 验证：`npm test`、`npm run backend:test`

- [ ] 实现路径 D 经历优先输入页。
  - 支持无目标岗位时展示候选方向
  - 验证：`npm test`

- [ ] 实现 Step 2 目标岗位理解页。
  - 四块：岗位任务、能力要求、硬门槛、可包装机会
  - 验证：`npm test`

- [ ] 实现 Step 3 用户经历输入页。
  - 只收事实，不让用户选能力标签
  - 验证：`npm test`

- [ ] 实现 Step 4 AI 追问与证据匹配页。
  - 展示经历摘要、追问、证据状态
  - 验证：`npm test`

- [ ] 实现 Step 5 材料输出页。
  - 四块输出：岗位能力匹配报告、作品集结构、简历 bullet、面试提纲
  - 每条输出显示证据状态
  - 验证：`npm test`

## Phase 5：端到端验证与收尾

- [ ] 跑通路径 A 完整链路。
  - 流程：创建 session → 粘贴 JD → 填经历 → 追问 → 输出材料
  - 验证：`npm test`、`npm run backend:test`

- [ ] 跑通路径 B 完整链路。
  - 流程：选择岗位 → 填经历 → 追问 → 输出材料
  - 验证：`npm test`、`npm run backend:test`

- [ ] 跑通路径 C 完整链路。
  - 流程：测评 → 使用方向 → 填经历 → 追问 → 输出材料
  - 验证：`npm test`、`npm run backend:test`

- [ ] 跑通路径 D 完整链路。
  - 流程：填经历 → AI 推荐方向 → 确认方向 → 追问 → 输出材料
  - 验证：`npm test`、`npm run backend:test`

- [ ] 更新 README 的产品入口与运行说明。
  - 明确正式前端入口仍是 `frontend/index.html`
  - 验证：`npm test`

- [ ] 全量本地验证。
  - 验证：`npm run verify`

## 暂不做

- [ ] 账号体系。
- [ ] 长期材料库。
- [ ] 投递管理。
- [ ] 实时小红书/知乎搜索。
- [ ] 真实 AI provider 接入。
- [ ] 生产部署。
