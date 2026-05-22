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

RAW files are decoded for cropping and saved as JPEG outputs.

## Crop controls

For each photo:

1. Drag a rectangle around the bird.
2. Press `c` to confirm the selection, `s` to skip, or `q` to quit.
3. The preview shows the final aspect-matched crop.
4. Press `y` to save, `r` to redraw, `s` to skip, or `q` to quit.

## Environment

```bash
conda env create -f bridcrop_env.yaml
conda activate birdcrop
```

