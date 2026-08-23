#!/usr/bin/env python3
"""Bake the tech-stack panel into a static SVG with real brand marks.

Icon geometry is pulled from the Simple Icons CDN once, at authoring time, and
embedded directly - so the rendered card has no runtime dependency on any
third-party service. Re-run this only when the stack itself changes.

    python .github/scripts/build_stack.py
"""

from __future__ import annotations

import pathlib
import re
import sys
import urllib.error
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import build_cards as bc  # noqa: E402  (shared THEMES / chrome / text_width)

CDN = "https://cdn.simpleicons.org/{slug}"
OUT = pathlib.Path("assets")

# (label, simple-icons slug or None, brand colour, dark-mode override, light-mode override)
# Overrides exist only where the true brand colour disappears into the
# background - near-black marks on dark, near-white marks on light.
GROUPS: list[tuple[str, list[tuple]]] = [
    ("BLOCKCHAIN &amp; WEB3", [
        ("Solidity",   "solidity",    "#363636", "#D4D4D4", "#363636"),
        ("Ethereum",   "ethereum",    "#7B7BEA", None,      "#5A5AD6"),
        ("Algorand",   "algorand",    "#000000", "#E6EDF3", "#000000"),
        ("Foundry",    None,          "#FF6B35", None,      None),
        ("PyTeal",     None,          "#38BDF8", None,      "#0369A1"),
        ("IPFS",       "ipfs",        "#65C2CB", None,      None),
    ]),
    ("LANGUAGES", [
        ("TypeScript", "typescript",  "#3178C6", "#5CA3E8", None),
        ("Python",     "python",      "#3776AB", "#5C9FD6", None),
        ("JavaScript", "javascript",  "#F7DF1E", None,      "#C2AD00"),
    ]),
    ("FRONTEND", [
        ("React",      "react",       "#61DAFB", None,      "#0A8FB5"),
        ("Next.js",    "nextdotjs",   "#000000", "#E6EDF3", "#000000"),
        ("Vite",       "vite",        "#8B5CF6", None,      None),
        ("Tailwind",   "tailwindcss", "#06B6D4", None,      None),
    ]),
    ("AI &amp; DATA", [
        ("TensorFlow", "tensorflow",  "#FF6F00", None,      None),
        ("scikit-learn", "scikitlearn", "#F7931E", None,    "#C2740F"),
        ("NumPy",      "numpy",       "#4DABCF", None,      None),
        ("Pandas",     "pandas",      "#9B59B6", None,      None),
        ("Jupyter",    "jupyter",     "#F37626", None,      None),
        ("Google ADK", "googlegemini", "#8E7CF8", None,     "#6D4AEA"),
    ]),
    ("INFRA", [
        ("Supabase",   "supabase",    "#3FCF8E", None,      "#1F9E67"),
        ("Firebase",   "firebase",    "#FFCA28", None,      "#B8860B"),
        ("Vercel",     "vercel",      "#000000", "#E6EDF3", "#000000"),
        ("Node.js",    "nodedotjs",   "#5FA04E", None,      None),
        ("Git",        "git",         "#F05032", None,      None),
    ]),
]


