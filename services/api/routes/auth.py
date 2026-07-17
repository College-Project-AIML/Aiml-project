from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from datetime import datetime
from services.api.db import get_db
from services.api.auth import hash_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    user_id: str
    name: str
    email: str
    role: str
    created_at: datetime

@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest):
    with get_db() as cur:
        cur.execute("SELECT user_id FROM users WHERE email = %s", (req.email,))
        existing = cur.fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
            
        hashed = hash_password(req.password)
        cur.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s) RETURNING user_id",
            (req.name, req.email, hashed)
        )
        result = cur.fetchone()
        
        token = create_access_token(str(result['user_id']))
        return {"access_token": token, "token_type": "bearer"}
