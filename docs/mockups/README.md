# Approved Compute Atlas visual references

The six user-supplied designs are now stored here as actual 640 × 480 WebP review copies, not broken links. They preserve the layout and color direction. These are reduced-resolution references, not full-resolution originals. See [issue #2](https://github.com/Untitled1-Agent/compute-atlas/issues/2) for the implementation contract. Compare real desktop/mobile browser captures against these images when changing the interface.

**Design only.** Every number, name, date, boundary, road, building, cooling pond, utility line and relationship shown here must be independently sourced before appearing as research. Do not trace invented geometry into the app. Where geometry is unavailable, display a clearly marked evidence schematic. Research quantities retain their original units and measurement boundaries.

## 1. World
Editorial serif headline, large globe, luminous clusters, analytical right rail and bottom KPI cards.

![Global compute view](01-world-global.webp)

## 2. Continent
North America–Europe framing with restrained labels and geographic context. Europe must be discoverable, not hidden by an AI-only source selection.

![Continental view](02-continent-na-europe.webp)

## 3. Region
Regional centers, legible geographic context and a focused information rail.

![Regional view](03-region-east-midwest.webp)

## 4. Metro
Local facilities and independently sourced infrastructure; never infer utility service from a nearby line.

![Metro view](04-metro-chicago-new-carlisle.webp)

## 5. Campus
Map or 3D hero, power phases, attributes, evidence and notes. Community mapped footprints are not cadastral surveys; assumed heights must be labeled.

![Campus view](05-campus-horizon.webp)

## 6. Facility
Strong facility identity, clear evidence and counterparty cards. Orbit, pan and continuous scroll zoom should work without relying on a static rendering.

![Facility view](06-facility-helios.webp)

## Integrity
`sha256.json` fingerprints these exact review copies. `tests/test_references.py` fails if a reference disappears or changes without its manifest. These reference assets are documentation only and are not bundled into the app.
