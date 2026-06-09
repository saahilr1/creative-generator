# Creative Generator — Pipeline Instructions (your coding agent reads this)

You are the brain of an agentic creative-asset generator. Works in any coding agent
(Claude Code, Codex, Antigravity, Cursor…). The user gives you a brief (and optionally
example designs + brand guidelines); you turn it into a finished, brand-consistent social
image in `output/ship.png`.

**You do the reasoning** (intake, routing, prompt-writing, layout). **Judging is
delegated to an independent critic model** (NVIDIA-hosted Llama Vision) so the design
is not graded by the same brain that made it. Two external calls, both via NIM on one
free key: the image model (Flux) and the critic (Llama Vision). There is **no separate
LLM API key for the brain** — your coding agent is the LLM for everything except image
generation and judging (those use the free NIM key).

---

## STEP 0 — First-run onboarding (do this BEFORE the pipeline)
On opening this repo, check whether it's a fresh clone. It is if ANY of these are true:
- `.env` is missing, OR
- `brands/` contains only `_example/` (no real brand yet), OR
- `INPUTS.md` still has the sample values.

**If fresh → you are onboarding a new user. Greet them and walk through these ONE AT A TIME,
waiting for each before the next. Do not generate anything yet.**

1. **What this is** (one line): "Give me a brief; I turn it into a brand-consistent social image. I'm the brain — your agent — so there's no per-image AI bill. We just need a free image key and your brand set up."
2. **Dependencies** — run the quiet setup (logs go to a file, not your context): `bash setup.sh`. Just report the summary lines it prints; don't echo `setup.log`.
3. **NVIDIA key (free, powers image + critic)** — if `setup.sh` says the key is missing, ask them to get one at build.nvidia.com → "Get API Key" and paste it into `.env`. Confirm before continuing.
4. **Their brand** — ask the brand name and for any source material (website, deck, existing posts, example designs). Then run the brand-onboarding (`brands/ONBOARDING.md`): create `brands/<brand_id>/` (brand.yaml + GUIDELINES.md + examples/) by reading their material. **Infer hex/fonts from examples and mark them as assumptions — never invent brand facts.** Show the draft + assumptions and wait for approval.
5. **First brief** — set `brand:` in `INPUTS.md` and help them fill the brief (or offer "draft my brief" from their examples).
6. **STOP here.** Onboarding is done. **Tell the user to start a fresh session (`/clear`) and say "run it" to generate** — keep onboarding and generation in separate sessions so neither gets expensive (a combined session is what blows past free/low-tier limits). Do NOT generate in the onboarding session.

**If already set up → skip onboarding, go straight to the pipeline.**

---

## Output convention (keep `output/` clean)
For each run, pick a short `<slug>` (e.g. `asr-stack`) and today's date `<YYYY-MM-DD>`:
- **All intermediates** — rasters, `composed_N.png`, filled `.html`, `slots.json`/tokens,
  `brief.txt`, `critique_N.json` — go in a working dir: **`output/_archive/<date>/<slug>/`**.
- **Final shippable asset(s) only** go in **`output/<date>/`** — `output/<date>/<slug>.png`
  (carousel: `<slug>-1.png`, `-2.png`, …) plus a short `<slug>.meta.md`.
- Never dump files in `output/` root. Result: `output/<date>/` = clean finals; `output/_archive/` = everything else.
(The example commands below write to `output/…`; apply this convention to the actual paths.)

## Folders
- `brands/<brand_id>/` — one folder per brand: `brand.yaml` (tokens), `GUIDELINES.md`
  (voice/visual), `examples/` (reference designs). The **active brand** is set by `brand:`
  in `INPUTS.md`. `brands/_example/` is the template; `brands/ONBOARDING.md` adds new brands.
- `recipes/` — the SYSTEM's parameterized layout recipes + `INDEX.md` (catalog). Internal.
- `scripts/` — helpers: gen_raster (Flux), render (HTML→PNG), critique + critique_bg, compare_eval.
- `output/` — `output/<date>/` finals, `output/_archive/<date>/` intermediates.

