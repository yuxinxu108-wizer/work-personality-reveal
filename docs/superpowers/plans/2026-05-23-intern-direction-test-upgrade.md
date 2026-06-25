# Intern Direction Test Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the static internship direction test into a 25-question beginner-friendly quiz with 9 result directions, animal avatars, practical result guidance, expandable action plans, and inline jargon explanations.

**Architecture:** Keep the app static and browser-only. Split pure quiz data and scoring logic away from DOM rendering so scoring can be tested with Node's built-in test runner. Use progressive disclosure on the result page: compact result first, expandable day details and tap-to-explain jargon.

**Tech Stack:** Static HTML, CSS, vanilla JavaScript, Node.js built-in `node:test` for pure scoring tests, no build tool, no backend, no runtime AI API.

---

## File Structure

- Create: `package.json`
  - Adds a `test` script using Node's built-in test runner.
- Create: `data.js`
  - Owns `window.InternTestData`: directions, questions, action plans, jargon terms, portfolio themes, portfolio highlights, and avatar metadata.
- Create: `scoring.js`
  - Owns pure scoring helpers on `window.InternTestScoring` and CommonJS exports for tests.
- Modify: `script.js`
  - Becomes DOM rendering and interaction code only: screen switching, quiz rendering, result rendering, accordions, jargon popovers, copy summary.
- Modify: `index.html`
  - Adds result containers and loads `data.js`, `scoring.js`, then `script.js`.
- Modify: `styles.css`
  - Reworks visual system, quiz states, result page, animal avatar cards, accordions, and jargon popovers.
- Create: `test/scoring.test.js`
  - Tests scoring, tie handling, weighted answers, and content integrity.

## Task 1: Initialize Project Tooling

**Files:**
- Create: `package.json`

- [ ] **Step 1: Initialize git if missing**

Run:

```bash
git status --short
```

Expected if not initialized:

```text
fatal: not a git repository (or any of the parent directories): .git
```

If that output appears, run:

```bash
git init
```

Expected:

```text
Initialized empty Git repository in /Users/dadaxu/vibe-coding/intern-direction-test/.git/
```

- [ ] **Step 2: Add Node test script**

Create `package.json`:

```json
{
  "name": "intern-direction-test",
  "version": "1.0.0",
  "private": true,
  "type": "commonjs",
  "scripts": {
    "test": "node --test"
  }
}
```

- [ ] **Step 3: Run empty test suite**

Run:

```bash
npm test
```

Expected:

```text
# tests 0
# pass 0
# fail 0
```

- [ ] **Step 4: Commit tooling**

Run:

```bash
git add package.json
git commit -m "chore: initialize static quiz test tooling"
```

Expected: commit succeeds.

## Task 2: Add Data Model And Content

**Files:**
- Create: `data.js`
- Test: `test/scoring.test.js`

- [ ] **Step 1: Write content integrity tests**

Create `test/scoring.test.js` with:

```js
const test = require("node:test");
const assert = require("node:assert/strict");

const { data } = require("../data.js");

test("defines 9 directions", () => {
  assert.equal(Object.keys(data.directions).length, 9);
});

test("defines 25 questions", () => {
  assert.equal(data.questions.length, 25);
});

test("each question has broad weighted answers", () => {
  for (const question of data.questions) {
    assert.ok(question.id);
    assert.ok(question.text.length >= 10);
    assert.ok(question.answers.length >= 4);
    assert.ok(question.answers.length <= 6);

    for (const answer of question.answers) {
      assert.ok(answer.text.length >= 8);
      assert.ok(Array.isArray(answer.weights));
      assert.ok(answer.weights.length >= 1);
      assert.ok(answer.weights.length <= 2);

      for (const weight of answer.weights) {
        assert.ok(data.directions[weight.key], `Unknown direction ${weight.key}`);
        assert.ok(Number.isFinite(weight.value));
        assert.notEqual(weight.value, 0);
      }
    }
  }
});

test("directions include avatar, action plan, jargon, and portfolio data", () => {
  for (const key of Object.keys(data.directions)) {
    assert.ok(data.directions[key].animal);
    assert.ok(data.actionPlans[key].days.length === 7);
    assert.ok(data.jargonTerms[key].length >= 4);
    assert.ok(data.portfolioThemes[key]);
    assert.ok(data.portfolioHighlights[key]);
  }
});
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
npm test
```

Expected: FAIL because `../data.js` does not exist.

- [ ] **Step 3: Create `data.js`**

Create `data.js` with this structure and complete content:

