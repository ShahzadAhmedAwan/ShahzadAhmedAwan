#!/usr/bin/env python3
"""Refresh self-hosted GitHub profile cards using GitHub's public pages/API."""

from __future__ import annotations

import datetime as dt
import html
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path
from textwrap import wrap


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
USERNAME = "ShahzadAhmedAwan"
BG = "#101714"
PANEL = "#17221c"
GRID = "#26362b"
TEXT = "#e7eee8"
MUTED = "#9eaea2"
LIME = "#c8f169"
MINT = "#95d5b2"
LEVELS = ("#1a251e", "#29452f", "#44733d", "#75a943", LIME)


def fetch(url: str, *, accept: str = "application/vnd.github+json") -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "ShahzadAhmedAwan-profile-readme/1.0", "Accept": accept},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def svg_text(x: int, y: int, value: str, size: int, color: str, weight: int = 400) -> str:
    return (
        f'<text x="{x}" y="{y}" fill="{color}" font-family="Segoe UI,Arial,sans-serif" '
        f'font-size="{size}" font-weight="{weight}">{html.escape(value)}</text>'
    )


def write_svg(name: str, width: int, height: int, body: str) -> None:
    document = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img">'
        f'<rect width="{width}" height="{height}" rx="18" fill="{BG}"/>'
        f'<rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="17" '
        f'fill="none" stroke="{GRID}"/>{body}</svg>'
    )
    (ASSETS / name).write_text(document, encoding="utf-8")


def update_stats() -> None:
    profile = json.loads(fetch(f"https://api.github.com/users/{USERNAME}"))
    if not isinstance(profile, dict) or profile.get("login", "").lower() != USERNAME.lower():
        raise RuntimeError(f"GitHub profile {USERNAME} was not found in the public API response.")
    repos: list[dict] = []
    page = 1
    while True:
        url = (
            f"https://api.github.com/users/{USERNAME}/repos?type=owner&sort=updated"
            f"&per_page=100&page={page}"
        )
        batch = json.loads(fetch(url))
        if not isinstance(batch, list):
            raise RuntimeError("GitHub did not return a public repository list.")
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    star_count = sum(int(repo.get("stargazers_count", 0)) for repo in repos)
    original_repos = sum(1 for repo in repos if not repo.get("fork", False))
    body = [
        svg_text(28, 39, "PUBLIC PROFILE SIGNALS", 13, MINT, 700),
        svg_text(28, 76, "Shahzad Ahmed Awan  /  GitHub", 20, TEXT, 600),
    ]
    tiles = [
        ("FOLLOWERS", str(profile.get("followers", 0))),
        ("PUBLIC REPOS", str(profile.get("public_repos", 0))),
        ("ORIGINAL PROJECTS", str(original_repos)),
        ("STARS EARNED", str(star_count)),
    ]
    for index, (label, value) in enumerate(tiles):
        x = 28 + index * 214
        body.append(f'<rect x="{x}" y="105" width="194" height="90" rx="12" fill="{PANEL}"/>')
        body.append(svg_text(x + 16, 137, label, 11, MUTED, 700))
        body.append(svg_text(x + 16, 177, value, 28, LIME, 700))
    body.append(svg_text(28, 225, "github.com/ShahzadAhmedAwan  ·  refreshed daily", 12, MUTED))
    write_svg("profile-stats.svg", 900, 250, "".join(body))

    language_counts = Counter(
        repo.get("language") for repo in repos if repo.get("language") and not repo.get("fork", False)
    )
    ranked = language_counts.most_common(8)
    total = sum(language_counts.values()) or 1
    body = [
        svg_text(28, 39, "LANGUAGE MIX", 13, MINT, 700),
        svg_text(28, 76, "Primary language by original repository", 20, TEXT, 600),
    ]
    palette = [LIME, MINT, "#8ba7e8", "#e7b85c", "#cf8df0", "#70c7d6", "#ff8a72", "#a2b0a5"]
    bar_x, bar_y, bar_w = 28, 100, 844
    cursor = bar_x
    if ranked:
        for index, (language, count) in enumerate(ranked):
            segment = max(3, round(bar_w * count / total))
            body.append(f'<rect x="{cursor}" y="{bar_y}" width="{segment}" height="12" rx="6" fill="{palette[index]}"/>')
            cursor += segment + 3
        for index, (language, count) in enumerate(ranked):
            column, row = index % 4, index // 4
            x, y = 28 + column * 214, 149 + row * 42
            body.append(f'<circle cx="{x + 5}" cy="{y - 4}" r="5" fill="{palette[index]}"/>')
            percent = round(count * 100 / total)
            body.append(svg_text(x + 17, y, f"{language}  ·  {percent}%", 14, TEXT, 600))
    else:
        body.append(svg_text(28, 145, "Language data will appear after your first repository sync.", 14, MUTED))
    body.append(svg_text(28, 225, "Repository count, not lines of code  ·  refreshed daily", 12, MUTED))
    write_svg("languages.svg", 900, 250, "".join(body))

    active = [repo for repo in repos if not repo.get("fork", False)]
    active.sort(
        key=lambda repo: (
            repo.get("pushed_at") or repo.get("updated_at") or repo.get("created_at") or "",
            int(repo.get("stargazers_count", 0)),
        ),
        reverse=True,
    )
    body = [
        svg_text(28, 39, "BUILD LOG  /  RECENT PUBLIC PROJECTS", 13, MINT, 700),
        svg_text(28, 72, "Selected from your latest original repositories", 18, TEXT, 600),
    ]
    projects = active[:3]
    if projects:
        for index, repo in enumerate(projects):
            x = 28 + index * 286
            body.append(f'<rect x="{x}" y="92" width="270" height="198" rx="13" fill="{PANEL}" stroke="{GRID}"/>')
            body.append(svg_text(x + 16, 118, f"PROJECT  /  0{index + 1}", 10, MINT, 700))
            name = str(repo.get("name") or "Repository")
            if len(name) > 26:
                name = name[:23] + "…"
            body.append(svg_text(x + 16, 151, name, 17, TEXT, 700))
            description = str(repo.get("description") or "Public repository")
            lines = wrap(description, width=31, break_long_words=True, max_lines=3)
            for row, line in enumerate(lines):
                body.append(svg_text(x + 16, 178 + row * 19, line, 12, MUTED))
            language = str(repo.get("language") or "Mixed stack")
            stars = int(repo.get("stargazers_count", 0))
            body.append(f'<path d="M{x + 16} 250h238" stroke="{GRID}"/>')
            body.append(svg_text(x + 16, 274, f"{language}   ·   ★ {stars}", 12, LIME, 600))
    else:
        body.append(f'<rect x="28" y="92" width="844" height="198" rx="13" fill="{PANEL}" stroke="{GRID}"/>')
        body.append(svg_text(50, 148, "No public repositories returned yet", 18, TEXT, 600))
        body.append(svg_text(50, 180, "Check that the profile handle is correct, then run the card sync again.", 13, MUTED))
    write_svg("projects.svg", 900, 320, "".join(body))


