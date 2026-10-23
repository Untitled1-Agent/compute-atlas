# Compute Atlas

A source-cited, six-scale research atlas. Open `index.html` through a local HTTP server, or open the self-contained `compute_atlas.html` directly.

[Interface & evidence boundaries](docs/atlas-interface.md) · [Approved visual references](docs/mockups/README.md) · [Master implementation issue #2](https://github.com/Untitled1-Agent/compute-atlas/issues/2)

[Rebuilt production UI: six-reference comparison and screenshots](docs/design/mockup-ui-review.md) · [Global data implementation](docs/design/unified-atlas-review.md)

## Start with the global atlas

The default landscape (`#atlas`) puts all **6,471 source records across 122 named
countries and territories** in one map: project research, OpenStreetMap,
Equinix, Digital Realty, Epoch GPU clusters and Epoch AI data centers. Native
records may overlap; these counts are not a unique-facility census.

The production interface now follows the six approved compositions: relief globe, transatlantic view, regional and metro maps, campus imagery and a selected physical-feature dossier.

Move through World, Continent, Region, Metro, Campus and Facility. Filter by
country, operator, source collection, evidence availability or search. Select a
record without moving the camera; inspect its power, hardware, timeline,
counterparties, sources and notes inline. Compare up to three source records,
export their original fields, or save/share the complete view.

The atlas includes 42 separately attributed address geocodes, native physical
context containing **244,002 features at 169 locations in 32 countries**, and the existing licensed
historical campus imagery. Source outlines and tagged heights remain independent
of project ownership and power estimates. Context is loaded in checksum-pinned
chunks on the hosted app and embedded in the offline edition. Optional street
tiles require a connection; the captured map does not.

The previous project landscape remains at `#overview` under More research tools.
The complete source directories, report/workbook archive, company research,
models, evidence service and research shelf remain available.

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

Refine this collection by country, archived operator association, research
outcome or project-claim topic. Search results include the matching disclosure,
scope and original citation; the URL preserves the chosen view. Dossiers offer
recent dated disclosures, topic shortcuts, claim search, a primary-source trail
and a development chronology ordered by reported/as-of date. Undated documents
remain explicit. Regional investment programs appear as wider context rather
than a single facility's financing. See the [navigation checkpoint](docs/checkpoints/2026-10-10-research-navigation.md).

The opening analysis rail groups comparable target IT models by region, preserving
quantified and unquantified counts. Select a region to open its exact research
scope; refinements, camera, reload and browser history remain shareable. These are
partial, mixed-vintage model subtotals, not live market capacity. A dated campus
preview opens the exact historical source scene; scopes without accepted imagery
retain an explicit availability state. `python qa/landing.py` checks both HTTP
entrypoints and desktop, tablet and phone layouts.

## Connected analyst workspace

The primary **Facility directory** searches all 6,471 source records together,
across six native collections, with separate collection counts, intersecting country/operator/evidence filters,
source geometry previews, original documents and cited exports. The original
79-project capacity table remains available under **Capacity archive**. Source
records can overlap; directory rows are not a deduplicated census.

**Contracts & connections** brings 178 commercial/financing records and archived
contracts into one filterable evidence view. Its company-to-project diagram uses
only explicitly disclosed roles. Company dossiers and investment views link to
project disclosures with their dates and source locators.

The economics lab and investment lens save working assumptions locally. Name
cases, compare up to three, share the exact inputs, and export calculations with
references. Research-session exports include saved models and working inputs.
Shared model links exclude case names and private notes. Zero discount rates use
the finite annuity limit; invalid inputs cannot replace a saved valid case.

Community points on the landscape now open their original source record without
moving the camera. The visible-record list provides the same keyboard access.
Nearby campus map records remain independent leads until identity is verified.

**Search research** provides paginated discovery across every location, company,
current and historical claim, source, contract, benchmark, report section,
workbook cell and original attachment. Search formulas as well as cached values;
open the exact cell, cited claim or native directory record. Result-type filters
and page state survive reload. Exports contain all matching records and source
references, with private notes excluded.

Source records from all three native catalogs can be saved to the **Research
shelf**, alongside projects, companies, private notes and model cases. **Save this
view** keeps a named search, directory filter, map/roof selection or model input
link. Reopen or rename views, remove bookmarks with Undo, and transfer everything
through a research-session export. Source bookmarks retain their original version
reference; changed and unavailable publications remain explicit.

The facility directory, connections and full research search also export **CSV**
for spreadsheet analysis. Exports include every filtered match, native source
identities and dates. Text that a spreadsheet could execute as a formula is
escaped; numeric values retain their numeric meaning. Public record exports
exclude private notes. JSON exports retain richer source metadata.

## Global GPU clusters and AI data-center buildout

The complete public Epoch AI GPU-cluster publication adds **482 records with all
57 source fields**, including 190 publisher-anonymized records and 30 superseded
phases. Filter by geography, owner, accelerator and source certainty; inspect the
published locations, compare up to three clusters, follow predecessor/successor
links, save source records and export every matching row.

The complete AI data-center publication adds **95 data centers, 567 timeline
observations, 239 chip deployments, 143 chillers, 527 cooling towers and 32
accelerator specifications**. Explore all six tables, switch timeline metrics,
follow source-linked parent records, compare centers and download the original
source ZIP byte-for-byte, including offline. All 1,603 rows are searchable.

**Global coverage** shows country and territory coverage across all six native
facility collections. Select a country/source cell to open its exact directory
scope, or export every source publication together. Original values, source dates,
licenses, confidence tags and unknowns are preserved. These are complete captured
publications, not a complete census of global compute. Epoch power estimates are
separate from the original critical-IT models; no identities are automatically
merged. See the [source review](docs/research/2026-10-22-global-publications.md).

## Six-scale spatial explorer

The globe view now behaves as a semantic research map rather than a simple camera zoom. It moves through **World → Continent → Region → Metro → Campus → Facility**, while preserving the selected site and Snapshot/Target evidence layer.

At each scale the app recomputes the visible research scope from the checked-in facility graph. Comparable power totals include only finite IT-MW values from reviewed or imported site estimates; native-unit disclosures and contract-only records remain visible without being forced into a false GW total.

The finest scale deliberately distinguishes sourced facility facts from physical geometry. When parcel/building boundaries are not present in the research package, the UI renders an **evidence schematic explicitly labeled as not a parcel/building survey** rather than inventing site plans from the design mockups.

Layers beside Refine controls research anchors, community locations, labels,
roads, boundaries and a bounded Helios-area electricity snapshot. Select an
actual mapped line/substation or its keyboard-accessible list entry to inspect
native voltage, tags, source revision and capture date without losing the camera.
Source export preserves complete original geometry and ODbL attribution;
display paths are separately clipped. The community snapshot and historic aerial
retain separate dates. No campus service or IT capacity is inferred. See the
[design](docs/design/map-layers-electricity.md),
[checkpoint](docs/checkpoints/2026-10-11-source-aware-layers.md) and
[source boundaries](data/layers/README.md).

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

The atlas includes a searchable browser for all 122 named countries and territories. Country views lead to local source groups and physical locations within that geography. Breadcrumbs return to the full country scope, and semantic zoom updates the map, heading and rail together. All 6,471 captured records remain available, including records without coordinates.

The [aerial context publication](data/maps/anchor-imagery/README.md) adds 79 source-dated US image windows alongside the three separately reviewed campus scenes. Native outlines and captured map context remain available globally. Imagery retains its acquisition date, original raster metadata, public-domain terms and checksum; it does not establish campus ownership or building capacity. The image library, original-image downloads and native physical bookmarks also work in the offline edition.

`compute_atlas.html` is generated from the source tree. After changing `src/` or `data/`, run `python src/build.py` before publishing a refreshed standalone artifact; `index.html` always uses the checked-in source/data files directly.

## Testing

The PR/main CI runs the backend contracts, archival/hash integrity, application
interactions, six semantic scales, evidence and source history, identity,
worldwide geography, operator directories and source-polygon 3D. Every browser
suite publishes its assertion report and screenshots; actual HTTP checks cover
both hosted and standalone entrypoints, with separate SQLite service runs.
`qa/inspection.py` also verifies real CDP touch events, source geometry selection,
research lead exports and a Basic Auth proxy below `/compute/`.
`qa/global-journeys.py` follows country-to-physical-source journeys on all six
inhabited continents, checks cross-continent refinements, native physical
bookmarks, exact image exports and source-version recovery in both editions.

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

Starred facilities and companies, personal notes and session export/import live in browser local storage. Nothing is sent to a server. Export the shelf for a portable copy. Imports retain mapped-location notes and notes whose original record is unavailable. If storage fails, the app identifies session-only work and provides an export recovery action.

The project comparison picker searches all research projects and compares up to three, retaining dates, native power boundaries, counterparties and expandable technical, development and financing claims. Cited comparison exports exclude private notes unless you opt in. The evidence desk compares exact claim revisions and exports both sources; source drawers provide copyable and downloadable citations. The five-stop tour returns to your starting exploration when finished or closed.

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

The Worldwide locations collection exposes the separate attributed geographic catalog: **5,301 community map features** (19 October 2026 capture), including **1,913 in Europe**, across **115 named countries/territories**. These include overlapping points, building outlines and campus areas, not a unique-facility or operating-capacity census. Country, region, feature-type and text filters, global search, source-specific exports and private notes are available. Switch to **Capacity research** for the preserved 79-project research collection.

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


The Campus/Facility journey now separates a physical source feature from project
phase evidence. Facility defaults to the one reviewed Helios roof; New Carlisle
provides a chooser for three positional roof interpretations in the licensed
2025 Edison / IEC-2 image. Selecting a phase opens Evidence; returning restores
the prior physical feature and camera. Source drawers, cited feature exports,
shared links and typed local shelf/session records retain the image version.
The compact overview uses four initial project attributes and four documents,
with accessible expanders for the rest. The Chicago–New Carlisle frame is distinct
from its 250 km nearby-project research context. Locate actions preserve original
archival coordinates and name the reviewed scene separately.

Geometry dates, later physical-identity reviews, native utility tags, transformer
capacity, project grid power and critical IT remain separate. The Indiana image
is dated to 2025, not an inferred exact day. Positional roofs do not inherit permit
building names, current operating status or MW. The separate SR2 / IEC-3 component,
current Helios imagery, full building inventory, reviewed phase/circuit links,
fiber geometry and collection reconciliation remain open. See
[physical-selection design](docs/design/campus-feature-selection.md) and the
[cited source decisions](docs/research/new-carlisle-campus.md).
