#!/usr/bin/env python3
"""Render a finished HTML card to PNG via headless Chromium (Playwright).

Claude fills a template's {{TOKENS}} itself, writes the resulting HTML to a file,
then calls this script to screenshot it. This script is purely mechanical — no
design decisions live here.

Usage:
    python scripts/render.py --html output/_card_1.html --width 1080 --height 1350 --out output/composed_1.png

There's also a convenience mode that fills a template + a tokens JSON for you:
    python scripts/render.py --template templates/hero.html --tokens output/tokens_1.json \
        --raster output/raster_1.png --width 1080 --height 1350 --out output/composed_1.png
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys

from playwright.sync_api import sync_playwright


def _expand_lists(html: str, tokens: dict) -> str:
    """Expand repeatable blocks: {{#ITEMS}} ... {{field}} ... {{/ITEMS}} where
    tokens["ITEMS"] is a list of dicts. Lets the agent emit compact JSON (an array)
    instead of authoring repeated HTML — the token-economy win for variable-length
    content (stat cards, timeline steps, list rows, comic panels…).
    """
    def repl(m):
        name, inner = m.group(1), m.group(2)
        items = tokens.get(name)
        if not isinstance(items, list):
            return ""  # block with no matching array -> drop it
        rendered = []
        for it in items:
            block = inner
            if isinstance(it, dict):
                for k, v in it.items():
                    block = block.replace("{{" + k + "}}", str(v))
            else:
                block = block.replace("{{.}}", str(it))
            rendered.append(block)
        return "".join(rendered)

    return re.sub(r"\{\{#(\w+)\}\}(.*?)\{\{/\1\}\}", repl, html, flags=re.DOTALL)


def fill(template_html: str, tokens: dict) -> str:
    out = _expand_lists(template_html, tokens)          # repeatable blocks first
    for k, v in tokens.items():                          # then scalar tokens
        if not isinstance(v, (list, dict)):
            out = out.replace("{{" + k + "}}", str(v))
    return out


def raster_data_uri(path: str) -> str:
    b64 = base64.standard_b64encode(open(path, "rb").read()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def html_to_png(html: str, width: int, height: int, out: str, scale: int = 2) -> None:
    # scale = device pixel ratio. The layout is authored in CSS px (1080x1350); scale=2
    # supersamples to a 2160x2700 PNG — crisp on Retina / when zoomed, posts cleanly.
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=scale)
        # 'load' not 'networkidle': the Google Fonts CDN can keep a connection open and
        # stall networkidle. Load the DOM, then settle fonts; if the CDN is down, text
        # degrades to the system fallback rather than hanging the render.
        page.set_content(html, wait_until="load")
        try:
            page.wait_for_function("document.fonts.ready.then(()=>true)", timeout=4000)
        except Exception:
            pass
        page.wait_for_timeout(500)  # let web fonts paint
        page.screenshot(path=out, clip={"x": 0, "y": 0, "width": width, "height": height})
        browser.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", help="path to a fully-filled HTML file")
    ap.add_argument("--template", help="path to a template with {{TOKENS}}")
    ap.add_argument("--tokens", help="path to a JSON dict of token->value")
    ap.add_argument("--raster", help="path to raster PNG (injected as {{RASTER}} data URI)")
    ap.add_argument("--width", type=int, required=True)
    ap.add_argument("--height", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--scale", type=int, default=2, help="device pixel ratio (2 = crisp 2x supersample)")
    args = ap.parse_args()

    if args.html:
        html = open(args.html).read()
    elif args.template and args.tokens:
        tokens = json.load(open(args.tokens))
        if args.raster:
            tokens["RASTER"] = raster_data_uri(args.raster)
        html = fill(open(args.template).read(), tokens)
    else:
        raise SystemExit("Provide either --html, or both --template and --tokens.")

    html_to_png(html, args.width, args.height, args.out, scale=args.scale)
    print(f"OK composed saved -> {args.out} ({args.width*args.scale}x{args.height*args.scale})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
