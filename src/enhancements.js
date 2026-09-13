'use strict';
// Compute Atlas v2: evidence-first and investment-grade exploration enhancements.

const atlasFiniteNumber = value => value != null && Number.isFinite(Number(value));
const atlasNumber = value => atlasFiniteNumber(value) ? Number(value) : null;

function evidenceSummary(ss = D.sites) {
  const bucket = review => {
    const xs = ss.filter(s => s.review === review);
    const quantified = xs.filter(s => atlasFiniteNumber(s.snapshot?.it_mw));
    return {
      count: xs.length,
      snapshot: quantified.length,
      mw: quantified.reduce((n, s) => n + Number(s.snapshot.it_mw), 0),
    };
  };
  return {
    reviewed: bucket('reviewed-model'),
    archive: bucket('archive'),
    native: bucket('primary-noncomparable'),
    contract: bucket('contract-record'),
  };
}

function evidenceMixPanel() {
  const e = evidenceSummary();
  const parts = [
    ['Reviewed site models', e.reviewed, 'Independent/model-enriched records with explicit site caveats', 'model'],
    ['Imported site estimates', e.archive, 'Historical site estimates retained for breadth; not re-underwritten', 'archive'],
    ['Native-unit disclosures', e.native, 'Useful evidence left in issuer-native units rather than forced into GW', 'primary'],
    ['Contract records', e.contract, 'Commercial or counterparty records kept separate from installed supply', 'target'],
  ];
  return `<section class="panel panel-pad section-gap"><div class="panel-head"><div><h2>Evidence before aggregation</h2><p class="panel-sub">The atlas intentionally keeps unlike evidence in separate lanes. “Unknown” is never rendered as zero.</p></div><button class="text-button" data-action="method">Methodology ↗</button></div><div class="evidence-lanes">${parts.map(([label, x, note, cls]) => `<div class="evidence-lane"><div class="flex"><span class="pill ${cls}">${label}</span><strong>${x.count}</strong></div><div class="evidence-number">${x.snapshot ? gw(x.mw) + ' GW' : '—'}</div><div class="evidence-note">${x.snapshot} quantified snapshots · ${note}</div></div>`).join('')}</div><p class="footnote">The ${gw(e.reviewed.mw)} GW reviewed-model subtotal and ${gw(e.archive.mw)} GW imported-estimate subtotal are shown separately on purpose. They are not a global fleet census and should not be added to native-unit or contract-only records.</p></section>`;
}

function countryProfile() {
  const groups = new Map();
  for (const s of D.sites) {
    if (!['reviewed-model', 'archive'].includes(s.review)) continue;
    const mw = atlasNumber(s.snapshot?.it_mw);
    if (mw == null) continue;
    const g = groups.get(s.country) || {country: s.country, total: 0, reviewed: 0, archive: 0, count: 0};
    g.total += mw;
    g.count += 1;
    if (s.review === 'reviewed-model') g.reviewed += mw;
    else g.archive += mw;
    groups.set(s.country, g);
  }
  const rows = [...groups.values()].sort((a, b) => b.total - a.total).slice(0, 7);
  const max = Math.max(...rows.map(x => x.total), 1);
  return `<section class="panel panel-pad"><div class="panel-head"><div><h2>Geographic concentration of named snapshots</h2><p class="panel-sub">A partial site footprint, split by evidence quality.</p></div><button class="text-button" data-action="nav" data-id="globe">Open globe →</button></div><div class="geo-bars">${rows.map(g => `<button class="geo-row" data-action="filter-country" data-id="${esc(g.country)}"><span class="geo-name">${esc(g.country)}<small>${g.count} quantified dossiers</small></span><span class="geo-track"><i class="geo-reviewed" style="width:${g.reviewed / max * 100}%"></i><i class="geo-archive" style="width:${g.archive / max * 100}%"></i></span><span class="geo-value">${gw(g.total)} GW</span></button>`).join('')}</div><div class="tag-row"><span class="pill model">Reviewed model</span><span class="pill archive">Imported estimate</span></div><p class="footnote">Bars sum only comparable named site snapshots in this collection. They do not establish national installed AI-compute capacity, grid allocations, or commercially available supply.</p></section>`;
}

