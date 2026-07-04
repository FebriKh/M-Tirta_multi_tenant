# exports/pdf_export.py
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                 Paragraph, Spacer, HRFlowable)
from reportlab.lib.enums import TA_CENTER
from sqlalchemy.orm import Session
from shared.backend.crud import *
from shared.backend.models.pembayaran import Pembayaran
from shared.backend.models.meteran import Meteran
from dashboard.utils import nama_bulan, rupiah

EXPORT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(EXPORT_DIR, exist_ok=True)

BIRU      = colors.HexColor("#1F4E79")
BIRU_MUDA = colors.HexColor("#BDD7EE")
PUTIH     = colors.white
HIJAU     = colors.HexColor("#1F7A1F")
MERAH     = colors.HexColor("#C00000")
ABU       = colors.HexColor("#F2F2F2")

def base_style():
    return [
        ("BACKGROUND",     (0,0), (-1,0),  BIRU),
        ("TEXTCOLOR",      (0,0), (-1,0),  PUTIH),
        ("FONTNAME",       (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",       (0,0), (-1,0),  9),
        ("ALIGN",          (0,0), (-1,-1), "CENTER"),
        ("VALIGN",         (0,0), (-1,-1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0,1), (-1,-2), [PUTIH, ABU]),
        ("GRID",           (0,0), (-1,-1), 0.5, colors.grey),
        ("FONTSIZE",       (0,1), (-1,-1), 8),
        ("TOPPADDING",     (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",  (0,0), (-1,-1), 4),
        ("BACKGROUND",     (0,-1),(-1,-1), BIRU_MUDA),
        ("FONTNAME",       (0,-1),(-1,-1), "Helvetica-Bold"),
    ]

def get_styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle("Judul", fontSize=15, fontName="Helvetica-Bold",
                          textColor=PUTIH, alignment=TA_CENTER))
    s.add(ParagraphStyle("Sub",   fontSize=10, fontName="Helvetica",
                          textColor=PUTIH, alignment=TA_CENTER))
    s.add(ParagraphStyle("Seksi", fontSize=12, fontName="Helvetica-Bold",
                          textColor=BIRU, spaceBefore=14, spaceAfter=5))
    return s

def header_doc(styles, bulan, tahun, judul_override=None):
    judul = judul_override or f"LAPORAN KEUANGAN PAMSIMAS TIRTA LESTARI IV"
    t1 = Table([[Paragraph(judul, styles["Judul"])]],
               colWidths=[25*cm])
    t1.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), BIRU),
        ("TOPPADDING",    (0,0),(-1,-1), 10),
        ("BOTTOMPADDING", (0,0),(-1,-1), 10),
    ]))
    return [t1, Spacer(1, 0.3*cm)]

def section_ringkasan(styles, db, bulan, tahun):
    kas          = sinkron_kas(db, bulan, tahun)
    total_keluar = get_total_pengeluaran_bulan(db, bulan, tahun)
    piutang      = get_piutang_bulan(db, bulan, tahun)

    data = [
        ["Keterangan",              "Jumlah"],
        ["Target Penarikan",        rupiah(kas.target_penarikan)],
        ["Aktual Terkumpul",        rupiah(kas.aktual_terkumpul)],
        ["Dari Pemasangan Baru",    rupiah(kas.pemasukan_pemasangan)],
        ["Saldo Bulan Lalu",        rupiah(kas.saldo_bulan_lalu or 0)],
        ["Total Pengeluaran",       rupiah(total_keluar)],
        ["Piutang Belum Lunas",     f"{len(piutang)} pelanggan"],
        ["TOTAL SALDO KAS",         rupiah(kas.total_saldo)],
    ]
    t = Table(data, colWidths=[12*cm, 12*cm])
    t.setStyle(TableStyle(base_style() + [
        ("BACKGROUND", (0,7),(-1,7), BIRU),
        ("TEXTCOLOR",  (0,7),(-1,7), PUTIH),
        ("FONTNAME",   (0,7),(-1,7), "Helvetica-Bold"),
    ]))
    return [Paragraph("Ringkasan Kas", styles["Seksi"]), t]

