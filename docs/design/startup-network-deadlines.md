# Bounded hosted startup and terminal recovery

The deployed backend is healthy, but hosted startup waits for all initial data and
script requests without a deadline. A pending request can leave the opening screen
indefinitely. Optional monitor/publication polling also previously started during
module registration; the designed single startup boundary already corrects that.

Bound each initial live API data request to eight seconds. On expiry, use the
existing independently hash-pinned bundled-data fallback and its named snapshot
warning. Do not invent healthy service state or relabel a bundled publication as
fresh. Bound static data and styles to30seconds and each script load to20seconds. Load the two schemas through the same deadline-controlled chain before validating data. Preload styles without blocking the parser, then await their integrity-checked stylesheet load. A small inline opening style keeps the loading state readable before the complete stylesheet set arrives.
These limits describe stalled I/O, not a timer that marks an unfinished app ready.

Matching-asset or static/script timeout failure is terminal for that boot attempt.
Keep page composition deferred, do not publish ready markers or begin optional
polling, and show the accessible existing error/reload surface. Late script arrival
must not compose an incomplete page or dismiss that failure. A real reload starts
a fresh attempt. Normal startup still routes once and preserves requested scope.

Verify live-API delay produces the cited dated fallback and usable maps; static
and script stalls produce named failure/reload; late completion cannot turn a
failed attempt into ready; normal hosted and standalone startup, source/camera
navigation and integrity remain. Use actual bundled data with network interception
only for the declared outage cases. No dummy data or relaxed integrity checks.

Authenticated public acceptance uses a newly generated dedicated Atlas login,
never stored user credentials. The existing auth file is Atlas-only but root-owned;
installation requires an available administrator. Keep anonymous routes protected.
Schema preloads retain native hash-pinned HTML discovery without parser blocking.
Their executable load still uses the controlled20-second deadline and the same
release integrity pin. This preserves early transfer and bounded execution.
The authenticated public cold world took about11 seconds under the unchanged
CPU cap, while same-document campus navigation took about1 second. Preload the
initial module bytes together with native integrity pins so transfer can overlap.
Execution remains ordered and deadline-controlled, with one final composition.
Generate preloads from the declared loadScript calls, using the same source hashes
and asset version. Retain all existing source/integrity gates and compare normal
startup in a capped browser; preloading never authorizes partial readiness.
