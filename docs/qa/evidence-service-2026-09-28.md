# Evidence service validation — 28 September 2026

Tested source commit: `dbc6f9c5b4a70e3b35b1da76d27030aa8f8555df`.
Independent execution: [Actions run 36365746009](https://github.com/Untitled1-Agent/compute-atlas/actions/runs/36365746009).
Artifact: `evidence-service-review`, with exact source ZIP, COMMIT.txt, checksums, JSON results and actual Chromium screenshots. Artifact retention is seven days; these results remain recorded here.

| Suite | Result |
| --- | --- |
| Backend ledger, acquisition and API tests | 39 / 39 |
| Research/archive integrity | 15 / 15 |
| Original functional contracts | 48 / 48 |
| Six-scale explorer, hosted + standalone over HTTP | 103 / 103 |
| Smoke | 15 / 15 |
| Live HTTP audit | 27 / 27 |
| SQL-backed application over HTTP | 14 / 14 |

All JavaScript syntax checks passed. Rebuilding the standalone HTML produced no difference. The non-root Docker image built, started and returned HTTP 200 from its health endpoint.

## Actual acquisition

The worker fetched all nine registered primary sources and two registered feeds successfully (HTTP 200), producing 11 source versions and 29 pending review items. The accepted publication before and after acquisition was byte-identical. These are actual network captures, not test-fixture responses. Acquisition is not automatic publication.

## Visual inspection and remaining fix

Desktop globe and facility screenshots were inspected, including the service-hosted Helios dossier and mobile screenshots. The delivered 133 MW critical-IT value, planned phase and overlapping contracted envelope remain visibly separate. Exact campus geometry is not claimed.

Visual inspection found that a desktop-to-mobile resize can briefly leave the navigation panel covering content: the prior no-overflow assertion did not test occlusion. A separate follow-up will add immediate hidden/inert states and explicit menu/focus regressions. This report is not a claim of pixel-perfect fidelity or a public production deployment.

The earlier run 36365606854 failed at publishing its commit because the Actions token could not modify workflows. No tests ran in that attempt. Authorized workflow edits were then committed separately; the successful run above exercised the resulting source. Both temporary import workflows were subsequently removed.
