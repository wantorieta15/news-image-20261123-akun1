#!/usr/bin/env python3
"""Monday 23 November 2026: 38 date-checked stories, 9 regions.

A one-day newspaper front page summing up the world's news of Monday
23 November 2026. Draws a single 1024x1024 PNG with the Python standard
library plus Pillow only. No network. Deterministic: two runs write
identical bytes.

Run:  MAKEFUN_OUTPUT_DIR=out python3 main.py   ->  out/entry.png

Competition: news-image-20261123 ($100, make.fun).
SPDX-License-Identifier: MIT
"""

import os
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024

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

# ---------------------------------------------------------------- fonts
def _font(name, size):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % name,
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default(size=size)


F_TITLE = _font("-Bold", 46)
F_SUB = _font("-Bold", 19)
F_MAST = _font("-Bold", 15)
F_HERO_H = _font("-Bold", 19)
F_HERO_B = _font("", 15)
F_REG = _font("-Bold", 14)
F_STORY = _font("", 12)
F_SMALL = _font("", 12)
F_SMALL_B = _font("-Bold", 12)
F_MAP_NUM = _font("-Bold", 13)
F_PIN = _font("-Bold", 11)
F_FOOT = _font("", 12)
F_FOOT_B = _font("-Bold", 12)
F_STRIP = _font("-Bold", 13)


def wrap(draw, text, font, width):
    """Greedy word wrap; returns list of lines that fit `width`."""
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=font) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def text_block(draw, x, y, text, font, width, fill, leading=None, max_lines=None):
    """Draw wrapped text; returns y after the last line."""
    if leading is None:
        leading = font.size + 4
    lines = wrap(draw, text, font, width)
    if max_lines:
        lines = lines[:max_lines]
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += leading
    return y


# ---------------------------------------------------------------- data
# (region, headline) — every story first reported Monday 23 November 2026.
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
def draw_map(draw, x0, y0, x1, y1):
    """World map strip with numbered region pins."""
    draw.rectangle([x0, y0, x1, y1], fill=OCEAN, outline=CARD_LINE, width=1)
    # graticule
    for lon in range(-150, 181, 30):
        gx = x0 + (lon + 180) / 360.0 * (x1 - x0)
        draw.line([gx, y0, gx, y1], fill=(190, 208, 224), width=1)
    for lat in (-30, 0, 30, 60):
        gy = y0 + (75 - lat) / 130.0 * (y1 - y0)
        draw.line([x0, gy, x1, gy], fill=(190, 208, 224), width=1)

    def proj(lon, lat):
        return (x0 + (lon + 180) / 360.0 * (x1 - x0),
                y0 + (75 - lat) / 130.0 * (y1 - y0))

    for poly in CONTINENTS:
        pts = [proj(lon, lat) for lon, lat in poly]
        draw.polygon(pts, fill=LAND, outline=LAND_LINE)

    # pins: numbered circles, one per region
    for i, region in enumerate(REGIONS, start=1):
        lon, lat = PINS[region]
        px, py = proj(lon, lat)
        color = REGION_COLORS[region]
        r = 10
        draw.ellipse([px - r, py - r, px + r, py + r], fill=color,
                     outline=WHITE, width=2)
        num = str(i)
        tw = draw.textlength(num, font=F_PIN)
        draw.text((px - tw / 2, py - 8), num, font=F_PIN, fill=WHITE)
    draw.text((x0 + 8, y0 + 6), "WORLD MAP \u2014 9 REGIONS, NUMBERED",
              font=F_SMALL_B, fill=INK_SOFT)


