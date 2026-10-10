# Continuation audit — 9 October 2026

Verified GitHub main: `a9bf37ce972d9d95c84d651be7ae15cd34151ab7`, tree
`16502eb5f5e01cdd21f99c3e09f089b757ed641f`. PRs #20 and #21 are merged;
main CI run `37996834267` succeeded. The local checkout was still `47c5ea5`;
it was clean and has been recovered onto `feat/protected-compute-deployment`.

All six actual WebP references match `docs/mockups/sha256.json`. All eight
original research hashes and 15 integrity assertions pass. Rebuilding the
22.86 MiB standalone initially produced no diff. The first backend attempt
failed collection because the host lacked `defusedxml`; pinned dependencies
are now installed in an isolated `.venv`. The fresh baseline passed 191 tests. Updated backend/browser results follow
in the implementation checkpoint; historical CI counts are not new validation.

The SQLite-backed application was opened in Chromium over actual HTTP. Fresh
world, Europe, all six semantic scales, source-outline facility and mobile
captures are retained in `/tmp/compute-atlas-evidence/baseline-*.png`. No
uncaught JavaScript exceptions occurred in that capture pass.

| Area | Actual finding and priority |
| --- | --- |
| Geography | 5,265 OSM features, 1,908 in Europe; 3,700 outlines. These overlap, and 5,124 have unspecified lifecycle. Keep these denominators separate from 253 Equinix codes, 261 Digital Realty entries and 79 archive projects. |
| Evidence | 40 current observations, 35 attributes, 21 relationships, 22 primary sources and five unmapped leads. Only four map features have an operator specification review. Additional Nordic sources are documented in the parallel primary-source research note. |
| Identity | Equinix code/operator/country links are proposals. Nearby Digital Realty polygons explicitly carry no identity assertion. There is no reviewed global site census. Do not silently collapse adjacent records. |
| Interaction | Facility scenes implement single-pointer orbit and Shift-pan, but have no pinch gesture or selectable context buildings. The map also tracks only one pointer. Touch interaction is the first implementation priority. |
| Visuals | The navy/serif/mint shell, globe, rail and sourced outlines are real. Facility context is sparse and its geometry selection absent; improve the inspection experience without tracing mockup infrastructure. Mobile facility dossiers are legible but long. |
| Runtime | `/api` is hardcoded in injected bootstrap URLs. A deployment below `/compute` would escape its authenticated path. Add validated deployment-prefix support and test through a real reverse proxy. |
| Security | Static responses currently use `Cache-Control: public`; authenticated deployment must keep all responses private. The service allowlists assets and denies raw captures, Python, ledger and backups. Preserve that boundary. |
| Operations | Immutable claims/captures, WAL, review gates, retries, source health and online backup exist. Persistent hosting and scheduled backups still need to be installed; no new live deployment is claimed. |
| Maintenance | Large compressed functions and layered render/route overrides make extension fragile. Preserve the working architecture, add bounded gesture methods and explicit regression coverage instead of a broad rewrite. |
| Rights | OSM retains ODbL attribution. Operator publications do not establish an open reuse grant; the catalog README's older “no commercial directory is scraped” statement needs correction. Link-only research leads must not become bulk source-text copies. |
| Assets | Canonical references, originals, source captures and manifests are present. No relevant additional uploaded attachments were found in the task paths. Temporary browser/log artifacts remain outside tracked source. |

Next: implement touch navigation, selectable sourced geometry with an accessible
inspector, useful source-linked Nordic research leads, and deployment-prefix
support. Run the permanent browser/backend checks, rebuild and commit a durable
checkpoint, then deploy at `https://untitled1.cc/compute` behind Basic Auth as
the user's final step.
