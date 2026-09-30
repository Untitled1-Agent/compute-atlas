"""Static integrity audit for Compute Atlas source, entities and embedded originals."""
from __future__ import annotations

import base64
import hashlib
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKS = []


def check(name, ok, detail=None):
    CHECKS.append({"test": name, "pass_": bool(ok), "detail": detail})
    print(("PASS " if ok else "FAIL ") + name, flush=True)
    if not ok and detail is not None:
        print("  " + str(detail), flush=True)


def finite_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def hash_bytes(data):
    return hashlib.sha256(data).hexdigest()


atlas = json.loads((ROOT / "data/atlas.json").read_text())
archive = json.loads((ROOT / "data/archive.json").read_text())
manifest = json.loads((ROOT / "data/manifest.json").read_text())

# Core collection counts and identifier integrity.
expected_counts = {"sites": 79, "companies": 29, "sources": 64}
actual_counts = {key: len(atlas[key]) for key in expected_counts}
check("core collection counts match audited dataset", actual_counts == expected_counts, actual_counts)

for key in ("companies", "sites", "sources", "costs", "contracts"):
    ids = [row.get("id") for row in atlas.get(key, [])]
    bad = [x for x in ids if not isinstance(x, str) or not x.strip()]
    dupes = sorted({x for x in ids if ids.count(x) > 1})
    check(f"{key} IDs are present and unique", not bad and not dupes, {"missing": bad, "duplicates": dupes})

company_ids = {row["id"] for row in atlas["companies"]}
source_ids = {row["id"] for row in atlas["sources"]}
site_ref_errors = []
for site in atlas["sites"]:
    refs = site.get("company_ids") or []
    if any(ref not in company_ids for ref in refs):
        site_ref_errors.append({"site": site["id"], "company_ids": refs})
    primary = site.get("primary_company")
    if primary is not None and primary not in company_ids:
        site_ref_errors.append({"site": site["id"], "primary_company": primary})
check("all facility company references resolve", not site_ref_errors, site_ref_errors[:10])

# Source-reference tokens used throughout atlas records should resolve when they look like source IDs.
source_token_re = re.compile(r"\b(?:S|N)\d{2}\b")
unresolved = []
def walk(obj, path="root"):
    if isinstance(obj, dict):
        for key, value in obj.items():
            walk(value, f"{path}.{key}")
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            walk(value, f"{path}[{i}]")
    elif isinstance(obj, str):
        for token in source_token_re.findall(obj):
            if token not in source_ids:
                unresolved.append({"token": token, "path": path})
walk({k: atlas[k] for k in ("companies", "sites", "costs", "contracts") if k in atlas})
check("all Sxx/Nxx source tokens in analytical records resolve", not unresolved, unresolved[:20])

# Geographic and power-field sanity.
geo_errors = []
power_errors = []
for site in atlas["sites"]:
    lat, lon = site.get("lat"), site.get("lon")
    if (lat is None) != (lon is None):
        geo_errors.append({"site": site["id"], "lat": lat, "lon": lon})
    elif lat is not None and (not finite_number(lat) or not finite_number(lon) or not (-90 <= lat <= 90) or not (-180 <= lon <= 180)):
        geo_errors.append({"site": site["id"], "lat": lat, "lon": lon})
    for phase_name in ("snapshot", "target"):
        phase = site.get(phase_name)
        if not phase:
            continue
        value = phase.get("it_mw")
        if value is not None and (not finite_number(value) or value < 0):
            power_errors.append({"site": site["id"], "phase": phase_name, "it_mw": value})
check("all mapped coordinates are valid approximate lat/lon pairs", not geo_errors, geo_errors)
check("all disclosed comparable IT-MW fields are finite and non-negative", not power_errors, power_errors)

