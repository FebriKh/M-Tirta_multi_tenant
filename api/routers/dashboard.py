# M-Tirta/api/routers/dashboard.py
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from shared.backend.database import get_db
from shared.backend.crud import *
from shared.backend.crud.crud_notifikasi import (get_notif_terbaru,
    get_notif_belum_baca, tandai_semua_baca)
from api.dependencies import get_current_user
from shared.backend.crud.crud_kas import get_total_saldo_global
from datetime import datetime

router    = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="web/templates")

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request : Request,
    bulan   : int = None,      # tambah ini
    tahun   : int = None,      # tambah ini
    db      : Session = Depends(get_db),
    user    : dict    = Depends(get_current_user)
):
    now   = datetime.now()
    bulan = bulan or now.month
    tahun = tahun or now.year

    kas             = sinkron_kas(db, bulan, tahun)
    total_saldo_global = get_total_saldo_global(db)
    total_keluar    = get_total_pengeluaran_bulan(db, bulan, tahun)
    piutang         = get_piutang_bulan(db, bulan, tahun)
    meteran_bln     = get_meteran_bulanan(db, bulan, tahun)
    total_tagihan   = sum(m.total_tagihan for m, p in meteran_bln)
    total_pelanggan = len(get_all_pelanggan(db))
    total_meteran   = len(meteran_bln)

    # pemasukan bersih bulan ini
    pemasukan_bersih = (
        (kas.aktual_terkumpul or 0) +
        (kas.pemasukan_pemasangan or 0) +
        (kas.saldo_bulan_lalu or 0) -   # inject dana masuk ke saldo_bulan_lalu
        total_keluar
    )

    return templates.TemplateResponse(
        request = request,
        name    = "dashboard.html",
        context = {
            "user"            : user,
            "now"             : now,
            "bulan"           : bulan,
            "tahun"           : tahun,
            "total_saldo_global": total_saldo_global,
            "kas"             : kas,
            "total_tagihan"   : total_tagihan,
            "total_keluar"    : total_keluar,
            "piutang"         : piutang,
            "jumlah_piutang"  : len(piutang),
            "total_pelanggan" : total_pelanggan,
            "total_meteran"   : total_meteran,
            "pemasukan_bersih": pemasukan_bersih,
        }
    )

@router.get("/api/notifikasi", response_class=HTMLResponse)
async def notifikasi_panel(
    request : Request,
    db      : Session = Depends(get_db),
    user    : dict    = Depends(get_current_user)
):
    notifs = get_notif_terbaru(db, limit=20)
    tandai_semua_baca(db)

    html = ""
    for n in notifs:
        icon  = "droplets" if n.tipe == "meteran" else "wallet"
        color = "blue" if n.tipe == "meteran" else "green"
        waktu = n.created_at.strftime("%d/%m %H:%M")
        html += f"""
        <div class="list-item">
            <div class="icon-badge bg-{color}-50 shrink-0">
                <i data-lucide="{icon}" class="w-4 h-4 stroke-{color}-500"></i>
            </div>
            <div class="flex-1">
                <p class="text-sm text-gray-800">{n.pesan}</p>
                <p class="text-xs text-gray-400 mt-0.5">{waktu}</p>
            </div>
        </div>
        """
    if not notifs:
        html = '<p class="text-sm text-gray-400 text-center py-4">Belum ada notifikasi</p>'

    return HTMLResponse(html)

@router.get("/api/notifikasi/count")
async def notifikasi_count(
    db   : Session = Depends(get_db),
    user : dict    = Depends(get_current_user)
):
    count = get_notif_belum_baca(db)
    return {"count": count}
