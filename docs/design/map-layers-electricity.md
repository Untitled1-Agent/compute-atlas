# Map layers and electricity context

Design contract, 11 October 2026. References 03–06 ask for physical context and
source-aware layer controls. The editorial layout and shared camera remain the
baseline. This contract precedes implementation of this workstream.

## Intended journey

An analyst opens Layers beside Refine and Share, sees which geography is actually
available, enables a context layer, selects a mapped feature, reads its native
attributes and source, and returns to the same camera and project. The layer is
useful without implying a campus service connection or contributing IT MW.

Layers opens the existing responsive side drawer from the map toolbar. This keeps
controls readable on phones and leaves the camera in place. Its rows show an on/off
control, source, date or vintage, coverage and a source-inspection action. Research
markers, community locations, labels and road context are independently controlled.
Electricity has bounded source coverage. Fiber has an explicit unavailable reason;
no decorative connection is drawn. Active layers remain visible in a concise
legend. Camera/selection are retained when toggling. Keyboard and phone controls
have the same behavior. The panel closes with Escape and restores focus. Layer changes update the shared
route while the panel is open; return retains those changes.

Cartographic text uses the measured bounds of both the project name and its native
quantity/subtitle. Try alternate anchor positions before dropping a label. Reserve
control, legend, other-label and solid-marker bounds. Selected identity gets first
priority; the accessible record list remains the complete naming surface when
the map lacks room. City labels use the same collision rectangles. Do not allocate
the name width alone and let longer quantities overprint nearby text or circles.

## Electricity pilot

Use the public OpenStreetMap response for the small Helios-area rectangle
[-100.90,33.75,-100.83,33.80], retrieved 11 October 2026. Keep only complete ways
tagged power=line, power=minor_line or power=substation, with their source object
identity, version, edit timestamp, native tags and geometry. The response includes
ways extending outside the requested rectangle; display geometry is clipped to
the capture rectangle and coverage never expands to those complete-way extents.
Original complete-way coordinates stay available in the source export; display
clipping is a cartographic boundary, not a new source object or surveyed endpoint.
Exclude power plants, towers and circuit relationships from this pilot. Do not
infer any connection or associate the tagged operator with the campus owner.

The endpoint response is a dated community snapshot. An edit timestamp is not a
survey date, image date, commissioning date or confirmation of present conditions.
The 2022 aerial remains separately dated, so newer OSM outlines cannot be presented
as objects captured by that historical image. Source inspection exposes this
mixed-vintage boundary and the native construction tags. Retain original voltage
strings; kV labels are an explicit conversion of the source's voltage tag, never
IT MW. Missing tags occupy their designed inspector fields with Not tagged.

Electricity starts off. A coverage action frames its bounded geography. Outside
the rectangle the layer says no snapshot coverage, not no infrastructure. At region
and metro scales, thin amber lines and restrained amber outlines provide context.
At the Helios aerial scale, aligned outlines sit on the georeferenced ground plane
and remain flat. The legend distinguishes their source date from the image date.

## Selection and evidence

A mapped line or outline click and an accessible feature-list button are equivalent.
Selection retains map/canvas/camera and updates the adjacent inspector. The inspector
leads with the exact OSM identity and native name/type, followed by voltage, source
edit date, snapshot date, source-tagged operator and construction status. Project
service, ownership, operational status and capacity are not established by these
tags or by proximity. Selection does not become a project, building or phase ID.

The source action opens original OSM object/history links and the complete cited
snapshot export. Export preserves geometry, native tags, source IDs, version,
snapshot/query/license and limitations. No private research notes are included.
Attribution © OpenStreetMap contributors links to the ODbL license, visibly on the
map whenever the layer is enabled. The normalized ODbL snapshot remains independently
exportable and cannot be folded into project capacity or the historical roof dataset.

## State and failure

Shared routes retain layer booleans and electricity selection independently of
project/phase/roof selection. Unknown layer names and feature IDs safely fall back;
malformed coordinates cannot enter the renderer. Source drawer return, topics,
Back/Forward and phone inspector expansion retain the camera. Layer toggles repaint
the canvas rather than reconstructing it. Disabling electricity clears only its
feature selection and restores the existing project/roof rail.

Source coverage and unavailable layers are explicit. No live external dependency
is added to browsing; hosted/offline entrypoints use identical pinned source data.

## Acceptance

Review the layer panel, actual line/outline selection, mixed-vintage aerial overlay,
source inspector and no-coverage state at desktop, tablet and 320/390 phones. Check
for control/label overlap against the approved references. Test both entrypoints:
toggle with retained canvas/camera, actual geometry click and keyboard list parity,
source return, export, share/reload/Back, bounds clipping, missing tags, malformed
state and unchanged project/OSM catalog totals. Only merge after exact-head live,
visual and broad CI gates; then verify the actual deployed service. Keep local
tests serial and capped and Atlas backups disabled.

## Remaining source work

This pilot is partial community context. Official utility interconnect/connection
evidence, fiber routes, wider licensed electricity coverage, current campus imagery,
complete building inventory and reviewed building-to-phase identity remain open.
