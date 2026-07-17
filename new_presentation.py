#!/usr/bin/env python3
"""Scaffold a new presentation.

Prompts for the date and title, then creates
presentations/<year>/<mm-dd-slug>/ with a starter deck.yaml, a title slide,
and a blank acknowledgements slide. Add `lib:` entries to the generated
deck.yaml for any library content, then preview with:

    python build.py <year>/<name> --preview
"""
import html
import re
from datetime import datetime

from build import PRESENTATIONS, ROOT, save_deck

TITLE_HTML = """        <section
          class="title-slide"
          data-background-gradient="linear-gradient(225deg, #E04F39 0%, #AF2D24 50%, #8C1515 100%)"
        >
          <img
            src="theme/assets/logos/title_overlay.svg"
            aria-hidden="true"
            style="position:absolute; inset:0; width:100%; height:100%; object-fit:cover; opacity:0.12; pointer-events:none;"
          />
          <div style="position:relative; z-index:1; padding-top: 1.0em;">
            <h1>{title}</h1>
            <hr class="title-divider" />
            <!-- optional one-line subtitle: <p>...</p> -->
            <p>Matt Bain &nbsp;|&nbsp; <!-- venue/event --> &nbsp;|&nbsp; {pretty_date}</p>
          </div>
        </section>
"""

ACKNOWLEDGEMENTS_HTML = """        <section>
          <h3 style="margin: 0 0 0.4em;">Acknowledgements</h3>
          <div style="font-size: 0.42em;">
            <div class="col-box" style="border: 1px solid #ddd; border-radius: 8px; padding: 0.8em;">
              <ul>
                <li><!-- collaborators, group, funding, beamtime credit --></li>
              </ul>
            </div>
          </div>
        </section>
"""


def slugify(text: str, max_words: int = 4) -> str:
    words = re.findall(r"[A-Za-z0-9]+", text.lower())[:max_words]
    return "-".join(words) if words else "presentation"


def main() -> None:
    date_str = input("Date of presentation (YYYY-MM-DD): ").strip()
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise SystemExit(f"couldn't parse {date_str!r} as YYYY-MM-DD")

    title = input("Title: ").strip()
    if not title:
        raise SystemExit("title can't be empty")

    presentation_name = f"{date.strftime('%m-%d')}-{slugify(title)}"
    pretty_date = f"{date.strftime('%B')} {date.day}, {date.year}"
    presentation_dir = PRESENTATIONS / str(date.year) / presentation_name

    if presentation_dir.exists():
        raise SystemExit(f"{presentation_dir.relative_to(ROOT)} already exists")

    title_dir = presentation_dir / "slides" / "title"
    ack_dir = presentation_dir / "slides" / "acknowledgements"
    title_dir.mkdir(parents=True)
    ack_dir.mkdir(parents=True)

    (title_dir / "title.html").write_text(
        TITLE_HTML.format(title=html.escape(title, quote=False), pretty_date=pretty_date)
    )
    (ack_dir / "acknowledgements.html").write_text(ACKNOWLEDGEMENTS_HTML)

    save_deck(presentation_dir / "deck.yaml", {
        "title": title,
        "presentation_name": presentation_name,
        "year": date.year,
        "visibility": "unlisted",
        "frozen": False,
        "slug": None,
        "theme": "slac",
        "slides": [
            "slides/title/title.html",
            "slides/acknowledgements/acknowledgements.html",
        ],
    })

    rel = presentation_dir.relative_to(ROOT)
    print(f"\ncreated {rel}/")
    print("  deck.yaml")
    print("  slides/title/title.html                       <- fill in the venue/event placeholder")
    print("  slides/acknowledgements/acknowledgements.html <- fill in acknowledgements")
    print(f"\nAdd lib: entries to deck.yaml for library content, then preview:")
    print(f"  python build.py {date.year}/{presentation_name} --preview")


if __name__ == "__main__":
    main()
