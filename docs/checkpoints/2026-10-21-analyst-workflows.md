# Complete analyst workflows — 21 October 2026

The approved experience requires a connected research session, including failure
and return paths. This change completes the following workflows in both hosted
and standalone entrypoints:

- Search for and select up to three projects directly in comparison. Inspect
  independently dated estimates, all project-specific source power boundaries,
  counterparties, technical claims, development milestones and financing.
  Remove columns, follow a source and return, and export cited dossiers.
  Comparison exports omit private notes unless explicitly requested.
- Compare an accepted claim with its exact recorded predecessor. Changed fields,
  native quantities, dates, qualifications, source locators and review decisions
  remain explicit. Export both cited revisions without adding their quantities.
  Missing predecessors are identified rather than reconstructed.
- Copy or download primary-source citations. Clipboard denial leaves selected
  text and a working download alternative.
- Save companies alongside projects and physical source features. Company notes
  link to company dossiers. Session import retains project, company, mapped
  location and unavailable-record notes; malformed fields cannot break startup.
- Browser write failure immediately updates note status and exposes a persistent
  session export action. The current work remains recoverable in memory.
- Refine research by snapshot, target or missing estimates; combine with existing
  country, company, evidence and text filters. Share/reload and removable chips
  preserve the estimate filter. These are estimate categories, not live statuses.
- Start the five-stop tour from any research scale and return to the starting
  exploration URL on completion or early exit.

## Verification

`qa/analyst.py` exercises 62 assertions over both HTTP entrypoints, including
320/390px comparison and revision layouts, three-project limits, private export
choice, exact revision/source pairing, company notes, session transfer/reload,
clipboard refusal, storage write failure, filters and all tour stops.
`qa/editorial.py` passes 62 assertions; desktop world/campus/facility and mobile
comparison/revision captures were manually inspected. JavaScript syntax and
build synchronization are checked. Full remote CI remains the merge gate.

## App acceptance and external dependencies

The application includes the six research scales, independent geographic
catalog, company/contract/investment views, original report/workbook library,
source operations, local research shelf and portable exports. Existing suites
exercise these with the new workflow regressions on every pull request.

This change does not claim new source acquisition or current campus inventory.
The historical imagery, interpreted roofs, independent infrastructure features
and source-reported phase disclosures preserve their separate identities.
Current licensed imagery, complete buildings and reviewed phase/circuit links
remain research deliverables under issue #2. Network access to the relevant
publishers is saved in the cloud environment draft, pending environment review
and publication. No invented geometry or mockup quantities fill these gaps.

The production origin responds with the expected HTTP 401 challenge. This cloud
checkout has no configured deployment-host connection; merging and checking CI
are distinct from installing a release and authenticating its public UI.
