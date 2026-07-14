"""Build all GitHub profile README assets."""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
OUTPUT = ROOT / "output"
CONFIG_PATH = ROOT / "scripts" / "config.yaml"

PROFILE_SOURCES = [
    Path(r"C:\Users\saile\OneDrive\Documents\Profile Picture.png"),
    Path(
        r"C:\Users\saile\.cursor\projects\empty-window\assets"
        r"\c__Users_saile_AppData_Roaming_Cursor_User_workspaceStorage_empty-window_images_"
        r"Profile_Picture-002992f5-14fa-469f-a661-b49652d0b7bd.png"
    ),
]

EXPECTED_ASSETS = [
    "hero-dark.svg",
    "hero-light.svg",
    "ascii-dark.svg",
    "ascii-light.svg",
    "icons.svg",
    "logo.svg",
    "matrix-mask.svg",
    "profile.png",
]

FORBIDDEN_PATTERNS = [
    re.compile(r"<script\b", re.I),
    re.compile(r"javascript:", re.I),
    re.compile(r"\bon\w+\s*=", re.I),
    re.compile(r"xlink:href\s*=\s*[\"']https?://", re.I),
]

MAX_HERO_BYTES = 500 * 1024


def load_config() -> dict:
    with CONFIG_PATH.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def copy_profile_if_needed() -> None:
    target = ASSETS / "profile.png"
    ASSETS.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.stat().st_size > 0:
        return
    for source in PROFILE_SOURCES:
        if source.exists():
            shutil.copy2(source, target)
            print(f"Copied profile photo from {source} to {target}")
            return
    raise FileNotFoundError(
        "assets/profile.png is missing. Place your headshot at assets/profile.png"
    )


def validate_outputs(cfg: dict) -> None:
    missing = [name for name in EXPECTED_ASSETS if not (ASSETS / name).exists()]
    if missing:
        raise FileNotFoundError(f"Missing generated assets: {', '.join(missing)}")

    grid_path = OUTPUT / "ascii_grid.json"
    if not grid_path.exists():
        raise FileNotFoundError(f"Missing ASCII grid: {grid_path}")

    for svg_name in [name for name in EXPECTED_ASSETS if name.endswith(".svg")]:
        path = ASSETS / svg_name
        content = path.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_PATTERNS:
            if pattern.search(content):
                raise ValueError(f"Forbidden pattern {pattern.pattern} found in {svg_name}")

    for hero_name in ["hero-dark.svg", "hero-light.svg"]:
        size = (ASSETS / hero_name).stat().st_size
        if size > MAX_HERO_BYTES:
            raise ValueError(
                f"{hero_name} is {size} bytes (> {MAX_HERO_BYTES}). "
                "Reduce ASCII width or simplify animations."
            )

    readme = ROOT / "README.md"
    if not readme.exists():
        raise FileNotFoundError("README.md was not generated")

    print("Validation passed.")


def main() -> int:
    sys.path.insert(0, str(ROOT / "scripts"))

    from generate_ascii import run as run_ascii
    from generate_readme import run as run_readme
    from generate_svg import run as run_svg

    cfg = load_config()
    copy_profile_if_needed()
    OUTPUT.mkdir(parents=True, exist_ok=True)

    print("==> Generating ASCII grid")
    grid = run_ascii(cfg)

    print("==> Generating hero SVGs")
    run_svg(cfg, grid, mode="hero")

    print("==> Generating ASCII SVGs")
    run_svg(cfg, grid, mode="ascii")

    print("==> Generating supporting assets")
    run_svg(cfg, grid, mode="assets")

    print("==> Generating README.md")
    run_readme(cfg)

    validate_outputs(cfg)
    print("Build complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
