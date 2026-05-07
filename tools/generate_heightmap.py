#!/usr/bin/env python3
"""
Generate a 16-bit PNG heightmap for a MC1 level using the mc1-terrain-gen binary.

The terrain is procedurally generated from seed parameters — there is no stored
heightmap in the level files.  This script extracts the GEN_MAP params from the
level, invokes the C++ terrain generator (all 17 pipeline stages), then converts
its PGM output to a 16-bit grayscale PNG suitable for Godot's HTerrain plugin.

Usage:
    python generate_heightmap.py [--level N] [--all] [--stages N]
"""
import argparse
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("pip install Pillow")

from common import (
    extract_level_bytes, parse_gen_map,
    TERRAIN_BIN, LEVELS_DAT, LEVELS_TAB, OUT_HEIGHTS,
)

NUM_LEVELS   = 70
MAP_SIZE     = 256
MAX_HEIGHT   = 196   # engine height cap; maps to white in PGM


def pgm_to_png16(pgm_bytes: bytes) -> Image.Image:
    """Convert a P5 PGM to a 16-bit grayscale PIL image, scaling 0..196 → 0..65535."""
    lines = pgm_bytes.split(b"\n", 3)
    assert lines[0] == b"P5"
    w, h = map(int, lines[1].split())
    maxval = int(lines[2])
    raw = lines[3]
    pixels = [int(b) * 65535 // maxval for b in raw[: w * h]]
    img = Image.new("I", (w, h))
    img.putdata(pixels)
    return img.convert("I;16")


def generate_one(level_num: int, stages: int = 17) -> Path:
    raw = extract_level_bytes(level_num)
    gm = parse_gen_map(raw)

    OUT_HEIGHTS.mkdir(parents=True, exist_ok=True)
    out_png = OUT_HEIGHTS / f"level_{level_num:02d}.png"

    with tempfile.NamedTemporaryFile(suffix=".pgm", delete=False) as tmp:
        pgm_path = tmp.name

    cmd = [
        str(TERRAIN_BIN),
        "--levels-dat", str(LEVELS_DAT),
        "--levels-tab", str(LEVELS_TAB),
        "--level", str(level_num),
        "--stages", str(stages),
        "--output", pgm_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  terrain-gen failed: {result.stderr.strip()}", file=sys.stderr)
        return None

    pgm_bytes = Path(pgm_path).read_bytes()
    Path(pgm_path).unlink(missing_ok=True)

    img = pgm_to_png16(pgm_bytes)
    img.save(out_png)
    return out_png


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--stages", type=int, default=17,
                    help="Pipeline stages to run (1-17, default 17=full)")
    args = ap.parse_args()

    if not TERRAIN_BIN.exists():
        sys.exit(f"terrain-gen binary not found at {TERRAIN_BIN}\n"
                 "cd mc1-tools/terrain-gen && cmake -B build && cmake --build build")
    if not LEVELS_DAT.exists():
        sys.exit(f"LEVELS.DAT not found at {LEVELS_DAT}")

    levels = range(NUM_LEVELS) if args.all else \
             ([args.level] if args.level is not None else [0])

    for n in levels:
        print(f"Level {n:02d}...", end=" ", flush=True)
        out = generate_one(n, args.stages)
        if out:
            print(f"→ {out.name} ({MAP_SIZE}×{MAP_SIZE} 16-bit PNG)")
        else:
            print("FAILED")


if __name__ == "__main__":
    main()
