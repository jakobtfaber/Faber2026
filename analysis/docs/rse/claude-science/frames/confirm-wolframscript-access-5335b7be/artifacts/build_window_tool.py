"""Assemble a single self-contained HTML window/RFI editor from the per-burst assets.

Embeds each <name>_disp.png as base64 + its _disp.json into one HTML file. In the browser the
user, per burst: drags the on-pulse (blue) and off-pulse (grey) left/right borders on the time
axis, and paints RFI frequency bands (red) by dragging vertically on the spectrum. "Download
choices JSON" writes window_choices.json:
  {burst: {burst_lims:[t0,t1], off_lims:[t0,t1], rfi_bands_mhz:[[f0,f1],...]}}
which the re-run driver consumes.
"""
import os, json, base64, glob

ASSET_DIR = os.environ.get("ASSET_DIR", "/Users/jakobfaber/Developer/scratch/window_tool_assets")
OUT = os.environ.get("TOOL_OUT", "/Users/jakobfaber/Developer/scratch/window_editor.html")
BURSTS = ["casey", "whitney", "phineas", "mahi", "freya", "zach",
          "chromatica", "wilhelm", "oran", "hamilton", "johndoeII", "isha"]

data = {}
for name in BURSTS:
    pj = f"{ASSET_DIR}/{name}_disp.json"; pp = f"{ASSET_DIR}/{name}_disp.png"
    if not (os.path.exists(pj) and os.path.exists(pp)):
        print(f"  MISSING assets for {name}, skipping"); continue
    meta = json.load(open(pj))
    b64 = base64.b64encode(open(pp, "rb").read()).decode("ascii")
    meta["png_b64"] = b64
    data[name] = meta

payload = json.dumps(data)

