import http.server, os, tempfile, sys, json, io
from urllib.parse import urlparse, parse_qs
import ifcopenshell, ifcopenshell.geom
import trimesh, numpy as np, ezdxf

HTML = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>IFC Viewer</title>
<link rel="icon" href="/webicon.png" type="image/png">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:system-ui,sans-serif;overflow:hidden;background:#1a1a2e}
#c{position:fixed;inset:0}
#bar{position:fixed;top:20px;left:50%;transform:translateX(-50%);z-index:10;display:flex;gap:12px;align-items:center;background:rgba(26,26,46,0.9);backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,0.12);border-radius:16px;padding:8px 16px}
#btn{display:flex;align-items:center;gap:8px;padding:10px 22px;background:linear-gradient(135deg,#6366f1,#8b5cf6);color:white;border-radius:12px;cursor:pointer;font-size:14px;font-weight:600;border:none}
#btn:hover{transform:translateY(-1px);box-shadow:0 4px 16px rgba(99,102,241,0.5)}
#f{display:none}
#s{color:#a5b4fc;font-size:13px;font-weight:500}
#tip{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);color:rgba(255,255,255,0.3);font-size:12px;pointer-events:none;z-index:10}
#panel{position:fixed;top:80px;right:20px;width:280px;height:500px;overflow-y:auto;background:rgba(26,26,46,0.92);backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,0.12);border-radius:12px;padding:14px;z-index:10;color:#c7d2fe;font-size:13px;display:none}
#panel.visible{display:block}
#panel h3{color:#e0e7ff;font-size:14px;margin:0 0 8px;border-bottom:1px solid rgba(255,255,255,0.1);padding-bottom:6px}
#panel .row{display:flex;justify-content:space-between;padding:3px 0;border-bottom:1px solid rgba(255,255,255,0.04)}
#panel .key{color:#a5b4fc;flex-shrink:0;margin-right:8px}
#panel .val{color:#e0e7ff;text-align:right;word-break:break-all}
#catPanel{position:fixed;top:80px;left:290px;width:250px;max-height:calc(100vh-160px);overflow-y:auto;background:rgba(26,26,46,0.92);backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,0.12);border-radius:12px;padding:12px;z-index:10;color:#c7d2fe;font-size:12px;display:none}
#catPanel.visible{display:block}
#catPanel h3{color:#e0e7ff;font-size:13px;margin:0 0 8px;border-bottom:1px solid rgba(255,255,255,0.1);padding-bottom:6px;display:flex;justify-content:space-between;align-items:center}
#catPanel .cat-row{display:flex;align-items:center;gap:6px;padding:4px 6px;border-radius:6px;margin-bottom:2px;transition:background 0.15s}
#catPanel .cat-row:hover{background:rgba(255,255,255,0.05)}
#catPanel .cat-row.off{opacity:0.4}
#catPanel .cat-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0}
#catPanel .cat-name{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#catPanel .cat-count{color:#6366f1;font-size:11px;flex-shrink:0}
#catPanel .cat-btn{border:none;background:rgba(99,102,241,0.2);color:#a5b4fc;border-radius:4px;padding:2px 7px;font-size:10px;cursor:pointer;flex-shrink:0}
#catPanel .cat-btn:hover{background:rgba(99,102,241,0.5);color:white}
#catPanel .cat-eye{flex-shrink:0;font-size:14px;cursor:pointer;opacity:0.7}
#catPanel .cat-eye:hover{opacity:1}
#catPanel .cat-eye.off{opacity:0.25}
#treePanel{position:fixed;top:80px;left:20px;width:250px;max-height:calc(100vh-160px);overflow-y:auto;background:rgba(26,26,46,0.92);backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,0.12);border-radius:12px;padding:12px;z-index:10;color:#c7d2fe;font-size:12px;display:none}
#treePanel.visible{display:block}
#treePanel h3{color:#e0e7ff;font-size:13px;margin:0 0 8px;border-bottom:1px solid rgba(255,255,255,0.1);padding-bottom:6px}
#treePanel .model-node{margin-bottom:2px}
#treePanel .model-node .header{display:flex;align-items:center;gap:6px;padding:4px 6px;border-radius:6px;cursor:pointer;transition:background 0.15s}
#treePanel .model-node .header:hover{background:rgba(255,255,255,0.05)}
#treePanel .model-node .header.sel{background:rgba(99,102,241,0.25);border:1px solid rgba(99,102,241,0.4)}
#treePanel .model-node .dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
#treePanel .model-node .name{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#treePanel .model-node .count{color:#6366f1;font-size:10px;flex-shrink:0}
#treePanel .model-node .eye{flex-shrink:0;font-size:14px;cursor:pointer;opacity:0.7}
#treePanel .model-node .eye:hover{opacity:1}
#treePanel .model-node .eye.off{opacity:0.25}
#treePanel .model-node.off{opacity:0.4}
#treePanel .arrow{flex-shrink:0;font-size:10px;width:12px;text-align:center;cursor:pointer;color:#6366f1}
#treePanel .sub-items{display:none;padding-left:12px;border-left:1px solid rgba(255,255,255,0.08);margin-left:4px}
#treePanel .sub-items.open{display:block}
#treePanel .sub-row{display:flex;align-items:center;gap:4px;padding:2px 4px;border-radius:4px;font-size:11px;transition:background 0.15s}
#treePanel .sub-row:hover{background:rgba(255,255,255,0.04)}
#treePanel .sub-row.off{opacity:0.4}
#treePanel .sub-dot{width:7px;height:7px;border-radius:50%;flex-shrink:0}
#treePanel .sub-name{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#treePanel .sub-count{color:#6366f1;font-size:10px;flex-shrink:0}
#treePanel .sub-eye{flex-shrink:0;font-size:12px;cursor:pointer;opacity:0.7}
#treePanel .sub-eye:hover{opacity:1}
#treePanel .sub-eye.off{opacity:0.25}
#treePanel .sub-sel{border:none;background:rgba(99,102,241,0.2);color:#a5b4fc;border-radius:3px;padding:1px 5px;font-size:9px;cursor:pointer}
#treePanel .sub-sel:hover{background:rgba(99,102,241,0.5);color:white}
#chartPanel{position:fixed;top:80px;right:320px;width:500px;max-height:calc(100vh-160px);background:rgba(26,26,46,0.92);backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,0.12);border-radius:12px;padding:8px;z-index:10;display:none}
#chartPanel.visible{display:block}
#logo{position:fixed;top:16px;left:20px;z-index:5;height:36px;pointer-events:none;opacity:0.8}
</style></head>
<body>
<div id="c"></div>
<img id="logo" src="/favicon.png" alt="GT">
<div id="bar">
<button id="btn">Open IFC File</button>
<input type="file" id="f" accept=".ifc">
<button id="appendBtn" style="display:none;padding:8px 14px;background:rgba(34,197,94,0.2);color:#22c55e;border:1px solid rgba(34,197,94,0.3);border-radius:10px;cursor:pointer;font-size:13px;font-weight:600">Append IFC</button>
<input type="file" id="af" accept=".ifc" style="display:none">
<span id="s">Ready</span>
<button id="exp" style="display:none;padding:8px 16px;background:rgba(34,197,94,0.2);color:#22c55e;border:1px solid rgba(34,197,94,0.3);border-radius:10px;cursor:pointer;font-size:13px;font-weight:600">Export XLSX</button>
<button id="sec" style="display:none;padding:8px 16px;background:rgba(239,68,68,0.2);color:#ef4444;border:1px solid rgba(239,68,68,0.3);border-radius:10px;cursor:pointer;font-size:13px;font-weight:600">Section</button>
<button id="dxf" style="display:none;padding:8px 12px;background:rgba(59,130,246,0.2);color:#3b82f6;border:1px solid rgba(59,130,246,0.3);border-radius:10px;cursor:pointer;font-size:12px;font-weight:600">DXF</button>
<button id="chartBtn" style="display:none;padding:8px 14px;background:rgba(139,92,246,0.2);color:#a78bfa;border:1px solid rgba(139,92,246,0.3);border-radius:10px;cursor:pointer;font-size:13px;font-weight:600">📊 Charts</button>
</div>
<div id="tip">Wheel: zoom | Left drag: rotate | Right drag: pan | Click: select</div>
<div id="catPanel"></div>
<div id="treePanel"></div>
<div id="panel"></div>
<div id="chartPanel"></div>
<script src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"></script>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<script type="importmap">
{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"}}
</script>
<script type="module">
import * as THREE from "three";
import {OrbitControls} from "three/addons/controls/OrbitControls.js";
import {GLTFLoader} from "three/addons/loaders/GLTFLoader.js";

const E=id=>document.getElementById(id);
const s=E("s"),btn=E("btn"),fi=E("f"),af=E("af"),appendBtn=E("appendBtn"),c=E("c"),panel=E("panel"),exp=E("exp"),sec=E("sec"),dxf=E("dxf"),chartBtn=E("chartBtn"),chartPanel=E("chartPanel");
btn.onclick=()=>{if(window._models&&window._models.length>0){location.reload();return}fi.click();};
appendBtn.onclick=()=>af.click();
exp.onclick=()=>{if(!window._ifcProps||!window._ifcProps.length)return;const keys=["Type","GlobalId","Name"];const extra=new Set();window._ifcProps.forEach(p=>Object.keys(p).forEach(k=>{if(k!=="Type"&&k!=="GlobalId"&&k!=="Name")extra.add(k)}));keys.push(...[...extra].sort());const rows=[keys];window._ifcProps.forEach(p=>rows.push(keys.map(k=>p[k]||"")));const ws=XLSX.utils.aoa_to_sheet(rows);const wb=XLSX.utils.book_new();XLSX.utils.book_append_sheet(wb,ws,"IFC Properties");XLSX.writeFile(wb,"ifc_properties.xlsx");};
let secMode="off",clipPlane=null,visPlane=null,secDrag=false,secLastY=0;
sec.onclick=()=>{if(secMode==="off"){secMode="pick";sec.style.background="rgba(239,68,68,0.5)";sec.style.color="#fca5a5";s.textContent="Click a face to set section plane"}else removeSec()};dxf.onclick=()=>{if(!clipPlane||!visPlane)return;const n=clipPlane.normal;const p=visPlane.position;const o=mg.position;const q=`nx=${n.x}&ny=${n.y}&nz=${n.z}&px=${p.x}&py=${p.y}&pz=${p.z}&ox=${o.x}&oy=${o.y}&oz=${o.z}`;const a=document.createElement("a");a.href="/section-dxf?"+q;a.download="section.dxf";a.click();};
chartBtn.onclick=()=>showChart();
function createSec(normal,point){
removeSec();
clipPlane=new THREE.Plane(normal.clone().negate(),point.dot(normal));
r.clippingPlanes=[clipPlane];
mg.traverse(c=>{if(c.material){const mats=Array.isArray(c.material)?c.material:[c.material];mats.forEach(m=>{m.side=THREE.DoubleSide;m.needsUpdate=true})}});
const box=new THREE.Box3().setFromObject(mg);const s2=box.getSize(new THREE.Vector3());const sz=Math.max(s2.x,s2.y,s2.z)*0.5;
const pg=new THREE.PlaneGeometry(sz,sz);const pm=new THREE.MeshBasicMaterial({color:0xff4444,side:THREE.DoubleSide,transparent:true,opacity:0.2,depthTest:true,depthWrite:false});
visPlane=new THREE.Mesh(pg,pm);visPlane.position.copy(point);
visPlane.quaternion.setFromUnitVectors(new THREE.Vector3(0,0,1),normal);
sc.add(visPlane);secMode="active";
sec.style.background="rgba(239,68,68,0.7)";sec.style.color="white";dxf.style.display="inline-block";
s.textContent="Drag to move | Click Section to remove";
}
function removeSec(){
r.clippingPlanes=[];if(visPlane){sc.remove(visPlane);visPlane.geometry.dispose();visPlane.material.dispose();visPlane=null;}
clipPlane=null;secMode="off";secDrag=false;
mg.traverse(c=>{if(c.material){const mats=Array.isArray(c.material)?c.material:[c.material];mats.forEach(m=>{m.side=THREE.FrontSide;m.needsUpdate=true})}});
sec.style.background="rgba(239,68,68,0.2)";sec.style.color="#ef4444";dxf.style.display="none";
updateStatus();
}

const sc=new THREE.Scene();sc.background=new THREE.Color("#1a1a2e");
const cam=new THREE.PerspectiveCamera(55,innerWidth/innerHeight,0.001,1e9);
cam.position.set(20,15,20);
const r=new THREE.WebGLRenderer({antialias:true});
r.setPixelRatio(Math.min(devicePixelRatio,2));r.setSize(innerWidth,innerHeight);r.shadowMap.enabled=true;
c.appendChild(r.domElement);
sc.add(new THREE.AmbientLight("#ffffff",1.8));
const sun=new THREE.DirectionalLight("#ffffff",3.5);sun.position.set(30,50,20);sc.add(sun);
const grid=new THREE.GridHelper(40,30,"#444466","#2a2a3e");sc.add(grid);

const ctrl=new OrbitControls(cam,r.domElement);
ctrl.enableDamping=false;ctrl.target.set(0,3,0);
ctrl.enableZoom=false;

// Custom smooth additive zoom (5% per scroll)
c.addEventListener("wheel",(e)=>{
e.preventDefault();
const step=ctrl.target.distanceTo(cam.position)*0.05;
const dir=cam.position.clone().sub(ctrl.target).normalize();
if(e.deltaY>0)cam.position.addScaledVector(dir,step);
else cam.position.addScaledVector(dir,-step);
const d2=cam.position.distanceTo(ctrl.target);
if(d2<0.001)cam.position.copy(ctrl.target).addScaledVector(dir,0.001);
if(d2>1e9)cam.position.copy(ctrl.target).addScaledVector(dir,1e9);
},{passive:false});

let mg=new THREE.Group();sc.add(mg);
const modelColors=["#22c55e","#3b82f6","#f97316","#eab308","#ec4899","#8b5cf6","#06b6d4","#ef4444","#14b8a6","#f43f5e","#84cc16","#e11d48","#a855f7","#f59e0b"];
window._models=[];
let activeModelIndex=-1;
const loader=new GLTFLoader();
const raycaster=new THREE.Raycaster();raycaster.firstHitOnly=true;
const hlMat=new THREE.MeshStandardMaterial({color:0xff6600,emissive:0xff3300,emissiveIntensity:0.3,roughness:0.4,metalness:0.1,side:THREE.DoubleSide});
let hlMeshes=[];
function clearHl(){hlMeshes.forEach(({m,o})=>{m.material=o});hlMeshes=[]}

// Click to select
c.addEventListener("click",(e)=>{
if(e.button!==0)return;
const mouse=new THREE.Vector2((e.clientX/c.clientWidth)*2-1,-(e.clientY/c.clientHeight)*2+1);
raycaster.setFromCamera(mouse,cam);
const hits=raycaster.intersectObjects(mg.children,true);
if(secMode==="pick"){if(hits.length>0){const p=hits[0].point.clone();const nm=new THREE.Matrix3().getNormalMatrix(hits[0].object.matrixWorld);const n=hits[0].face.normal.clone().applyMatrix3(nm).normalize();createSec(n,p);}return;}
if(hits.length>0){
// Only select elements from active model
let mesh=hits[0].object;let elemMatch=mesh.name.match(/elem_(\\d+)/);
if(elemMatch){let ei=parseInt(elemMatch[1]);let am=window._models[activeModelIndex];if(am){if(ei<am.propStart||ei>=am.propStart+am.propCount){panel.classList.remove("visible");return}}}
clearHl();
hlMeshes.push({m:mesh,o:mesh.material});mesh.material=hlMat;
let props={};
const m=mesh.name.match(/elem_(\d+)/);
if(m&&window._ifcProps)props=window._ifcProps[parseInt(m[1])]||{};
let h="<h3>"+(props.Type||"Element")+"</h3>";
if(props.Name)h+="<div style='color:#818cf8;font-size:12px;margin-bottom:8px'>"+props.Name+"</div>";
if(props.GlobalId)h+="<div class='row'><span class='key'>GlobalId</span><span class='val' style='font-size:11px'>"+props.GlobalId+"</span></div>";
const psets={},others=[];
for(const[k,v]of Object.entries(props)){
if(k==="Type"||k==="Name"||k==="GlobalId")continue;
const dot=k.indexOf(".");
if(dot>0){const pn=k.substring(0,dot);if(!psets[pn])psets[pn]=[];psets[pn].push([k.substring(dot+1),v]);}
else others.push([k,v]);
}
for(const[pn,items]of Object.entries(psets)){
h+="<div style='color:#6366f1;font-size:11px;margin:8px 0 2px;font-weight:600;border-top:1px solid rgba(255,255,255,0.08);padding-top:4px'>"+pn+"</div>";
for(const[k,v]of items)h+="<div class='row'><span class='key'>"+k+"</span><span class='val'>"+v+"</span></div>";}
if(others.length){h+="<div style='color:#6366f1;font-size:11px;margin:8px 0 2px;font-weight:600;border-top:1px solid rgba(255,255,255,0.08);padding-top:4px'>Other</div>";
for(const[k,v]of others)h+="<div class='row'><span class='key'>"+k+"</span><span class='val'>"+v+"</span></div>";}
panel.innerHTML=h;panel.classList.add("visible");
}else{
clearHl();
panel.classList.remove("visible");
updateStatus();
}
});
r.domElement.addEventListener("pointerdown",e=>{if(secMode!=="active")return;const mouse=new THREE.Vector2((e.clientX/c.clientWidth)*2-1,-(e.clientY/c.clientHeight)*2+1);const rc=new THREE.Raycaster();rc.setFromCamera(mouse,cam);if(rc.intersectObject(visPlane).length>0){secDrag=true;secLastY=e.clientY;ctrl.enabled=false;e.stopPropagation();}});
r.domElement.addEventListener("pointermove",e=>{if(!secDrag||!clipPlane||!visPlane)return;const d=(secLastY-e.clientY)*cam.position.distanceTo(visPlane.position)*0.002;secLastY=e.clientY;clipPlane.constant+=d;visPlane.position.addScaledVector(clipPlane.normal.clone(),-d);});
r.domElement.addEventListener("pointerup",()=>{secDrag=false;ctrl.enabled=true;});

function totalElements(){let n=0;mg.children.forEach(c=>{c.traverse(cc=>{if(typeof cc.name==="string"&&cc.name.startsWith("elem_"))n++})});return n}
function updateStatus(){let m=window._models.length;s.textContent=totalElements()+" elements ("+m+" model"+(m!==1?"s":"")+")"}
function disposeRecursive(obj){obj.traverse(c=>{if(c.geometry)c.geometry.dispose();if(c.material)(Array.isArray(c.material)?c.material:[c.material]).forEach(m=>m.dispose())})}

async function loadModelData(buf,fname,append){
const resp=await fetch("/convert"+(append?"?append=1":""),{method:"POST",body:buf});
if(!resp.ok){s.textContent="Error: "+resp.status;return null}
const data=await resp.json();
const glbBytes=Uint8Array.from(atob(data.glb),c=>c.charCodeAt(0));
const blob=new Blob([glbBytes],{type:"model/gltf-binary"});
const url=URL.createObjectURL(blob);
return new Promise((resolve,reject)=>{loader.load(url,(gltf)=>{
URL.revokeObjectURL(url);
gltf.scene.name="model_"+window._models.length;
mg.add(gltf.scene);
const modelGroup=gltf.scene;
const startIdx=window._ifcProps?window._ifcProps.length:0;
const newProps=data.props||[];
window._ifcProps=window._ifcProps?[...window._ifcProps,...newProps]:newProps;
modelGroup.traverse(c=>{if(typeof c.name==="string"&&c.name.startsWith("elem_")){let n=parseInt(c.name.slice(5));if(!isNaN(n))c.name="elem_"+(startIdx+n)}});
const mi={name:fname,group:modelGroup,propStart:startIdx,propCount:newProps.length,visible:true,color:modelColors[window._models.length%modelColors.length]};
window._models.push(mi);
if(!append){
const box=new THREE.Box3().setFromObject(mg);
const center=new THREE.Vector3();box.getCenter(center);
mg.position.set(-center.x,-center.y,-center.z);
box.setFromObject(mg);box.getCenter(center);
const size=new THREE.Vector3();box.getSize(size);
const d=Math.max(size.x,size.y,size.z)||10;
cam.near=0.001;cam.far=Math.max(d*100,1e7);cam.updateProjectionMatrix();
ctrl.target.set(0,0,0);
cam.position.set(d*2, d*1.5, d*2);ctrl.update();
grid.position.set(0,box.min.y-0.5,0);
grid.scale.set(Math.max(d*1.5,20)/20,1,Math.max(d*1.5,20)/20);
}
buildCategories();buildModelTree();appendBtn.style.display="inline-block";exp.style.display="inline-block";sec.style.display="inline-block";chartBtn.style.display="inline-block";updateStatus();
resolve(mi);
},undefined,(err)=>{s.textContent="Load error: "+err;reject(err)});});
}

fi.onchange=async()=>{removeSec();
const f=fi.files[0];if(!f)return;
s.textContent="Uploading...";
clearHl();
while(mg.children.length>0){const c=mg.children[0];mg.remove(c);disposeRecursive(c)}
window._ifcProps=[];window._models=[];activeModelIndex=-1;panel.classList.remove("visible");E("catPanel").classList.remove("visible");E("treePanel").classList.remove("visible");E("chartPanel").classList.remove("visible");
try{const buf=await f.arrayBuffer();await loadModelData(buf,f.name,false)}catch(e){s.textContent="Error: "+e.message}
fi.value="";
};

af.onchange=async()=>{removeSec();
const f=af.files[0];if(!f)return;
s.textContent="Appending...";
try{const buf=await f.arrayBuffer();await loadModelData(buf,f.name,true)}catch(e){s.textContent="Error: "+e.message}
af.value="";
};
const catCols=["#ef4444","#f97316","#eab308","#22c55e","#06b6d4","#3b82f6","#8b5cf6","#ec4899","#14b8a6","#f43f5e","#84cc16","#e11d48","#a855f7","#f59e0b"];
let catData={};
function buildCategories(){
if(!window._ifcProps)return;
// Rebuild categories for all models
window._models.forEach((m,i)=>{
buildModelCategories(i);
});
// Auto-activate first model if none active
if(activeModelIndex<0&&window._models.length>0){activeModelIndex=0;buildModelCategories(0)}
renderCatPanel();
buildModelTree();
}
function buildModelCategories(idx){
const m=window._models[idx];if(!m)return;
const start=m.propStart;const count=m.propCount;
m.categories={};
for(let i=start;i<start+count;i++){
const p=window._ifcProps[i];if(!p)continue;
const t=p.Type||"Unknown";
if(!m.categories[t])m.categories[t]={indices:[],visible:true,color:catCols[Object.keys(m.categories).length%catCols.length]};
m.categories[t].indices.push(i);
}
}
function renderCatPanel(){
const cp=E("catPanel");
if(activeModelIndex<0||!window._models[activeModelIndex]){cp.classList.remove("visible");return}
const m=window._models[activeModelIndex];
const cd=m.categories||{};
let h='<h3>'+m.name+' <span style="font-size:10px;color:#6366f1">'+Object.keys(cd).length+' types</span></h3>';
for(const[t,d]of Object.entries(cd)){
const esc=t.replace(/'/g,"&#39;");
h+='<div class="cat-row'+(d.visible?'':' off')+'"><span class="cat-eye'+(d.visible?'':' off')+'" data-act="eye" data-cat="'+esc+'">👁</span><span class="cat-dot" style="background:'+d.color+'"></span><span class="cat-name">'+t.replace("Ifc","")+'</span><span class="cat-count">'+d.indices.length+'</span><button class="cat-btn" data-act="sel" data-cat="'+esc+'">Select</button></div>';
}
cp.innerHTML=h;cp.classList.add("visible");
cp.onclick=e=>{
const btn=e.target.closest("[data-act]");
if(!btn)return;
const cat=btn.dataset.cat;
if(btn.dataset.act==="eye")toggleCat(cat);
else selectCat(cat);
};
}
function toggleCat(type){
const m=window._models[activeModelIndex];if(!m||!m.categories)return;
const d=m.categories[type];if(!d)return;
d.visible=!d.visible;
d.indices.forEach(i=>{
const obj=mg.getObjectByName("elem_"+i);
if(obj)obj.visible=d.visible;
});
clearHl();renderCatPanel();
}
function selectCat(type){
clearHl();
const m=window._models[activeModelIndex];if(!m||!m.categories)return;
const d=m.categories[type];if(!d)return;
d.indices.forEach(i=>{
const obj=mg.getObjectByName("elem_"+i);
if(obj&&obj.visible){hlMeshes.push({m:obj,o:obj.material});obj.material=hlMat}
});
panel.innerHTML='<h3>'+type.replace("Ifc","")+'</h3><div class="row"><span class="key">Count</span><span class="val">'+d.indices.length+'</span></div>';
panel.classList.add("visible");
}

function buildModelTree(){
const tp=E("treePanel");
if(!window._models.length){tp.classList.remove("visible");return}
let h='<h3>Models <span style="font-size:10px;color:#6366f1">'+window._models.length+'</span></h3>';
window._models.forEach((m,i)=>{
const isActive=(i===activeModelIndex);
const expanded=m._expanded||false;
h+='<div class="model-node'+(m.visible?'':' off')+'">';
h+='<div class="header'+(isActive?' sel':'')+'">';
h+='<span class="arrow" data-act="expandModel" data-idx="'+i+'">'+(expanded?'▼':'▶')+'</span>';
h+='<span class="eye'+(m.visible?'':' off')+'" data-act="eyeModel" data-idx="'+i+'">👁</span>';
h+='<span class="dot" style="background:'+m.color+'"></span>';
h+='<span class="name" data-act="selModel" data-idx="'+i+'">'+m.name+'</span>';
h+='<span class="count">'+m.propCount+'</span></div>';
// Sub-items
const cd=m.categories||{};
h+='<div class="sub-items'+(expanded?' open':'')+'">';
for(const[type,cat] of Object.entries(cd)){
const esc=type.replace(/'/g,"&#39;");
h+='<div class="sub-row'+(cat.visible?'':' off')+'">';
h+='<span class="sub-eye'+(cat.visible?'':' off')+'" data-act="treeEye" data-model="'+i+'" data-cat="'+esc+'">👁</span>';
h+='<span class="sub-dot" style="background:'+cat.color+'"></span>';
h+='<span class="sub-name">'+type.replace("Ifc","")+'</span>';
h+='<span class="sub-count">'+cat.indices.length+'</span>';
h+='<span class="sub-sel" data-act="treeSel" data-model="'+i+'" data-cat="'+esc+'">Sel</span>';
h+='</div>';
}
h+='</div></div>';
});
tp.innerHTML=h;tp.classList.add("visible");
tp.onclick=e=>{
const btn=e.target.closest("[data-act]");
if(!btn)return;
const idx=parseInt(btn.dataset.idx);
if(btn.dataset.act==="eyeModel")toggleModel(idx);
else if(btn.dataset.act==="selModel")activateModel(idx);
else if(btn.dataset.act==="expandModel"){window._models[idx]._expanded=!window._models[idx]._expanded;buildModelTree()}
else if(btn.dataset.act==="treeEye"){treeToggleCat(parseInt(btn.dataset.model),btn.dataset.cat)}
else if(btn.dataset.act==="treeSel"){treeSelectCat(parseInt(btn.dataset.model),btn.dataset.cat)}
};
}
function treeToggleCat(mi,type){
const m=window._models[mi];if(!m||!m.categories)return;
const d=m.categories[type];if(!d)return;
d.visible=!d.visible;
d.indices.forEach(i=>{const obj=mg.getObjectByName("elem_"+i);if(obj)obj.visible=d.visible});
clearHl();buildModelTree();renderCatPanel();
}
function treeSelectCat(mi,type){
clearHl();
const m=window._models[mi];if(!m||!m.categories)return;
const d=m.categories[type];if(!d)return;
d.indices.forEach(i=>{const obj=mg.getObjectByName("elem_"+i);if(obj&&obj.visible){hlMeshes.push({m:obj,o:obj.material});obj.material=hlMat}});
panel.innerHTML='<h3>'+m.name+' / '+type.replace("Ifc","")+'</h3><div class="row"><span class="key">Count</span><span class="val">'+d.indices.length+'</span></div>';
panel.classList.add("visible");
}
function activateModel(idx){
if(idx<0||idx>=window._models.length)return;
clearHl();
activeModelIndex=idx;
if(window._models[idx]&&!window._models[idx].categories)buildModelCategories(idx);
renderCatPanel();
buildModelTree();
const m=window._models[idx];
if(m){
m.group.traverse(c=>{
if(typeof c.name==="string"&&c.name.startsWith("elem_")&&c.visible){hlMeshes.push({m:c,o:c.material});c.material=hlMat}
});
panel.innerHTML='<h3>'+m.name+'</h3><div class="row"><span class="key">Elements</span><span class="val">'+m.propCount+'</span></div>';
panel.classList.add("visible");
}
}
function toggleModel(idx){
const m=window._models[idx];if(!m)return;
m.visible=!m.visible;
m.group.traverse(c=>{if(typeof c.name==="string"&&c.name.startsWith("elem_"))c.visible=m.visible});
clearHl();buildModelTree();
}
function selectModel(idx){
clearHl();
const m=window._models[idx];if(!m)return;
m.group.traverse(c=>{
if(typeof c.name==="string"&&c.name.startsWith("elem_")&&c.visible){hlMeshes.push({m:c,o:c.material});c.material=hlMat}
});
panel.innerHTML='<h3>'+m.name+'</h3><div class="row"><span class="key">Elements</span><span class="val">'+m.propCount+'</span></div>';
panel.classList.add("visible");
}
function showChart(){
if(chartPanel.classList.contains("visible")){Plotly.purge(chartPanel);chartPanel.classList.remove("visible");return}
if(!window._ifcProps||!window._ifcProps.length)return;
const counts={};
window._ifcProps.forEach(p=>{const t=p.Type||"Unknown";counts[t]=(counts[t]||0)+1});
const entries=Object.entries(counts).sort((a,b)=>b[1]-a[1]);
const labels=entries.map(e=>e[0].replace("Ifc",""));
const types=entries.map(e=>e[0]);
const values=entries.map(e=>e[1]);
const barColors=values.map((_,i)=>catCols[i%catCols.length]);
const data=[{type:"bar",x:labels,y:values,marker:{color:barColors},text:values.map(v=>v.toString()),textposition:"outside",hoverinfo:"x+y"}];
const layout={paper_bgcolor:"rgba(0,0,0,0)",plot_bgcolor:"rgba(0,0,0,0)",font:{color:"#c7d2fe",size:11},xaxis:{tickangle:-45,gridcolor:"rgba(255,255,255,0.05)",tickfont:{size:10}},yaxis:{title:"Count",gridcolor:"rgba(255,255,255,0.05)"},margin:{l:50,r:20,t:10,b:80},showlegend:false};
Plotly.newPlot(chartPanel,data,layout,{responsive:true,displayModeBar:false});
chartPanel.classList.add("visible");
chartPanel.on("plotly_click",function(d){
const idx=d.points[0].pointIndex;const cat=types[idx];clearHl();
const m=window._models[activeModelIndex];
if(m&&m.categories&&m.categories[cat]){
const cd=m.categories[cat];
cd.indices.forEach(i=>{const obj=mg.getObjectByName("elem_"+i);if(obj&&obj.visible){hlMeshes.push({m:obj,o:obj.material});obj.material=hlMat}});
panel.innerHTML='<h3>'+cat.replace("Ifc","")+'</h3><div class="row"><span class="key">Count</span><span class="val">'+cd.indices.length+'</span></div>';
panel.classList.add("visible");
}
});
}
(function a(){requestAnimationFrame(a);ctrl.update();r.render(sc,cam);})();
window.addEventListener("resize",()=>{cam.aspect=innerWidth/innerHeight;cam.updateProjectionMatrix();r.setSize(innerWidth,innerHeight);});
</script></body></html>'''

def ifc_to_glb(data, append=False):
    tmpdir=tempfile.mkdtemp()
    ifc_path=os.path.join(tmpdir,"model.ifc")
    with open(ifc_path,"wb") as f:f.write(data)
    ifc=ifcopenshell.open(ifc_path)
    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    elements=ifc.by_type("IfcBuildingElement") or ifc.by_type("IfcProduct") or list(ifc)[:500]
    meshes=[]
    props_list=[]
    for elem in elements:
        try:
            shape=ifcopenshell.geom.create_shape(settings,elem)
            if not shape or not shape.geometry:continue
            verts=np.array(shape.geometry.verts,dtype=np.float64).reshape(-1,3)
            faces=np.array(shape.geometry.faces,dtype=np.int32).reshape(-1,3)
            if len(verts)==0 or len(faces)==0:continue
            m=trimesh.Trimesh(vertices=verts,faces=faces,process=False)
            R=np.array([[1,0,0],[0,0,-1],[0,1,0]],dtype=np.float64)
            m.apply_transform(np.vstack([np.hstack([R,np.zeros((3,1))]),[0,0,0,1]]))
            # Extract element properties
            props={"Type":elem.is_a(),"GlobalId":getattr(elem,"GlobalId",""),"Name":getattr(elem,"Name","") or ""}
            # Get property sets
            try:
                for rel in getattr(elem,"IsDefinedBy",[]) or []:
                    if rel.is_a("IfcRelDefinesByProperties"):
                        pset=rel.RelatingPropertyDefinition
                        if pset and pset.is_a("IfcPropertySet"):
                            pname=pset.Name or "Pset"
                            for prop in pset.HasProperties or []:
                                val=getattr(prop,"NominalValue",None)
                                if val:props[f"{pname}.{prop.Name}"]=str(val.wrappedValue if hasattr(val,"wrappedValue") else val)
            except:pass
            meshes.append(m)
            props_list.append(props)
        except:pass
    if not meshes:return None
    global _last_meshes
    if append:
        _last_meshes.extend(meshes)
    else:
        _last_meshes = meshes
    # Export as scene with separate meshes
    scene=trimesh.Scene()
    for i,m in enumerate(meshes):
        scene.add_geometry(m,node_name=f"elem_{i}")
    glb=scene.export(file_type="glb")
    # Encode GLB as base64 and return with props as JSON
    import base64
    return json.dumps({"glb":base64.b64encode(glb).decode(),"props":props_list}).encode()

_last_meshes = []

def _compute_section(normal, point, offset):
    p = np.array(point, dtype=np.float64) - np.array(offset, dtype=np.float64)
    n = np.array(normal, dtype=np.float64)
    n = n / np.linalg.norm(n) if np.linalg.norm(n) > 0 else n
    lines = []
    for m in _last_meshes:
        try:
            segs = trimesh.intersections.mesh_plane(m, n, p)
            if segs is not None and len(segs) > 0:
                lines.append(segs)
        except: pass
    if not lines: return None
    return np.vstack(lines)

def _flatten_section_to_xy(lines, normal, origin):
    """Project 3D section segments onto the section plane, then map to AutoCAD XY (Z=0).

    Coordinate convention (matches looking at the cut from the kept / unclipped side):
    - sheet +X  = right
    - sheet +Y  = up
    - sheet +Z  = 0 (all geometry flattened onto XY)
    """
    n = np.array(normal, dtype=np.float64)
    nn = np.linalg.norm(n)
    n = n / nn if nn > 1e-12 else np.array([0.0, 0.0, 1.0])
    origin = np.array(origin, dtype=np.float64)

    # Prefer world +Y as sheet-up. For near-horizontal sections (plan), use world +Z.
    up_ref = np.array([0.0, 1.0, 0.0]) if abs(n[1]) < 0.9 else np.array([0.0, 0.0, 1.0])
    # Project up onto the plane, then build a right-handed basis for a viewer
    # looking along -n (from kept side toward the cut face).
    v = up_ref - n * np.dot(up_ref, n)
    vn = np.linalg.norm(v)
    if vn < 1e-12:
        up_ref = np.array([1.0, 0.0, 0.0])
        v = up_ref - n * np.dot(up_ref, n)
        vn = np.linalg.norm(v)
    v = v / vn
    # right = up × look_back, look_back = n  =>  u = v × n
    # Previous u = ref × n produced a left/right mirror in AutoCAD.
    u = np.cross(v, n)
    un = np.linalg.norm(u)
    if un < 1e-12:
        u = np.array([1.0, 0.0, 0.0])
    else:
        u = u / un
    # Re-orthogonalize v so (u, v, n) is orthonormal and right-handed.
    v = np.cross(n, u)
    v = v / np.linalg.norm(v)

    flat = []
    for seg in lines:
        p0 = np.asarray(seg[0], dtype=np.float64) - origin
        p1 = np.asarray(seg[1], dtype=np.float64) - origin
        # Local plane coords: (right, up)
        # AutoCAD correction reported by user:
        #   1) CCW 90° about Z:  (x, y) -> (-y, x)
        #   2) 180° about N-S (Y): (x, y, z) -> (-x, y, -z)
        #   3) 180° about Z: (x, y) -> (-x, -y)
        # Combined on Z=0: (x, y) -> (-y, -x)
        x0, y0 = float(np.dot(p0, u)), float(np.dot(p0, v))
        x1, y1 = float(np.dot(p1, u)), float(np.dot(p1, v))
        a = (-y0, -x0, 0.0)
        b = (-y1, -x1, 0.0)
        flat.append((a, b))
    return flat

class H(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path=="/" or self.path=="/index.html":
            self.send_response(200);self.send_header("Content-Type","text/html; charset=utf-8");self.end_headers()
            self.wfile.write(HTML.encode())
        elif self.path.startswith("/favicon.png") or self.path=="/webicon.png":
            try:
                ico_path=os.path.join(os.path.dirname(__file__),"logo","az.png")
                with open(ico_path,"rb") as f:data=f.read()
                self.send_response(200);self.send_header("Content-Type","image/png")
                self.send_header("Content-Length",str(len(data)));self.end_headers()
                self.wfile.write(data)
            except: self.send_error(404)
        elif self.path.startswith("/section-dxf"):
            try:
                qs = parse_qs(urlparse(self.path).query)
                nx = float(qs.get("nx",[0])[0]); ny = float(qs.get("ny",[0])[0]); nz = float(qs.get("nz",[0])[0])
                px = float(qs.get("px",[0])[0]); py = float(qs.get("py",[0])[0]); pz = float(qs.get("pz",[0])[0])
                ox = float(qs.get("ox",[0])[0]); oy = float(qs.get("oy",[0])[0]); oz = float(qs.get("oz",[0])[0])
                lines = _compute_section((nx,ny,nz), (px,py,pz), (ox,oy,oz))
                if lines is None: self.send_error(404); return
                origin = np.array([px, py, pz], dtype=np.float64) - np.array([ox, oy, oz], dtype=np.float64)
                flat = _flatten_section_to_xy(lines, (nx, ny, nz), origin)
                doc = ezdxf.new(); msp = doc.modelspace()
                for a, b in flat:
                    msp.add_line(a, b)
                buf = io.StringIO(); doc.write(buf); data = buf.getvalue().encode("utf-8")
                self.send_response(200); self.send_header("Content-Type","application/octet-stream")
                self.send_header("Content-Disposition","attachment; filename=section.dxf")
                self.send_header("Content-Length",str(len(data))); self.end_headers()
                self.wfile.write(data)
            except Exception as e:
                import traceback; traceback.print_exc()
                self.send_response(500); self.send_header("Content-Type","text/plain"); self.end_headers()
                self.wfile.write(str(e).encode())
        else:super().do_GET()
    def do_POST(self):
        if self.path=="/convert" or self.path.startswith("/convert?"):
            qs = parse_qs(urlparse(self.path).query)
            append = qs.get("append",["0"])[0]=="1"
            cl=int(self.headers.get("Content-Length",0))
            if cl==0:self.send_error(400);return
            result=ifc_to_glb(self.rfile.read(cl), append=append)
            if result is None:self.send_error(500);return
            self.send_response(200);self.send_header("Content-Type","application/json");self.send_header("Content-Length",str(len(result)));self.end_headers()
            self.wfile.write(result)
        else:self.send_error(404)

if __name__=="__main__":
    port = int(sys.argv[1]) if len(sys.argv)>1 else 8080
    print(f"IFC Viewer running at http://localhost:{port}")
    http.server.HTTPServer(("0.0.0.0",port),H).serve_forever()
