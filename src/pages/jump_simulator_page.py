"""
3D Jump Simulator Page
محاكي القفزات ثلاثي الأبعاد - Three.js مدمج
"""

import streamlit as st
import streamlit.components.v1 as components

SIMULATOR_HTML = r"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D Jump Simulator</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: #0d1117; color: #c9d1d9; overflow: hidden; height: 100vh; }
        #canvas-container { position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: 1; }
        .ui-overlay { position: fixed; z-index: 10; pointer-events: none; }
        .ui-overlay > * { pointer-events: auto; }
        .header { top: 0; left: 0; right: 0; padding: 12px 20px; background: linear-gradient(180deg, rgba(13,17,23,0.95) 0%, transparent 100%); display: flex; justify-content: space-between; align-items: center; }
        .logo { display: flex; align-items: center; gap: 10px; }
        .logo-icon { width: 38px; height: 38px; background: linear-gradient(135deg, #1a73e8, #00c853); border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px; }
        .logo-text h1 { font-size: 16px; color: #fff; }
        .logo-text span { font-size: 11px; color: #8b949e; }
        .btn-group { display: flex; gap: 6px; }
        .btn { padding: 6px 12px; border-radius: 6px; border: 1px solid #30363d; background: #0d1117; color: #c9d1d9; cursor: pointer; font-size: 12px; transition: all 0.3s; }
        .btn:hover { border-color: #1a73e8; background: rgba(26,115,232,0.1); }
        .btn.active { background: #1a73e8; border-color: #1a73e8; color: #fff; }
        .btn-danger { background: rgba(255,23,68,0.1); border-color: #ff1744; color: #ff1744; }
        .btn-success { background: rgba(0,200,83,0.1); border-color: #00c853; color: #00c853; }
        .control-panel { right: 16px; top: 60px; width: 280px; background: rgba(22,27,34,0.97); border: 1px solid #30363d; border-radius: 14px; padding: 18px; max-height: calc(100vh - 80px); overflow-y: auto; }
        .panel-title { font-size: 14px; color: #fff; margin-bottom: 14px; padding-bottom: 10px; border-bottom: 1px solid #30363d; display: flex; align-items: center; gap: 6px; }
        .control-group { margin-bottom: 16px; }
        .jump-type-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 6px; }
        .jump-type-btn { padding: 8px; border-radius: 6px; border: 1px solid #30363d; background: #0d1117; color: #c9d1d9; cursor: pointer; font-size: 11px; text-align: center; transition: all 0.3s; }
        .jump-type-btn:hover { border-color: #1a73e8; }
        .jump-type-btn.active { background: #1a73e8; border-color: #1a73e8; color: #fff; }
        .jump-type-btn .bv { font-size: 9px; color: #8b949e; display: block; margin-top: 2px; }
        .jump-type-btn.active .bv { color: rgba(255,255,255,0.7); }
        .slider-container { margin-bottom: 12px; }
        .slider-label { display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 6px; }
        .slider-label span:first-child { color: #8b949e; }
        .slider-label span:last-child { color: #fff; font-weight: 600; }
        input[type="range"] { width: 100%; height: 5px; border-radius: 3px; background: #30363d; outline: none; -webkit-appearance: none; }
        input[type="range"]::-webkit-slider-thumb { -webkit-appearance: none; width: 16px; height: 16px; border-radius: 50%; background: #1a73e8; cursor: pointer; border: 2px solid #fff; }
        .metrics-panel { left: 16px; bottom: 70px; width: 240px; background: rgba(22,27,34,0.97); border: 1px solid #30363d; border-radius: 14px; padding: 16px; }
        .metric-item { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #30363d; }
        .metric-item:last-child { border-bottom: none; }
        .metric-name { font-size: 12px; color: #8b949e; }
        .metric-value { font-size: 14px; font-weight: 700; color: #fff; }
        .metric-value.good { color: #00c853; }
        .metric-value.warning { color: #ffd600; }
        .metric-value.bad { color: #ff1744; }
        .trajectory-panel { left: 16px; top: 60px; width: 190px; background: rgba(22,27,34,0.97); border: 1px solid #30363d; border-radius: 14px; padding: 14px; }
        .trajectory-canvas { width: 100%; height: 130px; background: #0d1117; border-radius: 6px; margin-top: 8px; }
        .playback-controls { bottom: 16px; left: 50%; transform: translateX(-50%); display: flex; gap: 10px; align-items: center; background: rgba(22,27,34,0.97); border: 1px solid #30363d; border-radius: 50px; padding: 10px 20px; }
        .play-btn { width: 44px; height: 44px; border-radius: 50%; background: #1a73e8; border: none; color: #fff; font-size: 18px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.3s; }
        .play-btn:hover { transform: scale(1.1); box-shadow: 0 0 16px rgba(26,115,232,0.5); }
        .time-display { font-size: 13px; color: #fff; font-family: monospace; min-width: 70px; text-align: center; }
        .toggle-row { display: flex; justify-content: space-between; align-items: center; padding: 6px 0; }
        .toggle-switch { position: relative; width: 40px; height: 22px; }
        .toggle-switch input { opacity: 0; width: 0; height: 0; }
        .toggle-slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background: #30363d; border-radius: 22px; transition: 0.3s; }
        .toggle-slider:before { position: absolute; content: ""; height: 16px; width: 16px; left: 3px; bottom: 3px; background: #fff; border-radius: 50%; transition: 0.3s; }
        input:checked + .toggle-slider { background: #1a73e8; }
        input:checked + .toggle-slider:before { transform: translateX(18px); }
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
    </style>
</head>
<body>
    <div id="canvas-container"></div>
    <div class="header ui-overlay">
        <div class="logo">
            <div class="logo-icon">⛸️</div>
            <div class="logo-text">
                <h1>محاكي القفزات ثلاثي الأبعاد</h1>
                <span>YASOOO — ISU 2024 Base Values</span>
            </div>
        </div>
        <div class="btn-group">
            <button class="btn" onclick="resetCamera()">🎥 الكاميرا</button>
            <button class="btn" onclick="toggleGrid()">⊞ شبكة</button>
            <button class="btn" onclick="toggleSkeleton()">🦴 هيكل</button>
        </div>
    </div>

    <div class="trajectory-panel ui-overlay">
        <div class="panel-title">📈 مسار القفزة</div>
        <canvas id="trajectoryCanvas" class="trajectory-canvas" width="190" height="130"></canvas>
        <div style="margin-top:8px;font-size:11px;color:#8b949e">
            <div style="display:flex;justify-content:space-between"><span>الارتفاع:</span><span id="trajHeight" style="color:#fff">0.00m</span></div>
            <div style="display:flex;justify-content:space-between;margin-top:3px"><span>المسافة:</span><span id="trajDistance" style="color:#fff">0.00m</span></div>
        </div>
    </div>

    <div class="control-panel ui-overlay">
        <div class="panel-title">🎯 نوع القفزة</div>
        <div class="jump-type-grid" id="jumpTypeGrid">
            <div class="jump-type-btn active" data-jump="axel" onclick="selectJump('axel')">Axel<span class="bv">BV: 1.10–12.50</span></div>
            <div class="jump-type-btn" data-jump="salchow" onclick="selectJump('salchow')">Salchow<span class="bv">BV: 0.40–9.70</span></div>
            <div class="jump-type-btn" data-jump="loop" onclick="selectJump('loop')">Loop<span class="bv">BV: 0.50–10.50</span></div>
            <div class="jump-type-btn" data-jump="toe_loop" onclick="selectJump('toe_loop')">Toe Loop<span class="bv">BV: 0.40–9.50</span></div>
            <div class="jump-type-btn" data-jump="flip" onclick="selectJump('flip')">Flip<span class="bv">BV: 0.50–11.00</span></div>
            <div class="jump-type-btn" data-jump="lutz" onclick="selectJump('lutz')">Lutz<span class="bv">BV: 0.60–11.50</span></div>
        </div>

        <div class="panel-title" style="margin-top:18px">🔢 عدد الدورات</div>
        <div class="btn-group">
            <button class="btn" data-rot="1" onclick="selectRotation(1)">1x</button>
            <button class="btn" data-rot="2" onclick="selectRotation(2)">2x</button>
            <button class="btn active" data-rot="3" onclick="selectRotation(3)">3x</button>
            <button class="btn" data-rot="4" onclick="selectRotation(4)">4x</button>
        </div>

        <div class="panel-title" style="margin-top:18px">⚙️ المعلمات</div>
        <div class="slider-container">
            <div class="slider-label"><span>قوة الإقلاع</span><span id="takeoffPowerVal">85%</span></div>
            <input type="range" id="takeoffPower" min="50" max="100" value="85" oninput="updateParam('takeoffPower',this.value)">
        </div>
        <div class="slider-container">
            <div class="slider-label"><span>سرعة الدوران</span><span id="rotationSpeedVal">3.5</span></div>
            <input type="range" id="rotationSpeed" min="1" max="5" step="0.1" value="3.5" oninput="updateParam('rotationSpeed',this.value)">
        </div>
        <div class="slider-container">
            <div class="slider-label"><span>زاوية الإقلاع</span><span id="takeoffAngleVal">45°</span></div>
            <input type="range" id="takeoffAngle" min="30" max="60" value="45" oninput="updateParam('takeoffAngle',this.value)">
        </div>

        <div class="panel-title" style="margin-top:18px">👁️ عرض</div>
        <div class="toggle-row"><span style="font-size:12px">الهيكل العظمي</span><label class="toggle-switch"><input type="checkbox" checked onchange="toggleSkeleton()"><span class="toggle-slider"></span></label></div>
        <div class="toggle-row"><span style="font-size:12px">مسار الحركة</span><label class="toggle-switch"><input type="checkbox" checked onchange="toggleTrajectory()"><span class="toggle-slider"></span></label></div>
        <div class="toggle-row"><span style="font-size:12px">بطء (Slow-Mo)</span><label class="toggle-switch"><input type="checkbox" onchange="toggleSlowMo()"><span class="toggle-slider"></span></label></div>

        <div class="panel-title" style="margin-top:18px">🔥 سيناريوهات</div>
        <div class="btn-group" style="flex-direction:column;gap:6px">
            <button class="btn btn-success" onclick="simulatePerfectJump()">✅ قفزة مثالية</button>
            <button class="btn" onclick="simulateUnderRotation()">⚠️ نقص دوران</button>
            <button class="btn btn-danger" onclick="simulateFall()">❌ سقوط</button>
            <button class="btn" onclick="simulateEdgeError()">📐 خطأ حافة</button>
        </div>
    </div>

    <div class="metrics-panel ui-overlay">
        <div class="panel-title">📊 مقاييس القفزة</div>
        <div class="metric-item"><span class="metric-name">الارتفاع</span><span class="metric-value" id="metricHeight">0.52m</span></div>
        <div class="metric-item"><span class="metric-name">زمن الهواء</span><span class="metric-value" id="metricAirTime">0.68s</span></div>
        <div class="metric-item"><span class="metric-name">الدورات</span><span class="metric-value" id="metricRotations">3.0</span></div>
        <div class="metric-item"><span class="metric-name">سرعة الدوران</span><span class="metric-value" id="metricRotSpeed">3.5 rps</span></div>
        <div class="metric-item"><span class="metric-name">القيمة الأساسية</span><span class="metric-value good" id="metricBV">8.00</span></div>
        <div class="metric-item"><span class="metric-name">GOE</span><span class="metric-value good" id="metricGOE">+3</span></div>
        <div class="metric-item"><span class="metric-name">النتيجة</span><span class="metric-value good" id="metricFinal">10.40</span></div>
        <div class="metric-item"><span class="metric-name">الحافة</span><span class="metric-value" id="metricEdge">Outside ✅</span></div>
    </div>

    <div class="playback-controls ui-overlay">
        <button class="btn" onclick="resetSimulation()">⏮</button>
        <button class="play-btn" id="playBtn" onclick="togglePlay()">▶</button>
        <button class="btn" onclick="stepForward()">⏭</button>
        <div class="time-display" id="timeDisplay">0.00s / 1.20s</div>
        <input type="range" id="timeline" min="0" max="100" value="0" style="width:160px" oninput="seekTimeline(this.value)">
    </div>

    <script>
        let scene, camera, renderer, controls;
        let skaterGroup, trajectoryPoints = [];
        let iceRink, gridHelper;
        let isPlaying = false, currentTime = 0, slowMo = false;
        let jumpData = { type:'axel', rotation:3, takeoffPower:85, rotationSpeed:3.5, takeoffAngle:45, hasFall:false, underRotation:0, edgeError:false };
        const BASE_VALUES = {
            axel:    {1:1.10, 2:2.30, 3:8.00, 4:12.50},
            salchow: {1:0.40, 2:1.30, 3:4.30, 4:9.70},
            loop:    {1:0.50, 2:1.70, 3:5.10, 4:10.50},
            toe_loop:{1:0.40, 2:1.30, 3:4.20, 4:9.50},
            flip:    {1:0.50, 2:1.80, 3:5.30, 4:11.00},
            lutz:    {1:0.60, 2:2.10, 3:5.90, 4:11.50}
        };

        function init() {
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0x0d1117);
            scene.fog = new THREE.Fog(0x0d1117, 12, 50);
            camera = new THREE.PerspectiveCamera(60, window.innerWidth/window.innerHeight, 0.1, 1000);
            camera.position.set(5, 3, 5);
            renderer = new THREE.WebGLRenderer({antialias:true});
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            document.getElementById('canvas-container').appendChild(renderer.domElement);
            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true; controls.dampingFactor = 0.05;
            controls.maxPolarAngle = Math.PI/2 - 0.05; controls.minDistance = 2; controls.maxDistance = 20;
            const ambient = new THREE.AmbientLight(0xffffff, 0.4); scene.add(ambient);
            const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
            dirLight.position.set(5, 10, 5); dirLight.castShadow = true;
            dirLight.shadow.mapSize.width = 2048; dirLight.shadow.mapSize.height = 2048;
            scene.add(dirLight);
            const spot = new THREE.SpotLight(0x1a73e8, 0.4); spot.position.set(-5, 8, -5); spot.angle = Math.PI/6; scene.add(spot);
            createIceRink(); createSkater();
            window.addEventListener('resize', onResize);
            animate(); drawTrajectory();
        }

        function createIceRink() {
            const geo = new THREE.PlaneGeometry(30, 60);
            const mat = new THREE.MeshStandardMaterial({color:0xc9e4ff, roughness:0.1, metalness:0.3, transparent:true, opacity:0.25});
            iceRink = new THREE.Mesh(geo, mat); iceRink.rotation.x = -Math.PI/2; iceRink.receiveShadow = true; scene.add(iceRink);
            const borderGeo = new THREE.EdgesGeometry(geo);
            const borderMat = new THREE.LineBasicMaterial({color:0x1a73e8});
            const borders = new THREE.LineSegments(borderGeo, borderMat);
            borders.rotation.x = -Math.PI/2; borders.position.y = 0.01; scene.add(borders);
            gridHelper = new THREE.GridHelper(20, 20, 0x30363d, 0x1a1f27); scene.add(gridHelper);
        }

        function createSkater() {
            skaterGroup = new THREE.Group();
            const parts = [
                {n:'head',     p:[0,1.7,0],     s:[0.12,0.15,0.13], c:0xffdbac},
                {n:'torso',    p:[0,1.35,0],    s:[0.25,0.4,0.15],  c:0x1a73e8},
                {n:'lUA',      p:[-0.3,1.5,0],  s:[0.08,0.28,0.08], c:0xffdbac},
                {n:'rUA',      p:[0.3,1.5,0],   s:[0.08,0.28,0.08], c:0xffdbac},
                {n:'lLA',      p:[-0.3,1.15,0], s:[0.07,0.22,0.07], c:0xffdbac},
                {n:'rLA',      p:[0.3,1.15,0],  s:[0.07,0.22,0.07], c:0xffdbac},
                {n:'lThigh',   p:[-0.1,0.9,0],  s:[0.1,0.33,0.1],   c:0x111827},
                {n:'rThigh',   p:[0.1,0.9,0],   s:[0.1,0.33,0.1],   c:0x111827},
                {n:'lShin',    p:[-0.1,0.5,0],  s:[0.09,0.28,0.09], c:0xffffff},
                {n:'rShin',    p:[0.1,0.5,0],   s:[0.09,0.28,0.09], c:0xffffff},
                {n:'lSkate',   p:[-0.1,0.15,0.05], s:[0.1,0.05,0.25], c:0x222222},
                {n:'rSkate',   p:[0.1,0.15,0.05],  s:[0.1,0.05,0.25], c:0x222222},
            ];
            parts.forEach(p => {
                const mesh = new THREE.Mesh(
                    new THREE.BoxGeometry(...p.s),
                    new THREE.MeshStandardMaterial({color:p.c, roughness:0.5})
                );
                mesh.position.set(...p.p); mesh.castShadow = true; mesh.name = p.n; skaterGroup.add(mesh);
            });
            [[0,1.7,0],[0,1.55,0],[-0.3,1.55,0],[0.3,1.55,0],[-0.3,1.25,0],[0.3,1.25,0],[0,1.15,0],[-0.1,1.05,0],[0.1,1.05,0]].forEach(pos => {
                const j = new THREE.Mesh(new THREE.SphereGeometry(0.035,8,8), new THREE.MeshStandardMaterial({color:0x00c853}));
                j.position.set(...pos); skaterGroup.add(j);
            });
            scene.add(skaterGroup);
        }

        function physics() {
            const g = 9.81, angle = jumpData.takeoffAngle * Math.PI/180, power = jumpData.takeoffPower/100;
            const v0 = 4.5 * power, vx = v0*Math.cos(angle), vy = v0*Math.sin(angle);
            const maxHeight = vy*vy/(2*g), airTime = 2*vy/g, distance = vx*airTime;
            const rotations = jumpData.rotationSpeed * airTime;
            return {v0, vx, vy, maxHeight, airTime, distance, rotations};
        }

        function updateSkaterPosition(time) {
            const p = physics(); const t = time/p.airTime;
            if (t < 0 || t > 1) return;
            const x = p.vx * time * 0.5;
            const y = p.vy * time - 0.5 * 9.81 * time * time;
            skaterGroup.position.x = x; skaterGroup.position.y = Math.max(y, 0);
            skaterGroup.rotation.y = p.rotations * 2 * Math.PI * t;
            if (t < 0.1) setPose('takeoff'); else if (t < 0.9) setPose('air'); else setPose('landing');
            document.getElementById('timeDisplay').textContent = `${(t * p.airTime).toFixed(2)}s / ${p.airTime.toFixed(2)}s`;
            document.getElementById('timeline').value = t * 100;
        }

        const POSES = {
            takeoff: {torso:[0,1.22,0,0.3],lThigh:[-0.14,0.78,0,-0.5],rThigh:[0.06,0.78,0,0.3],lShin:[-0.14,0.4,0,0.8],rShin:[0.06,0.4,0,0.5]},
            air:     {torso:[0,1.35,0,0],  lThigh:[-0.2,1.0,0,-0.8],  rThigh:[0.2,1.0,0,0.8],  lShin:[-0.2,0.7,0,1.2],  rShin:[0.2,0.7,0,-1.2]},
            landing: {torso:[0,1.2,0,-0.2],lThigh:[-0.1,0.78,0,-0.3], rThigh:[0.14,0.78,0,0.5], lShin:[-0.1,0.4,0,0.5],  rShin:[0.14,0.4,0,0.8]}
        };
        function setPose(phase) {
            const pose = POSES[phase]; if (!pose) return;
            for (const [nm, [x,y,z,rz]] of Object.entries(pose)) {
                const part = skaterGroup.getObjectByName(nm);
                if (part) { part.position.set(x,y,z); part.rotation.z = rz; }
            }
        }

        function drawTrajectory() {
            const canvas = document.getElementById('trajectoryCanvas');
            const ctx = canvas.getContext('2d'); const p = physics();
            ctx.clearRect(0,0,canvas.width,canvas.height);
            ctx.strokeStyle='#30363d'; ctx.lineWidth=1; ctx.beginPath();
            ctx.moveTo(15,120); ctx.lineTo(175,120); ctx.moveTo(15,120); ctx.lineTo(15,10); ctx.stroke();
            ctx.strokeStyle='#1a73e8'; ctx.lineWidth=2; ctx.beginPath();
            for (let i=0; i<=50; i++) {
                const tt = (i/50)*p.airTime;
                const x = 15 + (tt/p.airTime)*145;
                const yy = 120 - (p.vy*tt - 0.5*9.81*tt*tt)/p.maxHeight*95;
                if (i===0) ctx.moveTo(x,yy); else ctx.lineTo(x,yy);
            }
            ctx.stroke();
            if (currentTime > 0) {
                const tt = currentTime, t = tt/p.airTime;
                const x = 15 + t*145;
                const yy = 120 - (p.vy*tt - 0.5*9.81*tt*tt)/p.maxHeight*95;
                ctx.fillStyle='#00c853'; ctx.beginPath(); ctx.arc(x,yy,5,0,Math.PI*2); ctx.fill();
            }
            document.getElementById('trajHeight').textContent = p.maxHeight.toFixed(2)+'m';
            document.getElementById('trajDistance').textContent = p.distance.toFixed(2)+'m';
        }

        function updateMetricsDisplay() {
            const bv = BASE_VALUES[jumpData.type]?.[jumpData.rotation] || 0;
            const goe = jumpData.hasFall ? -5 : jumpData.underRotation > 0 ? -3 : 3;
            const final = bv * (1 + goe * 0.1);
            document.getElementById('metricBV').textContent = bv.toFixed(2);
            document.getElementById('metricGOE').textContent = (goe>0?'+':'')+goe;
            document.getElementById('metricGOE').className = 'metric-value ' + (goe>=0?'good':'bad');
            document.getElementById('metricFinal').textContent = final.toFixed(2);
            document.getElementById('metricFinal').className = 'metric-value ' + (final>=bv?'good':'bad');
            const p = physics();
            document.getElementById('metricHeight').textContent = p.maxHeight.toFixed(2)+'m';
            document.getElementById('metricAirTime').textContent = p.airTime.toFixed(2)+'s';
            document.getElementById('metricRotations').textContent = p.rotations.toFixed(1);
            document.getElementById('metricRotSpeed').textContent = jumpData.rotationSpeed.toFixed(1)+' rps';
            document.getElementById('metricEdge').textContent = jumpData.edgeError ? 'Inside ❌ (Flutz!)' : 'Outside ✅';
            document.getElementById('metricEdge').className = 'metric-value ' + (jumpData.edgeError?'bad':'');
        }

        function selectJump(type) {
            jumpData.type = type;
            document.querySelectorAll('.jump-type-btn').forEach(b=>b.classList.remove('active'));
            document.querySelector(`[data-jump="${type}"]`).classList.add('active');
            jumpData.hasFall=false; jumpData.underRotation=0; jumpData.edgeError=false;
            updateMetricsDisplay(); resetSimulation();
        }
        function selectRotation(rot) {
            jumpData.rotation = rot;
            document.querySelectorAll('[data-rot]').forEach(b=>b.classList.remove('active'));
            document.querySelector(`[data-rot="${rot}"]`).classList.add('active');
            updateMetricsDisplay(); resetSimulation();
        }
        function updateParam(param, value) {
            jumpData[param] = parseFloat(value);
            document.getElementById(param+'Val').textContent = param==='takeoffAngle' ? value+'°' : param==='takeoffPower' ? value+'%' : value;
            updateMetricsDisplay(); drawTrajectory();
        }

        function togglePlay() {
            isPlaying = !isPlaying;
            document.getElementById('playBtn').textContent = isPlaying ? '⏸' : '▶';
            if (isPlaying) playLoop();
        }
        function playLoop() {
            if (!isPlaying) return;
            const p = physics(), dt = slowMo ? 0.004 : 0.016;
            currentTime += dt;
            if (currentTime >= p.airTime) { currentTime = p.airTime; isPlaying=false; document.getElementById('playBtn').textContent='▶'; }
            updateSkaterPosition(currentTime); drawTrajectory();
            if (isPlaying) requestAnimationFrame(playLoop);
        }
        function resetSimulation() {
            isPlaying=false; currentTime=0; document.getElementById('playBtn').textContent='▶';
            trajectoryPoints.forEach(p=>scene.remove(p)); trajectoryPoints=[];
            skaterGroup.position.set(0,0,0); skaterGroup.rotation.set(0,0,0);
            setPose('takeoff'); updateMetricsDisplay(); drawTrajectory();
            document.getElementById('timeline').value=0;
            document.getElementById('timeDisplay').textContent='0.00s / '+physics().airTime.toFixed(2)+'s';
        }
        function stepForward() { const p=physics(); currentTime=Math.min(currentTime+0.08,p.airTime); updateSkaterPosition(currentTime); drawTrajectory(); }
        function seekTimeline(v) { currentTime=(v/100)*physics().airTime; updateSkaterPosition(currentTime); drawTrajectory(); }
        function simulatePerfectJump() { jumpData.takeoffPower=95;jumpData.rotationSpeed=4.0;jumpData.takeoffAngle=48;jumpData.hasFall=false;jumpData.underRotation=0;jumpData.edgeError=false; document.getElementById('takeoffPower').value=95;document.getElementById('rotationSpeed').value=4.0;document.getElementById('takeoffAngle').value=48; updateParam('takeoffPower',95);updateParam('rotationSpeed',4.0);updateParam('takeoffAngle',48); resetSimulation(); setTimeout(()=>togglePlay(),400); }
        function simulateUnderRotation() { jumpData.rotationSpeed=2.4;jumpData.underRotation=120; document.getElementById('rotationSpeed').value=2.4;updateParam('rotationSpeed',2.4); resetSimulation(); setTimeout(()=>togglePlay(),400); }
        function simulateFall() { jumpData.hasFall=true;jumpData.takeoffPower=58; document.getElementById('takeoffPower').value=58;updateParam('takeoffPower',58); updateMetricsDisplay(); resetSimulation(); setTimeout(()=>togglePlay(),400); }
        function simulateEdgeError() { jumpData.edgeError=true; updateMetricsDisplay(); resetSimulation(); }
        function resetCamera() { camera.position.set(5,3,5); camera.lookAt(0,1,0); controls.reset(); }
        function toggleGrid() { gridHelper.visible = !gridHelper.visible; }
        function toggleSkeleton() { skaterGroup.children.forEach(c=>{ if(c.name) c.visible=!c.visible; }); }
        function toggleTrajectory() { trajectoryPoints.forEach(p=>{ p.visible=!p.visible; }); }
        function toggleSlowMo() { slowMo=!slowMo; }
        function animate() { requestAnimationFrame(animate); controls.update(); renderer.render(scene,camera); }
        function onResize() { camera.aspect=window.innerWidth/window.innerHeight; camera.updateProjectionMatrix(); renderer.setSize(window.innerWidth,window.innerHeight); }

        init();
        updateMetricsDisplay();
    </script>
</body>
</html>"""


def show_jump_simulator():
    ar = st.session_state.get('language', 'ar') == 'ar'

    st.markdown(
        f"<h2 style='text-align:center;color:#1a73e8'>{'🎿 محاكي القفزات ثلاثي الأبعاد' if ar else '🎿 3D Jump Simulator'}</h2>",
        unsafe_allow_html=True
    )

    if ar:
        st.markdown("""
        **كيفية الاستخدام:**
        - اختر نوع القفزة من اللوحة اليمنى
        - حدد عدد الدورات (Single/Double/Triple/Quad)
        - اضبط قوة الإقلاع، سرعة الدوران، زاوية الإقلاع
        - اضغط ▶ لتشغيل المحاكاة أو جرب السيناريوهات الجاهزة
        - استخدم الماوس للتحكم في زاوية الكاميرا ثلاثية الأبعاد
        """)
    else:
        st.markdown("""
        **How to use:**
        - Select jump type from the right panel
        - Choose rotation count (Single/Double/Triple/Quad)
        - Adjust takeoff power, rotation speed, takeoff angle
        - Press ▶ to play simulation or try preset scenarios
        - Use mouse to rotate the 3D camera view
        """)

    components.html(SIMULATOR_HTML, height=780, scrolling=False)
