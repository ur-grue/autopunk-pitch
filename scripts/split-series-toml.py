#!/usr/bin/env python3
"""
split-series-toml.py — Splits a series TOML with [books.NN] sections into individual per-book TOMLs.

Usage:
    python3 scripts/split-series-toml.py templates/signal-and-noise-ai-romance.toml

Creates:
    templates/signal-noise-book-01.toml
    templates/signal-noise-book-02.toml
    ...
"""

import sys
import os

try:
    import tomllib
except ImportError:
    import tomli as tomllib


def load_toml(path):
    with open(path, "rb") as f:
        return tomllib.load(f)


def to_toml_value(v, indent=0):
    """Convert a Python value to TOML string representation."""
    if isinstance(v, str):
        if "\n" in v or len(v) > 80:
            return f'"""\n{v}"""'
        return f'"{v}"'
    elif isinstance(v, bool):
        return "true" if v else "false"
    elif isinstance(v, (int, float)):
        return str(v)
    elif isinstance(v, list):
        if all(isinstance(x, str) for x in v):
            items = ", ".join(f'"{x}"' for x in v)
            if len(items) > 80:
                items = ",\n".join(f'  "{x}"' for x in v)
                return f"[\n{items}\n]"
            return f"[{items}]"
        return str(v)
    return str(v)


def write_section(f, section_name, data, comment=None):
    """Write a TOML section."""
    if comment:
        f.write(f"# {comment}\n")
    f.write(f"[{section_name}]\n")
    for k, v in data.items():
        if isinstance(v, dict):
            continue  # Skip nested dicts, handle separately
        f.write(f"{k} = {to_toml_value(v)}\n")
    f.write("\n")


def build_previous_books(books, current_num):
    """Build a list of previous book references."""
    prev = []
    for i in range(1, current_num):
        key = f"{i:02d}"
        if key in books:
            b = books[key]
            title = b.get("title_working", f"Book {i}")
            heroine = b.get("heroine", "").split(",")[0] if b.get("heroine") else f"Heroine {i}"
            prev.append(f"{title} ({heroine})")
    return prev