```js
const directions = {
  ux: {
    label: "用户体验型",
    shortLabel: "C 端产品",
    animal: "小猫",
    tone: "细致、敏感、在意使用感受",
    summary: "你适合从真实使用场景里发现问题，把一个功能改得更顺手、更容易理解。",
    productJobs: ["C 端产品实习生", "用户体验产品实习生", "内容产品实习生"],
    operationJobs: ["用户运营实习生", "App 运营实习生", "用户研究实习生"],
    applicationKeywords: ["用户反馈", "体验优化", "功能路径", "竞品拆解", "原型表达"]
  },
  process: {
    label: "业务流程型",
    shortLabel: "B 端产品",
    animal: "小海狸",
    tone: "有结构感、能把混乱事情理清楚",
    summary: "你适合梳理角色、规则和步骤，把复杂协作变成更清楚的流程。",
    productJobs: ["B 端产品实习生", "后台产品实习生", "平台产品实习生"],
    operationJobs: ["业务运营实习生", "商家运营实习生", "平台运营实习生"],
    applicationKeywords: ["流程梳理", "规则设计", "后台页面", "状态流转", "协作效率"]
  },
  growth: {
    label: "数据增长型",
    shortLabel: "增长运营",
    animal: "小狐狸",
    tone: "敏锐、会从数字变化里找机会",
    summary: "你适合观察每一步有多少人留下来，用数字判断哪里最值得先改。",
    productJobs: ["增长产品实习生", "数据产品实习生", "商业化产品实习生"],
    operationJobs: ["增长运营实习生", "数据运营实习生", "用户增长实习生"],
    applicationKeywords: ["数据复盘", "报名路径", "效果对比", "增长实验", "结果分析"]
  },
  content: {
    label: "内容表达型",
    shortLabel: "内容运营",
    animal: "小鹦鹉",
    tone: "会表达、懂选题、能让人愿意看",
    summary: "你适合把信息整理成用户愿意点开、看懂、收藏或转发的内容。",
    productJobs: ["内容产品实习生", "社区产品实习生", "推荐产品实习生"],
    operationJobs: ["内容运营实习生", "新媒体运营实习生", "账号运营实习生"],
    applicationKeywords: ["选题策划", "标题优化", "内容排期", "平台调性", "传播复盘"]
  },
  campaign: {
    label: "活动转化型",
    shortLabel: "活动运营",
    animal: "小兔子",
    tone: "行动快、亲和、能把参与路径推起来",
    summary: "你适合把一个目标变成具体活动，让更多人愿意参与并完成关键动作。",
    productJobs: ["营销产品实习生", "活动产品实习生", "增长产品实习生"],
    operationJobs: ["活动运营实习生", "校园运营实习生", "营销运营实习生"],
    applicationKeywords: ["活动策划", "参与路径", "资源协调", "报名提升", "活动复盘"]
  },
  community: {
    label: "社群关系型",
    shortLabel: "用户运营",
    animal: "小水獭",
    tone: "温暖、会连接人、擅长长期陪伴",
    summary: "你适合维护用户关系，让用户愿意留下来、互动起来、持续参与。",
    productJobs: ["社区产品实习生", "会员产品实习生", "CRM 产品实习生"],
    operationJobs: ["社群运营实习生", "用户运营实习生", "私域运营实习生"],
    applicationKeywords: ["社群维护", "用户互动", "用户召回", "关系运营", "活跃机制"]
  },
  research: {
    label: "用户研究型",
    shortLabel: "需求洞察",
    animal: "小鹿",
    tone: "观察细腻、共情强、愿意理解别人",
    summary: "你适合通过聊天、观察和整理反馈，弄清楚真实用户到底需要什么。",
    productJobs: ["用户研究实习生", "产品调研实习生", "体验产品实习生"],
    operationJobs: ["用户运营实习生", "策略运营实习生", "社群运营实习生"],
    applicationKeywords: ["用户访谈", "反馈整理", "需求洞察", "问卷设计", "用户画像"]
  },
  strategy: {
    label: "商业分析型",
    shortLabel: "策略运营",
    animal: "小猫头鹰",
    tone: "冷静、看全局、喜欢判断优先级",
    summary: "你适合把目标、资源、竞品和结果放在一起看，判断下一步怎么做更划算。",
    productJobs: ["策略产品实习生", "商业化产品实习生", "数据产品实习生"],
    operationJobs: ["策略运营实习生", "商业分析实习生", "平台运营实习生"],
    applicationKeywords: ["竞品分析", "策略判断", "优先级", "商业模式", "问题拆解"]
  },
  project: {
    label: "项目推进型",
    shortLabel: "执行推进",
    animal: "小边牧",
    tone: "有节奏、会协调、能把事情往前推",
    summary: "你适合把目标拆成计划，协调不同人和资源，保证事情按时落地。",
    productJobs: ["项目型产品实习生", "产品运营实习生", "平台产品实习生"],
    operationJobs: ["项目运营实习生", "活动运营实习生", "校园运营实习生"],
    applicationKeywords: ["项目排期", "进度跟进", "跨方协调", "风险预案", "落地执行"]
  }
};

const questions = [
  q("q01", "社团招新海报发出去后，报名人数很少。你最想先做什么？", [
    a("找几个没报名的同学问问，他们卡在了哪里", [["research", 2], ["campaign", 1]]),
    a("把看到海报、点开链接、填完表单的人数分开看", [["growth", 2], ["campaign", 1]]),
    a("重写标题和活动介绍，让重点更明显", [["content", 2], ["campaign", 1]]),
    a("检查报名步骤是不是太麻烦，有没有信息缺失", [["ux", 2], ["process", 1]]),
    a("重新排一下宣传节奏和负责同学的分工", [["project", 2], ["process", 1]])
  ]),
  q("q02", "一个校园小程序被吐槽不好用，你会先关注哪件事？", [
    a("用户从打开到完成任务中哪一步最容易放弃", [["ux", 2], ["growth", 1]]),
    a("不同角色分别要做什么，规则是不是绕来绕去", [["process", 2], ["strategy", 1]]),
    a("吐槽里反复出现的真实原因是什么", [["research", 2], ["ux", 1]]),
    a("这些问题会不会影响关键目标，比如报名或预约", [["strategy", 2], ["growth", 1]]),
    a("先列出改版事项、负责人和完成时间", [["project", 2], ["process", 1]])
  ]),
  q("q03", "你负责一个求职账号，最近阅读量下降。你第一步更像会做什么？", [
    a("回看最近选题，判断是不是不够贴近学生焦虑", [["content", 2], ["research", 1]]),
    a("比较每篇标题、收藏、评论的变化", [["growth", 2], ["content", 1]]),
    a("去评论区和私信里找读者真实困惑", [["research", 2], ["community", 1]]),
    a("重新安排未来两周的选题和发布时间", [["project", 2], ["content", 1]]),
    a("组织一次资料领取或打卡活动拉回互动", [["campaign", 2], ["community", 1]])
  ]),
  q("q04", "团队对新功能意见不一致，你通常会怎么推进？", [
    a("先把目标和判断标准写清楚，再讨论取舍", [["strategy", 2], ["project", 1]]),
    a("找几个目标用户聊聊，看他们是否真的需要", [["research", 2], ["ux", 1]]),
    a("画出使用步骤，让大家看到哪里顺哪里卡", [["ux", 2], ["process", 1]]),
    a("列出每个方案要改的流程、规则和风险", [["process", 2], ["project", 1]]),
    a("定一个小范围试运行，先看真实反馈", [["growth", 2], ["campaign", 1]])
  ]),
  q("q05", "如果要你做一份作品集，你更想从哪里开始？", [
    a("拆解一个常用 App，提出更顺手的改法", [["ux", 2], ["research", 1]]),
    a("设计一个校园事务的线上处理流程", [["process", 2], ["project", 1]]),
    a("做一个账号选题计划，并写出内容样稿", [["content", 2], ["strategy", 1]]),
    a("设计一场线上活动，从宣传到报名都写清楚", [["campaign", 2], ["project", 1]]),
    a("分析一个项目哪里流失最多，并提出改进", [["growth", 2], ["strategy", 1]])
  ]),
  q("q06", "下面哪种工作最容易消耗你？", [
    a("连续几天回复用户、维护群气氛", [["community", -2], ["strategy", 1]]),
    a("反复检查流程、规则和异常情况", [["process", -2], ["content", 1]]),
    a("盯排期、催进度、协调不同人", [["project", -2], ["research", 1]]),
    a("对着表格比较不同结果的变化", [["growth", -2], ["ux", 1]]),
    a("不断改标题、文案和表达方式", [["content", -2], ["process", 1]])
  ]),
  q("q07", "活动当天突然出了问题，你最自然的反应是？", [
    a("先稳住现场节奏，安排谁处理哪件事", [["project", 2], ["campaign", 1]]),
    a("先告诉参与者现在该怎么做，减少混乱", [["community", 2], ["campaign", 1]]),
    a("先找到影响最大的一步，保证关键目标能完成", [["strategy", 2], ["growth", 1]]),
    a("先记录问题，方便结束后复盘", [["growth", 2], ["project", 1]]),
    a("先把临时说明改得更清楚", [["content", 2], ["ux", 1]])
  ]),
  q("q08", "朋友说想找互联网实习但完全没方向，你会怎么帮？", [
    a("问他平时更喜欢观察人、写东西、看数字还是推进事", [["research", 2], ["strategy", 1]]),
    a("帮他把岗位拆成每天具体会做什么", [["process", 2], ["content", 1]]),
    a("让他先做一个小项目，用结果反推适合什么", [["project", 2], ["strategy", 1]]),
    a("给他列一些好理解的岗位搜索词", [["content", 2], ["community", 1]]),
    a("建议他先投几类岗位，看反馈数据", [["growth", 2], ["strategy", 1]])
  ]),
  q("q09", "你最希望别人怎么评价你的工作？", [
    a("很懂用户，能发现别人没注意到的卡点", [["ux", 2], ["research", 1]]),
    a("表达清楚，能把复杂事情讲得好懂", [["content", 2], ["process", 1]]),
    a("判断靠谱，知道先做什么后做什么", [["strategy", 2], ["project", 1]]),
    a("推进稳定，说到的事情能落地", [["project", 2], ["campaign", 1]]),
    a("很会连接人，让大家愿意参与", [["community", 2], ["campaign", 1]])
  ]),
  q("q10", "看到一个竞品功能，你最容易注意到什么？", [
    a("它让用户怎么一步步完成任务", [["ux", 2], ["process", 1]]),
    a("它背后可能有哪些角色和规则", [["process", 2], ["strategy", 1]]),
    a("它在哪里引导用户继续下一步", [["growth", 2], ["campaign", 1]]),
    a("它怎么把卖点讲清楚", [["content", 2], ["strategy", 1]]),
    a("它有没有让用户互相互动", [["community", 2], ["ux", 1]])
  ]),
  q("q11", "如果只能选一种资料来判断问题，你会选？", [
    a("几段真实用户聊天记录", [["research", 2], ["community", 1]]),
    a("一张每一步人数变化表", [["growth", 2], ["strategy", 1]]),
    a("一张完整流程图", [["process", 2], ["ux", 1]]),
    a("一份活动排期和执行记录", [["project", 2], ["campaign", 1]]),
    a("一组内容标题和评论反馈", [["content", 2], ["research", 1]])
  ]),
  q("q12", "你做完一个项目后，最想复盘什么？", [
    a("用户到底有没有觉得更好用", [["ux", 2], ["research", 1]]),
    a("哪个环节最影响最终结果", [["growth", 2], ["strategy", 1]]),
    a("分工和排期哪里可以更顺", [["project", 2], ["process", 1]]),
    a("哪些话术、标题或内容更有效", [["content", 2], ["campaign", 1]]),
    a("用户有没有留下来继续互动", [["community", 2], ["growth", 1]])
  ]),
  q("q13", "你更不排斥哪类细活？", [
    a("把一个页面的按钮、提示和顺序改到更舒服", [["ux", 2], ["content", 1]]),
    a("把一堆步骤整理成清单和规则", [["process", 2], ["project", 1]]),
    a("把评论、私信和访谈内容分门别类", [["research", 2], ["community", 1]]),
    a("把活动物料、时间和负责人对齐", [["project", 2], ["campaign", 1]]),
    a("把一组数据整理成结论", [["growth", 2], ["strategy", 1]])
  ]),
  q("q14", "一个群越来越冷清，你会先做什么？", [
    a("观察大家什么时候最愿意说话", [["research", 2], ["community", 1]]),
    a("设计一个轻量话题或打卡机制", [["community", 2], ["campaign", 1]]),
    a("看哪些内容曾经让大家互动更多", [["content", 2], ["growth", 1]]),
    a("把新成员入群后的引导流程改清楚", [["process", 2], ["community", 1]]),
    a("设定一周目标并安排运营动作", [["project", 2], ["community", 1]])
  ]),
  q("q15", "老板只说一句“提升报名”，你会先追问什么？", [
    a("现在从看到信息到报名，每一步大概有多少人？", [["growth", 2], ["strategy", 1]]),
    a("目标用户是谁，他们为什么会想参加？", [["research", 2], ["campaign", 1]]),
    a("报名流程具体有几步，哪里可能麻烦？", [["ux", 2], ["process", 1]]),
    a("这次活动最重要的目标和限制是什么？", [["strategy", 2], ["project", 1]]),
    a("谁负责宣传、物料、答疑和统计？", [["project", 2], ["process", 1]])
  ]),
  q("q16", "你最喜欢哪种起步方式？", [
    a("先找人聊，听真实想法", [["research", 2], ["community", 1]]),
    a("先画步骤，理清发生了什么", [["process", 2], ["ux", 1]]),
    a("先看结果，找最明显的问题", [["growth", 2], ["strategy", 1]]),
    a("先写出来，让别人能看懂", [["content", 2], ["campaign", 1]]),
    a("先拆计划，确定怎么推进", [["project", 2], ["strategy", 1]])
  ]),
  q("q17", "团队只有一天时间完成展示，你会优先保证什么？", [
    a("故事讲清楚，别人一听就懂", [["content", 2], ["strategy", 1]]),
    a("流程完整，不要漏掉关键环节", [["process", 2], ["project", 1]]),
    a("结论有依据，不只是主观感觉", [["growth", 2], ["research", 1]]),
    a("分工明确，按时交付", [["project", 2], ["campaign", 1]]),
    a("展示对象能产生兴趣或参与", [["campaign", 2], ["community", 1]])
  ]),
  q("q18", "你看到用户反馈很分散，会怎么整理？", [
    a("按场景和情绪把反馈分组", [["research", 2], ["ux", 1]]),
    a("按功能步骤标出问题出现在哪里", [["ux", 2], ["process", 1]]),
    a("按影响目标的严重程度排序", [["strategy", 2], ["growth", 1]]),
    a("整理成一页清晰汇报给团队", [["content", 2], ["project", 1]]),
    a("把能马上处理的事派给对应负责人", [["project", 2], ["process", 1]])
  ]),
  q("q19", "下面哪件事最让你有成就感？", [
    a("把一个难懂页面改得一看就会用", [["ux", 2], ["content", 1]]),
    a("让一次活动从没人理到有人参加", [["campaign", 2], ["community", 1]]),
    a("通过观察发现用户真正的问题", [["research", 2], ["strategy", 1]]),
    a("把混乱任务推进到准时完成", [["project", 2], ["process", 1]]),
    a("用证据说明为什么要改某一步", [["growth", 2], ["strategy", 1]])
  ]),
  q("q20", "你更想避开哪种状态？", [
    a("一直和陌生用户沟通", [["research", -2], ["process", 1]]),
    a("一直写文案和改表达", [["content", -2], ["growth", 1]]),
    a("一直处理临时变化和催进度", [["project", -2], ["ux", 1]]),
    a("一直面对不确定数据找规律", [["growth", -2], ["community", 1]]),
    a("一直维护群和做互动", [["community", -2], ["strategy", 1]])
  ]),
  q("q21", "如果你要帮一个产品做新手引导，你会重点看？", [
    a("用户第一眼能不能知道下一步做什么", [["ux", 2], ["content", 1]]),
    a("引导是否覆盖不同用户的不同需求", [["research", 2], ["strategy", 1]]),
    a("引导结束后用户有没有继续使用", [["growth", 2], ["ux", 1]]),
    a("引导文案是不是简单直接", [["content", 2], ["ux", 1]]),
    a("设计、开发、运营谁在什么时候配合", [["project", 2], ["process", 1]])
  ]),
  q("q22", "你更能接受哪种不确定？", [
    a("先访谈几个人，再慢慢归纳需求", [["research", 2], ["ux", 1]]),
    a("先上线一个小活动，再看真实参与情况", [["campaign", 2], ["growth", 1]]),
    a("先做一个粗略方案，再协调大家补齐", [["project", 2], ["process", 1]]),
    a("先提出判断框架，再逐步找证据", [["strategy", 2], ["growth", 1]]),
    a("先发几种内容，观察哪种更受欢迎", [["content", 2], ["growth", 1]])
  ]),
  q("q23", "当一个任务没人明确负责时，你会？", [
    a("主动把任务拆开，问清每部分谁来做", [["project", 2], ["process", 1]]),
    a("先判断这件事对目标到底重不重要", [["strategy", 2], ["growth", 1]]),
    a("写一份清楚说明，让大家理解为什么要做", [["content", 2], ["project", 1]]),
    a("找受影响的人确认真实需求", [["research", 2], ["community", 1]]),
    a("先把最影响用户体验的部分补上", [["ux", 2], ["process", 1]])
  ]),
  q("q24", "你希望实习每天更多接触什么？", [
    a("真实用户和他们的反馈", [["research", 2], ["community", 1]]),
    a("功能、页面和使用路径", [["ux", 2], ["process", 1]]),
    a("内容、标题和平台表达", [["content", 2], ["campaign", 1]]),
    a("活动、资源和执行节奏", [["campaign", 2], ["project", 1]]),
    a("目标、数据和决策依据", [["strategy", 2], ["growth", 1]])
  ]),
  q("q25", "如果结果显示你适合多个方向，你更愿意怎么验证？", [
    a("做一个小项目，看自己最享受哪部分", [["project", 2], ["strategy", 1]]),
    a("找相关岗位的人聊聊真实工作内容", [["research", 2], ["community", 1]]),
    a("投递不同岗位，用反馈判断机会", [["growth", 2], ["strategy", 1]]),
    a("先选最容易做作品集的方向起步", [["content", 2], ["project", 1]]),
    a("拆出共同能力，做一个复合型项目", [["strategy", 2], ["process", 1]])
  ])
];

const actionPlans = Object.fromEntries(Object.keys(directions).map((key) => [
  key,
  {
    days: [
      day("Day 1", "了解方向", "弄清这个方向的日常工作", "看 3 个岗位描述，圈出反复出现的任务", "整理 5 个高频任务词"),
      day("Day 2", "找一个小场景", "选一个自己熟悉、能快速观察的对象", "从校园、社团、账号、App 里选一个具体场景", "写下场景和目标用户"),
      day("Day 3", "收集真实材料", "避免只靠自己想象", "找 3 个同学聊天，或整理 10 条真实反馈", "得到一页原始反馈"),
      day("Day 4", "拆问题", "把现象变成可以解决的问题", "按步骤、原因、影响程度整理材料", "得到问题清单"),
      day("Day 5", "提出方案", "给出能落地的小改法", "写 3 个改进点，并说明为什么先做它", "得到改进方案"),
      day("Day 6", "做成作品集", "把过程讲得清楚", "整理背景、问题、分析、方案、预期结果", "得到作品集初稿"),
      day("Day 7", "准备投递表达", "把项目变成能讲给面试官听的经历", "提炼岗位词、关键词和 1 分钟项目介绍", "得到投递摘要")
    ]
  }
]));

const jargonTerms = Object.fromEntries(Object.keys(directions).map((key) => [
  key,
  [
    term("复盘", "事情做完后，看哪里有效、哪里没用，下次怎么改。"),
    term("指标", "用来判断事情有没有变好的数字。"),
    term("转化", "用户从看到信息到完成关键动作，比如报名、关注或私信。"),
    term("用户反馈", "用户真实说过或做过的内容，用来判断问题。")
  ]
]));

const portfolioThemes = {
  ux: "做一个常用 App 的体验优化项目",
  process: "设计一个校园事务线上处理流程",
  growth: "分析一个报名或关注路径的流失问题",
  content: "搭建一个面向大学生求职的内容账号方案",
  campaign: "策划一场线上打卡或资料领取活动",
  community: "设计一个求职互助社群运营方案",
  research: "完成一次小型用户访谈和需求洞察项目",
  strategy: "做一个竞品和机会判断分析项目",
  project: "推进一个从计划到复盘的小型项目"
};

const portfolioHighlights = {
  ux: "重点展示你如何让流程更顺手。",
  process: "重点展示你如何把规则和步骤讲清楚。",
  growth: "重点展示你如何用数字判断优先级。",
  content: "重点展示你的表达、选题和内容结构。",
  campaign: "重点展示你如何设计参与路径。",
  community: "重点展示你如何让用户愿意互动和留下。",
  research: "重点展示你如何从真实反馈里发现问题。",
  strategy: "重点展示你如何比较方案并做取舍。",
  project: "重点展示你的排期、协调和落地能力。"
};

function q(id, text, answers) {
  return { id, text, answers };
}

function a(text, weights) {
  return { text, weights: weights.map(([key, value]) => ({ key, value })) };
}

function day(label, title, goal, steps, output) {
  return { label, title, goal, steps, output };
}

function term(label, explanation) {
  return { label, explanation };
}

const data = {
  directions,
  questions,
  actionPlans,
  jargonTerms,
  portfolioThemes,
  portfolioHighlights
};

if (typeof window !== "undefined") {
  window.InternTestData = data;
}

if (typeof module !== "undefined") {
  module.exports = { data };
}
```

