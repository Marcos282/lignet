import warnings
from io import BytesIO
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError


def normalize_photo(upload):
    if upload.size > 8 * 1024 * 1024:
        raise ValidationError("A foto excede 8 MB.")
    try:
        upload.seek(0)
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(upload) as source:
                if source.format not in ("JPEG", "PNG", "WEBP"):
                    raise ValidationError("Envie uma foto JPG, PNG ou WebP.")
                if source.width * source.height > 24_000_000 or max(source.size) > 12000:
                    raise ValidationError("A foto excede 24 megapixels ou 12.000 pixels de lado.")
                image = ImageOps.exif_transpose(source)
                image.thumbnail((1920, 1920))
                background = Image.new("RGB", image.size, "white")
                rgba = image.convert("RGBA")
                background.paste(rgba, mask=rgba.getchannel("A"))
                result = BytesIO()
                # Re-encoding removes EXIF/location data and discards the original filename.
                background.save(result, "JPEG", quality=86, optimize=True)
        return ContentFile(result.getvalue(), name=f"{uuid4().hex}.jpg")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ValidationError("Não foi possível abrir a foto com segurança.") from exc
    finally:
        upload.seek(0)
