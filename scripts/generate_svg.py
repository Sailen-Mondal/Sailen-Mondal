"""Generate SMIL-animated SVG assets for GitHub profile README."""

from __future__ import annotations

import argparse
import json
import random
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml

from generate_ascii import DEFAULT_CONFIG, DEFAULT_OUTPUT_DIR, run as run_ascii


ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT / "assets"

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", XLINK_NS)


@dataclass
class Theme:
    name: str
    bg: str
    text: str
    secondary: str
    dim: str
    cursor: str
    border: str
    panel: str


@dataclass
class Timeline:
    reveal: float = 3.0
    blink: float = 0.8
    flicker: float = 2.0
    dropout: float = 2.0
    dissolve: float = 2.0
    code_words: float = 3.0
    ai_words: float = 3.0
    reconstruct: float = 4.0
    hold: float = 2.0

    @property
    def total(self) -> float:
        return (
            self.reveal
            + self.blink
            + self.flicker
            + self.dropout
            + self.dissolve
            + self.code_words
            + self.ai_words
            + self.reconstruct
            + self.hold
        )

    def offsets(self) -> dict[str, float]:
        t0 = 0.0
        reveal_end = t0 + self.reveal
        blink_start = reveal_end
        blink_end = blink_start + self.blink
        flicker_start = blink_end
        flicker_end = flicker_start + self.flicker
        dropout_start = flicker_end
        dropout_end = dropout_start + self.dropout
        dissolve_start = dropout_end
        dissolve_end = dissolve_start + self.dissolve
        code_start = dissolve_end
        code_end = code_start + self.code_words
        ai_start = code_end
        ai_end = ai_start + self.ai_words
        reconstruct_start = ai_end
        reconstruct_end = reconstruct_start + self.reconstruct
        hold_start = reconstruct_end
        return {
            "loop": self.total,
            "reveal_start": t0,
            "reveal_end": reveal_end,
            "blink_start": blink_start,
            "blink_end": blink_end,
            "flicker_start": flicker_start,
            "flicker_end": flicker_end,
            "dropout_start": dropout_start,
            "dropout_end": dropout_end,
            "dissolve_start": dissolve_start,
            "dissolve_end": dissolve_end,
            "code_start": code_start,
            "code_end": code_end,
            "ai_start": ai_start,
            "ai_end": ai_end,
            "reconstruct_start": reconstruct_start,
            "reconstruct_end": reconstruct_end,
            "hold_start": hold_start,
        }


