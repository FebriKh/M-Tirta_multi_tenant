# backend/models/pemasangan.py
from sqlalchemy import Column, Integer, ForeignKey, Date, String
from sqlalchemy.orm import relationship
from shared.backend.database import Base

BIAYA_PEMASANGAN = 1_200_000

class Pemasangan(Base):
    __tablename__ = "pemasangan"

    id              = Column(Integer, primary_key=True, index=True)
    pelanggan_id    = Column(Integer, ForeignKey("pelanggan.id"), nullable=False)
    tanggal         = Column(Date,    nullable=False)
    operasional     = Column(Integer, default=0)   # total biaya operasional
    masuk_kas       = Column(Integer, default=0)   # 1.200.000 - operasional
    keterangan      = Column(String,  nullable=True)  # teks bebas

    pelanggan       = relationship("Pelanggan", backref="pemasangan")
