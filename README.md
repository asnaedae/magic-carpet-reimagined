# Magic Carpet Reimagined

A reimagining of Bullfrog's *Magic Carpet* (1994) built with Godot 4 (Forward+ / Vulkan).
Vanity project, macOS Apple Silicon.  Requires you to supply your own copy of the game data.

## Philosophy

Original assets are a starting point, not a constraint.  Terrain generation seeds are
reproduced exactly; geometry, materials, and lighting are rebuilt for a modern Vulkan renderer
with SDFGI, volumetric fog, and triplanar texture blending.

## Prerequisites

| Tool | Purpose |
|------|---------|
| [Godot 4.3+](https://godotengine.org/) | Game engine (Forward+ renderer) |
| Python 3.11+ | Extraction pipeline |
| Pillow (`pip install Pillow`) | Image conversion |
| Magic Carpet (GOG / Boxer) | Game data (not included) |
| Built `mc1-tools` binaries | RNC decompression + terrain gen |

The `mc1-tools` binaries are in the sibling `../mc1-tools/` directory and should already
be built if you've been following the main project.

## Quick start

```bash
# 1. Install Python deps
pip install -r tools/requirements.txt

# 2. Extract data (palette + level 0 JSON + heightmap + first 20 textures)
cd tools && python extract_all.py

# 3. Open the project in Godot
open /Applications/Godot.app --args --path /path/to/godot-mc
```

## Extraction tools

| Script | Output | Notes |
|--------|--------|-------|
| `extract_palette.py` | `assets/palette.{png,json}` | 256-colour VGA palette |
| `extract_level.py --level N` | `assets/levels/level_NN.json` | GEN_MAP params + entity table |
| `extract_textures.py` | `assets/textures/tile_NNNN.png` | Terrain texture tiles |
| `generate_heightmap.py --level N` | `assets/heightmaps/level_NN.png` | 256×256 16-bit PNG |
| `extract_all.py --all-levels` | All of the above for all 70 levels | ~2 min |

## Data file locations

Configured in `tools/common.py`:

```
LEVELS.DAT   /Applications/Magic Carpet Plus™.app/.../CARPET.CD/LEVELS/LEVELS.DAT
TMAPS.DAT    ../upstream-mc2/build/Debug/inst/mc1-bin/CD_Files/DATA/TMAPS0-0.DAT
PAL.DAT      ../upstream-mc2/build/Debug/inst/mc1-bin/CD_Files/DATA/PAL0-0.DAT
```

## Level format summary

Each level decompresses to 38,812 bytes:
- **GEN_MAP** (48 bytes): 12 × uint32 terrain generation seeds
- **Reserved** (1,042 bytes): all zeros
- **THING_INIT** (37,710 bytes): 2,095 × 18-byte entity records (Class, Model, X, Y, …)

The terrain is **procedurally generated** at runtime from the seed parameters — there is no
stored heightmap.  The `mc1-terrain-gen` binary implements all 17 pipeline stages.

## Project structure

```
godot-mc/
├── project.godot
├── scenes/world/World.tscn      — main scene with terrain loader + sky
├── scripts/terrain/
│   └── terrain_loader.gd        — builds MeshInstance3D from 16-bit heightmap
├── shaders/
│   └── terrain.gdshader         — triplanar slope/height blending shader
├── tools/                       — Python extraction pipeline
│   ├── common.py                — shared RNC decompressor + format parsers
│   ├── extract_palette.py
│   ├── extract_textures.py
│   ├── extract_level.py
│   ├── generate_heightmap.py
│   └── extract_all.py
└── assets/                      — gitignored; populated by tools/extract_all.py
    ├── palette.png
    ├── levels/level_NN.json
    ├── textures/tile_NNNN.png
    └── heightmaps/level_NN.png
```

## Related projects

- [thobbsinteractive/magic-carpet-2-hd](https://github.com/thobbsinteractive/magic-carpet-2-hd) — MC2 engine reconstruction (basis for our data tools)
- [MCLevelEdit](../MCLevelEdit/) — C# level editor with validated terrain generator
- [MagicCarpetFileFormat](../MagicCarpetFileFormat/) — complete format specification
