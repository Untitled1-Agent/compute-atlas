# Geographic canvas: source geometry, framing and local roads

Design contract, 11 October 2026. The region/metro references require a readable
geographic system, not floating project points. This pass follows the independent
layer/inspection work and precedes its own implementation.

## Findings from the current implementation

The flat-map path renderer applies a globe-oriented screen-distance cutoff to
successive vertices. At close zoom, a real road segment can cross the viewport
while both endpoints lie outside it; the segment is silently broken. The native
electricity renderer similarly accepts paths only when a vertex is on screen,
missing crossing segments and enclosing polygons. Source geometry and screen
visibility must be separate decisions. Do not densify source geometry into new
survey measurements or infer endpoints at screen boundaries.

The general basemap is Natural Earth and remains generalized. Its road capture
was thinned to roughly two-kilometer spacing. That cannot establish campus access
roads. The existing small Helios-area OSM response also contains 36 highway ways;
this independent dated input can provide local road context without another bulk
capture. Preserve its IDs, edits, native tags and original coordinates under ODbL.

## Intended view

World/continent keep the quiet globe and sparse labels. Region/metro show continuous
reference roads and administrative geography, with clear source limits. The local
Helios capture adds thin, restrained community road lines behind native electricity
and research markers. The historical aerial remains independently dated; road
geometry is not presented as captured by that image. Road names appear only when
native tags supply them and readable placement is available.

An enabled Road context layer controls both generalized reference roads and this
explicitly bounded local detail. Layers shows both providers, dates, coverage and
independent source export. Outside the local snapshot, generalized roads remain
available; no worldwide street coverage is implied. Community attribution remains
visible when local roads are enabled, even if location/electricity layers are off.
No road line establishes public access, campus service or project ownership.

## Geometry behavior

Flat Mercator paths must retain legitimate crossing segments. Longitude wrap must
split at the dateline; the globe still splits at the horizon and rejects implausible
projected jumps. Canvas clipping is a display operation only. A native context path
is visible if a vertex is in frame, a segment intersects the frame, or its closed
area contains the frame. Visible crossing lines and enclosing areas remain
inspectable with their original source identity. Point selection and camera state
remain unchanged.

Source polygons retain native rings. A clipped unclosed source path cannot become
an invented filled polygon. Screen intersection checks must handle parallel, zero-
length and non-finite segments safely. Native exports retain full geometry; no
viewport clipping is written back to the source publication.

Mercator longitudes use the copy nearest the camera's center. A camera spanning
170–190° must connect 179° to −179° as a short crossing; a camera centered on 0°
must split that segment at its projection seam. Bounds culling uses the same copy.
Split/horizon/non-finite paths are never filled as invented closed areas.
Coverage copy distinguishes visible geometry, an overlapping capture with no
mapped feature in view, and a viewport outside the bounded capture.

## Versioned source assets

A release key must include pinned dataset content as well as CSS/JavaScript, so a
source-only update receives a fresh cache identity. Source inspection should use
readable UTC dates/times; exact capture timestamps remain in the cited export.
Review loading/error behavior when an older entrypoint meets a new release, rather
than accepting a mixture of cached source assets.

The hosted entrypoint pins both scripts/styles and source JSON with browser
integrity checks. A stale entrypoint encountering changed assets stops with a
readable recovery message and explicit Reload action; it does not silently combine
releases or retry forever. The standalone publication remains self-contained.
Road source inspection shows native names/references/access tags, object history,
capture/edit dates, original query/checksum/license and a complete cited export.
Timestamp display uses readable UTC; exact precision remains in exported data.

## Layout and acceptance

Preserve the editorial map/rail widths and four lower metrics. Short desktops
reserve attribution space. Canvas text avoids controls, quantities, markers and
neighbor labels; phone controls remain separate from source dates and captions.
Review Chicago–New Carlisle region/metro as well as Helios local/aerial/oblique,
plus world/Atlantic/Asia, desktop, 768/1024 tablet and 320/390 phone.

Validate real crossing roads and native lines with offscreen endpoints, enclosing
area selection, dateline/horizon behavior, independent layer/source export, camera
retention, malformed coordinates, both hosted/offline entrypoints and unchanged
research/catalog totals. Broad CI and exact-head live/manual visual gates precede
merge; actual deployment is verified afterward. Use one capped browser at a time
and keep Atlas-only cleanup, one active release and backups disabled.

Official utility/fiber coverage, current licensed imagery, complete buildings,
reviewed building-to-phase identities and inventory reconciliation remain open.
The retained offscreen project needs an explicit locate action in a subsequent
navigation design. Facility mode also needs a source-feature-first selection
design: a selected disclosed phase must not imply that a historical roof has that
phase's capacity. The operator's July 2026 image contains one long building and
equipment yards, not the four-building inventory in the visual reference.