- [ ] **Step 4: Run tests**

Run:

```bash
npm test
```

Expected: PASS for 4 tests.

- [ ] **Step 5: Commit data model**

Run:

```bash
git add data.js test/scoring.test.js
git commit -m "feat: add expanded quiz data model"
```

Expected: commit succeeds.

## Task 3: Add Scoring Logic

**Files:**
- Create: `scoring.js`
- Modify: `test/scoring.test.js`

- [ ] **Step 1: Add scoring tests**

Append to `test/scoring.test.js`:

```js
const { scoreAnswers, selectResult, buildPortfolioSuggestion } = require("../scoring.js");

test("scores weighted answers across directions", () => {
  const scores = scoreAnswers({
    q01: 1,
    q02: 0,
    q03: 1
  }, data.questions, data.directions);

  assert.ok(scores.growth > 0);
  assert.ok(scores.campaign > 0);
  assert.ok(scores.ux > 0);
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
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
npm test
```

Expected: FAIL because `../scoring.js` does not exist.

- [ ] **Step 3: Create `scoring.js`**

Create `scoring.js`:

```js
function createEmptyScores(directions) {
  return Object.fromEntries(Object.keys(directions).map((key) => [key, 0]));
}

function scoreAnswers(answersByQuestionId, questions, directions) {
  const scores = createEmptyScores(directions);

  for (const question of questions) {
    const answerIndex = answersByQuestionId[question.id];
    if (!Number.isInteger(answerIndex)) continue;

    const answer = question.answers[answerIndex];
    if (!answer) continue;

    for (const weight of answer.weights) {
      scores[weight.key] += weight.value;
    }
  }

  return scores;
}

function selectResult(scores) {
  const ranked = Object.entries(scores)
    .sort((a, b) => b[1] - a[1])
    .map(([key, value]) => ({ key, value }));

  const main = ranked[0].key;
  const mainScore = ranked[0].value;
  const secondScore = ranked[1] ? ranked[1].value : 0;
  const thirdScore = ranked[2] ? ranked[2].value : 0;
  const scoreSpread = mainScore - (ranked[4] ? ranked[4].value : 0);
  const isMultiSided = scoreSpread <= 3;

  const supporting = [ranked[1].key];
  if (thirdScore === secondScore || Math.abs(thirdScore - secondScore) <= 1) {
    supporting.push(ranked[2].key);
  }

  return {
    main,
    supporting: supporting.slice(0, 2),
    ranked,
    isMultiSided
  };
}

function normalizeScores(scores) {
  const values = Object.values(scores);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  return Object.fromEntries(
    Object.entries(scores).map(([key, value]) => [
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
```

