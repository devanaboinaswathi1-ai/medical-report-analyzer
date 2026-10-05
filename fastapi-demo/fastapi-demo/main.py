from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Medical Report Analyzer API", version="1.0.0")

# Security Configuration
SECRET_KEY = "medical-report-analyzer-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-Memory Database
fake_users_db = {}
fake_reports_db = {}

# Models
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

# Helper Functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

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
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = fake_users_db.get(username)
    if user is None:
        raise credentials_exception
    return user

# API Endpoints
@app.get("/", tags=["Root"])
async def root():
    return {"message": "Medical Report Analyzer API", "version": "1.0"}

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}

@app.post("/api/register", response_model=User, tags=["Authentication"])
async def register(user: UserRegister):
    if user.username in fake_users_db:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    for existing_user in fake_users_db.values():
        if existing_user["email"] == user.email:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    fake_users_db[user.username] = {
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "hashed_password": hashed_password
    }
    fake_reports_db[user.username] = []
    
    print(f"✅ User registered: {user.username}")
    return User(username=user.username, email=user.email, full_name=user.full_name)

@app.post("/api/login", response_model=Token, tags=["Authentication"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = fake_users_db.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user["username"]})
    print(f"✅ User logged in: {form_data.username}")
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/me", response_model=User, tags=["Authentication"])
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return User(
        username=current_user["username"],
        email=current_user["email"],
        full_name=current_user["full_name"]
    )

@app.get("/api/history", tags=["Reports"])
async def get_history(current_user: dict = Depends(get_current_user)):
    user_reports = fake_reports_db.get(current_user["username"], [])
    print(f"📋 Fetching {len(user_reports)} reports for: {current_user['username']}")
    return {"reports": user_reports}

@app.post("/api/upload", tags=["Reports"])
async def upload_report(current_user: dict = Depends(get_current_user)):
    new_report = {
        "id": f"report_{len(fake_reports_db.get(current_user['username'], []))+1}",
        "name": "Sample Blood Test.pdf",
        "date": datetime.now().isoformat(),
        "risksDetected": 2,
        "parameters": 10,
        "status": "analyzed"
    }
    
    if current_user["username"] not in fake_reports_db:
        fake_reports_db[current_user["username"]] = []
    
    fake_reports_db[current_user["username"]].append(new_report)
    print(f"📤 Report uploaded for: {current_user['username']}")
    return {"message": "Report uploaded successfully", "report": new_report}

@app.get("/api/report/{report_id}", tags=["Reports"])
async def get_report(report_id: str, current_user: dict = Depends(get_current_user)):
    user_reports = fake_reports_db.get(current_user["username"], [])
    for report in user_reports:
        if report["id"] == report_id:
            return report
    raise HTTPException(status_code=404, detail="Report not found")

if __name__ == "__main__":
    print("🏥 Medical Report Analyzer API - http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)