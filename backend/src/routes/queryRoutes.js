const express = require("express");

const { handleQuery, handleHealthCheck } = require("../controllers/queryController");
const { validateQueryPayload } = require("../middleware/validateRequest");

const router = express.Router();

router.get("/health", handleHealthCheck);
router.post("/", validateQueryPayload, handleQuery);

module.exports = router;
