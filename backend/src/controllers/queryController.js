const { submitNaturalLanguageQuery, pingAiEngine } = require("../services/aiEngineClient");

async function handleQuery(req, res, next) {
  try {
    const payload = {
      query: req.body.query,
      context: req.body.context || {},
      provider: req.body.provider,
    };

    const response = await submitNaturalLanguageQuery(payload);
    res.status(200).json({
      sql: response.sql || "",
      result: Array.isArray(response.result) ? response.result : [],
      logs: Array.isArray(response.logs) ? response.logs : [],
    });
  } catch (error) {
    next(error);
  }
}

async function handleHealthCheck(req, res, next) {
  try {
    const response = await pingAiEngine();
    res.status(200).json(response);
  } catch (error) {
    next(error);
  }
}

module.exports = {
  handleQuery,
  handleHealthCheck,
};
