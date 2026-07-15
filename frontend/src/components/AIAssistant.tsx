"use client";

import React, { useState } from "react";
import { MessageSquare, X, Send, Bot, Terminal, ShieldAlert } from "lucide-react";

interface ToolCall {
  tool_name: string;
  tool_args: any;
  tool_output: any;
}

interface Message {
  sender: "user" | "bot";
  text: string;
  thoughtProcess?: string;
  toolCalls?: ToolCall[];
}

export default function AIAssistant() {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: "bot",
      text: "Hello! I am your LoomSense AI Digital Copilot. Ask me about shop floor statuses, delay predictions, or request a scheduling run / scenario analysis.",
    }
  ]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    const userMsg = query;
    setMessages((prev) => [...prev, { sender: "user", text: userMsg }]);
    setQuery("");
    setIsLoading(true);

    const tenantId = localStorage.getItem("tenant_id") || "factory_alpha";

    try {
      const resp = await fetch("http://localhost:8000/api/v1/assistant/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Tenant-ID": tenantId
        },
        body: JSON.stringify({ query: userMsg, tenant_id: tenantId })
      });
      
      if (resp.ok) {
        const data = await resp.json();
        setMessages((prev) => [
          ...prev,
          {
            sender: "bot",
            text: data.answer,
            thoughtProcess: data.thought_process,
            toolCalls: data.tool_calls
          }
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          { sender: "bot", text: "I encountered a communication error with the backend servers." }
        ]);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: "Network error. Make sure the FastAPI server is running on localhost:8000." }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      {/* Floating Chat Trigger button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 p-4 bg-violet-600 rounded-full text-white shadow-xl hover:bg-violet-700 hover:scale-110 active:scale-95 transition-all duration-200 z-50 glow-border-purple"
        >
          <MessageSquare className="w-6 h-6 animate-pulse" />
        </button>
      )}

      {/* Floating Chat Dialog */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 w-96 h-[500px] glass-panel z-50 flex flex-col border border-violet-500/30 overflow-hidden shadow-2xl">
          {/* Header */}
          <div className="p-4 bg-violet-950/40 border-b border-white/5 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bot className="w-5 h-5 text-violet-400 glow-text-purple" />
              <div>
                <h3 className="font-bold text-sm text-white">LoomSense Copilot</h3>
                <span className="text-[9px] uppercase tracking-widest text-violet-400 font-semibold">
                  Agentic AI Layer
                </span>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="p-1 hover:bg-white/10 rounded-lg text-gray-400 hover:text-white transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Chat history */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg, index) => (
              <div
                key={index}
                className={`flex flex-col ${msg.sender === "user" ? "items-end" : "items-start"}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl p-3 text-sm leading-relaxed ${
                    msg.sender === "user"
                      ? "bg-violet-600 text-white rounded-br-none shadow-md shadow-violet-950/20"
                      : "bg-slate-900 border border-white/5 text-gray-200 rounded-bl-none"
                  }`}
                >
                  {msg.text}
                </div>

                {/* Show Thought Process / Reasoning chain if bot message */}
                {msg.sender === "bot" && msg.thoughtProcess && (
                  <div className="mt-2 w-[85%] bg-black/45 border border-violet-500/10 rounded-lg p-2 text-[10px] font-mono text-violet-300 flex items-start gap-1.5">
                    <Terminal className="w-3.5 h-3.5 mt-0.5 text-violet-400 shrink-0" />
                    <div>
                      <span className="font-bold text-violet-400 block mb-0.5">AGENT LOG:</span>
                      {msg.thoughtProcess}
                    </div>
                  </div>
                )}

                {/* Show Tool Calls run behind the scenes */}
                {msg.sender === "bot" && msg.toolCalls && msg.toolCalls.length > 0 && (
                  <div className="mt-1.5 w-[85%] space-y-1">
                    {msg.toolCalls.map((tc, idx) => (
                      <div key={idx} className="bg-slate-950/70 border border-emerald-500/20 rounded p-1.5 text-[9px] font-mono text-emerald-400 flex flex-col">
                        <div className="flex items-center gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                          <span className="font-bold">Tool:</span> {tc.tool_name}
                        </div>
                        <div className="mt-1 text-gray-500 text-[8px] truncate">
                          Args: {JSON.stringify(tc.tool_args)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
            
            {isLoading && (
              <div className="flex items-center gap-2 text-xs text-gray-400 font-mono">
                <span className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-ping" />
                Copilot is reasoning and selecting tools...
              </div>
            )}
          </div>

          {/* Form input */}
          <form onSubmit={handleSubmit} className="p-3 border-t border-white/5 bg-slate-950/30 flex gap-2">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask: 'Why is ORD-factory_alpha-1001 delayed?'"
              className="flex-1 bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-violet-500"
            />
            <button
              type="submit"
              disabled={isLoading}
              className="p-2 bg-violet-600 rounded-xl text-white hover:bg-violet-700 disabled:opacity-50 transition-colors shrink-0"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      )}
    </>
  );
}