def contribution_cells(document: str) -> list[tuple[dt.date, int, int]]:
    cells: list[tuple[dt.date, int, int]] = []
    for tag in re.findall(r"<rect\b[^>]*>", document):
        date_match = re.search(r'data-date=[\'"]([^\'"]+)', tag)
        count_match = re.search(r'data-count=[\'"]([^\'"]+)', tag)
        level_match = re.search(r'data-level=[\'"]([^\'"]+)', tag)
        if not (date_match and count_match and level_match):
            continue
        try:
            day = dt.date.fromisoformat(date_match.group(1))
            count = int(count_match.group(1))
            level = max(0, min(4, int(level_match.group(1))))
        except (TypeError, ValueError):
            continue
        cells.append((day, count, level))
    return cells


def update_contributions() -> None:
    document = fetch(f"https://github.com/users/{USERNAME}/contributions", accept="text/html").decode("utf-8", "replace")
    cells = contribution_cells(document)
    if len(cells) < 300:
        raise RuntimeError(f"GitHub returned only {len(cells)} contribution cells; keeping the previous chart.")

    today = dt.date.today()
    start = today - dt.timedelta(days=363)
    start -= dt.timedelta(days=(start.weekday() + 1) % 7)
    shown = [cell for cell in cells if start <= cell[0] <= today]
    week_count = ((today - start).days // 7) + 1
    left, top, cell_size, gap = 42, 63, 11, 4
    graph_width = week_count * (cell_size + gap)
    body = [
        svg_text(28, 37, "CONTRIBUTION CALENDAR", 13, MINT, 700),
        svg_text(28, 65 + 7 * (cell_size + gap) + 12, "Daily contributions · last 12 months", 12, MUTED),
    ]
    months: dict[tuple[int, int], str] = {}
    for day, count, level in shown:
        week = (day - start).days // 7
        row = (day.weekday() + 1) % 7
        x = left + week * (cell_size + gap)
        y = top + row * (cell_size + gap)
        body.append(
            f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" rx="3" '
            f'fill="{LEVELS[level]}" aria-label="{day.isoformat()}: {count} contributions"/>'
        )
        if day.day <= 7:
            months[(week, day.month)] = day.strftime("%b").upper()
    for (week, _month), label in months.items():
        body.append(svg_text(left + week * (cell_size + gap), 52, label, 9, MUTED, 600))
    body.append(svg_text(28, 225, "Source: GitHub public contribution calendar · refreshed daily", 12, MUTED))
    width = max(900, left * 2 + graph_width)
    write_svg("contributions.svg", width, 250, "".join(body))


def main() -> int:
    ASSETS.mkdir(parents=True, exist_ok=True)
    completed = 0
    try:
        update_stats()
        print("Updated profile-stats.svg, languages.svg, and projects.svg")
        completed += 1
    except (OSError, ValueError, urllib.error.URLError, RuntimeError) as error:
        print(f"::warning::Profile/repository card refresh failed: {error}", file=sys.stderr)
    try:
        update_contributions()
        print("Updated contributions.svg")
        completed += 1
    except (OSError, ValueError, urllib.error.URLError, RuntimeError) as error:
        print(f"::warning::Contribution chart refresh failed: {error}", file=sys.stderr)
    if not completed:
        print("No cards were refreshed; existing SVGs are unchanged.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
