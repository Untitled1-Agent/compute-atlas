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
