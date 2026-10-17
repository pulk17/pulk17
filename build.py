#!/usr/bin/env python3
"""Builds the pulk17 GitHub profile: README.md + assets/*.svg (light and dark).

Design: each image is a sheet from an engineering drawing set. The hero is the
general-arrangement sheet (what goes in, what system handles it, what comes out),
the project strips are its detail drawings A-E, and the skills table is the parts
list, where every part points back to the detail that proves it.

Every number here was checked against the source repos on 17 Oct 2026.

To rebuild after changing a number or a line of copy:
    npm i @fontsource/ibm-plex-sans-condensed@5.3.0 @fontsource/ibm-plex-mono@5.3.0
    pip install fonttools brotli
    FONTDIR=node_modules/@fontsource python3 build.py
Type: IBM Plex Sans Condensed + IBM Plex Mono, converted to outlines so every viewer sees the same thing.
"""
import html
import os

from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

OUT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(OUT, "assets")
FONTDIR = os.environ.get(
    "FONTDIR",
    "/tmp/claude-0/-home-claude/b2bc8e0e-318c-5df2-8a32-06c2caf2cdcb/scratchpad/fonts/node_modules/@fontsource",
)

FACES = {
    "c4": ("PlexCond", 400, f"{FONTDIR}/ibm-plex-sans-condensed/files/ibm-plex-sans-condensed-latin-400-normal.woff2"),
    "c5": ("PlexCond", 500, f"{FONTDIR}/ibm-plex-sans-condensed/files/ibm-plex-sans-condensed-latin-500-normal.woff2"),
    "c6": ("PlexCond", 600, f"{FONTDIR}/ibm-plex-sans-condensed/files/ibm-plex-sans-condensed-latin-600-normal.woff2"),
    "m4": ("PlexMono", 400, f"{FONTDIR}/ibm-plex-mono/files/ibm-plex-mono-latin-400-normal.woff2"),
}
STACK = {
    "PlexCond": "'PlexCond','IBM Plex Sans Condensed','Roboto Condensed','Arial Narrow','Helvetica Neue',Arial,sans-serif",
    "PlexMono": "'PlexMono','IBM Plex Mono',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace",
}
_FONTS = {k: TTFont(p) for k, (_, _, p) in FACES.items()}

# Black sheet (dark) and drawing sheet (light). Accent = reviewer's markup amber:
# used only for cross-reference letters, the moving data pulses and measured figures.
THEMES = {
    "dark": dict(bg="#000000", grid="#1C1C1C", line="#EDEDED", sub="#A3A3A3",
                 acc="#F2C14E", soft="#121212", fill="#EDEDED"),
    "light": dict(bg="#F7F9FC", grid="#E3EAF2", line="#12304F", sub="#526B85",
                  acc="#8F5A00", soft="#EDF2F8", fill="#12304F"),
}


def text_width(s, face, size, ls=0.0):
    f = _FONTS[face]
    cmap = f.getBestCmap()
    hmtx = f["hmtx"]
    upm = f["head"].unitsPerEm
    total = 0
    for ch in s:
        g = cmap.get(ord(ch))
        if g is None:
            raise ValueError(f"glyph {ch!r} missing from {face}")
        total += hmtx[g][0]
    return total * size / upm + ls * max(len(s) - 1, 0)


def wrap(s, face, size, maxw):
    words, lines, cur = s.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if text_width(trial, face, size) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


