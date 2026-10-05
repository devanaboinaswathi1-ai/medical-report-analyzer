const express = require("express");
const router = express.Router();
const MedicalReport = require("../models/MedicalReport");

// Create new medical report
router.post("/create", async (req, res) => {
  try {
    const report = new MedicalReport(req.body);
    await report.save();

    res.status(201).json({
      message: "Medical report saved successfully",
      data: report,
    });
  } catch (error) {
    res.status(500).json({
      error: error.message,
    });
  }
});

module.exports = router;
