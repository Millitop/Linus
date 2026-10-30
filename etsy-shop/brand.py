"""Shared design system for all printable planner products.

Every product script imports from here so the whole shop looks like one
brand. Pages are drawn with reportlab and built in two sizes (US Letter
and A4), because Etsy buyers expect both.

Usage in a product script:

    from brand import *

    def draw_pages(c, page):        # page is a Page helper (see below)
        page.header("Weekly Plan", "WEEK OF ________")
        ...
        page.finish()               # footer + showPage

    build("weekly-planner", "Weekly Planner", draw_pages)
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, LETTER, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent
FONT_DIR = ROOT / "fonts"
OUT_DIR = ROOT / "products"

SHOP_NAME = "Linnea Paper Co."
SHOP_TAGLINE = "calm printables for an organized life"

# ---- Fonts -----------------------------------------------------------------
for _name in ["DMSerifDisplay-Regular", "Lato-Light", "Lato-Regular", "Lato-Bold", "Lato-Italic"]:
    pdfmetrics.registerFont(TTFont(_name, str(FONT_DIR / f"{_name}.ttf")))

SERIF = "DMSerifDisplay-Regular"   # headings
SANS_LIGHT = "Lato-Light"
SANS = "Lato-Regular"
SANS_BOLD = "Lato-Bold"            # small caps-style labels
ITALIC = "Lato-Italic"

# ---- Palette (warm neutral + sage + terracotta) -------------------------------
INK = HexColor("#3B3A36")        # main text
MUTED = HexColor("#8A857C")      # secondary text
LINE = HexColor("#CFC8BC")       # writing lines / borders
LINE_SOFT = HexColor("#E6E0D6")  # dotted grids, faint guides
PAPER = HexColor("#FFFFFF")      # keep background white: buyers print at home
CREAM = HexColor("#F6F1E9")      # soft fills (header bands, boxes)
SAGE = HexColor("#9CAF98")       # primary accent
SAGE_LIGHT = HexColor("#DDE5DA")
TERRA = HexColor("#C98B6B")      # secondary accent
TERRA_LIGHT = HexColor("#F1DED3")
SAND = HexColor("#E9DCC6")

ACCENTS = [(SAGE, SAGE_LIGHT), (TERRA, TERRA_LIGHT), (HexColor("#A7B6C4"), HexColor("#E1E7ED"))]

SIZES = {"letter": LETTER, "a4": A4}

MARGIN = 36        # 0.5 inch: safe for home printers
GUTTER = 14


@dataclass
class Box:
    x: float
    y: float      # bottom
    w: float
    h: float

    @property
    def top(self):
        return self.y + self.h

    @property
    def right(self):
        return self.x + self.w

    def inset(self, d):
        return Box(self.x + d, self.y + d, self.w - 2 * d, self.h - 2 * d)

    def cols(self, n, gap=GUTTER):
        w = (self.w - gap * (n - 1)) / n
        return [Box(self.x + i * (w + gap), self.y, w, self.h) for i in range(n)]

    def rows(self, n, gap=GUTTER):
        h = (self.h - gap * (n - 1)) / n
        return [Box(self.x, self.top - (i + 1) * h - i * gap, self.w, h) for i in range(n)]

    def split_v(self, frac, gap=GUTTER):
        """Split top/bottom. frac = share for the top part."""
        th = (self.h - gap) * frac
        return Box(self.x, self.top - th, self.w, th), Box(self.x, self.y, self.w, self.h - gap - th)

    def split_h(self, frac, gap=GUTTER):
        """Split left/right. frac = share for the left part."""
        lw = (self.w - gap) * frac
        return Box(self.x, self.y, lw, self.h), Box(self.x + lw + gap, self.y, self.w - gap - lw, self.h)


class Page:
    """Drawing helpers bound to one canvas. Coordinates are reportlab points
    (origin bottom-left). `self.body` is the free area under the header."""

    def __init__(self, c: canvas.Canvas, size, product_title: str, accent=0):
        self.c = c
        self.W, self.H = size
        self.product_title = product_title
        self.accent, self.accent_light = ACCENTS[accent % len(ACCENTS)]
        self.page_no = 0
        self.reset()

    def reset(self):
        self.body = Box(MARGIN, MARGIN + 22, self.W - 2 * MARGIN, self.H - 2 * MARGIN - 22)

    # -- text ---------------------------------------------------------------
    def text(self, x, y, s, font=SANS, size=10, color=INK, align="left", spacing=0):
        c = self.c
        c.setFillColor(color)
        c.setFont(font, size)
        if spacing:
            t = c.beginText()
            t.setFont(font, size)
            t.setCharSpace(spacing)
            w = pdfmetrics.stringWidth(s, font, size) + spacing * (len(s) - 1)
            ox = {"left": 0, "center": -w / 2, "right": -w}[align]
            t.setTextOrigin(x + ox, y)
            t.textOut(s)
            t.setCharSpace(0)
            c.drawText(t)
            return
        {"left": c.drawString, "center": c.drawCentredString, "right": c.drawRightString}[align](x, y, s)

    def label(self, x, y, s, color=None, size=7.5, align="left"):
        """Small spaced uppercase label, e.g. section titles."""
        self.text(x, y, s.upper(), SANS_BOLD, size, color or MUTED, align, spacing=1.4)

    # -- header / footer ----------------------------------------------------
    def header(self, title, subtitle=None, right_fields=("DATE",)):
        """Serif title top-left, optional label under it, fill-in fields top-right.
        Shrinks self.body to the area below."""
        c = self.c
        top = self.H - MARGIN
        self.text(MARGIN, top - 30, title, SERIF, 30, INK)
        if subtitle:
            self.label(MARGIN, top - 46, subtitle, self.accent)
        # fill-in fields on the right
        fx = self.W - MARGIN
        y = top - 14
        for f in right_fields or ():
            self.label(fx - 150, y, f, size=7)
            c.setStrokeColor(LINE)
            c.setLineWidth(0.7)
            c.line(fx - 150 + pdfmetrics.stringWidth(f.upper(), SANS_BOLD, 7) + 1.4 * len(f) + 6, y - 1, fx, y - 1)
            y -= 18
        # thin accent rule
        c.setStrokeColor(self.accent)
        c.setLineWidth(1.2)
        c.line(MARGIN, top - 58, MARGIN + 40, top - 58)
        c.setStrokeColor(LINE_SOFT)
        c.setLineWidth(0.6)
        c.line(MARGIN + 44, top - 58, self.W - MARGIN, top - 58)
        self.body = Box(MARGIN, MARGIN + 22, self.W - 2 * MARGIN, top - 72 - (MARGIN + 22))

    def footer(self):
        self.page_no += 1
        self.text(MARGIN, MARGIN, SHOP_NAME.upper(), SANS_BOLD, 6.5, LINE, spacing=1.6)
        self.text(self.W - MARGIN, MARGIN, f"{self.product_title.upper()}  ·  PERSONAL USE ONLY", SANS_BOLD, 6.5, LINE, "right", spacing=1.2)

    def finish(self):
        self.footer()
        self.c.showPage()
        self.reset()

    # -- building blocks ----------------------------------------------------
    def panel(self, b: Box, title=None, fill=None, radius=8, stroke=LINE, title_color=None):
        """Rounded box with an optional label. Returns inner Box for content."""
        c = self.c
        c.setLineWidth(0.7)
        c.setStrokeColor(stroke)
        if fill:
            c.setFillColor(fill)
        c.roundRect(b.x, b.y, b.w, b.h, radius, stroke=1 if stroke else 0, fill=1 if fill else 0)
        inner = b.inset(10)
        if title:
            self.label(inner.x, inner.top - 6, title, title_color or self.accent)
            inner = Box(inner.x, inner.y, inner.w, inner.h - 16)
        return inner

    def title_band(self, b: Box, title, fill=None, h=20):
        """Filled band with a label, used for column headers (e.g. weekdays)."""
        c = self.c
        c.setFillColor(fill or self.accent_light)
        c.roundRect(b.x, b.top - h, b.w, h, 5, stroke=0, fill=1)
        self.label(b.x + b.w / 2, b.top - h + 7, title, INK, align="center")
        return Box(b.x, b.y, b.w, b.h - h - 4)

    def lines(self, b: Box, spacing=20, color=LINE, start_offset=None, width=0.6):
        """Horizontal writing lines filling the box. Returns number drawn."""
        c = self.c
        c.setStrokeColor(color)
        c.setLineWidth(width)
        y = b.top - (start_offset if start_offset is not None else spacing)
        n = 0
        while y >= b.y - 0.1:
            c.line(b.x, y, b.right, y)
            y -= spacing
            n += 1
        return n

    def checklist(self, b: Box, spacing=20, box=8, color=None):
        """Lines with a small checkbox at the start of each."""
        c = self.c
        y = b.top - spacing
        n = 0
        while y >= b.y - 0.1:
            c.setStrokeColor(color or self.accent)
            c.setLineWidth(0.8)
            c.roundRect(b.x, y + 2, box, box, 1.5, stroke=1, fill=0)
            c.setStrokeColor(LINE)
            c.setLineWidth(0.6)
            c.line(b.x + box + 6, y, b.right, y)
            y -= spacing
            n += 1
        return n

    def dot_grid(self, b: Box, step=14, r=0.55, color=LINE):
        c = self.c
        c.setFillColor(color)
        nx = int(b.w // step)
        ny = int(b.h // step)
        ox = b.x + (b.w - nx * step) / 2
        oy = b.y + (b.h - ny * step) / 2
        for i in range(nx + 1):
            for j in range(ny + 1):
                c.circle(ox + i * step, oy + j * step, r, stroke=0, fill=1)

    def grid(self, b: Box, cols, rows, color=LINE, width=0.6, header_fill=None, header_h=0):
        """Table grid. Returns (col_xs, row_ys) edges, top to bottom for rows."""
        c = self.c
        cw = b.w / cols
        rh = (b.h - header_h) / rows
        if header_fill and header_h:
            c.setFillColor(header_fill)
            c.rect(b.x, b.top - header_h, b.w, header_h, stroke=0, fill=1)
        c.setStrokeColor(color)
        c.setLineWidth(width)
        xs = [b.x + i * cw for i in range(cols + 1)]
        ys = [b.top] + ([b.top - header_h] if header_h else []) + [b.top - header_h - (j + 1) * rh for j in range(rows)]
        for x in xs:
            c.line(x, b.y, x, b.top)
        for y in ys:
            c.line(b.x, y, b.right, y)
        return xs, ys

    def circle_row(self, x, y, n, r=4.5, gap=4, color=None):
        """Row of empty circles (for water glasses, habit dots...)."""
        c = self.c
        c.setStrokeColor(color or self.accent)
        c.setLineWidth(0.8)
        for i in range(n):
            c.circle(x + r + i * (2 * r + gap), y, r, stroke=1, fill=0)

    def leaf(self, x, y, s=10, color=None):
        """Tiny decorative sprig (brand motif). Use sparingly."""
        c = self.c
        c.saveState()
        c.setStrokeColor(color or self.accent)
        c.setLineWidth(0.9)
        c.setFillColor(color or self.accent)
        c.line(x, y, x, y + 2.2 * s)
        for i, side in enumerate([-1, 1, -1, 1]):
            yy = y + 0.45 * s * (i + 1)
            p = c.beginPath()
            p.moveTo(x, yy)
            p.curveTo(x + side * 0.5 * s, yy + 0.1 * s, x + side * 0.7 * s, yy + 0.45 * s, x + side * 0.75 * s, yy + 0.6 * s)
            p.curveTo(x + side * 0.35 * s, yy + 0.55 * s, x + side * 0.1 * s, yy + 0.3 * s, x, yy)
            c.drawPath(p, stroke=0, fill=1)
        c.restoreState()

    def cover(self, title, subtitle, contents: list[str]):
        """Standard first page: product cover + what's inside."""
        c = self.c
        W, H = self.W, self.H
        c.setFillColor(CREAM)
        c.rect(0, H * 0.42, W, H * 0.58, stroke=0, fill=1)
        self.leaf(W / 2, H * 0.80, 14)
        self.label(W / 2, H * 0.74, SHOP_NAME, self.accent, 9, "center")
        # wrap long title on two lines if needed
        size = 46
        words = title.split()
        lines = [title]
        if pdfmetrics.stringWidth(title, SERIF, size) > W - 2 * MARGIN - 40:
            mid = len(words) // 2
            lines = [" ".join(words[:mid]), " ".join(words[mid:])]
        y = H * 0.64
        for ln in lines:
            self.text(W / 2, y, ln, SERIF, size, INK, "center")
            y -= size * 1.05
        self.text(W / 2, y - 6, subtitle, ITALIC, 13, MUTED, "center")
        # contents
        self.label(W / 2, H * 0.34, "What's inside", self.accent, 9, "center")
        y = H * 0.34 - 26
        for item in contents:
            self.text(W / 2, y, item, SANS, 11, INK, "center")
            y -= 18
        self.text(W / 2, MARGIN + 14, "Print at 100% / \"actual size\". Undated so you can start any time.", SANS_LIGHT, 8.5, MUTED, "center")
        self.footer()
        c.showPage()
        self.reset()


