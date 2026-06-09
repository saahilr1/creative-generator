# Your Brief

Fill in the fields below, then tell Claude: **"run the creative generator"**.
Only the first 7 are required. Leave the optional ones blank if you don't need them.

---

## Required

**brand:** your_brand
<!-- which brand to use. Must match a folder name in brands/ (copy brands/_example/ to start). -->

**theme:** the AI tool-overwhelm trap for busy PMs
<!-- the throughline/topic for this run. Anchors both image + copy. For a carousel,
     it's the thread that ties all slides together. <= 100 characters -->

**post_purpose:** hook
<!-- one of: hook | explainer | case-study | promo | quote -->

**mode:** routine
<!-- routine = token-lean, fill a recipe (good for everyday posts).
     hero = invest in a bespoke visual concept: Flux-as-CONTENT (scenes/personas, in the
     brand's style) + design components, not just text-in-boxes. Costs more; use for flagship posts. -->

**format:**
<!-- OPTIONAL. Leave blank and the agent picks the best recipe (recipes/INDEX.md) from your
     brief and shows the pick + why before generating. Or force one: stat_grid | stack |
     annotated_line | compare | timeline | listicle | big_statement | hand_quote | hero | magazine.
     Ignored in hero mode (hero composes bespoke). -->

**headline:** 47 tools bookmarked. 2 actually used.
<!-- the big line. <= 120 characters -->

**body_or_bullets:** The AI tool overwhelm is real. Most people collect tools they never open. The fix isn't more tools — pick 2 and go deep.
<!-- supporting text or 3-5 bullets (one per line). <= 500 characters -->

**audience_one_liner:** PMs adding AI to existing workflows
<!-- who this is for. <= 60 characters -->

**tone:** bold
<!-- one of: calm | bold | playful | academic | urgent -->

**aspect_ratio:** 4:5
<!-- one of: 1:1 | 4:5 | 9:16 | 16:9   (4:5 = 1080x1350, best for Instagram) -->

**colour_intent:** cool-dark
<!-- one of: warm-light | cool-dark | high-contrast | pastel | mono -->

---

## Optional

**must_include:** a tidy desk with a notebook and coffee, calm focus
<!-- things the image SHOULD show. <= 200 characters -->

**must_avoid:** no robots, no AI logos, no children's-book style
<!-- things the image must NOT show. <= 200 characters -->

**reference_images:**
<!-- optional: list file paths to mood/reference images (used as context only) -->

---

## Output mode

**output_type:** single
<!-- one of: single | variations | carousel -->

**variations_count:** 3
<!-- only used if output_type = variations. How many options to generate (2-4) -->

**carousel_slides:** auto
<!-- only used if output_type = carousel. A number (e.g. 4) or "auto" to let Claude
     break the body into a sensible hook -> points -> CTA sequence -->

