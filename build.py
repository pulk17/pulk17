#!/usr/bin/env python3
"""Builds the profile README's images (assets/*.svg) and README.md.

Look: plain ink on a transparent background, so the images sit on GitHub's own
page in light and dark mode. One accent, a violet close to GitHub's "merged"
purple, used only on things that were actually shipped or measured. The only
motion is the order book in the hero.

Type is Geist, converted to outlines so every viewer sees the same thing.

    npm i @fontsource/geist-sans@5.3.0 @fontsource/geist-mono@5.3.0
    pip install fonttools brotli
    FONTDIR=node_modules/@fontsource python3 build.py

The "Open source" table is not written here: scripts/contrib.py owns the block
between <!-- contrib:start --> and <!-- contrib:end -->, and this script keeps
whatever is there.
"""
import html
import json
import math
import os

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

OUT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(OUT, "assets")
FONTDIR = os.environ.get("FONTDIR", "node_modules/@fontsource")
FACES = {
    "r": f"{FONTDIR}/geist-sans/files/geist-sans-latin-400-normal.woff2",
    "m": f"{FONTDIR}/geist-sans/files/geist-sans-latin-500-normal.woff2",
    "b": f"{FONTDIR}/geist-sans/files/geist-sans-latin-600-normal.woff2",
    "mono": f"{FONTDIR}/geist-mono/files/geist-mono-latin-400-normal.woff2",
}
_F = {k: TTFont(p) for k, p in FACES.items()}

# Text colours match GitHub's own so the images read as part of the page.
THEMES = {
    "light": dict(ink="#1F2328", sub="#59636E", faint="#D1D9E0", wash="#F6F8FA", acc="#6E40C9", acc2="#E9E1FB"),
    "dark": dict(ink="#E6EDF3", sub="#9198A1", faint="#30363D", wash="#151B23", acc="#B392F0", acc2="#2A2140"),
}
W = 720  # every image shares this width, so they line up on the page


# ------------------------------------------------------------------ type engine
def width(s, face, size, ls=0.0):
    f = _F[face]
    cmap, hmtx, upm = f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm
    tot = 0
    for ch in s:
        if ord(ch) not in cmap:
            raise ValueError(f"glyph {ch!r} missing from {face}")
        tot += hmtx[cmap[ord(ch)]][0]
    return tot * size / upm + ls * max(len(s) - 1, 0)


def wrap(s, face, size, maxw):
    lines, cur = [], ""
    for w in s.split():
        t = (cur + " " + w).strip()
        if width(t, face, size) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    return lines + ([cur] if cur else [])


class Svg:
    def __init__(self, h, title, desc, theme):
        self.h, self.title, self.desc, self.P = h, title, desc, THEMES[theme]
        self.els, self.defs, self.css, self.glyphs = [], [], [], {}

    def add(self, s):
        self.els.append(s)

    def text(self, x, y, s, face, size, fill, anchor="start", ls=0.0, cls=""):
        f = _F[face]
        cmap, hmtx, upm = f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm
        w = width(s, face, size, ls)
        x0 = {"start": x, "middle": x - w / 2, "end": x - w}[anchor]
        k, pen, uses = size / upm, 0.0, []
        for ch in s:
            g = cmap[ord(ch)]
            if ch != " ":
                uses.append(f'<use href="#{self.glyph(face, g)}" x="{pen / k:.0f}"/>')
            pen += hmtx[g][0] * k + ls
        c = f' class="{cls}"' if cls else ""
        self.add(f'<g{c} fill="{fill}" transform="translate({x0:.2f} {y:.2f}) scale({k:.5f} {-k:.5f})">{"".join(uses)}</g>')
        return w

    def para(self, x, y, s, face, size, fill, maxw, lead):
        lines = wrap(s, face, size, maxw)
        for i, line in enumerate(lines):
            self.text(x, y + i * lead, line, face, size, fill)
        return y + (len(lines) - 1) * lead

    def glyph(self, face, g):
        if (face, g) not in self.glyphs:
            gs = _F[face].getGlyphSet()
            pen = SVGPathPen(gs)
            gs[g].draw(pen)
            gid = f"{face}{len(self.glyphs):x}"
            self.glyphs[(face, g)] = gid
            self.defs.append(f'<path id="{gid}" d="{pen.getCommands()}"/>')
        return self.glyphs[(face, g)]

    def render(self):
        t, d = html.escape(self.title), html.escape(self.desc)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {self.h}" width="{W}" height="{self.h}" '
                f'role="img" aria-labelledby="t d"><title id="t">{t}</title><desc id="d">{d}</desc>'
                f'<style>{"".join(self.css)}</style><defs>{"".join(self.defs)}</defs>{"".join(self.els)}</svg>\n')


