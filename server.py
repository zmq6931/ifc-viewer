import http.server, os, tempfile, sys, json
import ifcopenshell, ifcopenshell.geom
import trimesh, numpy as np

HTML = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>IFC Viewer</title>
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
#catPanel{position:fixed;top:80px;left:20px;width:250px;max-height:calc(100vh-160px);overflow-y:auto;background:rgba(26,26,46,0.92);backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,0.12);border-radius:12px;padding:12px;z-index:10;color:#c7d2fe;font-size:12px;display:none}
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
</style></head>
<body>
<div id="c"></div>
<div id="bar">
<button id="btn">Open IFC File</button>
<input type="file" id="f" accept=".ifc">
<span id="s">Ready</span>
</div>
<div id="tip">Wheel: zoom | Left drag: rotate | Right drag: pan | Click: select</div>
<div id="catPanel"></div>
<div id="panel"></div>
<script type="importmap">
{"imports":{"three":"https://unpkg.com/three@0.160.0/build/three.module.js","three/addons/":"https://unpkg.com/three@0.160.0/examples/jsm/"}}
</script>
<script type="module">
import * as THREE from "three";
import {OrbitControls} from "three/addons/controls/OrbitControls.js";
import {GLTFLoader} from "three/addons/loaders/GLTFLoader.js";

const E=id=>document.getElementById(id);
const s=E("s"),btn=E("btn"),fi=E("f"),c=E("c"),panel=E("panel");
btn.onclick=()=>fi.click();

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
if(hits.length>0){
clearHl();
const mesh=hits[0].object;
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
s.textContent=mg.children.length+" elements";
}
});

fi.onchange=async()=>{
const f=fi.files[0];if(!f)return;
s.textContent="Uploading...";
while(mg.children.length>0){const c=mg.children[0];mg.remove(c);if(c.geometry)c.geometry.dispose();if(c.material)(Array.isArray(c.material)?c.material:[c.material]).forEach(m=>m.dispose());}
try{
const buf=await f.arrayBuffer();
const resp=await fetch("/convert",{method:"POST",body:buf});
if(!resp.ok){s.textContent="Error: "+resp.status;return;}
const data=await resp.json();
// Decode base64 GLB
const glbBytes=Uint8Array.from(atob(data.glb),c=>c.charCodeAt(0));
const blob=new Blob([glbBytes],{type:"model/gltf-binary"});
const url=URL.createObjectURL(blob);
// Store props globally for click handler
window._ifcProps=data.props||[];
s.textContent="Loading...";
loader.load(url,(gltf)=>{
mg.add(gltf.scene);URL.revokeObjectURL(url);
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
s.textContent=mg.children.length+" elements";buildCategories();
},undefined,(err)=>{s.textContent="Load error: "+err;});
}catch(e){s.textContent="Error: "+e.message;}
};
const catCols=["#ef4444","#f97316","#eab308","#22c55e","#06b6d4","#3b82f6","#8b5cf6","#ec4899","#14b8a6","#f43f5e","#84cc16","#e11d48","#a855f7","#f59e0b"];
let catData={};
function buildCategories(){
if(!window._ifcProps)return;
catData={};
window._ifcProps.forEach((p,i)=>{
const t=p.Type||"Unknown";
if(!catData[t])catData[t]={indices:[],visible:true,color:catCols[Object.keys(catData).length%catCols.length]};
catData[t].indices.push(i);
});
renderCatPanel();
}
function renderCatPanel(){
const cp=E("catPanel");
let h='<h3>Categories <span style="font-size:10px;color:#6366f1">'+Object.keys(catData).length+'</span></h3>';
for(const[t,d]of Object.entries(catData)){
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
const d=catData[type];if(!d)return;
d.visible=!d.visible;
d.indices.forEach(i=>{
const obj=mg.getObjectByName("elem_"+i);
if(obj)obj.visible=d.visible;
});
clearHl();renderCatPanel();
}
function selectCat(type){
clearHl();
const d=catData[type];if(!d)return;
d.indices.forEach(i=>{
const obj=mg.getObjectByName("elem_"+i);
if(obj&&obj.visible){hlMeshes.push({m:obj,o:obj.material});obj.material=hlMat}
});
panel.innerHTML='<h3>'+type.replace("Ifc","")+'</h3><div class="row"><span class="key">Count</span><span class="val">'+d.indices.length+'</span></div>';
panel.classList.add("visible");
}
(function a(){requestAnimationFrame(a);ctrl.update();r.render(sc,cam);})();
window.addEventListener("resize",()=>{cam.aspect=innerWidth/innerHeight;cam.updateProjectionMatrix();r.setSize(innerWidth,innerHeight);});
</script></body></html>'''

def ifc_to_glb(data):
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
    # Export as scene with separate meshes
    scene=trimesh.Scene()
    for i,m in enumerate(meshes):
        scene.add_geometry(m,node_name=f"elem_{i}")
    glb=scene.export(file_type="glb")
    # Encode GLB as base64 and return with props as JSON
    import base64
    return json.dumps({"glb":base64.b64encode(glb).decode(),"props":props_list}).encode()

class H(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path=="/" or self.path=="/index.html":
            self.send_response(200);self.send_header("Content-Type","text/html; charset=utf-8");self.end_headers()
            self.wfile.write(HTML.encode())
        else:super().do_GET()
    def do_POST(self):
        if self.path=="/convert":
            cl=int(self.headers.get("Content-Length",0))
            if cl==0:self.send_error(400);return
            result=ifc_to_glb(self.rfile.read(cl))
            if result is None:self.send_error(500);return
            self.send_response(200);self.send_header("Content-Type","application/json");self.send_header("Content-Length",str(len(result)));self.end_headers()
            self.wfile.write(result)
        else:self.send_error(404)

if __name__=="__main__":
    port = int(sys.argv[1]) if len(sys.argv)>1 else 8080
    print(f"IFC Viewer running at http://localhost:{port}")
    http.server.HTTPServer(("0.0.0.0",port),H).serve_forever()
