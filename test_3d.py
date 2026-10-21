import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide", page_title="量子矩陣深空終端", page_icon="🌌")

# ==========================================
# 🎨 1. 深空宇宙暗藍底色與全域設定 (原封不動)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&family=JetBrains+Mono:wght@600;800&display=swap');
    * { box-sizing: border-box; margin: 0; padding: 0; }
    .stApp {
        background-color: #030814 !important;
        background-image: radial-gradient(circle at 50% 20%, rgba(0, 210, 255, 0.18) 0%, rgba(3, 8, 20, 0) 65%), linear-gradient(rgba(0, 210, 255, 0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 210, 255, 0.035) 1px, transparent 1px) !important;
        background-size: 100% 100%, 45px 45px, 45px 45px !important;
        background-position: center top, center center, center center !important;
        background-attachment: fixed !important;
    }
    header[data-testid="stHeader"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🛸 2. 終極全息展示層
# ==========================================
components.html(
    f"""
    <!DOCTYPE html><html><head>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&family=JetBrains+Mono:wght@600;800&display=swap" rel="stylesheet">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ overflow: hidden; background: transparent; font-family: 'Inter', sans-serif; user-select: none; }}
        #canvas-container {{ position: absolute; top: 0; left: 0; width: 100vw; height: 560px; z-index: 1; pointer-events: none; }}
        #ui-container {{ position: relative; z-index: 10; width: 100vw; display: flex; flex-direction: column; align-items: center; padding-top: 195px; }}
        .hero-title {{ color: #FFF !important; font-size: 2.3rem; font-weight: 900; letter-spacing: 2.5px; text-shadow: 0 0 25px rgba(0,210,255,0.75), 0 2px 4px rgba(0,0,0,0.9); margin-bottom: 8px; text-align: center; }}
        .status-pill {{ display: inline-flex; align-items: center; gap: 8px; background: rgba(0,210,255,0.12); border: 1px solid rgba(0,210,255,0.45); border-radius: 999px; padding: 5px 18px; color: #FFF !important; font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 700; letter-spacing: 1px; box-shadow: 0 0 20px rgba(0,210,255,0.25); margin-bottom: 24px; }}
        .status-dot {{ width: 8px; height: 8px; background: #00F59B; border-radius: 50%; box-shadow: 0 0 10px #00F59B; }}
        .cards-wrapper {{ display: flex; justify-content: center; gap: 26px; width: 100%; max-width: 950px; }}
        .metric-card {{ flex: 1; background: rgba(6,18,40,0.72); border: 1px solid rgba(0,210,255,0.35); border-top: 2px solid rgba(0,210,255,0.95); border-radius: 14px; padding: 18px 20px; text-align: center; backdrop-filter: blur(16px); box-shadow: 0 15px 35px rgba(0,0,0,0.85), inset 0 1px 0 rgba(255,255,255,0.2); transition: transform 0.25s; }}
        .metric-card:hover {{ transform: translateY(-4px); border-top: 2px solid #FFD700; box-shadow: 0 18px 45px rgba(0,0,0,0.95), 0 0 20px rgba(0,210,255,0.4); }}
        .card-label {{ color: #FFF !important; font-size: 1.1rem; font-weight: 800; letter-spacing: 0.5px; margin-bottom: 8px; text-shadow: 0 2px 4px rgba(0,0,0,0.95); }}
        .card-value {{ color: #FFD700 !important; font-size: 2.4rem; font-weight: 900; text-shadow: 0 0 25px rgba(255,215,0,0.7); }}
    </style></head><body>
    <div id="canvas-container"></div>
    <div id="ui-container">
        <div class="hero-title">大指揮官 · 全球量化矩陣核心</div>
        <div class="status-pill"><span class="status-dot"></span>QUANTUM STREAM // 14,309 ASSETS DYNAMIC MONITORING</div>
        <div class="cards-wrapper">
            <div class="metric-card"><div class="card-label">👑 觸發標的數</div><div class="card-value">100 隻</div></div>
            <div class="metric-card"><div class="card-label">🐉 真龍 / 真皇數</div><div class="card-value">35 隻</div></div>
            <div class="metric-card"><div class="card-label">🚨 跌穿防線數量</div><div class="card-value">0 隻</div></div>
        </div>
    </div>
    <script>
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(40, window.innerWidth/560, 0.1, 1000);
        camera.position.set(0, 1.2, 25);
        const renderer = new THREE.WebGLRenderer({{alpha:true, antialias:true}});
        renderer.setSize(window.innerWidth, 560); renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.15;
        document.getElementById('canvas-container').appendChild(renderer.domElement);

        scene.add(new THREE.AmbientLight(0x0a223d, 2.2));
        const cL = new THREE.DirectionalLight(0x00e5ff, 3.8); cL.position.set(-15, 14, 12); scene.add(cL);
        const eL = new THREE.DirectionalLight(0x00f59b, 2.8); eL.position.set(16, 12, 10); scene.add(eL);

        function cHalo() {{
            const c = document.createElement('canvas'); c.width=512; c.height=512; const ctx = c.getContext('2d');
            const g = ctx.createRadialGradient(256,256,120,256,256,252);
            g.addColorStop(0, 'rgba(0,220,255,0.38)'); g.addColorStop(0.5, 'rgba(0,180,255,0.16)'); g.addColorStop(0.85, 'rgba(0,140,255,0.04)'); g.addColorStop(1, 'rgba(0,0,0,0)');
            ctx.fillStyle = g; ctx.fillRect(0,0,512,512); return new THREE.CanvasTexture(c);
        }}
        const halo = new THREE.Mesh(new THREE.PlaneGeometry(38,38), new THREE.MeshBasicMaterial({{map:cHalo(), transparent:true, blending:THREE.AdditiveBlending, depthWrite:false}}));
        halo.position.set(0, 3.8, -9); scene.add(halo);

        // =====================================
        // 🛸 3. 中央核心 (原封不動)
        // =====================================
        const coreGrp = new THREE.Group(); coreGrp.position.set(0, 4.2, 0); scene.add(coreGrp);
        const cryGeo = new THREE.OctahedronGeometry(2.35, 0);
        
        const cry = new THREE.Mesh(cryGeo, new THREE.MeshPhysicalMaterial({{color:0x0c3156, emissive:0x041b30, metalness:0.6, roughness:0.02, transmission:0.95, thickness:3.0, ior:2.4, transparent:true, opacity:0.9, reflectivity:1.0, clearcoat:1.0, clearcoatRoughness:0.05}}));
        coreGrp.add(cry);
        cry.add(new THREE.LineSegments(new THREE.EdgesGeometry(cryGeo), new THREE.LineBasicMaterial({{color:0x67e8f9, linewidth:2, transparent:true, opacity:0.95, blending:THREE.AdditiveBlending}})));
        
        const innerCry = new THREE.Mesh(cryGeo, new THREE.MeshPhysicalMaterial({{color:0x00d9ff, metalness:0.5, roughness:0.05, transmission:0.8, ior:2.0, transparent:true, opacity:0.4, blending:THREE.AdditiveBlending}}));
        innerCry.scale.set(0.85, 0.85, 0.85);
        cry.add(innerCry);

        const dGeo = new THREE.BufferGeometry(); const dPos = new Float32Array(240);
        for(let i=0;i<80;i++){{ dPos[i*3]=(Math.random()-0.5)*2.2; dPos[i*3+1]=-0.3-Math.random()*1.5; dPos[i*3+2]=(Math.random()-0.5)*2.2; }}
        dGeo.setAttribute('position', new THREE.BufferAttribute(dPos, 3));
        cry.add(new THREE.Points(dGeo, new THREE.PointsMaterial({{size:0.08, color:0xffffff, transparent:true, opacity:0.85, blending:THREE.AdditiveBlending}})));
        const iCore = new THREE.Mesh(new THREE.SphereGeometry(0.95,32,32), new THREE.MeshStandardMaterial({{color:0xffea00, emissive:0xff9900, emissiveIntensity:2.4, roughness:0.2}}));
        coreGrp.add(iCore);

        function cRing(r, t, tx, tz, o) {{
            const ring = new THREE.Mesh(new THREE.TorusGeometry(r,t,16,120), new THREE.MeshBasicMaterial({{color:0x00e5ff, transparent:true, opacity:o, blending:THREE.AdditiveBlending}}));
            ring.rotation.x = tx; ring.rotation.z = tz; return ring;
        }}
        const r1=cRing(4.8,0.025,1.36,0.15,0.7); const r2=cRing(5.6,0.02,1.28,-0.22,0.55); const r3=cRing(6.4,0.02,1.46,0.35,0.45);
        coreGrp.add(r1, r2, r3);
        const satGrp = new THREE.Group(); satGrp.rotation.x=1.46; satGrp.rotation.z=0.35; coreGrp.add(satGrp);
        const sat = new THREE.Mesh(new THREE.SphereGeometry(0.16,16,16), new THREE.MeshBasicMaterial({{color:0x67e8f9, blending:THREE.AdditiveBlending}}));
        sat.position.set(6.4,0,0); satGrp.add(sat);

        // =====================================
        // 💡 9. 【精雕細琢】左側虛擬電子風格電燈 (俯視立體角度 + 精緻纖細鎢絲)
        // =====================================
        const bulbGrp = new THREE.Group();
        bulbGrp.position.set(-19.5, 1.2, -3.5);
        bulbGrp.rotation.x = 0.42; // 🌟 俯視角度，底座、內心與光軌立體展開！
        bulbGrp.scale.set(0.75, 0.75, 0.75);
        scene.add(bulbGrp);

        // A. 水滴燈泡外形幾何
        const bulbPoints = [];
        bulbPoints.push(new THREE.Vector2(0, -2.1));
        bulbPoints.push(new THREE.Vector2(0.5, -2.0));
        bulbPoints.push(new THREE.Vector2(0.65, -1.4));
        bulbPoints.push(new THREE.Vector2(0.55, -0.6));
        bulbPoints.push(new THREE.Vector2(1.1, 0.2));
        bulbPoints.push(new THREE.Vector2(1.5, 1.0));
        bulbPoints.push(new THREE.Vector2(1.3, 1.8));
        bulbPoints.push(new THREE.Vector2(0.8, 2.3));
        bulbPoints.push(new THREE.Vector2(0, 2.5));
        const bulbGeo = new THREE.LatheGeometry(bulbPoints, 32);

        // B. 全息透光玻璃外殼 + 數碼 Wireframe
        const bulbShell = new THREE.Mesh(bulbGeo, new THREE.MeshPhysicalMaterial({{
            color: 0x00e5ff,
            emissive: 0x002244,
            transmission: 0.92,
            roughness: 0.05,
            transparent: true,
            opacity: 0.45,
            ior: 1.5,
            side: THREE.DoubleSide
        }}));
        bulbGrp.add(bulbShell);

        const bulbWire = new THREE.Mesh(bulbGeo, new THREE.MeshBasicMaterial({{
            color: 0x00f5ff,
            wireframe: true,
            transparent: true,
            opacity: 0.16,
            blending: THREE.AdditiveBlending
        }}));
        bulbGrp.add(bulbWire);

        // C. 內部量子纖細雙拱鎢絲 (縮細纖巧，高階發光)
        const filCurve1 = new THREE.CatmullRomCurve3([
            new THREE.Vector3(-0.16, -0.6, 0),
            new THREE.Vector3(-0.16, 0.5, 0),
            new THREE.Vector3(-0.09, 1.1, 0.08),
            new THREE.Vector3(0, 1.25, 0),
            new THREE.Vector3(0.09, 1.1, -0.08),
            new THREE.Vector3(0.16, 0.5, 0),
            new THREE.Vector3(0.16, -0.6, 0)
        ]);
        const filTube = new THREE.Mesh(new THREE.TubeGeometry(filCurve1, 32, 0.015, 8, false), new THREE.MeshBasicMaterial({{
            color: 0xffd700,
            blending: THREE.AdditiveBlending
        }}));
        bulbGrp.add(filTube);

        // 鎢絲內核細拱 (第二層微型結構)
        const filCurve2 = new THREE.CatmullRomCurve3([
            new THREE.Vector3(-0.09, -0.6, 0),
            new THREE.Vector3(-0.09, 0.35, 0),
            new THREE.Vector3(0, 0.8, 0.06),
            new THREE.Vector3(0.09, 0.35, 0),
            new THREE.Vector3(0.09, -0.6, 0)
        ]);
        const filTube2 = new THREE.Mesh(new THREE.TubeGeometry(filCurve2, 24, 0.012, 6, false), new THREE.MeshBasicMaterial({{
            color: 0xff9900,
            blending: THREE.AdditiveBlending
        }}));
        bulbGrp.add(filTube2);

        // 頂部微型發光晶核 (取代粗糙大黃球)
        const filNode = new THREE.Mesh(new THREE.OctahedronGeometry(0.1, 0), new THREE.MeshBasicMaterial({{
            color: 0xffffff,
            blending: THREE.AdditiveBlending
        }}));
        filNode.position.set(0, 1.25, 0);
        bulbGrp.add(filNode);
        filNode.add(new THREE.PointLight(0xffbe00, 2.5, 12));

        // 燈泡內部電子微粒子流
        const ionCount = 35;
        const ionGeo = new THREE.BufferGeometry();
        const ionPos = new Float32Array(ionCount * 3);
        for(let i=0; i<ionCount; i++) {{
            ionPos[i*3] = (Math.random()-0.5) * 1.3;
            ionPos[i*3+1] = -0.2 + Math.random() * 1.7;
            ionPos[i*3+2] = (Math.random()-0.5) * 1.3;
        }}
        ionGeo.setAttribute('position', new THREE.BufferAttribute(ionPos, 3));
        const ionSystem = new THREE.Points(ionGeo, new THREE.PointsMaterial({{
            size: 0.04,
            color: 0xffe680,
            transparent: true,
            opacity: 0.8,
            blending: THREE.AdditiveBlending
        }}));
        bulbGrp.add(ionSystem);

        // D. 金屬螺口燈座與發光層圈
        const bulbSock = new THREE.Mesh(new THREE.CylinderGeometry(0.6, 0.45, 0.9, 24), new THREE.MeshStandardMaterial({{
            color: 0x0b1d33,
            metalness: 0.8,
            roughness: 0.2
        }}));
        bulbSock.position.y = -2.1;
        bulbGrp.add(bulbSock);

        for (let i = 0; i < 3; i++) {{
            const r = new THREE.Mesh(new THREE.TorusGeometry(0.62 - i * 0.05, 0.035, 8, 32), new THREE.MeshBasicMaterial({{
                color: 0x00e5ff,
                transparent: true,
                opacity: 0.85,
                blending: THREE.AdditiveBlending
            }}));
            r.position.y = -1.8 - i * 0.3;
            r.rotation.x = 1.57;
            bulbGrp.add(r);
        }}

        // E. 浮動電子數據環 (Cyber Scanner Orbit)
        const bOrbit = new THREE.Mesh(new THREE.TorusGeometry(2.2, 0.025, 16, 64), new THREE.MeshBasicMaterial({{
            color: 0xfa5cff,
            transparent: true,
            opacity: 0.75,
            blending: THREE.AdditiveBlending
        }}));
        bOrbit.rotation.x = 1.1;
        bOrbit.rotation.y = 0.3;
        bulbGrp.add(bOrbit);

        // =====================================
        // 🌟 4. 左側水晶星 (原封不動)
        // =====================================
        function cStar() {{
            const g = new THREE.IcosahedronGeometry(1.2, 4); const p = g.attributes.position; const v = new THREE.Vector3(); const phi = (1+Math.sqrt(5))/2;
            const dirs = [[0,1,phi],[0,-1,phi],[0,1,-phi],[0,-1,-phi],[1,phi,0],[-1,phi,0],[1,-phi,0],[-1,-phi,0],[phi,0,1],[-phi,0,1],[phi,0,-1],[-phi,0,-1]].map(d=>new THREE.Vector3(...d).normalize());
            for(let i=0;i<p.count;i++){{
                v.fromBufferAttribute(p,i); const u = v.clone().normalize(); let m = -1;
                for(let d of dirs){{ const dot=u.dot(d); if(dot>m) m=dot; }}
                let s=0; if(m>0.42){{ let t=(m-0.42)/0.58; s=(t*t*(3-2*t))*1.5; }}
                v.copy(u).multiplyScalar((1.0+s)*1.35); p.setXYZ(i,v.x,v.y,v.z);
            }}
            g.computeVertexNormals(); return g;
        }}
        const gStar = new THREE.Mesh(cStar(), new THREE.MeshPhysicalMaterial({{color:0x00d9ff, emissive:0x004766, emissiveIntensity:0.85, transmission:0.65, roughness:0.08, metalness:0.12, thickness:3.0, ior:1.54, transparent:true, opacity:0.92}}));
        gStar.position.set(-13.0, 1.0, -3.5); scene.add(gStar);

        // =====================================
        // 🏛️ 5. 右側長虹玻璃 (原封不動)
        // =====================================
        const fWall = new THREE.Group(); fWall.position.set(8.5, 0.4, -4.0); scene.add(fWall);
        function cBump() {{
            const c=document.createElement('canvas'); c.width=128; c.height=16; const ctx=c.getContext('2d');
            for(let x=0;x<128;x++){{ const v=Math.pow(Math.sin((x/128)*Math.PI*12),2.0); const cv=Math.floor(v*255); ctx.fillStyle=`rgb(${{cv}},${{cv}},${{cv}})`; ctx.fillRect(x,0,1,16); }}
            const t=new THREE.CanvasTexture(c); t.wrapS=t.wrapT=THREE.RepeatWrapping; t.repeat.set(3,1); return t;
        }}
        const bump = cBump();
        function cAlpha(ft, fb) {{
            const c=document.createElement('canvas'); c.width=4; c.height=512; const ctx=c.getContext('2d');
            const g=ctx.createLinearGradient(0,0,0,512); g.addColorStop(0,'#000'); g.addColorStop(ft*0.4,'#444'); g.addColorStop(ft,'#fff'); g.addColorStop(1-fb,'#fff'); g.addColorStop(1-fb*0.4,'#444'); g.addColorStop(1,'#000');
            ctx.fillStyle=g; ctx.fillRect(0,0,4,512); const t=new THREE.CanvasTexture(c); t.needsUpdate=true; return t;
        }}
        const slats = [
            {{h:10.5, y:-0.3, z:-1.0, r:0.35, a:false, ft:0.35, fb:0.35}}, {{h:6.8, y:-1.6, z:-0.6, r:0.38, a:false, ft:0.4, fb:0.4}},
            {{h:11.5, y:0.0, z:0.2, r:0.42, a:false, ft:0.3, fb:0.3}}, {{h:13.8, y:0.4, z:0.8, r:0.5, a:true, ft:0.28, fb:0.28}},
            {{h:7.5, y:1.8, z:-0.8, r:0.36, a:false, ft:0.4, fb:0.4}}, {{h:10.8, y:-0.4, z:-0.2, r:0.39, a:false, ft:0.32, fb:0.32}},
            {{h:6.2, y:-2.2, z:-1.2, r:0.34, a:false, ft:0.45, fb:0.45}}, {{h:12.2, y:0.2, z:0.0, r:0.4, a:false, ft:0.3, fb:0.3}},
            {{h:8.5, y:1.2, z:-1.5, r:0.3, a:false, ft:0.35, fb:0.35}}
        ];
        slats.forEach((s, idx) => {{
            const m = new THREE.Mesh(new THREE.CylinderGeometry(s.r,s.r,s.h,32,1,true), new THREE.MeshPhysicalMaterial({{color:s.a?0xffa200:0x00f5bb, emissive:s.a?0xcc4400:0x003322, emissiveIntensity:s.a?1.6:0.5, transmission:0.88, roughness:0.12, metalness:0.25, ior:1.52, transparent:true, opacity: 1.0, alphaMap:cAlpha(s.ft,s.fb), bumpMap:bump, bumpScale:0.06, depthWrite:false, side:THREE.DoubleSide}}));
            m.position.set(idx*0.85, s.y, s.z); fWall.add(m);
            const pts=[]; const lCols=[]; const bc=new THREE.Color(s.a?0xffea77:0x67e8f9);
            for(let j=0;j<=30;j++){{ const t=j/30; pts.push(new THREE.Vector3(0,(s.h/2)-(s.h*t),s.r*1.02)); let al=1; if(t<s.ft) al=Math.pow(t/s.ft,2); else if(t>(1-s.fb)) al=Math.pow((1-t)/s.fb,2); const fi=al*(s.a?0.95:0.6); lCols.push(bc.r*fi,bc.g*fi,bc.b*fi); }}
            const hg=new THREE.BufferGeometry().setFromPoints(pts); hg.setAttribute('color',new THREE.Float32BufferAttribute(lCols,3));
            m.add(new THREE.Line(hg, new THREE.LineBasicMaterial({{vertexColors:true, transparent:true, blending:THREE.AdditiveBlending}})));
        }});

        // =====================================
        // 🧠 6. 爺爺純代碼手繪：神經雲全息大腦 (原封不動)
        // =====================================
        const bSys = new THREE.Group(); bSys.position.set(17.5, 1.2, -3.5); bSys.rotation.x=0.6; bSys.scale.set(0.75,0.75,0.75); scene.add(bSys);
        
        const brainParticleCount = 15000;
        const bGeo = new THREE.BufferGeometry();
        const bPos = new Float32Array(brainParticleCount * 3);
        const bCol = new Float32Array(brainParticleCount * 3);
        const c1 = new THREE.Color(0x00d9ff); 
        const c2 = new THREE.Color(0xaa00ff); 

        let pIdx = 0;
        while(pIdx < brainParticleCount) {{
            let x = (Math.random() - 0.5) * 4.4; let y = (Math.random() - 0.5) * 3.6; let z = (Math.random() - 0.5) * 4.0;
            let lobeX = Math.abs(x) - 0.6; let dist = (lobeX*lobeX)/1.8 + (y*y)/1.4 + (z*z)/1.6;
            if (dist < 1.0) {{
                let noise = Math.sin(x*4)*Math.cos(y*5)*Math.sin(z*4) * 0.15;
                if (dist + noise > 0.8) {{ 
                    bPos[pIdx*3] = x; bPos[pIdx*3+1] = y + 1.0; bPos[pIdx*3+2] = z;
                    let mixRatio = Math.random();
                    bCol[pIdx*3] = c1.r * mixRatio + c2.r * (1-mixRatio); bCol[pIdx*3+1] = c1.g * mixRatio + c2.g * (1-mixRatio); bCol[pIdx*3+2] = c1.b * mixRatio + c2.b * (1-mixRatio);
                    pIdx++;
                }}
            }}
        }}
        bGeo.setAttribute('position', new THREE.BufferAttribute(bPos, 3)); bGeo.setAttribute('color', new THREE.BufferAttribute(bCol, 3));
        const bMat = new THREE.PointsMaterial({{size: 0.05, vertexColors: true, transparent: true, opacity: 0.75, blending: THREE.AdditiveBlending}});
        const brainCloud = new THREE.Points(bGeo, bMat); bSys.add(brainCloud);

        const bSh = new THREE.Mesh(new THREE.SphereGeometry(2.8,36,36), new THREE.MeshPhysicalMaterial({{color:0x0099ff, emissive:0x330066, emissiveIntensity:0.65, transmission:0.92, transparent:true, opacity:0.22, roughness:0.08, ior:1.15, side:THREE.DoubleSide, depthWrite:false}}));
        bSh.position.y=0.5; bSys.add(bSh);
        
        const o1Grp = new THREE.Group(); o1Grp.position.y=0.5; o1Grp.rotation.x=1.03; o1Grp.rotation.y=0.35; bSys.add(o1Grp);
        o1Grp.add(new THREE.Mesh(new THREE.TorusGeometry(3.7,0.035,16,120), new THREE.MeshBasicMaterial({{color:0xfa5cff, transparent:true, opacity:0.9, blending:THREE.AdditiveBlending}})));
        
        const o2Grp = new THREE.Group(); o2Grp.position.y=0.5; o2Grp.rotation.x=-0.78; o2Grp.rotation.y=-0.28; bSys.add(o2Grp);
        o2Grp.add(new THREE.Mesh(new THREE.TorusGeometry(3.9,0.03,16,120), new THREE.MeshBasicMaterial({{color:0x00f0ff, transparent:true, opacity:0.9, blending:THREE.AdditiveBlending}})));

        const base = new THREE.Group(); base.position.y=-1.8; base.rotation.x=1.57; bSys.add(base);
        base.add(new THREE.Mesh(new THREE.RingGeometry(1.4,1.44,64), new THREE.MeshBasicMaterial({{color:0xfa5cff, side:THREE.DoubleSide, transparent:true, opacity:0.85, blending:THREE.AdditiveBlending}})));
        base.add(new THREE.Mesh(new THREE.RingGeometry(2.3,2.34,64), new THREE.MeshBasicMaterial({{color:0x00f0ff, side:THREE.DoubleSide, transparent:true, opacity:0.75, blending:THREE.AdditiveBlending}})));
        base.add(new THREE.Mesh(new THREE.RingGeometry(3.2,3.24,64), new THREE.MeshBasicMaterial({{color:0x0099ff, side:THREE.DoubleSide, transparent:true, opacity:0.45, blending:THREE.AdditiveBlending}})));
        
        const rGeo = new THREE.BufferGeometry(); const rPts = [];
        for(let i=0;i<32;i++){{ const a=(i/32)*Math.PI*2; rPts.push(0,0,0,Math.cos(a)*3.2,Math.sin(a)*3.2,0); }}
        rGeo.setAttribute('position', new THREE.Float32BufferAttribute(rPts,3));
        base.add(new THREE.LineSegments(rGeo, new THREE.LineBasicMaterial({{color:0x00e5ff, transparent:true, opacity:0.4, blending:THREE.AdditiveBlending}})));
        
        const beam = new THREE.Mesh(new THREE.CylinderGeometry(0.3,2.0,1.8,32,1,true), new THREE.MeshBasicMaterial({{color:0x00f0ff, transparent:true, opacity:0.35, side:THREE.DoubleSide, blending:THREE.AdditiveBlending, depthWrite:false}}));
        beam.position.set(0,-0.9,0); bSys.add(beam);

        // =====================================
        // 🌐 7. 貫穿全景的量子數據流粒子 (原封不動)
        // =====================================
        const fCount=850; const fbGeo=new THREE.BufferGeometry(); const fbPos=new Float32Array(fCount*3); const fbCols=new Float32Array(fCount*3);
        for(let i=0;i<fCount;i++){{
            const lane=i%6; const x=(Math.random()-0.5)*46; const y=-1.2+(lane-2.5)*0.65+Math.sin(x*0.22+lane)*1.1+(Math.random()-0.5)*0.35; const z=-2.5+(Math.random()-0.5)*3.5;
            fbPos[i*3]=x; fbPos[i*3+1]=y; fbPos[i*3+2]=z; const c=(lane%2===0)?new THREE.Color(0x00d9ff):new THREE.Color(0xf59e0b); fbCols[i*3]=c.r; fbCols[i*3+1]=c.g; fbCols[i*3+2]=c.b;
        }}
        fbGeo.setAttribute('position', new THREE.BufferAttribute(fbPos,3)); fbGeo.setAttribute('color', new THREE.BufferAttribute(fbCols,3));
        const fibSys = new THREE.Points(fbGeo, new THREE.PointsMaterial({{size:0.3, vertexColors:true, transparent:true, opacity:0.85, blending:THREE.AdditiveBlending}}));
        scene.add(fibSys);

        // =====================================
        // 🎬 8. 動態全息渲染循環
        // =====================================
        const clk = new THREE.Clock();
        function anim() {{
            requestAnimationFrame(anim); const t=clk.getElapsedTime();
            
            cry.rotation.y=t*0.35; cry.rotation.z=t*0.12; 
            innerCry.rotation.x=-t*0.2; innerCry.rotation.y=-t*0.4; 
            
            const s=1+Math.sin(t*2.2)*0.05; iCore.scale.set(s,s,s);
            r1.rotation.z=t*0.2; r2.rotation.z=-t*0.15; r3.rotation.z=t*0.1;
            sat.position.x=Math.cos(t*0.8)*6.4; sat.position.y=Math.sin(t*0.8)*6.4;
            gStar.rotation.x=Math.sin(t*0.4)*0.2; gStar.rotation.y=t*0.25; gStar.rotation.z=Math.cos(t*0.3)*0.15; gStar.position.y=1+Math.sin(t*0.5)*0.2;
            fWall.position.y=0.4+Math.sin(t*0.4)*0.22;
            
            // 💡 電燈懸浮律動與外環旋轉 (前傾俯視角度保持立體)
            bulbGrp.rotation.y = t * 0.25;
            bulbGrp.position.y = 1.2 + Math.sin(t * 1.4) * 0.12;
            bOrbit.rotation.z = -t * 0.5;

            brainCloud.rotation.y = t * 0.15;
            brainCloud.position.y = Math.sin(t*1.6)*0.15;
            
            o1Grp.rotation.z-=0.015; o2Grp.rotation.z+=0.012; base.rotation.z+=0.005;
            
            const p=fibSys.geometry.attributes.position.array; for(let i=0;i<fCount;i++){{ p[i*3]+=0.09; if(p[i*3]>23) p[i*3]=-23; }}
            fibSys.geometry.attributes.position.needsUpdate=true; renderer.render(scene, camera);
        }}
        anim();
        window.addEventListener('resize', () => {{ camera.aspect=window.innerWidth/560; camera.updateProjectionMatrix(); renderer.setSize(window.innerWidth, 560); }});
    </script></body></html>
    """,
    height=560,
)