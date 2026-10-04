# Implementation checkpoints

Start with the newest dated file here and the latest comment on [issue #2](https://github.com/Untitled1-Agent/compute-atlas/issues/2). Do not restart from the original pasted handoff: it predates the evidence service and several merged PRs.

Each checkpoint names its upstream commit, changes, exact test mode, known limitations, and the next runnable step. Code and regression tests belong in the same PR. An open PR is not a pass certificate; inspect the exact head and permanent CI run before merging.

## Recovering an exact tree

The `Reproducible review bundle` workflow archives the tracked tree for PRs. `Build and verify review branches` also preserves a tested source ZIP, commit/tree IDs, SHA-256 manifest and browser artifacts for 14 days. Download the artifact, verify the ZIP against `SHA256SUMS`, and compare the extracted Git tree with `TREE.txt`. Archive files and their checksums must not be regenerated or discarded.

Branches under `review/` can use the build workflow to regenerate the large standalone without uploading an encoded HTML payload. It runs the full test suite before committing **only** `compute_atlas.html`, checks that the branch has not advanced, and never writes main or merges a PR. No temporary importer or encoded transport file is required. Open the PR after the generated commit (or push a normal source/checkpoint commit) so the permanent pull-request CI tests its exact head. Commits made by the workflow token do not themselves start a new workflow.

## Test honesty

The normal QA mode uses real HTTP and Chromium in CI. In restricted browser environments, `qa/zoom-explorer.py`, `qa/evidence-desk.py` and `qa/source-health.py` support `--in-memory`. The source-health mode uses the real temporary SQLite/ASGI API through a test bridge, not browser HTTP. These results are useful local checks, **not** substitutes for the real-HTTP CI runs. Synthetic acquisition fixtures are labeled and never enter the research publication.
