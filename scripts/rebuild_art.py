#!/usr/bin/env python3
"""Restore FRIS reference artwork as independent assets; keep controls as HTML."""
import base64
import io
import re
import subprocess
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parents[1]
historical = "db1319af4627a48b4c0f6f1d9b97616576ce21bf"
source = subprocess.check_output(["git", "show", f"{historical}:preview/index.html"], cwd=root).decode("utf-8")
matches = re.findall(r"data:image/(?:png|jpeg|webp);base64,([A-Za-z0-9+/=]+)", source)
if not matches:
    raise RuntimeError("No embedded art was found in the approved historic HTML")
images = []
for encoded in matches:
    try:
        images.append(Image.open(io.BytesIO(base64.b64decode(encoded))).convert("RGB"))
    except Exception:
        continue
if not images:
    raise RuntimeError("Could not decode historic art")
print("All available historical images:", [(i, x.size) for i, x in enumerate(images)])
im = max(images, key=lambda x: x.width * x.height)
print("Original artwork resolution:", im.size)
sx, sy = im.width / 1024, im.height / 1536

def crop(name, box):
    coords = tuple(round(val * (sx if i % 2 == 0 else sy)) for i, val in enumerate(box))
    out = im.crop(coords)
    target = root / "preview" / "art" / (name + ".webp")
    target.parent.mkdir(parents=True, exist_ok=True)
    out.save(target, "WEBP", quality=94, method=6)
    print("Created", target, out.size)

crop("skyline", (0, 50, 1024, 482))
crop("lessons", (15, 700, 347, 925))
crop("practice", (346, 699, 671, 925))
crop("repeat", (680, 697, 1015, 925))
crop("desk", (0, 1136, 1024, 1399))

file = root / "preview" / "index.html"
html = file.read_text(encoding="utf-8")
html, n = re.subn(
    r'<header class="hero">.*?</header>',
    '<header class="hero"><img class="hero-photo" src="art/skyline.webp" alt="FRIS! je Duits op, Duitse skyline"></header>',
    html, count=1, flags=re.S)
if n != 1:
    raise RuntimeError("Header insertion point not found")
for name in ("lessons", "practice", "repeat"):
    replacement = f'<img class="tile-illustration" src="art/{name}.webp" alt="" loading="eager">'
    html, n = re.subn(r'<svg class="tile-illustration".*?</svg>', replacement, html, count=1, flags=re.S)
    if n != 1:
        raise RuntimeError("Art slot not found: " + name)
html, n = re.subn(r'<svg class="footer-illustration".*?</svg>',
                 '<img class="footer-illustration" src="art/desk.webp" alt="" loading="eager">',
                 html, count=1, flags=re.S)
if n != 1:
    raise RuntimeError("Footer insertion point not found")
extra = """
<style id="approved-art">
header.hero{height:auto;aspect-ratio:1024/432;max-height:none;flex-shrink:0}
.hero-photo{display:block;width:100%;height:100%;object-fit:fill}
.home-panel{background:#fffaf1}
.home-actions{padding:12px 13px 8px;gap:4px}
.tile-illustration{width:100%;height:auto;aspect-ratio:1.45;object-fit:contain;filter:none}
.footer-illustration{display:block;width:100%;height:auto;aspect-ratio:1024/263;object-fit:cover;margin-top:5px}
.greeting{padding:8px 12px 0}
.greeting h1{font-family:"Segoe Script","Brush Script MT","Comic Sans MS",cursive;font-weight:900;font-style:italic;font-size:clamp(34px,9vw,52px)}
.tile-label{font-family:"Segoe Script","Brush Script MT","Comic Sans MS",cursive}
.home-action{min-height:0}
.progress-wrap{margin-top:auto;padding:14px 28px 9px}
@media(max-height:720px){header.hero{height:auto}.footer-illustration{height:auto}.tile-illustration{height:auto}}
</style>
"""
html = html.replace("</head>", extra + "</head>", 1)
file.write_text(html, encoding="utf-8")
print("Finished HTML", len(html))
