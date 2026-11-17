import { createOpenRouter } from "@openrouter/ai-sdk-provider";

/**
 * Free OpenRouter models that support tool calling, tried in this order.
 * OpenRouter falls through to the next one when a model is rate-limited or down,
 * which happens often on the free tier.
 *
 * Chosen by running questions from the merchant requests against each free
 * tool-calling model (Nov 2026). All three picked the right tool with exact
 * dates and reported correct numbers. Ernie was fastest (~4s per answer).
 */
export const DEFAULT_FREE_MODELS = [
  "baidu/ernie-5.5-flash-preview:free",
  "inclusionai/ling-3.2-flash:free",
  "nvidia/nemotron-3-ultra-550b-a55b:free",
];

export class MissingApiKeyError extends Error {
  constructor() {
    super("OPENROUTER_API_KEY is not set. Add it to .env.local (see .env.example).");
  }
}

/**
 * The chat model, configured from the environment:
 * - OPENROUTER_API_KEY (required)
 * - OPENROUTER_MODEL (optional): one model ID, or a comma-separated list to
 *   try in order. Defaults to DEFAULT_FREE_MODELS.
 */
export function getChatModel() {
  const apiKey = process.env.OPENROUTER_API_KEY;
  if (!apiKey) throw new MissingApiKeyError();

  const models = (process.env.OPENROUTER_MODEL ?? "")
    .split(",")
    .map((model) => model.trim())
    .filter(Boolean);
  const [primary, ...fallbacks] = models.length > 0 ? models : DEFAULT_FREE_MODELS;

  const openrouter = createOpenRouter({ apiKey, appName: "Shopify Merchant Analytics" });
  return openrouter.chat(primary, {
    // One question → one tool call.
    parallelToolCalls: false,
    // OpenRouter tries these in order (https://openrouter.ai/docs/features/model-routing).
    ...(fallbacks.length > 0 ? { models: [primary, ...fallbacks] } : {}),
  });
}
