#!/usr/bin/env python3
"""Independent eval for the FLUX BACKGROUND alone (not the final composite).

Why this exists: the main critic judges the finished card, so a weak/empty background
can hide behind good text. To tune Flux outputs (and a future LoRA) we must score the
raw raster on its own. Same independent model (Llama-3.2-90B-Vision via NIM).

Usage:
    python scripts/critique_bg.py --image output/voice_bg.png --brief output/voice_brief.txt \
        --brand brand.yaml --out output/bgcritique_voice.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import requests

# reuse helpers from the main critic
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from critique import _load_env, _downscaled_jpeg_b64, _extract_json, NIM_CHAT_URL, MODEL  # noqa: E402

BG_DIMENSIONS = ["brand_color_fit", "visual_interest", "theme_relevance", "foreground_safe"]


def _bg_prompt(brief: str, brand: str) -> str:
    return f"""You are judging ONLY a BACKGROUND image (a full-bleed backdrop that text and
graphics will later be layered ON TOP of). Do NOT expect any text in it.

THE POST BRIEF (for theme/colour intent):
{brief}

BRAND TOKENS:
{brand or "(none provided)"}

Score each 1-10 (10 = excellent) for a *background*:
- brand_color_fit: uses/evokes the brand palette (e.g. dark near-black + a warm accent); no off-brand colours
- visual_interest: has a deliberate, non-empty visual element/texture — NOT a plain flat fill; rewards subtle relevant motifs, penalises "empty black"
- theme_relevance: evokes the post's subject (e.g. voice / sound / signal) WITHOUT literal clichés
- foreground_safe: leaves clean negative space for text on top, is not too busy, and contains NO text/letters/logos

Return ONLY a JSON object, no prose:
{{"brand_color_fit":int,"visual_interest":int,"theme_relevance":int,"foreground_safe":int,
"feedback":"one or two specific, actionable sentences for the next Flux prompt"}}"""


def main() -> int:
    _load_env()
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--brief", required=True)
    ap.add_argument("--brand", default="")
    ap.add_argument("--out", default="")
    ap.add_argument("--threshold", type=float, default=7.0)
    ap.add_argument("--timeout", type=int, default=280)
    args = ap.parse_args()

    key = os.environ.get("NVIDIA_API_KEY", "")
    if not key:
        raise SystemExit("NVIDIA_API_KEY not set.")

    brief = open(args.brief).read() if os.path.exists(args.brief) else args.brief
    brand = open(args.brand).read() if args.brand and os.path.exists(args.brand) else ""
    b64 = _downscaled_jpeg_b64(args.image)

    content = f'{_bg_prompt(brief, brand)}\n<img src="data:image/jpeg;base64,{b64}" />'
    body = {"model": MODEL, "messages": [{"role": "user", "content": content}],
            "max_tokens": 500, "temperature": 0.2, "top_p": 0.9}
    resp = requests.post(NIM_CHAT_URL,
                         headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
                         json=body, timeout=args.timeout)
    if resp.status_code != 200:
        raise SystemExit(f"NIM bg-critic error {resp.status_code}: {resp.text[:400]}")

    data = _extract_json(resp.json()["choices"][0]["message"]["content"])
    scores = {d: float(data.get(d, 0)) for d in BG_DIMENSIONS}
    average = round(sum(scores.values()) / len(scores), 2)
    result = {"model": MODEL, "kind": "background", "scores": scores, "average": average,
              "pass": average >= args.threshold, "feedback": data.get("feedback", ""),
              "threshold": args.threshold}
    out_str = json.dumps(result, indent=2)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        open(args.out, "w").write(out_str)
    print(out_str)
    return 0


if __name__ == "__main__":
    sys.exit(main())
