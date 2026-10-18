"""Read-only browser regression checks for the isolated design study."""
import hashlib
import json
import re
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from preview_atlas_design import Handler, document


def main():
    exported = ROOT / 'docs/design/atlas-redesign-review.html'
    assert document() == exported.read_text(), 'Re-export the design study'
    manifest = json.loads((exported.parent / 'review/sha256.json').read_text())
    for name, receipt in manifest.items():
        content = (exported.parent / name).read_bytes()
        assert len(content) == receipt['bytes'], name
        assert hashlib.sha256(content).hexdigest() == receipt['sha256'], name

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{server.server_port}/compute/'
    errors = []
    views = 0
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path='/usr/bin/chromium',
                                         args=['--no-sandbox'])
            page = browser.new_page(viewport={'width': 1366, 'height': 900})
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(base)

            # Choosing a search result must dismiss its modal and expose the
            # selected project, rather than leaving an obsolete blocking drawer.
            page.locator('.topbar [data-panel="search"]').click()
            page.locator('#design-search').fill('Helios')
            page.locator('#search-results [data-project]').click()
            expect(page.get_by_role('dialog')).to_have_count(0)
            expect(page.locator('.selected-card')).to_contain_text('Helios')
            page.locator('.selected-card [data-preview]').click()
            expect(page.locator('.component-line')).to_contain_text('Helios')
            page.locator('.roof-picker [data-feature]').first.click()
            expect(page.locator('.feature-quantity')).to_contain_text('m²')
            page.locator('[data-panel="image"]').first.click()
            expect(page.get_by_role('dialog')).to_contain_text('Not established')
            page.keyboard.press('Escape')
            expect(page.get_by_role('dialog')).to_have_count(0)

            # Applying refinements is another navigation path out of a drawer.
            page.goto(base)
            page.locator('[data-panel="filters"]').click()
            page.locator('#design-filter').fill('Helios')
            page.locator('[data-apply-filter]').click()
            expect(page.get_by_role('dialog')).to_have_count(0)
            assert page.evaluate('scope().length') == 1

            page.goto(base)
            page.locator('[data-regional-entry="Europe"]').click()
            assert page.evaluate('scope().every(s=>region(s)==="Europe")')
            page.reload()
            assert page.evaluate('state.region') == 'Europe'
            page.go_back()
            assert page.evaluate('state.scale') == 'world'

            # An existing native-only record has no snapshot IT estimate. It
            # must not become zero or an invalid numeric quantity.
            native = page.evaluate('DATA.sites.find(s=>s.snapshot?.it_mw==null).id')
            for variant in 'ABC':
                page.goto(base + f'?variant={variant}&scale=campus&site={native}')
                expect(page.locator('body')).not_to_contain_text('NaN')
                expect(page.locator('body')).to_contain_text('Not quantified')
                assert not re.search(r'(?<![\d,])0 MW', page.locator('body').inner_text())
            page.goto(base + f'?scale=campus&site={native}')
            page.locator('.project-tabs [data-topic="energy"]').click()
            expect(page.locator('.detail-content')).to_contain_text('Not quantified')
            page.goto(base + f'?site={native}&inspect=1')
            page.locator('[data-compare-add]').click()
            expect(page.locator('.comparison-table')).to_contain_text('Not quantified')
            expect(page.locator('.comparison-table')).not_to_contain_text('NaN')
            expect(page.locator('.comparison-table')).not_to_contain_text('Not quantified MW')

            for width, height in [(1440, 900), (1366, 768), (1024, 768),
                                  (390, 844), (320, 800)]:
                page.set_viewport_size({'width': width, 'height': height})
                for variant in 'ABC':
                    scales = ['world', 'continent', 'region', 'metro', 'campus',
                              'facility'] if variant == 'A' else ['world']
                    for scale in scales:
                        page.goto(base + f'?variant={variant}&scale={scale}')
                        expect(page.locator('#design-map')).to_be_visible()
                        assert page.evaluate(
                            'document.documentElement.scrollWidth <= innerWidth'
                        ), (variant, scale, width)
                        if variant == 'A' and scale == 'world' and width in [1440, 1366]:
                            bounds = page.locator('.metrics').bounding_box()
                            assert bounds['y'] + bounds['height'] <= height
                        views += 1
            assert not errors, errors
            browser.close()
        print(f'Design review passed: export/hashes, navigation, native power, '
              f'{views} responsive views, no browser errors')
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


if __name__ == '__main__':
    main()
