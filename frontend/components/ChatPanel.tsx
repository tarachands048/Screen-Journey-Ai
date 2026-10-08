"use client";
import { useState, useEffect, useRef } from "react";
import { Send, Trash2, Bot, User } from "lucide-react";
import { ChatMessage, ChatSource } from "@/types";
import { sendChat, getChatHistory, clearChatHistory } from "@/lib/api";
import ReactMarkdown from "react-markdown";

interface Props {
  sessionId: string;
  sessionName: string;
}

export default function ChatPanel({ sessionId, sessionName }: Props) {
  const [messages, setMessages] = useState<(ChatMessage & { sources?: ChatSource[] })[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [suggested, setSuggested] = useState<string[]>([
    "Summarize this session",
    "What was shown on the first page?",
    "Where did the user spend the most time?",
  ]);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getChatHistory(sessionId).then((history) => {
      setMessages(history.map((m: any) => ({ ...m, sources: [] })));
    });
  }, [sessionId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async (text?: string) => {
    const msg = (text || input).trim();
    if (!msg || loading) return;
    setInput("");
    setLoading(true);

    const userMsg: ChatMessage & { sources?: ChatSource[] } = {
      id: Date.now().toString(),
      session_id: sessionId,
      role: "user",
      content: msg,
      created_at: new Date().toISOString(),
      sources: [],
    };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const res = await sendChat(sessionId, msg);
      const assistantMsg = {
        id: (Date.now() + 1).toString(),
        session_id: sessionId,
        role: "assistant" as const,
        content: res.answer,
        created_at: new Date().toISOString(),
        sources: res.sources || [],
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          session_id: sessionId,
          role: "assistant" as const,
          content: "Sorry, I couldn't process that. Make sure Ollama is running.",
          created_at: new Date().toISOString(),
          sources: [],
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = async () => {
    await clearChatHistory(sessionId);
    setMessages([]);
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between p-3 border-b">
        <div className="flex items-center gap-2 text-sm font-medium">
          <Bot className="w-4 h-4 text-primary" /> AI Chat
        </div>
        <button onClick={handleClear} className="text-muted-foreground hover:text-destructive transition-colors" title="Clear history">
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-3 min-h-0">
        {messages.length === 0 && (
          <div className="space-y-2">
            <p className="text-muted-foreground text-xs text-center">Ask anything about this session</p>
            <div className="space-y-1">
              {suggested.map((q) => (
                <button
                  key={q}
                  onClick={() => send(q)}
                  className="w-full text-left text-xs p-2 rounded bg-muted hover:bg-accent transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={`flex gap-2 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
            <div className={`rounded-full w-6 h-6 flex items-center justify-center flex-shrink-0 ${msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"}`}>
              {msg.role === "user" ? <User className="w-3 h-3" /> : <Bot className="w-3 h-3" />}
            </div>
            <div className={`max-w-[85%] ${msg.role === "user" ? "items-end" : "items-start"} flex flex-col gap-1`}>
              <div className={`rounded-lg px-3 py-2 text-sm ${msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"}`}>
                <ReactMarkdown className="prose prose-sm dark:prose-invert max-w-none">{msg.content}</ReactMarkdown>
              </div>
              {msg.sources && msg.sources.length > 0 && (
                <div className="space-y-0.5">
                  {msg.sources.map((s, i) => (
                    <span key={i} className="text-xs text-muted-foreground block">
                      Source: {s.page_title || "Step"} @ {s.timestamp}s
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex gap-2">
            <div className="rounded-full w-6 h-6 flex items-center justify-center bg-muted">
              <Bot className="w-3 h-3" />
            </div>
            <div className="bg-muted rounded-lg px-3 py-2 text-sm text-muted-foreground animate-pulse">
              Thinking…
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="p-3 border-t">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && (e.ctrlKey || !e.shiftKey) && send()}
            placeholder="Ask about this session… (Enter to send)"
            className="flex-1 text-sm border rounded-md px-3 py-1.5 bg-background"
            disabled={loading}
          />
          <button
            onClick={() => send()}
            disabled={loading || !input.trim()}
            className="p-1.5 rounded-md bg-primary text-primary-foreground disabled:opacity-50"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
