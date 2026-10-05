# 5 October 2026 — Global disclosure coverage

## Upstream

Main `d241efb59d695451c7c70d10a1d284dd702d1cbc` (PR #12). The preceding source-health checkpoint contains the exact build, CI and artifact identities.

## Implemented in this slice

- An accessible global coverage/disclosure drawer, reachable from the map rail and primary-review KPI. Coverage denominators are record counts, not market share or confidence scores.
- Geography, measurement-boundary, status and text filters, with ten-row pages. Current revisions only; null stays undisclosed, comparison operators and native units survive. Quantities are never automatically summed.
- Primary-source navigation, back-state retention, native-unit mobile layout, explicit candidate section, and cited JSON export preserving source URLs, reporting dates, retrieval dates and nulls.
- Filtered source-to-facility drill-down works even when the previous map was filtered to another geography. Source-status updates preserve the search caret.
- Four freshly read Google location pages (P19–P22) and source-linked candidates: Hamina, Changhua County, Singapore, Quilicura. All remain **unmapped candidates**. No new site, MW, coordinates, parcel or building geometry is fabricated.
- Every new source registers a seven-day refresh job in the existing acquisition service; actual fetching still depends on a running worker and publisher access. No fetch success is inferred from editorial retrieval.

## Fixed during local browser review

The first KPI prototype did not match the original HTML whitespace. It now transforms only the identified review card via a DOM template rather than fragile paired string replacements. A PUE assertion initially compared the whole value-and-unit element; the corrected assertion checks the numeric node and independently verifies the exported comparison and unit. Cross-geography selection is explicitly protected and regression-tested.

## Validation at source checkpoint

Backend pytest 63/63; archive integrity 15/15; global-coverage in-memory Chromium 28/28; source-health in-memory Chromium + real SQLite ASGI bridge 28/28; six-scale in-memory Chromium 58/58; evidence-desk in-memory Chromium 24/24. Desktop coverage/world and mobile native-unit screenshots were opened and inspected. These local results are not browser-HTTP validation. Both review-build and permanent PR workflows must run the real-HTTP suites on the exact final generated head before merge.

## Preserved data boundaries

The 79 archived projects, 75 approximate map anchors, 64 original source records, 29 companies and eight checksum-protected research originals are unchanged. The primary layer remains 40 current observation rows (including two undisclosed quantities) across 14 reviewed projects, plus the existing facts/relationships/revision history. It now cites 22 primary sources and lists five candidates. Candidate counts must never inflate mapped counts or power subtotals. See [the candidate research note](../research/2026-10-05-google-location-candidates.md).

## Next reproducible step

Inspect the review-branch build artifact (source ZIP, COMMIT, TREE, SHA256SUMS, all results and screenshots). Open the PR at its generated head and require independent permanent CI. Record run IDs and merged commit on issue #2. The next data slice should add a reviewed site-identity registry with provenance and coordinate precision, then promote candidates through an explicit decision — not by mutating the historical archive or geocoding place names silently. Exact site geometry and broader current capacity coverage remain research gaps.
