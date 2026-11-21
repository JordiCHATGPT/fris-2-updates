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
for i, m in enumerate(re.finditer(r"data:image/(?:png|jpeg|webp);base64,", source)):
    print("SOURCE CONTEXT", i, repr(source[max(0, m.start() - 220):m.start()]))
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
print("Using separate historic assets: navbar, hero buttons, desk, skyline")
def crop_image(name, image, box=None):
    out = image.crop(box) if box else image
    target = root / "preview" / "art" / (name + ".webp")
    target.parent.mkdir(parents=True, exist_ok=True)
    out.save(target, "WEBP", quality=96, method=6)
    print("Created", target, out.size, target.stat().st_size)
if len(images) != 4:
    raise RuntimeError("Unexpected original image inventory")
navigation, cards, desk, skyline = images
crop_image("skyline", skyline)
crop_image("lessons", cards, (0, 0, 341, cards.height))
crop_image("practice", cards, (341, 0, 683, cards.height))
crop_image("repeat", cards, (683, 0, 1024, cards.height))
crop_image("desk", desk)
crop_image("navigation", navigation)

file = root / "preview" / "index.html"
html = file.read_text(encoding="utf-8")
# The first successful rebuild already installed these independent image slots.
if 'src="art/skyline.webp"' not in html:
    raise RuntimeError("Expected new component header not found")
for name in ("lessons","practice","repeat","desk"):
    if f'src="art/{name}.webp"' not in html:
        raise RuntimeError("Missing independent artwork component " + name)
extra = """
<style id="approved-art">
header.hero{height:auto;aspect-ratio:1024/442;max-height:none;flex-shrink:0}
.hero-photo{display:block;width:100%;height:100%;object-fit:fill}
.home-panel{background:#fffaf1}
.home-actions{padding:12px 13px 8px;gap:4px}
.tile-illustration{width:100%;height:auto;aspect-ratio:341/274;object-fit:contain;filter:none}
.footer-illustration{display:block;width:100%;height:auto;aspect-ratio:1024/141;object-fit:cover;margin-top:5px}
.greeting{padding:8px 12px 0}
.greeting h1{font-family:"Segoe Script","Brush Script MT","Comic Sans MS",cursive;font-weight:900;font-style:italic;font-size:clamp(34px,9vw,52px)}
.tile-label{font-family:"Segoe Script","Brush Script MT","Comic Sans MS",cursive}
.home-action{min-height:0}
.progress-wrap{margin-top:auto;padding:14px 28px 9px}
@media(max-height:720px){header.hero{height:auto}.footer-illustration{height:auto}.tile-illustration{height:auto}}
</style>
"""
html = re.sub(r"<style id=\"approved-art\">.*?</style>", "", html, flags=re.S)\nhtml = html.replace("</head>", extra + "</head>", 1)
file.write_text(html, encoding="utf-8")
print("Finished HTML", len(html))
