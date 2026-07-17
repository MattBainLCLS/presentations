# Build Plan: Reveal.js Presentation Monorepo Migration

## Goal
Convert the current multi-repo, side-by-side-clone workflow into a single
monorepo with a **slide library** + **manifest-based presentation assembly**.
Solve the fan-in problem (folding new slides back into the library) and the
duplication/drift problem, while preserving historical decks exactly.

---

## Core Model (read first)

- **The library is the primary asset.** Individual slides live once, organized by
  topic. Presentations are lightweight manifests that compose library slides.
- **Author with live references; freeze on delivery (Option B).**
  - While building a talk, `deck.yaml` *references* canonical library slides →
    full reuse, single source of truth.
  - On delivery, a `--freeze` step **copies** resolved slides into the
    presentation folder and rewrites the manifest to local paths. The deck
    becomes permanently self-contained and immune to future library edits.
  - Consequence: editing a slide in 2027 does NOT alter a frozen 2026 deck.
    Duplication happens only intentionally, at freeze time, as the price of
    historical immutability.
- **A frozen deck is a self-contained folder.** This is also the foundation for a
  future "fully private / local-only" deploy mode (NOT built now — see Future Work).

---

## Target Repository Structure

```
slides-monorepo/
  slides/                      # THE LIBRARY (canonical, reusable slides)
    <category>/                # taxonomy TBD — see Open Decision #1
      <slide-name>/
        <slide-name>.html      # a reveal.js <section> fragment
        figures/               # generated static figures (svg/png/gif)
        scripts/               # Python generators for this slide's figures
        data/                  # source data for scripts
        interactives/          # standalone interactive .html (iframed)
  shared/
    reveal/                    # reveal.js (vendored, version-pinned)
    style-guide/               # migrated from slac_presentation_template_reveal
      css/
      js/
      assets/ (backgrounds, logos)
      template.html            # reference template
  presentations/
    <year>/                    # nested by year (kept per user preference)
      <presentation-name>/
        deck.yaml              # the manifest
        slides/                # presentation-specific slides + frozen copies
        assets/                # presentation-specific one-off assets
  templates/
    index.html.j2             # reveal.js shell (Jinja2)
  build.py                    # manifest -> dist/<...>/index.html
  requirements.txt
  .gitignore                  # ignores local dist/
  .github/workflows/
    deploy.yml
  README.md
```

---

## deck.yaml Schema

```yaml
title: "Department Meeting — HCF Post-Compression"
presentation_name: "06-30-department-meeting"
year: 2026

visibility: unlisted          # public | unlisted
                              #   public   -> listed on landing page, indexable
                              #   unlisted -> omitted from landing page,
                              #               noindex meta + robots disallow,
                              #               obscure URL slug

frozen: false                 # set true by `build.py --freeze`; frozen decks
                              # reference local ./slides copies and are NOT
                              # rebuilt from the live library in CI

slug: null                    # optional non-guessable URL slug for unlisted decks
                              # (auto-generated on freeze if visibility: unlisted)

theme: slac                   # resolves to shared/style-guide

reveal_config:                # optional per-deck reveal.js overrides
  transition: slide
  controls: true

slides:                       # ordered list; each references library or local
  - slides/title/title.html                 # presentation-local (title/ack)
  - lib: fundamentals/soliton-intro         # library reference (author mode)
  - lib: hardware/fiber-types
  - slides/acknowledgements/ack.html
```

Notes:
- `lib:` entries resolve against `slides/` (the library).
- Plain path entries resolve against the presentation folder (local slides).
- On `--freeze`, every `lib:` entry is copied into the presentation's `slides/`
  and rewritten to a local path; `frozen:` flips to `true`.

---

## build.py Responsibilities

1. Parse `deck.yaml`.
2. Resolve slides:
   - `lib:` → `slides/<...>` (author mode)
   - path → presentation-local
3. **Run generators:** execute each referenced slide's `scripts/*.py` to
   (re)produce `figures/` and export interactive data. (Idempotent; can be
   skipped with `--no-generate` for fast preview.)
4. Assemble slide HTML into `templates/index.html.j2`:
   - `.html` fragments injected as-is
   - `interactives/*.html` embedded via `<iframe>` (client-side JS works on
     static hosting)
   - SVG figures referenced as `<img src=...>` (NOT inlined) — matches user
     preference and existing structure
5. Copy referenced figures/assets/interactives into `dist/<year>/<name>/`.
6. Inject theme CSS/JS from `shared/style-guide`.
7. For `visibility: unlisted`: inject `<meta name="robots" content="noindex">`,
   emit under obscure `slug`, exclude from landing page.
8. Render final `dist/<year>/<name>/index.html`.

Modes:
- `build.py <presentation>`            — build one deck (author mode)
- `build.py --all`                     — build all decks (CI)
- `build.py --freeze <presentation>`   — copy lib slides local, rewrite manifest,
                                          set frozen:true (delivery step)
- `build.py --no-generate`             — skip Python generation (fast preview)

Landing page:
- Auto-generate `dist/index.html` listing only `visibility: public` decks,
  grouped by year.

---

## GitHub Pages via Actions (.github/workflows/deploy.yml)

