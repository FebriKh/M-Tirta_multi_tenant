from pathlib import Path
from PIL import Image, ImageOps
import re


def slugify(text: str) -> str:
    """
    Febri Nugroho
    ->
    febri-nugroho
    """
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def save_profile_image(
    source_file,
    destination,
    size=512,
    quality=82
):
    """
    Upload JPG/PNG
        ↓
    Crop tengah
        ↓
    Resize
        ↓
    Convert WEBP
        ↓
    Compress
    """

    destination = Path(destination)

    destination.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    image = Image.open(source_file)

    # perbaiki orientasi foto HP
    image = ImageOps.exif_transpose(image)

    if image.mode != "RGB":
        image = image.convert("RGB")

    image = ImageOps.fit(
        image,
        (size, size),
        Image.Resampling.LANCZOS
    )

    image.save(
        destination,
        format="WEBP",
        quality=quality,
        optimize=True
    )

    return destination


def save_logo_image(
    source_file,
    destination,
    size=512,
    quality=85
):
    """
    Upload logo

        JPG / PNG / WEBP
              ↓
      Perbaiki orientasi
              ↓
     Resize proporsional
              ↓
       Canvas 512x512
              ↓
        Convert WEBP
              ↓
         Compress
    """

    destination = Path(destination)

    destination.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    image = Image.open(source_file)

    image = ImageOps.exif_transpose(image)

    if image.mode in ("RGBA", "LA"):
        # pertahankan transparansi
        background = Image.new(
            "RGBA",
            image.size,
            (255, 255, 255, 0)
        )
        background.paste(image, mask=image.split()[-1])
        image = background
    else:
        image = image.convert("RGBA")

    # resize tanpa merusak rasio
    image.thumbnail(
        (size, size),
        Image.Resampling.LANCZOS
    )

    # canvas transparan
    canvas = Image.new(
        "RGBA",
        (size, size),
        (255, 255, 255, 0)
    )

    x = (size - image.width) // 2
    y = (size - image.height) // 2

    canvas.paste(image, (x, y), image)

    canvas.save(
        destination,
        format="WEBP",
        quality=quality,
        method=6,
        optimize=True
    )

    return destination

