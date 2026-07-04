# shared/backend/models/notifikasi.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from shared.backend.database import Base

class Notifikasi(Base):
    __tablename__ = "notifikasi"

    id          = Column(Integer, primary_key=True, index=True)
    pengurus_id = Column(Integer, nullable=True)  # None = broadcast semua
    pesan       = Column(Text,    nullable=False)
    tipe        = Column(String,  default="info") # info, pembayaran, meteran
    is_read     = Column(Boolean, default=False)
    created_at  = Column(DateTime, server_default=func.now())
