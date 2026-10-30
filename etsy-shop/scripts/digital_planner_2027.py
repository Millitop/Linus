"""2027 Digital Planner — hyperlinked landscape iPad PDF (GoodNotes / Notability / Xodo).

Run:  python3 scripts/digital_planner_2027.py
Out:  products/digital-planner-2027/digital-planner-2027.pdf

Uses the shared brand fonts/palette from brand.py but its own canvas setup
(1366 x 1024 pt landscape, cream background, right-hand tab bar, links).
"""
from __future__ import annotations

import calendar
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brand import (  # noqa: E402
    INK, MUTED, LINE, LINE_SOFT, CREAM, SAGE, SAGE_LIGHT, TERRA, TERRA_LIGHT, SAND,
    SERIF, SANS, SANS_LIGHT, SANS_BOLD, ITALIC, SHOP_NAME, OUT_DIR, Box,
)
from reportlab.lib.colors import HexColor, white  # noqa: E402
from reportlab.pdfbase import pdfmetrics  # noqa: E402
from reportlab.pdfgen import canvas  # noqa: E402
from reportlab import rl_config  # noqa: E402

rl_config.useA85 = 0  # binary streams: smaller file

SLUG = "digital-planner-2027"
TITLE = "2027 Digital Planner"
YEAR = 2027

W, H = 1366, 1024
BG = HexColor("#FBF8F3")          # soft cream screen background
CARD = white
TAB_W = 84
L = 60
R = W - TAB_W - 36
BODY_TOP = H - 166
BODY_BOT = 58

# seasonal accents: (strong, light, active-tab)
BLUE = (HexColor("#A7B6C4"), HexColor("#E1E7ED"), HexColor("#7F94A8"))
GREEN = (SAGE, SAGE_LIGHT, HexColor("#819B7D"))
CLAY = (TERRA, TERRA_LIGHT, HexColor("#BC7A58"))
OCHRE = (HexColor("#C4A574"), HexColor("#F0E6D2"), HexColor("#AE8E58"))
NEUTRAL = (HexColor("#B5AA98"), SAND, HexColor("#8A857C"))


def season(m):
    return {12: BLUE, 1: BLUE, 2: BLUE, 3: GREEN, 4: GREEN, 5: GREEN,
            6: CLAY, 7: CLAY, 8: CLAY}.get(m, OCHRE)


MONTHS = [calendar.month_name[m] for m in range(1, 13)]
MON_ABBR = [calendar.month_abbr[m] for m in range(1, 13)]
DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
CAL = calendar.Calendar(firstweekday=0)

# ---- weeks -----------------------------------------------------------------
FIRST_MON = date(YEAR, 1, 1) - timedelta(days=date(YEAR, 1, 1).weekday())
WEEKS = []
d = FIRST_MON
while d <= date(YEAR, 12, 31):
    WEEKS.append(d)
    d += timedelta(days=7)


def week_key(monday):
    return f"w{monday.isoformat()}"


def week_of(day):
    return day - timedelta(days=day.weekday())


def week_month(monday):
    thu = monday + timedelta(days=3)
    if thu.year < YEAR:
        return 1
    if thu.year > YEAR:
        return 12
    return thu.month


WEEKS_BY_MONTH = {m: [w for w in WEEKS if week_month(w) == m] for m in range(1, 13)}

N_NOTES = 10


def mkey(m, kind=""):
    return f"m{m:02d}{kind}"


# ---- drawing primitives --------------------------------------------------------
def sw(s, font, size, spacing=0):
    return pdfmetrics.stringWidth(s, font, size) + spacing * max(len(s) - 1, 0)


def text(c, x, y, s, font=SANS, size=11, color=INK, align="left", spacing=0):
    c.setFillColor(color)
    w = sw(s, font, size, spacing)
    ox = {"left": 0, "center": -w / 2, "right": -w}[align]
    t = c.beginText()
    t.setFont(font, size)
    t.setCharSpace(spacing)
    t.setTextOrigin(x + ox, y)
    t.textOut(s)
    c.drawText(t)
    return w


def label(c, x, y, s, color=MUTED, size=9, align="left", spacing=1.6):
    return text(c, x, y, s.upper(), SANS_BOLD, size, color, align, spacing)


