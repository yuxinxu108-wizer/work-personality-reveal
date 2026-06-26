# 产品级改造 Issue 草案

来源：基于当前项目健康检查结果整理。  
状态：草案，尚未发布到 issue tracker。

## 推荐第一批

1. 一键可复现开发和测试环境
2. 清理项目正式入口和历史遗留文件
3. 建立产品级测评结果可信度
4. 为 JD 证据增加可信度分层

这四个完成后，项目会从“能跑的 MVP”变成“可以继续产品化的稳定底座”。

---

## Issue 1: 建立产品级测评结果可信度

状态：已完成第一版。接口现在会拒绝有效答题不足的提交，并返回结果可信度、有效答题数和结果解释。

## What to build

测评提交后，不只返回主方向、辅助方向和分数，还要返回结果可信度、缺题状态、关键得分来源和结果解释。用户应该能看懂“为什么我是这个方向”以及“这个结果有多稳定”。

## Acceptance criteria

- [ ] 空答案或明显不足答案不再直接给出确定结果。
- [ ] 结果返回包含可信度等级，例如 `high / medium / low`。
- [ ] 结果返回包含缺题数量、有效答题数量和是否达到最低答题要求。
- [ ] 结果返回包含主方向的简短解释依据。
- [ ] 前端结果页展示“结果稳定度”和简短解释。
- [ ] 后端和前端测试覆盖正常答题、缺题、低置信度场景。

## Blocked by

None - can start immediately

---

## Issue 2: 保存测评记录并支持结果复盘

状态：已完成第一版。成功提交测评后会保存匿名测评记录，并在响应里返回 `assessment_run_id`。

## What to build

每次用户提交测评时，保存一次匿名测评记录，包括 answers、scores、main direction、supporting directions、confidence 和 created_at，并在响应里返回 run id。后续可以用这些记录分析题目质量、方向分布和结果稳定性。

## Acceptance criteria

- [ ] 每次提交成功后生成唯一测评记录。
- [ ] 结果响应包含 `assessment_run_id`。
- [ ] 数据库可查询历史测评分布。
- [ ] 保存字段包含答案、原始分数、归一化分数、主方向、辅助方向、可信度和创建时间。
- [ ] 测试覆盖记录写入和字段完整性。

## Blocked by

- Issue 1: 建立产品级测评结果可信度

---

## Issue 3: 为 JD 证据增加可信度分层

状态：已完成第一版。证据 summary 现在包含样本数、建议样本阈值、来源质量分布、最近采集时间和证据可信度文案。

## What to build

JD evidence 返回样本数、样本阈值、来源质量、证据等级和更新时间。前端根据证据可信度展示不同文案，避免样本很少的方向也被包装成强结论。

## Acceptance criteria

- [ ] 每个方向返回 `evidence_confidence`。
- [ ] 证据响应包含样本数、最低建议样本数、来源质量分布和最近更新时间。
- [ ] 样本不足方向，例如 UX 只有 7 条时，前端明确提示“样本较少”。
- [ ] 样本充足方向展示更强结论文案。
- [ ] 无正式证据时，结果页不展示伪确定结论。
- [ ] 测试覆盖样本不足、样本达标、无证据三种状态。

## Blocked by

None - can start immediately

---

## Issue 4: 建立 JD 审核状态和抽查闭环

状态：已完成第一版。JD annotation 现在支持 `review_level`，可区分 `rule_generated`、`manual_reviewed`、`spot_checked`；旧的 `codex_rule_review` 数据会被自动识别为规则生成。证据 summary 会返回审核等级分布和强审核样本数量。

## What to build

JD annotation 需要区分规则生成、人工审核、抽查通过等状态。结果页强证据只使用达到正式标准的 JD，维护者可以看到哪些数据还需要抽查。

## Acceptance criteria

- [ ] JD 记录能区分规则生成、人工审核、抽查通过。
- [ ] 结果页强证据只使用达到正式标准的记录。
- [ ] 数据脚本能输出待抽查数量和各方向审核覆盖。
- [ ] 审核等级变更可重复导入，不破坏已有记录。
- [ ] 测试覆盖不同审核等级的过滤逻辑。

## Blocked by

- Issue 3: 为 JD 证据增加可信度分层

---

## Issue 5: 补齐结果页行动建议，让结果真正可执行

## What to build

基于主方向、辅助方向和 JD 高频任务，返回可展示的行动计划。结果页不再隐藏 7 天行动计划，而是给用户明确的下一步。

## Acceptance criteria

- [ ] 每个方向至少有一套 7 天行动计划。
- [ ] 行动计划能结合主方向和辅助方向生成或选择。
- [ ] 结果页稳定展示行动计划，不再因为空数组隐藏该模块。
- [ ] 行动建议引用当前方向 JD 高频任务或能力关键词。
- [ ] 测试覆盖 9 个方向都有行动计划。

