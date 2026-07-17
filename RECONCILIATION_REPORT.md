# Library/Presentation Reconciliation Report

Generated during migration (Phase 3). Compares the 13 slides present in both
`lcls_laser_slides/` (library) and `presentation/` (delivered 2026 deck) from
the source repo. Per migration policy, the **presentation version wins** for
any divergence; this report is the record of what changed and why.

## Slides compared (13)

fiber_types, generating_a_soliton, hcf_gvd, hcf_loss_length,
noble_gas_nonlinearity, rdw_tunability, soliton_fission_length, soliton_intro,
soliton_self_compression, spm_interactive, time_bandwidth, timescales,
upcoming_rdw

## Divergences found (2)

### 1. `hcf_gvd` (→ `slides/fiber-hardware/hcf_gvd`)

- `.html` fragment: **identical** in both copies.
- `figures/`: the **library copy was missing `soliton_optical_animation.gif`
  entirely**, even though the shared HTML references
  `<img src="figures/soliton_optical_animation.gif">`. This made the library
  copy of this slide broken/non-renderable on its own.
- The presentation copy has the complete asset.
- **Resolution:** seeded the library with the presentation's copy (HTML +
  figures), fixing the missing-asset bug.

### 2. `upcoming_rdw` (→ `slides/rdw/upcoming_rdw`)

- `.html` fragment differs:

  ```diff
  -          <h3 style="margin: 0 0 0.4em;">Upcoming — Investigating Deep UV Driven Photochemistry in Alkenes with Sub-10 fs Time Resolution</h3>
  +          <h3 style="margin: 0 0 0.4em;">Motivation — Clocking Deep-UV Photochemistry in Alkenes with Sub-10 fs Resolution</h3>
  ...
  -                  <img src="figures/Butadiene.svg" style="height: 48px; object-fit: contain;" />
  +                  <img src="figures/Butadiene.png" style="height: 48px; object-fit: contain;" />
  ...
  -                  <img src="figures/2-4-Hexadiene-2-5-dimethyl.svg" style="height: 48px; object-fit: contain;" />
  +                  <img src="figures/2-4-Hexadiene-2-5-dimethyl.png" style="height: 48px; object-fit: contain;" />
  ```

- `figures/`: **identical** in both copies (`Butadiene.png`,
  `2-4-Hexadiene-2-5-dimethyl.png`, `butadiene_s2_plot.png` — all PNGs, no
  SVGs present in either copy).
- The library HTML referenced `.svg` files that don't actually exist in
  either copy's `figures/` folder (a stale/broken reference); the
  presentation HTML was updated to reference the real `.png` files and to a
  revised, reframed title ("Motivation" framing vs. "Upcoming").
- **Resolution:** seeded the library with the presentation's copy (HTML
  fixed references + reframed title; figures unchanged since already
  identical).

## No divergence — no action taken (11)

The following slides were byte-for-byte identical between the library and
presentation copies (compared recursively: `.html`, `figures/`, `scripts/`,
`data/`, `interactives/`) — the library seed from Phase 2 stands as-is:

- fiber_types
- generating_a_soliton
- hcf_loss_length
- noble_gas_nonlinearity
- rdw_tunability
- soliton_fission_length
- soliton_intro
- soliton_self_compression
- spm_interactive
- time_bandwidth
- timescales

## Addendum (Phase 5): a third, more-authoritative version exists — `index.html`

The comparison above is between `lcls_laser_slides/<slide>/<slide>.html`
(library) and `presentation/<slide>/<slide>.html` (the standalone fragment
copy stored alongside each slide's assets inside `presentation/`). It does
**not** cover a third copy of the same content: the `<section>` markup
actually **inlined in `presentation/index.html`** — the file that was
literally opened and presented on 2026-06-30.

While recreating the frozen 2026 deck (Phase 5) and diffing the rebuild
against `presentation/index.html`, it became clear that for 9 of the 13
slides above, the standalone fragment file had **continued to be edited
after the talk** (expanded speaker notes, and in one case new visible
content — see `fiber_types` below), while `index.html` was never updated to
match. So the fragment/library content is a *newer* draft; `index.html` is
the *as-delivered* snapshot:

| Slide | Fragment/library vs. `index.html` (as delivered 6/30) |
|---|---|
| `fiber_types` | Fragment adds two new fibre-type write-ups (Photonic Bandgap, Hollow Capillary) and an expanded trade-off bullet not shown on 6/30 |
| `timescales` | Fragment's speaker notes are a cleaned-up rewrite of what was delivered |
| `noble_gas_nonlinearity` | Fragment's speaker notes add 2 bullets not delivered |
| `time_bandwidth` | Fragment's speaker notes are an expanded rewrite |
| `spm_interactive` | Fragment's speaker notes are an expanded rewrite |
| `soliton_intro` | Fragment's speaker notes add Russell historical detail not delivered |
| `hcf_gvd` | Fragment's speaker notes are an expanded rewrite (independent of the missing-GIF issue above) |
| `soliton_fission_length` | Fragment's speaker notes are an expanded rewrite |
| `generating_a_soliton` | Fragment's speaker notes are an expanded rewrite |

**Resolution:** per instruction, the **frozen 2026 deck**
(`presentations/2026/06-30-department-meeting/`) uses content extracted
directly from `presentation/index.html` for these 9 slides — i.e. exactly
what appeared on 6/30 — not the newer fragment/library text. This is a
Phase-5-only correction: **the library itself was left unchanged** (it
correctly reflects the current, more-refined fragment content for future
reuse; the "presentation wins" rule for library-seeding purposes was already
satisfied since library == fragment for these 9 slides, with no divergence
between them). Only the frozen historical record needed the older,
as-delivered text substituted in.
