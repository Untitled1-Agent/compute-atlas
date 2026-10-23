# Compute Atlas — six-reference visual comparison

The production atlas follows the six supplied compositions. The current review compares actual **1280 × 960** browser captures with the **640 × 480** reference copies at the same 4:3 aspect ratio. The hosted app and the downloadable standalone share the implementation.

[Side-by-side comparison and adjustable overlays](mockup-ui-review.html) · [Capture routes and viewport receipts](review/mockup-ui/capture-notes.json) · [Approved references](../mockups/README.md)

| Reference | Production capture | Composition |
| --- | --- | --- |
| World | [World](review/mockup-ui/world.png) | Dark relief globe, atmospheric edge, sparse luminous hubs, three editorial sections, four scoped measurements |
| Continent | [North America–Europe](review/mockup-ui/atlantic.png) | Transatlantic framing, regional analysis, country ranking and complete two-continent source scope |
| Region | [Midwest and East Coast](review/mockup-ui/region.png) | Restrained roads and source lights, Northern Virginia focus, bounded market drill-down and operator links |
| Metro | [Chicago–New Carlisle](review/mockup-ui/metro.png) | Local corridor, compact selected-campus dossier, dated power scopes, cited development evidence and disclosed relationships |
| Campus | [New Carlisle](review/mockup-ui/campus.png) | Historical imagery, mint reviewed roof outlines, evidence and takeaways beneath the map, power ladder and editable private notes alongside |
| Facility | [Helios](review/mockup-ui/facility.png) | Selected physical feature, adjacent evidence inspector and counterparties, four lower panels for power, attributes, sources and takeaways |

[Short desktop](review/mockup-ui/world-1280.png) · [Tablet](review/mockup-ui/world-768.png) · [Phone](review/mockup-ui/world-390.png) · [Tablet physical inspection](review/mockup-ui/facility-768.png) · [Phone physical inspection](review/mockup-ui/facility-390.png)

## What changed in the fidelity pass

The sidebar, content inset and analysis-rail widths now follow the reference proportions. The same navigation shell continues through the directory, company, contract, investment, library and data-room pages. Economics, guided exploration and original sources are directly accessible. Guided exploration restores the original research page when launched outside the map.

Cartography uses a dark blue relief treatment, a soft atmospheric edge and a limited set of prominent green hubs. Smaller source locations remain lights; large halos are no longer painted around every group. Nearby lights share display pixels without removing records from inspection, filtering or export. The underlying geography and source membership remain unchanged. Hit detection follows both the visible source lights and their grouped hubs, so a light away from the hub center still opens its source members without moving the camera.

The regional screen has a distinct market-focus rail and a working Northern Virginia drill-down. Regional and metro measurements sit beneath their map, beside the analytical rail. World and continent measurements span the composition. All first-screen measurements and rail content fit the reference-ratio viewport.

Campus and facility now have different lower structures. Physical source selection sits on the map. Campus prioritizes original sources and takeaways below the hero, with a compact dossier, power ladder and editable private notes in the rail. Facility exposes all four lower evidence panels in the first reference-ratio viewport. Roof outlines use mint emphasis; separately sourced electricity context uses a quieter violet treatment.

## Connected functionality and global data

All six scales share filtering, source selection, camera state, comparison, exports and the research shelf. Topics retain the map while exposing power, hardware, timeline, counterparties, investment, sources and private notes. Feature and phase identities remain independent. Saved physical evidence returns to the rebuilt atlas through shelf reopening and session export/import. Shared views pin source versions; unavailable versions require explicit recovery.

The [worldwide exploration review](global-exploration-review.md) extends those journeys through every inhabited continent. A searchable country browser, local source groups and geographic breadcrumbs keep the user in the selected scope. Native physical features also save as portable, version-pinned research views. An additional 79 dated NAIP image windows, their native raster metadata and exact image downloads are available in both editions. These geographic captures retain their own dates and do not replace separately reviewed campus evidence.

All six captured publications remain: **6,471 native records across 122 named countries and territories**, **6,126 mapped positions**, and **4,394 native facility outlines**. Complete native fields, supporting rows, original reports, workbooks and eight attachments remain available. The global physical-context archive contains **244,002 native objects at 169 locations in 32 countries**, with separate geocode provenance. Worldwide Natural Earth reference geography and licensed relief are embedded in the offline edition.

Source records can overlap. These publications are not a census of every undisclosed facility. Current facility-power subtotals use only Epoch's current-power model; project IT models, GPU estimates and infrastructure tags remain separate. Real source dates, roof geometry, location names and quantities replace the mockups' illustrative content. Unreported heights, capacities and building-to-phase assignments remain unknown.

## Validation

`qa/editorial-parity.py` checks both entrypoints, the six reference-ratio compositions, complete lower evidence panels, visible measurements and rails, bounded market navigation, inline note saving, guided return from research pages, source-version recovery, actual session export/import, independent phase and feature identities, original source exports and responsive layouts down to 320 pixels. The original reports are checked section by section for viewport overflow. Screenshots are visually reviewed separately from assertions.

`qa/unified-atlas.py` covers the primary global-data, camera, source-selection and physical-context journeys. Existing backend, source integrity, research-workspace, campus, native file, service and delivery suites remain required in CI. Each merge is followed by verification of the actual merged tree and rebuilt download. A passing test count is not a claim of pixel identity between real evidence and illustrative reference content.
