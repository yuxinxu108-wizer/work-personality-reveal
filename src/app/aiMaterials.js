export const materialStatusValues = ["sufficient", "needs-more", "not-recommended"];

export function buildAiMaterialsRequest({ targetRole, roleProfile, experience }) {
  return {
    targetRole,
    roleProfile: {
      name: roleProfile.name,
      family: roleProfile.family,
      tasks: roleProfile.tasks,
      skills: roleProfile.skills,
      hardReqs: roleProfile.hardReqs,
      coreAbilities: roleProfile.coreAbilities,
      packagable: roleProfile.packagable,
    },
    experience: {
      name: experience?.name || "",
      type: experience?.type || "",
      whatDid: experience?.whatDid || "",
      output: experience?.output || "",
      evidenceText: experience?.evidenceText || "",
    },
    instructions:
      "请基于用户真实经历生成求职材料。不要编造用户没有提供的数据；缺失数据必须标记为需要补充；不适合该经历承载的能力必须标记为不建议写。",
  };
}

export function buildDeepSeekChatPayload({ model, request }) {
  return {
    model,
    messages: [
      {
        role: "system",
        content:
          "你是一个严谨的中文产品/运营实习求职材料助手。你必须只返回合法 json，不要 markdown，不要代码块。不要编造用户没有提供的数据；缺失数据必须标记为 needs-more；不适合该经历承载的能力必须标记为 not-recommended。",
      },
      {
        role: "user",
        content: [
          "请基于以下岗位画像和用户经历，生成求职材料 JSON。",
          "JSON 顶层字段必须包含：fitScore, overallComment, summaryCards, followUpQuestions, matchReport, portfolio, resumeOptimized, resumeRaw, interview。",
          "status 只能使用 sufficient、needs-more、not-recommended。",
          JSON.stringify(request),
        ].join("\n\n"),
      },
    ],
    response_format: { type: "json_object" },
    stream: false,
    max_tokens: 5000,
    temperature: 0.3,
  };
}

export function normalizeAiMaterials(raw) {
  const fallback = createFallbackMaterials();
  const data = raw && typeof raw === "object" ? raw : {};

  return {
    fitScore: clampScore(data.fitScore ?? fallback.fitScore),
    overallComment: safeText(data.overallComment, fallback.overallComment),
    summaryCards: ensureLength(
      normalizeList(data.summaryCards, fallback.summaryCards, normalizeSummaryCard),
      fallback.summaryCards,
      3
    ),
    followUpQuestions: ensureLength(
      normalizeList(data.followUpQuestions, fallback.followUpQuestions, normalizeQuestion),
      fallback.followUpQuestions,
      5
    ),
    matchReport: ensureLength(
      normalizeList(data.matchReport, fallback.matchReport, normalizeMatchItem),
      fallback.matchReport,
      4
    ),
    portfolio: ensureLength(
      normalizeList(data.portfolio, fallback.portfolio, normalizePortfolioSection),
      fallback.portfolio,
      4
    ),
    resumeOptimized: ensureLength(
      normalizeList(data.resumeOptimized, fallback.resumeOptimized, normalizeResumeBullet),
      fallback.resumeOptimized,
      3
    ),
    resumeRaw: ensureLength(
      normalizeList(data.resumeRaw, fallback.resumeRaw, normalizeResumeBullet),
      fallback.resumeRaw,
      3
    ),
    interview: ensureLength(
      normalizeList(data.interview, fallback.interview, normalizeInterviewPart),
      fallback.interview,
      4
    ),
  };
}

