from fastapi import FastAPI, HTTPException, Depends, status, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
import hashlib
from typing import Optional

app = FastAPI(title="Medical Report Analyzer with Auth")

SECRET_KEY = "my-secret-key-12345"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

fake_users_db = {}
fake_reports_db = {}

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
    
    user = fake_users_db.get(username)
    if not user:
        raise credentials_exception
    return user

# ═══════════════════════════════════════════════════════════
# PUBLIC ENDPOINTS
# ═══════════════════════════════════════════════════════════

@app.get("/")
async def root():
    return {"message": "Medical Report Analyzer API", "version": "1.0", "auth": "enabled"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# ═══════════════════════════════════════════════════════════
# AUTHENTICATION ENDPOINTS
# ═══════════════════════════════════════════════════════════

@app.post("/api/register", response_model=User)
async def register(user: UserRegister):
    print(f"🔵 Register endpoint called for: {user.username}")
    
    if user.username in fake_users_db:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    for existing_user in fake_users_db.values():
        if existing_user["email"] == user.email:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed = get_password_hash(user.password)
    fake_users_db[user.username] = {
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "hashed_password": hashed
    }
    fake_reports_db[user.username] = []
    
    print(f"✅ User registered: {user.username}")
    return User(username=user.username, email=user.email, full_name=user.full_name)

@app.post("/api/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    print(f"🔵 Login attempt for: {form_data.username}")
    
    user = fake_users_db.get(form_data.username)
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

# ═══════════════════════════════════════════════════════════
# PROTECTED REPORT ENDPOINTS
# ═══════════════════════════════════════════════════════════

@app.get("/api/history")
async def get_history(current_user: dict = Depends(get_current_user)):
    reports = fake_reports_db.get(current_user["username"], [])
    print(f"📋 Fetching {len(reports)} reports for: {current_user['username']}")
    return {"reports": reports}

@app.post("/api/upload")
async def upload_report(
    file: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user)
):
    print(f"📤 Upload request from user: {current_user['username']}")
    
    # Get filename from uploaded file or use default
    filename = file.filename if file else "Sample Blood Test.pdf"
    
    # Create new report
    new_report = {
        "id": f"report_{len(fake_reports_db.get(current_user['username'], []))+1}",
        "name": filename,
        "date": datetime.now().isoformat(),
        "risksDetected": 2,
        "parameters": 10,
        "status": "analyzed"
    }
    
    # Initialize reports list if doesn't exist
    if current_user["username"] not in fake_reports_db:
        fake_reports_db[current_user["username"]] = []
    
    # Add report to user's reports
    fake_reports_db[current_user["username"]].append(new_report)
    
    print(f"✅ Report uploaded for: {current_user['username']} - {filename}")
    
    return {
        "message": "Report uploaded successfully", 
        "report": new_report
    }

@app.get("/api/report/{report_id}")
async def get_report(report_id: str, current_user: dict = Depends(get_current_user)):
    user_reports = fake_reports_db.get(current_user["username"], [])
    
    for report in user_reports:
        if report["id"] == report_id:
            return report
    
    raise HTTPException(status_code=404, detail="Report not found")

# ═══════════════════════════════════════════════════════════
# DEBUG ENDPOINT (Remove in production)
# ═══════════════════════════════════════════════════════════

@app.get("/debug/users")
async def debug_users():
    """Debug endpoint to see all registered users"""
    return {
        "total_users": len(fake_users_db),
        "users": [
            {"username": u["username"], "email": u["email"]} 
            for u in fake_users_db.values()
        ]
    }

@app.get("/debug/reports")
async def debug_reports():
    """Debug endpoint to see all reports"""
    total = sum(len(reports) for reports in fake_reports_db.values())
    return {
        "total_reports": total,
        "reports_by_user": {
            username: len(reports) 
            for username, reports in fake_reports_db.items()
        }
    }