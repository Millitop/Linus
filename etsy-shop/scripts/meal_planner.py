"""Meal Planner & Grocery List — Linnea Paper Co.

Run from /home/user/Linus/etsy-shop:  python3 scripts/meal_planner.py
Writes products/meal-planner/meal-planner-{letter,a4}.pdf
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brand import *  # noqa: E402,F403

SLUG = "meal-planner"
TITLE = "Meal Planner & Grocery List"

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAYS_SHORT = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]


# ---- local helpers -----------------------------------------------------------
def label_w(s, size=7.5, spacing=1.4):
    s = s.upper()
    return pdfmetrics.stringWidth(s, SANS_BOLD, size) + spacing * (len(s) - 1)


def field(p, x, y, w, name, size=7, color=None):
    """Spaced label followed by a fill-in line, all within width w."""
    p.label(x, y, name, color, size)
    c = p.c
    c.setStrokeColor(LINE)
    c.setLineWidth(0.6)
    c.line(x + label_w(name, size) + 6, y - 1.5, x + w, y - 1.5)


def band(p, b, title, fill, h=20, color=INK):
    """Title band over box b that returns content area under it."""
    c = p.c
    c.setFillColor(fill)
    c.roundRect(b.x, b.top - h, b.w, h, 5, stroke=0, fill=1)
    p.label(b.x + b.w / 2, b.top - h + (h - 5.5) / 2, title, color, align="center")
    return Box(b.x, b.y, b.w, b.h - h - 4)


def numbered_lines(p, b, spacing=20, color=None, start=1):
    """Writing lines with small step numbers in the margin."""
    c = p.c
    y = b.top - spacing
    n = start
    while y >= b.y - 0.1:
        p.text(b.x + 6, y + 3, f"{n}", SANS_BOLD, 7.5, color or p.accent, "center")
        c.setStrokeColor(LINE)
        c.setLineWidth(0.6)
        c.line(b.x + 16, y, b.right, y)
        y -= spacing
        n += 1
    return n - start


def dotted_lines(p, b, spacing=20, color=None):
    """Writing lines with a small bullet dot at the start."""
    c = p.c
    y = b.top - spacing
    while y >= b.y - 0.1:
        c.setFillColor(color or p.accent)
        c.circle(b.x + 3, y + 4, 1.4, stroke=0, fill=1)
        c.setStrokeColor(LINE)
        c.setLineWidth(0.6)
        c.line(b.x + 12, y, b.right, y)
        y -= spacing


def table(p, b, cols, row_h=22, fill=None, check_cols=(), check_color=None, head_h=20):
    """Minimal table: header band with labels, ruled rows, soft column dividers.
    cols = [(name, weight)]. Returns rows drawn."""
    c = p.c
    total = sum(w for _, w in cols)
    xs = [b.x]
    for _, w in cols:
        xs.append(xs[-1] + b.w * w / total)
    c.setFillColor(fill or p.accent_light)
    c.roundRect(b.x, b.top - head_h, b.w, head_h, 5, stroke=0, fill=1)
    for i, (name, _) in enumerate(cols):
        cx = (xs[i] + xs[i + 1]) / 2
        if i == 0 and len(cols) > 1:
            p.label(xs[0] + 10, b.top - head_h + (head_h - 5.5) / 2, name, INK, 7)
        else:
            p.label(cx, b.top - head_h + (head_h - 5.5) / 2, name, INK, 7, "center")
    top = b.top - head_h
    n = int((top - b.y) // row_h)
    bottom = top - n * row_h
    c.setStrokeColor(LINE_SOFT)
    c.setLineWidth(0.6)
    for x in xs[1:-1]:
        c.line(x, top - 4, x, bottom)
    c.setStrokeColor(LINE)
    for j in range(1, n + 1):
        y = top - j * row_h
        c.line(b.x, y, b.right, y)
    for ci in check_cols:
        cx = (xs[ci] + xs[ci + 1]) / 2
        for j in range(n):
            y = top - (j + 0.5) * row_h
            c.setStrokeColor(check_color or p.accent)
            c.setLineWidth(0.8)
            c.roundRect(cx - 4, y - 4, 8, 8, 1.5, stroke=1, fill=0)
    return n


def checkbox(p, x, y, s=8, color=None):
    c = p.c
    c.setStrokeColor(color or p.accent)
    c.setLineWidth(0.8)
    c.roundRect(x, y, s, s, 1.5, stroke=1, fill=0)


# ---- pages --------------------------------------------------------------------
def cover(p):
    p.cover(
        "Meal Planner & Grocery List",
        "plan the week, shop once, eat well",
        [
            "Weekly meal plans (two layouts)",
            "Grocery list by category",
            "Monthly dinner planner",
            "Recipe cards & full recipe sheet",
            "Pantry, fridge & freezer inventory",
            "Meal prep plan",
            "Go-to meals & takeout favorites",
        ],
    )


def weekly_grid(p):
    p.header("Weekly Meal Plan", "Plan it once, enjoy it all week", right_fields=("WEEK OF",))
    left, right = p.body.split_h(0.71)
    c = p.c
    meals = ["Breakfast", "Lunch", "Dinner", "Snacks"]
    day_w = 46
    head_h = 20
    gap = 4
    cols_box = Box(left.x + day_w + gap, left.y, left.w - day_w - gap, left.h)
    col_boxes = cols_box.cols(4, gap=gap)
    for i, (cb, m) in enumerate(zip(col_boxes, meals)):
        fill = TERRA_LIGHT if m == "Snacks" else p.accent_light
        c.setFillColor(fill)
        c.roundRect(cb.x, cb.top - head_h, cb.w, head_h, 5, stroke=0, fill=1)
        p.label(cb.x + cb.w / 2, cb.top - head_h + 7, m, INK, 7, "center")
    grid_top = left.top - head_h - gap
    rows = Box(left.x, left.y, left.w, grid_top - left.y).rows(7, gap=gap)
    for r, d in zip(rows, DAYS_SHORT):
        # day tab
        c.setFillColor(CREAM)
        c.roundRect(r.x, r.y, day_w, r.h, 5, stroke=0, fill=1)
        p.label(r.x + day_w / 2, r.y + r.h / 2 - 3, d, INK, 7.5, "center")
        for cb in col_boxes:
            cell = Box(cb.x, r.y, cb.w, r.h)
            c.setStrokeColor(LINE)
            c.setLineWidth(0.6)
            c.roundRect(cell.x, cell.y, cell.w, cell.h, 5, stroke=1, fill=0)
            p.lines(Box(cell.x + 6, cell.y + 6, cell.w - 12, cell.h - 8), 17, LINE_SOFT)
    gtop, gbot = right.split_v(0.74)
    inner = p.panel(gtop, "Grocery list", title_color=TERRA)
    p.checklist(Box(inner.x, inner.y, inner.w, inner.h + 4), 19.5, color=TERRA)
    inner = p.panel(gbot, "Notes")
    p.lines(Box(inner.x, inner.y, inner.w, inner.h + 4), 19.5)
    p.finish()


def weekly_list(p):
    p.header("Weekly Menu", "Simple days, good food", right_fields=("WEEK OF",))
    left, right = p.body.split_h(0.63)
    c = p.c
    rows = left.rows(7, gap=8)
    for r, d in zip(rows, DAYS):
        c.setStrokeColor(LINE)
        c.setLineWidth(0.6)
        c.roundRect(r.x, r.y, r.w, r.h, 6, stroke=1, fill=0)
        # day tab on the left
        tab_w = 34
        c.setFillColor(p.accent_light)
        c.roundRect(r.x, r.y, tab_w, r.h, 6, stroke=0, fill=1)
        c.rect(r.x + tab_w - 6, r.y, 6, r.h, stroke=0, fill=1)
        c.saveState()
        c.translate(r.x + tab_w / 2 + 2.5, r.y + r.h / 2)
        c.rotate(90)
        p.label(0, 0, d[:3], INK, 7.5, "center")
        c.restoreState()
        inner = Box(r.x + tab_w + 10, r.y + 6, r.w - tab_w - 20, r.h - 10)
        lab = [("B", "Breakfast"), ("L", "Lunch"), ("D", "Dinner"), ("S", "Snack")]
        n = len(lab)
        step = inner.h / n
        lw = label_w("Breakfast", 6.5) + 8
        for k, (_, full) in enumerate(lab):
            y = inner.top - (k + 1) * step + 3
            col = TERRA if full == "Snack" else MUTED
            p.label(inner.x, y + 1.5, full, col, 6.5)
            c.setStrokeColor(LINE)
            c.setLineWidth(0.6)
            c.line(inner.x + lw, y, inner.right, y)
    top, rest = right.split_v(0.42)
    mid, bot = rest.split_v(0.5)
    inner = p.panel(top, "Prep notes")
    p.lines(Box(inner.x, inner.y, inner.w, inner.h + 4), 19.5)
    inner = p.panel(mid, "Prep ahead", title_color=TERRA)
    p.checklist(Box(inner.x, inner.y, inner.w, inner.h + 4), 19.5, color=TERRA)
    inner = p.panel(bot, "Leftovers & extras")
    dotted_lines(p, Box(inner.x, inner.y, inner.w, inner.h + 4), 19.5)
    p.finish()


def grocery(p):
    p.header("Grocery List", "Shop once, shop smart", right_fields=("WEEK OF", "STORE"))
    cats = ["Produce", "Dairy & eggs", "Meat & fish", "Bakery", "Pantry", "Frozen", "Household", "Other"]
    colbox = p.body.cols(2)
    i = 0
    for col in colbox:
        for b in col.rows(4):
            color = TERRA if i % 2 else p.accent
            inner = p.panel(b, cats[i], title_color=color)
            p.checklist(Box(inner.x, inner.y, inner.w, inner.h + 2), 19, color=color)
            i += 1
    p.finish()


def monthly(p):
    p.header("Monthly Meal Planner", "Dinner, sorted", right_fields=("MONTH", "YEAR"))
    c = p.c
    cal, notes = p.body.split_v(0.86, gap=12)
    gap = 4
    cols = cal.cols(7, gap=gap)
    head_h = 20
    for cb, d in zip(cols, DAYS_SHORT):
        fill = TERRA_LIGHT if d in ("SAT", "SUN") else p.accent_light
        c.setFillColor(fill)
        c.roundRect(cb.x, cb.top - head_h, cb.w, head_h, 5, stroke=0, fill=1)
        p.label(cb.x + cb.w / 2, cb.top - head_h + 7, d, INK, 7, "center")
    grid = Box(cal.x, cal.y, cal.w, cal.h - head_h - gap)
    for r in grid.rows(6, gap=gap):
        for cb in cols:
            cell = Box(cb.x, r.y, cb.w, r.h)
            c.setStrokeColor(LINE)
            c.setLineWidth(0.6)
            c.roundRect(cell.x, cell.y, cell.w, cell.h, 5, stroke=1, fill=0)
            # date spot
            c.setStrokeColor(LINE_SOFT)
            c.circle(cell.x + 11, cell.top - 11, 7, stroke=1, fill=0)
            p.lines(Box(cell.x + 6, cell.y + 6, cell.w - 12, cell.h - 24), 16, LINE_SOFT, start_offset=16)
    a, b = notes.split_h(0.5)
    inner = p.panel(a, "Meals to try", title_color=TERRA)
    dotted_lines(p, Box(inner.x, inner.y, inner.w, inner.h + 4), 18, TERRA)
    inner = p.panel(b, "Notes")
    p.lines(Box(inner.x, inner.y, inner.w, inner.h + 4), 18)
    p.finish()


def recipe_card(p, b, color, light):
    c = p.c
    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    c.roundRect(b.x, b.y, b.w, b.h, 10, stroke=1, fill=0)
    # top band
    bh = 58
    c.setFillColor(light)
    p_ = c.beginPath()
    r = 10
    x0, y0, x1, y1 = b.x, b.top - bh, b.right, b.top
    p_.moveTo(x0, y0)
    p_.lineTo(x0, y1 - r)
    p_.arcTo(x0, y1 - 2 * r, x0 + 2 * r, y1, startAng=180, extent=-90)
    p_.lineTo(x1 - r, y1)
    p_.arcTo(x1 - 2 * r, y1 - 2 * r, x1, y1, startAng=90, extent=-90)
    p_.lineTo(x1, y0)
    p_.close()
    c.drawPath(p_, stroke=0, fill=1)
    pad = 16
    ix, iw = b.x + pad, b.w - 2 * pad
    field(p, ix, b.top - 24, iw, "Recipe", 7.5, INK)
    fw = (iw - 2 * 16) / 3
    for k, name in enumerate(["Serves", "Prep", "Cook"]):
        field(p, ix + k * (fw + 16), b.top - 46, fw, name, 7, INK)
    body = Box(ix, b.y + 12, iw, b.h - bh - 12 - 14)
    left, right = body.split_h(0.42, gap=22)
    p.label(left.x, left.top - 6, "Ingredients", color)
    dotted_lines(p, Box(left.x, left.y, left.w, left.h - 10), 19, color)
    p.label(right.x, right.top - 6, "Method", color)
    numbered_lines(p, Box(right.x, right.y, right.w, right.h - 10), 19, color)


def recipe_cards(p):
    p.header("Recipe Cards", "Little cards for big favorites", right_fields=())
    top, bot = p.body.split_v(0.5, gap=22)
    recipe_card(p, top, p.accent, p.accent_light)
    # dashed cut guide between cards
    c = p.c
    c.saveState()
    c.setDash(3, 3)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.5)
    y = (top.y + bot.top) / 2
    c.line(p.body.x, y, p.body.right, y)
    c.restoreState()
    recipe_card(p, bot, TERRA, TERRA_LIGHT)
    p.finish()


def recipe_sheet(p):
    p.header("Recipe", "From our kitchen", right_fields=())
    c = p.c
    b = p.body
    y = b.top - 14
    field(p, b.x, y, b.w, "Recipe name", 7.5)
    y -= 30
    gap = 18
    fw = (b.w - 3 * gap) / 4
    for k, name in enumerate(["Serves", "Prep time", "Cook time", "Oven temp"]):
        field(p, b.x + k * (fw + gap), y, fw, name, 7)
    y -= 28
    # meal type tags
    tags = ["Breakfast", "Lunch", "Dinner", "Side", "Dessert", "Snack"]
    x = b.x
    p.label(x, y, "Type", MUTED, 7)
    x += label_w("Type", 7) + 14
    for t in tags:
        checkbox(p, x, y - 1.5, 8, TERRA)
        p.text(x + 13, y, t, SANS, 8.5, INK)
        x += 13 + pdfmetrics.stringWidth(t, SANS, 8.5) + 16
    y -= 18
    rest = Box(b.x, b.y, b.w, y - b.y)
    main, bottom = rest.split_v(0.74)
    left, right = main.split_h(0.38)
    inner = p.panel(left, "Ingredients")
    dotted_lines(p, Box(inner.x, inner.y, inner.w, inner.h + 4), 20)
    inner = p.panel(right, "Method")
    numbered_lines(p, Box(inner.x, inner.y, inner.w, inner.h + 4), 20)
    nb, rb = bottom.split_h(0.66)
    inner = p.panel(nb, "Notes & swaps", title_color=TERRA)
    p.lines(Box(inner.x, inner.y, inner.w, inner.h + 4), 20)
    inner = p.panel(rb, "Rating", title_color=TERRA)
    p.circle_row(inner.x + 1, inner.top - 16, 5, r=6, gap=6, color=TERRA)
    yy = inner.top - 44
    field(p, inner.x, yy, inner.w, "Source", 7)
    field(p, inner.x, yy - 24, inner.w, "Make again?", 7)
    p.finish()


def pantry(p):
    p.header("Pantry Inventory", "Know what you have", right_fields=("UPDATED",))
    cols = p.body.cols(2)
    spec = [("Item", 3.2), ("Qty", 1), ("Best by", 1.4), ("Buy", 0.9)]
    for k, cb in enumerate(cols):
        table(p, cb, spec, row_h=22.5, fill=p.accent_light if k == 0 else TERRA_LIGHT,
              check_cols=(3,), check_color=p.accent if k == 0 else TERRA)
    p.finish()


def fridge_freezer(p):
    p.header("Fridge & Freezer", "Use it up, waste less", right_fields=("UPDATED",))
    cols = p.body.cols(2)
    spec = [("Item", 3), ("Date in", 1.3), ("Use by", 1.3)]
    for k, (cb, name) in enumerate(zip(cols, ["Fridge", "Freezer"])):
        color, light = (p.accent, p.accent_light) if k == 0 else (TERRA, TERRA_LIGHT)
        top, bot = cb.split_v(0.79)
        p.text(cb.x, cb.top - 18, name, SERIF, 18, INK)
        c = p.c
        c.setStrokeColor(color)
        c.setLineWidth(1.2)
        c.line(cb.x, cb.top - 26, cb.x + 24, cb.top - 26)
        table(p, Box(top.x, top.y, top.w, top.h - 36), spec, row_h=22.5, fill=light)
        inner = p.panel(bot, "Use first", title_color=color)
        p.checklist(Box(inner.x, inner.y, inner.w, inner.h + 4), 19.5, color=color)
    p.finish()


def meal_prep(p):
    p.header("Meal Prep Plan", "A little effort, a calmer week", right_fields=("PREP DAY",))
    c = p.c
    top, bot = p.body.split_v(0.56)
    l, r = top.split_h(0.45)
    inner = p.panel(l, "Prep day checklist")
    p.checklist(Box(inner.x, inner.y, inner.w, inner.h + 4), 20)
    inner = p.panel(r, "Cook & batch", title_color=TERRA)
    table(p, Box(inner.x, inner.y, inner.w, inner.h - 4),
          [("Recipe", 3), ("Portions", 1.3), ("Done", 1)], row_h=22, fill=TERRA_LIGHT,
          check_cols=(2,), check_color=TERRA)
    inner = p.panel(bot, "Containers")
    boxes = []
    rows = Box(inner.x, inner.y, inner.w, inner.h - 2).rows(2, gap=10)
    for rr in rows:
        boxes += rr.cols(4, gap=10)
    for k, cb in enumerate(boxes):
        light = p.accent_light if k % 2 == 0 else TERRA_LIGHT
        # lid
        c.setFillColor(light)
        c.roundRect(cb.x + 4, cb.top - 10, cb.w - 8, 10, 4, stroke=0, fill=1)
        # tub
        c.setStrokeColor(LINE)
        c.setLineWidth(0.7)
        c.roundRect(cb.x, cb.y, cb.w, cb.h - 13, 7, stroke=1, fill=0)
        ib = Box(cb.x + 9, cb.y + 8, cb.w - 18, cb.h - 13 - 12)
        field(p, ib.x, ib.top - 12, ib.w, "Meal", 6.5)
        field(p, ib.x, ib.top - 34, ib.w, "Day", 6.5)
        p.lines(Box(ib.x, ib.y, ib.w, ib.h - 40), 18, LINE_SOFT, start_offset=18)
    p.finish()


def favorites(p):
    p.header("Go-To Meals", "The ones everyone loves", right_fields=())
    sections = [
        ("Breakfasts", False), ("Lunches", True),
        ("Dinners", False), ("30-minute meals", True),
        ("Snacks & sides", False), ("Sweet treats", True),
    ]
    cols = p.body.cols(2)
    grid = [cb.rows(3) for cb in cols]
    k = 0
    for r in range(3):
        for cidx in range(2):
            name, terra = sections[k]
            k += 1
            b = grid[cidx][r]
            color = TERRA if terra else p.accent
            inner = p.panel(b, name, title_color=color)
            dotted_lines(p, Box(inner.x, inner.y, inner.w, inner.h + 4), 20, color)
    p.finish()


def takeout(p):
    p.header("Takeout Favorites", "For the nights off", right_fields=())
    c = p.c
    main, bot = p.body.split_v(0.80)
    spec = [("Restaurant", 2.2), ("Cuisine", 1.2), ("Phone / app", 1.6), ("Our usual order", 3.2)]
    total = sum(w for _, w in spec)
    n = table(p, main, spec, row_h=40)
    # faint middle line in the order column for two-line orders
    x0 = main.x + main.w * (total - spec[-1][1]) / total
    c.setStrokeColor(LINE_SOFT)
    c.setLineWidth(0.5)
    top = main.top - 20
    for j in range(n):
        y = top - (j + 0.5) * 40
        c.line(x0 + 8, y, main.right - 4, y)
    l, r = bot.split_h(0.5)
    inner = p.panel(l, "Allergies & preferences", title_color=TERRA)
    p.lines(Box(inner.x, inner.y, inner.w, inner.h + 4), 20)
    inner = p.panel(r, "Want to try")
    dotted_lines(p, Box(inner.x, inner.y, inner.w, inner.h + 4), 20)
    p.finish()


def draw(p):
    cover(p)
    weekly_grid(p)
    weekly_list(p)
    grocery(p)
    monthly(p)
    recipe_cards(p)
    recipe_sheet(p)
    pantry(p)
    fridge_freezer(p)
    meal_prep(p)
    favorites(p)
    takeout(p)


if __name__ == "__main__":
    build(SLUG, TITLE, draw, accent=0)