class Svg:
    def __init__(self, w, h, title, desc, theme):
        self.w, self.h, self.title, self.desc = w, h, title, desc
        self.P = THEMES[theme]
        self.els, self.used, self.css = [], {k: set() for k in FACES}, []
        self.glyphs, self.defs = {}, []

    def add(self, s):
        self.els.append(s)

    def text(self, x, y, s, face, size, fill, anchor="start", ls=0.0, extra=""):
        f = _FONTS[face]
        cmap, hmtx, upm = f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm
        w = text_width(s, face, size, ls)
        x0 = x if anchor == "start" else (x - w / 2 if anchor == "middle" else x - w)
        k = size / upm
        uses, pen_x = [], 0.0
        for ch in s:
            g = cmap[ord(ch)]
            if ch != " ":
                gid = self.glyph(face, g)
                uses.append(f'<use href="#{gid}" x="{pen_x / k:.0f}"/>')
            pen_x += hmtx[g][0] * k + ls
        self.add(f'<g fill="{fill}" transform="translate({x0:.2f} {y:.2f}) scale({k:.5f} {-k:.5f})"{extra}>' + "".join(uses) + "</g>")

    def glyph(self, face, g):
        key = (face, g)
        if key not in self.glyphs:
            gs = _FONTS[face].getGlyphSet()
            pen = SVGPathPen(gs)
            gs[g].draw(pen)
            gid = f"{face}{len(self.glyphs):x}"
            self.glyphs[key] = gid
            self.defs.append(f'<path id="{gid}" d="{pen.getCommands()}"/>')
        return self.glyphs[key]

    def render(self):
        t, d = html.escape(self.title), html.escape(self.desc)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}" '
                f'role="img" aria-labelledby="t d"><title id="t">{t}</title><desc id="d">{d}</desc>'
                f'<style>{"".join(self.css)}</style><defs>{"".join(self.defs)}</defs>' + "".join(self.els) + "</svg>")


def arrow(svg, x1, y, x2, color, w=1.2):
    svg.add(f'<line x1="{x1}" y1="{y}" x2="{x2 - 6}" y2="{y}" stroke="{color}" stroke-width="{w}"/>')
    svg.add(f'<path d="M{x2 - 7},{y - 4} L{x2},{y} L{x2 - 7},{y + 4} Z" fill="{color}"/>')


