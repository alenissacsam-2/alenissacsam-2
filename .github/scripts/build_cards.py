#!/usr/bin/env python3
"""Render branded SVG cards for the profile README from live GitHub data.

Depends only on the standard library so the workflow needs no install step.
Run with --mock to render from fixture data (no token required).

    python .github/scripts/build_cards.py --mock
    GITHUB_TOKEN=... python .github/scripts/build_cards.py
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

USER = "alenissacsam-2"
OUT = pathlib.Path("assets/generated")
API = "https://api.github.com/graphql"

# Cards to show under featured_work, in order. Unknown names are skipped, so
# this list is safe to edit without touching the rest of the script.
FEATURED = [
    "algorand-identity-verification",
    "blockchain-certificate-verification",
    "ethereum-identity-dapp",
    "AI-Powered-Infrastructure-Design-with-Google-ADK",
    "txline-prediction-markets",
    "NN-From-Scratch-for-MNIST",
]

# Languages that say nothing useful about the work.
LANG_SKIP = {"HTML", "CSS", "Makefile", "Dockerfile", "Shell", "Batchfile"}

THEMES = {
    "dark": dict(
        bg="#080C14", panel="#0B121C", bar="#0C1220", stroke="#1B2635",
        inner="#0E1826", grid="#16202D", track="#141F2B",
        text="#E6EDF3", muted="#7D8590", dim="#3E4C5A",
        cyan="#22D3EE", violet="#8B5CF6", green="#34D399", sky="#7DD3FC",
        amber="#FBBF24",
        heat=["#141F2B", "#0D4A5A", "#1487A0", "#22D3EE", "#8DE6F7"],
    ),
    "light": dict(
        bg="#FFFFFF", panel="#F6F8FA", bar="#EEF2F6", stroke="#D5DCE3",
        inner="#F0F4F8", grid="#EAEEF2", track="#E4E9EF",
        text="#1F2328", muted="#59636E", dim="#98A1AB",
        cyan="#0E7490", violet="#6D28D9", green="#047857", sky="#0369A1",
        amber="#B45309",
        heat=["#E7ECF1", "#B4E4F0", "#5FC6DE", "#1E96B4", "#0E6D85"],
    ),
}

QUERY = """
query($login: String!) {
  user(login: $login) {
    login
    followers { totalCount }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false,
                 orderBy: {field: PUSHED_AT, direction: DESC}) {
      totalCount
      nodes {
        name
        description
        stargazerCount
        forkCount
        pushedAt
        primaryLanguage { name color }
        languages(first: 12, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


# ---------------------------------------------------------------- data


def fetch(token: str) -> dict:
    body = json.dumps({"query": QUERY, "variables": {"login": USER}}).encode()
    req = urllib.request.Request(
        API,
        data=body,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": f"{USER}-profile-cards",
        },
    )
    with urllib.request.urlopen(req, timeout=45) as r:
        payload = json.load(r)
    if "errors" in payload:
        raise RuntimeError(f"GraphQL errors: {payload['errors']}")
    user = (payload.get("data") or {}).get("user")
    if not user:
        raise RuntimeError("GraphQL returned no user")
    return user


def fetch_rest() -> dict:
    """Seed real repo/language data from the public REST API, no token needed.

    Contribution totals and streaks are only exposed to authenticated callers,
    so those come back as None and render as a placeholder until the workflow
    runs with GITHUB_TOKEN. Better an honest dash than an invented number.
    """
    def get(url: str):
        req = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{USER}-profile-cards",
        })
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)

    profile = get(f"https://api.github.com/users/{USER}")
    raw = get(f"https://api.github.com/users/{USER}/repos?per_page=100&sort=pushed")

    nodes = []
    for r in raw:
        if r["fork"]:
            continue
        try:
            langs = get(r["languages_url"])
        except urllib.error.URLError:
            langs = {}
        nodes.append({
            "name": r["name"],
            "description": r.get("description"),
            "stargazerCount": r["stargazers_count"],
            "forkCount": r["forks_count"],
            "pushedAt": r["pushed_at"],
            "primaryLanguage": ({"name": r["language"], "color": LANG_COLORS.get(r["language"], "#8B5CF6")}
                                if r.get("language") else None),
            "languages": {"edges": [
                {"size": size, "node": {"name": name, "color": LANG_COLORS.get(name, "#8B5CF6")}}
                for name, size in langs.items()
            ]},
        })

    return {
        "login": USER,
        "followers": {"totalCount": profile["followers"]},
        "repositories": {"totalCount": profile["public_repos"], "nodes": nodes},
        "contributionsCollection": None,
    }