def generate_book_toml(series_config, book_num, book_config, all_books, output_path):
    """Generate a standalone TOML for one book."""
    meta = series_config.get("metadata", {})
    setting = series_config.get("setting", {})
    emotional = series_config.get("emotional_design", {})
    nd_rep = series_config.get("neurodivergent_representation", {})
    romantic = series_config.get("romantic_dynamic", {})
    series_arc = series_config.get("series_arc", {})
    pacing = series_config.get("pacing", {})
    cover = series_config.get("cover_design", {})
    marketing = series_config.get("marketing", {})

    title = book_config.get("title_working", f"Book {book_num}")
    subtitle = book_config.get("subtitle", "")
    heroine_desc = book_config.get("heroine", "")
    heroine_name = heroine_desc.split(",")[0] if heroine_desc else f"Heroine {book_num}"

    prev_books = build_previous_books(all_books, book_num)

    with open(output_path, "w") as f:
        # Header comment
        f.write(f"# {'=' * 65}\n")
        f.write(f"# {meta.get('series_name', 'Series')} — Book {book_num}: {title}\n")
        f.write(f"# {subtitle}\n")
        f.write(f"# {'=' * 65}\n")
        f.write(f"# Auto-generated from {os.path.basename(sys.argv[1])}\n\n")

        # [metadata] — merged series + book-specific
        f.write("[metadata]\n")
        f.write(f'name = "{title}"\n')
        f.write(f'series_name = "{meta.get("series_name", "")}"\n')
        f.write(f'genre = "{meta.get("genre", "")}"\n')
        f.write(f'sub_genre = "{meta.get("sub_genre", "")}"\n')
        f.write(f'tone = "{meta.get("tone", "")}"\n')
        f.write(f"themes = {to_toml_value(meta.get('themes', []))}\n")
        f.write(f'target_audience = "{meta.get("target_audience", "")}"\n')
        f.write(f'author_style = "{meta.get("author_style", "")}"\n')
        f.write(f"n_chapters = {meta.get('n_chapters', 24)}\n")
        f.write(f"chapter_length = {meta.get('chapter_length', 2500)}\n")
        f.write(f'heat_level = "{meta.get("heat_level", "fade-to-black")}"\n')
        f.write(f'content_rating = "{meta.get("content_rating", "")}"\n')
        f.write(f'description = "{subtitle}"\n')
        tropes = book_config.get("tropes", [])
        f.write(f"tropes = {to_toml_value(tropes)}\n")
        f.write("\n")

        # [series]
        f.write("[series]\n")
        f.write(f'series_name = "{meta.get("series_name", "")}"\n')
        f.write(f"book_number = {book_num}\n")
        f.write(f"total_books = {meta.get('n_books', 12)}\n")
        f.write(f'ai_name = "{series_arc.get("ai_name", "Aria")}"\n')
        f.write(f'overarching_question = "{series_arc.get("overarching_question", "")}"\n')
        f.write(f'ai_evolution = """\n{series_arc.get("ai_evolution", "")}\n"""\n')
        f.write(f'connection_between_books = """\n{series_arc.get("connection_between_books", "")}\n"""\n')
        f.write(f"previous_books = {to_toml_value(prev_books)}\n")
        f.write("\n")

        # [book_specific]
        f.write("[book_specific]\n")
        f.write(f'title = "{title}"\n')
        f.write(f'subtitle = "{subtitle}"\n')
        f.write(f'heroine = """\n{heroine_desc}\n"""\n')
        f.write(f'heroine_nd = "{book_config.get("heroine_nd", "")}"\n')
        f.write(f'ai_form = """\n{book_config.get("ai_form", "")}\n"""\n')
        f.write(f"tropes = {to_toml_value(tropes)}\n")
        f.write(f'setting = "{book_config.get("setting", "")}"\n')
        f.write(f'emotional_core = """\n{book_config.get("emotional_core", "")}\n"""\n')
        f.write(f'accent_color = "{book_config.get("accent_color", "")}"\n')
        f.write("\n")

        # [setting] — series-level
        write_section(f, "setting", setting, "Series-level setting")

        # [emotional_design]
        write_section(f, "emotional_design", emotional)

        # [neurodivergent_representation]
        write_section(f, "neurodivergent_representation", nd_rep, "Critical for prompt quality")

        # [romantic_dynamic]
        write_section(f, "romantic_dynamic", romantic)

        # [pacing]
        write_section(f, "pacing", pacing)

        # [cover_design]
        write_section(f, "cover_design", cover)

    print(f"  Book {book_num:2d}: {output_path} ({title})")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/split-series-toml.py <series-toml>")
        sys.exit(1)

    toml_path = sys.argv[1]
    config = load_toml(toml_path)

    meta = config.get("metadata", {})
    books = config.get("books", {})
    n_books = meta.get("n_books", len(books))
    series_slug = meta.get("series_name", "series").lower().replace(" ", "-").replace("&", "and")

    if not books:
        print("ERROR: No [books.NN] sections found in TOML")
        sys.exit(1)

    output_dir = os.path.dirname(toml_path) or "templates"
    print(f"Splitting {toml_path} into {n_books} individual TOMLs...")
    print(f"Output: {output_dir}/{series_slug}-book-NN.toml\n")

    for i in range(1, n_books + 1):
        key = f"{i:02d}"
        if key not in books:
            print(f"  WARNING: [books.{key}] not found, skipping")
            continue
        output_path = os.path.join(output_dir, f"{series_slug}-book-{key}.toml")
        generate_book_toml(config, i, books[key], books, output_path)

    print(f"\nDone. {n_books} TOMLs generated.")


if __name__ == "__main__":
    main()
