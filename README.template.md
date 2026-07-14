# {{NAME}}

```text
$ whoami
{{NAME}}
$ role
Java Backend Developer
$ status
Building production systems on the terminal.
```

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/hero-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/hero-light.svg">
  <img alt="{{NAME}} - terminal profile" src="assets/hero-dark.svg">
</picture>

## GitHub Stats

```bash
$ gh api user --jq .login
{{USERNAME}}
```

<p align="center">
  <img alt="GitHub Stats" src="{{STATS_URL}}" />
</p>

<p align="center">
  <img alt="GitHub Streak" src="{{STREAK_URL}}" />
</p>

<p align="center">
  <img alt="Top Languages" src="{{LANGS_URL}}" />
</p>

## Featured Projects

```bash
$ ls ~/projects
```

{{PROJECTS_TABLE}}

## Tech Stack

```bash
$ cat ~/.stack
```

{{TECH_STACK_BADGES}}

## Contact

```bash
$ cat ~/.contact
```

| Channel | Link |
| --- | --- |
| GitHub | [{{USERNAME}}]({{GITHUB}}) |
| LinkedIn | [Profile]({{LINKEDIN}}) |
| Email | [sailenmondal@gmail.com]({{EMAIL}}) |

## Resume

[![Resume](https://img.shields.io/badge/resume-view-4E6E4A?style=flat-square)]({{RESUME_URL}})

---

```bash
$ echo "Thanks for visiting" && exit 0
```
