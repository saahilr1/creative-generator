# Onboard a new brand

Each brand lives in `brands/<brand_id>/` with three things:
- `brand.yaml` — exact tokens (palette, fonts, wordmark)
- `GUIDELINES.md` — voice + visual rules (Always / Never, example phrases)
- `examples/` — 3–6 reference designs the brand likes

To add a brand, open this repo in Claude Code and paste the prompt below.

---

## Onboarding prompt (copy, fill the two blanks, paste)

```
Onboard a new brand into this creative generator.

brand_id: <short-slug, e.g. zleven>
source material: <paths to the brand's existing docs / site export / example designs>

Steps:
1. Create brands/<brand_id>/ with brand.yaml, GUIDELINES.md, and examples/
   (use brands/_example/ as the structure to mirror).
2. Read the source material and extract:
   - brand.yaml tokens: brand_name, palette (bg/fg/accent/muted hex), google_font +
     font_stack, brandbar_text/wordmark, default_aspect_ratio, raster_style_suffix.
   - GUIDELINES.md: who we are, voice & tone, visual style, colours (the feel),
     Always list, Never list, example phrases we use.
3. Copy 3–6 example designs into brands/<brand_id>/examples/ (or tell me to drop them in).
4. CRITICAL — do not invent brand facts. If an exact hex, font, or rule isn't in the
   source, infer it from the examples and clearly mark it as an assumption. List every
   assumption separately.
5. Show me the drafted brand.yaml + GUIDELINES.md + your assumptions, and WAIT for my
   review. Do not generate any asset yet.
6. After I approve, set INPUTS.md `brand: <brand_id>`. Done.
```

---

## Then generate
1. Set `brand: <brand_id>` in `INPUTS.md` and fill the brief.
2. Tell Claude "run the creative generator" (or "draft my brief" first).
