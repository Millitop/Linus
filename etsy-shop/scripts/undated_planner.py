"""Undated Daily & Weekly Planner — Linnea Paper Co.

Run from the etsy-shop folder:  python scripts/undated_planner.py
Writes products/undated-planner/undated-planner-{letter,a4}.pdf
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brand import *  # noqa: E402,F403

SLUG = "undated-planner"
TITLE = "Undated Daily & Weekly Planner"

DAYS_MON = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAYS_SUN = ["Sunday"] + DAYS_MON[:6]
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


# ---- local helpers ---------------------------------------------------------------
def section(p, b: Box, title, color=None):
    """Border-less section: label + short accent rule. Returns content box."""
    p.label(b.x, b.top - 7, title, color or p.accent)
    return Box(b.x, b.y, b.w, b.h - 14)


def numbered_lines(p, b: Box, n, spacing=24):
    """Numbered writing lines (1, 2, 3...) with a serif numeral."""
    c = p.c
    y = b.top - spacing
    for i in range(n):
        p.text(b.x + 2, y + 3, str(i + 1), SERIF, 13, p.accent)
        c.setStrokeColor(LINE)
        c.setLineWidth(0.6)
        c.line(b.x + 18, y, b.right, y)
        y -= spacing


def date_chip(p, x, y, w=16, h=13):
    """Tiny filled rounded box for writing a date number (top-left of cells)."""
    c = p.c
    c.setFillColor(p.accent_light)
    c.roundRect(x, y - h, w, h, 3, stroke=0, fill=1)


# ---- pages ---------------------------------------------------------------------------
def year_overview(p):
    p.header("Year at a Glance", "Goals & intentions", right_fields=("YEAR",))
    b = p.body
    top_h = 84
    top = Box(b.x, b.top - top_h, b.w, top_h)
    word, vision = top.split_h(0.36)
    inner = p.panel(word, "Word of the year", fill=CREAM, stroke=CREAM)
    p.lines(Box(inner.x, inner.y + 2, inner.w, inner.h), spacing=inner.h - 4)
    inner = p.panel(vision, "This year I want to feel")
    p.lines(inner, 20)

    rest = Box(b.x, b.y, b.w, b.h - top_h - GUTTER)
    goals_area, months_area = rest.split_v(0.44)
    areas = ["Health & body", "Work & career", "Money", "Relationships", "Personal growth", "Fun & adventure"]
    rows = goals_area.rows(2, gap=10)
    i = 0
    for r in rows:
        for cb in r.cols(3, gap=10):
            p.checklist(p.panel(cb, areas[i]), 20)
            i += 1

    p.label(months_area.x, months_area.top - 7, "Monthly focus", p.accent)
    m = Box(months_area.x, months_area.y, months_area.w, months_area.h - 18)
    i = 0
    for r in m.rows(3, gap=10):
        for cb in r.cols(4, gap=10):
            inner = p.title_band(cb, MONTHS[i], h=18)
            p.lines(Box(inner.x + 4, inner.y + 2, inner.w - 8, inner.h - 2), 19)
            i += 1
    p.finish()


def monthly_calendar(p, days, start_label):
    p.header("Monthly Calendar", start_label, right_fields=("MONTH", "YEAR"))
    b = p.body
    cal, bottom = b.split_v(0.80)
    hh = 22
    xs, ys = p.grid(cal, 7, 6, header_fill=p.accent_light, header_h=hh)
    c = p.c
    # rounded look: overdraw outer border
    for i, d in enumerate(days):
        cx = (xs[i] + xs[i + 1]) / 2
        p.label(cx, cal.top - hh + 8, d[:3], INK, align="center")
    for j in range(6):
        for i in range(7):
            date_chip(p, xs[i] + 5, ys[j + 1] - 5)
    # weekend tint: none (keeps ink low); bottom area
    left, right = bottom.split_h(0.5)
    p.lines(p.panel(left, "Focus this month"), 20)
    p.checklist(p.panel(right, "Don't forget"), 20)
    p.finish()


def monthly_review(p):
    p.header("Monthly Goals", "Plan · track · reflect", right_fields=("MONTH", "YEAR"))
    b = p.body
    top_h = b.h * 0.33
    top = Box(b.x, b.top - top_h, b.w, top_h)
    l, r = top.split_h(0.5)
    p.checklist(p.panel(l, "Goals this month"), 21)
    p.lines(p.panel(r, "Important dates"), 21)

    # habit tracker
    hab_h = 158
    hab = Box(b.x, top.y - GUTTER - hab_h, b.w, hab_h)
    inner = p.panel(hab, "Habit tracker")
    name_w = 104
    n_rows = 5
    head = 14
    rh = (inner.h - head) / n_rows
    cell = (inner.w - name_w) / 31
    rad = min(4.2, cell / 2 - 1.6)
    c = p.c
    for d in range(31):
        cx = inner.x + name_w + cell * (d + 0.5)
        p.text(cx, inner.top - 9, str(d + 1), SANS, 6.5, MUTED, "center")
    for k in range(n_rows):
        cy = inner.top - head - rh * (k + 0.5)
        c.setStrokeColor(LINE)
        c.setLineWidth(0.6)
        c.line(inner.x, cy - 6, inner.x + name_w - 12, cy - 6)
        c.setStrokeColor(p.accent)
        c.setLineWidth(0.7)
        for d in range(31):
            c.circle(inner.x + name_w + cell * (d + 0.5), cy, rad, stroke=1, fill=0)

    # reflection
    refl = Box(b.x, b.y, b.w, hab.y - GUTTER - b.y)
    rows = refl.rows(2, gap=GUTTER)
    a, bb = rows[0].split_h(0.5)
    p.lines(p.panel(a, "Wins & highlights"), 21)
    p.lines(p.panel(bb, "What I learned"), 21)
    a, bb = rows[1].split_h(0.5)
    inner = p.panel(a, "How did this month feel?")
    # rating circles + lines
    p.circle_row(inner.x + 2, inner.top - 10, 5, r=7, gap=10)
    for k in range(5):
        p.text(inner.x + 2 + 7 + k * 24, inner.top - 12.5, str(k + 1), SANS, 7, MUTED, "center")
    p.lines(Box(inner.x, inner.y, inner.w, inner.h - 22), 21)
    p.checklist(p.panel(bb, "Next month I will"), 21)
    p.finish()


def weekly_vertical(p):
    p.header("Weekly Plan", "One week at a time", right_fields=("WEEK OF", "MONTH"))
    b = p.body
    left, right = b.split_h(0.64)
    c = p.c
    lab_w = 54
    for d, row in zip(DAYS_MON, left.rows(7, gap=8)):
        c.setFillColor(p.accent_light)
        c.roundRect(row.x, row.y, lab_w, row.h, 6, stroke=0, fill=1)
        p.label(row.x + lab_w / 2, row.y + row.h / 2 + 4, d[:3], INK, size=8, align="center")
        # date line under day name
        c.setStrokeColor(p.accent)
        c.setLineWidth(0.6)
        c.line(row.x + lab_w / 2 - 12, row.y + row.h / 2 - 10, row.x + lab_w / 2 + 12, row.y + row.h / 2 - 10)
        lb = Box(row.x + lab_w + 10, row.y, row.w - lab_w - 10, row.h)
        sp = (row.h - 2) / 4
        p.lines(lb, sp, start_offset=sp)

    focus_h = 92
    focus = Box(right.x, right.top - focus_h, right.w, focus_h)
    p.lines(p.panel(focus, "Weekly focus", fill=CREAM, stroke=CREAM), 20)
    rest = Box(right.x, right.y, right.w, right.h - focus_h - GUTTER)
    pri_h = 3 * 26 + 42
    pri = Box(rest.x, rest.top - pri_h, rest.w, pri_h)
    todo, notes = Box(rest.x, rest.y, rest.w, rest.h - pri_h - GUTTER).split_v(0.52)
    numbered_lines(p, p.panel(pri, "Top priorities"), 3, spacing=26)
    p.checklist(p.panel(todo, "To do"), 20)
    p.dot_grid(p.panel(notes, "Notes"), 14)
    p.finish()


def weekly_horizontal(p):
    p.header("Week Ahead", "Weekly overview", right_fields=("WEEK OF", "MONTH"))
    b = p.body
    strip_h = 54
    strip = Box(b.x, b.top - strip_h, b.w, strip_h)
    s1, s2 = strip.split_h(0.5)
    inner = p.panel(s1, "This week's focus", fill=CREAM, stroke=CREAM)
    p.lines(Box(inner.x, inner.y + 2, inner.w, inner.h), inner.h - 4)
    inner = p.panel(s2, "Water / habit of the week", fill=CREAM, stroke=CREAM)
    nd = 7
    r = 6.5
    gap = (inner.w - nd * 2 * r) / (nd - 1)
    gap = min(gap, 22)
    cy = inner.y + inner.h / 2 - 1
    for k in range(nd):
        cx = inner.x + r + k * (2 * r + gap)
        p.c.setStrokeColor(p.accent)
        p.c.setLineWidth(0.8)
        p.c.setFillColor(PAPER)
        p.c.circle(cx, cy, r, stroke=1, fill=1)
        p.text(cx, cy - 2.3, DAYS_MON[k][0], SANS_BOLD, 6.5, MUTED, "center")

    rest = Box(b.x, b.y, b.w, b.h - strip_h - GUTTER)
    rows = rest.rows(2, gap=GUTTER)
    cells = rows[0].cols(4, gap=10) + rows[1].cols(4, gap=10)
    for d, cb in zip(DAYS_MON, cells[:7]):
        inner = p.title_band(cb, d)
        p.checklist(Box(inner.x + 2, inner.y, inner.w - 4, inner.h), 20)
    last = cells[7]
    p.lines(p.panel(last, "Notes", fill=None), 20)
    p.finish()


def daily_planner(p):
    p.header("Daily Plan", "Make today count", right_fields=("DATE", "DAY"))
    b = p.body
    left, right = b.split_h(0.54)
    c = p.c
    # schedule
    inner = p.panel(left, "Schedule")
    hours = ["6 AM", "7", "8", "9", "10", "11", "12 PM", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10 PM"]
    n = len(hours)
    sh = inner.h / n
    tx = inner.x + 40
    for i, h in enumerate(hours):
        yt = inner.top - i * sh
        p.text(inner.x + 30, yt - 11, h, SANS_BOLD if h.endswith("M") else SANS, 8, MUTED, "right")
        c.setStrokeColor(LINE)
        c.setLineWidth(0.6)
        c.line(inner.x, yt, inner.right, yt)
        c.setStrokeColor(LINE_SOFT)
        c.setLineWidth(0.5)
        c.setDash(1, 2.5)
        c.line(tx, yt - sh / 2, inner.right, yt - sh / 2)
        c.setDash()
    c.setStrokeColor(LINE)
    c.setLineWidth(0.6)
    c.line(inner.x, inner.y, inner.right, inner.y)
    c.setStrokeColor(p.accent_light)
    c.setLineWidth(1)
    c.line(tx - 4, inner.top, tx - 4, inner.y)

    # right column
    top3_h = 116
    top3 = Box(right.x, right.top - top3_h, right.w, top3_h)
    numbered_lines(p, p.panel(top3, "Top 3 today", fill=CREAM, stroke=CREAM), 3, spacing=25)
    water_h = 50
    grat_h = 104
    notes_h = 104
    y = right.y
    notes = Box(right.x, y, right.w, notes_h); y += notes_h + GUTTER
    grat = Box(right.x, y, right.w, grat_h); y += grat_h + GUTTER
    water = Box(right.x, y, right.w, water_h); y += water_h + GUTTER
    todo = Box(right.x, y, right.w, top3.y - GUTTER - y)
    p.checklist(p.panel(todo, "To do"), 21)
    inner = p.panel(water, "Water")
    p.circle_row(inner.x + 1, inner.y + inner.h / 2 + 1, 8, r=6, gap=(inner.w - 2 - 8 * 12) / 7)
    p.lines(p.panel(grat, "Grateful for"), 21)
    p.lines(p.panel(notes, "Notes"), 21)
    p.finish()


def daily_minimal(p):
    p.header("Today", "Simple daily page", right_fields=("DATE", "DAY"))
    b = p.body
    c = p.c
    # intention
    ih = 46
    inten = Box(b.x, b.top - ih, b.w, ih)
    inner = section(p, inten, "Today's intention")
    p.lines(inner, inner.h - 2)
    mid_h = b.h * 0.60
    mid = Box(b.x, inten.y - 22 - mid_h, b.w, mid_h)
    l, r = mid.split_h(0.5, gap=28)
    p.checklist(section(p, l, "To do"), 22)
    parts = r.rows(3, gap=16)
    for name, pb in zip(["Morning", "Afternoon", "Evening"], parts):
        p.lines(section(p, pb, name), 22)
    bottom = Box(b.x, b.y, b.w, mid.y - 24 - b.y)
    l, r = bottom.split_h(0.5, gap=28)
    p.lines(section(p, l, "Good things today"), 22)
    p.lines(section(p, r, "Tomorrow"), 22)
    # thin vertical divider between columns
    c.setStrokeColor(LINE_SOFT)
    c.setLineWidth(0.6)
    xm = b.x + b.w / 2
    c.line(xm, mid.top, xm, b.y)
    c.line(b.x, mid.y - 10, b.right, mid.y - 10)
    p.finish()


def todo_list(p):
    p.header("To-Do List", "Get it out of your head", right_fields=("DATE", "LIST"))
    b = p.body
    c = p.c
    for col, title in zip(b.split_h(0.5), ["To do", "Also to do"]):
        inner = p.panel(col, title)
        sp = 22
        y = inner.top - sp
        while y >= inner.y - 0.1:
            c.setStrokeColor(p.accent)
            c.setLineWidth(0.8)
            c.roundRect(inner.x, y + 2, 8, 8, 1.5, stroke=1, fill=0)
            c.setStrokeColor(LINE)
            c.setLineWidth(0.6)
            c.line(inner.x + 14, y, inner.right, y)
            y -= sp
    p.finish()


def notes_dot(p):
    p.header("Notes", "Dot grid", right_fields=("DATE", "TOPIC"))
    inner = p.panel(p.body)
    p.dot_grid(inner.inset(4), 14, r=0.6)
    p.finish()


def notes_lined(p):
    p.header("Notes", "Lined", right_fields=("DATE", "TOPIC"))
    inner = p.panel(p.body)
    inner = Box(inner.x, inner.y, inner.w, inner.h - 6)
    p.lines(inner, 22)
    c = p.c
    c.setStrokeColor(p.accent_light)
    c.setLineWidth(1)
    c.line(inner.x + 34, p.body.top - 1, inner.x + 34, p.body.y + 1)
    p.finish()


def contacts(p):
    p.header("Contacts", "& important dates", right_fields=())
    b = p.body
    c = p.c
    con_area, dates_area = b.split_v(0.60)
    fields = ["Name", "Phone", "Email", "Address"]
    for row in con_area.rows(3, gap=10):
        for cb in row.cols(2, gap=GUTTER):
            inner = p.panel(cb)
            sp = inner.h / len(fields)
            for k, f in enumerate(fields):
                y = inner.top - (k + 1) * sp + 3
                p.label(inner.x, y + 2, f, MUTED, size=6.5)
                c.setStrokeColor(LINE)
                c.setLineWidth(0.6)
                c.line(inner.x + 52, y, inner.right, y)
    inner = p.panel(dates_area, "Birthdays & important dates")
    for col in inner.cols(2, gap=24):
        hh = 16
        p.label(col.x, col.top - 10, "Date", MUTED, size=6.5)
        p.label(col.x + 70, col.top - 10, "Occasion", MUTED, size=6.5)
        body = Box(col.x, col.y, col.w, col.h - hh)
        sp = 22
        y = body.top - sp
        while y >= body.y - 0.1:
            c.setStrokeColor(LINE)
            c.setLineWidth(0.6)
            c.line(col.x, y, col.x + 58, y)
            c.line(col.x + 70, y, col.right, y)
            y -= sp
    p.finish()


def draw(p):
    p.cover(TITLE, "undated pages to plan your days, weeks & months", [
        "Year at a glance & goals",
        "Monthly calendar · Sunday & Monday start",
        "Monthly goals & review",
        "Weekly plan · two layouts",
        "Daily planner · detailed & minimal",
        "To-do list · notes · contacts",
    ])
    year_overview(p)
    monthly_calendar(p, DAYS_SUN, "Sunday start")
    monthly_calendar(p, DAYS_MON, "Monday start")
    monthly_review(p)
    weekly_vertical(p)
    weekly_horizontal(p)
    daily_planner(p)
    daily_minimal(p)
    todo_list(p)
    notes_dot(p)
    notes_lined(p)
    contacts(p)


if __name__ == "__main__":
    build(SLUG, TITLE, draw, accent=0)
