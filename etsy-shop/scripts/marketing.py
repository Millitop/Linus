"""Generate Etsy listing images and Pinterest pins for each product.

Reads page renders from products/<slug>/preview/*.png and text from
listings/listings.json, lays them out with HTML and screenshots them
with headless Chromium.

    python3 scripts/marketing.py              # all products
    python3 scripts/marketing.py budget-planner

Output:
    marketing/<slug>/etsy-01-hero.png ... (2700x2025, Etsy's 4:3 size)
    marketing/<slug>/pin-1.png ...        (1000x1500, Pinterest 2:3)
"""
from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

import subprocess

CHROME = "/opt/pw-browsers/chromium"

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "fonts"
OUT = ROOT / "marketing"

PRODUCTS = {
    # slug: (display name, short line, accent hex, accent light, format note)
    "undated-planner": ("Daily & Weekly Planner", "Undated · start any day", "#9CAF98", "#DDE5DA", "US Letter + A4"),
    "budget-planner": ("Budget Planner", "Take calm control of your money", "#C98B6B", "#F1DED3", "US Letter + A4"),
    "habit-wellness-tracker": ("Habit & Wellness Tracker", "Small steps, every day", "#A7B6C4", "#E1E7ED", "US Letter + A4"),
    "meal-planner": ("Meal Planner & Grocery List", "Plan the week, shop once", "#9CAF98", "#F1DED3", "US Letter + A4"),
    "digital-planner-2027": ("2027 Digital Planner", "Hyperlinked for GoodNotes & iPad", "#9CAF98", "#DDE5DA", "iPad · GoodNotes · Notability"),
    "life-planner-bundle": ("Life Planner Bundle", "Planner + Budget + Habits + Meals", "#C98B6B", "#E9DCC6", "4 planners · US Letter + A4"),
}
BUNDLE_PARTS = ["undated-planner", "budget-planner", "habit-wellness-tracker", "meal-planner"]


