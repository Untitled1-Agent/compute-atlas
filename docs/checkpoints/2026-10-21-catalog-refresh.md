# Reviewed geographic refresh and absent-record recovery

The 19 October 2026 scheduled OSM capture was re-normalized locally after checking
its source and Natural Earth hashes. The output exactly matches the candidate,
passes the catalog validator, and is pinned by `data/catalog/publication-review.json`.
Source run: https://github.com/Untitled1-Agent/compute-atlas/actions/runs/39242678199.

The map contains 5,301 source features across 115 named countries/territories,
including 1,913 in Europe. Compared with the 5 October publication, 50 identities
are added, 14 are absent and 102 records changed. The changed fields are retained
in the review receipt. All four operator-reviewed records are unchanged; no
review is reassigned across identities. Every IT-power value remains null and
community mapping lifecycle tags remain distinct from operating claims. The
79-project research collection, accepted power claims, source interpretations,
campus imagery and original attachments are unchanged.

Absent records are not inferred closed, demolished or merged. The prior capture
remains in Git history. An old bookmarked source identity now opens an explicit
unavailable-record notice with its original OSM link, private note and session
export. Camera URL updates and reload preserve that identity. The research shelf
can reopen the unavailable record; only an explicit recovery action clears it.

New SQLite volumes seed this reviewed capture. Existing services deliberately
retain their accepted catalog until an operator stages this file and accepts its
hash with the existing `catalog-stage` / `catalog-accept --expected-current`
workflow. Deploying code does not silently replace an accepted database snapshot.

The current public imagery service queries were also checked on 20 October:
USGS returned the existing 2022 Helios raster and Indiana returned the 2025 New
Carlisle tile. This confirms these service responses, not absence of newer imagery
elsewhere. No source date, building-to-phase relationship or utility service link
was inferred. The 20 October source-monitor run recorded 236 captured versions
and 283 pending review items; 63 sources returned HTTP 403. These retrieval and
review outcomes remain separate from the accepted publication.
