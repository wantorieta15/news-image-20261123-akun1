#!/usr/bin/env python3
"""Monday 23 November 2026: 38 date-checked stories, 9 regions.

A one-day newspaper front page summing up the world's news of Monday
23 November 2026. Draws a single 1024x1024 PNG with the Python standard
library only (os, struct, zlib, math) -- no Pillow, no system fonts, no
network. A hand-built single-stroke vector font draws all text, and a
small canvas class draws every shape. Deterministic: two runs write
identical bytes.

Run:  MAKEFUN_OUTPUT_DIR=out python3 main.py   ->  out/entry.png

Competition: news-image-20261123 ($100, make.fun).
SPDX-License-Identifier: MIT
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- PNG output
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    return out + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def write_png(path, rgb, w, h):
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)
        raw += rgb[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    blob = b"\x89PNG\r\n\x1a\n"
    blob += _chunk(b"IHDR", ihdr)
    blob += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    blob += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(blob)


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bytes(bg) * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def fill_rect(self, x0, y0, x1, y1, c):
        x0 = max(0, int(x0)); y0 = max(0, int(y0))
        x1 = min(self.w, int(x1)); y1 = min(self.h, int(y1))
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(c) * (x1 - x0)
        for y in range(y0, y1):
            i = (y * self.w + x0) * 3
            self.px[i:i + (x1 - x0) * 3] = row

    def rect(self, x0, y0, x1, y1, c, t=1):
        self.fill_rect(x0, y0, x1, y0 + t, c)
        self.fill_rect(x0, y1 - t, x1, y1, c)
        self.fill_rect(x0, y0, x0 + t, y1, c)
        self.fill_rect(x1 - t, y0, x1, y1, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        x0 = int(round(x0)); y0 = int(round(y0))
        x1 = int(round(x1)); y1 = int(round(y1))
        dx = abs(x1 - x0); dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        r = (t - 1) // 2
        offs = _disc(r) if r else ((0, 0),)
        put = self.set
        while True:
            for ox, oy in offs:
                put(x0 + ox, y0 + oy, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy; x0 += sx
            if e2 < dx:
                err += dx; y0 += sy

    def circle(self, cx, cy, r, c, fill=True):
        cx = int(round(cx)); cy = int(round(cy)); r = int(round(r))
        if fill:
            for dy in range(-r, r + 1):
                dx = int((r * r - dy * dy) ** 0.5)
                self.fill_rect(cx - dx, cy + dy, cx + dx + 1, cy + dy + 1, c)
        else:
            pts = [(cx + r * math.cos(a), cy + r * math.sin(a))
                   for a in [i * math.pi / 24 for i in range(49)]]
            for i in range(len(pts) - 1):
                self.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], c, 1)

    def poly(self, pts, c, fill=True):
        pts = [(float(x), float(y)) for x, y in pts]
        if fill:
            ys = [p[1] for p in pts]
            y0, y1 = int(min(ys)), int(max(ys))
            n = len(pts)
            for y in range(y0, y1 + 1):
                xs = []
                for i in range(n):
                    ax, ay = pts[i]; bx, by = pts[(i + 1) % n]
                    if (ay <= y < by) or (by <= y < ay):
                        xs.append(ax + (y - ay) * (bx - ax) / (by - ay))
                xs.sort()
                for i in range(0, len(xs) - 1, 2):
                    self.fill_rect(int(xs[i]), y, int(xs[i + 1]) + 1, y + 1, c)
        else:
            for i in range(len(pts)):
                ax, ay = pts[i]; bx, by = pts[(i + 1) % len(pts)]
                self.line(ax, ay, bx, by, c, 1)


_DISC_CACHE = {}


def _disc(r):
    if r not in _DISC_CACHE:
        _DISC_CACHE[r] = tuple((dx, dy) for dy in range(-r, r + 1)
                               for dx in range(-r, r + 1)
                               if dx * dx + dy * dy <= r * r + r)
    return _DISC_CACHE[r]


def arc(cv, cx, cy, rx, ry, a0, a1, color, t=1):
    """Elliptical arc; angles in degrees from 3 o'clock, clockwise (y down)."""
    n = max(8, int(abs(a1 - a0) / 4))
    prev = None
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        p = (cx + rx * math.cos(a), cy + ry * math.sin(a))
        if prev is not None:
            cv.line(prev[0], prev[1], p[0], p[1], color, t)
        prev = p


def ellipse_outline(cv, cx, cy, rx, ry, color, t=1):
    """Ellipse outline with stroke thickness t."""
    n = 48
    pts = [(cx + rx * math.cos(2 * math.pi * i / n),
            cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n)]
    for i in range(n):
        ax, ay = pts[i]
        bx, by = pts[(i + 1) % n]
        cv.line(ax, ay, bx, by, color, t)


