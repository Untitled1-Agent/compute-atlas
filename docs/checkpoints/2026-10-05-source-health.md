# 5 October 2026 — Source acquisition console

## Starting point

Upstream main: `bef273f20516486280d541711196949db5f85597` (PR #11).
Verified tree: `4d456d7fc8037a9067eacb82bb0da1189824d6c1`.
Baseline permanent Actions run: `37206950371`, success.
The old source archive was recovered from artifact `11304224246`; the archive SHA-256 is `9e3f3dff7ff3a40d16581ccb56002b813e2fd1c4cbca18907246f5a561341d4e`. The extracted tree exactly matched main.

## Implemented

- `src/source-health.js` / `.css`: paginated source activity, source-specific append-only event history, separate acquisition queue and publication panels.
- Separate successful-fetch, source-publication, editorial-retrieval, first-body-capture and latest-body-observation dates. Full SHA-256 identities remain inspectable.
- Explicit never-fetched, overdue, deferred, paused, unavailable and malformed-response states. Good cached results retain their original timestamps after failures.
- Request identity guards prevent late results from reopening a closed drawer or overwriting a newly selected source. Queue completion also cannot reopen a dismissed drawer.
- All source strings are escaped; source links accept only HTTPS without credentials. The public UI never mutates the ledger or publishes a claim.
- `qa/source-health.py` tests SQL pagination, returning A/B/A representations, empty states, XSS, focus, mobile overflow, request races and offline no-network behavior.
- Both entrypoints and the standalone builder include the module. The permanent CI includes its real-HTTP suite.
- Reusable `review/**` workflow builds and tests before synchronizing only the generated standalone; source checkpoints and exact-tree recovery are documented.

## Local validation at this checkpoint

- Python backend: **62/62** tests passed.
- Data/archive integrity: **15/15** checks passed.
- Six-scale Chromium in-memory suite: **58/58** checks passed.
- Evidence desk Chromium in-memory suite: **24/24** checks passed.
- Source-health Chromium + SQLite ASGI bridge: **28/28** checks passed.
- Syntax and standalone rebuild completed. Desktop and mobile source-health screenshots were opened and inspected; synthetic fixtures are clearly labeled.

This container's Chromium denies local HTTP navigation (`ERR_BLOCKED_BY_ADMINISTRATOR`). No browser policy was changed. The real-HTTP suites must pass on the GitHub runner before merge; local in-memory results are not represented as HTTP validation.

## Next runnable checkpoint

1. Build this branch through `Build and verify review branches`; inspect every suite and its source/hash artifact.
2. Open the PR at the generated head and require the permanent live-checks workflow to pass independently.
3. Update issue #2 with PR, exact head and CI IDs before merging.
4. Continue global primary-source coverage and map presentation in a separate PR. The 79-site historical archive and its IT-MW estimates are unchanged by this console PR.

## Merged checkpoint

PR #12 merged as `d241efb59d695451c7c70d10a1d284dd702d1cbc`. Tested head: `c98a4b07a628ef7ac758572e738d70baf593fc7e`. Build run `37244875707` and independent permanent PR run `37245288613` both passed. Results: 62 backend tests and 335/335 application QA assertions, including actual HTTP/Chromium suites. The downloaded source-health desktop/mobile and world screenshots were inspected. The source ZIP SHA-256 is `3dab81fc9aecc1bbe663d284497e2d5603cef23e60af045df8a1968fece8e0a6`.
