#!/usr/bin/env python3
"""Check file completeness, source hashes, coverage, and embedded attachments."""
from __future__ import annotations
import base64
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

def main() -> None:
    manifest = json.loads((ROOT / "delivery/manifest.json").read_text(encoding="utf-8"))
    failures: list[str] = []
    for entry in manifest["files"]:
        path = ROOT / entry["path"]
        if not path.is_file():
            failures.append("Missing: " + entry["path"])
            continue
        data = path.read_bytes()
        if len(data) != entry["bytes"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
            failures.append("Changed: " + entry["path"])
    if failures:
        print("Delivery is incomplete or differs from the original snapshot:", file=sys.stderr)
        print("\n".join(failures), file=sys.stderr)
        raise SystemExit(1)
    atlas = json.loads((ROOT / "data/atlas.json").read_text(encoding="utf-8"))
    for key in ("sites", "companies", "sources"):
        if len(atlas[key]) != manifest["coverage"][key]:
            raise ValueError("Coverage mismatch: " + key)
    originals = json.loads((ROOT / "data/manifest.json").read_text(encoding="utf-8"))
    html = (ROOT / "compute_atlas.html").read_text(encoding="utf-8")
    match = re.search(r'<script type="application/json" id="original-files">(.*?)</script>', html, re.S)
    if not match:
        raise ValueError("Embedded original-file archive is missing.")
    embedded = json.loads(match.group(1))
    if set(embedded) != {item["filename"] for item in originals}:
        raise ValueError("Embedded attachment inventory differs from the source manifest.")
    for item in originals:
        content = base64.b64decode(embedded[item["filename"]], validate=True)
        if hashlib.sha256(content).hexdigest() != item["sha256"]:
            raise ValueError("Embedded attachment mismatch: " + item["filename"])
    print(f"PASS: {len(manifest['files'])} delivery files match their original SHA-256 hashes.")
    print(f"PASS: {len(originals)} embedded original attachments match their source hashes.")
    print("PASS: coverage = " + json.dumps(manifest["coverage"], sort_keys=True))
    print("This verifies packaging integrity; it is not a fresh investment-data audit.")

if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError) as error:
        print(f"Validation failed: {error}", file=sys.stderr)
        raise SystemExit(1)