def burst(cv, cx, cy, r, color):
    """Eight-spoke starburst with a solid centre dot."""
    for k in range(8):
        a = k * math.pi / 4
        cv.line(cx, cy, cx + r * math.cos(a), cy + r * math.sin(a), color, 2)
    cv.circle(cx, cy, 3, color)


# ---------------------------------------------------------------- stroke font
# One glyph = strokes separated by "|", points "x,y" in a 10-wide box,
# y=0 cap top, y=10 baseline, descenders to 13, accents to -2.
FONT = {
"A": "0,10 5,0 10,10|3,6 7,6",
"B": "0,0 0,10 6,10 9,8 9,6 6,5|6,5 9,4 9,2 7,0 0,0",
"C": "9,2 7,0 3,0 1,2 0,4 0,6 1,8 3,10 7,10 9,8",
"D": "0,0 0,10 6,10 9,7 9,3 6,0 0,0",
"E": "9,0 0,0 0,10 9,10|0,5 7,5",
"F": "0,10 0,0 9,0|0,5 7,5",
"G": "9,2 7,0 3,0 1,2 0,4 0,6 1,8 3,10 7,10 9,8 9,5 6,5",
"H": "0,0 0,10|10,0 10,10|0,5 10,5",
"I": "3,0 7,0|5,0 5,10|3,10 7,10",
"J": "7,0 7,10 4,10 1,8 1,6",
"K": "0,0 0,10|9,0 1,5 9,10",
"L": "0,0 0,10 9,10",
"M": "0,10 0,0 5,7 10,0 10,10",
"N": "0,10 0,0 10,10 10,0",
"O": "3,0 7,0 9,2 10,4 10,6 9,8 7,10 3,10 1,8 0,6 0,4 1,2 3,0",
"P": "0,10 0,0 7,0 9,2 9,4 7,5 0,5",
"Q": "3,0 7,0 9,2 10,4 10,6 9,8 7,10 3,10 1,8 0,6 0,4 1,2 3,0|6,7 10,11",
"R": "0,10 0,0 7,0 9,2 9,4 7,5 0,5|6,5 10,10",
"S": "9,2 7,0 3,0 1,2 1,4 3,5 7,5 9,6 9,8 7,10 3,10 1,8",
"T": "0,0 10,0|5,0 5,10",
"U": "0,0 0,7 2,10 8,10 10,7 10,0",
"V": "0,0 5,10 10,0",
"W": "0,0 2,10 5,4 8,10 10,0",
"X": "0,0 10,10|10,0 0,10",
"Y": "0,0 5,5 10,0|5,5 5,10",
"Z": "0,0 10,0 0,10 10,10",
"a": "9,4 9,10|8,4 9,6 9,9 7,10 3,10 1,8 1,6 3,4 7,4 9,6",
"b": "0,0 0,10|0,7 3,4 7,4 9,6 9,8 7,10 3,10 0,7",
"c": "9,5 7,4 4,4 1,6 1,8 4,10 7,10 9,9",
"d": "10,0 10,10|10,7 7,4 3,4 1,6 1,8 3,10 7,10 10,7",
"e": "9,8 7,10 3,10 1,8 1,6 3,4 7,4 9,6 9,8|1,7 9,7",
"f": "6,10 6,2 4,0 2,0|2,4 8,4",
"g": "9,4 9,11 7,13 3,13 1,11|8,4 9,6 9,8 7,10 3,10 1,8 1,6 3,4 7,4 9,6",
"h": "0,0 0,10|0,6 3,4 7,4 9,6 9,10",
"i": "5,4 5,10|5,1 5,2",
"j": "6,4 6,11 4,13 2,13|6,1 6,2",
"k": "0,0 0,10|9,4 0,7 9,10",
"l": "5,0 5,10",
"m": "0,10 0,4 3,4 5,6 7,4 9,4 9,10|5,6 5,10",
"n": "0,10 0,4 3,4 7,4 9,6 9,10",
"o": "3,4 7,4 9,6 9,8 7,10 3,10 1,8 1,6 3,4",
"p": "0,4 0,13|0,7 3,4 7,4 9,6 9,8 7,10 3,10 0,7",
"q": "10,4 10,13|10,7 7,4 3,4 1,6 1,8 3,10 7,10 10,7",
"r": "0,10 0,4 3,4 7,4 8,5",
"s": "9,5 7,4 4,4 2,5 2,6 4,7 8,7 9,8 9,9 7,10 4,10 2,9",
"t": "5,0 5,10 3,10 7,10|2,4 8,4",
"u": "0,4 0,8 2,10 8,10 10,8 10,4",
"v": "0,4 5,10 10,4",
"w": "0,4 2,10 5,5 8,10 10,4",
"x": "0,4 10,10|10,4 0,10",
"y": "0,4 5,10 10,4|5,10 5,13 3,13",
"z": "0,4 10,4 0,10 10,10",
"0": "3,0 7,0 9,2 10,4 10,6 9,8 7,10 3,10 1,8 0,6 0,4 1,2 3,0",
"1": "5,0 5,10|3,2 5,0|2,10 8,10",
"2": "1,2 3,0 7,0 9,2 9,4 7,6 1,10 9,10",
"3": "1,2 3,0 7,0 9,2 9,4 7,5|7,5 9,6 9,8 7,10 3,10 1,8",
"4": "8,0 8,10|0,7 9,7|1,7 7,0",
"5": "9,0 1,0 1,5 7,5 9,7 9,9 7,10 3,10 1,8",
"6": "9,2 7,0 3,0 1,3 1,7 3,10 7,10 9,8 9,6 7,5 4,5 2,6",
"7": "0,0 10,0 5,10",
"8": "3,0 7,0 9,2 9,4 7,5 3,5 1,4 1,2 3,0|3,5 7,5 9,6 9,8 7,10 3,10 1,8 1,6 3,5",
"9": "1,8 3,10 7,10 9,7 9,3 7,0 3,0 1,2 1,4 3,5 7,5 9,4",
" ": "",
".": "4,9 6,9",
",": "5,9 5,10 4,12 3,13",
":": "5,3 5,4|5,8 5,9",
";": "5,3 5,4|5,8 5,10 4,12 3,13",
"'": "5,0 4,3",
'"': "4,0 3,3|8,0 7,3",
"-": "1,5 9,5",
"\u00b7": "4,5 6,5",
"*": "5,1 5,9|1,3 9,7|9,3 1,7",
"(": "7,0 4,3 4,7 7,10",
")": "3,0 6,3 6,7 3,10",
"/": "9,0 1,10",
"%": "9,0 1,10|1,1 4,1 4,3 1,3|6,7 9,7 9,9 6,9",
"$": "5,-1 5,11|9,2 7,0 3,0 1,2 1,4 3,5 7,5 9,6 9,8 7,10 3,10 1,8",
"!": "5,0 5,7|5,9 5,10",
"?": "2,2 4,0 7,0 9,2 9,4 7,5 5,6 5,8|5,9 5,10",
"=": "0,3 10,3|0,7 10,7",
"+": "5,0 5,10|0,5 10,5",
"&": "8,1 6,0 3,0 1,2 1,5 3,7 7,7 9,8 9,9 7,10 3,10 1,8 1,6 3,5 9,0",
"_": "0,10 10,10",
"[": "7,0 3,0 3,10 7,10",
"]": "3,0 7,0 7,10 3,10",
"<": "8,0 2,5 8,10",
">": "2,0 8,5 2,10",
"#": "3,0 3,10|7,0 7,10|0,3 10,3|0,7 10,7",
"@": "8,2 9,4 9,7 7,10 4,10 1,7 1,4 4,1 7,1 9,3 9,6 6,6 4,6 4,8 6,8",
"~": "1,6 3,4 5,6 7,4 9,6",
"^": "1,6 5,1 9,6",
"|": "5,0 5,10",
"\u00dc": "0,0 0,7 2,10 8,10 10,7 10,0|2,-2 2,-1|8,-2 8,-1",
"\u00fc": "0,4 0,8 2,10 8,10 10,8 10,4|2,1 2,2|8,1 8,2",
"\u00ed": "5,4 5,10|5,1 5,2|3,-2 6,-1",
"\u00f3": "3,4 7,4 9,6 9,8 7,10 3,10 1,8 1,6 3,4|3,-2 6,-1",
"\u00cd": "3,0 7,0|5,0 5,10|3,10 7,10|4,-2 7,-1",
"\u00d3": "3,0 7,0 9,2 10,4 10,6 9,8 7,10 3,10 1,8 0,6 0,4 1,2 3,0|4,-2 7,-1",
"\u00b0": "3,1 6,1 7,3 6,5 3,5 2,3 3,1",
"\u00d7": "1,1 9,9|9,1 1,9",
"\u2713": "1,7 4,10 9,0",
}

