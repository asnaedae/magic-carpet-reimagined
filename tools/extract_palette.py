#!/usr/bin/env python3
"""Extract the MC1 day palette → palette.png (256×1) and palette.json."""
import json
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("pip install Pillow")

from common import load_palette, ASSETS, PAL_DAT


def main():
    print(f"Loading palette from {PAL_DAT}")
    pal = load_palette(PAL_DAT)

    ASSETS.mkdir(parents=True, exist_ok=True)

    # 256×1 PNG strip
    img = Image.new("RGB", (256, 1))
    img.putdata(pal)
    out_png = ASSETS / "palette.png"
    img.save(out_png)
    print(f"Wrote {out_png}")

    # JSON for easy inspection
    out_json = ASSETS / "palette.json"
    out_json.write_text(json.dumps(
        [{"index": i, "r": r, "g": g, "b": b} for i, (r, g, b) in enumerate(pal)],
        indent=2,
    ))
    print(f"Wrote {out_json}")


if __name__ == "__main__":
    main()
