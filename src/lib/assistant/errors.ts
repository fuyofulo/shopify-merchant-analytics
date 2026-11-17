import { APICallError, RetryError } from "ai";

/**
 * Turns a model or provider error into a sentence a merchant can act on.
 * Retries wrap the provider's error in a RetryError, so look at the last attempt.
 */
export function merchantErrorMessage(error: unknown): string {
  const cause = RetryError.isInstance(error) ? error.lastError : error;
  if (APICallError.isInstance(cause)) {
    if (cause.statusCode === 429) {
      // OpenRouter's free tier has a per-minute limit and a daily cap ("free-models-per-day").
      return /per-day/i.test(`${cause.message} ${cause.responseBody ?? ""}`)
        ? "The free AI model has used up today's free requests. The limit resets at midnight UTC, so please try again then."
        : "The free AI model is busy right now. Please try again in a minute.";
    }
    if (cause.statusCode === 401 || cause.statusCode === 403) {
      return "The OpenRouter API key was rejected. Check OPENROUTER_API_KEY.";
    }
  }
  return "Something went wrong while answering. Please try again.";
}