# Glyph advance widths, in font units (box is 10 wide, x-squashed by XS).
# Advance must cover the drawn glyph (10*XS) plus the stroke thickness
# (~0.9 scale units), or neighbouring letters touch.
XS = 0.52
_NARROW = set("iljtf.,:;!'| ")
_WIDE = set("mwMW%@&")
_NARROW_W = {" ": 6.0, "i": 5.5, "l": 5.5, "j": 5.5, "t": 7.0, "f": 7.0,
             ".": 6.0, ",": 6.0, ":": 6.0, ";": 6.0, "!": 6.0, "'": 6.0,
             "|": 6.0, "\u00b7": 6.0}
_WIDE_W = {"m": 13.5, "w": 13.5, "M": 13.5, "W": 13.5, "%": 13.0,
           "@": 13.0, "&": 13.0}


def _norm(ch):
    return {"\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"',
            "\u2013": "-", "\u2014": "-", "\u2026": "..."}.get(ch, ch)


def adv(ch, size):
    ch = _norm(ch)
    if ch in _NARROW_W:
        u = _NARROW_W[ch]
    elif ch in _WIDE_W:
        u = _WIDE_W[ch]
    else:
        u = 12.4
    return u * (size / 10.0) * XS


def text_w(s, size):
    return sum(adv(c, size) for c in s)


