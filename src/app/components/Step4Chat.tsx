import React, { useEffect, useRef, useState } from "react";
import { ArrowRight, RefreshCw, Sparkles } from "lucide-react";

type EvidenceStatus = "sufficient" | "needs-more" | "not-recommended";

interface Message {
  role: "ai" | "user";
  content: string;
  timestamp: Date;
}

interface Step4ChatProps {
  onFinish: () => void;
  onRegenerate: () => void;
  targetRole: string;
  experienceName: string;
  materials: {
    fitScore: number;
    overallComment: string;
    followUpQuestions: Array<{ question: string; hint: string }>;
    matchReport: Array<{
      ability: string;
      status: EvidenceStatus;
      evidence: string;
      suggestion: string;
    }>;
  } | null;
  isGenerating: boolean;
  error: string;
}

function EvidenceTag({ status }: { status: EvidenceStatus }) {
  if (status === "sufficient") {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
        证据充分
      </span>
    );
  }
  if (status === "needs-more") {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200">
        需要补充
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-slate-50 text-slate-500 border border-slate-200">
      不建议写
    </span>
  );
}

export function Step4Chat({
  onFinish,
  onRegenerate,
  targetRole,
  experienceName,
  materials,
  isGenerating,
  error,
}: Step4ChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentInput, setCurrentInput] = useState("");
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(-1);
  const [isTyping, setIsTyping] = useState(false);
  const [answeredCount, setAnsweredCount] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const questions = materials?.followUpQuestions || [];
  const minimumAnswers = Math.min(3, questions.length);

  useEffect(() => {
    if (isGenerating) {
      setMessages([
        {
          role: "ai",
          content: `我正在读取「${targetRole}」的岗位要求和「${experienceName || "这段经历"}」的经历信息，生成更贴合岗位的追问。`,
          timestamp: new Date(),
        },
      ]);
      setCurrentQuestionIndex(-1);
      setAnsweredCount(0);
      return;
    }

    if (materials) {
      setMessages([
        {
          role: "ai",
          content: `你好，我已经完成初步证据分析。\n\n目标岗位：${targetRole}\n经历：${experienceName || "未命名经历"}\n初步匹配度：${materials.fitScore}%\n\n${materials.overallComment}\n\n接下来我会像面试官一样追问 ${questions.length} 个问题，帮你把证据补完整。你可以输入「开始」进入第一题。`,
          timestamp: new Date(),
        },
      ]);
      setCurrentQuestionIndex(-1);
      setAnsweredCount(0);
      return;
    }

    setMessages([
      {
        role: "ai",
        content: error || "还没有生成追问。请点击重新生成，或返回上一步检查经历信息。",
        timestamp: new Date(),
      },
    ]);
  }, [isGenerating, materials, error, targetRole, experienceName]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const askNextQuestion = (questionIndex: number) => {
    if (!materials) return;

    if (questionIndex >= questions.length) {
      setIsTyping(true);
      setTimeout(() => {
        setMessages((prev) => [
          ...prev,
          {
            role: "ai",
            content: `这一轮追问完成。\n\n我已经把你的回答和原始经历一起纳入材料草稿。现在可以查看 AI 生成的岗位匹配报告、作品集结构、简历 Bullet 和面试讲述提纲。`,
            timestamp: new Date(),
          },
        ]);
        setIsTyping(false);
      }, 700);
      return;
    }

    setIsTyping(true);
    setTimeout(() => {
      const question = questions[questionIndex];
      setMessages((prev) => [
        ...prev,
        {
          role: "ai",
          content: `问题 ${questionIndex + 1}/${questions.length}\n\n${question.question}\n\n提示：${question.hint}`,
          timestamp: new Date(),
        },
      ]);
      setCurrentQuestionIndex(questionIndex);
      setIsTyping(false);
    }, 500);
  };

  const handleSend = () => {
    if (!currentInput.trim() || isTyping || !materials) return;

    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        content: currentInput,
        timestamp: new Date(),
      },
    ]);
    setCurrentInput("");

    if (currentQuestionIndex === -1) {
      askNextQuestion(0);
      return;
    }

    setAnsweredCount((prev) => prev + 1);
    setIsTyping(true);
    setTimeout(() => {
      const acknowledgements = [
        "收到，这个细节可以增强证据可信度。",
        "明白，这能帮助我判断你的个人贡献。",
        "这个回答有用，后面会体现在材料建议里。",
        "好的，这里可以作为面试追问时的补充素材。",
        "了解，我会把这部分放进证据判断里。",
      ];
      setMessages((prev) => [
        ...prev,
        {
          role: "ai",
          content: acknowledgements[currentQuestionIndex % acknowledgements.length],
          timestamp: new Date(),
        },
      ]);
      setIsTyping(false);
      setTimeout(() => askNextQuestion(currentQuestionIndex + 1), 350);
    }, 450);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div>
      <div
        className="bg-white border border-border rounded-xl overflow-hidden flex flex-col"
        style={{ height: "600px" }}
      >
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`flex gap-3 max-w-[80%] ${
                  msg.role === "user" ? "flex-row-reverse" : "flex-row"
                }`}
              >
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                    msg.role === "ai"
                      ? "bg-primary text-white"
                      : "bg-muted text-foreground"
                  }`}
                >
                  {msg.role === "ai" ? (
                    <Sparkles className="w-4 h-4" />
                  ) : (
                    <span className="text-xs font-semibold">你</span>
                  )}
                </div>

                <div>
                  <div
                    className={`rounded-2xl px-4 py-3 ${
                      msg.role === "ai"
                        ? "bg-muted text-foreground"
                        : "bg-primary text-white"
                    }`}
                  >
                    <div className="text-sm leading-relaxed whitespace-pre-wrap">
                      {msg.content}
                    </div>
                  </div>
                  <div
                    className={`text-xs text-muted-foreground mt-1 px-1 ${
                      msg.role === "user" ? "text-right" : "text-left"
                    }`}
                  >
                    {msg.timestamp.toLocaleTimeString("zh-CN", {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </div>
                </div>
              </div>
            </div>
          ))}

          {isTyping && (
            <div className="flex justify-start">
              <div className="flex gap-3 max-w-[80%]">
                <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 bg-primary text-white">
                  <Sparkles className="w-4 h-4" />
                </div>
                <div className="rounded-2xl px-4 py-3 bg-muted">
                  <div className="flex gap-1">
                    <div
                      className="w-2 h-2 bg-muted-foreground/40 rounded-full animate-bounce"
                      style={{ animationDelay: "0ms" }}
                    />
                    <div
                      className="w-2 h-2 bg-muted-foreground/40 rounded-full animate-bounce"
                      style={{ animationDelay: "150ms" }}
                    />
                    <div
                      className="w-2 h-2 bg-muted-foreground/40 rounded-full animate-bounce"
                      style={{ animationDelay: "300ms" }}
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="border-t border-border p-4 bg-muted/30">
          {answeredCount >= questions.length && materials ? (
            <button
              onClick={onFinish}
              className="w-full py-3.5 bg-primary text-white rounded-lg font-semibold hover:bg-primary/90 transition-all flex items-center justify-center gap-2 hover:shadow-lg hover:shadow-primary/20"
            >
              <Sparkles className="w-4 h-4" />
              查看生成材料
            </button>
          ) : (
            <div className="flex gap-2">
              <textarea
                value={currentInput}
                onChange={(e) => setCurrentInput(e.target.value)}
                onKeyDown={handleKeyPress}
                disabled={!materials || isGenerating}
                placeholder={
                  isGenerating
                    ? "AI 正在生成追问..."
                    : currentQuestionIndex === -1
                    ? "输入「开始」或任意内容开始对话..."
                    : "输入你的回答..."
                }
                className="flex-1 px-4 py-3 bg-white border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary resize-none transition-all disabled:opacity-60"
                rows={2}
              />
              <button
                onClick={handleSend}
                disabled={!currentInput.trim() || isTyping || !materials}
                className="px-6 bg-primary text-white rounded-lg font-medium hover:bg-primary/90 transition-all disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
              >
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          )}

          <div className="mt-3 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-muted-foreground">
            <button
              onClick={onRegenerate}
              disabled={isGenerating}
              className="inline-flex items-center gap-1 text-primary font-medium hover:underline disabled:opacity-50"
            >
              <RefreshCw className="w-3 h-3" />
              重新生成追问
            </button>
            {materials && answeredCount >= minimumAnswers && answeredCount < questions.length && (
              <span>
                已达到最低要求（{answeredCount}/{questions.length}），可以
                <button
                  onClick={onFinish}
                  className="text-primary font-medium hover:underline ml-1"
                >
                  直接查看生成材料
                </button>
              </span>
            )}
          </div>
        </div>
      </div>

      {materials && (
        <div className="mt-4 bg-white border border-border rounded-xl p-5">
          <h3 className="text-sm font-semibold text-foreground mb-3">
            证据匹配状态
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {materials.matchReport.slice(0, 6).map((item) => (
              <div key={item.ability} className="flex items-center gap-2 text-xs">
                <EvidenceTag status={item.status} />
                <span className="text-muted-foreground">{item.ability}</span>
              </div>
            ))}
          </div>

          <div className="mt-4 pt-4 border-t border-border">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-muted-foreground">整体匹配度</span>
              <span className="text-sm font-semibold text-primary">
                {materials.fitScore}%
              </span>
            </div>
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-primary rounded-full transition-all duration-500"
                style={{ width: `${materials.fitScore}%` }}
              />
            </div>
          </div>
        </div>
      )}

      {error && !isGenerating && (
        <div className="mt-4 bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-800">
          {error}
        </div>
      )}
    </div>
  );
}