html = r"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>CHIME window / RFI editor</title>
<style>
 body{font-family:-apple-system,Helvetica,Arial,sans-serif;margin:0;background:#111;color:#eee}
 #bar{padding:8px 12px;background:#1c1c1c;position:sticky;top:0;border-bottom:1px solid #333;z-index:10}
 select,button{font-size:14px;padding:4px 8px;margin-right:8px;background:#2a2a2a;color:#eee;border:1px solid #444;border-radius:4px}
 button:hover{background:#3a3a3a;cursor:pointer}
 #wrap{padding:12px}
 .mode{margin-right:10px}
 .mode.active{background:#2c74b3;border-color:#2c74b3}
 #cv{border:1px solid #333;cursor:crosshair;display:block;margin-top:8px;background:#000}
 #prof{border:1px solid #333;display:block;background:#000}
 #hint{font-size:12px;color:#aaa;margin:6px 0}
 #status{font-size:12px;color:#7fd17f;margin-left:8px}
 table{font-size:12px;border-collapse:collapse;margin-top:8px}
 td,th{border:1px solid #333;padding:2px 6px}
</style></head><body>
<div id="bar">
 <label>burst </label><select id="sel"></select>
 <button class="mode active" id="m_on"  data-m="on">on-pulse border</button>
 <button class="mode"        id="m_off" data-m="off">off-pulse border</button>
 <button class="mode"        id="m_rfi" data-m="rfi">paint RFI band</button>
 <button id="clearrfi">clear RFI (this burst)</button>
 <button id="reset">reset windows (this burst)</button>
 <button id="dl">⬇ download choices JSON</button>
 <span id="status"></span>
</div>
<div id="wrap">
 <div id="hint"></div>
 <canvas id="prof" width="900" height="90"></canvas>
 <canvas id="cv" width="900" height="500"></canvas>
 <div id="tbl"></div>
</div>
<script>
const DATA = __PAYLOAD__;
const names = Object.keys(DATA);
const sel = document.getElementById('sel');
names.forEach(n=>{const o=document.createElement('option');o.value=n;o.text=n;sel.add(o);});
const cv=document.getElementById('cv'), ctx=cv.getContext('2d');
const pcv=document.getElementById('prof'), pctx=pcv.getContext('2d');
const W=900,H=500,PH=90;
let mode='on';
// per-burst editable state
const state={};
function initState(n){
  const d=DATA[n];
  state[n]={burst:[d.burst_lims[0],d.burst_lims[1]], off:[d.off_lims[0],d.off_lims[1]], rfi:[]};
}
names.forEach(initState);
let cur=names[0];
const imgs={};
function loadImg(n,cb){
  if(imgs[n]){cb();return;}
  const im=new Image(); im.onload=()=>{imgs[n]=im;cb();}; im.src="data:image/png;base64,"+DATA[n].png_b64;
}
// coordinate helpers: time bin <-> x pixel; freq MHz <-> y pixel
function binToX(n,b){return b/DATA[n].ntime*W;}
function xToBin(n,x){return Math.max(0,Math.min(DATA[n].ntime,Math.round(x/W*DATA[n].ntime)));}
function freqToY(n,f){const d=DATA[n];return H-(f-d.fmin)/(d.fmax-d.fmin)*H;} // fmin at bottom (origin lower)
function yToFreq(n,y){const d=DATA[n];return d.fmin+(H-y)/H*(d.fmax-d.fmin);}
function draw(){
  const n=cur,d=DATA[n],s=state[n];
  ctx.clearRect(0,0,W,H);
  if(imgs[n]) ctx.drawImage(imgs[n],0,0,W,H);
  // RFI bands
  ctx.fillStyle='rgba(214,39,40,0.30)';
  s.rfi.forEach(([f0,f1])=>{const y0=freqToY(n,Math.max(f0,f1)),y1=freqToY(n,Math.min(f0,f1));
    ctx.fillRect(0,y0,W,y1-y0);});
  // off window (grey)
  const ox0=binToX(n,s.off[0]),ox1=binToX(n,s.off[1]);
  ctx.fillStyle='rgba(149,165,166,0.20)'; ctx.fillRect(ox0,0,ox1-ox0,H);
  ctx.strokeStyle='#95a5a6'; ctx.lineWidth=2; ctx.setLineDash([6,4]);
  [ox0,ox1].forEach(x=>{ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,H);ctx.stroke();});
  // on window (blue)
  const bx0=binToX(n,s.burst[0]),bx1=binToX(n,s.burst[1]);
  ctx.fillStyle='rgba(44,116,179,0.22)'; ctx.fillRect(bx0,0,bx1-bx0,H);
  ctx.strokeStyle='#2c74b3';
  [bx0,bx1].forEach(x=>{ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,H);ctx.stroke();});
  ctx.setLineDash([]);
  drawProf();
  drawTbl();
}
function drawProf(){
  const n=cur,d=DATA[n],s=state[n];
  pctx.clearRect(0,0,W,PH); pctx.fillStyle='#000'; pctx.fillRect(0,0,W,PH);
  const p=d.profile; let mn=Infinity,mx=-Infinity;
  p.forEach(v=>{if(v!=null){if(v<mn)mn=v;if(v>mx)mx=v;}});
  const rng=(mx-mn)||1;
  // windows behind profile
  const bx0=binToX(n,s.burst[0]),bx1=binToX(n,s.burst[1]);
  const ox0=binToX(n,s.off[0]),ox1=binToX(n,s.off[1]);
  pctx.fillStyle='rgba(149,165,166,0.25)'; pctx.fillRect(ox0,0,ox1-ox0,PH);
  pctx.fillStyle='rgba(44,116,179,0.28)'; pctx.fillRect(bx0,0,bx1-bx0,PH);
  pctx.strokeStyle='#eee'; pctx.lineWidth=1; pctx.beginPath();
  const nd=d.ntime_disp;
  for(let i=0;i<nd;i++){const v=p[i]; if(v==null)continue;
    const x=i/nd*W, y=PH-((v-mn)/rng)*(PH-6)-3;
    if(i===0)pctx.moveTo(x,y); else pctx.lineTo(x,y);}
  pctx.stroke();
}
function drawTbl(){
  const n=cur,s=state[n],d=DATA[n];
  let h=`<table><tr><th>quantity</th><th>value</th></tr>`;
  h+=`<tr><td>on-pulse bins</td><td>[${s.burst[0]}, ${s.burst[1]}] (${s.burst[1]-s.burst[0]} bins)</td></tr>`;
  h+=`<tr><td>off-pulse bins</td><td>[${s.off[0]}, ${s.off[1]}] (${s.off[1]-s.off[0]} bins)</td></tr>`;
  h+=`<tr><td>RFI bands (MHz)</td><td>${s.rfi.map(b=>`[${b[0].toFixed(1)}–${b[1].toFixed(1)}]`).join(', ')||'none'}</td></tr>`;
  h+=`<tr><td>de-scallop</td><td>${d.descallop_method}</td></tr></table>`;
  document.getElementById('tbl').innerHTML=h;
}
// dragging
let drag=null; // {kind:'on'|'off', edge:0|1} or {kind:'rfi', f0}
function nearestEdge(n,x){
  const s=state[n];
  const cands=[['on',0,binToX(n,s.burst[0])],['on',1,binToX(n,s.burst[1])],
               ['off',0,binToX(n,s.off[0])],['off',1,binToX(n,s.off[1])]];
  let best=null,bd=14;
  cands.forEach(([k,e,px])=>{const dd=Math.abs(px-x); if(dd<bd){bd=dd;best={kind:k,edge:e};}});
  return best;
}
cv.addEventListener('mousedown',ev=>{
  const r=cv.getBoundingClientRect(); const x=ev.clientX-r.left, y=ev.clientY-r.top;
  const n=cur;
  if(mode==='rfi'){drag={kind:'rfi',f0:yToFreq(n,y)}; return;}
  // on/off border modes: grab nearest matching edge, else move whichever edge is closer
  let e=nearestEdge(n,x);
  if(!e || e.kind!==mode){
    const s=state[n], arr=(mode==='on')?s.burst:s.off;
    const d0=Math.abs(binToX(n,arr[0])-x), d1=Math.abs(binToX(n,arr[1])-x);
    e={kind:mode, edge: d0<=d1?0:1};
  }
  drag=e; applyDrag(x,y);
});
cv.addEventListener('mousemove',ev=>{if(!drag)return;
  const r=cv.getBoundingClientRect(); applyDrag(ev.clientX-r.left, ev.clientY-r.top);});
window.addEventListener('mouseup',ev=>{
  if(drag&&drag.kind==='rfi'){
    const r=cv.getBoundingClientRect(); const y=ev.clientY-r.top;
    const f1=yToFreq(cur,y); const lo=Math.min(drag.f0,f1),hi=Math.max(drag.f0,f1);
    if(hi-lo>0.2) state[cur].rfi.push([lo,hi]);
    draw();
  }
  drag=null;});
function applyDrag(x,y){
  const n=cur,s=state[n];
  if(drag.kind==='rfi'){draw();
    // live preview band
    const yy=freqToY(n,drag.f0);
    ctx.fillStyle='rgba(214,39,40,0.25)'; ctx.fillRect(0,Math.min(yy,y),W,Math.abs(y-yy)); return;}
  const b=xToBin(n,x); const arr=(drag.kind==='on')?s.burst:s.off;
  arr[drag.edge]=b; if(arr[0]>arr[1])arr.reverse();
  draw();
}
// controls
document.querySelectorAll('.mode').forEach(btn=>btn.addEventListener('click',()=>{
  mode=btn.dataset.m; document.querySelectorAll('.mode').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('hint').textContent =
    mode==='rfi' ? 'RFI mode: drag vertically on the spectrum to paint a frequency band to mask.'
    : 'Window mode: drag a border line left/right on the spectrum (or click near an edge).';
}));
document.getElementById('clearrfi').onclick=()=>{state[cur].rfi=[];draw();};
document.getElementById('reset').onclick=()=>{initState(cur);draw();};
sel.onchange=()=>{cur=sel.value; loadImg(cur,draw);};
document.getElementById('dl').onclick=()=>{
  const out={};
  names.forEach(n=>{const s=state[n]; out[n]={burst_lims:s.burst, off_lims:s.off, rfi_bands_mhz:s.rfi};});
  const blob=new Blob([JSON.stringify(out,null,2)],{type:'application/json'});
  const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download='window_choices.json'; a.click();
  document.getElementById('status').textContent='saved window_choices.json';
};
document.getElementById('hint').textContent='Window mode: drag a border line left/right on the spectrum (or click near an edge).';
loadImg(cur,draw);
</script></body></html>"""

html = html.replace("__PAYLOAD__", payload)
with open(OUT, "w") as fh:
    fh.write(html)
print(f"WROTE {OUT}  ({len(html)/1e6:.1f} MB, {len(data)} bursts)")
