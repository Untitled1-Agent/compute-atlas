# Digital Realty global location directory — 9 October 2026

Primary source: https://www.digitalrealty.com/data-centers

The independently retrieved public HTML (2026-10-09T20:32:16.770273+00:00) contains a public `__NEXT_DATA__` facilities array with **261 location entries**. The separate metros array has 60 entries and is never used as facility coordinates. Source SHA-256: `83b181224e4d8259d7ebbf44fd0b402a063480d9dbb36453ca134f3cd309bee5`. Read-only capture run: 37987628566. The receipt in `data/catalog/digital-realty-review.json` pins the capture artifact and the exact derived publication.

## What is supported

The captured facility entries contain publisher node IDs, titles/codes, facility URLs, latitude/longitude pairs, localities and regional/country grouping. There are 128 EMEA, 111 Americas and 22 APAC entries. All 261 have publisher map pins. These are not surveyed building coordinates. A published location entry can cover multiple buildings: `JB1+JB3` and `HND10 + HND11` are retained as single entries, not expanded into fabricated individual records. Original source titles are retained separately from trimmed display names.

## Source inconsistencies, not silent corrections

Nine Dublin entries are assigned to the source country group `United Kingdom`; two Kuala Lumpur entries have null country headings. The source also uses `Cile` and `Bogota` as country-group labels. Preserve these exactly. They must not be described as verified jurisdiction, or used to certify a match to community geography. Filtering by source country is explicitly a publisher-group filter. The general source warning appears in the accepted metadata; the UI must flag affected rows before presenting this as geographic coverage.

The source headline says 300+ data centers, but the captured array has 261 entries. Neither number establishes complete coverage of the operator fleet or of global operating facilities. Different codes may share a campus pin; do not add them to OSM map-feature counts or the historical capacity collection.

## Intentionally excluded

No utility-power field is relabeled IT load. No operating status, available inventory, ownership of every listed campus, parcel boundary, building outline, or building height is inferred. The derived directory keeps `it_mw: null`, has no geometry, and labels every coordinate pair `publisher_pin`. Source HTML is not included in the application; the application stores only the reviewed factual projection and source-response hash.

## Refresh

The weekly capture fetches the registered official URL through the existing robots-aware, size-limited, public-HTTPS monitor. It writes candidates only. Each publisher has an isolated accepted head in the immutable SQLite directory ledger. A source refresh cannot move an accepted head without a named editorial decision and expected-current hash. Once checked in, the accepted publication rebuilds entirely offline and does not depend on artifact retention.
