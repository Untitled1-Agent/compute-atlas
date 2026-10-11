# Map-linked research and mobile inspection

The [design contract](../design/map-records-mobile-state.md) preceded implementation.
This step addresses mobile selection, synchronized records and shareable exploration
state from the wider [experience design](../design/atlas-experience.md).

Research records now have geographic, visible-map and selection scopes with the same
refinements, a twelve-row table, date/basis, sort, pagination, retained selection,
comparison and an export of all matching cited dossiers. OSM locations remain separate;
unmapped research projects remain in the facility directory. A settled camera change
updates visible rows without replacing the canvas or changing hover into navigation.

Links retain the validated globe/Mercator camera, labels, road context, preset, cluster
members, campus location/evidence view, topic/claim, record scope/sort/page and disclosure.
Sharing has a selectable URL and clipboard fallback. Drawer return preserves the full
exploration route; reading a dossier no longer starts a locate animation behind it.
Private shelf, comparison and notes are absent from shared links and record exports.

Phone layout follows map → compact selection → research in actual document order.
Expand and Escape keep the selection/camera and restore focus. Source return retains
expansion. Desktop keeps the full adjacent rail. Long record tables scroll internally
on phones and fill the desktop width.

Manual visual review found and corrected a legacy two-column list style that clipped
the table and hid its actions/pager. Acceptance now checks full desktop width and the
pager's placement after all rows, in addition to reviewing actual captures.

`qa/exploration.py` covers both hosted and embedded entrypoints. Broad regression runs
on remote CI; local live-candidate/deployed tests use serial resource-capped browsers.
Exact-head live/visual gates and their results are recorded on the implementation PR.

This is interaction progress, not completed campus imagery. Reviewed geographic
identities, dated aerial imagery, building/phase links, infrastructure context and
inventory reconciliation remain open. The mockup's illustrative capacities/building
names are not imported as evidence.
