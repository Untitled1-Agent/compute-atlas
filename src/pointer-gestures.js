'use strict';
/* One pointer orbits/pans; two pointers zoom and translate the same camera.
 * Keep pointer capture and cancellation in one place for maps and 3D scenes. */
class AtlasPointerGestures {
  constructor(canvas, callbacks) {
    this.canvas=canvas; this.callbacks=callbacks; this.pointers=new Map();
    this.listeners=[]; this.previous=null; this.suppressClick=false;
    this.on('pointerdown', e=>this.down(e));
    this.on('pointermove', e=>this.move(e));
    this.on('pointerup', e=>this.end(e,false));
    this.on('pointercancel', e=>this.end(e,true));
    this.on('lostpointercapture', e=>this.end(e,true));
  }
  on(type, fn) {this.canvas.addEventListener(type,fn);this.listeners.push([type,fn]);}
  snapshot() {
    const [a,b]=[...this.pointers.values()];
    return {x:(a.clientX+b.clientX)/2,y:(a.clientY+b.clientY)/2,
      distance:Math.hypot(a.clientX-b.clientX,a.clientY-b.clientY)};
  }
  down(event) {
    if(event.button!==0 || this.pointers.size>=2)return;
    this.pointers.set(event.pointerId,event);
    try {this.canvas.setPointerCapture(event.pointerId);} catch (_) {}
    if(this.pointers.size===1){this.suppressClick=false;this.callbacks.start(event);}
    else {this.suppressClick=true;this.previous=this.snapshot();this.callbacks.cancel();}
  }
  move(event) {
    if(!this.pointers.has(event.pointerId)){if(!this.pointers.size)this.callbacks.hover?.(event);return;}
    this.pointers.set(event.pointerId,event);
    if(this.pointers.size===1){this.callbacks.move(event);return;}
    const next=this.snapshot(),old=this.previous;this.previous=next;
    if(old.distance<8 || next.distance<8)return;
    this.callbacks.pinch(next.distance/old.distance,{clientX:old.x,clientY:old.y},
      {x:next.x-old.x,y:next.y-old.y});
  }
  end(event, cancelled) {
    if(!this.pointers.has(event.pointerId))return;
    const wasPinching=this.pointers.size===2;
    this.pointers.delete(event.pointerId);this.previous=null;
    if(wasPinching || cancelled){this.suppressClick=true;this.callbacks.cancel();}
    if(this.pointers.size)this.callbacks.start([...this.pointers.values()][0]);
    else this.callbacks.end(event,cancelled||this.suppressClick);
    try {this.canvas.releasePointerCapture(event.pointerId);} catch (_) {}
  }
  destroy() {this.listeners.forEach(([type,fn])=>this.canvas.removeEventListener(type,fn));this.pointers.clear();}
}
