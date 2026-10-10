# Public HTTPS authentication checkpoint — 10 October 2026

The administrator applied the corrected installer. Nginx's successful reload is
recorded at `00:53:37 UTC`. The requested public route is now present at
`https://untitled1.cc/compute/` and challenges with Basic realm `Compute Atlas`.

Fresh real public HTTPS checks at `01:00:52 UTC` returned 401 anonymously for the
entrypoint, `/api/publication`, `/src/app.js`, `/data/evidence.json`, an original
PDF attachment and `/compute_atlas.html`. This verifies the actual public
authentication boundary, rather than the temporary QA proxy. The
[receipt](evidence/2026-10-10/public-authentication.json) records all six statuses
and challenge headers without credentials.

The persistent loopback application is healthy, its database is ready and its
background source monitor is enabled. It remains pinned to implementation
`6eb17786ff771fb66a066fd0f18601725ff2c1af`. Current runtime counts are 79 archive
sites, 37 registered sources, 31 source versions, 77 pending review items, 40
accepted observations and 61 fetch attempts; these separate denominators are
not an operating-site census. The online backup timer is already installed.

The installer timing correction is commit `4638872` on
`feat/protected-compute-deployment` in PR #22. Its ten operations tests and eleven
actual isolated Nginx reload/auth checks pass. Latest fix CI also passes:
[browser audit 38010937080](https://github.com/Untitled1-Agent/compute-atlas/actions/runs/38010937080)
and [source bundle 38010937074](https://github.com/Untitled1-Agent/compute-atlas/actions/runs/38010937074).

Authenticated production HTTPS and browser acceptance have not yet run.
Automatic approval review rejected sending the stored existing login to the
website because that credential transfer needed explicit authorization. The
user was asked to approve checks at this exact destination or test the login
themselves. No credentialed request was sent by the rejected operation. Existing
configuration was inspected locally to answer the user's requested login and
credential-reuse questions; no plaintext password or hash is included in this
checkpoint, receipt or repository. Keep the pending authenticated check distinct
from the successful public anonymous checks.
