# Using Compute Atlas

Start with the landscape for geographic context, the Facility directory for a
known place, or Search research for a company, disclosure, source or formula.
The [approved references](mockups/README.md) define the six-scale visual hierarchy.
The records and source imagery define what the app can actually show.

## Move from geography to evidence

World → Continent → Region → Metro → Campus → Facility. Select a visible marker
or use the keyboard-accessible record list. Inspect the selection before entering
the next scale. Drag or use arrow keys to pan/orbit; scroll, pinch or use the +/−
controls to zoom. Country, company, stage, evidence and text refinements intersect.
Map-linked lists can follow the viewport or the full geographic scope. Back,
Forward, reload and shared addresses retain camera, selection, filters and topic.

Campus and facility views distinguish projects, disclosed phases and physical
source features. Three historical imagery scenes across Helios and New Carlisle
contain nine accepted roof interpretations. Select a roof to inspect its dated
image and versioned geometry. Its area does not establish IT power, operating
status or a phase allocation. Other projects retain useful evidence schematics
and explicit image availability instead of invented buildings.

The worldwide catalog contains 5,301 community map records. Geometry supports
plan and orbit views; missing building heights remain unknown unless an explicitly
illustrative display height is enabled. The Equinix and Digital Realty directories
contribute 253 and 261 separate source listings. Publisher pins and nearby map
features are not automatically reconciled into the same facility.

Road and electricity layers expose native geometry, source dates and coverage.
Nearby electricity infrastructure does not prove campus service. Fiber routes
remain unavailable where licensed, reviewed geometry is absent.

## Research a project or company

The Facility directory searches all 5,894 native records and keeps their collection
identities separate. Inspect location precision, source dates, native disclosures
and source geometry before opening a dossier or original source. The Capacity
archive preserves the original 79-project view and independent IT power models.

Project dossiers organize cited claims by power, technical design, development,
commercial terms and financing. Read exact source locators, wider-context labels,
conflicts and earlier revisions. Compare up to three projects with each quantity's
original boundary and date. Company dossiers connect the named projects,
explicitly disclosed roles and financing. Contracts & connections exposes the
complete 178-record commercial/financing/archive collection without summing
unrelated financial quantities.

Search research indexes all native locations, companies, current and earlier
claims, sources, contracts, costs, 108 report sections, 5,938 workbook cells and
eight original files. Results are paginated without truncating the collection.
Workbook matches open the exact original sheet/cell, including cached values and
formula text. The original attachments remain available byte-for-byte.

## Keep and transfer your work

Save projects, companies, mapped locations, operator listings and reviewed source
features to the Research shelf. Add private notes in the corresponding inspector.
Use **Save this view** to name the current research address, including the filters,
selection and camera supported by that destination. Open or rename saved views;
remove native bookmarks or views with Undo. Changed source versions and missing
native records retain their earlier bookmark identity and notes.

The economics lab and investment lens save working inputs locally. Name cases,
compare up to three from the same model, share exact hypothetical assumptions and
export calculations with references. Invalid inputs cannot overwrite a valid case.

**Export session** includes notes, saved identities, views, comparison selections,
model cases and drafts. **Import session replaces the current local session**;
export existing work first if you want to retain a separate copy. This is browser
storage, not account synchronization. If storage is unavailable, the app explains
that research lasts only for the open session and offers an export.

Cited JSON and spreadsheet CSV exports contain every matching record, not only
the visible page. These record exports exclude private notes; session exports
include them. CSV text that could be interpreted as a formula is escaped, while
native numeric negatives remain numeric values.

## Read the publication's limits

`data/atlas.json` preserves the original projects and models. The separate accepted
evidence publication adds issuer/regulatory disclosures and revision history.
Source date, status, measurement boundary and scope travel with every claim.
Original attachments are unchanged. Named-site sums remain partial, mixed-vintage
model subtotals. IT load, gross power, equipment TDP, obligations and backlog are
distinct quantities; an unknown value never becomes zero.

The SQLite service adds publication APIs, acquisition history, capture retention
and an editorial queue. A new capture is not accepted evidence until reviewed.
Source-health screens distinguish request failures, raw-capture availability,
accepted publication and bundled fallback. The service exposes read-only research;
editorial decisions use the documented service workflow.

The standalone HTML embeds the app, data, maps, historical scenes and originals.
It works offline after loading; external source links still require a connection.
The hosted app loads local repository assets and can use the optional service.
Neither presentation implies live facility telemetry or current market pricing.

## Verify a release

Run `python src/build.py` to synchronize both generated entrypoints. The test
workflow covers the evidence ledger, data integrity, both browser entrypoints,
source failures, six scales, comparisons, research-session transfer, offline
attachments and phone/tablet layouts. `qa/research-workspace.py` exercises native
bookmarks, saved views and spreadsheet exports. Browser screenshot artifacts are
review evidence; inspect them alongside the approved mockups.
