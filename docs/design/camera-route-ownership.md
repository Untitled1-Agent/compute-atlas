# A delayed camera save belongs to its original route

The installed native-overlay acceptance intermittently lost a malformed physical
return's recovery notice. A state-logging retry passed; the first failure's cause
is not fully established. A separate deterministic reproduction shows an existing
navigation race in both hosted and standalone entries: schedule a camera save,
publish a new route while its parser is queued, and the old camera callback
rewrites the URL with the previous component and selection after 220 ms.

Camera movement should update its current view. A debounced update must never
replace a later requested component, source version, recovery or browser-history
destination. The URL, selected identity, camera and source state belong together.

Three treatments were considered. Checking only whether the map is still alive
is the current behavior and does not protect a pending route. Waiting longer
before navigation cannot establish ownership. Bind each delayed save to the hash
it was scheduled against; if the hash changes, discard that callback. Choose the
third treatment for both physical and geographic camera writers. Existing map
destruction/object guards remain, as do immediate explicit navigation updates.

Test current-route pan/orbit/zoom publishing, a newly requested versioned source
and malformed recovery destination, subsequent parsing, Back/Forward, camera
rounding and source-return identity. Run both real HTTP entrypoints and verify
physical/geographic cases with a deterministic pending-router interval. Compare
records and quantities before/after. No data, source versions, captures, defaults
or rendering treatment changes. Live and manual acceptance precede merge; actual
installed/public checks precede final acceptance.
