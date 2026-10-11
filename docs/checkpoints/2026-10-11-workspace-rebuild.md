# Map-led workspace rebuild

The earlier experience pass (#26) fixed navigation defects but did not resolve the approved mockups' composition. The user's rejection was correct. Passing functional tests was not evidence of visual parity.

## Gaps and changes

| Gap against the six approved screenshots | Change |
| --- | --- |
| A location catalog opened instead of the compute/capital landscape | Fresh visits open the world capacity landscape; explicit catalog bookmarks still open Locations. |
| Stacked collection banners and large scale controls displaced the map | One compact toolbar carries the six scales and collection navigation. |
| Boxed analysis cards competed with a small globe | A dominant geographic canvas sits beside a borderless, three-section editorial rail. KPIs form a compact lower edge. |
| Sparse geographic context hid worldwide coverage | Existing OSM location points appear as a separately labeled context layer; no capacity or project identity is assigned to them. |
| Campus/facility looked like the same long report | Source-reported phase selection updates the facility rail and shareable URL. Topic navigation opens the relevant cited dossier section; full claims are progressively disclosed. |
| The geometry inspector sat below its canvas | Source geometry and its selected-record inspector now share one row. Context framing uses the displayed polygon bounds. |
| Dense map-label boxes obscured geography | Geographic labels use a text shadow instead of opaque rectangular backgrounds. |

## Unresolved visual and structural gaps

The campus mockups show aerial imagery, reviewed parcel/building outlines, and phase-to-building identities. The current researched Helios and New Carlisle dossiers do not establish those geometries. This release does **not** resolve that gap. Capacity evidence is an explicitly labeled interactive schematic. Real community polygons remain available in Locations, without inferring a link to a researched project.

The reference screenshots also imply a reconciled facility inventory and investment allocation. The 79 researched projects and 5,265 community records remain separate source collections; no reconciliation or new per-building financial data is asserted by this layout work.

## Acceptance

`qa/workspace.py` exercises both delivered entrypoints over HTTP: default navigation, all six scales, map dominance, selected-phase evidence, reload and browser Back, geographic-boundary disclosure, research access, source geometry framing, desktop KPI visibility and mobile overflow. Existing suites retain catalog behavior checks through explicit navigation. Full CI and live candidate testing are required before merge. Screenshots must be reviewed, including the remaining gaps above.

Shared-machine limits: one low-priority local browser at a time, full suites on GitHub. The user's disabled backup timer remains disabled. No other project's storage is in scope.