def fetch_glyph(slug: str) -> str:
    """Return the inner markup of a 24x24 Simple Icons SVG."""
    req = urllib.request.Request(CDN.format(slug=slug), headers={"User-Agent": "profile-stack-builder"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode("utf-8")
    inner = re.sub(r"^.*?<svg[^>]*>|</svg>\s*$", "", body, flags=re.S).strip()
    # Drop any hard-coded fill so the wrapping <g> controls colour.
    inner = re.sub(r'\sfill="[^"]*"', "", inner)
    if "<path" not in inner:
        raise RuntimeError(f"no path data for {slug}")
    return inner


def build(theme_name: str, t: dict, glyphs: dict[str, str]) -> str:
    W = 1000
    pad_x, icon, gap, chip_h = 14, 15.0, 8.0, 32.0
    label_size, chip_gap, row_gap = 11.5, 9.0, 16.0

    # ---- lay chips out first so the canvas can be sized to fit ----
    rows: list[list[dict]] = []
    group_at: list[tuple[str, int]] = []
    for gname, entries in GROUPS:
        group_at.append((gname, len(rows)))
        row: list[dict] = []
        x = 48.0
        for label, slug, brand, dark_c, light_c in entries:
            color = (dark_c if theme_name == "dark" else light_c) or brand
            has_icon = slug is not None
            w = pad_x * 2 + bc.text_width(label, label_size, True) + (icon + gap if has_icon else 0)
            if x + w > W - 48:
                rows.append(row)
                row, x = [], 48.0
            row.append({"label": label, "slug": slug, "color": color, "x": x, "w": w})
            x += w + chip_gap
        rows.append(row)

    H = 42 + 26
    row_y: list[float] = []
    gi = 0
    for i, _row in enumerate(rows):
        while gi < len(group_at) and group_at[gi][1] == i:
            H += 26  # group heading
            gi += 1
        row_y.append(H)
        H += chip_h + row_gap
    H = int(H + 18)

    svg = bc.head(W, H, "Tech stack").replace("%GRID%", t["grid"])
    svg += bc.chrome(t, W, H, "~/stack", "--all --group domain")
    svg += f'<g clip-path="url(#clip)">\n'
    svg += f'  <rect x="1" y="43" width="{W - 2}" height="{H - 44}" fill="url(#grid)" opacity="0.5"/>\n'

    heading_before = {idx: name for name, idx in group_at}
    delay = 0.08
    for i, row in enumerate(rows):
        if i in heading_before:
            svg += (f'  <g class="r" style="animation-delay:{delay:.2f}s">'
                    f'<text class="m" x="48" y="{row_y[i] - 10:.0f}" font-size="10" letter-spacing="2.2" '
                    f'fill="{t["cyan"]}">&#187; {heading_before[i]}</text></g>\n')
            delay += 0.05
        for chip in row:
            y = row_y[i]
            svg += f'  <g class="r" style="animation-delay:{delay:.2f}s">\n'
            svg += (f'    <rect x="{chip["x"]:.1f}" y="{y:.1f}" width="{chip["w"]:.1f}" height="{chip_h}" '
                    f'rx="{chip_h / 2:.1f}" fill="{t["panel"]}" stroke="{t["stroke"]}"/>\n')
            tx = chip["x"] + pad_x
            if chip["slug"]:
                s = icon / 24.0
                gy = y + (chip_h - icon) / 2
                svg += (f'    <g transform="translate({tx:.1f} {gy:.1f}) scale({s:.4f})" '
                        f'fill="{chip["color"]}">{glyphs[chip["slug"]]}</g>\n')
                tx += icon + gap
            else:
                svg += f'    <circle cx="{tx + 5:.1f}" cy="{y + chip_h / 2:.1f}" r="4" fill="{chip["color"]}"/>\n'
                tx += icon + gap
            svg += (f'    <text class="m" x="{tx:.1f}" y="{y + chip_h / 2 + 4:.1f}" font-size="{label_size}" '
                    f'fill="{t["text"]}">{chip["label"]}</text>\n')
            svg += f'  </g>\n'
            delay += 0.022

    svg += f'  <rect class="sweep" x="0" y="43" width="200" height="{H - 44}" fill="url(#sweepg)"/>\n'
    svg += '</g>\n</svg>\n'
    return svg


def main() -> int:
    slugs = sorted({s for _, entries in GROUPS for _, s, *_ in entries if s})
    glyphs: dict[str, str] = {}
    for slug in slugs:
        try:
            glyphs[slug] = fetch_glyph(slug)
        except (urllib.error.URLError, RuntimeError, TimeoutError) as e:
            print(f"error: {slug}: {e}", file=sys.stderr)
            return 1
    print(f"fetched {len(glyphs)} brand marks")

    OUT.mkdir(parents=True, exist_ok=True)
    for name, t in bc.THEMES.items():
        path = OUT / f"stack-{name}.svg"
        path.write_text(build(name, t, glyphs), encoding="utf-8")
        print(f"wrote {path} ({path.stat().st_size}b)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