def link(c, key, x, y, w, h):
    c.linkRect("", key, (x, y, x + w, y + h), relative=0, thickness=0)


def card(c, b: Box, fill=CARD, stroke=LINE_SOFT, r=14):
    if fill:
        c.setFillColor(fill)
    if stroke:
        c.setStrokeColor(stroke)
    c.setLineWidth(0.8)
    c.roundRect(b.x, b.y, b.w, b.h, r, stroke=1 if stroke else 0, fill=1 if fill else 0)


def panel(c, b: Box, title=None, accent=SAGE, pad=18, fill=CARD):
    card(c, b, fill)
    inner = b.inset(pad)
    if title:
        label(c, inner.x, inner.top - 8, title, accent, 9)
        inner = Box(inner.x, inner.y, inner.w, inner.h - 22)
    return inner


def hlines(c, b: Box, spacing=32, color=LINE, width=0.6, first=None):
    c.setStrokeColor(color)
    c.setLineWidth(width)
    y = b.top - (first if first is not None else spacing)
    while y >= b.y - 0.1:
        c.line(b.x, y, b.right, y)
        y -= spacing


def checklist(c, b: Box, spacing=36, accent=SAGE, box=11):
    y = b.top - spacing
    while y >= b.y - 0.1:
        c.setStrokeColor(accent)
        c.setLineWidth(0.9)
        c.roundRect(b.x, y + 2, box, box, 2.5, stroke=1, fill=0)
        c.setStrokeColor(LINE)
        c.setLineWidth(0.6)
        c.line(b.x + box + 10, y, b.right, y)
        y -= spacing


