#!/usr/bin/env python3
"""Generate a background raster with Flux Schnell via NVIDIA NIM (free tier).

This is the ONLY step that needs an external key (NVIDIA, free). Everything else
in the pipeline is done by Claude in-context.

Usage:
    python scripts/gen_raster.py --prompt "..." --seed 1 --out output/raster_1.png
    python scripts/gen_raster.py --prompt "..." --width 1024 --height 1024 --out ...
"""

from __future__ import annotations

import argparse
import base64
import os
import sys

import requests

NIM_URL = "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-schnell"


def _load_env():
    """Tiny .env loader so users don't need python-dotenv installed."""
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(here, ".env")
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def _extract_b64(data: dict) -> str:
    if "image" in data:
        return data["image"]
    if data.get("artifacts"):
        art = data["artifacts"][0]
        return art.get("base64") or art.get("b64_json") or art["image"]
    raise SystemExit(f"Unexpected NIM response shape: keys={list(data)}")


def main() -> int:
    _load_env()
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=1024)
    ap.add_argument("--height", type=int, default=1024)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--steps", type=int, default=4)
    args = ap.parse_args()

    key = os.environ.get("NVIDIA_API_KEY", "")
    if not key:
        raise SystemExit(
            "NVIDIA_API_KEY not set. Copy .env.example to .env and add your free "
            "key from build.nvidia.com."
        )

    headers = {
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    body = {
        "prompt": args.prompt,
        "cfg_scale": 0,  # Schnell ignores this; positive prompt only
        "width": args.width,
        "height": args.height,
        "seed": args.seed,
        "steps": args.steps,
    }
    # NIM can be slow/flaky — retry with backoff before giving up.
    import time
    resp = None
    last = ""
    for attempt in range(1, 4):
        try:
            resp = requests.post(NIM_URL, headers=headers, json=body, timeout=180)
            if resp.status_code == 200:
                break
            last = f"HTTP {resp.status_code}: {resp.text[:300]}"
        except requests.exceptions.RequestException as e:
            last = str(e)
        if attempt < 3:
            wait = attempt * 5
            print(f"  NIM attempt {attempt} failed ({last[:80]}); retrying in {wait}s…")
            time.sleep(wait)
    if resp is None or resp.status_code != 200:
        raise SystemExit(f"NIM failed after 3 attempts: {last}")

    png = base64.b64decode(_extract_b64(resp.json()))
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "wb") as f:
        f.write(png)
    print(f"OK raster saved -> {args.out} ({len(png)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