- [ ] **Step 4: Run tests**

Run:

```bash
npm test
```

Expected: PASS for 8 tests.

- [ ] **Step 5: Commit scoring**

Run:

```bash
git add scoring.js test/scoring.test.js
git commit -m "feat: add weighted scoring logic"
```

Expected: commit succeeds.

## Task 4: Update HTML Structure

**Files:**
- Modify: `index.html`

- [ ] **Step 1: Replace script loading order**

At the bottom of `index.html`, replace the current script tag with:

```html
    <script src="./data.js"></script>
    <script src="./scoring.js"></script>
    <script src="./script.js"></script>
```

- [ ] **Step 2: Update home copy and count**

Change the home title, pill, and supporting copy to:

```html
<span class="brand-mark">实习隐藏人格测试</span>
<span class="pill">25 道白话场景题</span>
...
<h1 id="home-title">测测你的互联网实习隐藏人格</h1>
<p class="hero-copy">
  不用先懂产品、运营和行业黑话。根据你面对真实场景时的自然反应，找到更值得优先尝试的实习方向。
</p>
```

- [ ] **Step 3: Replace result content grid**

Inside `<section id="result" ...>`, keep the section shell and replace the inner result body with containers used by `script.js`:

```html
<div class="result-hero">
  <div id="avatarBadge" class="avatar-badge" aria-hidden="true"></div>
  <div>
    <p class="eyebrow">你的实习隐藏人格</p>
    <h1 id="resultTitle"></h1>
    <p id="resultSummary"></p>
  </div>
</div>

<div id="multiNote" class="multi-note"></div>

<div class="content-grid">
  <section class="panel support-panel">
    <h2>辅助方向</h2>
    <div id="supportingDirections"></div>
  </section>

  <section class="panel">
    <h2>能力分布</h2>
    <div id="scoreBars" class="score-bars"></div>
  </section>

  <section class="panel wide">
    <h2>三步路线</h2>
    <div id="routeSteps" class="route-steps"></div>
  </section>

  <section class="panel wide">
    <h2>7 天行动计划</h2>
    <div id="actionPlan" class="day-list"></div>
  </section>

  <section class="panel wide project-panel">
    <h2>作品集项目建议</h2>
    <p id="projectIdea"></p>
  </section>

  <section class="panel">
    <h2>适合搜索的岗位</h2>
    <div class="job-columns">
      <div>
        <h3>产品岗</h3>
        <ul id="productJobs"></ul>
      </div>
      <div>
        <h3>运营岗</h3>
        <ul id="operationJobs"></ul>
      </div>
    </div>
  </section>

  <section class="panel">
    <h2>投递关键词</h2>
    <div id="applicationKeywords" class="keyword-list"></div>
  </section>
</div>

<div id="jargonSheet" class="jargon-sheet" hidden></div>
```

