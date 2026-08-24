#!/usr/bin/env python3
"""Build shared/res/{16,24,32}px — monochrome alpha masks from existing PNG.

Strips hue. RGB is black; shape lives in alpha. Hosts tint to graphite /
closed-white / mid-gray from the theme (or the user icons.fg pref).

Run from repo root:
  python shared/tools/build_res.py
"""
from __future__ import annotations

import os
import shutil
import sys

from PIL import Image

HERE = os.path.dirname(os.path.realpath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(REPO, 'shared', 'res')
SIZES = (16, 24, 32)

# Closed white / mid gray / graphite — baked copies for hosts that load
# a palette folder instead of runtime tint.
PALETTES = {
    'white': (0xC4, 0xC4, 0xC4),
    'gray': (0x8A, 0x8A, 0x8A),
    'graphite': (0x3A, 0x3A, 0x3A),
}

SOURCES = (
    os.path.join(REPO, 'shared', 'png'),
    os.path.join(REPO, 'plugins', 'cudatext', 'cuda_statghost', 'png'),
    os.path.join(REPO, 'plugins', 'cudatext', 'cuda_statghost', 'icons'),
    os.path.join(REPO, 'plugins', 'vscode', 'media', 'icons'),
    os.path.join(REPO, 'plugins', 'cudatext', 'w_todo', 'icons'),
)

# Hand-crafted per-size masters: shared/src/<stem>/{16,24,32}.png
# When present, used as-is instead of resizing the harvested PNG.
EXACT_SRC = os.path.join(REPO, 'shared', 'src')

HOST_COPIES = (
    os.path.join(REPO, 'plugins', 'cudatext', 'cuda_statghost', 'res'),
    os.path.join(REPO, 'plugins', 'vscode', 'media', 'res'),
)

SKIP_PREFIX = ('statghost_256', 'statghost_graphite_256')

README = '''STATghost plugin glyphs — canonical stash
=========================================

All chrome / brand / stash icons live here. Hosts copy this tree
(`cuda_statghost/res/`, `plugins/vscode/media/res/`). Do not add a
second icon set per editor.

Layout
------
  16px/ 24px/ 32px/     alpha masks (RGB black, shape in alpha)
  white/16px|24px|32px  closed white  #C4C4C4
  gray/16px|24px|32px   mid gray      #8A8A8A
  graphite/…            graphite      #3A3A3A

Rebuild after changing a source PNG (shared/png, shared/src/<stem>/{16,24,32}.png, Tinn stash, …):

  python shared/tools/build_res.py

Hosts
-----
CudaText toolbar/side: load mask + tint (icons.py). Pref icons.fg =
  auto | light (white) | dark (graphite) | gray | theme.
VS Code panel: same pref; CSS mask uses --sg-cell-fg.

Lab stash `plugins/cudatext/w_todo/icons/` stays as Tinn extract
reference. Production chrome does not load it.
'''


def _collect():
    """basename → path of the largest PNG (area, then mtime)."""
    best = {}
    for root in SOURCES:
        if not os.path.isdir(root):
            continue
        for dirpath, _, files in os.walk(root):
            for name in files:
                if not name.lower().endswith('.png'):
                    continue
                stem = os.path.splitext(name)[0]
                if any(stem.startswith(p) for p in SKIP_PREFIX):
                    continue
                path = os.path.join(dirpath, name)
                try:
                    with Image.open(path) as im:
                        area = im.size[0] * im.size[1]
                except OSError:
                    continue
                prev = best.get(name)
                if prev is None or area > prev[0]:
                    best[name] = (area, path)
    return {name: path for name, (_a, path) in best.items()}


def _to_mask(im: Image.Image) -> Image.Image:
    im = im.convert('RGBA')
    r, g, b, a = im.split()
    amin, amax = a.getextrema()
    if amin == 255 and amax == 255:
        luma = im.convert('L')
        mean = sum(luma.getdata()) / float(max(1, luma.size[0] * luma.size[1]))
        if mean > 127:
            a = Image.eval(luma, lambda p: 255 - p)
        else:
            a = luma
    black = Image.new('L', im.size, 0)
    return Image.merge('RGBA', (black, black, black, a))


def _resize(im: Image.Image, px: int) -> Image.Image:
    if im.size == (px, px):
        return im
    src = min(im.size)
    resample = Image.Resampling.NEAREST if src <= 16 and px > src else Image.Resampling.LANCZOS
    return im.resize((px, px), resample)


def _exact_mask(name: str, px: int) -> Image.Image | None:
    stem = os.path.splitext(name)[0]
    path = os.path.join(EXACT_SRC, stem, '%d.png' % px)
    if not os.path.isfile(path):
        return None
    with Image.open(path) as raw:
        mask = _to_mask(raw)
    if mask.size != (px, px):
        return _resize(mask, px)
    return mask


def _tint(mask: Image.Image, rgb) -> Image.Image:
    r, g, b = rgb
    a = mask.split()[3]
    return Image.merge('RGBA', (
        Image.new('L', mask.size, r),
        Image.new('L', mask.size, g),
        Image.new('L', mask.size, b),
        a,
    ))


def main():
    glyphs = _collect()
    if not glyphs:
        print('no source PNGs', file=sys.stderr)
        return 1

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT, exist_ok=True)

    for px in SIZES:
        os.makedirs(os.path.join(OUT, '%dpx' % px), exist_ok=True)
        for pal in PALETTES:
            os.makedirs(os.path.join(OUT, pal, '%dpx' % px), exist_ok=True)

    for name, src in sorted(glyphs.items()):
        with Image.open(src) as raw:
            mask = _to_mask(raw)
        for px in SIZES:
            sized = _exact_mask(name, px)
            if sized is None:
                sized = _resize(mask, px)
            sized.save(os.path.join(OUT, '%dpx' % px, name), 'PNG')
            for pal, rgb in PALETTES.items():
                _tint(sized, rgb).save(
                    os.path.join(OUT, pal, '%dpx' % px, name), 'PNG',
                )

    with open(os.path.join(OUT, 'README.txt'), 'w', encoding='utf-8') as fh:
        fh.write(README)

    for dest in HOST_COPIES:
        if os.path.isdir(dest):
            shutil.rmtree(dest)
        shutil.copytree(OUT, dest)

    print('glyphs', len(glyphs))
    print('wrote', OUT)
    for dest in HOST_COPIES:
        print('copied', dest)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
