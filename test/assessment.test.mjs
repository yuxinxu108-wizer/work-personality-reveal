import test from "node:test";
import assert from "node:assert/strict";

import {
  assessmentQuestions,
  buildAssessmentShareText,
  buildAssessmentResult,
  directionOrder,
  directions,
} from "../src/app/assessment.js";
import { getRoleProfile, roleProfiles } from "../src/app/roleCatalog.js";
import {
  buildAiMaterialsRequest,
  buildDeepSeekChatPayload,
  normalizeAiMaterials,
} from "../src/app/aiMaterials.js";

test("assessment imports all 25 questions from the existing direction test", () => {
  assert.equal(assessmentQuestions.length, 25);
  assert.deepEqual(
    assessmentQuestions.map((question) => question.id),
    Array.from({ length: 25 }, (_, index) => `q${String(index + 1).padStart(2, "0")}`)
  );
  assert.ok(assessmentQuestions.every((question) => question.answers.length === 5));
  assert.equal(
    assessmentQuestions[23].answers[4].text,
    "目标、数据和决策依据"
  );
  assert.deepEqual(directionOrder, [
    "content",
    "research",
    "growth",
    "process",
    "project",
    "campaign",
    "community",
    "strategy",
  ]);
});

test("role catalog resolves different selected roles to different profiles", () => {
  assert.equal(getRoleProfile("内容运营实习生").id, "content-ops");
  assert.equal(getRoleProfile("用户研究实习生").id, "research");
  assert.equal(getRoleProfile("增长运营实习生").id, "growth-ops");
  assert.equal(getRoleProfile("数据运营").id, "growth-ops");
  assert.equal(getRoleProfile("社群运营").id, "community-ops");
  assert.equal(getRoleProfile("用户运营与社群").id, "community-ops");
  assert.equal(getRoleProfile("C 端产品").id, "ux-product");
  assert.equal(getRoleProfile("策略运营").id, "strategy-ops");
  assert.equal(roleProfiles.length, 9);
  assert.notDeepEqual(
    getRoleProfile("用户研究实习生").tasks,
    getRoleProfile("内容运营实习生").tasks
  );
});

test("every role skill has plain-language explanation and evidence examples", () => {
  for (const profile of roleProfiles) {
    for (const skill of profile.skills) {
      assert.ok(
        skill.explain && skill.explain.length >= 12,
        `${profile.id} ${skill.skill} is missing explanation`
      );
      assert.ok(
        skill.evidence && skill.evidence.length >= 4,
        `${profile.id} ${skill.skill} is missing evidence examples`
      );
    }
  }
});

test("assessment directions include mascot personality copy", () => {
  assert.equal(directions.research.mascotName, "小鹿");
  assert.ok(directions.research.personality.includes("像小鹿一样"));
  assert.equal(directions.growth.mascotName, "狐狸");
  assert.ok(directions.process.personality.includes("把复杂流程"));
});

test("content-heavy answers produce content as the main direction with normalized scores", () => {
  const answers = {
    q01: 2,
    q03: 0,
    q05: 2,
    q09: 1,
    q10: 3,
    q11: 4,
    q18: 3,
    q24: 2,
  };

  const result = buildAssessmentResult(answers);

  assert.equal(result.main.key, "content");
  assert.equal(result.supporting[0].key, "research");
  assert.equal(result.scores.content, 100);
  assert.ok(result.ranked.every((item) => Number.isInteger(item.score)));
  assert.equal(result.radar.length, 8);
  assert.deepEqual(
    result.radar.map((item) => item.label),
    [
      "内容表达",
      "用户洞察",
      "数据意识",
      "流程拆解",
      "项目推进",
      "活动转化",
      "社群关系",
      "策略判断",
    ]
  );
});

test("AI materials request carries role and experience context", () => {
  const request = buildAiMaterialsRequest({
    targetRole: "用户研究实习生",
    roleProfile: getRoleProfile("用户研究实习生"),
    experience: {
      name: "校园 App 用户访谈",
      type: "课程作业",
      whatDid: "访谈了 8 位同学，整理痛点并输出报告",
      output: "完成 12 页调研报告",
      evidenceText: "有访谈提纲和报告截图",
    },
  });

  assert.equal(request.targetRole, "用户研究实习生");
  assert.equal(request.roleProfile.family, "用户研究型");
  assert.equal(request.experience.name, "校园 App 用户访谈");
  assert.ok(request.instructions.includes("不要编造用户没有提供的数据"));
});

test("AI materials normalizer keeps display arrays usable", () => {
  const materials = normalizeAiMaterials({
    fitScore: 82,
    overallComment: "适合包装为用户研究经历。",
    summaryCards: [
      { label: "值得包装", title: "用户访谈", detail: "有真实样本", status: "sufficient" },
    ],
    followUpQuestions: [
      { question: "访谈对象是谁？", hint: "说明样本来源" },
    ],
    matchReport: [
      { ability: "用户访谈", status: "sufficient", evidence: "8 位同学访谈", suggestion: "补充样本筛选标准" },
    ],
    portfolio: [
      { section: "01 · 项目背景", items: ["说明调研目标"], status: "sufficient" },
    ],
    resumeOptimized: [
      { text: "围绕校园 App 完成 8 位用户访谈并输出调研报告。", status: "sufficient", note: "可使用" },
    ],
    resumeRaw: [
      { text: "访谈了 8 位同学。", status: "sufficient", note: "原始描述" },
    ],
    interview: [
      { part: "① 背景", content: "课程项目需要调研校园 App。", status: "sufficient", tip: "先讲目标" },
    ],
  });

  assert.equal(materials.fitScore, 82);
  assert.equal(materials.summaryCards.length, 3);
  assert.equal(materials.followUpQuestions[0].question, "访谈对象是谁？");
  assert.equal(materials.resumeOptimized[0].status, "sufficient");
});

test("DeepSeek payload uses chat completions JSON mode", () => {
  const request = buildAiMaterialsRequest({
    targetRole: "用户研究实习生",
    roleProfile: getRoleProfile("用户研究实习生"),
    experience: {
      name: "校园 App 用户访谈",
      type: "课程作业",
      whatDid: "访谈了 8 位同学",
      output: "完成 12 页调研报告",
      evidenceText: "有访谈纪要",
    },
  });

  const payload = buildDeepSeekChatPayload({
    model: "deepseek-v4-flash",
    request,
  });

  assert.equal(payload.model, "deepseek-v4-flash");
  assert.deepEqual(payload.response_format, { type: "json_object" });
  assert.equal(payload.stream, false);
  assert.ok(payload.messages[0].content.includes("json"));
  assert.ok(payload.messages[1].content.includes("校园 App 用户访谈"));
});

test("assessment share text summarizes result for copying", () => {
  const result = buildAssessmentResult({
    q01: 0,
    q02: 2,
    q04: 1,
    q08: 0,
    q11: 0,
    q16: 0,
    q18: 0,
    q24: 0,
  });
  const text = buildAssessmentShareText(result);

  assert.ok(text.includes("我的产品/运营实习方向测评结果"));
  assert.ok(text.includes(result.main.label));
  assert.ok(text.includes(result.main.mascotName));
  assert.ok(text.includes("推荐岗位"));
});
