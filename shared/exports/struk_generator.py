# exports/struk_generator.py
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from sqlalchemy.orm import Session
from shared.backend.crud import *
from dashboard.utils import nama_bulan, rupiah
from dashboard.config import load_config, ASSETS_DIR

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# warna
BIRU_TUA  = "#1F4E79"
PUTIH     = "#FFFFFF"
ABU_MUDA  = "#F8F9FA"
ABU_TUA   = "#6C757D"
HITAM     = "#212529"
HIJAU     = "#1D9E75"
MERAH     = "#D85A30"
KUNING_BG = "#FFF3CD"
KUNING    = "#856404"

def hex_to_rgb(hex_color: str) -> tuple:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def get_font(size: int, bold: bool = False):
    """coba load font system, fallback ke default"""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in font_paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def draw_line(draw, y, x1, x2, color="#DEE2E6", dash=False):
    if dash:
        x = x1
        while x < x2:
            draw.line([(x, y), (min(x+8, x2), y)], fill=color, width=1)
            x += 14
    else:
        draw.line([(x1, y), (x2, y)], fill=color, width=1)
    return y

def draw_row(draw, y, label, value, font_label, font_value,
             w, pad, value_color=None):
    draw.text((pad, y), label, font=font_label, fill=hex_to_rgb(ABU_TUA))
    value_color = value_color or HITAM
    bbox = draw.textbbox((0, 0), value, font=font_value)
    vw   = bbox[2] - bbox[0]
    draw.text((w - pad - vw, y), value,
              font=font_value, fill=hex_to_rgb(value_color))
    return y + 24

