"""Live HTTP/browser audit for Compute Atlas.

Unlike functional.py, this suite serves the repository over HTTP and exercises the
real hosted entrypoint, real same-origin asset fetches, hosted attachment downloads,
and the self-contained standalone artifact in Chromium.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
RESULTS = []


def check(name, ok, detail=None):
    item = {"test": name, "pass_": bool(ok), "detail": detail}
    RESULTS.append(item)
    print(("PASS " if ok else "FAIL ") + name, flush=True)
    if not ok and detail is not None:
        print("  " + str(detail), flush=True)


def finite(value):
    try:
        return value is not None and float(value) == float(value) and abs(float(value)) != float("inf")
    except (TypeError, ValueError):
        return False


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass


def launch(browser_type):
    explicit = os.environ.get("CHROMIUM_PATH")
    system = explicit or shutil.which("chromium") or shutil.which("chromium-browser")
    kwargs = {"headless": True, "args": ["--no-sandbox"]}
    if system:
        kwargs["executable_path"] = system
    return browser_type.launch(**kwargs)


server = ThreadingHTTPServer(
    ("127.0.0.1", 0), partial(QuietHandler, directory=str(ROOT))
)
threading.Thread(target=server.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{server.server_port}/"

with sync_playwright() as p:
    browser = launch(p.chromium)
    context = browser.new_context(accept_downloads=True, viewport={"width": 1536, "height": 1000})

    # --- Hosted/repository-native app ---
    page = context.new_page()
    hosted_errors = []
    hosted_requests = []
    hosted_bad_responses = []
    page.on("pageerror", lambda e: hosted_errors.append(str(e)))
    page.on("request", lambda r: hosted_requests.append(r.url))
    page.on(
        "response",
        lambda r: hosted_bad_responses.append((r.status, r.url)) if r.status >= 400 else None,
    )
    response = page.goto(base + "index.html", wait_until="networkidle")
    page.wait_for_function("document.documentElement.classList.contains('atlas-ready')")

    check("hosted index returns HTTP 200", response is not None and response.status == 200, response.status if response else None)
    check("hosted app reaches atlas-ready state", page.evaluate("document.documentElement.classList.contains('atlas-ready')"))
    check("hosted status correctly identifies repository data", "WEB · REPOSITORY DATA" in page.locator(".side-status").inner_text())
    check("hosted app has no boot error", page.locator(".boot-error").count() == 0)

    counts = page.evaluate("({sites:ATLAS.data.sites.length,companies:ATLAS.data.companies.length,sources:ATLAS.data.sources.length})")
    check("hosted dataset counts are 79 / 29 / 64", counts == {"sites": 79, "companies": 29, "sources": 64}, counts)
    check("hosted overview exposes four evidence lanes", page.locator(".evidence-lane").count() == 4)
    expected_issuers = page.evaluate("ATLAS.data.companies.filter(c=>c.commitment&&c.stock).length")
    check("capital dashboard row count is data-driven", page.locator(".investor-table tbody tr").count() == expected_issuers, expected_issuers)

    # Geographic concentration must navigate into the globe and preserve the selected country.
    first_geo = page.locator(".geo-row").first
    country = first_geo.get_attribute("data-id")
    first_geo.click()
    page.wait_for_timeout(120)
    state = page.evaluate("({view:ATLAS.state.view,country:ATLAS.state.filter.country})")
    check("geography drill-down routes to globe with country filter", state == {"view": "globe", "country": country}, state)
    check("globe canvas exists after geography drill-down", page.locator("#globe-canvas").count() == 1)

    # Every facility is checked against the enhancement's phase-ladder rules.
    facilities = page.evaluate("ATLAS.data.sites.map(s=>({id:s.id,name:s.name,snapshot:s.snapshot?.it_mw??null,target:s.target?.it_mw??null}))")
    phase_failures = []
    for site in facilities:
        page.evaluate("id=>ATLAS.openDrawer('site',id)", site["id"])
        expected_rows = int(finite(site["snapshot"])) + int(finite(site["target"]))
        actual_rows = page.locator(".phase-row").count()
        actual_cards = page.locator(".phase-card").count()
        expected_cards = 1 if expected_rows else 0
        if actual_rows != expected_rows or actual_cards != expected_cards:
            phase_failures.append({"site": site["name"], "expected_rows": expected_rows, "actual_rows": actual_rows, "cards": actual_cards})
    check("all facility phase ladders match comparable power fields", not phase_failures, phase_failures[:10])
    page.locator('[data-action="close-drawer"]').click()

    # Every company commitment record must omit undisclosed fields, not render them as zero rows.
    companies = page.evaluate("ATLAS.data.companies.map(c=>({id:c.id,name:c.name,commitment:c.commitment}))")
    capital_failures = []
    commitment_fields = ["capex_b", "uncommenced_leases_b", "purchase_or_contract_b", "rpo_b"]
    for company in companies:
        commitment = company["commitment"]
        if not commitment:
            continue
        expected_rows = sum(1 for key in commitment_fields if finite(commitment.get(key)))
        page.evaluate("id=>ATLAS.openDrawer('company',id)", company["id"])
        actual_rows = page.locator(".capital-row").count()
        if actual_rows != expected_rows:
            capital_failures.append({"company": company["name"], "expected_rows": expected_rows, "actual_rows": actual_rows})
    check("all company capital stacks omit undisclosed categories", not capital_failures, capital_failures)
    page.locator('[data-action="close-drawer"]').click()

    page.evaluate("ATLAS.navigate('companies')")
    card_text = page.locator("#content").inner_text()
    check("company cards no longer contain placeholder KPI labels", "Open dossier" not in card_text and "Footnotes" not in card_text)
    check("company cards expose KPI blocks for every company", page.locator(".company-card .company-kpis").count() == counts["companies"])

    # Hosted attachment path must serve the original bytes, not a broken or HTML response.
    page.evaluate("ATLAS.state.dataTab='files';ATLAS.navigate('data')")
    manifest = page.evaluate("ATLAS.data.manifest")
    with page.expect_download(timeout=10000) as info:
        page.locator('[data-action="original-file"]').first.click()
    download = info.value
    downloaded = Path(download.path())
    digest = hashlib.sha256(downloaded.read_bytes()).hexdigest()
    check("hosted original-file download matches manifest SHA-256", digest == manifest[0]["sha256"], {"file": download.suggested_filename, "sha256": digest})

    # Search and mobile layout over the actual HTTP entrypoint.
    page.locator(".search-trigger").click()
    page.locator("#global-search").fill("Helios")
    page.wait_for_timeout(200)
    check("hosted global search returns deep results", page.locator(".search-result").count() > 2)
    page.locator('[data-action="close-search"]').click()
    page.set_viewport_size({"width": 390, "height": 844})
    page.evaluate("ATLAS.navigate('overview')")
    check("hosted mobile overview has no page-wide horizontal overflow", page.evaluate("document.documentElement.scrollWidth<=innerWidth+1"))

    external = [u for u in hosted_requests if urlparse(u).hostname not in {"127.0.0.1", "localhost"}]
    check("hosted app makes no external network requests", not external, external)
    check("hosted app has no HTTP error responses", not hosted_bad_responses, hosted_bad_responses)
    check("hosted app has no uncaught JavaScript errors", not hosted_errors, hosted_errors)

    # Explicitly break the enhancement script; the user should get a visible boot error, not an exception.
    failed = context.new_page()
    failure_errors = []
    failed.on("pageerror", lambda e: failure_errors.append(str(e)))
    failed.route("**/src/enhancements.js", lambda route: route.abort())
    failed.goto(base + "index.html", wait_until="networkidle")
    failed.wait_for_selector(".boot-error")
    check("hosted asset failure renders visible error state", "Could not load src/enhancements.js" in failed.locator("#boot-error-message").inner_text())
    check("hosted asset failure does not throw uncaught page error", not failure_errors, failure_errors)
    failed.close()

    # --- Self-contained standalone app served over HTTP ---
    standalone = context.new_page()
    standalone_errors = []
    standalone_requests = []
    standalone.on("pageerror", lambda e: standalone_errors.append(str(e)))
    standalone.on("request", lambda r: standalone_requests.append(r.url))
    standalone_response = standalone.goto(base + "compute_atlas.html", wait_until="load", timeout=30000)
    standalone.wait_for_selector(".evidence-lane")
    check("standalone artifact returns HTTP 200", standalone_response is not None and standalone_response.status == 200)
    check("standalone artifact includes audited enhancement layer", standalone.locator(".evidence-lane").count() == 4 and standalone.locator(".investor-table").count() == 1)
    embedded_count = standalone.evaluate("Object.keys(JSON.parse(document.getElementById('original-files').textContent)).length")
    check("standalone artifact still embeds all eight original files", embedded_count == 8, embedded_count)
    external_standalone = [u for u in standalone_requests if urlparse(u).hostname not in {"127.0.0.1", "localhost"}]
    check("standalone artifact makes no external requests", not external_standalone, external_standalone)
    check("standalone artifact has no uncaught JavaScript errors", not standalone_errors, standalone_errors)
    check("standalone artifact is genuinely self-contained over HTTP", len(standalone_requests) == 1, standalone_requests)

    browser.close()

server.shutdown()

report = {
    "base_url": base,
    "passed": sum(x["pass_"] for x in RESULTS),
    "total": len(RESULTS),
    "checks": RESULTS,
}
(ROOT / "qa/live_results.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
if report["passed"] != report["total"]:
    raise SystemExit(1)
