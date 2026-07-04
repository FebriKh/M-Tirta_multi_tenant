# backend/models/pelanggan.py
from sqlalchemy import Column, Integer, String, Boolean, Date, Numeric
from shared.backend.database import Base

class Pelanggan(Base):
    __tablename__ = "pelanggan"

    id                  = Column(Integer, primary_key=True, index=True)
    nama                = Column(String,  nullable=False)
    nomor_hp            = Column(String,  nullable=True)
    alamat              = Column(String,  nullable=True)
    area                = Column(String,  nullable=True)
    desa                = Column(String,  nullable=True)
    tgl_daftar          = Column(Date,    nullable=True)
    status_aktif        = Column(Boolean, default=True)
    angka_meteran_awal  = Column(Numeric(10, 2), default=0)  # ← tambah ini
