# Unified global atlas: implementation and visual review

The default landscape now uses all six source collections in one geographic
workspace. The previous landing covered only the 79 archived project dossiers.
The new opening view exposes 6,471 native records across 122 named countries and
territories, with 6,126 mapped positions and 4,394 native facility outlines.

The source collections retain every original row and field. Counts describe
source records, not a deduplicated global facility census. Project MW IT,
Epoch facility MW, GPU H100 equivalents, mapped geometry and operator listings
retain their own dates, meanings and identities.

## Six-scale review

These are captures of the production app, not an isolated design prototype.
The [approved references](../mockups/README.md) define the hierarchy. The capture
set reviews the dominant map, editorial rail, scale controls, source selection,
physical inspection and responsive layouts.

| State | Production capture |
| --- | --- |
| World | [Global atlas](review/unified-atlas/01-world.png) |
| Continent | [Europe](review/unified-atlas/02-continent.png) |
| Region | [Germany](review/unified-atlas/03-region.png) |
| Metro | [Frankfurt](review/unified-atlas/04-metro.png) |
| Campus | [New Carlisle imagery](review/unified-atlas/05-campus.png) |
| Facility | [Selected roof and source context](review/unified-atlas/06-facility.png) |
| Native 3D | [Frankfurt source outline and tagged height](review/unified-atlas/07-global-native-3d.png) |
| Phone | [390 × 844](review/unified-atlas/08-phone.png) |
| Short desktop | [1280 × 720](review/unified-atlas/09-short-desktop.png) |

[Capture routes and viewport receipts](review/unified-atlas/capture-notes.json)
retain the exact view parameters. The facility rail describes the selected
physical feature; project-level capacity appears as separate context. Native
heights and historical roof interpretations are not converted into inferred
power allocations or current operating status.

## Global physical data

The shipped context contains **244,002 unique OpenStreetMap objects**, captured
around **169 eligible published locations in 32 countries**, with zero failed
capture batches. All non-anonymous GPU rows with coordinates and all sufficiently
precise address geocodes are represented by those anchors. The complete global
GPU publication, including anonymous and unlocated rows, remains in the atlas.

The 49 compressed source chunks retain the exact Overpass response bytes,
including native IDs, tags, geometry, versions and edit timestamps. Their query,
OSM database date and both compressed and original-response SHA-256 values are
published in `data/layers/global-context-index.json`. Nearby features remain
independent context; proximity establishes neither campus membership nor service.

The 95 AI center records have explicit geocoding outcomes: 42 resolved address
or locality matches, 39 unmatched addresses and 14 records without an address.
These are separate provenance records, never replacement publisher coordinates.
Three existing licensed historical imagery components and nine reviewed roof
interpretations remain available with their image rights and observation dates.

## Workflows

Country, operator, source collection, evidence and text filters intersect. The
visible-map scope, paginated directory, selection, comparison and exports share
one state. Clicking a cluster first exposes its actual members; entering a scale
changes the camera explicitly. Unmapped selections are never replaced by an
arbitrary facility. Missing image IDs remain visible with a recovery action.

The eight inline topics cover overview, power, hardware, development timeline,
counterparties, investment, original evidence and private notes. Supporting
Epoch rows open over the atlas. Closing the evidence returns to the same map.
Comparison and public exports preserve units and omit private notes. Saved and
shared views retain camera, feature, filters, topic, timeline metric and comparison.

The hosted app loads context on demand and verifies its checksum. The standalone
embeds each compressed chunk separately so selecting one location does not parse
the entire global context archive. Optional street tiles require a connection;
the bundled geography, source records, imagery and context work offline.

The SQLite service serves only checksum-named context archives under the public
context directory. Publication fallback notices remain visible on the main
atlas, and source monitoring, research leads and original files remain reachable.

## Reproduce acquisition and publication

```sh
python tools/capture_atlas_locations.py
python tools/capture_atlas_context.py
python tools/package_atlas_context.py
python src/build.py
python -m pytest tests -q
python qa/unified-atlas.py
```

The geocoder respects its request interval and caches misses. Context acquisition
reuses complete cached responses and splits uncached work into bounded queries.
Incomplete capture sets cannot replace the accepted context package. Intermediate
raw responses remain under `work/`; the app ships compressed, verifiable sources.

Browser acceptance covers both shipped entrypoints and the real Python service.
The existing project, source review, archive, original-file, model, protected
service and research-shelf suites continue to cover their retained workflows.
Production hosting is a separate deployment; these captures establish repository,
service and offline behavior.
