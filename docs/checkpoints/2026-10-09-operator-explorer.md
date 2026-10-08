# Reviewed operator explorer — 9 October 2026

This continues PR #18 and the earlier 3D/catalog/reference work (#15–#17), not a replacement of those features.

## Recoverable source and data

The first successful directory capture is Actions run 37859006031, artifact 11584839240. Its exact ZIP, candidate JSON and accepted publication hashes are in `data/catalog/operator-directory-review.json`. The directory was independently read from the official publisher table. It contains 253 codes across 33 source country groups (93 EMEA, 53 APAC, 107 Americas). This is the full captured table, not a claim of the publisher's complete fleet or a global census.

The read-only capture initially failed on valid HTML with omitted cell/row end tags. Pinned HTML5 parsing plus the exact regression resolved it; no partial directory was published. The source is undated. Actual capture and review timestamps are retained, not replaced with this checkpoint's title date.

`tools/materialize_reviewed_directory.py` permits only the hash-pinned, explicitly reviewed artifact projection. The review workflow verifies it, tests the source and commits the generated publication and standalone on review branches only. Once tracked, the publication rebuilds offline; artifact retention is not a runtime dependency. No latest-artifact lookup or automatic editorial acceptance is allowed.

## App and database

Independent immutable SQLite directory snapshots, records and decisions; SQL country/text pagination; leased internal editorial acceptance and read-only same-origin APIs. Source changes are monitored through the ordinary review queue and the weekly candidate workflow. Staging is never publication. Service outages or invalid data produce a visible fallback to the checked-in snapshot.

The operator directory is available from the main navigation, collection tabs, global search and deep links. It includes all records, including 123 without a proposed map link. Exact operator/code/country rules yield proposals for 130 codes; eight codes have multiple candidate map features. These proposals are not certified identity or geometry. UK/USA/UAE country aliases are explicit; all 253 browser proposals match the Python implementation. FR2 does not absorb FR2.6. No code count is added to OSM features or archived capacity.

## Validation and continuation

Local backend: 168 passing tests. Local embedded directory browser: 25/25; embedded catalog/3D: 35/35. Local HTTP navigation is blocked, so actual hosted, standalone and SQLite-backed HTTP validation must run in Actions on the final head. Do not report the embedded runs as HTTP. Fresh screenshots were opened and inspected; the final CI artifact is authoritative for the committed source.

Next: add further independent operator directories, resolve proposed matches through address-specific reviews, and deepen reported facility specifications. The community catalog still has overlapping features and incomplete coverage. Neither the directory nor source-outline 3D establishes an operating-capacity census or a surveyed building model.

The optional directory CLI wrapper was not included after its repository write could not be completed. The original CLI is unchanged; the tested internal DirectoryStore interface and read-only HTTP endpoints are included.
