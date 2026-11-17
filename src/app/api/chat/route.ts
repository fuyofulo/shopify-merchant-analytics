import type { UIMessage } from "ai";

import { streamMerchantAnswer } from "@/lib/assistant/answer";
import { merchantErrorMessage } from "@/lib/assistant/errors";
import { getChatModel, MissingApiKeyError } from "@/lib/assistant/model";

/**
 * POST /api/chat — streams an answer to a merchant's question.
 *
 * Body, either:
 *   { "messages": UIMessage[] }   // what the AI SDK's useChat() sends
 *   { "question": "..." }         // a single question, handy for curl
 *
 * Responds with an AI SDK UI message stream (server-sent events) that carries
 * the tool call (with its exact dates), the tool result (rows, totals and a
 * chart spec), and the model's answer text.
 */
export async function POST(request: Request) {
  let body: { messages?: unknown; question?: unknown };
  try {
    body = await request.json();
  } catch {
    return Response.json({ error: "Request body must be valid JSON." }, { status: 400 });
  }

  const messages = toMessages(body);
  if (!messages) {
    return Response.json(
      { error: 'Send { "question": "..." } or { "messages": [...] } (AI SDK UI messages).' },
      { status: 400 },
    );
  }

  let model;
  try {
    model = getChatModel();
  } catch (error) {
    if (error instanceof MissingApiKeyError) return Response.json({ error: error.message }, { status: 500 });
    throw error;
  }

  const result = await streamMerchantAnswer({ model, messages });
  return result.toUIMessageStreamResponse({ onError: describeError });
}

function toMessages(body: { messages?: unknown; question?: unknown }): UIMessage[] | null {
  if (typeof body.question === "string" && body.question.trim()) {
    return [{ id: "question", role: "user", parts: [{ type: "text", text: body.question.trim() }] }];
  }
  if (Array.isArray(body.messages) && body.messages.length > 0) return body.messages as UIMessage[];
  return null;
}

/** Logs the full error on the server; the merchant gets a short sentence they can act on. */
function describeError(error: unknown): string {
  console.error("[api/chat]", error);
  return merchantErrorMessage(error);
}
