const express = require("express");
const cors = require("cors");

const queryRoutes = require("./routes/queryRoutes");
const { notFoundHandler, errorHandler } = require("./middleware/errorHandler");

const app = express();

app.disable("x-powered-by");
app.use(
  cors({
    origin: process.env.CORS_ORIGIN || "*",
    methods: ["GET", "POST"],
    allowedHeaders: ["Content-Type"],
  }),
);
app.use(express.json({ limit: "1mb" }));
app.use((req, res, next) => {
  if (req.method === "POST" && (req.path === "/query" || req.path === "/api/query" || req.path === "/api/query/")) {
    console.log("Incoming query:", req.body);
  }

  next();
});

app.get("/health", (req, res) => {
  res.json({
    status: "ok",
    service: "queryease-backend",
    aiEngineUrl: process.env.AI_ENGINE_URL || "http://127.0.0.1:8000",
  });
});

// The backend only acts as an API gateway and leaves SQL generation to the AI service.
app.use("/api/query", queryRoutes);
app.use("/query", queryRoutes);

app.use(notFoundHandler);
app.use(errorHandler);

module.exports = app;
