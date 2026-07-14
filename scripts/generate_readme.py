"""Generate README.md from template and config."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "scripts" / "config.yaml"
DEFAULT_TEMPLATE = ROOT / "README.template.md"
DEFAULT_OUTPUT = ROOT / "README.md"


def load_config(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def stats_url(username: str) -> str:
    return (
        "https://github-readme-stats.vercel.app/api"
        f"?username={username}"
        "&show_icons=true"
        "&hide_border=false"
        "&bg_color=050505"
        "&title_color=8AF76E"
        "&text_color=6CCF5F"
        "&icon_color=8AF76E"
        "&border_color=4E6E4A"
    )


def streak_url(username: str) -> str:
    return (
        "https://github-readme-streak-stats.herokuapp.com"
        f"?user={username}"
        "&background=050505"
        "&border=4E6E4A"
        "&stroke=4E6E4A"
        "&ring=6CCF5F"
        "&fire=8AF76E"
        "&currStreakLabel=8AF76E"
        "&sideLabels=6CCF5F"
        "&currStreakNum=8AF76E"
        "&sideNums=6CCF5F"
        "&dates=4E6E4A"
    )


def langs_url(username: str) -> str:
    return (
        "https://github-readme-stats.vercel.app/api/top-langs"
        f"?username={username}"
        "&layout=compact"
        "&bg_color=050505"
        "&title_color=8AF76E"
        "&text_color=6CCF5F"
        "&border_color=4E6E4A"
    )


def badge(label: str, message: str, color: str = "4E6E4A") -> str:
    from urllib.parse import quote

    return f"https://img.shields.io/badge/{quote(label)}-{quote(message)}-{color}?style=flat-square"


def render_projects(projects: list[dict]) -> str:
    lines = ["| Project | Description |", "| --- | --- |"]
    for project in projects:
        lines.append(f"| [{project['name']}]({project['url']}) | {project['desc']} |")
    return "\n".join(lines)


def render_tech_stack(stack: list[str]) -> str:
    badges = []
    for item in stack:
        slug = item.replace(" ", "%20")
        badges.append(f"![{item}]({badge(item, 'terminal', '1A5C12')})")
    return " ".join(badges)


def render_template(cfg: dict, template_path: Path) -> str:
    gh = cfg["github"]
    identity = cfg["identity"]
    username = gh["username"]

    replacements = {
        "{{NAME}}": identity["name"],
        "{{TAGLINE}}": identity.get("tagline", identity["role"]),
        "{{USERNAME}}": username,
        "{{STATS_URL}}": stats_url(username),
        "{{STREAK_URL}}": streak_url(username),
        "{{LANGS_URL}}": langs_url(username),
        "{{PROJECTS_TABLE}}": render_projects(gh["featured_projects"]),
        "{{TECH_STACK_BADGES}}": render_tech_stack(gh["tech_stack"]),
        "{{LINKEDIN}}": gh["social"]["linkedin"],
        "{{EMAIL}}": gh["social"]["email"],
        "{{GITHUB}}": gh["social"]["github"],
        "{{RESUME_URL}}": gh["resume_url"],
    }

    content = template_path.read_text(encoding="utf-8")
    for key, value in replacements.items():
        content = content.replace(key, value)
    return content


def run(
    cfg: dict | None = None,
    template_path: Path | None = None,
    output_path: Path | None = None,
) -> Path:
    if cfg is None:
        cfg = load_config(DEFAULT_CONFIG)
    if template_path is None:
        template_path = DEFAULT_TEMPLATE
    if output_path is None:
        output_path = DEFAULT_OUTPUT

    readme = render_template(cfg, template_path)
    output_path.write_text(readme, encoding="utf-8")
    print(f"Wrote {output_path}")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate README.md")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    cfg = load_config(args.config)
    run(cfg, args.template, args.output)


if __name__ == "__main__":
    main()