# GraphQL hands back a colour per language; REST does not, so keep a small map
# for the languages that actually show up in these repos.
LANG_COLORS = {
    "TypeScript": "#3178c6", "JavaScript": "#f1e05a", "Python": "#3572A5",
    "Solidity": "#AA6746", "Jupyter Notebook": "#DA5B0B", "HTML": "#e34c26",
    "CSS": "#563d7c", "Shell": "#89e051", "C++": "#f34b7d", "Java": "#b07219",
    "Go": "#00ADD8", "Rust": "#dea584", "Ruby": "#701516", "PHP": "#4F5D95",
    "Dart": "#00B4AB", "Kotlin": "#A97BFF", "Swift": "#F05138", "SCSS": "#c6538c",
}


def mock() -> dict:
    """Fixture shaped exactly like the GraphQL response."""
    def repo(name, desc, stars, forks, lang, color, days, sizes):
        pushed = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
        return {
            "name": name,
            "description": desc,
            "stargazerCount": stars,
            "forkCount": forks,
            "pushedAt": pushed.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "primaryLanguage": {"name": lang, "color": color},
            "languages": {"edges": [
                {"size": s, "node": {"name": n, "color": c}} for n, c, s in sizes
            ]},
        }

    return {
        "login": USER,
        "followers": {"totalCount": 4},
        "repositories": {
            "totalCount": 15,
            "nodes": [
                repo("algorand-identity-verification",
                     "DID and trust-score system on Algorand with biometric and document verification",
                     0, 0, "TypeScript", "#3178c6", 1,
                     [("TypeScript", "#3178c6", 210000), ("Python", "#3572A5", 90000)]),
                repo("blockchain-certificate-verification",
                     "On-chain certificate registry - issue, template, batch-issue and verify credentials",
                     0, 0, "JavaScript", "#f1e05a", 1,
                     [("Solidity", "#AA6746", 120000), ("JavaScript", "#f1e05a", 160000)]),
                repo("ethereum-identity-dapp",
                     "Ethereum identity verification with face and voice checks plus server-side attestation",
                     0, 0, "TypeScript", "#3178c6", 1,
                     [("TypeScript", "#3178c6", 180000), ("Solidity", "#AA6746", 60000)]),
                repo("AI-Powered-Infrastructure-Design-with-Google-ADK",
                     "Multi-agent infrastructure design system built on Google's Agent Development Kit",
                     0, 0, "Jupyter Notebook", "#DA5B0B", 1,
                     [("Jupyter Notebook", "#DA5B0B", 300000), ("Python", "#3572A5", 40000)]),
                repo("txline-prediction-markets",
                     "Prediction market interface for on-chain event trading",
                     0, 0, "TypeScript", "#3178c6", 36,
                     [("TypeScript", "#3178c6", 95000)]),
                repo("NN-From-Scratch-for-MNIST",
                     "Neural network built from first principles - no ML frameworks, just NumPy",
                     0, 0, "Jupyter Notebook", "#DA5B0B", 1,
                     [("Jupyter Notebook", "#DA5B0B", 70000), ("Python", "#3572A5", 25000)]),
                repo("Order_Flow_Analyzer-NinjaTrader-Arena",
                     "Real-time order-flow and market-microstructure analysis",
                     0, 0, "JavaScript", "#f1e05a", 22,
                     [("JavaScript", "#f1e05a", 55000)]),
            ],
        },
        "contributionsCollection": {
            "totalCommitContributions": 486,
            "totalPullRequestContributions": 12,
            "restrictedContributionsCount": 0,
            "contributionCalendar": {
                "totalContributions": 512,
                "weeks": _mock_weeks(),
            },
        },
    }


def _mock_weeks() -> list[dict]:
    """53 weeks of plausible, deterministic activity ending today."""
    today = dt.date.today()
    start = today - dt.timedelta(days=today.weekday() + 1 + 52 * 7)
    weeks, seed = [], 7
    for w in range(53):
        days = []
        for dow in range(7):
            day = start + dt.timedelta(days=w * 7 + dow)
            if day > today:
                break
            seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
            roll = seed % 100
            count = 0 if roll < 34 else (roll % 11) + (6 if w > 47 else 0)
            days.append({"date": day.isoformat(), "contributionCount": count})
        weeks.append({"contributionDays": days})
    return weeks


