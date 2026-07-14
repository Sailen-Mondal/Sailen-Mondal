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


TECH_LOGOS = {
    "Java": ("https://cdn.jsdelivr.net/gh/devicons/devicon/icons/java/java-original.svg", "", "https://www.java.com/"),
    "Spring Boot": ("springboot", "6DB33F", "https://spring.io/projects/spring-boot"),
    "Hibernate": ("hibernate", "59666C", "https://hibernate.org/"),
    "PostgreSQL": ("postgresql", "4169E1", "https://www.postgresql.org/"),
    "MongoDB": ("mongodb", "47A248", "https://www.mongodb.com/"),
    "Redis": ("redis", "DC382D", "https://redis.io/"),
    "React": ("react", "61DAFB", "https://react.dev/"),
    "Docker": ("docker", "2496ED", "https://www.docker.com/"),
    "GitHub Actions": ("githubactions", "2088FF", "https://github.com/features/actions"),
    "Linux": ("linux", "FCC624", "https://www.linux.org/"),
    "LangChain": ("langchain", "1C3C3C", "https://www.langchain.com/"),
    "OpenRouter": ("openrouter", "6B57FF", "https://openrouter.ai/"),
    "Gemini": ("googlegemini", "4285F4", "https://gemini.google.com/"),
}


def render_tech_stack(stack: list[str]) -> str:
    rows = []
    for start in range(0, len(stack), 7):
        items = stack[start : start + 7]
        logos = []
        labels = []
        for item in items:
            slug, color, url = TECH_LOGOS[item]
            icon_url = slug if slug.startswith("https://") else f"https://cdn.simpleicons.org/{slug}/{color}"
            logos.append(
                f'<a href="{url}"><img alt="{item}" src="{icon_url}" width="38" height="38" /></a>'
            )
            labels.append(item)
        rows.append('<p align="center">' + "&nbsp;&nbsp;".join(logos) + "</p>")
        rows.append('<p align="center"><sub>' + " &middot; ".join(labels) + "</sub></p>")
    return "\n".join(rows)


def render_template(cfg: dict, template_path: Path) -> str:
    gh = cfg["github"]
    identity = cfg["identity"]
    username = gh["username"]

    replacements = {
        "{{NAME}}": identity["name"],
        "{{TAGLINE}}": identity.get("tagline", identity["role"]),
        "{{USERNAME}}": username,
        "{{CAREER_COPILOT_URL}}": gh["featured_projects"][0]["url"],
        "{{WHATSAPP_ASSISTANT_URL}}": gh["featured_projects"][1]["url"],
        "{{TECH_STACK_LOGOS}}": render_tech_stack(gh["tech_stack"]),
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
