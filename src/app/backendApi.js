import { directionOrder, directions } from "./assessment.js";

export const ASSESSMENT_API_BASE =
  getEnvValue("VITE_ASSESSMENT_API_BASE") || "http://127.0.0.1:8000";

export async function fetchBackendQuestions(fetchImpl = globalThis.fetch) {
  const response = await fetchImpl(`${ASSESSMENT_API_BASE}/api/questions`);
  if (!response.ok) {
    throw new Error("测评题目接口暂时不可用");
  }
  const questions = await response.json();
  return questions.map(normalizeBackendQuestion);
}

export async function submitBackendAssessment(
  answers,
  fetchImpl = globalThis.fetch
) {
  const response = await fetchImpl(`${ASSESSMENT_API_BASE}/api/assessment/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answers }),
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "测评提交接口暂时不可用");
  }
  return normalizeBackendAssessmentResult(payload);
}

export function normalizeBackendQuestion(question) {
  return {
    id: question.id,
    text: question.text,
    answers: (question.options || []).map((option) => ({
      id: option.id,
      text: option.text,
    })),
  };
}

export function normalizeBackendAssessmentResult(payload) {
  const scores = payload.scores || {};
  const main = normalizeDirection(payload.main_direction, payload.result);
  const supporting = (payload.supporting_directions || [])
    .map((key) => normalizeDirection(key))
    .filter(Boolean);

  return {
    main,
    supporting,
    ranked: Object.entries(scores)
      .sort((a, b) => b[1] - a[1])
      .map(([key, score]) => ({ ...normalizeDirection(key), score })),
    scores,
    rawScores: scores,
    radar: directionOrder.map((key) => ({
      key,
      label: directions[key]?.abilityLabel || key,
      score: Number.isFinite(scores[key]) ? scores[key] : 0,
    })),
    isComposite: Boolean(payload.is_multi_sided),
    backend: payload,
  };
}

function normalizeDirection(key, result = {}) {
  const fallback = directions[key];
  if (!key || !fallback) return null;

  return {
    ...fallback,
    label: result.title || fallback.label,
    summary: result.summary || fallback.summary,
    roles: fallback.roles,
  };
}

function getEnvValue(name) {
  if (typeof import.meta !== "undefined" && import.meta.env) {
    return import.meta.env[name];
  }
  return undefined;
}
