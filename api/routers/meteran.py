# M-Tirta/api/routers/meteran.py
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from shared.backend.template import render_template
from sqlalchemy.orm import Session
from shared.backend.database import get_db
from shared.backend.crud import *
from api.dependencies import get_current_user
from datetime import datetime

router    = APIRouter(tags=["meteran"])

@router.get("/meteran", response_class=HTMLResponse)
async def meteran_page(
    request : Request,
    bulan   : int = None,
    tahun   : int = None,
    db      : Session = Depends(get_db),
    user    : dict    = Depends(get_current_user)
):
    now   = datetime.now()
    bulan = bulan or now.month
    tahun = tahun or now.year

    pelanggan_list = get_all_pelanggan(db)
    data_meteran   = get_meteran_bulanan(db, bulan, tahun)

    rows = []
    for m, p in data_meteran:
        terbayar = get_total_terbayar(db, m.id)
        sisa     = m.total_tagihan - terbayar
        rows.append({
            "id"           : m.id,
            "nama"         : p.nama,
            "area"         : p.area or "-",
            "angka_awal"   : float(m.angka_awal),
            "angka_akhir"  : float(m.angka_akhir),
            "kubikasi"     : float(m.kubikasi),
            "total_tagihan": m.total_tagihan,
            "terbayar"     : terbayar,
            "sisa"         : sisa,
            "status"       : "Lunas" if sisa == 0 else "Belum Lunas"
        })

    return render_template(
        request = request,
        name    = "meteran.html",
        context = {
            "user"          : user,
            "bulan"         : bulan,
            "tahun"         : tahun,
            "pelanggan_list": pelanggan_list,
            "data_meteran"  : rows,
            "bulan_list"    : list(range(1, 13)),
        }
    )

@router.post("/meteran/input")
async def input_meteran_post(
    request     : Request,
    pelanggan_id: int   = Form(...),
    bulan       : int   = Form(...),
    tahun       : int   = Form(...),
    angka_akhir : float = Form(...),
    angka_awal  : float = Form(None),
    db          : Session = Depends(get_db),
    user        : dict    = Depends(get_current_user)
):
    m, msg = input_meteran(
        db, pelanggan_id, bulan, tahun,
        angka_akhir, angka_awal
    )
    if m:
        sinkron_kas(db, bulan, tahun)
        return RedirectResponse(
            url=f"/meteran?bulan={bulan}&tahun={tahun}&success=1",
            status_code=302
        )
    return RedirectResponse(
        url=f"/meteran?bulan={bulan}&tahun={tahun}&error={msg}",
        status_code=302
    )

@router.get("/meteran/angka-awal/{pelanggan_id}")
async def get_angka_awal(
    pelanggan_id: int,
    bulan       : int,
    tahun       : int,
    db          : Session = Depends(get_db),
    user        : dict    = Depends(get_current_user)
):
    """endpoint untuk HTMX — cek angka awal otomatis"""
    angka_awal = get_angka_awal_otomatis(db, pelanggan_id, bulan, tahun)
    if angka_awal is not None:
        return HTMLResponse(
            f'<input type="number" name="angka_awal" value="{angka_awal}" '
            f'step="0.01" class="w-full border rounded-lg px-3 py-2 bg-gray-100" '
            f'readonly title="Otomatis dari bulan lalu">'
        )
    return HTMLResponse(
        f'<input type="number" name="angka_awal" step="0.01" '
        f'class="w-full border rounded-lg px-3 py-2" '
        f'placeholder="Masukkan angka awal" required>'
    )
