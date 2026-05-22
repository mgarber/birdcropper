from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps

RASTER_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
RAW_EXTENSIONS = {".cr2", ".cr3"}
SUPPORTED_EXTENSIONS = RASTER_EXTENSIONS | RAW_EXTENSIONS


@dataclass(frozen=True)
class OpenedPhoto:
    image: Image.Image
    exif: bytes | None
    source_is_raw: bool


def supported_extensions_text() -> str:
    return ", ".join(sorted(SUPPORTED_EXTENSIONS))


def is_supported_photo(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_EXTENSIONS


def open_photo(path: Path) -> OpenedPhoto:
    """Open a supported photo as a Pillow image."""
    if path.suffix.lower() in RAW_EXTENSIONS:
        return open_raw_photo(path)

    img = Image.open(path)
    img = ImageOps.exif_transpose(img)
    return OpenedPhoto(
        image=img,
        exif=img.info.get("exif"),
        source_is_raw=False,
    )


def open_raw_photo(path: Path) -> OpenedPhoto:
    try:
        import rawpy
    except ImportError as exc:
        raise RuntimeError(
            "Canon RAW files need the optional rawpy package. For now, test "
            "with JPEG, PNG, or TIFF files, or run: python -m pip install rawpy"
        ) from exc

    with rawpy.imread(str(path)) as raw:
        rgb = raw.postprocess(use_camera_wb=True, no_auto_bright=True, output_bps=8)

    return OpenedPhoto(
        image=Image.fromarray(rgb),
        exif=None,
        source_is_raw=True,
    )


def output_path_for(source_path: Path, output_dir: Path, suffix: str) -> Path:
    output_ext = ".jpg" if source_path.suffix.lower() in RAW_EXTENSIONS else source_path.suffix
    return output_dir / f"{source_path.stem}{suffix}{output_ext}"


def save_photo(img: Image.Image, out_path: Path, exif: bytes | None = None) -> None:
    ext = out_path.suffix.lower()
    save_kwargs = {}

    if ext in {".jpg", ".jpeg"}:
        save_kwargs.update({"quality": 95, "subsampling": 0})
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
    elif ext in {".tif", ".tiff"}:
        save_kwargs["compression"] = "tiff_lzw"

    if exif is not None and ext in {".jpg", ".jpeg", ".tif", ".tiff"}:
        save_kwargs["exif"] = exif

    img.save(out_path, **save_kwargs)
