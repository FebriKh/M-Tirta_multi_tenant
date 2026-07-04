# backend/crud/crud_kas.py
from sqlalchemy.orm import Session
from shared.backend.models.kas import Kas
from shared.backend.crud.crud_meteran import get_meteran_bulanan
from shared.backend.crud.crud_pembayaran import get_total_pembayaran_bulan
from shared.backend.crud.crud_pemasangan import get_pemasukan_pemasangan_bulan
from shared.backend.crud.crud_pengeluaran import get_total_pengeluaran_bulan

def get_kas_bulan(db: Session, bulan: int, tahun: int):
    return db.query(Kas).filter(
        Kas.bulan == bulan,
        Kas.tahun == tahun
    ).first()

def sinkron_kas(db: Session, bulan: int, tahun: int):
    kas = get_kas_bulan(db, bulan, tahun)
    if not kas:
        kas = Kas(bulan=bulan, tahun=tahun)
        db.add(kas)
        db.flush()  # ← tambah ini supaya kas.id tersedia

    # target dari meteran
    meteran_bulan        = get_meteran_bulanan(db, bulan, tahun)
    kas.target_penarikan = sum(m.total_tagihan for m, p in meteran_bulan)

    # aktual dari pembayaran
    kas.aktual_terkumpul = get_total_pembayaran_bulan(db, bulan, tahun)

    # dari pemasangan
    kas.pemasukan_pemasangan = get_pemasukan_pemasangan_bulan(db, bulan, tahun)

    # pengeluaran bulan ini
    total_keluar = get_total_pengeluaran_bulan(db, bulan, tahun)

    # pastikan saldo_bulan_lalu tidak None
    saldo_lalu = kas.saldo_bulan_lalu or 0  # ← fix utama disini

    # total saldo dinamis
    kas.total_saldo = (
        saldo_lalu +
        kas.aktual_terkumpul +
        kas.pemasukan_pemasangan -
        total_keluar
    )

    db.commit()
    db.refresh(kas)
    return kas

def capture_saldo_akhir_bulan(db: Session, bulan: int, tahun: int):
    """
    dipanggil otomatis tiap akhir bulan jam 22:00
    menyimpan total_saldo bulan ini sebagai saldo_bulan_lalu di bulan depan
    """
    kas_ini = get_kas_bulan(db, bulan, tahun)
    if not kas_ini:
        return

    # tentukan bulan depan
    bulan_depan = bulan + 1
    tahun_depan = tahun
    if bulan_depan > 12:
        bulan_depan = 1
        tahun_depan = tahun + 1

    kas_depan = get_kas_bulan(db, bulan_depan, tahun_depan)
    if not kas_depan:
        kas_depan = Kas(bulan=bulan_depan, tahun=tahun_depan)
        db.add(kas_depan)

    kas_depan.saldo_bulan_lalu = kas_ini.total_saldo
    db.commit()

def inject_saldo_awal(db: Session, bulan: int, tahun: int,
                      saldo: int, keterangan: str = None):
    kas = get_kas_bulan(db, bulan, tahun)
    if not kas:
        kas = Kas(bulan=bulan, tahun=tahun)
        db.add(kas)
        db.flush()

    kas.saldo_bulan_lalu = saldo
    kas.keterangan       = keterangan  # ← tambah ini
    db.commit()
    return sinkron_kas(db, bulan, tahun)

def get_total_saldo_global(db: Session) -> int:
    """
    Mengambil saldo kas terakhir yang memiliki nilai.
    Tidak terpengaruh periode dashboard.
    """
    kas = (
        db.query(Kas)
        .filter(Kas.total_saldo > 0)
        .order_by(Kas.tahun.desc(), Kas.bulan.desc())
        .first()
    )

    return kas.total_saldo if kas else 0

