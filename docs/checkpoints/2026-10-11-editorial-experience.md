# Design-led editorial experience

The user rejected the deployed workspace as still far from the approved mockups and requested a complete design before implementation. [Design PR #28](https://github.com/Untitled1-Agent/compute-atlas/pull/28) captures three structurally different layouts, nineteen manual browser captures and the missing-feature specification. Its prototype remains outside main. The production baseline is A — Editorial atlas.

The implementation changes the actual journey:

- Six primary destinations with secondary tools grouped below; geographic breadcrumbs follow the selected project's real scope.
- A dominant globe/map, adjacent editorial rail, four legible research metrics, and compact scale controls inside the canvas.
- Marker clicks inspect a project or geographic cluster while retaining scale and camera. Cluster membership is explicit; entering the next scale is a separate action.
- An explicitly selected project remains identifiable when refinements exclude it. Removable chips restore the filtered scope.
- Campus topics replace content beneath the same hero: power, technical design, timeline, counterparties, financing, and sources. URL reload and keyboard navigation retain the topic. Dates and evidence boundaries are unchanged.
- Phase selections retain their source identity and shareable URL. Reading/closing a source restores that context.
- A separate three-project comparison includes dated independent estimates, source-reported scopes, roles, citations, removal and cited dossier export. It persists with private browser research; company comparison remains separate.
- Campus source and note sections sit below the map. Original dossiers, report library, operator directories, financial models, acquisition monitor and the evidence revision desk remain reachable.

The phase hero is explicitly an evidence diagram. Neither the mockups nor the display creates a project/building match, actual height, imagery license or inferred IT power. The existing mapped-feature explorer remains available through the Locations collection.

The wider design remains open: licensed dated imagery, reviewed project/feature identities and infrastructure layers; complete inventory reconciliation; viewport-scoped paginated records; a compact mobile selection sheet; overlay/camera sharing; and more complete source-acquisition coverage. This release must not close issue #2 or claim full mockup parity.

## Acceptance

`qa/editorial.py` exercises both hosted and standalone entrypoints through topic selection/reload, phase/source return, keyboard navigation, shelf feedback, comparison/export/removal/persistence, excluded-selection recovery and 390/320-pixel layouts. Existing six-scale, workspace, geography, research, source, service and archive suites remain required. Changed assertions reflect the intentional click-to-inspect and inline-topic behaviors, rather than accepting the old automatic drilldown/drawer flow.

CI runs the broad regression remotely. Local browsers remain serial in an Atlas-only unit capped at 50% CPU, 640 MiB and 96 tasks. Live-candidate, manual screenshot review, exact-head CI and deployed acceptance are mandatory before reporting deployment. Daily backups remain disabled and no rollback/snapshot is created under the user's instruction.
