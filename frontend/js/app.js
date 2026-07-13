import { fetchDirections, fetchQuestions, submitAssessment } from "./api.js";
import { clear, renderApiError, setText } from "./render.js";

let directions = {};
let questions = [];
let currentIndex = 0;
let answersByQuestionId = {};
let latestResult = null;
let advanceTimer = null;
const ADVANCE_DELAY_MS = 900;

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
const nextBtn = document.getElementById("nextBtn");

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
  directions = Object.fromEntries(
    directionList.map((direction) => [direction.key, direction])
  );
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
  nextBtn.disabled = selectedAnswer === undefined;
  nextBtn.textContent = currentIndex === questions.length - 1 ? "查看结果" : "下一题";
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
  advanceTimer = window.setTimeout(advanceToNext, ADVANCE_DELAY_MS);
}

async function advanceToNext() {
  clearAdvanceTimer();
  const question = questions[currentIndex];
  if (!question || answersByQuestionId[question.id] === undefined) return;
  if (currentIndex < questions.length - 1) {
    currentIndex += 1;
    renderQuestion();
    return;
  }
  await showLoadingThenResult();
}

async function showLoadingThenResult() {
  try {
    showScreen("loading");
    latestResult = await submitAssessment(answersByQuestionId);
    renderResult(latestResult);
    showScreen("result");
  } catch (error) {
    showScreen("quiz");
    renderApiError(error.message);
  }
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
  renderConfidence(payload.confidence, payload.result_explanation);
  setText("projectIdea", payload.result.portfolio_suggestion);
  renderSupporting(payload.supporting_directions);
  renderScoreBars(payload.scores);
  renderRouteSteps(payload.result.route_steps);
  renderActionPlan(payload.result.action_plan);
  renderEvidence(payload.evidence);
}

function renderConfidence(confidence, explanation) {
  const labels = {
    high: "结果稳定度：高",
    medium: "结果稳定度：中",
    low: "结果稳定度：低",
    insufficient: "结果稳定度：不足"
  };
  setText("resultConfidence", labels[confidence?.level] || "结果稳定度：待确认");
  setText(
    "resultExplanation",
    explanation || confidence?.reason || "当前结果适合作为实习方向探索线索。"
  );
}

function renderAvatar(direction) {
  const avatar = document.getElementById("avatarBadge");
  clear(avatar);
  const sticker = document.createElement("div");
  sticker.className = `animal-sticker animal-${direction.key}`;
  const image = document.createElement("img");
  image.src = direction.avatar_src;
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

function renderActionPlan(plan) {
  const container = document.getElementById("actionPlan");
  const panel = container.closest(".panel");
  clear(container);
  if (!Array.isArray(plan) || !plan.length) {
    panel.hidden = true;
    return;
  }
  panel.hidden = false;
  plan.forEach((day, index) => {
    const item = document.createElement("article");
    const toggle = document.createElement("button");
    const label = document.createElement("strong");
    const title = document.createElement("span");
    const detail = document.createElement("div");
    item.className = "day-item";
    toggle.type = "button";
    toggle.className = "day-toggle";
    toggle.setAttribute("aria-expanded", index === 0 ? "true" : "false");
    label.textContent = day.label || `Day ${index + 1}`;
    title.textContent = day.title || day.text || "";
    detail.className = "day-detail";
    detail.hidden = index !== 0;
    renderActionPlanDetail(detail, day);
    toggle.append(label, title);
    toggle.addEventListener("click", () => {
      const expanded = toggle.getAttribute("aria-expanded") === "true";
      toggle.setAttribute("aria-expanded", expanded ? "false" : "true");
      detail.hidden = expanded;
    });
    item.append(toggle, detail);
    container.appendChild(item);
  });
}

function renderActionPlanDetail(container, day) {
  appendField(container, "目标", day.goal);
  if (Array.isArray(day.tasks) && day.tasks.length) {
    const list = document.createElement("ul");
    day.tasks.forEach((task) => {
      const item = document.createElement("li");
      item.textContent = task;
      list.appendChild(item);
    });
    container.appendChild(list);
  }
  appendField(container, "产出", day.deliverable);
  appendField(container, "简历表达", day.resume_sentence);
  if (Array.isArray(day.jd_keywords) && day.jd_keywords.length) {
    const chips = document.createElement("div");
    chips.className = "keyword-list day-keywords";
    renderChips(chips, day.jd_keywords);
    container.appendChild(chips);
  }
}

function appendField(container, label, value) {
  if (!value) return;
  const paragraph = document.createElement("p");
  const strong = document.createElement("strong");
  strong.textContent = `${label}：`;
  paragraph.append(strong, value);
  container.appendChild(paragraph);
}

function renderEvidence(evidence) {
  const recommendedRoles = findElement("recommendedRoles", "operationJobs");
  const hardRequirements = findElement("hardRequirements");
  const frequentTasks = findElement("frequentTasks", "productJobs");
  const resumeKeywords = findElement("resumeKeywords", "applicationKeywords");
  [recommendedRoles, hardRequirements, frequentTasks, resumeKeywords].forEach((node) => {
    if (node) clear(node);
  });

  const roles = evidence.recommended_roles || evidence.representative_roles || [];
  const hardItems = evidence.hard_requirements || evidence.high_frequency_tools || [];
  const tasks = evidence.high_frequency_tasks || [];
  const resumeItems = evidence.resume_keywords || evidence.high_frequency_capabilities || [];
  const evidenceConfidence = evidence.evidence_confidence;

  renderList(recommendedRoles, roles, "暂无可展示岗位");
  renderList(frequentTasks, tasks, "暂无高频任务");
  renderChips(hardRequirements, [
    `参考 ${evidence.jd_count} 条 JD`,
    evidenceConfidence?.message,
    ...hardItems
  ].filter(Boolean));
  renderChips(resumeKeywords, resumeItems);
}

function findElement(...ids) {
  for (const id of ids) {
    const element = document.getElementById(id);
    if (element) return element;
  }
  return null;
}

function renderList(container, items, emptyText) {
  if (!container) return;
  if (!items.length) {
    const item = document.createElement("li");
    item.textContent = emptyText;
    container.appendChild(item);
    return;
  }
  items.forEach((text) => {
    const item = document.createElement("li");
    item.textContent = text;
    container.appendChild(item);
  });
}

function renderChips(container, items) {
  if (!container) return;
  const values = items.length ? items : ["暂无可展示关键词"];
  values.forEach((text) => {
    const chip = document.createElement("span");
    chip.textContent = text;
    container.appendChild(chip);
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
nextBtn.addEventListener("click", advanceToNext);
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
