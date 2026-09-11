# Compute Atlas

A standalone research app connecting AI infrastructure, facility-level evidence, contracting relationships, cost layers and investment questions.

## Open the app

Open `compute_atlas.html` in a modern desktop browser. The globe is most immersive on a large screen; the interface also adapts to a phone. If a document preview displays source code or blocks scripts, save the HTML and open the saved file in a browser.

No account, server, installation, API key or internet connection is required to use the app. Its interface, data, globe geometry, report figures and eight original attachments are all embedded. External source links require a connection. This is a dated local collection, not a hosted product or a live market/availability feed.

The HTML is approximately 12 MiB because it contains the original research files, not just screenshots or excerpts.

## Start exploring

The opening page provides the main interpretive findings and two routes into the evidence. Rotate the globe and choose a facility, or start with an investment question and follow the related companies, cost records, contracts and sources.

The five-stop guided exploration connects New Carlisle, Helios, Zhangbei, Horinger and the interactive cost model. It demonstrates the important distinction between gross power, IT power, useful compute, asset ownership and economic value.

### Views and interactions

| View | What it provides |
|---|---|
| The landscape | High-level findings, a live interactive globe, coverage counts, a clearly labeled partial site footprint and investment-question links. |
| Globe explorer | Drag rotation, wheel zoom, keyboard navigation, regional flights, full-screen mode, marker labels, proximity clusters, company/country/evidence filters and snapshot/target selection. Markers can scale by IT power, H100-equivalents, modeled cost or equal size. |
| Facility directory | Sortable records, card and table views, a clickable power-versus-compute scatter chart, search, filtering and CSV export. Unlocated projects remain accessible. |
| Facility dossiers | Location accuracy, modeled operating and target phases, hardware where available, reported facts, timelines where available, roles in the ownership chain, cost scope, caveats, original report rows and source links. |
| Company universe | 29 company cards, role/region filters and a comparison tray supporting up to four companies. |
| Contracts & connections | A clickable relationship graph and all 11 original capacity programs. The graph is schematic, not a physical cable map or an additive flow of GW. |
| Costs & hardware | All 16 original cost benchmarks, five hardware-normalization records, per-company cost interpretations, original direct-cost evidence and an interactive economics lab. |
| Investment lens | Original financial obligations and historical market inputs with date/verification warnings; theses, risks and monitoring questions; a user-input project-NPV sensitivity. |
| Guided explorations | A five-stop narrative through the evidence and the economic model. |
| Full report library | Both complete report versions reflowed for reading, section navigation, text/table search, original embedded figures and exact PDF retrieval. |
| Data room & sources | All source records, correction register, both original workbooks, formula/value inspection for every populated cell, both complete original JSON models and the file-checksum manifest. |
| Research shelf | Starred facilities and companies, personal notes and session export/import. |

Use `/` or `Ctrl/Cmd + K` to search across facilities, companies, sources, contracts, cost benchmarks, report text and workbook cells. `Escape` closes a dialog. Facility and company cards link back to the globe and associated evidence. Detail routes use URL fragments, so a hosted copy can support shareable links to specific records.

Notes and stars use browser local storage when available. Some browsers restrict storage for local files; the app warns when persistence is unavailable. Export the research shelf to retain a portable copy. No notes are sent to a server.

## Coverage

The delivered dataset includes **79 facility/project dossiers**, **75 approximate map anchors**, **29 companies**, **11 Chinese companies**, **64 source records**, and **all 92 original facility-phase rows**. Those rows comprise 55 snapshot records and 37 planned records; multiple phases of a named site are joined rather than counted as separate physical facilities by default. Separate owner/developer records are not silently merged where identity or scope is uncertain.

Both original report versions remain accessible: 108 sections and 101 tables in total, including duplicated material across versions. Both workbooks provide 23 worksheets and 5,938 populated or formula-bearing cells. The app also embeds the eight original PDF, DOCX, XLSX and JSON files byte-for-byte, with SHA-256 checksums.

China coverage includes Alibaba, Tencent, Baidu, ByteDance, Huawei, China Mobile, China Telecom, China Unicom, GDS, VNET and SenseTime. Seven named Chinese facility records are included. Some companies have a coverage card but no defensibly quantified, mapped accelerator inventory. Unknown is not zero.

## Reading the evidence

This app is more granular than its headline visualizations. A large marker does not make a record more certain.

**This is not a complete inventory of globally available compute.** The original named-site estimates do not establish the full fleet of each company, the amount available to rent or its utilization. Snapshot records have mixed source vintages. The app build date is not the measurement date of every number.

**The original reports and workbooks are archives, not newly certified financial disclosures.** They are deliberately preserved without alteration, including superseded conclusions. The correction register and facility dossiers show the revised interpretation. The app does not claim to have regenerated corrected PDFs or spreadsheets.

**IT load, gross facility power, accelerator TDP, contracted critical power, customer demand and campus targets are separate quantities.** Targets are not automatically signed, incremental or operational. A facility can appear under its developer, landlord, cloud operator and customer. Do not add these roles together.