def chips(s, x, y, items):
    """Tech stack as quiet words separated by space, not dots."""
    P = s.P
    for it in items:
        x += s.text(x, y, it, "r", 12.5, P["sub"]) + 16


# ------------------------------------------------------------------ hero
HERO_FACTS = [
    ("Upstream C++", "PRs to ClickHouse, Boost", "and Microsoft STL"),
    ("1986", "peak Codeforces rating,", "Candidate Master"),
    ("GSoC 2026", "Google Summer of Code", "with CCExtractor"),
]
# Projects drawn as branches merging into main: (row in the Open source table, label).
HERO_BRANCHES = [("ClickHouse", "ClickHouse"), ("Microsoft STL", "Microsoft STL"),
                 ("CCExtractor", "CCExtractor"), ("Boost.Geometry", "Boost")]
SUMMARY = os.path.join(OUT, "contrib.summary.json")  # written by scripts/contrib.py


def branch_status():
    """{name: (merged, open)} from the last contrib.py run, so the dots stay true."""
    if not os.path.exists(SUMMARY):
        return {}
    with open(SUMMARY) as f:
        return {k: (v["merged"], v["open"]) for k, v in json.load(f).items()}


def status_words(merged, open_):
    parts = ([f"{merged} merged"] if merged else []) + ([f"{open_} in review"] if open_ else [])
    return ", ".join(parts)


def hero_alt(st):
    rows = []
    for key, label in HERO_BRANCHES:
        m, o = st.get(key, (0, 0))
        rows.append(f"{label} ({status_words(m, o)})" if (m or o) else label)
    return ("Pulkit Chauhan. C++ systems engineer who contributes to databases and core C++ libraries. "
            "Final-year computer science student at UPES, open to software engineering roles from January 2027. "
            "Open-source work drawn as branches merging into main: " + "; ".join(rows) + ". "
            "Upstream C++ PRs to ClickHouse, Boost and Microsoft STL. Peak Codeforces rating 1986, Candidate Master. "
            "Google Summer of Code 2026 with CCExtractor.")


