(() => {
function createEmptyScores(directions) {
  return Object.fromEntries(Object.keys(directions || {}).map((key) => [key, 0]));
}

function scoreAnswers(answersByQuestionId, questions, directions) {
  const scores = createEmptyScores(directions);
  const answers = answersByQuestionId || {};

  for (const question of questions || []) {
    if (!question || !question.id || !Array.isArray(question.answers)) continue;

    const answerIndex = answers[question.id];
    if (!Number.isInteger(answerIndex)) continue;

    const answer = question.answers[answerIndex];
    if (!answer || !Array.isArray(answer.weights)) continue;

    for (const weight of answer.weights) {
      if (!weight || !Object.prototype.hasOwnProperty.call(scores, weight.key)) continue;
      if (!Number.isFinite(weight.value)) continue;

      scores[weight.key] += weight.value;
    }
  }

  return scores;
}

function selectResult(scores) {
  const ranked = Object.entries(scores || {})
    .sort((a, b) => b[1] - a[1])
    .map(([key, value]) => ({ key, value }));

  const main = ranked[0] ? ranked[0].key : undefined;
  const supporting = ranked[1] ? [ranked[1].key] : [];
  const secondScore = ranked[1] ? ranked[1].value : undefined;
  const thirdScore = ranked[2] ? ranked[2].value : undefined;

  if (
    ranked[2] &&
    (thirdScore === secondScore || Math.abs(thirdScore - secondScore) <= 1)
  ) {
    supporting.push(ranked[2].key);
  }

  const topScore = ranked[0] ? ranked[0].value : 0;
  const fifthScore = ranked[4] ? ranked[4].value : topScore;
  const isMultiSided = topScore - fifthScore <= 3;

  return {
    main,
    supporting: supporting.slice(0, 2),
    ranked,
    isMultiSided
  };
}

function normalizeScores(scores) {
  const entries = Object.entries(scores || {});
  const values = entries.map(([, value]) => value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min;

  if (!entries.length) return {};
  if (range === 0) {
    return Object.fromEntries(entries.map(([key]) => [key, 0]));
  }

  return Object.fromEntries(
    entries.map(([key, value]) => [
      key,
      Math.round(((value - min) / range) * 100)
    ])
  );
}

function buildPortfolioSuggestion(mainKey, supportKey, data) {
  const theme = data.portfolioThemes[mainKey];
  const highlight = data.portfolioHighlights[supportKey];
  return `${theme}，并把亮点放在：${highlight}`;
}

const api = {
  createEmptyScores,
  scoreAnswers,
  selectResult,
  normalizeScores,
  buildPortfolioSuggestion
};

if (typeof window !== "undefined") {
  window.InternTestScoring = api;
}

if (typeof module !== "undefined") {
  module.exports = api;
}
})();
