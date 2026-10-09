# Checkpoint — additional primary directory

Base main: `79cdb78be003cf906d4acfa060f0c3377287094d`, verified tree `be2f92af84149439a36918d6a4dfe199708ccec6`.

This slice adds a second complete captured operator directory (Digital Realty, 261 entries), a fail-closed public-page parser, per-publisher immutable directory heads, publisher-scoped read-only APIs, weekly candidate capture, and hash-pinned materialization. Equinix stays at its own independent accepted head; old `/api/operators/*` calls still default to Equinix. `?publisher=digital-realty` chooses the new directory. No source changes auto-publish.

Recovery: read the research note and the committed receipt. The review builder materializes only the exact accepted factual projection and runs all suites before committing the generated directory/standalone. No temporary code transport or raw-source probe workflow is part of this slice. The earlier raw-source research branch is not a publication.

Local result: 191 backend tests passed, including 23 new Digital Realty tests and 29 existing directory tests. The full local run used the installed html5lib parser via the vendored package path. Full independent CI is required before merge; local Chromium HTTP navigation is blocked. Do not reuse older test counts as validation of this head.

Next slice: expose the additional publisher in the UI, flag raw source geography anomalies, show publisher pins as a separate non-additive map layer, keep community-outline 3D clearly separate, refine the viewport layout and test pointer-anchored scene zoom.