def dot_grid(c, b: Box, step=28, r=0.9, color=LINE):
    # dots as zero-length round-capped strokes: tiny content streams
    nx, ny = int(b.w // step), int(b.h // step)
    ox = b.x + (b.w - nx * step) / 2
    oy = b.y + (b.h - ny * step) / 2
    c.saveState()
    c.setStrokeColor(color)
    c.setLineWidth(2 * r)
    c.setLineCap(1)
    p = c.beginPath()
    for i in range(nx + 1):
        for j in range(ny + 1):
            x, y = ox + i * step, oy + j * step
            p.moveTo(x, y)
            p.lineTo(x, y)
    c.drawPath(p, stroke=1, fill=0)
    c.restoreState()


def leaf(c, x, y, s=12, color=SAGE):
    c.saveState()
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(1.0)
    c.line(x, y, x, y + 2.2 * s)
    for i, side in enumerate([-1, 1, -1, 1]):
        yy = y + 0.45 * s * (i + 1)
        p = c.beginPath()
        p.moveTo(x, yy)
        p.curveTo(x + side * 0.5 * s, yy + 0.1 * s, x + side * 0.7 * s, yy + 0.45 * s, x + side * 0.75 * s, yy + 0.6 * s)
        p.curveTo(x + side * 0.35 * s, yy + 0.55 * s, x + side * 0.1 * s, yy + 0.3 * s, x, yy)
        c.drawPath(p, stroke=0, fill=1)
    c.restoreState()


def wrap(s, font, size, width):
    words, lines, cur = s.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if sw(t, font, size) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def para(c, x, y, s, width, font=SANS, size=12, color=INK, leading=1.5):
    for ln in wrap(s, font, size, width):
        text(c, x, y, ln, font, size, color)
        y -= size * leading
    return y


def chip_w(s, size=8.5, sp=1.4):
    return sw(s.upper(), SANS_BOLD, size, sp) + 30


def chip(c, x_right, y, s, key, accent=None, filled=False):
    """Pill-shaped link button, right-aligned at x_right. Returns its left x."""
    size, sp = 8.5, 1.4
    tw = sw(s.upper(), SANS_BOLD, size, sp)
    w, h = tw + 30, 28
    x = x_right - w
    c.setLineWidth(0.8)
    c.setStrokeColor(LINE)
    c.setFillColor(accent if filled else CARD)
    c.roundRect(x, y, w, h, h / 2, stroke=0 if filled else 1, fill=1)
    label(c, x + w / 2, y + 10, s, white if filled else INK, size, "center", sp)
    link(c, key, x, y, w, h)
    return x


# ---- page frame -------------------------------------------------------------------
class Planner:
    def __init__(self, path):
        self.c = canvas.Canvas(str(path), pagesize=(W, H), pageCompression=1)
        self.c.setTitle(f"{TITLE} — {SHOP_NAME}")
        self.c.setAuthor(SHOP_NAME)
        self.c.setSubject("Hyperlinked 2027 digital planner for GoodNotes, Notability and Xodo")
        self.c.setCreator(SHOP_NAME)
        self.c.showOutline()
        self.pages = 0

    def start(self, key, outline=None, level=0, closed=None):
        c = self.c
        c.setFillColor(BG)
        c.rect(0, 0, W, H, stroke=0, fill=1)
        c.bookmarkPage(key, fit="Fit")
        if outline:
            c.addOutlineEntry(outline, key, level=level, closed=closed)

    def finish(self, active=None):
        self.tabs(active)
        self.footer()
        self.c.showPage()
        self.pages += 1

    def footer(self):
        c = self.c
        label(c, L, 28, SHOP_NAME, LINE, 7.5, spacing=1.8)
        label(c, R, 28, f"{TITLE}  ·  personal use only", LINE, 7.5, "right", 1.4)

    def tabs(self, active):
        c = self.c
        items = [("Year", "year", NEUTRAL)] + [(MON_ABBR[m - 1], mkey(m), season(m)) for m in range(1, 13)] + [("Notes", "n01", NEUTRAL)]
        top, bot, gap, ggap = H - 40, 40, 5, 16
        th = (top - bot - 11 * gap - 2 * ggap) / 14
        y = top
        for i, (name, key, (strong, light, dark)) in enumerate(items):
            if i in (1, 13):
                y -= ggap - gap
            y -= th
            is_active = key == active
            x = W - (80 if is_active else 66)
            c.setFillColor(dark if is_active else light)
            c.roundRect(x, y, W - x + 12, th, 9, stroke=0, fill=1)
            label(c, (x + W) / 2 + (2 if is_active else 0), y + th / 2 - 4, name, white if is_active else INK, 10.5, "center", 1.6)
            link(c, key, x, y, W - x, th)
            y -= gap

    def header(self, title, crumb, accent, chips=(), crumb_key=None, title_size=50):
        c = self.c
        cw = label(c, L, H - 64, crumb, accent, 9.5)
        if crumb_key:
            link(c, crumb_key, L - 4, H - 72, cw + 8, 22)
        text(c, L, H - 122, title, SERIF, title_size, INK)
        x = R
        for s, key, filled in reversed(list(chips)):
            x = chip(c, x, H - 122, s, key, accent, filled) - 10
        c.setStrokeColor(accent)
        c.setLineWidth(1.6)
        c.line(L, H - 146, L + 48, H - 146)
        c.setStrokeColor(LINE_SOFT)
        c.setLineWidth(0.8)
        c.line(L + 54, H - 146, R, H - 146)

    # -- mini month (year page + weekly sidebar) ---------------------------------
    def mini_month(self, b: Box, m, accent, title_size=20, highlight=None, day_size=11.5):
        c = self.c
        strong, light, dark = accent
        name_w = text(c, b.x, b.top - title_size, MONTHS[m - 1], SERIF, title_size, INK)
        link(c, mkey(m), b.x - 4, b.top - title_size - 6, name_w + 8, title_size + 10)
        cw = b.w / 7
        y = b.top - title_size - 24
        for i, dn in enumerate("MTWTFSS"):
            label(c, b.x + cw * i + cw / 2, y, dn, strong if i < 5 else MUTED, 8, "center", 0)
        weeks = CAL.monthdatescalendar(YEAR, m)
        rows_h = y - 10 - b.y
        rh = min(rows_h / 6, day_size * 2.5)
        y -= 10
        for wk in weeks:
            y -= rh
            if highlight is not None and wk[0] == highlight:
                c.setFillColor(light)
                c.roundRect(b.x, y + 1, b.w, rh - 2, (rh - 2) / 2, stroke=0, fill=1)
            for i, day in enumerate(wk):
                if day.month != m:
                    continue
                text(c, b.x + cw * i + cw / 2, y + rh / 2 - day_size * 0.35, str(day.day), SANS,
                     day_size, INK if i < 5 else MUTED, "center")
                link(c, week_key(week_of(day)), b.x + cw * i, y, cw, rh)


# ---- pages ------------------------------------------------------------------------
def page_cover(p: Planner):
    c = p.c
    p.start("cover", "Cover")
    b = Box(L, BODY_BOT, R - L, H - 60 - BODY_BOT)
    card(c, b, CARD, None, 22)
    cx = b.x + b.w / 2
    # soft seasonal band
    band = [BLUE, GREEN, CLAY, OCHRE]
    bw = 160
    for i, a in enumerate(band):
        c.setFillColor(a[1])
        c.rect(cx - 2 * bw + i * bw, b.y + 110, bw, 6, stroke=0, fill=1)
    leaf(c, cx, H - 250, 16, SAGE)
    label(c, cx, H - 290, SHOP_NAME, SAGE, 11, "center", 3)
    text(c, cx, H - 530, "2027", SERIF, 230, INK, "center")
    text(c, cx, H - 610, "Digital Planner", SERIF, 54, INK, "center")
    text(c, cx, H - 660, "a calm, hyperlinked year for GoodNotes, Notability & Xodo", ITALIC, 18, MUTED, "center")
    feats = ["Monday start", "Monthly & weekly", "Goals & habits", "Tabbed & linked"]
    label(c, cx, H - 720, "   ·   ".join(feats), MUTED, 10, "center", 1.8)
    # start buttons
    x = cx + 160
    bx = chip(c, x, H - 800, "Year at a glance", "year", SAGE, True)
    chip(c, bx - 14, H - 800, "How to use", "howto")
    text(c, cx, b.y + 60, "Tap the tabs on the right to jump to any month.", SANS_LIGHT, 12, MUTED, "center")
    p.finish()


def page_howto(p: Planner):
    c = p.c
    p.start("howto", "How to use")
    p.header("How to use your planner", "Start here", SAGE, chips=[("Year at a glance", "year", True)])
    cols = Box(L, BODY_BOT + 372, R - L, BODY_TOP - BODY_BOT - 372).cols(3, 20)
    steps = [
        ("1", "Download", [
            "On Etsy, open You → Purchases and reviews, then tap Download files next to this order.",
            "On iPad, save the PDF to the Files app (or iCloud Drive) so your note app can find it.",
            "Tip: download on the iPad itself if you can; it saves a step.",
        ]),
        ("2", "Import", [
            "GoodNotes: tap + (New) → Import, choose the PDF. It opens as a new notebook.",
            "Notability: tap Import (or + → Import file) and choose the PDF.",
            "Xodo: tap the folder icon → Browse files and open the PDF.",
            "Or in Files, tap the PDF → Share → open in your app.",
        ]),
        ("3", "Navigate", [
            "The tabs on the right go to Year, each month and Notes, from every page.",
            "Year page: tap a month name for its calendar, or any date for that week.",
            "Month page: tap a week row (or its W-number) to open that weekly spread.",
            "Weekly pages have buttons back to the month and to the previous / next week.",
        ]),
    ]
    for b, (n, title, items) in zip(cols, steps):
        inner = panel(c, b, None)
        c.setFillColor(SAGE_LIGHT)
        c.circle(inner.x + 22, inner.top - 22, 22, stroke=0, fill=1)
        text(c, inner.x + 22, inner.top - 30, n, SERIF, 24, INK, "center")
        text(c, inner.x + 58, inner.top - 31, title, SERIF, 28, INK)
        y = inner.top - 80
        for it in items:
            c.setFillColor(SAGE)
            c.circle(inner.x + 4, y + 4, 2.4, stroke=0, fill=1)
            y = para(c, inner.x + 16, y, it, inner.w - 16, SANS, 13.5, INK, 1.42) - 10
    ins = Box(L, BODY_BOT + 230, R - L, 122)
    inner = panel(c, ins, "What's inside  ·  tap to jump", SAGE)
    items = [("Year at a glance", "year"), ("Important dates", "dates"), ("2027 goals", "goals"),
             ("Monthly calendars", mkey(1)), ("Goals & review", mkey(1, "g")), ("Habit trackers", mkey(1, "h")),
             ("53 weekly spreads", week_key(WEEKS[0])), ("10 notes pages", "n01")]
    widths = [chip_w(s_) for s_, _ in items]
    gap = (inner.w - sum(widths)) / (len(items) - 1)
    x = inner.x
    for (s_, k), w_ in zip(items, widths):
        chip(c, x + w_, inner.y + 14, s_, k)
        x += w_ + gap
    tips = Box(L, BODY_BOT, R - L, 210)
    inner = panel(c, tips, "Good to know", TERRA, fill=CARD)
    tcols = inner.cols(2, 40)
    left_t = [
        "If a link doesn't respond, switch your app to read-only / view mode, tap the link, then switch back to writing.",
        "Links only work inside the planner: keep it as one notebook rather than copying pages into another file.",
        "Weeks start on Monday and use ISO week numbers. The first week begins Mon, Dec 28, 2026 so Jan 1–3 have a home.",
    ]
    right_t = [
        "Need more room? Duplicate any Notes page in your app's page / thumbnail view.",
        "Add stickers, photos and highlights freely; the planner is a flat PDF, so nothing will shift.",
        "For personal use only. Please don't share or resell the file. Thank you for supporting a small shop!",
    ]
    for col, items in zip(tcols, [left_t, right_t]):
        y = col.top - 10
        for it in items:
            c.setFillColor(TERRA)
            c.circle(col.x + 4, y + 4, 2.4, stroke=0, fill=1)
            y = para(c, col.x + 16, y, it, col.w - 16, SANS, 12.5, INK, 1.4) - 10
    p.finish()


def page_year(p: Planner):
    c = p.c
    p.start("year", "Year at a glance")
    p.header("2027", "Year at a glance", NEUTRAL[2],
             chips=[("Important dates", "dates", False), ("Yearly goals", "goals", False)])
    boxes = []
    for row in Box(L, BODY_BOT, R - L, BODY_TOP - BODY_BOT).rows(3, 18):
        boxes += row.cols(4, 18)
    for m, b in enumerate(boxes, 1):
        card(c, b)
        acc = season(m)
        c.setFillColor(acc[0])
        c.roundRect(b.x + 22, b.top - 10, 30, 3, 1.5, stroke=0, fill=1)
        p.mini_month(Box(b.x + 22, b.y + 12, b.w - 44, b.h - 30), m, acc, 22, day_size=12)
    p.finish("year")


def page_dates(p: Planner):
    c = p.c
    p.start("dates", "Important dates")
    p.header("Important Dates", "2027 · birthdays, holidays, deadlines", NEUTRAL[2],
             chips=[("Year at a glance", "year", False), ("Yearly goals", "goals", False)])
    boxes = []
    for row in Box(L, BODY_BOT, R - L, BODY_TOP - BODY_BOT).rows(3, 18):
        boxes += row.cols(4, 18)
    for m, b in enumerate(boxes, 1):
        card(c, b)
        acc = season(m)
        inner = b.inset(20)
        w_ = text(c, inner.x, inner.top - 20, MONTHS[m - 1], SERIF, 22, INK)
        link(c, mkey(m), inner.x - 4, inner.top - 26, w_ + 8, 32)
        c.setFillColor(acc[0])
        c.roundRect(inner.x, inner.top - 34, 30, 3, 1.5, stroke=0, fill=1)
        hlines(c, Box(inner.x, inner.y, inner.w, inner.h - 44), 32)
    p.finish("year")


def page_goals(p: Planner):
    c = p.c
    p.start("goals", "Yearly goals")
    p.header("2027 Goals", "Dream it, plan it, do it", SAGE,
             chips=[("Year at a glance", "year", False), ("Important dates", "dates", False)])
    top, rest = Box(L, BODY_BOT, R - L, BODY_TOP - BODY_BOT).split_v(0.2, 18)
    word, vision = top.split_h(0.3, 18)
    inner = panel(c, word, "Word of the year", SAGE)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.6)
    c.line(inner.x, inner.y + 18, inner.right, inner.y + 18)
    inner = panel(c, vision, "This year I want to feel…", SAGE)
    hlines(c, inner, 34)
    cats = [("Personal", GREEN), ("Health & wellbeing", CLAY), ("Career & work", BLUE),
            ("Money", OCHRE), ("Relationships", CLAY), ("Learning & fun", GREEN)]
    boxes = []
    for row in rest.rows(2, 18):
        boxes += row.cols(3, 18)
    for b, (name, acc) in zip(boxes, cats):
        inner = panel(c, b, name, acc[2])
        checklist(c, inner, 38, acc[0])
    p.finish("year")