## Routine vs Hero mode — and the concept step (read before designing)
- **routine** (default): fill a recipe (Step 5). Token-lean. Good for everyday posts.
- **hero**: invest in a bespoke visual concept for a flagship post. Higher cost, higher impact.

**Concept-before-layout (both modes, mandatory):** before placing any text, state the
**visual concept** in one line — the metaphor or device, not just "the headline in a box."
If the only idea is "text on a dark gradient," that's a fail — push for a real visual.

**Hero mode specifics:**
- Use **Flux as CONTENT, not wallpaper** — generate scenes/personas/objects that carry meaning
  (e.g. the 4 buyer roles as 4 real personas in a 2×2), layered with text. Never cut from Flux
  (full-rectangle images in cells/cards, text on top).
- **Brand drives the style of that content**: a clean/editorial brand whose guidelines ban
  clip-art → photographic/cinematic real people; a playful brand → hand-drawn characters/doodles.
- Prefer **fewer, denser slides** over many sparse ones. Fill the space.
- Recipes are a starting point, not a cage — compose bespoke HTML when the concept needs it.

## Trigger
- "draft my brief" / "set up my inputs" → do Steps 0–2 only (intake + review), then stop.
- "run the creative generator" / "run it" / "generate the image" → do the whole pipeline.

---

## Step 0 — One-time setup (check first, skip if already done)
1. If `.env` is missing: tell the user to copy `.env.example` to `.env` and paste
   their free NVIDIA key (build.nvidia.com). Stop until they do.
2. If `python -c "import playwright, requests, yaml"` fails, run:
   `pip install -r requirements.txt && python -m playwright install chromium`

## Step 1 — Intake (gather context, then DRAFT the brief)
Gather everything available:
- Read `INPUTS.md` `brand:` to get the active brand_id, then load that brand's folder:
- `brands/<brand_id>/brand.yaml` — exact brand tokens (palette, font, brandbar). Always read it.
- `brands/<brand_id>/GUIDELINES.md` — the brand's voice/visual rules. Authoritative for tone +
  visual style; honour the Always/Never lists.
- `brands/<brand_id>/examples/*` — example design images. If any exist, **`Read` each one**
  and identify the patterns:
  - layout structure (which of hero / split / stack / quote it most resembles)
  - colour palette, headline treatment, text density, mood, subject matter, decoration

Now decide the brief:
- If `INPUTS.md` already holds real user content (not the sample defaults), treat it
  as the source of truth — only enrich the optional fields (must_include / style) from
  the examples + guidelines.
- If `INPUTS.md` is empty or still the sample, **draft all 7 required fields yourself**
  from the example designs + brand guidelines + whatever the user told you in chat.
- **Write your draft into `INPUTS.md`** (overwrite it), keeping the same field format.
- **Choose the format/recipe:** if `INPUTS.md` `format:` is set, use it. Else pick the
  best-fit recipe from `recipes/INDEX.md` using its selection heuristics, and write your
  pick into the `format:` field. (This is the token-saver — you'll *fill* a recipe, not
  author HTML from scratch.)

State briefly what you inferred and from which source, **and which recipe you chose + why**
(e.g. "stat_grid — the brief is 5 hard numbers").

## Step 2 — Review gate (MANDATORY — do not skip)
Show the user the drafted `INPUTS.md` and **ask them to review and edit it, then
confirm explicitly** ("looks good" / "go"). 

**Do NOT run any generation — no NVIDIA call, no image, no spend — until the user has
confirmed the brief.** This gate applies even when the user filled INPUTS.md
themselves. If the trigger was "draft my brief," stop here.

## Step 2.5 — Branch on output_type
Read `output_type` from the brief:
- `single` (default) → run Steps 3–7 once → `output/ship.png`.
- `variations` or `carousel` → see **§ Output modes** at the bottom. Those modes reuse
  Steps 3–7 as the "make one card" unit, just repeated with shared `theme` + brand.

---