def merge_lines(s, st, x0, y0):
    """Each project is a branch. A filled dot means work merged there, a hollow
    one means it's in review. Merged branches send a pulse into main."""
    P = s.P
    trunk, start, node, end = W - 70, x0 + 118, x0 + 148, W
    rows = [y0 + 22 + i * 38 for i in range(len(HERO_BRANCHES))]
    main_y = rows[-1] + 62
    s.css.append(".pulse{opacity:0}@media (prefers-reduced-motion:reduce){.pulse{display:none}}")

    def route(y):  # branch -> trunk -> main, one path so a pulse can ride it end to end
        return (f"M{start},{y} H{trunk - 26} Q{trunk},{y} {trunk},{y + 26} "
                f"V{main_y - 26} Q{trunk},{main_y} {trunk + 26},{main_y} H{end}")

    # trunk and main
    s.add(f'<path d="M{trunk},{rows[0] + 26} V{main_y - 26} Q{trunk},{main_y} {trunk + 26},{main_y} H{end}" '
          f'fill="none" stroke="{P["ink"]}" stroke-width="1.4"/>')
    s.text(end, main_y - 9, "main", "m", 11, P["sub"], anchor="end")
    for i, ((key, label), y) in enumerate(zip(HERO_BRANCHES, rows)):
        m, o = st.get(key, (0, 0))
        s.text(x0, y + 1, label, "m", 13, P["ink"])
        words = status_words(m, o)
        if words:
            s.text(x0, y + 16, words, "r", 11, P["sub"])
        s.add(f'<path d="M{start},{y} H{node - 6}" stroke="{P["sub"]}" stroke-width="1"/>'
              f'<path d="M{node + 6},{y} H{trunk - 26} Q{trunk},{y} {trunk},{y + 26}" fill="none" stroke="{P["sub"]}" stroke-width="1"/>')
        if m:
            s.add(f'<circle cx="{node}" cy="{y}" r="4.5" fill="{P["acc"]}"/>')
            s.add(f'<circle class="pulse" r="2.6" fill="{P["acc"]}">'
                  f'<animateMotion dur="3.4s" begin="{i * 1.1:.1f}s" repeatCount="indefinite" path="{route(y)}"/>'
                  f'<animate attributeName="opacity" dur="3.4s" begin="{i * 1.1:.1f}s" repeatCount="indefinite" '
                  f'values="0;1;1;0" keyTimes="0;0.1;0.85;1"/></circle>')
        else:
            s.add(f'<circle cx="{node}" cy="{y}" r="4" fill="none" stroke="{P["acc"]}" stroke-width="1.3"/>')
    # legend
    ly = main_y + 4
    s.add(f'<circle cx="{x0 + 4}" cy="{ly - 4}" r="3.5" fill="{P["acc"]}"/>')
    w = s.text(x0 + 13, ly, "merged", "r", 11, P["sub"])
    lx = x0 + 13 + w + 16
    s.add(f'<circle cx="{lx + 4}" cy="{ly - 4}" r="3.2" fill="none" stroke="{P["acc"]}" stroke-width="1.2"/>')
    s.text(lx + 13, ly, "in review", "r", 11, P["sub"])
    return main_y


def hero(theme):
    st = branch_status()
    s = Svg(330, "Pulkit Chauhan", hero_alt(st), theme)
    P = s.P
    s.text(0, 52, "Pulkit Chauhan", "b", 44, P["ink"], ls=-1.3)
    y = s.para(0, 92, "C++ systems engineer. I contribute to databases and core C++ libraries.",
               "r", 19, P["ink"], 360, 26)
    s.para(0, y + 36, "Final-year computer science student at UPES. "
                      "Open to software engineering roles from January 2027.", "r", 14, P["sub"], 385, 21)
    merge_lines(s, st, 430, 8)
    s.add(f'<line x1="0" y1="234" x2="{W}" y2="234" stroke="{P["faint"]}" stroke-width="1"/>')
    col = W / 3
    for i, (fig, l1, l2) in enumerate(HERO_FACTS):
        x = i * col
        s.text(x, 274, fig, "b", 24, P["ink"], ls=-0.5)
        s.text(x, 298, l1, "r", 12.5, P["sub"])
        s.text(x, 316, l2, "r", 12.5, P["sub"])
    return s.render()


# ------------------------------------------------------------------ project cards
def card(theme, title, blurb, facts, stack, visual, alt, h=232):
    s = Svg(h, title, alt, theme)
    P = s.P
    s.text(0, 46, title, "b", 28, P["ink"], ls=-0.6)
    y = s.para(0, 78, blurb, "r", 15, P["ink"], 330, 22)
    y += 34
    for fig, cap in facts:
        w = s.text(0, y, fig, "m", 15, P["acc"])
        s.text(w + 8, y, cap, "r", 13, P["sub"])
        y += 22
    chips(s, 0, h - 16, stack)
    visual(s, 380, 30)
    return s.render()


