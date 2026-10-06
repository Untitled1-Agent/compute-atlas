# Global catalog foundation — 7 October 2026

Base: main `f4ab0c91613d9e6b69763b415f5dbb585420d3f8` (six reference images committed in PR #15).

Source capture: Actions run 37385525742 / artifact 11377886172, SHA-256
`a401b83b3c050172854373055ff0fdb844dd6823ad936ddbcb78de3a6f75b37f`.
Captured 2026-10-05T22:57:10Z, OSM base 22:54:06Z. 5,265 map features,
1,908 classified in Europe, 115 named countries/territories and 45 country-unknown
features. These are NOT deduplicated facilities or operating-capacity statistics.

Added deterministic normalization, fixed-endpoint bounded weekly captures,
separately licensed/attributed ODbL publication, immutable SQLite snapshot staging,
review decisions with a current-head lease, indexed paginated geographic search,
and read-only catalog APIs. Operator reviews for PA9x, FR5, AM3 and LD8 retain
kVA/m²/storeys in their reported units; their pages join the background source
monitor without entering the historical research/capacity publication. Changed
pages and OSM captures do not automatically replace accepted research.

Next slice: integrate the catalog in the map/search and ship an orbitable 3D
facility view, continuous wheel navigation, desktop/mobile screenshot review.
Keep 79 archival sites separate. Do not manufacture a power total, merge colocated
features by proximity, extrude campus land as a building, or call a default display
height measured. Main/PR HTTP validation is required; this local Chromium session
blocks HTTP navigation. The original research, six references, and all byte-hashed
originals must remain intact.
