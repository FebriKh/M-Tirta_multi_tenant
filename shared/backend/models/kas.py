# backend/models/kas.py
from sqlalchemy import Column, Integer, String
from shared.backend.database import Base

class Kas(Base):
    __tablename__ = "kas"

    id                    = Column(Integer, primary_key=True, index=True)
    bulan                 = Column(Integer, nullable=False)
    tahun                 = Column(Integer, nullable=False)

    # dari tabel meteran — total tagihan yang seharusnya terkumpul
    target_penarikan      = Column(Integer, default=0)

    # dari tabel pembayaran — aktual yang masuk bulan ini
    aktual_terkumpul      = Column(Integer, default=0)

    # dari tabel pemasangan — uang masuk dari pelanggan baru
    pemasukan_pemasangan  = Column(Integer, default=0)

    # di-capture otomatis tiap akhir bulan jam 22:00
    saldo_bulan_lalu      = Column(Integer, default=0)

    # tambah kolom di class Kas
    keterangan            = Column(String, nullable=True)

    # dinamis: saldo_bulan_lalu + aktual_terkumpul + 
    #          pemasukan_pemasangan - pengeluaran
    total_saldo           = Column(Integer, default=0)
