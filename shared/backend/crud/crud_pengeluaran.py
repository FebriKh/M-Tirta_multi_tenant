# backend/crud/crud_pengeluaran.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from shared.backend.models.pengeluaran import Pengeluaran
from datetime import date

def catat_pengeluaran(db: Session, keperluan: str, jumlah: int,
                      direquest_oleh: str = None, keterangan: str = None):
    p = Pengeluaran(
        tanggal        = date.today(),
        keperluan      = keperluan,
        jumlah         = jumlah,
        direquest_oleh = direquest_oleh,
        keterangan     = keterangan
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p

def get_pengeluaran_bulan(db: Session, bulan: int, tahun: int):
    return (
        db.query(Pengeluaran)
        .filter(
            func.extract("month", Pengeluaran.tanggal) == bulan,
            func.extract("year",  Pengeluaran.tanggal) == tahun
        )
        .order_by(Pengeluaran.tanggal)
        .all()
    )

def get_total_pengeluaran_bulan(db: Session, bulan: int, tahun: int) -> int:
    result = db.query(func.sum(Pengeluaran.jumlah)).filter(
        func.extract("month", Pengeluaran.tanggal) == bulan,
        func.extract("year",  Pengeluaran.tanggal) == tahun
    ).scalar()
    return result or 0
