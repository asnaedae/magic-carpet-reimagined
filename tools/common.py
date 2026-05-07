"""Shared utilities for Magic Carpet 1 data extraction."""
import struct
import subprocess
import tempfile
import os
from pathlib import Path

# ── Tool binaries ──────────────────────────────────────────────────────────────
_TOOLS = Path(__file__).parent.parent.parent
RNC_BIN      = _TOOLS / "mc1-tools/rnc-decompress/build/rnc-decompress"
TERRAIN_BIN  = _TOOLS / "mc1-tools/terrain-gen/build/mc1-terrain-gen"

# ── Source data paths ──────────────────────────────────────────────────────────
# Levels: use the original GOG install (RNC-compressed, unmodified).
# The sandbox copy has been patched by mc1-to-mc2-levels.py.
GOG_CD       = Path("/Applications/Magic Carpet Plus™.app/Contents/Resources/game/CARPET.CD")
LEVELS_DAT   = GOG_CD / "LEVELS/LEVELS.DAT"
LEVELS_TAB   = GOG_CD / "LEVELS/LEVELS.TAB"

# Textures, palette, sprites: from the extracted sandbox DATA directory.
_SANDBOX     = _TOOLS / "upstream-mc2/build/Debug/inst/mc1-bin/CD_Files/DATA"
TMAPS_DAT    = _SANDBOX / "TMAPS0-0.DAT"
TMAPS_TAB    = _SANDBOX / "TMAPS0-0.TAB"
PAL_DAT      = _SANDBOX / "PAL0-0.DAT"   # Day palette (6-bit VGA, RNC-compressed)
BUILD_DAT    = _SANDBOX / "BUILD0-0.DAT"
BUILD_TAB    = _SANDBOX / "BUILD0-0.TAB"

# ── Output paths (relative to this file's parent = godot-mc/) ─────────────────
ASSETS       = Path(__file__).parent.parent / "assets"
OUT_TEXTURES = ASSETS / "textures"
OUT_HEIGHTS  = ASSETS / "heightmaps"
OUT_LEVELS   = ASSETS / "levels"