def data_uri(p: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()


def pages_for(slug: str) -> list[Path]:
    if slug == "life-planner-bundle":
        parts = [pages_for(s) for s in BUNDLE_PARTS]
        covers = [p[0] for p in parts]
        rest = [pg for p in parts for pg in p[1:3]]
        return covers + rest
    prev = ROOT / "products" / slug / "preview"
    files = sorted(prev.glob("*.png"))
    # printable products: prefer letter renders
    letter = [f for f in files if "letter" in f.name]
    return letter or files


def css(accent, light):
    return f"""
@font-face {{ font-family: 'DM Serif'; src: url('file://{FONTS}/DMSerifDisplay-Regular.ttf'); }}
@font-face {{ font-family: 'Lato'; src: url('file://{FONTS}/Lato-Regular.ttf'); font-weight: 400; }}
@font-face {{ font-family: 'Lato'; src: url('file://{FONTS}/Lato-Bold.ttf'); font-weight: 700; }}
@font-face {{ font-family: 'Lato'; src: url('file://{FONTS}/Lato-Light.ttf'); font-weight: 300; }}
@font-face {{ font-family: 'Lato'; src: url('file://{FONTS}/Lato-Italic.ttf'); font-style: italic; }}
:root {{ --accent: {accent}; --light: {light}; --ink: #3B3A36; --muted: #8A857C; --cream: #F6F1E9; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: 'Lato', sans-serif; color: var(--ink); background: var(--cream); overflow: hidden; }}
.serif {{ font-family: 'DM Serif', serif; font-weight: 400; }}
.label {{ font-weight: 700; letter-spacing: .22em; text-transform: uppercase; color: var(--accent); }}
.sheet {{ position: absolute; background: #fff; box-shadow: 0 30px 60px rgba(59,58,54,.16), 0 6px 14px rgba(59,58,54,.08); border-radius: 6px; overflow: hidden; }}
.sheet img {{ width: 100%; height: 100%; object-fit: cover; object-position: top; display: block; }}
.pill {{ display: inline-block; background: #fff; border-radius: 999px; padding: .5em 1.3em; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; color: var(--ink); }}
.blob {{ position: absolute; border-radius: 50%; background: var(--light); }}
"""


def sheet(img, x, y, w, h, rot=0, z=1):
    return f'<div class="sheet" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;transform:rotate({rot}deg);z-index:{z}"><img src="{img}"></div>'


def sheet_dims(slug, w):
    # page aspect: Letter portrait 8.5x11, digital planner landscape 1366x1024
    return (w, w * 1024 / 1366) if slug == "digital-planner-2027" else (w, w * 11 / 8.5)


def leaf_svg(color, size=60):
    return f'''<svg width="{size}" height="{size*1.6}" viewBox="0 0 40 64" fill="{color}"><rect x="19.4" y="4" width="1.2" height="58" fill="{color}"/>
<path d="M20 50 C28 49 33 43 34 38 C27 38 22 43 20 50Z"/><path d="M20 38 C12 37 7 31 6 26 C13 26 18 31 20 38Z"/>
<path d="M20 26 C28 25 33 19 34 14 C27 14 22 19 20 26Z"/><path d="M20 14 C13 13 9 8 8 4 C14 4 18 8 20 14Z"/></svg>'''


# ---------------------------------------------------------------- Etsy images
def etsy_hero(slug, pages, name, line, fmt, n_pages):
    W, H = 2700, 2025
    imgs = [data_uri(p) for p in pages]
    a, l = PRODUCTS[slug][2], PRODUCTS[slug][3]
    if slug == "digital-planner-2027":
        sw, sh = sheet_dims(slug, 1500)
        stack = sheet(imgs[min(1, len(imgs)-1)], 1080, 470, sw * .82, sh * .82, 4, 1) + sheet(imgs[0], 1000, 560, sw, sh, -2, 2)
    else:
        sw, sh = sheet_dims(slug, 900)
        pick = [imgs[i % len(imgs)] for i in (2, 1, 0)] if len(imgs) > 2 else imgs[::-1]
        stack = (sheet(pick[0], 1700, 300, sw, sh, 7, 1) + sheet(pick[1], 1380, 380, sw, sh, -3, 2)
                 + sheet(pick[-1], 1100, 480, sw, sh, -9, 3)) if len(pick) >= 3 else sheet(pick[0], 1300, 400, sw, sh, -4, 2)
    body = f'''
<div class="blob" style="width:1500px;height:1500px;left:1250px;top:250px"></div>
{stack}
<div style="position:absolute;left:170px;top:330px;width:900px;z-index:5">
  {leaf_svg(a, 54)}
  <div class="label" style="font-size:34px;margin:40px 0 30px">Linnea Paper Co.</div>
  <div class="serif" style="font-size:{150 if len(name) < 18 else 124}px;line-height:1.02">{name}</div>
  <div style="font-style:italic;font-size:48px;color:var(--muted);margin-top:40px">{line}</div>
  <div style="margin-top:80px;display:flex;flex-direction:column;gap:26px;font-size:40px">
    <div><span class="pill" style="font-size:30px">{n_pages}</span></div>
    <div><span class="pill" style="font-size:30px">{fmt}</span></div>
    <div><span class="pill" style="font-size:30px">Instant download</span></div>
  </div>
</div>'''
    return W, H, body


def etsy_inside(slug, pages, name):
    W, H = 2700, 2025
    imgs = [data_uri(p) for p in pages]
    land = slug == "digital-planner-2027"
    cols = 3 if land else 6
    n = min(len(imgs), cols * 2 if land else 12)
    tw = 700 if land else 360
    th = tw * (1024 / 1366 if land else 11 / 8.5)
    gap = 40
    gw = cols * tw + (cols - 1) * gap
    x0 = (W - gw) / 2
    y0 = 430
    cells = ""
    for i in range(n):
        r, cidx = divmod(i, cols)
        cells += sheet(imgs[i], x0 + cidx * (tw + gap), y0 + r * (th + 60), tw, th)
    body = f'''
<div style="position:absolute;top:150px;width:100%;text-align:center">
  <div class="label" style="font-size:34px">What's inside</div>
  <div class="serif" style="font-size:110px;margin-top:20px">{name}</div>
</div>{cells}'''
    return W, H, body


def etsy_how(slug, fmt):
    W, H = 2700, 2025
    digital = slug == "digital-planner-2027"
    steps = (["Purchase & download the PDF", "Import into GoodNotes, Notability or any PDF app", "Tap the tabs to jump between months & weeks", "Write with your Apple Pencil — reuse forever"]
             if digital else
             ["Purchase & download instantly", "Choose US Letter or A4", "Print at home or at a print shop", "Print again whenever you need more"])
    items = "".join(f'''<div style="display:flex;align-items:center;gap:50px;margin-bottom:70px">
      <div class="serif" style="width:150px;height:150px;border-radius:50%;background:var(--light);display:flex;align-items:center;justify-content:center;font-size:80px;flex:none">{i+1}</div>
      <div style="font-size:62px">{s}</div></div>''' for i, s in enumerate(steps))
    body = f'''
<div style="position:absolute;inset:120px;background:#fff;border-radius:40px;padding:140px 180px">
  <div class="label" style="font-size:34px">How it works</div>
  <div class="serif" style="font-size:120px;margin:24px 0 100px">Instant download</div>
  {items}
  <div style="position:absolute;bottom:120px;left:180px;font-size:38px;color:var(--muted)">{fmt} · Personal use · No physical item will be shipped</div>
</div>'''
    return W, H, body


# ---------------------------------------------------------------- Pins
def pin(slug, pages, name, line, variant, cta="Instant download on Etsy"):
    W, H = 1000, 1500
    imgs = [data_uri(p) for p in pages]
    a = PRODUCTS[slug][2]
    land = slug == "digital-planner-2027"
    if variant == 1:  # big title top, stacked pages below
        sw, sh = sheet_dims(slug, 720 if land else 500)
        pages_html = (sheet(imgs[min(1, len(imgs)-1)], 190, 600, sw, sh, 5, 1) + sheet(imgs[0], 60, 720, sw, sh, -3, 2)) if land else \
            (sheet(imgs[min(2, len(imgs)-1)], 400, 560, sw, sh, 6, 1) + sheet(imgs[0], 120, 610, sw, sh, -5, 2))
        body = f'''<div class="blob" style="width:1100px;height:1100px;left:-50px;top:620px"></div>
<div style="position:absolute;top:90px;width:100%;text-align:center;padding:0 70px;z-index:5">
  <div class="label" style="font-size:22px">{"Digital · Hyperlinked" if land else "Printable · Minimal"}</div>
  <div class="serif" style="font-size:{104 if len(name) < 20 else 86}px;line-height:1.02;margin-top:22px">{name}</div>
  <div style="font-style:italic;font-size:34px;color:var(--muted);margin-top:24px">{line}</div>
</div>{pages_html}
<div style="position:absolute;bottom:56px;width:100%;text-align:center;z-index:5"><span class="pill" style="font-size:22px;background:var(--ink);color:#fff">{cta}</span></div>'''
    elif variant == 2:  # one big page + label bar
        sw, sh = sheet_dims(slug, 880 if land else 700)
        idx = min(1, len(imgs) - 1)
        body = f'''{sheet(imgs[idx], (W - sw) / 2, 120, sw, sh)}
<div style="position:absolute;left:0;right:0;bottom:0;height:{1500 - 120 - sh + 60}px;background:var(--light)"></div>
<div style="position:absolute;bottom:70px;width:100%;text-align:center;padding:0 60px;z-index:5">
  <div class="serif" style="font-size:{80 if len(name) < 22 else 66}px;line-height:1.05">{name}</div>
  <div class="label" style="font-size:22px;margin-top:20px;color:var(--ink)">{line}</div>
</div>'''
    else:  # grid of pages: "X pages inside"
        tw = 400 if land else 290
        th = tw * (1024 / 1366 if land else 11 / 8.5)
        cells = ""
        n = 4
        cols = 2
        gx = (W - cols * tw - 50) / 2
        for i in range(min(n, len(imgs))):
            r, cc = divmod(i, cols)
            cells += sheet(imgs[i], gx + cc * (tw + 50), 430 + r * (th + 50), tw, th)
        body = f'''
<div style="position:absolute;top:90px;width:100%;text-align:center;padding:0 60px">
  {leaf_svg(a, 34)}
  <div class="serif" style="font-size:{76 if len(name) < 22 else 62}px;line-height:1.05;margin-top:18px">{name}</div>
  <div class="label" style="font-size:20px;margin-top:18px">See every page inside</div>
</div>{cells}
<div style="position:absolute;bottom:56px;width:100%;text-align:center"><span class="pill" style="font-size:22px;background:var(--ink);color:#fff">{cta}</span></div>'''
    return W, H, body


def render(W, H, body, accent, light, out_path):
    html = f"<!doctype html><html><head><meta charset='utf-8'><style>{css(accent, light)}</style></head><body style='width:{W}px;height:{H}px;position:relative'>{body}</body></html>"
    tmp = out_path.with_suffix(".html")
    tmp.write_text(html)
    subprocess.run([CHROME, "--headless", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                    "--allow-file-access-from-files", "--virtual-time-budget=1500",
                    f"--window-size={W},{H}", f"--screenshot={out_path}", f"file://{tmp}"],
                   check=True, capture_output=True)
    tmp.unlink()
    print("wrote", out_path.relative_to(ROOT))


def page_count_label(slug):
    import pypdf
    if slug == "life-planner-bundle":
        n = sum(page_count_label_n(s) for s in BUNDLE_PARTS)
    else:
        n = page_count_label_n(slug)
    return f"{n} pages" if n else "Printable PDF"


def page_count_label_n(slug):
    import pypdf
    d = ROOT / "products" / slug
    pdfs = sorted(d.glob("*letter.pdf")) or sorted(d.glob("*.pdf"))
    return len(pypdf.PdfReader(pdfs[0]).pages) if pdfs else 0


def main(slugs):
    if True:
        for slug in slugs:
            pages = pages_for(slug)
            if not pages:
                print("skip (no previews):", slug)
                continue
            name, line, a, l, fmt = PRODUCTS[slug]
            out = OUT / slug
            out.mkdir(parents=True, exist_ok=True)
            n_label = page_count_label(slug)
            jobs = [
                ("etsy-01-hero.png", etsy_hero(slug, pages, name, line, fmt, n_label)),
                ("etsy-02-inside.png", etsy_inside(slug, pages, name)),
                ("etsy-03-how.png", etsy_how(slug, fmt)),
                ("pin-1.png", pin(slug, pages, name, line, 1)),
                ("pin-2.png", pin(slug, pages, name, line, 2)),
                ("pin-3.png", pin(slug, pages, name, line, 3)),
            ]
            # extra Etsy images: single large pages
            singles = pages[1:5] if slug != "life-planner-bundle" else []
            for i, pg in enumerate(singles):
                W, H = 2700, 2025
                sw, sh = sheet_dims(slug, 2000 if slug == "digital-planner-2027" else 1350)
                if sh > H - 160:
                    sh = H - 160
                    sw = sh * (1366 / 1024 if slug == "digital-planner-2027" else 8.5 / 11)
                body = f'<div class="blob" style="width:1700px;height:1700px;left:500px;top:160px"></div>' + sheet(data_uri(pg), (W - sw) / 2, (H - sh) / 2, sw, sh)
                jobs.append((f"etsy-{i + 4:02d}-page.png", (W, H, body)))
            for fname, (W, H, body) in jobs:
                render(W, H, body, a, l, out / fname)


if __name__ == "__main__":
    main(sys.argv[1:] or list(PRODUCTS))