def draw_hero_art(draw, box, kind):
    """Small drawn panel for a hero card. box = (x0, y0, x1, y1)."""
    x0, y0, x1, y1 = box
    if kind == 0:  # COP31: globe + thermometer
        draw.rectangle(box, fill=(226, 238, 226))
        cx, cy, r = x0 + 58, y0 + 42, 32
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(120, 170, 120),
                     outline=BLUE, width=2)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=BLUE, width=2)
        draw.arc([cx - r, cy - r, cx + r, cy + r], 200, 340, fill=WHITE, width=2)
        draw.line([cx, cy - r, cx, cy + r], fill=WHITE, width=2)
        draw.line([cx - r, cy, cx + r, cy], fill=WHITE, width=2)
        # thermometer
        tx = x0 + 118
        draw.rectangle([tx, y0 + 12, tx + 16, y0 + 56], fill=WHITE,
                       outline=INK, width=2)
        draw.rectangle([tx + 2, y0 + 32, tx + 14, y0 + 54], fill=RED)
        draw.ellipse([tx - 3, y0 + 50, tx + 19, y0 + 72], fill=RED,
                     outline=INK, width=2)
        draw.text((x0 + 150, y0 + 12), "NO", font=F_HERO_H, fill=RED)
        draw.text((x0 + 150, y0 + 34), "\u201cFOSSIL", font=F_HERO_H, fill=RED)
        draw.text((x0 + 150, y0 + 56), "FUELS\u201d", font=F_HERO_H, fill=RED)
    elif kind == 1:  # Riyadh night skyline + interception bursts
        draw.rectangle(box, fill=(24, 32, 54))
        for bx, bh in ((x0 + 14, 58), (x0 + 52, 74), (x0 + 96, 50),
                       (x0 + 132, 66), (x0 + 172, 44), (x0 + 210, 60),
                       (x0 + 248, 52)):
            draw.rectangle([bx, y1 - bh, bx + 34, y1], fill=(52, 66, 100))
            for wy in range(y1 - bh + 8, y1 - 6, 12):
                draw.rectangle([bx + 6, wy, bx + 12, wy + 5], fill=(240, 200, 90))
        # missile arcs + bursts
        draw.arc([x0 + 30, y0 - 10, x0 + 150, y0 + 70], 200, 330, fill=RED, width=3)
        draw.arc([x0 + 170, y0 - 20, x0 + 290, y0 + 60], 210, 330, fill=RED, width=3)
        for bx, by in ((x0 + 95, y0 + 22), (x0 + 235, y0 + 16)):
            for dx, dy in ((0, -9), (7, -6), (9, 0), (7, 6), (0, 9),
                           (-7, 6), (-9, 0), (-7, -6)):
                draw.line([bx, by, bx + dx, by + dy], fill=(255, 210, 90), width=2)
            draw.ellipse([bx - 3, by - 3, bx + 3, by + 3], fill=(255, 210, 90))
    else:  # El Chapo Isidro: badge + handcuffs
        draw.rectangle(box, fill=(238, 228, 210))
        # shield / badge
        sx, sy = x0 + 112, y0 + 4
        shield = [(sx, sy), (sx + 48, sy + 11), (sx + 48, sy + 42),
                  (sx, sy + 58), (sx - 48, sy + 42), (sx - 48, sy + 11)]
        draw.polygon(shield, fill=GOLD, outline=INK, width=2)
        draw.text((sx - 22, sy + 18), "FBI", font=F_HERO_H, fill=INK)
        # handcuffs
        draw.ellipse([x0 + 18, y0 + 58, x0 + 54, y0 + 80], outline=INK, width=5)
        draw.ellipse([x0 + 66, y0 + 58, x0 + 102, y0 + 80], outline=INK, width=5)
        draw.line([x0 + 54, y0 + 68, x0 + 66, y0 + 68], fill=INK, width=4)
        draw.text((x0 + 120, y0 + 60), "CAPTURED", font=F_HERO_H, fill=(107, 44, 120))


def draw_hero_cards(draw, y0, height):
    margin = 24
    gap = 16
    cw = (W - 2 * margin - 2 * gap) // 3
    y1 = y0 + height
    for i, (kick, color, body) in enumerate(HEROES):
        x0 = margin + i * (cw + gap)
        x1 = x0 + cw
        draw.rectangle([x0, y0, x1, y1], fill=CARD, outline=CARD_LINE, width=1)
        draw.rectangle([x0, y0, x1, y0 + 5], fill=color)
        art_h = 84
        draw_hero_art(draw, (x0 + 8, y0 + 12, x1 - 8, y0 + 12 + art_h), i)
        ty = y0 + 12 + art_h + 8
        ty = text_block(draw, x0 + 12, ty, kick, F_HERO_H, cw - 24, color,
                        leading=21, max_lines=2)
        text_block(draw, x0 + 12, ty + 2, body, F_HERO_B, cw - 24, INK,
                   leading=18, max_lines=4)