# ITCH 5.0 "Add Order" message: field widths in bytes, from the spec.
ITCH_ADD = [("type", 1), ("locate", 2), ("track", 2), ("time", 6), ("order ref", 8),
            ("side", 1), ("shares", 4), ("stock", 8), ("price", 4)]


def vis_itch(s, x0, y0):
    """One 36-byte Add Order message, field by field, becoming a change in the book."""
    P = s.P
    span = W - x0
    unit = span / 36
    s.text(x0, y0 + 10, "One Add Order message, 36 bytes", "r", 12, P["sub"])
    y = y0 + 22
    x = x0
    hot = {"side", "shares", "price"}
    for name, n in ITCH_ADD:
        w = n * unit
        on = name in hot
        s.add(f'<rect x="{x + 0.5:.1f}" y="{y}" width="{w - 1:.1f}" height="26" rx="2" '
              f'fill="{P["acc2"] if on else "none"}" stroke="{P["acc"] if on else P["faint"]}" stroke-width="1"/>')
        if width(name, "r", 10) < w - 4:
            s.text(x + w / 2, y + 17, name, "r", 10, P["acc"] if on else P["sub"], anchor="middle")
        x += w
    # arrow down into the book
    ax = x0 + span * 0.78
    s.add(f'<path d="M{ax},{y + 34} V{y + 60}" stroke="{P["sub"]}" stroke-width="1" fill="none"/>'
          f'<path d="M{ax - 4},{y + 55} L{ax},{y + 61} L{ax + 4},{y + 55}" stroke="{P["sub"]}" stroke-width="1" fill="none"/>')
    by = y + 72
    s.text(x0, by - 4, "AAPL book", "r", 12, P["sub"])
    rows = [("145.66", 0.35, False), ("145.65", 0.55, False), ("145.64", 0.62, True), ("145.63", 0.80, False)]
    for i, (px, q, new) in enumerate(rows):
        yy = by + 6 + i * 17
        s.text(x0, yy + 11, px, "mono", 11, P["acc"] if new else P["sub"])
        bw = (span - 60) * q
        if i < 2:
            s.add(f'<rect x="{x0 + 52}" y="{yy}" width="{bw:.1f}" height="13" rx="1.5" fill="none" stroke="{P["sub"]}" stroke-width="1"/>')
        else:
            s.add(f'<rect x="{x0 + 52}" y="{yy}" width="{bw:.1f}" height="13" rx="1.5" fill="{P["acc"]}" fill-opacity="{0.95 if new else 0.55}"/>')
        if new:
            s.text(x0 + 52 + bw + 8, yy + 11, "+100", "mono", 11, P["acc"])


def vis_graph(s, x0, y0):
    """An app drawn as a graph. The new wire and node are the change waiting for approval."""
    P = s.P

    def node(x, y, label, new=False, w=96):
        s.add(f'<rect x="{x}" y="{y}" width="{w}" height="30" rx="6" fill="{P["acc2"] if new else "none"}" '
              f'stroke="{P["acc"] if new else P["sub"]}" stroke-width="1"{" stroke-dasharray=\"3 3\"" if new else ""}/>')
        s.text(x + w / 2, y + 19.5, label, "m" if new else "r", 12, P["acc"] if new else P["ink"], anchor="middle")
        return (x, y, w)

    def wire(a, b, new=False):
        (ax, ay, aw), (bx, by, _) = a, b
        x1, y1, x2, y2 = ax + aw, ay + 15, bx, by + 15
        mx = (x1 + x2) / 2
        s.add(f'<path d="M{x1},{y1} C{mx},{y1} {mx},{y2} {x2},{y2}" fill="none" '
              f'stroke="{P["acc"] if new else P["sub"]}" stroke-width="1"{" stroke-dasharray=\"3 3\"" if new else ""}/>')
        s.add(f'<circle cx="{x2}" cy="{y2}" r="2.2" fill="{P["acc"] if new else P["sub"]}"/>')

    ing = node(x0, y0 + 62, "Ingress", w=80)
    svc = node(x0 + 112, y0 + 62, "Service", w=82)
    dep = node(x0 + 226, y0 + 62, "Deployment", w=114)
    cfg = node(x0 + 112, y0 + 128, "ConfigMap", w=82, new=True)
    wire(ing, svc)
    wire(svc, dep)
    wire(cfg, dep, new=True)
    for i in range(3):
        px = x0 + 234 + i * 36
        s.add(f'<rect x="{px}" y="{y0 + 112}" width="26" height="20" rx="4" fill="none" stroke="{P["faint"]}" stroke-width="1"/>')
        s.add(f'<path d="M{x0 + 283},{y0 + 92} V{y0 + 112}" stroke="{P["faint"]}" stroke-width="1"/>')
    s.text(x0 + 234, y0 + 148, "3 pods", "r", 11, P["sub"])
    s.text(x0, y0 + 10, "Your app as a graph", "r", 12, P["sub"])
    s.text(x0 + 112, y0 + 178, "+ new, waits for your approval", "r", 11, P["acc"])


