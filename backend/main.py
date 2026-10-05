from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel
import hashlib
from typing import Optional
import google.generativeai as genai
from PyPDF2 import PdfReader
from PIL import Image
import pytesseract
import io
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json
from database import save_report, get_all_reports, get_report_by_id, create_user, get_user_by_username, get_user_by_email
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Medical Report Analyzer API")

SECRET_KEY = "my-secret-key-12345"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")

class UserRegister(BaseModel):
    username: str
    email: str
    password: str
    full_name: str

class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    username: str
    email: str
    full_name: str

def get_password_hash(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain, hashed):
    return get_password_hash(plain) == hashed

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await get_user_by_username(username)
    if not user:
        raise credentials_exception
    return user

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Google Gemini AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('models/gemini-2.5-flash')
    print("✅ Gemini AI configured successfully")
else:
    print("⚠️  WARNING: GEMINI_API_KEY not found in .env file")

# Helper function to extract text from PDF
def extract_text_from_pdf(file_bytes):
    try:
        pdf_file = io.BytesIO(file_bytes)
        pdf_reader = PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading PDF: {str(e)}")

# Helper function to extract text from image using OCR
def extract_text_from_image(file_bytes):
    try:
        # Load image from bytes
        image = Image.open(io.BytesIO(file_bytes))
        
        # Point to the Tesseract executable path on Windows
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        # Extract text using pytesseract
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image OCR: {str(e)}")

# Helper function to analyze medical report with AI
def analyze_medical_report(report_text):
    prompt = f"""
You are a specialized Medical AI Assistant. Your task is to analyze medical laboratory reports.

CRITICAL: If the text provided is NOT a medical laboratory report (e.g., if it's a menu, a personal letter, a photo of a cat, or random text), you MUST:
1. Set the "isMedicalReport" field to false.
2. Set the "summary" to "Input document is not recognized as a medical laboratory report."
3. Leave "parameters" and "risks" as empty arrays [].
4. Set "overallAssessment" to "Validation Failed: No medical data found."

Medical Report Text to analyze:
{report_text}

Expected JSON Output format:
{{
  "isMedicalReport": true,
  "summary": "Brief overview of the report findings",
  "parameters": [
    {{
      "name": "Parameter name",
      "value": "Value with unit",
      "normalRange": "Normal range",
      "status": "normal/high/low"
    }}
  ],
  "risks": [
    {{
      "severity": "low/medium/high",
      "parameter": "Parameter name",
      "finding": "Description of abnormal finding",
      "recommendation": "Specific recommendation"
    }}
  ],
  "overallAssessment": "Overall health status assessment",
  "recommendations": [
    "Actionable health recommendation"
  ]
}}

Important: Return ONLY the JSON object. No additional text.
"""
    
    try:
        response = model.generate_content(prompt)
        ai_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if ai_text.startswith("```json"):
            ai_text = ai_text[7:]
        if ai_text.startswith("```"):
            ai_text = ai_text[3:]
        if ai_text.endswith("```"):
            ai_text = ai_text[:-3]
        ai_text = ai_text.strip()
        
        # Try to parse JSON
        try:
            parsed_result = json.loads(ai_text)
            return parsed_result
        except json.JSONDecodeError:
            # If parsing fails, return structured response with raw text
            return {
                "summary": "AI analysis completed",
                "raw_analysis": ai_text,
                "parameters": [],
                "risks": [],
                "overallAssessment": "Please review the raw analysis",
                "recommendations": []
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")

# Root endpoint
@app.get("/")
def read_root():
    return {
        "message": "Medical Report Analyzer API",
        "version": "1.0.0",
        "status": "running",
        "gemini_configured": GEMINI_API_KEY is not None
    }

# Health check endpoint
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "ai_ready": GEMINI_API_KEY is not None
    }

