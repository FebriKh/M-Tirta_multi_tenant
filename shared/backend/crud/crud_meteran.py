# backend/crud/crud_meteran.py
from sqlalchemy.orm import Session
from shared.backend.models.meteran import Meteran, BEBAN_DASAR, TARIF_PER_KUBIK
from shared.backend.models.pelanggan import Pelanggan

def hitung_tagihan(angka_awal: float, angka_akhir: float) -> dict:
    kubikasi    = round(float(angka_akhir) - float(angka_awal), 2)
    tagihan_air = int(kubikasi * TARIF_PER_KUBIK)
    total       = tagihan_air + BEBAN_DASAR
    return {
        "kubikasi"      : kubikasi,
        "tagihan_air"   : tagihan_air,
        "beban_dasar"   : BEBAN_DASAR,
        "total_tagihan" : total
    }

def get_meteran_bulan_lalu(db: Session, pelanggan_id: int,
                            bulan: int, tahun: int):
    """ambil meteran bulan lalu untuk auto-fill angka awal"""
    bulan_lalu = bulan - 1
    tahun_lalu = tahun
    if bulan_lalu == 0:
        bulan_lalu = 12
        tahun_lalu = tahun - 1

    return db.query(Meteran).filter(
        Meteran.pelanggan_id == pelanggan_id,
        Meteran.bulan        == bulan_lalu,
        Meteran.tahun        == tahun_lalu
    ).first()

def get_angka_awal_otomatis(db: Session, pelanggan_id: int,
                             bulan: int, tahun: int):
    """
    Prioritas:
    1. angka_akhir dari meteran bulan lalu (pelanggan lama)
    2. angka_meteran_awal dari tabel pelanggan (penarikan pertama)
    3. None = pelanggan baru, belum ada data sama sekali
    """
    # cek meteran bulan lalu
    m = get_meteran_bulan_lalu(db, pelanggan_id, bulan, tahun)
    if m:
        return float(m.angka_akhir)

    # cek angka meteran awal dari data pelanggan
    from shared.backend.models.pelanggan import Pelanggan
    p = db.query(Pelanggan).filter(Pelanggan.id == pelanggan_id).first()
    if p and p.angka_meteran_awal is not None and float(p.angka_meteran_awal) >= 0:
        return float(p.angka_meteran_awal)

    # betul-betul tidak ada data
    return None

def input_meteran(db: Session, pelanggan_id: int, bulan: int,
                  tahun: int, angka_akhir: float,
                  angka_awal: float = None):
    # cek duplikat
    existing = db.query(Meteran).filter(
        Meteran.pelanggan_id == pelanggan_id,
        Meteran.bulan        == bulan,
        Meteran.tahun        == tahun
    ).first()
    if existing:
        return None, "Data meteran bulan ini sudah ada"

    # ← TAMBAH VALIDASI INI
    # cek apakah bulan/tahun input >= bulan/tahun daftar pelanggan
    from shared.backend.models.pelanggan import Pelanggan
    p = db.query(Pelanggan).filter(Pelanggan.id == pelanggan_id).first()
    if p and p.tgl_daftar:
        bulan_daftar = p.tgl_daftar.month
        tahun_daftar = p.tgl_daftar.year
        # konversi ke angka untuk perbandingan mudah
        periode_input  = tahun * 12 + bulan
        periode_daftar = tahun_daftar * 12 + bulan_daftar
        if periode_input < periode_daftar:
            return None, (
                f"Tidak bisa input meteran untuk bulan "
                f"{bulan}/{tahun}. "
                f"Pelanggan baru terdaftar sejak "
                f"{bulan_daftar}/{tahun_daftar}."
            )

    # auto-fill angka awal dari bulan lalu
    if angka_awal is None:
        angka_awal = get_angka_awal_otomatis(db, pelanggan_id, bulan, tahun)
    if angka_awal is None:
        return None, "BUTUH_ANGKA_AWAL"  # pelanggan baru, minta input manual

    if angka_akhir < angka_awal:
        return None, "Angka akhir tidak boleh lebih kecil dari angka awal"

    hasil = hitung_tagihan(angka_awal, angka_akhir)

    m = Meteran(
        pelanggan_id  = pelanggan_id,
        bulan         = bulan,
        tahun         = tahun,
        angka_awal    = angka_awal,
        angka_akhir   = angka_akhir,
        kubikasi      = hasil["kubikasi"],
        tagihan_air   = hasil["tagihan_air"],
        beban_dasar   = hasil["beban_dasar"],
        total_tagihan = hasil["total_tagihan"]
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return m, "OK"

    if m:  # setelah berhasil simpan
        try:
            from shared.backend.crud.crud_notifikasi import tambah_notif
            nama = m.pelanggan.nama
            tambah_notif(
                db,
                pesan = (f"Meteran pelanggan {nama} bulan "
                         f"{bulan}/{tahun} telah diinput."),
                tipe  = "meteran"
            )
        except Exception:
            pass

def get_meteran_bulanan(db: Session, bulan: int, tahun: int):
    return (
        db.query(Meteran, Pelanggan)
        .join(Pelanggan, Meteran.pelanggan_id == Pelanggan.id)
        .filter(Meteran.bulan == bulan, Meteran.tahun == tahun)
        .order_by(Pelanggan.area, Pelanggan.nama)
        .all()
    )

def get_meteran_by_id(db: Session, meteran_id: int):
    return db.query(Meteran).filter(Meteran.id == meteran_id).first()

def get_history_meteran(db: Session, pelanggan_id: int, limit: int = 12):
    """history meteran 12 bulan terakhir"""
    return (
        db.query(Meteran)
        .filter(Meteran.pelanggan_id == pelanggan_id)
        .order_by(Meteran.tahun.desc(), Meteran.bulan.desc())
        .limit(limit)
        .all()
    )
