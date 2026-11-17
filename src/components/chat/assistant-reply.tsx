"use client";

import { isTextUIPart, isToolUIPart } from "ai";
import { useEffect, useRef, useState } from "react";

import { stepsFor, type Step } from "@/lib/assistant/steps";
import { isReportOutput, type MerchantUIMessage } from "@/lib/assistant/ui-types";
import { ReportView } from "@/components/report/report-view";

import { AnswerText } from "./answer-text";

function StepIcon({ status }: { status: Step["status"] }) {
  if (status === "active") {
    return <span aria-hidden className="mt-1.5 h-2 w-2 shrink-0 animate-pulse rounded-full bg-muted" />;
  }
  if (status === "error") return <span aria-hidden className="w-2 shrink-0 text-critical">✕</span>;
  return <span aria-hidden className="w-2 shrink-0">✓</span>;
}

/** Minimum time each step stays as the newest line, so it can be read. */
const STEP_DWELL_MS = 450;

/**
 * How many steps to show. The report itself runs in milliseconds, so the tool
 * call and its result usually arrive together; revealing the real steps one at
 * a time (each newest step on screen for at least STEP_DWELL_MS) lets the
 * merchant read what was run before the steps fold away. Nothing is invented:
 * only steps that have already happened are shown. Errors show everything at once.
 */
function useRevealedCount(total: number, instant: boolean): number {
  const [count, setCount] = useState(1);
  const shownAt = useRef(0);

  useEffect(() => {
    shownAt.current = Date.now();
  }, [count]);

  useEffect(() => {
    if (instant || count >= total) return;
    const wait = Math.max(0, STEP_DWELL_MS - (Date.now() - shownAt.current));
    const timer = setTimeout(() => setCount((current) => current + 1), wait);
    return () => clearTimeout(timer);
  }, [count, total, instant]);

  return instant ? total : Math.min(count, total);
}

/** What the assistant is doing, in muted grey: built from the real streamed tool call. */
function StepList({ steps }: { steps: Step[] }) {
  return (
    <ol className="space-y-1 text-sm text-muted" aria-live="polite">
      {steps.map((step) => (
        <li key={step.id} className="flex gap-2">
          <StepIcon status={step.status} />
          <span className={step.status === "error" ? "text-ink-2" : undefined}>{step.label}</span>
        </li>
      ))}
    </ol>
  );
}

/**
 * One assistant reply, in the order the merchant experiences it:
 *  1. While waiting: the steps, in grey, appearing as they happen. No chart skeleton.
 *  2. When the result arrives: the chart pops in and the steps fold into "Show steps (N)".
 *  3. The plain-English answer streams in under the chart.
 * If something fails, the steps stay open and a friendly message takes the chart's place.
 */
export function AssistantReply({
  message,
  error,
  onRetry,
}: {
  message?: MerchantUIMessage;
  error?: Error;
  onRetry?: () => void;
}) {
  const parts = message?.parts ?? [];
  const toolPart = parts.find(isToolUIPart);
  const text = parts
    .filter(isTextUIPart)
    .map((part) => part.text)
    .join("");

  const allSteps = stepsFor(toolPart, Boolean(error));
  const failed = Boolean(error) || allSteps.some((step) => step.status === "error");
  const revealed = useRevealedCount(allSteps.length, failed);
  const revealing = revealed < allSteps.length;
  const steps = allSteps
    .slice(0, revealed)
    .map((step, index) =>
      revealing && index === revealed - 1 ? { ...step, label: step.activeLabel ?? step.label, status: "active" as const } : step,
    );

  // The chart lands (and the steps fold) only once every step has been shown.
  const resultReady = toolPart?.state === "output-available" && !revealing;
  const output = resultReady ? toolPart.output : undefined;
  const folded = resultReady && !failed;

  return (
    <div className="space-y-3">
      {folded ? (
        <details className="group">
          <summary className="cursor-pointer select-none list-none text-xs text-muted hover:text-ink-2">
            <span className="inline-block transition-transform group-open:rotate-90" aria-hidden>
              ›
            </span>{" "}
            Show steps ({steps.length})
          </summary>
          <div className="mt-2 pl-3">
            <StepList steps={steps} />
          </div>
        </details>
      ) : (
        <StepList steps={steps} />
      )}

      {isReportOutput(output) && <ReportView report={output} />}

      {failed && (
        <div className="pop-in rounded-xl border border-hairline bg-surface px-4 py-3 text-sm text-ink-2">
          <p>{error?.message || "Sorry, I couldn't get that report. Please try asking again."}</p>
          {onRetry && (
            <button
              type="button"
              onClick={onRetry}
              className="mt-2 rounded-md border border-hairline px-2.5 py-1 text-xs text-ink hover:bg-wash"
            >
              Try again
            </button>
          )}
        </div>
      )}

      {text && !revealing && <AnswerText text={text} />}
    </div>
  );
}
