#!/usr/bin/env python3
"""Independent vision critic — meta/llama-3.2-90b-vision-instruct via NVIDIA NIM.

Why a separate model: in Claude-as-brain mode the designer and judge were the same
session (self-grading bias). This script judges the composed image with a DIFFERENT
model, so the verdict is independent. It also keeps the image out of Claude's context.

Usage:
    python scripts/critique.py --image output/composed_1.png --brief output/brief.txt \
        --brand brand.yaml --out output/critique_1.json

Reads the same rubric the human uses (see eval/README.md). Returns scores
JSON to --out (and stdout). Average + ship verdict are computed in Python, not trusted
to the model.
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import os
import re
import sys

import requests

NIM_CHAT_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MODEL = "meta/llama-3.2-90b-vision-instruct"
BASE_DIMENSIONS = [
    "subject_match",
    "mood_match",
    "composition_quality",
    "text_readability",
    "brand_consistency",
]
# added only when a reference template is supplied
TEMPLATE_DIMENSION = "template_fidelity"
# The binding limit is the model's 32768-token context: inline base64 counts as tokens
# (~3 chars/token). Keep the image small so b64 + prompt + completion fit comfortably.
MAX_B64 = 60_000   # ~20K tokens for the image, leaving room for prompt + 700 completion


def _load_env():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(here, ".env")
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def _downscaled_jpeg_b64(image_path: str, max_b64: int = MAX_B64, max_dim: int = 512) -> str:
    """Downscale to <=max_dim px long side as JPEG so it fits the token budget."""
    try:
        from PIL import Image
    except ImportError:
        raise SystemExit("Pillow needed: pip install pillow")
    img = Image.open(image_path).convert("RGB")
    long_side = max(img.size)
    if long_side > max_dim:
        scale = max_dim / long_side
        img = img.resize((int(img.width * scale), int(img.height * scale)))
    quality = 75
    while True:
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality)
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        if len(b64) <= max_b64 or quality <= 30:
            return b64
        quality -= 10


def _rubric_prompt(brief: str, brand: str, has_reference: bool) -> str:
    ref_block = ""
    tf_line = ""
    tf_json = ""
    if has_reference:
        ref_block = (
            "\nThere are TWO images. The FIRST is a REFERENCE TEMPLATE (the structure to "
            "match). The SECOND is the OUTPUT being judged. Judge STRUCTURE against the "
            "reference (layout topology, how elements are grouped/arranged) — NOT colour or "
            "font, since style follows the brand, not the reference.\n"
        )
        tf_line = ("- template_fidelity: how closely the OUTPUT's structure/layout matches the "
                   "REFERENCE template (ignore colour/font/brand)\n")
        tf_json = '"template_fidelity":int,'
    return f"""You are an independent art director judging a finished social-media card
against the brief that commissioned it. Be demanding but fair.
{ref_block}
THE BRIEF:
{brief}

BRAND TOKENS (for brand_consistency):
{brand or "(none provided)"}

Score each 1-10 (10 = excellent):
- subject_match: shows what the brief asked, including any must_include
- mood_match: matches the intended tone/mood
- composition_quality: balanced, clear focal area, room for text, uncluttered
- text_readability: headline/body legible vs background (contrast, size)
- brand_consistency: palette/font/brand label match the brand tokens
{tf_line}
Also list any must_avoid items that appear (must_avoid_violations).

Return ONLY a JSON object, no prose:
{{"subject_match":int,"mood_match":int,"composition_quality":int,
"text_readability":int,"brand_consistency":int,{tf_json}
"must_avoid_violations":[string],
"verdict":"ship|redo_raster|redo_compose|redo_both",
"feedback":"one or two specific, actionable sentences"}}"""


def _extract_json(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise SystemExit(f"Critic did not return JSON. Raw: {text[:400]}")
    return json.loads(m.group(0))


def main() -> int:
    _load_env()
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--brief", required=True, help="path to brief text/json file")
    ap.add_argument("--brand", default="", help="path to brand.yaml (optional)")
    ap.add_argument("--reference", default="", help="reference template image to score structure against (optional)")
    ap.add_argument("--out", default="", help="where to write scores JSON (else stdout)")
    ap.add_argument("--threshold", type=float, default=7.5)
    ap.add_argument("--timeout", type=int, default=120)
    args = ap.parse_args()

    key = os.environ.get("NVIDIA_API_KEY", "")
    if not key:
        raise SystemExit("NVIDIA_API_KEY not set (same key as image gen).")

    brief = open(args.brief).read() if os.path.exists(args.brief) else args.brief
    brand = open(args.brand).read() if args.brand and os.path.exists(args.brand) else ""

    has_ref = bool(args.reference and os.path.exists(args.reference))
    dimensions = BASE_DIMENSIONS + ([TEMPLATE_DIMENSION] if has_ref else [])
    # two images must share the 32K-token budget, so cap each tighter when both are sent
    per_cap, per_dim = (28_000, 400) if has_ref else (MAX_B64, 512)

    prompt = _rubric_prompt(brief, brand, has_ref)
    # NVIDIA VLM convention: image embedded as an <img> data-URL inside the content.
    content = prompt
    if has_ref:
        ref_b64 = _downscaled_jpeg_b64(args.reference, max_b64=per_cap, max_dim=per_dim)
        content += f'\nREFERENCE TEMPLATE:\n<img src="data:image/jpeg;base64,{ref_b64}" />'
    out_b64 = _downscaled_jpeg_b64(args.image, max_b64=per_cap, max_dim=per_dim)
    content += f'\nOUTPUT TO JUDGE:\n<img src="data:image/jpeg;base64,{out_b64}" />'

    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": content}],
        "max_tokens": 700,
        "temperature": 0.2,
        "top_p": 0.9,
    }
    resp = requests.post(
        NIM_CHAT_URL,
        headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
        json=body,
        timeout=args.timeout,
    )
    if resp.status_code != 200:
        raise SystemExit(f"NIM critic error {resp.status_code}: {resp.text[:500]}")

    raw = resp.json()["choices"][0]["message"]["content"]
    data = _extract_json(raw)

    # compute average + verdict ourselves (don't trust model arithmetic)
    scores = {d: float(data.get(d, 0)) for d in dimensions}
    average = round(sum(scores.values()) / len(scores), 2)
    violations = data.get("must_avoid_violations", []) or []
    if violations:
        verdict = data.get("verdict") if data.get("verdict") in (
            "redo_raster", "redo_compose", "redo_both") else "redo_both"
    elif average >= args.threshold:
        verdict = "ship"
    else:
        verdict = data.get("verdict") or "redo_both"

    result = {
        "model": MODEL,
        "scores": scores,
        "average": average,
        "must_avoid_violations": violations,
        "verdict": verdict,
        "feedback": data.get("feedback", ""),
        "threshold": args.threshold,
    }
    out_str = json.dumps(result, indent=2)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w") as f:
            f.write(out_str)
    print(out_str)
    return 0


if __name__ == "__main__":
    sys.exit(main())