def digest(user: dict) -> dict:
    repos = user["repositories"]["nodes"]
    contrib = user["contributionsCollection"]

    totals: dict[str, dict] = {}
    for r in repos:
        for edge in r["languages"]["edges"]:
            node = edge["node"]
            name = node["name"]
            if name in LANG_SKIP:
                continue
            slot = totals.setdefault(name, {"size": 0, "color": node.get("color") or "#8B5CF6"})
            slot["size"] += edge["size"]

    ranked = sorted(totals.items(), key=lambda kv: kv[1]["size"], reverse=True)[:6]
    grand = sum(v["size"] for _, v in ranked) or 1
    langs = [
        {"name": n, "color": v["color"], "pct": v["size"] * 100.0 / grand}
        for n, v in ranked
    ]

    by_name = {r["name"]: r for r in repos}
    picked = [by_name[n] for n in FEATURED if n in by_name]
    for r in repos:  # top up from most-recently-pushed if FEATURED is thin
        if len(picked) >= 6:
            break
        if r not in picked:
            picked.append(r)

    if contrib:
        weeks = contrib["contributionCalendar"].get("weeks", [])
        current, longest = streaks(weeks)
        commits = contrib["totalCommitContributions"] + contrib.get("restrictedContributionsCount", 0)
        contributions = contrib["contributionCalendar"]["totalContributions"]
        prs = contrib["totalPullRequestContributions"]
    else:
        # Seeded from REST: contribution data needs an authenticated caller.
        weeks, current, longest = [], None, None
        commits = contributions = prs = None

    return {
        "commits": commits,
        "contributions": contributions,
        "prs": prs,
        "repos": user["repositories"]["totalCount"],
        "followers": user["followers"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in repos),
        "streak": current,
        "longest": longest,
        "weeks": weeks,
        "langs": langs,
        "projects": picked[:6],
    }


def streaks(weeks: list[dict]) -> tuple[int, int]:
    """Current and longest run of consecutive active days.

    A zero-contribution *today* does not break the current streak - the day
    isn't over yet - but any earlier gap does.
    """
    days = [d for w in weeks for d in w["contributionDays"]]
    days.sort(key=lambda d: d["date"])
    if not days:
        return 0, 0

    longest = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] > 0 else 0
        longest = max(longest, run)

    today = dt.date.today().isoformat()
    tail = days[:-1] if (days[-1]["date"] == today and days[-1]["contributionCount"] == 0) else days
    current = 0
    for d in reversed(tail):
        if d["contributionCount"] == 0:
            break
        current += 1
    return current, longest


# ---------------------------------------------------------------- helpers


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


# Rough advance widths as a fraction of font-size, tuned for the mono/sans
# stacks used below. Good enough to wrap without a font library.
def text_width(s: str, size: float, mono: bool) -> float:
    if mono:
        return len(s) * size * 0.60
    w = 0.0
    for ch in s:
        if ch in "iljI.,:;'|!": w += 0.28
        elif ch in "ftr()[]{}/\\-": w += 0.36
        elif ch in "mwMW": w += 0.87
        elif ch.isupper(): w += 0.68
        else: w += 0.53
    return w * size


def wrap(s: str, size: float, limit: float, lines: int, mono: bool) -> list[str]:
    words = s.split()
    out: list[str] = []
    cur, used = "", 0
    for word in words:
        trial = f"{cur} {word}".strip()
        if text_width(trial, size, mono) <= limit or not cur:
            cur, used = trial, used + 1
            continue
        out.append(cur)
        if len(out) == lines:
            cur = ""
            break
        cur, used = word, used + 1
    if cur:
        out.append(cur)
    out = out[:lines]
    # Ran out of room mid-sentence: ellipsize the last line we kept.
    if used < len(words) and out:
        last = out[-1]
        while last and text_width(last + "...", size, mono) > limit:
            last = last[:-1]
        out[-1] = last.rstrip(" ,.;:-") + "..."
    return out