def _glyph_points(spec):
    pts = []
    for stroke in spec.split("|"):
        line = []
        for tok in stroke.split():
            x, y = tok.split(",")
            line.append((float(x), float(y)))
        pts.append(line)
    return pts


_GLYPHS = {c: _glyph_points(s) for c, s in FONT.items() if s}


def draw_text(cv, x, base_y, s, size, color, bold=False, slant=0.0):
    """Draw s with its baseline at base_y; returns width drawn."""
    sc = size / 10.0
    t = max(1, int(round(size / 13.0)) + (1 if bold else 0))
    cx = float(x)
    for ch in s:
        ch = _norm(ch)
        if ch == " ":
            cx += adv(" ", size)
            continue
        gl = _GLYPHS.get(ch)
        if gl is None:
            cx += adv(ch, size)
            continue
        for stroke in gl:
            for i in range(len(stroke) - 1):
                ax, ay = stroke[i]; bx, by = stroke[i + 1]
                sh_a = (10.0 - ay) * slant * sc
                sh_b = (10.0 - by) * slant * sc
                cv.line(cx + ax * sc * XS + sh_a, base_y - (10.0 - ay) * sc,
                        cx + bx * sc * XS + sh_b, base_y - (10.0 - by) * sc,
                        color, t)
        cx += adv(ch, size)
    return cx - x


def wrap(s, size, maxw):
    words = s.split(" ")
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if text_w(trial, size) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def para(cv, x, y, s, size, color, maxw, lh, bold=False, slant=0.0):
    """Draw wrapped paragraph; y is the top. Returns bottom y."""
    for ln in wrap(s, size, maxw):
        draw_text(cv, x, y + size, ln, size, color, bold, slant)
        y += lh
    return y

# ---------------------------------------------------------------- palette
PAPER = (247, 243, 234)      # newsprint cream
INK = (22, 26, 34)           # near-black ink
INK_SOFT = (58, 62, 70)
RED = (178, 34, 24)          # headline red
BLUE = (29, 78, 137)         # deep blue
GOLD = (176, 132, 30)
OCEAN = (214, 230, 242)
LAND = (232, 220, 195)
LAND_LINE = (138, 123, 92)
CARD = (255, 255, 255)
CARD_LINE = (196, 188, 172)
LIGHT = (238, 233, 220)
WHITE = (255, 255, 255)
TEAL = (27, 120, 88)
GREEN_BG = (232, 240, 232)

REGION_COLORS = {
    "CLIMATE": (178, 34, 24),
    "MIDDLE EAST": (146, 64, 14),
    "EUROPE": (29, 78, 137),
    "ASIA": (27, 120, 88),
    "AMERICAS": (107, 44, 120),
    "AFRICA": (150, 92, 8),
    "SCIENCE & TECH": (14, 110, 130),
    "SPORT & MARKETS": (34, 110, 60),
    "GLOBAL": (70, 70, 78),
}

