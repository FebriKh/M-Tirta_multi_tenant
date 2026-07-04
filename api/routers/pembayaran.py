# M-Tirta/api/routers/pembayaran.py

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from shared.backend.database import get_db
from shared.backend.crud import *
from api.dependencies import get_current_user

from datetime import datetime

router = APIRouter(tags=["pembayaran"])
templates = Jinja2Templates(directory="web/templates")

PER_PAGE_TAGIHAN = 10
PER_PAGE_RIWAYAT = 10


@router.get("/pembayaran", response_class=HTMLResponse)
async def pembayaran_page(
    request: Request,
    bulan: int = None,
    tahun: int = None,
    page_tagihan: int = 1,
    page_riwayat: int = 1,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    now = datetime.now()

    bulan = bulan or now.month
    tahun = tahun or now.year

    # ===============================
    # TAGIHAN BELUM LUNAS
    # ===============================

    data_meteran = get_meteran_bulanan(db, bulan, tahun)

    belum_lunas = []

    for m, p in data_meteran:

        sisa = get_sisa_tagihan(db, m.id)

        if sisa > 0:

            tunggakan = get_tunggakan_pelanggan(db, p.id)

            belum_lunas.append({

                "meteran_id": m.id,
                "pelanggan_nama": p.nama,
                "pelanggan_area": p.area or "-",
                "total_tagihan": m.total_tagihan,
                "terbayar": get_total_terbayar(db, m.id),
                "sisa": sisa,
                "jml_tunggakan": len(tunggakan)

            })

    total_tagihan = len(belum_lunas)

    total_page_tagihan = max(
        1,
        (total_tagihan + PER_PAGE_TAGIHAN - 1) // PER_PAGE_TAGIHAN
    )

    page_tagihan = max(
        1,
        min(page_tagihan, total_page_tagihan)
    )

    start = (page_tagihan - 1) * PER_PAGE_TAGIHAN

    belum_lunas = belum_lunas[start:start + PER_PAGE_TAGIHAN]

    # ===============================
    # RIWAYAT TRANSAKSI
    # ===============================

    riwayat = get_pembayaran_bulan(db, bulan, tahun)

    rows_riwayat = []

    for b, m in riwayat:

        rows_riwayat.append({

            "tanggal": b.tgl_bayar.strftime("%d/%m/%Y"),
            "nama": m.pelanggan.nama,
            "area": m.pelanggan.area or "-",
            "jumlah": b.jumlah_bayar,
            "diskon": b.diskon or 0,
            "metode": b.metode,
            "status": b.status,
            "catatan": b.catatan or "-"

        })

    total_riwayat = len(rows_riwayat)

    total_page_riwayat = max(
        1,
        (total_riwayat + PER_PAGE_RIWAYAT - 1) // PER_PAGE_RIWAYAT
    )

    page_riwayat = max(
        1,
        min(page_riwayat, total_page_riwayat)
    )

    start = (page_riwayat - 1) * PER_PAGE_RIWAYAT

    rows_riwayat = rows_riwayat[start:start + PER_PAGE_RIWAYAT]

    return templates.TemplateResponse(
        request=request,
        name="pembayaran.html",
        context={
            "user": user,

            "bulan": bulan,
            "tahun": tahun,

            "bulan_list": list(range(1, 13)),

            "belum_lunas": belum_lunas,
            "total_tagihan": total_tagihan,
            "page_tagihan": page_tagihan,
            "total_page_tagihan": total_page_tagihan,

            "riwayat": rows_riwayat,
            "page_riwayat": page_riwayat,
            "total_page_riwayat": total_page_riwayat,
        }
    )


@router.post("/pembayaran/catat")
async def catat_pembayaran_post(
    request: Request,
    meteran_id: int = Form(...),
    jumlah_bayar: int = Form(...),
    diskon: int = Form(0),
    metode: str = Form(...),
    catatan: str = Form(""),
    bulan: int = Form(...),
    tahun: int = Form(...),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):

    b, msg = catat_pembayaran(
        db,
        meteran_id,
        jumlah_bayar,
        metode,
        catatan or None,
        diskon=diskon
    )

    if b:

        sinkron_kas(db, bulan, tahun)

        try:
            from shared.exports.struk_generator import generate_struk
            generate_struk(db, b.id)
        except Exception:
            pass

        return RedirectResponse(
            url=f"/pembayaran?bulan={bulan}&tahun={tahun}&success=1",
            status_code=302
        )

    return RedirectResponse(
        url=f"/pembayaran?bulan={bulan}&tahun={tahun}&error={msg}",
        status_code=302
    )

