#!/usr/bin/env python3
"""
Extract level data from MC1 LEVELS.DAT → JSON.

Usage:
    python extract_level.py [--level N] [--all]
"""
import argparse
import json
import sys
from pathlib import Path

from common import (
    extract_level_bytes, parse_gen_map, parse_entities,
    LEVELS_DAT, LEVELS_TAB, OUT_LEVELS,
)

NUM_LEVELS = 70


def extract_one(level_num: int) -> dict:
    raw = extract_level_bytes(level_num)
    gen_map = parse_gen_map(raw)
    entities = parse_entities(raw)
    return {
        "level": level_num,
        "gen_map": gen_map,
        "entity_count": len(entities),
        "entities": entities,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", type=int, default=None, help="Level number (0-69)")
    ap.add_argument("--all", action="store_true", help="Extract all 70 levels")
    args = ap.parse_args()

    if not LEVELS_DAT.exists():
        sys.exit(f"LEVELS.DAT not found at {LEVELS_DAT}\n"
                 "Set LEVELS_DAT in common.py to point to your MC1 install.")

    OUT_LEVELS.mkdir(parents=True, exist_ok=True)

    levels = range(NUM_LEVELS) if args.all else ([args.level] if args.level is not None else [0])

    for n in levels:
        print(f"Extracting level {n:02d}...", end=" ", flush=True)
        try:
            data = extract_one(n)
        except Exception as e:
            print(f"FAILED: {e}")
            continue
        out = OUT_LEVELS / f"level_{n:02d}.json"
        out.write_text(json.dumps(data, indent=2))
        print(f"{data['entity_count']} entities → {out.name}")


if __name__ == "__main__":
    main()
