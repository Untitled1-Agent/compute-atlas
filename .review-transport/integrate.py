"""Apply the small reviewed integration edits; final source hashes are verified by CI."""
from pathlib import Path

def edit(name, changes):
    p=Path(name); text=p.read_text()
    for old,new in changes:
        assert text.count(old)==1,(name,old[:80],text.count(old))
        text=text.replace(old,new)
    p.write_text(text)

edit('src/zoom-explorer.js',[
    ("+fmt(o.value):'Not quantified';}","+o.value.toLocaleString('en-US',{maximumFractionDigits:12}):'Not quantified';}"),
    ('${spatialStageStrip(level)}${atlasFilterbar()}', '''<div class="atlas-navigation-row">${spatialStageStrip(level)}<details class="atlas-filter-panel" ${state.spatialFiltersOpen?'open':''}><summary class="atlas-filter-toggle">Refine ${scope.sites.length} ${scope.sites.length===1?'project':'projects'}</summary>${atlasFilterbar()}</details><button class="atlas-monitor-launch" data-atlas-action="monitor" aria-label="Source monitor and review queue" title="Source monitor and review queue">▤<span class="sr-only" id="atlas-monitor-label">${globalThis.ATLAS_SERVICE?'Source monitor connecting…':'Source-cited · offline ready'}</span></button></div>'''),
    ('''<button class="atlas-monitor-badge" data-atlas-action="monitor"><i></i><span id="atlas-monitor-label">${globalThis.ATLAS_SERVICE?'Source monitor connecting…':'Source-cited · offline ready'}</span></button>''',''),
    ("download(id+'-cited-dossier.json',{publication_date:ATLAS_PRIMARY.published_at,archive:s,primary_observations:primaryObservations(s),primary_facts:primaryFacts(s),primary_relationships:primaryRelationships(s),primary_sources:primarySourceIds(s).map(primarySource),private_note:saved.notes[id]||'',policy:ATLAS_PRIMARY.policy})", "download(id+'-cited-dossier.json',atlasCitedDossier(s))"),
    ("${atlasRow('Coordinate precision',esc(s.coordinate_precision||'Not mapped'))}", "${atlasRow('Coordinate precision',esc(s.coordinate_precision||'Not mapped'))}"+'''<button class="atlas-evidence-link" data-atlas-action="evidence-desk" data-id="${esc(s.id)}">All quantities, attributes & revision history <span>↗</span></button>'''),
    ('''<p class="atlas-card-footnote">Review date ${esc(ATLAS_PRIMARY.published_at||D.meta.built)}''', '''<button class="atlas-evidence-link" data-atlas-action="evidence-desk" data-id="${esc(s.id)}">Open the evidence desk <span>↗</span></button><p class="atlas-card-footnote">Review date ${esc(ATLAS_PRIMARY.published_at||D.meta.built)}''')
])
edit('index.html',[
    ('<link rel="stylesheet" href="src/zoom-explorer.css">','<link rel="stylesheet" href="src/zoom-explorer.css">\n<link rel="stylesheet" href="src/evidence-desk.css">'),
    (".then(()=>loadScript('src/service-client.js'))",".then(()=>loadScript('src/evidence-desk.js'))\n     .then(()=>loadScript('src/service-client.js'))")
])
edit('src/build.py',[
    ("'src/zoom-explorer.css')","'src/zoom-explorer.css','src/evidence-desk.css')"),
    ("'src/zoom-explorer.js','src/service-client.js'","'src/zoom-explorer.js','src/evidence-desk.js','src/service-client.js'")
])
edit('qa/zoom-explorer.py',[("            page.locator('#atlas-country-filter').select_option('China')", "            page.locator('.atlas-filter-toggle').click()\n            check(entry + ' filter panel opens accessibly', page.locator('.atlas-filter-panel').get_attribute('open') is not None)\n            page.locator('#atlas-country-filter').select_option('China')")])
needle="            page.set_viewport_size({'width':390,'height':844})"
edit('qa/service.py',[(needle,Path('.review-transport/service-test.txt').read_text()+needle)])
# The permanent CI workflow was updated through the authorized GitHub connector.
# Do not request workflow write permission from the source-build runner.
p=Path('src/service-client.js');p.write_text(p.read_text()+Path('.review-transport/publication-client.js').read_text())
p=Path('docs/evidence-service.md');p.write_text(p.read_text()+Path('.review-transport/evidence-docs.md').read_text())
