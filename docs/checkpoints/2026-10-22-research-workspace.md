# Portable research workspace — 22 October 2026

Native map and operator records can now be saved directly from the common
directory, map inspector and publisher explorers. Their bookmarks retain source
identity and version metadata. A changed source publication is identified on the
shelf; an unavailable record retains its bookmark and private note. No project,
operator or geometry identities are merged.

Named views restore directory/search filters, geographic camera and dated roof
selection, model assumptions, company refinements, report position, workbook
selection, capacity archive layout, cost tabs and company comparisons. Views can
be renamed and reopened; view/bookmark removal supports Undo. Session exports and
imports transfer these alongside existing notes, source features and models.
Imported routes, identities and collection sizes are validated. The existing
project-research API remains distinct from the shelf API.

The directory, connections and full search offer complete filtered CSV exports.
Native quantities, dates, identifiers, source links, licensing and source metadata
remain attached; private notes are excluded. Spreadsheet formula text is escaped,
while native negative numeric values remain numeric. JSON exports remain available.
Help explains the actual hosted/offline mode, session replacement and the complete
workflow. Saved work leads the shelf; empty model/note sections are suppressed.
Hosted and standalone shelf styles are explicitly checked. Hosted help offers the self-contained app download. Unsupported external
arrow glyphs and duplicated link arrows were replaced with legible navigation.

## Local acceptance

The user explicitly requested continued verification in this workspace and will
handle production deployment. All 35 local regression suites passed after fixing
a shelf/project API collision and rerunning the affected tests. The new research
workspace suite passes 79/79 across both entrypoints; project research passes
146/146. Backend tests pass 276/276. Browser runs were serial and low priority.

Managed Chromium blocks native `file://` navigation. The functional and smoke
suites now accept explicit `ATLAS_STANDALONE_HTTP=1`: load the embedded artifact
through local HTTP, switch the browser offline, and verify no further requests.
The functional suite passes 48/48 in that mode. Native file navigation remains the
default in CI; the local HTTP/offline mode is labeled in its receipt.

The actual Docker image was built locally using a temporary CA secret with TLS
verification enabled. Container checks pass 7/7: non-root execution, read-only
root, readable hosted/standalone assets, private-file isolation and persistent
SQLite state across replacement. The optional CA build mount is not an image
layer. Build contexts exclude virtual environments, QA output and documentation.

Original attachments, accepted source publications and native collections are
unchanged. This release completes additional application workflows; it does not
invent current imagery, complete campus inventories or unsupported fiber/service
relationships. Production deployment remains the user's step. Daily backup timers
remain disabled.
