function validateQueryPayload(req, res, next) {
  const { query, context, provider } = req.body || {};
  const normalizedQuery = typeof query === "string" ? query.trim() : "";
  const normalizedProvider = typeof provider === "string" ? provider.trim().toLowerCase() : undefined;
  const allowedProviders = new Set(["rules", "gemini"]);

  if (typeof query !== "string" || normalizedQuery.length < 3) {
    return res.status(400).json({
      message: "The request body must include a query string with at least 3 characters.",
    });
  }

  if (normalizedQuery.length > 2000) {
    return res.status(400).json({
      message: "The query must not exceed 2000 characters.",
    });
  }

  if (context !== undefined && (typeof context !== "object" || Array.isArray(context) || context === null)) {
    return res.status(400).json({
      message: "If provided, context must be a JSON object.",
    });
  }

  if (provider !== undefined && typeof provider !== "string") {
    return res.status(400).json({
      message: "If provided, provider must be a string.",
    });
  }

  if (normalizedProvider !== undefined && !allowedProviders.has(normalizedProvider)) {
    return res.status(400).json({
      message: "Provider must be one of: rules, gemini.",
    });
  }

  req.body.query = normalizedQuery;
  if (normalizedProvider !== undefined) {
    req.body.provider = normalizedProvider;
  }

  return next();
}

module.exports = {
  validateQueryPayload,
};
