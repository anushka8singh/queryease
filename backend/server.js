const app = require("./src/app");

const port = Number(process.env.PORT || 3001);

app.listen(port, () => {
  console.log(`QueryEase backend listening on port ${port}`);
});
