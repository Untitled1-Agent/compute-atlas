# Map-linked research and mobile selection design

11 October 2026. Follow-up to the editorial experience design and PR #29.
This contract is written before the next implementation.

## Mobile inspection

At phone widths the map comes first. The selected project's summary sits directly
below it, before metrics and long topic content. The summary names the project or
cluster and its independently dated power scope. A 44-pixel minimum button expands
the full existing inspector in place. It is a disclosure, not a modal: the map remains
usable and the reading order stays map → selection → quantities → research.

A new map selection collapses the previous inspector, retains the camera, and puts
keyboard focus on the new summary. Expand/collapse retains selection and camera.
Escape collapses an expanded inspector and restores focus to its summary. Opening a
source still uses the existing evidence drawer and its return path. Desktop retains
the adjacent full rail. Mobile expansion is local UI state, not a shared preference.

## Map-linked record table

A disclosure below the main composition contains a table with three named scopes:

- Geographic scope: projects in the current world/system/market/corridor, after refinements.
- Visible map: that same collection restricted to anchors projected inside the current
  canvas. Globe points on the far hemisphere are excluded. Panning updates the table
  after settling without replacing the canvas or losing selection/focus.
- Selection: selected cluster members or the selected project, intersected with the
  same refinements. An excluded selection remains identified in the existing warning.

Show scope, matching count, sort, and previous/next page controls. Twelve records per
page keeps phones and keyboard navigation manageable. Sort by estimate descending
(unknown last), project name, or location. The quantity retains snapshot/target basis,
date and estimate status. Native-unit records remain named and show unquantified
rather than zero. Row selection updates the map rail at the same scale; entering a
campus is a separate action. Compare and a cited export use the same scoped collection.
The export covers all matches, not just one page. Unmapped dossiers remain available
through the facility directory; OSM locations never enter the research subtotal.

Changing scope, refinements or sort resets to the first page. Camera movement updates
visible records, clamps/reset pagination as needed, and leaves the selected project
intact. Hover alone must not trigger updates. A closed table incurs no repeated DOM
work. On phones the table scrolls within its own container, never the page.

## Shared exploration state

The current route already retains scale, selected project, inspection, phase,
company/country/text/evidence refinements, campus topic and phase claim. Extend it
with a validated camera, label/road context, geographic preset, selected cluster
members, campus evidence/location view, record scope/sort and disclosure state.

A Share view action exposes a selectable URL and uses clipboard where permitted,
with a text-field fallback. Private notes, research shelf and comparison storage are
excluded. Camera changes replace the current history entry after settling; explicit
scale, selection, refinement and topic changes retain normal navigation history.
Browser Back/Forward and reload reconstruct camera and overlays without overwriting
an incoming camera with the outgoing map. Invalid/non-finite/out-of-range parameters
fall back safely. Old links remain valid and reset omitted options to defaults.

## Acceptance

Verify both hosted and embedded standalone: a moved globe, a panned/zoomed regional
map, labels/roads off, a selected cluster, campus location view, reload, Back/Forward,
invalid URL, empty visible scope, pagination/sort/export, retained filtered selection,
and mobile expand/Escape/source return. Inspect 1440 desktop, 1366×768, tablet, 390
and 320 phone captures. Do not merge until live candidate testing and manual visual
review pass. Resource limits and Atlas-only cleanup remain in force.