def ago(iso: str) -> str:
    when = dt.datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    days = (dt.datetime.now(dt.timezone.utc) - when).days
    if days <= 0: return "today"
    if days == 1: return "yesterday"
    if days < 30: return f"{days}d ago"
    if days < 365: return f"{days // 30}mo ago"
    return f"{days // 365}y ago"


def compact(n: int | None, suffix: str = "") -> str:
    """Short number, or an em dash when the value isn't available yet."""
    if n is None: return "—"
    if n >= 1_000_000: return f"{n / 1_000_000:.1f}M".replace(".0M", "M") + suffix
    if n >= 1_000: return f"{n / 1000:.1f}k".replace(".0k", "k") + suffix
    return f"{n}{suffix}"


def panel(t: dict, w: int, h: int, title: str, meta: str, accent: str) -> str:
    """Section frame for the body cards.

    Deliberately NOT the terminal window used by the hero - traffic lights on
    every card made the page read as one template stamped five times. These get
    a hairline accent edge and a titled rule instead, so the family resemblance
    survives without the repetition.
    """
    return f"""<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="13" fill="{t['bg']}" stroke="{t['stroke']}" stroke-width="1.5"/>
<g clip-path="url(#clip)">
  <rect x="1" y="1" width="{w - 2}" height="3" fill="{accent}"/>
  <rect x="34" y="31" width="3.5" height="18" rx="1.75" fill="{accent}"/>
  <text class="s" x="48" y="46" font-size="15" font-weight="700" letter-spacing="2.6" fill="{t['text']}">{esc(title)}</text>
  <text class="m" x="{w - 34}" y="46" font-size="11.5" text-anchor="end" fill="{t['dim']}">{esc(meta)}</text>
  <line x1="34" y1="64" x2="{w - 34}" y2="64" stroke="{t['stroke']}"/>
</g>"""


STYLE = """<style>
  .m { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
  .s { font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif; }
  text { text-rendering: geometricPrecision; }
  @keyframes rise { 0% { opacity:0; transform:translateY(8px) } 100% { opacity:1; transform:translateY(0) } }
  @keyframes grow { 0% { transform:scaleX(0) } 100% { transform:scaleX(1) } }
  @keyframes glide { 0% { transform:translateX(-200px) } 100% { transform:translateX(%WIDTH%px) } }
  .r { opacity:0; animation: rise .7s ease-out forwards; }
  .g { transform-origin:left center; animation: grow 1.1s cubic-bezier(.25,.9,.3,1) forwards; transform:scaleX(0); }
  .sweep { animation: glide 8s cubic-bezier(.4,0,.6,1) infinite; }

  /* Resolve to the finished state, not frame zero - otherwise every
     faded-in row would sit at opacity 0 and the card would look empty. */
  @media (prefers-reduced-motion: reduce) {
    .r { opacity:1; transform:none; animation:none; }
    .g { transform:scaleX(1); animation:none; }
    .sweep { opacity:0; animation:none; }
  }
</style>"""


def head(w: int, h: int, label: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" '
        f'height="{h}" role="img" aria-label="{esc(label)}">\n'
        f'<defs>\n'
        f'  <clipPath id="clip"><rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="13"/></clipPath>\n'
        f'  <linearGradient id="sweepg" x1="0" y1="0" x2="1" y2="0">\n'
        f'    <stop offset="0%" stop-color="#22D3EE" stop-opacity="0"/>\n'
        f'    <stop offset="50%" stop-color="#22D3EE" stop-opacity="0.13"/>\n'
        f'    <stop offset="100%" stop-color="#22D3EE" stop-opacity="0"/>\n'
        f'  </linearGradient>\n'
        f'  <pattern id="grid" width="26" height="26" patternUnits="userSpaceOnUse">\n'
        f'    <path d="M26 0H0V26" fill="none" stroke="%GRID%" stroke-width="1"/>\n'
        f'  </pattern>\n'
        f'</defs>\n' + STYLE.replace("%WIDTH%", str(w)) + "\n"
    )


# ---------------------------------------------------------------- telemetry


