# Independent context snapshots

`helios-power.json` is a normalized derivative of one bounded public
[OpenStreetMap API response](https://api.openstreetmap.org/api/0.6/map?bbox=-100.90,33.75,-100.83,33.80),
captured on 11 October 2026. It contains 33 complete power-line ways and five
substation-area ways. The manifest retains the response checksum, capture time,
source object IDs, revisions, edit dates, native tags, node references and complete
original coordinates. Editor account metadata is excluded.

The independent snapshot is licensed under **ODbL 1.0**, attributed to
© OpenStreetMap contributors. See [OpenStreetMap copyright](https://www.openstreetmap.org/copyright)
and the [OSMF attribution guidelines](https://osmfoundation.org/wiki/Attribution_Guidelines).
The app offers the entire cited derivative as an independent JSON export and
displays attribution when its community location or electricity layer is enabled.

The requested rectangle defines capture coverage. Complete ways returned by the
API can extend beyond it: `geometry` retains their native coordinates while
`display_paths` clips them to the capture bounds. Clipped endpoints are display
boundaries, not surveyed infrastructure endpoints. This collection is partial;
an empty viewport cannot establish the absence of infrastructure.

`tools/normalize_power_context.py INPUT.xml OUTPUT.json CAPTURE_TIMESTAMP` makes
the normalized derivative. It rejects incomplete selected ways, invalid geometry
and empty captures rather than silently erasing the snapshot.

The source [power=line](https://wiki.openstreetmap.org/wiki/Tag:power%3Dline)
and [power=substation](https://wiki.openstreetmap.org/wiki/Tag:power%3Dsubstation)
tags describe community mapping. Native voltage strings are retained verbatim;
the inspector converts volts to kV only for display. Object edit dates are not
survey dates, commissioning dates or confirmation of current operation. The
2022 campus aerial is independently dated. No service connection, campus owner,
building/phase identity, height or IT-capacity allocation is inferred from this
context. Research and geographic-catalog collections remain unchanged.