- [ ] **Step 4: Commit HTML**

Run:

```bash
git add index.html
git commit -m "feat: update quiz page structure"
```

Expected: commit succeeds.

## Task 5: Rewrite Browser App Rendering

**Files:**
- Modify: `script.js`

- [ ] **Step 1: Replace global state and initialization**

Replace the top of `script.js` with:

```js
const data = window.InternTestData;
const scoring = window.InternTestScoring;

let currentIndex = 0;
let answersByQuestionId = {};

const screens = {
  home: document.getElementById("home"),
  quiz: document.getElementById("quiz"),
  loading: document.getElementById("loading"),
  result: document.getElementById("result")
};
```

- [ ] **Step 2: Add screen and quiz rendering helpers**

Add:

```js
function showScreen(name) {
  Object.values(screens).forEach((screen) => screen.classList.remove("is-active"));
  screens[name].classList.add("is-active");
}

function renderQuestion() {
  const question = data.questions[currentIndex];
  document.getElementById("questionMeta").textContent = `第 ${currentIndex + 1} / ${data.questions.length} 题`;
  document.getElementById("progressBar").style.width = `${((currentIndex + 1) / data.questions.length) * 100}%`;
  document.getElementById("questionText").textContent = question.text;

  const list = document.getElementById("optionsList");
  list.innerHTML = "";

  question.answers.forEach((answer, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "option-btn";
    button.textContent = answer.text;
    if (answersByQuestionId[question.id] === index) {
      button.classList.add("is-selected");
    }
    button.addEventListener("click", () => selectAnswer(question.id, index));
    list.appendChild(button);
  });

  document.getElementById("prevBtn").disabled = currentIndex === 0;
}

function selectAnswer(questionId, answerIndex) {
  answersByQuestionId[questionId] = answerIndex;
  renderQuestion();

  window.setTimeout(() => {
    if (currentIndex < data.questions.length - 1) {
      currentIndex += 1;
      renderQuestion();
      return;
    }
    showLoadingThenResult();
  }, 180);
}
```