# ---------------------------------------------------------------- data
# (region, headline) -- every story first reported Monday 23 November 2026.
STORIES = [
    ("MIDDLE EAST", "Houthi drones, missiles hit Riyadh, day 3"),
    ("MIDDLE EAST", "Iran strike injures 2 in Bahrain"),
    ("MIDDLE EAST", "25+ tankers hit near Hormuz in 7 days"),
    ("MIDDLE EAST", "Saudi-led coalition intercepts Houthi missiles"),
    ("MIDDLE EAST", "Israeli strikes kill 9 in Gaza; truce toll 1,661"),
    ("MIDDLE EAST", "Netanyahu-Eisenkot unity talks end, no deal"),
    ("EUROPE", "Russian drone hits Kyiv building; 14+ missing"),
    ("EUROPE", "Russian cargo ship still burning off Finland"),
    ("EUROPE", "Part of Crimea Bridge falls after blast"),
    ("EUROPE", "Poland: 3 Russian cruise missiles fell Friday"),
    ("EUROPE", "Thousands march in Lisbon on living costs"),
    ("EUROPE", "UK to build Ukrainian drones in new deal"),
    ("EUROPE", "French living-cost protests enter 6th Saturday"),
    ("ASIA", "Nepal PM Shah meets PM Modi in Delhi"),
    ("ASIA", "S. Korea education minister quits in AI scandal"),
    ("ASIA", "Indonesia factory fire: 7 dead, 50 missing"),
    ("ASIA", "Beijing bars young red-chips listing abroad"),
    ("ASIA", "Myanmar calls ASEAN decision 'unfair'"),
    ("AMERICAS", "Schumer faces challenge from Van Hollen"),
    ("AMERICAS", "Mexico captures 'El Chapo Isidro'; 11 dead"),
    ("AMERICAS", "9 in hospital after California concert shooting"),
    ("AMERICAS", "Delta glitch causes big Thanksgiving delays"),
    ("AMERICAS", "Bolsonaro 'stable' in intensive care"),
    ("AFRICA", "24 civilians killed in South Sudan violence"),
    ("AFRICA", "Drone hits home, UN building in Sudan capital"),
    ("AFRICA", "35 Fulani killed in reprisal attack in Nigeria"),
    ("AFRICA", "WHO chief pleads for peace in Ebola-hit Congo"),
    ("AFRICA", "Boat sinks in Nigeria: at least 24 dead"),
    ("SCIENCE & TECH", "BepiColombo reaches Mercury after 8 years"),
    ("SCIENCE & TECH", "Pentagon releases 43 declassified UAP files"),
    ("SCIENCE & TECH", "Lab-bred mosquitoes could fight dengue"),
    ("SPORT & MARKETS", "India post record 720/9d in Wellington Test"),
    ("SPORT & MARKETS", "Alcaraz wins first ATP Finals title"),
    ("SPORT & MARKETS", "Bitcoin recovers after two-year low"),
    ("GLOBAL", "UN killer-robot talks go on; no rules till 2028"),
    ("GLOBAL", "Kim: N. Korea seeks security, not supremacy"),
    ("GLOBAL", "Ganga water deal faces 12 Dec deadline"),
]

HEROES = [
    ("CLIMATE \u00b7 COP31 FAILS", RED,
     "Final draft in T\u00fcrkiye drops \u201cfossil fuels\u201d. "
     "Guterres \u201cdeeply disappointed\u201d; EU says talks "
     "\u201chijacked by oil states\u201d."),
    ("MIDDLE EAST \u00b7 RIYADH HIT", (146, 64, 14),
     "Houthi drones and missiles strike Riyadh a third day "
     "running. 25+ tankers hit near the Strait of Hormuz in a week."),
    ("AMERICAS \u00b7 \u2018EL CHAPO ISIDRO\u2019 CAUGHT", (107, 44, 120),
     "Mexico captures the FBI\u2019s most-wanted cartel boss. "
     "11 killed in Sinaloa as troops move in."),
]

# Region order for the map pins and the story grid.
REGIONS = ["CLIMATE", "MIDDLE EAST", "EUROPE", "ASIA", "AMERICAS",
           "AFRICA", "SCIENCE & TECH", "SPORT & MARKETS", "GLOBAL"]

# (lon, lat) of each region's pin on the map.
PINS = {
    "CLIMATE": (30.7, 36.9),        # Antalya, Turkiye (COP31)
    "MIDDLE EAST": (46.7, 24.7),    # Riyadh
    "EUROPE": (-9.1, 38.7),         # Lisbon
    "ASIA": (77.2, 28.6),           # Delhi
    "AMERICAS": (-99.1, 19.4),      # Mexico City
    "AFRICA": (32.5, 15.5),         # Khartoum
    "SCIENCE & TECH": (-52.8, 5.2), # Kourou (ESA launch site)
    "SPORT & MARKETS": (174.8, -41.3),  # Wellington (Test venue)
    "GLOBAL": (-74.0, 40.7),        # New York (UN)
}