def vis_room(s, x0, y0):
    """Phones around the server. One vote goes in, the result goes out to everyone."""
    P = s.P
    cx, cy = x0 + 170, y0 + 98
    s.add(f'<circle cx="{cx}" cy="{cy}" r="30" fill="none" stroke="{P["ink"]}" stroke-width="1"/>')
    s.text(cx, cy + 4, "server", "m", 12, P["ink"], anchor="middle")
    n, r = 6, 86
    for i in range(n):
        a = -math.pi / 2 + (i - (n - 1) / 2) * (2 * math.pi / n)
        px, py = cx + r * 1.55 * math.cos(a), cy + r * 0.95 * math.sin(a)
        hot = i == 1
        x1, y1 = cx + 32 * math.cos(a), cy + 32 * math.sin(a)
        s.add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{px:.1f}" y2="{py:.1f}" stroke="{P["acc"] if hot else P["faint"]}" stroke-width="1"/>')
        s.add(f'<rect x="{px - 9:.1f}" y="{py - 15:.1f}" width="18" height="30" rx="4" fill="{P["acc2"] if hot else "none"}" '
              f'stroke="{P["acc"] if hot else P["sub"]}" stroke-width="1"/>')
        if hot:
            s.text(px, py - 22, "vote", "m", 11, P["acc"], anchor="middle")
    s.text(x0, y0 + 10, "One room", "r", 12, P["sub"])


CARDS = {
    "pitchfork": dict(
        title="PitchFork",
        blurb="Rebuilds the live order book for every stock from a full day of raw NASDAQ data, then tests trading signals on it.",
        facts=[("8.9M msg/s", "on one laptop core"), ("46 KB", "WebAssembly build that runs in the browser")],
        stack=["C++17", "WebAssembly", "Linux"], visual=vis_itch,
        alt="PitchFork: rebuilds the live order book for every stock from a full day of raw NASDAQ ITCH 5.0 data, "
            "then tests trading signals on it. 8.9 million messages a second on one laptop core. A 46 KB WebAssembly "
            "build runs in the browser. The drawing shows one 36-byte Add Order message, field by field, turning into "
            "a new level in the AAPL book. Built with C++17, WebAssembly and Linux."),
    "k8n": dict(
        title="k8n",
        blurb="A visual IDE for Kubernetes. Draw your app as a graph; k8n writes the YAML, shows the diff and deploys only after you approve it.",
        facts=[("One binary", "for Windows, macOS and Linux"), ("AI assistant", "proposes fixes, you approve them")],
        stack=["Go", "Next.js", "Kubernetes"], visual=vis_graph,
        alt="k8n: a visual IDE for Kubernetes. Draw your app as a graph; k8n writes the YAML, shows the diff and "
            "deploys only after you approve it. One binary for Windows, macOS and Linux. An AI assistant proposes "
            "fixes that you approve. The drawing shows Ingress, Service and Deployment nodes, with a new ConfigMap "
            "waiting for approval. Built with Go, Next.js and Kubernetes."),
    "undercover": dict(
        title="Undercover",
        blurb="A real-time multiplayer party game. Friends join from their phones, and the server runs every round so nobody can cheat.",
        facts=[("Live rooms", "synced over Socket.IO"), ("Deployed", "playable from any phone browser")],
        stack=["TypeScript", "Socket.IO", "Redis"], visual=vis_room,
        alt="Undercover: a real-time multiplayer party game. Friends join from their phones, and the server runs "
            "every round so nobody can cheat. Live rooms synced over Socket.IO; deployed and "
            "playable from any phone browser. The drawing shows six phones around the server, one sending a vote. "
            "Built with TypeScript, Socket.IO and Redis."),
}