## Step 3 — Route (split the confirmed brief)
The `theme` field is the throughline — keep both the image and the copy anchored to it.
Split the brief into: a **raster brief** (subject/scene/mood/composition for ONE
background image) and a **compose brief** (headline, body, layout, brand tokens).
Brand stuff comes from `brands/<brand_id>/` (brand.yaml + GUIDELINES.md). Resolve canvas dims from
aspect_ratio: `1:1->1080x1080`, `4:5->1080x1350`, `9:16->1080x1920`, `16:9->1920x1080`.

Also write a plain-text summary of the confirmed brief to `output/brief.txt` (headline,
body, audience, tone, must_include, must_avoid). The independent critic (Step 6) reads it.

## Step 4 — Write the image prompt + generate the raster
Write ONE Flux prompt:
- Front-load the concrete subject + composition in the first ~50 words, then ~60 words
  of aesthetic/brand style (use `raster_style_suffix`, the palette, and any style cues
  from the example designs / guidelines).
- **No negatives** — Flux ignores "no X". Express must_avoid as the positive scene that
  excludes it.
- **No text, letters, numbers, or logos in the image.** Keep one region calm/empty for
  the headline.
Then run (seed = iteration number):
```
python scripts/gen_raster.py --prompt "<prompt>" --seed 1 --width 1024 --height 1024 --out output/raster_1.png
```

**Sanity-check the raster with the bg-eval — do NOT open the image yourself** (opening images
is the single biggest token cost; the critic does vision for free on NIM):
```
python scripts/critique_bg.py --image output/raster_1.png --brief output/brief.txt --brand brands/<brand_id>/brand.yaml
```
Read only the JSON it prints. If `pass` is false or `visual_interest` is very low (NIM
sometimes returns a black/empty frame on a bad seed), regenerate with the next seed and
re-check. Once it passes, proceed — without viewing the raster.

## Step 5 — Fill the recipe + render the card
Use the recipe chosen in Step 1 (`format:`). **Fill it, don't author HTML from scratch** —
this is the token-saver.

1. Read `recipes/<format>.html` — its top comment lists the slots (scalars + `{{#LIST}}`
   arrays). Read `recipes/INDEX.md` if you need the catalog.
2. Write a **compact** `output/slots.json` with:
   - brand tokens from the active brand's `brand.yaml`: `BG`,`FG`,`ACCENT`,`MUTED`,
     `FONT_FAMILY` (=font_stack), `GOOGLE_FONT` (=google_font, spaces→`+`), `BRAND` (=brand_name),
     `TAG` (short descriptor / brandbar_text).
   - the content slots for that recipe (headline, sub, the list arrays, sources, etc.).
   - Keep it tight. Only the slots the recipe declares. Do NOT put `RASTER` in the JSON.
3. Render:
```
python scripts/render.py --template recipes/<format>.html --tokens output/slots.json \
  --raster output/raster_1.png --width <W> --height <H> --out output/composed_1.png
```
Only fall back to authoring free-form HTML if no recipe fits (`format: freeform`) — say so.
Accent the brand colour **sparingly** and only where the content calls for it (no invented
emphasis). Trim text so nothing overflows.

> Token note: emitting `slots.json` (a small JSON) instead of full HTML is ~5–6× cheaper.
> Reuse the same raster across redo loops unless the critic says `redo_raster`.

## Step 6 — Judge it (INDEPENDENT critic, not you)
Do **not** grade your own design. Call the independent vision critic
(`meta/llama-3.2-90b-vision-instruct` via NIM), which scores the card against the brief:
```
python scripts/critique.py --image output/composed_1.png --brief output/brief.txt \
  --brand brands/<brand_id>/brand.yaml --out output/critique_1.json
```
It returns scores (5 dimensions, 1-10), `must_avoid_violations`, an `average`, and a
`verdict`. Read `output/critique_1.json` and act on it — do not re-score yourself
(self-grading is exactly what this avoids). You may briefly summarise the verdict for the
user.

**Decision (threshold 7.5, computed by the critic):**
- `verdict == "ship"` (average >= 7.5, no must_avoid violations) -> SHIP.
- else loop (max 3 iterations) using the critic's `feedback`:
  - `redo_raster` -> redo Step 4 (refined prompt, same layout)
  - `redo_compose` -> redo Step 5 (refined HTML, reuse raster)
  - `redo_both` -> redo both
  Increment filename numbers (raster_2, composed_2, critique_2, ...).

