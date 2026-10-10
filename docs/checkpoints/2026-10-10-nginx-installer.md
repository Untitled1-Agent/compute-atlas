# Self-contained administrator installer — 10 October 2026

The user will run the final Nginx installation. A Python filename was unavailable
in their terminal, so `deploy/install_nginx.sh` now embeds the complete installer
and canonical location configuration. Its contents can be pasted directly into
the Untitled1 terminal; no repository path or sibling file is needed. It uses the
existing `/files` login hashes in a separate private password file.

The script checks the Atlas database health before edits, preserves other
locations, supports reruns, backs up the old site, validates/reloads Nginx and
checks six anonymous routes against the real local HTTPS virtual host. A failed
validation, reload or auth check restores and reloads the original configuration.
Private password-file creation uses a restrictive umask. No credentials are
included in the script, tests, source history or this checkpoint.

Validation: shell syntax and embedded Python compilation pass; all eight
operations tests pass, including full standalone installation, configuration
equivalence, idempotence, credential preservation, unhealthy-service prevention
and restoration after Nginx/auth failures. The self-contained Python body passed
its read-only dry run against this actual server. No Nginx edits were executed.

The pinned application remains implementation commit
`6eb17786ff771fb66a066fd0f18601725ff2c1af`, whose 216 backend tests and 778
application/data checks passed previously. PR #22's latest pre-installer checks
also pass (live run 38003488633 and source bundle run 38003488695).
The service and backup timer are active; loopback health is ready. Public
`https://untitled1.cc/compute/` still returned 404 at this checkpoint. After the
administrator executes the script, verify public anonymous 401 and authenticated
HTTPS/browser behavior before recording the deployment as live.

## Reload timing regression and correction

The first administrator attempt failed in the embedded Python auth check at
line 99. Host access logs show `/compute/` returned 404 at `00:45:18 UTC`; the
service journal shows the installation reload and rollback reload in that same
second. There were no contemporaneous Nginx error-log entries. The target site is
the configuration actually included by the service. This identifies the early
auth check as the failure, with a reload activation race as the cause supported
by the observed sequence and the native regression below.

[Nginx reloads by signaling its master](https://nginx.org/en/docs/control.html),
which applies the configuration and starts new workers. The installer had
incorrectly assumed that the reload command's return meant requests already
used the new configuration. The check now retries old-route 404 responses within
a shared 20-second deadline. All six routes must still return 401; unexpected
statuses such as 200 fail immediately, and a persistent 404 still restores and
reloads the previous configuration.

Ten operations tests now pass. `qa/nginx_reload.py` additionally starts an actual
unprivileged Nginx on a temporary random loopback port, pauses only that fixture's
master while queuing its reload, and reproduces a completed reload command with
workers still returning 404. The corrected canonical installer helper waits for
the resumed master, then verifies six real anonymous 401 responses, valid Basic
Auth 200 and invalid credentials 401. All eleven checks pass. This is actual
isolated HTTP Nginx validation, not proof of production HTTPS publication.

The corrected installer was atomically installed at
`/home/username1/compute-nginx.sh` with SHA-256
`e15f02ecb526e5d5c1eb8fe540eee9e56a929670203d5f51084d39eac6930af2`.
Its real-host dry run passes. The administrator reruns
`/bin/bash /home/username1/compute-nginx.sh`; no new download or copied script is
needed. Actual public/authenticated acceptance still follows this root step.
