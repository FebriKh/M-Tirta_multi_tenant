# backend/crud/crud_pembayaran.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from shared.backend.models.pembayaran import Pembayaran
from shared.backend.models.meteran import Meteran
from datetime import date

def get_total_terbayar(db: Session, meteran_id: int) -> int:
    result = db.query(func.sum(Pembayaran.jumlah_bayar)).filter(
        Pembayaran.meteran_id == meteran_id
    ).scalar()
    return result or 0

def get_sisa_tagihan(db: Session, meteran_id: int) -> int:
    m = db.query(Meteran).filter(Meteran.id == meteran_id).first()
    if not m:
        return 0
    return m.total_tagihan - get_total_terbayar(db, meteran_id)

def catat_pembayaran(db: Session, meteran_id: int, jumlah_bayar: int,
                     metode: str, catatan: str = None, diskon: int = 0):

    m = db.query(Meteran).filter(Meteran.id == meteran_id).first()
    if not m:
        return None, "Data meteran tidak ditemukan"

    sisa = get_sisa_tagihan(db, meteran_id)

    # validasi diskon
    if diskon < 0:
        return None, "Diskon tidak boleh negatif"
    if diskon > m.total_tagihan:
        return None, f"Diskon melebihi total tagihan (Rp {m.total_tagihan:,})"

    # tagihan setelah diskon
    tagihan_setelah_diskon = sisa - diskon
    if tagihan_setelah_diskon < 0:
        tagihan_setelah_diskon = 0

    if jumlah_bayar <= 0:
        return None, "Jumlah bayar harus lebih dari 0"
    if jumlah_bayar > tagihan_setelah_diskon:
        return None, f"Melebihi tagihan setelah diskon (Rp {tagihan_setelah_diskon:,})"

    # kalau diskon diterapkan, update total_tagihan di meteran
    if diskon > 0:
        m.total_tagihan = m.total_tagihan - diskon
        db.flush()

    sisa_baru  = get_sisa_tagihan(db, meteran_id)
    status     = "lunas" if jumlah_bayar >= sisa_baru else "cicil"

    b = Pembayaran(
        meteran_id   = meteran_id,
        tgl_bayar    = date.today(),
        jumlah_bayar = jumlah_bayar,
        diskon       = diskon,
        metode       = metode,
        status       = status,
        catatan      = catatan
    )
    db.add(b)
    db.commit()
    db.refresh(b)
    return b, "OK"

    if b:  # setelah berhasil simpan
        # auto notif
        try:
            from shared.backend.crud.crud_notifikasi import tambah_notif
            nama = b.meteran.pelanggan.nama
            bln  = b.meteran.bulan
            thn  = b.meteran.tahun
            status_text = "Lunas" if b.status == "lunas" else "Cicil"
            tambah_notif(
                db,
                pesan = (f"Pelanggan {nama} telah melakukan pembayaran "
                         f"bulan {bln}/{thn} via {metode.upper()}. "
                         f"Status: {status_text}"),
                tipe  = "pembayaran"
            )
        except Exception:
            pass

def get_riwayat_cicilan(db: Session, meteran_id: int):
    """ambil semua cicilan untuk 1 meteran"""
    return (
        db.query(Pembayaran)
        .filter(Pembayaran.meteran_id == meteran_id)
        .order_by(Pembayaran.tgl_bayar)
        .all()
    )

def get_piutang_bulan(db: Session, bulan: int, tahun: int):
    semua_meteran = db.query(Meteran).filter(
        Meteran.bulan == bulan,
        Meteran.tahun == tahun
    ).all()
    return [m for m in semua_meteran if get_sisa_tagihan(db, m.id) > 0]

def get_pembayaran_bulan(db: Session, bulan: int, tahun: int):
    return (
        db.query(Pembayaran, Meteran)
        .join(Meteran, Pembayaran.meteran_id == Meteran.id)
        .filter(Meteran.bulan == bulan, Meteran.tahun == tahun)
        .order_by(Pembayaran.tgl_bayar.desc())
        .all()
    )

def get_total_pembayaran_bulan(db: Session, bulan: int, tahun: int) -> int:
    result = (
        db.query(func.sum(Pembayaran.jumlah_bayar))
        .join(Meteran, Pembayaran.meteran_id == Meteran.id)
        .filter(Meteran.bulan == bulan, Meteran.tahun == tahun)
        .scalar()
    )
    return result or 0

def get_tunggakan_pelanggan(db: Session, pelanggan_id: int):
    semua = db.query(Meteran).filter(
        Meteran.pelanggan_id == pelanggan_id
    ).all()
    tunggakan = []
    for m in semua:
        sisa = get_sisa_tagihan(db, m.id)
        if sisa > 0:
            tunggakan.append({
                "meteran_id": m.id,
                "bulan"     : m.bulan,
                "tahun"     : m.tahun,
                "total"     : m.total_tagihan,
                "terbayar"  : get_total_terbayar(db, m.id),
                "sisa"      : sisa
            })
    return tunggakan
