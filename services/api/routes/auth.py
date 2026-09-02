from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from datetime import datetime
from services.api.db import get_db
from services.api.auth import hash_password, create_access_token, verify_google_token

router = APIRouter(prefix="/auth", tags=["auth"])

class GoogleVerifyRequest(BaseModel):
    credential: str

class GoogleVerifyResponse(BaseModel):
    access_token: str
    user_id: str
    name: str
    email: str
    avatar_url: str | None = None

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

@router.post("/google/verify", response_model=GoogleVerifyResponse)
async def google_verify(req: GoogleVerifyRequest):
    """
    Verify a Google ID token, upsert the user, and return a JWT session.
    """
    google_payload = await verify_google_token(req.credential)

    google_sub = google_payload.get("sub")
    email = google_payload.get("email", "")
    name = google_payload.get("name", email.split("@")[0] if email else "User")
    avatar_url = google_payload.get("picture")

    if not google_sub:
        raise HTTPException(status_code=400, detail="Missing Google user ID")

    with get_db() as cur:
        # Check for existing user by Google sub
        cur.execute(
            "SELECT user_id, name, email FROM users WHERE oauth_provider = 'google' AND oauth_id = %s",
            (google_sub,),
        )
        existing = cur.fetchone()

        if existing:
            # Update name/email/avatar if changed
            cur.execute(
                "UPDATE users SET name = %s, email = %s, avatar_url = %s WHERE user_id = %s",
                (name, email, avatar_url, existing["user_id"]),
            )
            user_id = str(existing["user_id"])
        else:
            # Also check if there's an existing account with this email (link them)
            cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
            linked = cur.fetchone()

            if linked:
                cur.execute(
                    "UPDATE users SET oauth_provider = 'google', oauth_id = %s, avatar_url = %s WHERE user_id = %s",
                    (google_sub, avatar_url, linked["user_id"]),
                )
                user_id = str(linked["user_id"])
            else:
                # Create new user
                cur.execute(
                    "INSERT INTO users (name, email, oauth_provider, oauth_id, avatar_url) "
                    "VALUES (%s, %s, 'google', %s, %s) RETURNING user_id",
                    (name, email, google_sub, avatar_url),
                )
                result = cur.fetchone()
                user_id = str(result["user_id"])

    token = create_access_token(user_id)
    return {
        "access_token": token,
        "user_id": user_id,
        "name": name,
        "email": email,
        "avatar_url": avatar_url,
    }


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
