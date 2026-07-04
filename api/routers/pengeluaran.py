# M-Tirta/api/routers/pengeluaran.py
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

router    = APIRouter(tags=["pengeluaran"])

@router.get("/pengeluaran", response_class=HTMLResponse)
async def pengeluaran_page(
    request : Request,
    bulan   : int = None,
    tahun   : int = None,
    db      : Session = Depends(get_db),
    user    : dict    = Depends(get_current_user)
):
    now   = datetime.now()
    bulan = bulan or now.month
    tahun = tahun or now.year

    data  = get_pengeluaran_bulan(db, bulan, tahun)
    total = get_total_pengeluaran_bulan(db, bulan, tahun)
    pengurus_list = get_all_pengurus(db)

    return render_template(
        request = request,
        name    = "pengeluaran.html",
        context = {
            "user"         : user,
            "bulan"        : bulan,
            "tahun"        : tahun,
            "data"         : data,
            "total"        : total,
            "pengurus_list": pengurus_list,
            "bulan_list"   : list(range(1, 13)),
        }
    )

@router.post("/pengeluaran/catat")
async def catat_pengeluaran_post(
    keperluan      : str = Form(...),
    jumlah         : int = Form(...),
    direquest_oleh : str = Form(""),
    keterangan     : str = Form(""),
    db             : Session = Depends(get_db),
    user           : dict    = Depends(get_current_user)
):
    now = datetime.now()
    catat_pengeluaran(
        db, keperluan, jumlah,
        direquest_oleh or None,
        keterangan or None
    )
    sinkron_kas(db, now.month, now.year)
    return RedirectResponse(url="/pengeluaran?success=1", status_code=302)
