# Research navigation refinement — 10 October 2026

Baseline: `c89553113f57672e0c921c3d29bd4319a625dca8` on
`feat/project-dossier-research`. Work branch: `feat/research-navigation`,
stacked on the completed project research PR. The user requested refinement
after the enrichment of all 79 archived dossiers.

## What changed

The richer evidence was difficult to scan. Search listed project names without
showing the matching claim; long dossiers mixed disclosure dates with older
announcements, and empty category cards consumed substantial space.

The research index now combines geography, archived operator association,
review outcome and project-claim topic filters. Results show a matching claim,
its scope, qualifier and original citation. Source publishers/titles, locators,
reporting periods and native formatted quantities are searchable. Contextual
matches retain their own label and qualification. Individual filters can be
removed, and a complete reset restores keyboard focus to search.

The index URL records its query, filters, ordering and page. Reloading that URL
restores the view; optional session storage retains the previous research view
when returning from a reloaded site dossier. Invalid filter values are ignored,
query length is bounded, and unavailable storage does not prevent navigation.

Dossiers surface recent dated disclosures from distinct categories, with
citations and qualifications. Topic and claim shortcuts open hidden claim
groups, scroll below the sticky header and focus the requested section.
Per-project search preserves input focus and separates project claims from
context. Desktop drawer claims use a full-width reading column; missing
categories remain compact and explicit. The primary source trail shows exact
documents, publisher attribution, publication/retrieval dates and claim scopes.

The development chronology and its cited export are ordered by reported/as-of
date. Those dates do not become inferred completion dates. A plan is still a
plan even if its proposed completion date has passed; undated documents are
kept separate from dated ordering. The Wisconsin commissioning statement is
visible ahead of the older planned schedule.

## Evidence boundaries and performance

The original Wisconsin investment observation explicitly says its more-than
$7 billion program includes a second facility. Its legacy
`regional_investment` boundary now receives the same wider-context treatment
as newer `applies_to: context` claims across dossiers, source views, the evidence
desk and native disclosures. It is excluded from project-financing cards and
facility attributes. Cited exports preserve the original amount, boundary and
qualifier while listing its ID among contextual claims.

All research datasets and original archives are byte-identical to the baseline.
This checkpoint reorganizes accepted evidence; it adds no publisher claims,
capacity estimates or inferred operational status. Current publication and
revision decisions remain unchanged.

Research profiles and searchable text are indexed once per accepted publication,
rather than rebuilding revision chains for every project on every keystroke.
Applying an explicit reviewed publication invalidates the cache and retains the
chosen filters. Literal matching escapes text before adding highlight markup.
Temporary QA ledger fixtures exercise untrusted text without changing production
research.

## Validation and release

Actual Chromium exercises the SQLite HTTP application and standalone HTTP,
including filters, date ordering, cited matches, native units, deep-link reloads,
pagination, hidden-claim navigation, context boundaries, explicit publication
updates, keyboard focus and 320/390-pixel mobile layouts. The first pass exposed
pagination hidden beneath the sticky header, delayed default drawer focus
overriding a requested claim, and filters lost after a dossier reload; all three
were corrected and rerun.

Local affected suites and archive integrity pass **463/463** assertions,
including **122/122** research checks across the actual SQLite and standalone
HTTP entrypoints. All 19 JavaScript modules parse. Two standalone builds have
identical SHA-256
`930d23546e16f0002f4072184bcd8b67a2c552c9a0e231f26c8cec485ec0840a`.

Fresh [QA results](evidence/2026-10-10/research-navigation-qa.json) and inspected
[desktop search](evidence/2026-10-10/research-navigation-index-desktop.png),
[desktop disclosures](evidence/2026-10-10/research-navigation-brief-desktop.png)
and [mobile disclosures](evidence/2026-10-10/research-navigation-brief-mobile.png)
are retained. The original attachment/integrity checks, affected browser regression
suites, JavaScript parsing and deterministic standalone generation are required
before release. Exact-head CI runs the complete backend and browser suites.

Deployment occurs only after those checks pass. The release preserves the live
ledger and captures, takes a verified backup, retains the previous release and
changes the application symlink atomically. The exact commit, CI links, backup
hash and deployed-browser receipt are recorded on issue #2 and the SHARED
project blackboard. Existing Basic Auth remains in place. Production acceptance
uses the actual loopback deployment and anonymous public HTTPS auth checks;
authenticated public-browser acceptance is not claimed.
