#!/usr/bin/env python3
"""Generate an animated terminal-style SVG with live GitHub stats.

Run daily by .github/workflows/daily-commit.yml. Uses only stdlib (urllib)
plus GH_TOKEN from the environment for API auth.
"""
import json
import os
import urllib.request
from datetime import datetime, timezone
from xml.sax.saxutils import escape

USERNAME = "jimididit"
TOKEN = os.environ.get("GH_TOKEN", "")
OUT_PATH = "terminal-stats.svg"

API = "https://api.github.com"


def gh_get(path):
    req = urllib.request.Request(f"{API}{path}")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def fetch_stats():
    repos = []
    page = 1
    while True:
        batch = gh_get(f"/users/{USERNAME}/repos?per_page=100&page={page}&type=owner")
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    total_stars = sum(r.get("stargazers_count", 0) for r in repos)
    lang_counts = {}
    for r in repos:
        lang = r.get("language")
        if lang:
            lang_counts[lang] = lang_counts.get(lang, 0) + 1
    top_lang = max(lang_counts, key=lang_counts.get) if lang_counts else "N/A"

    return {
        "repos": len(repos),
        "stars": total_stars,
        "top_lang": top_lang,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }


# ponytail: hardcoded line list, add a template arg if lines need to vary per-run
def build_lines(stats):
    return [
        ("$ whoami", "jimididit — security researcher & purple teamer"),
        ("$ stats --github", f"repos: {stats['repos']}  stars: {stats['stars']}  top-lang: {stats['top_lang']}"),
        ("$ status", f"last sync: {stats['date']}"),
    ]


SVG_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<svg width="560" height="{height}" viewBox="0 0 560 {height}" xmlns="http://www.w3.org/2000/svg" font-family="'Fira Code','Consolas',monospace">
  <defs>
    <clipPath id="rounded"><rect width="560" height="{height}" rx="10" ry="10"/></clipPath>
  </defs>
  <g clip-path="url(#rounded)">
    <rect width="560" height="{height}" fill="#0d1117"/>
    <rect width="560" height="28" fill="#161b22"/>
    <circle cx="16" cy="14" r="5" fill="#ff5f56"/>
    <circle cx="34" cy="14" r="5" fill="#ffbd2e"/>
    <circle cx="52" cy="14" r="5" fill="#27c93f"/>
    <text x="280" y="18" fill="#8b949e" font-size="12" text-anchor="middle">jimi@nokturnal:~</text>
{rows}
  </g>
  <rect width="559" height="{height_minus1}" rx="10" ry="10" fill="none" stroke="#30363d"/>
</svg>
"""

ROW_TEMPLATE = """    <text x="16" y="{y}" font-size="14">
      <tspan fill="#1abc9c">{prompt}</tspan>
    </text>
    <text x="16" y="{y2}" fill="#c9d1d9" font-size="14" opacity="0">
      {output}
      <animate attributeName="opacity" begin="{delay}s" dur="0.4s" values="0;1" fill="freeze"/>
    </text>
"""


def render_svg(lines):
    rows = []
    y = 56
    delay = 0.3
    for prompt, output in lines:
        rows.append(ROW_TEMPLATE.format(y=y, y2=y + 20, prompt=escape(prompt), output=escape(output), delay=round(delay, 2)))
        y += 46
        delay += 0.8
    height = y + 12
    return SVG_TEMPLATE.format(height=height, height_minus1=height - 1, rows="".join(rows))


def main():
    stats = fetch_stats()
    lines = build_lines(stats)
    svg = render_svg(lines)
    with open(OUT_PATH, "w") as f:
        f.write(svg)
    print(f"Wrote {OUT_PATH} with stats: {stats}")


if __name__ == "__main__":
    main()
