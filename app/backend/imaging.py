"""Turn uploaded bytes into a clean PIL image, with friendly errors for bad input.

Supports JPG, PNG (8/16-bit), BMP, WEBP, TIFF and DICOM (.dcm). Never raises anything
other than AppError for bad input.
"""
from __future__ import annotations

import io
import warnings
from dataclasses import dataclass
from pathlib import PurePath

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

from .config import MAX_UPLOAD_BYTES
from .errors import AppError

# Refuse absurd pixel counts (decompression bombs) but allow large scanner exports.
Image.MAX_IMAGE_PIXELS = 120_000_000

PIL_FORMATS = {"JPEG", "MPO", "PNG", "BMP", "WEBP", "TIFF"}
IMAGE_EXTS = {".jpg", ".jpeg", ".jfif", ".png", ".bmp", ".webp", ".tif", ".tiff"}
DICOM_EXTS = {".dcm", ".dicom"}
SUPPORTED_TEXT = "JPG, PNG, BMP, WEBP, TIFF or DICOM (.dcm)"
MIN_SIDE = 64


@dataclass
class Decoded:
    image: Image.Image
    kind: str  # "JPEG", "PNG", ..., "DICOM"
    width: int
    height: int


def check_size(n: int) -> None:
    if n == 0:
        raise AppError(400, "empty_file", "The file is empty. Choose a chest X-ray image and try again.")
    if n > MAX_UPLOAD_BYTES:
        mb = MAX_UPLOAD_BYTES // (1024 * 1024)
        raise AppError(413, "file_too_large", f"The file is larger than {mb} MB. Use a smaller or compressed image.")


def _is_dicom(data: bytes, filename: str) -> bool:
    if len(data) > 132 and data[128:132] == b"DICM":
        return True
    return PurePath(filename or "").suffix.lower() in DICOM_EXTS


def _to_uint8(arr: np.ndarray, lo_pct: float = 0.0, hi_pct: float = 100.0) -> np.ndarray:
    arr = np.asarray(arr, dtype=np.float32)
    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        return np.zeros(arr.shape, dtype=np.uint8)
    lo = float(np.percentile(finite, lo_pct)) if lo_pct > 0 else float(finite.min())
    hi = float(np.percentile(finite, hi_pct)) if hi_pct < 100 else float(finite.max())
    if hi - lo < 1e-6:
        return np.zeros(arr.shape, dtype=np.uint8)
    out = (np.nan_to_num(arr, nan=lo) - lo) / (hi - lo)
    return (np.clip(out, 0.0, 1.0) * 255.0).round().astype(np.uint8)


def _decode_dicom(data: bytes) -> Decoded:
    try:
        import pydicom
    except ImportError as exc:  # pragma: no cover - pydicom is in requirements
        raise AppError(415, "dicom_unavailable", "DICOM support is not installed on this computer.") from exc
    try:
        from pydicom.pixels import apply_modality_lut, apply_voi_lut  # pydicom >= 3
    except ImportError:  # pragma: no cover - older pydicom
        from pydicom.pixel_data_handlers.util import apply_modality_lut, apply_voi_lut  # type: ignore

    try:
        ds = pydicom.dcmread(io.BytesIO(data), force=True)
    except Exception as exc:
        raise AppError(422, "corrupt_dicom", "This DICOM file could not be read. It may be damaged.") from exc
    if "PixelData" not in ds:
        raise AppError(422, "dicom_no_image", "This DICOM file has no image inside it.")
    try:
        arr = ds.pixel_array
    except Exception as exc:
        raise AppError(
            422,
            "dicom_unsupported",
            "This DICOM uses a compression this app cannot open. Export it as PNG or JPG and try again.",
        ) from exc

    arr = np.asarray(arr)
    frames = int(getattr(ds, "NumberOfFrames", 1) or 1)
    spp = int(getattr(ds, "SamplesPerPixel", 1) or 1)
    if frames > 1 and arr.ndim >= 3:
        arr = arr[0]
    if spp >= 3 and arr.ndim == 3:
        arr = arr[..., :3].astype(np.float32).mean(axis=-1)
        gray = _to_uint8(arr)
    else:
        if arr.ndim != 2:
            raise AppError(422, "dicom_unsupported", "This DICOM image has an unusual layout and cannot be shown.")
        try:
            out = apply_modality_lut(arr, ds)
            has_window = "WindowCenter" in ds or "VOILUTSequence" in ds
            if has_window:
                out = apply_voi_lut(out, ds, index=0)
                gray = _to_uint8(out)
            else:
                # No window stored: use a robust percentile window.
                gray = _to_uint8(out, 0.5, 99.5)
        except Exception:
            gray = _to_uint8(arr, 0.5, 99.5)
        if str(getattr(ds, "PhotometricInterpretation", "")).upper() == "MONOCHROME1":
            gray = 255 - gray  # MONOCHROME1 stores bone dark; flip to the usual look
    img = Image.fromarray(gray)
    return Decoded(img, "DICOM", img.width, img.height)


