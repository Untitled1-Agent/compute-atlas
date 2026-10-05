# Compute Atlas

A source-cited, six-scale research atlas. Open `index.html` through a local HTTP server, or open the self-contained `compute_atlas.html` directly.

[Interface & evidence boundaries](docs/atlas-interface.md) · [Approved visual references](docs/mockups/README.md) · [Master implementation issue #2](https://github.com/Untitled1-Agent/compute-atlas/issues/2)

## Run the live evidence service

```sh
pip install -r requirements.txt
python -m server serve
# Open http://127.0.0.1:8000
```

The Python service adds a persistent SQLite ledger, a same-origin publication API,
full-text site search, and a robots-aware background source monitor. Captures and
RSS discoveries enter a review queue; they never silently replace accepted site
facts. `docker compose up --build -d` supplies a persistent-volume deployment.

[Service, review and backup guide](docs/evidence-service.md). The standalone remains
fully offline; it does not claim that background acquisition is running.

## Original research delivery

A standalone research app connecting AI infrastructure, facility-level evidence, contracting relationships, cost layers and investment questions — rendered as an interactive globe-plus-dossier experience.

Two entrypoints are included:

- **`index.html`** — the reviewable web-app entrypoint. It loads the checked-in structured data and source code directly, which makes iteration and GitHub Pages-style hosting straightforward.
- **`compute_atlas.html`** — the self-contained offline build. No account, server, API key, or internet connection is required; interface, data, globe geometry, report figures and eight original attachments are embedded.

The web entrypoint falls back to repository attachment links for original PDFs/XLSX/DOCX files; the standalone build retrieves those files from its embedded archive.

## The dataset

- **79 facility/project dossiers**, 75 approximate map anchors, 29 companies (11 Chinese), 64 source records
- **92 original facility-phase rows** (55 snapshot + 37 planned); multi-phase sites are joined, not double-counted
- Both original report versions preserved byte-for-byte (108 sections, 101 tables), both workbooks (23 worksheets, 5,938 cells), 8 original attachments with SHA-256 checksums

China coverage includes Alibaba, Tencent, Baidu, ByteDance, Huawei, China Mobile, China Telecom, China Unicom, GDS, VNET and SenseTime. Unknown is not zero — some companies have coverage cards but no defensibly quantified accelerator inventory.

## Six-scale spatial explorer

The globe view now behaves as a semantic research map rather than a simple camera zoom. It moves through **World → Continent → Region → Metro → Campus → Facility**, while preserving the selected site and Snapshot/Target evidence layer.

At each scale the app recomputes the visible research scope from the checked-in facility graph. Comparable power totals include only finite IT-MW values from reviewed or imported site estimates; native-unit disclosures and contract-only records remain visible without being forced into a false GW total.

The finest scale deliberately distinguishes sourced facility facts from physical geometry. When parcel/building boundaries are not present in the research package, the UI renders an **evidence schematic explicitly labeled as not a parcel/building survey** rather than inventing site plans from the design mockups.

## How to explore

Open `index.html` from a web server for the repository-native app, or open `compute_atlas.html` directly for the offline build. Two routes in:

1. **The globe** — rotate, zoom, pick a facility. Markers scale by IT power, H100-equivalents, modeled cost, or equal size.
2. **An investment question** — follow the related companies, cost records, contracts and sources.

The landing page now starts with explicit evidence lanes, a seven-issuer capital-intensity dashboard, geographic concentration of named snapshots, and a five-stop guided tour connecting New Carlisle, Helios, Zhangbei, Horinger and the interactive cost model. Facility dossiers include snapshot-to-target power ladders; company dossiers separate period capex, future obligations and RPO/backlog.

Press `/` or `Ctrl/Cmd + K` to search across facilities, companies, sources, contracts, cost benchmarks, report text and workbook cells.

## Reading the evidence — the caveats that matter

- **Not a complete inventory of global compute.** Named-site estimates do not establish full fleets, rentable capacity or utilization.
- **Reports and workbooks are archives, not certified disclosures.** Superseded conclusions are deliberately preserved; the correction register shows the revised interpretation.
- **Separate quantities stay separate.** IT load ≠ gross facility power ≠ accelerator TDP ≠ contracted critical power ≠ customer demand. Targets are not automatically signed, incremental or operational. Facility roles (developer, landlord, cloud operator, customer) are never summed.
- **H100-equivalents are a theoretical throughput convention**, not rented instances or a standardized token price.
- **Cost layers remain separate.** Modeled replacement value is neither procurement price, book value nor an equity-valuation floor.
- **Map coordinates are city/county/district/state-level anchors**, not surveyed building positions.
- **Market data are historical and unverified.** Investment sensitivities are analytical tools, not recommendations.

## Economics model

The cost lab annualizes equipment and facility capex separately via a capital-recovery factor:

```
CRF(r, n) = r / [1 - (1 + r)^(-n)]
CRF(0, n) = 1 / n
Annual capital charge = equipment capex × equipment CRF
                      + facility capex × facility CRF
Annual electricity ($B / IT-GW-year) = 8.76 × PUE × electricity ($/kWh)
Annual modeled cost = annual capital charge + electricity + other operating cost
Cost per productive H100e-hour = annual modeled cost / (H100e count × 8,760 × productive utilization)
```

Electricity is conservatively charged at full design IT load year-round, independent of utilization. The model omits taxes, working capital, salvage value, demand charges and accelerator-degradation curves. All defaults are editable hypothetical assumptions.

## Source package & rebuilding

```
index.html               Repository-native web entrypoint
compute_atlas.html       Generated standalone delivery (rebuild after source changes)
src/index.html           Offline build shell
src/styles.css           Responsive visual design
src/app.js               Routing, globe, charts, dossiers, search, scenarios
src/enhancements.js      Evidence lanes, capital dashboard, facility/company overlays
src/enhancements.css     Styling for the analytical enhancement layer
src/build.py             Portable, standard-library-only HTML bundler
src/build_data.py        Enrichment/correction transform
src/extract_sources.py   Optional report/workbook extraction
 data/atlas.json         App entities, evidence, corrections
 data/archive.json       Report extractions, workbook cells, models
 data/world.json         Bundled Natural Earth geometry
 data/manifest.json      File names, sizes, SHA-256 checksums
originals/               Eight unmodified attachments
qa/integrity.py          Static entity/reference/hash sanity checks
qa/functional.py         Deep in-browser functional coverage
qa/smoke.py              Fast authoritative route/interaction checks
qa/live.py               Real HTTP hosted + standalone Chromium audit
.github/workflows/live-checks.yml
                         PR/main CI for all QA layers and build synchronization
```

Rebuild after editing:

```
python src/build.py
```

Python 3.10+, standard library only. The builder validates original-file hashes and embeds all assets. Neither build command fetches live market or facility data.

`compute_atlas.html` is generated from the source tree. After changing `src/` or `data/`, run `python src/build.py` before publishing a refreshed standalone artifact; `index.html` always uses the checked-in source/data files directly.

## Testing

The PR/main CI runs four complementary layers, currently **105/105 explicit assertions passing**:

- **15/15 integrity checks** — unique entity IDs, valid company/source references, coordinate and IT-power sanity, archive coverage, source-manifest consistency, all eight checked-in original SHA-256 hashes, all eight embedded standalone-original hashes, and investment-field numeric sanity.
- **48/48 functional checks** — all 199 entity/source/cost/contract dossiers, every report section and workbook sheet, globe interaction, China filtering, scatter selection, four-company comparison, search, research shelf, formulas, economics scenarios, investment sensitivity, guided tour, mobile overflow, evidence lanes, company KPIs, facility phase ladders and hosted boot/failure behavior.
- **15/15 smoke checks** — all main routes, Asia globe fly-to, facility dossier completeness, cost sensitivity and mobile overflow. Smoke failures now fail the process rather than merely appearing in a JSON report.
- **27/27 live HTTP checks** — the repository-native `index.html` and generated `compute_atlas.html` are served over real HTTP in Chromium; checks cover HTTP status, same-origin asset loading, geography → globe drill-down, every facility phase ladder, every company capital stack, hosted original-file hash fidelity, search, mobile layout, explicit asset-failure UX, no external network dependencies, no HTTP errors and no uncaught browser exceptions.

CI additionally rebuilds `compute_atlas.html` and requires a zero diff, and runs JavaScript syntax checks on both core and enhancement code. The live job runs on pull requests and `main`; concurrency cancels stale runs instead of stacking duplicate QA jobs.

## Research shelf

Starred facilities and companies, personal notes and session export/import live in browser local storage. Nothing is sent to a server. Export the shelf for a portable copy.

## Attribution

Facility enrichment identifies Epoch AI and links exact site pages. Natural Earth supplies the bundled public-domain geographic context. Source publication rights remain with their respective publishers; inclusion in a research app is not a blanket license to redistribute third-party material independently.

## Repository status

**Private repository.** Current contents:

- `docs/compute_atlas_guide.md` — the full delivery guide (what ships, how to use and rebuild it)
- App source, full dataset, original attachments, QA files, and built `compute_atlas.html` — included

## License

Private repository — all rights reserved. No redistribution license granted.

## Source-backed identity and map precision

Facility attributes and full dossiers now open an **Identity & location** panel.
Six reviewed project identities are displayed beside, not substituted for,
unverified historical map pins. Distinct projects sharing one city anchor remain
separate; adjacency carries its own source. The cited JSON export matches the
read-only SQLite API. See the [source review](docs/research/2026-10-05-site-identities.md)
and [implementation checkpoint](docs/checkpoints/2026-10-05-site-identity.md).

The current primary layer has 35 factual attributes including these six identity
facts. This adds no capacity, mapped sites, or surveyed geometry. The original
archive and all existing observation rows are unchanged by this slice.