def section_tagihan(styles, db, bulan, tahun):
    data_raw = get_meteran_bulanan(db, bulan, tahun)
    rows     = [["No","Nama","Area","Kubikasi","Total","Terbayar","Sisa","Status"]]
    t_tag = t_bayar = t_sisa = 0

    for i, (m, p) in enumerate(data_raw, 1):
        terbayar = get_total_terbayar(db, m.id)
        sisa     = m.total_tagihan - terbayar
        rows.append([
            i, p.nama, p.area or "-",
            f"{float(m.kubikasi):.2f} m3",
            rupiah(m.total_tagihan),
            rupiah(terbayar),
            rupiah(sisa),
            "Lunas" if sisa == 0 else "Belum"
        ])
        t_tag += m.total_tagihan; t_bayar += terbayar; t_sisa += sisa

    rows.append(["","TOTAL","","",
                  rupiah(t_tag), rupiah(t_bayar), rupiah(t_sisa), ""])

    col_w = [0.8*cm, 5*cm, 2*cm, 2.5*cm, 3*cm, 3*cm, 3*cm, 2*cm]
    t     = Table(rows, colWidths=col_w, repeatRows=1)
    st    = base_style()
    for i, (m, p) in enumerate(data_raw, 1):
        sisa  = m.total_tagihan - get_total_terbayar(db, m.id)
        warna = HIJAU if sisa == 0 else MERAH
        st   += [("TEXTCOLOR", (7,i),(7,i), warna),
                 ("FONTNAME",  (7,i),(7,i), "Helvetica-Bold")]
    t.setStyle(TableStyle(st))
    return [Paragraph("Rekap Tagihan", styles["Seksi"]), t]

def section_pengeluaran(styles, db, bulan, tahun):
    data  = get_pengeluaran_bulan(db, bulan, tahun)
    total = get_total_pengeluaran_bulan(db, bulan, tahun)
    rows  = [["No","Tanggal","Keperluan","Jumlah","Direquest"]]

    for i, p in enumerate(data, 1):
        rows.append([
            i, p.tanggal.strftime("%d/%m/%Y"),
            p.keperluan, rupiah(p.jumlah),
            p.direquest_oleh or "-"
        ])
    rows.append(["","","TOTAL", rupiah(total),""])

    col_w = [0.8*cm, 2.5*cm, 8*cm, 3*cm, 3*cm]
    t     = Table(rows, colWidths=col_w, repeatRows=1)
    t.setStyle(TableStyle(base_style()))
    return [Paragraph("Pengeluaran", styles["Seksi"]), t]

def section_footer(styles):
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    ft  = Table(
        [[f"Dicetak: {now}", "Bendahara,", "Ketua,"],
         ["", "", ""],
         ["", "( Rofikoh Haryanti )", "( Bp Sawin )"]],
        colWidths=[9*cm, 7*cm, 7*cm]
    )
    ft.setStyle(TableStyle([
        ("FONTSIZE",  (0,0),(-1,-1), 8),
        ("ALIGN",     (1,0),(-1,-1), "CENTER"),
        ("FONTNAME",  (0,2),(-1,2),  "Helvetica-Bold"),
        ("TOPPADDING",(0,0),(-1,-1), 4),
    ]))
    return [Spacer(1, 1*cm), HRFlowable(width="100%"),
            Spacer(1, 0.3*cm), ft]

