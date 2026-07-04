# M-Tirta/api/routers/developer.py
import json
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fastapi import APIRouter, Depends, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from shared.backend.database import get_db
from shared.backend.crud import *
from api.dependencies import get_current_user, require_role
from datetime import datetime

router    = APIRouter(tags=["developer"])
templates = Jinja2Templates(directory="web/templates")
TENANT_DIR  = "/root/M-Tirta/tenants/tirta-lestari-iv"
CONFIG_FILE = os.path.join(TENANT_DIR, "config.json")
ASSETS_DIR  = os.path.join(TENANT_DIR, "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

def load_tenant_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {}

def save_tenant_config(data: dict):
    cfg = load_tenant_config()
    cfg.update(data)
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)

@router.get("/developer", response_class=HTMLResponse)
async def developer_page(
    request : Request,
    db      : Session = Depends(get_db),
    user    : dict    = Depends(require_role(["developer"]))
):
    now = datetime.now()
    from shared.backend.models.meteran import Meteran
    from shared.backend.models.pembayaran import Pembayaran

    stats = {
        "total_pelanggan": len(get_all_pelanggan(db, aktif_only=False)),
        "total_pengurus" : len(get_all_pengurus(db)),
        "total_meteran"  : db.query(Meteran).count(),
        "total_transaksi": db.query(Pembayaran).count(),
    }
    cfg = load_tenant_config()

    return templates.TemplateResponse(
        request = request,
        name    = "developer.html",
        context = {
            "user" : user,
            "stats": stats,
            "now"  : now,
            "cfg"   : cfg,
        }
    )

@router.post("/developer/simpan-warna")
async def simpan_warna(
    warna_primer  : str = Form(...),
    warna_aksen   : str = Form(...),
    user          : dict = Depends(require_role(["developer"]))
):
    save_tenant_config({
        "warna_primer": warna_primer,
        "warna_aksen" : warna_aksen
    })
    return RedirectResponse(url="/developer?warna=1", status_code=302)

@router.post("/developer/simpan-info")
async def simpan_info(
    nama_app    : str = Form(...),
    nama_org    : str = Form(...),
    alamat_org  : str = Form(""),
    user        : dict = Depends(require_role(["developer"]))
):
    save_tenant_config({
        "nama_app"  : nama_app,
        "nama_org"  : nama_org,
        "alamat_org": alamat_org
    })
    return RedirectResponse(url="/developer?info=1", status_code=302)

@router.post("/developer/upload-logo")
async def upload_logo(
    logo : UploadFile = File(...),
    user : dict       = Depends(require_role(["developer"]))
):
    ext      = logo.filename.split(".")[-1].lower()
    filename = f"logo_org.{ext}"
    filepath = os.path.join(ASSETS_DIR, filename)
    import shutil
    with open(filepath, "wb") as f:
        shutil.copyfileobj(logo.file, f)
    save_tenant_config({"logo_file": filename})
    return RedirectResponse(url="/developer?logo=1", status_code=302)

@router.post("/developer/upload-bg")
async def upload_bg(
    bg   : UploadFile = File(...),
    halaman: str = Form("login"),
    user : dict       = Depends(require_role(["developer"]))
):
    ext      = bg.filename.split(".")[-1].lower()
    filename = f"bg_{halaman}.{ext}"
    filepath = os.path.join(ASSETS_DIR, filename)
    import shutil
    with open(filepath, "wb") as f:
        shutil.copyfileobj(bg.file, f)
    save_tenant_config({f"bg_{halaman}": filename})
    return RedirectResponse(url="/developer?bg=1", status_code=302)

@router.post("/developer/inject-saldo")
async def inject_saldo_post(
    bulan      : int = Form(...),
    tahun      : int = Form(...),
    saldo      : int = Form(...),
    keterangan : str = Form(...),
    db         : Session = Depends(get_db),
    user       : dict    = Depends(require_role(["developer"]))
):
    inject_saldo_awal(db, bulan, tahun, saldo, keterangan)
    return RedirectResponse(url="/developer?inject=1", status_code=302)

@router.post("/developer/sinkron-kas")
async def sinkron_kas_post(
    bulan : int = Form(...),
    tahun : int = Form(...),
    db    : Session = Depends(get_db),
    user  : dict    = Depends(require_role(["developer"]))
):
    sinkron_kas(db, bulan, tahun)
    return RedirectResponse(url="/developer?sinkron=1", status_code=302)
