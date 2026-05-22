from __future__ import annotations


def adjust_bbox_to_aspect(
    bbox: tuple[int, int, int, int],
    orig_size: tuple[int, int],
) -> tuple[int, int, int, int]:
    """
    Adjust a bbox so that it has the original image aspect ratio.

    The box keeps the user's selected center as much as possible while staying
    inside the image bounds.
    """
    left, top, right, bottom = bbox
    img_w, img_h = orig_size

    orig_ar = img_w / img_h
    sel_w = right - left
    sel_h = bottom - top

    cx = (left + right) / 2.0
    cy = (top + bottom) / 2.0

    new_w1 = sel_w
    new_h1 = sel_w / orig_ar

    new_h2 = sel_h
    new_w2 = sel_h * orig_ar

    area_sel = sel_w * sel_h
    area1 = new_w1 * new_h1
    area2 = new_w2 * new_h2

    if abs(area1 - area_sel) < abs(area2 - area_sel):
        new_w, new_h = new_w1, new_h1
    else:
        new_w, new_h = new_w2, new_h2

    new_w = min(new_w, img_w)
    new_h = min(new_h, img_h)

    left_new = cx - new_w / 2.0
    right_new = cx + new_w / 2.0
    top_new = cy - new_h / 2.0
    bottom_new = cy + new_h / 2.0

    if left_new < 0:
        shift = -left_new
        left_new += shift
        right_new += shift
    if right_new > img_w:
        shift = right_new - img_w
        left_new -= shift
        right_new -= shift
    if top_new < 0:
        shift = -top_new
        top_new += shift
        bottom_new += shift
    if bottom_new > img_h:
        shift = bottom_new - img_h
        top_new -= shift
        bottom_new -= shift

    left_new = int(round(max(0, left_new)))
    top_new = int(round(max(0, top_new)))
    right_new = int(round(min(img_w, right_new)))
    bottom_new = int(round(min(img_h, bottom_new)))

    return (left_new, top_new, right_new, bottom_new)


def center_crop_box(
    image_size: tuple[int, int],
    factor: float,
) -> tuple[int, int, int, int]:
    """Return a centered crop box for the given size and crop factor."""
    if not 0 < factor <= 1:
        raise ValueError("crop factor must be greater than 0 and no more than 1")

    w, h = image_size
    new_w = int(w * factor)
    new_h = int(h * factor)

    left = (w - new_w) // 2
    top = (h - new_h) // 2
    right = left + new_w
    bottom = top + new_h

    return (left, top, right, bottom)

