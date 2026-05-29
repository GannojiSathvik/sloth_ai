"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import { Send, Loader2, ExternalLink, ChevronDown } from "lucide-react";
import ReactMarkdown from "react-markdown";

// ── Types ──────────────────────────────────────────────────────────────────────

type ModelId = "aura" | "bitch_iso";

type Source = {
  title: string;
  url: string;
};

type Message = {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  low_confidence?: boolean;
};

// ── Model Config ───────────────────────────────────────────────────────────────

const MODELS = {
  aura: {
    id: "aura" as ModelId,
    name: "AURA",
    chip: "✦ AURA",
    tagline: "Charisma · Confidence · Social Intelligence",
    accent: "#4f8ef7",
    accentDim: "rgba(79,142,247,0.12)",
    accentBorder: "rgba(79,142,247,0.28)",
    accentGlow: "rgba(79,142,247,0.35)",
    userBubble: "rgba(79,142,247,0.16)",
    userBorder: "rgba(79,142,247,0.3)",
    bg: "#07090f",
    orb: "radial-gradient(ellipse at 15% 15%, rgba(79,142,247,0.13) 0%, transparent 55%), radial-gradient(ellipse at 85% 85%, rgba(99,102,241,0.08) 0%, transparent 55%)",
    placeholder: "Ask AURA about charisma, confidence, social skills…",
    emptyTitle: "How can I elevate you today?",
    emptySubtitle: "Sloth AI — trained on 400+ Charisma on Command videos. Ask about social dynamics, body language, or confidence.",
  },
  bitch_iso: {
    id: "bitch_iso" as ModelId,
    name: "BITCH ISO",
    chip: "◆ BITCH ISO",
    tagline: "Standards · Feminine Energy · Self-Worth",
    accent: "#c9a84c",
    accentDim: "rgba(201,168,76,0.10)",
    accentBorder: "rgba(201,168,76,0.25)",
    accentGlow: "rgba(201,168,76,0.30)",
    userBubble: "rgba(201,168,76,0.10)",
    userBorder: "rgba(201,168,76,0.25)",
    bg: "#080603",
    orb: "radial-gradient(ellipse at 15% 15%, rgba(201,168,76,0.10) 0%, transparent 55%), radial-gradient(ellipse at 85% 85%, rgba(140,20,20,0.07) 0%, transparent 55%)",
    placeholder: "Ask Bitch Iso about standards, energy, mindset…",
    emptyTitle: "What do you need clarity on?",
    emptySubtitle: "Sloth AI — unbothered and high-value. Ask about feminine energy, standards, or mindset.",
  },
} as const;

// ── Source Card ────────────────────────────────────────────────────────────────

function SourceCard({ source, accent }: { source: Source; accent: string }) {
  return (
    <a
      href={source.url}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs transition-opacity hover:opacity-75"
      style={{
        background: "rgba(255,255,255,0.04)",
        border: "1px solid rgba(255,255,255,0.08)",
        color: accent,
      }}
    >
      <ExternalLink className="w-3 h-3 flex-shrink-0" />
      <span className="truncate font-medium" title={source.title}>{source.title}</span>
    </a>
  );
}

// ── Message Bubble ─────────────────────────────────────────────────────────────

