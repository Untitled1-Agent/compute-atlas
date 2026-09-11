#!/usr/bin/env python3
"""Import the original Compute Atlas ZIP into this checkout, without publishing it."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="Path to compute_atlas_complete_app.zip")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "delivery/manifest.json").read_text(encoding="utf-8"))
    if sha256(args.archive.read_bytes()) != manifest["zip_sha256"]:
        raise ValueError("ZIP checksum mismatch; use the original complete-app delivery.")
    expected = {entry["member"]: entry for entry in manifest["files"]}
    payload: list[tuple[Path, bytes]] = []
    with zipfile.ZipFile(args.archive) as archive:
        members = [item for item in archive.infolist() if not item.is_dir()]
        if len(members) != len(expected) or {item.filename for item in members} != set(expected):
            raise ValueError("ZIP contents differ from the checked manifest.")
        for item in members:
            entry = expected[item.filename]
            path = PurePosixPath(entry["path"])
            if path.is_absolute() or ".." in path.parts or "\\" in entry["path"]:
                raise ValueError("Unsafe destination in manifest.")
            target = ROOT.joinpath(*path.parts)
            if not target.resolve().is_relative_to(ROOT.resolve()):
                raise ValueError("Destination escapes this checkout.")
            if item.file_size != entry["bytes"]:
                raise ValueError("Unexpected member size: " + item.filename)
            data = archive.read(item)
            if sha256(data) != entry["sha256"]:
                raise ValueError("Member checksum mismatch: " + item.filename)
            payload.append((target, data))
    # Validate the entire archive before changing any tracked files.
    for target, data in payload:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    status = ROOT / "delivery/README.md"
    status.write_text(
        "# Complete delivery imported\n\n"
        "The app, source, full data archive, eight original attachments, and QA files "
        "are present in this checkout. Run `python tools/validate_delivery.py` to "
        "verify all package hashes. This status describes file completeness, not "
        "a fresh financial-data audit.\n\n"
        "Importing does not commit, push, merge, enable Pages, or change repository visibility. "
        "Review the diff before committing and pushing this PR branch.\n",
        encoding="utf-8",
    )
    readme = ROOT / "README.md"
    if readme.exists():
        text = readme.read_text(encoding="utf-8")
        text = text.replace(
            "- App source (`src/`, `data/`, `originals/`, `qa/`, built `compute_atlas.html`) — pending upload",
            "- App source, full dataset, original attachments, QA files, and built `compute_atlas.html` — included",
        )
        readme.write_text(text, encoding="utf-8")
    print(f"Imported {len(payload)} checksum-verified files into {ROOT}.")
    print("Next: python tools/validate_delivery.py")

if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        print(f"Import failed: {error}", file=sys.stderr)
        raise SystemExit(1)
