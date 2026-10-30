"""Budget Planner — Linnea Paper Co.

Run from the etsy-shop folder:  python scripts/budget_planner.py
Writes products/budget-planner/budget-planner-{letter,a4}.pdf
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brand import *  # noqa: E402,F403
from reportlab.pdfbase.pdfmetrics import stringWidth  # noqa: E402

TITLE = "Budget Planner"
HEADER_H = 20      # table header row height
SEC_TITLE = 16     # space taken by a section label above a table
ROW_TEXT = 8.5     # pre-filled row text size


# ---------------------------------------------------------------------------
# small helpers (local to this product; brand.py stays untouched)
# ---------------------------------------------------------------------------
def label_w(s, size, spacing):
    return stringWidth(s.upper(), SANS_BOLD, size) + spacing * (len(s) - 1)


def fit_size(s, maxw, size=7.5):
    sp = 1.4
    while label_w(s, size, sp) > maxw and size > 5.2:
        size -= 0.25
        sp = max(0.5, sp - 0.12)
    return size, sp


def fit_label(p, x, y, s, maxw, color=INK, size=7.5, align="center", fixed=None):
    """Spaced caps label that shrinks to fit maxw (or uses fixed=(size, spacing))."""
    size, sp = fixed or fit_size(s, maxw, size)
    p.text(x, y, s.upper(), SANS_BOLD, size, color, align, spacing=sp)


def field(p, x, y, w, name, size=7, color=None):
    """LABEL ________ fill-in line, total width w, baseline y."""
    p.label(x, y, name, color=color, size=size)
    lw = label_w(name, size, 1.4)
    c = p.c
    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    c.line(x + lw + 6, y - 1.5, x + w, y - 1.5)


def checkbox(p, cx, cy, s=8, color=None):
    c = p.c
    c.setStrokeColor(color or p.accent)
    c.setLineWidth(0.8)
    c.roundRect(cx - s / 2, cy - s / 2, s, s, 1.5, stroke=1, fill=0)


def section_title(p, x, top, title, w=None, note=None):
    p.label(x, top - 8, title, p.accent)
    if note and w:
        p.text(x + w, top - 8, note, ITALIC, 8, MUTED, "right")


def table(p, x, top, w, specs, n_rows, row_h, prefill=(), total=None, header_h=HEADER_H):
    """specs: list of (label, frac, kind) with kind in text|box|yn.
    Header row in accent_light, horizontal rules, soft vertical dividers.
    total: label for a cream total row appended after n_rows (or None).
    Returns bottom y."""
    c = p.c
    fr = sum(s[1] for s in specs)
    xs = [x]
    for s in specs:
        xs.append(xs[-1] + w * s[1] / fr)
    xs[-1] = x + w
    rows = n_rows + (1 if total else 0)
    bottom = top - header_h - rows * row_h
    # header
    c.setFillColor(p.accent_light)
    c.roundRect(x, top - header_h, w, header_h, 4, stroke=0, fill=1)
    box_fits = [fit_size(s[0], xs[i + 1] - xs[i] - 8) for i, s in enumerate(specs) if s[2] == "box"]
    box_fit = min(box_fits) if box_fits else None
    for i, s in enumerate(specs):
        cw = xs[i + 1] - xs[i]
        if i == 0 and s[2] == "text":
            fit_label(p, xs[i] + 8, top - header_h / 2 - 2.6, s[0], cw - 12, align="left")
        else:
            fit_label(p, (xs[i] + xs[i + 1]) / 2, top - header_h / 2 - 2.6, s[0], cw - 8,
                      fixed=box_fit if s[2] == "box" else None)
    # total row fill
    if total:
        c.setFillColor(CREAM)
        c.rect(x, bottom, w, row_h, stroke=0, fill=1)
    # vertical dividers
    c.setStrokeColor(LINE_SOFT)
    c.setLineWidth(0.6)
    for xx in xs[1:-1]:
        c.line(xx, top - header_h, xx, bottom)
    # row rules
    c.setStrokeColor(LINE)
    c.setLineWidth(0.6)
    for r in range(1, rows + 1):
        y = top - header_h - r * row_h
        c.line(x, y, x + w, y)
    # cells
    for r in range(n_rows):
        yb = top - header_h - (r + 1) * row_h
        mid = yb + row_h / 2
        if r < len(prefill) and prefill[r]:
            p.text(xs[0] + 8, mid - 3, prefill[r], SANS, ROW_TEXT, MUTED)
        for i, s in enumerate(specs):
            cx = (xs[i] + xs[i + 1]) / 2
            if s[2] == "box":
                checkbox(p, cx, mid, 8)
            elif s[2] == "yn":
                for dx, t in ((-8, "Y"), (8, "N")):
                    c.setStrokeColor(p.accent)
                    c.setLineWidth(0.7)
                    c.circle(cx + dx, mid, 5.5, stroke=1, fill=0)
                    p.text(cx + dx, mid - 2.2, t, SANS_BOLD, 5.8, MUTED, "center")
    if total:
        p.label(xs[0] + 8, bottom + row_h / 2 - 2.6, total, INK, 7)
        # blank out box/yn cells in the total row: nothing drawn there
    return bottom


def stack(p, b, sections, gap=GUTTER, max_row=None):
    """Stack titled tables in box b, sharing one row height that fills b."""
    n = sum(s["rows"] + (1 if s.get("total") else 0) for s in sections)
    over = sum((SEC_TITLE if s.get("title") else 0) + HEADER_H for s in sections) + gap * (len(sections) - 1)
    rh = (b.h - over) / n
    if max_row:
        rh = min(rh, max_row)
    top = b.top
    for s in sections:
        if s.get("title"):
            section_title(p, b.x, top, s["title"], b.w, s.get("note"))
            top -= SEC_TITLE
        top = table(p, b.x, top, b.w, s["specs"], s["rows"], rh, s.get("prefill", ()), s.get("total"))
        top -= gap
    return top + gap


def stats(p, b, labels, sub=None):
    """Row of cream summary boxes with a label: big blank space to write in."""
    for bx, name in zip(b.cols(len(labels), 10), labels):
        p.c.setFillColor(CREAM)
        p.c.roundRect(bx.x, bx.y, bx.w, bx.h, 6, stroke=0, fill=1)
        fit_label(p, bx.x + 10, bx.top - 15, name, bx.w - 20, p.accent, 7, "left")


def numbered_circle(p, cx, cy, r, n, color=None, size=None):
    c = p.c
    c.setStrokeColor(color or p.accent)
    c.setLineWidth(0.9)
    c.circle(cx, cy, r, stroke=1, fill=0)
    if n is not None:
        fs = size or max(6.5, min(11, r * 0.55))
        p.text(cx, cy - fs * 0.35, str(n), SANS, fs, LINE, "center")


def circle_grid(p, b, cols, rows, numbered=True, fill_ratio=0.78, start=1):
    """Grid of circles centred in b. Returns radius used."""
    cw, ch = b.w / cols, b.h / rows
    r = min(cw, ch) / 2 * fill_ratio
    k = start
    for j in range(rows):
        for i in range(cols):
            cx = b.x + cw * (i + 0.5)
            cy = b.top - ch * (j + 0.5)
            numbered_circle(p, cx, cy, r, k if numbered else None)
            k += 1
    return r


def check_title(p, title, fields):
    """Guard: the serif title must not run into the top-right fill-in fields."""
    tw = stringWidth(title, SERIF, 30)
    limit = p.W - MARGIN - 150 - 12 if fields else p.W - MARGIN
    assert MARGIN + tw < limit, f"title too wide: {title}"


def head(p, title, subtitle, fields=("DATE",)):
    check_title(p, title, fields)
    p.header(title, subtitle, right_fields=fields)
    return p.body


# ---------------------------------------------------------------------------
# pages
# ---------------------------------------------------------------------------
def pg_cover(p):
    p.cover(TITLE, "a calm, simple system for your money", [
        "Financial Goals  ·  Annual Overview",
        "Monthly Budget  ·  Monthly Review",
        "Expense Tracker  ·  Weekly Spending",
        "Bill Payment Tracker  ·  Subscriptions",
        "Savings Goal  ·  Sinking Funds",
        "Debt Payoff  ·  Debt Payment Log",
        "No-Spend Challenge  ·  Net Worth",
        "Notes",
    ])


def pg_goals(p):
    b = head(p, "Financial Goals", "Dream it, plan it, fund it", ("YEAR",))
    why_h = 112
    why = Box(b.x, b.top - why_h, b.w, why_h)
    inner = p.panel(why, "My money why", fill=CREAM, stroke=CREAM)
    p.lines(Box(inner.x, inner.y + 2, inner.w, inner.h - 2), 22)
    rest = Box(b.x, b.y, b.w, b.h - why_h - GUTTER - 6)
    specs = [("Goal", .46, "text"), ("Amount", .18, "text"), ("Target date", .22, "text"), ("Done", .14, "box")]
    stack(p, rest, [
        dict(title="Short-term  ·  this year", specs=specs, rows=4),
        dict(title="Mid-term  ·  1 to 5 years", specs=specs, rows=4),
        dict(title="Long-term  ·  5+ years", specs=specs, rows=4),
    ], gap=18)
    p.finish()


MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


def pg_annual(p):
    b = head(p, "Annual Overview", "Your year at a glance", ("YEAR",))
    top, bot = b.split_v(0.74, 18)
    specs = [("Month", .16, "text"), ("Income", .16, "text"), ("Expenses", .16, "text"),
             ("Savings", .16, "text"), ("Debt paid", .16, "text"), ("Left over", .20, "text")]
    stack(p, top, [dict(specs=specs, rows=12, prefill=MONTHS, total="Total")])
    inner = p.panel(bot, "Big expenses & notes for the year")
    p.lines(inner, 22)
    p.finish()


def pg_monthly(p):
    b = head(p, "Monthly Budget", "Give every penny a purpose", ("MONTH", "YEAR"))
    strip = Box(b.x, b.top - 52, b.w, 52)
    stats(p, strip, ["Total income", "Total expenses", "Total saved", "Left over"])
    body = Box(b.x, b.y, b.w, b.h - 52 - 18)
    left, right = body.split_h(0.5, 18)
    s3 = [("Budget", .26, "text"), ("Actual", .26, "text")]
    stack(p, left, [
        dict(title="Income", specs=[("Source", .48, "text")] + s3, rows=5, total="Total income",
             prefill=["Paycheck", "Side income"]),
        dict(title="Fixed expenses", specs=[("Bill", .48, "text")] + s3, rows=10, total="Total fixed",
             prefill=["Rent / mortgage", "Utilities", "Phone & internet", "Insurance", "Transport"]),
    ])
    stack(p, right, [
        dict(title="Variable expenses", specs=[("Category", .48, "text")] + s3, rows=10, total="Total variable",
             prefill=["Groceries", "Eating out", "Fuel", "Household", "Personal care", "Entertainment", "Gifts"]),
        dict(title="Savings & debt", specs=[("Goal / debt", .48, "text")] + s3, rows=5, total="Total",
             prefill=["Emergency fund"]),
    ])
    p.finish()


def pg_expenses(p):
    b = head(p, "Expense Tracker", "Every little thing counts", ("MONTH",))
    strip_h = 50
    tb = Box(b.x, b.y + strip_h + 18, b.w, b.h - strip_h - 18)
    specs = [("Date", .13, "text"), ("Description", .45, "text"), ("Category", .24, "text"), ("Amount", .18, "text")]
    rows = int((tb.h - HEADER_H) // 22) - 1
    stack(p, tb, [dict(specs=specs, rows=rows, total="Page total")])
    stats(p, Box(b.x, b.y, b.w, strip_h), ["Monthly budget", "Total spent", "Remaining"])
    p.finish()


def pg_bills(p):
    b = head(p, "Bill Tracker", "Check off each bill as it is paid", ("YEAR",))
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    specs = [("Bill", .22, "text"), ("Due", .08, "text"), ("Amount", .12, "text")] + [(m, .58 / 12, "box") for m in months]
    rows = int((b.h - HEADER_H) // 26)
    stack(p, b, [dict(specs=specs, rows=rows)])
    p.finish()


def pg_weekly(p):
    b = head(p, "Weekly Spending", "Small steps, big change", ("WEEK OF",))
    strip = Box(b.x, b.top - 50, b.w, 50)
    stats(p, strip, ["Weekly budget", "Total spent", "Remaining"])
    grid = Box(b.x, b.y, b.w, b.h - 50 - 18)
    cols = grid.cols(2, 18)
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "Notes"]
    cells = [cell for col in cols for cell in col.rows(4, 14)]
    c = p.c
    sp = 20
    for cell, day in zip(cells, days):
        inner = p.title_band(cell, day)
        n = int(inner.h // 19)
        sp = inner.h / n          # stretch rows so the cell is filled in both sizes
        bottom = inner.top - n * sp
        if day == "Notes":
            p.lines(Box(inner.x, bottom, inner.w, inner.h), sp)
            continue
        divx = inner.x + inner.w * 0.72
        # total row (last row)
        c.setFillColor(CREAM)
        c.rect(inner.x, bottom, inner.w, sp, stroke=0, fill=1)
        p.lines(Box(inner.x, bottom, inner.w, n * sp), sp)
        c.setStrokeColor(LINE_SOFT)
        c.setLineWidth(0.6)
        c.line(divx, inner.top, divx, bottom)
        p.label(divx - 8, bottom + sp / 2 - 2.6, "Day total", INK, 6.5, "right")
    p.finish()


def pg_savings(p):
    b = head(p, "Savings Goal", "Watch it grow, coin by coin", ("START DATE",))
    info_h = 70
    info = Box(b.x, b.top - info_h, b.w, info_h)
    inner = p.panel(info, None, fill=CREAM, stroke=CREAM)
    l, r = inner.split_h(0.5, 24)
    y1 = inner.top - 16
    y2 = y1 - 26
    field(p, l.x, y1, l.w, "Saving for")
    field(p, l.x, y2, l.w, "Goal amount")
    field(p, r.x, y1, r.w, "Target date")
    field(p, r.x, y2, r.w, "Each coin =")
    # coins
    rest = Box(b.x, b.y, b.w, b.h - info_h - 18)
    coin_h = rest.h * 0.56
    cb = Box(rest.x, rest.top - coin_h, rest.w, coin_h)
    section_title(p, cb.x, cb.top, "Color in a coin each time you save", cb.w, "50 coins to your goal")
    circle_grid(p, Box(cb.x, cb.y, cb.w, cb.h - SEC_TITLE - 4), 10, 5, fill_ratio=0.8)
    # deposit log, two side-by-side tables
    lb = Box(rest.x, rest.y, rest.w, rest.h - coin_h - 18)
    section_title(p, lb.x, lb.top, "Deposit log")
    tb = Box(lb.x, lb.y, lb.w, lb.h - SEC_TITLE)
    specs = [("Date", .3, "text"), ("Amount", .35, "text"), ("Balance", .35, "text")]
    n = int((tb.h - HEADER_H) // 22)
    rh = (tb.h - HEADER_H) / n
    for col in tb.cols(2, 18):
        table(p, col.x, col.top, col.w, specs, n, rh)
    p.finish()


def pg_debt(p):
    b = head(p, "Debt Payoff", "The snowball method", ("START DATE",))
    top, bot = b.split_v(0.42, 20)
    specs = [("Order", .09, "text"), ("Creditor", .29, "text"), ("Balance", .16, "text"), ("Rate", .11, "text"),
             ("Min. payment", .17, "text"), ("Paid off", .18, "text")]
    stack(p, top, [dict(title="My debts", specs=specs, rows=7, prefill=[str(k) for k in range(1, 8)],
                        note="List smallest balance first. Pay minimums on all, extra on #1.")])
    section_title(p, bot.x, bot.top, "Payoff progress  ·  color in as you go")
    grid = Box(bot.x, bot.y, bot.w, bot.h - SEC_TITLE)
    cells = [cell for row in grid.rows(2, 14) for cell in row.cols(2, 14)]
    for i, cell in enumerate(cells):
        inner = p.panel(cell, f"Debt {i + 1}")
        y = inner.top - 12
        field(p, inner.x, y, inner.w, "Creditor")
        y -= 22
        hw = (inner.w - 12) / 2
        field(p, inner.x, y, hw, "Balance")
        field(p, inner.x + hw + 12, y, hw, "Each =")
        # 20 circles, 2 rows of 10, filling the leftover space above the final line
        circ = Box(inner.x, inner.y + 22, inner.w, y - 10 - (inner.y + 22))
        circle_grid(p, circ, 10, 2, numbered=False, fill_ratio=0.72)
        field(p, inner.x, inner.y + 4, inner.w, "Debt free on")
    p.finish()


def pg_debt_log(p):
    b = head(p, "Debt Payment Log", "One payment at a time", None)
    specs = [("Date", .18, "text"), ("Payment", .2, "text"), ("Interest", .18, "text"),
             ("New balance", .24, "text"), ("Notes", .2, "text")]
    for half in b.rows(2, 24):
        inner = p.panel(half, None)
        y = inner.top - 12
        tw = (inner.w - 24) / 3
        for k, name in enumerate(["Creditor", "Start balance", "Rate"]):
            field(p, inner.x + k * (tw + 12), y, tw, name)
        tb = Box(inner.x, inner.y, inner.w, inner.h - 30)
        n = int((tb.h - HEADER_H) // 22)
        table(p, tb.x, tb.top, tb.w, specs, n, (tb.h - HEADER_H) / n)
    p.finish()


def pg_sinking(p):
    b = head(p, "Sinking Funds", "Save ahead for the things you know are coming", None)
    cells = [cell for row in b.rows(2, 18) for cell in row.cols(2, 18)]
    c = p.c
    for cell in cells:
        inner = p.panel(cell, None)
        y = inner.top - 12
        hw = (inner.w - 12) / 2
        field(p, inner.x, y, inner.w, "Saving for")
        y -= 24
        field(p, inner.x, y, hw, "Goal")
        field(p, inner.x + hw + 12, y, hw, "Due by")
        y -= 24
        field(p, inner.x, y, hw, "Per month")
        field(p, inner.x + hw + 12, y, hw, "Saved")
        # colour-in progress bar
        y -= 34
        bar_h = 18
        c.setStrokeColor(p.accent)
        c.setLineWidth(0.8)
        c.roundRect(inner.x, y, inner.w, bar_h, 4, stroke=1, fill=0)
        seg = inner.w / 10
        c.setStrokeColor(p.accent_light)
        c.setLineWidth(0.8)
        for k in range(1, 10):
            c.line(inner.x + k * seg, y + 1, inner.x + k * seg, y + bar_h - 1)
        for k in range(1, 11):
            p.text(inner.x + k * seg - seg / 2, y - 9, f"{k * 10}%", SANS, 6, MUTED, "center")
        # log
        top = y - 22
        tb_h = top - inner.y
        specs = [("Date", .3, "text"), ("Added", .35, "text"), ("Total", .35, "text")]
        n = int((tb_h - HEADER_H) // 20)
        table(p, inner.x, top, inner.w, specs, n, (tb_h - HEADER_H) / n)
    p.finish()


def pg_subs(p):
    b = head(p, "Subscriptions", "Know what renews, keep what you love", ("UPDATED",))
    strip_h = 50
    tb = Box(b.x, b.y + strip_h + 18, b.w, b.h - strip_h - 18)
    specs = [("Service", .26, "text"), ("Category", .17, "text"), ("Renews", .13, "text"),
             ("Monthly", .14, "text"), ("Yearly", .14, "text"), ("Keep?", .16, "yn")]
    rows = int((tb.h - HEADER_H) // 24) - 1
    stack(p, tb, [dict(specs=specs, rows=rows, total="Total")])
    stats(p, Box(b.x, b.y, b.w, strip_h), ["Monthly total", "Yearly total", "Saved by cancelling"])
    p.finish()


def pg_nospend(p):
    b = head(p, "No-Spend Challenge", "30 days of mindful spending", ("START DATE",))
    top, bot = b.split_v(0.58, 18)
    section_title(p, top.x, top.top, "Color in each no-spend day", top.w, "only essentials count")
    circle_grid(p, Box(top.x, top.y, top.w, top.h - SEC_TITLE - 2), 6, 5, fill_ratio=0.74)
    cols = bot.cols(3, 14)
    titles = ["I can still buy", "I'm taking a break from", "Reflection"]
    for col, t in zip(cols, titles):
        inner = p.panel(col, t)
        if t == "Reflection":
            y = inner.top - 12
            field(p, inner.x, y, inner.w, "Money saved")
            y -= 24
            field(p, inner.x, y, inner.w, "My reward")
            p.lines(Box(inner.x, inner.y, inner.w, y - 6 - inner.y), 20)
        else:
            p.checklist(inner, 20)
    p.finish()


def pg_networth(p):
    b = head(p, "Net Worth", "Know where you stand", ("DATE",))
    top_h = b.h * 0.50
    top = Box(b.x, b.top - top_h, b.w, top_h)
    left, right = top.split_h(0.5, 18)
    s2 = [("Value", .38, "text")]
    stack(p, left, [dict(title="Assets  ·  what I own", specs=[("Account / item", .62, "text")] + s2, rows=9,
                         total="Total assets",
                         prefill=["Checking", "Savings", "Emergency fund", "Retirement", "Investments", "Home", "Vehicle"])])
    stack(p, right, [dict(title="Liabilities  ·  what I owe", specs=[("Debt", .62, "text")] + s2, rows=9,
                          total="Total liabilities",
                          prefill=["Mortgage", "Car loan", "Student loan", "Credit cards", "Personal loan"])])
    # equation
    eq_h = 66
    eq = Box(b.x, top.y - 20 - eq_h, b.w, eq_h)
    sym_w = 26
    bw = (eq.w - 2 * sym_w) / 3
    names = ["Total assets", "Total liabilities", "My net worth"]
    for k, name in enumerate(names):
        bx = Box(eq.x + k * (bw + sym_w), eq.y, bw, eq.h)
        p.c.setFillColor(p.accent_light if k == 2 else CREAM)
        p.c.roundRect(bx.x, bx.y, bx.w, bx.h, 6, stroke=0, fill=1)
        fit_label(p, bx.x + bx.w / 2, bx.top - 16, name, bx.w - 16, p.accent if k < 2 else INK, 7)
        if k < 2:
            sx, sy = bx.right + sym_w / 2, eq.y + eq.h / 2
            p.c.setStrokeColor(MUTED)
            p.c.setLineWidth(1.2)
            for dy in ((0,) if k == 0 else (-3, 3)):
                p.c.line(sx - 6, sy + dy, sx + 6, sy + dy)
    # check-ins
    ck = Box(b.x, b.y, b.w, eq.y - 20 - b.y)
    specs = [("Date", .18, "text"), ("Assets", .2, "text"), ("Liabilities", .2, "text"),
             ("Net worth", .22, "text"), ("Change", .2, "text")]
    stack(p, ck, [dict(title="Check-ins through the year", specs=specs, rows=6)])
    p.finish()


def pg_review(p):
    b = head(p, "Monthly Review", "Reflect, reset, keep going", ("MONTH",))
    strip = Box(b.x, b.top - 52, b.w, 52)
    stats(p, strip, ["Income", "Spent", "Saved", "Debt paid"])
    bottom_h = 48
    grid = Box(b.x, b.y + bottom_h + 14, b.w, b.h - 52 - 18 - bottom_h - 14)
    titles = ["Wins this month", "Where I overspent", "What I learned", "Next month I will"]
    cells = [cell for row in grid.rows(2, 14) for cell in row.cols(2, 14)]
    for cell, t in zip(cells, titles):
        inner = p.panel(cell, t)
        if t == "Next month I will":
            p.checklist(inner, 22)
        else:
            p.lines(inner, 22)
    # bottom strip: feeling + next goal
    bb = Box(b.x, b.y, b.w, bottom_h)
    inner = p.panel(bb, None, fill=CREAM, stroke=CREAM)
    l, r = inner.split_h(0.52, 24)
    cy = inner.y + inner.h / 2
    p.label(l.x, cy - 2.6, "This month felt", INK, 7)
    lw = label_w("This month felt", 7, 1.4)
    words = ["tight", "okay", "great"]
    x = l.x + lw + 16
    for w in words:
        p.c.setStrokeColor(p.accent)
        p.c.setLineWidth(0.8)
        p.c.circle(x + 6, cy, 6, stroke=1, fill=0)
        p.text(x + 16, cy - 3, w, SANS, 8.5, MUTED)
        x += 16 + stringWidth(w, SANS, 8.5) + 14
    assert x - 14 < l.right, "mood row too wide"
    field(p, r.x, cy - 2.6, r.w, "Next month's savings goal", color=INK)
    p.finish()


def pg_notes(p):
    b = head(p, "Notes", "Ideas, plans & money thoughts", ("DATE",))
    inner = p.panel(b, None)
    p.dot_grid(inner, 14)
    p.finish()


def draw(p):
    pg_cover(p)
    pg_goals(p)
    pg_annual(p)
    pg_monthly(p)
    pg_expenses(p)
    pg_weekly(p)
    pg_bills(p)
    pg_subs(p)
    pg_savings(p)
    pg_sinking(p)
    pg_debt(p)
    pg_debt_log(p)
    pg_nospend(p)
    pg_networth(p)
    pg_review(p)
    pg_notes(p)


if __name__ == "__main__":
    build("budget-planner", TITLE, draw, accent=1)
