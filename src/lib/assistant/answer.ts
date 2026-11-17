import { convertToModelMessages, stepCountIs, streamText, type LanguageModel, type UIMessage } from "ai";
import { z } from "zod";

import { describeDataset, type DatasetDescription } from "@/lib/analytics";

import { buildInstructions } from "./instructions";
import { createMerchantTools } from "./tools";

/**
 * The date the assistant treats as "today". The order data is historical and
 * ends on 2025-10-27 (the day the merchant requests were sent), so by default
 * "today" is the last day of data. Set STORE_TODAY=YYYY-MM-DD to override it.
 */
export function storeToday(dataset: DatasetDescription = describeDataset()): string {
  const override = process.env.STORE_TODAY?.trim();
  if (override) {
    if (!z.iso.date().safeParse(override).success) {
      throw new Error(`STORE_TODAY must be a date in YYYY-MM-DD format, got "${override}".`);
    }
    return override;
  }
  return dataset.latestDataDate ?? new Date().toISOString().slice(0, 10);
}

/**
 * Answers a merchant's question as a stream, in two steps:
 *   1. The model must make exactly one tool call (toolChoice "required"), with
 *      exact dates taken from the date table in the instructions.
 *   2. The model answers in plain words from that result, with no tools available.
 */
export async function streamMerchantAnswer({
  model,
  messages,
  today,
}: {
  model: LanguageModel;
  messages: UIMessage[];
  today?: string;
}) {
  const dataset = describeDataset();
  const tools = createMerchantTools();

  return streamText({
    model,
    instructions: buildInstructions(today ?? storeToday(dataset), dataset),
    messages: await convertToModelMessages(messages, { tools }),
    tools,
    prepareStep: ({ stepNumber }) => (stepNumber === 0 ? { toolChoice: "required" } : { toolChoice: "none" }),
    stopWhen: stepCountIs(2),
    temperature: 0,
  });
}