function investorDashboard() {
  const cs = D.companies
    .filter(c => c.commitment && c.stock)
    .map(c => {
      const f = c.commitment;
      const st = c.stock;
      const fp = companyFootprint(c);
      const capex = atlasNumber(f.capex_b);
      const ocf = atlasNumber(f.ocf_b);
      const leases = atlasNumber(f.uncommenced_leases_b);
      const rpo = atlasNumber(f.rpo_b);
      const marketCap = atlasNumber(st.market_cap_b);
      return {
        c, f, fp,
        capexOCF: capex != null && ocf != null && ocf !== 0 ? capex / ocf : null,
        leasePct: leases != null && marketCap != null && marketCap !== 0 ? leases / marketCap : null,
        rpoPct: rpo != null && marketCap != null && marketCap !== 0 ? rpo / marketCap : null,
      };
    })
    .sort((a, b) => (b.capexOCF ?? -Infinity) - (a.capexOCF ?? -Infinity));
  return `<section class="panel panel-pad section-gap"><div class="panel-head"><div><h2>Capital intensity dashboard</h2><p class="panel-sub">${cs.length} issuers with matched financial-footnote records. Periods differ; market values are the archived 31 Aug 2026 snapshot.</p></div><button class="text-button" data-action="nav" data-id="investment">Investment lens →</button></div><div class="table-wrap"><table class="investor-table"><thead><tr><th>Company</th><th>Capex / OCF</th><th>Uncommenced leases</th><th>RPO / backlog</th><th>Named site snapshot</th><th>Question</th></tr></thead><tbody>${cs.map(x => `<tr class="clickable" data-action="invest-company" data-id="${x.c.id}" tabindex="0"><td><span class="cell-title"><i class="dot" style="background:${x.c.color}"></i>${esc(x.c.name)}</span><span class="cell-sub">${esc(x.c.ticker)} · ${esc(x.f.period)}</span></td><td><strong>${x.capexOCF != null ? fmt(x.capexOCF, 2) + '×' : '—'}</strong><div class="ratio-track"><i style="width:${Math.min(100, (x.capexOCF || 0) / 4 * 100)}%;background:${x.c.color}"></i></div></td><td>${x.f.uncommenced_leases_b != null ? money(x.f.uncommenced_leases_b, 1) : '—'}${x.leasePct != null ? `<br><span class="cell-sub">${fmt(x.leasePct * 100, 1)}% of archived mkt cap</span>` : ''}</td><td>${x.f.rpo_b != null ? money(x.f.rpo_b, 1) : '—'}${x.rpoPct != null ? `<br><span class="cell-sub">${fmt(x.rpoPct * 100, 1)}% of archived mkt cap</span>` : ''}</td><td>${x.fp.count ? `${gw(x.fp.mw)} GW<br><span class="cell-sub">${x.fp.count} primary-owner sites · partial</span>` : 'Not quantified'}</td><td><span class="cell-sub">${esc(x.c.risk)}</span></td></tr>`).join('')}</tbody></table></div><p class="footnote">Capex, OCF, leases, RPO and market capitalization are not economically interchangeable. This table is a diligence index into the footnotes, not a valuation ranking.</p></section>`;
}

function phaseLadder(s) {
  const a = s.snapshot;
  const b = s.target;
  const av = atlasNumber(a?.it_mw);
  const bv = atlasNumber(b?.it_mw);
  if (av == null && bv == null) return '';
  const max = Math.max(av || 0, bv || 0, 1);
  const delta = av != null && bv != null ? bv - av : null;
  const pct = delta != null && av !== 0 ? delta / av * 100 : null;
  const row = (label, x, value, cls) => value != null ? `<div class="phase-row"><span class="phase-label">${label}<small>${esc(x?.date || 'Date not supplied')}</small></span><span class="phase-track"><i class="${cls}" style="width:${Math.max(2, value / max * 100)}%"></i></span><span class="phase-value">${fmt(value)} MW</span></div>` : '';
  return `<section class="phase-card"><div class="panel-head"><div><h3>Power phase ladder</h3><p class="panel-sub">IT-load boundary only; target is an end-state.</p></div>${delta != null ? `<span class="phase-delta ${delta >= 0 ? 'up' : 'down'}">${delta >= 0 ? '+' : ''}${fmt(delta)} MW · ${pct != null ? (pct >= 0 ? '+' : '') + fmt(pct, 0) + '%' : '—'}</span>` : ''}</div>${row('Snapshot', a, av, 'snapshot')}${row('Projected end-state', b, bv, 'target')}<p class="footnote">The delta is a visual comparison, not an assertion that all difference is signed, funded, incremental, or available.</p></section>`;
}

function capitalStack(c) {
  const f = c.commitment;
  if (!f) return '';
  const items = [
    ['Cash capex', f.capex_b, 'spend'],
    ['Uncommenced leases', f.uncommenced_leases_b, 'obligation'],
    ['Purchase / contractual', f.purchase_or_contract_b, 'obligation'],
    ['RPO / backlog', f.rpo_b, 'demand'],
  ].filter(([, value]) => atlasFiniteNumber(value));
  if (!items.length) return '';
  const max = Math.max(...items.map(([, value]) => Number(value)), 1);
  return `<h2>Capital and demand scale</h2><section class="capital-stack"><div class="capital-stack-head"><span>${esc(f.period)}</span><span>Different accounting categories · do not add mechanically</span></div>${items.map(([label, value, kind]) => `<div class="capital-row"><span>${label}</span><span class="capital-track"><i class="${kind}" style="width:${Number(value) / max * 100}%"></i></span><strong>${money(Number(value), 1)}</strong></div>`).join('')}<div class="capital-legend"><span><i class="spend"></i>period spend</span><span><i class="obligation"></i>future obligation / commitment</span><span><i class="demand"></i>commercial visibility</span></div><p class="footnote">RPO/backlog is not a funding obligation; capex is period spend; leases and purchase commitments can overlap or cover non-AI assets.</p></section>`;
}