def page_month(p: Planner, m):
    c = p.c
    acc = season(m)
    strong, light, dark = acc
    p.start(mkey(m), MONTHS[m - 1], 0, closed=True)
    prev_k = mkey(m - 1) if m > 1 else "year"
    next_k = mkey(m + 1) if m < 12 else "n01"
    p.header(MONTHS[m - 1], f"{YEAR} · month {m:02d}", dark, crumb_key="year",
             chips=[("‹", prev_k, False), ("Goals & review", mkey(m, "g"), False),
                    ("Habits", mkey(m, "h"), False), ("›", next_k, False)])
    body = Box(L, BODY_BOT, R - L, BODY_TOP - BODY_BOT)
    cal_b, side = body.split_h(0.775, 20)
    card(c, cal_b)
    wk_col = 52
    hdr_h = 40
    gx = cal_b.x + wk_col
    gw = cal_b.right - gx - 14
    cw = gw / 7
    top = cal_b.top - 12
    for i, dn in enumerate(DAY_NAMES):
        label(c, gx + cw * i + cw / 2, top - hdr_h / 2 - 4, dn[:3], strong if i < 5 else MUTED, 9.5, "center")
    weeks = CAL.monthdatescalendar(YEAR, m)
    grid_top = top - hdr_h
    grid_bot = cal_b.y + 14
    rh = (grid_top - grid_bot) / len(weeks)
    # weekend tint
    c.setFillColor(HexColor("#FAF7F2"))
    c.rect(gx + 5 * cw, grid_bot, 2 * cw, grid_top - grid_bot, stroke=0, fill=1)
    c.setStrokeColor(LINE_SOFT)
    c.setLineWidth(0.8)
    for j in range(len(weeks) + 1):
        y = grid_top - j * rh
        c.line(cal_b.x + 14, y, gx + gw, y)
    for i in range(1, 7):
        c.line(gx + cw * i, grid_bot, gx + cw * i, grid_top)
    for j, wk in enumerate(weeks):
        y0 = grid_top - (j + 1) * rh
        wn = wk[0].isocalendar()[1]
        # week pill
        px, pw, ph = cal_b.x + 12, wk_col - 18, 26
        c.setFillColor(light)
        c.roundRect(px, y0 + rh - ph - 10, pw, ph, ph / 2, stroke=0, fill=1)
        label(c, px + pw / 2, y0 + rh - ph - 10 + 9, f"W{wn}", INK, 8.5, "center", 0.6)
        for i, day in enumerate(wk):
            inm = day.month == m
            text(c, gx + cw * i + 12, y0 + rh - 32, str(day.day), SERIF, 22,
                 (INK if i < 5 else MUTED) if inm else LINE)
        link(c, week_key(wk[0]), cal_b.x + 8, y0, gx + gw - cal_b.x - 8, rh)
    # sidebar
    f_b, n_b = side.split_v(0.36, 18)
    inner = panel(c, f_b, "Focus this month", dark)
    checklist(c, inner, 36, strong)
    inner = panel(c, n_b, "Notes", dark)
    hlines(c, inner, 32)
    p.finish(mkey(m))