**Independent engineering estimates are labeled as models.** The reviewed Epoch site records are not operator-metered power or issuer-certified GPU inventories. Most original site records remain explicitly archival, not comprehensively re-verified. Source cards identify publication dates and review status; two enrichment records also disclose that only indexed excerpts could be reviewed.

**H100-equivalents are a theoretical throughput convention.** They are not rented H100 instances, identical model-training speed or a standardized token price. Precision, density, memory, interconnect, software and workload affect useful performance. Server-housing capacity, floor area and computing-power measures with unspecified precision are not converted into invented AI GW.

**Cost layers remain separate.** Facilities, hardware, leases and managed services are not interchangeable. Modeled replacement value is neither procurement price, book value nor a floor for equity valuation. Company-wide capex cannot be assigned entirely to AI without supporting evidence.

**Map coordinates are approximate anchors.** They are manually assigned city, county, district or state-level locations, not surveyed building positions. Four unresolved records remain off-map but searchable. Natural Earth country outlines provide illustrative geographic context, not an endorsement of disputed borders.

**Market data are historical and unverified.** Original 31 August 2026 prices and market capitalizations are shown as archive inputs, not live quotes. Project economics and investment sensitivities are analytical tools, not stock price targets or investment recommendations.

## Economics model

The cost lab separates equipment and facility capital, then annualizes each using a capital-recovery factor:

```
CRF(r, n) = r / [1 - (1 + r)^(-n)]
CRF(0, n) = 1 / n
Annual capital charge = equipment capex × equipment CRF
                      + facility capex × facility CRF
Annual electricity ($B / IT-GW-year) = 8.76 × PUE × electricity ($/kWh)
Annual modeled cost = annual capital charge + electricity + other operating cost
Cost per productive H100e-hour = annual modeled cost in dollars
                              / (H100e count × 8,760 × productive utilization)
```

Electricity is conservatively charged at full design IT load for the whole year, independently of productive utilization. The model omits taxes, working capital, salvage value, demand charges and a specific accelerator-degradation curve. Its capital-recovery rate is a scenario assumption, not a sourced company financing rate.

Defaults are editable hypothetical assumptions, including the historical $37.883B reference stack from the supplied report. The live annuity model uses explicit assumptions and is not intended to reproduce every historical TCO number in the archive.

The investment sensitivity computes project NPV from user-supplied GW, initial capex, annual free cash flow, project life and discount rate. Annual free cash flow is assumed to include maintenance and refresh requirements. No terminal value, growth or separate tax model is added. The percentage of assumed equity value is a sensitivity, not an estimated share-price return.

## Source package and rebuilding

```
compute_atlas.html       Complete standalone delivery
src/index.html           App shell
src/styles.css           Responsive visual design
src/app.js               Routing, globe, charts, dossiers, search and scenarios
src/build.py             Portable, standard-library-only HTML bundler
src/build_data.py        Enrichment/correction transform from the original model
src/extract_sources.py   Optional original report/workbook extraction
 data/atlas.json         App entities, evidence, original-row links and corrections
 data/archive.json       Both report extractions, workbook cells and original models
 data/world.json         Bundled Natural Earth geometry
 data/manifest.json      Original file names, sizes and SHA-256 checksums
 originals/              Eight unmodified supplied attachments
 qa/                     Browser tests, results and selected screenshots
```

To change presentation or edit the structured dataset, update the relevant files and run:

```
python src/build.py
```

Python 3.10 or later is sufficient for that build step; it uses only the standard library. The builder validates original-file hashes and embeds all assets into the new HTML. Run `python src/build_data.py` only when intentionally regenerating `data/atlas.json` from the enrichment transform; it overwrites manual edits to that JSON. Neither command fetches current market or facility data.

Optional source extraction requires `python-docx`; the distributed world geometry is reused. The historical fallback for rebuilding cartography also requires geospatial dependencies and a Natural Earth shapefile, so routine app builds should use the bundled `world.json`.

## Testing and limits

The final functional suite passed **40 of 40 checks**, including all 199 entity/source detail records, every report section, all worksheets, globe dragging and marker selection, China filtering, scatter selection, four-company comparison, scenario responses, session controls, tour navigation and mobile overflow checks. The original PDF downloaded from the app matched the attachment's SHA-256 checksum. A separate smoke suite passed 15 checks.

There were no uncaught JavaScript errors and no external network requests during those tests. Tests used the exact built HTML in managed Chromium through `set_content`, because that environment restricted file and localhost navigation. Native operating-system opening and all browser brands were not independently tested. Full-screen capability is browser-dependent. All interactive calculations and archive retrieval operate client-side.

## Attribution

Facility enrichment identifies Epoch AI and links the exact site pages in source cards. User-supplied reports, workbook values and embedded figures remain attributed through the original source ledgers. Natural Earth supplies the bundled public-domain geographic context. Source publication rights remain with their respective publishers; inclusion in a research app is not a blanket license to redistribute third-party material independently.
