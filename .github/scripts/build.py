#!/usr/bin/env python3
"""Build the passport profile: every SVG under assets/generated, the 3D seal
inside README.md, and (with `stamp`) a visa stamp for a visitor.

    python .github/scripts/build.py --mock          # fixture data, no token
    GITHUB_TOKEN=... python .github/scripts/build.py
    python .github/scripts/build.py stamp --login octocat --serial 7

Needs fonttools and Pillow (see .github/workflows/cards.yml).
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import html
import io
import json
import math
import os
import pathlib
import random
import re
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
USER = "alenissacsam-2"
OUT = ROOT / "assets" / "generated"
FONTS = ROOT / "assets" / "fonts"
STAMPS = ROOT / "stamps"
README = ROOT / "README.md"
API = "https://api.github.com/graphql"

HOLDER = {
    "surname": "SAM",
    "given": "ALEN ISSAC",
    "nationality": "INDIAN",
    "residence": "KERALA, INDIA",
    "institution": "IIT HYDERABAD",
    "field": "DECENTRALIZED IDENTITY",
    "chains": "ETHEREUM / ALGORAND",
}

# Visa pages, in order. `port` is where the work lives, `title` what the stamp says.
VISAS = [
    ("algorand-identity-verification", "IDENTITY", "ALGORAND", "PYTEAL / REACT"),
    ("blockchain-certificate-verification", "CERTIFICATES", "ETHEREUM", "SOLIDITY / IPFS"),
    ("ethereum-identity-dapp", "IDENTITY DAPP", "ETHEREUM", "SOLIDITY / ETHERS"),
    ("AI-Powered-Infrastructure-Design-with-Google-ADK", "AGENTS", "GOOGLE ADK", "PYTHON"),
    ("txline-prediction-markets", "PREDICTION", "ON-CHAIN", "TYPESCRIPT"),
    ("NN-From-Scratch-for-MNIST", "NEURAL NET", "FIRST PRINCIPLES", "NUMPY"),
]

LANG_SKIP = {"HTML", "CSS", "SCSS", "Makefile", "Dockerfile", "Shell", "Batchfile"}

# Daylight is the document as printed. UV is the same document under a 365nm
# inspection lamp: paper goes dark, security inks fluoresce.
DAY = dict(
    name="day", paper="#E8EEEC", paper2="#DDE6E3", ink="#13213A", label="#4C5E6E",
    line="#2E8B82", line2="#8C79B6", red="#C42F2A", edge="#C5D2CE", portrait="#13213A",
    ghost="#13213A", ghost_op=0.16, fibre=0.0, mrz="#13213A", cover="#16243F",
    stamp_inks=["#C42F2A", "#1F4FA8", "#5B3C9E", "#1E7A55", "#13213A", "#A8531C"],
    dot="#13213A",
)
UV = dict(
    name="uv", paper="#0B0A1A", paper2="#121129", ink="#E6E8FF", label="#9296CC",
    line="#5CF2C8", line2="#7FA8FF", red="#FF6B4A", edge="#2C2856", portrait="#4A4785",
    ghost="#FF5FA8", ghost_op=0.75, fibre=1.0, mrz="#E6E8FF", cover="#0F1530",
    stamp_inks=["#FF6B4A", "#7FA8FF", "#C79BFF", "#5CF2C8", "#E6E8FF", "#FFB04A"],
    dot="#5CF2C8",
)

QUERY = """
query($login: String!) {
  user(login: $login) {
    login createdAt avatarUrl
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false,
                 orderBy: {field: PUSHED_AT, direction: DESC}) {
      totalCount
      nodes {
        name createdAt pushedAt stargazerCount url
        primaryLanguage { name }
        languages(first: 12, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""

# ---------------------------------------------------------------- data


def _get(url: str, token: str | None = None, body: bytes | None = None):
    headers = {"User-Agent": f"{USER}-passport", "Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"bearer {token}"
    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read()


def fetch(token: str) -> dict:
    body = json.dumps({"query": QUERY, "variables": {"login": USER}}).encode()
    payload = json.loads(_get(API, token, body))
    if "errors" in payload:
        raise RuntimeError(f"GraphQL errors: {payload['errors']}")
    user = (payload.get("data") or {}).get("user")
    if not user:
        raise RuntimeError("GraphQL returned no user")
    return user


def mock() -> dict:
    """Deterministic fixture shaped like the GraphQL response."""
    today = dt.date.today()
    start = today - dt.timedelta(days=today.weekday() + 1 + 52 * 7)
    weeks, seed = [], 11
    for w in range(53):
        days = []
        for d in range(7):
            day = start + dt.timedelta(days=w * 7 + d)
            if day > today:
                break
            seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
            roll = seed % 100
            n = 0 if (roll < 38 or w < 8) else (roll % 9) + (5 if w > 44 else 0)
            days.append({"date": day.isoformat(), "contributionCount": n})
        weeks.append({"contributionDays": days})

    def repo(name, created, langs):
        age = int(hashlib.sha256(name.encode()).hexdigest(), 16) % 40
        pushed = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=age, hours=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
        return {"name": name, "createdAt": created, "pushedAt": pushed, "stargazerCount": 0,
                "primaryLanguage": {"name": langs[0][0]},
                "url": f"https://github.com/{USER}/{name}",
                "languages": {"edges": [{"size": s, "node": {"name": n}} for n, s in langs]}}

    return {
        "login": USER, "createdAt": "2025-11-14T14:57:31Z",
        "avatarUrl": "https://avatars.githubusercontent.com/u/244016305?v=4",
        "repositories": {"totalCount": 16, "nodes": [
            repo(VISAS[0][0], "2025-12-02T10:00:00Z", [("TypeScript", 9), ("Python", 4)]),
            repo(VISAS[1][0], "2026-01-19T10:00:00Z", [("JavaScript", 8), ("Solidity", 5)]),
            repo(VISAS[2][0], "2026-02-07T10:00:00Z", [("TypeScript", 7), ("Solidity", 3)]),
            repo(VISAS[3][0], "2026-03-22T10:00:00Z", [("Jupyter Notebook", 9), ("Python", 2)]),
            repo(VISAS[4][0], "2026-05-30T10:00:00Z", [("TypeScript", 6)]),
            repo(VISAS[5][0], "2025-11-20T10:00:00Z", [("Jupyter Notebook", 4), ("Python", 2)]),
        ]},
        "contributionsCollection": {"contributionCalendar": {
            "totalContributions": sum(d["contributionCount"] for w in weeks for d in w["contributionDays"]),
            "weeks": weeks}},
    }


def digest(user: dict) -> dict:
    repos = user["repositories"]["nodes"]
    totals: dict[str, int] = {}
    for r in repos:
        for e in r["languages"]["edges"]:
            if e["node"]["name"] not in LANG_SKIP:
                totals[e["node"]["name"]] = totals.get(e["node"]["name"], 0) + e["size"]
    langs = [n for n, _ in sorted(totals.items(), key=lambda kv: -kv[1])][:4]

    cal = user["contributionsCollection"]["contributionCalendar"]
    days = sorted((d for w in cal["weeks"] for d in w["contributionDays"]), key=lambda d: d["date"])
    longest = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] else 0
        longest = max(longest, run)
    tail = days[:-1] if days and days[-1]["contributionCount"] == 0 else days  # today isn't over
    current = 0
    for d in reversed(tail):
        if not d["contributionCount"]:
            break
        current += 1

    by_name = {r["name"]: r for r in repos}
    return {
        "created": user["createdAt"][:10],
        "avatar": user.get("avatarUrl"),
        "repos": user["repositories"]["totalCount"],
        "total": cal["totalContributions"],
        "weeks": cal["weeks"],
        "longest": longest,
        "current": current,
        "langs": langs,
        "visas": [(by_name.get(n), n, t, p, s) for n, t, p, s in VISAS],
        "recent": sorted((r for r in repos if r["name"] != USER and r.get("pushedAt")),
                         key=lambda r: r["pushedAt"], reverse=True)[:6],
    }


# ---------------------------------------------------------------- fonts

FACES = {  # css class -> (file, axis location)
    "fl": ("Archivo.ttf", {"wght": 600, "wdth": 125}),   # labels, expanded caps
    "fv": ("Archivo.ttf", {"wght": 800, "wdth": 112}),   # values
    "fb": ("Archivo.ttf", {"wght": 450, "wdth": 100}),   # body
    "fw": ("Archivo.ttf", {"wght": 760, "wdth": 100}),   # compact values
    "fm": ("AzeretMono.ttf", {"wght": 500}),             # MRZ, serials
}
_instances: dict[str, bytes] = {}


def _instance(cls: str) -> bytes:
    if cls not in _instances:
        from fontTools.ttLib import TTFont
        from fontTools.varLib import instancer
        file, axes = FACES[cls]
        font = instancer.instantiateVariableFont(TTFont(FONTS / file), axes)
        buf = io.BytesIO()
        font.save(buf)
        _instances[cls] = buf.getvalue()
    return _instances[cls]


def font_css(svg: str) -> str:
    """@font-face rules for the faces this SVG uses, subset to its own text."""
    from fontTools import subset
    from fontTools.ttLib import TTFont
    chars = "".join(html.unescape(m) for m in re.findall(r"<(?:text|tspan|textPath)\b[^>]*>([^<]*)", svg))
    rules = []
    for cls in FACES:
        if f'class="{cls}' not in svg and f" {cls}\"" not in svg and f" {cls} " not in svg:
            continue
        font = TTFont(io.BytesIO(_instance(cls)))
        opts = subset.Options()
        opts.flavor, opts.hinting, opts.name_IDs, opts.layout_features = "woff", False, [], ["kern"]
        sub = subset.Subsetter(opts)
        sub.populate(text=chars + " ")
        sub.subset(font)
        buf = io.BytesIO()
        font.flavor = "woff"
        font.save(buf)
        b64 = base64.b64encode(buf.getvalue()).decode()
        rules.append(f"@font-face{{font-family:{cls};src:url(data:font/woff;base64,{b64}) format('woff')}}"
                     f".{cls}{{font-family:{cls},'Archivo','Segoe UI',sans-serif}}")
    return "".join(rules)


def text_len(cls: str, text: str, size: float, spacing: float = 0) -> float:
    """Advance width of `text` in face `cls`, in SVG units."""
    from fontTools.ttLib import TTFont
    font = _fonts.get(cls) or _fonts.setdefault(cls, TTFont(io.BytesIO(_instance(cls))))
    cmap, hmtx, upm = font.getBestCmap(), font["hmtx"], font["head"].unitsPerEm
    units = sum(hmtx[cmap[ord(ch)]][0] for ch in text if ord(ch) in cmap)
    return units * size / upm + spacing * len(text)


_fonts: dict = {}


def ink(fid: str, seed: str, w: float, h: float) -> tuple[str, str]:
    """A rubber-stamp impression: bled edge, speckle, uneven pressure, sometimes a partial strike.
    Returns (defs, attributes for the inked group)."""
    rng = random.Random(seed)
    ang = rng.uniform(0, 360)
    lo = rng.uniform(.35, .6)          # where the stamp got the least pressure
    edge = rng.random() < .35          # partial strike: one side barely touched paper
    stops = (f'<stop offset="0" stop-color="#fff"/><stop offset=".55" stop-color="#fff" stop-opacity="{(1 + lo) / 2:.2f}"/>'
             f'<stop offset="{.86 if edge else 1}" stop-color="#fff" stop-opacity="{lo * (.45 if edge else 1):.2f}"/>'
             + ('<stop offset="1" stop-color="#fff" stop-opacity=".05"/>' if edge else ""))
    defs = (f'<filter id="{fid}" x="-8%" y="-8%" width="116%" height="116%">'
            f'<feTurbulence type="fractalNoise" baseFrequency=".035" numOctaves="2" seed="{rng.randint(1, 99)}" result="w"/>'
            f'<feDisplacementMap in="SourceGraphic" in2="w" scale="3.2" xChannelSelector="R" yChannelSelector="G" result="bled"/>'
            f'<feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="2" seed="{rng.randint(1, 99)}" result="n"/>'
            f'<feColorMatrix in="n" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -1.15 1.42" result="sp"/>'
            f'<feComposite in="bled" in2="sp" operator="in"/></filter>'
            f'<linearGradient id="{fid}g" gradientTransform="rotate({ang:.0f} .5 .5)">{stops}</linearGradient>'
            f'<mask id="{fid}m" maskUnits="userSpaceOnUse" x="0" y="0" width="{w}" height="{h}">'
            f'<rect width="{w}" height="{h}" fill="url(#{fid}g)"/></mask>')
    return defs, f'filter="url(#{fid})" mask="url(#{fid}m)"'


def finish(svg_body: str, w: int, h: int, title: str, css: str) -> str:
    fonts = font_css(svg_body)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'role="img" aria-label="{esc(title)}"><title>{esc(title)}</title>'
            f"<style>{fonts}{css}"
            "@media (prefers-reduced-motion:reduce){*{animation:none!important}}</style>"
            f"{svg_body}</svg>")


# ---------------------------------------------------------------- helpers


def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def f1(v: float) -> str:
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


def poly(pts) -> str:
    return "M" + "L".join(f"{f1(x)} {f1(y)}" for x, y in pts) + "Z"


def mrz_check(s: str) -> str:
    """ICAO 9303 check digit: weights 7,3,1 over digits, A=10..Z=35, '<'=0."""
    total = 0
    for i, ch in enumerate(s):
        v = int(ch) if ch.isdigit() else (ord(ch) - 55 if ch.isalpha() else 0)
        total += v * (7, 3, 1)[i % 3]
    return str(total % 10)


assert mrz_check("L898902C3") == "6" and mrz_check("740812") == "2"  # ICAO 9303 specimen


def mrz(doc_hash: str) -> tuple[str, str]:
    name = f"{HOLDER['surname']}<<{HOLDER['given'].replace(' ', '<')}"
    line1 = ("P<UTO" + name).ljust(44, "<")[:44]  # UTO: ICAO's specimen state, not a real country
    doc = doc_hash[:9].upper()
    personal = doc_hash[9:23].upper()
    dob = exp = "<<<<<<"
    parts = [doc + mrz_check(doc), dob + mrz_check(dob), exp + mrz_check(exp), personal + mrz_check(personal)]
    composite = mrz_check("".join(parts))
    line2 = parts[0] + "IND" + parts[1] + "<" + parts[2] + parts[3] + composite
    assert len(line1) == len(line2) == 44, (line1, line2)
    return line1, line2


def fmt_date(iso: str) -> str:
    d = dt.date.fromisoformat(iso[:10])
    return f"{d.day:02d} {d.strftime('%b').upper()} {d.year}"


# ---------------------------------------------------------------- engraved portrait


def portrait_paths(avatar: str | None, x0: float, y0: float, w: float, h: float) -> str:
    """The avatar as an intaglio engraving: one wavy line per row, thick where dark."""
    try:
        from PIL import Image, ImageOps
        raw = _get(avatar + ("&" if "?" in avatar else "?") + "s=460")
        img = Image.open(io.BytesIO(raw)).convert("L")
    except Exception as e:  # no avatar: the window keeps its guilloché and frame
        print(f"portrait skipped: {e}", file=sys.stderr)
        return ""
    s = img.size[0]
    img = img.crop((int(s * .13), int(s * .06), int(s * .87), int(s * .06 + s * .74 * h / w)))
    pitch, step = 4.6, 3.2
    rows, cols = int(h / pitch), int(w / step)
    img = ImageOps.autocontrast(img.resize((cols + 1, rows), Image.LANCZOS), cutoff=2)
    px = img.load()
    out = []
    for j in range(rows):
        top, bot = [], []
        for i in range(cols + 1):
            b = px[i, j] / 255.0
            t = 0.12 + 1.75 * (1 - b) ** 1.15
            x = x0 + i * step
            y = y0 + j * pitch + pitch / 2 + 0.9 * math.sin(i * step / 21 + j * 0.42)
            top.append((x, y - t))
            bot.append((x, y + t))
        out.append(poly(top + bot[::-1]))
    return f'<path d="{"".join(out)}"/>'


# ---------------------------------------------------------------- guilloché


def rose(cx, cy, r0, a, n, b, m, phi, steps=720):
    pts = []
    for i in range(steps):
        t = 2 * math.pi * i / steps
        r = r0 + a * math.sin(n * t) + b * math.sin(m * t + phi)
        pts.append((cx + r * math.cos(t), cy + r * math.sin(t)))
    return poly(pts)


def rosette(rng: random.Random, cx, cy, scale, ida, idb, c1, c2, sw, copies=(22, 16), delay=1.15, spin=False):
    """Two moiré rings, each one curve repeated with a small rotation."""
    n1, n2 = rng.choice([9, 10, 11, 12, 13]), rng.choice([17, 19, 21, 23])
    d1 = rose(cx, cy, 92 * scale, 18 * scale, n1, 5 * scale, n1 * 3, rng.uniform(0, 6.28))
    d2 = rose(cx, cy, 50 * scale, 10 * scale, n2 // 2, 4 * scale, n2, rng.uniform(0, 6.28))
    out = [f'<defs><path id="{ida}" d="{d1}"/><path id="{idb}" d="{d2}"/></defs>']
    # counter-rotating rings make the moire drift, the way a real guilloche shifts as you tilt it
    out.append(f'<g style="transform-origin:{cx}px {cy}px;animation:spin 160s linear infinite">' if spin else "<g>")
    for k in range(copies[0]):
        out.append(f'<use href="#{ida}" transform="rotate({f1(k * 360 / n1 / copies[0])} {cx} {cy})" '
                   f'fill="none" stroke="{c1}" stroke-width="{sw}" class="wv" '
                   f'style="animation-delay:{delay + k * .035:.3f}s"/>')
    out.append("</g>")
    out.append(f'<g style="transform-origin:{cx}px {cy}px;animation:spin 110s linear infinite reverse">' if spin else "<g>")
    for k in range(copies[1]):
        out.append(f'<use href="#{idb}" transform="rotate({f1(k * 360 / n2 / copies[1])} {cx} {cy})" '
                   f'fill="none" stroke="{c2}" stroke-width="{sw}" class="wv" '
                   f'style="animation-delay:{delay + .4 + k * .035:.3f}s"/>')
    out.append("</g>")
    return "".join(out)


def fibres(rng: random.Random, w, h, n=70) -> str:
    """UV security fibres: short fluorescent hairs scattered in the paper."""
    cols = ["#FF5FA8", "#5CF2C8", "#7FA8FF", "#FFE45C"]
    out = []
    for _ in range(n):
        x, y = rng.uniform(30, w - 30), rng.uniform(30, h - 30)
        a = rng.uniform(0, math.pi)
        L = rng.uniform(7, 16)
        x2, y2 = x + L * math.cos(a), y + L * math.sin(a)
        cx, cy = (x + x2) / 2 + rng.uniform(-4, 4), (y + y2) / 2 + rng.uniform(-4, 4)
        tw = f' class="tw" style="animation-delay:{rng.uniform(0, 4):.1f}s"' if rng.random() < .22 else ""
        out.append(f'<path{tw} d="M{f1(x)} {f1(y)}Q{f1(cx)} {f1(cy)} {f1(x2)} {f1(y2)}" '
                   f'stroke="{rng.choice(cols)}" stroke-width="1.1" fill="none" opacity="{rng.uniform(.55, .95):.2f}"/>')
    return "".join(out)


DOTS = {  # 5x7 dot matrix for the laser-perforated document number
    "0": "01110100011001110101110011000101110", "1": "00100011000010000100001000010001110",
    "2": "01110100010000100010001000100011111", "3": "11111000100010000010000011000101110",
    "4": "00010001100101010010111110001000010", "5": "11111100001111000001000011000101110",
    "6": "00110010001000011110100011000101110", "7": "11111000010001000100010000100001000",
    "8": "01110100011000101110100011000101110", "9": "01110100011000101111000010001001100",
    "A": "01110100011000111111100011000110001", "B": "11110100011000111110100011000111110",
    "C": "01110100011000010000100001000101110", "D": "11100100101000110001100011001011100",
    "E": "11111100001000011110100001000011111", "F": "11111100001000011110100001000010000",
}


def perforation(text: str, x0: float, y0: float, pitch: float = 4.4, r: float = 1.25) -> str:
    """Holes reading `text` top to bottom, rotated like a passport's laser number."""
    out = []
    y = y0
    for ch in text:
        bits = DOTS.get(ch, DOTS["0"])
        for k, bit in enumerate(bits):
            if bit == "1":
                row, col = divmod(k, 5)
                # rotate 90deg: columns run down the page, rows run right-to-left
                out.append(f'<circle cx="{f1(x0 + (6 - row) * pitch)}" cy="{f1(y + col * pitch)}" r="{r}"/>')
        y += 6.5 * pitch
    return "".join(out)


# ---------------------------------------------------------------- passport


PASSPORT_CSS = """
.wv{opacity:1;animation:wv .5s ease-out both}
@keyframes wv{from{opacity:0}}
.up{animation:up .7s cubic-bezier(.16,1,.3,1) both}
@keyframes up{from{opacity:0;transform:translateY(9px)}}
#cover{transform-origin:20px 380px;animation:open 1.05s cubic-bezier(.55,0,.75,.35) .45s both}
@keyframes open{0%{transform:none}60%{transform:scale(.55,1.05)}100%{transform:scale(0,1.08);visibility:hidden}}
#shade{animation:shade 1.05s ease-in .45s both}
@keyframes shade{to{opacity:.75}}
#mrzclip rect{animation:print 1.1s steps(44,end) 2.05s both}
@keyframes print{from{transform:scaleX(0)}}
#scan{animation:scan 9s linear 2.05s infinite both}
@keyframes scan{0%{transform:translateX(0);opacity:1}12%{transform:translateX(1064px);opacity:1}12.1%,100%{transform:translateX(1064px);opacity:0}}
@keyframes spin{to{transform:rotate(360deg)}}
.tw{animation:tw 3.4s ease-in-out infinite}
@keyframes tw{50%{opacity:.12}}
#stampin{transform-box:fill-box;transform-origin:center;animation:thunk .42s cubic-bezier(.16,1,.3,1) 3.25s both}
@keyframes thunk{from{opacity:0;transform:scale(1.6) rotate(3deg)}}
#foil{animation:foil 7s ease-in-out 1.6s infinite alternate both}
@media (prefers-reduced-motion:reduce){#cover,#scan{display:none}}
@keyframes foil{from{transform:translateX(-260px)}to{transform:translateX(160px)}}
"""


def render_passport(d: dict, t: dict, doc_hash: str, portrait: str) -> str:
    W, H = 1200, 760
    rng = random.Random(doc_hash)
    l1, l2 = mrz(doc_hash)
    doc_no = doc_hash[:9].upper()
    issued = fmt_date(d["created"])
    built = dt.datetime.now(dt.timezone.utc).strftime("%d %b %Y %H:%M UTC").upper()
    uv = t["name"] == "uv"

    def field(x, y, label, value, size=21, delay=1.3, color=None):
        cls = "fv" if size > 30 else "fw"
        return (f'<g class="up" style="animation-delay:{delay:.2f}s">'
                f'<text x="{x}" y="{y}" class="fl" font-size="14.5" letter-spacing="1.4" fill="{t["label"]}">{esc(label)}</text>'
                f'<text x="{x}" y="{y + size + 4}" class="{cls}" font-size="{size}" fill="{color or t["ink"]}">{esc(value)}</text></g>')

    b = []
    b.append(f"""<defs>
<clipPath id="doc"><rect x="20" y="20" width="1160" height="720" rx="30"/></clipPath>
<clipPath id="win"><rect x="68" y="150" width="262" height="338" rx="14"/></clipPath>
<clipPath id="mrzclip"><rect x="68" y="604" width="1064" height="100"/></clipPath>
<pattern id="wave" width="26" height="9" patternUnits="userSpaceOnUse"><path d="M0 4.5C6.5 0 6.5 0 13 4.5S19.5 9 26 4.5" fill="none" stroke="{t['line']}" stroke-width=".6" opacity="{.22 if not uv else .16}"/></pattern>
<linearGradient id="gutter" x1="0" x2="1"><stop offset="0" stop-color="#000" stop-opacity="{.16 if not uv else .5}"/><stop offset="1" stop-color="#000" stop-opacity="0"/></linearGradient>
<linearGradient id="iris" x1="0" x2="1" y1="0" y2=".35"><stop offset="0" stop-color="#5CF2C8" stop-opacity="0"/><stop offset=".22" stop-color="#5CF2C8"/><stop offset=".4" stop-color="#9F86FF"/><stop offset=".55" stop-color="#FF7AB8"/><stop offset=".72" stop-color="#FFD66B"/><stop offset=".9" stop-color="#5CF2C8"/><stop offset="1" stop-color="#5CF2C8" stop-opacity="0"/></linearGradient>
<clipPath id="ovd"><path d="M248 402h66a16 16 0 0 1 16 16v54a16 16 0 0 1-16 16h-66z"/></clipPath>
<radialGradient id="emboss" cx=".42" cy=".38" r=".7"><stop offset="0" stop-color="#E9EEF7"/><stop offset=".55" stop-color="#AEB8CC"/><stop offset="1" stop-color="#6C7894"/></radialGradient>
<mask id="holes"><rect width="{W}" height="{H}" fill="#fff"/><g fill="#000">{perforation(doc_no, 1128, 168)}</g></mask>
</defs>""")

    # document body
    b.append(f'<g mask="url(#holes)"><g clip-path="url(#doc)">')
    b.append(f'<rect x="20" y="20" width="1160" height="720" fill="{t["paper"]}"/>')
    b.append(f'<rect x="20" y="20" width="1160" height="560" fill="url(#wave)"/>')
    if uv:
        b.append(fibres(rng, W, H))
        # hidden UV image: only the lamp shows it
        b.append(f'<g opacity=".28">{rosette(random.Random(doc_hash[::-1]), 600, 330, 2.6, "ua", "ub", "#FF5FA8", "#7FA8FF", .7, (10, 8), .9)}</g>')
    b.append(f'<rect x="20" y="20" width="70" height="720" fill="url(#gutter)"/>')

    # header
    b.append(f'<g class="up" style="animation-delay:1.15s">'
             f'<text x="68" y="92" class="fv" font-size="30" letter-spacing="9" fill="{t["ink"]}">PASSPORT</text>'
             f'<text x="372" y="91" class="fl" font-size="13" letter-spacing="3" fill="{t["label"]}">VERIFIABLE CREDENTIAL</text></g>')
    for i, (lab, val, col) in enumerate([("TYPE", "P", t["ink"]), ("CODE", "UTO", t["ink"]), ("DOCUMENT NO.", doc_no, t["red"])]):
        x = [770, 848, 946][i]
        b.append(f'<g class="up" style="animation-delay:{1.2 + i * .05:.2f}s">'
                 f'<text x="{x}" y="64" class="fl" font-size="13.5" letter-spacing="1.4" fill="{t["label"]}">{lab}</text>'
                 f'<text x="{x}" y="94" class="{"fm" if i == 2 else "fv"}" font-size="{24 if i == 2 else 23}" fill="{col}">{val}</text></g>')
    # microprint rule: reads DONT TRUST VERIFY under a loupe
    micro = ("DONT TRUST VERIFY " * 40)[:300]
    b.append(f'<text x="68" y="124" class="fm" font-size="4.3" letter-spacing=".4" fill="{t["label"]}" textLength="1064" lengthAdjust="spacing">{micro}</text>')

    # portrait window
    b.append(f'<g class="up" style="animation-delay:1.25s"><rect x="68" y="150" width="262" height="338" rx="14" fill="{t["paper2"]}"/>'
             f'<g clip-path="url(#win)"><g fill="{t["portrait"]}" id="pt">{portrait}</g></g>'
             f'<rect x="68.5" y="150.5" width="261" height="337" rx="13.5" fill="none" stroke="{t["edge"]}"/></g>')
    # optically variable patch over the photo corner
    b.append(f'<g clip-path="url(#ovd)" opacity="{.38 if not uv else .55}"><rect id="foil" x="150" y="380" width="360" height="130" fill="url(#iris)"/></g>'
             f'<path d="M248 402h66a16 16 0 0 1 16 16v54a16 16 0 0 1-16 16h-66z" fill="none" stroke="{t["line"]}" stroke-width=".8" opacity=".6"/>')

    # fields
    b.append(field(372, 156, "SURNAME", HOLDER["surname"], 40, 1.3))
    b.append(field(372, 230, "GIVEN NAMES", HOLDER["given"], 40, 1.36))
    b.append(field(372, 304, "NATIONALITY", HOLDER["nationality"], 21, 1.42))
    b.append(field(604, 304, "RESIDENCE", HOLDER["residence"], 21, 1.46))
    b.append(field(372, 356, "INSTITUTION", HOLDER["institution"], 21, 1.5))
    b.append(field(604, 356, "DATE OF ISSUE", issued, 21, 1.54))
    b.append(field(372, 408, "FIELD", HOLDER["field"], 21, 1.58))
    b.append(field(372, 460, "CHAINS", HOLDER["chains"], 21, 1.62))
    b.append(field(372, 512, "VALID UNTIL", "DISPROVEN", 21, 1.66, color=t["red"]))
    b.append(field(604, 512, "SIGNATURE", "SIGSTORE / REKOR", 21, 1.7))

    # rosette + secondary ghost portrait
    b.append(rosette(rng, 968, 300, 1.08, "ra", "rb", t["line"], t["line2"], .65, spin=True))
    b.append(f'<circle cx="968" cy="300" r="22" fill="{t["paper"]}"/>'
             f'<text x="968" y="307" text-anchor="middle" class="fv" font-size="19" letter-spacing="1" fill="{t["ink"]}">AIS</text>')
    if portrait:
        b.append(f'<g opacity="{t["ghost_op"]}" fill="{t["ghost"]}" class="up" style="animation-delay:1.9s">'
                 f'<use href="#pt" transform="translate(1046 448) scale(.3) translate(-68 -150)"/></g>')

    # machine readable zone
    b.append(f'<rect x="20" y="580" width="1160" height="160" fill="{t["paper"]}"/>'
             f'<line x1="68" y1="590" x2="1132" y2="590" stroke="{t["edge"]}"/>')
    b.append(f'<g clip-path="url(#mrzclip)">'
             f'<text x="68" y="646" class="fm" font-size="29" fill="{t["mrz"]}" textLength="1064" lengthAdjust="spacing">{esc(l1)}</text>'
             f'<text x="68" y="692" class="fm" font-size="29" fill="{t["mrz"]}" textLength="1064" lengthAdjust="spacing">{esc(l2)}</text></g>'
             f'<rect id="scan" x="66" y="612" width="3" height="88" fill="{t["red"]}" opacity="0"/>')
    b.append(f'<text x="1132" y="722" text-anchor="end" class="fm" font-size="10.5" fill="{t["label"]}">BUILT {built} / SHA-256 {doc_hash[:32]}</text>')

    # VERIFIED stamp
    b.append(f'<defs>{ink("vs", doc_hash, W, H)[0]}</defs><g id="stampin"><g transform="rotate(-9 955 478)" {ink("vs", doc_hash, W, H)[1]} fill="none" stroke="{t["red"]}" opacity="{.88 if not uv else .95}">'
             f'<rect x="830" y="426" width="250" height="104" rx="12" stroke-width="4.5"/>'
             f'<rect x="840" y="436" width="230" height="84" rx="7" stroke-width="1.6"/>'
             f'<text x="955" y="488" text-anchor="middle" class="fv" font-size="38" letter-spacing="4" fill="{t["red"]}" stroke="none">VERIFIED</text>'
             f'<text x="955" y="511" text-anchor="middle" class="fl" font-size="11" letter-spacing="2.2" fill="{t["red"]}" stroke="none">SIGSTORE / {built[:11]}</text></g></g>')
    b.append("</g>")  # clip
    b.append(f'<rect x="20.5" y="20.5" width="1159" height="719" rx="29.5" fill="none" stroke="{t["edge"]}"/></g>')

    # the cover, which swings open on load
    b.append(f'<g id="cover"><rect x="20" y="20" width="1160" height="720" rx="30" fill="{t["cover"]}"/>'
             f'<rect x="20" y="20" width="1160" height="720" rx="30" fill="url(#wave)" opacity=".5"/>'
             f'<g opacity=".95">{rosette(random.Random(doc_hash), 600, 300, 1.3, "ca", "cb", "url(#emboss)", "url(#emboss)", 1.1, (18, 12), 0)}</g>'
             f'<text x="600" y="520" text-anchor="middle" class="fv" font-size="54" letter-spacing="22" fill="url(#emboss)">PASSPORT</text>'
             f'<text x="600" y="566" text-anchor="middle" class="fl" font-size="15" letter-spacing="7" fill="#AEB8CC">VERIFIABLE CREDENTIAL</text>'
             f'<g fill="none" stroke="#AEB8CC" stroke-width="2.4" transform="translate(574 618)"><rect width="52" height="34" rx="5"/><circle cx="26" cy="17" r="7"/><path d="M0 17h19M33 17h19"/></g>'
             f'<rect id="shade" x="20" y="20" width="1160" height="720" rx="30" fill="#000" opacity="0"/></g>')

    title = f"Passport of {HOLDER['given'].title()} {HOLDER['surname'].title()}, document {doc_no}: decentralized identity, IIT Hyderabad, Ethereum and Algorand. Valid until disproven."
    return finish("".join(b), W, H, title, PASSPORT_CSS)


# ---------------------------------------------------------------- visa stamps

STAMP_CSS = """
.ink{transform-box:fill-box;transform-origin:center;animation:thunk .45s cubic-bezier(.16,1,.3,1) .2s both}
@keyframes thunk{from{opacity:0;transform:scale(1.35)}}
"""


def _arc_text(cx, cy, r, text, size, color, start=-90, sweep=180, pid="arc", cls="fl", spacing=3):
    a0, a1 = math.radians(start - sweep / 2), math.radians(start + sweep / 2)
    x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
    x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
    return (f'<path id="{pid}" d="M{f1(x0)} {f1(y0)}A{r} {r} 0 {int(abs(sweep) > 180)} {int(sweep > 0)} {f1(x1)} {f1(y1)}" fill="none"/>'
            f'<text class="{cls}" font-size="{size}" letter-spacing="{spacing}" fill="{color}">'
            f'<textPath href="#{pid}" startOffset="50%" text-anchor="middle">{esc(text)}</textPath></text>')


def render_visa(i: int, repo: dict | None, name: str, title: str, port: str, stack: str, t: dict) -> str:
    W, H = 400, 300
    c = t["stamp_inks"][i % len(t["stamp_inks"])]
    rng = random.Random(name)
    rot = rng.uniform(-7, 6)
    date = fmt_date(repo["createdAt"]) if repo else "PENDING"
    stars = repo["stargazerCount"] if repo else 0
    cx, cy = W / 2, H / 2
    shape = i % 6
    g = []

    room = [168, 246, 214, 246, 220, 200][shape]

    def small(x, y, text, room, size=15.0):
        while size > 10 and text_len("fl", text, size, 2) > room:
            size -= .5
        return f'<text x="{x}" y="{y}" text-anchor="middle" class="fl" font-size="{size}" letter-spacing="2" fill="{c}">{esc(text)}</text>'

    if shape == 0:  # round, text on the rim
        g += [f'<circle cx="{cx}" cy="{cy}" r="128" stroke-width="5"/>', f'<circle cx="{cx}" cy="{cy}" r="96" stroke-width="1.6"/>',
              _arc_text(cx, cy, 109, f"PORT OF ENTRY / {port}", 14, c, -90, 200, f"a{i}", spacing=2.4),
              small(cx, cy + 56, stack, 150)]
        ty = cy + 4
    elif shape == 1:  # notched rectangle
        g += [f'<path d="M58 64h284l16 16v140l-16 16H58l-16-16V80z" stroke-width="5"/>',
              f'<path d="M66 76h268v148H66z" stroke-width="1.4"/>']
        ty = cy + 6
    elif shape == 2:  # octagon
        p = [(cx + 132 * math.cos(math.radians(22.5 + 45 * k)), cy + 112 * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)]
        g += [f'<path d="{poly(p)}" stroke-width="5"/>']
        ty = cy - 12  # keep the stack line between the octagon's vertical sides
    elif shape == 3:  # oval
        g += [f'<ellipse cx="{cx}" cy="{cy}" rx="160" ry="104" stroke-width="5"/>', f'<ellipse cx="{cx}" cy="{cy}" rx="146" ry="90" stroke-width="1.4"/>']
        ty = cy + 6
    elif shape == 4:  # arrow tab, an exit stamp
        g += [f'<path d="M48 70h250l56 80-56 80H48z" stroke-width="5"/>']
        ty = cy + 6
    else:  # shield
        g += [f'<path d="M80 52h240v110c0 52-62 80-120 98-58-18-120-46-120-98z" stroke-width="5"/>']
        ty = cy - 4
    if shape != 0:
        g.append(small(cx, ty - 46, port, room))
        g.append(small(cx, ty + 56, stack, room * (.78 if shape == 5 else 1)))
    size = 34 if shape else 26
    while size > 16 and text_len("fv", title, size, 1.5) > room:
        size -= 1
    g.append(f'<text x="{cx}" y="{ty + 8}" text-anchor="middle" class="fv" font-size="{size}" letter-spacing="1.5" fill="{c}">{esc(title)}</text>')
    g.append(f'<text x="{cx}" y="{ty + 30}" text-anchor="middle" class="fm" font-size="15" fill="{c}">{date}{f"  /  {stars} STAR" + ("S" if stars != 1 else "") if stars else ""}</text>')

    defs, attrs = ink(f"r{i}", name, W, H)
    strike = "".join(g)
    ghost = (f'<g transform="translate({math.cos(da := rng.uniform(0, 6.28)) * 1.4:.1f} {math.sin(da) * 1.4:.1f}) rotate({rot + rng.uniform(-1.2, 1.2):.1f} {cx} {cy})" '
             f'opacity=".16">{strike}</g>') if rng.random() < .34 else ""  # stamp bounced: a faint second strike
    body = (f"<defs>{defs}</defs><g {attrs} fill=\"none\" stroke=\"{c}\" opacity=\".92\">{ghost}"
            f'<g transform="rotate({rot:.1f} {cx} {cy})">{strike}</g></g>')
    body = f'<g class="ink" style="animation-delay:{.2 + i * .16:.2f}s">{body}</g>'
    css = STAMP_CSS + (".ink>g{animation:glow 5s ease-in-out infinite alternate}@keyframes glow{from{opacity:.7}}" if t["name"] == "uv" else "")
    return finish(body, W, H, f"Visa stamp: {name}, {title.title()} on {port.title()}, entered {date}", css)


# ---------------------------------------------------------------- entry log (contribution perforation)

LOG_CSS = """
.ln{animation:draw 2.6s cubic-bezier(.16,1,.3,1) both}
@keyframes draw{from{stroke-dasharray:var(--L);stroke-dashoffset:var(--L)}to{stroke-dasharray:var(--L);stroke-dashoffset:0}}
#lamp{animation:lamp 7s cubic-bezier(.45,0,.55,1) 2.8s infinite both}
@keyframes lamp{from{transform:translateX(-160px)}to{transform:translateX(940px)}}
.pk{animation:pk .5s cubic-bezier(.16,1,.3,1) 2.4s both}
@keyframes pk{from{opacity:0;transform:translateY(6px)}}
.now{transform-box:fill-box;transform-origin:center;animation:now 2.4s ease-out infinite}
@keyframes now{from{transform:scale(1);opacity:.9}to{transform:scale(3.2);opacity:0}}
"""


def render_log(d: dict, t: dict) -> str:
    """The year as one engraved guilloche band: calm where nothing shipped, swelling where it did."""
    W, H = 1200, 330
    b = []

    def field(x, y, label, value):
        return (f'<text x="{x}" y="{y}" class="fl" font-size="14.5" letter-spacing="1.4" fill="{t["label"]}">{label}</text>'
                f'<text x="{x}" y="{y + 32}" class="fv" font-size="26" fill="{t["ink"]}">{esc(value)}</text>')

    b.append(field(40, 52, "ENTRIES, LAST 12 MONTHS", f"{d['total']:,}"))
    b.append(field(40, 126, "LONGEST STAY", f"{d['longest']} DAY{'S' if d['longest'] != 1 else ''}"))
    b.append(field(40, 200, "CURRENT STAY", f"{d['current']} DAY{'S' if d['current'] != 1 else ''}"))
    b.append(f'<text x="40" y="274" class="fl" font-size="14.5" letter-spacing="1.4" fill="{t["label"]}">LANGUAGES SPOKEN</text>'
             f'<text x="40" y="300" class="fb" font-size="17" fill="{t["ink"]}">{esc(", ".join(d["langs"] or ["-"]))}</text>')
    b.append(f'<line x1="340" y1="40" x2="340" y2="306" stroke="{t["edge"]}"/>')

    days = sorted((c for w in d["weeks"] for c in w["contributionDays"]), key=lambda c: c["date"])
    n = len(days) or 1
    raw = [c["contributionCount"] for c in days] or [0]
    sig = 2.6  # gaussian smoothing in days, so single commits read as swells, not spikes
    ker = [math.exp(-(k * k) / (2 * sig * sig)) for k in range(-8, 9)]
    sm = [sum(raw[i + k - 8] * ker[k] for k in range(17) if 0 <= i + k - 8 < n) for i in range(n)]
    top = max(sm) or 1
    x0, x1, cy = 380, 1160, 150
    step = (x1 - x0) / max(n - 1, 1)
    amp = [6 + 68 * (v / top) ** .75 for v in sm]

    lines = 12
    paths = []
    for k in range(lines):
        ph = 2 * math.pi * k / lines
        pts = [(x0 + i * step, cy + amp[i] * math.sin(i * step / 15 + ph)) for i in range(n)]
        paths.append(("M" + "L".join(f"{f1(x)} {f1(y)}" for x, y in pts),
                      sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))))
    band = "".join(f'<path d="{pth}" class="ln" style="--L:{L:.0f};animation-delay:{.1 + k * .05:.2f}s"/>'
                   for k, (pth, L) in enumerate(paths))
    b.append(f'<g fill="none" stroke="{t["line"]}" stroke-width=".9" opacity=".6">{band}</g>')
    # the inspection lamp: a brighter copy of the band, visible only inside a sweeping window
    lamp_ink = t["line2"] if t["name"] == "uv" else t["ink"]
    b.append(f'<defs><linearGradient id="lg"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff"/>'
             f'<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
             f'<mask id="lm" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}"><rect id="lamp" x="{x0}" y="40" width="160" height="230" fill="url(#lg)"/></mask></defs>'
             f'<g mask="url(#lm)" fill="none" stroke="{lamp_ink}" stroke-width="1.2">'
             + "".join(f'<path d="{pth}"/>' for pth, _ in paths) + "</g>")

    # month rule
    seen = set()
    for i, c in enumerate(days):
        day = dt.date.fromisoformat(c["date"])
        if day.day == 1 and (day.year, day.month) not in seen:
            seen.add((day.year, day.month))
            x = x0 + i * step
            b.append(f'<line x1="{f1(x)}" y1="252" x2="{f1(x)}" y2="260" stroke="{t["label"]}"/>'
                     f'<text x="{f1(x + 4)}" y="276" class="fl" font-size="12.5" letter-spacing="1.4" fill="{t["label"]}">{day.strftime("%b").upper()}</text>')
    b.append(f'<line x1="{x0}" y1="252" x2="{x1}" y2="252" stroke="{t["edge"]}"/>')

    # peak and today
    if max(raw) > 0:
        ip = max(range(n), key=lambda i: raw[i])
        xp = x0 + ip * step
        label = f"PEAK {raw[ip]} / {fmt_date(days[ip]['date'])[:6]}"
        anchor = "end" if xp > x1 - 160 else "start"
        tx = xp - 8 if anchor == "end" else xp + 8
        b.append(f'<g class="pk"><line x1="{f1(xp)}" y1="{f1(cy - amp[ip] - 6)}" x2="{f1(xp)}" y2="56" stroke="{t["red"]}" stroke-width="1.2"/>'
                 f'<text x="{f1(tx)}" y="62" text-anchor="{anchor}" class="fm" font-size="15" fill="{t["red"]}">{esc(label)}</text></g>')
    b.append(f'<circle cx="{x1}" cy="{cy}" r="4" fill="{t["red"]}"/><circle class="now" cx="{x1}" cy="{cy}" r="4" fill="{t["red"]}"/>')
    return finish("".join(b), W, H, f"Entry log: {d['total']} contributions in the last year drawn as one guilloche band, longest streak {d['longest']} days, current streak {d['current']} days.", LOG_CSS)


# ---------------------------------------------------------------- departures board (split flap)

BOARD_CSS = """
.fp{animation-name:flip;animation-fill-mode:both}
@keyframes flip{from{transform:translateY(var(--k))}99%,to{transform:translateY(0)}}
.fh{transform-box:fill-box;transform-origin:50% 100%;animation-name:hinge;animation-timing-function:linear}
@keyframes hinge{from{opacity:.22;transform:scaleY(1)}to{opacity:.04;transform:scaleY(0)}}
.bl{animation:bl 1.1s steps(2,jump-none) infinite}
@keyframes bl{50%{opacity:.25}}
"""
FLAPS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
GATES = {"TypeScript": "TS", "JavaScript": "JS", "Python": "PY", "Solidity": "SOL", "Jupyter Notebook": "NB",
         "Rust": "RS", "Go": "GO", "HTML": "WEB", "CSS": "WEB", "Shell": "SH", "C++": "CPP", "Move": "MV"}


def fit_words(s: str, n: int) -> str:
    out = ""
    for w in s.upper().replace("-", " ").replace("_", " ").split():
        if len(out) + len(w) + bool(out) > n:
            break
        out += (" " if out else "") + w
    return out or s.upper()[:n]


def board_rows(recent: list[dict], now: dt.datetime) -> list[tuple[list[str], str]]:
    rows = []
    for r in recent:
        pushed = dt.datetime.fromisoformat(r["pushedAt"].replace("Z", "+00:00"))
        age = (now - pushed).total_seconds() / 86400
        status = "BOARDING" if age <= 3 else "IN FLIGHT" if age <= 30 else "LANDED"
        lang = (r.get("primaryLanguage") or {}).get("name")
        gate = GATES.get(lang, (lang or "--")[:3].upper())
        flight = "AS " + hashlib.sha256(r["name"].encode()).hexdigest()[:3].upper()
        rows.append(([pushed.strftime("%H:%M"), flight, fit_words(r["name"], 18), gate, status], status))
    return rows


def render_board(d: dict, t: dict) -> str:
    """Recent pushes as a split-flap departures board; every tile flips through letters before it lands."""
    now = dt.datetime.now(dt.timezone.utc)
    rows = board_rows(d["recent"], now)
    uv = t["name"] == "uv"
    cols = [("TIME", 5), ("FLIGHT", 6), ("DESTINATION", 18), ("GATE", 3), ("REMARKS", 9)]
    pitch, tw, th, gap, rh = 24, 22, 40, 16, 54
    x0, y0 = 76, 118
    W, H = 1200, y0 + max(len(rows), 1) * rh + 34
    pal = dict(board="#101B30" if not uv else "#07060F", tile="#1C2B48" if not uv else "#16152E",
               lo="#18263F" if not uv else "#121127", ch="#EEF2F1" if not uv else "#E6E8FF",
               lab="#8FA3B8" if not uv else "#9296CC", amber="#F5B93D" if not uv else "#FFB04A",
               fly="#7FD6CB" if not uv else "#5CF2C8", land="#8FA3B8" if not uv else "#9296CC")
    tone = {"BOARDING": pal["amber"], "IN FLIGHT": pal["fly"], "LANDED": pal["land"]}
    rng = random.Random(d["created"] + str(len(rows)))
    b = [f'<rect width="{W}" height="{H}" rx="26" fill="{pal["board"]}"/>'
         f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="25.5" fill="none" stroke="{t["edge"]}" opacity="{.6 if uv else 0}"/>'
         f'<text x="{x0}" y="62" class="fv" font-size="28" letter-spacing="9" fill="{pal["ch"]}">DEPARTURES</text>'
         f'<text x="{W - x0}" y="62" text-anchor="end" class="fm" font-size="15" fill="{pal["lab"]}">LAST PUSH, UTC / UPDATED {now.strftime("%H:%M")}</text>']
    xs, x = [], x0
    for name, n in cols:
        xs.append(x)
        b.append(f'<text x="{x}" y="100" class="fl" font-size="12.5" letter-spacing="1.6" fill="{pal["lab"]}">{name}</text>')
        x += n * pitch + gap
    clips, cells = [], []
    for ri, (vals, status) in enumerate(rows):
        top = y0 + ri * rh
        clips.append(f'<clipPath id="r{ri}"><rect x="0" y="{top}" width="{W}" height="{th}"/></clipPath>')
        row = [f'<g clip-path="url(#r{ri})">']
        settle = 0
        for ci, ((_, n), val) in enumerate(zip(cols, vals)):
            col_cells = []
            for k in range(n):
                cx = xs[ci] + k * pitch
                ch = val[k] if k < len(val) else " "
                flips = rng.randint(3, 8)
                dl = .25 + ri * .16 + (xs[ci] - x0 + k * pitch) / pitch * .022
                dur = flips * .065
                settle = max(settle, dl + dur)
                fill = tone[status] if ci == 4 else pal["ch"]
                strip = "".join(f'<tspan x="{cx + tw / 2}" y="{top + 29 + j * th}">{rng.choice(FLAPS)}</tspan>' for j in range(1, flips + 1))
                col_cells.append(
                    f'<rect x="{cx}" y="{top}" width="{tw}" height="{th}" rx="3" fill="{pal["tile"]}"/>'
                    f'<rect x="{cx}" y="{top + th / 2}" width="{tw}" height="{th / 2}" rx="3" fill="{pal["lo"]}"/>'
                    f'<text class="fm fp" font-size="25" text-anchor="middle" fill="{fill}" '
                    f'style="--k:-{flips * th}px;animation-duration:{dur:.2f}s;animation-delay:{dl:.2f}s;animation-timing-function:steps({flips},end)">'
                    f'<tspan x="{cx + tw / 2}" y="{top + 29}">{esc(ch) if ch != " " else "&#160;"}</tspan>{strip}</text>'
                    f'<rect class="fh" x="{cx}" y="{top}" width="{tw}" height="{th / 2}" fill="#fff" opacity="0" '
                    f'style="animation-duration:.065s;animation-delay:{dl:.2f}s;animation-iteration-count:{flips}"/>')
            if ci == 4 and status == "BOARDING":
                row.append(f'<g class="bl" style="animation-delay:{settle:.2f}s">{"".join(col_cells)}</g>')
            else:
                row += col_cells
        row.append(f'<rect x="0" y="{top + th / 2 - .75}" width="{W}" height="1.5" fill="{pal["board"]}"/></g>')
        cells.append("".join(row))
    if not rows:
        cells.append(f'<text x="{x0}" y="{y0 + 30}" class="fm" font-size="22" fill="{pal["lab"]}">NO DEPARTURES TODAY</text>')
    b.insert(0, f"<defs>{''.join(clips)}</defs>")
    b += cells
    names = ", ".join(f"{v[2].lower()} {s.lower()}" for v, s in rows)
    return finish("".join(b), W, H, f"Departures board of recently pushed repositories: {names}.", BOARD_CSS)


# ---------------------------------------------------------------- ink pads (pick an ink, open the customs form)

INKS = {"Red": ("#C42F2A", "#FF6B4A"), "Blue": ("#1F4FA8", "#7FA8FF"),
        "Violet": ("#5B3C9E", "#C79BFF"), "Green": ("#1E7A55", "#5CF2C8")}
SHAPES = ["Round", "Octagon", "Shield"]
PURPOSES = ["Collaboration", "Hiring", "Learning", "Sightseeing"]

PAD_CSS = """
.sh{animation:sh 3.6s cubic-bezier(.45,0,.55,1) infinite}
@keyframes sh{from{transform:translateX(-140px)}to{transform:translateX(320px)}}
.dab{transform-box:fill-box;transform-origin:center;animation:dab 4.8s cubic-bezier(.16,1,.3,1) infinite both}
@keyframes dab{0%{opacity:0;transform:scale(1.25)}7%{opacity:.6;transform:scale(1)}55%,100%{opacity:0;transform:scale(1)}}
"""


def render_pad(i: int, name: str, t: dict) -> str:
    W, H = 280, 150
    c = INKS[name][t["name"] == "uv"]
    uv = t["name"] == "uv"
    tin = "#B9C6C2" if not uv else "#2C2856"
    b = [f'<defs><clipPath id="felt"><rect x="34" y="30" width="212" height="70" rx="10"/></clipPath>'
         f'<filter id="tx"><feTurbulence type="fractalNoise" baseFrequency=".7" numOctaves="2" seed="{i + 3}"/>'
         f'<feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -1.6 1.25"/><feComposite in2="SourceGraphic" operator="in"/></filter>'
         f'<linearGradient id="sg"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity="{.32 if not uv else .22}"/>'
         f'<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>'
         f'<rect x="20" y="16" width="240" height="98" rx="18" fill="{tin}"/>'
         f'<rect x="20.5" y="16.5" width="239" height="97" rx="17.5" fill="none" stroke="{t["ink"]}" stroke-opacity=".25"/>'
         f'<g clip-path="url(#felt)"><rect x="34" y="30" width="212" height="70" fill="{c}"/>'
         f'<rect x="34" y="30" width="212" height="70" fill="#000" opacity=".35" filter="url(#tx)"/>'
         f'<circle class="dab" cx="{110 + i * 17}" cy="65" r="22" fill="none" stroke="#000" stroke-opacity=".5" stroke-width="4" style="animation-delay:{i * 1.2:.1f}s"/>'
         f'<rect class="sh" x="34" y="20" width="70" height="90" fill="url(#sg)" transform="skewX(-18)" style="animation-delay:{i * .4:.1f}s"/></g>'
         f'<text x="{W / 2}" y="140" text-anchor="middle" class="fl" font-size="15" letter-spacing="3" fill="{t["label"]}">{name.upper()}</text>']
    return finish("".join(b), W, H, f"{name} ink pad: open the customs declaration with {name.lower()} ink", PAD_CSS)


def outline(shape: str, cx: float, cy: float, r: float) -> list[str]:
    """Outer and inner rule of a visitor stamp."""
    if shape == "Octagon":
        return [poly([(cx + q * math.cos(math.radians(22.5 + 45 * k)), cy + q * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)])
                for q in (r, r * .84)]
    if shape == "Shield":
        def sh(q):
            return (f"M{f1(cx - q * .86)} {f1(cy - q * .8)}H{f1(cx + q * .86)}V{f1(cy + q * .1)}"
                    f"C{f1(cx + q * .86)} {f1(cy + q * .55)} {f1(cx + q * .4)} {f1(cy + q * .8)} {f1(cx)} {f1(cy + q)}"
                    f"C{f1(cx - q * .4)} {f1(cy + q * .8)} {f1(cx - q * .86)} {f1(cy + q * .55)} {f1(cx - q * .86)} {f1(cy + q * .1)}Z")
        return [sh(r), sh(r * .84)]
    return [f"M{f1(cx - q)} {f1(cy)}a{q} {q} 0 1 0 {f1(2 * q)} 0a{q} {q} 0 1 0 {f1(-2 * q)} 0Z" for q in (r, r * .78)]


def declaration(body: str, login: str) -> dict:
    """Read the customs form out of an issue body. Untrusted: only whitelisted values survive."""
    fields = {k.strip().lower(): v.strip() for k, v in re.findall(r"^###\s*(.+?)\s*\n+([^\n#][^\n]*)", body or "", re.M)}
    pick = int(hashlib.sha256(login.lower().encode()).hexdigest(), 16)
    ink = fields.get("ink", "").title()
    shape = fields.get("stamp shape", "").title()
    purpose = fields.get("purpose of visit", "").title()
    return {"ink": ink if ink in INKS else list(INKS)[pick % 4],
            "shape": shape if shape in SHAPES else "Round",
            "purpose": purpose if purpose in PURPOSES else None}


_form = "### Purpose of visit\n\nHiring\n\n### Ink\n\nviolet\n\n### Stamp shape\n\n_No response_\n"
assert declaration(_form, "x") == {"ink": "Violet", "shape": "Round", "purpose": "Hiring"}
assert declaration("### Ink\n\n<script>", "x")["ink"] in INKS


# ---------------------------------------------------------------- chip readout (inside README)


def chip_block(portrait: str) -> str:
    line1 = mrz("0" * 64)[0]
    lines = portrait.count("Z")
    p_hash = hashlib.sha256(portrait.encode()).hexdigest()
    return "\n".join([
        "```console",
        "> SELECT AID A0 00 00 02 47 10 01   # the ICAO eMRTD applet",
        "< 90 00",
        f"> READ DG1    {line1}",
        f"> READ DG2    portrait, {lines} engraved lines, sha256 {p_hash[:16]}",
        f"> READ DG11   {HOLDER['institution']} / {HOLDER['field']}",
        f"> READ DG15   public key {key_pins()}, cut into the key at the bottom",
        "> READ SOD    signed by Sigstore from GitHub Actions; verify it below",
        "< 90 00",
        "```",
    ])


# ---------------------------------------------------------------- stamped visitors

REG_CSS = """
.slot{transform-origin:120px 110px;animation:spin 24s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
"""


def visitor_mark(cx, cy, r, login, serial, c, fid, cls_size=1.0, shape="Round") -> str:
    login = login.upper()
    size = 15 * cls_size
    room = r * 1.45
    while size > 8 and text_len("fv", login, size) > room:
        size -= .5
    while len(login) > 4 and text_len("fv", login, size) > room:
        login = login[:-2] + "…"
    o, i = outline(shape, cx, cy, r)
    return (f'<g filter="url(#{fid})" fill="none" stroke="{c}"><path d="{o}" stroke-width="3"/>'
            f'<path d="{i}" stroke-width="1"/>'
            f'<text x="{cx}" y="{cy + 4}" text-anchor="middle" class="fv" font-size="{size:.1f}" fill="{c}" stroke="none">{esc(login)}</text>'
            f'<text x="{cx}" y="{cy + 22}" text-anchor="middle" class="fm" font-size="10" fill="{c}" stroke="none">No. {serial:04d}</text></g>')


def render_registry(entries: list[dict], t: dict) -> str:
    W, H = 1200, 220
    recent = entries[-7:][::-1]
    root = merkle([e["digest"] for e in entries]) if entries else "0" * 64
    b = [f'<defs><filter id="rv" x="-5%" y="-5%" width="110%" height="110%"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="5"/>'
         f'<feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -1.3 1.45"/><feComposite in="SourceGraphic" operator="in"/></filter></defs>']
    if not entries:  # lead with the invitation; the counter means nothing at zero
        b.append(f'<g class="slot" fill="none" stroke="{t["label"]}" stroke-width="2" stroke-dasharray="6 7"><circle cx="120" cy="110" r="74"/></g>'
                 f'<text x="120" y="115" text-anchor="middle" class="fl" font-size="14.5" letter-spacing="2" fill="{t["label"]}">YOUR STAMP</text>'
                 f'<text x="232" y="98" class="fv" font-size="30" fill="{t["ink"]}">No one stamped yet.</text>'
                 f'<text x="232" y="134" class="fb" font-size="19" fill="{t["label"]}">Pick an ink above, fill in the declaration, and No. 0001 is yours.</text>')
        return finish("".join(b), W, H, "No visitors stamped yet. Open an issue titled stamp me to get the first stamp.", REG_CSS)
    b.append(f'<text x="40" y="50" class="fl" font-size="14.5" letter-spacing="1.4" fill="{t["label"]}">STAMPS ISSUED</text>'
             f'<text x="40" y="96" class="fv" font-size="40" fill="{t["ink"]}">{len(entries):,}</text>'
             f'<text x="40" y="150" class="fl" font-size="14.5" letter-spacing="1.4" fill="{t["label"]}">MERKLE ROOT</text>'
             f'<text x="40" y="172" class="fm" font-size="12.5" fill="{t["ink"]}">{root[:22]}</text>'
             f'<text x="40" y="190" class="fm" font-size="12.5" fill="{t["ink"]}">{root[22:44]}</text>'
             f'<line x1="300" y1="36" x2="300" y2="190" stroke="{t["edge"]}"/>')
    for k, e in enumerate(recent):
        cx = 400 + k * 120
        c = INKS[e["ink"]][t["name"] == "uv"] if e.get("ink") in INKS else t["stamp_inks"][k % len(t["stamp_inks"])]
        rot = random.Random(e["login"]).uniform(-12, 12)
        b.append(f'<g class="ink" style="animation-delay:{.15 + k * .12:.2f}s"><g transform="rotate({rot:.1f} {cx} 112)">'
                 + visitor_mark(cx, 112, 56, e["login"], e["serial"], c, "rv", .8, e.get("shape", "Round")) + "</g></g>")
    return finish("".join(b), W, H, f"{len(entries)} visitors stamped. Merkle root {root[:16]}.", REG_CSS + STAMP_CSS)


def merkle(leaves: list[str]) -> str:
    level = [bytes.fromhex(x) for x in leaves]
    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])
        level = [hashlib.sha256(level[i] + level[i + 1]).digest() for i in range(0, len(level), 2)]
    return level[0].hex()