def ref_bubble(svg, cx, cy, r, letter, size):
    P = svg.P
    svg.add(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{P["bg"]}" stroke="{P["acc"]}" stroke-width="1.5"/>')
    svg.text(cx, cy + size * 0.36, letter, "c6", size, P["acc"], anchor="middle")


# --------------------------------------------------------------------------- hero
HERO_ROWS = [
    # letter, raw input sample, system, output, headline figure
    ("A", "A  AAPL  B  100  145.64", "PitchFork", "every stock's live orders", "460M updates in under a minute"),
    ("B", "POST /runs/{id}/restart", "sample-platform", "CCExtractor's test platform", "34 changes merged, 330+ tests"),
    ("C", "kind: Deployment", "k8n", "cloud apps you can draw", "AI helpers you approve"),
    ("D", "vote { target: 4 }", "Undercover", "a live party game", "real-time and cheat-proof"),
    ("E", None, "Band-Former", "guitar tabs from any song", "AI plus a fast C++ engine"),
]
TITLE_BLOCK = [
    ("School", ["UPES Dehradun, B.Tech CS", "Graduating May 2027"]),
    ("Open source", ["Google Summer of Code 2026", "CCExtractor, 34 commits merged"]),
    ("Codeforces", ["Peak 1986, Candidate Master"]),
    ("LeetCode", ["Knight"]),
    ("Certification", ["AWS Solutions Architect", "Associate"]),
    ("Available", ["Full-time from January 2027"]),
]


def hero(theme):
    W, H = 960, 520
    alt = ("Pulkit Chauhan. Final-year CS student who builds fast, well-tested software in C++, Go, Python and TypeScript. "
           "Five projects: PitchFork rebuilds every stock's live orders from a day of NASDAQ data, about 460 million updates in under a minute; "
           "sample-platform is CCExtractor's test platform, 34 changes merged and 330+ tests; k8n lets you draw cloud apps, with AI helpers you approve; "
           "Undercover is a live, cheat-proof party game; Band-Former turns any song into guitar tabs. "
           "UPES Dehradun, graduating May 2027. Google Summer of Code 2026 with CCExtractor. "
           "Codeforces peak 1986, Candidate Master. LeetCode Knight. AWS Solutions Architect Associate. "
           "Available full-time from January 2027.")
    s = Svg(W, H, "Pulkit Chauhan", alt, theme)
    P = s.P
    s.css.append(
        ".pulse{opacity:0;animation:run 2.8s linear infinite}"
        "@keyframes run{0%{transform:translateX(0);opacity:0}12%{opacity:1}80%{opacity:1}100%{transform:translateX(34px);opacity:0}}"
        "@media (prefers-reduced-motion:reduce){.pulse{animation:none;opacity:0}}"
    )
    # sheet: outer trim line, inner frame, faint grid inside the frame
    s.add(f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" fill="{P["bg"]}" stroke="{P["sub"]}" stroke-opacity="0.5"/>')
    s.add(f'<clipPath id="f"><rect x="16" y="16" width="{W - 32}" height="{H - 32}"/></clipPath>')
    grid = "".join(f'M{x},16V{H - 16}' for x in range(40, W - 16, 24)) + "".join(f'M16,{y}H{W - 16}' for y in range(40, H - 16, 24))
    s.add(f'<path d="{grid}" stroke="{P["grid"]}" stroke-width="1" clip-path="url(#f)" fill="none"/>')
    s.add(f'<rect x="16" y="16" width="{W - 32}" height="{H - 32}" fill="none" stroke="{P["line"]}" stroke-width="1.6"/>')

    # identity
    s.text(48, 100, "Pulkit Chauhan", "c6", 56, P["line"], ls=-0.6)
    for i, ln in enumerate(wrap("Final-year CS student. I build fast, well-tested software in C++, Go, Python and TypeScript.", "c4", 19, 540)):
        s.text(49, 138 + i * 25, ln, "c4", 19, P["sub"])

    # general arrangement: input -> system -> output
    s.text(48, 222, "Raw input", "c5", 13, P["sub"])
    s.text(296, 222, "System", "c5", 13, P["sub"])
    s.text(458, 222, "What comes out", "c5", 13, P["sub"])
    s.add(f'<line x1="48" y1="231" x2="640" y2="231" stroke="{P["sub"]}" stroke-opacity="0.45"/>')
    for i, (letter, raw, system, out, fig) in enumerate(HERO_ROWS):
        yc = 262 + i * 50
        if raw:
            assert text_width(raw, "m4", 13) <= 186, raw
            s.text(48, yc + 4.5, raw, "m4", 13, P["sub"])
        else:  # audio waveform
            pts, x = [], 48
            amps = [2, 5, 9, 4, 11, 7, 3, 10, 6, 12, 5, 8, 3, 9, 4, 7, 2, 6, 3]
            for k, a in enumerate(amps):
                pts.append(f"{x},{yc - a}" if k % 2 == 0 else f"{x},{yc + a}")
                x += 9.6
            s.add(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{P["sub"]}" stroke-width="1.4" stroke-linejoin="round"/>')
        arrow(s, 240, yc, 282, P["line"])
        s.add(f'<circle class="pulse" cx="242" cy="{yc}" r="3" fill="{P["acc"]}" style="animation-delay:{i * 0.55:.2f}s"/>')
        s.add(f'<rect x="288" y="{yc - 17}" width="140" height="34" fill="{P["bg"]}" stroke="{P["line"]}" stroke-width="1.4"/>')
        assert text_width(system, "c6", 15) <= 124, system
        s.text(358, yc + 5, system, "c6", 15, P["line"], anchor="middle")
        ref_bubble(s, 288, yc - 17, 9, letter, 11)
        arrow(s, 428, yc, 452, P["line"])
        assert text_width(out, "c5", 14.5) <= 184, out
        assert text_width(fig, "c4", 12.5) <= 184, fig
        s.text(458, yc - 1, out, "c5", 14.5, P["line"])
        s.text(458, yc + 16, fig, "c4", 12.5, P["acc"])

    # title block
    x0, y0, bw = 668, 44, 260
    bottom = H - 44
    base = [28 + 19 * len(vals) + 6 for _, vals in TITLE_BLOCK]
    spare = (bottom - 40 - y0) - sum(base)
    assert spare >= 0, ("title block overflow", spare)
    y = y0
    rows = []
    for (label, vals), h in zip(TITLE_BLOCK, base):
        h += spare / len(TITLE_BLOCK)
        rows.append((y, h, label, vals))
        y += h
    s.add(f'<rect x="{x0}" y="{y0}" width="{bw}" height="{bottom - y0}" fill="{P["bg"]}" stroke="{P["line"]}" stroke-width="1.4"/>')
    for ry, rh, label, vals in rows:
        pad = (rh - (28 + 19 * len(vals) + 6)) / 2
        s.text(x0 + 14, ry + 20 + pad, label, "c4", 12, P["sub"])
        for k, v in enumerate(vals):
            assert text_width(v, "c5", 15) <= bw - 28, v
            s.text(x0 + 14, ry + 40 + pad + 19 * k, v, "c5", 15, P["line"])
        s.add(f'<line x1="{x0}" y1="{ry + rh}" x2="{x0 + bw}" y2="{ry + rh}" stroke="{P["line"]}" stroke-opacity="0.55"/>')
    s.text(x0 + 14, bottom - 14, "github.com/pulk17", "c5", 13, P["sub"])
    s.text(x0 + bw - 14, bottom - 14, "Oct 2026", "c4", 13, P["sub"], anchor="end")
    return s.render()


# ------------------------------------------------------------------ detail strips
def strip(theme, letter, title, subtitle, facts, chips, schematic, alt):
    W = 960
    s = Svg(W, 10, title, alt, theme)
    P = s.P
    body = []  # drawn after we know the height
    fx, fmax = 404, 524
    y = 128
    lines_out = []
    for fact in facts:
        lines = wrap(fact, "c4", 15.5, fmax)
        lines_out.append((y, lines))
        y += 21 * len(lines) + 10
    chip_y = y + 2
    H = max(chip_y + 24 + 26, 276)
    s.h = H
    s.add(f'<rect x="0.75" y="0.75" width="{W - 1.5}" height="{H - 1.5}" fill="{P["bg"]}" stroke="{P["line"]}" stroke-width="1.5"/>')
    ref_bubble(s, 42, 46, 17, letter, 17)
    s.text(72, 55, title, "c6", 27, P["line"], ls=-0.2)
    tw = text_width(title, "c6", 27, -0.2)
    s.text(72 + tw + 14, 55, subtitle, "c4", 16.5, P["sub"])
    assert 72 + tw + 14 + text_width(subtitle, "c4", 16.5) <= W - 24, subtitle
    s.add(f'<line x1="24" y1="82" x2="{W - 24}" y2="82" stroke="{P["sub"]}" stroke-opacity="0.45"/>')
    s.add(f'<line x1="368" y1="100" x2="368" y2="{H - 24}" stroke="{P["sub"]}" stroke-opacity="0.45"/>')
    for fy, lines in lines_out:
        s.add(f'<line x1="{fx - 18}" y1="{fy - 5}" x2="{fx - 8}" y2="{fy - 5}" stroke="{P["acc"]}" stroke-width="2"/>')
        for k, ln in enumerate(lines):
            s.text(fx, fy + 21 * k, ln, "c4", 15.5, P["line"])
    cx = fx
    for c in chips:
        cw = text_width(c, "c5", 13) + 20
        s.add(f'<rect x="{cx}" y="{chip_y}" width="{cw:.1f}" height="24" rx="3" fill="none" stroke="{P["sub"]}" stroke-opacity="0.8"/>')
        s.text(cx + cw / 2, chip_y + 16.5, c, "c5", 13, P["sub"], anchor="middle")
        cx += cw + 8
    assert cx <= W - 16, ("chips overflow", title)
    schematic(s, P, H)
    return s.render()


def sch_orderbook(s, P, H):
    mid = 182
    asks = [70, 104, 132, 168]
    bids = [84, 118, 146, 176]
    for k, w in enumerate(asks):
        y = mid - 18 - k * 16
        s.add(f'<rect x="{300 - w}" y="{y}" width="{w}" height="11" fill="none" stroke="{P["line"]}" stroke-width="1.2"/>')
        s.text(40, y + 9.5, f"145.{65 + k:02d}", "m4", 11, P["sub"])
    for k, w in enumerate(bids):
        y = mid + 7 + k * 16
        s.add(f'<rect x="{300 - w}" y="{y}" width="{w}" height="11" fill="{P["fill"]}" fill-opacity="0.82"/>')
        s.text(40, y + 9.5, f"145.{64 - k:02d}", "m4", 11, P["sub"])
    s.add(f'<line x1="98" y1="{mid}" x2="300" y2="{mid}" stroke="{P["sub"]}" stroke-dasharray="3 4"/>')
    s.add(f'<rect x="{300 - asks[0] - 5}" y="{mid - 18}" width="3" height="11" fill="{P["acc"]}"/>')
    s.add(f'<rect x="{300 - bids[0] - 5}" y="{mid + 7}" width="3" height="11" fill="{P["acc"]}"/>')
    s.text(92, mid - 6, "asks", "c4", 12, P["sub"])
    s.text(92, mid + 16, "bids", "c4", 12, P["sub"])


def sch_api(s, P, H):
    codes = ["200", "400", "401", "403", "404", "409"]
    routes = ["/runs", "/samples", "/auth", "/users", "/system"]
    for j, c in enumerate(codes):
        s.text(132 + j * 34, 124, c, "m4", 11, P["sub"], anchor="middle")
    for i, r in enumerate(routes):
        y = 146 + i * 24
        s.text(40, y + 4, r, "m4", 11.5, P["sub"])
        for j in range(len(codes)):
            s.add(f'<rect x="{125 + j * 34}" y="{y - 7}" width="14" height="14" fill="{P["fill"]}" fill-opacity="0.82"/>')
    s.text(40, 146 + 5 * 24 + 4, "each feature tested, error cases included", "c4", 12, P["sub"])


def sch_graph(s, P, H):
    def node(x, y, label, w=92):
        s.add(f'<rect x="{x}" y="{y}" width="{w}" height="26" rx="4" fill="{P["soft"]}" stroke="{P["line"]}" stroke-width="1.2"/>')
        s.text(x + w / 2, y + 17.5, label, "c5", 12, P["line"], anchor="middle")
    node(36, 116, "Ingress")
    node(150, 116, "Service")
    node(150, 190, "Deployment")
    node(36, 190, "ConfigMap")
    arrow(s, 128, 129, 150, P["line"])
    s.add(f'<line x1="196" y1="142" x2="196" y2="184" stroke="{P["line"]}" stroke-width="1.2"/>')
    s.add(f'<path d="M192,183 L196,190 L200,183 Z" fill="{P["line"]}"/>')
    arrow(s, 128, 203, 150, P["line"])
    # compiled manifest
    s.add(f'<path d="M262,112 h52 l14,14 v112 h-66 Z" fill="{P["bg"]}" stroke="{P["line"]}" stroke-width="1.2"/>')
    s.add(f'<path d="M314,112 v14 h14" fill="none" stroke="{P["line"]}" stroke-width="1.2"/>')
    for k, t in enumerate(["kind:", "spec:", "  image:", "  ports:", "dry-run"]):
        s.text(268, 146 + k * 18, t, "m4", 10.5, P["acc"] if t == "dry-run" else P["sub"])
    arrow(s, 242, 203, 262, P["line"])


def sch_game(s, P, H):
    for k in range(3):
        y = 108 + k * 50
        s.add(f'<rect x="40" y="{y}" width="26" height="42" rx="5" fill="none" stroke="{P["line"]}" stroke-width="1.2"/>')
        s.add(f'<line x1="49" y1="{y + 37}" x2="57" y2="{y + 37}" stroke="{P["line"]}" stroke-width="1.2"/>')
        s.add(f'<line x1="70" y1="{y + 21}" x2="124" y2="178" stroke="{P["sub"]}" stroke-width="1.1"/>')
    s.add(f'<rect x="124" y="152" width="92" height="52" fill="{P["soft"]}" stroke="{P["line"]}" stroke-width="1.3"/>')
    s.text(170, 175, "server", "c5", 13, P["line"], anchor="middle")
    s.text(170, 193, "owns state", "c4", 11.5, P["sub"], anchor="middle")
    arrow(s, 216, 178, 236, P["line"])
    for k, ph in enumerate(["lobby", "role reveal", "clue", "vote", "elimination"]):
        y = 124 + k * 26
        active = ph == "vote"
        if active:
            s.add(f'<circle cx="248" cy="{y - 4}" r="4" fill="{P["acc"]}"/>')
        else:
            s.add(f'<circle cx="248" cy="{y - 4}" r="3" fill="none" stroke="{P["sub"]}"/>')
        s.text(260, y, ph, "c5" if active else "c4", 12.5, P["line"] if active else P["sub"])


def sch_tab(s, P, H):
    pts, x = [], 36
    amps = [3, 8, 14, 6, 18, 10, 4, 15, 9, 20, 6, 12, 4, 13, 5]
    for k, a in enumerate(amps):
        pts.append(f"{x},{176 - a}" if k % 2 == 0 else f"{x},{176 + a}")
        x += 7.5
    s.add(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{P["sub"]}" stroke-width="1.5" stroke-linejoin="round"/>')
    arrow(s, 150, 176, 176, P["line"])
    strings = ["e", "B", "G", "D", "A", "E"]
    ys = [134 + k * 17 for k in range(6)]
    for name, y in zip(strings, ys):
        s.text(192, y + 4, name, "m4", 11, P["sub"], anchor="end")
        s.add(f'<line x1="200" y1="{y}" x2="334" y2="{y}" stroke="{P["line"]}" stroke-opacity="0.8"/>')
    chords = [(228, ["3", "0", "0", "0", "2", "3"]), (270, ["0", "1", "0", "2", "3", None]), (312, ["2", "3", "2", "0", None, None])]
    for cx, frets in chords:
        for f, y in zip(frets, ys):
            if f is None:
                continue
            s.add(f'<rect x="{cx - 5}" y="{y - 7}" width="10" height="14" fill="{P["bg"]}"/>')
            s.text(cx, y + 4, f, "m4", 11.5, P["acc"], anchor="middle")


PROJECTS = [
    dict(letter="A", title="PitchFork", subtitle="A stock exchange replay engine",
         facts=["Takes a full day of real NASDAQ data and rebuilds the live buy and sell orders for every stock: about 460 million updates in under a minute, on a laptop.",
                "Also runs in the browser, so anyone can watch a real trading day play back live with nothing to install.",
                "I used it to test a well-known trading signal on 6,300+ stocks and measured exactly how much of it survives real trading costs."],
         chips=["C++17", "WebAssembly", "Linux", "JavaScript"], sch=sch_orderbook,
         repo="https://github.com/pulk17/NASDAQ-ITCH-OrderBook", live="https://pitchfork.pages.dev/", live_label="Live demo"),
    dict(letter="B", title="sample-platform", subtitle="Google Summer of Code 2026, CCExtractor",
         facts=["Selected for Google's open-source program to build the public API and web dashboard for the system that tests CCExtractor, an open-source subtitle tool.",
                "34 of my changes were reviewed and merged into the main project by its maintainers.",
                "Wrote 330+ automated tests so cases like expired logins and duplicate uploads are handled correctly."],
         chips=["Python", "Flask", "MySQL", "React", "TypeScript"], sch=sch_api,
         repo="https://github.com/CCExtractor/sample-platform", live="https://github.com/CCExtractor/sample-platform/commits/master?author=pulk17", live_label="My merged work"),
    dict(letter="C", title="k8n", subtitle="Build and deploy cloud apps by drawing them",
         facts=["Design an app on a visual canvas and deploy it to Kubernetes without writing configuration files by hand.",
                "Built-in AI assistants spot common problems and suggest fixes, but nothing changes until you approve it.",
                "Works with Claude Code, so an AI agent goes through the same safety checks as a person would."],
         chips=["Go", "Next.js", "Kubernetes", "PostgreSQL"], sch=sch_graph,
         repo="https://github.com/pulk17/k8n", live="https://k8n.pages.dev/", live_label="Live site"),
    dict(letter="D", title="Undercover", subtitle="A real-time multiplayer party game",
         facts=["Friends join from their phones and play together live, with no app to install.",
                "The server runs the game, so no player can cheat by tampering with their own phone.",
                "Includes error monitoring and protection against spam requests."],
         chips=["TypeScript", "React", "Socket.IO", "Redis"], sch=sch_game,
         repo="https://github.com/pulk17/undercover-game", live="https://undercover-game-client.vercel.app/", live_label="Play it"),
    dict(letter="E", title="Band-Former", subtitle="Turns a song into guitar tabs",
         facts=["Paste a YouTube link and get a playable guitar tab back.",
                "AI models separate the guitar from the rest of the song and pick out the notes.",
                "A fast C++ engine then works out a comfortable way to play them on a real guitar."],
         chips=["Python", "PyTorch", "C++17"], sch=sch_tab,
         repo="https://github.com/pulk17/Band-Former", live=None, live_label=None),
]


# -------------------------------------------------------------------- parts list
PARTS = [
    [("Languages", [("C++17/20", "AE"), ("Go", "C"), ("Python", "BE"), ("TypeScript and JavaScript", "ABCD"), ("SQL", "BC"), ("Bash", "AB")]),
     ("Systems and performance", [("Linux", "A"), ("Benchmarking and profiling", "A"), ("WebAssembly", "A")]),
     ("AI and ML", [("PyTorch", "E"), ("AI agents and Claude Code", "C")])],
    [("Backend and web", [("REST APIs and OpenAPI", "B"), ("Flask and FastAPI", "BE"), ("Gin", "C"), ("Express and Socket.IO", "D"), ("React", "BD"), ("Next.js", "C")]),
     ("Data", [("MySQL", "B"), ("PostgreSQL", "C"), ("Redis", "D")]),
     ("Infrastructure", [("Docker", "BCE"), ("Kubernetes and Helm", "C")])],
]


def parts(theme):
    W = 960
    names = {p["letter"]: p["title"] for p in PROJECTS}
    alt = "Skills, each with the projects that use it. " + "; ".join(
        f"{grp}: " + ", ".join(f"{n} ({', '.join(names[c] for c in refs)})" for n, refs in items)
        for col in PARTS for grp, items in col)
    s = Svg(W, 10, "Skills and where they are used", alt, theme)
    P = s.P
    rows_h = [sum(34 + 27 * len(items) for _, items in col) for col in PARTS]
    H = 70 + max(rows_h) + 22
    s.h = H
    s.add(f'<rect x="0.75" y="0.75" width="{W - 1.5}" height="{H - 1.5}" fill="{P["bg"]}" stroke="{P["line"]}" stroke-width="1.5"/>')
    s.text(28, 47, "Each skill points to the projects that use it:", "c4", 15, P["sub"])
    lx = 28 + text_width("Each skill points to the projects that use it:", "c4", 15) + 22
    for k, v in names.items():
        ref_bubble(s, lx + 9.5, 42, 9.5, k, 11.5)
        s.text(lx + 25, 47, v, "c5", 15, P["line"])
        lx += 25 + text_width(v, "c5", 15) + 20
    assert lx <= W - 20, ("legend overflow", lx)
    s.add(f'<line x1="24" y1="70" x2="{W - 24}" y2="70" stroke="{P["sub"]}" stroke-opacity="0.45"/>')
    for ci, col in enumerate(PARTS):
        x0 = 28 + ci * 470
        y = 70
        for grp, items in col:
            y += 34
            s.text(x0, y - 4, grp, "c6", 15, P["line"])
            for name, refs in items:
                y += 27
                s.text(x0 + 12, y - 8, name, "c4", 15, P["line"])
                bx = x0 + 420
                for c in reversed(refs):
                    ref_bubble(s, bx, y - 13, 9.5, c, 11.5)
                    bx -= 24
                s.add(f'<line x1="{x0 + 12}" y1="{y}" x2="{x0 + 432}" y2="{y}" stroke="{P["grid"]}"/>')
    if True:
        s.add(f'<line x1="480" y1="88" x2="480" y2="{H - 22}" stroke="{P["sub"]}" stroke-opacity="0.35"/>')
    return s.render()


# ------------------------------------------------------------------------ README
def picture(name, alt, width="100%"):
    return (f'<picture>\n  <source media="(prefers-color-scheme: dark)" srcset="./assets/{name}-dark.svg">\n'
            f'  <img alt="{html.escape(alt)}" src="./assets/{name}-light.svg" width="{width}">\n</picture>')


def readme():
    out = []
    out.append(picture("hero", "Pulkit Chauhan: final-year CS student who builds fast, tested systems in C++, Go, Python and TypeScript. Diagram of five systems and a title block of credentials."))
    out.append("")
    out.append("I'm Pulkit, a final-year Computer Science student at UPES Dehradun, graduating in May 2027. "
               "I build software that is fast, carefully tested, and backed by real numbers. "
               "I'm looking for software engineering roles starting January 2027.")
    out.append("")
    out.append("## Things I've built")
    out.append("")
    for p in PROJECTS:
        alt = f"{p['letter']}. {p['title']}: {p['subtitle']} " + " ".join(p["facts"]) + " Built with " + ", ".join(p["chips"]) + "."
        out.append(f'<a href="{p["repo"]}">\n' + picture(f"detail-{p['letter'].lower()}", alt) + "\n</a>")
        out.append("")
        links = [f"[Code]({p['repo']})"]
        if p["live"]:
            links.append(f"[{p['live_label']}]({p['live']})")
        out.append("&nbsp;&nbsp;|&nbsp;&nbsp;".join(links))
        out.append("")
    out.append("## Skills")
    out.append("")
    out.append(picture("skills", "Skills table: each skill lists the projects above that use it."))
    out.append("")
    out.append("## What I bring")
    out.append("")
    out.append("- **Speed I can prove.** My exchange replay engine handles about 460 million updates in under a minute.")
    out.append("- **Code others trust.** 34 changes reviewed and merged by CCExtractor's maintainers, backed by 330+ automated tests.")
    out.append("- **Strong problem solving.** Candidate Master on Codeforces, with a peak rating of 1986.")
    out.append("- **Careful use of AI.** In k8n, AI suggests changes and a person approves them before anything happens.")
    out.append("")
    out.append("## Get in touch")
    out.append("")
    out.append("[Email](mailto:chauhanpulkit1708@gmail.com)&nbsp;&nbsp;|&nbsp;&nbsp;"
               "[LinkedIn](https://www.linkedin.com/in/pulk1t/)&nbsp;&nbsp;|&nbsp;&nbsp;"
               "[Codeforces](https://codeforces.com/profile/pulk1t)&nbsp;&nbsp;|&nbsp;&nbsp;"
               "[LeetCode](https://leetcode.com/u/pulk1tt/)&nbsp;&nbsp;|&nbsp;&nbsp;"
               "[Website](https://pulk1t.vercel.app/)")
    out.append("")
    return "\n".join(out)


def main():
    os.makedirs(ASSETS, exist_ok=True)
    for theme in THEMES:
        files = {"hero": hero(theme), "skills": parts(theme)}
        for p in PROJECTS:
            alt = f"{p['title']}: {p['subtitle']}"
            files[f"detail-{p['letter'].lower()}"] = strip(theme, p["letter"], p["title"], p["subtitle"], p["facts"], p["chips"], p["sch"], alt)
        for name, svg in files.items():
            with open(os.path.join(ASSETS, f"{name}-{theme}.svg"), "w") as fh:
                fh.write(svg)
    with open(os.path.join(OUT, "README.md"), "w") as fh:
        fh.write(readme())
    for f in sorted(os.listdir(ASSETS)):
        print(f"{f:24} {os.path.getsize(os.path.join(ASSETS, f)) / 1024:6.1f} KB")


if __name__ == "__main__":
    main()
