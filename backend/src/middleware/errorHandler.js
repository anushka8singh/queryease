function notFoundHandler(req, res, next) {
  res.status(404).json({
    message: `Route ${req.method} ${req.originalUrl} was not found.`,
  });
}

function errorHandler(error, req, res, next) {
  const statusCode = error.statusCode || error.status || 500;
  const isServerError = statusCode >= 500;
  const isJsonSyntaxError = error instanceof SyntaxError && error.status === 400 && "body" in error;

  if (isJsonSyntaxError) {
    return res.status(400).json({
      message: "Request body contains invalid JSON.",
    });
  }

  const details = error.details || null;

  res.status(statusCode).json({
    message: details?.message || (isServerError ? "Unexpected server error." : error.message || "Request failed."),
    details: isServerError && !details ? null : details,
  });
}

module.exports = {
  notFoundHandler,
  errorHandler,
};
