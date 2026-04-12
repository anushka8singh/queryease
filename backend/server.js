const app = require("./src/app");

const port = Number(process.env.PORT || 5000);
const aiEngineUrl = process.env.AI_ENGINE_URL || "http://127.0.0.1:8000";

app.listen(port, () => {
  console.log(`QueryEase backend listening on port ${port}`);
  console.log(`Frontend origin expected at http://localhost:5173`);
  console.log(`AI engine target: ${aiEngineUrl}/ai`);
});