LINKS = {
    "pitchfork": [("Source", "https://github.com/pulk17/NASDAQ-ITCH-OrderBook"), ("Live demo", "https://pitchfork.pages.dev/")],
    "k8n": [("Source", "https://github.com/pulk17/k8n"), ("Try the editor", "https://k8n.pages.dev/")],
    "undercover": [("Source", "https://github.com/pulk17/undercover-game"), ("Play it", "https://undercover-game-client.vercel.app/")],
}


# ------------------------------------------------------------------ README
def picture(name, alt, href=None):
    pic = (f'<picture>\n  <source media="(prefers-color-scheme: dark)" srcset="./assets/{name}-dark.svg">\n'
           f'  <img alt="{html.escape(alt)}" src="./assets/{name}-light.svg" width="100%">\n</picture>')
    return f'<a href="{href}">\n{pic}\n</a>' if href else pic


def readme(contrib_block):
    parts = [picture("hero", hero_alt(branch_status())), "", "## Open source", "", contrib_block, "", "## Projects", ""]
    for key, c in CARDS.items():
        parts += [picture(key, c["alt"], LINKS[key][0][1]), "",
                  "&emsp;".join(f"[{t}]({u})" for t, u in LINKS[key]), "", ""]
    parts += [
        "**Also:** [Band-Former](https://github.com/pulk17/Band-Former) turns a song into guitar tab you can actually "
        "play. PyTorch models pick out the notes, then a C++ search chooses fingerings a real hand can reach.",
        "",
        "## Contact",
        "",
        "&emsp;".join([
            "[Email](mailto:chauhanpulkit1708@gmail.com)",
            "[LinkedIn](https://www.linkedin.com/in/pulk1t/)",
            "[Codeforces](https://codeforces.com/profile/pulk1t)",
            "[LeetCode](https://leetcode.com/u/pulk1tt/)",
            "[Website](https://pulk1t.vercel.app/)",
        ]),
        "",
    ]
    return "\n".join(parts)


def current_contrib_block():
    path = os.path.join(OUT, "README.md")
    start, end = "<!-- contrib:start -->", "<!-- contrib:end -->"
    if os.path.exists(path):
        t = open(path).read()
        if start in t and end in t:
            return t[t.index(start): t.index(end) + len(end)]
    return f"{start}\n_Run `python scripts/contrib.py` to fill this in._\n{end}"


def main():
    os.makedirs(ASSETS, exist_ok=True)
    for theme in THEMES:
        with open(os.path.join(ASSETS, f"hero-{theme}.svg"), "w") as f:
            f.write(hero(theme))
        for key, c in CARDS.items():
            with open(os.path.join(ASSETS, f"{key}-{theme}.svg"), "w") as f:
                f.write(card(theme, c["title"], c["blurb"], c["facts"], c["stack"], c["visual"], c["alt"]))
    block = current_contrib_block()
    with open(os.path.join(OUT, "README.md"), "w") as f:
        f.write(readme(block))
    print("built", sorted(os.listdir(ASSETS)))


if __name__ == "__main__":
    main()