# ---------------------------------------------------------------- 3D seal (inline STL)


def earclip(pts: list[tuple[float, float]]) -> list[tuple[int, int, int]]:
    """Triangulate a simple counter-clockwise polygon."""
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    idx, out = list(range(len(pts))), []
    while len(idx) > 3:
        for k in range(len(idx)):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            a, b, c = pts[i0], pts[i1], pts[i2]
            if cross(a, b, c) <= 1e-9:
                continue
            if any(cross(a, b, pts[j]) >= 0 and cross(b, c, pts[j]) >= 0 and cross(c, a, pts[j]) >= 0
                   for j in idx if j not in (i0, i1, i2)):
                continue
            out.append((i0, i1, i2))
            idx.pop(k)
            break
        else:
            raise ValueError("polygon is not simple or not counter-clockwise")
    out.append(tuple(idx))
    return out


def _area(pts, tris):
    return sum(abs((pts[b][0] - pts[a][0]) * (pts[c][1] - pts[a][1]) - (pts[b][1] - pts[a][1]) * (pts[c][0] - pts[a][0])) / 2
               for a, b, c in tris)


_L = [(0, 0), (2, 0), (2, 1), (1, 1), (1, 3), (0, 3)]  # an L, area 4
assert abs(_area(_L, earclip(_L)) - 4) < 1e-9


