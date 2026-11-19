from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from PIL import Image, ImageOps


MAX_IMAGE_SIDE = 2048
JPEG_QUALITY = 85


def prepare_photo(upload):
    upload.seek(0)
    with Image.open(upload) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
        image.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE), Image.Resampling.LANCZOS)
        output = BytesIO()
        image.save(output, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    output.seek(0)
    name = f"{Path(upload.name).stem}.jpg"
    return name, ContentFile(output.read())
