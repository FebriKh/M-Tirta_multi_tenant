# M-Tirta/api/routers/auth.py
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fastapi import APIRouter, Depends, Request, Response, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from shared.backend.template import render_template
from sqlalchemy.orm import Session
from shared.backend.database import get_db
from shared.backend.crud.crud_pengurus import get_pengurus_by_user_web
from shared.backend.tenant_assets import current_tenant
from shared.backend.tenant_config import tenant_config
from api.dependencies import create_token, DEV_USER, DEV_PASS, DEV_NAMA

router    = APIRouter(prefix="/api/auth", tags=["auth"])

def authenticate_user(db: Session, username: str, password: str) -> dict | None:
    # cek developer
    if username == DEV_USER and password == DEV_PASS:
        return {
            "id"      : 0,
            "nama"    : DEV_NAMA,
            "jabatan" : "developer",
            "user_web": DEV_USER,
            "tenant_id": current_tenant()
        }
    # cek database
    p = get_pengurus_by_user_web(db, username)
    if p and p.password_web == password:
        return {
            "id"      : p.id,
            "nama"    : p.nama,
            "jabatan" : p.jabatan,
            "user_web": p.user_web,
            "tenant_id": current_tenant()
        }
    return None

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    cfg = tenant_config(current_tenant())
    return render_template(
        request=request,
        name="login.html",
        context={
            "error": request.query_params.get("error"),
            "cfg": cfg,
        }
    )

@router.post("/login")
async def login(
    response : Response,
    username : str = Form(...),
    password : str = Form(...),
    db       : Session = Depends(get_db)
):
    user = authenticate_user(db, username, password)
    if not user:
        return RedirectResponse(
            url="/api/auth/login?error=1",
            status_code=302
        )
    token = create_token(user)
    resp  = RedirectResponse(url="/dashboard", status_code=302)
    resp.set_cookie(
        key      = "access_token",
        value    = token,
        httponly = True,
        max_age  = 60 * 60 * 8  # 8 jam
    )
    return resp

@router.get("/logout")
async def logout():
    resp = RedirectResponse(url="/api/auth/login", status_code=302)
    resp.delete_cookie("access_token")
    return resp
