# backend/crud/crud_pemasangan.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from shared.backend.models.pemasangan import Pemasangan, BIAYA_PEMASANGAN
from shared.backend.crud.crud_pelanggan import tambah_pelanggan
from datetime import date

def catat_pemasangan(db: Session, nama_pelanggan: str, alamat: str,
                     area: str, desa: str = None, nomor_hp: str = None,
                     operasional: int = 0, keterangan: str = None,
                     angka_meteran_awal: float = 0):

    masuk_kas = BIAYA_PEMASANGAN - operasional
    if masuk_kas < 0:
        return None, f"Operasional melebihi biaya pemasangan (Rp {BIAYA_PEMASANGAN:,})"

    pelanggan = tambah_pelanggan(
        db                 = db,
        nama               = nama_pelanggan,
        alamat             = alamat,
        area               = area,
        desa               = desa,
        nomor_hp           = nomor_hp,
        angka_meteran_awal = angka_meteran_awal   # ← tambah ini
    )

    p = Pemasangan(
        pelanggan_id = pelanggan.id,
        tanggal      = date.today(),
        operasional  = operasional,
        masuk_kas    = masuk_kas,
        keterangan   = keterangan
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p, "OK"

def get_all_pemasangan(db: Session):
    return (
        db.query(Pemasangan)
        .order_by(Pemasangan.tanggal.desc())
        .all()
    )

def get_pemasukan_pemasangan_bulan(db: Session, bulan: int, tahun: int) -> int:
    result = db.query(func.sum(Pemasangan.masuk_kas)).filter(
        func.extract("month", Pemasangan.tanggal) == bulan,
        func.extract("year",  Pemasangan.tanggal) == tahun
    ).scalar()
    return result or 0
