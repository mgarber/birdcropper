from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
from matplotlib.widgets import RectangleSelector
from PIL import Image

from birdcropper.crop import adjust_bbox_to_aspect
from birdcropper.io import image_paths, input_dir_argument, output_dir_for, resolve_input_dir
from birdcropper.photo import open_photo, output_path_for, save_photo, supported_extensions_text
from birdcropper.suggest import suggest_subject_bbox

# Disable Matplotlib's default keybindings that conflict with ours.
mpl.rcParams["keymap.save"] = []
mpl.rcParams["keymap.quit"] = []
mpl.rcParams["keymap.quit_all"] = []

SUFFIX = "_cropped"


@dataclass(frozen=True)
class CropSettings:
    upscale_to_original: bool = True
    preview_max_side: int = 1800
    auto_margin: float = 0.08


@dataclass(frozen=True)
class DisplayImage:
    array: np.ndarray
    size: tuple[int, int]
    scale_x: float
    scale_y: float


def build_display_image(img: Image.Image, max_side: int) -> DisplayImage:
    """Create a smaller display copy and track how it maps to the original."""
    display = img.convert("RGB")
    orig_w, orig_h = display.size

    if max(orig_w, orig_h) > max_side:
        display.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)

    disp_w, disp_h = display.size
    return DisplayImage(
        array=np.array(display),
        size=(disp_w, disp_h),
        scale_x=orig_w / disp_w,
        scale_y=orig_h / disp_h,
    )


def display_bbox_to_original(
    bbox: tuple[int, int, int, int],
    display: DisplayImage,
    orig_size: tuple[int, int],
) -> tuple[int, int, int, int]:
    left, top, right, bottom = bbox
    orig_w, orig_h = orig_size

    return (
        int(round(max(0, left * display.scale_x))),
        int(round(max(0, top * display.scale_y))),
        int(round(min(orig_w, right * display.scale_x))),
        int(round(min(orig_h, bottom * display.scale_y))),
    )


def original_bbox_to_display(
    bbox: tuple[int, int, int, int],
    display: DisplayImage,
) -> tuple[float, float, float, float]:
    left, top, right, bottom = bbox
    return (
        left / display.scale_x,
        top / display.scale_y,
        right / display.scale_x,
        bottom / display.scale_y,
    )


def draw_and_select_bbox(img_path: Path, settings: CropSettings):
    """
    First stage: user draws a rectangle, presses c/s/q.
    Returns (action, bbox, image) where bbox is in original image coordinates.
    """
    photo = open_photo(img_path)
    img = photo.image
    w, h = img.size
    display = build_display_image(img, settings.preview_max_side)
    disp_w, disp_h = display.size

    selected = {"bbox": None, "action": None}
    suggestion_rect = {"patch": None}

    def set_selected_bbox(display_bbox, edgecolor: str):
        selected["bbox"] = display_bbox_to_original(
            display_bbox,
            display,
            (w, h),
        )

        left, top, right, bottom = display_bbox
        if suggestion_rect["patch"] is None:
            suggestion_rect["patch"] = Rectangle(
                (left, top),
                right - left,
                bottom - top,
                fill=False,
                edgecolor=edgecolor,
                linewidth=2,
            )
            ax.add_patch(suggestion_rect["patch"])
        else:
            patch = suggestion_rect["patch"]
            patch.set_xy((left, top))
            patch.set_width(right - left)
            patch.set_height(bottom - top)
            patch.set_edgecolor(edgecolor)
        fig.canvas.draw_idle()

    def onselect(eclick, erelease):
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata
        if x1 is None or y1 is None or x2 is None or y2 is None:
            return

        left = int(max(0, min(x1, x2)))
        right = int(min(disp_w, max(x1, x2)))
        top = int(max(0, min(y1, y2)))
        bottom = int(min(disp_h, max(y1, y2)))

        if right <= left or bottom <= top:
            selected["bbox"] = None
            return

        set_selected_bbox((left, top, right, bottom), "cyan")

    def onclick(event):
        if event.inaxes != ax or event.xdata is None or event.ydata is None:
            return
        toolbar = getattr(fig.canvas, "toolbar", None)
        if toolbar is not None and getattr(toolbar, "mode", ""):
            return

        display_bbox = suggest_subject_bbox(
            display.array,
            (event.xdata, event.ydata),
            margin_fraction=settings.auto_margin,
        )
        set_selected_bbox(display_bbox, "yellow")

    def onkey(event):
        if event.key in ("c", "s", "q"):
            selected["action"] = event.key
            plt.close(event.canvas.figure)

    fig, ax = plt.subplots(figsize=(10, 7))
    ax.imshow(display.array)
    ax.set_title(
        f"{img_path.name}\n"
        "Click the bird to suggest a crop, or drag to draw one.\n"
        "Then press: 'c' = confirm selection, 's' = skip, 'q' = quit"
    )

    selector = RectangleSelector(
        ax,
        onselect,
        interactive=True,
        button=[1],
        minspanx=5,
        minspany=5,
        spancoords="pixels",
    )
    fig._birdcropper_selector = selector

    fig.canvas.mpl_connect("button_press_event", onclick)
    fig.canvas.mpl_connect("key_press_event", onkey)
    plt.show()
    plt.close(fig)

    return selected["action"], selected["bbox"], (w, h), img


