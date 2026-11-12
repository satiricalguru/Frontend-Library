/* "The Shelf" — an original Three.js scene for the Frontend Library landing page.
 * One instanced, rounded card per Refero brand palette. Scroll progress morphs the
 * cards from a loose nebula, into a helix "shelf", into a flat mosaic wall.
 */
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const smooth = (t) => t * t * (3 - 2 * t);
const ease = (t) => 1 - Math.pow(1 - t, 3);
const range = (p, a, b) => clamp((p - a) / (b - a));
function hash(i) { const x = Math.sin(i * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); }

export function createShelf(canvas, { count = 1342, reduced = false } = {}) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;

  const scene = new THREE.Scene();
  const bg = new THREE.Color('#07080c');
  scene.background = bg;
  scene.fog = new THREE.Fog(bg, 22, 70);
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;

  const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 200);
  const key = new THREE.DirectionalLight('#ffffff', 1.6); key.position.set(6, 10, 12); scene.add(key);
  const rim = new THREE.DirectionalLight('#3550ff', 2.2); rim.position.set(-10, -4, -6); scene.add(rim);

  const geometry = new RoundedBoxGeometry(1, 0.64, 0.07, 3, 0.06);
  const material = new THREE.MeshPhysicalMaterial({ roughness: 0.32, metalness: 0.05, clearcoat: 0.7, clearcoatRoughness: 0.2 });
  const mesh = new THREE.InstancedMesh(geometry, material, count);
  mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  const group = new THREE.Group(); group.add(mesh); scene.add(group);

  // ── three layouts ───────────────────────────────────────────
  const A = [], B = [], C = [];
  const qA = [], qB = [], qC = [];
  const golden = Math.PI * (3 - Math.sqrt(5));
  const cols = Math.ceil(Math.sqrt(count * 1.7));
  const rows = Math.ceil(count / cols);
  const e = new THREE.Euler();
  for (let i = 0; i < count; i++) {
    const h1 = hash(i), h2 = hash(i + 91), h3 = hash(i + 517);
    // A — nebula: fibonacci sphere with radial noise
    const y = 1 - (i / (count - 1)) * 2, r = Math.sqrt(1 - y * y), th = golden * i;
    const rad = 5 + h1 * 8;
    A.push(new THREE.Vector3(Math.cos(th) * r * rad, y * rad * 0.62, Math.sin(th) * r * rad));
    qA.push(new THREE.Quaternion().setFromEuler(e.set(h1 * 6.3, h2 * 6.3, h3 * 6.3)));
    // B — helix shelf (a spiral library)
    const t = i / count, ang = t * Math.PI * 2 * 11;
    const shelfR = 5.4 + Math.sin(t * 40) * 0.08;
    B.push(new THREE.Vector3(Math.cos(ang) * shelfR, (t - 0.5) * 24, Math.sin(ang) * shelfR));
    qB.push(new THREE.Quaternion().setFromEuler(e.set(0, -ang + Math.PI / 2, 0.06)));
    // C — mosaic wall, centred
    const cx = i % cols, cy = Math.floor(i / cols);
    C.push(new THREE.Vector3((cx - (cols - 1) / 2) * 1.08, ((rows - 1) / 2 - cy) * 0.74, 0));
    qC.push(new THREE.Quaternion());
  }
  const delay = Float32Array.from({ length: count }, (_, i) => hash(i + 7));
  const wallDelay = Float32Array.from({ length: count }, (_, i) => clamp(C[i].length() / 30 + hash(i + 3) * 0.15));

  // ── colors: placeholder ramp until real brand palettes arrive ──
  const color = new THREE.Color();
  for (let i = 0; i < count; i++) {
    color.setHSL(0.63 + hash(i) * 0.06, 0.15 + hash(i + 1) * 0.6, 0.18 + hash(i + 2) * 0.62);
    mesh.setColorAt(i, color);
  }
  function setPalette(hexes) {
    if (!hexes?.length) return;
    for (let i = 0; i < count; i++) { color.set(hexes[i % hexes.length]); mesh.setColorAt(i, color); }
    mesh.instanceColor.needsUpdate = true;
  }

  // ── state ───────────────────────────────────────────────────
  let progress = 0, target = 0, px = 0, py = 0, tpx = 0, tpy = 0;
  let running = false, raf = 0, last = performance.now(), time = 0;
  const m = new THREE.Matrix4(), q = new THREE.Quaternion(), p = new THREE.Vector3(), s = new THREE.Vector3(1, 1, 1), tmp = new THREE.Vector3();

  function layout(pr) {
    const ab = range(pr, 0.1, 0.46);   // nebula → helix
    const bc = range(pr, 0.56, 0.86);  // helix → wall
    for (let i = 0; i < count; i++) {
      const d = delay[i];
      const lab = smooth(clamp(ab * 1.6 - d * 0.6));
      const lbc = smooth(clamp(bc * 1.6 - wallDelay[i] * 0.6));
      p.copy(A[i]).lerp(B[i], lab);
      q.copy(qA[i]).slerp(qB[i], lab);
      if (lbc > 0) {
        // rotate the helix point into world space so the hand-off to the wall is seamless
        tmp.copy(p).applyAxisAngle(THREE.Object3D.DEFAULT_UP, group.rotation.y * (1 - lbc));
        p.lerpVectors(tmp, C[i], lbc);
        p.z += Math.sin(lbc * Math.PI) * (2.5 + d * 3); // cards arc forward as they fly in
        q.slerp(qC[i], lbc);
      }
      if (pr > 0.84) {
        const w = range(pr, 0.84, 1);
        p.z += Math.sin(C[i].x * 0.35 + time * 1.4) * Math.cos(C[i].y * 0.4 + time) * 0.22 * w;
      } else if (lab < 1) {
        p.y += Math.sin(time * 0.8 + d * 6.3) * 0.12 * (1 - lab); // nebula drift
      }
      s.setScalar(0.62 + 0.38 * Math.max(lab, lbc));
      m.compose(p, q, s);
      mesh.setMatrixAt(i, m);
    }
    mesh.instanceMatrix.needsUpdate = true;

    // group spin fades out as the wall forms
    const spin = 1 - smooth(bc);
    group.rotation.y = (time * 0.06 + pr * Math.PI * 1.6) * spin;
    group.rotation.x = 0.18 * (1 - ab) * spin;
    // on wide screens the scene sits right of the headline, then centres for the wall
    group.position.y = (camera.aspect < 0.8 ? 5.5 : 0) * (1 - ab);
    group.position.x = (camera.aspect > 1.15 ? THREE.MathUtils.lerp(6.5, 3.6, ab) : 0) * (1 - smooth(bc));

    // camera choreography
    const helixY = THREE.MathUtils.lerp(9, -9, range(pr, 0.3, 0.62));
    const camZ = THREE.MathUtils.lerp(24, 19, ab);
    const wallZ = THREE.MathUtils.lerp(36, 13, ease(range(pr, 0.82, 1)));
    camera.position.set(px * 1.2, THREE.MathUtils.lerp(ab > 0 ? helixY * ab : 0, 0, smooth(bc)) + py * 0.8, THREE.MathUtils.lerp(camZ, wallZ, smooth(bc)));
    camera.lookAt(0, camera.position.y * 0.85, 0);
  }

  function resize() {
    const w = canvas.clientWidth, h = canvas.clientHeight;
    if (!w || !h) return;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.fov = w < 720 ? 52 : 38;
    camera.updateProjectionMatrix();
  }

  function frame(now) {
    const dt = Math.min(0.05, (now - last) / 1000); last = now;
    if (!reduced) time += dt;
    progress += (target - progress) * (reduced ? 1 : 1 - Math.pow(0.0008, dt));
    px += (tpx - px) * 0.06; py += (tpy - py) * 0.06;
    layout(progress);
    renderer.render(scene, camera);
    if (running) raf = requestAnimationFrame(frame);
  }

  const ro = new ResizeObserver(resize); ro.observe(canvas); resize();
  layout(0); renderer.render(scene, camera);

  return {
    setProgress(v) { target = clamp(v); if (!running) { progress = target; layout(progress); renderer.render(scene, camera); } },
    setPointer(x, y) { if (!reduced) { tpx = x; tpy = y; } },
    setPalette(h) { setPalette(h); if (!running) renderer.render(scene, camera); },
    start() { if (running) return; running = true; last = performance.now(); raf = requestAnimationFrame(frame); },
    stop() { running = false; cancelAnimationFrame(raf); },
    dispose() { this.stop(); ro.disconnect(); geometry.dispose(); material.dispose(); pmrem.dispose(); renderer.dispose(); },
  };
}