function MessageBubble({ msg, model }: { msg: Message; model: typeof MODELS[ModelId] }) {
  const isUser = msg.role === "user";
  const [sourcesOpen, setSourcesOpen] = useState(false);

  return (
    <div className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}>
      {/* AI avatar */}
      {!isUser && (
        <div
          className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold mt-1"
          style={{ background: model.accentDim, border: `1px solid ${model.accentBorder}`, color: model.accent }}
        >
          {model.id === "aura" ? "✦" : "◆"}
        </div>
      )}

      <div className={`flex flex-col gap-1.5 max-w-[82%] ${isUser ? "items-end" : "items-start"}`}>
        {/* Bubble */}
        <div
          className="px-4 py-3 rounded-2xl text-sm leading-relaxed"
          style={
            isUser
              ? {
                  background: model.userBubble,
                  border: `1px solid ${model.userBorder}`,
                  color: "#f0f4ff",
                  borderTopRightRadius: "6px",
                }
              : {
                  background: "rgba(255,255,255,0.03)",
                  border: "1px solid rgba(255,255,255,0.06)",
                  color: "#e2e8f0",
                  borderTopLeftRadius: "6px",
                }
          }
        >
          <div className="prose prose-invert prose-sm max-w-none prose-p:my-1 prose-p:leading-relaxed prose-pre:bg-black/50">
            <ReactMarkdown>{msg.content || "\u200b"}</ReactMarkdown>
          </div>
        </div>

        {/* Low Confidence Warning */}
        {!isUser && msg.low_confidence && (
          <div className="text-xs px-3 py-2 rounded-lg" style={{ background: "rgba(255,165,0,0.1)", border: "1px solid rgba(255,165,0,0.2)", color: "rgba(255,165,0,0.8)" }}>
            ⚠️ Low confidence — this topic may not be well covered in the channel
          </div>
        )}

        {/* Sources */}
        {!isUser && msg.sources && msg.sources.length > 0 && (
          <div>
            <button
              onClick={() => setSourcesOpen((o) => !o)}
              className="flex items-center gap-1 text-xs mb-1.5 transition-opacity hover:opacity-70"
              style={{ color: model.accent }}
            >
              <span>{msg.sources.length} source{msg.sources.length > 1 ? "s" : ""}</span>
              <ChevronDown
                className="w-3 h-3 transition-transform"
                style={{ transform: sourcesOpen ? "rotate(180deg)" : "none" }}
              />
            </button>
            {sourcesOpen && (
              <div className="flex flex-col gap-1">
                {msg.sources.map((s, i) => (
                  <SourceCard key={i} source={s} accent={model.accent} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* User avatar */}
      {isUser && (
        <div
          className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold mt-1"
          style={{ background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.1)", color: "#94a3b8" }}
        >
          U
        </div>
      )}
    </div>
  );
}

// ── Typing Indicator ───────────────────────────────────────────────────────────

function TypingDots({ model }: { model: typeof MODELS[ModelId] }) {
  return (
    <div className="flex gap-3 justify-start">
      <div
        className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
        style={{ background: model.accentDim, border: `1px solid ${model.accentBorder}`, color: model.accent }}
      >
        {model.id === "aura" ? "✦" : "◆"}
      </div>
      <div
        className="px-4 py-3 rounded-2xl flex items-center gap-1.5"
        style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)", borderTopLeftRadius: "6px" }}
      >
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="w-1.5 h-1.5 rounded-full"
            style={{
              background: model.accent,
              animation: `typingBounce 1.2s ${i * 0.2}s infinite ease-in-out`,
            }}
          />
        ))}
      </div>
    </div>
  );
}

// ── Model Dropdown ─────────────────────────────────────────────────────────────

function ModelPicker({
  active,
  onChange,
  disabled,
}: {
  active: ModelId;
  onChange: (id: ModelId) => void;
  disabled: boolean;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const model = MODELS[active];

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  return (
    <div ref={ref} className="relative flex-shrink-0">
      <button
        type="button"
        onClick={() => !disabled && setOpen((o) => !o)}
        disabled={disabled}
        className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all whitespace-nowrap"
        style={{
          background: model.accentDim,
          border: `1px solid ${model.accentBorder}`,
          color: model.accent,
          cursor: disabled ? "not-allowed" : "pointer",
        }}
      >
        {model.chip}
        <ChevronDown
          className="w-3 h-3 transition-transform"
          style={{ transform: open ? "rotate(180deg)" : "none" }}
        />
      </button>

      {open && (
        <div
          className="absolute bottom-full mb-2 left-0 rounded-xl overflow-hidden z-50 min-w-[160px]"
          style={{
            background: "#111118",
            border: "1px solid rgba(255,255,255,0.1)",
            boxShadow: "0 8px 32px rgba(0,0,0,0.6)",
          }}
        >
          {(Object.values(MODELS) as typeof MODELS[ModelId][]).map((m) => (
            <button
              key={m.id}
              type="button"
              onClick={() => { onChange(m.id); setOpen(false); }}
              className="w-full flex items-center gap-3 px-4 py-3 text-sm text-left transition-all"
              style={{
                background: m.id === active ? m.accentDim : "transparent",
                color: m.id === active ? m.accent : "rgba(255,255,255,0.5)",
              }}
            >
              <span className="font-bold">{m.chip}</span>
              <span className="text-xs opacity-60 truncate">{m.tagline.split("·")[0].trim()}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Main Chat ──────────────────────────────────────────────────────────────────

export default function ChatUI() {
  const [activeModel, setActiveModel] = useState<ModelId>("aura");
  const [histories, setHistories] = useState<Record<ModelId, Message[]>>({ aura: [], bitch_iso: [] });
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const model = MODELS[activeModel];
  const messages = histories[activeModel];

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => { scrollToBottom(); }, [messages, isLoading, scrollToBottom]);

  const switchModel = (id: ModelId) => {
    if (isLoading) return;
    setActiveModel(id);
    setTimeout(() => inputRef.current?.focus(), 50);
  };

  // ── Send message — single state update prevents duplicate bubbles ─────────
  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userText = input.trim();
    setInput("");
    setIsLoading(true);

    // Send history but exclude the empty placeholder we just added for the AI
    const historyToSend = histories[activeModel]
      .filter((m, idx) => idx < histories[activeModel].length) // only actual history, but wait, the active one was just added. Actually we just use the previous history.
      .map(m => ({ role: m.role, content: m.content }))
      .filter(m => m.content.trim() !== "");

    // ONE setState: add user + empty AI placeholder together (prevents duplicate)
    setHistories((h) => ({
      ...h,
      [activeModel]: [
        ...h[activeModel],
        { role: "user", content: userText },
        { role: "assistant", content: "", sources: [] },
      ],
    }));

    let streamedContent = "";
    let streamedSources: Source[] = [];

    try {
      const res = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          message: userText, 
          model: activeModel,
          history: historyToSend 
        }),
      });

      if (!res.body) throw new Error("No response body");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const raw = decoder.decode(value, { stream: true });
        for (const line of raw.split("\n\n")) {
          if (!line.startsWith("data: ")) continue;
          const dataStr = line.slice(6).trim();
          if (!dataStr || dataStr === "[DONE]") continue;

          try {
            const data = JSON.parse(dataStr);
            if (data.type === "sources") {
              streamedSources = data.sources;
              setHistories((h) => {
                const msgs = [...h[activeModel]];
                msgs[msgs.length - 1] = { 
                  ...msgs[msgs.length - 1], 
                  sources: streamedSources,
                  low_confidence: data.low_confidence 
                };
                return { ...h, [activeModel]: msgs };
              });
            } else if (data.type === "token") {
              streamedContent += data.content;
              setHistories((h) => {
                const msgs = [...h[activeModel]];
                msgs[msgs.length - 1] = { ...msgs[msgs.length - 1], content: streamedContent, sources: streamedSources };
                return { ...h, [activeModel]: msgs };
              });
            } else if (data.type === "error") {
              streamedContent = `⚠️ ${data.content}`;
              setHistories((h) => {
                const msgs = [...h[activeModel]];
                msgs[msgs.length - 1] = { ...msgs[msgs.length - 1], content: streamedContent };
                return { ...h, [activeModel]: msgs };
              });
            }
          } catch { /* skip malformed JSON */ }
        }
      }
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : "Unknown error";
      setHistories((h) => {
        const msgs = [...h[activeModel]];
        msgs[msgs.length - 1] = {
          ...msgs[msgs.length - 1],
          content: `⚠️ Could not reach the API server.\nMake sure \`python api_server.py\` is running.\n\n\`${errMsg}\``,
        };
        return { ...h, [activeModel]: msgs };
      });
    } finally {
      setIsLoading(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  };

  return (
    <>
      {/* Keyframe injection */}
      <style>{`
        @keyframes typingBounce {
          0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
          30% { transform: translateY(-5px); opacity: 1; }
        }
        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(6px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>

      <div
        className="relative flex flex-col h-full w-full max-w-4xl mx-auto rounded-2xl overflow-hidden shadow-2xl"
        style={{
          background: model.bg,
          border: "1px solid rgba(255,255,255,0.07)",
          transition: "background 0.4s ease",
        }}
      >
        {/* Theme orbs */}
        <div
          className="absolute inset-0 pointer-events-none transition-all duration-700"
          style={{ background: model.orb }}
        />

        {/* ── Header ──────────────────────────────────────────── */}
        <div
          className="relative z-10 flex items-center justify-between px-5 py-4 border-b"
          style={{ borderColor: "rgba(255,255,255,0.07)", background: "rgba(0,0,0,0.25)", backdropFilter: "blur(12px)" }}
        >
          <div className="flex items-center gap-3">
            <div
              className="w-9 h-9 rounded-xl flex items-center justify-center font-bold text-base flex-shrink-0"
              style={{
                background: model.accentDim,
                border: `1px solid ${model.accentBorder}`,
                color: model.accent,
                boxShadow: `0 0 16px ${model.accentGlow}`,
                transition: "all 0.3s ease",
              }}
            >
              {model.id === "aura" ? "✦" : "◆"}
            </div>
            <div>
              <div className="text-sm font-bold text-white" style={{ transition: "all 0.3s" }}>{model.name}</div>
              <div className="text-xs" style={{ color: "rgba(255,255,255,0.38)" }}>{model.tagline}</div>
            </div>
          </div>

          {/* Clear button */}
          {messages.length > 0 && !isLoading && (
            <button
              onClick={() => setHistories((h) => ({ ...h, [activeModel]: [] }))}
              className="text-xs px-3 py-1.5 rounded-lg transition-opacity hover:opacity-70"
              style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.08)", color: "rgba(255,255,255,0.3)" }}
            >
              Clear
            </button>
          )}
        </div>

        {/* ── Chat Area ───────────────────────────────────────── */}
        <div className="relative z-10 flex-1 overflow-y-auto px-5 py-5 space-y-5 custom-scrollbar">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center gap-4 select-none opacity-60">
              <div
                className="w-14 h-14 rounded-2xl flex items-center justify-center text-2xl"
                style={{
                  background: model.accentDim,
                  border: `1px solid ${model.accentBorder}`,
                  color: model.accent,
                  boxShadow: `0 0 24px ${model.accentGlow}`,
                }}
              >
                {model.id === "aura" ? "✦" : "◆"}
              </div>
              <div>
                <h2 className="text-base font-semibold text-white mb-1">{model.emptyTitle}</h2>
                <p className="text-xs max-w-xs leading-relaxed" style={{ color: "rgba(255,255,255,0.38)" }}>
                  {model.emptySubtitle}
                </p>
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg, i) => (
                <div key={i} style={{ animation: i === messages.length - 1 || i === messages.length - 2 ? "fadeUp 0.25s ease-out" : "none" }}>
                  <MessageBubble msg={msg} model={model} />
                </div>
              ))}
              {isLoading && messages[messages.length - 1]?.content === "" && (
                <TypingDots model={model} />
              )}
            </>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* ── Input Bar ───────────────────────────────────────── */}
        <div
          className="relative z-10 px-4 py-3 border-t"
          style={{ borderColor: "rgba(255,255,255,0.07)", background: "rgba(0,0,0,0.3)", backdropFilter: "blur(12px)" }}
        >
          <form onSubmit={sendMessage} className="flex items-center gap-2">
            {/* Model selector pill — inside input bar */}
            <ModelPicker active={activeModel} onChange={switchModel} disabled={isLoading} />

            {/* Text input */}
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={model.placeholder}
              disabled={isLoading}
              className="flex-1 bg-white/5 text-white text-sm rounded-xl py-3 px-4 focus:outline-none transition-all placeholder-white/20"
              style={{
                border: `1px solid ${input.trim() ? model.accentBorder : "rgba(255,255,255,0.08)"}`,
              }}
            />

            {/* Send button */}
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="w-10 h-10 flex-shrink-0 flex items-center justify-center rounded-xl transition-all"
              style={{
                background: input.trim() && !isLoading ? model.accent : "rgba(255,255,255,0.05)",
                border: `1px solid ${input.trim() && !isLoading ? model.accent : "rgba(255,255,255,0.08)"}`,
                color: input.trim() && !isLoading ? "#fff" : "rgba(255,255,255,0.2)",
                boxShadow: input.trim() && !isLoading ? `0 0 12px ${model.accentGlow}` : "none",
              }}
            >
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </button>
          </form>
        </div>
      </div>
    </>
  );
}