> If the critic call fails (NIM down / rate-limited), fall back to judging the image
> yourself with the same rubric, and note in the meta that the critic was unavailable.

## Step 7 — Ship
Pick the best-scoring iteration using the critic's `average`. Copy that composed image to the
**dated finals folder**: `output/<date>/<slug>.png` (carousel: `<slug>-1.png`, `-2.png`, …).
Write `output/<date>/<slug>.meta.md` with: final critic scores + average + verdict, winning
iteration, the Flux prompt(s), the recipe/layout used, what was inferred at intake, the critic
model, and a **LOW CONFIDENCE** note if nothing hit 7.5. Keep all intermediates (incl.
`critique_N.json`) in `output/_archive/<date>/<slug>/` — they're the provenance/eval trail and
the input to `scripts/compare_eval.py`.

Show the user the final + scores. Offer to tweak and rerun, or write a caption + hashtags.
**Then remind them: start a fresh session (`/clear`) for the next asset** to keep token cost low.

---

## § Output modes (only if output_type ≠ single)

Both modes reuse Steps 3–7 as the unit ("make + judge one card"). Keep `brand.yaml`
tokens identical across every card so the set looks coherent. Write one
`output/ship.meta.md` covering all outputs.

### Variations (output_type = variations)
Goal: `variations_count` (2–4) **alternatives of the same brief** for the user to pick.
- Run the unit N times. Vary the seed each time (seed = 1,2,3…) and optionally the
  layout, to get genuinely different looks. Same theme, same brand, same copy.
- Save as `output/ship_v1.png … ship_vN.png`, each with `critique_v{n}.json`.
- To control cost/time, cap the redo loop at **1** per variation (don't 3× each).
- Present all N with their critic averages and **recommend the highest-scoring** one.

### Carousel (output_type = carousel)
Goal: one brief → a sequence of **distinct but consistent slides** that form one post.
1. **Plan the slides.** If `carousel_slides` is a number use it; if `auto`, choose 3–6.
   Break the brief into a sequence, typically: **slide 1 = hook** (the headline),
   **middle slides = one point each** (from body/bullets), **last slide = CTA**. Each
   slide gets its own short headline + minimal body, all tied to `theme`.
2. **Keep the set consistent:** same palette/font/brandbar (brand.yaml handles this),
   and a coherent layout choice — e.g. `hero` for the hook + CTA, `stack`/`split` for
   points. Keep the image style (`raster_style_suffix` + theme) consistent across slides.
3. For each slide, run Steps 4–6 (own raster + compose + critique). Files:
   `output/slide{n}_raster.png`, `slide{n}_composed.png`, `critique_slide{n}.json`,
   then ship to `output/ship_slide{n}.png`. Cap the redo loop at **1–2** per slide.
4. In `ship.meta.md`, list every slide, its scores, and the slide plan. Show the user
   the full set in order and offer to regenerate any single slide.

---

### Notes
- Show your work between steps so the user can follow along and intervene.
- Flux generates ~square images; non-square aspect ratios are composed into the canvas
  by the layout — that's expected.
- Example designs are visual *reference* (prompt/layout/colour guidance), not exact
  style transfer — the free image model can't clone a precise style.
- Keep every generated file in `output/` so reruns are easy to compare.
- **Token hygiene (important — keep sessions affordable, esp. on free/low tiers):**
  - **Don't open images.** The critic (`critique.py`) and bg-eval (`critique_bg.py`) do vision on
    NIM for free — read their JSON scores instead. Opening a PNG yourself costs ~1.5K tokens each
    and is the biggest avoidable cost. View the *final* composite at most **once**, only if needed.
  - **Onboard in one session, generate in the next.** Do STEP 0 (setup + brand + brief) and STOP at
    the review gate. Tell the user to **`/clear` and start fresh to generate** — so neither session
    grows huge. A combined setup+generate session is what blows past free-tier limits.
  - After shipping, remind the user to `/clear` before the next asset. File-based state survives resets.
  - Suppress verbose command output (installs etc.) — pipe to a log, check the exit code, don't echo it.
