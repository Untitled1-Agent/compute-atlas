# Geographic canvas checkpoint

Design committed first: `85940d5` specifies continuous geographic paths, projection
seams, independent local road sources and matched-release loading. The next campus
interaction contract is in `docs/design/campus-feature-selection.md`; its physical
identity/phase changes are not included in this implementation.

## Resulting behavior

- Flat-map roads retain crossing segments with offscreen endpoints. Nearby
  longitude copies preserve genuine dateline crossings while projection seams
  and globe horizons still split; broken paths cannot become invented filled areas.
- Native electricity context stays visible/inspectable for crossing lines and
  enclosing polygons. Empty in-capture views and outside-coverage views differ.
- One already captured OSM response supplies 36 local road ways, independent of
  the 38 electricity features and research/catalog inventories. Original geometry,
  native names/access tags, edits, history, query/hash/license and export remain.
- Local roads draw beneath research and roof selection. Quiet globe views retain
  their existing hierarchy. Road-name labels use source tags and avoid duplicates,
  controls, research markers and neighboring labels. Attribution survives when
  community location/electricity layers are disabled.
- Hosted release identity includes source assets. Scripts/styles/static JSON use
  browser integrity checks; a stale page receiving changed assets offers explicit
  reload recovery. Live evidence APIs retain their independent publication path.
  The standalone remains self-contained. Source timestamps are readable UTC while
  cited exports retain exact precision.

## Verification contract

Targeted source/numerical tests cover original geometry, private access, malformed
coordinates, zero/parallel segments, offscreen crossings, enclosing areas,
dateline/horizon splitting and source-only release identity. The geographic browser
suite verifies actual native ways/areas, source/history/export and camera return,
shared road state, 1366px short desktop, 768px tablet, 320/390px phones and changed
JSON/JavaScript/CSS recovery. Both entrypoints are required.

Before merge: exact-head live candidate, all six scale and source/phone/tablet
manual visual review, green full CI/review-build/source bundle. After activation:
repeat deployed acceptance, preserve original attachments and accepted evidence,
then remove only the superseded Atlas release/captures. The full mockup issue
remains open for current imagery, complete buildings, reviewed phase/utility
relationships, broader fiber/utility coverage and inventory reconciliation.