def page_month_goals(p: Planner, m):
    c = p.c
    acc = season(m)
    strong, light, dark = acc
    p.start(mkey(m, "g"), "Goals & review", 1)
    p.header(f"{MONTHS[m - 1]} Goals & Review", f"{YEAR} · {MONTHS[m - 1]}", dark, crumb_key=mkey(m),
             chips=[(f"← {MONTHS[m - 1]}", mkey(m), False), ("Habits", mkey(m, "h"), False)])
    body = Box(L, BODY_BOT, R - L, BODY_TOP - BODY_BOT)
    left, right = body.split_h(0.5, 20)
    g, lower = left.split_v(0.6, 18)
    inner = panel(c, g, "Goals this month", dark)
    checklist(c, inner, 38, strong)
    wrd, dts = lower.split_h(0.42, 18)
    inner = panel(c, wrd, "One word / theme", dark)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.6)
    c.line(inner.x, inner.top - 46, inner.right, inner.top - 46)
    label(c, inner.x, inner.y + 52, "Energy check", MUTED, 8)
    for i in range(5):
        c.setStrokeColor(strong)
        c.setLineWidth(0.9)
        c.circle(inner.x + 12 + i * 30, inner.y + 22, 10, stroke=1, fill=0)
    inner = panel(c, dts, "Key dates", dark)
    hlines(c, inner, 32)
    rows = right.rows(3, 18)
    for b, t in zip(rows, ["Wins & highlights", "What I learned", "Next month I'll…"]):
        inner = panel(c, b, t, dark)
        hlines(c, inner, 32)
    p.finish(mkey(m))