def key_pins() -> str:
    return hashlib.sha256(USER.encode()).hexdigest()[:9]


def key_stl(weeks: list[dict]) -> str:
    """A key: nine pins cut to sha256(username); the grip's ridges are the last twelve months of commits."""
    tris = []
    T = 2.6

    def quad(a, b, c, d):
        tris.append((a, b, c))
        tris.append((a, c, d))

    def prism(poly2d, z0, z1):
        for a, b, c in earclip(poly2d):
            tris.append(((*poly2d[a], z1), (*poly2d[b], z1), (*poly2d[c], z1)))
            tris.append(((*poly2d[a], z0), (*poly2d[c], z0), (*poly2d[b], z0)))
        m = len(poly2d)
        for i in range(m):
            p, q = poly2d[i], poly2d[(i + 1) % m]
            quad((*p, z0), (*q, z0), (*q, z1), (*p, z1))

    # blade: pins as V cuts along the bottom edge, a shoulder stop, a pointed tip
    pins = [int(h, 16) for h in key_pins()]
    base, topy = -4.4, 4.4
    blade = [(11, base), (15, base), (15, base - 2.2), (18.5, base - 2.2), (18.5, base)]
    for k, h in enumerate(pins):
        c = 23 + k * 4.6
        y = base + .36 * h
        if k == 0:
            blade.append((c - 2.3, base))
        blade += [(c - .55, y), (c + .55, y), (c + 2.3, base)]
    blade += [(66, base), (69, -1.2), (68.5, 1.6), (65.5, topy), (11, topy)]
    prism(blade, 0, T)
    prism([(19, .9), (61, .9), (61, 2.3), (19, 2.3)], T, T + .7)       # warding ridge, front
    prism([(19, -1.9), (61, -1.9), (61, -.5), (19, -.5)], -.7, 0)      # warding ridge, back

    # bow: a ring whose outer edge rises once per month of activity
    months: dict[tuple[int, int], int] = {}
    for w in weeks:
        for c in w["contributionDays"]:
            dd = dt.date.fromisoformat(c["date"])
            months[(dd.year, dd.month)] = months.get((dd.year, dd.month), 0) + c["contributionCount"]
    vals = [months[k] for k in sorted(months)][-12:]
    vals = [0] * (12 - len(vals)) + vals
    top = max(vals) or 1
    seg, r_in, r_out = 96, 5.6, 13.5
    a_lo, a_hi = math.radians(30), math.radians(330)   # leave the neck where the blade joins
    ring = []
    for j in range(seg):
        a = 2 * math.pi * j / seg
        r = r_out
        if a_lo <= a <= a_hi:
            f = (a - a_lo) / (a_hi - a_lo) * 12
            m, frac = min(int(f), 11), f - int(f)
            r += (1.1 + 4.4 * (vals[m] / top) ** .7) * math.sin(math.pi * frac) ** 2
        ring.append(((r_in * math.cos(a), r_in * math.sin(a)), (r * math.cos(a), r * math.sin(a))))
    for j in range(seg):
        (i0, o0), (i1, o1) = ring[j], ring[(j + 1) % seg]
        quad((*i0, T), (*o0, T), (*o1, T), (*i1, T))
        quad((*i1, 0), (*o1, 0), (*o0, 0), (*i0, 0))
        quad((*o0, 0), (*o1, 0), (*o1, T), (*o0, T))
        quad((*i1, 0), (*i0, 0), (*i0, T), (*i1, T))

    def v(p):
        return " ".join(f1(c) for c in p)

    lines = ["solid key"]
    for a, b_, c in tris:
        u = [b_[i] - a[i] for i in range(3)]
        w = [c[i] - a[i] for i in range(3)]
        nrm = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0])
        ln = math.sqrt(sum(x * x for x in nrm)) or 1
        lines.append(f"facet normal {' '.join(f1(x / ln) for x in nrm)}\nouter loop\nvertex {v(a)}\nvertex {v(b_)}\nvertex {v(c)}\nendloop\nendfacet")
    lines.append("endsolid key")
    return "\n".join(lines)


