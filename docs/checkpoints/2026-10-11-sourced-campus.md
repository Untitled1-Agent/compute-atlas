# Dated campus imagery and historical source-feature inspection

The [campus design contract](../design/sourced-campus-scene.md) was committed before
implementation. This work replaces Helios's default evidence-only hero with an
actual georeferenced historical aerial, while retaining its independent phase
evidence view and inline research topics.

The image is a small, raster-locked USDA NAIP / USGS crop acquired 2022-09-05.
Its capture date, public-domain attribution, checksum and returned EPSG:3857 extent
are retained in [the scene manifest](../../data/campus/scenes.json). The original
long roof is manually interpreted from the crop. Pixel vertices and geographic
coordinates are retained; automated checks verify they agree with the returned
export extent. The requested crop bounds cannot substitute for that extent.

The project match was reviewed against TDLR/TCEQ name and address, EPA Galaxy
Helios and legacy Argo registry records, and Galaxy's July 2026 aerial exhibit.
The registry anchors and their reported precision remain visible in the source
drawer. Neither a geocoded address nor a coarse registry point is promoted to a
surveyed roof centroid. The operator figure is linked and was privately inspected;
its restricted image is not reproduced. USGS's [NAIP archive documentation](https://www.usgs.gov/centers/eros/science/usgs-eros-archive-aerial-photography-national-agriculture-imagery-program-naip)
identifies public-domain usage and the acquisition program.

Plan and oblique views project the same historic ground plane. No measured height
is available, so the roof is flat. Clicking it or the accessible feature button
retains the canvas/camera and changes the adjacent inspector, breadcrumb, scale
and shared link. Feature inspection has its own identity, date, source drawer
and cited export; it does not allocate campus MW to the roof. Selecting a disclosed
phase returns to the evidence diagram and its dated claim. Topics and source
return preserve selection/camera. Phones expand their compact selection after a
roof selection; view controls and attribution have reserved space.

Hosted pages fetch the immutable small image locally; the standalone publication
embeds it with checksum verification. Image decode failure retains the outline,
source and feature selection with a recovery message. Invalid camera/feature
parameters safely fall back. The interpreted feature is independent of OSM and
accepted research inventories. Original attachments, accepted claims and the
project/OSM counts remain unchanged.

Visual review corrected an initial phone overlap between the view switcher and
scale toolbar. Dedicated hosted/standalone journeys, source-asset tests, broad
regression, exact-head live testing and actual deployed visual verification are
required before merge/release. Results are recorded on the implementation PR.

This closes a historical imagery/feature-selection pilot, not current campus
parity. Current imagery, a complete building inventory, parcel boundaries,
reviewed building/phase links, other reference campuses, infrastructure and
inventory reconciliation remain open under issue #2.
