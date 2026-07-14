import test from "node:test";
import assert from "node:assert/strict";

import {
  normalizeBackendAssessmentResult,
  normalizeBackendQuestion,
} from "../src/app/backendApi.js";

test("backend questions normalize to the existing assessment question shape", () => {
  const question = normalizeBackendQuestion({
    id: "q01",
    text: "社团招新海报发出去后，报名人数很少。你最想先做什么？",
    question_type: "scenario",
    options: [
      { id: "q01_a1", text: "找几个没报名的同学问问，他们卡在了哪里" },
      { id: "q01_a2", text: "把看到、点开、填完表单的人数分开看" },
    ],
  });

  assert.deepEqual(question, {
    id: "q01",
    text: "社团招新海报发出去后，报名人数很少。你最想先做什么？",
    answers: [
      { id: "q01_a1", text: "找几个没报名的同学问问，他们卡在了哪里" },
      { id: "q01_a2", text: "把看到、点开、填完表单的人数分开看" },
    ],
  });
});

test("backend assessment result normalizes to the result page shape", () => {
  const result = normalizeBackendAssessmentResult({
    main_direction: "growth",
    supporting_directions: ["strategy"],
    scores: {
      content: 20,
      research: 40,
      growth: 100,
      process: 10,
      project: 50,
      campaign: 75,
      community: 0,
      strategy: 80,
      ux: 30,
    },
    is_multi_sided: false,
    result: {
      title: "数据增长型",
      summary: "适合观察每一步有多少人留下来。",
      support_summary: "也适合做策略判断。",
      portfolio_suggestion: "做一个转化漏斗复盘。",
    },
  });

  assert.equal(result.main.key, "growth");
  assert.equal(result.main.label, "数据增长型");
  assert.equal(result.main.roleLabel, "增长运营");
  assert.equal(result.supporting[0].key, "strategy");
  assert.equal(result.scores.growth, 100);
  assert.equal(result.radar.length, 8);
  assert.deepEqual(result.radar.map((item) => item.key), [
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
