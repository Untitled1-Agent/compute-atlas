# Non-root container delivery — 21 October 2026

A real image build exposed a startup failure hidden by ordinary checkout modes:
Docker preserves copied directory/file permissions. Private 0700/0600 source
paths remained root-owned, so UID 10001 could not read `server/__init__.py`.
Runtime source, data, originals and both entrypoints now copy with the service
account's ownership. The service continues to run unprivileged with a read-only
root and only its data volume writable.

Seven container checks pass locally: non-root execution, SQLite health, populated
accepted observations, readable hosted/standalone assets, rejected private paths,
persistent database across container replacement, and byte-identical publication
after restart. The local build supplied this platform's proxy CA as a temporary
BuildKit secret while preserving TLS verification. The new CI job builds the
unmodified Dockerfile from deliberately restrictive file modes and runs the same
checks. No production container, ledger or backup was touched.
