# Protected deployment at untitled1.cc/compute

The hosted service uses the accepted SQLite publication and its registered-source
monitor. Nginx authenticates every entrypoint, asset, original attachment and API
under `/compute/`. The offline HTML is a dated snapshot. HTTP redirects to HTTPS;
`/compute` redirects to `/compute/` without exposing application content.

## Release and service

Run the complete checks before installing a release. Archive a verified Git
commit into `~/.local/share/compute-atlas/releases/<commit>/`, retain its commit
and tree identifiers, and atomically point `current` to that directory. Keep the
Python environment at `~/.local/share/compute-atlas/venv/`, with the pinned
`requirements.txt`. The database, content-addressed captures and backups live
beside the release directories; deployment never replaces the ledger.

Install the three units in `deploy/` into `~/.config/systemd/user/`, then:

```sh
systemctl --user daemon-reload
systemctl --user enable --now compute-atlas.service compute-atlas-backup.timer
systemctl --user status compute-atlas.service
curl --fail http://127.0.0.1:8137/api/health
```

The service binds only to `127.0.0.1:8137`, uses `/compute` as its configured
external root, and starts the background monitor. API bootstrap URLs use
`/compute/api`; relative assets stay within the protected route. Every response
has private cache policy. Forwarded headers cannot redefine the root path.
Private state uses a restrictive umask. The application exposes read-only API
endpoints and an explicit web-asset allowlist.

Verify that the user's systemd manager persists after logout (`loginctl
show-user username1 -p Linger` on this host). Enable lingering through the host
administrator if necessary. Review `journalctl --user -u compute-atlas.service`
and the app's source monitor for failures, deferrals and review items. An
acquisition failure never replaces accepted quantities.

## Nginx and authentication

`deploy/nginx-compute.conf` is the complete location block. The administrator
installs it into the existing TLS server with:

```sh
sudo /usr/bin/python3 /path/to/verified/release/deploy/install_nginx.py
```

`--dry-run` checks that the existing server can be edited without changing it.
The installer preserves other locations, backs up the current site configuration,
edits atomically, runs `nginx -t`, and reloads. A failed validation restores the
previous file. It copies the existing `/files` password hashes into a separate
root-owned `/etc/nginx/.compute-atlas-htpasswd` the first time, so the existing
login works without changing `/files`. Later password updates to either file
are independent. Passwords and hashes are never included in the repository.

Verify anonymous requests to `/compute/`, `/compute/api/publication`, JS, data,
original attachments and the standalone return **401**. Verify authenticated
requests return the application and private API responses. Test the actual
HTTPS URL in Chromium, including searches, touch zoom, geometry selection,
deep links and mobile layout. Do not infer deployment success from a loopback
test or an installer exit alone.

## Backup and recovery

```sh
systemctl --user start compute-atlas-backup.service
systemctl --user list-timers compute-atlas-backup.timer
```

The daily timer snapshots the committed WAL through SQLite's online backup API,
checks database integrity, and copies exactly the immutable body hashes that the
snapshot references. A missing/corrupt capture fails the backup. Only a complete
backup is renamed from `.staging-*` to a timestamped directory. Its manifest
records database and body hashes. This preserves accepted research, decisions,
history, source captures and review queues consistently, including while the
worker is active. Backups remain outside web assets; no automatic deletion is
enabled. Monitor disk usage and retain an off-host copy according to the source
retention policy.

To recover, stop the service, preserve the existing state directory, validate a
completed backup's manifest and database, restore its `atlas.sqlite3` and
`blobs/` into a fresh private state directory, then restart and check the
publication and histories. Keep the displaced database and WAL files together.
To roll back application code, atomically point `current` to a retained tested
release and restart. Retain a matching backup before a schema downgrade;
rolling back code alone does not roll back editorial decisions or migrations.
