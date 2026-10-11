# Startup rendering and bounded live acceptance

Design contract before the startup correction, 11 October 2026.

Exact-head live testing found intermittent reload timeouts under the shared VPS's
CPU/RAM caps. Isolated hosted and standalone diagnostics completed with correct
state and no JavaScript or memory-pressure errors. The hosted CPU profile showed
intermediate geographic maps drawing while successive modules were still loading,
alongside repeated locale formatter construction. Waiting longer does not remove
that unnecessary work.

Keep module registration, source validation and route parsing intact. Defer map
animation and drawing while the hosted loader installs modules. After the last
module, clear the loading flag and mark the current map dirty so it draws the
complete source/selection/layer state. Use the same boundary for the synchronous
standalone; failures clear the flag and retain the existing boot error recovery.
Do not create a background animation or skip any source/ready-state assertion.

Cache the English number formatter by requested precision. Preserve the current
handling of missing/non-finite quantities, decimal digits and units. This changes
formatting work, not accepted values or measurement boundaries.

Verify cold load and disabled-layer reload through both entrypoints, complete
ready state, retained camera/selection, cited quantities and unchanged screenshots.
Measure under the existing 640 MiB, zero-swap, 50% CPU browser cap. Restart the
exact-head live/manual and remote regression gates before merging.

The first focused run preserved formatting, camera, layers and selection, but a
standalone reload still took 240 seconds. Deferring canvas frames alone is not
sufficient: module registration calls the page renderer repeatedly. Extend the
boundary to each page-rendering entry point. Route and module state still register
in order; page composition and map construction wait for the completed registry.
After clearing the boundary, invoke the final decorated renderer once. Explicit
catalog, operator, publisher and source routes must retain their existing state
and drawers. Verify these routes as well as geographic and physical startup.

Begin optional monitor/publication polling after the completed render boundary,
so their eight-second network deadlines do not run during module registration.
Emit one ready event from both entrypoints; a service-client loaded without a boot
boundary retains immediate polling. Keep genuine network errors, dated fallback,
manual retries and the existing five-minute visible-page refresh behavior.

A direct archival project dossier route must also work when retained scale state
chooses a physical scene. Opening the dossier only requests geographic camera
movement from renderers that support it; physical scene cameras remain intact.
Include direct dossier entry/reload in the physical regression journey.

The direct dossier reload exposed another intermediate composition path: route
registration repeatedly opens and extends the archival drawer before the final
module. Defer initial route execution as well as page rendering. Register all
route handlers normally, then invoke the final route handler once after clearing
the bootstrap boundary. It parses the original route, composes the matching page
and opens the requested drawer with the complete source registry. Empty-entry
default landscape behavior, later hash navigation and route validation remain.

Publish route-dependent ready markers only after that initial route completes.
Remote testing caught the hosted deep-link check observing the pre-route state
between the last module's ready marker and the loader's final route callback.
Keep individual-module readiness behavior for use without a bootstrap boundary;
both full entrypoints release the complete ready-marker set after final routing,
then emit the service-start event. Readiness must describe the rendered route.
