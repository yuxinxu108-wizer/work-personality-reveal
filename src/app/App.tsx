import React, { useEffect, useRef, useState } from "react";
import {
  ArrowRight,
  ChevronRight,
  CheckCircle2,
  AlertCircle,
  XCircle,
  FileText,
  Target,
  Layers,
  Compass,
  Briefcase,
  BookOpen,
  BarChart2,
  Users,
  Megaphone,
  TrendingUp,
  PenLine,
  MessageSquare,
  Upload,
  ChevronDown,
  Sparkles,
  ArrowLeft,
  Copy,
  Download,
  Info,
  Check,
} from "lucide-react";
import { Step4Chat } from "./components/Step4Chat";
import {
  assessmentQuestions,
  buildAssessmentShareText,
  buildAssessmentResult,
} from "./assessment.js";
import {
  fetchBackendQuestions,
  submitBackendAssessment,
} from "./backendApi.js";
import { getRoleProfile } from "./roleCatalog.js";
import {
  buildAiMaterialsRequest,
  createFallbackMaterials,
  normalizeAiMaterials,
} from "./aiMaterials.js";

// ─── Types ───────────────────────────────────────────────────────────────────

type Page =
  | "home"
  | "step1"
  | "pathA"
  | "pathB"
  | "pathC"
  | "pathD"
  | "step2"
  | "step3"
  | "step4"
  | "step5";

type EvidenceStatus = "sufficient" | "needs-more" | "not-recommended";

interface AppState {
  currentPage: Page;
  targetRole: string;
  jdText: string;
  experiences: string[];
}

type ExperienceDraft = {
  name: string;
  type: string;
  whatDid: string;
  output: string;
  evidenceText: string;
};

type AiMaterials = ReturnType<typeof normalizeAiMaterials>;

// ─── Shared Components ───────────────────────────────────────────────────────

function EvidenceTag({ status }: { status: EvidenceStatus }) {
  if (status === "sufficient") {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
        <CheckCircle2 className="w-3 h-3" />
        证据充分
      </span>
    );
  }
  if (status === "needs-more") {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200">
        <AlertCircle className="w-3 h-3" />
        需要补充
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-slate-50 text-slate-500 border border-slate-200">
      <XCircle className="w-3 h-3" />
      不建议写
    </span>
  );
}

function Header({
  onHome,
  showBack,
  onBack,
}: {
  onHome: () => void;
  showBack?: boolean;
  onBack?: () => void;
}) {
  return (
    <header className="sticky top-0 z-50 bg-white/90 backdrop-blur-sm border-b border-border">
      <div className="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">
        <div className="flex items-center gap-3">
          {showBack && onBack && (
            <button
              onClick={onBack}
              className="text-muted-foreground hover:text-foreground transition-colors p-1 -ml-1"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
          )}
          <button
            onClick={onHome}
            className="flex items-center gap-2 font-semibold text-foreground hover:opacity-80 transition-opacity"
            style={{ fontFamily: "'Plus Jakarta Sans', system-ui, sans-serif" }}
          >
            <div className="w-6 h-6 bg-primary rounded flex items-center justify-center">
              <Target className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="text-sm">实习证据向导</span>
          </button>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-xs text-muted-foreground hidden sm:block">
            产品 / 运营实习准备工具
          </span>
          <button className="text-xs text-primary font-medium hover:underline">
            登录
          </button>
        </div>
      </div>
    </header>
  );
}

