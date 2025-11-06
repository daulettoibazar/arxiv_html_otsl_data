#!/usr/bin/env python3
"""
Remove any consecutive spaces (>1) from HTML files in a folder.

Default folder: <repo>/tables/html (non-recursive).
Use --html-dir to override and --recursive to scan subfolders.

Behavior: sequences of two or more literal spaces "  " are removed (replaced with "").
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path


def build_logger() -> logging.Logger:
	logger = logging.getLogger("remove_consecutive_spaces")
	if logger.handlers:
		return logger
	logger.setLevel(logging.INFO)
	handler = logging.StreamHandler(sys.stdout)
	handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
	logger.addHandler(handler)
	return logger


LOGGER = build_logger()


SPACE_RUN_RE = re.compile(r" {2,}")  # two or more literal spaces


def resolve_default_html_dir() -> Path:
	return Path(__file__).parent / "tables" / "html"


def clean_file(path: Path) -> bool:
	"""Remove runs of 2+ spaces from file; return True if modified."""
	try:
		original = path.read_text(encoding="utf-8", errors="ignore")
	except Exception as e:
		LOGGER.error(f"Failed to read {path}: {e}")
		return False

	cleaned = SPACE_RUN_RE.sub("", original)
	if cleaned == original:
		return False

	try:
		path.write_text(cleaned, encoding="utf-8")
		return True
	except Exception as e:
		LOGGER.error(f"Failed to write {path}: {e}")
		return False


def parse_args(argv=None):
	p = argparse.ArgumentParser(description="Remove consecutive spaces (>1) from HTML files.")
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

	files = sorted(
		html_dir.rglob("*.html") if args.recursive else html_dir.glob("*.html")
	)
	if not files:
		LOGGER.info(f"No HTML files found in {html_dir} (recursive={args.recursive}).")
		return 0

	LOGGER.info(f"Processing {len(files)} files in {html_dir} (recursive={args.recursive})...")
	modified = 0
	for f in files:
		if clean_file(f):
			modified += 1

	LOGGER.info(f"Done. Modified {modified}/{len(files)} files.")
	return 0


if __name__ == "__main__":
	sys.exit(main())

