# Checkpoint — publisher maps and cursor-anchored facility zoom

Starting main: `7d2871833ea4260c4d10a1df632c08c6b5e427db` (PR #20), exact tree `a67372907144e36f72216476f162a7639cb4ec16`. PR #20 independent CI `37990699404` passed all steps. The downloaded review-build source matched all 151 tracked files, with 191 backend tests and 603 application assertions.

This next slice adds the separate Digital Realty publisher-pin map, source collection switcher, Europe/EMEA filters, source-geography and compound-title warnings, source-linked nearby geometry inspection, deep links, cited exports, and service fallback. It refines map/rail layout so the world summary cards fit the desktop viewport and scopes specification recommendations to the selected geography. The six committed mockups remain design references only.

Facility wheel zoom now keeps a projected point fixed under the pointer after orbit/pan. Tiny wheel deltas, line/page input modes, keyboard alternatives and control-wheel behavior are tested. The primary map never turns a point into a synthetic building or combines its denominator with OSM features or historical capacity.

Local browser validation: the dedicated publisher suite passed 39/39 embedded assertions; old catalog and operator suites passed 35/35 and 25/25 embedded assertions. Those are not HTTP tests. The permanent workflows run fresh real hosted, standalone and SQL-backed HTTP tests, including publication failure and pending/accepted states, before merge. Do not represent local fallback tests as server validation.

Recovery: see `docs/publisher-maps.md`, `docs/research/2026-10-09-digital-realty.md` and the accepted projection/receipt under `data/catalog/`. Rebuild with `python src/build.py`; run `python -m server serve` for the persistent source service. No new public persistent deployment has been created. Near-complete global operating coverage is still not established.
