# Project research audit — 10 October 2026

Baseline branch `feat/protected-compute-deployment`, commit `806d6da`.
The 79 archived dossiers contain primary observations, facts or relationships
for only 14 distinct projects: 40 observations, 35 facts, 21 relationships and
27 curated primary source records. The map catalog and publisher directories
are separate collections; their thousands of geographic records do not deepen
these project dossiers.

The request is to enrich each existing project with multiple defensible sources.
Research partitions cover all 79: 27 Google/Microsoft, 23 Meta/Amazon/xAI/Tesla,
22 partners/Stargate and seven Chinese projects. Follow operator disclosures to
utility, regulator, government and counterparty evidence. Preserve unresolved
internal labels and campus-versus-building distinctions.

Implementation adds categorized, source-located project claims, explicit wider
context, a per-project research review and open questions. Source acquisition
remains independent of editorial acceptance. Archived models, original files,
map anchors and source-native identities remain recoverable.

## Delivered research

Work branch: `feat/project-dossier-research`, stacked on the protected-deployment
branch. The [project-by-project review](../research/2026-10-10-project-dossiers.md)
links four detailed research memos and the retained machine-readable bundles.

- 230 curated primary sources, up from 27. Exact matching URLs reuse existing
  source IDs; publisher labels do not imply independent corroboration.
- 703 new claims: 530 project-specific and 173 explicitly contextual. The current
  accepted layer contains 47 observations, 731 facts and 21 relationships.
- Project-specific primary evidence for 68/79 projects, up from 14. All 79 have
  cited research and review records: 57 enriched, 14 partial and eight unresolved
  identities. These outcomes are not completeness or confidence scores.
- Six categories: identity/location, technical design, power/energy,
  development/milestones, commercial relationships and investment/financing.
  Each enriched claim includes a source locator, reporting date or explicit
  absence, scope and qualification.

Important corrections include the dated Wisconsin Fairwater, Temple and Kuna
operating milestones; the small Lordstown proof-of-concept; Project Jupiter's
updated fuel-cell plan; Google's separate withdrawal/discharge/consumption
figures; and Baidu's D15 expansion versus the wider Yangquan compute network.
Unresolved North/East aliases, Meta/QTS and Oracle/DayOne associations remain
context. China-native FP16, PUE, GJ, generation MW, hectares and mu retain their
original meanings. No new quantity is converted into archived IT MW or H100e.

## Application and ledger

The searchable **Project research** index opens all 79 dossiers, with pagination,
six-category claim cards, original disclosure links, source locations and open
questions. The same research appears in campus/facility views, global search,
map filters and cited JSON exports. Wider context is visibly separated and is
excluded from facility power ladders and attributes. Source/back navigation,
deep-link reloads and explicitly applied publication updates preserve research
context, including on mobile.

The editorial merge tool rejects immutable-claim collisions and is idempotent.
SQLite validates enriched claims and review records; reimport preserves existing
decisions and revision history. An index on claim decisions fixes the slower
publication queries exposed by the larger ledger. Background source capture
continues to produce review items rather than silently accepting new claims.

The host has little free disk. New captures preserve a 128 MiB reserve and
record normal retryable failures when space is insufficient. Backup preflight
checks the database, referenced bodies and a 64 MiB reserve before allocating a
snapshot. Only this project's disposable pytest state was cleared; persistent
research, captures, backups and other applications were retained.

## Verification

Local verification uses actual Chromium, the SQLite-backed HTTP application,
static HTTP entrypoints and the native offline file. Embedded/in-memory modes
are not counted as HTTP coverage.

- All 236 backend regressions pass, including editorial boundaries, import and
  backup round trips, acquisition retry behavior and low-disk protections.
- The new project-research suite passes 62/62 checks across SQLite and standalone
  HTTP, including citations, project/context exports, all 79 dossier exports,
  search, deep links, keyboard focus, mobile navigation and publication updates.
- All 14 browser suites and archive integrity pass 842/842 assertions.
- Archive integrity passes 15/15 checks. All eight original attachments remain
  byte-identical; 92 phases, 108 sections, 101 tables and 5,938 workbook cells
  remain available. Original models, map anchors and geographic datasets have
  no changes.
- JavaScript syntax passes for all 19 modules. Two successive standalone builds
  produce SHA-256 `72eb0c262ea18991229528fec58e5aa053afc4f9c0b198f4f4287b0d9f77f462`.

The complete browser results are retained in
[project-research-qa.json](evidence/2026-10-10/project-research-qa.json). Inspected
screenshots show the [desktop project/context distinction](evidence/2026-10-10/project-research-desktop.png),
[mobile native-unit dossier](evidence/2026-10-10/project-research-mobile.png) and
[unresolved-project index](evidence/2026-10-10/project-research-index-mobile.png).
Earlier failures exposed stale fixed claim counts, an ambiguous export selector,
large-HTML `set_content` timeouts and clicking a moving camera. Tests now retain
the original claims within the richer publication, scope the intended export,
open the actual offline file and wait for camera completion. Running large
browser and backend audits concurrently introduced long timeouts on this
resource-constrained host; the final browser checks run serially.

Deployment follows completed local checks and successful CI for the exact PR
head. The release keeps the existing ledger, captures and authentication config,
takes a verified backup, and updates the pinned application atomically. The
release commit, CI run and actual deployment receipt are recorded on tracking
issue #2 and the local SHARED project blackboard. Production checks include
loopback publication/assets and anonymous public auth gates. No production
credential-transfer check is attempted in this workstream; an authenticated
public-browser pass is not claimed.
