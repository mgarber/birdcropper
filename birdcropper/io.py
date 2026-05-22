from __future__ import annotations

import argparse
from pathlib import Path
from tkinter import Tk, filedialog

from birdcropper.photo import is_supported_photo


def choose_input_dir(title: str = "Choose the folder with bird photos") -> Path | None:
    """Open a native folder picker and return the selected directory."""
    root = Tk()
    root.withdraw()
    root.update()
    selected = filedialog.askdirectory(title=title, mustexist=True)
    root.destroy()

    if not selected:
        return None
    return Path(selected).expanduser().resolve()


def image_paths(input_dir: Path) -> list[Path]:
    """Return supported photo paths in a stable order."""
    return sorted(
        p for p in input_dir.iterdir()
        if p.is_file() and is_supported_photo(p)
    )


def output_dir_for(input_dir: Path, name: str = "cropped_out") -> Path:
    output_dir = input_dir / name
    output_dir.mkdir(exist_ok=True)
    return output_dir


def input_dir_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "input_dir",
        nargs="?",
        type=Path,
        help="Folder containing photos. If omitted, a folder picker opens.",
    )


def resolve_input_dir(input_dir: Path | None) -> Path | None:
    if input_dir is None:
        return choose_input_dir()
    return input_dir.expanduser().resolve()