function StepProgress({ current, total }: { current: number; total: number }) {
  const steps = ["岗位分析", "经历输入", "证据匹配", "材料生成"];
  return (
    <div className="max-w-5xl mx-auto px-6 py-5">
      <div className="flex items-center gap-0">
        {steps.map((step, i) => {
          const stepNum = i + 1;
          const isActive = stepNum === current;
          const isDone = stepNum < current;
          return (
            <div key={i} className="flex items-center">
              <div className="flex items-center gap-2">
                <div
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold transition-all ${
                    isDone
                      ? "bg-primary text-white"
                      : isActive
                      ? "bg-primary text-white ring-2 ring-primary/20"
                      : "bg-muted text-muted-foreground"
                  }`}
                >
                  {isDone ? <Check className="w-3 h-3" /> : stepNum}
                </div>
                <span
                  className={`text-xs font-medium hidden sm:block ${
                    isActive
                      ? "text-foreground"
                      : isDone
                      ? "text-primary"
                      : "text-muted-foreground"
                  }`}
                >
                  {step}
                </span>
              </div>
              {i < steps.length - 1 && (
                <div
                  className={`w-8 sm:w-16 h-px mx-2 ${
                    isDone ? "bg-primary" : "bg-border"
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function PageShell({
  children,
  showProgress,
  progressStep,
  onHome,
  onBack,
  showBack,
}: {
  children: React.ReactNode;
  showProgress?: boolean;
  progressStep?: number;
  onHome: () => void;
  onBack?: () => void;
  showBack?: boolean;
}) {
  return (
    <div
      className="min-h-screen bg-background"
      style={{ fontFamily: "'Plus Jakarta Sans', system-ui, sans-serif" }}
    >
      <Header onHome={onHome} showBack={showBack} onBack={onBack} />
      {showProgress && progressStep && (
        <div className="border-b border-border bg-white">
          <StepProgress current={progressStep} total={4} />
        </div>
      )}
      <main className="max-w-5xl mx-auto px-6 py-10">{children}</main>
    </div>
  );
}

// ─── Page: Home ───────────────────────────────────────────────────────────────

function HomePage({ onStart, onAssess }: { onStart: () => void; onAssess: () => void }) {
  const features = [
    {
      icon: <FileText className="w-5 h-5" />,
      title: "真实 JD 拆解",
      desc: "粘贴任意招聘 JD，自动提取岗位任务、能力要求和可包装机会，不是泛泛解读。",
    },
    {
      icon: <Layers className="w-5 h-5" />,
      title: "经历证据包装",
      desc: "AI 逐条追问你的真实经历，识别可信证据，标注哪些能写、哪些需补充、哪些不建议写。",
    },
    {
      icon: <Briefcase className="w-5 h-5" />,
      title: "求职材料输出",
      desc: "生成简历 bullet、作品集页面结构和面试讲述提纲，每条都带证据状态标注。",
    },
  ];

  return (
    <div
      className="min-h-screen bg-background"
      style={{ fontFamily: "'Plus Jakarta Sans', system-ui, sans-serif" }}
    >
      <Header onHome={() => {}} />

      {/* Hero */}
      <section className="max-w-5xl mx-auto px-6 pt-20 pb-16">
        <div className="max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-secondary text-primary font-medium mb-8 border border-primary/10 text-[12px]">
            <Sparkles className="w-3.5 h-3.5" />
            专为产品 / 运营实习求职设计
          </div>
          <h1
            className="text-4xl sm:text-5xl font-bold text-foreground leading-tight mb-6"
            style={{ fontFamily: "'Lora', Georgia, serif", lineHeight: 1.2 }}
          >
            从目标岗位到简历表达，
            <br />
            <span className="text-primary">一步步</span>准备产品 / 运营实习
          </h1>
          <p className="text-muted-foreground leading-relaxed mb-10 max-w-xl text-[16px]">
            粘贴真实 JD 或选择产品 / 运营岗位，添加你的项目或经历，AI
            帮你拆解岗位要求、识别可信证据，并生成作品集结构、简历 bullet
            和面试讲述提纲。
          </p>
          <div className="flex flex-col sm:flex-row gap-3">
            <button
              onClick={onStart}
              className="inline-flex items-center justify-center gap-2 px-7 py-3.5 bg-primary text-white rounded-lg font-semibold hover:bg-primary/90 transition-all hover:shadow-lg hover:shadow-primary/20 active:scale-[0.98]"
            >
              开始准备
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={onAssess}
              className="inline-flex items-center justify-center gap-2 px-7 py-3.5 bg-white text-foreground border border-border rounded-lg font-medium hover:bg-muted/50 transition-colors"
            >
              <Compass className="w-4 h-4 text-muted-foreground" />
              还不知道方向？先做方向测评
            </button>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-5xl mx-auto px-6 pb-20">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {features.map((f, i) => (
            <div
              key={i}
              className="bg-white rounded-xl border border-border p-6 hover:border-primary/20 hover:shadow-sm transition-all group"
            >
              <div className="w-10 h-10 rounded-lg bg-secondary flex items-center justify-center text-primary mb-4 group-hover:bg-primary group-hover:text-white transition-all">
                {f.icon}
              </div>
              <h3 className="font-semibold text-foreground mb-2">{f.title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {f.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Process */}
      <section className="bg-white border-t border-border">
        <div className="max-w-5xl mx-auto px-6 py-16">
          <h2
            className="text-xl font-semibold text-foreground mb-10 text-center"
            style={{ fontFamily: "'Lora', Georgia, serif" }}
          >
            四步完成求职材料准备
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-6">
            {[
              { num: "01", label: "确定目标岗位", desc: "粘贴 JD 或选择方向" },
              { num: "02", label: "理解岗位要求", desc: "拆解任务、能力与门槛" },
              { num: "03", label: "输入真实经历", desc: "AI 追问获取完整细节" },
              { num: "04", label: "生成求职材料", desc: "简历、作品集、面试稿" },
            ].map((step) => (
              <div key={step.num} className="text-center">
                <div
                  className="text-3xl font-bold text-primary/20 mb-2"
                  style={{ fontFamily: "'JetBrains Mono', monospace" }}
                >
                  {step.num}
                </div>
                <div className="font-semibold text-sm text-foreground mb-1">
                  {step.label}
                </div>
                <div className="text-xs text-muted-foreground">{step.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <footer className="border-t border-border">
        <div className="max-w-5xl mx-auto px-6 py-6 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span className="text-xs text-muted-foreground">
            产品/运营实习证据向导 · 不做娱乐测评，只做可信材料
          </span>
          <span className="text-xs text-muted-foreground">
            仅用于求职辅助，请勿填写虚假经历
          </span>
        </div>
      </footer>
    </div>
  );
}

// ─── Page: Step 1 Status Split ────────────────────────────────────────────────

function Step1Page({
  onNav,
  onHome,
}: {
  onNav: (p: Page) => void;
  onHome: () => void;
}) {
  const cards = [
    {
      icon: <FileText className="w-6 h-6" />,
      title: "我有想投的 JD",
      desc: "已经找到具体招聘信息，想围绕这条 JD 准备材料",
      tag: "最精准",
      tagColor: "bg-primary text-white",
      page: "pathA" as Page,
    },
    {
      icon: <Target className="w-6 h-6" />,
      title: "我有目标岗位",
      desc: "知道自己想做产品或运营哪个方向，但还没有具体 JD",
      tag: "常见",
      tagColor: "bg-secondary text-primary",
      page: "pathB" as Page,
    },
    {
      icon: <Compass className="w-6 h-6" />,
      title: "我不知道方向",
      desc: "对产品和运营都感兴趣，不确定自己更适合哪个方向",
      tag: "需测评",
      tagColor: "bg-muted text-muted-foreground",
      page: "pathC" as Page,
    },
    {
      icon: <Layers className="w-6 h-6" />,
      title: "我只想包装已有经历",
      desc: "已有具体的项目或经历，想直接分析能包装成什么材料",
      tag: "经历优先",
      tagColor: "bg-muted text-muted-foreground",
      page: "pathD" as Page,
    },
  ];

  return (
    <PageShell onHome={onHome} onBack={onHome} showBack>
      <div className="max-w-2xl mx-auto">
        <div className="mb-10">
          <div
            className="text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-3"
            style={{ fontFamily: "'JetBrains Mono', monospace" }}
          >
            Step 1 · 状态确认
          </div>
          <h1 className="text-2xl font-bold text-foreground mb-3">
            你现在准备产品 / 运营实习，处在哪一步？
          </h1>
          <p className="text-muted-foreground">
            选择最符合你现状的入口，后续流程会根据你的情况定制。
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {cards.map((card) => (
            <button
              key={card.page}
              onClick={() => onNav(card.page)}
              className="text-left bg-white border border-border rounded-xl p-6 hover:border-primary/30 hover:shadow-md transition-all group active:scale-[0.99]"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="w-11 h-11 rounded-lg bg-muted flex items-center justify-center text-muted-foreground group-hover:bg-secondary group-hover:text-primary transition-all">
                  {card.icon}
                </div>
                <span
                  className={`text-xs font-medium px-2 py-0.5 rounded-full ${card.tagColor}`}
                >
                  {card.tag}
                </span>
              </div>
              <h3 className="font-semibold text-foreground mb-2">
                {card.title}
              </h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {card.desc}
              </p>
              <div className="mt-4 flex items-center gap-1 text-xs text-primary font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                选择这个入口
                <ChevronRight className="w-3.5 h-3.5" />
              </div>
            </button>
          ))}
        </div>
      </div>
    </PageShell>
  );
}

// ─── Page: Path A – JD Paste ──────────────────────────────────────────────────

function PathAPage({
  onNext,
  onHome,
  onBack,
}: {
  onNext: (targetRole?: string) => void;
  onHome: () => void;
  onBack: () => void;
}) {
  const [jd, setJd] = useState("");
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [city, setCity] = useState("");
  const [source, setSource] = useState("");
  const [error, setError] = useState("");

  const handleAnalyze = () => {
    if (jd.trim().length < 80) {
      setError("JD 内容太短，请粘贴完整招聘描述（建议包含岗位职责和任职要求）。");
      return;
    }
    setError("");
    onNext(role.trim() || undefined);
  };

  return (
    <PageShell onHome={onHome} onBack={onBack} showBack>
      <div className="max-w-2xl mx-auto">
        <div className="mb-8">
          <div
            className="text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-3"
            style={{ fontFamily: "'JetBrains Mono', monospace" }}
          >
            路径 A · 粘贴 JD
          </div>
          <h1 className="text-2xl font-bold text-foreground mb-2">
            粘贴你想投的职位描述
          </h1>
          <p className="text-sm text-muted-foreground">
            请粘贴完整的招聘 JD，包括岗位职责和任职要求。AI
            会自动提取关键信息，不需要你手动整理。
          </p>
        </div>

        <div className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              职位描述 <span className="text-destructive">*</span>
            </label>
            <textarea
              value={jd}
              onChange={(e) => {
                setJd(e.target.value);
                if (error) setError("");
              }}
              placeholder="将完整的 JD 文本粘贴到这里，包括岗位职责、任职要求等…"
              className="w-full h-52 px-4 py-3 bg-white border border-border rounded-lg text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary resize-none transition-all"
            />
            <div className="flex items-center justify-between mt-1.5">
              {error ? (
                <p className="text-xs text-destructive flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" />
                  {error}
                </p>
              ) : (
                <p className="text-xs text-muted-foreground">
                  建议粘贴完整 JD，字数越多分析越准确
                </p>
              )}
              <span className="text-xs text-muted-foreground">
                {jd.length} 字
              </span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                公司名称
                <span className="text-muted-foreground font-normal ml-1">
                  （可选）
                </span>
              </label>
              <input
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                placeholder="如：字节跳动"
                className="w-full px-3 py-2.5 bg-white border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                岗位名称
                <span className="text-muted-foreground font-normal ml-1">
                  （可选）
                </span>
              </label>
              <input
                value={role}
                onChange={(e) => setRole(e.target.value)}
                placeholder="如：产品经理实习生"
                className="w-full px-3 py-2.5 bg-white border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                城市
                <span className="text-muted-foreground font-normal ml-1">
                  （可选）
                </span>
              </label>
              <input
                value={city}
                onChange={(e) => setCity(e.target.value)}
                placeholder="如：北京"
                className="w-full px-3 py-2.5 bg-white border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                JD 来源
                <span className="text-muted-foreground font-normal ml-1">
                  （可选）
                </span>
              </label>
              <input
                value={source}
                onChange={(e) => setSource(e.target.value)}
                placeholder="如：Boss 直聘、实习僧"
                className="w-full px-3 py-2.5 bg-white border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
              />
            </div>
          </div>

          <div className="pt-2">
            <button
              onClick={handleAnalyze}
              className="w-full py-3.5 bg-primary text-white rounded-lg font-semibold hover:bg-primary/90 transition-all hover:shadow-lg hover:shadow-primary/20 active:scale-[0.99] flex items-center justify-center gap-2"
            >
              <Sparkles className="w-4 h-4" />
              分析这条 JD
            </button>
          </div>
        </div>
      </div>
    </PageShell>
  );
}

// ─── Page: Path B – Role Selection ───────────────────────────────────────────

function PathBPage({
  onNext,
  onHome,
  onBack,
}: {
  onNext: (targetRole: string) => void;
  onHome: () => void;
  onBack: () => void;
}) {
  const [selected, setSelected] = useState<string | null>(null);

  const roles = [
    {
      id: "ux-product",
      name: "C 端产品",
      targetRole: "C 端产品",
      icon: <Target className="w-5 h-5" />,
      desc: "面向普通用户的 App / 小程序体验、需求和原型方向",
    },
    {
      id: "process-product",
      name: "B 端产品",
      targetRole: "B 端产品",
      icon: <Briefcase className="w-5 h-5" />,
      desc: "后台、平台、SaaS、商家/运营工作台等流程型产品",
    },
    {
      id: "research",
      name: "用户研究",
      targetRole: "用户研究",
      icon: <Users className="w-5 h-5" />,
      desc: "通过访谈、问卷、反馈归类找到真实用户需求",
    },
    {
      id: "content-ops",
      name: "内容运营",
      targetRole: "内容运营",
      icon: <PenLine className="w-5 h-5" />,
      desc: "选题、文案、账号运营、内容复盘和作品表达",
    },
    {
      id: "growth-ops",
      name: "增长运营",
      targetRole: "增长运营",
      icon: <TrendingUp className="w-5 h-5" />,
      desc: "围绕拉新、转化、留存和数据复盘做优化",
    },
    {
      id: "campaign-ops",
      name: "活动运营",
      targetRole: "活动运营",
      icon: <Megaphone className="w-5 h-5" />,
      desc: "策划活动玩法、宣传路径、报名参与和效果复盘",
    },
    {
      id: "community-ops",
      name: "用户运营与社群",
      targetRole: "用户运营与社群",
      icon: <MessageSquare className="w-5 h-5" />,
      desc: "维护用户关系、社群活跃、用户触达和召回",
    },
    {
      id: "project-ops",
      name: "项目运营",
      targetRole: "项目运营",
      icon: <Layers className="w-5 h-5" />,
      desc: "拆计划、排进度、协调资源、推进项目按时落地",
    },
    {
      id: "strategy-ops",
      name: "策略运营",
      targetRole: "策略运营",
      icon: <BarChart2 className="w-5 h-5" />,
      desc: "分析目标、竞品、资源和优先级，输出策略建议",
    },
  ];

  const selectedRole = roles.find((r) => r.id === selected);
  const selectedProfile = selectedRole ? getRoleProfile(selectedRole.targetRole) : null;

  return (
    <PageShell onHome={onHome} onBack={onBack} showBack>
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <div
            className="text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-3"
            style={{ fontFamily: "'JetBrains Mono', monospace" }}
          >
            路径 B · 目标岗位选择
          </div>
          <h1 className="text-2xl font-bold text-foreground mb-2">
            选择你的目标岗位方向
          </h1>
          <p className="text-sm text-muted-foreground">
            这里按我们沉淀的 9 个产品 / 运营细分方向展示。选择后会展示具体任务、能力解释和可包装机会。
          </p>
        </div>

        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-2.5 mb-8">
          {roles.map((role) => (
            <button
              key={role.id}
              onClick={() => setSelected(role.id)}
              className={`flex flex-col items-center gap-1.5 p-3 rounded-lg border transition-all text-center ${
                selected === role.id
                  ? "border-primary bg-secondary text-primary shadow-sm"
                  : "border-border bg-white text-foreground hover:border-primary/30 hover:bg-muted/40"
              }`}
            >
              <div
                className={`transition-colors ${
                  selected === role.id ? "text-primary" : "text-muted-foreground"
                }`}
              >
                {role.icon}
              </div>
              <span className="text-xs font-medium leading-tight">{role.name}</span>
            </button>
          ))}
        </div>

        {selectedRole && selectedProfile && (
          <div className="bg-white border border-border rounded-xl p-6 mb-6 animate-in fade-in slide-in-from-bottom-2 duration-200">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h2 className="font-semibold text-foreground text-lg">
                  {selectedRole.name}
                </h2>
                <p className="text-xs text-muted-foreground mt-1">
                  {selectedRole.desc}
                </p>
              </div>
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <span
                  style={{ fontFamily: "'JetBrains Mono', monospace" }}
                  className="font-medium text-foreground"
                >
                  {selectedProfile.jdCount.toLocaleString()}+
                </span>
                条相关 JD
              </div>
            </div>

            <div className="grid grid-cols-2 gap-5 mb-5">
              <div>
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2.5">
                  常见任务
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {selectedProfile.tasks.slice(0, 3).map((t: string) => (
                    <span
                      key={t}
                      className="text-xs px-2 py-1 bg-muted rounded-md text-foreground"
                    >
                      {t}
                    </span>
                  ))}
                </div>
              </div>
              <div>
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2.5">
                  常见能力要求
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {selectedProfile.skills.slice(0, 3).map((s: { skill: string }) => (
                    <span
                      key={s.skill}
                      className="text-xs px-2 py-1 bg-secondary rounded-md text-primary"
                    >
                      {s.skill}
                    </span>
                  ))}
                </div>
              </div>
              <div>
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2.5">
                  工具 / 技能 / 材料门槛
                </h4>
                <ul className="space-y-1">
                  {selectedProfile.hardReqs.slice(0, 2).map((r: string) => (
                    <li
                      key={r}
                      className="text-xs text-muted-foreground flex items-start gap-1.5"
                    >
                      <AlertCircle className="w-3 h-3 text-amber-500 mt-0.5 shrink-0" />
                      {r}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2.5">
                  可用经历包装
                </h4>
                <ul className="space-y-1">
                  {selectedProfile.packagable.slice(0, 3).map((p: { opportunity: string }) => (
                    <li
                      key={p.opportunity}
                      className="text-xs text-emerald-700 flex items-start gap-1.5"
                    >
                      <CheckCircle2 className="w-3 h-3 text-emerald-500 mt-0.5 shrink-0" />
                      {p.opportunity}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            <button
              onClick={() => onNext(selectedRole.targetRole)}
              className="w-full py-3 bg-primary text-white rounded-lg font-semibold hover:bg-primary/90 transition-all flex items-center justify-center gap-2"
            >
              使用这个岗位作为我的目标
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        )}

        {!selectedRole && (
          <div className="text-center py-10 text-muted-foreground text-sm">
            选择上方任意岗位，查看详细说明
          </div>
        )}
      </div>
    </PageShell>
  );
}

// ─── Page: Path C – Assessment Quiz ──────────────────────────────────────────

const AUTO_ADVANCE_DELAY_MS = 450;

function AbilityRadar({ items }: { items: Array<{ label: string; score: number }> }) {
  const size = 280;
  const center = size / 2;
  const radius = 92;
  const levels = [0.25, 0.5, 0.75, 1];
  const angleFor = (index: number) =>
    (Math.PI * 2 * index) / items.length - Math.PI / 2;
  const pointFor = (index: number, value: number) => {
    const angle = angleFor(index);
    return {
      x: center + Math.cos(angle) * radius * value,
      y: center + Math.sin(angle) * radius * value,
    };
  };
  const polygon = items
    .map((item, index) => {
      const point = pointFor(index, item.score / 100);
      return `${point.x},${point.y}`;
    })
    .join(" ");

  return (
    <svg
      viewBox={`0 0 ${size} ${size}`}
      className="w-full max-w-[280px] mx-auto"
      role="img"
      aria-label="能力分布雷达图"
    >
      {levels.map((level) => (
        <polygon
          key={level}
          points={items
            .map((_, index) => {
              const point = pointFor(index, level);
              return `${point.x},${point.y}`;
            })
            .join(" ")}
          fill="none"
          stroke="rgba(29, 78, 216, 0.16)"
          strokeWidth="1"
        />
      ))}
      {items.map((_, index) => {
        const end = pointFor(index, 1);
        return (
          <line
            key={index}
            x1={center}
            y1={center}
            x2={end.x}
            y2={end.y}
            stroke="rgba(29, 78, 216, 0.12)"
            strokeWidth="1"
          />
        );
      })}
      <polygon
        points={polygon}
        fill="rgba(29, 78, 216, 0.16)"
        stroke="#1D4ED8"
        strokeWidth="2"
      />
      {items.map((item, index) => {
        const point = pointFor(index, 1.24);
        return (
          <text
            key={item.label}
            x={point.x}
            y={point.y}
            textAnchor="middle"
            dominantBaseline="middle"
            className="fill-muted-foreground"
            style={{ fontSize: "11px", fontWeight: 500 }}
          >
            {item.label}
          </text>
        );
      })}
    </svg>
  );
}

function AbilityScores({
  items,
}: {
  items: Array<{ key: string; label: string; score: number }>;
}) {
  return (
    <div className="space-y-2.5">
      {items.map((item) => (
        <div key={item.key} className="grid grid-cols-[72px_1fr_32px] items-center gap-3">
          <span className="text-xs text-muted-foreground">{item.label}</span>
          <div className="h-2 rounded-full bg-muted overflow-hidden">
            <div
              className="h-full rounded-full bg-primary"
              style={{ width: `${item.score}%` }}
            />
          </div>
          <span
            className="text-xs font-semibold text-foreground tabular-nums text-right"
            style={{ fontFamily: "'JetBrains Mono', monospace" }}
          >
            {item.score}
          </span>
        </div>
      ))}
    </div>
  );
}

function PathCPage({
  onNext,
  onHome,
  onBack,
}: {
  onNext: (targetRole: string) => void;
  onHome: () => void;
  onBack: () => void;
}) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [questions, setQuestions] = useState(assessmentQuestions);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [showResult, setShowResult] = useState(false);
  const [backendStatus, setBackendStatus] = useState<"loading" | "connected" | "fallback">("loading");
  const [backendResult, setBackendResult] = useState<ReturnType<typeof buildAssessmentResult> | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const [shareCopied, setShareCopied] = useState(false);
  const autoAdvanceTimer = useRef<number | null>(null);

  const question = questions[currentIndex] || assessmentQuestions[currentIndex];
  const selectedAnswer = answers[question.id];
  const progress = ((currentIndex + 1) / questions.length) * 100;
  const localResult = buildAssessmentResult(answers);
  const result = backendResult || localResult;
  const supporting = result.supporting[0];
  const title = result.isComposite && supporting
    ? `你的方向倾向：${result.main.label} × ${supporting.label}`
    : `你的主方向：${result.main.label}`;

  useEffect(() => {
    let isMounted = true;

    fetchBackendQuestions()
      .then((backendQuestions) => {
        if (!isMounted) return;
        if (backendQuestions.length > 0) {
          setQuestions(backendQuestions);
          setBackendStatus("connected");
        } else {
          setBackendStatus("fallback");
        }
      })
      .catch(() => {
        if (isMounted) {
          setBackendStatus("fallback");
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    return () => {
      if (autoAdvanceTimer.current !== null) {
        window.clearTimeout(autoAdvanceTimer.current);
      }
    };
  }, []);

  const clearAutoAdvance = () => {
    if (autoAdvanceTimer.current !== null) {
      window.clearTimeout(autoAdvanceTimer.current);
      autoAdvanceTimer.current = null;
    }
  };

  const finishAssessment = async () => {
    setIsSubmitting(true);
    setSubmitError("");
    try {
      const resultFromBackend = await submitBackendAssessment(answers);
      setBackendResult(resultFromBackend);
    } catch (error) {
      setBackendResult(null);
      setSubmitError(
        error instanceof Error
          ? `后端测评接口暂时不可用，已使用本地算法生成结果：${error.message}`
          : "后端测评接口暂时不可用，已使用本地算法生成结果。"
      );
    } finally {
      setIsSubmitting(false);
      setShowResult(true);
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  const advanceFromIndex = (questionIndex: number) => {
    if (questionIndex === questions.length - 1) {
      void finishAssessment();
      return;
    }

    setCurrentIndex((index) =>
      index === questionIndex ? questionIndex + 1 : index
    );
  };

  const selectAnswer = (answerIndex: number) => {
    clearAutoAdvance();
    setAnswers((current) => ({
      ...current,
      [question.id]: answerIndex,
    }));

    const questionIndex = currentIndex;
    autoAdvanceTimer.current = window.setTimeout(() => {
      autoAdvanceTimer.current = null;
      advanceFromIndex(questionIndex);
    }, AUTO_ADVANCE_DELAY_MS);
  };

  const goNextQuestion = () => {
    if (selectedAnswer === undefined) return;
    clearAutoAdvance();
    advanceFromIndex(currentIndex);
  };

  const restartAssessment = () => {
    clearAutoAdvance();
    setAnswers({});
    setBackendResult(null);
    setSubmitError("");
    setCurrentIndex(0);
    setShowResult(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleBack = () => {
    if (showResult) {
      clearAutoAdvance();
      setShowResult(false);
      setCurrentIndex(questions.length - 1);
      window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }
    onBack();
  };

  const shareAssessmentResult = async () => {
    const text = buildAssessmentShareText(result);
    if (navigator.share) {
      try {
        await navigator.share({
          title: "产品/运营实习方向测评结果",
          text,
        });
        return;
      } catch {
        // Fall back to clipboard when native share is cancelled or unavailable.
      }
    }

    if (navigator.clipboard) {
      await navigator.clipboard.writeText(text);
      setShareCopied(true);
      window.setTimeout(() => setShareCopied(false), 1800);
    }
  };

  if (!showResult) {
    return (
      <PageShell onHome={onHome} onBack={handleBack} showBack>
        <div className="max-w-2xl mx-auto">
          <div className="mb-8">
            <div
              className="text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-3"
              style={{ fontFamily: "'JetBrains Mono', monospace" }}
            >
              路径 C · 方向测评
            </div>
            <h1 className="text-2xl font-bold text-foreground mb-2">
              先用 {questions.length} 道题确定一个可尝试方向
            </h1>
            <p className="text-sm text-muted-foreground">
              不需要先懂岗位黑话。按你面对真实场景时最自然的反应选择即可。
            </p>
            <p className="text-xs text-muted-foreground mt-2">
              {backendStatus === "connected"
                ? "已连接本地 FastAPI，题目和提交结果来自数据库。"
                : backendStatus === "loading"
                ? "正在连接本地 FastAPI..."
                : "暂未连接到 FastAPI，当前使用本地题库兜底。"}
            </p>
          </div>

          <div className="bg-white border border-border rounded-xl p-6">
            <div className="flex items-center justify-between gap-4 mb-5">
              <div>
                <div
                  className="text-xs text-muted-foreground mb-1"
                  style={{ fontFamily: "'JetBrains Mono', monospace" }}
                >
                  Question {currentIndex + 1} / {questions.length}
                </div>
                <div className="text-sm font-semibold text-foreground">
                  第 {currentIndex + 1} 题
                </div>
              </div>
              <div className="w-40 h-2 rounded-full bg-muted overflow-hidden">
                <div
                  className="h-full bg-primary rounded-full transition-all"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>

            <h2 className="text-xl font-bold text-foreground mb-5">
              {question.text}
            </h2>

            <div className="space-y-3">
              {question.answers.map((answer: { text: string }, answerIndex: number) => {
                const isSelected = selectedAnswer === answerIndex;
                return (
                  <button
                    key={answer.text}
                    type="button"
                    onClick={() => selectAnswer(answerIndex)}
                    className={`w-full text-left rounded-lg border px-4 py-3 transition-all ${
                      isSelected
                        ? "border-primary bg-secondary text-primary shadow-sm"
                        : "border-border bg-white hover:border-primary/30 hover:bg-muted/30"
                    }`}
                  >
                    <span className="text-sm font-medium">{answer.text}</span>
                  </button>
                );
              })}
            </div>

            <div className="flex items-center justify-between gap-3 mt-6">
              <button
                type="button"
                disabled={currentIndex === 0}
                onClick={() => {
                  clearAutoAdvance();
                  setCurrentIndex((index) => Math.max(0, index - 1));
                }}
                className="px-4 py-2 text-sm font-medium rounded-lg border border-border bg-white text-muted-foreground disabled:opacity-40 disabled:cursor-not-allowed hover:bg-muted/40 transition-colors"
              >
                上一题
              </button>
              <button
                type="button"
                disabled={selectedAnswer === undefined || isSubmitting}
                onClick={goNextQuestion}
                className="px-5 py-2.5 text-sm font-semibold rounded-lg bg-primary text-white disabled:opacity-40 disabled:cursor-not-allowed hover:bg-primary/90 transition-colors inline-flex items-center gap-2"
              >
                {isSubmitting
                  ? "生成结果中..."
                  : currentIndex === questions.length - 1
                  ? "查看结果"
                  : "下一题"}
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </PageShell>
    );
  }

  return (
    <PageShell onHome={onHome} onBack={handleBack} showBack>
      <div className="max-w-5xl mx-auto pb-10">
        <div className="mb-8">
          <div
            className="text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-3"
            style={{ fontFamily: "'JetBrains Mono', monospace" }}
          >
            路径 C · 方向测评结果
          </div>
          <h1 className="text-2xl font-bold text-foreground mb-2">
            你的方向测评结果
          </h1>
          <p className="text-sm text-muted-foreground">
            以下是基于你的答题行为的推荐。测评是辅助参考，不是最终答案，可以根据实际情况调整。
          </p>
          {submitError && (
            <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mt-3">
              {submitError}
            </p>
          )}
        </div>

        <div className="bg-white border border-border rounded-xl p-6 mb-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 mb-6">
            <div className="min-w-0">
              <div className="text-xs text-muted-foreground mb-1">方向类别判断</div>
              <div className="text-2xl font-bold text-foreground mb-2">
                {title}
              </div>
              <p className="text-sm text-muted-foreground max-w-md">
                {result.isComposite && supporting
                  ? `${result.main.personality} 同时你也带有「${supporting.label}」倾向，准备材料时可以把两类证据组合展示。`
                  : result.main.personality}
              </p>
            </div>

            <div className="shrink-0 self-center sm:self-start">
              <div className="w-32 h-32 sm:w-36 sm:h-36 rounded-2xl border border-primary/10 bg-secondary/40 overflow-hidden flex items-center justify-center">
                <img
                  src={result.main.avatarSrc}
                  alt={`${result.main.label}人格图标`}
                  className="w-full h-full object-cover"
                />
              </div>
              <div className="text-center text-xs text-muted-foreground mt-2">
                {result.main.mascotName}型画像
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-[0.9fr_1.1fr] gap-5">
          <div className="bg-white border border-border rounded-xl p-6">
            <h2 className="text-lg font-bold text-foreground mb-5">推荐方向</h2>
            <div className="space-y-4">
              <div>
                <div className="text-xs text-muted-foreground mb-1">主方向</div>
                <div className="font-semibold text-foreground">
                  {result.main.label} / {result.main.roleLabel}
                </div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground mb-1">辅助方向</div>
                <div className="font-semibold text-foreground">
                  {result.supporting.map((item: { label: string }) => item.label).join(" / ")}
                </div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground mb-2">
                  可优先尝试的岗位
                </div>
                <div className="flex flex-wrap gap-2">
                  {result.main.roles.map((role: string) => (
                    <span
                      key={role}
                      className="px-2.5 py-1 rounded border border-primary/15 bg-secondary/60 text-xs font-medium text-primary"
                    >
                      {role}
                    </span>
                  ))}
                </div>
              </div>

              <div className="p-3.5 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-2.5">
                <AlertCircle className="w-4 h-4 text-amber-600 mt-0.5 shrink-0" />
                <div>
                  <div className="text-sm font-medium text-amber-800 mb-0.5">
                    风险提示
                  </div>
                  <div className="text-xs text-amber-700">{result.main.risk}</div>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white border border-border rounded-xl p-6">
            <h2 className="text-lg font-bold text-foreground mb-5">能力分布</h2>
            <div className="grid grid-cols-1 md:grid-cols-[280px_1fr] gap-6 items-center">
              <AbilityRadar items={result.radar} />
              <div>
                <div className="text-sm font-semibold text-foreground mb-4">
                  各能力评分
                </div>
                <AbilityScores
                  items={result.radar.map(
                    (item: { key: string; label: string; score: number }) => ({
                      key: item.key,
                      label: item.label,
                      score: item.score,
                    })
                  )}
                />
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6 flex flex-col sm:flex-row justify-end items-stretch sm:items-center gap-3">
          <button
            onClick={() => window.print()}
            className="px-4 py-3 text-sm font-semibold rounded-lg border border-border bg-white text-foreground hover:bg-muted/40 transition-colors"
          >
            打印 / 保存 PDF
          </button>
          <button
            onClick={shareAssessmentResult}
            className="px-4 py-3 text-sm font-semibold rounded-lg border border-border bg-white text-foreground hover:bg-muted/40 transition-colors"
          >
            {shareCopied ? "已复制分享文案" : "复制分享文案"}
          </button>
          <button
            onClick={restartAssessment}
            className="px-4 py-3 text-sm font-semibold text-muted-foreground hover:text-foreground transition-colors"
          >
            重新测评
        </button>
        <button
          onClick={() => onNext(result.main.roles[0])}
          className="px-5 py-3 bg-primary text-white rounded-lg font-semibold shadow-lg shadow-primary/20 hover:bg-primary/90 transition-all flex items-center justify-center gap-2"
        >
            使用这个方向作为我的目标岗位
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </PageShell>
  );
}

// ─── Page: Path D – Experience First ─────────────────────────────────────────

function PathDPage({
  onNext,
  onHome,
  onBack,
}: {
  onNext: () => void;
  onHome: () => void;
  onBack: () => void;
}) {
  const [name, setName] = useState("");
  const [type, setType] = useState("");
  const [whatDid, setWhatDid] = useState("");
  const [output, setOutput] = useState("");
  const [hasEvidence, setHasEvidence] = useState<string>("");
  const [rolePreference, setRolePreference] = useState("");

  const expTypes = [
    "课程作业",
    "社团活动",
    "比赛",
    "实习",
    "内容账号",
    "调研",
    "数据分析",
    "其他",
  ];

  const canSubmit = name && type && whatDid && output;

  return (
    <PageShell onHome={onHome} onBack={onBack} showBack>
      <div className="max-w-2xl mx-auto">
        <div className="mb-8">
          <div
            className="text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-3"
            style={{ fontFamily: "'JetBrains Mono', monospace" }}
          >
            路径 D · 经历优先输入
          </div>
          <h1 className="text-2xl font-bold text-foreground mb-2">
            先告诉我你有什么经历
          </h1>
          <p className="text-sm text-muted-foreground">
            只填真实发生的事，不需要包装语言。AI
            会根据你的描述分析可以匹配哪些岗位和能力。
          </p>
        </div>

        <div className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              项目或经历名称 <span className="text-destructive">*</span>
            </label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="如：大三第二学期用户行为分析课程项目"
              className="w-full px-3 py-2.5 bg-white border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              经历类型 <span className="text-destructive">*</span>
            </label>
            <div className="flex flex-wrap gap-2">
              {expTypes.map((t) => (
                <button
                  key={t}
                  onClick={() => setType(t)}
                  className={`px-3 py-1.5 rounded-lg text-sm border transition-all ${
                    type === t
                      ? "border-primary bg-secondary text-primary font-medium"
                      : "border-border bg-white text-foreground hover:border-primary/30"
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              你具体做了什么？<span className="text-destructive">*</span>
            </label>
            <textarea
              value={whatDid}
              onChange={(e) => setWhatDid(e.target.value)}
              placeholder="尽量具体，比如：我负责设计问卷、收集了120份回收的数据，然后用 Excel 做了频率分析…"
              className="w-full h-28 px-3 py-2.5 bg-white border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary resize-none transition-all"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              最后产出了什么？<span className="text-destructive">*</span>
            </label>
            <textarea
              value={output}
              onChange={(e) => setOutput(e.target.value)}
              placeholder="如：交了一份12页的分析报告，得到老师90分评价；或者：社团纳新报名人数比去年多了40%…"
              className="w-full h-24 px-3 py-2.5 bg-white border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary resize-none transition-all"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              有没有数据、反馈、链接、截图或文件？
            </label>
            <div className="flex gap-2 mb-2">
              {["有", "没有", "有但不全"].map((opt) => (
                <button
                  key={opt}
                  onClick={() => setHasEvidence(opt)}
                  className={`px-3 py-1.5 rounded-lg text-sm border transition-all ${
                    hasEvidence === opt
                      ? "border-primary bg-secondary text-primary font-medium"
                      : "border-border bg-white text-foreground hover:border-primary/30"
                  }`}
                >
                  {opt}
                </button>
              ))}
            </div>
            {hasEvidence === "有" && (
              <button className="flex items-center gap-2 text-sm text-primary border border-dashed border-primary/30 rounded-lg px-4 py-2.5 hover:bg-secondary/50 transition-colors w-full justify-center">
                <Upload className="w-4 h-4" />
                上传截图或文件（可选）
              </button>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              岗位偏好
              <span className="text-muted-foreground font-normal ml-1">
                （可选，留空则自动推荐）
              </span>
            </label>
            <input
              value={rolePreference}
              onChange={(e) => setRolePreference(e.target.value)}
              placeholder="如：内容运营、用户研究、产品经理…"
              className="w-full px-3 py-2.5 bg-white border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
            />
          </div>

          <button
            onClick={onNext}
            disabled={!canSubmit}
            className="w-full py-3.5 bg-primary text-white rounded-lg font-semibold hover:bg-primary/90 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none hover:shadow-lg hover:shadow-primary/20"
          >
            <Sparkles className="w-4 h-4" />
            分析我的经历
          </button>
        </div>
      </div>
    </PageShell>
  );
}

// ─── Page: Step 2 – Role Understanding ───────────────────────────────────────

function Step2Page({
  onNext,
  onHome,
  onBack,
  targetRole,
}: {
  onNext: () => void;
  onHome: () => void;
  onBack: () => void;
  targetRole: string;
}) {
  const [expanded, setExpanded] = useState<string | null>("skills");
  const targetProfile = getRoleProfile(targetRole);

  const sections = [
    {
      id: "tasks",
      title: "岗位任务：具体做什么",
      icon: <BookOpen className="w-4 h-4" />,
      content: (
        <ul className="space-y-2">
          {[
            ...targetProfile.tasks,
          ].map((task: string, i: number) => (
            <li key={i} className="flex items-start gap-2 text-sm text-foreground">
              <span
                className="text-primary font-mono text-xs mt-1"
                style={{ fontFamily: "'JetBrains Mono', monospace" }}
              >
                {String(i + 1).padStart(2, "0")}
              </span>
              {task}
            </li>
          ))}
        </ul>
      ),
    },
    {
      id: "skills",
      title: "能力要求：是什么意思，怎么证明",
      icon: <Target className="w-4 h-4" />,
      content: (
        <div className="space-y-3.5">
          {targetProfile.skills.map((item: { skill: string; level: string; explain?: string; evidence?: string }) => (
            <div
              key={item.skill}
              className="rounded-lg border border-border p-3 bg-white"
            >
              <div className="flex items-center justify-between gap-3 mb-1.5">
                <span className="text-sm font-medium text-foreground">{item.skill}</span>
                <span
                  className={`text-xs px-2 py-0.5 rounded-full font-medium shrink-0 ${
                    item.level === "高频"
                      ? "bg-primary/10 text-primary"
                      : item.level === "中频"
                      ? "bg-secondary text-secondary-foreground"
                      : "bg-muted text-muted-foreground"
                  }`}
                >
                  {item.level}
                </span>
              </div>
              {item.explain && (
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {item.explain}
                </p>
              )}
              {item.evidence && (
                <p className="text-xs text-primary/80 mt-1.5">
                  可证明材料：{item.evidence}
                </p>
              )}
            </div>
          ))}
        </div>
      ),
    },
    {
      id: "hard",
      title: "工具 / 技能 / 材料门槛",
      icon: <AlertCircle className="w-4 h-4" />,
      content: (
        <div className="space-y-2.5">
          {targetProfile.hardReqs.map((req: string, index: number) => (
            <div key={req} className="flex items-start gap-2 text-sm">
              {index < 2 ? (
                <XCircle className="w-4 h-4 text-destructive mt-0.5 shrink-0" />
              ) : (
                <CheckCircle2 className="w-4 h-4 text-muted-foreground mt-0.5 shrink-0" />
              )}
              <span
                className={index < 2 ? "text-foreground font-medium" : "text-muted-foreground"}
              >
                {req}
              </span>
            </div>
          ))}
          <p className="text-xs text-muted-foreground pt-1">
            这里的“门槛”不是说没有就不能投，而是面试官最容易追问的工具、技能或可展示材料。
          </p>
        </div>
      ),
    },
    {
      id: "package",
      title: "可包装机会",
      icon: <Sparkles className="w-4 h-4" />,
      content: (
        <div className="space-y-3">
          {targetProfile.packagable.map((item: { opportunity: string; status: EvidenceStatus; note: string }) => (
            <div key={item.opportunity} className="p-3 bg-muted/40 rounded-lg">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-sm font-medium text-foreground">
                  {item.opportunity}
                </span>
                <EvidenceTag status={item.status} />
              </div>
              <p className="text-xs text-muted-foreground">{item.note}</p>
            </div>
          ))}
        </div>
      ),
    },
  ];

  return (
    <PageShell
      onHome={onHome}
      onBack={onBack}
      showBack
      showProgress
      progressStep={1}
    >
      <div className="max-w-3xl mx-auto">
        <div className="mb-8">
          <div
            className="text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-3"
            style={{ fontFamily: "'JetBrains Mono', monospace" }}
          >
            Step 2 · 目标岗位理解
          </div>
          <div className="flex items-start justify-between gap-4 mb-4">
            <div>
              <h1 className="text-2xl font-bold text-foreground mb-1">
                {targetProfile.name} — 岗位解读
              </h1>
              <p className="text-sm text-muted-foreground">
                基于 {targetProfile.jdCount.toLocaleString()} 条相关 JD 综合分析 · 按你的选择生成
              </p>
            </div>
          </div>

          {/* Key conclusion */}
          <div className="bg-secondary border border-primary/20 rounded-xl p-5">
            <div className="text-xs font-semibold text-primary uppercase tracking-wide mb-2">
              核心结论 — 这个岗位最值得你用经历证明的能力
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {targetProfile.coreAbilities.map((item: { label: string; desc: string }, index: number) => (
                <div key={item.label} className="flex items-start gap-2.5">
                  <span
                    className="text-2xl font-bold text-primary/30 leading-none"
                    style={{ fontFamily: "'JetBrains Mono', monospace" }}
                  >
                    {index + 1}
                  </span>
                  <div>
                    <div className="font-medium text-sm text-foreground">
                      {item.label}
                    </div>
                    <div className="text-xs text-muted-foreground mt-0.5">
                      {item.desc}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-2.5">
          <div className="bg-white border border-border rounded-xl p-5">
            <div className="text-sm font-semibold text-foreground mb-3">
              证据状态说明
            </div>
            <div className="flex flex-wrap gap-2 mb-2">
              <EvidenceTag status="sufficient" />
              <EvidenceTag status="needs-more" />
              <EvidenceTag status="not-recommended" />
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed">
              从这里开始，系统会标注每类经历是否适合作为当前岗位证据：证据充分可以优先写，需要补充代表还缺数据/截图/过程，不建议写代表和当前岗位关系弱。
            </p>
          </div>

          {sections.map((section) => (
            <div
              key={section.id}
              className={`bg-white border rounded-xl overflow-hidden transition-all ${
                section.id === "package"
                  ? "border-primary/30"
                  : "border-border"
              }`}
            >
              <button
                onClick={() =>
                  setExpanded(expanded === section.id ? null : section.id)
                }
                className="w-full flex items-center justify-between p-5 hover:bg-muted/30 transition-colors"
              >
                <div className="flex items-center gap-2.5">
                  <span
                    className={`${
                      section.id === "package"
                        ? "text-primary"
                        : "text-muted-foreground"
                    }`}
                  >
                    {section.icon}
                  </span>
                  <span
                    className={`font-semibold ${
                      section.id === "package"
                        ? "text-primary"
                        : "text-foreground"
                    }`}
                  >
                    {section.title}
                  </span>
                  {section.id === "package" && (
                    <span className="text-xs px-2 py-0.5 bg-primary text-white rounded-full font-medium">
                      重点
                    </span>
                  )}
                </div>
                <ChevronDown
                  className={`w-4 h-4 text-muted-foreground transition-transform ${
                    expanded === section.id ? "rotate-180" : ""
                  }`}
                />
              </button>
              {expanded === section.id && (
                <div className="px-5 pb-5">{section.content}</div>
              )}
            </div>
          ))}
        </div>

        <div className="mt-6">
          <button
            onClick={onNext}
            className="w-full py-3.5 bg-primary text-white rounded-lg font-semibold hover:bg-primary/90 transition-all flex items-center justify-center gap-2 hover:shadow-lg hover:shadow-primary/20"
          >
            继续：输入我的经历
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </PageShell>
  );
}

// ─── Page: Step 3 – Experience Input ─────────────────────────────────────────

function Step3Page({
  onNext,
  onHome,
  onBack,
  targetRole,
}: {
  onNext: () => void;
  onHome: () => void;
  onBack: () => void;
  targetRole: string;
}) {
  const [name, setName] = useState("");
  const [type, setType] = useState("");
  const [whatDid, setWhatDid] = useState("");
  const [output, setOutput] = useState("");
  const [evidenceText, setEvidenceText] = useState("");
  const targetProfile = getRoleProfile(targetRole);

  const expTypes = [
    "课程作业",
    "社团活动",
    "比赛",
    "实习",
    "内容账号",
    "调研",
    "数据分析",
    "其他",
  ];

  const canSubmit = name && type && whatDid && output;

  return (
    <PageShell
      onHome={onHome}
      onBack={onBack}
      showBack
      showProgress
      progressStep={2}
    >
      <div className="max-w-2xl mx-auto">
        <div className="mb-8">
          <div
            className="text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-3"
            style={{ fontFamily: "'JetBrains Mono', monospace" }}
          >
            Step 3 · 经历输入
          </div>
          <h1 className="text-2xl font-bold text-foreground mb-2">
            描述你的一段经历
          </h1>
          <p className="text-sm text-muted-foreground">
            只填事实，不需要包装语言。AI 会自动提取可用于证明能力的细节，并追问遗漏信息。
          </p>
        </div>

        <div className="space-y-5">
          <div className="p-4 bg-secondary/60 rounded-lg border border-primary/10 text-sm text-primary">
            <div className="font-medium mb-1">本次准备目标岗位：{targetProfile.name}</div>
            <div className="text-xs text-primary/70">
              你的描述将围绕{targetProfile.family}方向的核心能力进行匹配分析
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              项目或经历名称 <span className="text-destructive">*</span>
            </label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="如：大学三年级小红书账号运营"
              className="w-full px-3 py-2.5 bg-white border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              经历类型 <span className="text-destructive">*</span>
            </label>
            <div className="flex flex-wrap gap-2">
              {expTypes.map((t) => (
                <button
                  key={t}
                  onClick={() => setType(t)}
                  className={`px-3 py-1.5 rounded-lg text-sm border transition-all ${
                    type === t
                      ? "border-primary bg-secondary text-primary font-medium"
                      : "border-border bg-white text-foreground hover:border-primary/30"
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              你具体做了什么？<span className="text-destructive">*</span>
            </label>
            <textarea
              value={whatDid}
              onChange={(e) => setWhatDid(e.target.value)}
              placeholder="尽量具体。比如：我运营了一个美食探店账号，每周发3篇图文，自己写文案、拍照和后期处理…"
              className="w-full h-28 px-3 py-2.5 bg-white border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary resize-none transition-all"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              最后产出了什么？<span className="text-destructive">*</span>
            </label>
            <textarea
              value={output}
              onChange={(e) => setOutput(e.target.value)}
              placeholder="如：账号累计4200粉丝，有3篇笔记破万阅读，最高获赞680，有一篇被官方收录…"
              className="w-full h-24 px-3 py-2.5 bg-white border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary resize-none transition-all"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              数据、反馈、链接或截图
              <span className="text-muted-foreground font-normal ml-1">（可选但强烈建议）</span>
            </label>
            <textarea
              value={evidenceText}
              onChange={(e) => setEvidenceText(e.target.value)}
              placeholder="先用文字描述即可。如：有问卷原始数据、访谈记录、后台截图、项目报告链接、老师评价等。"
              className="w-full h-20 px-3 py-2.5 bg-white border border-dashed border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary resize-none transition-all"
            />
            <p className="text-xs text-muted-foreground mt-1.5">
              演示版先不上传文件，AI 会根据你写下的证据描述判断可信度
            </p>
          </div>

          <button
            onClick={() =>
              onNext({
                name,
                type,
                whatDid,
                output,
                evidenceText,
              })
            }
            disabled={!canSubmit}
            className="w-full py-3.5 bg-primary text-white rounded-lg font-semibold hover:bg-primary/90 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-lg hover:shadow-primary/20"
          >
            <Sparkles className="w-4 h-4" />
            提交经历，开始 AI 追问
          </button>
        </div>
      </div>
    </PageShell>
  );
}

// ─── Page: Step 4 – AI Follow-up & Evidence Matching ─────────────────────────

function Step4Page({
  onNext,
  onHome,
  onBack,
  targetRole,
  experience,
  materials,
  onMaterialsGenerated,
}: {
  onNext: () => void;
  onHome: () => void;
  onBack: () => void;
  targetRole: string;
  experience: ExperienceDraft | null;
  materials: AiMaterials | null;
  onMaterialsGenerated: (materials: AiMaterials) => void;
}) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState("");
  const targetProfile = getRoleProfile(targetRole);

  const generateMaterials = async () => {
    if (!experience) {
      setError("还没有经历信息，请先返回上一步填写。");
      return;
    }

    setIsGenerating(true);
    setError("");

    try {
      const response = await fetch("/api/generate-materials", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          targetRole,
          roleProfile: targetProfile,
          experience,
        }),
      });
      const data = await response.json();

      if (!response.ok) {
        if (data.fallback) {
          onMaterialsGenerated(normalizeAiMaterials(data.fallback));
        }
        throw new Error(data.error || "AI 生成失败");
      }

      onMaterialsGenerated(normalizeAiMaterials(data.materials));
    } catch (err) {
      setError(err instanceof Error ? err.message : "AI 生成失败，请稍后重试。");
    } finally {
      setIsGenerating(false);
    }
  };

  useEffect(() => {
    if (!materials && experience) {
      generateMaterials();
    }
  }, [materials, experience?.name, targetRole]);

  return (
    <PageShell
      onHome={onHome}
      onBack={onBack}
      showBack
      showProgress
      progressStep={3}
    >
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <div
            className="text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-3"
            style={{ fontFamily: "'JetBrains Mono', monospace" }}
          >
            Step 4 · AI 追问与证据匹配
          </div>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-foreground mb-1">
                项目小助手对话
              </h1>
              <p className="text-sm text-muted-foreground">
                AI 会根据你的目标岗位和真实经历生成追问、证据匹配和求职材料草稿
              </p>
            </div>
          </div>
        </div>

        <Step4Chat
          onFinish={onNext}
          onRegenerate={generateMaterials}
          targetRole={targetProfile.name}
          experienceName={experience?.name || ""}
          materials={materials}
          isGenerating={isGenerating}
          error={error}
        />
      </div>
    </PageShell>
  );
}

// ─── Page: Step 5 – Output ────────────────────────────────────────────────────

function Step5Page({
  onHome,
  onBack,
  targetRole,
  experience,
  materials,
}: {
  onHome: () => void;
  onBack: () => void;
  targetRole: string;
  experience: ExperienceDraft | null;
  materials: AiMaterials | null;
}) {
  const [activeTab, setActiveTab] = useState("match");
  const [showRaw, setShowRaw] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);
  const targetProfile = getRoleProfile(targetRole);
  const displayMaterials = materials || normalizeAiMaterials(
    createFallbackMaterials({ targetRole, experience })
  );

  const handleCopy = async (id: string, text?: string) => {
    if (text && navigator.clipboard) {
      await navigator.clipboard.writeText(text);
    }
    setCopied(id);
    setTimeout(() => setCopied(null), 1800);
  };

  const tabs = [
    { id: "match", label: "岗位匹配报告" },
    { id: "portfolio", label: "作品集结构" },
    { id: "resume", label: "简历 Bullet" },
    { id: "interview", label: "面试讲述提纲" },
  ];

  return (
    <PageShell
      onHome={onHome}
      onBack={onBack}
      showBack
      showProgress
      progressStep={4}
    >
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <div
            className="text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-3"
            style={{ fontFamily: "'JetBrains Mono', monospace" }}
          >
            Step 5 · 材料输出
          </div>
          <h1 className="text-2xl font-bold text-foreground mb-6">
            你的求职材料已生成
          </h1>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6">
            {displayMaterials.summaryCards.map((card: { label: string; title: string; detail: string; status: EvidenceStatus }) => (
              <div key={card.label} className="bg-white border border-border rounded-xl p-4">
                <div className="flex items-center gap-1.5 mb-2">
                  {card.status === "sufficient" ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  ) : card.status === "needs-more" ? (
                    <AlertCircle className="w-4 h-4 text-amber-600" />
                  ) : (
                    <XCircle className="w-4 h-4 text-muted-foreground" />
                  )}
                  <span className="text-xs font-semibold text-muted-foreground">
                    {card.label}
                  </span>
                </div>
                <p className="text-sm text-foreground font-medium">{card.title}</p>
                <p className="text-xs text-muted-foreground mt-1">{card.detail}</p>
              </div>
            ))}
          </div>

          <div className="p-4 bg-secondary/50 border border-primary/10 rounded-lg text-sm text-primary">
            当前目标：{targetProfile.name} · 经历：{experience?.name || "未填写"} · AI 匹配度：
            <span className="font-bold ml-1">{displayMaterials.fitScore}</span>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-5 p-1 bg-muted rounded-lg">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 py-2 px-3 rounded-md text-sm font-medium transition-all ${
                activeTab === tab.id
                  ? "bg-white text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab: Match Report */}
        {activeTab === "match" && (
          <div className="space-y-4">
            {displayMaterials.matchReport.map((item: { ability: string; status: EvidenceStatus; evidence: string; suggestion: string }) => (
              <div
                key={item.ability}
                className="bg-white border border-border rounded-xl p-5"
              >
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-foreground">{item.ability}</h3>
                  <EvidenceTag status={item.status} />
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                  <div>
                    <div className="text-xs font-medium text-muted-foreground mb-1.5">
                      证据来源
                    </div>
                    <p className="text-foreground">{item.evidence}</p>
                  </div>
                  <div>
                    <div className="text-xs font-medium text-muted-foreground mb-1.5">
                      使用建议
                    </div>
                    <p className="text-foreground">{item.suggestion}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Tab: Portfolio */}
        {activeTab === "portfolio" && (
          <div className="space-y-4">
            <div className="bg-white border border-border rounded-xl overflow-hidden">
              <div className="px-5 py-4 border-b border-border flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-foreground">
                    作品集页面结构建议
                  </h3>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    适合 Notion、飞书或 PDF 格式作品集
                  </p>
                </div>
                <EvidenceTag status="sufficient" />
              </div>
              <div className="p-5 space-y-4">
                {displayMaterials.portfolio.map((block: { section: string; items: string[]; status: EvidenceStatus }) => (
                  <div key={block.section} className="border border-border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <span
                        className="text-sm font-semibold text-foreground"
                        style={{ fontFamily: "'JetBrains Mono', monospace" }}
                      >
                        {block.section}
                      </span>
                      <EvidenceTag status={block.status} />
                    </div>
                    <ul className="space-y-1.5">
                      {block.items.map((item, i) => (
                        <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                          <span className="text-border mt-1.5">·</span>
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Tab: Resume */}
        {activeTab === "resume" && (
          <div className="space-y-5">
            <div className="flex items-center gap-3 p-4 bg-muted/50 rounded-lg text-sm text-muted-foreground">
              <Info className="w-4 h-4 shrink-0" />
              所有 bullet 都基于你提供的真实信息生成。标注了证据状态，请根据实际情况使用，不要填写未发生的内容。
            </div>

            <div className="bg-white border border-border rounded-xl overflow-hidden">
              <div className="px-5 py-4 border-b border-border flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-foreground">
                      {showRaw ? "真实原始版" : "求职优化版"}
                    </h3>
                    <EvidenceTag status="sufficient" />
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {showRaw
                      ? "直接描述你做了什么，适合自评参考"
                      : "优化了动词和结构，适合直接使用"}
                  </p>
                </div>
                <button
                  onClick={() => setShowRaw(!showRaw)}
                  className="text-xs text-primary font-medium border border-primary/20 rounded-lg px-3 py-1.5 hover:bg-secondary transition-colors"
                >
                  {showRaw ? "查看优化版" : "查看原始版"}
                </button>
              </div>
              <div className="p-5 space-y-4">
                {(showRaw
                  ? displayMaterials.resumeRaw
                  : displayMaterials.resumeOptimized
                ).map((bullet: { text: string; status: EvidenceStatus; note: string }, i: number) => (
                  <div key={i} className="border border-border rounded-lg p-4">
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <p className="text-sm text-foreground leading-relaxed flex-1">
                        · {bullet.text}
                      </p>
                      <button
                        onClick={() => handleCopy(String(i), bullet.text)}
                        className="shrink-0 p-1.5 rounded hover:bg-muted transition-colors"
                      >
                        {copied === String(i) ? (
                          <Check className="w-3.5 h-3.5 text-emerald-600" />
                        ) : (
                          <Copy className="w-3.5 h-3.5 text-muted-foreground" />
                        )}
                      </button>
                    </div>
                    <EvidenceTag status={bullet.status} />
                    {bullet.status === "needs-more" && (
                      <p className="text-xs text-amber-600 mt-2">
                        {bullet.note}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Tab: Interview */}
        {activeTab === "interview" && (
          <div className="space-y-4">
            <div className="bg-white border border-border rounded-xl overflow-hidden">
              <div className="px-5 py-4 border-b border-border">
                <h3 className="font-semibold text-foreground">面试讲述提纲</h3>
                <p className="text-xs text-muted-foreground mt-0.5">
                  适用于"介绍一段你觉得最有代表性的经历"类问题
                </p>
              </div>
              <div className="p-5 space-y-5">
                {displayMaterials.interview.map((item: { part: string; content: string; status: EvidenceStatus; tip: string }) => (
                  <div key={item.part} className="border border-border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span
                        className="text-xs font-semibold text-muted-foreground"
                        style={{ fontFamily: "'JetBrains Mono', monospace" }}
                      >
                        {item.part}
                      </span>
                      <EvidenceTag status={item.status} />
                    </div>
                    <p className="text-sm text-foreground leading-relaxed mb-2.5">
                      {item.content}
                    </p>
                    <div className="flex items-start gap-1.5 text-xs text-muted-foreground">
                      <Info className="w-3 h-3 mt-0.5 shrink-0" />
                      {item.tip}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        <div className="mt-6 flex flex-col sm:flex-row gap-3">
          <button className="flex-1 py-3 border border-border bg-white text-foreground rounded-lg font-medium hover:bg-muted/40 transition-colors flex items-center justify-center gap-2">
            <Download className="w-4 h-4" />
            导出为 PDF
          </button>
          <button
            onClick={onHome}
            className="flex-1 py-3 bg-primary text-white rounded-lg font-semibold hover:bg-primary/90 transition-all flex items-center justify-center gap-2"
          >
            <ArrowRight className="w-4 h-4" />
            准备下一段经历
          </button>
        </div>
      </div>
    </PageShell>
  );
}

// ─── Main App ─────────────────────────────────────────────────────────────────

export default function App() {
  const [page, setPage] = useState<Page>("home");
  const [history, setHistory] = useState<Page[]>([]);
  const [targetRole, setTargetRole] = useState("内容运营实习生");
  const [experienceDraft, setExperienceDraft] = useState<ExperienceDraft | null>(null);
  const [aiMaterials, setAiMaterials] = useState<AiMaterials | null>(null);

  const navigate = (next: Page) => {
    setHistory((h) => [...h, page]);
    setPage(next);
  };

  const selectTargetRoleAndNavigate = (role: string | undefined, next: Page) => {
    if (role) {
      setTargetRole(getRoleProfile(role).name);
      setAiMaterials(null);
    }
    navigate(next);
  };

  const submitExperienceAndNavigate = (experience: ExperienceDraft) => {
    setExperienceDraft(experience);
    setAiMaterials(null);
    navigate("step4");
  };

  const goBack = () => {
    setHistory((h) => {
      const prev = h[h.length - 1];
      if (prev) {
        setPage(prev);
        return h.slice(0, -1);
      }
      return h;
    });
  };

  const goHome = () => {
    setHistory([]);
    setPage("home");
  };

  const nav = (p: Page) => () => navigate(p);

  if (page === "home") {
    return (
      <HomePage
        onStart={nav("step1")}
        onAssess={nav("pathC")}
      />
    );
  }
  if (page === "step1") {
    return (
      <Step1Page
        onNav={(p) => navigate(p)}
        onHome={goHome}
      />
    );
  }
  if (page === "pathA") {
    return (
      <PathAPage
        onNext={(role) => selectTargetRoleAndNavigate(role, "step2")}
        onHome={goHome}
        onBack={goBack}
      />
    );
  }
  if (page === "pathB") {
    return (
      <PathBPage
        onNext={(role) => selectTargetRoleAndNavigate(role, "step2")}
        onHome={goHome}
        onBack={goBack}
      />
    );
  }
  if (page === "pathC") {
    return (
      <PathCPage
        onNext={(role) => selectTargetRoleAndNavigate(role, "step2")}
        onHome={goHome}
        onBack={goBack}
      />
    );
  }
  if (page === "pathD") {
    return (
      <PathDPage
        onNext={nav("step4")}
        onHome={goHome}
        onBack={goBack}
      />
    );
  }
  if (page === "step2") {
    return (
      <Step2Page
        onNext={nav("step3")}
        onHome={goHome}
        onBack={goBack}
        targetRole={targetRole}
      />
    );
  }
  if (page === "step3") {
    return (
      <Step3Page
        onNext={submitExperienceAndNavigate}
        onHome={goHome}
        onBack={goBack}
        targetRole={targetRole}
      />
    );
  }
  if (page === "step4") {
    return (
      <Step4Page
        onNext={nav("step5")}
        onHome={goHome}
        onBack={goBack}
        targetRole={targetRole}
        experience={experienceDraft}
        materials={aiMaterials}
        onMaterialsGenerated={setAiMaterials}
      />
    );
  }
  if (page === "step5") {
    return (
      <Step5Page
        onHome={goHome}
        onBack={goBack}
        targetRole={targetRole}
        experience={experienceDraft}
        materials={aiMaterials}
      />
    );
  }
  return null;
}
