#!/usr/bin/env python3
"""Build reveal.js presentations from deck.yaml manifests.

See README.md for the full model. Summary:
  - `slides/<category>/<name>/` is the canonical library.
  - `presentations/<year>/<name>/deck.yaml` is a manifest that composes
    library slides (`lib: <category>/<name>`) and/or presentation-local
    slides (plain paths, relative to the presentation folder).
  - `--freeze` copies every `lib:` slide into the presentation's local
    `slides/` folder, rewrites the manifest to local paths, and sets
    `frozen: true`. Frozen decks are self-contained and are never rebuilt
    against the live library (see `resolve_slides`).
"""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parent
SLIDES_LIB = ROOT / "slides"
SHARED = ROOT / "shared"
PRESENTATIONS = ROOT / "presentations"
TEMPLATES = ROOT / "templates"
DIST = ROOT / "dist"

ASSET_DIRS = ("figures", "interactives")


def load_deck(deck_yaml_path: Path) -> dict:
    with open(deck_yaml_path) as f:
        return yaml.safe_load(f)


def save_deck(deck_yaml_path: Path, deck: dict) -> None:
    with open(deck_yaml_path, "w") as f:
        yaml.safe_dump(deck, f, sort_keys=False, default_flow_style=False)


def generate_slug() -> str:
    import secrets
    return secrets.token_hex(4)


def ensure_slug(deck_yaml_path: Path, deck: dict) -> dict:
    """Lazily assign + persist a slug the first time an unlisted deck is
    built, so authoring/previewing a deck doesn't require freezing it
    first just to get an output path."""
    if deck.get("visibility") == "unlisted" and not deck.get("slug"):
        deck["slug"] = generate_slug()
        save_deck(deck_yaml_path, deck)
        print(f"assigned slug {deck['slug']!r} to {deck_yaml_path.parent.name}")
    return deck


def resolve_slides(deck: dict, presentation_dir: Path) -> list[tuple[Path, str]]:
    """Resolve each deck.yaml slide entry to (slide_dir, slide_name).

    `lib:` entries resolve against the library (author mode only — a
    frozen deck must not contain any `lib:` entries). Plain string entries
    resolve against the presentation folder (local slides, including
    already-frozen copies).
    """
    resolved = []
    for entry in deck["slides"]:
        if isinstance(entry, dict) and "lib" in entry:
            if deck.get("frozen"):
                raise ValueError(
                    f"frozen deck {presentation_dir.name} has a lib: entry "
                    f"({entry['lib']!r}) — frozen decks must be fully local"
                )
            slide_dir = SLIDES_LIB / entry["lib"]
            slide_name = slide_dir.name
        else:
            html_path = presentation_dir / entry
            slide_dir = html_path.parent
            slide_name = slide_dir.name
        resolved.append((slide_dir, slide_name))
    return resolved


def run_generators(slide_dir: Path) -> None:
    scripts_dir = slide_dir / "scripts"
    if not scripts_dir.is_dir():
        return
    for script in sorted(scripts_dir.glob("*.py")):
        subprocess.run([sys.executable, str(script)], cwd=slide_dir, check=True)


def rewrite_asset_paths(html: str, slide_name: str) -> str:
    """Rewrite slide-relative `figures/`/`interactives/` src refs to be
    namespaced under the slide's own folder, since multiple slides'
    fragments are assembled into a single combined index.html."""
    for asset_dir in ASSET_DIRS:
        html = re.sub(
            rf'(src=["\']){asset_dir}/',
            rf'\g<1>{slide_name}/{asset_dir}/',
            html,
        )
    return html


def copy_slide_assets(slide_dir: Path, dest_dir: Path) -> None:
    for asset_dir in ASSET_DIRS:
        src = slide_dir / asset_dir
        if src.is_dir():
            shutil.copytree(src, dest_dir / slide_dir.name / asset_dir, dirs_exist_ok=True)


def copy_theme_and_reveal(dest_dir: Path) -> None:
    shutil.copytree(SHARED / "style-guide", dest_dir / "theme", dirs_exist_ok=True,
                     ignore=shutil.ignore_patterns("template.html"))
    shutil.copytree(SHARED / "reveal", dest_dir / "reveal", dirs_exist_ok=True,
                     ignore=shutil.ignore_patterns("*.tgz"))


