# HealthCheck AI: Medical Report Analyzer

An AI-powered web application designed for patients and healthcare providers to instantly analyze and interpret complex medical laboratory reports.

## 🚀 Key Features

*   **Secure Authentication**: User registration and login using JWT (JSON Web Tokens) for session management.
*   **Intelligent Document Upload**: Support for both PDF digital reports and high-resolution **Image OCR** (JPEG/PNG) for physical report photos.
*   **AI Analysis**: Utilizes **Google Gemini 2.5 Flash** to extract medical data, evaluate risks, and provide actionable health summaries.
*   **Dynamic Health Dashboard**: A premium, real-time interface showing health parameters, risk assessments, and health status color-coding.
*   **Persistent Medical History**: Integrated with **MongoDB** to store every analysis for long-term health tracking.
*   **Export & Share**: Direct options to download an AI-generated text summary or share findings using the Web Share API.

## 🛠️ Technical Stack

- **Frontend**: React (with smooth animations and Tailwind CSS).
- **Backend**: FastAPI (Python).
- **Database**: MongoDB (Atlas).
- **AI Engine**: Google Generative AI (Gemini).
- **OCR Engine**: Tesseract OCR.

---

## 💻 Setup Instructions for Review

### 1. Prerequisites
- **Python 3.10+**
- **Node.js**
- **Tesseract OCR** (installed to `C:\Program Files\Tesseract-OCR\`)
- **MongoDB** account/atlas uri.

### 2. Running the Backend
1. Open a terminal in `/backend`.
2. Activate Virtual Environment: `.\venv\Scripts\Activate.ps1`
3. Start the API: `uvicorn main:app --reload --host 0.0.0.0 --port 8000`

### 3. Running the Frontend
1. Open a new terminal in `/frontend`.
2. Start the React app: `npm start`
3. View at: `http://localhost:3000` (by default).

---

## 🎯 Review Presentation Flow (Checklist)

1.  **Login/Register**: Demonstrate creating a new user account.
2.  **PDF/Image Upload**: Show that the system can read both text-based PDFs AND phone photos of laboratory reports.
3.  **Live Analysis**: Show the system analyzing the report in real-time.
4.  **Dashboard walkthrough**: Explain the risk levels and parameter tracking.
5.  **History Tab**: Demonstrate how old reports are saved and retrieved from the database.
6.  **Download Summary**: Click the download button to show the generated summary export.

---

**Built with ❤️ for AI Healthcare.**