def page_habits(p: Planner, m):
    c = p.c
    acc = season(m)
    strong, light, dark = acc
    p.start(mkey(m, "h"), "Habit tracker", 1)
    p.header(f"{MONTHS[m - 1]} Habits", f"{YEAR} · {MONTHS[m - 1]}", dark, crumb_key=mkey(m),
             chips=[(f"← {MONTHS[m - 1]}", mkey(m), False), ("Goals & review", mkey(m, "g"), False)])
    body = Box(L, BODY_BOT, R - L, BODY_TOP - BODY_BOT)
    card(c, body)
    inner = body.inset(22)
    ndays = calendar.monthrange(YEAR, m)[1]
    name_w = 230
    cw = (inner.w - name_w) / 31
    hdr = 50
    nrows = 15
    rh = (inner.h - hdr) / nrows
    gx = inner.x + name_w
    label(c, inner.x, inner.top - 30, "Habit", dark, 9)
    for dday in range(1, ndays + 1):
        dt = date(YEAR, m, dday)
        x = gx + (dday - 1) * cw + cw / 2
        wk = dt.weekday()
        label(c, x, inner.top - 14, "MTWTFSS"[wk], strong if wk < 5 else MUTED, 7.5, "center", 0)
        text(c, x, inner.top - 34, str(dday), SANS_BOLD if wk >= 5 else SANS, 10, INK if wk < 5 else MUTED, "center")
    for j in range(nrows):
        y = inner.top - hdr - (j + 1) * rh
        if j % 2 == 0:
            c.setFillColor(HexColor("#FAF7F2"))
            c.roundRect(inner.x - 8, y, inner.w + 16, rh, 6, stroke=0, fill=1)
        c.setStrokeColor(LINE)
        c.setLineWidth(0.6)
        c.line(inner.x, y + 12, gx - 18, y + 12)
        for dday in range(ndays):
            c.setStrokeColor(LINE)
            c.setLineWidth(0.7)
            c.circle(gx + dday * cw + cw / 2, y + rh / 2, min(cw, rh) * 0.3, stroke=1, fill=0)
    p.finish(mkey(m))