def write_block(name: str, content: str) -> None:
    text = README.read_text(encoding="utf-8")
    start, end = f"<!-- {name}:start -->", f"<!-- {name}:end -->"
    if start not in text or end not in text:
        print(f"README has no {name} markers; skipping", file=sys.stderr)
        return
    block = f"{start}\n{content}\n{end}"
    text = re.sub(re.escape(start) + r".*?" + re.escape(end), lambda _: block, text, flags=re.S)
    README.write_bytes(text.encode("utf-8"))


def write_seal(weeks: list[dict]) -> None:
    caption = (f"Nine pins, cut to the first nine hex digits of `sha256(\"{USER}\")` = `{key_pins()}`. "
               "The ridges on the grip are the last twelve months of commits. Drag to turn it.")
    write_block("seal", f"{caption}\n\n```stl\n{key_stl(weeks)}\n```")


# ---------------------------------------------------------------- visitor stamp


def load_registry() -> list[dict]:
    idx = STAMPS / "index.json"
    return json.loads(idx.read_text(encoding="utf-8")) if idx.exists() else []


def issue_stamp(login: str, serial: int | None = None, body: str = "") -> dict:
    """Write stamps/<login>.json + .svg and update the registry. Idempotent per login."""
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})", login):
        raise SystemExit(f"refusing odd login: {login!r}")
    STAMPS.mkdir(exist_ok=True)
    entries = load_registry()
    existing = next((e for e in entries if e["login"].lower() == login.lower()), None)
    if existing:
        return existing
    serial = serial or len(entries) + 1
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    decl = declaration(body, login)
    cred = {
        "@context": ["https://www.w3.org/ns/credentials/v2"],
        "type": ["VerifiableCredential", "VisaStamp"],
        "issuer": f"https://github.com/{USER}",
        "validFrom": now,
        "credentialSubject": {"id": f"https://github.com/{login}", "serial": serial, **{k: v for k, v in decl.items() if v}},
        "proof": "Sigstore attestation via GitHub Actions; verify with: "
                 f"gh attestation verify stamps/{login}.json -R {USER}/{USER}",
    }
    raw = json.dumps(cred, indent=2).encode() + b"\n"
    (STAMPS / f"{login}.json").write_bytes(raw)
    entry = {"login": login, "serial": serial, "issued": now, **decl, "digest": hashlib.sha256(raw).hexdigest()}
    entries.append(entry)
    (STAMPS / "index.json").write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")
    (STAMPS / f"{login}.svg").write_text(render_visitor(entry), encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    for t in (DAY, UV):
        (OUT / f"registry-{t['name']}.svg").write_text(render_registry(entries, t), encoding="utf-8")
    return entry


def render_visitor(e: dict) -> str:
    """The stamp a visitor embeds in their own README; themes itself."""
    W = H = 300
    date = fmt_date(e["issued"])
    shape = e.get("shape", "Round")
    day, uv = INKS.get(e.get("ink"), INKS["Red"])
    o, i = outline(shape, 150, 150 if shape != "Shield" else 146, 138)
    if shape == "Round":
        rim = (_arc_text(150, 150, 116, f"VERIFIED BY {USER.upper()}", 12.5, "currentColor", -90, 230, "va", spacing=2)
               + _arc_text(150, 150, 128, date, 13, "currentColor", 90, -90, "vb", "fm", 2))
    else:
        top = f"VERIFIED BY {USER.upper()}"
        ts = 10.5
        while ts > 7 and text_len("fl", top, ts, 1.4) > 150:
            ts -= .25
        rim = (f'<text x="150" y="{90 if shape == "Octagon" else 80}" text-anchor="middle" class="fl" font-size="{ts}" letter-spacing="1.4" fill="currentColor">{top}</text>'
               f'<text x="150" y="{232 if shape == "Octagon" else 222}" text-anchor="middle" class="fm" font-size="12.5" fill="currentColor">{date}</text>')
    purpose = ""
    if e.get("purpose"):
        pt, ps = f'PURPOSE / {e["purpose"].upper()}', 10.5
        while ps > 7 and text_len("fl", pt, ps, 1.6) > 140:
            ps -= .25
        purpose = (f'<text x="150" y="{198 if shape != "Shield" else 194}" text-anchor="middle" class="fl" font-size="{ps}" '
                   f'letter-spacing="1.6" fill="currentColor">{pt}</text>')
    body = (f'<defs><filter id="rv" x="-5%" y="-5%" width="110%" height="110%"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="4"/>'
            f'<feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -1.3 1.45"/><feComposite in="SourceGraphic" operator="in"/></filter></defs>'
            f'<g class="ink c" transform="rotate(-8 150 150)" filter="url(#rv)" fill="none">'
            f'<path d="{o}" stroke-width="5"/><path d="{i}" stroke-width="1.6"/>' + rim + purpose
            + f'<text x="150" y="146" text-anchor="middle" class="fv" font-size="{max(12, min(28, 170 / max(len(e["login"]), 1))):.0f}" fill="currentColor">{esc(e["login"].upper())}</text>'
            f'<text x="150" y="174" text-anchor="middle" class="fm" font-size="15" fill="currentColor">No. {e["serial"]:04d}</text></g>')
    css = (f".c{{color:{day};stroke:{day}}}@media (prefers-color-scheme:dark){{.c{{color:{uv};stroke:{uv}}}}}"
           + STAMP_CSS)
    return finish(body, W, H, f"Visa stamp No. {e['serial']} for {e['login']}, issued by {USER}", css)


# ---------------------------------------------------------------- main


def build(data: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = digest(data)
    portrait = portrait_paths(d["avatar"], 68, 150, 262, 338) if d["avatar"] else ""
    write_seal(d["weeks"])
    write_block("chip", chip_block(portrait))
    doc_hash = hashlib.sha256(README.read_bytes()).hexdigest()  # after the blocks: this is the file we sign
    entries = load_registry()
    for t in (DAY, UV):
        (OUT / f"passport-{t['name']}.svg").write_text(render_passport(d, t, doc_hash, portrait), encoding="utf-8")
        (OUT / f"log-{t['name']}.svg").write_text(render_log(d, t), encoding="utf-8")
        (OUT / f"board-{t['name']}.svg").write_text(render_board(d, t), encoding="utf-8")
        for i, ink_name in enumerate(INKS):
            (OUT / f"pad-{ink_name.lower()}-{t['name']}.svg").write_text(render_pad(i, ink_name, t), encoding="utf-8")
        (OUT / f"registry-{t['name']}.svg").write_text(render_registry(entries, t), encoding="utf-8")
        for i, (repo, name, title, port, stack) in enumerate(d["visas"]):
            (OUT / f"visa-{i + 1}-{t['name']}.svg").write_text(render_visa(i, repo, name, title, port, stack, t), encoding="utf-8")
    print(f"built: document {doc_hash[:9].upper()}, {d['total']} contributions, {len(entries)} stamps")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?", default="cards", choices=["cards", "stamp"])
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--login")
    ap.add_argument("--serial", type=int)
    a = ap.parse_args()
    if a.cmd == "stamp":
        if not a.login:
            ap.error("stamp needs --login")
        e = issue_stamp(a.login, a.serial, os.environ.get("ISSUE_BODY", ""))
        print(json.dumps(e))
        return 0
    token = os.environ.get("GITHUB_TOKEN")
    if a.mock or not token:
        if not a.mock:
            print("no GITHUB_TOKEN; using --mock data", file=sys.stderr)
        data = mock()
    else:
        data = fetch(token)
    build(data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
