#!/usr/bin/env python3
"""Generate high-resolution copies of the game textures for use with --renderscale.

The game looks in data/textures/hd/ for a texture before data/textures/ whenever it
is started with --renderscale 2 (or higher). Texture coordinates are normalised, so a
texture of any size works; an exact multiple of the original size gives the best result.

By default textures are resized with Lanczos filtering (requires Pillow). For much better
results, pass an external upscaler such as Real-ESRGAN with --command; {in}, {out} and
{scale} are substituted. The alpha channel is always upscaled here, because many AI
upscalers drop or damage it.

Examples:
    tools/upscale_textures.py
    tools/upscale_textures.py --command \\
        "realesrgan-ncnn-vulkan -i {in} -o {out} -s {scale} -n realesr-animevideov3"
"""

import argparse
import glob
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent

# Tilesets are 256x256 sheets of 20x20 tiles packed edge to edge (see Tileengine.hpp)
TILE_SIZE = 20
TILES_PER_ROW = 12
TILE_PAD = 4
# FileHeader layout in level .map files: UsedTilesets count, then SetNames[64][16]
HEADER_SIZE = 1292
USED_TILESETS_OFFSET = 248
SET_NAMES_OFFSET = 249
SET_NAME_LEN = 16


def find_tilesets(levels_dir):
    """Return the lower-cased file names of all tilesets referenced by level files."""
    names = set()
    for path in glob.glob(str(levels_dir / "**" / "*.map"), recursive=True):
        with open(path, "rb") as f:
            header = f.read(HEADER_SIZE)
        if len(header) < HEADER_SIZE:
            continue
        for i in range(header[USED_TILESETS_OFFSET]):
            start = SET_NAMES_OFFSET + i * SET_NAME_LEN
            name = header[start:start + SET_NAME_LEN].split(b"\0")[0].decode("latin1")
            if name:
                names.add(name.lower())
    return names


def lanczos(img, size):
    # Resize in premultiplied alpha so transparent (black) pixels don't bleed dark fringes
    return img.convert("RGBa").resize(size, Image.LANCZOS).convert("RGBA")


def resize(img, scale, command):
    size = (img.width * scale, img.height * scale)
    result = lanczos(img, size)

    if command:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_in = Path(tmp) / "in.png"
            tmp_out = Path(tmp) / "out.png"
            img.convert("RGB").save(tmp_in)
            cmd = [arg.format(**{"in": tmp_in, "out": tmp_out, "scale": scale}) for arg in shlex.split(command)]
            # Upscalers tend to print GPU details and progress to stderr; only show it on failure
            run = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            # ncnn-vulkan tools exit with 0 even when the GPU job fails (e.g. after a GPU reset),
            # leaving a black image, so check the log as well
            if run.returncode != 0 or not tmp_out.exists() or "vkQueueSubmit failed" in run.stdout:
                raise RuntimeError(f"upscaler failed (exit {run.returncode}):\n{run.stdout.strip()}")
            rgb = Image.open(tmp_out).convert("RGB")
            if rgb.size != size:
                rgb = rgb.resize(size, Image.LANCZOS)
            rgb.putalpha(result.getchannel("A"))
            result = rgb

    return result


def resize_tileset(img, scale, command):
    """Upscale each tile on its own, so neighbouring tiles on the sheet don't bleed into its edges.

    Every tile is surrounded by copies of its own edge pixels and spread out on a larger sheet,
    which is upscaled in one go (one external upscaler run per tileset), then the tile centres
    are copied back.
    """
    result = resize(img, scale, command)  # covers any area outside the tile grid
    pixels = np.asarray(img)
    cell = TILE_SIZE + 2 * TILE_PAD
    spread = np.zeros((TILES_PER_ROW * cell, TILES_PER_ROW * cell, 4), dtype=np.uint8)
    for ty in range(TILES_PER_ROW):
        for tx in range(TILES_PER_ROW):
            tile = pixels[ty * TILE_SIZE:(ty + 1) * TILE_SIZE, tx * TILE_SIZE:(tx + 1) * TILE_SIZE]
            spread[ty * cell:(ty + 1) * cell, tx * cell:(tx + 1) * cell] = np.pad(
                tile, ((TILE_PAD, TILE_PAD), (TILE_PAD, TILE_PAD), (0, 0)), mode="edge")

    big = resize(Image.fromarray(spread, "RGBA"), scale, command)
    tile_px = TILE_SIZE * scale
    for ty in range(TILES_PER_ROW):
        for tx in range(TILES_PER_ROW):
            left = (tx * cell + TILE_PAD) * scale
            top = (ty * cell + TILE_PAD) * scale
            tile = big.crop((left, top, left + tile_px, top + tile_px))
            result.paste(tile, (tx * tile_px, ty * tile_px))
    return result


def upscale(src, dst, scale, command, is_tileset):
    img = Image.open(src).convert("RGBA")
    if is_tileset and img.size == (256, 256):
        result = resize_tileset(img, scale, command)
    else:
        result = resize(img, scale, command)
    result.save(dst, optimize=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scale", type=int, default=2, help="upscale factor (default: 2)")
    parser.add_argument("--src", type=Path, default=ROOT / "data" / "textures", help="source texture folder")
    parser.add_argument("--dst", type=Path, help="output folder (default: <src>/hd)")
    parser.add_argument("--command", help="external upscaler command, with {in}, {out} and {scale} placeholders")
    parser.add_argument("--force", action="store_true", help="overwrite textures that already exist in the output")
    args = parser.parse_args()

    dst = args.dst or args.src / "hd"
    dst.mkdir(parents=True, exist_ok=True)

    tilesets = find_tilesets(args.src.parent / "levels")
    textures = sorted(args.src.glob("*.png"))
    for i, src in enumerate(textures, 1):
        out = dst / src.name
        if out.exists() and not args.force:
            continue
        print(f"[{i}/{len(textures)}] {src.name}")
        try:
            upscale(src, out, args.scale, args.command, src.name.lower() in tilesets)
        except Exception as e:  # keep going; the game falls back to the original texture
            print(f"  failed: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
