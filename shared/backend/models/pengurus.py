# backend/models/pengurus.py
from sqlalchemy import Column, Integer, String
from shared.backend.database import Base

class Pengurus(Base):
    __tablename__ = "daftar_pengurus"

    id           = Column(Integer, primary_key=True, index=True)
    nama         = Column(String, nullable=False)
    nomor_hp     = Column(String, nullable=True)
    chat_id      = Column(String, nullable=True, unique=True)
    jabatan      = Column(String, nullable=False)  # ketua/bendahara/teknisi
    user_web     = Column(String, nullable=True, unique=True)
    password_web = Column(String, nullable=True)
