# M-Tirta/api/routers/developer.py
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fastapi import APIRouter, Depends, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from shared.backend.template import render_template
from sqlalchemy.orm import Session
from shared.backend.database import get_db
from shared.backend.tenant_config import (tenant_config, save_tenant_config,)
from shared.backend.crud import *
from api.dependencies import get_current_user, require_role
from datetime import datetime

router    = APIRouter(tags=["developer"])

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
    cfg = tenant_config(user["tenant_id"])

    return render_template(
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
    save_tenant_config(
        user["tenant_id"],
        {
            "warna_primer": warna_primer,
            "warna_aksen": warna_aksen
        }
    )
    return RedirectResponse(url="/developer?warna=1", status_code=302)

@router.post("/developer/simpan-info")
async def simpan_info(
    nama_app    : str = Form(...),
    nama_org    : str = Form(...),
    alamat_org  : str = Form(""),
    user        : dict = Depends(require_role(["developer"]))
):
    save_tenant_config(
        user["tenant_id"],
        {
            "nama_app": nama_app,
            "nama_org": nama_org,
            "alamat_org": alamat_org
        }
    )
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
    save_tenant_config(
        user["tenant_id"],
        {
            "logo_file": filename
        }
    )
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
    save_tenant_config(
        user["tenant_id"],
        {
            f"bg_{halaman}": filename
        }
    )
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
