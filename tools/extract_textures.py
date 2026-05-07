#!/usr/bin/env python3
"""
Extract MC1 terrain texture tiles from TMAPS0-0.DAT → PNG images.

Each TAB entry maps to one RNC-compressed block in the DAT.  The block
decompresses to: 6-byte header {u8 unk1, u8 unk2, u16 w, u16 h} + w×h palette
indices.  Pixels are coloured using the day palette from PAL0-0.DAT.

Usage:
    python extract_textures.py [--index N]   # single tile
    python extract_textures.py [--all]       # all ~530 tiles (slow)
"""
import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("pip install Pillow")

from common import (
    extract_texture_block, parse_tmaps_tab,
    load_palette, OUT_TEXTURES, TMAPS_DAT, TMAPS_TAB, PAL_DAT,
)


def render_tile(w: int, h: int, pixels: bytes,
                palette: list[tuple[int, int, int]]) -> Image.Image:
    img = Image.new("RGB", (w, h))
    rgb_pixels = [palette[b] for b in pixels]
    img.putdata(rgb_pixels)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", type=int, default=None, help="Single tile index")
    ap.add_argument("--all", action="store_true", help="Extract all tiles")
    args = ap.parse_args()

    if not TMAPS_DAT.exists():
        sys.exit(f"TMAPS0-0.DAT not found at {TMAPS_DAT}")

    OUT_TEXTURES.mkdir(parents=True, exist_ok=True)
    palette = load_palette(PAL_DAT)

    entries = parse_tmaps_tab(TMAPS_TAB)
    n_entries = len(entries)

    indices = range(n_entries) if args.all else \
              ([args.index] if args.index is not None else range(min(20, n_entries)))

    ok = 0
    for i in indices:
        result = extract_texture_block(i, TMAPS_DAT, TMAPS_TAB)
        if result is None:
            continue
        w, h, pixels = result
        img = render_tile(w, h, pixels, palette)
        out = OUT_TEXTURES / f"tile_{i:04d}.png"
        img.save(out)
        print(f"  tile {i:04d}: {w}×{h} → {out.name}")
        ok += 1

    print(f"Done: {ok} tiles extracted to {OUT_TEXTURES}")


if __name__ == "__main__":
    main()