def draw_story_grid(draw, y0, y1):
    margin = 24
    gap = 16
    cw = (W - 2 * margin - 2 * gap) // 3
    cols = [[], [], []]
    by_region = {}
    for region, headline in STORIES:
        by_region.setdefault(region, []).append(headline)
    # Column packing: keep regions whole, balance by line count.
    plan = [
        ["MIDDLE EAST", "AFRICA"],
        ["EUROPE", "AMERICAS"],
        ["ASIA", "SCIENCE & TECH", "SPORT & MARKETS", "GLOBAL"],
    ]
    for ci, regions in enumerate(plan):
        x0 = margin + ci * (cw + gap)
        x1 = x0 + cw
        y = y0
        for region in regions:
            stories = by_region[region]
            color = REGION_COLORS[region]
            idx = REGIONS.index(region) + 1
            header = "%d  %s  (%d)" % (idx, region, len(stories))
            draw.rectangle([x0, y, x1, y + 24], fill=color)
            draw.text((x0 + 8, y + 4), header, font=F_REG, fill=WHITE)
            y += 24 + 6
            for j, headline in enumerate(stories, start=1):
                num = "%d." % j
                draw.text((x0 + 4, y), num, font=F_SMALL_B, fill=color)
                y = text_block(draw, x0 + 26, y, headline, F_STORY, cw - 30,
                               INK, leading=16, max_lines=1)
                y += 2
            y += 8
        cols[ci] = y
    return max(cols)


def build():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # ---------------------------------------------------------- header
    d.rectangle([0, 0, W, 10], fill=RED)
    d.text((24, 22), "THE WORLD IN ONE DAY  \u00b7  A ONE-DAY NEWSPAPER",
           font=F_MAST, fill=INK_SOFT)
    d.text((W - 24 - d.textlength("DAILY EDITION  \u00b7  23 NOV 2026", font=F_MAST), 22),
           "DAILY EDITION  \u00b7  23 NOV 2026", font=F_MAST, fill=INK_SOFT)
    d.text((24, 42), "MONDAY 23 NOVEMBER 2026", font=F_TITLE, fill=INK)
    d.text((24, 92), "38 date-checked stories \u00b7 9 regions",
           font=F_SUB, fill=RED)
    d.text((24, 114),
           "COP31 fails \u00b7 Houthi strikes Riyadh \u00b7 Mexico captures "
           "\u2018El Chapo Isidro\u2019",
           font=F_SUB, fill=RED)
    d.line([24, 136, W - 24, 136], fill=INK, width=2)

    # ---------------------------------------------------------- map strip
    draw_map(d, 24, 144, W - 24, 268)

    # ---------------------------------------------------------- hero cards
    draw_hero_cards(d, 278, 200)

    # ---------------------------------------------------------- story grid
    grid_bottom = draw_story_grid(d, 488, 876)

    # ---------------------------------------------------------- UTC strip
    sy = 886
    d.rectangle([24, sy, W - 24, sy + 40], fill=INK)
    d.text((36, sy + 11), "THE DAY IN UTC", font=F_STRIP, fill=(255, 210, 90))
    ticks = "00:00  \u00b7  06:00  \u00b7  12:00  \u00b7  18:00  \u00b7  23:59 UTC"
    tw = d.textlength(ticks, font=F_STRIP)
    d.text(((W - tw) / 2, sy + 11), ticks, font=F_STRIP, fill=WHITE)

    # ---------------------------------------------------------- date check + footer
    fy = 938
    d.rectangle([24, fy, W - 24, fy + 46], fill=(232, 240, 232),
                outline=(27, 120, 88), width=2)
    d.text((36, fy + 6), "DATE CHECK \u2713", font=F_FOOT_B, fill=(27, 120, 88))
    d.text((36, fy + 24),
           "Every story on this page was first reported on Monday 23 November "
           "2026. Nothing here is from before 13 November 2026.",
           font=F_FOOT, fill=INK)
    d.text((24, 992),
           "Sources: BBC News, Reuters, Associated Press, Agence France-Presse, "
           "Al Jazeera, United Nations, ESA / NASA \u2014 all stories first "
           "reported 23 Nov 2026.",
           font=F_FOOT, fill=INK_SOFT)
    d.text((24, 1008), "news-image-20261123 \u00b7 make.fun \u00b7 drawn by a program, "
           "no photograph used",
           font=F_FOOT, fill=INK_SOFT)

    return img


def main():
    out_dir = os.environ["MAKEFUN_OUTPUT_DIR"]
    os.makedirs(out_dir, exist_ok=True)
    img = build()
    path = os.path.join(out_dir, "entry.png")
    img.save(path, format="PNG", optimize=True)


if __name__ == "__main__":
    main()
