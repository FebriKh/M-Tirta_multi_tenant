# M-Tirta/api/routers/pelanggan.py
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from shared.backend.template import render_template
from sqlalchemy.orm import Session
from shared.backend.database import get_db
from shared.backend.crud import *
from shared.backend.models.pemasangan import BIAYA_PEMASANGAN
from api.dependencies import get_current_user
from datetime import date, datetime

router    = APIRouter(tags=["pelanggan"])

PER_PAGE_PELANGGAN  = 15
PER_PAGE_PEMASANGAN = 10

@router.get("/pelanggan", response_class=HTMLResponse)
async def pelanggan_page(
    request  : Request,
    cari     : str = "",
    area     : str = "",
    page_p   : int = 1,   # page pelanggan
    page_psng: int = 1,   # page pemasangan
    db       : Session = Depends(get_db),
    user     : dict    = Depends(get_current_user)
):
    # --- pelanggan ---
    semua = get_all_pelanggan(db, aktif_only=True)
    if cari:
        semua = [p for p in semua if cari.lower() in p.nama.lower()]
    if area:
        semua = [p for p in semua if p.area and area.lower() in p.area.lower()]

    total_p      = len(semua)
    total_page_p = max(1, (total_p + PER_PAGE_PELANGGAN - 1) // PER_PAGE_PELANGGAN)
    page_p       = max(1, min(page_p, total_page_p))
    start_p      = (page_p - 1) * PER_PAGE_PELANGGAN
    semua_page   = semua[start_p:start_p + PER_PAGE_PELANGGAN]

    # --- pemasangan ---
    all_psng      = get_all_pemasangan(db)
    total_psng    = len(all_psng)
    total_page_psng = max(1, (total_psng + PER_PAGE_PEMASANGAN - 1) // PER_PAGE_PEMASANGAN)
    page_psng     = max(1, min(page_psng, total_page_psng))
    start_psng    = (page_psng - 1) * PER_PAGE_PEMASANGAN
    psng_page     = all_psng[start_psng:start_psng + PER_PAGE_PEMASANGAN]

    now = datetime.now()

    return render_template(
        request = request,
        name    = "pelanggan.html",
        context = {
            "user"           : user,
            "semua"          : semua_page,
            "total_p"        : total_p,
            "page_p"         : page_p,
            "total_page_p"   : total_page_p,
            "cari"           : cari,
            "area"           : area,
            "psng_list"      : psng_page,
            "total_psng"     : total_psng,
            "page_psng"      : page_psng,
            "total_page_psng": total_page_psng,
            "biaya_pemasangan": BIAYA_PEMASANGAN,
            "bulan_list"     : list(range(1, 13)),
            "now_bulan"      : now.month,
            "now_tahun"      : now.year,
        }
    )

@router.post("/pelanggan/tambah")
async def tambah_pelanggan_post(
    nama             : str   = Form(...),
    nomor_hp         : str   = Form(""),
    alamat           : str   = Form(""),
    area             : str   = Form(""),
    desa             : str   = Form(""),
    angka_meteran_awal: float = Form(0),
    bulan_daftar     : int   = Form(...),
    tahun_daftar     : int   = Form(...),
    db               : Session = Depends(get_db),
    user             : dict    = Depends(get_current_user)
):
    tgl_daftar = date(tahun_daftar, bulan_daftar, 1)
    tambah_pelanggan(
        db, nama=nama, alamat=alamat,
        area=area, desa=desa,
        nomor_hp=nomor_hp or None,
        angka_meteran_awal=angka_meteran_awal,
        tgl_daftar=tgl_daftar
    )
    return RedirectResponse(url="/pelanggan?success=1", status_code=302)

@router.post("/pelanggan/edit/{pelanggan_id}")
async def edit_pelanggan_post(
    pelanggan_id : int,
    nama         : str = Form(...),
    nomor_hp     : str = Form(""),
    alamat       : str = Form(""),
    area         : str = Form(""),
    desa         : str = Form(""),
    db           : Session = Depends(get_db),
    user         : dict    = Depends(get_current_user)
):
    update_pelanggan(
        db, pelanggan_id,
        nama=nama, nomor_hp=nomor_hp or None,
        alamat=alamat, area=area, desa=desa
    )
    return RedirectResponse(url="/pelanggan?updated=1", status_code=302)

@router.post("/pelanggan/nonaktif/{pelanggan_id}")
async def nonaktif_pelanggan_post(
    pelanggan_id : int,
    db           : Session = Depends(get_db),
    user         : dict    = Depends(get_current_user)
):
    nonaktifkan_pelanggan(db, pelanggan_id)
    return RedirectResponse(url="/pelanggan?nonaktif=1", status_code=302)

@router.post("/pemasangan/tambah")
async def tambah_pemasangan_post(
    nama_pelanggan   : str   = Form(...),
    nomor_hp         : str   = Form(""),
    alamat           : str   = Form(""),
    area             : str   = Form(""),
    desa             : str   = Form(""),
    operasional      : int   = Form(0),
    angka_meteran_awal: float = Form(0),
    keterangan       : str   = Form(""),
    db               : Session = Depends(get_db),
    user             : dict    = Depends(get_current_user)
):
    now = datetime.now()
    hasil, msg = catat_pemasangan(
        db,
        nama_pelanggan     = nama_pelanggan,
        alamat             = alamat,
        area               = area,
        desa               = desa,
        nomor_hp           = nomor_hp or None,
        operasional        = operasional,
        keterangan         = keterangan or None,
        angka_meteran_awal = angka_meteran_awal
    )
    if hasil:
        sinkron_kas(db, now.month, now.year)
        return RedirectResponse(url="/pelanggan?pasang=1", status_code=302)
    return RedirectResponse(url=f"/pelanggan?error={msg}", status_code=302)
