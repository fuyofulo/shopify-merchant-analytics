"use client";

import { useChat } from "@ai-sdk/react";
import { isTextUIPart } from "ai";
import { useEffect, useRef, useState, type FormEvent } from "react";

import type { MerchantUIMessage } from "@/lib/assistant/ui-types";

import { AssistantReply } from "./assistant-reply";

/** The merchant chat: ask a question, watch the steps, get a chart and a short answer. */
export function Chat({ suggestions, dataNote }: { suggestions: string[]; dataNote: string }) {
  const { messages, sendMessage, status, error, stop, regenerate } = useChat<MerchantUIMessage>();
  const [input, setInput] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  const busy = status === "submitted" || status === "streaming";
  const last = messages.at(-1);
  // Waiting for the first streamed part: show a reply with just the first step.
  const pendingReply = (busy || error) && last?.role === "user";

  useEffect(() => {
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    endRef.current?.scrollIntoView({ block: "end", behavior: reduceMotion ? "auto" : "smooth" });
  }, [messages, status]);

  const ask = (question: string) => {
    const text = question.trim();
    if (!text || busy) return;
    sendMessage({ text });
    setInput("");
  };

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    ask(input);
  };

  return (
    <div className="mx-auto flex h-dvh w-full max-w-3xl flex-col px-4">
      <header className="border-b border-hairline py-4">
        <h1 className="text-lg font-semibold text-ink">Store assistant</h1>
        <p className="text-sm text-ink-2">Ask about sales, returns or repeat customers. {dataNote}</p>
      </header>

      <main className="flex-1 overflow-y-auto py-6">
        {messages.length === 0 ? (
          <div className="space-y-3">
            <p className="text-sm text-ink-2">Try a question merchants have asked:</p>
            <ul className="flex flex-wrap gap-2">
              {suggestions.map((suggestion) => (
                <li key={suggestion}>
                  <button
                    type="button"
                    onClick={() => ask(suggestion)}
                    className="rounded-full border border-hairline bg-surface px-3 py-1.5 text-sm text-ink hover:bg-wash"
                  >
                    {suggestion}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ) : (
          <ol className="space-y-6">
            {messages.map((message, index) =>
              message.role === "user" ? (
                <li key={message.id} className="flex justify-end">
                  <p className="max-w-[85%] rounded-2xl bg-wash px-4 py-2 text-[15px] text-ink">
                    {message.parts.filter(isTextUIPart).map((part) => part.text).join("")}
                  </p>
                </li>
              ) : (
                <li key={message.id}>
                  <AssistantReply
                    message={message}
                    error={index === messages.length - 1 ? error : undefined}
                    onRetry={index === messages.length - 1 && error ? () => regenerate() : undefined}
                  />
                </li>
              ),
            )}
            {pendingReply && (
              <li>
                <AssistantReply error={error} onRetry={error ? () => regenerate() : undefined} />
              </li>
            )}
          </ol>
        )}
        <div ref={endRef} />
      </main>

      <form onSubmit={onSubmit} className="flex gap-2 border-t border-hairline py-4">
        <label htmlFor="question" className="sr-only">
          Ask a question about your store
        </label>
        <input
          id="question"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="e.g. which coats got returned most over the last couple weeks?"
          autoComplete="off"
          className="min-w-0 flex-1 rounded-lg border border-hairline bg-surface px-3 py-2 text-[15px] text-ink placeholder:text-muted focus:outline-2 focus:outline-accent"
        />
        {busy ? (
          <button
            type="button"
            onClick={() => stop()}
            className="rounded-lg border border-hairline px-4 py-2 text-sm text-ink hover:bg-wash"
          >
            Stop
          </button>
        ) : (
          <button
            type="submit"
            disabled={!input.trim()}
            className="rounded-lg bg-ink px-4 py-2 text-sm font-medium text-surface disabled:opacity-40"
          >
            Ask
          </button>
        )}
      </form>
    </div>
  );
}