def _normalise_mode(img: Image.Image) -> Image.Image:
    """Return an 'L' or 'RGB' image. Keep colour so the X-ray check can spot photos."""
    mode = img.mode
    if mode in ("I;16", "I;16B", "I;16L", "I;16N", "I", "F"):
        return Image.fromarray(_to_uint8(np.asarray(img)))
    if mode in ("RGBA", "LA", "PA") or (mode == "P" and "transparency" in img.info):
        rgba = img.convert("RGBA")
        black = Image.new("RGBA", rgba.size, (0, 0, 0, 255))
        return Image.alpha_composite(black, rgba).convert("RGB")
    if mode == "L":
        return img
    if mode in ("1", "P"):
        return img.convert("L") if mode == "1" else img.convert("RGB")
    if mode in ("RGB",):
        return img
    return img.convert("RGB")  # CMYK, YCbCr, LAB, HSV...


def decode_image(data: bytes, filename: str) -> Decoded:
    check_size(len(data))
    if _is_dicom(data, filename):
        dec = _decode_dicom(data)
    else:
        ext = PurePath(filename or "").suffix.lower()
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                img = Image.open(io.BytesIO(data))
                fmt = (img.format or "").upper()
                if fmt not in PIL_FORMATS:
                    raise AppError(
                        415,
                        "unsupported_type",
                        f"{fmt or 'This'} files are not supported. Upload a {SUPPORTED_TEXT} file.",
                    )
                try:
                    img.seek(0)
                except EOFError:
                    pass
                img.load()
                img = ImageOps.exif_transpose(img) or img
                img = _normalise_mode(img)
                img.load()
        except AppError:
            raise
        except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
            raise AppError(413, "image_too_large", "The image has too many pixels to process safely.") from exc
        except UnidentifiedImageError as exc:
            if ext and ext not in IMAGE_EXTS:
                raise AppError(415, "unsupported_type", f"This file type is not supported. Upload a {SUPPORTED_TEXT} file.") from exc
            raise AppError(422, "corrupt_image", "This file is not a readable image. It may be damaged or not an image at all.") from exc
        except Exception as exc:  # truncated / broken files raise OSError, SyntaxError, ValueError...
            raise AppError(422, "corrupt_image", "This image is damaged or incomplete and could not be opened.") from exc
        dec = Decoded(img, fmt, img.width, img.height)

    if min(dec.width, dec.height) < MIN_SIDE:
        raise AppError(422, "image_too_small", f"The image is too small ({dec.width}×{dec.height}). Use an X-ray at least {MIN_SIDE} px wide.")
    return dec


def make_thumbnail(png_bytes: bytes, long_side: int) -> bytes:
    img = Image.open(io.BytesIO(png_bytes))
    img = img.convert("RGB") if img.mode not in ("L", "RGB") else img
    img.thumbnail((long_side, long_side), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=86, optimize=True)
    return buf.getvalue()
