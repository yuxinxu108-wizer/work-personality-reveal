const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const { data } = require("../data.js");
const {
  scoreAnswers,
  selectResult,
  normalizeScores,
  buildPortfolioSuggestion
} = require("../scoring.js");

test("defines 9 directions", () => {
  assert.equal(Object.keys(data.directions).length, 9);
});

test("defines 25 questions", () => {
  assert.equal(data.questions.length, 25);
});

test("question IDs are unique", () => {
  const ids = data.questions.map((question) => question.id);
  assert.equal(new Set(ids).size, ids.length);
});

test("each question has broad weighted answers", () => {
  for (const question of data.questions) {
    assert.ok(question.id);
    assert.ok(question.text.length >= 10);
    assert.ok(question.answers.length >= 4);
    assert.ok(question.answers.length <= 6);

    for (const answer of question.answers) {
      const weightKeys = answer.weights.map((weight) => weight.key);

      assert.ok(answer.text.length >= 8);
      assert.ok(Array.isArray(answer.weights));
      assert.ok(answer.weights.length >= 1);
      assert.ok(answer.weights.length <= 2);
      assert.equal(new Set(weightKeys).size, weightKeys.length);

      for (const weight of answer.weights) {
        assert.ok(data.directions[weight.key], `Unknown direction ${weight.key}`);
        assert.ok(Number.isFinite(weight.value));
        assert.notEqual(weight.value, 0);
        assert.ok([-2, 1, 2].includes(weight.value));
      }
    }
  }
});

test("directions include user-facing metadata and supporting data", () => {
  for (const [key, direction] of Object.entries(data.directions)) {
    assert.ok(direction.label);
    assert.ok(direction.shortLabel);
    assert.ok(direction.summary);
    assert.ok(direction.tone);
    assert.ok(direction.avatarSrc);
    assert.ok(direction.animal);
    assert.ok(direction.productJobs.length > 0);
    assert.ok(direction.operationJobs.length > 0);
    assert.ok(direction.applicationKeywords.length > 0);
    assert.ok(data.actionPlans[key].days.length === 7);
    assert.ok(data.jargonTerms[key].length >= 4);
    assert.ok(data.portfolioThemes[key]);
    assert.ok(data.portfolioHighlights[key]);
  }
});

test("browser script export does not reserve common lexical global names", () => {
  const source = fs.readFileSync(require.resolve("../data.js"), "utf8");
  const context = vm.createContext({ window: {} });

  vm.runInContext(source, context);
  vm.runInContext("const directions = {}; const questions = [];", context);

  assert.ok(context.window.InternTestData);
  assert.equal(Object.keys(context.window.InternTestData.directions).length, 9);
});

test("scores weighted answers across directions", () => {
  const scores = scoreAnswers({ q01: 1, q02: 0, q03: 1 }, data.questions, data.directions);
  assert.ok(scores.growth > 0);
  assert.ok(scores.campaign > 0);
  assert.ok(scores.ux > 0);
});

test("ignores missing and invalid answer indexes", () => {
  const scores = scoreAnswers(
    { q01: 99, q02: "0", q03: 1, missing: 0 },
    data.questions,
    data.directions
  );

  assert.equal(scores.growth, 2);
  assert.equal(scores.content, 1);
  assert.equal(scores.ux, 0);
});

test("selects one main direction and one support by default", () => {
  const result = selectResult({
    ux: 10,
    process: 4,
    growth: 9,
    content: 2,
    campaign: 1,
    community: 0,
    research: 7,
    strategy: 3,
    project: 2
  });

  assert.equal(result.main, "ux");
  assert.deepEqual(result.supporting, ["growth"]);
  assert.equal(result.isMultiSided, false);
});

test("keeps two supporting directions when tied", () => {
  const result = selectResult({
    ux: 10,
    process: 8,
    growth: 8,
    content: 2,
    campaign: 1,
    community: 0,
    research: 7,
    strategy: 3,
    project: 2
  });

  assert.equal(result.main, "ux");
  assert.deepEqual(result.supporting, ["process", "growth"]);
});

test("builds portfolio suggestion from main and support", () => {
  const suggestion = buildPortfolioSuggestion("content", "growth", data);
  assert.match(suggestion, /内容账号/);
  assert.match(suggestion, /数字/);
});

test("normalizes scores to rounded 0 to 100 values", () => {
  assert.deepEqual(normalizeScores({ ux: -2, growth: 3, content: 8 }), {
    ux: 0,
    growth: 50,
    content: 100
  });
});

test("normalizes zero-range scores to zero", () => {
  assert.deepEqual(normalizeScores({ ux: 4, growth: 4 }), {
    ux: 0,
    growth: 0
  });
});

test("scoring browser script export does not reserve common lexical global names", () => {
  const source = fs.readFileSync(require.resolve("../scoring.js"), "utf8");
  const context = vm.createContext({ window: {} });

  vm.runInContext(source, context);
  vm.runInContext(
    "const scoreAnswers = null; const selectResult = null; const normalizeScores = null;",
    context
  );

  assert.ok(context.window.InternTestScoring);
  assert.equal(typeof context.window.InternTestScoring.scoreAnswers, "function");
});
