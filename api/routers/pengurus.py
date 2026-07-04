# M-Tirta/api/routers/pengurus.py
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import shutil

from fastapi import APIRouter, Depends, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy.orm import Session
from shared.backend.template import render_template
from shared.backend.database import get_db
from shared.backend.tenant_config import (tenant_config, save_tenant_config)
from shared.backend.crud import *
from shared.assets.image_processor import (save_profile_image, save_logo_image, slugify,)
from shared.backend.tenant_assets import (profil_dir, asset_dir, logo_file, current_tenant, tenant_config,)
from api.dependencies import get_current_user

router    = APIRouter(tags=["pengurus"])
templates = Jinja2Templates(directory="web/templates")

@router.get("/pengurus", response_class=HTMLResponse)
async def pengurus_page(
    request : Request,
    db      : Session = Depends(get_db),
    user    : dict    = Depends(get_current_user)
):
    semua = get_all_pengurus(db)

    return render_template(
        request = request,
        name    = "pengurus.html",
        context = {"user": user, "semua": semua}
    )

@router.post("/pengurus/upload-foto")
async def upload_foto(
    foto: UploadFile = File(...),
    request: Request = None,
    user: dict = Depends(get_current_user)
):
    # ambil tenant dari token
    tenant = user.get("tenant_id")

    if not tenant:
        return RedirectResponse("/pengurus?error=tenant", status_code=302)

    # folder profil tenant
    folder = profil_dir(tenant)

    # nama file berdasarkan nama pengurus
    filename = slugify(user["nama"]) + ".webp"

    # simpan sementara
    tmp = Path(folder) / ("tmp_" + foto.filename)

    with open(tmp, "wb") as buffer:
        shutil.copyfileobj(foto.file, buffer)

    # resize + convert + compress
    try:
        save_profile_image(
            tmp,
            Path(folder) / filename
        )
        print("SAVE BERHASIL")
    except Exception as e:
        print("ERROR SAVE =", e)

    # hapus file sementara
    if tmp.exists():
        tmp.unlink()

    return RedirectResponse(
        "/pengurus?foto=1",
        status_code=302
    )

@router.post("/pengurus/upload-logo")
async def upload_logo(
    logo: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    tenant = user["tenant_id"]

    folder = asset_dir(tenant)

    tmp = folder / ("tmp_" + logo.filename)

    with open(tmp, "wb") as buffer:
        shutil.copyfileobj(logo.file, buffer)

    save_logo_image(
        tmp,
        logo_file(tenant)
    )

    if tmp.exists():
        tmp.unlink()

    return RedirectResponse(
        "/pengurus?logo=1",
        status_code=302
    )

@router.post("/pengurus/profil-organisasi")
async def simpan_profil_organisasi(
    nama_org   : str = Form(...),
    alamat_org : str = Form(""),
    telepon    : str = Form(""),
    whatsapp   : str = Form(""),
    email      : str = Form(""),
    website    : str = Form(""),
    user        : dict = Depends(get_current_user)
):
    save_tenant_config(
        user["tenant_id"],
        {
            "nama_org": nama_org,
            "alamat_org": alamat_org,
            "telepon": telepon,
            "whatsapp": whatsapp,
            "email": email,
            "website": website,
        }
    )

    return RedirectResponse(
        "/pengurus?profil=1",
        status_code=302
    )

@router.get("/profil/{nama}")
async def get_profile_photo(
    nama: str,
    user: dict = Depends(get_current_user)
):
    tenant = user["tenant_id"]

    file = profil_dir(tenant) / f"{slugify(nama)}.webp"

    if file.exists():
        return FileResponse(file)

    return FileResponse("web/static/img/default-avatar.webp")

@router.get("/logo")
async def get_logo():

    tenant = current_tenant()

    file = logo_file(tenant)

    if file.exists():
        return FileResponse(file)

    return FileResponse("web/static/img/default-logo.webp")

@router.post("/pengurus/tambah")
async def tambah_pengurus_post(
    nama        : str = Form(...),
    nomor_hp    : str = Form(""),
    chat_id     : str = Form(""),
    jabatan     : str = Form(...),
    user_web    : str = Form(""),
    password_web: str = Form(""),
    db          : Session = Depends(get_db),
    user        : dict    = Depends(get_current_user)
):
    tambah_pengurus(
        db, nama=nama, jabatan=jabatan,
        nomor_hp=nomor_hp or None,
        chat_id=chat_id or None,
        user_web=user_web or None,
        password_web=password_web or None
    )
    return RedirectResponse(url="/pengurus?success=1", status_code=302)

@router.post("/pengurus/edit/{pengurus_id}")
async def edit_pengurus_post(
    pengurus_id : int,
    nama        : str = Form(...),
    nomor_hp    : str = Form(""),
    chat_id     : str = Form(""),
    jabatan     : str = Form(...),
    user_web    : str = Form(""),
    password_web: str = Form(""),
    db          : Session = Depends(get_db),
    user        : dict    = Depends(get_current_user)
):
    kwargs = dict(
        nama=nama, jabatan=jabatan,
        nomor_hp=nomor_hp or None,
        chat_id=chat_id or None,
        user_web=user_web or None
    )
    if password_web:
        kwargs["password_web"] = password_web
    update_pengurus(db, pengurus_id, **kwargs)
    return RedirectResponse(url="/pengurus?updated=1", status_code=302)

@router.post("/pengurus/hapus/{pengurus_id}")
async def hapus_pengurus_post(
    pengurus_id : int,
    db          : Session = Depends(get_db),
    user        : dict    = Depends(get_current_user)
):
    hapus_pengurus(db, pengurus_id)
    return RedirectResponse(url="/pengurus?deleted=1", status_code=302)

@router.post("/pengurus/ganti-password")
async def ganti_password_post(
    user_web_baru    : str = Form(...),
    password_web_baru: str = Form(...),
    db               : Session = Depends(get_db),
    user             : dict    = Depends(get_current_user)
):
    if user.get("jabatan") != "developer":
        ganti_kredensial_web(
            db, user["id"],
            user_web_baru, password_web_baru
        )
    return RedirectResponse(url="/pengurus?password=1", status_code=302)
