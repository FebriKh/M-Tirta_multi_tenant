# M-Tirta/api/routers/laporan.py
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, FileResponse
from shared.backend.template import render_template
from sqlalchemy.orm import Session
from shared.backend.database import get_db
from shared.backend.crud import *
from api.dependencies import get_current_user
from datetime import datetime

router    = APIRouter(tags=["laporan"])

def get_periode_list(bulan_awal, tahun_awal, bulan_akhir, tahun_akhir):
    periode = []
    b, t    = bulan_awal, tahun_awal
    while (t * 12 + b) <= (tahun_akhir * 12 + bulan_akhir):
        periode.append((b, t))
        b += 1
        if b > 12:
            b = 1
            t += 1
    return periode

@router.get("/laporan", response_class=HTMLResponse)
async def laporan_page(
    request     : Request,
    bulan_awal  : int = None,
    tahun_awal  : int = None,
    bulan_akhir : int = None,
    tahun_akhir : int = None,
    db          : Session = Depends(get_db),
    user        : dict    = Depends(get_current_user)
):
    now         = datetime.now()
    bulan_awal  = bulan_awal  or 1
    tahun_awal  = tahun_awal  or now.year
    bulan_akhir = bulan_akhir or now.month
    tahun_akhir = tahun_akhir or now.year

    periode_list  = get_periode_list(bulan_awal, tahun_awal,
                                      bulan_akhir, tahun_akhir)
    rows_ring     = []
    grand_target  = grand_terkumpul = grand_masuk = grand_keluar = 0

    for b, t in periode_list:
        kas    = sinkron_kas(db, b, t)
        keluar = get_total_pengeluaran_bulan(db, b, t)
        rows_ring.append({
            "bulan"      : b,
            "tahun"      : t,
            "target"     : kas.target_penarikan,
            "terkumpul"  : kas.aktual_terkumpul,
            "pemasangan" : kas.pemasukan_pemasangan,
            "pengeluaran": keluar,
            "saldo"      : kas.total_saldo
        })
        grand_target    += kas.target_penarikan
        grand_terkumpul += kas.aktual_terkumpul
        grand_masuk     += kas.pemasukan_pemasangan
        grand_keluar    += keluar

    kas_akhir = sinkron_kas(db, bulan_akhir, tahun_akhir)

    return render_template(
        request = request,
        name    = "laporan.html",
        context = {
            "user"           : user,
            "bulan_awal"     : bulan_awal,
            "tahun_awal"     : tahun_awal,
            "bulan_akhir"    : bulan_akhir,
            "tahun_akhir"    : tahun_akhir,
            "rows_ring"      : rows_ring,
            "grand_target"   : grand_target,
            "grand_terkumpul": grand_terkumpul,
            "grand_masuk"    : grand_masuk,
            "grand_keluar"   : grand_keluar,
            "saldo_akhir"    : kas_akhir.total_saldo,
            "bulan_list"     : list(range(1, 13)),
        }
    )

@router.get("/laporan/export/excel")
async def export_excel(
    bulan_awal  : int,
    tahun_awal  : int,
    bulan_akhir : int,
    tahun_akhir : int,
    db          : Session = Depends(get_db),
    user        : dict    = Depends(get_current_user)
):
    from shared.exports.excel_export import export_laporan_range
    path = export_laporan_range(
        db, bulan_awal, tahun_awal,
        bulan_akhir, tahun_akhir
    )
    return FileResponse(
        path,
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename   = os.path.basename(path)
    )

@router.get("/laporan/export/pdf")
async def export_pdf(
    bulan_awal  : int,
    tahun_awal  : int,
    bulan_akhir : int,
    tahun_akhir : int,
    db          : Session = Depends(get_db),
    user        : dict    = Depends(get_current_user)
):
    from shared.exports.pdf_export import export_laporan_range_pdf
    path = export_laporan_range_pdf(
        db, bulan_awal, tahun_awal,
        bulan_akhir, tahun_akhir
    )
    return FileResponse(
        path,
        media_type = "application/pdf",
        filename   = os.path.basename(path)
    )
