# Source-aware layers and native infrastructure inspection

The [layer design contract](../design/map-layers-electricity.md) was committed
before implementation. This work fills the missing map-layer journey: independent
research, community-location, label, road, boundary and electricity controls;
source/vintage/coverage inspection; native feature selection; and retained camera,
shared state and phone selection.

The responsive Layers drawer uses the existing map toolbar and drawer behavior.
Toggles repaint the canvas and update its shared route. Hiding research markers
also removes their pointer and keyboard targets. Electricity starts disabled.
Fiber exposes the specific missing source rather than drawing speculative links.
The visible legend tracks enabled layers and distinguishes bounded coverage from
the absence of infrastructure. An explicit action frames the captured geography.

The [independent ODbL snapshot](../../data/layers/README.md) contains 38 native OSM
ways around Helios. Complete original geometry, tags and revision metadata remain
exportable; display paths are separately clipped. Amber lines and substation
outlines align with the georeferenced campus ground plane. The community snapshot
and historical image retain separate dates. This is local context, not a surveyed
utility plan or proof of campus service, ownership or capacity.

An actual line/area click and the accessible feature list select the same source
identity. The adjacent inspector leads with source-tagged kV, native attributes,
edit date, capture date and original source/history links. Selection preserves the
canvas/camera and can be shared, reloaded, inspected by topic or returned from a
source drawer. Phones show the same selected identity in both their compact
summary and expanded inspector. Disabling electricity restores project/roof
inspection; roof and phase selection remain separate journeys.

Visual review reserved a single phone toolbar row above the image date; the
short-desktop canvas also reserves space for the new attribution row so its
four metrics stay visible.

Cartographic labels now measure both the project name and quantity subtitle,
try four placements and avoid solid markers, controls, other project labels and
place labels. Source records remain available when a crowded map cannot label
every point.

Validation must cover both hosted and standalone publications, actual geometry
selection, keyboard list parity, licensed full-source export, independent toggles,
shared state, malformed input, missing coverage and unchanged collection totals.
Broad regression, exact-head live testing and manual desktop/tablet/phone visual
review precede merge; the actual deployed service is verified afterward. Results
are recorded on the implementation PR and local release receipt.

Open work includes official wider electricity and connection evidence, licensed
fiber routes, current campus imagery, a complete building inventory, reviewed
building/phase identity and research/catalog reconciliation. This partial pilot
does not close the overall six-reference implementation issue.