export function createFallbackMaterials(context = {}) {
  const roleName = context.targetRole || "目标岗位";
  const experienceName = context.experience?.name || "这段经历";

  return {
    fitScore: 72,
    overallComment: `${experienceName}可以先围绕${roleName}做基础包装，但关键数据和过程细节还需要补充。`,
    summaryCards: [
      {
        label: "值得包装",
        title: "已有真实经历",
        detail: "经历本身可以作为材料起点，但需要明确职责、方法和结果。",
        status: "sufficient",
      },
      {
        label: "最适合包装为",
        title: "岗位相关能力",
        detail: `围绕${roleName}的核心能力表达，不要泛泛写参与项目。`,
        status: "sufficient",
      },
      {
        label: "最需补充",
        title: "量化结果和证据截图",
        detail: "补充数据、反馈、链接、截图或交付物，会显著提升可信度。",
        status: "needs-more",
      },
    ],
    followUpQuestions: [
      { question: "这段经历的目标是什么？为什么要做？", hint: "说明业务目标或项目背景。" },
      { question: "你具体负责哪些动作？哪些是你独立完成的？", hint: "拆清楚个人贡献。" },
      { question: "过程中遇到过什么问题？你怎么调整？", hint: "体现判断和迭代能力。" },
      { question: "有没有数据、反馈或交付物能证明结果？", hint: "尽量提供数字和截图。" },
      { question: "这段经历最能证明目标岗位的哪项能力？", hint: "把经历和岗位能力连起来。" },
    ],
    matchReport: [
      {
        ability: "岗位核心能力",
        status: "needs-more",
        evidence: "已有经历描述，但能力证据还不够具体。",
        suggestion: "补充具体动作、判断依据和结果数据。",
      },
    ],
    portfolio: [
      {
        section: "01 · 项目背景",
        items: ["说明项目目标、用户/对象、你承担的角色。"],
        status: "sufficient",
      },
      {
        section: "02 · 关键动作",
        items: ["按时间线展示你做了什么、如何判断、如何推进。"],
        status: "needs-more",
      },
      {
        section: "03 · 结果证据",
        items: ["放数据、反馈、截图、报告或链接。"],
        status: "needs-more",
      },
      {
        section: "04 · 复盘迁移",
        items: [`总结这段经历如何迁移到${roleName}。`],
        status: "sufficient",
      },
    ],
    resumeOptimized: [
      {
        text: `围绕${roleName}相关目标参与${experienceName}，负责关键执行与结果复盘，沉淀可展示材料。`,
        status: "needs-more",
        note: "需要补充具体数字后再用于简历。",
      },
      {
        text: "梳理项目过程中的问题与调整策略，输出阶段性结论并形成后续优化建议。",
        status: "needs-more",
        note: "需要补充具体方法和产出。",
      },
      {
        text: "结合真实反馈或数据评估项目结果，为后续同类项目提供可复用经验。",
        status: "needs-more",
        note: "需要补充反馈来源。",
      },
    ],
    resumeRaw: [
      {
        text: context.experience?.whatDid || "描述你具体做了什么。",
        status: "needs-more",
        note: "原始经历描述。",
      },
      {
        text: context.experience?.output || "描述最后产出了什么。",
        status: "needs-more",
        note: "原始结果描述。",
      },
      {
        text: context.experience?.evidenceText || "补充数据、截图、链接或反馈。",
        status: "needs-more",
        note: "证据补充项。",
      },
    ],
    interview: [
      {
        part: "① 背景",
        content: `我当时参与了${experienceName}，目标是解决一个和${roleName}相关的问题。`,
        status: "sufficient",
        tip: "先讲清楚背景和目标。",
      },
      {
        part: "② 任务",
        content: "我主要负责把目标拆成具体动作，并推进其中最关键的执行环节。",
        status: "needs-more",
        tip: "补充你的具体职责。",
      },
      {
        part: "③ 行动",
        content: "过程中我根据反馈做过调整，并把调整前后的变化记录下来。",
        status: "needs-more",
        tip: "补充具体调整案例。",
      },
      {
        part: "④ 结果",
        content: "最后形成了可展示的结果，也让我理解了这个岗位需要的核心能力。",
        status: "needs-more",
        tip: "补充量化结果。",
      },
    ],
  };
}

function normalizeList(value, fallback, normalizer) {
  const source = Array.isArray(value) ? value : fallback;
  return source.map((item, index) => normalizer(item, fallback[index] || fallback[0]));
}

function ensureLength(list, fallback, minLength) {
  const result = [...list];
  for (let index = result.length; index < minLength; index += 1) {
    result.push(fallback[index] || fallback[fallback.length - 1]);
  }
  return result;
}

function normalizeSummaryCard(item, fallback) {
  return {
    label: safeText(item?.label, fallback.label),
    title: safeText(item?.title, fallback.title),
    detail: safeText(item?.detail, fallback.detail),
    status: safeStatus(item?.status, fallback.status),
  };
}

function normalizeQuestion(item, fallback) {
  return {
    question: safeText(item?.question, fallback.question),
    hint: safeText(item?.hint, fallback.hint),
  };
}

function normalizeMatchItem(item, fallback) {
  return {
    ability: safeText(item?.ability, fallback.ability),
    status: safeStatus(item?.status, fallback.status),
    evidence: safeText(item?.evidence, fallback.evidence),
    suggestion: safeText(item?.suggestion, fallback.suggestion),
  };
}

function normalizePortfolioSection(item, fallback) {
  return {
    section: safeText(item?.section, fallback.section),
    items: Array.isArray(item?.items) && item.items.length > 0
      ? item.items.map((text) => safeText(text, "")).filter(Boolean)
      : fallback.items,
    status: safeStatus(item?.status, fallback.status),
  };
}

function normalizeResumeBullet(item, fallback) {
  return {
    text: safeText(item?.text, fallback.text),
    status: safeStatus(item?.status, fallback.status),
    note: safeText(item?.note, fallback.note),
  };
}

function normalizeInterviewPart(item, fallback) {
  return {
    part: safeText(item?.part, fallback.part),
    content: safeText(item?.content, fallback.content),
    status: safeStatus(item?.status, fallback.status),
    tip: safeText(item?.tip, fallback.tip),
  };
}

function safeText(value, fallback) {
  return typeof value === "string" && value.trim() ? value.trim() : fallback;
}

function safeStatus(value, fallback) {
  return materialStatusValues.includes(value) ? value : fallback;
}

function clampScore(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return 70;
  return Math.max(0, Math.min(100, Math.round(number)));
}