def generate_struk(db: Session, pembayaran_id: int) -> str:
    """generate struk PNG dari ID pembayaran"""
    from shared.backend.models.pembayaran import Pembayaran as PB
    from shared.backend.models.meteran import Meteran

    b = db.query(PB).filter(PB.id == pembayaran_id).first()
    if not b:
        raise ValueError("Pembayaran tidak ditemukan")

    m   = b.meteran
    p   = m.pelanggan
    cfg = load_config()

    # data struk
    tgl_bayar   = b.tgl_bayar.strftime("%d %B %Y")
    is_cicil    = b.status == "cicil"
    terbayar    = get_total_terbayar(db, m.id)
    sisa        = get_sisa_tagihan(db, m.id)
    riwayat     = get_riwayat_cicilan(db, m.id)
    tunggakan   = get_tunggakan_pelanggan(db, p.id)
    # filter tunggakan bulan lain (bukan bulan ini)
    tunggakan_lain = [t for t in tunggakan if t["meteran_id"] != m.id]

    # ukuran kanvas — hitung tinggi dinamis
    W   = 400
    PAD = 24
    H_BASE = 520
    H_CICIL    = 30 * len(riwayat) + 60 if is_cicil else 0
    H_TUNGGAK  = 30 * len(tunggakan_lain) + 60 if tunggakan_lain else 0
    H          = H_BASE + H_CICIL + H_TUNGGAK

    img  = Image.new("RGB", (W, H), hex_to_rgb(PUTIH))
    draw = ImageDraw.Draw(img)

    # font
    f_big    = get_font(22, bold=True)
    f_med    = get_font(15, bold=True)
    f_norm   = get_font(13)
    f_norm_b = get_font(13, bold=True)
    f_small  = get_font(11)

    # --- HEADER ---
    draw.rectangle([(0, 0), (W, 90)],
                   fill=hex_to_rgb(BIRU_TUA))
    nama_app = cfg.get("nama_app", "PamSR")
    nama_org = cfg.get("nama_org", "Pamsimas SR")

    # cek logo
    logo_file = cfg.get("logo_file", "")
    logo_x    = PAD
    if logo_file:
        logo_path = os.path.join(ASSETS_DIR, logo_file)
        if os.path.exists(logo_path):
            logo = Image.open(logo_path).convert("RGBA")
            logo = logo.resize((50, 50))
            img.paste(logo, (PAD, 20), logo)
            logo_x = PAD + 60

    draw.text((logo_x, 20), nama_app,
              font=f_med, fill=hex_to_rgb(PUTIH))
    draw.text((logo_x, 42), nama_org,
              font=f_small, fill=(255, 255, 255, 180))
    draw.text((logo_x, 60), cfg.get("alamat_org", ""),
              font=f_small, fill=(200, 200, 200))

    y = 100

    # --- BADGE STATUS ---
    if is_cicil:
        draw.rounded_rectangle([(PAD, y), (PAD+70, y+22)],
                                radius=11,
                                fill=hex_to_rgb(KUNING_BG))
        draw.text((PAD+8, y+4), "CICILAN",
                  font=f_small, fill=hex_to_rgb(KUNING))
    else:
        draw.rounded_rectangle([(PAD, y), (PAD+70, y+22)],
                                radius=11,
                                fill=hex_to_rgb("#D1FAE5"))
        draw.text((PAD+8, y+4), "LUNAS",
                  font=f_small, fill=hex_to_rgb("#065F46"))

    y += 32
    draw.text((PAD, y), f"Rp {b.jumlah_bayar:,}".replace(",", "."),
              font=f_big, fill=hex_to_rgb(HITAM))
    y += 34
    draw.text((PAD, y), tgl_bayar,
              font=f_small, fill=hex_to_rgb(ABU_TUA))
    y += 24

    draw_line(draw, y, 0, W)
    y += 16

    # --- INFO PELANGGAN ---
    inisial = p.nama[:2].upper()
    draw.ellipse([(PAD, y), (PAD+36, y+36)],
                 fill=hex_to_rgb("#DBEAFE"))
    draw.text((PAD+10, y+8), inisial,
              font=f_norm_b, fill=hex_to_rgb("#1E40AF"))
    draw.text((PAD+44, y+2), p.nama,
              font=f_norm_b, fill=hex_to_rgb(HITAM))
    area_desa = f"{p.area or ''} · {p.desa or ''}".strip(" ·")
    draw.text((PAD+44, y+20), area_desa,
              font=f_small, fill=hex_to_rgb(ABU_TUA))
    y += 52

    draw_line(draw, y, 0, W)
    y += 16

    # --- RINCIAN TAGIHAN ---
    draw.text((PAD, y), "RINCIAN TAGIHAN",
              font=f_small, fill=hex_to_rgb(ABU_TUA))
    y += 20

    y = draw_row(draw, y, "Periode",
                 f"{nama_bulan(m.bulan)} {m.tahun}",
                 f_norm, f_norm, W, PAD)
    y = draw_row(draw, y, "Kubikasi",
                 f"{float(m.kubikasi):.1f} m³",
                 f_norm, f_norm, W, PAD)
    y = draw_row(draw, y, "Total tagihan",
                 rupiah(m.total_tagihan + (b.diskon or 0)),
                 f_norm, f_norm, W, PAD)

    if b.diskon and b.diskon > 0:
        y = draw_row(draw, y, "Diskon",
                     f"- {rupiah(b.diskon)}",
                     f_norm, f_norm_b, W, PAD,
                     value_color=HIJAU)

    draw_line(draw, y, PAD, W-PAD, dash=True)
    y += 12

    if is_cicil:
        y = draw_row(draw, y, "Dibayar sekarang",
                     rupiah(b.jumlah_bayar),
                     f_norm_b, f_norm_b, W, PAD)
        y = draw_row(draw, y, "Sisa tagihan",
                     rupiah(sisa),
                     f_norm_b, f_norm_b, W, PAD,
                     value_color=MERAH)
    else:
        y = draw_row(draw, y, "Total Bayar",
                     rupiah(b.jumlah_bayar),
                     f_norm_b, f_norm_b, W, PAD)

    draw_line(draw, y, 0, W)
    y += 16

    # --- RIWAYAT CICILAN ---
    if is_cicil and riwayat:
        draw.text((PAD, y), "RIWAYAT CICILAN",
                  font=f_small, fill=hex_to_rgb(ABU_TUA))
        y += 20
        for i, cicil in enumerate(riwayat, 1):
            tgl  = cicil.tgl_bayar.strftime("%d/%m/%Y")
            label = f"Cicilan ke-{i} · {tgl}"
            draw.text((PAD, y), label,
                      font=f_small, fill=hex_to_rgb(ABU_TUA))
            nilai = rupiah(cicil.jumlah_bayar)
            bbox  = draw.textbbox((0,0), nilai, font=f_small)
            vw    = bbox[2] - bbox[0]
            draw.text((W-PAD-vw, y), nilai,
                      font=f_small, fill=hex_to_rgb(HITAM))
            y += 26

        draw_line(draw, y, 0, W)
        y += 16

    # --- TUNGGAKAN BULAN LAIN ---
    if tunggakan_lain:
        draw.rectangle([(0, y), (W, y+24)],
                       fill=hex_to_rgb("#FFF3CD"))
        draw.text((PAD, y+6), "TUNGGAKAN BULAN LALU",
                  font=f_small, fill=hex_to_rgb(KUNING))
        y += 30

        total_tunggak = 0
        for t in tunggakan_lain:
            label = f"{nama_bulan(t['bulan'])} {t['tahun']}"
            draw.text((PAD, y), label,
                      font=f_small, fill=hex_to_rgb(ABU_TUA))
            nilai = rupiah(t["sisa"])
            bbox  = draw.textbbox((0,0), nilai, font=f_small)
            vw    = bbox[2] - bbox[0]
            draw.text((W-PAD-vw, y), nilai,
                      font=f_small, fill=hex_to_rgb(MERAH))
            y += 24
            total_tunggak += t["sisa"]

        draw_line(draw, y, PAD, W-PAD, dash=True)
        y += 12
        draw.text((PAD, y), "Total tunggakan",
                  font=f_norm_b, fill=hex_to_rgb(HITAM))
        nilai = rupiah(total_tunggak)
        bbox  = draw.textbbox((0,0), nilai, font=f_norm_b)
        vw    = bbox[2] - bbox[0]
        draw.text((W-PAD-vw, y), nilai,
                  font=f_norm_b, fill=hex_to_rgb(MERAH))
        y += 30

        draw_line(draw, y, 0, W)
        y += 16

    # --- INFO PEMBAYARAN ---
    draw.text((PAD, y), "INFO PEMBAYARAN",
              font=f_small, fill=hex_to_rgb(ABU_TUA))
    y += 20
    y = draw_row(draw, y, "Metode",
                 b.metode.upper(), f_norm, f_norm, W, PAD)
    y = draw_row(draw, y, "No. Transaksi",
                 f"#TRX-{b.id:05d}", f_norm, f_norm, W, PAD)
    if b.catatan:
        y = draw_row(draw, y, "Catatan",
                     b.catatan, f_norm, f_norm, W, PAD)

    draw_line(draw, y, 0, W)
    y += 16

    # --- FOOTER ---
    pesan = "Terima kasih telah membayar tepat waktu!" \
            if not is_cicil else "Harap segera melunasi sisa tagihan."
    bbox_p = draw.textbbox((0,0), pesan, font=f_small)
    pw     = bbox_p[2] - bbox_p[0]
    draw.text(((W-pw)//2, y), pesan,
              font=f_small, fill=hex_to_rgb(ABU_TUA))
    y += 20

    domain = "kasegeran.pamsr.my.id"
    bbox_d = draw.textbbox((0,0), domain, font=f_small)
    dw     = bbox_d[2] - bbox_d[0]
    draw.text(((W-dw)//2, y), domain,
              font=f_small, fill=hex_to_rgb("#ADB5BD"))

    # crop ke tinggi aktual
    img_crop = img.crop((0, 0, W, min(y+40, H)))

    filename = f"struk_{b.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
    filepath = os.path.join(OUTPUT_DIR, filename)
    img_crop.save(filepath, "PNG", quality=95)
    return filepath
