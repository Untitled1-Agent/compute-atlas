"""Protect the user-approved visual references from broken documentation links."""
import hashlib
import json
from pathlib import Path


def test_six_approved_visual_references_are_real_files():
    root = Path(__file__).resolve().parents[1] / 'docs' / 'mockups'
    manifest = json.loads((root / 'sha256.json').read_text())
    assert len(manifest) == 6
    readme = (root / 'README.md').read_text()
    for name, expected in manifest.items():
        body = (root / name).read_bytes()
        assert body[:4] == b'RIFF' and body[8:12] == b'WEBP'
        assert hashlib.sha256(body).hexdigest() == expected
        assert f']({name})' in readme
