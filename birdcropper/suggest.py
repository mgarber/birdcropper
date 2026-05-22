from __future__ import annotations

from collections import deque

import numpy as np


def suggest_subject_bbox(
    image: np.ndarray,
    click_xy: tuple[float, float],
    margin_fraction: float = 0.08,
) -> tuple[int, int, int, int]:
    """
    Estimate a subject box from a clicked point in an RGB preview image.

    This intentionally uses a lightweight contrast-based heuristic. It works
    best when the clicked subject differs from the surrounding background.
    """
    h, w = image.shape[:2]
    click_x = int(round(click_xy[0]))
    click_y = int(round(click_xy[1]))
    click_x = min(max(click_x, 0), w - 1)
    click_y = min(max(click_y, 0), h - 1)

    arr = image.astype(np.float32) / 255.0
    radius = max(40, int(min(w, h) * 0.22))

    x0 = max(0, click_x - radius)
    x1 = min(w, click_x + radius + 1)
    y0 = max(0, click_y - radius)
    y1 = min(h, click_y + radius + 1)
    window = arr[y0:y1, x0:x1]

    bg_color = _estimate_border_color(window)
    bg_luma = _luminance(bg_color)
    luma = _luminance(window)

    color_diff = np.linalg.norm(window - bg_color, axis=2)
    luma_diff = np.abs(luma - bg_luma)
    score = color_diff + luma_diff

    local_x = click_x - x0
    local_y = click_y - y0
    component = _best_component(score, local_x, local_y)
    if component is None:
        return _fallback_box(w, h, click_x, click_y)

    rows, cols = np.where(component)
    left = int(cols.min()) + x0
    right = int(cols.max()) + x0 + 1
    top = int(rows.min()) + y0
    bottom = int(rows.max()) + y0 + 1

    return _add_margin((left, top, right, bottom), (w, h), margin_fraction)


def _estimate_border_color(window: np.ndarray) -> np.ndarray:
    top = window[0, :, :]
    bottom = window[-1, :, :]
    left = window[:, 0, :]
    right = window[:, -1, :]
    border = np.concatenate([top, bottom, left, right], axis=0)
    return np.median(border, axis=0)


def _luminance(rgb: np.ndarray) -> np.ndarray:
    return (rgb[..., 0] * 0.2126) + (rgb[..., 1] * 0.7152) + (rgb[..., 2] * 0.0722)


def _best_component(
    score: np.ndarray,
    seed_x: int,
    seed_y: int,
) -> np.ndarray | None:
    h, w = score.shape
    total = h * w
    min_area = max(12, int(total * 0.00008))
    max_area = max(min_area, int(total * 0.35))

    for percentile in (55, 60, 65, 70, 75, 80, 85, 90):
        threshold = float(np.percentile(score, percentile))
        mask = score >= threshold
        seed = _seed_near_click(mask, seed_x, seed_y)
        if seed is None:
            continue

        component = _connected_component(mask, seed)
        area = int(component.sum())
        if min_area <= area <= max_area:
            return component

    return None


def _seed_near_click(mask: np.ndarray, seed_x: int, seed_y: int) -> tuple[int, int] | None:
    h, w = mask.shape
    if mask[seed_y, seed_x]:
        return seed_x, seed_y

    search_radius = max(3, int(min(w, h) * 0.02))
    x0 = max(0, seed_x - search_radius)
    x1 = min(w, seed_x + search_radius + 1)
    y0 = max(0, seed_y - search_radius)
    y1 = min(h, seed_y + search_radius + 1)
    nearby = np.argwhere(mask[y0:y1, x0:x1])
    if nearby.size == 0:
        return None

    distances = (nearby[:, 1] + x0 - seed_x) ** 2 + (nearby[:, 0] + y0 - seed_y) ** 2
    best = nearby[int(np.argmin(distances))]
    return int(best[1] + x0), int(best[0] + y0)


def _connected_component(mask: np.ndarray, seed: tuple[int, int]) -> np.ndarray:
    h, w = mask.shape
    seed_x, seed_y = seed
    visited = np.zeros_like(mask, dtype=bool)
    queue: deque[tuple[int, int]] = deque([(seed_x, seed_y)])
    visited[seed_y, seed_x] = True

    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if nx < 0 or nx >= w or ny < 0 or ny >= h:
                continue
            if visited[ny, nx] or not mask[ny, nx]:
                continue
            visited[ny, nx] = True
            queue.append((nx, ny))

    return visited


def _add_margin(
    bbox: tuple[int, int, int, int],
    image_size: tuple[int, int],
    margin_fraction: float,
) -> tuple[int, int, int, int]:
    left, top, right, bottom = bbox
    img_w, img_h = image_size
    box_w = right - left
    box_h = bottom - top
    margin = max(4, int(round(min(box_w, box_h) * margin_fraction)))

    return (
        max(0, left - margin),
        max(0, top - margin),
        min(img_w, right + margin),
        min(img_h, bottom + margin),
    )


def _fallback_box(
    img_w: int,
    img_h: int,
    click_x: int,
    click_y: int,
) -> tuple[int, int, int, int]:
    side = max(40, int(min(img_w, img_h) * 0.18))
    half = side // 2
    return (
        max(0, click_x - half),
        max(0, click_y - half),
        min(img_w, click_x + half),
        min(img_h, click_y + half),
    )
