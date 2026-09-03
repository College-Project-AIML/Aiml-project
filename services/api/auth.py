import os
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
import httpx

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(user_id: str) -> str:
    secret_key = os.getenv("SECRET_KEY", "CHANGE_ME")
    algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    expire_minutes = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))
    
    expire = datetime.utcnow() + timedelta(minutes=expire_minutes)
    payload = {"sub": str(user_id), "exp": expire}
    
    return jwt.encode(payload, secret_key, algorithm=algorithm)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    secret_key = os.getenv("SECRET_KEY", "CHANGE_ME")
    algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


# ── Google OAuth helpers ─────────────────────────────────────────────────────

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

async def verify_google_token(credential: str) -> dict:
    """
    Verify a Google ID token by calling Google's tokeninfo endpoint.
    Returns the verified payload with fields like sub, email, name, picture.
    Raises HTTPException on failure.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": credential},
            timeout=10.0,
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    payload = resp.json()

    # Validate audience matches our client ID (if configured)
    if GOOGLE_CLIENT_ID and payload.get("aud") != GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=401, detail="Token audience mismatch")

    # Check token hasn't expired (tokeninfo returns 200 even for expired;
    # check the exp claim explicitly)
    exp = payload.get("exp")
    if exp and int(exp) < int(datetime.utcnow().timestamp()):
        raise HTTPException(status_code=401, detail="Google token expired")

    return payload
