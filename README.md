# Presentations

A monorepo for building reveal.js presentations from a shared **slide
library** and lightweight **manifests**. Historical decks are frozen at
delivery time so they render identically forever, even as the library keeps
evolving.

## Core model

- **The library is the primary asset.** Individual slides live once, in
  `slides/<category>/<name>/`, organized by topic. Presentations are
  manifests (`deck.yaml`) that compose library slides.
- **Author with live references; freeze on delivery.** While building a
  talk, `deck.yaml` can reference library slides with `lib: <category>/<name>`
  — one source of truth, full reuse. When the talk is delivered, running
  `build.py --freeze` **copies** the resolved slides into the presentation's
  own `slides/` folder and rewrites the manifest to local paths. The deck
  becomes a permanently self-contained snapshot, immune to future library
  edits — editing a slide next year will not change what a frozen deck
  renders. Duplication only happens intentionally, at freeze time, as the
  price of historical immutability.
- A frozen deck is just a self-contained folder — it doesn't depend on
  anything outside itself, which is also what would let it be served
  fully locally in the future (see Future Work in `build-plan.md`).

## Prerequisites

- Python 3
- A virtualenv with `requirements.txt` installed:

  ```bash
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
  ```

- Local preview: build a deck and serve it in one step (this also opens it
  in your browser). Serving — not just opening `index.html` directly — is
  required if the deck has interactive iframes:

  ```bash
  .venv/bin/python build.py 2026/06-30-department-meeting --preview
  ```

## Create a new presentation

1. Scaffold it — prompts for the date and title, then creates
   `presentations/<year>/<mm-dd-slug>/` with a starter `deck.yaml`, a title
   slide, and a blank acknowledgements slide:

   ```bash
   .venv/bin/python new_presentation.py
   ```

   Fill in the venue/event placeholder in the generated title slide and the
   acknowledgements list.
2. Add `lib: <category>/<name>` entries to `deck.yaml`'s `slides:` list for
   any library content; add further presentation-specific slides as local
   files under `presentations/<year>/<name>/slides/<name>/<name>.html`.
3. Preview locally:

   ```bash
   .venv/bin/python build.py <year>/<name> --preview
   ```

   Generator scripts are **not** re-run by default — add `--generate` when
   you've actually edited a slide's `scripts/*.py` and need its figures
   refreshed. This keeps ordinary preview/build runs from silently touching
   committed library figures (regeneration isn't perfectly byte-reproducible
   across runs/machines).
4. Push to `main` to deploy (see Privacy/visibility below for what that
   means for `unlisted` decks).

## Add a new reusable slide to the library

1. Create `slides/<category>/<name>/` (pick a category from the taxonomy
   below, or propose a new one).
2. Add:
   - `<name>.html` — a bare `<section>...</section>` fragment (no `<html>`
     wrapper). Reference its own figures as `figures/...` and any
     interactive as `interactives/...` — **not** prefixed with the slide's
     own name. `build.py` namespaces these automatically when it assembles
     multiple slides into one page.
   - `figures/` — generated static figures (svg/png/gif).
   - `scripts/` — Python generators that (re)produce `figures/`. Always
     edit the generator, never the generated file directly.
   - `data/` — source data for the generators, if any.
   - `interactives/` — standalone interactive `.html` (embedded via
     `<iframe>` when referenced from a deck).
3. Reference it from a deck with `lib: <category>/<name>`.

## Freeze a delivered presentation

```bash
.venv/bin/python build.py --freeze <year>/<name>
```

This copies every `lib:` slide the deck uses into the presentation's own
`slides/` folder, rewrites `deck.yaml` to point at those local copies, and
sets `frozen: true`. From then on, CI (`build.py --all`) rebuilds the deck
from its own local copies only — it never touches the library again, so the
historical record can't drift even if the source library slide is edited or
deleted later. Do this once, right after (or as part of) actually giving the
talk.

## Harvest: promoting a presentation-local slide into the library

If a slide you wrote as presentation-local turns out to be reusable, copy
its folder into `slides/<category>/<name>/`, normalize its image/interactive
paths back to the slide-relative `figures/...` / `interactives/...`
convention (drop any presentation-specific prefix), and switch the
originating deck's manifest entry to `lib: <category>/<name>` (or leave an
already-frozen deck's local copy untouched — freezing is a one-way copy, not
a symlink). One-off results tied to a specific dataset or beamtime
(a specific experiment's raw photos, a specific molecule's one-time result
plot) generally aren't good harvest candidates — keep those presentation
-local.

## Privacy / visibility

Each deck sets `visibility: public` or `visibility: unlisted` in
`deck.yaml`:

- `public` — listed on the landing page (`dist/index.html`), grouped by
  year, indexable by search engines. Served at:
  `https://<YOUR_GITHUB_USERNAME_OR_ORG>.github.io/<YOUR_REPO_NAME>/<year>/<presentation_name>/`
- `unlisted` — omitted from the landing page, served at an obscure
  `slug` instead of its name, and rendered with
  `<meta name="robots" content="noindex, nofollow">`. Served at:
  `https://<YOUR_GITHUB_USERNAME_OR_ORG>.github.io/<YOUR_REPO_NAME>/<year>/<slug>/`

**Unlisted is obscurity, not security.** This repository (and therefore its
GitHub Pages output) is public if the GitHub repo is public — anyone with
the URL, or anyone who reads the repo's source/history, can see an
"unlisted" deck's content. Never use `unlisted` for embargoed or genuinely
sensitive material; there is no access control here, only "not linked from
anywhere and not indexed."

## Taxonomy conventions

Library slides are organized under `slides/<category>/` by physics topic:

- `fundamentals/` — pulse physics building blocks (timescales, time-bandwidth
  product, spectral phase, dispersion)
- `fiber-hardware/` — fiber types and hardware (HCF types, GVD, loss length,
  capillary handling)
- `nonlinear-optics/` — SPM and nonlinearity (chirp, noble-gas nonlinearity,
  OPA broadening)
- `solitons/` — soliton formation, self-compression, fission
- `rdw/` — resonant dispersive wave emission and tunability
- `post-compression/` — post-compression technique and results
- `experiments/` — apparatus, diagnostics, and experiment-specific results
  (pump-probe, IRF measurements, per-molecule results with a generator)
- `meta/` — generic reusable chrome, e.g. a library title-slide template

The taxonomy is expected to grow. Propose a new category (or a split of an
existing one) rather than jamming a slide somewhere it doesn't fit — this
list isn't sacred, just the current best guess.

## SVG / asset conventions

- SVGs (and all other figures) are referenced as `<img src="figures/...">`
  — **never inlined** into the slide HTML.
- Generator scripts live in `scripts/`, beside the `figures/` they produce,
  and read/write with paths relative to the slide's own folder (i.e. a
  generator is run with its slide folder as the working directory, not the
  presentation root — `build.py` does this automatically).
- Always edit the generator script and re-run it; never hand-edit a
  generated SVG/PNG/GIF.