def decompress_rnc(path: Path) -> bytes:
    """Decompress an RNC1 file; return raw bytes. Pass-through if not RNC."""
    data = path.read_bytes()
    if data[:4] != b"RNC\x01":
        return data
    with tempfile.NamedTemporaryFile(suffix=".raw", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        subprocess.run(
            [str(RNC_BIN), str(path), tmp_path],
            check=True, capture_output=True,
        )
        return Path(tmp_path).read_bytes()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def decompress_rnc_bytes(data: bytes) -> bytes:
    """Decompress raw RNC1 bytes; return decompressed bytes."""
    if data[:4] != b"RNC\x01":
        return data
    with tempfile.NamedTemporaryFile(suffix=".rnc", delete=False) as fi:
        fi.write(data)
        fi_path = fi.name
    with tempfile.NamedTemporaryFile(suffix=".raw", delete=False) as fo:
        fo_path = fo.name
    try:
        subprocess.run(
            [str(RNC_BIN), fi_path, fo_path],
            check=True, capture_output=True,
        )
        return Path(fo_path).read_bytes()
    finally:
        for p in (fi_path, fo_path):
            if os.path.exists(p):
                os.unlink(p)


def read_u32_le(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def read_u16_le(data: bytes, offset: int) -> int:
    return struct.unpack_from("<H", data, offset)[0]


def load_palette(path: Path = PAL_DAT) -> list[tuple[int, int, int]]:
    """Load a VGA 6-bit palette file → list of 256 (R, G, B) 8-bit tuples."""
    raw = decompress_rnc(path)
    assert len(raw) >= 768, f"Palette too short: {len(raw)} bytes"
    pal = []
    for i in range(256):
        r, g, b = raw[i * 3], raw[i * 3 + 1], raw[i * 3 + 2]
        # VGA 6-bit: multiply by 4 to scale to 8-bit
        pal.append((min(r * 4, 255), min(g * 4, 255), min(b * 4, 255)))
    return pal


# ── LEVELS.DAT parser ──────────────────────────────────────────────────────────

LEVEL_SIZE   = 38_812   # decompressed bytes per level
GEN_MAP_FIELDS = [
    ("pre_header", 0x00),
    ("seed",       0x04),
    ("offset",     0x08),
    ("raise",      0x0C),
    ("gnarl",      0x10),
    ("river",      0x14),
    ("source",     0x18),
    ("snlin",      0x1C),
    ("snflt",      0x20),
    ("bhlin",      0x24),
    ("bhflt",      0x28),
    ("rkste",      0x2C),
]

ENTITY_TABLE_OFFSET = 0x0442
ENTITY_SLOT_COUNT   = 2095
ENTITY_SLOT_SIZE    = 18

ENTITY_CLASSES = {
    2:  "Scenery",
    3:  "PlayerStart",
    5:  "Creature",
    7:  "Weather",
    10: "Effect",
    12: "Unknown12",
    13: "SpellPickup",
}

CREATURE_MODELS = {
    0: "Dragon", 1: "Vulture", 2: "Bee", 3: "Worm", 4: "Archer",
    5: "Crab", 6: "Kraken", 7: "Troll", 8: "Griffon", 9: "Skeleton",
    10: "Emu", 11: "Genie", 12: "Builder", 13: "Townie", 14: "Trader",
    16: "Wyvern",
}

SCENERY_MODELS = {0: "Tree", 1: "StandingStone", 2: "Dolmen", 3: "BadStone"}

EFFECT_MODELS = {
    0: "Explosion", 1: "BigExplosion", 5: "Splash", 6: "Fire",
    8: "MiniVolcano", 9: "Volcano", 11: "Crater", 13: "WhiteSmoke",
    14: "BlackSmoke", 15: "Earthquake", 17: "Meteor", 23: "Lightning",
    24: "RainOfFire", 25: "StealMana", 28: "Wall", 29: "Path",
    31: "Canyon", 34: "Teleport", 39: "ManaBall", 45: "Wizard",
    49: "Unknown49", 50: "RidgeNode", 52: "CrabEgg",
}


def extract_level_bytes(level_num: int,
                        dat: Path = LEVELS_DAT,
                        tab: Path = LEVELS_TAB) -> bytes:
    """Extract and decompress level N from LEVELS.DAT."""
    dat_data = dat.read_bytes()
    tab_data = tab.read_bytes()

    assert dat_data[:8] == b"BULLFROG", "Not a BULLFROG levels file"

    start = read_u32_le(tab_data, level_num * 4)
    end   = read_u32_le(tab_data, (level_num + 1) * 4)
    chunk = dat_data[start:end]

    raw = decompress_rnc_bytes(chunk)
    assert len(raw) >= LEVEL_SIZE, f"Level {level_num}: decompressed size {len(raw)} < {LEVEL_SIZE}"
    return raw[:LEVEL_SIZE]


def parse_gen_map(raw: bytes) -> dict:
    """Parse the GEN_MAP header (first 48 bytes) of a decompressed level."""
    result = {}
    for name, offset in GEN_MAP_FIELDS:
        result[name] = read_u32_le(raw, offset)
    return result


def parse_entities(raw: bytes) -> list[dict]:
    """Parse the THING_INIT entity table from a decompressed level."""
    entities = []
    for s in range(ENTITY_SLOT_COUNT):
        p = ENTITY_TABLE_OFFSET + s * ENTITY_SLOT_SIZE
        slot = raw[p : p + ENTITY_SLOT_SIZE]
        if all(b == 0 for b in slot):
            continue
        cls   = read_u16_le(slot, 0x00)
        model = read_u16_le(slot, 0x02)
        xpos  = read_u16_le(slot, 0x04)
        ypos  = read_u16_le(slot, 0x06)
        disid = read_u16_le(slot, 0x08)
        swisz = read_u16_le(slot, 0x0A)
        swiid = read_u16_le(slot, 0x0C)
        par   = read_u16_le(slot, 0x0E)
        child = read_u16_le(slot, 0x10)

        model_map = {2: SCENERY_MODELS, 5: CREATURE_MODELS, 10: EFFECT_MODELS}.get(cls, {})
        entities.append({
            "class":      cls,
            "class_name": ENTITY_CLASSES.get(cls, f"Unknown{cls}"),
            "model":      model,
            "model_name": model_map.get(model, f"model{model}"),
            "x":          xpos,
            "y":          ypos,
            "disid":      disid,
            "swisz":      swisz,
            "swiid":      swiid,
            "parent":     par,
            "child":      child,
        })
    return entities


# ── TMAPS parser ───────────────────────────────────────────────────────────────
# TMAPS0-0.DAT: "BULLFROG" (8 bytes) + sequential RNC blocks.
# TMAPS0-0.TAB: 530 × 10-byte entries: {uint32 unc_size, uint32 cmp_offset, uint16 pad}
# Each decompressed block: 6-byte header {uint8 unk1, uint8 unk2, uint16_LE w, uint16_LE h}
#   followed by w×h raw paletted pixel bytes.

TAB_ENTRY_SIZE = 10
TAB_UNC_OFFSET = 0   # uint32 LE: decompressed size
TAB_CMP_OFFSET = 4   # uint32 LE: byte offset of RNC block in DAT file (from start)


def parse_tmaps_tab(tab_path: Path = TMAPS_TAB) -> list[dict]:
    tab = tab_path.read_bytes()
    n = len(tab) // TAB_ENTRY_SIZE
    entries = []
    for i in range(n):
        base = i * TAB_ENTRY_SIZE
        unc_size  = read_u32_le(tab, base + TAB_UNC_OFFSET)
        cmp_offset = read_u32_le(tab, base + TAB_CMP_OFFSET)
        if unc_size == 0 or cmp_offset == 0:
            entries.append(None)
        else:
            entries.append({"unc_size": unc_size, "cmp_offset": cmp_offset})
    return entries


def extract_texture_block(index: int,
                           dat_path: Path = TMAPS_DAT,
                           tab_path: Path = TMAPS_TAB) -> tuple[int, int, bytes] | None:
    """Extract texture block `index` → (width, height, raw_pixels) or None."""
    entries = parse_tmaps_tab(tab_path)
    if index >= len(entries) or entries[index] is None:
        return None

    entry = entries[index]
    dat = dat_path.read_bytes()
    rnc_chunk = dat[entry["cmp_offset"]:]
    raw = decompress_rnc_bytes(rnc_chunk)

    if len(raw) < 6:
        return None

    # 6-byte per-block header: {uint8 unk1, uint8 unk2, uint16 w, uint16 h}
    w = read_u16_le(raw, 2)
    h = read_u16_le(raw, 4)
    pixels = raw[6 : 6 + w * h]
    if len(pixels) < w * h:
        return None
    return w, h, pixels
