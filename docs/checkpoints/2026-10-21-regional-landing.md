# Regional landing analysis and physical entry

The World and Continent landing now implements the geographic analysis proposed
in [the landing design](../design/landing-regional-analysis.md). The right rail
compares geographic regions rather than repeating the three largest projects.
Every mapped research record belongs to one region through the existing
`spatialContinent` vocabulary. Only comparable finite target IT estimates enter
the subtotal; quantified and unquantified counts remain visible, including
unknown-only regions. Partial, mixed-vintage targets are neither live capacity
nor incremental additions.

Regional links create explicit `region` URL state and preserve refinements.
The selected scope survives sharing, camera changes, reload and Back/Forward.
Default regional cameras face the requested geography; explicit shared cameras
retain priority. Clearing the region or returning to World restores global
coverage. An empty filtered region stays empty instead of displaying unrelated
projects.

The final rail section previews an accepted historical source scene in the
current research scope and opens that exact scene and image version at Campus.
It displays the source observation date. If no scene exists in the scope, the
entry explicitly says imagery is unavailable and opens project evidence instead.
Historical roof interpretation does not establish current operations or a
roof-to-phase IT allocation. No source records, geometry or research quantities
were changed.

The metric strip spans map and rail on desktop. At tablet and phone widths it
follows the map before analysis; the desktop globe now frames the Atlantic with
the Americas inside the hemisphere. Campus and Facility keep their existing
physical inspection layout. Both generated entrypoints were rebuilt.

## Validation

`qa/landing.py` exercises both real HTTP entrypoints, raw target-total
reconstruction, unknown-only regions, keyboard drilldown, multi-country Europe,
refinement retention, explicit cameras, share links, reload, Back/Forward, empty
states, exact campus source identity and responsive reading order. It passed
54/54 checks, with screenshots at 1366, 1440, 1024, 768, 390 and 320 pixels.
The suite is registered in the existing CI workflow and summary.

Manual comparison used the original World and Campus references and actual
browser captures. The World metrics fit 1366×768 and 1440×900. Current source
images remain historical: Helios 2022 and New Carlisle 2025. Current licensed
imagery, complete physical inventories, reviewed roof/phase correspondence and
wider fiber coverage still require sourced research; mockup geometry and numbers
are not substitutes.

The backend suite passed 271 tests. Additional current-run checks passed:
archive integrity 15/15, workspace 71/71, HTTP hosted/standalone 27/27,
SQLite service 27/27, camera routes 24/24, startup/recovery 39/39,
six-scale explorer 127/127, responsive experience 56/56 and global labels 26/26.
JavaScript syntax and whitespace checks passed. Repeating the standalone build
reproduced both entrypoints byte-for-byte. This is local validation, not a claim
that the complete remote CI workflow has run.
