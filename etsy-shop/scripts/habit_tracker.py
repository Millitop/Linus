"""Habit & Wellness Tracker — Linnea Paper Co.

Run from /home/user/Linus/etsy-shop:  python3 scripts/habit_tracker.py
Writes products/habit-wellness-tracker/habit-wellness-tracker-{letter,a4}.pdf
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brand import *  # noqa: E402,F401,F403
from reportlab.pdfbase.pdfmetrics import stringWidth  # noqa: E402

SLUG = "habit-wellness-tracker"
TITLE = "Habit & Wellness Tracker"

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
MONTH_DAYS = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
WEEKDAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]


# ---- small helpers (local to this product) ---------------------------------
def label_w(s, size=7.5, spacing=1.4):
    s = s.upper()
    return stringWidth(s, SANS_BOLD, size) + spacing * (len(s) - 1)


def field(p, x, y, w, name, size=7):
    """LABEL ________ fill-in line, width w starting at x (baseline y)."""
    p.label(x, y, name, size=size)
    lx = x + label_w(name, size) + 6
    c = p.c
    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    c.line(lx, y - 1, x + w, y - 1)


def face(p, x, y, r, mood, color=None):
    """Simple line-art face. mood 0 (low) .. 4 (great)."""
    c = p.c
    col = color or p.accent
    c.saveState()
    c.setStrokeColor(col)
    c.setFillColor(col)
    c.setLineWidth(0.8)
    c.circle(x, y, r, stroke=1, fill=0)
    er = max(0.55, r * 0.09)
    c.circle(x - 0.33 * r, y + 0.22 * r, er, stroke=0, fill=1)
    c.circle(x + 0.33 * r, y + 0.22 * r, er, stroke=0, fill=1)
    k = (mood - 2) / 2.0
    my = y - 0.28 * r + (0.12 * r if k < 0 else 0)
    cy = my - k * 0.32 * r
    pth = c.beginPath()
    pth.moveTo(x - 0.42 * r, my)
    pth.curveTo(x - 0.15 * r, cy, x + 0.15 * r, cy, x + 0.42 * r, my)
    c.drawPath(pth, stroke=1, fill=0)
    c.restoreState()


def glass(p, x, y, w, h, color=None):
    """Outline drinking glass with bottom-left at (x, y)."""
    c = p.c
    c.saveState()
    c.setStrokeColor(color or p.accent)
    c.setLineWidth(0.8)
    pth = c.beginPath()
    pth.moveTo(x, y + h)
    pth.lineTo(x + w, y + h)
    pth.lineTo(x + w * 0.86, y)
    pth.lineTo(x + w * 0.14, y)
    pth.close()
    c.drawPath(pth, stroke=1, fill=0)
    c.restoreState()


def checkbox(p, x, y, s=8, color=None):
    c = p.c
    c.setStrokeColor(color or p.accent)
    c.setLineWidth(0.8)
    c.roundRect(x, y, s, s, 1.5, stroke=1, fill=0)


def idea_list(p, b, items, spacing=19):
    """Pre-filled checklist (box + text + soft line)."""
    c = p.c
    y = b.top - spacing + 4
    for it in items:
        if y < b.y - 0.1:
            break
        checkbox(p, b.x, y + 1, 7.5)
        p.text(b.x + 15, y + 2, it, SANS, 9, INK)
        y -= spacing
    return y


def numbered_lines(p, b, n, spacing=None):
    spacing = spacing or b.h / n
    c = p.c
    for i in range(n):
        y = b.top - (i + 1) * spacing + 4
        p.text(b.x, y + 3, f"{i + 1}.", SANS_BOLD, 8, p.accent)
        c.setStrokeColor(LINE)
        c.setLineWidth(0.6)
        c.line(b.x + 14, y, b.right, y)


def scale_row(p, x, y, n, r, gap, numbers=True):
    """Row of n numbered circles, centred on baseline y. Returns end x."""
    c = p.c
    c.setLineWidth(0.8)
    for i in range(n):
        cx = x + r + i * (2 * r + gap)
        c.setStrokeColor(p.accent)
        c.circle(cx, y, r, stroke=1, fill=0)
        if numbers:
            p.text(cx, y - 2.3, str(i + 1), SANS, 6.5, MUTED, "center")
    return x + n * (2 * r + gap) - gap


def table(p, b, widths, headers, n_rows, header_h=20, row_h=None, zebra=False,
          vcolor=LINE, header_size=7):
    """Ruled table anchored at b.top. widths: list of numbers, one may be None
    (takes the remainder). Returns (xs, ys) with ys top->bottom row edges."""
    c = p.c
    fixed = sum(w for w in widths if w is not None)
    widths = [w if w is not None else b.w - fixed for w in widths]
    xs = [b.x]
    for w in widths:
        xs.append(xs[-1] + w)
    row_h = row_h or (b.h - header_h) / n_rows
    top = b.top
    bottom = top - header_h - n_rows * row_h
    ys = [top - header_h - i * row_h for i in range(n_rows + 1)]
    # header band
    c.setFillColor(p.accent_light)
    c.rect(b.x, top - header_h, b.w, header_h, stroke=0, fill=1)
    if zebra:
        c.setFillColor(CREAM)
        for i in range(1, n_rows, 2):
            c.rect(b.x, ys[i + 1], b.w, row_h, stroke=0, fill=1)
    for i, h in enumerate(headers):
        if not h:
            continue
        cw = xs[i + 1] - xs[i]
        size = header_size
        while label_w(h, size, 1.0) > cw - 6 and size > 5:
            size -= 0.25
        p.text((xs[i] + xs[i + 1]) / 2, top - header_h / 2 - size * 0.36, h.upper(),
               SANS_BOLD, size, INK, "center", spacing=1.0)
    c.setLineWidth(0.6)
    c.setStrokeColor(vcolor)
    for x in xs[1:-1]:
        c.line(x, bottom, x, top)
    c.setStrokeColor(LINE)
    for y in ys:
        c.line(b.x, y, b.right, y)
    c.line(b.x, top, b.right, top)
    c.line(b.x, bottom, b.x, top)
    c.line(b.right, bottom, b.right, top)
    return xs, ys


def note(p, x, y, s, align="left", size=8):
    p.text(x, y, s, ITALIC, size, MUTED, align)


# ---- pages --------------------------------------------------------------------
def cover(p):
    p.cover(TITLE, "track the small things that make you feel well", [
        "Monthly & Weekly Habit Trackers",
        "30-Day Habit Challenge",
        "Mood Year in Pixels  ·  Mood & Energy Tracker",
        "Sleep Tracker  ·  Water Intake Tracker",
        "Workout Log  ·  Self-Care Checklist & Ideas",
        "Daily Wellness Journal  ·  Weekly Reflection",
        "Cycle Tracker",
    ])


def monthly_habits(p):
    p.header("Monthly Habit Tracker", "Small steps, every day", right_fields=("MONTH", "YEAR"))
    b = p.body
    name_w = 138
    cw = (b.w - name_w) / 32           # 31 days + total column
    header_h, rh = 22, 23
    n = int((b.h * 0.66 - header_h) / rh)
    gh = header_h + n * rh
    grid_b = Box(b.x, b.top - gh, b.w, gh)
    widths = [name_w] + [cw] * 32
    headers = ["Habit"] + [str(i) for i in range(1, 32)] + [""]
    xs, ys = table(p, grid_b, widths, headers, n, header_h, rh, zebra=True, header_size=6.5)
    # emphasise the totals column
    c = p.c
    c.setFillColor(p.accent_light)
    c.rect(xs[-2], ys[-1], xs[-1] - xs[-2], ys[0] - ys[-1], stroke=0, fill=1)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.6)
    for y in ys:
        c.line(xs[-2], y, xs[-1], y)
    c.line(xs[-2], ys[-1], xs[-2], grid_b.top)
    c.line(xs[-1], ys[-1], xs[-1], grid_b.top)
    p.text((xs[-2] + xs[-1]) / 2, grid_b.top - header_h / 2 - 2.4, "#", SANS_BOLD, 7, INK, "center")
    note(p, b.x, ys[-1] - 14, "Color in a square each day you complete a habit. Total your days in the last column.")
    rest = Box(b.x, b.y, b.w, ys[-1] - 26 - b.y)
    l, r = rest.split_h(0.5)
    p.lines(p.panel(l, "Goals this month"), 20)
    p.lines(p.panel(r, "Reflection"), 20)
    p.finish()


def weekly_habits(p):
    p.header("Weekly Habit Tracker", "Consistency over perfection", right_fields=("WEEK OF",))
    b = p.body
    habit_w = b.w * 0.34
    goal_w = 56
    dw = (b.w - habit_w - goal_w) / 7
    header_h, rh = 24, 29
    n = int((b.h * 0.6 - header_h) / rh)
    gh = header_h + n * rh
    xs, ys = table(p, Box(b.x, b.top - gh, b.w, gh), [habit_w] + [dw] * 7 + [goal_w],
                   ["Habit"] + WEEKDAYS + ["Done"], n, header_h, rh, vcolor=LINE_SOFT)
    c = p.c
    r = min(7.5, rh * 0.28)
    for i in range(n):
        cy = (ys[i] + ys[i + 1]) / 2
        for d in range(7):
            c.setStrokeColor(p.accent)
            c.setLineWidth(0.8)
            c.circle((xs[d + 1] + xs[d + 2]) / 2, cy, r, stroke=1, fill=0)
        p.text((xs[-2] + xs[-1]) / 2, cy - 3, "/ 7", SANS_LIGHT, 9, MUTED, "center")
    rest = Box(b.x, b.y, b.w, ys[-1] - 14 - b.y)
    cols = rest.cols(3)
    p.lines(p.panel(cols[0], "This week's focus"), 20)
    p.checklist(p.panel(cols[1], "Little wins"), 20)
    p.lines(p.panel(cols[2], "Notes"), 20)
    p.finish()


def challenge_page(p):
    p.header("30-Day Habit Challenge", "One habit, thirty days", right_fields=())
    for blk in p.body.rows(2, gap=16):
        inner = p.panel(blk, None)
        c = p.c
        # fields
        y = inner.top - 12
        sd = (inner.w - 8) * 0.3
        field(p, inner.x + 4, y, inner.w - 8 - sd - 20, "My challenge")
        field(p, inner.right - 4 - sd, y, sd, "Start date")
        y -= 24
        half = (inner.w - 8 - 20) / 2
        field(p, inner.x + 4, y, half, "Why it matters")
        field(p, inner.x + 4 + half + 20, y, half, "Reward")
        # circles 10 x 3
        cols, rows = 10, 3
        area_top = y - 14
        area_bot = inner.y + 22
        slot_w = (inner.w - 8) / cols
        slot_h = (area_top - area_bot) / rows
        rr = min(slot_w, slot_h) * 0.36
        for j in range(rows):
            for i in range(cols):
                k = j * cols + i + 1
                cx = inner.x + 4 + slot_w * (i + 0.5)
                cy = area_top - slot_h * (j + 0.5)
                c.setStrokeColor(p.accent)
                c.setLineWidth(0.9)
                c.circle(cx, cy, rr, stroke=1, fill=0)
                p.text(cx, cy - 3.6, str(k), SERIF, 11, LINE, "center")
        note(p, inner.x + inner.w / 2, inner.y + 4,
             "Color in a circle for every day you show up. Missed one? Simply begin again.", "center")
    p.finish()


def year_grid(p, b, legend_title, legend_items, legend_w, note_text, extra_lines=True):
    """12 months x 31 days grid on the left, legend on the right."""
    c = p.c
    gb, lb = b.split_h((b.w - legend_w - GUTTER) / (b.w - GUTTER))
    day_w = 22
    mw = (gb.w - day_w) / 12
    header_h = 20
    rh = (gb.h - header_h) / 31
    xs, ys = table(p, gb, [day_w] + [mw] * 12, [""] + MONTHS, 31, header_h, rh, header_size=6.5)
    for d in range(31):
        cy = (ys[d] + ys[d + 1]) / 2
        p.text((xs[0] + xs[1]) / 2, cy - 2.4, str(d + 1), SANS_BOLD, 6.5, MUTED, "center")
    # shade days that don't exist
    c.setFillColor(LINE_SOFT)
    for m, nd in enumerate(MONTH_DAYS):
        for d in range(nd, 31):
            c.rect(xs[m + 1] + 0.3, ys[d + 1] + 0.3, mw - 0.6, rh - 0.6, stroke=0, fill=1)
    # legend
    inner = p.panel(lb, legend_title)
    y = inner.top - 10
    sq = 16
    for it in legend_items:
        c.setStrokeColor(LINE)
        c.setLineWidth(0.8)
        c.roundRect(inner.x, y - sq + 4, sq, sq, 3, stroke=1, fill=0)
        p.text(inner.x + sq + 8, y - sq / 2 + 1, it, SANS, 9, INK)
        y -= sq + 12
    # blank legend slots
    for _ in range(2):
        c.setStrokeColor(LINE)
        c.roundRect(inner.x, y - sq + 4, sq, sq, 3, stroke=1, fill=0)
        c.line(inner.x + sq + 8, y - sq / 2, inner.right, y - sq / 2)
        y -= sq + 12
    y -= 6
    c.setStrokeColor(LINE_SOFT)
    c.line(inner.x, y, inner.right, y)
    y -= 14
    # wrap note text
    words, line, lines = note_text.split(), "", []
    for w in words:
        t = (line + " " + w).strip()
        if stringWidth(t, ITALIC, 8) > inner.w:
            lines.append(line)
            line = w
        else:
            line = t
    lines.append(line)
    for ln in lines:
        note(p, inner.x, y, ln)
        y -= 11
    if extra_lines:
        y -= 10
        p.label(inner.x, y, "Notes", p.accent)
        p.lines(Box(inner.x, inner.y, inner.w, y - 4 - inner.y), 20)
    return xs, ys


def year_in_pixels(p):
    p.header("Mood Year in Pixels", "One little square a day", right_fields=("YEAR",))
    year_grid(p, p.body, "Mood key",
              ["Joyful", "Calm", "Content", "Productive", "Tired", "Anxious", "Sad", "Frustrated"],
              128, "Choose a color for each mood, color the swatch, then fill in one square each day.")
    p.finish()


def mood_energy(p):
    p.header("Mood & Energy Tracker", "Notice your rhythms", right_fields=("MONTH", "YEAR"))
    b = p.body
    c = p.c
    lab_w = 34
    dw = (b.w - lab_w) / 31
    header_h = 18
    rh = min(30, b.h / 26)

    def chart(top, title, row_labels):
        p.label(b.x, top - 8, title, p.accent)
        gh = header_h + 5 * rh
        gb = Box(b.x, top - 18 - gh, b.w, gh)
        xs, ys = table(p, gb, [lab_w] + [dw] * 31, [""] + [str(i) for i in range(1, 32)], 5,
                       header_h, rh, vcolor=LINE_SOFT, header_size=6)
        # dot guides at the centre of each cell
        c.setFillColor(LINE)
        for i in range(5):
            cy = (ys[i] + ys[i + 1]) / 2
            for d in range(31):
                c.circle((xs[d + 1] + xs[d + 2]) / 2, cy, 0.7, stroke=0, fill=1)
            row_labels(i, (xs[0] + xs[1]) / 2, cy)
        return gb.y

    def mood_lab(i, x, y):
        face(p, x, y, min(8.5, rh * 0.36), 4 - i)

    def energy_lab(i, x, y):
        lvl = 5 - i
        bw, bh = 16, 8
        bx = x - bw / 2 - 1
        c.setStrokeColor(p.accent)
        c.setLineWidth(0.8)
        c.roundRect(bx, y - bh / 2, bw, bh, 1.5, stroke=1, fill=0)
        c.setFillColor(p.accent)
        c.rect(bx + bw, y - 1.6, 1.8, 3.2, stroke=0, fill=1)
        seg = (bw - 3) / 5
        for s in range(lvl):
            c.rect(bx + 1.5 + s * seg + 0.3, y - bh / 2 + 1.5, seg - 0.6, bh - 3, stroke=0, fill=1)

    y = chart(b.top, "Mood", mood_lab)
    y = chart(y - 20, "Energy", energy_lab)
    note(p, b.x, y - 14, "Place a dot in each day's column and join the dots to see how you've been feeling.")
    rest = Box(b.x, b.y, b.w, y - 28 - b.y)
    top, bot = rest.split_v(0.52)
    l, r = top.split_h(0.5)
    p.lines(p.panel(l, "What lifted me"), 20)
    p.lines(p.panel(r, "What drained me"), 20)
    p.lines(p.panel(bot, "Patterns I noticed"), 20)
    p.finish()


def sleep_tracker(p):
    p.header("Sleep Tracker", "Rest is productive too", right_fields=("MONTH", "YEAR"))
    b = p.body
    c = p.c
    hours = ["8P", "9P", "10P", "11P", "12A", "1A", "2A", "3A", "4A", "5A", "6A", "7A", "8A", "9A"]
    day_w, tot_w = 24, 40
    r, gap = 3.6, 3.2
    q_w = 5 * 2 * r + 4 * gap + 14
    hw = (b.w - day_w - tot_w - q_w) / len(hours)
    header_h = 22
    rh = (b.h - header_h - 34) / 31
    gb = Box(b.x, b.y + 34, b.w, b.h - 34)
    xs, ys = table(p, gb, [day_w] + [hw] * len(hours) + [tot_w, q_w],
                   ["Day"] + hours + ["Hrs", "Quality"], 31, header_h, rh, vcolor=LINE, header_size=6.5)
    # half-hour guides
    c.setStrokeColor(LINE_SOFT)
    c.setLineWidth(0.5)
    c.setDash(1, 2)
    for i in range(len(hours)):
        x = (xs[i + 1] + xs[i + 2]) / 2
        c.line(x, ys[-1], x, ys[0])
    c.setDash()
    for d in range(31):
        cy = (ys[d] + ys[d + 1]) / 2
        p.text((xs[0] + xs[1]) / 2, cy - 2.4, str(d + 1), SANS_BOLD, 6.5, MUTED, "center")
        scale_row(p, xs[-2] + 7, cy, 5, r, gap, numbers=False)
    note(p, b.x, b.y + 16, "Shade the hours you slept, total them up and rate how rested you felt (1–5 circles).")
    field(p, b.x + b.w * 0.62, b.y + 16, b.w * 0.38, "Sleep goal")
    p.finish()


def water_tracker(p):
    p.header("Water Intake Tracker", "Sip, sip, hooray", right_fields=("MONTH", "YEAR"))
    b = p.body
    c = p.c
    strip_h = 34
    inner = p.panel(Box(b.x, b.top - strip_h, b.w, strip_h), None, fill=CREAM, stroke=CREAM)
    third = (inner.w - 40) / 3
    yy = inner.y + inner.h / 2 - 3
    field(p, inner.x + 4, yy, third, "Daily goal")
    field(p, inner.x + 24 + third, yy, third, "1 glass =")
    field(p, inner.x + 44 + 2 * third, yy, third - 8, "Monthly avg")
    area = Box(b.x, b.y, b.w, b.h - strip_h - 16)
    halves = area.cols(2, gap=24)
    n_g = 8
    for hi, col in enumerate(halves):
        days = range(1, 17) if hi == 0 else range(17, 32)
        rh = col.h / 16
        gw = min(15, (col.w - 34) / n_g * 0.62)
        gh = min(rh * 0.6, gw * 1.3)
        step = (col.w - 34) / n_g
        for k, d in enumerate(days):
            top = col.top - k * rh
            cy = top - rh / 2
            c.setFillColor(p.accent_light)
            c.circle(col.x + 11, cy, 10, stroke=0, fill=1)
            p.text(col.x + 11, cy - 3, str(d), SANS_BOLD, 8, INK, "center")
            for g in range(n_g):
                gx = col.x + 34 + g * step + (step - gw) / 2
                glass(p, gx, cy - gh / 2, gw, gh)
            c.setStrokeColor(LINE_SOFT)
            c.setLineWidth(0.6)
            if k < 15:
                c.line(col.x, top - rh, col.right, top - rh)
        if hi == 1:
            cy = col.top - 15.5 * rh
            note(p, col.x + 4, cy - 3, "Color in a glass for every one you drink.")
    p.finish()


def workout_log(p):
    p.header("Workout Log", "Move in a way that feels good", right_fields=("DATE", "DAY"))
    b = p.body
    c = p.c
    # session details
    det_h = 60
    inner = p.panel(Box(b.x, b.top - det_h, b.w, det_h), "Session")
    w3 = (inner.w - 40) / 3
    y = inner.y + 6
    field(p, inner.x, y, w3, "Type")
    field(p, inner.x + w3 + 20, y, w3, "Duration")
    field(p, inner.x + 2 * w3 + 40, y, w3, "Location")
    # strength table
    y = b.top - det_h - 18
    p.label(b.x, y - 8, "Strength", p.accent)
    bottom_h, rh, n_c = 150, 22, 4
    avail = b.h - det_h - bottom_h - GUTTER
    n_s = min(12, int((avail - 18 - 22 - 26 - 18 - 22 - n_c * rh) / rh))
    gh = 22 + n_s * rh
    xs, ys = table(p, Box(b.x, y - 18 - gh, b.w, gh), [None, 62, 62, 62, 62, b.w * 0.2],
                   ["Exercise", "Set 1", "Set 2", "Set 3", "Set 4", "Notes"], n_s, 22, rh, vcolor=LINE)
    note(p, b.x, ys[-1] - 13, "Write reps × weight in each set column.")
    # cardio table
    y = ys[-1] - 26
    p.label(b.x, y - 8, "Cardio", p.accent)
    gh = 22 + n_c * rh
    xs, ys = table(p, Box(b.x, y - 18 - gh, b.w, gh), [None, 70, 70, 90, b.w * 0.2],
                   ["Activity", "Time", "Distance", "Intensity", "Notes"], n_c, 22, rh, vcolor=LINE)
    # bottom: how I felt + notes
    rest = Box(b.x, b.y, b.w, bottom_h)
    l, r = rest.split_h(0.42)
    inner = p.panel(l, "How I felt")
    fr = 9.5
    span = inner.w - 50
    for i, lab in enumerate(["Before", "After"]):
        cy = inner.top - 13 - i * 28
        p.label(inner.x, cy - 3, lab, size=7)
        for m in range(5):
            face(p, inner.x + 50 + span / 5 * (m + 0.5), cy, fr, m)
    field(p, inner.x, inner.top - 72, inner.w, "Water")
    field(p, inner.x, inner.top - 98, inner.w, "Stretch")
    p.lines(p.panel(r, "Notes & progress"), 20)
    p.finish()


def self_care(p):
    p.header("Self-Care Checklist", "Fill your cup first", right_fields=("MONTH",))
    b = p.body
    top, bot = b.split_v(0.62)
    cats = {
        "Mind": ["Read for 20 minutes", "Journal your thoughts", "Do a puzzle or crossword",
                 "Learn something new", "Take a social media break", "Listen to a podcast",
                 "Write a to-do list", "Plan something fun"],
        "Body": ["Go for a gentle walk", "Stretch or do yoga", "Drink a full glass of water",
                 "Take a warm bath", "Cook a nourishing meal", "Get an early night",
                 "Dance to a favorite song", "Spend time outside"],
        "Heart": ["Call a friend or family member", "Write a thank-you note", "Watch a comfort film",
                  "Say no without guilt", "Write three gratitudes", "Hug someone you love",
                  "Do something kind", "Laugh out loud"],
        "Home": ["Make your bed", "Declutter one drawer", "Light a candle", "Buy fresh flowers",
                 "Change the bedsheets", "Open the windows", "Tidy for 10 minutes",
                 "Make a cozy corner"],
    }
    rows = top.rows(2)
    boxes = rows[0].cols(2) + rows[1].cols(2)
    for bx, (name, items) in zip(boxes, cats.items()):
        inner = p.panel(bx, name)
        sp = min(20, inner.h / len(items))
        idea_list(p, inner, items, sp)
    l, r = bot.split_h(0.5)
    p.checklist(p.panel(l, "My go-to self-care"), 20)
    p.lines(p.panel(r, "Ideas to try this month"), 20)
    p.finish()


def daily_journal(p):
    p.header("Daily Wellness Journal", "Be gentle with yourself", right_fields=("DATE", "DAY"))
    b = p.body
    c = p.c
    # check-in strip
    strip_h = 78
    strip = Box(b.x, b.top - strip_h, b.w, strip_h)
    cols = strip.cols(3)
    inner = p.panel(cols[0], "Mood")
    fr = min(9.5, inner.w / 10 - 1.5)
    for m in range(5):
        face(p, inner.x + inner.w / 5 * (m + 0.5), inner.y + inner.h / 2 - 2, fr, m)
    inner = p.panel(cols[1], "Water")
    gw = min(12, inner.w / 8 * 0.62)
    gh = gw * 1.35
    step = inner.w / 8
    for g in range(8):
        glass(p, inner.x + g * step + (step - gw) / 2, inner.y + inner.h / 2 - 2 - gh / 2, gw, gh)
    inner = p.panel(cols[2], "Energy  ·  Sleep")
    r = 6.5
    gap = (inner.w * 0.55 - 10 * r) / 4
    cy = inner.y + inner.h / 2 - 2
    scale_row(p, inner.x, cy, 5, r, gap)
    field(p, inner.x + inner.w * 0.62, cy - 3, inner.w * 0.38, "Hrs")

    rest = Box(b.x, b.y, b.w, strip.y - GUTTER - b.y)
    r1, r2, r3 = rest.rows(3)
    l, r_ = r1.split_h(0.58)
    inner = p.panel(l, "Today I'm grateful for")
    numbered_lines(p, Box(inner.x, inner.y, inner.w, inner.h + 6), 3, (inner.h + 6) / 3)
    inner = p.panel(r_, "Affirmation", fill=CREAM, stroke=CREAM)
    p.lines(inner, 24)
    l, r_ = r2.split_h(0.58)
    p.lines(p.panel(l, "Today's wins"), 22)
    p.checklist(p.panel(r_, "Self-care & movement"), 22)
    p.lines(p.panel(r3, "Thoughts & reflections"), 22)
    p.finish()


def weekly_reflection(p):
    p.header("Weekly Reflection", "Look back, move forward", right_fields=("WEEK OF",))
    b = p.body
    cats = ["Sleep", "Mood", "Energy", "Movement", "Nutrition", "Hydration", "Self-care", "Calm"]
    row_sp = 21
    rate_h = 16 + 20 + len(cats) * row_sp
    inner = p.panel(Box(b.x, b.top - rate_h, b.w, rate_h), "Rate your week  (1 – 10)")
    lab_w = 90
    r = 7.5
    span = inner.w - lab_w
    gap = (span - 20 * r) / 9
    for i, cat in enumerate(cats):
        cy = inner.top - 12 - i * row_sp
        p.text(inner.x, cy - 3, cat, SANS, 9, INK)
        scale_row(p, inner.x + lab_w, cy, 10, r, gap)
    rest = Box(b.x, b.y, b.w, b.top - rate_h - GUTTER - b.y)
    word_h = 36
    grid = Box(rest.x, rest.y + word_h + GUTTER, rest.w, rest.h - word_h - GUTTER)
    rows = grid.rows(2)
    names = ["What went well", "What felt hard", "What I learned", "Next week's focus"]
    for bx, nm in zip(rows[0].cols(2) + rows[1].cols(2), names):
        p.lines(p.panel(bx, nm), 20)
    inner = p.panel(Box(rest.x, rest.y, rest.w, word_h), None, fill=CREAM, stroke=CREAM)
    field(p, inner.x + 4, inner.y + inner.h / 2 - 3, inner.w - 8, "This week in one word")
    p.finish()


def cycle_tracker(p):
    p.header("Cycle Tracker", "Know your body", right_fields=("YEAR",))
    b = p.body
    log_h = 150
    gb = Box(b.x, b.y + log_h + GUTTER, b.w, b.h - log_h - GUTTER)
    year_grid(p, gb, "Key",
              ["Light flow", "Medium flow", "Heavy flow", "Spotting", "Cramps", "Low energy"],
              128, "Color each swatch, then mark each day in the grid.")
    lb = Box(b.x, b.y, b.w, log_h)
    p.label(lb.x, lb.top - 8, "Cycle log", p.accent)
    tb = Box(lb.x, lb.y, lb.w, lb.h - 18)
    table(p, tb, [88, 88, 84, 84, None],
          ["Start date", "End date", "Period length", "Cycle length", "Notes & symptoms"], 5, 22)
    p.finish()


def draw(p):
    cover(p)
    monthly_habits(p)
    weekly_habits(p)
    challenge_page(p)
    year_in_pixels(p)
    mood_energy(p)
    sleep_tracker(p)
    water_tracker(p)
    workout_log(p)
    self_care(p)
    daily_journal(p)
    weekly_reflection(p)
    cycle_tracker(p)


if __name__ == "__main__":
    build(SLUG, TITLE, draw, accent=2)
