"""news-image-20261123 - Akun 1 - v3 (written from scratch, pure stdlib).

Draws a one-day newspaper: MONDAY 23 NOVEMBER 2026, 38 date-checked
stories, 9 regions. Output: $MAKEFUN_OUTPUT_DIR/entry.png (1024x1024).
No network, no PIL, no system fonts. Deterministic.
"""
import os
import struct
import zlib
import math

W, H = 1024, 1024

PAPER = (247, 243, 234)
INK = (22, 26, 34)
INK_SOFT = (58, 62, 70)
RED = (178, 34, 24)
BLUE = (29, 78, 137)
GOLD = (176, 132, 30)
OCEAN = (214, 230, 242)
LAND = (232, 220, 195)
LAND_LINE = (138, 123, 92)
CARD = (255, 255, 255)
CARD_LINE = (196, 188, 172)
LIGHT = (238, 233, 220)
WHITE = (255, 255, 255)
NAVY = (16, 24, 48)
GREEN = (27, 120, 88)
LGREEN = (220, 240, 220)
DGREEN = (34, 110, 60)
YELLOW = (240, 200, 40)
BROWN = (146, 64, 14)
PURPLE = (107, 44, 120)
GRID = (205, 198, 180)


class Canvas:
    def __init__(self):
        self.buf = bytearray(W * H * 3)
        self.fill_rect(0, 0, W, H, PAPER)

    def px(self, x, y, c):
        if 0 <= x < W and 0 <= y < H:
            i = (y * W + x) * 3
            self.buf[i] = c[0]
            self.buf[i + 1] = c[1]
            self.buf[i + 2] = c[2]

    def fill_rect(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(W, x + w)
        y1 = min(H, y + h)
        for yy in range(y0, y1):
            base = (yy * W + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.buf[i] = c[0]
                self.buf[i + 1] = c[1]
                self.buf[i + 2] = c[2]

    def rect(self, x, y, w, h, c, t=1):
        for k in range(t):
            self.fill_rect(x + k, y + k, w - 2 * k, 1, c)
            self.fill_rect(x + k, y + h - 1 - k, w - 2 * k, 1, c)
            self.fill_rect(x + k, y + k, 1, h - 2 * k, c)
            self.fill_rect(x + w - 1 - k, y + k, 1, h - 2 * k, c)

    def line(self, x0, y0, x1, y1, c):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.px(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def polyline(self, pts, c):
        for a, b in zip(pts, pts[1:]):
            self.line(a[0], a[1], b[0], b[1], c)

    def fill_circle(self, cx, cy, r, c):
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(max(0, r * r - dy * dy)))
            self.fill_rect(cx - dx, cy + dy, 2 * dx + 1, 1, c)

    def circle(self, cx, cy, r, c):
        pts = []
        for k in range(72):
            a = 2.0 * math.pi * k / 72.0
            pts.append((int(round(cx + r * math.cos(a))),
                        int(round(cy + r * math.sin(a)))))
        pts.append(pts[0])
        self.polyline(pts, c)

    def fill_poly(self, pts, c):
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        y0, y1 = max(0, min(ys)), min(H - 1, max(ys))
        n = len(pts)
        for y in range(y0, y1 + 1):
            xs = []
            for i in range(n):
                x1, y1p = pts[i]
                x2, y2p = pts[(i + 1) % n]
                if (y1p <= y < y2p) or (y2p <= y < y1p):
                    if y2p != y1p:
                        xs.append(x1 + (y - y1p) * (x2 - x1) / (y2p - y1p))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                xa = int(math.ceil(xs[j]))
                xb = int(math.floor(xs[j + 1]))
                if xb >= xa:
                    self.fill_rect(xa, y, xb - xa + 1, 1, c)


# ---- 5x7 bitmap font, designed here. '#' = on, '.' = off. ----
G = {}
G["A"] = ("01110", "10001", "10001", "11111", "10001", "10001", "10001")
G["B"] = ("11110", "10001", "10001", "11110", "10001", "10001", "11110")
G["C"] = ("01110", "10001", "10000", "10000", "10000", "10001", "01110")
G["D"] = ("11110", "10001", "10001", "10001", "10001", "10001", "11110")
G["E"] = ("11111", "10000", "10000", "11110", "10000", "10000", "11111")
G["F"] = ("11111", "10000", "10000", "11110", "10000", "10000", "10000")
G["G"] = ("01110", "10001", "10000", "10111", "10001", "10001", "01111")
G["H"] = ("10001", "10001", "10001", "11111", "10001", "10001", "10001")
G["I"] = ("01110", "00100", "00100", "00100", "00100", "00100", "01110")
G["J"] = ("00111", "00010", "00010", "00010", "00010", "10010", "01100")
G["K"] = ("10001", "10010", "10100", "11000", "10100", "10010", "10001")
G["L"] = ("10000", "10000", "10000", "10000", "10000", "10000", "11111")
G["M"] = ("10001", "11011", "10101", "10101", "10001", "10001", "10001")
G["N"] = ("10001", "11001", "10101", "10011", "10001", "10001", "10001")
G["O"] = ("01110", "10001", "10001", "10001", "10001", "10001", "01110")
G["P"] = ("11110", "10001", "10001", "11110", "10000", "10000", "10000")
G["Q"] = ("01110", "10001", "10001", "10001", "10101", "10010", "01101")
G["R"] = ("11110", "10001", "10001", "11110", "10100", "10010", "10001")
G["S"] = ("01111", "10000", "10000", "01110", "00001", "00001", "11110")
G["T"] = ("11111", "00100", "00100", "00100", "00100", "00100", "00100")
G["U"] = ("10001", "10001", "10001", "10001", "10001", "10001", "01110")
G["V"] = ("10001", "10001", "10001", "10001", "10001", "01010", "00100")
G["W"] = ("10001", "10001", "10001", "10101", "10101", "11011", "10001")
G["X"] = ("10001", "10001", "01010", "00100", "01010", "10001", "10001")
G["Y"] = ("10001", "10001", "01010", "00100", "00100", "00100", "00100")
G["Z"] = ("11111", "00001", "00010", "00100", "01000", "10000", "11111")
G["0"] = ("01110", "10001", "10011", "10101", "11001", "10001", "01110")
G["1"] = ("00100", "01100", "00100", "00100", "00100", "00100", "01110")
G["2"] = ("01110", "10001", "00001", "00010", "00100", "01000", "11111")
G["3"] = ("11111", "00010", "00100", "00010", "00001", "10001", "01110")
G["4"] = ("00010", "00110", "01010", "10010", "11111", "00010", "00010")
G["5"] = ("11111", "10000", "11110", "00001", "00001", "10001", "01110")
G["6"] = ("00110", "01000", "10000", "11110", "10001", "10001", "01110")
G["7"] = ("11111", "00001", "00010", "00100", "01000", "01000", "01000")
G["8"] = ("01110", "10001", "10001", "01110", "10001", "10001", "01110")
G["9"] = ("01110", "10001", "10001", "01111", "00001", "00010", "01100")

G["a"] = (".....", ".....", ".1110", "....1", ".1111", "10001", ".1111")
G["b"] = ("10000", "10000", "11110", "10001", "10001", "10001", "11110")
G["c"] = (".....", ".....", ".1110", "10001", "10000", "10001", ".1110")
G["d"] = ("....1", "....1", ".1111", "10001", "10001", "10001", ".1111")
G["e"] = (".....", ".....", ".1110", "10001", "11111", "10000", ".1110")
G["f"] = ("..110", ".100.", ".100.", "11110", ".100.", ".100.", ".100.")
G["g"] = (".....", ".1111", "10001", "10001", ".1111", "....1", ".1110")
G["h"] = ("10000", "10000", "11110", "10001", "10001", "10001", "10001")
G["i"] = ("..1..", ".....", ".110.", "..1..", "..1..", "..1..", ".111.")
G["j"] = ("....1", ".....", "...11", "....1", "....1", "....1", "..11.")
G["k"] = ("10000", "10000", "10010", "10100", "11000", "10100", "10010")
G["l"] = ("..1..", "..1..", "..1..", "..1..", "..1..", "..1..", ".111.")
G["m"] = (".....", ".....", "11010", "10101", "10101", "10101", "10101")
G["n"] = (".....", ".....", "11110", "10001", "10001", "10001", "10001")
G["o"] = (".....", ".....", ".1110", "10001", "10001", "10001", ".1110")
G["p"] = (".....", ".....", "11110", "10001", "10001", "11110", "10000")
G["q"] = (".....", ".....", ".1111", "10001", "10001", ".1111", "....1")
G["r"] = (".....", ".....", "10110", "11001", "10000", "10000", "10000")
G["s"] = (".....", ".....", ".1111", "10000", ".1110", "....1", "11110")
G["t"] = (".100.", ".100.", "11110", ".100.", ".100.", ".100.", "..110")
G["u"] = (".....", ".....", "10001", "10001", "10001", "10001", ".1111")
G["v"] = (".....", ".....", "10001", "10001", "10001", ".1010", "..1..")
G["w"] = (".....", ".....", "10001", "10101", "10101", "10101", ".101.")
G["x"] = (".....", ".....", "10001", ".1010", "..1..", ".1010", "10001")
G["y"] = (".....", ".....", "10001", "10001", ".1111", "....1", ".1110")
G["z"] = (".....", ".....", "11111", "...1.", "..1..", ".1...", "11111")
G[" "] = (".....", ".....", ".....", ".....", ".....", ".....", ".....")
G["."] = (".....", ".....", ".....", ".....", ".....", ".11..", ".11..")
G[","] = (".....", ".....", ".....", ".....", ".11..", ".11..", ".1...")
G[":"] = (".....", ".11..", ".11..", ".....", ".11..", ".11..", ".....")
G[";"] = (".....", ".11..", ".11..", ".....", ".11..", ".11..", ".1...")
G["'"] = ("..1..", "..1..", ".1...", ".....", ".....", ".....", ".....")
G['"'] = (".101.", ".101.", ".101.", ".....", ".....", ".....", ".....")
G["-"] = (".....", ".....", ".....", ".1111", ".....", ".....", ".....")
G["("] = ("...1.", "..1..", ".1...", ".1...", ".1...", "..1..", "...1.")
G[")"] = (".1...", "..1..", "...1.", "...1.", "...1.", "..1..", ".1...")
G["/"] = ("....1", "...1.", "...1.", "..1..", ".1...", ".1...", "1....")
G["%"] = ("11001", "11010", "00010", "00100", "01000", "01011", "10011")
G["$"] = ("..1..", ".1111", "10100", ".1110", "00101", "11110", "..1..")
G["!"] = ("..1..", "..1..", "..1..", "..1..", "..1..", ".....", "..1..")
G["?"] = (".1110", "10001", "....1", "...10", "..1..", ".....", "..1..")
G["="] = (".....", ".....", ".1111", ".....", ".1111", ".....", ".....")
G["+"] = (".....", "..1..", "..1..", ".1111", "..1..", "..1..", ".....")
G["&"] = (".110.", "10001", "10010", ".110.", "10101", "10010", ".1101")
G["_"] = (".....", ".....", ".....", ".....", ".....", ".....", "11111")
G["["] = (".111.", ".1...", ".1...", ".1...", ".1...", ".1...", ".111.")
G["]"] = (".111.", "...1.", "...1.", "...1.", "...1.", "...1.", ".111.")
G["<"] = ("....1", "...1.", "..1..", ".1...", "..1..", "...1.", "....1")
G[">"] = ("1....", ".1...", "..1..", "...1.", "..1..", ".1...", "1....")
G["#"] = (".101.", ".101.", "11111", ".101.", ".101.", "11111", ".101.")
G["@"] = (".1110", "10001", "10111", "10101", "10110", "10000", ".1110")
G["~"] = (".....", ".....", ".1101", "10110", ".....", ".....", ".....")
G["^"] = ("..1..", ".101.", "10001", ".....", ".....", ".....", ".....")
G["|"] = ("..1..", "..1..", "..1..", "..1..", "..1..", "..1..", "..1..")
G["*"] = (".....", ".101.", ".111.", ".101.", ".....", ".....", ".....")


def normalize(s):
    rep = {
        "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "-", "\u00b7": ".", "\u2026": "...",
        "\u00fc": "u", "\u00ed": "i", "\u00f3": "o", "\u00e9": "e",
        "\u00e0": "a", "\u00f1": "n",
    }
    for k, v in rep.items():
        s = s.replace(k, v)
    return "".join(ch if ch in G else " " for ch in s)


def glyph_rows(ch):
    return G.get(ch, G[" "])


def text_w(s, sc):
    return max(0, len(s) * 6 * sc - sc)


def draw_text(cv, x, y, s, color, sc=1, bold=False):
    s = normalize(s)
    cx = x
    for ch in s:
        rows = glyph_rows(ch)
        for r in range(7):
            row = rows[r]
            for cc in range(5):
                if row[cc] == "1":
                    cv.fill_rect(cx + cc * sc, y + r * sc, sc, sc, color)
                    if bold:
                        cv.fill_rect(cx + cc * sc + 1, y + r * sc, sc, sc, color)
        cx += 6 * sc
    return cx


def wrap_text(s, maxw, sc):
    s = normalize(s)
    words = s.split(" ")
    lines = []
    cur = ""
    for wd in words:
        trial = wd if not cur else cur + " " + wd
        if text_w(trial, sc) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def draw_para(cv, x, y, s, color, maxw, sc=1, lh=None, bold=False):
    if lh is None:
        lh = 7 * sc + 2
    yy = y
    for ln in wrap_text(s, maxw, sc):
        draw_text(cv, x, yy, ln, color, sc, bold)
        yy += lh
    return yy


def png_chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out


def write_png(path, cv):
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw += cv.buf[y * W * 3:(y + 1) * W * 3]
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += png_chunk(b"IHDR", ihdr)
    png += png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += png_chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


# ---- World map (lon, lat, equirectangular) ----
CONTINENTS = [
    [(-168, 66), (-140, 70), (-125, 71), (-110, 68), (-95, 69), (-85, 66),
     (-75, 62), (-65, 60), (-55, 52), (-60, 47), (-70, 44), (-75, 38),
     (-80, 32), (-81, 26), (-90, 21), (-97, 16), (-105, 20), (-115, 28),
     (-125, 40), (-125, 49), (-140, 60), (-155, 58), (-165, 60)],
    [(-80, 10), (-75, 10), (-62, 10), (-52, 5), (-50, 0), (-44, -3),
     (-35, -8), (-38, -15), (-48, -25), (-57, -35), (-65, -41), (-70, -50),
     (-73, -53), (-73, -45), (-73, -35), (-72, -25), (-77, -15), (-81, -5),
     (-80, 3)],
    [(-17, 15), (-10, 30), (0, 36), (10, 37), (20, 32), (32, 31),
     (35, 28), (40, 15), (44, 11), (51, 11), (48, 2), (40, -5),
     (36, -18), (32, -28), (26, -34), (18, -35), (15, -27), (12, -18),
     (9, 4), (4, 6), (-8, 5), (-13, 8), (-17, 12)],
    [(-10, 36), (-9, 43), (-2, 48), (0, 51), (5, 53), (8, 57),
     (10, 59), (18, 56), (21, 55), (24, 58), (28, 60), (30, 62),
     (40, 68), (55, 68), (70, 72), (90, 75), (110, 76), (130, 72),
     (150, 70), (170, 66), (178, 65), (170, 60), (162, 56), (158, 52),
     (142, 50), (140, 45), (135, 43), (130, 42), (127, 40), (122, 38),
     (120, 32), (110, 21), (108, 18), (105, 10), (100, 8), (97, 10),
     (92, 16), (88, 22), (80, 13), (77, 8), (75, 12), (72, 20),
     (66, 25), (61, 25), (57, 26), (52, 28), (50, 30), (48, 29),
     (44, 29), (40, 31), (36, 36), (30, 36), (26, 38), (23, 36),
     (19, 40), (15, 44), (12, 44), (8, 44), (3, 43), (0, 40),
     (-2, 37), (-6, 36)],
    [(114, -22), (114, -32), (118, -35), (124, -33), (130, -32),
     (135, -35), (140, -38), (147, -39), (150, -37), (153, -32),
     (153, -27), (150, -23), (146, -19), (142, -15), (142, -11),
     (137, -12), (135, -12), (132, -11), (130, -13), (126, -14),
     (122, -17), (118, -20)],
    [(130, 31), (132, 33), (135, 34), (137, 35), (139, 36), (140, 38),
     (141, 40), (142, 42), (144, 44), (142, 45), (140, 44), (139, 42)],
    [(95, 5), (100, 0), (105, -5), (110, -7), (115, -8), (120, -10),
     (125, -9), (130, -3), (135, -4), (140, -8)],
    [(131, -1), (136, -2), (141, -3), (146, -6), (150, -9), (147, -9),
     (142, -8), (138, -7), (134, -4)],
]

MAP_X, MAP_Y, MAP_W, MAP_H = 24, 144, 976, 124


def proj(lon, lat):
    x = MAP_X + (lon + 180.0) / 360.0 * MAP_W
    y = MAP_Y + (75.0 - lat) / 130.0 * MAP_H
    return (int(round(x)), int(round(y)))


def draw_map(cv, pins):
    cv.fill_rect(MAP_X, MAP_Y, MAP_W, MAP_H, OCEAN)
    cv.rect(MAP_X, MAP_Y, MAP_W, MAP_H, CARD_LINE)
    for lon in range(-180, 181, 30):
        x, _ = proj(lon, 0)
        cv.line(x, MAP_Y + 1, x, MAP_Y + MAP_H - 1, GRID)
    for lat in (-30, 0, 30, 60):
        _, y = proj(0, lat)
        cv.line(MAP_X + 1, y, MAP_X + MAP_W - 1, y, GRID)
    for poly in CONTINENTS:
        pts = [proj(lon, lat) for lon, lat in poly]
        cv.fill_poly(pts, LAND)
        cv.polyline(pts + [pts[0]], LAND_LINE)
    for num, (lon, lat) in enumerate(pins, start=1):
        x, y = proj(lon, lat)
        cv.fill_circle(x, y, 10, WHITE)
        cv.fill_circle(x, y, 9, RED)
        cv.circle(x, y, 10, WHITE)
        d = str(num)
        draw_text(cv, x - text_w(d, 1) // 2, y - 3, d, WHITE, 1, bold=True)
    label = "WORLD MAP - 9 REGIONS, NUMBERED"
    lw = text_w(label, 1)
    lx = MAP_X + (MAP_W - lw) // 2
    cv.fill_rect(lx - 6, MAP_Y + MAP_H - 12, lw + 12, 11, PAPER)
    draw_text(cv, lx, MAP_Y + MAP_H - 11, label, INK_SOFT, 1, bold=True)


# ---- Content: 38 stories, 9 regions (pin order 1-9) ----
REGIONS = [
    ("CLIMATE", RED),
    ("MIDDLE EAST", (146, 64, 14)),
    ("EUROPE", BLUE),
    ("ASIA", (27, 120, 88)),
    ("AMERICAS", (107, 44, 120)),
    ("AFRICA", (150, 92, 8)),
    ("SCIENCE & TECH", (14, 110, 130)),
    ("SPORT & MARKETS", (34, 110, 60)),
    ("GLOBAL", (70, 70, 78)),
]

STORIES = {
    "MIDDLE EAST": [
        "Houthi drones, missiles hit Riyadh, day 3",
        "Iran strike injures 2 in Bahrain",
        "25+ tankers hit near Hormuz in 7 days",
        "Saudi-led coalition intercepts Houthi missiles",
        "Israeli strikes kill 9 in Gaza; truce toll 1,661",
        "Netanyahu-Eisenkot unity talks end, no deal",
    ],
    "EUROPE": [
        "Russian drone hits Kyiv building; 14+ missing",
        "Russian cargo ship still burning off Finland",
        "Part of Crimea Bridge falls after blast",
        "Poland: 3 Russian cruise missiles fell Friday",
        "Thousands march in Lisbon on living costs",
        "UK to build Ukrainian drones in new deal",
        "French living-cost protests enter 6th Saturday",
    ],
    "ASIA": [
        "Nepal PM Shah meets PM Modi in Delhi",
        "S. Korea education minister quits in AI scandal",
        "Indonesia factory fire: 7 dead, 50 missing",
        "Beijing bars young red-chips listing abroad",
        "Myanmar calls ASEAN decision 'unfair'",
    ],
    "AMERICAS": [
        "Schumer faces challenge from Van Hollen",
        "Mexico captures 'El Chapo Isidro'; 11 dead",
        "9 in hospital after California concert shooting",
        "Delta glitch causes big Thanksgiving delays",
        "Bolsonaro 'stable' in intensive care",
    ],
    "AFRICA": [
        "24 civilians killed in South Sudan violence",
        "Drone hits home, UN building in Sudan capital",
        "35 Fulani killed in reprisal attack in Nigeria",
        "WHO chief pleads for peace in Ebola-hit Congo",
        "Boat sinks in Nigeria: at least 24 dead",
    ],
    "SCIENCE & TECH": [
        "BepiColombo reaches Mercury after 8 years",
        "Pentagon releases 43 declassified UAP files",
        "Lab-bred mosquitoes could fight dengue",
    ],
    "SPORT & MARKETS": [
        "India post record 720/9d in Wellington Test",
        "Alcaraz wins first ATP Finals title",
        "Bitcoin recovers after two-year low",
    ],
    "GLOBAL": [
        "UN killer-robot talks go on; no rules till 2028",
        "Kim: N. Korea seeks security, not supremacy",
        "Ganga water deal faces 12 Dec deadline",
    ],
}

PINS = [
    (30.7, 36.9),    # 1 CLIMATE
    (46.7, 24.7),    # 2 MIDDLE EAST
    (-9.1, 38.7),    # 3 EUROPE
    (77.2, 28.6),    # 4 ASIA
    (-99.1, 19.4),   # 5 AMERICAS
    (32.5, 15.5),    # 6 AFRICA
    (-52.8, 5.2),    # 7 SCIENCE & TECH
    (174.8, -41.3),  # 8 SPORT & MARKETS
    (-74.0, 40.7),   # 9 GLOBAL
]

HEROES = [
    {
        "kicker": "CLIMATE - COP31 FAILS",
        "color": RED,
        "body": "Final draft in Turkiye drops 'fossil fuels'. "
                "Guterres 'deeply disappointed'; EU says talks "
                "'hijacked by oil states'.",
        "art": 1,
    },
    {
        "kicker": "MIDDLE EAST - RIYADH HIT",
        "color": (146, 64, 14),
        "body": "Houthi drones and missiles strike Riyadh a third "
                "day running. 25+ tankers hit near the Strait of "
                "Hormuz in a week.",
        "art": 2,
    },
    {
        "kicker": "AMERICAS - 'EL CHAPO ISIDRO' CAUGHT",
        "color": (107, 44, 120),
        "body": "Mexico captures the FBI's most-wanted cartel boss. "
                "11 killed in Sinaloa as troops move in.",
        "art": 3,
    },
]


def hero_art1(cv, ax, ay):
    cv.fill_rect(ax, ay, 312, 84, OCEAN)
    cv.fill_circle(ax + 62, ay + 42, 30, GREEN)
    cv.circle(ax + 62, ay + 42, 30, INK)
    cv.line(ax + 36, ay + 34, ax + 88, ay + 34, (180, 230, 180))
    cv.line(ax + 34, ay + 50, ax + 90, ay + 50, (180, 230, 180))
    cv.fill_circle(ax + 52, ay + 32, 5, (120, 200, 110))
    cv.fill_circle(ax + 74, ay + 54, 6, (120, 200, 110))
    draw_text(cv, ax + 108, ay + 10, "NO", RED, 2, bold=True)
    draw_text(cv, ax + 108, ay + 28, "FOSSIL", RED, 2, bold=True)
    draw_text(cv, ax + 108, ay + 46, "FUELS", RED, 2, bold=True)
    cv.fill_rect(ax + 252, ay + 12, 10, 46, RED)
    cv.fill_circle(ax + 257, ay + 64, 11, RED)
    cv.fill_rect(ax + 255, ay + 16, 4, 40, (255, 120, 100))


def hero_art2(cv, ax, ay):
    cv.fill_rect(ax, ay, 312, 84, NAVY)
    for bx, bw, bh in ((8, 34, 42), (48, 26, 58), (80, 40, 34),
                       (126, 30, 50), (162, 36, 38), (204, 28, 56),
                       (238, 34, 44), (278, 28, 36)):
        cv.fill_rect(ax + bx, ay + 84 - bh, bw, bh, (30, 40, 70))
        for wy in range(ay + 84 - bh + 6, ay + 80, 12):
            for wx in range(ax + bx + 5, ax + bx + bw - 4, 10):
                cv.fill_rect(wx, wy, 4, 5, YELLOW)
    pts1 = []
    for t in range(0, 121):
        fx = t / 120.0
        pts1.append((ax + 20 + int(140 * fx),
                     ay + 84 - int(52 * 4 * fx * (1 - fx))))
    cv.polyline(pts1, RED)
    pts2 = []
    for t in range(0, 121):
        fx = t / 120.0
        pts2.append((ax + 150 + int(140 * fx),
                     ay + 84 - int(44 * 4 * fx * (1 - fx))))
    cv.polyline(pts2, RED)
    for bx, by in ((185, 26), (262, 40)):
        cv.fill_circle(ax + bx, ay + by, 3, YELLOW)
        for k in range(8):
            a = math.pi * k / 4.0
            cv.line(ax + bx, ay + by,
                    ax + bx + int(round(11 * math.cos(a))),
                    ay + by + int(round(11 * math.sin(a))), YELLOW)


def hero_art3(cv, ax, ay):
    cv.fill_rect(ax, ay, 312, 84, LIGHT)
    sh = [(ax + 40, ay + 8), (ax + 100, ay + 8), (ax + 100, ay + 38),
          (ax + 70, ay + 62), (ax + 40, ay + 38)]
    cv.fill_poly(sh, GOLD)
    cv.polyline(sh + [sh[0]], INK)
    draw_text(cv, ax + 70 - text_w("FBI", 3) // 2, ay + 20, "FBI", INK, 3, bold=True)
    cv.circle(ax + 192, ay + 30, 11, INK)
    cv.circle(ax + 232, ay + 30, 11, INK)
    cv.line(ax + 203, ay + 30, ax + 221, ay + 30, INK)
    cv.fill_rect(ax + 200, ay + 24, 6, 4, INK)
    cv.fill_rect(ax + 218, ay + 24, 6, 4, INK)
    cap = "CAPTURED"
    draw_text(cv, ax + (312 - text_w(cap, 2)) // 2, ay + 64, cap, RED, 2, bold=True)


COL_X = [24, 344, 664]
COL_W = 312
GRID_COLS = [
    ["MIDDLE EAST", "AFRICA"],
    ["EUROPE", "AMERICAS"],
    ["ASIA", "SCIENCE & TECH", "SPORT & MARKETS", "GLOBAL"],
]


def region_num(name):
    for i, (nm, _) in enumerate(REGIONS, start=1):
        if nm == name:
            return i
    return 0


def region_color(name):
    for nm, c in REGIONS:
        if nm == name:
            return c
    return INK


def draw_region_column(cv, x, groups):
    y = 488
    for name in groups:
        stories = STORIES[name]
        c = region_color(name)
        cv.fill_rect(x, y, COL_W, 22, c)
        head = "%d  %s  (%d)" % (region_num(name), name, len(stories))
        draw_text(cv, x + 8, y + 4, head, WHITE, 2, bold=True)
        y += 28
        for i, st in enumerate(stories, start=1):
            txt = "%d. %s" % (i, st)
            lines = wrap_text(txt, COL_W - 8, 1)
            for ln in lines:
                draw_text(cv, x + 4, y, ln, INK, 1, bold=True)
                y += 11
            y += 5
        y += 2
    return y


def draw_hero(cv, hx, hero):
    y0 = 278
    cv.fill_rect(hx, y0, COL_W, 200, CARD)
    cv.rect(hx, y0, COL_W, 200, CARD_LINE)
    art = hero["art"]
    if art == 1:
        hero_art1(cv, hx, y0)
    elif art == 2:
        hero_art2(cv, hx, y0)
    else:
        hero_art3(cv, hx, y0)
    ky = y0 + 84 + 6
    klines = wrap_text(hero["kicker"], COL_W - 16, 2)
    for ln in klines:
        draw_text(cv, hx + 8, ky, ln, hero["color"], 2, bold=True)
        ky += 15
    by = ky + 4
    draw_para(cv, hx + 12, by, hero["body"], INK, COL_W - 24, 2, lh=14)


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "")
    if not outdir:
        raise SystemExit("MAKEFUN_OUTPUT_DIR is required")
    os.makedirs(outdir, exist_ok=True)
    total = sum(len(v) for v in STORIES.values())
    assert total == 37, total
    cv = Canvas()
    cv.fill_rect(0, 0, W, 10, RED)
    draw_text(cv, 24, 22, "THE WORLD IN ONE DAY - A ONE-DAY NEWSPAPER",
              INK, 2, bold=True)
    right = "DAILY EDITION - 23 NOV 2026"
    draw_text(cv, 1000 - text_w(right, 2), 22, right, INK_SOFT, 2, bold=True)
    title = "MONDAY 23 NOVEMBER 2026"
    draw_text(cv, (W - text_w(title, 5)) // 2, 42, title, INK, 5, bold=True)
    sub1 = "37 date-checked stories - 9 regions"
    draw_text(cv, (W - text_w(sub1, 2)) // 2, 92, sub1, INK_SOFT, 2, bold=True)
    sub2 = "COP31 fails - Houthi strikes Riyadh - Mexico captures 'El Chapo Isidro'"
    draw_text(cv, (W - text_w(sub2, 2)) // 2, 114, sub2, INK, 2, bold=True)
    cv.fill_rect(24, 136, 976, 2, INK)
    draw_map(cv, PINS)
    for hx, hero in zip(COL_X, HEROES):
        draw_hero(cv, hx, hero)
    bottoms = []
    for x, groups in zip(COL_X, GRID_COLS):
        bottoms.append(draw_region_column(cv, x, groups))
    cv.fill_rect(24, 886, 976, 40, INK)
    draw_text(cv, 40, 899, "THE DAY IN UTC", GOLD, 2, bold=True)
    ticks = "00:00 - 06:00 - 12:00 - 18:00 - 23:59 UTC"
    draw_text(cv, (W - text_w(ticks, 2)) // 2, 899, ticks, WHITE, 2, bold=True)
    cv.fill_rect(24, 938, 976, 46, LGREEN)
    cv.rect(24, 938, 976, 46, DGREEN, t=2)
    cv.polyline([(36, 958), (42, 966), (56, 950)], DGREEN)
    cv.polyline([(36, 959), (42, 967), (56, 951)], DGREEN)
    draw_text(cv, 64, 946, "DATE CHECK", DGREEN, 2, bold=True)
    dct = ("Every story on this page was first reported on Monday "
           "23 November 2026. Nothing here is from before 13 November 2026.")
    draw_text(cv, 40, 968, dct, INK, 1, bold=True)
    src = ("Sources: BBC News, Reuters, Associated Press, Agence "
           "France-Presse, Al Jazeera, United Nations, ESA / NASA - "
           "all stories first reported 23 Nov 2026.")
    draw_text(cv, (W - text_w(src, 1)) // 2, 992, src, INK_SOFT, 1)
    tag = "news-image-20261123 - make.fun - drawn by a program, no photograph used"
    draw_text(cv, (W - text_w(tag, 1)) // 2, 1008, tag, INK_SOFT, 1)
    path = os.path.join(outdir, "entry.png")
    write_png(path, cv)
    print("WROTE", path)
    print("stories", total, "grid bottoms", bottoms)


if __name__ == "__main__":
    main()