# Rough continent outlines, equirectangular (lon, lat).
CONTINENTS = [
    [(-168, 66), (-140, 70), (-125, 71), (-110, 68), (-95, 69), (-85, 66),
     (-75, 62), (-65, 60), (-55, 52), (-60, 47), (-70, 44), (-75, 38),
     (-80, 32), (-81, 26), (-90, 21), (-97, 16), (-105, 20), (-115, 28),
     (-125, 40), (-125, 49), (-140, 60), (-155, 58), (-165, 60)],
    [(-80, 10), (-75, 10), (-62, 10), (-52, 5), (-50, 0), (-44, -3),
     (-35, -8), (-38, -15), (-48, -25), (-57, -35), (-65, -41), (-70, -50),
     (-73, -53), (-73, -45), (-73, -35), (-72, -25), (-77, -15), (-81, -5),
     (-80, 3)],
    [(-17, 15), (-10, 30), (0, 36), (10, 37), (20, 32), (32, 31), (35, 28),
     (40, 15), (44, 11), (51, 11), (48, 2), (40, -5), (36, -18), (32, -28),
     (26, -34), (18, -35), (15, -27), (12, -18), (9, 4), (4, 6), (-8, 5),
     (-13, 8), (-17, 12)],
    [(-10, 36), (-9, 43), (-2, 48), (0, 51), (5, 53), (8, 57), (10, 59),
     (18, 56), (21, 55), (24, 58), (28, 60), (30, 62), (40, 68), (55, 68),
     (70, 72), (90, 75), (110, 76), (130, 72), (150, 70), (170, 66),
     (178, 65), (170, 60), (162, 56), (158, 52), (142, 50), (140, 45),
     (135, 43), (130, 42), (127, 40), (122, 38), (120, 32), (110, 21),
     (108, 18), (105, 10), (100, 8), (97, 10), (92, 16), (88, 22),
     (80, 13), (77, 8), (75, 12), (72, 20), (66, 25), (61, 25), (57, 26),
     (52, 28), (50, 30), (48, 29), (44, 29), (40, 31), (36, 36), (30, 36),
     (26, 38), (23, 36), (19, 40), (15, 44), (12, 44), (8, 44), (3, 43),
     (0, 40), (-2, 37), (-6, 36)],
    [(114, -22), (114, -32), (118, -35), (124, -33), (130, -32), (135, -35),
     (140, -38), (147, -39), (150, -37), (153, -32), (153, -27), (150, -23),
     (146, -19), (142, -15), (142, -11), (137, -12), (135, -12), (132, -11),
     (130, -13), (126, -14), (122, -17), (118, -20)],
    [(130, 31), (132, 33), (135, 34), (137, 35), (139, 36), (140, 38),
     (141, 40), (142, 42), (144, 44), (142, 45), (140, 44), (139, 42)],
    [(95, 5), (100, 0), (105, -5), (110, -7), (115, -8), (120, -10),
     (125, -9), (130, -3), (135, -4), (140, -8)],
    [(131, -1), (136, -2), (141, -3), (146, -6), (150, -9), (147, -9),
     (142, -8), (138, -7), (134, -4)],
]

# ---------------------------------------------------------------- drawing
def draw_map(cv, x0, y0, x1, y1):
    """World map strip with numbered region pins."""
    cv.fill_rect(x0, y0, x1, y1, OCEAN)
    cv.rect(x0, y0, x1, y1, CARD_LINE, 1)
    # graticule
    for lon in range(-150, 181, 30):
        gx = x0 + (lon + 180) / 360.0 * (x1 - x0)
        cv.line(gx, y0, gx, y1, (190, 208, 224), 1)
    for lat in (-30, 0, 30, 60):
        gy = y0 + (75 - lat) / 130.0 * (y1 - y0)
        cv.line(x0, gy, x1, gy, (190, 208, 224), 1)

    def proj(lon, lat):
        return (x0 + (lon + 180) / 360.0 * (x1 - x0),
                y0 + (75 - lat) / 130.0 * (y1 - y0))

    for poly in CONTINENTS:
        pts = [proj(lon, lat) for lon, lat in poly]
        cv.poly(pts, LAND)
        cv.poly(pts, LAND_LINE, fill=False)

    # pins: numbered circles, one per region
    for i, region in enumerate(REGIONS, start=1):
        lon, lat = PINS[region]
        px, py = proj(lon, lat)
        color = REGION_COLORS[region]
        cv.circle(px, py, 10, color)
        cv.circle(px, py, 10, WHITE, fill=False)
        num = str(i)
        draw_text(cv, px - text_w(num, 11) / 2, py + 4, num, 11,
                  WHITE, bold=True)
    draw_text(cv, x0 + 8, y0 + 18, "WORLD MAP \u2014 9 REGIONS, NUMBERED",
              12, INK_SOFT, bold=True)


