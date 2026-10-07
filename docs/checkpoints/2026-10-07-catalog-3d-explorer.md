# Worldwide explorer and source-outline 3D checkpoint

Base main: `b0d9bf08035fa7d8b118840f8d1b6b8d19143d54` (PR #16), tree `969d3c014b21dea7bcf3f869c6464055bd86573c`.

## Implemented

The global catalog is now a first-class landing page and search/directory collection. Region/country/feature-type/query filters reach all 5,265 captured map records, including 1,908 in Europe. They are explicitly overlapping community features, not a complete census of unique operating facilities. The separate 79-project capacity archive and all original attachments are unchanged. Four previously reviewed operator specifications remain independent corroboration of identity and native-unit attributes.

The facility view uses the selected source polygon as a true three-dimensional camera scene with orbit, pan, wheel, keyboard, plan view and optional nearby source context. Only building features extrude. Missing heights use an explicitly labeled adjustable display height, can be disabled, and are never exported as facts. Points have no manufactured footprints; campus/industrial areas stay flat. Tagged heights are labeled OSM community data, never surveyed measurements. No synthetic satellite imagery, fictional buildings, or utility geometry is introduced.

Globe and regional wheel interactions are continuous, normalize pixel/line/page deltas, preserve the canvas and anchor regional zoom to the cursor. The original six-scale capacity map also gains continuous wheel magnification between semantic transitions. Browser accessibility zoom is not captured.

Hosted, offline and database modes share the UI. The service loads the accepted SQL catalog; malformed/unavailable publication falls back visibly to the dated checked-in snapshot. Source-specific exports, private local notes, hash deep links and global search are integrated. ODbL attribution and full catalog export remain visible.

## Validation at source handoff

Local results: 122 backend tests, 15 archive integrity assertions, 48 functional assertions, 59 embedded six-scale assertions, 28 embedded global-coverage assertions and 35 embedded catalog/3D assertions pass. Local Chromium blocks HTTP navigation; embedded results are NOT HTTP validation. Permanent GitHub Actions additionally runs hosted, offline and SQL-backed Chromium over actual HTTP, including the new catalog suite. Its result must be inspected before merge and recorded in the PR / issue #2.

Screenshots at desktop, 390px and 320px have been exercised. Screenshot review caught blocked Plan/3D buttons and excessive nearby geometry; the controls now receive pointer events and nearby context is opt-in. All six approved visual references are already committed under `docs/mockups/` (PR #15), independently protected by manifest checks.

The inherited post-merge CI failure was a premature hosted bootstrap assertion. Tests now wait for the final application module and explicitly select the archival view for archival expectations, rather than testing mid-boot or confusing geography with capacity research. No research assertions were removed.

## Resume / limitations

Use `python -m server serve` for persistent SQLite and the registered source worker. Weekly catalog acquisition creates candidate snapshots only; it does not silently publish new mapping or certify operator facts. No public deployment is created by this change.

Next research work: broader independently sourced operator directories and facility identity matching, explicit overlap resolution, current status/capacity review, and more primary facility attributes. Do not claim this OSM catalog reaches all data centers or infer missing capacity from floor area/kVA/footprints. Unknown is not zero.
