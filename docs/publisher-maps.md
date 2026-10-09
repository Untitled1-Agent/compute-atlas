# Primary publisher maps

The operator-directory selector exposes two **separate source collections**, not a combined data-center count. Equinix codes retain proposed community-map matches. Digital Realty entries retain only their published map pins and direct official facility URLs. Source fields are not copied between the two publishers or into the archival capacity collection.

## Digital Realty

The 9 October 2026 accepted snapshot contains 261 publisher entries: 128 in the source EMEA group, 111 Americas and 22 APAC. The **Europe** shortcut uses the source's continent field and selects 111 entries, not all of EMEA. Country selectors explicitly filter raw publisher country headings, including `Not specified`. No surveyed jurisdiction is asserted by those labels.

Review notes flag the nine Dublin entries under the raw United Kingdom heading, two missing country headings, the source's Cile/Bogota labels, and compound location titles. HND10 has the compound source title HND10 + HND11 even though the published code is HND10; both fields remain intact. Notes are not automatic corrections. Search, filters, pagination and cited JSON export preserve the full publication denominator alongside the selected rows.

Every marker opens its original source record. Nearby OSM building-outline anchors within 250 m are offered only as **independent geographic cross-checks**; distance does not certify the same campus, operator or building. Clicking one opens its own source-outline 3D view. A publisher point with no outline is not turned into an invented building. Missing height remains an explicitly illustrative extrusion, which can be switched off.

## Navigation

Open Operator directory, then Digital Realty; or use `#publisher?region=Europe`. The map is draggable and wheel-zoomable. Fine wheel input is applied continuously rather than discarded. Plus/minus and Home provide keyboard alternatives. Facility 3D wheel zoom is anchored at the pointer even after rotation or shift-panning. Control-wheel is left for browser accessibility zoom. The original world/region/campus research navigation is unchanged.

## Service publication

The server loads `/api/operators/publication?publisher=digital-realty` independently of Equinix. Pending snapshots remain private. Reload explicitly loads the latest accepted snapshot; acceptance does not change an already-open research view. Invalid/unavailable API responses fall back visibly to the checked-in reviewed snapshot. Static/offline applications never claim a running source worker.

The weekly candidate capture and the ordinary source monitor remain review-only. The accepted source projection, parser, provenance receipt, schema and standalone build are committed, so normal offline rebuilding does not depend on expiring Actions artifacts. No cross-source summed capacity, new power disclosure or global operating census is established.