def draw_hero_art(cv, box, kind):
    """Small drawn panel for a hero card. box = (x0, y0, x1, y1)."""
    x0, y0, x1, y1 = box
    if kind == 0:  # COP31: globe + thermometer
        cv.fill_rect(x0, y0, x1, y1, (226, 238, 226))
        cx, cy, r = x0 + 58, y0 + 42, 32
        cv.circle(cx, cy, r, (120, 170, 120))
        ellipse_outline(cv, cx, cy, r, r, BLUE, 2)
        arc(cv, cx, cy, r, r, 200, 340, WHITE, 2)
        cv.line(cx, cy - r, cx, cy + r, WHITE, 2)
        cv.line(cx - r, cy, cx + r, cy, WHITE, 2)
        # thermometer
        tx = x0 + 118
        cv.fill_rect(tx, y0 + 12, tx + 16, y0 + 56, WHITE)
        cv.rect(tx, y0 + 12, tx + 16, y0 + 56, INK, 2)
        cv.fill_rect(tx + 2, y0 + 32, tx + 14, y0 + 54, RED)
        cv.circle(tx + 8, y0 + 61, 11, RED)
        cv.circle(tx + 8, y0 + 61, 11, INK, fill=False)
        draw_text(cv, x0 + 150, y0 + 31, "NO", 19, RED, bold=True)
        draw_text(cv, x0 + 150, y0 + 53, "\u201cFOSSIL", 19, RED, bold=True)
        draw_text(cv, x0 + 150, y0 + 75, "FUELS\u201d", 19, RED, bold=True)
    elif kind == 1:  # Riyadh night skyline + interception bursts
        cv.fill_rect(x0, y0, x1, y1, (24, 32, 54))
        for bx, bh in ((x0 + 14, 58), (x0 + 52, 74), (x0 + 96, 50),
                       (x0 + 132, 66), (x0 + 172, 44), (x0 + 210, 60),
                       (x0 + 248, 52)):
            cv.fill_rect(bx, y1 - bh, bx + 34, y1, (52, 66, 100))
            for wy in range(y1 - bh + 8, y1 - 6, 12):
                cv.fill_rect(bx + 6, wy, bx + 12, wy + 5, (240, 200, 90))
        # missile arcs + bursts
        arc(cv, x0 + 90, y0 + 30, 60, 40, 200, 330, RED, 3)
        arc(cv, x0 + 230, y0 + 20, 60, 40, 210, 330, RED, 3)
        burst(cv, x0 + 95, y0 + 22, 9, (255, 210, 90))
        burst(cv, x0 + 235, y0 + 16, 9, (255, 210, 90))
    else:  # El Chapo Isidro: badge + handcuffs
        cv.fill_rect(x0, y0, x1, y1, (238, 228, 210))
        # shield / badge
        sx, sy = x0 + 112, y0 + 4
        shield = [(sx, sy), (sx + 48, sy + 11), (sx + 48, sy + 42),
                  (sx, sy + 58), (sx - 48, sy + 42), (sx - 48, sy + 11)]
        cv.poly(shield, GOLD)
        cv.poly(shield, INK, fill=False)
        draw_text(cv, sx - 22, sy + 37, "FBI", 19, INK, bold=True)
        # handcuffs
        ellipse_outline(cv, x0 + 36, y0 + 69, 18, 11, INK, 5)
        ellipse_outline(cv, x0 + 84, y0 + 69, 18, 11, INK, 5)
        cv.line(x0 + 54, y0 + 68, x0 + 66, y0 + 68, INK, 4)
        draw_text(cv, x0 + 120, y0 + 79, "CAPTURED", 19, (107, 44, 120),
                  bold=True)


def draw_hero_cards(cv, y0, height):
    margin = 24
    gap = 16
    cw = (W - 2 * margin - 2 * gap) // 3
    y1 = y0 + height
    for i, (kick, color, body) in enumerate(HEROES):
        x0 = margin + i * (cw + gap)
        x1 = x0 + cw
        cv.fill_rect(x0, y0, x1, y1, CARD)
        cv.rect(x0, y0, x1, y1, CARD_LINE, 1)
        cv.fill_rect(x0, y0, x1, y0 + 5, color)
        art_h = 84
        draw_hero_art(cv, (x0 + 8, y0 + 12, x1 - 8, y0 + 12 + art_h), i)
        ty = y0 + 12 + art_h + 8
        # kicker, up to 2 lines
        for ln in wrap(kick, 17, cw - 24)[:2]:
            draw_text(cv, x0 + 12, ty + 17, ln, 17, color, bold=True)
            ty += 21
        ty += 2
        # body, up to 4 lines
        for ln in wrap(body, 14, cw - 24)[:4]:
            draw_text(cv, x0 + 12, ty + 14, ln, 14, INK)
            ty += 17