def build_deck(presentation_dir: Path, no_generate: bool = False) -> Path:
    deck_yaml_path = presentation_dir / "deck.yaml"
    deck = ensure_slug(deck_yaml_path, load_deck(deck_yaml_path))

    slide_htmls = []
    for entry, (slide_dir, slide_name) in zip(deck["slides"], resolve_slides(deck, presentation_dir)):
        html_filename = Path(entry).name if isinstance(entry, str) else f"{slide_name}.html"
        html_path = slide_dir / html_filename
        if not deck.get("frozen") and not no_generate:
            run_generators(slide_dir)
        html = html_path.read_text()
        slide_htmls.append(rewrite_asset_paths(html, slide_name))

    is_unlisted = deck.get("visibility") == "unlisted"
    out_name = deck["slug"] if is_unlisted else deck["presentation_name"]
    out_dir = DIST / str(deck["year"]) / out_name
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    for slide_dir, _ in resolve_slides(deck, presentation_dir):
        copy_slide_assets(slide_dir, out_dir)
    copy_theme_and_reveal(out_dir)

    env = Environment(loader=FileSystemLoader(str(TEMPLATES)))
    template = env.get_template("index.html.j2")
    rendered = template.render(
        title=deck["title"],
        noindex=is_unlisted,
        slides_html="\n".join(slide_htmls),
        reveal_config_overrides=deck.get("reveal_config"),
    )
    (out_dir / "index.html").write_text(rendered)

    print(f"built {presentation_dir.name} -> dist/{deck['year']}/{out_name}/index.html"
          + ("  [unlisted]" if is_unlisted else ""))
    return out_dir


def freeze_deck(presentation_dir: Path) -> None:
    deck_yaml_path = presentation_dir / "deck.yaml"
    deck = load_deck(deck_yaml_path)
    if deck.get("frozen"):
        print(f"{presentation_dir.name} is already frozen")
        return

    local_slides_dir = presentation_dir / "slides"
    local_slides_dir.mkdir(exist_ok=True)

    new_slides = []
    for entry in deck["slides"]:
        if isinstance(entry, dict) and "lib" in entry:
            src_dir = SLIDES_LIB / entry["lib"]
            slide_name = src_dir.name
            dest_dir = local_slides_dir / slide_name
            shutil.copytree(src_dir, dest_dir, dirs_exist_ok=True)
            new_slides.append(f"slides/{slide_name}/{slide_name}.html")
        else:
            new_slides.append(entry)
    deck["slides"] = new_slides
    deck["frozen"] = True
    if deck.get("visibility") == "unlisted" and not deck.get("slug"):
        deck["slug"] = generate_slug()

    save_deck(deck_yaml_path, deck)
    print(f"froze {presentation_dir.name} — {len(new_slides)} slides now local, frozen: true")


def all_presentation_dirs() -> list[Path]:
    return sorted(p.parent for p in PRESENTATIONS.glob("*/*/deck.yaml"))


def generate_landing_page() -> None:
    by_year: dict[int, list[dict]] = {}
    for pdir in all_presentation_dirs():
        deck = load_deck(pdir / "deck.yaml")
        if deck.get("visibility") != "public":
            continue
        by_year.setdefault(deck["year"], []).append(deck)

    env = Environment(loader=FileSystemLoader(str(TEMPLATES)))
    template = env.get_template("landing.html.j2")
    rendered = template.render(by_year=dict(sorted(by_year.items(), reverse=True)))
    DIST.mkdir(exist_ok=True)
    (DIST / "index.html").write_text(rendered)
    print("built dist/index.html (landing page)")


def free_port() -> int:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def serve(directory: Path) -> None:
    """Serve `directory` over HTTP and open it in the default browser.
    Blocks until Ctrl+C — required (not just convenient) for slides with
    <iframe>-embedded interactives, which browsers refuse to load over a
    bare file:// path."""
    import time
    import webbrowser

    port = free_port()
    proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--directory", str(directory)]
    )
    url = f"http://localhost:{port}/"
    time.sleep(0.3)
    print(f"previewing {directory} at {url}  (Ctrl+C to stop)")
    webbrowser.open(url)
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()


def resolve_presentation_arg(arg: str) -> Path:
    candidate = PRESENTATIONS / arg
    if (candidate / "deck.yaml").is_file():
        return candidate
    candidate = Path(arg)
    if (candidate / "deck.yaml").is_file():
        return candidate
    raise SystemExit(f"no deck.yaml found for presentation {arg!r}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("presentation", nargs="?",
                         help="presentation to build, e.g. 2026/06-30-department-meeting")
    parser.add_argument("--all", action="store_true", help="build every presentation")
    parser.add_argument("--freeze", metavar="PRESENTATION",
                         help="copy lib: slides local, rewrite manifest, set frozen: true")
    parser.add_argument("--no-generate", action="store_true",
                         help="skip running slide generator scripts (fast preview)")
    parser.add_argument("--preview", action="store_true",
                         help="after building, serve the output and open it in a browser")
    args = parser.parse_args()

    if args.freeze:
        freeze_deck(resolve_presentation_arg(args.freeze))
        return

    if args.all:
        for pdir in all_presentation_dirs():
            build_deck(pdir, no_generate=args.no_generate)
        generate_landing_page()
        if args.preview:
            serve(DIST)
        return

    if not args.presentation:
        parser.error("specify a presentation, or use --all / --freeze")

    out_dir = build_deck(resolve_presentation_arg(args.presentation), no_generate=args.no_generate)
    generate_landing_page()
    if args.preview:
        serve(out_dir)


if __name__ == "__main__":
    main()