def export_laporan_pdf(db: Session, bulan: int, tahun: int) -> str:
    filename = f"Laporan_PamSR_{nama_bulan(bulan)}_{tahun}.pdf"
    filepath = os.path.join(EXPORT_DIR, filename)
    doc    = SimpleDocTemplate(filepath, pagesize=landscape(A4),
                               leftMargin=1.5*cm, rightMargin=1.5*cm,
                               topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles  = get_styles()
    content = []

    # ← hanya ini, yang lama dihapus
    content += header_doc(
        styles,
        bulan, tahun,
        judul_override=f"LAPORAN KEUANGAN PAMSIMAS TIRTA LESTARI IV\nPeriode: {nama_bulan(bulan)} {tahun}"
    )

    content += section_ringkasan(styles, db, bulan, tahun)
    content += [Spacer(1, 0.3*cm)]
    content += section_tagihan(styles, db, bulan, tahun)
    content += [Spacer(1, 0.3*cm)]
    content += section_pengeluaran(styles, db, bulan, tahun)
    content += section_footer(styles)
    doc.build(content)
    return filepath

def export_laporan_range_pdf(db: Session,
                              bulan_awal: int, tahun_awal: int,
                              bulan_akhir: int, tahun_akhir: int) -> str:
    filename = (f"Laporan_PamSR_"
                f"{nama_bulan(bulan_awal)}{tahun_awal}_"
                f"sd_{nama_bulan(bulan_akhir)}{tahun_akhir}.pdf")
    filepath = os.path.join(EXPORT_DIR, filename)

    doc    = SimpleDocTemplate(filepath, pagesize=landscape(A4),
                               leftMargin=1.5*cm, rightMargin=1.5*cm,
                               topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = get_styles()

    # hitung semua bulan dalam range
    periode_list = []
    b, t = bulan_awal, tahun_awal
    while (t * 12 + b) <= (tahun_akhir * 12 + bulan_akhir):
        periode_list.append((b, t))
        b += 1
        if b > 12:
            b = 1
            t += 1

    content = []

    # header dokumen
    judul = (f"LAPORAN KEUANGAN PAMSIMAS TIRTA LESTARI IV\n"
             f"{nama_bulan(bulan_awal)} {tahun_awal} — "
             f"{nama_bulan(bulan_akhir)} {tahun_akhir}")
    content += header_doc(styles, bulan_awal, tahun_awal,
                          judul_override=judul)

    # ringkasan per bulan
    ring_data = [["Bulan","Target","Terkumpul",
                  "Pemasangan","Pengeluaran","Saldo"]]
    grand = [0, 0, 0, 0]

    for b, t in periode_list:
        kas    = sinkron_kas(db, b, t)
        keluar = get_total_pengeluaran_bulan(db, b, t)
        ring_data.append([
            f"{nama_bulan(b)} {t}",
            rupiah(kas.target_penarikan),
            rupiah(kas.aktual_terkumpul),
            rupiah(kas.pemasukan_pemasangan),
            rupiah(keluar),
            rupiah(kas.total_saldo)
        ])
        grand[0] += kas.target_penarikan
        grand[1] += kas.aktual_terkumpul
        grand[2] += kas.pemasukan_pemasangan
        grand[3] += keluar

    ring_data.append([
        "TOTAL",
        rupiah(grand[0]), rupiah(grand[1]),
        rupiah(grand[2]), rupiah(grand[3]), ""
    ])

    col_w = [3*cm, 3.5*cm, 3.5*cm, 3.5*cm, 3.5*cm, 3.5*cm]
    t_ring = Table(ring_data, colWidths=col_w, repeatRows=1)
    t_ring.setStyle(TableStyle(base_style()))
    content += [
        Paragraph("Ringkasan Per Bulan", styles["Seksi"]),
        t_ring,
        Spacer(1, 0.5*cm)
    ]

    # detail per bulan — mengalir
    for b, t in periode_list:
        content += [
            Paragraph(f"── {nama_bulan(b)} {t} ──",
                      styles["Seksi"]),
        ]
        content += section_tagihan(styles, db, b, t)
        content += [Spacer(1, 0.3*cm)]
        content += section_pengeluaran(styles, db, b, t)
        content += [Spacer(1, 0.5*cm)]

    content += section_footer(styles)
    doc.build(content)
    return filepath
