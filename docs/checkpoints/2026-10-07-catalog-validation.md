# Catalog foundation verified checkpoint

Base main: f4ab0c91613d9e6b69763b415f5dbb585420d3f8.
Read-only verification run 37540794529 passed 122 backend tests and all 461 existing application/data assertions, including actual HTTP hosted, standalone and SQLite-backed Chromium suites. Embedded functional/smoke modes are not described as HTTP. The new 3D/browser catalog interface is a separate next PR.

The tested normalized ODbL database has SHA-256 `108c7065110bfb775d7d6ba7e7b6a52ce6e23559e4b72bbf45d98a221d9ea670`. The deterministic source recovery ZIP is `fa3dc16383d6d938a48b8112b261efaf82d269a91b64360fe334d11a3a78a8b2`. It contains the identical sanitized capture and country polygons from source artifact 11377886172. The original artifact's outer ZIP hash differs by packaging, not source bytes.

Reviewed source bytes and data were published on the review branch in e004bf58f9e6c4bff3849ed5c95894ec4eaf5e50. Both temporary integration workflows and the readable transfer patch have been removed. Only the permanent read-only weekly candidate-capture workflow remains. A new permanent PR run must pass on this cleaned head before merge.

Coverage: 5,265 overlapping community map features, 1,908 in Europe, 115 named countries/territories. These are not a complete inventory of unique operating data centers. Four operator specifications corroborate identities and native-unit attributes without certifying polygons, heights or IT power. No archival research record or capacity quantity is changed.
