from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

from birdcropper.crop import center_crop_box
from birdcropper.io import image_paths, input_dir_argument, output_dir_for, resolve_input_dir
from birdcropper.photo import open_photo, output_path_for, save_photo, supported_extensions_text

DEFAULT_CROP_FACTOR = 0.3
SUFFIX = "_cropped"


def crop_center(image: Image.Image, factor: float) -> Image.Image:
    """Return a centered crop of the image with the given factor."""
    return image.crop(center_crop_box(image.size, factor))


def process_image(img_path: Path, output_dir: Path, crop_factor: float):
    print(f"Processing: {img_path.name}")
    photo = open_photo(img_path)
    img = photo.image

    orig_size = img.size

    cropped = crop_center(img, crop_factor)
    upscaled = cropped.resize(orig_size, Image.Resampling.LANCZOS)

    out_path = output_path_for(img_path, output_dir, SUFFIX)
    save_photo(upscaled, out_path, photo.exif)
    print(f"Saved: {out_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Center-crop bird photos and resize them back to original dimensions."
    )
    input_dir_argument(parser)
    parser.add_argument(
        "--crop-factor",
        type=float,
        default=DEFAULT_CROP_FACTOR,
        help="Fraction of width and height to keep in the center crop.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    input_dir = resolve_input_dir(args.input_dir)
    if input_dir is None:
        print("No folder selected. Nothing to do.")
        return

    output_dir = output_dir_for(input_dir)
    images = image_paths(input_dir)

    if not images:
        print(f"No supported photos found in {input_dir}")
        print(f"Supported extensions: {supported_extensions_text()}")
        return

    for img_path in images:
        process_image(img_path, output_dir, args.crop_factor)


if __name__ == "__main__":
    main()
