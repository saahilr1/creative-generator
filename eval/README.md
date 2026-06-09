# Evaluation — score outputs, calibrate the critic

The pipeline ships with an independent vision critic (Llama-3.2-90B via NIM) that scores
every asset. A critic is only trustworthy if it agrees with you — so you keep a small set of
your own scores and check how closely the critic tracks them.

## Setup (once)
```
cp calibration_scores.template.csv calibration_scores.csv
```
Your `calibration_scores.csv` stays local (gitignored). Only this README + the template ship.

## Score an asset (1 row per asset)
Open `calibration_scores.csv` and add a row. In each of the 6 dimension columns, write
**`<score> | <feedback>`** (1–10) — the feedback is the signal for what to improve:

| Dimension | Score on |
|---|---|
| `subject_match` | shows what the brief asked |
| `mood_match` | matches the tone; the idea lands visually |
| `composition_quality` | balance + **use of space** (not empty, not cramped) |
| `text_readability` | legibility only |
| `brand_consistency` | palette / font / wordmark on-brand |
| `template_fidelity` | structure matches the reference (if any) |

Example cell: `7.5 | labels don't reuse the headline's terms; add direction`
Also fill `human_avg`, `human_ship` (Y/N), and `notes`.

## Measure (critic vs you)
```
python ../scripts/compare_eval.py --human calibration_scores.csv --critique-dir .
```
Writes `eval_comparison.csv` (per-dimension human · critic · delta · feedback) and prints
MAE (≤1.5), Spearman (≥0.6), ship-agreement (≥0.80). Group by dimension to see where the
process is weakest. If the critic misses your targets across ~30 assets, recalibrate its
prompt or swap the critic model.
