# Sourced campus spatial view

Design contract, 11 October 2026. This work closes part of the campus/facility
spatial gap in approved references 05 and 06. The contract precedes implementation.
The first pilot is Helios; coverage is explicitly one historical roof, not a
complete campus building inventory.

## Screen and interaction

Campus opens with a real aerial hero, with date and attribution permanently
visible. Plan and oblique views share the same georeferenced image and interpreted
roof outline. Oblique viewing changes the camera, not the captured scene. Roofs
remain flat because no measured height has been established. Missing imagery at
other projects retains the existing evidence/location fallback.

The campus header and research topics stay in place. An accessible feature button
is equivalent to clicking the outline. Selection changes the adjacent inspector,
breadcrumb and URL without replacing the canvas or resetting its camera. A phone
selection expands the compact inspector. Escape/source return follows the existing
workspace behavior. Selected-feature export contains the geometry, image date,
interpretation method and original source references; it excludes private notes,
invented heights and project-level power allocation.

The spatial inspector leads with the selected feature's identity, capture date and
geometry basis. It says “IT allocation not established” rather than displaying
campus MW as a building quantity. The next section links the parent project and
its separately dated phase disclosures. Phase buttons switch to the interactive
evidence diagram and select a claim; no visual building-to-phase identity is
asserted. Aerial/plan and evidence modes remain separate, shareable selections.

Pan, zoom, orbit, reset, plan/oblique mode, selected feature and source return are
retained across topics and shared links. Validate finite bounds before restoring
scene camera values. Continuous movement replaces history after settling; explicit
view/feature changes create history entries. Source inspection does not move the
scene. Failure to decode imagery leaves the outline usable with a recovery message.

## Source and identity review

The image is USDA NAIP, served by the USGS National Map, raster
`m_3310010_sw_14_060_20220905`, OBJECTID 190775, acquired 2022-09-05 at 0.6 m
native resolution. The small 1200 × 1000 crop is locked to that raster, rendered
NaturalColor, and retains the export service's returned EPSG:3857 extent. The
export adjusts the requested bounds to the output aspect; digitization must use
the returned extent, not the request rectangle. NAIP is public domain. Store the
exact crop hash, metadata/query parameters and USGS attribution. Embed the small
asset in the offline publication; do not create a live tile dependency.

The match is an Atlas interpretation reviewed against these primary sources:

- TDLR Helios Light Speed registration, TABS2025012175, 984 County Road 112,
  Afton, Dickens County. Its original postal code is retained independently.
- TCEQ registration RN111537775 / permit 179090 and public application address.
- EPA FRS Galaxy Helios 110071953658 has the same name/address. Its geocoded
  coordinate is an address anchor, not the roof centroid. EPA's legacy Argo Data
  Center 110071142021 lies near the historical building but has very coarse
  recorded accuracy. Neither registry point is promoted to surveyed geometry.
- Galaxy's July 2026 campus aerial in its Q2 2026 exhibit corroborates the long
  original building, flanking electrical equipment, access pattern and nearby
  substation. Link the original exhibit; its restricted image is not reproduced.

The roof polygon is manually interpreted from the white roof visible in the
2022 NAIP crop. The interpretation is dated and explicitly approximate. It is
neither a parcel nor a certified building footprint. No phase ID, operating
status, height, present-day completeness or building IT power is inferred.
2022 imagery predates the AI conversion. Current dated claims remain in the
accepted evidence ledger and must not be overwritten by this display layer.

## Data boundary

A small independently versioned campus scene manifest links one research project
to one reviewed historical feature and one licensed image. It is separate from
the OSM and operator directories. Feature IDs do not impersonate OSM objects.
The 79-project capacity inventory and 5,265 community-map records are unchanged;
the image-derived feature never becomes another capacity-bearing facility.

Store image bytes/hash/extent/date/raster ID, geometry/derivation/date, primary
identity references, review result and limitations. Source/detail drawer makes
these fields accessible. Export retains the same boundaries. Source licensing
and identity review are recorded in the repository before publishing the feature.

## Acceptance before merge

Review campus plan, oblique and selected-roof screens next to the approved
references at equal desktop viewports; also inspect short desktop and 320/390
phones. Require visible image date, readable selection, controls clear of labels,
and useful adjacent inspection. A functional test total alone is insufficient.

Through hosted and standalone entrypoints, test actual image decode, georeferenced
outline alignment, mouse/keyboard/list selection, retained canvas/camera, topic
and source return, share/reload/Back, invalid camera fallback, phase versus roof
selection, cited export and unavailable-image fallback. Run broad regression on
remote CI, serial local live tests within existing VPS caps, then actual deployed
acceptance. Preserve original attachments and accepted publication hash. Keep
Atlas backups disabled and remove the prior release only after acceptance.

## Still open after the pilot

Current licensed imagery, additional building inventory, reviewed building/phase
relationships, campus parcel boundaries, other reference campuses, infrastructure
connections and inventory reconciliation. A historical roof pilot does not close
issue #2 or establish full mockup parity.
