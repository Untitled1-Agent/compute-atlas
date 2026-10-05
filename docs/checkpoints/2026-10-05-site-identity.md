# Site identity, source-established locality and integration checkpoint

## Starting tree and integration audit

Main at start: `28bef01074c5c675590493b693ef0f10e7aed847`; tree
`869a7181e84d94c0b542d1d7ebfeca1b1ad698f3`. The recovered source ZIP was
verified against that exact tree, including executable modes and ignored tracked QA.

The user requested merging all prior work. Open stacked PRs #5, #6, #7, #8 and #9
had **no unique commits**: their exact heads were ancestors of main, respectively
52, 39, 27, 24 and 16 commits behind. GitHub rejected retargeting the ancestor-only
PR #5 to main. All five were closed with per-PR ancestry evidence, not reapplied or
discarded. Main's source tree was not changed by the integration audit. Issue #2
contains the dated audit checkpoint and continuation plan.

## This slice

Six immutable typed identity facts add source-established names and localities to
existing projects, not new facilities or map coordinates. Identity claims use the
existing fact/decision/revision ledger. Only current accepted facts are exposed by
`GET /api/sites/{id}/identity` and the browser's read-only identity panel.

The panel juxtaposes the publisher's locality with the explicitly unverified
archive pin, preserves each independent description, identifies records sharing
an exact archival coordinate without merging them, cites adjacency separately,
and exports the same contract as the database API. Reviewed refreshes preserve
selection, notes and drawer history. Malformed identity updates are rejected.

No observation, source URL, source retrieval date, old claim, candidate, company,
map coordinate, archived research file or original attachment is changed.
Primary coverage remains 14 projects / 40 current observation rows / 22 sources;
there are 35 factual attributes (six new identities), 21 counterparty rows and
five unmapped candidates. The archive remains 79 projects / 75 map anchors.

## Local validation before publication

99 backend tests (36 new identity tests) passed. Integrity passed 15/15.
Actual local Chromium rendered the built standalone and passed identity 33/33,
six-scale 58/58, evidence desk 24/24 and coverage 28/28 assertions. Desktop and
mobile screenshots were opened and inspected; export-toast animations and
full-page capture scroll positions were allowed to settle before capture.

Local HTTP navigation is blocked by the execution environment with
`ERR_BLOCKED_BY_ADMINISTRATOR`. In-memory tests are **not** described as HTTP
validation. The permanent workflow additionally tests both entrypoints over real
HTTP, the SQLite service, source-health failures and original functional suites.
Exact remote commit, Actions run IDs and artifact checksums belong in the PR and
issue #2 once those checks complete; do not infer a remote pass from this file.

## Resume and boundaries

1. Confirm current main and open PRs through GitHub, not this dated note.
2. Run `python -m pytest tests -q`, `python src/build.py` and all permanent CI suites.
3. Inspect actual `qa/screenshots/*identity*.png` against the mockups.
4. Continue source-backed coordinate precision and independently reviewed global
   candidate promotion; do not turn a locality into a surveyed campus boundary.

No persistent public deployment is created by this change. Run `python -m server
serve` for the database/worker; the standalone is a dated offline publication.
