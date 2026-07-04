# backend/models/pembayaran.py
from sqlalchemy import Column, Integer, ForeignKey, Date, String
from sqlalchemy.orm import relationship
from shared.backend.database import Base

class Pembayaran(Base):
    __tablename__ = "pembayaran"

    id           = Column(Integer, primary_key=True, index=True)
    meteran_id   = Column(Integer, ForeignKey("meteran.id"), nullable=False)
    tgl_bayar    = Column(Date,    nullable=False)
    jumlah_bayar = Column(Integer, nullable=False)
    diskon       = Column(Integer, default=0)
    metode       = Column(String,  nullable=False)   # cash / transfer
    status       = Column(String,  nullable=False)   # lunas / cicil
    catatan      = Column(String,  nullable=True)

    meteran      = relationship("Meteran", backref="pembayaran")
