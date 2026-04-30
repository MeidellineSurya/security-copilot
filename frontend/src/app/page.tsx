"use client";

import { useState, useRef, useEffect } from "react";
import { ChatMessage } from "@/components/ChatMessage";
import { SuggestedPrompts } from "@/components/SuggestedPrompts";
import { querycopilot, fetchAssessments, seedData } from "@/lib/api";
import { Message, Assessment } from "@/types";

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [suggestedFollowups, setSuggestedFollowups] = useState<string[]>([]);
  const [seeding, setSeeding] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadAssessments();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function loadAssessments() {
    try {
      const data = await fetchAssessments();
      if (data.length > 0) setAssessment(data[0]);
    } catch {}
  }

  async function handleSeed() {
    setSeeding(true);
    try {
      const result = await seedData();
      await loadAssessments();
      setMessages([{
        role: "assistant",
        content: `✅ Demo data loaded for **${result.assessment_id ? "AcmePay" : "your company"}**.\n\n${result.risks_created} risks seeded. You can now ask me anything about this assessment.`,
        timestamp: new Date(),
      }]);
    } catch (e) {
      alert("Seed failed — is the backend running?");
    } finally {
      setSeeding(false);
    }
  }

  async function sendMessage(text: string) {
    if (!text.trim() || !assessment || loading) return;

    const userMsg: Message = { role: "user", content: text, timestamp: new Date() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    setSuggestedFollowups([]);

    // Build conversation history for memory
    const history = messages.map((m) => ({ role: m.role, content: m.content }));

    try {
      const response = await querycopilot(text, assessment.id, history);
      const assistantMsg: Message = {
        role: "assistant",
        content: response.answer,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
      setSuggestedFollowups(response.suggested_followups || []);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "⚠️ Failed to reach the copilot backend. Check that FastAPI is running on port 8000.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  }

  const isEmpty = messages.length === 0;

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <span className="text-white text-xs font-bold">SC</span>
          </div>
          <div>
            <h1 className="font-semibold text-gray-900 text-sm">Security Copilot</h1>
            {assessment ? (
              <p className="text-xs text-gray-500">{assessment.company} · {assessment.industry}</p>
            ) : (
              <p className="text-xs text-gray-400">No assessment loaded</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {assessment && (
            <span className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded-full border border-green-200">
              Assessment active
            </span>
          )}
          <button
            onClick={handleSeed}
            disabled={seeding}
            className="text-xs px-3 py-1.5 border border-gray-200 rounded-lg hover:bg-gray-50 text-gray-600 disabled:opacity-50"
          >
            {seeding ? "Loading..." : "Load demo data"}
          </button>
        </div>
      </header>

      {/* Chat area */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-3xl mx-auto">
          {isEmpty ? (
            <div className="flex flex-col items-center justify-center h-full min-h-[400px] text-center">
              <div className="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center mb-4">
                <span className="text-white text-2xl">🛡️</span>
              </div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Security Analyst Copilot</h2>
              <p className="text-gray-500 text-sm mb-6 max-w-md">
                Ask me anything about your assessment. I'll analyse risks, prioritise findings,
                and give you actionable recommendations.
              </p>
              {!assessment ? (
                <button
                  onClick={handleSeed}
                  disabled={seeding}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
                >
                  {seeding ? "Loading..." : "Load demo assessment to get started"}
                </button>
              ) : (
                <div className="w-full max-w-lg">
                  <p className="text-xs text-gray-400 mb-3 uppercase tracking-wide">Suggested questions</p>
                  <SuggestedPrompts onSelect={(p) => sendMessage(p)} />
                </div>
              )}
            </div>
          ) : (
            <>
              {messages.map((msg, i) => (
                <ChatMessage key={i} message={msg} />
              ))}
              {loading && (
                <div className="flex justify-start mb-4">
                  <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs font-bold mr-3 mt-1">
                    AI
                  </div>
                  <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
                    <div className="flex gap-1 items-center h-5">
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]" />
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                    </div>
                  </div>
                </div>
              )}
              {suggestedFollowups.length > 0 && !loading && (
                <div className="mb-4 pl-11">
                  <p className="text-xs text-gray-400 mb-2">Follow-up questions</p>
                  <SuggestedPrompts prompts={suggestedFollowups} onSelect={(p) => sendMessage(p)} />
                </div>
              )}
            </>
          )}
          <div ref={bottomRef} />
        </div>
      </div>

      {/* Input area */}
      <div className="bg-white border-t border-gray-200 px-4 py-4 shrink-0">
        <div className="max-w-3xl mx-auto">
          <div className="flex gap-3 items-end">
            <textarea
              className="flex-1 resize-none border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent max-h-32 min-h-[48px]"
              placeholder={assessment ? "Ask about your risks..." : "Load a demo assessment first"}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={!assessment || loading}
              rows={1}
            />
            <button
              onClick={() => sendMessage(input)}
              disabled={!input.trim() || !assessment || loading}
              className="px-4 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors text-sm font-medium shrink-0"
            >
              Send
            </button>
          </div>
          <p className="text-xs text-gray-400 mt-2 text-center">
            Powered by retrieval-augmented generation · risks sourced from MongoDB
          </p>
        </div>
      </div>
    </div>
  );
}