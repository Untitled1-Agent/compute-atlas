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

The [10 October project research review](docs/research/2026-10-10-project-dossiers.md)
investigates all 79 dossiers, adding 703 cited claims and growing the primary
layer to 230 sources. 68 projects have project-specific primary claims; wider
context and eight unresolved identities are marked separately. **Project
research** opens the searchable index and six-category dossiers, with reporting
dates, source locators, disagreements and open questions.

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

The PR/main CI runs the backend contracts, archival/hash integrity, application
interactions, six semantic scales, evidence and source history, identity,
worldwide geography, operator directories and source-polygon 3D. Every browser
suite publishes its assertion report and screenshots; actual HTTP checks cover
both hosted and standalone entrypoints, with separate SQLite service runs.
`qa/inspection.py` also verifies real CDP touch events, source geometry selection,
research lead exports and a Basic Auth proxy below `/compute/`.

```sh
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
python -m pytest tests -q
python src/build.py
python qa/inspection.py
python qa/project-research.py
```

The browser scripts use a system Chromium when available, otherwise the installed
Playwright Chromium. CI rebuilds the standalone and requires no diff, checks
JavaScript syntax, and runs every suite listed in `live-checks.yml`. Current
counts and tested revisions belong in the dated implementation checkpoints;
a historical result is not evidence of a new pass.

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

## Worldwide locations and facility 3D

The default landing now exposes the separate attributed geographic catalog: **5,265 community map features**, including **1,908 in Europe**, across **115 named countries/territories**. These include overlapping points, building outlines and campus areas, not a unique-facility or operating-capacity census. Country, region, feature-type and text filters, global search, source-specific exports and private notes are available. Switch to **Capacity research** for the preserved 79-project research collection.

Scroll the globe to magnify continuously, then into regional geography. Click an individual feature (or use the directory) for its **3D source-outline view**. Drag to orbit, Shift-drag to pan, pinch or scroll to zoom, or use arrow keys / plus / minus / Home. Shift-arrow keys pan. Click a visible sourced building or use the mapped-feature selector to inspect its geometry without moving the camera. Nearby features retain their own source identities, and the inspected record is shareable through the URL. Plan view, label and nearby-context controls are available. Only source-tagged buildings extrude. An unknown height is explicitly labeled illustrative, adjustable and removable; campus areas stay flat and point-only records never receive invented buildings. Operator storey counts are not converted into meters or power.

The Python service reads the accepted SQL catalog. Static/offline versions use the dated bundled publication and never pretend to run a worker. A service failure displays an explicit fallback warning. OSM-derived records retain ODbL attribution; the complete geographic catalog can be exported from its methodology panel. See [the implementation checkpoint](docs/checkpoints/2026-10-07-catalog-3d-explorer.md), [geographic catalog provenance](docs/checkpoints/2026-10-07-global-catalog.md), and the [six committed visual references](docs/mockups/README.md).

## Scoped research leads

**Research leads** opens searchable, cited candidates without adding them to mapped
sites or capacity totals. The October 2026 atNorth research links FIN05 in Salo,
DEN01 in Ballerup and NOR01 in Haugaland. Planned IT, gross-power, secured-power
and native campus/site-power disclosures keep separate scopes, sources and
states; unknown geography and operating IT load stay null. Source navigation
retains the query, and a cited JSON export preserves the original boundaries.
See the [primary-source research](docs/research/2026-10-09-additional-operator-sources.md).

The service supports a validated `--root-path /compute` for protected subpath
hosting. [Protected deployment and recovery](docs/protected-deployment.md) covers
the loopback service, TLS Basic Auth, persistent state and consistent daily
backups. A local proxy test does not certify a production deployment.