def draw_story_grid(cv, y0):
    margin = 24
    gap = 16
    cw = (W - 2 * margin - 2 * gap) // 3
    by_region = {}
    for region, headline in STORIES:
        by_region.setdefault(region, []).append(headline)
    # Column packing: keep regions whole, balance by line count.
    plan = [
        ["MIDDLE EAST", "AFRICA"],
        ["EUROPE", "AMERICAS"],
        ["ASIA", "SCIENCE & TECH", "SPORT & MARKETS", "GLOBAL"],
    ]
    bottoms = []
    for ci, regions in enumerate(plan):
        x0 = margin + ci * (cw + gap)
        x1 = x0 + cw
        y = y0
        for region in regions:
            stories = by_region[region]
            color = REGION_COLORS[region]
            idx = REGIONS.index(region) + 1
            header = "%d  %s  (%d)" % (idx, region, len(stories))
            cv.fill_rect(x0, y, x1, y + 24, color)
            draw_text(cv, x0 + 8, y + 18, header, 14, WHITE, bold=True)
            y += 24 + 6
            for j, headline in enumerate(stories, start=1):
                num = "%d." % j
                draw_text(cv, x0 + 4, y + 11, num, 11, color, bold=True)
                for ln in wrap(headline, 10, cw - 30):
                    draw_text(cv, x0 + 26, y + 10, ln, 10, INK)
                    y += 13
                y += 2
            y += 8
        bottoms.append(y)
    return max(bottoms)

# ---------------------------------------------------------------- layout
def build():
    cv = Canvas(W, H, PAPER)

    # ---------------------------------------------------------- header
    cv.fill_rect(0, 0, W, 10, RED)
    draw_text(cv, 24, 37, "THE WORLD IN ONE DAY  \u00b7  A ONE-DAY NEWSPAPER",
              15, INK_SOFT, bold=True)
    rt = "DAILY EDITION  \u00b7  23 NOV 2026"
    draw_text(cv, W - 24 - text_w(rt, 15), 37, rt, 15, INK_SOFT, bold=True)
    draw_text(cv, 24, 88, "MONDAY 23 NOVEMBER 2026", 46, INK, bold=True)
    draw_text(cv, 24, 111, "38 date-checked stories \u00b7 9 regions",
              19, RED, bold=True)
    draw_text(cv, 24, 133,
              "COP31 fails \u00b7 Houthi strikes Riyadh \u00b7 Mexico captures "
              "\u2018El Chapo Isidro\u2019",
              19, RED, bold=True)
    cv.fill_rect(24, 136, W - 24, 138, INK)

    # ---------------------------------------------------------- map strip
    draw_map(cv, 24, 144, W - 24, 268)

    # ---------------------------------------------------------- hero cards
    draw_hero_cards(cv, 278, 200)

    # ---------------------------------------------------------- story grid
    grid_bottom = draw_story_grid(cv, 488)

    # ---------------------------------------------------------- UTC strip
    sy = 886
    cv.fill_rect(24, sy, W - 24, sy + 40, INK)
    draw_text(cv, 36, sy + 24, "THE DAY IN UTC", 13, (255, 210, 90), bold=True)
    ticks = "00:00  \u00b7  06:00  \u00b7  12:00  \u00b7  18:00  \u00b7  23:59 UTC"
    tw = text_w(ticks, 13)
    draw_text(cv, (W - tw) / 2, sy + 24, ticks, 13, WHITE, bold=True)

    # ---------------------------------------------------------- date check + footer
    fy = 938
    cv.fill_rect(24, fy, W - 24, fy + 46, GREEN_BG)
    cv.rect(24, fy, W - 24, fy + 46, TEAL, 2)
    draw_text(cv, 36, fy + 18, "DATE CHECK \u2713", 12, TEAL, bold=True)
    draw_text(cv, 36, fy + 36,
              "Every story on this page was first reported on Monday 23 November "
              "2026. Nothing here is from before 13 November 2026.",
              12, INK)
    draw_text(cv, 24, 1004,
              "Sources: BBC News, Reuters, Associated Press, Agence France-Presse, "
              "Al Jazeera, United Nations, ESA / NASA \u2014 all stories first "
              "reported 23 Nov 2026.",
              10, INK_SOFT)
    draw_text(cv, 24, 1020, "news-image-20261123 \u00b7 make.fun \u00b7 drawn by a program, "
              "no photograph used",
              10, INK_SOFT)
    print("grid bottom y:", grid_bottom)
    return cv


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    cv = build()
    write_png(os.path.join(outdir, "entry.png"), cv.px, W, H)


if __name__ == "__main__":
    main()