def preview_adjusted_bbox(
    img: Image.Image,
    bbox_adj: tuple[int, int, int, int],
    img_path: Path,
    settings: CropSettings,
):
    """
    Second stage: show adjusted aspect-locked bbox and ask user to accept.
    Returns one of 'y' (yes), 'r' (redo), 's' (skip), 'q' (quit).
    """
    display = build_display_image(img, settings.preview_max_side)
    left, top, right, bottom = original_bbox_to_display(bbox_adj, display)
    rect_w = right - left
    rect_h = bottom - top

    result = {"key": None}

    def onkey(event):
        if event.key in ("y", "r", "s", "q"):
            result["key"] = event.key
            plt.close(event.canvas.figure)

    fig, ax = plt.subplots(figsize=(10, 7))
    ax.imshow(display.array)
    ax.add_patch(
        Rectangle(
            (left, top),
            rect_w,
            rect_h,
            fill=False,
            edgecolor="yellow",
            linewidth=2,
        )
    )
    ax.set_title(
        f"{img_path.name}\n"
        "Adjusted crop to match original aspect ratio.\n"
        "Press: 'y' = accept & save, 'r' = redraw, 's' = skip, 'q' = quit"
    )

    fig.canvas.mpl_connect("key_press_event", onkey)
    plt.show()
    plt.close(fig)

    return result["key"]


def interactive_crop(img_path: Path, settings: CropSettings):
    """
    Full interaction:
      - User draws a box, presses c/s/q
      - If 'c', adjust aspect ratio and show preview
      - User presses y/r/s/q
    Returns:
      - 'QUIT' to stop everything
      - None to skip this image
      - bbox (left, top, right, bottom) to crop & save
    """
    while True:
        action, bbox_user, orig_size, img = draw_and_select_bbox(img_path, settings)

        if action == "q":
            return "QUIT"
        if action == "s" or bbox_user is None:
            print("Skipped.")
            return None
        if action == "c":
            bbox_adj = adjust_bbox_to_aspect(bbox_user, orig_size)
            choice = preview_adjusted_bbox(img, bbox_adj, img_path, settings)
            if choice == "y":
                return bbox_adj
            if choice == "r":
                continue
            if choice == "s":
                print("Skipped after preview.")
                return None
            if choice == "q":
                return "QUIT"


def process_image(img_path: Path, output_dir: Path, settings: CropSettings):
    print(f"\n>>> {img_path.name}")
    bbox = interactive_crop(img_path, settings)

    if bbox == "QUIT":
        return "QUIT"
    if bbox is None:
        return None

    photo = open_photo(img_path)
    img = photo.image
    orig_size = img.size

    cropped = img.crop(bbox)

    if settings.upscale_to_original:
        final = cropped.resize(orig_size, Image.Resampling.LANCZOS)
    else:
        final = cropped

    out_path = output_path_for(img_path, output_dir, SUFFIX)
    save_photo(final, out_path, photo.exif)
    print(f"Cropped and saved: {out_path}")
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Interactively crop bird photos and save full-resolution outputs."
    )
    input_dir_argument(parser)
    parser.add_argument(
        "--no-upscale",
        action="store_true",
        help="Save the cropped image at crop size instead of resizing to original size.",
    )
    parser.add_argument(
        "--preview-max-side",
        type=int,
        default=1800,
        help="Largest preview dimension shown while selecting crops.",
    )
    parser.add_argument(
        "--auto-margin",
        type=float,
        default=0.08,
        help="Margin fraction to add around click-suggested subject boxes.",
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
    settings = CropSettings(
        upscale_to_original=not args.no_upscale,
        preview_max_side=args.preview_max_side,
        auto_margin=args.auto_margin,
    )

    if not images:
        print(f"No supported photos found in {input_dir}")
        print(f"Supported extensions: {supported_extensions_text()}")
        return

    print(f"Found {len(images)} images in {input_dir}")
    print(f"Saving cropped photos to {output_dir}")
    print(
        "For each image:\n"
        " 1) Click the bird to suggest a crop, or drag a rectangle manually.\n"
        "    Press 'c' to propose crop, 's' to skip, 'q' to quit.\n"
        " 2) Preview shows final aspect-locked crop.\n"
        "    Press 'y' = accept and save, 'r' = redraw, 's' = skip, 'q' = quit."
    )

    for img_path in images:
        status = process_image(img_path, output_dir, settings)
        if status == "QUIT":
            print("Stopping at user request.")
            break


if __name__ == "__main__":
    main()
