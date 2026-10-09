#!/usr/bin/env python3
"""Version a static publication by its runtime asset paths and bytes.

Run against the final Pages artifact, after instance config is populated.
Event payloads, reports, timestamps and Git history are not version inputs.
"""

import argparse
import hashlib
import json
from pathlib import Path


REQUIRED_FILES = (
    "categories.json", "cities.json", "source_priority.json",
    "xmlui/index.html", "xmlui/shell.js", "xmlui/shell.css",
    "xmlui/helpers.js", "xmlui/xs-trace.js", "xmlui/Main.xmlui",
    "xmlui/Globals.xs", "xmlui/config.json",
    "xmlui/xmlui/xmlui-standalone.umd.js",
    "xmlui/xmlui/xmlui-masonry.js", "xmlui/xmlui/xmlui-grid-layout.js",
    "xmlui/xmlui/xmlui-grid-layout.css",
)
ASSET_DIRS = ("xmlui/components", "xmlui/themes", "xmlui/icons", "xmlui/xmlui")
ASSET_SUFFIXES = {".xmlui", ".xs", ".js", ".css", ".json", ".svg", ".html",
                  ".woff", ".woff2", ".png", ".jpg", ".webp"}


def asset_paths(root: Path) -> list[str]:
    paths = set(REQUIRED_FILES)
    for directory in ASSET_DIRS:
        found = [p for p in (root / directory).rglob("*")
                 if p.is_file() and p.suffix in ASSET_SUFFIXES]
        if not found:
            raise ValueError(f"Missing or empty asset directory: {directory}")
        paths.update(p.relative_to(root).as_posix() for p in found)
    # Include optional root-level code-behind and future runtime assets.
    paths.update(p.relative_to(root).as_posix() for p in (root / "xmlui").iterdir()
                 if p.is_file() and p.suffix in ASSET_SUFFIXES
                 and p.name not in {"test.html", "config.local.js"})
    for name in sorted(paths):
        path = root / name
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"Missing or symlinked runtime asset: {name}")
    return sorted(paths)


def app_version(root: Path) -> str:
    digest = hashlib.sha256(b"community-calendar-assets-v1\0")
    for name in asset_paths(root):
        # Length framing distinguishes file boundaries and captures renames.
        encoded = name.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
        digest.update(hashlib.sha256((root / name).read_bytes()).digest())
    return digest.hexdigest()[:16]


def write_version(root: Path) -> str:
    version = app_version(root)  # Validate all inputs before touching output.
    target = root / "xmlui/version.txt"
    temporary = target.with_suffix(".tmp")
    temporary.write_text(version + "\n", encoding="utf-8")
    temporary.replace(target)
    return version


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--list", action="store_true", help="List inputs as JSON; write nothing")
    args = parser.parse_args()
    try:
        print(json.dumps(asset_paths(args.root)) if args.list else write_version(args.root))
    except (OSError, ValueError) as exc:
        parser.exit(1, f"app-version: {exc}\n")


if __name__ == "__main__":
    main()
