# Primary operator directories

Open **Operator directory** from the navigation or the map's collection tabs. Search by facility code, locality or source country group. Select a row to inspect service coverage, provenance, and separately labeled map-match proposals. Missing coordinates and IT load remain unknown; map features, directory codes and archival capacity records have different denominators.

The service exposes `GET /api/operators/publication`, `/api/operators/records` (q, country, region, limit, offset), and `/api/operators/status`. Publication responses have ETags; all endpoints are read-only. A browser reload explicitly loads a newer accepted directory. A failed or malformed service response falls back visibly to the dated checked-in file.

Acquisition and review:

```sh
python tools/capture_operator_directory.py var/operator-candidate
```

`DirectoryStore.stage` and `DirectoryStore.accept` provide the internal editorial interface. Acceptance requires a named reviewer, reason and expected-current hash. Snapshots and decisions are append-only. There is no public HTTP write endpoint or new directory CLI wrapper in this slice. Restarting the service does not overwrite a later manual acceptance with the bundled seed.

For a reviewed repository update, commit the exact capture artifact/candidate/publication hashes and editorial metadata to `data/catalog/operator-directory-review.json` on a review branch. The review builder materializes only those bytes, validates them, runs all checks and commits the generated directory plus standalone with a branch-head lease. The source publication remains checked in and usable after Actions artifacts expire. The weekly candidate workflow and background source monitor never approve data automatically.
