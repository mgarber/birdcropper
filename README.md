# birdcropper

Interactive crop tools for bird photos, including high-resolution telephoto
images.

## Run the interactive cropper

```bash
python interactive_crop.py
```

When the program starts, choose the folder that contains the photos. Cropped
images are saved into a `cropped_out` folder inside the selected photo folder.

Supported input formats:

- JPEG: `.jpg`, `.jpeg`
- PNG: `.png`
- TIFF: `.tif`, `.tiff`
- Canon RAW: `.cr2`, `.cr3`

RAW files need the optional `rawpy` package. They are decoded for cropping and
saved as JPEG outputs.

## Crop controls

For each photo:

1. Click on the bird to let the program suggest a crop.
2. If the suggestion is wrong, drag a rectangle manually.
3. Press `c` to confirm the shown selection, `s` to skip, or `q` to quit.
4. The preview shows the final aspect-matched crop.
5. Press `y` to save, `r` to redraw, `s` to skip, or `q` to quit.

Suggested crops are drawn in yellow. Manual drag selections are drawn in cyan.

The automatic suggestion is a lightweight estimate from the clicked point. It
works best when the bird clearly differs from the background.

## Environment

```bash
conda env create -f bridcrop_env.yaml
conda activate birdcrop
```

If the environment already exists:

```bash
conda env update -f bridcrop_env.yaml --prune
conda activate birdcrop
```

## Optional Canon RAW Support

Start by testing the program on JPEG, PNG, or TIFF photos. After that works,
try installing RAW support:

```bash
conda activate birdcrop
python -m pip install rawpy
```

If `rawpy` does not install cleanly on your machine, the regular photo formats
will still work.
