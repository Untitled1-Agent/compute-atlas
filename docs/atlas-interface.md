# The six-scale research atlas

The app opens on an evidence-first landscape, not a generic KPI dashboard.
The large globe and flat regional maps use real Natural Earth reference geography.
Every luminous facility marker belongs to the research archive; decorative land
stippling is not additional data. Roads are generalized roads, not utility/fiber
routes. The [approved visual references](mockups/README.md) guide the layout only.

## Exploration

World → Continent → Region → Metro → Campus → Facility. Click a visible marker,
use the scale strip, the +/- controls, or a deliberate wheel gesture. Drag/arrow
keys rotate or pan. Search, country, company and evidence filters apply to the
collection. Named selection and snapshot/target choice survive scale changes;
HTTP deep links and browser back/forward restore exploration state.

On the campus and facility screens, current sources support an **evidence
schematic**, not surveyed parcels or building footprints. No mockup geometry,
substation, transmission line, customer, or capacity number is treated as a fact.
An accessible record list supplies a keyboard alternative to the map.

## Two independent evidence layers

`data/atlas.json` preserves 79 historical project dossiers and their original
models. `data/evidence.json` adds reviewed issuer/regulatory disclosures without
rewriting that archive. Source date, status, measurement boundary and scope travel
with each observation. The reviewed regulatory sources include Helios construction
registration and emergency-generation technical review; neither is proof of live
IT utilization. The original eight research attachments remain byte-identical.

A primary disclosure is not telemetry. A modeled target is not delivered capacity.
A lease can include a delivered phase. An approved campus power envelope is not
critical IT load. Unknown values never become zero. Named-site sums are partial,
mixed-vintage model subtotals—not a global market census or company fleet total.

## Review and verification

`python src/build.py` regenerates the offline publication with all original
attachments. The hosted `index.html` loads local repository assets only. The
standalone HTML embeds all assets and makes no external requests.

Run `python qa/integrity.py`, `python qa/functional.py`, `python qa/smoke.py`,
`python qa/zoom-explorer.py`, and `python qa/live.py`. The last two run Chromium
against a real HTTP server. `qa/zoom-explorer.py --in-memory` is an explicitly
narrower mode for managed environments that block browser navigation; it is not
an HTTP pass. CI stores all six desktop scales and mobile screenshots as artifacts.
Compare those with `docs/mockups/`, not with an invented description of the app.