# Authentication endpoints
@app.post("/api/register", response_model=User)
async def register(user: UserRegister):
    print(f"🔵 Register endpoint called for: {user.username}")
    
    existing_user = await get_user_by_username(user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
        
    existing_email = await get_user_by_email(user.email)
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    hashed_password = get_password_hash(user.password)
    user_dict = {
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "hashed_password": hashed_password
    }
    
    await create_user(user_dict)
    print(f"✅ User registered in MongoDB: {user.username}")
    return User(username=user.username, email=user.email, full_name=user.full_name)

@app.post("/api/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    print(f"🔵 Login attempt for: {form_data.username}")
    
    user = await get_user_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
        
    token = create_access_token(data={"sub": user["username"]})
    print(f"✅ Login successful: {form_data.username}")
    return {"access_token": token, "token_type": "bearer"}

@app.get("/api/me", response_model=User)
async def get_me(current_user: dict = Depends(get_current_user)):
    return User(
        username=current_user["username"],
        email=current_user["email"],
        full_name=current_user["full_name"]
    )

# File upload and analysis endpoint
@app.post("/api/upload")
async def upload_report(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    print(f"📄 Received file: {file.filename} from user: {current_user['username']}")
    
    # Validate file type
    allowed_types = ["application/pdf", "image/jpeg", "image/png"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDF, JPG, and PNG are allowed."
        )
    
    # Check file size (max 10MB)
    file_bytes = await file.read()
    file_size_mb = len(file_bytes) / (1024 * 1024)
    if file_size_mb > 10:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 10MB."
        )
    
    print(f"📊 File size: {file_size_mb:.2f} MB")
    
    try:
        # Extract text based on file type
        if file.content_type == "application/pdf":
            print("📖 Extracting text from PDF...")
            report_text = extract_text_from_pdf(file_bytes)
        elif file.content_type in ["image/jpeg", "image/png"]:
            print("👁️ Extracting text from Image via OCR...")
            report_text = extract_text_from_image(file_bytes)
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type."
            )
        
        if not report_text or len(report_text.strip()) < 15:
            error_msg = "Could not extract sufficient text."
            if file.content_type == "application/pdf":
                error_msg += " Please ensure the PDF contains readable text."
            else:
                error_msg += " Ensure the image is clear, brightly lit, and the text is legible."
            raise HTTPException(
                status_code=400,
                detail=error_msg
            )
        
        print(f"✅ Extracted {len(report_text)} characters")
        
        # Analyze with AI
        if not GEMINI_API_KEY:
            print("⚠️  No API key - returning mock data")
            analysis_result = {
                "summary": "Mock analysis - API key not configured",
                "parameters": [
                    {
                        "name": "Hemoglobin",
                        "value": "13.2 g/dL",
                        "normalRange": "13.5-17.5 g/dL",
                        "status": "low"
                    },
                    {
                        "name": "WBC Count",
                        "value": "7,500 /µL",
                        "normalRange": "4,000-11,000 /µL",
                        "status": "normal"
                    }
                ],
                "risks": [
                    {
                        "severity": "low",
                        "parameter": "Hemoglobin",
                        "finding": "Slightly below normal range",
                        "recommendation": "Consider iron-rich diet and consult doctor"
                    }
                ],
                "overallAssessment": "Generally healthy with minor concerns",
                "recommendations": [
                    "Consult with healthcare provider about hemoglobin levels",
                    "Maintain regular checkups"
                ]
            }
        else:
            print("🤖 Analyzing with Gemini AI...")
            analysis_result = analyze_medical_report(report_text)
            print("✅ AI analysis completed")
        
        # Prepare response data (all JSON-serializable)
        response_data = {
            "success": True,
            "filename": file.filename,
            "fileSize": f"{file_size_mb:.2f} MB",
            "uploadDate": datetime.now().isoformat(),
            "extractedTextPreview": report_text[:300] + "...",
            "analysis": analysis_result,
            "username": current_user["username"]
        }
        
        # Save to MongoDB database
        try:
            # Save a copy to database
            report_id = await save_report(response_data.copy())
            # Add string version of ID to response
            response_data["reportId"] = str(report_id)
            print(f"✅ Saved to database with ID: {report_id}")
        except Exception as e:
            print(f"⚠️  Warning: Could not save to database: {str(e)}")
            response_data["reportId"] = None
        
        print("✅ Sending response to frontend")
        return JSONResponse(content=response_data)
    
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )

# Get analysis history from database
@app.get("/api/history")
async def get_history(current_user: dict = Depends(get_current_user)):
    try:
        reports = await get_all_reports()
        # Format for frontend
        formatted_reports = []
        for report in reports:
            # Simple permission check
            if report.get("username") == current_user["username"] or "username" not in report:
                formatted_reports.append({
                    "id": report["_id"],
                    "name": report["filename"],
                    "date": report["uploadDate"],
                    "risksDetected": len(report["analysis"].get("risks", [])),
                    "parameters": len(report["analysis"].get("parameters", [])),
                    "status": "analyzed"
                })
        print(f"📊 Retrieved {len(formatted_reports)} reports from database for {current_user['username']}")
        return {"reports": formatted_reports}
    except Exception as e:
        print(f"❌ Error fetching history: {str(e)}")
        # Return empty list if database is not available
        return {"reports": []}

# Get specific report by ID
@app.get("/api/report/{report_id}")
async def get_report(report_id: str, current_user: dict = Depends(get_current_user)):
    try:
        report = await get_report_by_id(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        # Check ownership
        if report.get("username") and report.get("username") != current_user["username"]:
            raise HTTPException(status_code=403, detail="Not authorized to view this report")
        return report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving report: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Medical Report Analyzer API...")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)