Trigger:
```yaml
on:
  push:
    branches: [main]
  workflow_dispatch:        # manual "Run" button
```

Steps:
1. Checkout
2. Set up Python; `pip install -r requirements.txt`
3. Run `build.py --all`
   - **Frozen decks are rebuilt from their own local slide copies**, so their
     output never drifts even as the library evolves.
4. Upload `dist/` via `actions/upload-pages-artifact`
5. Deploy via `actions/deploy-pages`

URLs:
- Public:   `https://<user>.github.io/<repo>/<year>/<name>/`
- Unlisted: `https://<user>.github.io/<repo>/<year>/<slug>/` (obscure), noindex,
  not linked from landing page.

Privacy caveat (documented in README): a public repo's Pages AND source are
public. "Unlisted" is obscurity, not security — never use it for embargoed data.

---

## Migration Steps (clean history; no subtree import)

### Step 0 — Scaffold
- Create target structure, `.gitignore` (ignore local `dist/`),
  `requirements.txt` (aggregate deps from existing `requirements.txt` files).

### Step 1 — Migrate shared assets
- `slac_presentation_template_reveal/` → `shared/style-guide/`.
- Vendor reveal.js into `shared/reveal/` (version-pinned).
- Drop `presentation/theme/` — it is a copy of the style guide; reference the
  shared one instead.

### Step 2 — Seed the library
- `lcls_laser_slides/` is already fragment-structured → seed `slides/`.
- **Taxonomy is deferred (Open Decision #1):** for now, propose a category
  mapping for user approval before moving files. Do NOT auto-organize.

### Step 3 — Reconcile duplicated/diverged slides
- Diff slides present in BOTH `lcls_laser_slides/` and `presentation/`.
- **User decision on this migration: presentation versions win** for any
  diverged slide (e.g. `hcf_gvd`, `soliton_intro`). Seed the library with the
  presentation's version.
- Produce a reconciliation report listing each diverged slide + diff for the
  record, but apply "presentation wins" as the default this pass.

### Step 4 — Harvest presentation-only reusable slides into the library
- e.g. `tmmda/` (has generator) → library.
- Determine reusability per slide; anything genuinely one-off stays local.

### Step 5 — Recreate the 2026 deck as a FROZEN presentation
- Create `presentations/2026/06-30-department-meeting/`.
- Title/acknowledgements slides (currently inline in `presentation/index.html`,
  not reusable) → presentation-local `slides/`.
- Because this deck is already delivered, migrate it in **frozen state**:
  slides copied local, manifest points at local copies, `frozen: true`.
- **Validation test:** rebuilt frozen deck should match the original
  `presentation/index.html` output. If it matches, migration is correct.

### Step 6 — Clean up strays
- Delete top-level loose images (`Butadiene_IRF.png`, `IMG_5168.jpg`, etc.)
  after verifying they duplicate files already inside slide `figures/` folders.

### Step 7 — Add tooling & docs
- Add `build.py`, `templates/index.html.j2`, `deploy.yml`, `README.md`.

### Step 8 — Deploy & verify
- Push to `main`, confirm GH Pages builds and the 2026 deck renders correctly at
  its URL.

### Explicitly NOT migrated
- `AGENTS.md` files — intentionally dropped (early agent-instruction artifacts).
  A fresh top-level AGENTS.md can be added later if desired.

---

## README.md — Required Contents

1. **Overview / core model** — library + manifest, author-then-freeze.
2. **Prerequisites** — Python, deps, local preview command.
3. **Create a new presentation:**
   - Make `presentations/<year>/<name>/`, write `deck.yaml`.
   - Reference library slides via `lib:`; add local slides for one-off content.
   - `python build.py <presentation>` to preview locally.
   - Push to deploy.
4. **Add a new reusable slide to the library:**
   - Create `slides/<category>/<name>/` with `.html`, `figures/`, `scripts/`,
     `data/`, `interactives/` as needed.
   - Add metadata header comment (title/tags/needs).
   - Reference from decks via `lib:`.
5. **Freeze a delivered presentation:**
   - `python build.py --freeze <presentation>` — copies library slides local,
     rewrites manifest, sets `frozen: true`. Explains WHY (historical immutability).
6. **Harvest:** promoting a good presentation-local slide into the library.
7. **Privacy / visibility:**
   - `public` vs `unlisted` behavior.
   - Explicit warning: public repo Pages + source are public; unlisted =
     obscurity, not security. Do not use for embargoed material.
8. **Taxonomy conventions** (filled in once Open Decision #1 is resolved).
9. **SVG/asset conventions:** SVGs referenced as images; generators live beside
   slides.

---

## Open Decisions (for the implementing Claude Code session)

1. **Taxonomy (deferred):** propose a category tree mapping the existing flat
   library slides into `slides/<category>/`, get user approval before moving.

---

## Future Work (NOT in scope now)

- **Fully-private presentations:** a frozen deck is already a self-contained
  folder. A future mode would build such a deck to a local `dist/` served from
  the user's machine (e.g. `python -m http.server`) or shared as a zip, skipping
  GH Pages entirely. Option B's freeze mechanism is the foundation for this;
  no work required now beyond not foreclosing it.
