const mongoose = require("mongoose");

const MedicalReportSchema = new mongoose.Schema(
  {
    patientName: {
      type: String,
      required: true,
    },
    age: {
      type: Number,
      required: true,
    },
    reportType: {
      type: String,
      required: true,
    },
    extractedText: {
      type: String,
    },
  },
  { timestamps: true }
);

module.exports = mongoose.model("MedicalReport", MedicalReportSchema);