# Archive coverage already relied on by the app.
phase_rows = sum(len(site.get("raw", [])) for site in atlas["sites"])
report_sections = sum(len(report["sections"]) for report in archive["reports"])
report_tables = sum(report["table_count"] for report in archive["reports"])
workbook_cells = sum(len(sheet["cells"]) for book in archive["workbooks"] for sheet in book["sheets"])
check("archive coverage remains 92 phases / 108 sections / 101 tables / 5938 cells", (phase_rows, report_sections, report_tables, workbook_cells) == (92, 108, 101, 5938), {"phase_rows": phase_rows, "report_sections": report_sections, "report_tables": report_tables, "workbook_cells": workbook_cells})

# Originals on disk must exactly match their source manifest.
manifest_names = [item["filename"] for item in manifest]
disk_failures = []
for item in manifest:
    path = ROOT / "originals" / item["filename"]
    if not path.exists():
        disk_failures.append({"file": item["filename"], "error": "missing"})
        continue
    data = path.read_bytes()
    digest = hash_bytes(data)
    if digest != item["sha256"]:
        disk_failures.append({"file": item["filename"], "expected": item["sha256"], "actual": digest})
check("all eight checked-in original files match manifest SHA-256", not disk_failures and len(manifest) == 8, disk_failures)

# Atlas' exposed manifest must agree with the source manifest.
check("atlas exposed original-file manifest matches data/manifest.json", atlas.get("manifest") == manifest, {"atlas_manifest_count": len(atlas.get("manifest", [])), "source_manifest_count": len(manifest)})

# The generated standalone must contain the same original bytes, not merely eight filenames.
html = (ROOT / "compute_atlas.html").read_text()
match = re.search(r'<script type="application/json" id="original-files">(.*?)</script>', html, flags=re.S)
embedded_failures = []
if not match:
    embedded_failures.append({"error": "original-files script missing"})
else:
    embedded = json.loads(match.group(1))
    if set(embedded) != set(manifest_names):
        embedded_failures.append({"error": "embedded filename set differs", "embedded": sorted(embedded), "manifest": sorted(manifest_names)})
    for item in manifest:
        payload = embedded.get(item["filename"])
        if payload is None:
            continue
        try:
            data = base64.b64decode(payload, validate=True)
        except Exception as exc:
            embedded_failures.append({"file": item["filename"], "error": f"invalid base64: {exc}"})
            continue
        digest = hash_bytes(data)
        if digest != item["sha256"]:
            embedded_failures.append({"file": item["filename"], "expected": item["sha256"], "actual": digest})
check("standalone embeds byte-identical copies of all eight originals", not embedded_failures, embedded_failures)

# Numeric sanity in the investment layer. OCF may legitimately be negative; assets,
# obligations, capex, prices and physical-capacity quantities may not.
financial_errors = []
for company in atlas["companies"]:
    commitment = company.get("commitment") or {}
    stock = company.get("stock") or {}
    for key in ("capex_b", "net_ppe_b", "cip_b", "uncommenced_leases_b", "purchase_or_contract_b", "total_obligations_b", "debt_b", "rpo_b"):
        value = commitment.get(key)
        if value is not None and (not finite_number(value) or value < 0):
            financial_errors.append({"company": company["id"], "field": key, "value": value})
    ocf = commitment.get("ocf_b")
    if ocf is not None and not finite_number(ocf):
        financial_errors.append({"company": company["id"], "field": "ocf_b", "value": ocf})
    for key in ("share_price", "market_cap_b", "current_it_gw", "current_h100e_m"):
        value = stock.get(key)
        if value is not None and (not finite_number(value) or value < 0):
            financial_errors.append({"company": company["id"], "field": "stock." + key, "value": value})
check("investment-layer numeric fields are finite and constrained only where economically non-negative", not financial_errors, financial_errors)

result = {"passed": sum(row["pass_"] for row in CHECKS), "total": len(CHECKS), "checks": CHECKS}
(ROOT / "qa/integrity_results.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
if result["passed"] != result["total"]:
    raise SystemExit(1)
