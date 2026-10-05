require("dotenv").config(); // must be first

const express = require("express");
const mongoose = require("mongoose");
const reportRoutes = require("./routes/reportRoutes");

const app = express();
const PORT = process.env.PORT || 5000;

app.use(express.json());
app.use("/api/reports", reportRoutes);

// MongoDB connection
mongoose
  .connect(process.env.MONGO_URI)
  .then(() => console.log("✅ MongoDB Connected Successfully"))
  .catch((err) =>
    console.error("❌ MongoDB Connection Error:", err.message)
  );

app.get("/", (req, res) => {
  res.send("Medical Report Analyzer Backend Running");
});

app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
});
