"use strict";
/* The six-scale editorial interface. Data and camera state remain in the atlas. */
const UI_TOPICS = [
  ["overview", "Overview"],
  ["power", "Power & phases"],
  ["hardware", "Technical design"],
  ["timeline", "Timeline"],
  ["partners", "Counterparties"],
  ["finance", "Investment"],
  ["sources", "Sources & evidence"],
  ["notes", "Notes"],
];
const uiIcon = (name) => {
  const paths = {
    arrow: "M4 12h16M14 6l6 6-6 6",
    expand: "M8 3H3v5m13-5h5v5M3 16v5h5m13-5v5h-5",
    layers: "m12 3 9 5-9 5-9-5 9-5Zm-9 9 9 5 9-5M3 16l9 5 9-5",
    filter: "M3 6h18M6 12h12M9 18h6",
    pin: "M12 21s7-7 7-12a7 7 0 0 0-14 0c0 5 7 12 7 12Zm0-15v6m-3-3h6",
    source: "M6 3h9l4 4v14H6V3Zm9 0v5h4M9 12h7M9 16h7",
    power: "m13 2-9 12h7l-1 8 10-13h-7l0-7Z",
    building:
      "M4 21V5l8-3 8 3v16M8 7v2m4-3v3m4-2v2M8 12v2m4-2v2m4-2v2M9 21v-4h6v4",
    search: "m20 20-5-5M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0",
    globe:
      "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20ZM2 12h20M12 2c-6 6-6 14 0 20 6-6 6-14 0-20Z",
    check: "m5 12 4 4L19 6",
    close: "m6 6 12 12M6 18 18 6",
    compare: "M5 5v14m7-17v20m7-15v10",
    help: "M9 8a3 3 0 1 1 5 2c-2 1-2 2-2 4m0 4h.01",
  };
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.35" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${paths[name] || paths.source}"/></svg>`;
};
function uaClusterTitle(rows) {
  if (rows.length === 1) return rows[0].name;
  if (uaState.scale >= 2) {
    const lon = rows.reduce((n, r) => n + r.lon, 0) / rows.length,
      lat = rows.reduce((n, r) => n + r.lat, 0) / rows.length;
    let city = null,
      nearest = 180;
    for (const place of ATLAS_CONTEXT.places || []) {
      const distance = spatialDistance(place, { lat, lon });
      if (distance < nearest) {
        nearest = distance;
        city = place;
      }
    }
    if (city) return city.name;
  }
  const country = [...new Set(rows.map((r) => r.country))],
    regions = [...new Set(rows.map((r) => r.region))],
    lon = rows.reduce((s, r) => s + r.lon, 0) / rows.length,
    lat = rows.reduce((s, r) => s + r.lat, 0) / rows.length;
  if (country.length === 1 && country[0] === "United States")
    return lon < -114
      ? "US West"
      : lon < -103
        ? "US Mountain West"
        : lon < -94
          ? lat < 36
            ? "Texas & the Plains"
            : "US Plains"
          : lon < -82 && lat >= 37
            ? "US Midwest"
            : "US East";
  if (country.length === 1) {
    const cities = rows.map((r) => r.native.city).filter(Boolean);
    return cities.length > rows.length * 0.4
      ? cities.sort(
          (a, b) =>
            cities.filter((x) => x === b).length -
            cities.filter((x) => x === a).length,
        )[0]
      : country[0];
  }
  if (regions.length === 1 && regions[0] === "Europe")
    return lat > 55
      ? "Northern Europe"
      : lon < 12
        ? "Western Europe"
        : "Central Europe";
  if (regions.length === 1 && regions[0] === "North America")
    return lon < -100 ? "Western North America" : "Eastern North America";
  if (lat > 32 && lon > -15 && lon < 40)
    return lon < 12 ? "Western Europe" : "Central Europe";
  if (regions.length === 1) return regions[0];
  return lon < -35
    ? "The Americas"
    : lon > 60
      ? "Asia Pacific"
      : "Cross-border cluster";
}
function uiPower(value) {
  return value == null
    ? "Not reported"
    : value >= 1000
      ? fmt(value / 1000, 2) + " GW"
      : fmt(value, 0) + " MW";
}
function uiModel(rows) {
  const centers = rows.filter((r) => r.collection === "epochdc"),
    known = centers.filter((r) => uaMeasure(r).value != null);
  return {
    count: centers.length,
    known: known.length,
    power: known.length
      ? known.reduce((s, r) => s + uaMeasure(r).value, 0)
      : null,
  };
}
function uiKicker(text, action = "") {
  return `<div class="ui-kicker"><span>${text}</span>${action || uiIcon("arrow")}</div>`;
}
function uiTopics() {
  return `<nav class="ua-topics" aria-label="Research topics">${UI_TOPICS.map(([id, name]) => `<button data-ua-topic="${id}" aria-pressed="${uaState.topic === id}">${name}</button>`).join("")}</nav>`;
}
function uiFilterChips() {
  return [
    ["region", uaState.region !== "All" && uaState.region],
    ["country", uaState.country !== "All" && uaState.country],
    ["q", uaState.q],
    ["operator", uaState.operator],
    ["coverage", uaState.coverage !== "all" && uaState.coverage],
  ]
    .filter(([, v]) => v)
    .map(
      ([k, v]) =>
        `<button data-ui-clear-filter="${k}">${esc(v)} <span>×</span></button>`,
    )
    .join("");
}
function uiFilters() {
  return `<div class="ui-refinements">${uaFilters()}<nav class="ua-collections" aria-label="Map source collection"><button data-ua-collection="all" aria-pressed="${uaState.collection === "all"}">All compute <span>${fmt(uaRecords().length)}</span></button>${Object.entries(
    UA_SHORT,
  )
    .map(
      ([id, name]) =>
        `<button data-ua-collection="${id}" aria-pressed="${uaState.collection === id}"><i style="background:${UA_COLORS[id]}"></i>${name}</button>`,
    )
    .join(
      "",
    )}</nav><div class="ui-active-filters">${uiFilterChips()}</div></div>`;
}
uaKpis = function (rows) {
  const model = uiModel(rows),
    gpu = rows.filter((r) => r.collection === "gpu"),
    mapped = rows.filter((r) => r.mapped),
    countries = new Set(
      rows
        .map((r) => r.country)
        .filter((c) => !["Unknown", "Not supplied"].includes(c)),
    );
  return `<button class="ua-metric" data-ui-measure="power"><span>Published facility power</span><strong>${uiPower(model.power)}</strong><small>${model.known} quantified centers · Epoch current model</small></button><button class="ua-metric" data-ui-measure="locations"><span>Mapped source records</span><strong>${fmt(mapped.length)}</strong><small>${fmt(rows.length - mapped.length)} additional records without coordinates</small></button><button class="ua-metric" data-ui-measure="hardware"><span>Published GPU clusters</span><strong>${fmt(gpu.length)}</strong><small>Native records, including historical phases</small></button><button class="ua-metric" data-ui-measure="coverage"><span>Countries & territories</span><strong>${fmt(countries.size)}</strong><small>${fmt(rows.length)} records across independent publications</small></button>`;
};
function uiSourceRanking(rows, field = "region", count = 5) {
  return `<div class="ua-ranks ui-source-ranking">${uaRanks(rows, field, count).map(([name, n], i) => `<button ${field === "region" ? "data-ua-region" : "data-ua-country"}="${esc(name)}"><span>${String(i + 1).padStart(2, "0")}</span><b>${esc(name)}</b><strong>${fmt(n)}</strong></button>`).join("")}</div><small>Native source records · publications may overlap</small>`;
}
function uiOperatorMarks(rows) {
  return `<div class="ui-operator-marks" aria-label="Operators in this scope">${uaRanks(rows.filter(r => r.operator && !/unknown|not supplied/i.test(r.operator)), "operator", 6).map(([name]) => `<button data-ui-operator="${esc(name)}">${esc(name)}</button>`).join("")}</div>`;
}
function uiRegionalRail(rows) {
  const local = rows.filter(r => r.mapped && r.lon > -78.5 && r.lon < -76.5 && r.lat > 38 && r.lat < 39.5);
  if (!local.length) return null;
  const model = uiModel(local), projects = local.filter(r => r.collection === "projects");
  return `<section class="ua-editorial ui-market-card">${uiKicker("01 / MARKET FOCUS")}<h2>Northern Virginia</h2><p class="ui-market-subtitle">An established compute market.</p><p>Explore the published facilities around Ashburn and Northern Virginia, from mapped infrastructure to dated project disclosures.</p><dl class="ua-facts"><div><dt>${uiIcon("power")} Published facility power</dt><dd>${uiPower(model.power)}</dd></div><div><dt>${uiIcon("building")} Mapped source records</dt><dd>${fmt(local.length)}</dd></div><div><dt>${uiIcon("source")} Project dossiers</dt><dd>${projects.length}</dd></div><div><dt>${uiIcon("layers")} Source collections</dt><dd>${new Set(local.map(r => r.collection)).size}</dd></div></dl><small>Power: Epoch current model · ${model.known} quantified centers.<br>Records within 38–39.5°N, 76.5–78.5°W; not a market census.</small></section><section class="ua-editorial">${uiKicker("02 / INFRASTRUCTURE ADVANTAGE")}<div class="ui-market-points"><div>${uiIcon("building")}<p><b>Physical infrastructure</b>Inspect native mapped outlines and published facility locations.</p></div><div>${uiIcon("power")}<p><b>Power with a clear boundary</b>Keep facility-power models separate from project IT capacity.</p></div><div>${uiIcon("source")}<p><b>Original evidence</b>Read the disclosures and exact source fields behind each record.</p></div></div><button class="btn primary" data-ui-market="virginia">Explore Northern Virginia ${uiIcon("arrow")}</button></section><section class="ua-editorial">${uiKicker("03 / OPERATORS IN THIS SCOPE")}${uiOperatorMarks(local)}</section>`;
}
uaWorldRail = function (rows) {
  if (uaState.scale === 2 && uaState.country === "United States") {
    const market = uiRegionalRail(rows);
    if (market) return market;
  }
  const region = uaState.country !== "All" ? uaState.country : uaState.region,
    continental = uaState.scale === 1,
    atlantic = continental && ["All", "Atlantic"].includes(region),
    model = uiModel(rows),
    globalModel = uiModel(uaRecords()),
    share = model.power != null && globalModel.power ? Math.round(model.power / globalModel.power * 100) : null,
    projects = rows.filter(r => r.collection === "projects"),
    heading = atlantic ? "North America and Europe.<br>A connected compute economy." : region !== "All" ? esc(region) + ".<br>A landscape of opportunity." : "Compute is a global<br>asset class.";
  return `<section class="ua-editorial">${uiKicker("01 / " + (continental ? "REGIONAL TAKEAWAY" : "GLOBAL TAKEAWAY"))}<h2>${heading}</h2><p>${atlantic ? `${share == null ? "Explore" : share + "% of the captured current facility-power model is reported in"} these two continents. Follow the places, operators and original evidence behind the footprint.` : "From silicon to substations, the physical infrastructure behind AI connects power, capital and place."}</p><button class="text-button" ${atlantic ? 'data-ui-preset="region"' : 'data-ui-preset="atlantic"'}>${atlantic ? "Explore the regional landscape" : "Explore North America & Europe"} ${uiIcon("arrow")}</button></section><section class="ua-editorial">${uiKicker("02 / " + (atlantic ? "TRANSATLANTIC FOOTPRINT" : "WHERE COMPUTE LIVES"))}<h2>${atlantic ? "Two continents.<br>Local foundations." : "Where the capacity<br>is taking shape."}</h2>${uiSourceRanking(rows, atlantic ? "country" : "region", 5)}</section><section class="ua-editorial ui-buildout-card">${uiKicker("03 / THE NEXT BUILDOUT")}<h2>A more distributed,<br>more connected landscape.</h2><p>${fmt(projects.length)} project dossiers connect this geographic view to disclosed development, dated power scopes and counterparties.</p><button class="text-button" data-ui-preset="campus">Inside a campus ${uiIcon("arrow")}</button></section>`;
};
function uiPartners(r) {
  if (r.collection === "projects") {
    const rows = primaryRelationships(r.native).slice(0, 5);
    return rows.length
      ? rows
          .map(
            (p) =>
              `<button data-action="company" data-id="${esc(p.company_id)}"><span>${esc(p.role)}</span><b>${esc(company(p.company_id)?.name || p.company_id)}</b>${uiIcon("arrow")}</button>`,
          )
          .join("")
      : `<p>${esc(r.operator || "No counterparties reported in this source.")}</p>`;
  }
  const fields = r.native.fields || {},
    roles = [
      ["Owner", fields.Owner || r.operator],
      ["Users", fields.Users],
      ["Investors", fields.Investors],
      ["Energy", fields["Energy companies"]],
    ];
  return (
    roles
      .filter(([, v]) => v)
      .slice(0, 4)
      .map(
        ([role, value]) =>
          `<div><span>${role}</span><b>${esc(String(value).replace(/#\w+/g, "").trim())}</b></div>`,
      )
      .join("") || "<p>No counterparties reported in this source.</p>"
  );
}
function uiPhaseRows(r) {
  return r.collection === "projects" ? workspacePhases(r.native) : [];
}
function uiPowerLadder(r) {
  const rows = uiPhaseRows(r);
  if (!rows.length) return "";
  const max = Math.max(1, ...rows.map((p) => p.value || 0));
  return `<section class="ui-power-ladder">${uiKicker("POWER BUILDOUT / MW IT")}<p class="ui-caption">Separate dated scopes · not additive</p>${rows
    .slice(0, 5)
    .map(
      (p, i) =>
        `<button data-ui-phase="${esc(p.id)}" aria-pressed="${uaState.phase === p.id}"><span>${esc(p.scope || "Reported IT scope")}</span><span class="ui-bar"><i style="width:${Math.max(2, ((p.value || 0) / max) * 100)}%;--bar:${i ? "#9eaaeb" : "#92e2c0"}"></i></span><b>${p.value == null ? "—" : fmt(p.value)}</b><time>${esc(p.as_of || "Undated")}</time></button>`,
    )
    .join("")}</section>`;
}
function uiTakeaways(r) {
  if (r.collection === "projects") {
    const rows = atlasResearchProfile(r.native)
      .rows.filter((p) => !primaryIsContext(p))
      .slice(0, 3);
    if (rows.length)
      return rows
        .map(
          (p, i) =>
            `<button data-ui-claim="${esc(p.id)}"><span>${String(i + 1).padStart(2, "0")}</span><p>${esc(atlasResearchLabel(p) + ": " + atlasResearchPlainValue(p))}</p>${uiIcon("arrow")}</button>`,
        )
        .join("");
  }
  const m = uaMeasure(r);
  return [
    ["Source identity", `${UA_SHORT[r.collection]} · ${r.name}`],
    ["Measurement boundary", `${m.label} · ${m.date || r.date || "Undated"}`],
    ["Location evidence", r.coordinate_basis || "No coordinates supplied"],
  ]
    .map(
      ([label, value], i) =>
        `<div><span>${String(i + 1).padStart(2, "0")}</span><p><b>${label}</b>${esc(value)}</p></div>`,
    )
    .join("");
}
uaSelectedRail = function (r, rows) {
  if (!r)
    return uaState.selected
      ? `<section id="ua-selection" class="ua-editorial"><h2>Record unavailable.</h2><p>${esc(uaState.selected)} is not in this publication.</p><button class="btn" data-ua-clear-selection>Return to this scope</button></section>`
      : uaWorldRail(rows);
  const m = uaMeasure(r),
    physical = uaState.scale >= 4,
    inside = rows.some((x) => x.id === r.id),
    phase = uiPhaseRows(r).find((p) => p.id === uaState.phase),
    metric = phase
      ? {
          ...m,
          value: phase.value,
          unit: phase.unit,
          label: phase.scope,
          date: phase.as_of,
        }
      : m;
  if (!phase && r.mapped && uaState.scale >= 3) return uiCompactDossier(r, rows);
  return `<section id="ua-selection" class="ua-editorial ua-selected">${uiKicker(physical ? "01 / FACILITY DOSSIER" : "01 / SELECTED LOCATION", `<button class="text-button" data-ua-clear-selection aria-label="Clear selection">${uiIcon("close")}</button>`)}<h2 tabindex="-1">${esc(phase ? phase.scope : r.name)}</h2><p class="ui-place">${uiIcon("pin")}${esc(r.place || r.country)}</p>${!inside ? '<p class="ua-notice">Outside the active filters. <button class="text-button" data-ua-reveal>Show its scope →</button></p>' : ""}<div class="ui-status-row">${uaBadge(r)}${r.collection === "gpu" ? `<span>${esc(r.native.status)}</span>` : ""}</div><div class="ua-selected-number"><b>${metric.value == null ? (r.geometry ? "Mapped footprint" : "Location record") : compact(metric.value) + " " + metric.unit}</b><span>${esc(metric.label)} · ${esc(metric.date || r.date || "Not dated")}</span></div><dl class="ua-facts"><div><dt>Operator / owner</dt><dd>${esc(r.operator || "Not disclosed")}</dd></div>${r.collection === "projects" ? `<div><dt>Target IT model</dt><dd>${r.target_mw == null ? "Not quantified" : fmt(r.target_mw) + " MW IT"}</dd></div>` : ""}<div><dt>Location basis</dt><dd>${esc(r.coordinate_basis || "Not supplied")}</dd></div></dl><div class="ua-actions">${r.mapped ? `<button class="btn primary" data-ua-dive>${physical ? "Inspect physical features" : uaState.scale < 3 ? "Explore this market" : "Enter this campus"} ${uiIcon("arrow")}</button>` : "<p>No map location supplied.</p>"}${researchPin(r.id)}<button class="text-button" data-ua-compare="${esc(r.id)}">${uiIcon("compare")}${uaState.compare.includes(r.id) ? "Comparing" : "Compare"}</button><button class="text-button" data-ua-export="${esc(r.id)}">Export ↓</button></div></section>${physical && r.collection === "projects" ? uiPowerLadder(r) : `<section class="ua-editorial">${uiKicker("02 / KEY TAKEAWAYS")}<div class="ui-takeaways">${uiTakeaways(r)}</div><button class="text-button" data-ua-topic="sources">Read original evidence ${uiIcon("arrow")}</button></section>`}<section class="ua-editorial">${uiKicker("03 / COUNTERPARTIES")}<div class="ui-partners">${uiPartners(r)}</div><button class="text-button" data-ua-topic="partners">All disclosed relationships ${uiIcon("arrow")}</button></section>${physical ? `<section class="ua-editorial ui-note-card">${uiKicker("04 / ANALYST NOTES")}<p>Your questions, assumptions and observations stay attached to this source record.</p><button class="text-button" data-ua-topic="notes">${saved.notes[r.id] ? "Read your note" : "Add a research note"} +</button></section>` : ""}`;
};
function uiEvidenceSources(r) {
  const claims = r.collection === "projects" ? atlasResearchProfile(r.native).rows : [];
  const sources = [...new Map(claims.map(p => [p.source_id, p])).values()].slice(0, 3);
  return `<section class="ui-deck-sources"><h3>${uiIcon("source")} Sources & evidence</h3>${sources.length ? sources.map(p => `<button class="ui-source-row" data-ui-claim="${esc(p.id)}">${uiIcon("source")}<span>${esc(primarySource(p.source_id)?.title || atlasResearchLabel(p))}</span><time>${esc(p.as_of || "Undated")}</time></button>`).join("") : `<p>${esc(UA_SHORT[r.collection])} retains its original fields and source references.</p>`}<button class="text-button" data-ua-topic="sources">View all source evidence ${uiIcon("arrow")}</button></section>`;
}
function uiOverview(r) {
  const m = uaMeasure(r), campus = uaState.scale === 4;
  const takeaways = `<section class="ui-deck-takeaways"><h3>${uiIcon("check")} Key takeaways</h3><div class="ui-takeaways">${uiTakeaways(r)}</div></section>`;
  if (campus) return `<div class="ui-evidence-deck ui-campus-deck">${uiEvidenceSources(r)}${takeaways}</div>`;
  return `<div class="ui-evidence-deck"><section>${r.collection === "projects" ? uiPowerLadder(r) : `<h3>${uiIcon("power")} Power & compute</h3>${uaPowerContent(r)}`}</section><section><h3>${uiIcon("building")} Facility attributes</h3><dl class="ua-facts"><div><dt>Source identity</dt><dd>${esc(r.id)}</dd></div><div><dt>Country / territory</dt><dd>${esc(r.country)}</dd></div><div><dt>Operator / owner</dt><dd>${esc(r.operator || "Not supplied")}</dd></div><div><dt>Source observation</dt><dd>${esc(m.date || r.date || "Not supplied")}</dd></div><div><dt>Physical evidence</dt><dd>${r.geometry ? "Native mapped footprint" : CAMPUS_SCENES.scenes.some(s => s.project_id === r.id) ? "Historical imagery & reviewed outlines" : "Independent mapped context"}</dd></div></dl></section>${uiEvidenceSources(r)}${takeaways}</div>`;
}
function uiCompactDossier(r, rows) {
  const physical = uaState.scale >= 4, m = uaMeasure(r), scenes = CAMPUS_SCENES.scenes.filter(s => s.project_id === r.id), scene = uaState.scene ? scenes.find(s => s.id === uaState.scene) : scenes[0];
  return `<section id="ua-selection" class="ua-editorial ua-selected ui-compact-dossier">${uiKicker(physical ? "01 / FACILITY DOSSIER" : "01 / SELECTED CLUSTER", `<button class="text-button" data-ua-clear-selection aria-label="Clear selection">${uiIcon("close")}</button>`)}<h2 tabindex="-1">${esc(r.name)}</h2><p class="ui-place">${uiIcon("pin")}${esc(r.place || r.country)}</p>${!rows.some(x => x.id === r.id) ? '<p class="ua-notice">Outside the active filters. <button class="text-button" data-ua-reveal>Show its scope →</button></p>' : ""}<div class="ui-status-row">${uaBadge(r)}${scene ? '<span>Reviewed imagery</span>' : ''}</div><dl class="ua-facts"><div><dt>${esc(m.label)}</dt><dd>${m.value == null ? "Not reported" : compact(m.value) + " " + m.unit}</dd></div>${r.collection === "projects" ? `<div><dt>Target IT model</dt><dd>${r.target_mw == null ? "Not reported" : fmt(r.target_mw) + " MW IT"}</dd></div>` : ""}<div><dt>Operator / owner</dt><dd>${esc(r.operator || "Not supplied")}</dd></div><div><dt>Source observation</dt><dd>${esc(m.date || r.date || "Undated")}</dd></div>${scene ? `<div><dt>Historical image</dt><dd>${esc(scene.image.acquired_at)}</dd></div><div><dt>Reviewed roof outlines</dt><dd>${scene.features.length} · image interpretation</dd></div>` : ""}</dl><div class="ua-actions"><button class="btn primary" data-ua-dive>${physical ? "Inspect physical features" : "View full site dossier"} ${uiIcon("arrow")}</button><div class="ui-dossier-tools">${researchPin(r.id)}<button class="text-button" data-ua-compare="${esc(r.id)}">${uiIcon("compare")} ${uaState.compare.includes(r.id) ? "Comparing" : "Compare"}</button><button class="text-button" data-ua-export="${esc(r.id)}">Export ↓</button></div></div></section>${physical ? uiPowerLadder(r) : `<section class="ua-editorial">${uiKicker("02 / LOCAL POWER & BUILDOUT")}<h2>Power, land and<br>the development story.</h2><div class="ui-takeaways">${uiTakeaways(r)}</div></section>`}<section class="ua-editorial">${uiKicker("03 / " + (physical ? "ANALYST NOTES" : "DISCLOSED RELATIONSHIPS"))}${physical ? `<label class="ui-note-label" for="ui-campus-note">Your research questions & observations</label><textarea id="ui-campus-note" data-note="${esc(r.id)}" placeholder="Add a note about this campus…">${esc(saved.notes[r.id] || "")}</textarea><div class="ui-note-footer"><small data-storage-status>${storageOK ? "Private · saved in this browser" : "Session only · export before closing"}</small><button class="text-button" data-action="export-session">Export notes ↓</button></div>` : `<div class="ui-partners">${uiPartners(r)}</div>`}</section>`;
}
const uiPreviousDetail = uaDetail;
uaDetail = function (r) {
  if (!r) return "";
  if (uaState.topic !== "overview") {
    let html = uiPreviousDetail(r);
    return html.replace(
      /<nav class="ua-topics"[\s\S]*?<\/nav>/,
      uaState.scale >= 4 ? "" : uiTopics(),
    );
  }
  return `<section class="ua-detail" aria-label="Selected record research">${uaState.scale >= 4 ? "" : uiTopics()}<div id="ua-topic-content">${uiOverview(r)}</div></section>`;
};
function uiTitle(r) {
  if (uaState.scale >= 4 && r) return [esc(["coreweave-helios", "amazon-anthropic-new-carlisle"].includes(r.id) ? r.name + " Data Center Campus" : r.name), r.place || r.country];
  if (uaState.scale === 3 && r)
    return [
      r.id === "amazon-anthropic-new-carlisle"
        ? "Chicago to New Carlisle."
        : esc(r.name),
      "Power, land, and compute in the local landscape.",
    ];
  if (uaState.scale === 2 && uaState.country === "United States")
    return ["The Midwest and East Coast<br>powering what’s next.", ""];
  if (uaState.scale >= 2 && r) return [esc(r.name), r.place || r.country];
  if (uaState.country !== "All")
    return [esc(uaState.country) + ".<br>Infrastructure in focus.", ""];
  if (uaState.scale === 1 && ["All", "Atlantic"].includes(uaState.region))
    return [
      "North America ↔ Europe.<br>The core of a global compute economy.",
      "",
    ];
  if (uaState.region !== "All")
    return [esc(uaState.region) + ".<br>A connected compute landscape.", ""];
  return ["A global view<br>of compute capital.", ""];
}
function uiMap(r, rows, physical, scenes) {
  const scope = physical
    ? "Campus site map"
    : uaState.scale === 3
      ? "Local facilities & infrastructure"
      : uaState.scale === 2
        ? uaState.country === "United States"
          ? "US East & Midwest compute map"
          : uaState.country !== "All"
            ? uaState.country + " compute map"
            : "Regional compute map"
        : uaState.scale === 1
          ? ["All", "Atlantic"].includes(uaState.region)
            ? "North America – Europe"
            : uaState.region
          : "Global compute map";
  return `<section class="ua-map-panel atlas-map-panel"><div class="ua-map-head"><div><h2>${scope}</h2><p>${fmt(rows.filter((r) => r.mapped).length)} mapped records · ${physical ? "dated physical sources" : "global source coverage"}</p></div><div class="ui-map-actions"><button data-ui-refine aria-label="Refine the atlas">${uiIcon("filter")} Refine</button><button class="text-button" data-ua-share>Share ${uiIcon("arrow")}</button></div></div><div class="ua-map-stage"><canvas id="ua-map" tabindex="0" aria-label="Compute atlas. Drag to rotate or pan, scroll to zoom. Use the directory for keyboard access to every record."></canvas><div class="ua-layer-control"><button class="btn small" data-ua-layers>${uiIcon("layers")} Layers</button>${physical ? `<div class="ua-mode-tabs">${[["plan", "Plan"], ["3d", "3D"], ...(scenes.length ? [["aerial", "Satellite"]] : [])].map(([id, label]) => `<button data-ua-mode="${id}" aria-pressed="${uaState.mode === id}">${label}</button>`).join("")}</div>` : ""}</div>${physical && scenes.length ? `<label class="ua-scene-choice"><span>Image component</span><select data-ua-scene>${uaState.scene && !scenes.some((s) => s.id === uaState.scene) ? `<option selected value="${esc(uaState.scene)}">Requested image unavailable</option>` : ""}${scenes.map((s) => `<option value="${esc(s.id)}" ${uaState.scene === s.id ? "selected" : ""}>${esc(s.component || s.title)} · ${esc(s.image.acquired_at)}</option>`).join("")}</select></label>` : ""}<div class="ua-map-legend">${(physical
    ? [
        ["#9ee5c8", "Reviewed / native outlines"],
        ["#b4a7e5", "Mapped electricity context"],
      ]
    : [
        ["#a3e7c4", "Compute / power publications"],
        ["#9bc5de", "Mapped facilities & directories"],
        ["#a7a2e3", "Published GPU clusters"],
      ]
  )
    .map(
      ([color, label]) =>
        `<span><i style="background:${color}"></i>${label}</span>`,
    )
    .join(
      "",
    )}<small>${physical ? "Source dates & heights retained" : "Cluster size = source-record concentration"}</small></div><div class="ua-context-status" id="ua-context-status" role="status"></div><div class="ua-coordinate" id="ua-coordinate">DRAG TO EXPLORE · SCROLL TO ZOOM</div><div class="ua-map-buttons"><button data-ua-map="labels" aria-label="Toggle map labels">Aa</button><button data-ua-map="in" aria-label="Zoom in">+</button><button data-ua-map="out" aria-label="Zoom out">−</button><button data-ua-map="expand" aria-label="Expand map">${uiIcon("expand")}</button><button data-ua-map="reset" aria-label="Reset camera">◎</button></div></div><div class="ui-map-bottom"><nav class="ua-scales" aria-label="Geographic scale">${UA_SCALES.map((label, i) => `<button data-ua-scale="${i}" aria-pressed="${uaState.scale === i}">${label}</button>`).join("")}</nav><button class="text-button" data-ua-context-source>Map sources ${uiIcon("arrow")}</button></div><footer class="ua-map-attribution">Natural Earth · ${catalogLink("https://www.openstreetmap.org/copyright", "© OpenStreetMap contributors")}<span>${physical ? "Independent physical context" : "Native records may overlap"}</span></footer></section>`;
}
uaView = function () {
  const rows = uaRows(),
    r = uaRecord(uaState.selected),
    physical = uaState.scale >= 4 && r?.mapped,
    scenes = r ? CAMPUS_SCENES.scenes.filter((s) => s.project_id === r.id) : [],
    [title, subtitle] = uiTitle(r);
  return `<article class="unified-atlas ui-editorial-atlas ${physical ? "ui-physical-view" : ""}" data-ua-scale="${uaState.scale}"><header class="ua-intro"><div><div class="eyebrow">${physical ? "FACILITY & CAMPUS" : "COMPUTE FROM THE GROUND UP"}</div><h1>${title}</h1>${subtitle ? `<p class="ui-subtitle">${esc(subtitle)}</p>` : ""}</div><div class="ua-intro-aside"><p>${physical ? "A source-led view of the campus: physical context, dated power, counterparties and original evidence." : "Explore the physical places, power and partnerships behind AI. Move from a global perspective to a single facility."}</p><button class="btn primary" ${physical ? "data-research-save-view" : "data-ua-guide"}>${physical ? "Save to research shelf" : "Take the guided tour"} ${uiIcon("arrow")}</button></div></header>${uaPublicationNotices()}<div class="ua-layout"><div class="ua-map-column">${physical ? uiTopics() : ""}${uiMap(r, rows, physical, scenes)}${!physical ? `<nav class="ua-regions" aria-label="World regions">${catalogRegions.map((region) => `<button data-ua-region="${region}" aria-pressed="${uaState.region === region}">${region === "All" ? "All regions" : region}</button>`).join("")}</nav>` : ""}<div id="ua-cluster-members">${uaMembersHTML()}</div><div id="ua-physical-inspector"></div></div><aside class="ua-rail">${uaSelectedRail(r, rows)}</aside>${physical ? "" : `<section class="ua-kpis">${uaKpis(rows)}</section>`}</div>${uaDetail(r)}${uaComparison()}<section class="ui-directory-wrap">${uiFilters()}<section id="ua-directory" class="ua-directory">${uaRecordTable(rows)}</section></section><footer class="ua-source-footer">${fmt(uaRecords().length)} native source records · six complete captured publications · ${UA_LOCATIONS.records.filter((r) => r.status === "resolved").length} separately attributed geocodes.<div class="ua-source-tools"><button class="text-button" data-atlas-action="monitor">Source health & acquisition →</button><button class="text-button" data-coverage-candidates>Unresolved research leads →</button><button class="text-button" data-action="nav" data-id="data">Original files & audit trail →</button></div></footer></article>`;
};
const uiBaseURL = uaURL;
uaURL = function () {
  const hash = uiBaseURL();
  return uaState.phase
    ? hash + "&phase=" + encodeURIComponent(uaState.phase)
    : hash;
};
const uiBaseParse = uaParse;
uaParse = function (query) {
  uaState.phase =
    new URLSearchParams(query).get("phase")?.slice(0, 500) || null;
  uiBaseParse(query);
};
const uiBaseNav = renderNav;
renderNav = function () {
  uiBaseNav();
  if (state.view !== "atlas" && $("#tour")?.classList.contains("ui-guide"))
    $("#tour").hidden = true;
  document.body.classList.add("ui-atlas-active");
  const nav = document.querySelector("#navigation"), more = nav.querySelector(".workspace-nav-more");
  for (const [id, before] of [["costs", "investment"], ["data", null]]) {
    const item = more?.querySelector(`[data-id="${id}"]`);
    if (item) nav.insertBefore(item, before ? nav.querySelector(`[data-id="${before}"]`) : more);
  }
  const data = nav.querySelector('[data-id="data"]');
  if (data) data.innerHTML = icon("data") + "Data room & sources";
  const guide = document.createElement("button");
  guide.className = "nav-item ui-guide-nav";
  guide.dataset.uiOpenGuide = "true";
  guide.innerHTML = uiIcon("globe") + "Guided exploration";
  nav.insertBefore(guide, nav.querySelector('[data-id="reports"]') || more);
  if ([...nav.children].some(el => el.dataset.id === state.view) && more) more.open = false;
};
const uiBasePhysicalRail = uaPhysicalRail;
uaPhysicalRail = function (record, source) {
  return (
    uiBasePhysicalRail(record, source) +
    `<section class="ua-editorial">${uiKicker("03 / COUNTERPARTIES")}<div class="ui-partners">${uiPartners(source)}</div></section>`
  );
};
function uiPreset(id) {
  const common = {
    members: [],
    region: "All",
    country: "All",
    q: "",
    operator: "",
    coverage: "all",
    collection: "all",
    selected: null,
    feature: null,
    phase: null,
    scene: null,
    sceneCamera: null,
    camera: null,
    scope: "geography",
    topic: "overview",
  };
  const views = {
    world: {
      scale: 0,
      camera: {
        flat: false,
        lat: 24,
        lon: 20,
        zoom: .95,
        bounds: [-180, -80, 180, 80],
      },
    },
    atlantic: {
      scale: 1,
      region: "Atlantic",
      camera: {
        flat: false,
        lat: 39,
        lon: -43,
        zoom: 1.65,
        bounds: [-180, -80, 180, 80],
      },
    },
    region: {
      scale: 2,
      country: "United States",
      camera: {
        flat: true,
        lat: 38,
        lon: -84,
        zoom: 1,
        bounds: [-96, 30, -69, 47],
      },
      scope: "viewport",
    },
    metro: {
      scale: 3,
      scope: "viewport",
      selected: "amazon-anthropic-new-carlisle",
      camera: {
        flat: true,
        lat: 41.5,
        lon: -87,
        zoom: 1,
        bounds: [-88.3, 40.6, -85.5, 42.5],
      },
    },
    campus: {
      scale: 4,
      selected: "amazon-anthropic-new-carlisle",
      scene: "new-carlisle-sr2-2025",
      mode: "3d",
    },
    facility: {
      scale: 5,
      selected: "coreweave-helios",
      feature: CAMPUS_SCENES.scenes.find(
        (s) => s.project_id === "coreweave-helios",
      )?.features[0]?.id,
      mode: "3d",
    },
  };
  uaGo({ ...common, ...views[id] });
}
function uiMeasure(kind) {
  const rows = uaRows(),
    model = uiModel(rows);
  openDrawer("atlas-measure");
  $("#drawer-type").textContent = "METRIC & SOURCE BOUNDARY";
  $("#drawer-content").innerHTML =
    `<h1>${{ power: "Published facility power", locations: "Mapped source records", hardware: "Published GPU clusters", coverage: "Countries & territories" }[kind]}</h1><p>${kind === "power" ? `${model.known} of ${model.count} Epoch AI centers in this scope report a “Current power (MW)” value. The subtotal is ${uiPower(model.power)}. This is the publisher’s facility-power model, not critical IT load or a world-market estimate.` : kind === "hardware" ? "Every native GPU record in this scope is counted, including superseded phases and anonymous records. The count is not a unique operating-cluster census." : kind === "locations" ? "Locations combine native publisher coordinates, community geometry centers and separately attributed address geocodes. Records across publications can refer to the same facility." : "Distinct named source countries and territories in the active scope. Geographic source coverage is not a measure of completeness within a country."}</p><p>Source observations retain their own dates. Filters and geographic scope apply before this measurement is calculated.</p><button class="btn primary" data-ua-export-all>Export the underlying records ↓</button><button class="btn" data-action="nav" data-id="data">Open original source files</button>`;
}
document.addEventListener("click", (e) => {
  const button = e.target.closest("button");
  if (!button) return;
  const d = button.dataset;
  if (d.uiOpenGuide) { uaStartGuide(); return; }
  if (d.uiOperator) {
    uaGo({operator: d.uiOperator});
    return;
  }
  if (d.uiMarket === "virginia") {
    uaGo({scale: 3, country: "United States", scope: "viewport", selected: null, camera: {flat:true,lat:38.75,lon:-77.5,zoom:1,bounds:[-78.5,38,-76.5,39.5]}});
    return;
  }
  if (d.uiPreset) {
    uiPreset(d.uiPreset);
    return;
  }
  if ("uiRefine" in d) {
    const panel = $(".ua-filter-panel");
    panel.open = true;
    panel.scrollIntoView({ block: "center", behavior: "smooth" });
    $("#ua-query")?.focus({ preventScroll: true });
    return;
  }
  if (d.uiClearFilter) {
    uaGo({
      [d.uiClearFilter]: ["region", "country"].includes(d.uiClearFilter)
        ? "All"
        : d.uiClearFilter === "coverage"
          ? "all"
          : "",
    });
    return;
  }
  if (d.uiMeasure) {
    uiMeasure(d.uiMeasure);
    return;
  }
  if (d.uiPhase) {
    uaState.phase = d.uiPhase;
    document
      .querySelectorAll("[data-ui-phase]")
      .forEach((b) =>
        b.setAttribute("aria-pressed", String(b.dataset.uiPhase === d.uiPhase)),
      );
    uaState.feature = null;
    globe?.features?.forEach((f) => (f.selected = false));
    if (globe) globe.dirty = true;
    uaRemember();
    history.pushState(null, "", uaURL());
    $(".ua-rail").innerHTML = uaSelectedRail(
      uaRecord(uaState.selected),
      uaRows(),
    );
    return;
  }
  if (d.uiClaim) {
    const row = atlasResearchProfile(
      uaRecord(uaState.selected)?.native,
    ).rows.find((r) => r.id === d.uiClaim);
    if (!row) return;
    uaRemember();
    openDrawer("atlas-claim");
    $("#drawer-type").textContent = "ORIGINAL PROJECT DISCLOSURE";
    $("#drawer-content").innerHTML =
      "<h1>Follow the evidence.</h1>" + atlasResearchClaim(row);
  }
});
// Meaningful six-scale entry points when the world has no selected facility.
document.addEventListener(
  "click",
  (e) => {
    if (state.view !== "atlas") return;
    const button = e.target.closest("[data-ua-scale]");
    if (!button || button.tagName !== "BUTTON" || uaRecord(uaState.selected))
      return;
    const scale = Number(button.dataset.uaScale);
    if (
      (scale === 1 && uaState.region === "All") ||
      (scale === 2 && uaState.country === "All")
    ) {
      e.preventDefault();
      e.stopImmediatePropagation();
      uiPreset(scale === 1 ? "atlantic" : "region");
    }
  },
  true,
);

document.addEventListener("click", (e) => {
  const b = e.target.closest("[data-ua-topic]");
  if (b && state.view === "atlas")
    document
      .querySelectorAll("[data-ua-topic]")
      .forEach((x) =>
        x.setAttribute(
          "aria-pressed",
          String(x.dataset.uaTopic === uaState.topic),
        ),
      );
});
uaPhysicalRail = function (record, source) {
  const canSave = Boolean(
      globe?.manifest?.features.some((f) => f.id === record.id),
    ),
    area = record.derived_outline_area,
    voltage = record.tags?.voltage,
    height = record.height_m,
    date = record.observed_at || record.updated_at || "",
    value = area
      ? "≈ " + fmt(area.rounded_m2)
      : height != null
        ? fmt(height, 1)
        : voltage
          ? String(voltage)
          : "—",
    unit = area
      ? "m² roof outline"
      : height != null
        ? "m source height"
        : voltage
          ? "V native tag"
          : "No height supplied";
  return `<section id="ua-feature-selection" class="ua-editorial ua-selected">${uiKicker("PHYSICAL SOURCE FEATURE", `<button class="text-button" data-ua-clear-feature aria-label="Clear physical selection">${uiIcon("close")}</button>`)}<h2 tabindex="-1">${esc(record.name)}</h2><p>${esc(source.name)} · ${record.observed_at ? "historical roof interpretation" : "native mapped feature"}</p><div class="ui-feature-metrics"><div><b>${esc(value)}</b><span>${unit}</span></div><div><b>${esc(date.slice(0, 4) || "—")}</b><span>${record.observed_at ? "Image observation" : "Source edit"}</span></div><div><b>${height == null ? "—" : fmt(height, 1) + " m"}</b><span>${height == null ? "Height unreported" : "Mapped height"}</span></div></div><div class="ua-actions"><button class="btn primary" ${canSave ? "data-ui-save-feature" : 'data-ua-export-feature="' + esc(record.id) + '"'}>${uiIcon("source")} ${canSave ? "Save physical evidence" : "Export physical evidence"}</button><button class="text-button" data-ua-export-feature="${esc(record.id)}">Export record ↓</button><button class="text-button" data-ua-context-source>Source provenance ${uiIcon("arrow")}</button></div><p class="ui-feature-id">${esc(record.id)} · version ${esc(record.source_version || record.review_sha256?.slice(0, 12) || "reviewed interpretation")}</p>${
    record.tags
      ? `<details class="ui-feature-tags"><summary>Inspect all native tags</summary><dl class="ua-facts">${Object.entries(
          record.tags,
        )
          .map(([k, v]) => `<div><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`)
          .join("")}</dl></details>`
      : ""
  }</section><section class="ua-editorial">${uiKicker("02 / KEY TAKEAWAYS")}<div class="ui-takeaways"><div><span>01</span><p><b>Independent physical evidence</b>${esc(record.derivation || "Source geometry and edit history remain distinct from project ownership and capacity.")}</p></div><div><span>02</span><p><b>Project power is separately scoped</b>${uaMeasure(source).value == null ? "This source does not establish facility power." : esc(compact(uaMeasure(source).value) + " " + uaMeasure(source).unit + " · " + uaMeasure(source).label)}. No building-level allocation is inferred.</p></div></div><button class="text-button" data-ua-clear-feature>Return to ${esc(source.name)} ${uiIcon("arrow")}</button></section><section class="ua-editorial">${uiKicker("03 / PROJECT COUNTERPARTIES")}<div class="ui-partners">${uiPartners(source)}</div></section>`;
};
document.addEventListener("click", (e) => {
  if (!e.target.closest("[data-ui-save-feature]")) return;
  const record = globe?.features?.find(
    (f) => f.record.id === uaState.feature,
  )?.record;
  if (!record) return;
  if (globe.manifest?.features.some((f) => f.id === record.id)) {
    const entry = { ...campusVersionEntry(globe.manifest, record), atlas_view: true };
    saved.sourceFeatures = saved.sourceFeatures.filter(
      (x) =>
        x.feature_id !== entry.feature_id || x.project_id !== entry.project_id,
    );
    saved.sourceFeatures.push(entry);
    save();
    toast(
      storageOK
        ? "Physical evidence saved to your research shelf."
        : "Saved for this session. Export before closing.",
    );
  } else {
    download("physical-evidence-" + record.id + ".json", {
      record,
      capture: uaContext?.capture,
    });
    toast("Native physical evidence exported with its source capture.");
  }
});
let uiTourReturn = null;
uaStartGuide = function () {
  uaRemember();
  uiTourReturn = state.view === "atlas" ? uaURL() : researchCurrentHash();
  uaGuideStep(0);
};
uaGuideStep = function (step) {
  const stops = [
    [
      "world",
      "The global landscape",
      "Start with all six source collections. Rotate the globe or select a geographic cluster to inspect its actual members.",
    ],
    [
      "atlantic",
      "A transatlantic system",
      "North America and Europe share a geographic view. Country coverage and power remain scoped to their original publications.",
    ],
    [
      "region",
      "The Midwest and East Coast",
      "Inspect regional concentrations. Roads and boundaries are reference geography; a nearby line does not establish utility service.",
    ],
    [
      "metro",
      "Chicago to New Carlisle",
      "The visible map now sets the record scope. Explore the local facilities, then follow the selected campus into its physical evidence.",
    ],
    [
      "campus",
      "Inside New Carlisle",
      "Explore dated imagery, reviewed roof outlines, independently mapped electricity context and the project’s reported power scopes.",
    ],
    [
      "facility",
      "A single physical feature",
      "The selected Helios roof has its own inspector and source version. Its geometry does not inherit the parent project’s capacity.",
    ],
  ];
  if (step >= stops.length) {
    $("#tour").hidden = true;
    toast("Journey complete. Keep exploring or return to a saved view.");
    return;
  }
  const [preset, title, copy] = stops[step];
  uiPreset(preset);
  window.scrollTo({ top: 0, behavior: "instant" });
  const tour = $("#tour");
  tour.classList.add("ui-guide");
  tour.hidden = false;
  tour.innerHTML = `<div class="ui-kicker"><span>GUIDED EXPLORATION · ${step + 1} / ${stops.length}</span><button class="text-button" data-ui-end-guide aria-label="Close guided exploration">${uiIcon("close")}</button></div><h3>${title}</h3><p>${copy}</p><div class="ui-guide-actions"><button class="text-button" data-ui-return-guide>Return to my view</button>${step ? `<button class="btn" data-ua-guide-next="${step - 1}">Back</button>` : ""}<button class="btn primary" data-ua-guide-next="${step + 1}">${step === stops.length - 1 ? "Finish" : "Next scale"} ${uiIcon("arrow")}</button></div>`;
};
document.addEventListener("click", (e) => {
  if (e.target.closest("[data-ui-end-guide]")) $("#tour").hidden = true;
  if (e.target.closest("[data-ui-return-guide]")) {
    $("#tour").hidden = true;
    if (uiTourReturn) location.hash = uiTourReturn;
  }
});
document.addEventListener("keydown", (e) => {
  if (
    e.key === "Escape" &&
    !$("#tour").hidden &&
    $("#tour").classList.contains("ui-guide")
  )
    $("#tour").hidden = true;
});
function uiMobileRail(html) {
  return html.replace(
    "</section>",
    '</section><button class="ui-mobile-inspector" data-ui-mobile-details aria-expanded="false">Show full dossier <span>＋</span></button>',
  );
}
const uiDesktopSelectedRail = uaSelectedRail;
uaSelectedRail = function (r, rows) {
  const html = uiDesktopSelectedRail(r, rows);
  return r ? uiMobileRail(html) : html;
};
const uiDesktopPhysicalRail = uaPhysicalRail;
uaPhysicalRail = function (record, source) {
  const html = uiDesktopPhysicalRail(record, source);
  const notice = !uaRows().some((r) => r.id === source.id)
    ? `<p class="ua-notice">Outside the active filters. <button class="text-button" data-ua-reveal>Show its scope →</button></p>`
    : "";
  return uiMobileRail(html.replace("</h2>", "</h2>" + notice));
};
const uiPreviousGo = uaGo;
uaGo = function (patch = {}, replace = false) {
  if (
    "selected" in patch &&
    patch.selected !== uaState.selected &&
    !("phase" in patch)
  )
    uaState.phase = null;
  uiPreviousGo(patch, replace);
};
ATLAS.explorer.go = uaGo;
document.addEventListener("click", (e) => {
  const button = e.target.closest("[data-ui-mobile-details]");
  if (!button) return;
  const rail = button.closest(".ua-rail"),
    open = !rail.classList.contains("ui-mobile-open");
  rail.classList.toggle("ui-mobile-open", open);
  button.setAttribute("aria-expanded", String(open));
  button.innerHTML =
    (open ? "Show summary" : "Show full dossier") +
    " <span>" +
    (open ? "−" : "＋") +
    "</span>";
});
const uiOriginalContextSource = uaContextSource;
uaContextSource = function () {
  uiOriginalContextSource();
  const s = AtlasTerrain.source;
  $("#drawer-content").insertAdjacentHTML(
    "beforeend",
    `<h2>Background relief</h2><p>${esc(s.title)} · ${esc(s.publisher)} · ${esc(s.license)}. ${esc(s.transformation)}</p><p>Reference scale: ${esc(s.scale)}. This raster supplies geographic context, not current imagery or facility observations.</p><p class="ua-source-code">Published texture SHA-256: ${esc(s.sha256)}<br>Source raster SHA-256: ${esc(s.source_raster_sha256)}</p>${catalogLink(s.source_url, "Original geographic raster", "btn")}${catalogLink(s.license_url, "Reuse terms", "btn")}<button class="btn" data-ui-export-terrain>Export relief provenance ↓</button>`,
  );
};
document.addEventListener("click", (e) => {
  if (e.target.closest("[data-ui-export-terrain]"))
    download("compute-atlas-relief-provenance.json", AtlasTerrain.source);
});

const uiBaseRefreshData = uaRefreshData;
uaRefreshData = function () {
  uiBaseRefreshData();
  const chips = document.querySelector(".ui-active-filters");
  if (chips) chips.innerHTML = uiFilterChips();
};
// Public integrations resolve the current production route owners.
ATLAS.explorer.url = () => uaURL();
ATLAS.explorer.go = (...args) => uaGo(...args);

// A shared physical view identifies the evidence version, not just its filename.
function uiSourceVersions() {
  const record = uaRecord(uaState.selected);
  if (uaState.scale < 4 || !record) return {};
  const scenes = CAMPUS_SCENES.scenes.filter((s) => s.project_id === record.id);
  const scene = uaState.scene
    ? scenes.find((s) => s.id === uaState.scene)
    : scenes[0];
  const electricity = ENERGY_COLLECTIONS.find(
    (c) =>
      c.scene_id === scene?.id &&
      c.features.some((f) => f.id === uaState.feature),
  );
  return {
    imageversion: scene?.image.sha256,
    featureversion: scene?.features.find((f) => f.id === uaState.feature)
      ?.review_sha256,
    contextversion:
      electricity?.response_sha256 ||
      (!scene ? uaCaptureFor(record)?.sha256 : null),
  };
}
const uiUnpinnedURL = uaURL;
uaURL = function () {
  const url = uiUnpinnedURL(),
    versions = uiSourceVersions();
  return (
    url +
    ["imageversion", "featureversion", "contextversion"]
      .map((key) => {
        const value = uaState[key] || versions[key];
        return uaState.scale >= 4 && value
          ? "&" + key + "=" + encodeURIComponent(value)
          : "";
      })
      .join("")
  );
};
const uiUnpinnedParse = uaParse;
uaParse = function (query) {
  const params = new URLSearchParams(query);
  for (const key of ["imageversion", "featureversion", "contextversion"])
    uaState[key] = params.get(key)?.slice(0, 128) || null;
  uiUnpinnedParse(query);
};
const uiUnpinnedGo = uaGo;
uaGo = function (patch = {}, replace = false) {
  const changesRecord =
    "selected" in patch && patch.selected !== uaState.selected;
  const changesScene = "scene" in patch && patch.scene !== uaState.scene;
  if (changesRecord || changesScene) {
    for (const key of ["imageversion", "featureversion", "contextversion"])
      if (!(key in patch)) uaState[key] = null;
    if (changesScene && !("feature" in patch))
      patch = { ...patch, feature: null };
  }
  if (
    "feature" in patch &&
    patch.feature !== uaState.feature &&
    !("featureversion" in patch)
  )
    uaState.featureversion = null;
  uiUnpinnedGo(patch, replace);
};
function uiVersionProblem() {
  if (uaState.scale < 4) return null;
  const versions = uiSourceVersions();
  for (const [key, label] of [
    ["imageversion", "Historical image"],
    ["featureversion", "Physical feature"],
    ["contextversion", "Native context capture"],
  ]) {
    if (uaState[key] && uaState[key] !== versions[key])
      return { label, requested: uaState[key], available: versions[key] };
  }
  return null;
}
const uiVersionedMount = uaMount;
uaMount = function () {
  const problem = uiVersionProblem();
  if (!problem) {
    uiVersionedMount();
    return;
  }
  globe?.destroy();
  globe = null;
  const stage = document.querySelector(".ua-map-stage");
  if (!stage) return;
  stage.classList.add("ui-source-unavailable");
  stage.insertAdjacentHTML(
    "beforeend",
    `<section class="ui-source-recovery" role="status"><div class="eyebrow">SOURCE VERSION UNAVAILABLE</div><h2>${esc(problem.label)} has changed.</h2><p>This shared view requests evidence that is not included in this publication. Its identity is retained; the current capture has not been substituted.</p><dl><dt>Requested version</dt><dd>${esc(problem.requested)}</dd><dt>Available version</dt><dd>${esc(problem.available || "Not included")}</dd></dl><button class="btn primary" data-ui-recover-source>Review the available publication →</button></section>`,
  );
};
document.addEventListener("click", (event) => {
  if (event.target.closest("[data-ui-recover-source]")) {
    const scenes = CAMPUS_SCENES.scenes.filter(
      (s) => s.project_id === uaState.selected,
    );
    const scene = scenes.find((s) => s.id === uaState.scene) || scenes[0];
    uaGo(
      {
        imageversion: null,
        featureversion: null,
        contextversion: null,
        scene: scene?.id || null,
        feature:
          scene &&
          !scene.features.some((f) => f.id === uaState.feature) &&
          !ENERGY_COLLECTIONS.some(
            (c) =>
              c.scene_id === scene.id &&
              c.features.some((f) => f.id === uaState.feature),
          )
            ? null
            : uaState.feature,
      },
      true,
    );
  }
  if (event.target.closest("[data-ui-clear-phase]"))
    uaGo({ phase: null }, true);
});
// Feature and phase identities are mutually exclusive, including event-only selections.
document.addEventListener(
  "ua-feature-select",
  () => {
    uaState.phase = null;
    uaState.featureversion = null;
    uaState.contextversion = null;
  },
  true,
);
document.addEventListener(
  "click",
  (event) => {
    if (event.target.closest("[data-ui-phase],[data-ua-clear-feature]")) {
      uaState.featureversion = null;
      if (globe?.manifest) uaState.contextversion = null;
    }
  },
  true,
);
document.addEventListener("change", (event) => {
  if (
    event.target.id === "ua-feature-choice" &&
    !event.target.value &&
    globe?.features
  ) {
    uaState.featureversion = null;
    if (globe.manifest) uaState.contextversion = null;
    globe.features.forEach((f) => (f.selected = false));
    globe.dirty = true;
    history.replaceState(null, "", uaURL());
  }
});
const uiAvailablePhaseRail = uaSelectedRail;
uaSelectedRail = function (record, rows) {
  if (
    record &&
    uaState.phase &&
    !uiPhaseRows(record).some((p) => p.id === uaState.phase)
  )
    return `<section class="ua-editorial ua-selected"><div class="eyebrow">REQUESTED POWER SCOPE</div><h2>Power scope unavailable.</h2><p>${esc(uaState.phase)} is not included in this publication. No other phase has been selected.</p><button class="btn primary" data-ui-clear-phase>Return to ${esc(record.name)} →</button></section>`;
  return uiAvailablePhaseRail(record, rows);
};

// Keep physical selection controls on the spatial hero; evidence follows immediately.
const uiSourceInspector = uaPhysicalInspector;
uaPhysicalInspector = function (id) {
  uiSourceInspector(id);
  const article = document.querySelector('.ui-editorial-atlas');
  if (!article || uaState.scale < 4) return;
  article.dataset.uaScale = uaState.scale;
  const controls = document.querySelector('#ua-physical-inspector');
  const stage = document.querySelector('.ua-map-stage');
  if (controls && stage && controls.parentElement !== stage) stage.append(controls);
  if (controls) controls.classList.toggle("ui-feature-unavailable", !!id && !globe?.features?.some(f => f.record.id === id));
  const detail = document.querySelector('#ua-topic-content');
  const source = uaRecord(uaState.selected);
  if (detail && source && uaState.topic === 'overview') detail.innerHTML = uiOverview(source);
};
