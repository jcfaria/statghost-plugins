"""Regenerate media/statghost.svg from STATghost brand PNG (activity-bar safe)."""
from __future__ import annotations

from pathlib import Path

from PIL import Image

VSCODE = Path(__file__).resolve().parents[1]
OUT = VSCODE / 'media' / 'statghost.svg'
SIZE = 24
# Opaque single fill — VS Code activity-bar icons are CSS-masked (alpha only).
FILL = '#000'


def brand_master() -> Path:
    candidates = [
        VSCODE.parents[2].parent / 'statghost' / 'src' / 'icons' / 'png' / 'statghost' / 'statghost_256.png',
        VSCODE.parents[2] / 'statghost' / 'src' / 'icons' / 'png' / 'statghost' / 'statghost_256.png',
        VSCODE / 'media' / 'statghost_ref.png',
    ]
    for path in candidates:
        if path.is_file():
            return path
    raise SystemExit('missing brand master (statghost_256.png or media/statghost_ref.png)')


def silhouette_from_brand(src: Path, size: int) -> Image.Image:
    im = Image.open(src).convert('RGBA')
    w, h = im.size
    mask = Image.new('L', (w, h), 0)
    px = im.load()
    mp = mask.load()
    for y in range(h):
        for x in range(w):
            if px[x, y][3] > 64:
                mp[x, y] = 255
    bbox = mask.getbbox()
    if not bbox:
        raise SystemExit(f'no opaque pixels in {src}')
    mask = mask.crop(bbox)
    mw, mh = mask.size
    side = max(mw, mh)
    sq = Image.new('L', (side, side), 0)
    sq.paste(mask, ((side - mw) // 2, (side - mh) // 2))
    small = sq.resize((size, size), Image.Resampling.LANCZOS)
    m = small.load()
    for y in range(size):
        for x in range(size):
            m[x, y] = 255 if m[x, y] > 32 else 0
    return small


def rects_from_mask(mask: Image.Image) -> list[tuple[int, int, int, int]]:
    size = mask.size[0]
    m = mask.load()
    rects: list[tuple[int, int, int, int]] = []
    for y in range(size):
        x = 0
        while x < size:
            if m[x, y]:
                x0 = x
                while x < size and m[x, y]:
                    x += 1
                rects.append((x0, y, x - x0, 1))
            else:
                x += 1
    return rects


def write_svg(rects: list[tuple[int, int, int, int]], out: Path) -> None:
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}" fill="{FILL}">',
        '  <g fill-rule="evenodd" clip-rule="evenodd">',
    ]
    for x, y, w, h in rects:
        lines.append(f'    <rect x="{x}" y="{y}" width="{w}" height="{h}"/>')
    lines.extend(['  </g>', '</svg>', ''])
    out.write_text('\n'.join(lines), encoding='utf-8')


def main() -> None:
    brand = brand_master()
    mask = silhouette_from_brand(brand, SIZE)
    rects = rects_from_mask(mask)
    write_svg(rects, OUT)
    print(f'wrote {OUT} ({len(rects)} rects) from {brand.name}')


if __name__ == '__main__':
    main()
