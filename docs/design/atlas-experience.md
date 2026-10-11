# Compute Atlas experience design

Design proposal, 11 October 2026. The six approved references define the visual direction. This proposal specifies the complete experience before implementation. The prototype is kept on `prototype/atlas-experience-design`; production remains at `e3c635f`.

[Visual review and three alternatives](https://github.com/Untitled1-Agent/compute-atlas/pull/28). The recommendation is A; the next implementation follows its hierarchy and interaction model. The prototype itself remains outside main.

## Product purpose

An analyst should be able to move from a geographic pattern to a named project, inspect what a power number means, identify the counterparties, and open the original evidence without losing their place. An investor should be able to connect that project to dated company financial context while preserving the difference between a site estimate, company spending, a lease obligation and backlog.

The current app exposes much of the underlying research, but its screens do not form that journey. A world view, a local project selection, a campus map and a phase inspector need distinct structures. A successful redesign makes the next useful action obvious at every scale.

## Visual direction and layout alternatives

**A — Editorial atlas, recommended.** The strongest match to the approved references: a narrow persistent sidebar, a quiet breadcrumb/search bar, a serif headline, a dominant map, a three-part editorial or selected-project rail, and four metrics along the map’s lower edge. The map and rail change purpose by scale. Detailed evidence appears below or in a drawer.

**B — Research workbench.** An icon sidebar frees horizontal space. A full-width map leads into an inspection strip and a visible record table. It favors repeated filtering and comparison over the narrative of the references. This is a possible analyst mode, rather than the default landing.

**C — Immersive explorer.** A full-width map occupies the page, with a floating inspector and metrics on the canvas. It favors spatial exploration; the evidence drawer carries longer reading. It is a possible expanded-map mode. Dense floating content may obscure geography at smaller widths.

The prototype switches these layouts on one route using `?variant=A`, `B` or `C`. Left/right arrows in the review bar cycle them. The variants intentionally differ in structure. All use the same existing research and geography.

## Shared design system

At a 1440-pixel desktop width, the editorial layout reserves about 200 pixels for navigation, 30 pixels of content inset, 300 pixels for the analysis rail, and a 28-pixel map/rail gap. The map receives the remaining width. Typography uses an editorial serif for headlines and major quantities, a plain sans serif for controls and prose, and small monospace text for source IDs and coordinate context.

The palette stays near the references: deep navy backgrounds, restrained blue cartography, pale text, muted blue-gray secondary text, mint for active selection and primary actions, blue for imported estimates, and violet for native-unit/contract records. Color is accompanied by labels or shapes. Borders define information groups; rounded dashboard cards should not dominate the canvas or editorial rail.

The visual hierarchy is: geographic identity → map/selection → the quantity and its boundary → next action → provenance. Every metric has a legible title, value, date/basis and relevant uncertainty. An unavailable metric occupies its designed slot with a specific reason, rather than silently disappearing or becoming zero.

The top bar contains geographic breadcrumbs, global search, publication date and help. The sidebar contains six primary destinations: Landscape, Facility directory, Company universe, Contracts & connections, Investment lens and Research library. Guided exploration, comparison, research shelf and source operations are secondary utilities. Six-scale controls belong to the map, with the current scale and selection visible in the breadcrumb.

## The six screens

| Scale | Main canvas | Information rail | Lower content | Primary next action |
|---|---|---|---|---|
| World | Rotatable globe; luminous geographic clusters; small source locations; sparse labels | Global takeaway, projected buildout, companies behind the footprint | Dated partial IT estimate, named projects, modeled targets, source-review coverage | Choose a region or cluster |
| Continent | Framed continental system; meaningful North America/Europe/Asia presets | Regional thesis, major clusters, coverage and counterparties | Same measurement framework, recomputed for the selected scope | Choose a market or region |
| Region | Flat geographic map; source anchors, cities, roads/boundaries and requested overlays | Selected project/cluster, disclosed power and development, other local projects | Scope metrics and accessible filtered records | Inspect a project, compare, or enter its metro |
| Metro | Local facilities with restrained context and named places | Selected campus, snapshot/target distinction, local constraints, evidence confidence | Local footprint metrics; selected records | Enter the selected campus |
| Campus | Spatial hero with sourced imagery/footprints when available; explicitly bounded fallback otherwise | Project identity, dated power scope, counterparties and review needs | Power phases, attributes, original documents, notes | Select a source feature or disclosed phase |
| Facility | Selected source feature in spatial context, or selected phase in its evidence diagram | Persistent selected-feature/phase inspector, key takeaways, related roles | Technical attributes, independent power scopes, cited claims and confidence | Open a claim/source, compare, export or navigate back |

### World and continent

The globe should be the visual center of the page. Cluster labels name the geography and disclose member count/basis; a leading project name should not stand in for a market. Small location points remain subordinate to quantified research markers. Capacity size, evidence basis and development status are distinct dimensions, so one overloaded color cannot imply all three.

Hover reveals a concise cluster summary. A click selects a cluster and exposes its membership; the panel provides an explicit action to enter the next scale. Geographic presets move the camera and scope together. The continent view needs distinct Atlantic and Asia framing, rather than a slightly magnified world globe. Cross-region relationships are shown only when the source supports the link, with the source available from the line or panel.

The right rail uses three short editorial sections, each with a concrete action. The four lower metrics are useful research measurements; sample market-wide totals and growth percentages from the mockups are not populated without an appropriate dataset. Metric explanations open in place or in a drawer, instead of filling the hero with methodological paragraphs.

### Region and metro

Clicking a marker selects it while retaining the camera and viewport. Selection updates the rail immediately. Entering the next scale is a separate explicit action, avoiding the current tendency to jump away from the clicked location. A cluster can expose its member list without treating each member as an additional unique facility.

The selected rail leads with identity, status, two separately labeled dated power scopes, and the next useful action. It then explains the local development evidence and relevant counterparties. Geographic map layers are controlled from a compact Layers panel: capacity research, community locations, labels, roads/boundaries, reviewed electricity infrastructure, and reviewed fiber/connectivity. Each layer shows its source, vintage and coverage. Unsupported infrastructure layers explain what is absent; proximity never becomes a service relationship.

The view offers selection-based and viewport-based record scopes, clearly named. Panning does not silently discard the selection. An accessible, paginated table uses the same filter state as the map and supports sorting, export and comparison. Country, company, status, evidence and text filters intersect. Active refinements remain visible as removable chips.

### Campus

Campus has its own header: identity, location, source-confirmed roles, save/export actions and topic navigation. Overview, Power & phases, Technical design, Timeline, Counterparties and Sources & evidence change the content within the campus screen. The map and selection remain present; topic buttons should not all eject the user into a generic long dossier.

The spatial hero supports plan, 3D and sourced imagery views. A selected outline uses a luminous mint boundary; related source features remain visually subordinate. Imagery displays capture date and attribution. Community footprints and illustrative heights remain explicitly identified. Building, phase and parcel selections use their own IDs, with a reviewed relationship required before one is presented as another.

When geometry is unavailable, the same hero slot contains an interactive evidence diagram. Dated power scopes are selectable nodes; they retain citation and scope. It provides useful phase investigation, without putting a bar chart in place of a campus map and implying that the map requirement is complete. A geometry review action explains the missing source work and the next acquisition step.

Below the hero, the power ladder and attribute sheet form one row; sources and research notes form the next. A selected source feature’s inspector belongs beside the hero. Project research remains discoverable, progressively disclosed and searchable.

### Facility or selected phase

The selected feature or phase has a persistent inspector: exact identity, parent context, status, dates, a dominant correctly bounded quantity where available, source reference, key takeaways and counterparty roles. Clicking geometry updates this inspector without resetting the camera. Clicking a disclosed phase selects its claim and retains the campus context. These are distinct selection types.

The inspector exposes export and comparison actions. Power and technical facts below keep their native units. Confidence describes the evidence and location precision; a decorative row of dots does not establish that a source is correct. The full dossier offers claim search, locators, revisions, disagreements and open questions.

## Connected feature design

| Feature | Designed behavior | Prototype coverage | Production requirement |
|---|---|---|---|
| Global discovery | Search facilities, companies, sources, claims, reports and attachments; show result type and matched text | Real project/company search and selection | Existing comprehensive search integrated into new shell; keyboard result navigation |
| Geographic navigation | Breadcrumbs, six scales, presets, smooth camera movement, restore Back/Forward | All six screens, query URLs and browser history | Preserve selection, filter, phase and camera together; avoid competing route owners |
| Selection | Inspect a marker before diving deeper; retain context | Marker selection, selected rail, explicit campus action | Keyboard map/list parity; cluster membership; viewport scope |
| Filters | Intersect country/company/evidence/status/text; visible removable refinements | Country/company/evidence filtering and empty results | Complete filters, active chips, counts, consistent table/map results |
| Layers | Show source, date, coverage and unavailable reason per layer | Locations, labels, roads; infrastructure requirement shown | Licensed imagery and reviewed electricity/fiber layers where defensible |
| Project topics | Change relevant content while retaining identity and map | Power, technical, chronology, counterparties and evidence | Complete project-specific content and URL/topic restoration |
| Sources | Open cited document, reporting date, retrieval/review state and relevant claims | Source drawer with real document metadata/link | Exact locators, archived originals, revision comparison and accepted evidence history |
| Comparison | Up to three projects; dates and boundaries shown per value | In-memory project selection and comparison drawer | Full comparable attributes, remove controls, export and source links |
| Company context | Reported roles, named footprint, separately dated financial quantities | Company drawer, directory and investment table | Interlinked company/project/contracts views; updated sources separately reviewed |
| Research shelf | Saved identities, notes, questions and comparison sets | Session notes, export and shelf concept | Existing local storage/export connected to new UI; storage-failure state |
| Guided exploration | Short narrative path with a next action and source context | Five-stop navigation | Preserve exploration return point; tour explanations sourced |
| Sources & updates | Publication status, acquisition health, revision review queue | Operations layout and state design | Integrate current monitor; distinguish offline snapshot from running service |
| Export/share | Share the current selection/filter/topic; export cited records and notes | Query URLs and notes export | Exact source-linked record/claim export, citation formats and share feedback |

## State and interaction model

The exploration state has a geographic scale and scope; a camera; a selection with type (`cluster`, `project`, `mapped feature` or `claim`); independent filter state; a dated estimate layer; active map layers; topic; and optional overlay (search, source, dossier, comparison or operations). Selection does not imply a new scale. A change to geography does not rewrite evidence. A topic/drawer does not steal the map’s URL ownership.

Back/Forward restore meaningful navigation and overlays; continuous camera movement replaces camera state without flooding browser history. Share URLs reproduce scope, selection, phase and topic. Closing a source returns to the claim/project and restores keyboard focus. Escape closes the topmost transient surface. Keyboard shortcuts do not intercept text entry or map arrow controls.

The comparison shelf and private research notes have a separate persistence boundary. Prototype interactions are in memory; they do not write evidence or alter the deployed app. Production source acquisition is read-only until an explicit editorial review action accepts a candidate revision.

## Mobile design

At narrow widths, the sidebar becomes a menu and the top bar retains the breadcrumb and search. The headline and introduction reflow intentionally. Map scale controls remain compact and touchable, with layer and scope controls grouped below the caption. Map labels thin out before the map becomes crowded. Legends, controls and coordinate text have reserved areas.

The map leads; four metrics become a two-by-two group. A selected marker opens a compact selection summary, expandable to the full inspector. Editorial analysis follows in reading order. Campus topic navigation scrolls horizontally; the spatial hero remains usable with pinch, drag and reset. The dossier is a full-width sheet. Comparison uses horizontally scrollable columns with sticky project labels. Source/citation targets remain comfortably touchable even when the label is visually small.

The current prototype demonstrates responsive stacked reading and full-width drawers. The production implementation must add the compact mobile selection sheet and complete keyboard/focus behavior; these are explicit design requirements, not inferred from a desktop shrink.

## Required non-happy-path states

1. **No matching projects:** explain the active scope and offer to clear refinements; never imply zero regional capacity.
2. **Selected record excluded by filters:** retain its identity with a clear notice and a restore/reset action.
3. **Unknown/native power:** keep the record visible and open its native source quantities; no invented MW axis.
4. **Missing geometry/imagery:** retain a useful evidence hero with source work and acquisition requirements visible.
5. **Conflicting or superseded evidence:** show separate statements and revision history, with the accepted decision identifiable.
6. **Source unavailable:** preserve the accepted claim and its archived source where available; show retrieval status separately.
7. **Service unavailable:** show the dated bundled publication and its vintage; operations do not appear live.
8. **Offline standalone:** identify the publication as a snapshot, with existing original attachments accessible.
9. **No stored notes/storage unavailable:** provide export and an explicit persistence state.
10. **Loading/error:** preserve shell and scope; show a useful recovery action and avoid presenting stale data as freshly loaded.

## Implementation sequence after design review

1. **Shell and state:** shared design tokens, navigation, geographic identity, one route owner and selected-state model. Keep the current app as the functional source until replacement behavior is verified.
2. **World/continent:** globe framing, geographic cluster identity, marker hierarchy, three-part analysis rail and useful sourced metrics. Verify both Atlantic and Asia views.
3. **Region/metro:** click-to-inspect, persistent local selection, layers, intersecting refinements and synchronized record table.
4. **Campus/facility:** distinct spatial hero, adjacent inspector, inline topics, correct phase/feature selection, power ladder, source/notes layout, explicit geometry fallback.
5. **Connected research:** comprehensive search, comparison, company/counterparty context, source revision drawers, shelf and acquisition operations.
6. **Source acquisition:** reviewed project/feature matches, licensed dated imagery, building-to-phase relationships and infrastructure context. Prioritize the approved example journeys, then expand coverage.
7. **Visual and interaction acceptance:** review every designed state at desktop, short desktop, tablet and phone sizes; verify the actual deployment. Only then close the corresponding gap.

Source acquisition is a workstream with deliverables. Recording the lack of imagery is not completion of the imagery workstream. Conversely, a design reference cannot establish a real parcel, facility count, capacity or source relationship.

## Acceptance contract

The editorial design should match the references in page hierarchy, relative widths, globe/map framing, headline scale, marker light, label density, right-rail composition and lower evidence structure. Compare at equal viewport sizes and review captures side by side; functional assertion totals alone do not establish visual quality.

Each six-scale journey must be coherent: marker → selected panel → next scale → selected project/feature/phase → source → return. Search, refinement, comparison, source history and mobile flows must be reviewed alongside the happy path. A missing-data fallback must remain useful and visibly different from a completed sourced spatial view.

Production acceptance requires no stale asset mixtures, no uncaught errors, working hosted/standalone entrypoints, unchanged original attachments and preserved accepted research. Broad regression runs use remote runners. Local browsers remain serial, low priority and resource-capped. Storage changes are limited to Compute Atlas; daily backups remain disabled under the user's instruction.

## Run the prototype

The throwaway prototype is on `prototype/atlas-experience-design`, not main. Check out that branch before running it.

From the repository: `python -m http.server 8141 --bind 127.0.0.1`.

Open `http://127.0.0.1:8141/src/atlas-design.prototype.html?variant=A&scale=world`.
Use the six scales, map controls, search, filters, comparison and project topics.
The review controls can switch to a mapped facility example or show the current
in-memory state. The prototype is a design artifact, not a completed implementation.
