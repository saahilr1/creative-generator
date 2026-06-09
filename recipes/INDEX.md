# Recipe catalog — the agent reads this to pick a layout

The logic agent picks the best-fit recipe from the brief (or uses `format:` from INPUTS.md
if the user set one), then fills its slots with a compact JSON and renders. Free-form HTML
is the fallback only when nothing here fits.

Each recipe is `recipes/<name>.html` with `{{TOKENS}}` and `{{#LIST}}…{{/LIST}}` blocks.
Render: `python scripts/render.py --template recipes/<name>.html --tokens output/slots.json
--raster output/bg.png --width W --height H --out output/composed.png`.

| Recipe | Use when the brief is… | Flux role | Status |
|---|---|---|---|
| `stat_grid` | several hard numbers / "by the numbers" | ambient bg | ✅ built |
| `stack` | a layered system / pipeline / process, bottom→top | ambient bg | ✅ built |
| `annotated_line` | one example/string with parts to call out | ambient bg | ▢ next |
| `compare` | A vs B, two options/approaches | ambient bg | ▢ next |
| `timeline` | a sequence / roadmap / steps over time | ambient bg | ▢ next |
| `listicle` | N tips / takeaways / a numbered list | ambient bg | ▢ next |
| `big_statement` | one punchy claim, no supporting data | full-bleed bg | ✅ built |
| `hand_quote` | a single quote/phrase, typography as the visual | optional faint bg | ▢ next (needs hand-lettered font) |
| `hero` | one headline + short body over an image | full-bleed bg | ✅ built |
| `product_ingredients` | a product to feature + its ingredients/specs (all-serif, consumer/editorial) | full-bleed product image | ✅ built |
| `magazine` | explainer: text column + illustration column | Flux illustration in a column | ▢ Phase B |
| `annotated_shot` | a real screenshot with callouts | none (user screenshot) | ▢ Phase C (new input) |
| `comic` | a short narrative in panels | Flux doodle panels | ▢ Phase C (needs LoRA for consistency) |

## Selection heuristics (cheap reasoning step)
- counts/percentages/figures → `stat_grid`
- "the X stack / pipeline / how it's built" → `stack`
- a sentence/code/string with tricky parts → `annotated_line`
- "X vs Y", trade-offs → `compare`
- "then → then → then", roadmap, dates → `timeline`
- "N ways / N tips / N lessons" → `listicle`
- a bold one-liner with no data → `big_statement` or `hand_quote`
- a quotation → `hand_quote`
- general hook + one image → `hero`
- long-form explainer with a feature image → `magazine`

If the user set `format:` in INPUTS.md, use it. Always state your pick + why at the review gate.
