# backend/crud/crud_pelanggan.py
from sqlalchemy.orm import Session
from shared.backend.models.pelanggan import Pelanggan
from datetime import date

def get_all_pelanggan(db: Session, aktif_only: bool = True):
    q = db.query(Pelanggan)
    if aktif_only:
        q = q.filter(Pelanggan.status_aktif == True)
    return q.order_by(Pelanggan.area, Pelanggan.nama).all()

def get_pelanggan_by_id(db: Session, pelanggan_id: int):
    return db.query(Pelanggan).filter(Pelanggan.id == pelanggan_id).first()

def cari_pelanggan_by_nama(db: Session, nama: str):
    """cari pelanggan dengan nama yang mirip"""
    return db.query(Pelanggan).filter(
        Pelanggan.nama.ilike(f"%{nama}%"),
        Pelanggan.status_aktif == True
    ).all()

def tambah_pelanggan(db: Session, nama: str, alamat: str = None,
                     area: str = None, desa: str = None,
                     nomor_hp: str = None,
                     angka_meteran_awal: float = 0,
                     tgl_daftar=None):
    from datetime import date
    p = Pelanggan(
        nama               = nama,
        nomor_hp           = nomor_hp,
        alamat             = alamat,
        area               = area,
        desa               = desa,
        tgl_daftar         = tgl_daftar or date.today(),
        status_aktif       = True,
        angka_meteran_awal = angka_meteran_awal
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p

def update_pelanggan(db: Session, pelanggan_id: int, **kwargs):
    p = get_pelanggan_by_id(db, pelanggan_id)
    if not p:
        return None
    for key, value in kwargs.items():
        setattr(p, key, value)
    db.commit()
    db.refresh(p)
    return p

def nonaktifkan_pelanggan(db: Session, pelanggan_id: int):
    """soft delete"""
    return update_pelanggan(db, pelanggan_id, status_aktif=False)

def aktifkan_pelanggan(db: Session, pelanggan_id: int):
    return update_pelanggan(db, pelanggan_id, status_aktif=True)