## Blocked by

- Issue 1: 建立产品级测评结果可信度
- Issue 3: 为 JD 证据增加可信度分层

---

## Issue 6: 整理前端测评流程 module

## What to build

把当前前端的答题状态、接口调用、结果渲染拆成更清晰的测评流程 module，并增加前端容错。用户答题时，刷新、退出、接口错误都不应该产生混乱体验。

## Acceptance criteria

- [ ] API 地址不再写死 localhost。
- [ ] 接口失败时展示明确恢复方式。
- [ ] 答题状态和结果渲染分离。
- [ ] 测评流程有清晰的状态定义，例如 home、quiz、loading、result、error。
- [ ] 前端测试或可验证脚本覆盖开始答题、上一题、提交失败、提交成功。

## Blocked by

- Issue 1: 建立产品级测评结果可信度

---

## Issue 7: 清理项目正式入口和历史遗留文件

状态：已完成第一版。根目录旧静态入口和自动生成备份文件已清理，README 明确了正式入口。

## What to build

明确哪个目录和文件是当前正式产品入口，移除或归档旧静态版本、`.backup-*` 文件和过时文档引用。维护者不应该需要猜哪个文件才是当前版本。

## Acceptance criteria

- [ ] README 明确当前正式运行方式。
- [ ] 旧版 `index.html`、`script.js`、`data.js`、`styles.css` 不再和 `frontend/` 混淆。
- [ ] 备份文件从正式项目路径移除或归档。
- [ ] 文档不再说当前 JD 只是 manual seed samples。
- [ ] 测试和本地启动仍然通过。

## Blocked by

None - can start immediately

---

## Issue 8: 建立一键可复现开发和测试环境

状态：已完成第一版。已添加 `npm run setup`、`npm run backend:test`、`npm run verify` 等脚本；当前机器仍需用户确认后运行 `npm run setup` 安装 Python 依赖。

## What to build

提供明确的环境安装、数据库初始化、前端启动、后端启动、测试命令。新机器或新会话可以快速启动项目、运行前后端测试。

## Acceptance criteria

- [ ] 一条或少量命令可以创建 Python 环境并安装依赖。
- [ ] README 不再假设 `.venv` 已存在。
- [ ] `npm test` 和 Python 后端测试都有可复现命令。
- [ ] 当前 Python 测试缺少 `pytest` 的问题被解决。
- [ ] 数据库初始化流程清晰，不会误覆盖真实 pilot 数据。

## Blocked by

None - can start immediately

---

## Issue 9: 增加产品级部署配置

## What to build

配置环境变量、生产 API 地址、CORS 来源、健康检查和基础部署说明，让项目可以从本地 demo 推进到可部署环境。

## Acceptance criteria

- [ ] 前端 API base 可通过环境配置。
- [ ] 后端 CORS 可通过环境配置。
- [ ] 提供本地、测试、生产三类配置说明。
- [ ] 健康检查能确认数据库可用状态。
- [ ] 部署说明包含前端静态资源和后端服务的启动方式。

## Blocked by

- Issue 6: 整理前端测评流程 module
- Issue 8: 建立一键可复现开发和测试环境

---

## Issue 10: 建立产品数据质量看板

状态：已完成第一版。已添加 `npm run data:quality`，可输出每个方向的正式 JD 数、强审核样本数、审核等级分布、来源质量、最近采集时间和覆盖状态。

## What to build

输出每个方向的 JD 数量、审核等级、来源质量、最近更新时间、样本不足提醒。维护者可以用这份报告判断当前 9 个方向的数据覆盖是否足够支撑产品结论。

## Acceptance criteria

- [ ] 可一键生成数据质量报告。
- [ ] 报告列出 9 个方向的覆盖差异。
- [ ] UX、project、content 等低样本方向明确标红或标记。
- [ ] 报告包含审核等级、来源质量和最近更新时间。
- [ ] 报告结果能指导下一轮 JD 采集。

## Blocked by

- Issue 3: 为 JD 证据增加可信度分层
- Issue 4: 建立 JD 审核状态和抽查闭环

---

## 建议执行顺序

1. Issue 8: 建立一键可复现开发和测试环境
2. Issue 7: 清理项目正式入口和历史遗留文件
3. Issue 1: 建立产品级测评结果可信度
4. Issue 3: 为 JD 证据增加可信度分层
5. Issue 2: 保存测评记录并支持结果复盘
6. Issue 4: 建立 JD 审核状态和抽查闭环
7. Issue 5: 补齐结果页行动建议，让结果真正可执行
8. Issue 6: 整理前端测评流程 module
9. Issue 10: 建立产品数据质量看板
10. Issue 9: 增加产品级部署配置
