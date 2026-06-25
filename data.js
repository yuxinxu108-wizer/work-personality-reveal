(() => {
const directions = {
  ux: {
    label: "用户体验型",
    shortLabel: "C 端产品",
    animal: "小猫",
    avatarSrc: "./assets/avatars/ux-cat.png",
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
    avatarSrc: "./assets/avatars/process-beaver.png",
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
    avatarSrc: "./assets/avatars/growth-fox.png",
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
    avatarSrc: "./assets/avatars/content-parrot.png",
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
    avatarSrc: "./assets/avatars/campaign-rabbit.png",
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
    avatarSrc: "./assets/avatars/community-otter.png",
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
    avatarSrc: "./assets/avatars/research-deer.png",
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
    avatarSrc: "./assets/avatars/strategy-owl.png",
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
    avatarSrc: "./assets/avatars/project-border-collie.png",
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
    a("一张完整的流程图", [["process", 2], ["ux", 1]]),
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
})();
