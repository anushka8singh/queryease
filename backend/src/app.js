const express = require("express");
const cors = require("cors");

const queryRoutes = require("./routes/queryRoutes");
const { notFoundHandler, errorHandler } = require("./middleware/errorHandler");

const app = express();

app.disable("x-powered-by");
app.use(
  cors({
    origin: process.env.CORS_ORIGIN || "*",
  }),
);
app.use(express.json({ limit: "1mb" }));

app.get("/health", (req, res) => {
  res.json({
    status: "ok",
    service: "queryease-backend",
    aiEngineUrl: process.env.AI_ENGINE_URL || "http://127.0.0.1:8000",
  });
});

// The backend only acts as an API gateway and leaves SQL generation to the AI service.
app.use("/api/query", queryRoutes);

app.use(notFoundHandler);
app.use(errorHandler);

module.exports = app;
