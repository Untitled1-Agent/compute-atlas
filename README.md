# Compute Atlas

A standalone research app connecting AI infrastructure, facility-level evidence, contracting relationships, cost layers and investment questions — rendered as an interactive globe-plus-dossier experience.

Everything ships as one self-contained HTML file (`compute_atlas.html`, ~12 MiB): no account, no server, no API key, no internet connection required to use the app. Interface, data, globe geometry, report figures and eight original attachments are all embedded.

## The dataset

- **79 facility/project dossiers**, 75 approximate map anchors, 29 companies (11 Chinese), 64 source records
- **92 original facility-phase rows** (55 snapshot + 37 planned); multi-phase sites are joined, not double-counted
- Both original report versions preserved byte-for-byte (108 sections, 101 tables), both workbooks (23 worksheets, 5,938 cells), 8 original attachments with SHA-256 checksums

China coverage includes Alibaba, Tencent, Baidu, ByteDance, Huawei, China Mobile, China Telecom, China Unicom, GDS, VNET and SenseTime. Unknown is not zero — some companies have coverage cards but no defensibly quantified accelerator inventory.

## How to explore

Open `compute_atlas.html` in a modern desktop browser (phone-friendly too). Two routes in:

1. **The globe** — rotate, zoom, pick a facility. Markers scale by IT power, H100-equivalents, modeled cost, or equal size.
2. **An investment question** — follow the related companies, cost records, contracts and sources.

A five-stop guided tour connects New Carlisle, Helios, Zhangbei, Horinger and the interactive cost model — the point being the distinction between gross power, IT power, useful compute, asset ownership and economic value.

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
compute_atlas.html       Complete standalone delivery
src/index.html           App shell
src/styles.css           Responsive visual design
src/app.js               Routing, globe, charts, dossiers, search, scenarios
src/build.py             Portable, standard-library-only HTML bundler
src/build_data.py        Enrichment/correction transform
src/extract_sources.py   Optional report/workbook extraction
 data/atlas.json         App entities, evidence, corrections
 data/archive.json       Report extractions, workbook cells, models
 data/world.json         Bundled Natural Earth geometry
 data/manifest.json      File names, sizes, SHA-256 checksums
originals/               Eight unmodified attachments
qa/                      Browser tests, results, screenshots
```

Rebuild after editing:

```
python src/build.py
```

Python 3.10+, standard library only. The builder validates original-file hashes and embeds all assets. Neither build command fetches live market or facility data.

## Testing

Final functional suite: **40/40 checks passed** — all 199 entity/source detail records, every report section, all worksheets, globe interaction, China filtering, scatter selection, four-company comparison, scenario responses, tour navigation and mobile overflow checks. No uncaught JS errors, no external network requests during tests.

## Research shelf

Starred facilities and companies, personal notes and session export/import live in browser local storage. Nothing is sent to a server. Export the shelf for a portable copy.

## Attribution

Facility enrichment identifies Epoch AI and links exact site pages. Natural Earth supplies the bundled public-domain geographic context. Source publication rights remain with their respective publishers; inclusion in a research app is not a blanket license to redistribute third-party material independently.

## Repository status

- `docs/compute_atlas_guide.md` — the full delivery guide (what ships, how to use and rebuild it)
- App source (`src/`, `data/`, `originals/`, `qa/`, built HTML) — pending upload

## License

TBD