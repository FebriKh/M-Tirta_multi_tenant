# M-Tirta/api/dependencies.py
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from shared.backend.database import get_db
from shared.backend.crud.crud_pengurus import get_pengurus_by_user_web
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY  = os.getenv("SECRET_KEY")
ALGORITHM   = os.getenv("ALGORITHM", "HS256")
DEV_USER    = os.getenv("DEV_USER_WEB")
DEV_PASS    = os.getenv("DEV_PASSWORD_WEB")
DEV_NAMA    = os.getenv("DEV_NAMA", "Developer")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def create_token(data: dict) -> str:
    from jose import jwt
    from datetime import datetime, timedelta
    expire = datetime.utcnow() + timedelta(
        minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 480))
    )
    data.update({"exp": expire})
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tidak valid"
        )

def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> dict:


    """ambil user dari cookie token"""
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Belum login"
        )
    payload = verify_token(token)
    return payload

def require_role(roles: list):
    """decorator untuk cek role"""
    def checker(user: dict = Depends(get_current_user)):
        if user.get("jabatan") == "developer":
            return user
        if user.get("jabatan") not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Akses ditolak"
            )
        return user
    return checker
