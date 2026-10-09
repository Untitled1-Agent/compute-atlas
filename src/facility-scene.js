'use strict';
/* Source-polygon 3D. Canvas projection, not synthetic satellite imagery.
 * OSM building heights are community tags. Missing heights are display-only.
 * Campus/industrial land is always a flat plane; points never become buildings.
 */
class FacilityScene {
  constructor(canvas, record, neighbors=[]) {
    this.canvas=canvas; this.ctx=canvas.getContext('2d',{alpha:false}); this.record=record;
    this.yaw=-.65; this.pitch=.68; this.zoom=1; this.pan={x:0,y:0}; this.listeners=[];
    this.destroyed=false; this.dirty=true; this.groups=[]; this.lat=record.lat; this.lon=record.lon;
    this.displayHeight=12; this.showContext=false; this.assumptions=true; this.labels=true;
    this.buildGeometry(neighbors);
    this.on('pointerdown', e=>{if(e.button!==0)return;this.drag={id:e.pointerId,x:e.clientX,y:e.clientY,yaw:this.yaw,pitch:this.pitch,pan:{...this.pan},shift:e.shiftKey};canvas.setPointerCapture(e.pointerId);});
    this.on('pointermove', e=>{if(!this.drag)return;let dx=e.clientX-this.drag.x,dy=e.clientY-this.drag.y;
      if(this.drag.shift)this.pan={x:this.drag.pan.x+dx,y:this.drag.pan.y+dy};
      else {this.yaw=this.drag.yaw+dx*.007;this.pitch=Math.max(.16,Math.min(1.48,this.drag.pitch+dy*.005));}this.dirty=true;});
    this.on('pointerup', e=>{this.drag=null;try{canvas.releasePointerCapture(e.pointerId);}catch(_){}});
    this.on('pointercancel',()=>{this.drag=null;});
    this.on('wheel',e=>{if(e.ctrlKey)return;e.preventDefault();const rect=canvas.getBoundingClientRect();this.zoomTo(this.zoom*Math.exp(-Math.max(-320,Math.min(320,e.deltaY*(e.deltaMode===1?16:e.deltaMode===2?this.h:1)))*.0025),{x:e.clientX-rect.left,y:e.clientY-rect.top});},{passive:false});
    this.on('keydown',e=>{if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','+','=','-','Home'].includes(e.key)){e.preventDefault();e.stopPropagation();
      if(e.key==='Home')this.reset();else if(['+','='].includes(e.key))this.zoomTo(this.zoom*1.2);else if(e.key==='-')this.zoomTo(this.zoom/1.2);
      else if(e.key==='ArrowLeft')this.yaw-=.12;else if(e.key==='ArrowRight')this.yaw+=.12;else this.pitch=Math.max(.16,Math.min(1.48,this.pitch+(e.key==='ArrowUp'?.09:-.09)));this.dirty=true;}});
    this.resizeObserver=new ResizeObserver(()=>this.resize());this.resizeObserver.observe(canvas.parentElement);this.resize();
    this.frame=()=>{if(this.destroyed)return;if(this.dirty){this.draw();this.dirty=false;}this.raf=requestAnimationFrame(this.frame);};this.raf=requestAnimationFrame(this.frame);
  }
  on(t,f,o){this.canvas.addEventListener(t,f,o);this.listeners.push([t,f,o]);}
  local(lon,lat){return [(lon-this.lon)*111320*Math.cos(this.lat*Math.PI/180),(lat-this.lat)*111320];}
  buildGeometry(neighbors){
    const selected=this.record, basePoints=(selected.geometry?.coordinates||[]).flat(2).map(p=>this.local(...p));
    this.extent=Math.max(20,...basePoints.map(p=>Math.hypot(...p)))*1.15;
    this.features=[selected,...neighbors.filter(r=>r.id!==selected.id&&r.geometry&&spatialDistance(selected,r)<.45).slice(0,60)]
      .map(r=>({record:r,selected:r.id===selected.id,polygons:(r.geometry?.coordinates||[]).map(poly=>poly.map(ring=>ring.map(p=>this.local(...p))))}));
  }
  resize(){this.w=this.canvas.parentElement.clientWidth;this.h=this.canvas.parentElement.clientHeight;this.dpr=Math.min(devicePixelRatio||1,2);this.canvas.width=Math.round(this.w*this.dpr);this.canvas.height=Math.round(this.h*this.dpr);this.canvas.style.width=this.w+'px';this.canvas.style.height=this.h+'px';this.dirty=true;}
  zoomTo(z,anchor=null){
    if(!Number.isFinite(z)||z<=0)return;
    const next=Math.max(.3,Math.min(8,z)),ratio=next/this.zoom;
    // Perspective is independent of zoom: this keeps the projected point under
    // the cursor fixed, even after orbiting or shift-panning the scene.
    if(anchor&&Number.isFinite(anchor.x)&&Number.isFinite(anchor.y))this.pan={
      x:anchor.x-this.w*.5-(anchor.x-this.w*.5-this.pan.x)*ratio,
      y:anchor.y-this.h*.53-(anchor.y-this.h*.53-this.pan.y)*ratio};
    this.zoom=next;this.dirty=true;
  }
  reset(){this.yaw=-.65;this.pitch=.68;this.zoom=1;this.pan={x:0,y:0};this.dirty=true;}
  destroy(){this.destroyed=true;cancelAnimationFrame(this.raf);this.resizeObserver.disconnect();this.listeners.forEach(([t,f,o])=>this.canvas.removeEventListener(t,f,o));}
  height(feature){return feature.record.kind==='building' ? (feature.record.height_m??(this.assumptions?this.displayHeight:0)):0;}
  project3(x,y,z=0){
    const a=x*Math.cos(this.yaw)-y*Math.sin(this.yaw), b=x*Math.sin(this.yaw)+y*Math.cos(this.yaw);
    const depth=b*Math.cos(this.pitch)-z*Math.sin(this.pitch), vertical=-b*Math.sin(this.pitch)-z*Math.cos(this.pitch);
    const scale=Math.min(this.w*.38,this.h*.36)/this.extent*this.zoom;
    const perspective=1/Math.max(.45,1+depth/(this.extent*8));
    return {x:this.w*.5+this.pan.x+a*scale*perspective,y:this.h*.53+this.pan.y+vertical*scale*perspective,depth};
  }
  polygon(rings,z,fill,stroke,width=1){const c=this.ctx;c.beginPath();for(const ring of rings){ring.forEach((p,i)=>{const q=this.project3(p[0],p[1],z);i?c.lineTo(q.x,q.y):c.moveTo(q.x,q.y);});c.closePath();}if(fill){c.fillStyle=fill;c.fill('evenodd');}if(stroke){c.strokeStyle=stroke;c.lineWidth=width;c.stroke();}}
  draw(){
    const c=this.ctx,w=this.w,h=this.h;c.setTransform(this.dpr,0,0,this.dpr,0,0);c.fillStyle='#07141d';c.fillRect(0,0,w,h);
    const halo=c.createRadialGradient(w*.5,h*.5,5,w*.5,h*.5,w*.55);halo.addColorStop(0,'#123e413d');halo.addColorStop(1,'#06131b00');c.fillStyle=halo;c.fillRect(0,0,w,h);
    const step=10**Math.floor(Math.log10(this.extent/3)),extent=this.extent*2.5;
    c.lineWidth=.6;c.strokeStyle='#29464f70';
    for(let n=-Math.ceil(extent/step);n<=Math.ceil(extent/step);n++){
      for(const pair of [[[n*step,-extent],[n*step,extent]],[[-extent,n*step],[extent,n*step]]]){const a=this.project3(...pair[0]),b=this.project3(...pair[1]);c.beginPath();c.moveTo(a.x,a.y);c.lineTo(b.x,b.y);c.stroke();}}
    const features=this.features.filter(f=>f.selected||this.showContext).sort((a,b)=>this.project3(...(b.polygons[0]?.[0]?.[0]||[0,0])).depth-this.project3(...(a.polygons[0]?.[0]?.[0]||[0,0])).depth);
    const surfaces=[];
    for(const f of features){let z=this.height(f);for(const poly of f.polygons){
      this.polygon(poly,0,f.selected?'#14564b50':'#13384635',f.selected?'#79e9ca80':'#335a6365');
      if(z>0){
        for(const ring of poly)for(let i=0;i<ring.length-1;i++){
          const a=ring[i],b=ring[i+1];const pts=[this.project3(...a,0),this.project3(...b,0),this.project3(...b,z),this.project3(...a,z)];
          surfaces.push({depth:pts.reduce((s,p)=>s+p.depth,0)/4,pts,fill:f.selected?'#245f59e8':'#1a3943cc',stroke:f.selected?'#6bc9b6b0':'#365a6575'});
        }
        surfaces.push({depth:poly[0].reduce((s,p)=>s+this.project3(...p,z).depth,0)/poly[0].length,poly,z,selected:f.selected});
      }
    }}
    // Painter ordering covers walls and roofs together. Roof holes use even-odd fill.
    for(const face of surfaces.sort((a,b)=>b.depth-a.depth)){
      if(face.poly)this.polygon(face.poly,face.z,face.selected?'#74c6bdaa':'#2b515e99',face.selected?'#b7ffe9':'#447483',face.selected?1.5:.7);
      else {c.beginPath();face.pts.forEach((p,i)=>i?c.lineTo(p.x,p.y):c.moveTo(p.x,p.y));c.closePath();c.fillStyle=face.fill;c.fill();c.strokeStyle=face.stroke;c.lineWidth=.8;c.stroke();}
    }
    const selected=this.features[0],height=this.height(selected),anchor=this.project3(0,0,height);
    if(!selected.polygons.length){c.strokeStyle='#8ceace';c.lineWidth=2;c.beginPath();c.arc(anchor.x,anchor.y,14,0,Math.PI*2);c.moveTo(anchor.x-20,anchor.y);c.lineTo(anchor.x+20,anchor.y);c.moveTo(anchor.x,anchor.y-20);c.lineTo(anchor.x,anchor.y+20);c.stroke();}
    // Labels describe the actual record, never fictional building phases.
    if(this.labels){const text=this.record.name.length>36?this.record.name.slice(0,34)+'…':this.record.name;
    c.font='12px -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif';const tw=c.measureText(text).width;const x=Math.max(18,Math.min(w-tw-30,anchor.x+35)), y=Math.max(122,Math.min(h-120,anchor.y-80));
    c.strokeStyle='#a1dfd2';c.beginPath();c.moveTo(anchor.x,anchor.y-4);c.lineTo(x-8,y+10);c.stroke();c.fillStyle='#081720f0';c.fillRect(x-5,y-8,tw+18,44);c.fillStyle='#e4f3ef';c.fillText(text,x+2,y+9);c.font='10px ui-monospace,monospace';c.fillStyle='#8fafa9';c.fillText(this.record.kind==='building'?'SOURCE BUILDING OUTLINE':this.record.geometry?'SOURCE AREA · NO EXTRUSION':'POINT ONLY · NO FOOTPRINT',x+2,y+25);
    }
    // North is derived from the world coordinates and rotates with the camera.
    const origin=this.project3(0,0),north=this.project3(0,this.extent*.4);const angle=Math.atan2(north.y-origin.y,north.x-origin.x),nx=w-39,ny=h-120;
    c.save();c.translate(nx,ny);c.rotate(angle+Math.PI/2);c.strokeStyle='#9bcabc';c.beginPath();c.moveTo(0,13);c.lineTo(0,-13);c.lineTo(-4,-5);c.moveTo(0,-13);c.lineTo(4,-5);c.stroke();c.restore();c.fillStyle='#9bcabc';c.font='10px ui-monospace,monospace';c.fillText('N',nx-3,ny-21);
    const readout=document.getElementById('scene-readout');if(readout)readout.textContent=`${Math.round(this.pitch*180/Math.PI)}° tilt · ${this.zoom.toFixed(2)}× · grid ${step} m`;
  }
}
