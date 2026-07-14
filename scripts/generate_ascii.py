"""Convert profile photo to ASCII grid JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml
from PIL import Image, ImageEnhance, ImageOps


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "scripts" / "config.yaml"
DEFAULT_INPUT = ROOT / "assets" / "profile.png"
DEFAULT_OUTPUT_DIR = ROOT / "output"


def load_config(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_and_preprocess(path: Path, cfg: dict) -> Image.Image:
    ascii_cfg = cfg["ascii"]
    width = int(ascii_cfg["width"])
    height = int(width * 1.25)

    image = Image.open(path).convert("L")
    image = ImageOps.autocontrast(image)

    # Center crop to portrait aspect ratio (chars are taller than wide).
    src_w, src_h = image.size
    target_ratio = width / height
    src_ratio = src_w / src_h

    if src_ratio > target_ratio:
        new_w = int(src_h * target_ratio)
        left = (src_w - new_w) // 2
        box = (left, 0, left + new_w, src_h)
    else:
        new_h = int(src_w / target_ratio)
        top = max(0, int(src_h * 0.08))
        box = (0, top, src_w, min(src_h, top + new_h))

    image = image.crop(box).resize((width, height), Image.Resampling.LANCZOS)

    contrast = float(ascii_cfg.get("contrast", 1.0))
    gamma = float(ascii_cfg.get("gamma", 1.0))
    image = ImageEnhance.Contrast(image).enhance(contrast)

    if gamma != 1.0:
        inv_gamma = 1.0 / gamma
        lut = [int((i / 255.0) ** inv_gamma * 255) for i in range(256)]
        image = image.point(lut)

    return image


def luminance_to_char(luminance: int, charset: str) -> str:
    index = int(luminance / 255 * (len(charset) - 1))
    return charset[index]


def image_to_grid(image: Image.Image, charset: str) -> list[list[dict]]:
    pixels = image.load()
    width, height = image.size
    grid: list[list[dict]] = []

    for row in range(height):
        line: list[dict] = []
        for col in range(width):
            luminance = int(pixels[col, row])
            line.append(
                {
                    "char": luminance_to_char(luminance, charset),
                    "luminance": luminance,
                    "row": row,
                    "col": col,
                }
            )
        grid.append(line)

    return grid


def export_grid(grid: list[list[dict]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "rows": len(grid),
        "cols": len(grid[0]) if grid else 0,
        "grid": grid,
    }
    with out_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False)


def export_preview(grid: list[list[dict]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["".join(cell["char"] for cell in row) for row in grid]
    out_path.write_text("\n".join(lines), encoding="utf-8")


def run(
    cfg: dict | None = None,
    input_path: Path | None = None,
    output_dir: Path | None = None,
) -> list[list[dict]]:
    if cfg is None:
        cfg = load_config(DEFAULT_CONFIG)
    if input_path is None:
        input_path = DEFAULT_INPUT
    if output_dir is None:
        output_dir = DEFAULT_OUTPUT_DIR

    charset = cfg["ascii"]["charset"]
    image = load_and_preprocess(input_path, cfg)
    grid = image_to_grid(image, charset)

    json_path = output_dir / "ascii_grid.json"
    preview_path = output_dir / "ascii_preview.txt"
    export_grid(grid, json_path)
    export_preview(grid, preview_path)

    print(f"ASCII grid: {len(grid[0])} cols x {len(grid)} rows")
    print(f"Wrote {json_path}")
    print(f"Wrote {preview_path}")
    return grid


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate ASCII grid from profile photo")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    cfg = load_config(args.config)
    run(cfg, args.input, args.output_dir)


if __name__ == "__main__":
    main()
