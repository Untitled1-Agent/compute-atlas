/* Small, dependency-free numerical kernel shared by the map and its tests. */
(function(root){
'use strict';
const finite=v=>typeof v==='number'&&Number.isFinite(v);
const clamp=(v,a,b)=>Math.min(b,Math.max(a,v));
const wrap=x=>((x+180)%360+360)%360-180;
const mercator=(lon,lat)=>[(wrap(lon)+180)/360,(1-Math.asinh(Math.tan(clamp(lat,-85.051129,85.051129)*Math.PI/180))/Math.PI)/2];
const inverse=(x,y)=>[wrap(x*360-180),Math.atan(Math.sinh(Math.PI*(1-2*clamp(y,0,1))))*180/Math.PI];
function distance(a,b){let r=Math.PI/180,dlat=(b.lat-a.lat)*r,dlon=wrap(b.lon-a.lon)*r;let q=Math.sin(dlat/2)**2+Math.cos(a.lat*r)*Math.cos(b.lat*r)*Math.sin(dlon/2)**2;return 6371*2*Math.atan2(Math.sqrt(clamp(q,0,1)),Math.sqrt(1-clamp(q,0,1)));}
function aggregate(sites,phase='snapshot'){
 const buckets={};let known=0,unknown=0;
 for(const s of sites){let k=s.review||'archive',b=buckets[k]||(buckets[k]={count:0,known:0,unknown:0,mw:0,ids:[]});b.count++;b.ids.push(s.id);let n=s[phase]?.it_mw;if(finite(n)&&n>=0){b.mw+=n;b.known++;known++;}else{b.unknown++;unknown++;}}
 return {buckets,count:sites.length,known,unknown};
}
function phaseDelta(s){let a=s.snapshot?.it_mw,b=s.target?.it_mw;if(!finite(a)||!finite(b))return null;return {mw:b-a,pct:a===0?null:(b-a)/a*100};}
function perGW(phase){return finite(phase?.it_mw)&&phase.it_mw>0&&finite(phase?.cost_b)?phase.cost_b/(phase.it_mw/1000):null;}
function normalizeView(v,siteIDs){
 const n=Number(v?.level),lat=Number(v?.lat),lon=Number(v?.lon),z=Number(v?.zoom);
 return {level:Number.isInteger(n)?clamp(n,0,5):0,lat:finite(lat)?clamp(lat,-85,85):27,lon:finite(lon)?wrap(lon):-59,zoom:finite(z)?clamp(z,.78,50000):1.06,selected:siteIDs.includes(v?.selected)?v.selected:null,phase:v?.phase==='target'?'target':'snapshot',base:'vector'};
}
function decodePolyline(text){let pts=[],index=0,lat=0,lon=0;while(index<text.length){let values=[];for(let i=0;i<2;i++){let shift=0,result=0,byte;do{byte=text.charCodeAt(index++)-63;result|=(byte&31)<<shift;shift+=5;}while(byte>=32&&index<text.length);values.push(result&1?~(result>>1):result>>1);}lat+=values[0];lon+=values[1];pts.push([lon/1000,lat/1000]);}return pts;}
const longitudeNear=(lon,center)=>lon+360*Math.round((center-lon)/360);
const screenPoint=p=>p&&finite(p.x)&&finite(p.y);
function clipScreenSegment(a,b,width,height){
 if(!screenPoint(a)||!screenPoint(b)||!finite(width)||!finite(height)||width<=0||height<=0)return null;
 const dx=b.x-a.x,dy=b.y-a.y;let lo=0,hi=1;
 for(const [p,q] of [[-dx,a.x],[dx,width-a.x],[-dy,a.y],[dy,height-a.y]]){
  if(p===0){if(q<0)return null;continue;}
  const t=q/p;if(p<0)lo=Math.max(lo,t);else hi=Math.min(hi,t);if(lo>hi)return null;
 }
 return [{x:a.x+lo*dx,y:a.y+lo*dy},{x:a.x+hi*dx,y:a.y+hi*dy}];
}
function insideScreenPolygon(p,points){
 if(!screenPoint(p)||points.length<4||!points.every(screenPoint))return false;
 let inside=false;
 for(let i=0,j=points.length-1;i<points.length;j=i++){
  const a=points[i],b=points[j];
  if((a.y>p.y)!==(b.y>p.y)&&p.x<(b.x-a.x)*(p.y-a.y)/(b.y-a.y)+a.x)inside=!inside;
 }
 return inside;
}
function screenPathVisible(points,width,height,closed=false){
 if(points.length<2||!points.every(screenPoint)||!finite(width)||!finite(height)||width<=0||height<=0)return false;
 if(points.some(p=>p.x>=0&&p.x<=width&&p.y>=0&&p.y<=height))return true;
 if(points.some((b,i)=>i&&clipScreenSegment(points[i-1],b,width,height)))return true;
 return closed&&insideScreenPolygon({x:width/2,y:height/2},points);
}
// Split at a projection seam/horizon. A screen-width jump is valid on Mercator.
function screenPaths(points,{flat=false,scene=false,width=0}={}){
 const paths=[];let path=[];
 const flush=()=>{if(path.length>1)paths.push(path);path=[];};
 for(const p of points){
  if(!screenPoint(p)||(!scene&&(!finite(p.z)||p.z<=0))){flush();continue;}
  const prev=path.at(-1);
  if(prev&&(flat?Math.abs(p.lon-prev.lon)>180:!scene&&Math.abs(p.x-prev.x)>=width*.65))flush();
  path.push(p);
 }
 flush();return paths;
}
const api={finite,clamp,wrap,mercator,inverse,distance,aggregate,phaseDelta,perGW,normalizeView,decodePolyline,longitudeNear,clipScreenSegment,insideScreenPolygon,screenPathVisible,screenPaths};
if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.AtlasSpatialMath=api;
})(globalThis);
