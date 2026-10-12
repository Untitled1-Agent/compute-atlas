# Make the opening atlas useful

12 October 2026. This refines the editorial layout selected in PR28, before implementation. The original world reference remains `docs/mockups/01-world-global.webp`. The public opening screen, rather than an opt-in campus layer, is the scope of this pass.

The [completed visual study](atlas-redesign-review.md) now shows all six scales, three structural alternatives, phone/tablet layouts and the proposed missing workflows. Its standalone clickable preview is kept on `prototype/atlas-redesign-review`, outside production. A is the recommendation; no user selection or implementation approval is inferred.

## Observed gap

The installed opening screen is still essentially the previous composition. Its globe fills nearly the whole map height, the four metrics sit only beneath the map, and the rail repeats a generic thesis, three projects and a company cloud. Recent campus improvements are hidden several interactions away. The reference has a balanced globe, meaningful geographic analysis and a full-width lower data edge.

## Layout and visual decision

Keep the existing editorial sidebar, serif headline and three-part rail. Frame the Atlantic with the Americas further inside the hemisphere, strengthen the source-derived land texture and luminous markers, and reserve breathing room around the globe. No random facility points, generated buildings or inferred connections.

For World and Continent, span the four metrics across the map and rail. Size the map against viewport height so all four values and labels fit at 1366×768 and 1440×900. Retain a useful minimum map size; compact heights can scroll. At tablet widths stack the rail below the map rather than leave an unusably narrow canvas. At phone widths retain the compact inspector and a two-by-two metric group. Campus dimensions stay independent.

## Three rail sections

1. **Compute is a physical asset class.** Show the filtered research count, country count and a labelled coverage strip separating comparable IT estimates from native/unknown records. Link to the methodology.
2. **Where capacity is being planned.** Rank geographic regions by their independently modelled target subtotal. Each row shows the comparable subtotal, number of quantified target records and unquantified records. Relative bars compare this partial research collection only. No growth percentage, live-capacity claim, incremental addition or full-market share. Unknown-only regions retain a named row. Changing a filter recomputes rows. Activating a row opens that exact geographic scope and preserves the active filters; Back/reload restore it.
3. **Go inside a campus.** Preview a real accepted historical scene for a project in the filtered scope. Display its imagery year and interpretation boundary. Open that exact scene at campus scale, with sources and roofs available. When no accepted imagery exists in the scope, show a named project entry with an explicit availability state instead of an unrelated image. Keep company context reachable from the primary navigation and selected project dossier.

## Measurement and navigation contracts

Only `spatialComparable(site, 'target')` contributes to regional target totals; null stays unknown. Each mapped research record belongs to exactly one region via the existing `spatialContinent` vocabulary. Regions with zero research records are not invented. The displayed total remains mixed-vintage and partial; scene imagery is independent of project estimates. Source data, publication, original research and inventory identities are unchanged.

Regional drilldown must use an explicit route scope, not a representative project's country as a substitute for the selected continent. Share, Back/Forward, full reload and filtered empty states must reproduce the region. A user-selected camera takes precedence over a new default framing. The campus preview uses the established scene navigation path and never bypasses scene validation.

## Review before publication

Compare World at 1366×768 and 1440×900 with the original reference, plus 1024/768px tablet and 390/320px phone. Verify metric visibility, map/rail reading order, native observations, marker and control overlap, regional sum reconstruction, unknown-only rows, filter changes, keyboard regional entry, exact scope after reload/Back, and exact preview scene identity. Exercise selection, layers and camera-route regression on the live read-only preview. Merge only after manual visual review and live checks; then verify installed/public assets and these same visible opening features.
