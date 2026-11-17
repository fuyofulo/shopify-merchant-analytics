import { createOpenRouter } from "@openrouter/ai-sdk-provider";

/**
 * Free OpenRouter models that support tool calling, tried in this order.
 * OpenRouter falls through to the next one when a model is rate-limited or down,
 * which happens often on the free tier.
 */
export const DEFAULT_FREE_MODELS = [
  "google/gemma-4-31b-it:free",
  "nvidia/nemotron-3-ultra-550b-a55b:free",
  "google/gemma-4-26b-a4b-it:free",
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
