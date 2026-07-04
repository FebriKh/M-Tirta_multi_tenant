# backend/auth.py
from sqlalchemy.orm import Session
from shared.backend.crud.crud_pengurus import get_pengurus_by_user_web
from dotenv import load_dotenv
import os

load_dotenv()

DEV_USER_WEB     = os.getenv("DEV_USER_WEB")
DEV_PASSWORD_WEB = os.getenv("DEV_PASSWORD_WEB")
DEV_NAMA         = os.getenv("DEV_NAMA", "Developer")

def login(db: Session, user_web: str, password_web: str) -> dict | None:
    """
    return dict user jika login berhasil, None jika gagal.
    cek developer dulu dari .env, baru cek database.
    """
    # cek developer
    if user_web == DEV_USER_WEB and password_web == DEV_PASSWORD_WEB:
        return {
            "id"      : 0,
            "nama"    : DEV_NAMA,
            "jabatan" : "developer",
            "user_web": DEV_USER_WEB
        }

    # cek database
    p = get_pengurus_by_user_web(db, user_web)
    if p and p.password_web == password_web:
        return {
            "id"      : p.id,
            "nama"    : p.nama,
            "jabatan" : p.jabatan,
            "user_web": p.user_web
        }

    return None

def cek_akses(role_dibutuhkan: list, role_user: str) -> bool:
    """cek apakah role user punya akses"""
    if role_user == "developer":
        return True
    return role_user in role_dibutuhkan
