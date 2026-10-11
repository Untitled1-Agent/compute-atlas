# Atlas experience review — 11 October 2026

Baseline: `9a9538dc64e1003f9f6666345a0d7b480ad9c200`, the deployed main tree.
Compared the actual loopback application and repository HTTP application against
all six approved references in `docs/mockups/`. Mockup geography and quantities
remain design examples, never research inputs.

## Findings and corrections

| Gap | Correction |
| --- | --- |
| The worldwide default map had no semantic scale control, although the capacity research map did. | Both collections now expose World through Facility. Geographic region/metro buttons focus an actual source feature; campus/facility require explicit feature selection. Campus shows nearby independent source geometry without asserting common ownership. |
| Opening a map record reset the result page; reloading lost camera position and pagination. | Camera, page, filters, selected geometry and campus/facility context are retained in bounded, validated deep links. Returning to results preserves the camera and page. |
| Changing country silently cleared search and geometry type. | Geographic filters intersect with the current text/type filters. Only Reset clears the complete selection. Invalid country and camera parameters fall back safely. |
| Map clusters and labels competed with the legend, particularly on phones. | Coarser world clustering, fewer labels, and a reserved mobile legend region. The heading distinguishes plotted features from matching records. |
| Fixed desktop map heights pushed metrics out of the overview, contrary to the references. | Viewport-aware map sizes, compact navigation, coordinated rail spacing and a visible KPI row. Mobile keeps a separate layout and scrollable navigation. |
| The campus screen repeated large model panels while recent primary research appeared much farther down. | Compact evidence schematic, direct power/design/timeline/counterparty/investment shortcuts, and recent dated disclosures immediately alongside the existing campus material. Shortcuts open and focus the original cited claims. |
| Expanded catalog maps lacked Escape dismissal and accurately labeled controls. | Escape closes the map and restores focus; label and expand controls expose their state. |
| The application advertised readiness before the last research modules had loaded. | `atlas-ready` is emitted after the final research module initializes. |
| CI caught a delayed camera save replacing an open research drawer's URL; closing drawers also dropped catalog parameters. | Camera persistence now respects drawer and route ownership. Closing by Escape or backdrop restores the complete map bookmark. Both directions have regressions. |

## Evidence boundaries that remain intentional

The 79 historical project dossiers and 5,265 overlapping OSM map features are
independent collections. Similar names or nearby coordinates do not establish
identity. Research campus views therefore retain an explicit evidence schematic
where no reviewed geometry link exists. The geographic collection can display
actual captured source outlines; unknown heights remain optional illustrations.
Neither the mockup's satellite image, its building names nor its utility routes
can be inserted as sourced evidence. Infrastructure, identities and financial
updates require additional source review, not visual inference.

Region/metro labels on the geographic map indicate camera scale, not official
administrative boundaries or a claim of complete market coverage. The plotted
count is separate from filtered collection counts. Capacity totals retain their
existing comparable-IT boundaries and do not absorb the geographic catalog.

## Verification and host limits

`qa/experience.py` exercises hosted and standalone HTTP, filter composition,
selection/back/reload, camera persistence, scale selection, geometry context,
focused project claims, Escape, keyboard navigation, and 320/390px layouts.
The required GitHub workflow runs this alongside all existing regressions.
The final candidate passed **27/27** checks over actual HTTP against an isolated
copy of the live SQLite ledger and the standalone publication. This includes
1440×1000 and 1366×768 KPI visibility, mobile legend/control separation, live
publication loading, real geometry selection and focused primary claims.
The earlier full interaction pass was **50/50**; CI adds the two short-desktop
checks and four drawer-return checks for **56** interaction assertions. See the [live receipt](evidence/2026-10-11/live-acceptance.json),
[world](evidence/2026-10-11/world-desktop.png),
[short desktop](evidence/2026-10-11/world-short-desktop.png), and
[source campus](evidence/2026-10-11/source-campus.png). All six research scales
and 320/390px mobile captures were also inspected locally.

Hosted regression suites now wait for complete application readiness; otherwise
the later operator/research modules can replace a DOM node while an earlier
suite is interacting with it. Final full CI and release receipts are linked from
[PR #26](https://github.com/Untitled1-Agent/compute-atlas/pull/26).

Local browsers run serially at lower CPU priority. Broad regression work runs
on GitHub Actions. Cleanup removed only reproducible Atlas QA screenshots, the
redundant Atlas development environment, and an obsolete Atlas test database;
three obsolete Atlas code releases were subsequently removed, recovering another
72 MiB while retaining the active and previous rollback releases. Production
state, source captures, all backups and other projects were untouched.
