# backend/crud/crud_pengurus.py
from sqlalchemy.orm import Session
from shared.backend.models.pengurus import Pengurus

def get_all_pengurus(db: Session):
    return db.query(Pengurus).order_by(Pengurus.jabatan, Pengurus.nama).all()

def get_pengurus_by_id(db: Session, pengurus_id: int):
    return db.query(Pengurus).filter(Pengurus.id == pengurus_id).first()

def get_pengurus_by_chat_id(db: Session, chat_id: str):
    return db.query(Pengurus).filter(Pengurus.chat_id == chat_id).first()

def get_pengurus_by_user_web(db: Session, user_web: str):
    return db.query(Pengurus).filter(Pengurus.user_web == user_web).first()

def cari_pengurus_by_nama(db: Session, nama: str):
    """cari pengurus dengan nama yang mirip"""
    return db.query(Pengurus).filter(
        Pengurus.nama.ilike(f"%{nama}%")
    ).all()

def tambah_pengurus(db: Session, nama: str, jabatan: str,
                    nomor_hp: str = None, chat_id: str = None,
                    user_web: str = None, password_web: str = None):
    pengurus = Pengurus(
        nama         = nama,
        jabatan      = jabatan,
        nomor_hp     = nomor_hp,
        chat_id      = chat_id,
        user_web     = user_web,
        password_web = password_web
    )
    db.add(pengurus)
    db.commit()
    db.refresh(pengurus)
    return pengurus

def update_pengurus(db: Session, pengurus_id: int, **kwargs):
    p = get_pengurus_by_id(db, pengurus_id)
    if not p:
        return None
    for key, value in kwargs.items():
        setattr(p, key, value)
    db.commit()
    db.refresh(p)
    return p

def hapus_pengurus(db: Session, pengurus_id: int):
    p = get_pengurus_by_id(db, pengurus_id)
    if not p:
        return False
    db.delete(p)
    db.commit()
    return True

def ganti_kredensial_web(db: Session, pengurus_id: int,
                          user_web: str, password_web: str):
    return update_pengurus(db, pengurus_id,
                           user_web=user_web,
                           password_web=password_web)

def verifikasi_login_web(db: Session, user_web: str, password_web: str):
    """return pengurus jika kredensial cocok, None jika tidak"""
    p = get_pengurus_by_user_web(db, user_web)
    if p and p.password_web == password_web:
        return p
    return None
