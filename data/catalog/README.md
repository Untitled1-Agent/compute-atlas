# Geographic coverage, separately licensed

`osm.json` is a derived OpenStreetMap feature database under **ODbL 1.0**.
© OpenStreetMap contributors. https://www.openstreetmap.org/copyright
License: https://opendatacommons.org/licenses/odbl/1-0/
The same licensed database is exportable in the offline app and through the API.
Its source IDs, versions, capture date, normalized geometry, member relationships,
raw tags and full acquisition manifest are retained. `source-capture.zip` preserves
the exact sanitized source and Natural Earth country input, with SHA-256 checks.

`reviews.json` is a separate, manually reviewed factual reference collection.
Operator source pages are linked, not republished. The separate original research
archive does not become OSM evidence and is not rewritten by catalog ingestion.

The map contains buildings, campus areas and points, which may overlap or describe
the same facility. Counts are map-feature counts, NOT unique data centers. Relation
membership is exposed rather than silently discarding or merging records. No
unprefixed OSM tag is interpreted as operating status. No floor area, kVA, cabinet
count, or height is converted to critical IT MW.

## Update and review

The weekly `catalog-capture.yml` creates candidate artifacts only. Its fixed HTTPS
endpoints, byte/time limits, incomplete-response checks and error manifest prevent
failed sources from erasing accepted data. Commercial directories remain
separate source-specific publications; their factual extraction is not an
open-data license or proof of a publisher permission grant. See the
[source-rights audit](../../docs/research/2026-10-09-additional-operator-sources.md).
PeeringDB bulk redistribution is excluded pending authorization under its AUP.

```sh
python tools/capture_catalog.py var/catalog-candidate
python tools/normalize_catalog.py var/catalog-candidate var/catalog-candidate/normalized.json
python -m server catalog-stage var/catalog-candidate/normalized.json
python -m server catalog-status
python -m server catalog-accept NEW_HASH --expected-current OLD_HASH --actor Reviewer --reason 'Reviewed geographic changes and source boundaries'
```

Do not accept unexpected mass deletions without checking query coverage. SQLite
keeps prior snapshots and review decisions. The accepted catalog is independent
of the capacity ledger. `catalog-accept` does not accept any new power claim.
