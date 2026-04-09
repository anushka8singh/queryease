const DEFAULT_AI_ENGINE_URL = process.env.AI_ENGINE_URL || "http://127.0.0.1:8000";
const REQUEST_TIMEOUT_MS = Number(process.env.AI_ENGINE_TIMEOUT_MS || 30000);
const AI_QUERY_PATHS = ["/ai/query", "/ai"];

async function callAiEngine(path, options = {}) {
  const url = new URL(path, DEFAULT_AI_ENGINE_URL).toString();
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  let response;
  try {
    response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
  } catch (error) {
    clearTimeout(timeout);

    const upstreamError = new Error("AI engine is unavailable.");
    upstreamError.statusCode = error.name === "AbortError" ? 504 : 502;
    upstreamError.details = {
      message:
        error.name === "AbortError"
          ? "AI engine request timed out."
          : "Unable to reach the AI engine service.",
    };
    throw upstreamError;
  }

  clearTimeout(timeout);

  let payload;
  try {
    payload = await response.json();
  } catch (error) {
    payload = {
      message: "AI engine returned a non-JSON response.",
    };
  }

  if (!response.ok) {
    const upstreamError = new Error(payload.message || "AI engine request failed.");
    upstreamError.statusCode = response.status;
    upstreamError.details = payload;
    throw upstreamError;
  }

  return payload;
}

async function submitNaturalLanguageQuery({ query, context, provider }) {
  const payload = { query, context, provider };
  let lastError;

  for (const path of AI_QUERY_PATHS) {
    try {
      return await callAiEngine(path, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });
    } catch (error) {
      lastError = error;
      if (error.statusCode !== 404) {
        throw error;
      }
    }
  }

  throw lastError;
}

async function pingAiEngine() {
  return callAiEngine("/health", {
    method: "GET",
  });
}

module.exports = {
  submitNaturalLanguageQuery,
  pingAiEngine,
};