def build(slug: str, title: str, draw_fn, sizes=("letter", "a4"), accent=0, landscape_pages=False):
    """Build one PDF per paper size into products/<slug>/<slug>-<size>.pdf.
    draw_fn(page) draws all pages using page.finish() between them."""
    out = OUT_DIR / slug
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    for sz in sizes:
        size = SIZES[sz]
        if landscape_pages:
            size = landscape(size)
        path = out / f"{slug}-{sz}.pdf"
        c = canvas.Canvas(str(path), pagesize=size)
        c.setTitle(f"{title} — {SHOP_NAME}")
        c.setAuthor(SHOP_NAME)
        c.setSubject(SHOP_TAGLINE)
        page = Page(c, size, title, accent)
        draw_fn(page)
        c.save()
        paths.append(path)
        print("wrote", path.relative_to(ROOT))
    return paths


def render_previews(pdf_path, out_dir=None, dpi=110):
    """Render every page to PNG for checking the design (uses pdftoppm)."""
    pdf_path = Path(pdf_path)
    out_dir = Path(out_dir or pdf_path.parent / "preview")
    out_dir.mkdir(parents=True, exist_ok=True)
    os.system(f'pdftoppm -png -r {dpi} "{pdf_path}" "{out_dir / pdf_path.stem}"')
    return sorted(out_dir.glob(f"{pdf_path.stem}*.png"))
