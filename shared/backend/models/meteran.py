# backend/models/meteran.py
from sqlalchemy import Column, Integer, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from shared.backend.database import Base

BEBAN_DASAR     = 5000
TARIF_PER_KUBIK = 3000

class Meteran(Base):
    __tablename__ = "meteran"

    id            = Column(Integer, primary_key=True, index=True)
    pelanggan_id  = Column(Integer, ForeignKey("pelanggan.id"), nullable=False)
    bulan         = Column(Integer, nullable=False)
    tahun         = Column(Integer, nullable=False)
    angka_awal    = Column(Numeric(10, 2), default=0)
    angka_akhir   = Column(Numeric(10, 2), default=0)
    kubikasi      = Column(Numeric(10, 2), default=0)
    tagihan_air   = Column(Integer, default=0)
    beban_dasar   = Column(Integer, default=BEBAN_DASAR)
    total_tagihan = Column(Integer, default=0)

    pelanggan     = relationship("Pelanggan", backref="meteran")
