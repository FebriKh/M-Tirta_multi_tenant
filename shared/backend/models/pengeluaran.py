# backend/models/pengeluaran.py
from sqlalchemy import Column, Integer, String, Date
from shared.backend.database import Base

class Pengeluaran(Base):
    __tablename__ = "pengeluaran"

    id              = Column(Integer, primary_key=True, index=True)
    tanggal         = Column(Date,   nullable=False)
    keperluan       = Column(String, nullable=False)  # teks bebas
    jumlah          = Column(Integer, nullable=False)
    direquest_oleh  = Column(String, nullable=True)   # nama pengurus
    keterangan      = Column(String, nullable=True)   # opsional
