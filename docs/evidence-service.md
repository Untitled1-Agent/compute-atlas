# Evidence service and source acquisition

## Run the application

```sh
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m server serve
# Open http://127.0.0.1:8000
```

This starts the same visual app with a SQLite publication API and a background
source worker. `--no-refresh` disables acquisition without disabling the app.
`docker compose up --build -d` uses a non-root, read-only container and a persistent
`evidence` volume. The port is bound to loopback. Use a TLS reverse proxy and
appropriate network policy before exposing it beyond the local machine.

The static `index.html` and self-contained `compute_atlas.html` still work without
this service. Neither static mode pretends a server is running. The service adds
its configuration only when serving the hosted entrypoint. If the publication
endpoint is unavailable during startup, the app falls back visibly to the
checked-in, dated publication.

## Data model and publication boundary

`var/atlas.sqlite3` uses foreign keys, WAL, busy timeouts and versioned migrations.
It stores historical datasets separately from accepted claims. Original research
attachments and model rows are not modified by capture. Sites have an FTS5 index;
observations retain unit, metric, boundary, status, scope, date, qualifier and
source ID. Relationships reference known counterparties. Missing quantities are
null; invalid, negative and non-finite capacity values are rejected.

Claims, source-version records, editorial decisions and audit events are
append-only. A changed claim requires a new ID and `supersedes`. Acceptance of a
revision hides the previous accepted claim from the current publication without
deleting it. Rejection can restore a prior accepted version only when no accepted descendant
remains. Migration 2 resolves complete revision ancestry, including withdrawn
intermediaries. Competing branches are rejected under a serialized write
transaction, including simultaneous reviewer decisions. Revisions retain their
metric, unit, boundary and scope; different measurement series stay separate. Initial seeding is
idempotent and never overrides an editor's subsequent rejection.

Source acquisition **does not publish numerical facts**. Fetching a page merely
records the HTTP outcome and, if changed, adds a review item. An HTML source uses
article/main text for semantic change detection so navigation-only changes do
not continuously create editorial work. The original response has a separate
SHA-256 hash. PDFs are captured as binary evidence, never claimed to have been
parsed or verified by this worker.

The public API is read-only. There is no anonymous mutation endpoint, no arbitrary
URL fetch endpoint, and no cross-origin API access. Private browser research
notes remain in that browser and never enter the service. Raw captured documents,
SQLite files, backups, environment files and Python source are not web assets.

## Bounded worker

Only sources and feeds registered in the reviewed evidence file are fetched.
Pages default to daily checks; each feed has its explicit schedule. Jobs use
durable leases and recover after interruption. Requests have timeouts, an 8 MiB
decompressed-body limit, a redirect limit, publisher robots checks, per-host
pacing, ETag/Last-Modified conditional requests and exponential retry backoff.
`Retry-After` is honored up to seven days. Robots failures are deferred, not
worked around. HTTPS, host allowlisting and DNS/IP checks reject private or
unregistered destinations. Deploy an egress firewall as an additional production
control: application URL checks are not a substitute for network isolation.

RSS/Atom items are deduplicated by source and URL. A candidate URL is not
fetched merely because it appeared in a feed, and its content never becomes a
site record without review. Publisher feed descriptions are not treated as
verified measurement claims.

```sh
python -m server status
python -m server refresh --limit 20       # one bounded pass through due jobs
python -m server queue --limit 20 --offset 0
python -m server submit observation claim.json --actor analyst
python -m server review CLAIM_ID accepted --actor analyst --reason "Checked primary source, scope and unit"
python -m server resolve QUEUE_ID acknowledged --actor analyst --reason "Compared capture with accepted claims"
python -m server export /tmp/reviewed-evidence.json
```

Acknowledging a queue item is not accepting a claim. Export produces current
accepted claims, explicitly labeled candidates and a separate `revision_history`
partition. Earlier and rejected claims in that partition are not current values
and never enter power totals. Ancestors are retained so the export can be imported
into a fresh ledger in any JSON ordering. The publication export preserves the
latest review status, not the entire decision log; use database backup for that. Review the exported diff
before replacing `data/evidence.json`; then rebuild with `python src/build.py`.
The export is atomic and has a deterministic publication hash. Hosted API clients
can use ETags; source capture times and publication dates remain different.

## Operations and recovery

The live monitor displays completed captures, failures, next attempts and a
paginated pending queue. It discloses unavailable/stale status rather than
showing cached responses as current. The API also exposes `/api/health`,
`/api/sites?q=...`, `/api/sources/{id}/versions`, `/api/claims/{id}/history` and
`/api/audit`. Claim history identifies the effective revision and its dated
editorial decisions. Unreviewed drafts are not returned by the history endpoint.

```sh
python -m server backup backups/atlas.sqlite3
```

Backups use SQLite's online backup API and include committed WAL changes. Back up
`var/blobs/` with the database and retain that volume across deployments. Raw
snapshots are content-addressed, stored for local research and not redistributed
by the API. Respect publisher terms and applicable retention policies. Monitor
disk use; this first implementation has no automatic raw-snapshot deletion.

A daily GitHub workflow supplies an additional capture/report path when enabled
on the default branch. Its Actions cache is a convenience, **not a durable
production backup**; eviction starts a fresh baseline. The long-running service
with a persistent volume is the durable operating mode. Workflow summaries do
not imply successful capture for deferred or blocked sources.

## Tests

`python -m pytest tests -q` covers immutability, provenance boundaries, nulls,
review gating, revision conflicts, lease recovery, 304s, semantic deduplication,
RSS discoveries, robots, redirects, private DNS, size limits, backoff, pagination,
backups, static-file isolation, read-only APIs and worker lifecycle. Browser QA
includes a separate service HTTP run in CI. The offline UI suite verifies that
no service probe is made by the self-contained build.


## Analyst evidence desk and update notifications

The facility attribute/source cards open a read-only evidence desk with searchable
quantities, attributes, counterparties and earlier revisions. Values retain their
measurement scope, source date, status and inequality. Non-power disclosures such
as PUE and annual kWh are not rounded into whole MW. Cited dossier export includes
source records for both current and superseded claims, separately from archival
estimates and the user's optional private note.

The service browser conditionally checks the publication ETag every five minutes
while visible. A changed *accepted publication* prompts the analyst to apply it;
a new source capture alone cannot change displayed capacity. Applying an update
preserves the selected facility, filters and private notes. Invalid/unavailable
responses keep the last loaded evidence and show a retry notice. The standalone
makes no background requests. The full database decision log remains available
through the read-only history API and durable backup.
