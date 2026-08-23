#!/usr/bin/env python3
"""Draw outline-only ls, remove_objects, and print glyphs.

Sources land in shared/png/ at 32px; build_res.py harvests and scales to
16/24/32 for both plugin hosts.

Run from repo root:
  python shared/tools/draw_outline_icons.py
"""
from __future__ import annotations

import math
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.realpath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(REPO, 'shared', 'png')
SIZE = 32


def _stroke(px: int) -> int:
    """~2px stroke at 16px canvas, scale proportionally."""
    return max(1, round(2 * px / 16))


def _blank(px: int) -> Image.Image:
    return Image.new('RGBA', (px, px), (0, 0, 0, 0))


def _draw_rect_outline(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float, float, float],
    *,
    stroke: int,
    alpha: int,
    angle: float = 0.0,
) -> None:
    """Axis-aligned or rotated rectangle outline on transparent canvas."""
    x0, y0, x1, y1 = xy
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    w, h = x1 - x0, y1 - y0
    rad = math.radians(angle)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    corners = [
        (-w / 2, -h / 2),
        (w / 2, -h / 2),
        (w / 2, h / 2),
        (-w / 2, h / 2),
    ]
    pts = []
    for dx, dy in corners:
        rx = cx + dx * cos_a - dy * sin_a
        ry = cy + dx * sin_a + dy * cos_a
        pts.append((rx, ry))
    color = (255, 255, 255, alpha)
    for i in range(4):
        draw.line([pts[i], pts[(i + 1) % 4]], fill=color, width=stroke)


def _draw_circle_outline(
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    r: float,
    *,
    stroke: int,
    alpha: int,
) -> None:
    color = (255, 255, 255, alpha)
    draw.ellipse(
        (cx - r, cy - r, cx + r, cy + r),
        outline=color,
        width=stroke,
    )


def draw_ls(px: int) -> Image.Image:
    """Three slightly overlapping square outlines — list/objects metaphor."""
    im = _blank(px)
    draw = ImageDraw.Draw(im)
    s = _stroke(px)
    # Back → front: lighter to stronger alpha for depth.
    boxes = (
        ((3.0, px * 0.52, px * 0.52, px - 3.0), 12, 175),   # bottom-left
        ((px * 0.28, px * 0.30, px * 0.72, px * 0.74), 0, 205),  # center
        ((px * 0.48, 3.0, px - 3.0, px * 0.48), -12, 255),  # top-right
    )
    for (x0, y0, x1, y1), angle, alpha in boxes:
        _draw_rect_outline(draw, (x0, y0, x1, y1), stroke=s, alpha=alpha, angle=angle)
    return im


def draw_remove_objects(px: int) -> Image.Image:
    """Two overlapping geometric outlines — square + circle."""
    im = _blank(px)
    draw = ImageDraw.Draw(im)
    s = _stroke(px)
    pad = px * 0.14
    side = px * 0.50
    _draw_rect_outline(
        draw,
        (pad, px - pad - side, pad + side, px - pad),
        stroke=s,
        alpha=200,
        angle=-8,
    )
    r = px * 0.26
    _draw_circle_outline(
        draw,
        px - pad - r * 0.85,
        pad + r * 1.05,
        r,
        stroke=s,
        alpha=255,
    )
    return im


def draw_print(px: int) -> Image.Image:
    """Glasses frame outline only — no lens fill."""
    im = _blank(px)
    draw = ImageDraw.Draw(im)
    s = _stroke(px)
    color = (255, 255, 255, 255)

    # Lens frame geometry (mirrors legacy print.png proportions).
    lens_w = px * 0.30
    lens_h = px * 0.28
    gap = px * 0.08
    top = px * 0.36
    left_x = px * 0.14
    right_x = px - left_x - lens_w
    bot = top + lens_h

    def lens_frame(x0: float) -> list[tuple[float, float]]:
        return [
            (x0, top),
            (x0 + lens_w, top),
            (x0 + lens_w, bot),
            (x0, bot),
            (x0, top),
        ]

    for pts in (lens_frame(left_x), lens_frame(right_x)):
        draw.line(pts, fill=color, width=s)

    # Bridge
    draw.line(
        [(left_x + lens_w, top + lens_h * 0.42), (right_x, top + lens_h * 0.42)],
        fill=color,
        width=s,
    )

    # Temple arms from outer top corners (legacy print.png geometry).
    arm_len = px * 0.24
    for corner_x, outward in ((left_x, -1.0), (right_x + lens_w, 1.0)):
        draw.line(
            [
                (corner_x, top),
                (corner_x + outward * arm_len * 0.65, top - arm_len),
            ],
            fill=color,
            width=s,
        )

    return im


GLYPHS = {
    'ls.png': draw_ls,
    'remove_objects.png': draw_remove_objects,
    'print.png': draw_print,
}


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    for name, fn in GLYPHS.items():
        path = os.path.join(OUT, name)
        fn(SIZE).save(path, 'PNG')
        print('wrote', path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
