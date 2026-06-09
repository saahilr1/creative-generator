#!/usr/bin/env python3
"""Level-A eval: does the Llama critic agree with the human?

Reads your human scores (eval/calibration_scores.csv) and the critic's saved JSON for
each example (eval/<example_id>.critique.json), then prints agreement metrics. Stdlib
only — no numpy/scipy.

Per example, save the critic output next to your scores:
    cp output/critique_1.json eval/ex01.critique.json   (matching example_id)

Run:
    python scripts/compare_eval.py --human eval/calibration_scores.csv --critique-dir eval
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys

DIMS = ["subject_match", "mood_match", "composition_quality",
        "text_readability", "brand_consistency", "template_fidelity"]


def _num(v):
    """Parse the score from a '<score> | <feedback>' cell; None if blank/missing."""
    if v is None:
        return None
    head = str(v).split("|", 1)[0].strip()
    try:
        return float(head)
    except ValueError:
        return None


def _fb(v):
    """Parse the feedback from a '<score> | <feedback>' cell ('' if none)."""
    if v is None or "|" not in str(v):
        return ""
    return str(v).split("|", 1)[1].strip()


def _ranks(xs):
    """Average ranks (1-based), ties share the mean rank."""
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(xs):
        j = i
        while j + 1 < len(xs) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def _pearson(a, b):
    n = len(a)
    if n < 2:
        return float("nan")
    ma, mb = sum(a) / n, sum(b) / n
    cov = sum((a[i] - ma) * (b[i] - mb) for i in range(n))
    va = sum((x - ma) ** 2 for x in a) ** 0.5
    vb = sum((x - mb) ** 2 for x in b) ** 0.5
    return cov / (va * vb) if va and vb else float("nan")


def spearman(a, b):
    return _pearson(_ranks(a), _ranks(b))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--human", default="eval/calibration_scores.csv")
    ap.add_argument("--critique-dir", default="eval")
    ap.add_argument("--out", default="eval/eval_comparison.csv", help="where to save the comparison CSV")
    ap.add_argument("--threshold", type=float, default=7.5)
    args = ap.parse_args()

    rows = list(csv.DictReader(open(args.human)))
    pairs = []  # (human_dict, critic_dict)
    skipped = []
    for r in rows:
        eid = (r.get("example_id") or "").strip()
        if not eid or not (r.get("subject_match") or "").strip():
            continue  # unscored row
        cpath = os.path.join(args.critique_dir, f"{eid}.critique.json")
        if not os.path.exists(cpath):
            skipped.append(eid)
            continue
        critic = json.load(open(cpath))
        pairs.append((r, critic))

    if not pairs:
        print("No matched example/critique pairs found. Score rows in the CSV and copy "
              "each critic JSON to eval/<example_id>.critique.json.")
        if skipped:
            print("Scored but missing critic JSON:", ", ".join(skipped))
        return 1

    n = len(pairs)

    # write the per-example, per-dimension comparison CSV into the eval folder
    comp_rows = []
    for h, c in pairs:
        eid = (h.get("example_id") or "").strip()
        for d in DIMS:
            hv, cv = _num(h.get(d)), _num(c["scores"].get(d))
            hfb = _fb(h.get(d))
            if hv is None and cv is None and not hfb:
                continue
            delta = round(cv - hv, 2) if (hv is not None and cv is not None) else ""
            comp_rows.append({"example_id": eid, "dimension": d,
                              "human": hv if hv is not None else "",
                              "critic": cv if cv is not None else "",
                              "delta_critic_minus_human": delta,
                              "human_feedback": hfb,
                              "critic_feedback": c.get("feedback", "") if d == DIMS[0] else ""})
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["example_id", "dimension", "human", "critic",
                                             "delta_critic_minus_human", "human_feedback",
                                             "critic_feedback"])
            w.writeheader()
            w.writerows(comp_rows)
        print(f"comparison CSV -> {args.out}\n")

    # per-dimension MAE
    print(f"=== Level-A: critic vs human  (n={n}) ===\n")
    print("Per-dimension MAE (target <= 1.5; only dims scored by both):")
    all_abs = []
    for d in DIMS:
        errs = [abs(_num(h.get(d)) - _num(c["scores"].get(d)))
                for h, c in pairs
                if _num(h.get(d)) is not None and _num(c["scores"].get(d)) is not None]
        all_abs += errs
        cell = f"{sum(errs)/len(errs):.2f} (n={len(errs)})" if errs else "— (no shared scores)"
        print(f"  {d:22s} {cell}")
    print(f"  {'OVERALL':22s} {sum(all_abs)/len(all_abs):.2f}\n" if all_abs else "")

    # rank correlation on averages over each example's human-scored dims (apples to apples)
    h_avg, c_avg = [], []
    for h, c in pairs:
        shared = [d for d in DIMS if _num(h.get(d)) is not None and _num(c["scores"].get(d)) is not None]
        if not shared:
            continue
        h_avg.append(sum(_num(h[d]) for d in shared) / len(shared))
        c_avg.append(sum(_num(c["scores"][d]) for d in shared) / len(shared))
    print(f"Spearman rank corr of averages (target >= 0.6): {spearman(h_avg, c_avg):.2f}\n")

    # ship-decision agreement
    def human_ship(h):
        return (h.get("human_ship") or "").strip().upper().startswith("Y")

    def critic_ship(c):
        return c.get("verdict") == "ship"

    tp = sum(1 for h, c in pairs if human_ship(h) and critic_ship(c))
    tn = sum(1 for h, c in pairs if not human_ship(h) and not critic_ship(c))
    fp = sum(1 for h, c in pairs if not human_ship(h) and critic_ship(c))
    fn = sum(1 for h, c in pairs if human_ship(h) and not critic_ship(c))
    acc = (tp + tn) / n
    prec = tp / (tp + fp) if (tp + fp) else float("nan")
    rec = tp / (tp + fn) if (tp + fn) else float("nan")
    print("Ship decision (vs human):")
    print(f"  agreement/accuracy (target >= 0.80): {acc:.2f}")
    print(f"  precision on 'ship' (target >= 0.80): {prec:.2f}  (passes junk if low)")
    print(f"  recall on 'ship'    (target >= 0.80): {rec:.2f}  (blocks good ones if low)")
    print(f"  confusion: TP={tp} TN={tn} FP={fp} FN={fn}")
    if skipped:
        print("\nNote: scored rows missing a critic JSON:", ", ".join(skipped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
