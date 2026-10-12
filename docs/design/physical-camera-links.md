# Physical camera share continuity

Aerial camera pitch is π/2. Five-decimal URL serialization produces 1.5708,
slightly above π/2; the strict reader rejects the application's own share link.
Reload consequently loses Aerial zoom and pan. Oblique views do not expose this.

Accept an upper pitch rounding tolerance of half the serialization quantum
(0.000005 radians), then clamp to π/2. Keep finite-value, count, zoom, pan and
orientation bounds. Do not expand the physical camera's usable pitch range.
Apply the same rule to the component camera format with explicit image focus.

Verify an actual Aerial zoom and keyboard pan, share/reload through both hosted
and standalone entrypoints, and compare restored camera state to the serialized
values. The test must use a changed camera rather than the default Aerial view.
Also verify the canonical angle round trip and rejection outside the tolerance.