def render_telemetry(d: dict, t: dict) -> str:
    W, H = 1000, 348
    svg = head(W, H, "GitHub telemetry").replace("%GRID%", t["grid"])
    svg += panel(t, W, H, "TELEMETRY", "live · last 12 months", t["sky"])
    svg += f'<g clip-path="url(#clip)">\n'
    svg += f'  <rect x="1" y="65" width="{W - 2}" height="{H - 66}" fill="url(#grid)" opacity="0.5"/>\n'

    # Ordered so the durable numbers lead. Activity counters sit below them
    # because they depend on commit attribution, which can legitimately read
    # low - a card that opens with four zeros undersells the work.
    stats = [
        ("projects shipped", compact(d["repos"]), t["cyan"]),
        ("languages", compact(len(d["langs"])), t["violet"]),
        ("contributions", compact(d["contributions"]), t["green"]),
        ("commits", compact(d["commits"]), t["sky"]),
        ("current streak", compact(d["streak"], "d"), t["amber"]),
        ("longest streak", compact(d["longest"], "d"), t["violet"]),
    ]
    for i, (label, value, color) in enumerate(stats):
        cx = 48 + (i % 2) * 236
        cy = 118 + (i // 2) * 74
        svg += f'  <g class="r" style="animation-delay:{0.10 + i * 0.07:.2f}s">\n'
        svg += f'    <rect x="{cx - 14}" y="{cy - 36}" width="3" height="48" rx="1.5" fill="{color}"/>\n'
        svg += f'    <text class="s" x="{cx}" y="{cy}" font-size="31" font-weight="800" fill="{t["text"]}">{value}</text>\n'
        svg += f'    <text class="m" x="{cx}" y="{cy + 18}" font-size="9.5" letter-spacing="1.8" fill="{t["dim"]}">{label.upper()}</text>\n'
        svg += f'  </g>\n'

    svg += f'  <line x1="512" y1="86" x2="512" y2="{H - 34}" stroke="{t["stroke"]}"/>\n'

    # ── language distribution ──
    lx, lw = 548, 404
    svg += f'  <g class="r" style="animation-delay:.30s">\n'
    svg += f'    <text class="m" x="{lx}" y="100" font-size="10" letter-spacing="2.2" fill="{t["cyan"]}">LANGUAGE DISTRIBUTION</text>\n'
    svg += f'  </g>\n'
    svg += f'  <defs><clipPath id="langclip"><rect x="{lx}" y="112" width="{lw}" height="11" rx="5.5"/></clipPath></defs>\n'
    svg += f'  <rect x="{lx}" y="112" width="{lw}" height="11" rx="5.5" fill="{t["track"]}"/>\n'
    svg += f'  <g clip-path="url(#langclip)">\n'
    svg += f'    <g class="g" style="transform-origin:{lx}px 117.5px; animation-delay:.35s">\n'
    off = 0.0
    for lang in d["langs"]:
        seg = lw * lang["pct"] / 100.0
        # +0.5 overlap keeps hairline gaps from showing between segments
        svg += (f'      <rect x="{lx + off:.2f}" y="112" width="{seg + 0.5:.2f}" height="11" '
                f'fill="{lang["color"]}"/>\n')
        off += seg
    svg += f'    </g>\n  </g>\n'

    for i, lang in enumerate(d["langs"]):
        col, row = i % 2, i // 2
        ex = lx + col * 206
        ey = 150 + row * 24
        svg += f'  <g class="r" style="animation-delay:{0.42 + i * 0.05:.2f}s">\n'
        svg += f'    <circle cx="{ex + 4}" cy="{ey - 4}" r="4.5" fill="{lang["color"]}"/>\n'
        svg += f'    <text class="m" x="{ex + 16}" y="{ey}" font-size="11.5" fill="{t["text"]}">{esc(lang["name"])}</text>\n'
        svg += f'    <text class="m" x="{ex + 186}" y="{ey}" font-size="11" text-anchor="end" fill="{t["dim"]}">{lang["pct"]:.1f}%</text>\n'
        svg += f'  </g>\n'

    # ── contribution heatmap, rendered from the real calendar ──
    svg += f'  <g class="r" style="animation-delay:.58s">\n'
    svg += f'    <text class="m" x="{lx}" y="234" font-size="10" letter-spacing="2.2" fill="{t["cyan"]}">CONTRIBUTION CALENDAR</text>\n'
    svg += f'  </g>\n'
    svg += render_heatmap(d["weeks"], t, lx, 244)

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    seeded = d["commits"] is None
    dotc = t["amber"] if seeded else t["green"]
    note = (f"seeded {stamp} &#183; contribution totals land on the first authenticated sync"
            if seeded else
            f"synced {stamp} &#183; regenerated daily from the github api")
    svg += f'  <g class="r" style="animation-delay:.80s">\n'
    svg += f'    <circle cx="52" cy="{H - 26}" r="3.5" fill="{dotc}"/>\n'
    svg += f'    <text class="m" x="64" y="{H - 22}" font-size="10.5" fill="{t["dim"]}">{note}</text>\n'
    svg += f'  </g>\n'
    svg += f'  <rect class="sweep" x="0" y="65" width="200" height="{H - 66}" fill="url(#sweepg)"/>\n'
    svg += '</g>\n</svg>\n'
    return svg


def render_heatmap(weeks: list[dict], t: dict, x0: int, y0: int) -> str:
    """53x7 grid of contribution cells, coloured on a five-step brand ramp."""
    cell, gap = 5.2, 1.6
    step = cell + gap
    if not weeks:
        # Seeded run: draw the empty year so the layout holds its shape until
        # the first authenticated sync fills it in.
        today = dt.date.today()
        start = today - dt.timedelta(days=today.weekday() + 1 + 52 * 7)
        weeks = [{"contributionDays": [
            {"date": (start + dt.timedelta(days=w * 7 + dow)).isoformat(), "contributionCount": 0}
            for dow in range(7) if start + dt.timedelta(days=w * 7 + dow) <= today
        ]} for w in range(53)]
    counts = [d["contributionCount"] for w in weeks for d in w["contributionDays"]]
    peak = max(counts) if counts else 0

    def bucket(n: int) -> str:
        if n <= 0: return t["heat"][0]
        if peak <= 1: return t["heat"][3]
        frac = n / peak
        if frac <= 0.25: return t["heat"][1]
        if frac <= 0.50: return t["heat"][2]
        if frac <= 0.80: return t["heat"][3]
        return t["heat"][4]

    out = [f'  <g class="r" style="animation-delay:.64s">\n']
    for wi, week in enumerate(weeks[-53:]):
        for day in week["contributionDays"]:
            dow = dt.date.fromisoformat(day["date"]).isoweekday() % 7  # Sun=0
            cx = x0 + wi * step
            cy = y0 + dow * step
            out.append(f'    <rect x="{cx:.1f}" y="{cy:.1f}" width="{cell}" height="{cell}" '
                       f'rx="1.3" fill="{bucket(day["contributionCount"])}"/>\n')
    legend_y = y0 + 7 * step + 14
    out.append(f'    <text class="m" x="{x0}" y="{legend_y}" font-size="9.5" fill="{t["dim"]}">less</text>\n')
    for i, shade in enumerate(t["heat"]):
        out.append(f'    <rect x="{x0 + 28 + i * 9:.1f}" y="{legend_y - 8}" width="{cell}" '
                   f'height="{cell}" rx="1.3" fill="{shade}"/>\n')
    out.append(f'    <text class="m" x="{x0 + 28 + len(t["heat"]) * 9 + 4:.0f}" y="{legend_y}" font-size="9.5" fill="{t["dim"]}">more</text>\n')
    out.append('  </g>\n')
    return "".join(out)


# ---------------------------------------------------------------- projects


def render_projects(d: dict, t: dict) -> str:
    W, H = 1000, 446
    svg = head(W, H, "Featured projects").replace("%GRID%", t["grid"])
    svg += panel(t, W, H, "FEATURED WORK", f'{len(d["projects"])} of {d["repos"]} repositories', t["green"])
    svg += f'<g clip-path="url(#clip)">\n'
    svg += f'  <rect x="1" y="65" width="{W - 2}" height="{H - 66}" fill="url(#grid)" opacity="0.5"/>\n'

    cw, ch = 452, 108
    for i, repo in enumerate(d["projects"]):
        col, row = i % 2, i // 2
        x = 30 + col * 488
        y = 82 + row * 120
        lang = repo.get("primaryLanguage") or {}
        lname = lang.get("name") or "Multi"
        lcolor = lang.get("color") or t["violet"]
        accent = [t["cyan"], t["violet"], t["green"]][row % 3]

        svg += f'  <g class="r" style="animation-delay:{0.10 + i * 0.07:.2f}s">\n'
        svg += f'    <rect x="{x}" y="{y}" width="{cw}" height="{ch}" rx="10" fill="{t["panel"]}" stroke="{t["stroke"]}"/>\n'
        svg += f'    <rect x="{x}" y="{y + 14}" width="3" height="{ch - 28}" rx="1.5" fill="{accent}"/>\n'
        svg += f'    <text class="m" x="{x + 20}" y="{y + 26}" font-size="9.5" letter-spacing="1.6" fill="{t["dim"]}">BLOCK #{i + 1:02d}</text>\n'

        name = repo["name"]
        nsize = 14.5
        while text_width(name, nsize, True) > cw - 40 and nsize > 10:
            nsize -= 0.5
        svg += f'    <text class="m" x="{x + 20}" y="{y + 48}" font-size="{nsize}" font-weight="700" fill="{accent}">{esc(name)}</text>\n'

        desc = repo.get("description") or "No description yet."
        for j, line in enumerate(wrap(desc, 10.5, cw - 44, 2, True)):
            svg += f'    <text class="m" x="{x + 20}" y="{y + 66 + j * 15}" font-size="10.5" fill="{t["muted"]}">{esc(line)}</text>\n'

        fy = y + ch - 14
        svg += f'    <circle cx="{x + 24}" cy="{fy - 4}" r="4" fill="{lcolor}"/>\n'
        svg += f'    <text class="m" x="{x + 34}" y="{fy}" font-size="10.5" fill="{t["text"]}">{esc(lname)}</text>\n'
        meta_x = x + 34 + text_width(lname, 10.5, True) + 18

        if repo["stargazerCount"]:
            svg += f'    <text class="m" x="{meta_x}" y="{fy}" font-size="10.5" fill="{t["amber"]}">&#9733; {repo["stargazerCount"]}</text>\n'
            meta_x += text_width(f'* {repo["stargazerCount"]}', 10.5, True) + 16
        if repo["forkCount"]:
            svg += f'    <text class="m" x="{meta_x}" y="{fy}" font-size="10.5" fill="{t["dim"]}">&#8862; {repo["forkCount"]}</text>\n'

        svg += f'    <text class="m" x="{x + cw - 20}" y="{fy}" font-size="10" text-anchor="end" fill="{t["dim"]}">updated {ago(repo["pushedAt"])}</text>\n'
        svg += f'  </g>\n'

    svg += f'  <rect class="sweep" x="0" y="65" width="200" height="{H - 66}" fill="url(#sweepg)"/>\n'
    svg += '</g>\n</svg>\n'
    return svg


# ---------------------------------------------------------------- main


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true", help="render from fixture data")
    ap.add_argument("--seed", action="store_true",
                    help="render real public data via REST, no token (contribution totals show as -)")
    args = ap.parse_args()

    if args.mock:
        user = mock()
    elif args.seed:
        try:
            user = fetch_rest()
        except (urllib.error.URLError, KeyError, TimeoutError) as e:
            print(f"error: public REST seed failed: {e}", file=sys.stderr)
            return 1
    else:
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if not token:
            print("error: GITHUB_TOKEN is not set (use --mock to render fixtures)", file=sys.stderr)
            return 1
        try:
            user = fetch(token)
        except (urllib.error.URLError, RuntimeError, TimeoutError) as e:
            # Leave the previously committed cards in place rather than
            # replacing good art with a broken render.
            print(f"error: could not reach the GitHub API: {e}", file=sys.stderr)
            return 1

    d = digest(user)
    OUT.mkdir(parents=True, exist_ok=True)
    for theme_name, t in THEMES.items():
        (OUT / f"telemetry-{theme_name}.svg").write_text(render_telemetry(d, t), encoding="utf-8")
        (OUT / f"projects-{theme_name}.svg").write_text(render_projects(d, t), encoding="utf-8")

    def show(v, suffix=""):
        return "pending" if v is None else f"{v}{suffix}"

    print(f"commits={show(d['commits'])} contributions={show(d['contributions'])} "
          f"prs={show(d['prs'])} repos={d['repos']} stars={d['stars']} "
          f"followers={d['followers']} streak={show(d['streak'], 'd')} "
          f"longest={show(d['longest'], 'd')} "
          f"calendar_days={sum(len(w['contributionDays']) for w in d['weeks'])}")
    print("langs: " + ", ".join(f"{l['name']} {l['pct']:.1f}%" for l in d["langs"]))
    print("projects: " + ", ".join(r["name"] for r in d["projects"]))
    print(f"wrote {len(THEMES) * 2} files to {OUT}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