def load_config(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_grid(path: Path) -> list[list[dict]]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload["grid"]


def theme_from_config(cfg: dict, name: str) -> Theme:
    colors = cfg["colors"][name]
    return Theme(name=name, **colors)


def svg(tag: str, **attrs: str) -> ET.Element:
    element = ET.Element(f"{{{SVG_NS}}}{tag}")
    for key, value in attrs.items():
        if value is not None:
            element.set(key.replace("_", "-"), str(value))
    return element


def sub(parent: ET.Element, tag: str, **attrs: str) -> ET.Element:
    element = svg(tag, **attrs)
    parent.append(element)
    return element


def text_content(parent: ET.Element, content: str) -> None:
    if content:
        parent.text = content


def char_color(luminance: int, theme: Theme) -> str:
    if luminance > 190:
        return theme.text
    if luminance > 120:
        return theme.secondary
    return theme.dim


def build_crt_defs(parent: ET.Element, theme: Theme, width: float, height: float) -> None:
    defs = sub(parent, "defs")

    scan_pattern = sub(
        defs,
        "pattern",
        id="scanlines",
        patternUnits="userSpaceOnUse",
        width="4",
        height="4",
    )
    sub(scan_pattern, "rect", width="4", height="1", fill=theme.text, opacity="0.035")
    sub(scan_pattern, "rect", y="1", width="4", height="3", fill="none")

    glow = sub(defs, "filter", id="glow", x="-20%", y="-20%", width="140%", height="140%")
    sub(glow, "feGaussianBlur", stdDeviation="0.6", result="blur")
    merge = sub(glow, "feMerge")
    source_node = sub(merge, "feMergeNode")
    source_node.set("in", "SourceGraphic")
    blur_node = sub(merge, "feMergeNode")
    blur_node.set("in", "blur")

    noise_filter = sub(defs, "filter", id="noise", x="0", y="0", width="100%", height="100%")
    turbulence = sub(
        noise_filter,
        "feTurbulence",
        type="fractalNoise",
        baseFrequency="0.85",
        numOctaves="1",
        stitchTiles="stitch",
        result="noise",
    )
    sub(
        turbulence,
        "animate",
        attributeName="seed",
        values="0;20;40;60;80;100;0",
        dur="8s",
        repeatCount="indefinite",
    )
    sub(noise_filter, "feColorMatrix", type="saturate", values="0")
    sub(noise_filter, "feComponentTransfer")
    blend = sub(noise_filter, "feBlend", in2="noise", mode="overlay")
    blend.set("in", "SourceGraphic")

    vignette = sub(
        defs,
        "radialGradient",
        id="vignette",
        cx="50%",
        cy="50%",
        r="70%",
    )
    sub(vignette, "stop", offset="55%", stop_color=theme.bg, stop_opacity="0")
    sub(vignette, "stop", offset="100%", stop_color="#000000", stop_opacity="0.35")

    clip = sub(defs, "clipPath", id="screenCurve")
    sub(clip, "rect", x="0", y="0", width=str(width), height=str(height), rx="8", ry="8")


def add_loop_opacity(
    element: ET.Element,
    values: str,
    key_times: str,
    begin: float,
    loop: float,
    dur: float | None = None,
) -> None:
    sub(
        element,
        "animate",
        attributeName="opacity",
        values=values,
        keyTimes=key_times,
        dur=f"{dur or loop}s",
        begin=f"{begin}s",
        repeatCount="indefinite",
    )


def build_portrait_panel(
    parent: ET.Element,
    grid: list[list[dict]],
    theme: Theme,
    cfg: dict,
    x_offset: float,
    y_offset: float,
    panel_width: float,
    panel_height: float,
    timeline: Timeline,
) -> None:
    ascii_cfg = cfg["ascii"]
    svg_cfg = cfg["svg"]
    char_w = float(ascii_cfg["char_width"])
    char_h = float(ascii_cfg["char_height"])
    font = svg_cfg["font_family"]
    font_size = str(svg_cfg["font_size"])
    offsets = timeline.offsets()
    loop = offsets["loop"]

    panel = sub(
        parent,
        "g",
        id="portraitPanel",
        transform=f"translate({x_offset},{y_offset})",
        clip_path="url(#screenCurve)",
    )

    frame = sub(
        panel,
        "rect",
        x="0",
        y="0",
        width=str(panel_width),
        height=str(panel_height),
        fill=theme.panel,
        stroke=theme.border,
        stroke_width="1",
        rx="6",
    )

    grid_height = len(grid) * char_h
    grid_width = len(grid[0]) * char_w if grid else 0
    start_x = (panel_width - grid_width) / 2
    start_y = (panel_height - grid_height) / 2 + 8

    portrait_group = sub(panel, "g", id="portraitAscii", filter="url(#glow)")
    binary_group = sub(panel, "g", id="binaryLayer", opacity="0")
    code_group = sub(panel, "g", id="codeLayer", opacity="0")
    ai_group = sub(panel, "g", id="aiLayer", opacity="0")

    random.seed(42)
    dropout_cells: set[tuple[int, int]] = set()
    total_cells = sum(len(row) for row in grid)
    for idx in random.sample(range(total_cells), k=min(120, total_cells // 3)):
        row = idx // len(grid[0])
        col = idx % len(grid[0])
        dropout_cells.add((row, col))

    for row_idx, row in enumerate(grid):
        row_group = sub(portrait_group, "g", id=f"row-{row_idx}", opacity="0")
        row_begin = offsets["reveal_start"] + row_idx * 0.04
        sub(
            row_group,
            "animate",
            attributeName="opacity",
            values="0;1;1;1;1;1;1;1;1;0;0;0;0;0;0;0;0;0;1",
            keyTimes="0;0.08;0.15;0.25;0.35;0.45;0.55;0.62;0.68;0.72;0.76;0.80;0.84;0.88;0.92;0.95;0.97;0.99;1",
            dur=f"{loop}s",
            begin=f"{row_begin}s",
            repeatCount="indefinite",
        )

        text_el = sub(
            row_group,
            "text",
            x=str(start_x),
            y=str(start_y + row_idx * char_h),
            fill=theme.text,
            font_family=font,
            font_size=font_size,
        )

        x_cursor = start_x
        for col_idx, cell in enumerate(row):
            tspan = sub(
                text_el,
                "tspan",
                x=str(x_cursor),
                fill=char_color(cell["luminance"], theme),
            )
            text_content(tspan, cell["char"])
            x_cursor += char_w

            if (row_idx, col_idx) in dropout_cells:
                dropout_begin = offsets["dropout_start"] + random.random() * timeline.dropout
                sub(
                    tspan,
                    "animate",
                    attributeName="opacity",
                    values="1;0;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1",
                    keyTimes="0;0.08;0.12;0.2;0.3;0.4;0.5;0.55;0.6;0.65;0.7;0.75;0.8;0.85;0.9;0.93;0.96;0.98;1",
                    dur=f"{loop}s",
                    begin=f"{dropout_begin}s",
                    repeatCount="indefinite",
                )

    add_loop_opacity(
        portrait_group,
        values="1;1;0.35;1;1;1;1;1;1;0;0;0;0;0;0;0;0;0;1",
        key_times="0;0.15;0.17;0.19;0.55;0.62;0.68;0.72;0.76;0.78;0.82;0.86;0.90;0.93;0.95;0.97;0.98;0.99;1",
        begin=offsets["blink_start"],
        loop=loop,
    )

    add_loop_opacity(
        binary_group,
        values="0;0;0;0;0;0;0;0;0;1;1;0;0;0;0;0;0;0;0",
        key_times="0;0.68;0.72;0.74;0.76;0.78;0.80;0.82;0.84;0.86;0.90;0.92;0.94;0.95;0.96;0.97;0.98;0.99;1",
        begin=0,
        loop=loop,
    )
    add_loop_opacity(
        code_group,
        values="0;0;0;0;0;0;0;0;0;0;0;1;1;0;0;0;0;0;0",
        key_times="0;0.76;0.80;0.82;0.84;0.86;0.88;0.90;0.92;0.93;0.94;0.95;0.97;0.98;0.985;0.99;0.995;0.998;1",
        begin=0,
        loop=loop,
    )
    add_loop_opacity(
        ai_group,
        values="0;0;0;0;0;0;0;0;0;0;0;0;0;1;1;0;0;0;0",
        key_times="0;0.82;0.86;0.88;0.90;0.92;0.93;0.94;0.95;0.96;0.97;0.975;0.98;0.985;0.99;0.995;0.997;0.999;1",
        begin=0,
        loop=loop,
    )

    binary_text = cfg["animation_words"]["binary"]
    sub(
        binary_group,
        "text",
        x=str(panel_width / 2),
        y=str(panel_height / 2),
        fill=theme.text,
        font_family=font,
        font_size="14",
        text_anchor="middle",
    ).text = binary_text

    code_words: Iterable[str] = cfg["animation_words"]["code"]
    ai_words: Iterable[str] = cfg["animation_words"]["ai"]

    for idx, word in enumerate(code_words):
        sub(
            code_group,
            "text",
            x=str(20),
            y=str(48 + idx * 22),
            fill=theme.secondary,
            font_family=font,
            font_size="12",
        ).text = word

    for idx, word in enumerate(ai_words):
        sub(
            ai_group,
            "text",
            x=str(20),
            y=str(48 + idx * 22),
            fill=theme.text,
            font_family=font,
            font_size="12",
        ).text = word

    flicker_overlay = sub(
        panel,
        "rect",
        x="0",
        y="0",
        width=str(panel_width),
        height=str(panel_height),
        fill=theme.text,
        opacity="0",
        pointer_events="none",
    )
    sub(
        flicker_overlay,
        "animate",
        attributeName="opacity",
        values="0;0.04;0;0.03;0;0.05;0;0;0;0;0;0;0;0;0;0;0;0;0",
        keyTimes="0;0.02;0.04;0.06;0.08;0.10;0.12;0.2;0.3;0.4;0.5;0.6;0.7;0.8;0.85;0.9;0.93;0.96;1",
        dur=f"{loop}s",
        begin=f"{offsets['flicker_start']}s",
        repeatCount="indefinite",
    )


def build_terminal_panel(
    parent: ET.Element,
    cfg: dict,
    theme: Theme,
    x_offset: float,
    y_offset: float,
    panel_width: float,
    panel_height: float,
) -> None:
    svg_cfg = cfg["svg"]
    identity = cfg["identity"]
    font = svg_cfg["font_family"]
    font_size = str(svg_cfg["font_size"])
    hostname = identity["hostname"]

    panel = sub(
        parent,
        "g",
        id="terminalPanel",
        transform=f"translate({x_offset},{y_offset})",
    )

    sub(
        panel,
        "rect",
        x="0",
        y="0",
        width=str(panel_width),
        height=str(panel_height),
        fill=theme.panel,
        stroke=theme.border,
        stroke_width="1",
        rx="6",
    )

    title = sub(
        panel,
        "text",
        x="16",
        y="24",
        fill=theme.dim,
        font_family=font,
        font_size="10",
    )
    title.text = f"{hostname}@terminal:~$"

    content_group = sub(panel, "g", id="terminalContent", transform="translate(16,42)")
    line_y = 0.0
    line_height = 14.0
    char_step = 0.05
    pause = 0.6
    time_cursor = 0.4

    for command in cfg["terminal_commands"]:
        cmd = command["cmd"]
        output = command["output"]
        prompt = f"$ {cmd}"

        prompt_text = sub(
            content_group,
            "text",
            x="0",
            y=str(line_y),
            fill=theme.text,
            font_family=font,
            font_size=font_size,
        )

        for idx, ch in enumerate(prompt):
            tspan = sub(prompt_text, "tspan", fill=theme.text, opacity="0")
            tspan.text = ch
            prompt_anim = sub(
                tspan,
                "animate",
                attributeName="opacity",
                to="1",
                begin=f"{time_cursor + idx * char_step}s",
                dur="40ms",
                fill="freeze",
            )
            prompt_anim.set("from", "0")

        time_cursor += len(prompt) * char_step + pause
        line_y += line_height

        for output_line in output.split("\n"):
            output_text = sub(
                content_group,
                "text",
                x="12",
                y=str(line_y),
                fill=theme.secondary,
                font_family=font,
                font_size=font_size,
                opacity="0",
            )
            output_text.text = output_line
            output_anim = sub(
                output_text,
                "animate",
                attributeName="opacity",
                to="1",
                begin=f"{time_cursor}s",
                dur="200ms",
                fill="freeze",
            )
            output_anim.set("from", "0")
            line_y += line_height
            time_cursor += 0.35

        time_cursor += pause

    cursor = sub(
        content_group,
        "rect",
        x="0",
        y=str(line_y - 10),
        width="8",
        height="12",
        fill=theme.cursor,
    )
    sub(
        cursor,
        "animate",
        attributeName="opacity",
        values="1;0;1",
        dur="1s",
        repeatCount="indefinite",
    )


def build_crt_overlay(parent: ET.Element, width: float, height: float, theme: Theme) -> None:
    sub(
        parent,
        "rect",
        width=str(width),
        height=str(height),
        fill="url(#scanlines)",
        opacity="1",
        pointer_events="none",
    )
    sub(
        parent,
        "rect",
        width=str(width),
        height=str(height),
        filter="url(#noise)",
        opacity="0.03",
        pointer_events="none",
    )
    sub(
        parent,
        "rect",
        width=str(width),
        height=str(height),
        fill="url(#vignette)",
        pointer_events="none",
    )


def build_dossier_hero(parent: ET.Element, cfg: dict, theme: Theme, width: int, height: int) -> None:
    """Build the single, wide terminal used as the profile's visual signature."""
    font = cfg["svg"]["font_family"]
    identity = cfg["identity"]
    margin = 28
    panel_width = width - margin * 2
    panel_height = height - margin * 2

    panel = sub(parent, "g", id="terminalDossier", transform=f"translate({margin},{margin})")
    sub(panel, "rect", width=str(panel_width), height=str(panel_height), fill=theme.panel, stroke=theme.border, stroke_width="2", rx="8")
    sub(panel, "rect", width=str(panel_width), height="46", fill=theme.bg, stroke=theme.border, stroke_width="1", rx="8")
    sub(panel, "rect", y="40", width=str(panel_width), height="6", fill=theme.bg)

    for index, color in enumerate(["#EF6A62", "#E5B84B", theme.secondary]):
        sub(panel, "circle", cx=str(24 + index * 18), cy="23", r="5", fill=color, opacity="0.9")

    window_title = sub(panel, "text", x="86", y="28", fill=theme.dim, font_family=font, font_size="13")
    window_title.text = f"{identity['username']}@portfolio:~"

    eyebrow = sub(panel, "text", x="42", y="94", fill=theme.secondary, font_family=font, font_size="14", letter_spacing="1")
    eyebrow.text = "PERSONAL TERMINAL DOSSIER"

    name = sub(panel, "text", x="42", y="150", fill=theme.text, font_family=font, font_size="42", font_weight="700")
    name.text = identity["name"].upper()

    role = sub(panel, "text", x="42", y="184", fill=theme.secondary, font_family=font, font_size="20")
    role.text = identity["role"]
    sub(panel, "line", x1="42", y1="212", x2=str(panel_width - 42), y2="212", stroke=theme.border, stroke_width="1")

    command_y = 252
    for index, command in enumerate(cfg["terminal_commands"][:3]):
        y = command_y + index * 40
        prompt = sub(panel, "text", x="42", y=str(y), fill=theme.text, font_family=font, font_size="15")
        prompt.text = f"$ {command['cmd']}"
        value = sub(panel, "text", x="250", y=str(y), fill=theme.secondary, font_family=font, font_size="15")
        value.text = command["output"].replace("\n", " | ")

    footer = sub(
        panel,
        "text",
        x=str(panel_width - 42),
        y="94",
        fill=theme.dim,
        font_family=font,
        font_size="12",
        letter_spacing="0.6",
        text_anchor="end",
    )
    footer.text = "KOLKATA, INDIA  //  JIS UNIVERSITY"
    cursor = sub(panel, "rect", x=str(panel_width - 58), y=str(panel_height - 42), width="12", height="18", fill=theme.cursor)
    sub(cursor, "animate", attributeName="opacity", values="1;0;1", dur="1.1s", repeatCount="indefinite")


def build_document(
    grid: list[list[dict]],
    cfg: dict,
    theme: Theme,
    width: int,
    height: int,
    mode: str,
) -> ET.ElementTree:
    timeline = Timeline()
    portrait_width = int(width * cfg["svg"]["portrait_ratio"])
    terminal_width = width - portrait_width - 24
    margin = 12

    root = svg(
        "svg",
        width=str(width),
        height=str(height),
        viewBox=f"0 0 {width} {height}",
    )

    sub(root, "rect", width=str(width), height=str(height), fill=theme.bg)
    build_crt_defs(root, theme, width, height)

    if mode == "ascii":
        build_portrait_panel(
            root,
            grid,
            theme,
            x_offset=margin,
            y_offset=margin,
            panel_width=portrait_width - margin,
            panel_height=height - margin * 2,
            cfg=cfg,
            timeline=timeline,
        )

    if mode == "hero":
        build_dossier_hero(root, cfg, theme, width, height)

    build_crt_overlay(root, width, height, theme)
    return ET.ElementTree(root)


def build_logo(cfg: dict, theme: Theme) -> ET.ElementTree:
    root = svg("svg", width="420", height="48", viewBox="0 0 420 48")
    sub(root, "rect", width="420", height="48", fill=theme.bg)
    text_el = sub(
        root,
        "text",
        x="12",
        y="32",
        fill=theme.text,
        font_family=cfg["svg"]["font_family"],
        font_size="20",
    )
    text_el.text = cfg["identity"]["username"]
    return ET.ElementTree(root)


def build_icons(cfg: dict, theme: Theme) -> ET.ElementTree:
    root = svg("svg", width="0", height="0", viewBox="0 0 0 0")
    defs = sub(root, "defs")
    icons = {
        "java": "J",
        "docker": "D",
        "github": "G",
        "linux": "L",
        "spring": "S",
        "postgres": "P",
    }
    for idx, (name, glyph) in enumerate(icons.items()):
        symbol = sub(defs, "symbol", id=f"icon-{name}", viewBox="0 0 24 24")
        sub(symbol, "rect", width="24", height="24", fill=theme.panel, stroke=theme.border)
        sub(
            symbol,
            "text",
            x="12",
            y="17",
            fill=theme.text,
            font_family=cfg["svg"]["font_family"],
            font_size="14",
            text_anchor="middle",
        ).text = glyph
    return ET.ElementTree(root)


def build_matrix_mask(width: int, height: int) -> ET.ElementTree:
    root = svg("svg", width=str(width), height=str(height), viewBox=f"0 0 {width} {height}")
    defs = sub(root, "defs")
    mask = sub(defs, "mask", id="matrixMask")
    sub(mask, "rect", width=str(width), height=str(height), fill="white")
    random.seed(7)
    for _ in range(400):
        x = random.randint(0, width - 4)
        y = random.randint(0, height - 4)
        sub(mask, "rect", x=str(x), y=str(y), width="3", height="3", fill="black")
    return ET.ElementTree(root)


def write_tree(tree: ET.ElementTree, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(path, encoding="utf-8", xml_declaration=True)


def run(
    cfg: dict,
    grid: list[list[dict]] | None = None,
    mode: str = "all",
    output_dir: Path | None = None,
) -> None:
    if output_dir is None:
        output_dir = ASSETS_DIR
    if grid is None:
        grid_path = DEFAULT_OUTPUT_DIR / "ascii_grid.json"
        if not grid_path.exists():
            grid = run_ascii(cfg)
        else:
            grid = load_grid(grid_path)

    width = int(cfg["svg"]["hero_width"])
    height = int(cfg["svg"]["hero_height"])

    if mode in {"hero", "all"}:
        for theme_name, filename in [("dark", "hero-dark.svg"), ("light", "hero-light.svg")]:
            theme = theme_from_config(cfg, theme_name)
            tree = build_document(grid, cfg, theme, width, height, mode="hero")
            write_tree(tree, output_dir / filename)
            print(f"Wrote {output_dir / filename}")

    if mode in {"ascii", "all"}:
        ascii_width = int(width * cfg["svg"]["portrait_ratio"]) + 24
        ascii_height = height
        for theme_name, filename in [("dark", "ascii-dark.svg"), ("light", "ascii-light.svg")]:
            theme = theme_from_config(cfg, theme_name)
            tree = build_document(grid, cfg, theme, ascii_width, ascii_height, mode="ascii")
            write_tree(tree, output_dir / filename)
            print(f"Wrote {output_dir / filename}")

    if mode in {"assets", "all"}:
        for theme_name, suffix in [("dark", "dark"), ("light", "light")]:
            theme = theme_from_config(cfg, theme_name)
            write_tree(build_logo(cfg, theme), output_dir / f"logo-{suffix}.svg")
        write_tree(build_logo(cfg, theme_from_config(cfg, "dark")), output_dir / "logo.svg")
        write_tree(build_icons(cfg, theme_from_config(cfg, "dark")), output_dir / "icons.svg")
        write_tree(build_matrix_mask(width, height), output_dir / "matrix-mask.svg")
        print(f"Wrote logo, icons, matrix-mask to {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate SVG assets")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--mode", choices=["hero", "ascii", "assets", "all"], default="all")
    args = parser.parse_args()

    cfg = load_config(args.config)
    run(cfg, mode=args.mode)


if __name__ == "__main__":
    main()
