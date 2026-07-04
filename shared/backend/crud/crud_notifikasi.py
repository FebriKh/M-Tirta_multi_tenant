# shared/backend/crud/crud_notifikasi.py
from sqlalchemy.orm import Session
from shared.backend.models.notifikasi import Notifikasi
from datetime import datetime

def tambah_notif(db: Session, pesan: str, tipe: str = "info",
                 pengurus_id: int = None):
    n = Notifikasi(pesan=pesan, tipe=tipe, pengurus_id=pengurus_id)
    db.add(n)
    db.commit()
    return n

def get_notif_terbaru(db: Session, limit: int = 20):
    return (
        db.query(Notifikasi)
        .order_by(Notifikasi.created_at.desc())
        .limit(limit)
        .all()
    )

def get_notif_belum_baca(db: Session) -> int:
    return db.query(Notifikasi).filter(
        Notifikasi.is_read == False
    ).count()

def tandai_semua_baca(db: Session):
    db.query(Notifikasi).update({"is_read": True})
    db.commit()
