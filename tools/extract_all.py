#!/usr/bin/env python3
"""
Run the full MC1 extraction pipeline.

    python extract_all.py [--levels] [--textures] [--heightmaps] [--all-levels]

With no flags, extracts: palette, level 0 JSON, level 0 heightmap, first 20 textures.
--all-levels processes all 70 levels (takes ~2 minutes for heightmaps).
"""
import argparse
import subprocess
import sys
from pathlib import Path


def run(script: str, *args):
    cmd = [sys.executable, str(Path(__file__).parent / script), *args]
    print(f"\n{'='*60}")
    print(f"  {' '.join(cmd)}")
    print(f"{'='*60}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"  WARNING: {script} exited with code {result.returncode}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--levels",     action="store_true", help="Extract level JSON only")
    ap.add_argument("--textures",   action="store_true", help="Extract textures only")
    ap.add_argument("--heightmaps", action="store_true", help="Generate heightmaps only")
    ap.add_argument("--all-levels", action="store_true", help="Process all 70 levels")
    args = ap.parse_args()

    do_all = not (args.levels or args.textures or args.heightmaps)

    # Palette — always
    run("extract_palette.py")

    # Level JSON
    if do_all or args.levels:
        if args.all_levels:
            run("extract_level.py", "--all")
        else:
            run("extract_level.py", "--level", "0")

    # Textures
    if do_all or args.textures:
        run("extract_textures.py")   # first 20 tiles by default

    # Heightmaps
    if do_all or args.heightmaps:
        if args.all_levels:
            run("generate_heightmap.py", "--all")
        else:
            run("generate_heightmap.py", "--level", "0")

    print("\nDone. Assets written to godot-mc/assets/")


if __name__ == "__main__":
    main()