def fmt_range(mon):
    sun = mon + timedelta(days=6)
    if mon.month == sun.month:
        return f"{MONTHS[mon.month - 1]} {mon.day} – {sun.day}"
    return f"{MON_ABBR[mon.month - 1]} {mon.day} – {MON_ABBR[sun.month - 1]} {sun.day}"


def page_week(p: Planner, idx, mon):
    c = p.c
    m = week_month(mon)
    acc = season(m)
    strong, light, dark = acc
    iso_y, wn, _ = mon.isocalendar()
    p.start(week_key(mon), f"Week {wn} · {fmt_range(mon)}", 1)
    prev_k = week_key(WEEKS[idx - 1]) if idx > 0 else mkey(1)
    next_k = week_key(WEEKS[idx + 1]) if idx < len(WEEKS) - 1 else "n01"
    crumb = f"Week {wn}" + (f" · {iso_y}" if iso_y != YEAR else "") + f"  ·  {MONTHS[m - 1]} {YEAR}"
    p.header(fmt_range(mon), crumb, dark, crumb_key=mkey(m), title_size=46,
             chips=[("‹ Prev", prev_k, False), (f"{MONTHS[m - 1]}", mkey(m), True), ("Next ›", next_k, False)])
    body = Box(L, BODY_BOT, R - L, BODY_TOP - BODY_BOT)
    days_b, side = body.split_h(0.765, 18)
    cells = []
    for row in days_b.rows(2, 16):
        cells += row.cols(4, 16)
    for i, b in enumerate(cells[:7]):
        day = mon + timedelta(days=i)
        card(c, b)
        out = day.year != YEAR
        wkend = i >= 5
        # header strip
        c.setFillColor(light if not wkend else HexColor("#F4EFE7"))
        c.roundRect(b.x + 8, b.top - 52, b.w - 16, 44, 10, stroke=0, fill=1)
        nw = text(c, b.x + 20, b.top - 43, str(day.day), SERIF, 30, MUTED if out else INK)
        label(c, b.x + 28 + nw, b.top - 28, DAY_NAMES[i], INK if not wkend else MUTED, 9)
        label(c, b.x + 28 + nw, b.top - 42, MON_ABBR[day.month - 1] + (f" {day.year}" if out else ""), MUTED, 7.5, spacing=1.2)
        hlines(c, Box(b.x + 16, b.y + 14, b.w - 32, b.h - 66), 30, first=34)
    nb = cells[7]
    inner = panel(c, nb, "Notes", dark)
    dot_grid(c, Box(inner.x, inner.y, inner.w, inner.h - 4), 20, 0.9)
    # sidebar: mini month, priorities, to do
    mm_b, rest = side.split_v(0.31, 16)
    card(c, mm_b)
    p.mini_month(Box(mm_b.x + 18, mm_b.y + 10, mm_b.w - 36, mm_b.h - 32), m, acc, 18, highlight=mon, day_size=10.5)
    pr_b, td_b = rest.split_v(0.45, 16)
    inner = panel(c, pr_b, "Top priorities", dark)
    # numbered priorities
    sp = inner.h / 3
    for k in range(3):
        y = inner.top - (k + 1) * sp + 10
        c.setFillColor(light)
        c.circle(inner.x + 11, y + 6, 11, stroke=0, fill=1)
        text(c, inner.x + 11, y + 1.5, str(k + 1), SERIF, 13, INK, "center")
        c.setStrokeColor(LINE)
        c.setLineWidth(0.6)
        c.line(inner.x + 30, y, inner.right, y)
    inner = panel(c, td_b, "To do", dark)
    checklist(c, inner, 34, strong)
    p.finish(mkey(m))


