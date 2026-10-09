# Touch, source geometry inspection and protected hosting — 9 October 2026

Continues main `a9bf37ce972d9d95c84d651be7ae15cd34151ab7` after rechecking
PRs #20/#21, main CI, archive hashes, the ledger/acquisition boundary and all
six approved visual references. The [initial audit](2026-10-09-continuation-audit.md)
records actual gaps before implementation.

## Implemented behavior

- Shared pointer capture, two-finger pinch/translation and cancellation for
  globe/regional maps and sourced facility scenes. Mercator zoom and pan keep
  the geographic cursor anchor; 3D zoom keeps its projected anchor after orbit
  and panning. Keyboard Shift-arrows pan and Home resets.
- Real rendered building/area hit testing, painter-order selection and an
  accessible source-feature selector. Context bounds fit nearby mapped geometry.
  Selection retains the camera and has a shareable inspected-feature URL.
  The original dossier stays labeled as the anchored record; the inspector
  displays the chosen feature's geometry source, attributes and export.
  Proximity asserts neither common ownership nor campus membership.
- Searchable Nordic primary-source leads for FIN05, DEN01 and NOR01. Sources
  P23–P27 bring the primary source count from 22 to 27 and the candidate count
  from five to eight. Planned IT, gross, secured and site/campus power retain
  native scopes, states, inequalities, reporting dates and individual citations.
  The DEN01 milestone discrepancy remains visible. Null coordinates and operating
  IT load remain null. Source Back retains the query; cited JSON exports retain
  supporting sources. The backend rejects malformed candidate measurements.
- Validated `--root-path /compute`, prefix-correct publication/API bootstrap,
  private cache policy for every response, and an inline favicon. No forwarded
  header can redefine the deployment path. Auth covers the whole prefix in the
  [prepared Nginx configuration](../../deploy/nginx-compute.conf).
- Persistent user-service units, bounded service resources, a daily backup timer,
  and an administrator installer that preserves other Nginx routes. Backups use
  committed SQLite WAL state and exactly its referenced immutable captures,
  verify body hashes, and publish only completed snapshots. A private state
  directory stays outside releases and the web root.

## Fresh validation

**216/216 backend tests and 778/778 application/data assertions passed locally.**
The 77 new browser checks use actual HTTP hosted and standalone builds plus a
temporary Basic Auth proxy below `/compute/` backed by SQLite. Real CDP touch
events check desktop/mobile pinch anchoring and canceled pointer capture.
Anonymous requests to app, assets, API, original report and offline build return
401 through that proxy. Browser requests stay inside the protected prefix.

The remaining suites verify all six scales, every archive/entity dossier,
quantities/history, acquisition consoles, identities, global geography, both
publisher collections, camera/history continuity, mobile widths, service failures,
no unexpected browser requests and no uncaught JavaScript exceptions.
[Per-suite results](evidence/2026-10-09/qa-summary.json) distinguish actual HTTP
from the existing intercepted/embedded functional suite. Mock sources and
temporary authentication are test fixtures; they are not production research.

All JavaScript syntax checks and Python compilation pass. Repeated standalone
rebuilds are byte-identical, SHA-256
`4a43e39d186207de21b29f40cc55996aa0115220e1fa03404ad5f703137a5c09`
(22.89 MiB). All eight original research files remain hash-identical, and all
six canonical references match their manifest.

The initial concurrent local run exceeded the coding session's 128-thread quota.
The permanent suites were rerun sequentially in bounded user services. The
catalog startup check now waits for rendered clusters rather than assuming
150 ms; original export checks explicitly select the dossier's export button
alongside the new inspector export. These corrections preserve their actual
behavioral assertions. Existing tracked scratch screenshots/reports were not
replaced by unrelated temporary outputs.

## Visual evidence and limits

The six fresh scale screenshots were inspected against the approved references.
The navy/serif/mint typography, central geographic view, source cards and right
rail remain coherent. Real scene selection adds useful inspection without
copying mockup infrastructure. The geometry inspector fits 320/390 px; longer
dossiers stack their source and research cards vertically.

Four representative actual-HTTP captures and their hashes are retained in
[the evidence directory](evidence/2026-10-09/screenshots.json). These are local
browser/proxy evidence, not proof of production authentication. Complete browser
outputs are reproducible with the checked-in QA scripts and preserved by CI.

Coverage remains 5,265 overlapping OSM features (1,908 Europe), 253 Equinix
codes, 261 Digital Realty publisher entries and 79 original project dossiers.
Current observations/attributes/relationships remain 40/35/21. This slice does
not establish a deduplicated global census or operating MW for Nordic leads.
Only four map features have independent operator specification matches.
Publisher bulk reuse permissions remain unresolved as documented in the
[research note](../research/2026-10-09-additional-operator-sources.md).

Production deployment is the final step and requires the host administrator to
apply Nginx. `/compute/` was still 404 during pre-deployment verification;
this checkpoint does not assert that the production route is live. The existing
user manager has lingering enabled. The host had about 0.9 GiB free before release
packaging: monitor storage, and retain off-host backups before unbounded capture
or backup history fills it. No unrelated files were deleted.
See [deployment and recovery](../protected-deployment.md) for the exact units,
private state, authentication and recovery procedures.