function companyCardKpis(c) {
  const fp = companyFootprint(c);
  const f = c.commitment;
  const capex = atlasNumber(f?.capex_b);
  const ocf = atlasNumber(f?.ocf_b);
  const capexOCF = capex != null && ocf != null && ocf !== 0 ? capex / ocf : null;
  const snapshotValue = fp.count ? `${gw(fp.mw)} GW` : 'Not quantified';
  const snapshotNote = fp.count ? `${fp.count} primary-owner ${fp.count === 1 ? 'site' : 'sites'} · partial` : 'Unknown is not zero';
  const ratioValue = capexOCF != null ? `${fmt(capexOCF, 2)}×` : 'Not populated';
  const ratioNote = capexOCF != null ? esc(f.period) : 'No matched capex / OCF record';
  return `<div class="company-kpis"><div><span>Named snapshot</span><strong>${snapshotValue}</strong><small>${snapshotNote}</small></div><div><span>Capex / OCF</span><strong>${ratioValue}</strong><small>${ratioNote}</small></div></div>`;
}

const coreOverviewView = overviewView;
const coreCompaniesView = companiesView;
const coreSiteDossier = siteDossier;
const coreCompanyDossier = companyDossier;
const coreDownloadOriginal = downloadOriginal;

overviewView = function() {
  const base = coreOverviewView();
  const rankStart = base.indexOf('<div class="grid-two">');
  if (rankStart < 0) return base + evidenceMixPanel() + investorDashboard();
  const prefix = base.slice(0, rankStart);
  const suffix = base.slice(rankStart);
  const split = suffix.indexOf('</section><section class="panel panel-pad">');
  const firstEnd = split >= 0 ? split + '</section>'.length : -1;
  const footprint = firstEnd > 0 ? suffix.slice(0, firstEnd) : suffix;
  const questions = firstEnd > 0 ? suffix.slice(firstEnd) : '';
  return `${prefix}${evidenceMixPanel()}${investorDashboard()}<div class="grid-two section-gap">${footprint.replace(/^<div class="grid-two">/, '')}${countryProfile()}</div>${questions ? `<div class="section-gap">${questions.replace(/<\/div>$/, '')}</div>` : ''}`;
};

companiesView = function() {
  const template = document.createElement('template');
  template.innerHTML = coreCompaniesView();
  template.content.querySelectorAll('.company-card').forEach(card => {
    const id = card.querySelector('[data-action="company"]')?.dataset.id;
    const c = company(id);
    const footer = card.querySelector('.company-card-footer');
    if (!c || !footer) return;
    footer.insertAdjacentHTML('beforebegin', companyCardKpis(c));
  });
  return template.innerHTML;
};

siteDossier = function(s) {
  const html = coreSiteDossier(s);
  const ladder = phaseLadder(s);
  if (!ladder) return html;
  const markers = ['</div><p class="footnote">Snapshot source', '</div><h2>The facility evidence</h2>'];
  for (const mark of markers) {
    const i = html.indexOf(mark);
    if (i >= 0) return html.slice(0, i + 6) + ladder + html.slice(i + 6);
  }
  return ladder + html;
};

companyDossier = function(c) {
  const html = coreCompanyDossier(c);
  const stack = capitalStack(c);
  const mark = '<h2>Financial footnote trail</h2>';
  return stack && html.includes(mark) ? html.replace(mark, stack + mark) : html;
};

downloadOriginal = function(name) {
  const files = JSON.parse($('#original-files')?.textContent || '{}');
  const b64 = files[name];
  if (!b64 && location.protocol !== 'file:') {
    const a = document.createElement('a');
    a.href = 'originals/' + encodeURIComponent(name);
    a.download = name;
    a.target = '_blank';
    a.rel = 'noopener';
    document.body.appendChild(a);
    a.click();
    a.remove();
    toast('Opening repository attachment: ' + name);
    return;
  }
  return coreDownloadOriginal(name);
};

document.addEventListener('click', e => {
  const b = e.target.closest('[data-action="filter-country"]');
  if (!b) return;
  const id = b.dataset.id;
  state.filter = {q: '', company: 'all', country: id, review: 'all', stage: 'all'};
  navigate('globe');
  if (globe) {
    const xs = D.sites.filter(s => s.country === id && s.lat != null && s.lon != null);
    if (xs.length) {
      globe.flyTo(
        xs.reduce((n, x) => n + x.lat, 0) / xs.length,
        xs.reduce((n, x) => n + x.lon, 0) / xs.length,
        1.8,
      );
    }
  }
});

render();