- [ ] **Step 3: Add result rendering**

Add:

```js
function showLoadingThenResult() {
  showScreen("loading");
  window.setTimeout(() => {
    renderResult();
    showScreen("result");
  }, 650);
}

function renderResult() {
  const rawScores = scoring.scoreAnswers(answersByQuestionId, data.questions, data.directions);
  const result = scoring.selectResult(rawScores);
  const normalized = scoring.normalizeScores(rawScores);
  const main = data.directions[result.main];
  const firstSupport = result.supporting[0];

  document.getElementById("avatarBadge").innerHTML = renderAvatar(result.main);
  document.getElementById("resultTitle").textContent = `${main.animal} ${main.label}`;
  document.getElementById("resultSummary").innerHTML = withJargon(main.summary, result.main);

  const multiNote = document.getElementById("multiNote");
  multiNote.textContent = result.isMultiSided
    ? "你的兴趣和工作方式比较多面，不是没有方向，而是可迁移能力比较强。建议先选一个最容易做作品集的方向起步。"
    : "";
  multiNote.hidden = !result.isMultiSided;

  renderSupporting(result.supporting);
  renderScoreBars(normalized);
  renderRouteSteps();
  renderActionPlan(result.main);
  renderJobs(main);
  renderKeywords(main.applicationKeywords);

  document.getElementById("projectIdea").innerHTML = withJargon(
    scoring.buildPortfolioSuggestion(result.main, firstSupport, data),
    result.main
  );
}
```

- [ ] **Step 4: Add section renderers**

Add:

