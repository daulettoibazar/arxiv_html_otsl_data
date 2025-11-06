#!/usr/bin/env python3
"""
Clean HTML files by removing specific whitespace characters.

Removes the following from each HTML file's content:
  - \n (newline)
  - \u2004  Three-Per-Em Space
  - \u2005  Four-Per-Em Space
  - \u2006  Six-Per-Em Space
  - \u2007  Figure Space
  - \u2008  Punctuation Space
  - \u2009  Thin Space
  - \u200A  Hair Space
  - \u202F  Narrow No-Break Space
  - \u205F  Medium Mathematical Space
  - \u3000  Ideographic Space

By default, processes HTML files in: <repo>/tables/html (non-recursive).
Use --html-dir to override and --recursive to include subfolders.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path


def build_logger() -> logging.Logger:
	logger = logging.getLogger("clean_html")
	if logger.handlers:
		return logger
	logger.setLevel(logging.INFO)
	handler = logging.StreamHandler(sys.stdout)
	handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
	logger.addHandler(handler)
	return logger


LOGGER = build_logger()


CHARS_TO_REMOVE = [
	"\n",
	"\u2004",  # Three-Per-Em Space
	"\u2005",  # Four-Per-Em Space
	"\u2006",  # Six-Per-Em Space
	"\u2007",  # Figure Space
	"\u2008",  # Punctuation Space
	"\u2009",  # Thin Space
	"\u200A",  # Hair Space
	"\u202F",  # Narrow No-Break Space
	"\u205F",  # Medium Mathematical Space
	"\u3000",  # Ideographic Space
]


def make_translation_table():
	"""Return a dict usable with str.translate to delete chars."""
	return {ord(c): None for c in CHARS_TO_REMOVE}


def clean_file(file_path: Path, trans_tbl) -> bool:
	"""Clean a single HTML file; return True if modified."""
	try:
		original = file_path.read_text(encoding="utf-8", errors="ignore")
	except Exception as e:
		LOGGER.error(f"Failed to read {file_path}: {e}")
		return False

	cleaned = original.translate(trans_tbl)
	if cleaned == original:
		return False

	try:
		file_path.write_text(cleaned, encoding="utf-8")
		return True
	except Exception as e:
		LOGGER.error(f"Failed to write {file_path}: {e}")
		return False


def resolve_default_html_dir() -> Path:
	base = Path(__file__).parent
	return base / "tables" / "html"


def parse_args(argv=None):
	p = argparse.ArgumentParser(description="Remove specific whitespace from HTML files.")
	p.add_argument(
		"--html-dir",
		type=Path,
		default=None,
		help="Directory containing .html files (default: <repo>/tables/html)",
	)
	p.add_argument(
		"--recursive",
		action="store_true",
		help="Recurse into subdirectories when searching for .html files.",
	)
	return p.parse_args(argv)


def main(argv=None) -> int:
	args = parse_args(argv)

	html_dir = args.html_dir or resolve_default_html_dir()
	if not html_dir.exists() or not html_dir.is_dir():
		LOGGER.error(f"HTML directory not found: {html_dir}")
		return 2

	pattern = "**/*.html" if args.recursive else "*.html"
	files = sorted(html_dir.rglob("*.html") if args.recursive else html_dir.glob("*.html"))

	if not files:
		LOGGER.info(f"No HTML files found in {html_dir} (recursive={args.recursive}).")
		return 0

	trans_tbl = make_translation_table()
	total = len(files)
	modified = 0

	LOGGER.info(f"Processing {total} HTML files in {html_dir} (recursive={args.recursive})...")
	for fp in files:
		if clean_file(fp, trans_tbl):
			modified += 1

	LOGGER.info(f"Done. Modified {modified}/{total} files.")
	return 0


if __name__ == "__main__":
	sys.exit(main())

