# Independently sourced electricity for campus components

The current electricity layer covers Helios only. Edison and SR2 now have dated
physical scenes, but no electrical context. The native-source decision and exact
bounded acquisitions are recorded in `docs/research/new-carlisle-electricity.md`.
Implement the initial 25 native ways: 22 lines and three substation outlines.
The 42 underground cables and dense electrical points remain source inventory.

## Collection and source identity

Keep the existing Helios publication and raw-response hash unchanged. Add separate
Edison and SR2 ODbL derivatives, each binding its scene ID, WGS84 query bounds,
capture UTC, response SHA-256, exact query URL and immutable source XML. A native
feature retains full way geometry, ID/version/edit timestamp/tags, referenced
node IDs and their captured versions/timestamps/coordinates. Exclude editor
account metadata from the app/export derivative; retain the original capture.

The normalizer takes bounds explicitly through segment and path clipping. Never
change a global bound and assume a Python default argument follows it. Full native
coordinates remain complete; display clipping is a separate bounded derivative.
Publish only the separately reviewed core-way inventory. Validate exact IDs,
native versions, raw hash, completeness, closed substation rings and node versions.

Native type + ID + version is a source identity, not a new circuit. Preserve each
capture's membership and provenance; detect conflicting versions. Close parallel
paths, matching voltages and overlapping envelopes are not deduplication keys.

## Rendering and interaction

On a physical scene, render only its associated electrical collection, projected
with the same ground-plane registration as the image. Regional/geographic views
may show all separately attributable bounded collections in view. The layer stays
opt-in; selecting another component preserves its enabled state, clears the old
active utility identity and retains each component's prior roof/view/camera.

“Frame component context” shows the full returned aerial extent; it does not imply
complete utility coverage or change research-anchor coordinates. Utility paths
use the existing restrained ochre style. Roof hit surfaces retain priority where
geometries overlap; an accessible native list supplies equivalent selection.

The selected utility inspector shows native type/name/ID, source-tagged voltage,
mapping edit/capture dates and explicit unknown ownership/service/energization/IT
allocation. Semicolon voltage tags remain separate values. Substation area is not
capacity. Prior roof identity and physical camera remain available through Return
physical. No connector, operating status or building/phase link is inferred.

## Source, export, share and recovery

The layer panel names each collection, scope, independent capture and imagery
date, partial coverage and source/license. The source drawer exposes native way
and node versions, complete tags/path, raw acquisition checksum and ODbL derivative
export. Every export identifies the collection and selected source version.

A utility share binds collection ID, response hash and native feature ID/version,
alongside physical component/image/roof-return camera. Back/Forward and reload
restore that exact identity. A missing collection, wrong scene association, changed
capture or unknown feature gets a named recovery; it never silently reopens a
different current object. The recovery's original reason and requested identity
survive canonical URL rewrite/reload. An explicit action opens current context.

## Acceptance

Test disjoint non-default clipping bounds, crossing ways retained in full, exact
native way/node versions and tags, the 25 core inventory, no project/power record
changes, component-specific visibility, roof-first hit priority, keyboard list
parity, source/export/return, malformed/stale share recovery and browser history.
Manually review aerial/oblique, whole-context framing, actual source panels and
all six desktop/tablet/phone sizes. Merge only after exact-head live/manual and
remote gates; verify the installed tree, publication preservation and actual
deployment. Use one capped browser and one checkout; final releases stay singular.