def page_notes(p: Planner, n):
    c = p.c
    dots = n > N_NOTES // 2
    key = f"n{n:02d}"
    p.start(key, "Notes" if n == 1 else None)
    if n > 1:
        c.addOutlineEntry(f"Notes {n}", key, level=1)
    prev_k = f"n{n - 1:02d}" if n > 1 else mkey(12)
    next_k = f"n{n + 1:02d}" if n < N_NOTES else "year"
    p.header("Notes", f"Notes {n} of {N_NOTES} · {'dot grid' if dots else 'lined'}", NEUTRAL[2],
             chips=[("‹", prev_k, False), ("Lined", "n01", not dots), ("Dot grid", f"n{N_NOTES // 2 + 1:02d}", dots), ("›", next_k, False)])
    body = Box(L, BODY_BOT, R - L, BODY_TOP - BODY_BOT)
    card(c, body)
    inner = body.inset(36)
    if dots:
        dot_grid(c, inner, 26, 1.0)
    else:
        hlines(c, inner, 38, first=30)
    p.finish("n01")


def main():
    out = OUT_DIR / SLUG
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{SLUG}.pdf"
    p = Planner(path)
    page_cover(p)
    page_howto(p)
    page_year(p)
    page_dates(p)
    page_goals(p)
    wi = 0
    for m in range(1, 13):
        page_month(p, m)
        page_month_goals(p, m)
        page_habits(p, m)
        for mon in WEEKS_BY_MONTH[m]:
            page_week(p, WEEKS.index(mon), mon)
            wi += 1
    for n in range(1, N_NOTES + 1):
        page_notes(p, n)
    p.c.save()
    assert wi == len(WEEKS)
    print(f"wrote {path} — {p.pages} pages, {len(WEEKS)} weeks")


if __name__ == "__main__":
    main()
