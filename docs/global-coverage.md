# Source health and global disclosure coverage

The map’s primary-review KPI and **Source coverage & disclosure explorer** open a separate coverage desk. Filter current reviewed quantities by geography, boundary, status and text, inspect their source, or export cited JSON. Native units and nulls remain intact; there is no cross-scope capacity total. Research candidates stay separate from mapped facilities.

The same-origin Python service also exposes a read-only source-health console with successful-fetch and editorial dates, immutable fetch events, retry/outage states, and the acquisition review queue. A static/offline build never claims a worker is running.

Start continuation work from [implementation checkpoints](checkpoints/README.md), not the old pasted handoff. See [global coverage checkpoint](checkpoints/2026-10-05-global-coverage.md) and [candidate source review](research/2026-10-05-google-location-candidates.md). Run `python qa/global-coverage.py` and `python qa/source-health.py` for their permanent real-HTTP suites; `--in-memory` is a labeled local fallback, not a substitute for HTTP CI.