```js
function renderSupporting(supportingKeys) {
  const container = document.getElementById("supportingDirections");
  container.innerHTML = supportingKeys.map((key) => {
    const direction = data.directions[key];
    return `<article class="support-item"><strong>${direction.animal} ${direction.label}</strong><p>${direction.summary}</p></article>`;
  }).join("");
}

function renderScoreBars(scores) {
  const container = document.getElementById("scoreBars");
  container.innerHTML = Object.entries(scores)
    .sort((a, b) => b[1] - a[1])
    .map(([key, value]) => {
      const direction = data.directions[key];
      return `<div class="score-row"><span>${direction.label}</span><div><i style="width:${value}%"></i></div><em>${value}</em></div>`;
    })
    .join("");
}

function renderRouteSteps() {
  const steps = [
    ["先看懂", "知道这个方向在实习里每天会做什么。"],
    ["做项目", "用一个小作品证明你能把想法落地。"],
    ["去投递", "用岗位词和关键词开始搜索、包装经历。"]
  ];
  document.getElementById("routeSteps").innerHTML = steps
    .map(([title, text], index) => `<article><span>${index + 1}</span><strong>${title}</strong><p>${text}</p></article>`)
    .join("");
}

function renderActionPlan(mainKey) {
  const container = document.getElementById("actionPlan");
  container.innerHTML = data.actionPlans[mainKey].days.map((item, index) => `
    <article class="day-item">
      <button type="button" class="day-toggle" aria-expanded="false" data-day="${index}">
        <span>${item.label}</span>
        <strong>${item.title}</strong>
      </button>
      <div class="day-detail" hidden>
        <p><b>今天目标：</b>${item.goal}</p>
        <p><b>具体怎么做：</b>${item.steps}</p>
        <p><b>当天产出：</b>${item.output}</p>
        <button type="button" class="ai-teaser" disabled>继续追问 AI（下一阶段开放）</button>
      </div>
    </article>
  `).join("");
}

function renderJobs(direction) {
  fillList("productJobs", direction.productJobs);
  fillList("operationJobs", direction.operationJobs);
}

function renderKeywords(keywords) {
  document.getElementById("applicationKeywords").innerHTML = keywords
    .map((keyword) => `<span>${keyword}</span>`)
    .join("");
}

function fillList(id, items) {
  document.getElementById(id).innerHTML = items.map((item) => `<li>${item}</li>`).join("");
}

function renderAvatar(key) {
  const direction = data.directions[key];
  return `<div class="animal-sticker animal-${key}"><span>${direction.animal}</span><small>${direction.shortLabel}</small></div>`;
}
```

- [ ] **Step 5: Add jargon and event wiring**

Add:

```js
function withJargon(text, directionKey) {
  return data.jargonTerms[directionKey].reduce((html, term) => {
    return html.replaceAll(
      term.label,
      `<button type="button" class="jargon-link" data-term="${term.label}" data-explanation="${term.explanation}">${term.label}</button>`
    );
  }, text);
}

function toggleDay(button) {
  const detail = button.nextElementSibling;
  const expanded = button.getAttribute("aria-expanded") === "true";
  button.setAttribute("aria-expanded", String(!expanded));
  detail.hidden = expanded;
}

function showJargon(button) {
  const sheet = document.getElementById("jargonSheet");
  sheet.hidden = false;
  sheet.innerHTML = `
    <div class="jargon-card" role="dialog" aria-label="${button.dataset.term}">
      <button type="button" class="jargon-close" aria-label="关闭">×</button>
      <strong>${button.dataset.term}</strong>
      <p>${button.dataset.explanation}</p>
    </div>
  `;
}

document.addEventListener("click", (event) => {
  const dayButton = event.target.closest(".day-toggle");
  if (dayButton) toggleDay(dayButton);

  const jargonButton = event.target.closest(".jargon-link");
  if (jargonButton) showJargon(jargonButton);

  if (event.target.closest(".jargon-close") || event.target.id === "jargonSheet") {
    document.getElementById("jargonSheet").hidden = true;
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    document.getElementById("jargonSheet").hidden = true;
  }
});
```

- [ ] **Step 6: Update existing button listeners**

Ensure the bottom of `script.js` contains:

```js
document.getElementById("startBtn").addEventListener("click", () => {
  currentIndex = 0;
  answersByQuestionId = {};
  renderQuestion();
  showScreen("quiz");
});

document.getElementById("backHomeBtn").addEventListener("click", () => showScreen("home"));

document.getElementById("prevBtn").addEventListener("click", () => {
  if (currentIndex > 0) {
    currentIndex -= 1;
    renderQuestion();
  }
});

document.getElementById("restartBtn").addEventListener("click", () => {
  currentIndex = 0;
  answersByQuestionId = {};
  renderQuestion();
  showScreen("quiz");
});

document.getElementById("copyBtn").addEventListener("click", async () => {
  const title = document.getElementById("resultTitle").textContent;
  const summary = document.getElementById("resultSummary").textContent;
  const project = document.getElementById("projectIdea").textContent;
  const text = `${title}\n${summary}\n作品集建议：${project}`;

  try {
    await navigator.clipboard.writeText(text);
    document.getElementById("copyBtn").textContent = "已复制";
    window.setTimeout(() => {
      document.getElementById("copyBtn").textContent = "复制结果摘要";
    }, 1200);
  } catch {
    window.prompt("复制失败，可以手动复制这段摘要：", text);
  }
});
```

- [ ] **Step 7: Run tests and browser smoke check**

Run:

```bash
npm test
```

Expected: PASS for all tests.

Open `index.html` in a browser, complete the quiz, and verify the result page renders.

- [ ] **Step 8: Commit rendering**

Run:

```bash
git add script.js
git commit -m "feat: render expanded quiz results"
```

Expected: commit succeeds.

## Task 6: Apply Visual Design

**Files:**
- Modify: `styles.css`

- [ ] **Step 1: Replace color tokens**

Update `:root`:

```css
:root {
  color-scheme: light;
  --bg: #f7f8fc;
  --surface: #ffffff;
  --surface-soft: #eef6ff;
  --surface-warm: #fff7ed;
  --text: #172033;
  --muted: #667085;
  --line: #dce3ee;
  --accent: #3b82f6;
  --accent-strong: #2563eb;
  --mint: #7dd3fc;
  --peach: #fdba74;
  --rose: #f9a8d4;
  --shadow: 0 16px 42px rgba(23, 32, 51, 0.10);
}
```

- [ ] **Step 2: Add avatar, result, accordion, and jargon styles**

Append:

