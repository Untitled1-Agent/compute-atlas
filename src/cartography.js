'use strict';
/* Offline cartography. Every geographical line comes from the attributed source
 * layer. Land stippling is map texture, never synthetic facility observations. */
const ATLAS_CONTEXT = JSON.parse(document.getElementById('context-data')?.textContent || '{}');
const geographicRadians = Math.PI / 180;
const mercatorY = lat => Math.log(Math.tan(Math.PI / 4 + Math.max(-83, Math.min(83, lat)) * geographicRadians / 2));
const contextBounds = new WeakMap();
function lineBounds(line) {
  let bounds = contextBounds.get(line);
  if (!bounds) {
    bounds = [Infinity, Infinity, -Infinity, -Infinity];
    for (const p of line) { bounds[0] = Math.min(bounds[0], p[0]); bounds[1] = Math.min(bounds[1], p[1]); bounds[2] = Math.max(bounds[2], p[0]); bounds[3] = Math.max(bounds[3], p[1]); }
    contextBounds.set(line, bounds);
  }
  return bounds;
}

class ResearchMap {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d', {alpha: false});
    this.level = state.spatialLevel || 0;
    this.scope = spatialScope(this.level, spatialDefaultSite());
    const selected = spatialDefaultSite();
    const asia = selected && spatialContinent(selected) === 'Asia';
    this.lat = this.level === 1 ? (asia ? 30 : 40) : 24;
    this.lon = this.level === 1 ? (asia ? 105 : -43) : -48;
    this.zoom = this.level === 1 ? 1.53 : 1;
    this.flat = this.level >= 2;
    this.labels = state.spatialLabels !== false;
    this.bounds = [...this.scope.bounds];
    this.cameraKey=[this.level,this.scope.label,state.filter.company,state.filter.country,state.filter.q,state.spatialEvidence].join('|');
    const camera=state.spatialCamera?.[this.cameraKey];
    if(camera){this.lat=camera.lat;this.lon=camera.lon;this.zoom=camera.zoom;this.bounds=[...camera.bounds];this.flat=camera.flat;}
    this.groups = []; this.target = null; this.drag = null; this.hover = null;
    this.dirty = true; this.destroyed = false; this.listeners = [];
    this.markerNodes = [...canvas.parentElement.querySelectorAll('.atlas-map-marker')];
    this.stars = Array.from({length: 180}, (_, i) => ({x: (i * 7717 % 997) / 997, y: (i * 4199 % 991) / 991, r: i % 11 ? .45 : .85}));
    this.on('pointerdown', event => {
      if (event.button !== 0) return;
      this.drag = {x: event.clientX, y: event.clientY, lat: this.lat, lon: this.lon, bounds: [...this.bounds], moved: false};
      this.canvas.setPointerCapture(event.pointerId); this.target = null; hideTip();
    });
    this.on('pointermove', event => this.pointerMove(event));
    this.on('pointerup', event => this.pointerUp(event));
    this.on('pointercancel', () => { this.drag = null; });
    this.on('pointerleave', () => { if (!this.drag) { this.hover = null; hideTip(); this.dirty = true; } });
    this.on('wheel', event => this.wheel(event), {passive: false});
    this.on('keydown', event => {
      if (!['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(event.key)) return;
      event.preventDefault();
      const dx = event.key === 'ArrowLeft' ? -1 : event.key === 'ArrowRight' ? 1 : 0;
      const dy = event.key === 'ArrowUp' ? 1 : event.key === 'ArrowDown' ? -1 : 0;
      if (this.flat) {
        const x = (this.bounds[2] - this.bounds[0]) * .08 * dx, y = (this.bounds[3] - this.bounds[1]) * .08 * dy;
        this.bounds = [this.bounds[0] + x, this.bounds[1] + y, this.bounds[2] + x, this.bounds[3] + y];
      } else { this.lon += dx * 12; this.lat = Math.max(-80, Math.min(80, this.lat + dy * 9)); }
      this.dirty = true;
    });
    this.resizeObserver = new ResizeObserver(() => this.resize());
    this.resizeObserver.observe(canvas.parentElement); this.resize();
    this.frame = () => {
      if (this.destroyed) return;
      if (this.target) {
        const dl = ((this.target.lon - this.lon + 540) % 360) - 180, da = this.target.lat - this.lat, dz = this.target.zoom - this.zoom;
        this.lon += dl * .14; this.lat += da * .14; this.zoom += dz * .14; this.dirty = true;
        if (Math.abs(dl) + Math.abs(da) + Math.abs(dz) < .03) { Object.assign(this, this.target); this.target = null; }
      }
      if (this.dirty) { this.draw(); this.dirty = false; }
      // RAF is only alive while this one visible map exists; no background animation.
      this.raf = requestAnimationFrame(this.frame);
    };
    this.raf = requestAnimationFrame(this.frame);
  }
  on(type, fn, options) { this.canvas.addEventListener(type, fn, options); this.listeners.push([type, fn, options]); }
  resize() {
    const parent = this.canvas.parentElement;
    this.w = parent.clientWidth; this.h = parent.clientHeight;
    this.dpr = Math.min(window.devicePixelRatio || 1, 2);
    this.canvas.width = Math.round(this.w * this.dpr); this.canvas.height = Math.round(this.h * this.dpr);
    this.canvas.style.width = this.w + 'px'; this.canvas.style.height = this.h + 'px'; this.dirty = true;
  }
  destroy() {
    if(!this.skipCameraSave){state.spatialCamera ||= {};state.spatialCamera[this.cameraKey]={lat:this.lat,lon:this.lon,zoom:this.zoom,bounds:[...this.bounds],flat:this.flat};}
    this.destroyed = true; cancelAnimationFrame(this.raf); this.resizeObserver.disconnect();
    this.listeners.forEach(([type, fn, options]) => this.canvas.removeEventListener(type, fn, options)); hideTip();
  }
  flyTo(lat, lon, zoom = 1.5) {
    // Compatibility with existing tours / research links; a requested hemisphere
    // never reclassifies the underlying evidence or changes geographic coordinates.
    this.flat = false;
    this.target = {lat, lon, zoom};
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) { Object.assign(this, this.target); this.target = null; this.dirty = true; }
  }
  wheel(event) {
    // Pixel-, line- and page-based wheels all feed the same continuous camera.
    // Do not ignore small trackpad deltas or replace the canvas per wheel tick.
    if (event.ctrlKey) return; // Preserve the browser's accessibility zoom gesture.
    event.preventDefault();
    const delta = Math.max(-320, Math.min(320, event.deltaY * (event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? this.h : 1)));
    if (!delta) return;
    const next = this.zoom * Math.exp(-delta * .0025);
    if (next > 3.2 && this.level < 4) {
      const rect=this.canvas.getBoundingClientRect(), x=event.clientX-rect.left, y=event.clientY-rect.top;
      const nearest=[...this.groups].sort((a,b)=>Math.hypot(a.x-x,a.y-y)-Math.hypot(b.x-x,b.y-y))[0];
      spatialTransition({level:this.level+1,selected:nearest?.sites?.[0]?.id});
    } else if (next < .65 && this.level > 0) spatialTransition({level:this.level-1});
    else this.zoomTo(next);
  }
  zoomTo(zoom) {
    const next = Math.min(12, Math.max(.6, zoom));
    if (this.flat) {
      const ratio = this.zoom / next, [x0, y0, x1, y1] = this.bounds, cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
      this.bounds = [cx + (x0 - cx) * ratio, cy + (y0 - cy) * ratio, cx + (x1 - cx) * ratio, cy + (y1 - cy) * ratio];
    }
    this.zoom = next; if (this.target) this.target.zoom = next; this.dirty = true;
  }
  project(lon, lat) {
    if (this.flat) return {x: this.cx + (lon * geographicRadians - this.mx) * this.scale, y: this.cy - (mercatorY(lat) - this.my) * this.scale, z: 1};
    const a = lat * geographicRadians, b = (lon - this.lon) * geographicRadians, cos = Math.cos(a), sin = Math.sin(a);
    return {x: this.cx + this.radius * cos * Math.sin(b), y: this.cy - this.radius * (this.cl0 * sin - this.sl0 * cos * Math.cos(b)), z: this.sl0 * sin + this.cl0 * cos * Math.cos(b)};
  }
  projectNow(lon, lat) { this.prepare(); return this.project(lon, lat); }
  prepare() {
    this.cx = this.w * .51; this.cy = this.h * .48;
    this.radius = Math.min(this.w * .47, this.h * .455) * this.zoom;
    this.sl0 = Math.sin(this.lat * geographicRadians); this.cl0 = Math.cos(this.lat * geographicRadians);
    if (this.flat) {
      const [x0, y0, x1, y1] = this.bounds;
      this.mx = (x0 + x1) * geographicRadians / 2; this.my = (mercatorY(y0) + mercatorY(y1)) / 2;
      this.scale = Math.min(this.w / ((x1 - x0) * geographicRadians), this.h / (mercatorY(y1) - mercatorY(y0))) * .97;
      this.cy = this.h * .47;
    }
  }
  pointerMove(event) {
    if (this.drag) {
      const dx = event.clientX - this.drag.x, dy = event.clientY - this.drag.y;
      if (Math.abs(dx) + Math.abs(dy) > 4){this.drag.moved=true;state.spatialFly='custom';document.querySelectorAll('[data-atlas-action="fly"]').forEach(b=>b.classList.remove('active'));}
      if (this.flat) {
        const x = dx / this.scale / geographicRadians, y = dy / this.scale / geographicRadians * Math.cos((this.bounds[1] + this.bounds[3]) / 2 * geographicRadians);
        this.bounds = [this.drag.bounds[0] - x, this.drag.bounds[1] + y, this.drag.bounds[2] - x, this.drag.bounds[3] + y];
      } else { this.lon = this.drag.lon - dx * .27 / this.zoom; this.lat = Math.max(-85, Math.min(85, this.drag.lat + dy * .23 / this.zoom)); }
      this.dirty = true; return;
    }
    const rect = this.canvas.getBoundingClientRect(), x = event.clientX - rect.left, y = event.clientY - rect.top;
    const hit = this.groups.find(g => Math.hypot(g.x - x, g.y - y) < g.r + 7);
    if (hit !== this.hover) { this.hover = hit || null; this.dirty = true; }
    this.canvas.style.cursor = hit ? 'pointer' : 'grab';
    if (hit) { const s = hit.sites[0]; showTip(event.clientX, event.clientY, `<b>${esc(s.name)}</b><br>${esc(s.location)}<br>${spatialPower(s) == null ? 'IT power not quantified' : fmt(spatialPower(s)) + ' MW · estimate'}${hit.sites.length>1?'<br>'+hit.sites.length+' clustered records · '+hit.known+' quantified<br>'+(hit.mw==null?'No comparable aggregate':fmt(hit.mw)+' MW cluster subtotal'):''}<br><small>Research anchor · click to explore</small>`); }
    else hideTip();
  }
  pointerUp(event) {
    if (!this.drag) return;
    const moved = this.drag.moved; this.drag = null;
    try { this.canvas.releasePointerCapture(event.pointerId); } catch (_) { /* Pointer may have been cancelled. */ }
    if (moved) return;
    const rect = this.canvas.getBoundingClientRect(), x = event.clientX - rect.left, y = event.clientY - rect.top;
    const hit = this.groups.find(g => Math.hypot(g.x - x, g.y - y) < g.r + 8);
    if (hit) spatialTransition({selected: hit.sites[0].id, level: Math.min(5, this.level + 1)});
  }
  path(line, stroke, width, fill = null) {
    const c = this.ctx;
    if (this.flat) {
      const b = lineBounds(line), v = this.bounds, px = (v[2] - v[0]) * .3, py = (v[3] - v[1]) * .3;
      if (b[2] < v[0] - px || b[0] > v[2] + px || b[3] < v[1] - py || b[1] > v[3] + py) return;
    }
    c.beginPath(); let previous = null, continuous = true;
    for (const point of line) {
      const p = this.project(point[0], point[1]);
      if (p.z <= 0) { previous = null; continuous = false; continue; }
      if (previous && Math.abs(p.x - previous.x) < this.w * .65) c.lineTo(p.x, p.y); else c.moveTo(p.x, p.y);
      previous = p;
    }
    if (fill && continuous) { c.fillStyle = fill; c.fill(); }
    c.strokeStyle = stroke; c.lineWidth = width; c.stroke();
  }
  draw() {
    if (!this.w || !this.h) return;
    const c = this.ctx, w = this.w, h = this.h;
    c.setTransform(this.dpr, 0, 0, this.dpr, 0, 0); this.prepare();
    c.fillStyle = '#07141e'; c.fillRect(0, 0, w, h);
    for (const star of this.stars) { c.fillStyle = '#38616c88'; c.fillRect(star.x * w, star.y * h, star.r, star.r); }
    const R = this.radius, cx = this.cx, cy = this.cy;
    if (!this.flat) {
      const halo = c.createRadialGradient(cx, cy, R * .95, cx, cy, R * 1.12);
      halo.addColorStop(0, '#5bbeb42e'); halo.addColorStop(.6, '#318b9320'); halo.addColorStop(1, '#318b9300');
      c.fillStyle = halo; c.beginPath(); c.arc(cx, cy, R * 1.12, 0, Math.PI * 2); c.fill();
    }
    c.save();
    if (!this.flat) { c.beginPath(); c.arc(cx, cy, R, 0, Math.PI * 2); c.clip(); }
    const sea = c.createRadialGradient(w * .4, h * .3, 30, w * .5, h * .5, w * .8);
    sea.addColorStop(0, '#0b2530'); sea.addColorStop(.6, '#081923'); sea.addColorStop(1, '#050e17');
    c.fillStyle = sea; c.fillRect(0, 0, w, h);
    const step = this.flat ? (this.level >= 3 ? .5 : 5) : 30;
    const lon0 = this.flat ? Math.floor(this.bounds[0] / step) * step - step : -180;
    const lon1 = this.flat ? this.bounds[2] + step : 180;
    const lat0 = this.flat ? Math.floor(this.bounds[1] / step) * step - step : -75;
    const lat1 = this.flat ? this.bounds[3] + step : 75;
    for (let lon = lon0; lon <= lon1; lon += step) this.path(Array.from({length: 91}, (_, i) => [lon, -85 + i * 170 / 90]), '#28515f38', .65);
    for (let lat = lat0; lat <= lat1; lat += step) this.path(Array.from({length: 181}, (_, i) => [-180 + i * 2, lat]), '#28515f38', .65);
    // Existing, attributed land points add cartographic texture only.
    if (!this.flat) for (const [lon, lat] of W.dots || []) {
      const p = this.project(lon, lat); if (p.z <= 0) continue;
      const size = .65 + .4 * p.z;
      c.fillStyle = `rgba(78,151,163,${.18 + p.z * .34})`; c.fillRect(p.x, p.y, size, size);
    }
    for (const line of (this.flat && ATLAS_CONTEXT.coast?.length ? ATLAS_CONTEXT.coast : W.lines || [])) this.path(line, this.flat ? '#33687b' : '#387688a0', this.flat ? .85 : .6);
    if (this.flat) {
      for (const line of ATLAS_CONTEXT.lakes || []) this.path(line, '#32708490', .8, '#091a28');
      c.setLineDash([3, 4]); for (const line of ATLAS_CONTEXT.states || []) this.path(line, '#43809470', .65); c.setLineDash([]);
      if (state.spatialRoads !== false) for (const line of ATLAS_CONTEXT.roads || []) this.path(line, this.level >= 3 ? '#467d8a69' : '#3358654a', this.level >= 3 ? .8 : .55);
      this.drawPlaces();
    }
    const shade = c.createLinearGradient(0, 0, w, h); shade.addColorStop(0, '#07121a00'); shade.addColorStop(.65, '#04101900'); shade.addColorStop(1, '#040c1870');
    c.fillStyle = shade; c.fillRect(0, 0, w, h); c.restore();
    if (!this.flat) { c.strokeStyle = '#4b9eab65'; c.lineWidth = 1; c.beginPath(); c.arc(cx, cy, R, 0, Math.PI * 2); c.stroke(); }
    this.drawMarkers();
    const position = document.getElementById('geo-position');
    if (position) position.textContent = this.flat ? 'MERCATOR · GENERALIZED CONTEXT · APPROXIMATE ANCHORS' : `${this.lat.toFixed(1)}° N  ${Math.abs(this.lon).toFixed(1)}° ${this.lon < 0 ? 'W' : 'E'}  ·  DRAG TO ROTATE`;
    const live = document.getElementById('globe-live');
    if (live) live.textContent = `${this.scope.sites.length} research records; ${this.groups.length} visible markers or clusters. Use the record list for keyboard access.`;
  }
  drawPlaces() {
    const c = this.ctx, occupied = [];
    c.font = '11px -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif'; c.textAlign = 'left';
    for (const place of [...(ATLAS_CONTEXT.places || [])].sort((a, b) => a.rank - b.rank)) {
      const p = this.project(place.lon, place.lat), text = place.name;
      if (p.x < 25 || p.x > this.w - 70 || p.y < 90 || p.y > this.h - 100) continue;
      const width = c.measureText(text).width;
      if (occupied.some(b => Math.abs(b.y - p.y) < 26 && p.x < b.x + b.w + 30 && p.x + width > b.x - 30)) continue;
      if (occupied.length > (this.level >= 3 ? 11 : 17)) break;
      occupied.push({x: p.x, y: p.y, w: width}); c.fillStyle = '#72aab9'; c.beginPath(); c.arc(p.x, p.y, 1.8, 0, Math.PI * 2); c.fill();
      c.shadowColor = '#051019'; c.shadowBlur = 5; c.fillStyle = '#8eafbc'; c.fillText(text, p.x + 6, p.y + 4); c.shadowBlur = 0;
    }
  }
  drawMarkers() {
    const c = this.ctx, phase = state.spatialPhase || 'snapshot', selected = state.spatialSelected;
    this.groups = [];
    const points = [];
    for (const s of this.scope.sites) {
      const p = this.project(s.lon, s.lat);
      if (p.z <= .015 || p.x < 10 || p.x > this.w - 10 || p.y < 64 || p.y > this.h - 58) continue;
      points.push({s,p,mw:spatialComparable(s,phase)?spatialPower(s,phase):null});
    }
    // Screen-space clusters disclose their membership. Their centroids are only
    // cartographic placements, never new or more precise facility coordinates.
    const clusters = [];
    for (const point of [...points].sort((a,b)=>(b.mw||0)-(a.mw||0))) {
      const near = this.level <= 1 ? clusters.find(g=>Math.hypot(g.p.x-point.p.x,g.p.y-point.p.y)<(this.level===0?21:18)) : null;
      if(near){near.members.push(point);const n=near.members.length;near.p={x:(near.p.x*(n-1)+point.p.x)/n,y:(near.p.y*(n-1)+point.p.y)/n,z:Math.min(near.p.z,point.p.z)};}
      else clusters.push({p:{...point.p},members:[point]});
    }
    const visible=clusters.map(g=>{
      const chosen=g.members.find(m=>m.s.id===selected)||g.members[0];
      const known=g.members.filter(m=>m.mw!=null),mw=known.length?known.reduce((n,m)=>n+m.mw,0):null;
      const r=Math.max(4,Math.min(this.flat?23:24,3+Math.sqrt(mw||0)*.32));
      const item={s:chosen.s,p:g.p,r,mw,members:g.members,known:known.length};
      this.groups.push({x:g.p.x,y:g.p.y,z:g.p.z,r,mw,known:known.length,sites:[chosen.s,...g.members.filter(m=>m!==chosen).map(m=>m.s)]});return item;
    });
    // Small points remain genuine source anchors, not randomly generated sites.
    if(this.level<=1)for(const item of points){c.fillStyle='#95dce399';c.beginPath();c.arc(item.p.x,item.p.y,1.7,0,Math.PI*2);c.fill();}
    const ranked = [...visible].sort((a, b) => Number(b.s.id === selected) - Number(a.s.id === selected) || (b.mw || 0) - (a.mw || 0));
    const labels = [], labeled = new Set();
    if (this.labels) for (const item of ranked) {
      const {s, p, r} = item, name = item.members.length>1 ? (s.name.length>16?s.name.slice(0,15)+'…':s.name)+' + '+(item.members.length-1) : s.name.length > 26 ? s.name.slice(0, 24) + '…' : s.name;
      c.font = '11px -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif';
      const width = Math.max(c.measureText(name).width, 112), x = p.x + r + 9, y = p.y - 14;
      const left = x + width > this.w - 16 ? p.x - r - width - 12 : x;
      if (left < 8 || y < 85 || y > this.h - 135 || labels.some(b => Math.abs(b.y - y) < 46 && left < b.x + b.w + 8 && left + width > b.x - 8)) continue;
      if (labels.length >= (this.flat ? 8 : 7)) break;
      labels.push({x: left, y, w: width}); labeled.add(s.id);
      item.label = {left, y, width, name};
    }
    for (const item of visible) {
      const {s, p, r} = item, chosen = s.id === selected;
      const color = item.members.some(m=>m.s.review==='reviewed-model') ? '#83e8c6' : item.known ? '#78b8f7' : '#a18cfa';
      c.save();
      const halo = c.createRadialGradient(p.x, p.y, r * .3, p.x, p.y, r * 2.9);
      halo.addColorStop(0, color + '40'); halo.addColorStop(.4, color + '16'); halo.addColorStop(1, color + '00');
      c.fillStyle = halo; c.beginPath(); c.arc(p.x, p.y, r * 2.9, 0, Math.PI * 2); c.fill();
      c.shadowColor = color; c.shadowBlur = 13; c.strokeStyle = color; c.fillStyle = color + '3d'; c.lineWidth = chosen ? 2 : 1.15;
      c.beginPath(); c.arc(p.x, p.y, r, 0, Math.PI * 2); c.fill(); c.stroke(); c.shadowBlur = 0;
      c.fillStyle = '#c9fff1'; c.beginPath(); c.arc(p.x, p.y, Math.max(1.5, r * .13), 0, Math.PI * 2); c.fill();
      if (chosen) { c.strokeStyle = '#bdffec9c'; c.setLineDash([3, 4]); c.beginPath(); c.arc(p.x, p.y, r + 7, 0, Math.PI * 2); c.stroke(); }
      c.restore();
      if (item.label) {
        const b = item.label;
        c.fillStyle = '#06121beb'; c.fillRect(b.left - 5, b.y - 2, b.width + 10, 34);
        c.font = '11px -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif'; c.textAlign = 'left'; c.fillStyle = '#e5eeec'; c.fillText(b.name, b.left, b.y + 10);
        c.font = '10px ui-monospace,monospace'; c.fillStyle = '#8eb3bd';
        c.fillText(item.mw == null ? 'Native / unquantified' : (item.mw>=1000?fmt(item.mw/1000,2)+' GW':fmt(item.mw)+' MW') + (item.members.length>1?' · '+item.known+' estimates':' · estimate'), b.left, b.y + 25);
      }
    }
    for (const node of this.markerNodes) {
      const item = visible.find(v => v.s.id === node.dataset.id);
      node.hidden = !item; node.tabIndex = item ? 0 : -1;
      if(item)node.setAttribute('aria-label',item.members.length>1?item.members.length+' clustered records near '+item.s.name+'; '+item.known+' comparable estimates; select to explore':item.s.name+'; '+(item.mw==null?'IT not quantified':fmt(item.mw)+' MW estimate'));
      if (item) { node.style.left = item.p.x + 'px'; node.style.top = item.p.y + 'px'; node.style.width = node.style.height = Math.max(24, item.r * 2) + 'px'; }
    }
  }
}
// Keep the existing app/tour debug surface while replacing its visual renderer.
AtlasGlobe = ResearchMap;
