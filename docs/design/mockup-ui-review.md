# Production UI rebuild against the six references

The previous global atlas delivered data and interactions but did not reproduce the approved visual composition. This rebuild replaces the production presentation: sidebar, typography, header, map proportions, cartography, analytical rail, metric edge and physical dossier. Both the hosted entrypoint and the offline download use it.

[Side-by-side visual review](mockup-ui-review.html) · [Capture routes and viewport receipts](review/mockup-ui/capture-notes.json) · [Reference definitions](../mockups/README.md)

| Reference | Production view | Delivered composition |
| --- | --- | --- |
| World | [World](review/mockup-ui/world.png) | Large relief globe, native source lights, three-part analysis rail, four scoped measurements |
| Continent | [North America–Europe](review/mockup-ui/atlantic.png) | Transatlantic camera and two-continent data scope |
| Region | [Midwest and East Coast](review/mockup-ui/region.png) | Reference roads, boundaries, cities and viewport-scoped records |
| Metro | [Chicago–New Carlisle](review/mockup-ui/metro.png) | Local corridor, selected campus, source-specific power and entry to physical evidence |
| Campus | [New Carlisle](review/mockup-ui/campus.png) | Historical imagery, independent outlines, dossier, phases, attributes and sources |
| Facility | [Helios roof](review/mockup-ui/facility.png) | Selected source feature, illuminated outline, native dimensions, versioned evidence and counterparties |

[Short desktop](review/mockup-ui/world-1280.png), [tablet](review/mockup-ui/world-768.png), [phone](review/mockup-ui/world-390.png), [tablet physical inspection](review/mockup-ui/facility-768.png) and [phone physical inspection](review/mockup-ui/facility-390.png) are also captured. Tablet maintains adjacent map and analysis. Phone places the dossier below the map with an expandable summary.

## Connected functionality

All six scales share filters, source selection, camera, comparison, exports and the research shelf. Refinements sit below the primary composition and are reachable from the map. Selected locations expose power, hardware, timeline, counterparties, investment, original evidence and private notes. Project power scopes are individually selectable without changing the physical camera or assigning project power to a roof. Claim drawers return focus to the originating control.

The guided journey traverses all six references and returns to the original exploration. Metric controls explain their units and underlying source population. Source inspection exposes image rights, observation dates, native object identity, versions and exports.

## Global data and geography

The full six captured publications remain: 6,471 native records across 122 named countries and territories, 6,126 mapped positions and 4,394 native facility outlines. Supporting rows, original workbook fields and attachments remain available. The global physical-context archive contains 244,002 native objects at 169 published locations in 32 countries, with separate geocode provenance.

Generalized geographic context now covers the whole world, including roads and places in South America, Africa, Asia and Oceania. A public-domain Natural Earth relief raster is supplied with source and output checksums, geographic bounds, license and reproducible capture code. Hosted and offline editions share the same raster and geometry.

The current global facility-power subtotal uses only Epoch's published current-power model. It does not add GPU estimates or project MW IT. Native records can overlap. The app does not imply a complete census of undisclosed facilities, and missing imagery, height or power remains unknown. Historical campus forms and quantities deliberately follow evidence rather than fictional reference numbers.

## Validation

The rebuild is covered by `qa/editorial-parity.py`: six compositions, adjacent inspectors, metric placement, transatlantic/metro scope, phase and source interactions, source-version saving, guided return, responsive layouts and offline operation. Screenshots are manually reviewed in addition to assertions. `qa/unified-atlas.py` covers the 88 primary global-data and physical-context checks. Two additional data tests verify worldwide reference geometry and byte-identical offline relief provenance.

The complete existing backend and browser workflows remain required in CI. Each merge is followed by a fresh review on the merged commit; a green test count alone is not a visual quality score.