```css
.result-hero {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: center;
  gap: 24px;
  padding: 42px 0 28px;
}

.avatar-badge {
  width: 156px;
  aspect-ratio: 1;
}

.animal-sticker {
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
  gap: 4px;
  border: 3px solid #ffffff;
  border-radius: 32px;
  background: linear-gradient(145deg, #e0f2fe, #fff7ed);
  box-shadow: 8px 8px 0 rgba(59, 130, 246, 0.14), var(--shadow);
  text-align: center;
}

.animal-sticker span {
  font-size: 26px;
  font-weight: 850;
}

.animal-sticker small {
  color: var(--muted);
  font-weight: 750;
}

.multi-note {
  margin-bottom: 18px;
  padding: 14px 16px;
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  background: #eff6ff;
  color: #1e3a8a;
  line-height: 1.6;
}

.support-item {
  padding: 14px 0;
  border-bottom: 1px solid var(--line);
}

.support-item:last-child {
  border-bottom: 0;
}

.score-row {
  display: grid;
  grid-template-columns: 112px minmax(0, 1fr) 36px;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
  color: #475467;
  font-size: 14px;
}

.score-row div {
  height: 9px;
  overflow: hidden;
  border-radius: 999px;
  background: #e7edf6;
}

.score-row i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--accent);
}

.score-row em {
  color: var(--muted);
  font-style: normal;
  text-align: right;
}

.route-steps {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.route-steps article {
  padding: 16px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #f8fafc;
}

.route-steps span {
  display: inline-grid;
  width: 28px;
  height: 28px;
  place-items: center;
  margin-bottom: 10px;
  border-radius: 999px;
  background: var(--accent);
  color: #fff;
  font-weight: 800;
}

.day-list {
  display: grid;
  gap: 10px;
}

.day-item {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #fff;
  overflow: hidden;
}

.day-toggle {
  width: 100%;
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr);
  gap: 12px;
  align-items: center;
  min-height: 58px;
  border: 0;
  background: transparent;
  color: var(--text);
  cursor: pointer;
  text-align: left;
}

.day-toggle span {
  color: var(--accent);
  font-weight: 850;
  text-align: center;
}

.day-toggle strong {
  padding-right: 16px;
}

.day-detail {
  padding: 0 18px 18px 84px;
  color: #475467;
  line-height: 1.65;
}

.ai-teaser {
  min-height: 38px;
  border: 1px dashed #bfdbfe;
  border-radius: 8px;
  background: #eff6ff;
  color: #1d4ed8;
}

.keyword-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.keyword-list span {
  border-radius: 999px;
  background: #eef6ff;
  color: #1d4ed8;
  padding: 7px 10px;
  font-size: 14px;
  font-weight: 700;
}

.jargon-link {
  border: 0;
  border-bottom: 2px dotted var(--accent);
  background: transparent;
  color: var(--accent-strong);
  cursor: pointer;
  font: inherit;
  padding: 0 1px;
}

.jargon-sheet {
  position: fixed;
  inset: 0;
  z-index: 20;
  display: grid;
  place-items: center;
  background: rgba(15, 23, 42, 0.22);
  padding: 20px;
}

.jargon-card {
  width: min(360px, 100%);
  position: relative;
  border-radius: 12px;
  background: #fff;
  box-shadow: var(--shadow);
  padding: 20px;
}

.jargon-card strong {
  display: block;
  margin-bottom: 8px;
}

.jargon-close {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 32px;
  height: 32px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: #fff;
  cursor: pointer;
}
```

- [ ] **Step 3: Add responsive adjustments**

Append:

```css
@media (max-width: 760px) {
  .result-hero {
    grid-template-columns: 1fr;
    padding-top: 28px;
  }

  .avatar-badge {
    width: 132px;
  }

  .content-grid,
  .preview-grid,
  .route-steps {
    grid-template-columns: 1fr;
  }

  .score-row {
    grid-template-columns: 96px minmax(0, 1fr) 30px;
  }

  .day-toggle {
    grid-template-columns: 64px minmax(0, 1fr);
  }

  .day-detail {
    padding-left: 76px;
  }

  .jargon-sheet {
    align-items: end;
    padding: 16px;
  }

  .jargon-card {
    border-radius: 16px;
  }
}
```

- [ ] **Step 4: Run tests and visual smoke check**

Run:

```bash
npm test
```

Expected: PASS for all tests.

Open `index.html` at desktop and mobile widths. Confirm text does not overlap, colors are restrained, accordions are readable, and the jargon sheet fits on mobile.

- [ ] **Step 5: Commit styles**

Run:

```bash
git add styles.css
git commit -m "style: refresh quiz visual design"
```

Expected: commit succeeds.

## Task 7: Final Verification

**Files:**
- Modify if needed: `index.html`, `styles.css`, `script.js`, `data.js`, `scoring.js`, `test/scoring.test.js`

- [ ] **Step 1: Run automated tests**

Run:

```bash
npm test
```

Expected: all tests pass.

- [ ] **Step 2: Manual end-to-end quiz check**

Open:

```text
/Users/dadaxu/vibe-coding/intern-direction-test/index.html
```

Expected:

- Home page says "测测你的互联网实习隐藏人格".
- Quiz shows 25 questions.
- Previous button works.
- Selection auto-advances.
- Result page shows one main direction.
- Result page shows one or two supporting directions.
- Score bars show all 9 directions.
- 7-day plan rows expand and collapse.
- Jargon terms open an explanation and close by Escape.
- Copy summary changes the button text to "已复制" or shows a manual fallback prompt.

- [ ] **Step 3: Commit final fixes**

If verification required edits, run:

```bash
git add index.html styles.css script.js data.js scoring.js test/scoring.test.js
git commit -m "fix: polish upgraded quiz flow"
```

Expected: commit succeeds when files changed. If no files changed, skip this commit.

- [ ] **Step 4: Review git status**

Run:

```bash
git status --short
```

Expected: no output.

## Self-Review

- Spec coverage: This plan covers static Phase 1, 9 directions, 25 questions, weighted scoring, main/support result selection, multi-sided copy, 3-step route, 7-day expandable action plan, portfolio suggestion by main/support direction, job and application keywords, inline jargon explanations, visual refresh, and copy summary.
- Scope check: Runtime AI, resume editing, accounts, analytics, and backend work remain outside this plan.
- Type consistency: The data keys used in `data.js`, `scoring.js`, `script.js`, and tests are `directions`, `questions`, `actionPlans`, `jargonTerms`, `portfolioThemes`, and `portfolioHighlights`.
- Execution risk: Animal avatars are implemented as styled sticker badges with animal names in Phase 1. Replacing them with generated bitmap assets can be a separate visual-asset task after this plan if desired.
