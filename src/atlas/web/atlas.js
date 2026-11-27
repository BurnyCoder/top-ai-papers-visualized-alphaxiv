"use strict";
// The published explorer runs entirely on frozen artifacts. Canvas uses an equal scale on both axes.
const by = id => document.getElementById(id);
const canvas = by("canvas"), plot = by("plot"), ctx = canvas.getContext("2d");
const pointLayer=document.createElement("canvas");
let paintedView=[];
const ids = new Map(), filters = ["cluster", "subject", "year", "likes"];
let papers = [], clusters = {}, filtered = [], filteredSet = new Set(), selected = -1;
let tab = "topics", rowsShown = 35, hovered = -1, scale = 1, cx = 0, cy = 0;
let width = 1, height = 1, ready = false, drawing = false, drag = null;
let abstractChunkSize=0;
const abstracts=new Map();
const number = n => n.toLocaleString("en-US");
function element(tag, value, cls) {
  const node = document.createElement(tag);
  if (value !== undefined) node.textContent = value;
  if (cls) node.className = cls;
  return node;
}
function button(text, cls, click) {
  const node = element("button", text, cls);
  node.type = "button";
  node.addEventListener("click", click);
  return node;
}
function option(target, value, text) {
  const o = element("option", text);
  o.value = String(value); by(target).append(o);
}
function paperURL(id) { return "https://www.alphaxiv.org/abs/" + id.split("/").map(encodeURIComponent).join("/"); }
function groupFor(id) { return clusters[String(id)]; }
function topicName(id) {
  const topic=groupFor(id);
  return topic.display_name || topic.name;
}
// Circle area is proportional to likes. Use CSS pixels so the same count is
// comparable across editions, projections, filters and zoom levels.
// https://observablehq.com/plot/marks/dot
function likeRadius(likes) { return Math.sqrt(likes / 10); }
function showSizeKey(threshold) {
  const key = by("sizeKey");
  for (const likes of [25, 100, 400, 1600]) {
    if (likes <= threshold) continue;
    const sample = element("span", undefined, "size-example");
    const dot = element("i");
    dot.setAttribute("aria-hidden", "true");
    dot.style.width = 2 * likeRadius(likes) + "px";
    sample.dataset.likes = likes;
    sample.append(dot, number(likes));
    key.append(sample);
  }
}
function toScreen(p) { return [(p.x-cx)*scale+width/2, height/2-(p.y-cy)*scale]; }
function fitTo(indices) {
  if (!indices.length) return;
  let left = Infinity, bottom = Infinity, right = -Infinity, top = -Infinity;
  for (const i of indices) {
    const p = papers[i];
    left=Math.min(left,p.x); right=Math.max(right,p.x); bottom=Math.min(bottom,p.y); top=Math.max(top,p.y);
  }
  cx = (left+right)/2; cy = (bottom+top)/2;
  scale = Math.min((width-60)/Math.max(right-left,.8), (height-50)/Math.max(top-bottom,.8));
  queueDraw();
}
function resize() {
  width=plot.clientWidth; height=plot.clientHeight;
  const ratio = Math.min(window.devicePixelRatio || 1, 3);
  canvas.width=Math.round(width*ratio); canvas.height=Math.round(height*ratio);
  ctx.setTransform(ratio,0,0,ratio,0,0);
  if (ready) fitTo(filtered);
}
function queueDraw() {
  if (drawing) return;
  drawing = true;
  requestAnimationFrame(() => { drawing=false; draw(); });
}
function enableProjectionControls(config){
  const menu=by("projection"),score=by("layoutScore");
  const umap=papers.map(p=>[p.x,p.y]);
  let pending=null,shown="umap",sequence=0;
  const caption=key=>"Full corpus · seed "+config.seed+" · "+(100*config.recall[key]).toFixed(2)+"% of original ten neighbors retained";
  by("mapLabel").textContent="Projection";menu.hidden=false;score.hidden=false;score.textContent=caption(shown);
  menu.onchange=async()=>{
    const serial=++sequence, key=menu.value;
    try{
      let coords=umap,permutation=null;
      if(key!=="umap"){
        score.textContent="Loading comparison coordinates…";
        if(!pending)pending=fetch(config.file).then(r=>{if(!r.ok)throw Error(r.status);return r.json();});
        const controls=await pending;
        if(key==="pca")coords=controls.pca;else permutation=controls.shuffled;
      }
      if(serial!==sequence)return;
      for(let i=0;i<papers.length;i++)[papers[i].x,papers[i].y]=coords[permutation?permutation[i]:i];
      shown=key;paintedView=[];score.textContent=caption(key);hideTip();fitTo(filtered);
    }catch{
      pending=null;if(serial!==sequence)return;
      menu.value=shown;score.textContent="Comparison could not be loaded. Select the projection to retry.";
    }
  };
}
function drawPoints(ctx) {
  ctx.clearRect(0,0,width,height);
  ctx.fillStyle="#ccd5c4";
  for(let x=14;x<width;x+=26) for(let y=14;y<height;y+=26) ctx.fillRect(x,y,1,1);
  const centers = new Map();
  // The paper list is sorted most-liked first. Paint in reverse so popular
  // papers remain visible in dense neighborhoods when the map is zoomed out.
  for (let j = filtered.length - 1; j >= 0; j--) {
    const p=papers[filtered[j]], [x,y]=toScreen(p), radius=p.radius;
    if(x < -radius || y < -radius || x>width+radius || y>height+radius) continue;
    const topic = groupFor(p.cluster);
    ctx.globalAlpha = p.cluster<0 ? .50 : .81;
    ctx.fillStyle=topic.color; ctx.beginPath(); ctx.arc(x,y,radius,0,Math.PI*2); ctx.fill();
    if(p.cluster>=0){
      const c=centers.get(p.cluster)||[0,0,0]; c[0]+=x; c[1]+=y; c[2]++; centers.set(p.cluster,c);
    }
  }
  ctx.globalAlpha=1;
  const occupied=[];
  ctx.font="600 10px system-ui"; ctx.textAlign="center"; ctx.textBaseline="middle";
  for (const [g,c] of [...centers].sort((a,b)=>b[1][2]-a[1][2])) {
    if(c[2]<12 || occupied.length>=Math.max(3,Math.floor(width/85))) continue;
    const name=topicName(g), w=ctx.measureText(name).width+10, x=c[0]/c[2], y=c[1]/c[2]-10;
    const bounds=[x-w/2,y-9,x+w/2,y+9];
    if(bounds[0]<6 || bounds[2]>width-6 || bounds[1]<6 || bounds[3]>height-6 ||
       occupied.some(b=>!(b[2]+5<bounds[0] || b[0]-5>bounds[2] || b[3]+3<bounds[1] || b[1]-3>bounds[3]))) continue;
    occupied.push(bounds);
    ctx.fillStyle="rgba(251,252,245,.89)"; ctx.fillRect(bounds[0],bounds[1],w,18);
    ctx.fillStyle="#224035"; ctx.fillText(name,x,y);
  }
}
function draw(){
  const view=[filtered,cx,cy,scale,width,height,canvas.width,canvas.height];
  if(view.some((v,i)=>v!==paintedView[i])){
    pointLayer.width=canvas.width;pointLayer.height=canvas.height;
    const layer=pointLayer.getContext("2d");
    layer.setTransform(canvas.width/width,0,0,canvas.height/height,0,0);
    drawPoints(layer);paintedView=view;
  }
  ctx.clearRect(0,0,width,height);ctx.drawImage(pointLayer,0,0,width,height);
  for(const i of [hovered,selected]){
    if(i<0 || !filteredSet.has(i)) continue;
    const p=papers[i], [x,y]=toScreen(p);
    ctx.strokeStyle="#fff";ctx.lineWidth=4.5;ctx.beginPath();ctx.arc(x,y,p.radius+3,0,Math.PI*2);ctx.stroke();
    ctx.strokeStyle="#123c31";ctx.lineWidth=2;ctx.stroke();
  }
}
function zoomAt(factor,x=width/2,y=height/2){
  const before=scale;
  scale=Math.max(2,Math.min(2000,scale*factor));
  cx+=(x-width/2)*(1/before-1/scale); cy-=(y-height/2)*(1/before-1/scale);
  queueDraw();
}
function nearest(x,y) {
  let best=-1, d=90;
  // Test frontmost dots first. When the pointer is in a gap, retain the
  // nearest-center tolerance so a small isolated paper is easy to select.
  for(const i of filtered){
    const p=papers[i], [px,py]=toScreen(p), dist=(px-x)**2+(py-y)**2;
    if(dist<=p.radius*p.radius)return i;
    if(dist<d){best=i;d=dist;}
  }
  return best;
}
function pointer(e){const rect=canvas.getBoundingClientRect();return [e.clientX-rect.left,e.clientY-rect.top];}
function hideTip(){hovered=-1;by("tip").hidden=true;queueDraw();}
canvas.addEventListener("wheel",e=>{e.preventDefault();zoomAt(Math.exp(-Math.max(-120,Math.min(120,e.deltaY))*.003),...pointer(e));hideTip();},{passive:false});
canvas.addEventListener("pointerdown",e=>{const [x,y]=pointer(e);drag={x,y,cx,cy,moved:false};canvas.setPointerCapture(e.pointerId);});
canvas.addEventListener("pointermove",e=>{
  const [x,y]=pointer(e);
  if(drag){if(Math.hypot(x-drag.x,y-drag.y)>3)drag.moved=true;
    if(drag.moved){cx=drag.cx-(x-drag.x)/scale;cy=drag.cy+(y-drag.y)/scale;hideTip();} return;}
  hovered=nearest(x,y);const tip=by("tip");
  tip.hidden=hovered<0;
  if(hovered>=0){const p=papers[hovered];tip.textContent=p.title+" · "+number(p.likes)+" likes";tip.style.left=Math.max(4,Math.min(width-tip.offsetWidth-5,x+12))+"px";
    tip.style.top=Math.max(4,Math.min(height-tip.offsetHeight-5,y+14))+"px";}
  queueDraw();
});
canvas.addEventListener("pointerup",e=>{if(drag && !drag.moved){const i=nearest(...pointer(e));if(i>=0)openPaper(i);}drag=null;});
canvas.addEventListener("pointercancel",()=>{drag=null;hideTip();});
canvas.addEventListener("pointerleave",hideTip);
canvas.addEventListener("keydown",e=>{
  const steps={ArrowLeft:[-1,0],ArrowRight:[1,0],ArrowUp:[0,1],ArrowDown:[0,-1]};
  if(steps[e.key]){e.preventDefault();cx+=steps[e.key][0]*32/scale;cy+=steps[e.key][1]*32/scale;queueDraw();}
  else if(["+","=","-"].includes(e.key)){e.preventDefault();zoomAt(e.key==="-"?.8:1.25);}
});
by("plus").onclick=()=>zoomAt(1.35);by("minus").onclick=()=>zoomAt(1/1.35);by("fit").onclick=()=>fitTo(filtered);
function updateFilter(){
  const q=by("query").value.trim().toLocaleLowerCase(), g=by("cluster").value;
  const s=by("subject").value, y=by("year").value, likes=Number(by("likes").value)||Number(by("likes").min);
  filtered=[];
  for(let i=0;i<papers.length;i++){const p=papers[i];
    if(p.likes>=likes && (g===""||String(p.cluster)===g) && (!s||p.subjects.includes(s)) &&
       (!y||p.date.slice(0,4)===y) && (!q||p.search.includes(q)))filtered.push(i);}
  filtered.sort((a,b)=>papers[b].likes-papers[a].likes||papers[a].title.localeCompare(papers[b].title));
  filteredSet=new Set(filtered);
  by("visible").textContent=number(filtered.length)+" visible";
  if(selected>=0 && !filteredSet.has(selected))clearSelection();
  rowsShown=35;hideTip();renderSide();
}
function clearSelection(){selected=-1;history.replaceState(null,"",location.pathname+location.search);}
function resetFields(){by("query").value="";for(const k of filters)by(k).value=k==="likes"?by(k).min:"";}
function chooseCluster(id){clearSelection();by("cluster").value=String(id);tab="papers";updateFilter();fitTo(filtered);}
function paperRow(i,meta=true){
  const p=papers[i], n=button("","row",()=>openPaper(i)), text=element("span",p.title);
  if(meta)text.append(element("span",number(p.likes)+" likes · "+p.date.slice(0,4),"subline"));
  n.append(text);return n;
}
function openPaper(i){
  if(i<0 || i>=papers.length)return;
  if(!filteredSet.has(i)){resetFields();updateFilter();}
  selected=i;tab="papers";hovered=-1;by("tip").hidden=true;
  const [x,y]=toScreen(papers[i]);if(x<12||x>width-12||y<12||y>height-12){cx=papers[i].x;cy=papers[i].y;}
  history.replaceState(null,"","#paper="+encodeURIComponent(papers[i].paper_id));renderSide();queueDraw();
}
function renderSide(){
  const b=by("sideBody");b.replaceChildren();b.scrollTop=0;
  by("topicTab").setAttribute("aria-pressed",String(tab==="topics"));
  by("paperTab").setAttribute("aria-pressed",String(tab==="papers"));
  if(selected>=0){
    const p=papers[selected], topic=groupFor(p.cluster);
    b.append(button("← Paper list","smallbtn",()=>{clearSelection();renderSide();queueDraw();}));
    b.append(element("h2",p.title),element("div",p.paper_id+" · "+number(p.likes)+" likes · "+p.date,"detailmeta"));
    b.append(element("p",p.authors.join(", ")));
    b.append(button(topicName(p.cluster),"smallbtn detailgroup",()=>chooseCluster(p.cluster)));
    if(p.subjects.length)b.append(element("div",p.subjects.join(" · "),"detailmeta"));
    const d=element("details"), body=element("p",p.abstract??(p.title_only?"Title-only record":"Loading abstract…"));
    if(!p.abstract && p.title_only)body.textContent="Title-only record";
    if(abstractChunkSize && !p.title_only){
      const index=selected, part=Math.floor(index/abstractChunkSize);
      d.addEventListener("toggle",async()=>{
        if(!d.open)return;
        try{
          if(!abstracts.has(part))abstracts.set(part,fetch("abstracts/"+part+".json").then(r=>{
            if(!r.ok)throw Error(r.status);return r.json();
          }));
          const texts=await abstracts.get(part);body.textContent=texts[index%abstractChunkSize];
        }catch{abstracts.delete(part);body.textContent="The abstract could not be loaded. Close and reopen to retry.";}
      });
    }
    d.append(element("summary","Abstract"),body);b.append(d);
    const link=element("a","Open on alphaXiv ↗","open");link.href=paperURL(p.paper_id);link.target="_blank";link.rel="noopener";b.append(link);
    b.append(element("h3","Closest papers in embedding space","sectitle"));
    for(const n of p.neighbors)b.append(paperRow(n,false));return;
  }
  if(tab==="topics"){
    b.append(element("h2","Topic index"),element("p","Select a topic to inspect its papers and the examples behind its name."));
    const counts=new Map();
    for(const i of filtered){const g=papers[i].cluster;counts.set(g,(counts.get(g)||0)+1);}
    for(const [g,count] of [...counts].sort((a,c)=>(a[0]<0)-(c[0]<0)||c[1]-a[1])){
      const topic=groupFor(g), n=button("","row",()=>chooseCluster(g)), sw=element("span",undefined,"swatch");
      sw.style.setProperty("--color",topic.color);n.append(sw,element("span",topicName(g)),element("span",number(count),"count"));b.append(n);
    }
  }else{
    const g=by("cluster").value, topic=groupFor(g);
    if(g!=="" && topic){
      b.append(element("h2",topicName(g)));
      if(topic.evidence && topic.evidence.length){const box=element("div",undefined,"evidence");
        box.append(element("h3","Evidence for Luna’s label","sectitle"));
        for(const id of topic.evidence){if(ids.has(id))box.append(paperRow(ids.get(id),false));}b.append(box);}
    }
    b.append(element("h3",number(filtered.length)+" papers · most liked first","sectitle"));
    for(const i of filtered.slice(0,rowsShown))b.append(paperRow(i));
    if(filtered.length>rowsShown)b.append(button("Show more papers","smallbtn more",()=>{
      const y=b.scrollTop;rowsShown+=45;renderSide();b.scrollTop=y;
    }));
  }
  if(!filtered.length)b.append(element("p","No papers match these filters."));
}
by("query").addEventListener("input",()=>{clearSelection();tab="papers";updateFilter();});
for(const k of filters){by(k).addEventListener(k==="likes"?"input":"change",()=>{clearSelection();tab="papers";updateFilter();});}
by("reset").onclick=()=>{resetFields();clearSelection();tab="topics";updateFilter();fitTo(filtered);};
by("topicTab").onclick=()=>{clearSelection();tab="topics";renderSide();queueDraw();};
by("paperTab").onclick=()=>{clearSelection();tab="papers";renderSide();queueDraw();};
new ResizeObserver(resize).observe(plot);
async function load(){
  const response=await fetch("atlas.json");if(!response.ok)throw Error(response.status);
  const data=await response.json();clusters=data.clusters;
  if(data.paper_parts){
    const parts=data.paper_parts, blocks=new Array(parts.length);
    let next=0,loaded=0;
    async function readParts(){
      while(next<parts.length){
        const i=next++, response=await fetch(parts[i]);
        if(!response.ok)throw Error(response.status);
        blocks[i]=await response.json();loaded+=blocks[i].length;
        by("subtitle").textContent="Loading "+number(loaded)+" of "+number(data.paper_count)+" papers…";
      }
    }
    await Promise.all(Array.from({length:Math.min(5,parts.length)},readParts));
    papers=blocks.flat();
    if(papers.length!==data.paper_count)throw Error("Incomplete index");
  }else papers=data.papers;
  by("datasetLink").href="https://huggingface.co/datasets/BurnyCoder/alphaxiv-paper-atlas/tree/atlas-"+encodeURIComponent(data.snapshot);
  abstractChunkSize=data.abstract_chunk_size||0;
  if(data.csv){by("csvDownload").href=data.csv;by("csvDownload").textContent="Download CSV (.gz) ↓";}
  // The original, tagged atlas predates the threshold field and used a strict cutoff of 100.
  const threshold=data.threshold_exclusive??100;
  showSizeKey(threshold);
  if(data.controls)enableProjectionControls(data.controls);
  by("likes").min=String(threshold+1);by("likes").value=by("likes").min;
  const root=threshold===100?"./":"../";
  for(const n of [10,20,50,100])option("edition",n,"Over "+n+" likes");
  by("edition").value=String(threshold);by("edition").hidden=false;
  by("edition").onchange=e=>{const n=Number(e.target.value);location.href=root+(n===100?"":"over-"+n+"/");};
  const subjects=new Set(),years=new Set();
  papers.forEach((p,i)=>{ids.set(p.paper_id,i);p.search=[p.title,p.paper_id,p.id,...p.authors].join(" ").toLocaleLowerCase();
    p.radius=likeRadius(p.likes);
    p.subjects.forEach(t=>subjects.add(t));if(p.date)years.add(p.date.slice(0,4));});
  for(const [id] of Object.entries(clusters).sort((a,b)=>a[1].name.localeCompare(b[1].name)))option("cluster",id,topicName(id));
  [...subjects].sort().forEach(s=>option("subject",s,s));[...years].sort().reverse().forEach(y=>option("year",y,y));
  by("subtitle").textContent=number(papers.length)+" papers with more than "+threshold+" likes on alphaXiv. Explore "+number(data.cluster_count)+" topic clusters.";
  by("stamp").textContent="Snapshot · "+data.date;
  by("footnote").textContent=number(data.unassigned)+" papers appear in gray without a cluster assignment.";
  const deep=new URLSearchParams(location.hash.slice(1)).get("paper");
  ready=true;updateFilter();resize();if(ids.has(deep))openPaper(ids.get(deep));
}
load().catch(()=>{by("subtitle").textContent="The snapshot could not be loaded. Reload to try again.";by("sideBody").textContent="Data unavailable.";});
