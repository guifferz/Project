const cv = document.getElementById('c');
const ctx = cv.getContext('2d');

let CW = 6, CH = 10;           // tamanho da célula (ajusta sozinho se ficar pesado)
let W, H, cols, rows;

function resize() {
  W = cv.width = innerWidth;
  H = cv.height = innerHeight;
  cols = Math.floor(W / CW);
  rows = Math.floor(H / CH);
  ctx.font = CH + 'px monospace';
  ctx.textBaseline = 'top';
}
addEventListener('resize', resize);
resize();

// ---------- Cena (unidades: raio de Schwarzschild = 1) ----------
const R_IN = 2.4, R_OUT = 9.5;   // borda interna/externa do disco
let CAM_DIST = 16;
const SCALE = 0.7;               // campo de visão
const ROLL = -0.22;              // inclina a imagem inteira
const MAX_STEPS = 200;

let az = 0.0, el = 0.16;         // ângulos da câmera

// Arrastar para girar
let drag = null;
cv.addEventListener('pointerdown', e => { drag = [e.clientX, e.clientY]; cv.setPointerCapture(e.pointerId); });
cv.addEventListener('pointerup',   () => drag = null);
cv.addEventListener('pointermove', e => {
  if (!drag) return;
  az -= (e.clientX - drag[0]) * 0.005;
  el = Math.max(-1.45, Math.min(1.45, el + (e.clientY - drag[1]) * 0.005));
  drag = [e.clientX, e.clientY];
});

// Zoom com a roda do mouse
cv.addEventListener('wheel', e => {
  e.preventDefault();
  CAM_DIST = Math.max(6, Math.min(40, CAM_DIST * (1 + e.deltaY * 0.001)));
}, { passive: false });

// Rotação automática (duplo clique liga/desliga)
let auto = true;
cv.addEventListener('dblclick', () => { auto = !auto; });

// ---------- Caracteres e cores ----------
const RAMP = " .'`^,:;-~+=*#%@";
const LEVELS = 40;
const LUT = [];
for (let k = 0; k < LEVELS; k++) {
  const l = k / (LEVELS - 1);
  const r = Math.min(255, 255 * Math.pow(l, 0.4));
  const g = Math.min(255, 245 * Math.pow(l, 0.95));
  const b = Math.min(255, 225 * Math.pow(l, 2.0));
  LUT.push(`rgb(${r|0},${g|0},${b|0})`);
}

function hash2(a, b) {
  const s = Math.sin(a * 12.9898 + b * 78.233) * 43758.5453;
  return s - Math.floor(s);
}

// ---------- Loop principal ----------
let ema = 16, last = performance.now();

function frame(now) {
  const t = now / 1000;
  if (auto && !drag) az += 0.004;

  // Base da câmera (olhando para a origem)
  const cx = CAM_DIST * Math.cos(el) * Math.sin(az);
  const cy = CAM_DIST * Math.sin(el);
  const cz = -CAM_DIST * Math.cos(el) * Math.cos(az);
  let fx = -cx / CAM_DIST, fy = -cy / CAM_DIST, fz = -cz / CAM_DIST;
  let rx = fz, ry = 0, rz = -fx;
  const rl = Math.hypot(rx, rz); rx /= rl; rz /= rl;
  const ux = fy * rz - fz * ry, uy = fz * rx - fx * rz, uz = fx * ry - fy * rx;

  const cR = Math.cos(ROLL), sR = Math.sin(ROLL);

  ctx.fillStyle = '#000';
  ctx.fillRect(0, 0, W, H);

  for (let j = 0; j < rows; j++) {
    for (let i = 0; i < cols; i++) {
      const u0 = ((i + 0.5) * CW - W / 2) / (H / 2) * SCALE;
      const v0 = -((j + 0.5) * CH - H / 2) / (H / 2) * SCALE;
      const u = u0 * cR - v0 * sR;
      const v = u0 * sR + v0 * cR;

      // direção do raio
      let vx = fx + u * rx + v * ux;
      let vy = fy + u * ry + v * uy;
      let vz = fz + u * rz + v * uz;
      let inv = 1 / Math.hypot(vx, vy, vz);
      vx *= inv; vy *= inv; vz *= inv;

      let px = cx, py = cy, pz = cz;

      // momento angular (constante) -> força da curvatura
      const hx = py * vz - pz * vy;
      const hy = pz * vx - px * vz;
      const hz = px * vy - py * vx;
      const h2 = hx * hx + hy * hy + hz * hz;

      let acc = 0, trans = 1, escaped = false;

      for (let s = 0; s < MAX_STEPS; s++) {
        const r2 = px * px + py * py + pz * pz;
        const r = Math.sqrt(r2);
        if (r < 1.0) break;                                   // caiu no buraco
        if (r > 45 && (px * vx + py * vy + pz * vz) > 0) { escaped = true; break; }

        let dt = 0.1 * (r - 0.85);
        dt = dt < 0.03 ? 0.03 : (dt > 0.7 ? 0.7 : dt);

        // curvatura da luz: a = -1.5 * h² * pos / r^5
        const f = -1.5 * h2 / (r2 * r2 * r) * dt;
        vx += px * f; vy += py * f; vz += pz * f;
        inv = 1 / Math.hypot(vx, vy, vz);
        vx *= inv; vy *= inv; vz *= inv;

        const npx = px + vx * dt, npy = py + vy * dt, npz = pz + vz * dt;

        // atravessou o plano do disco (y = 0)?
        if (py * npy < 0 && trans > 0.03) {
          const k = py / (py - npy);
          const hxp = px + (npx - px) * k;
          const hzp = pz + (npz - pz) * k;
          const R = Math.hypot(hxp, hzp);
          if (R > R_IN && R < R_OUT) {
            const phi = Math.atan2(hzp, hxp);
            const omega = 1.7 / Math.pow(R, 1.5);
            const p = phi - omega * t;

            // textura: espirais + anéis finos
            let tex = 0.6 + 0.22 * Math.sin(3 * p + R * 2.2)
                          + 0.18 * Math.sin(7 * p - R * 4.1)
                          + 0.14 * Math.sin(R * 30);
            if (tex < 0.1) tex = 0.1;

            // efeito Doppler + redshift gravitacional
            const vorb = Math.sqrt(0.5 / R);
            const tx = -hzp / R, tz = hxp / R;           // tangente da órbita
            const beta = vorb * (-(tx * vx + tz * vz));  // velocidade em direção ao observador
            const g = (1 / (1 - beta)) * Math.sqrt(1 - 1 / R);

            let em = Math.pow(R_IN / R, 1.1) * tex * Math.pow(g, 2.0) * 2.6;
            const edge = Math.min(1, (R_OUT - R) / 2.5);  // esmaece na borda externa
            em *= edge;

            acc += em * trans;
            trans *= 0.55;                                // disco semitransparente
          }
        }
        px = npx; py = npy; pz = npz;
      }

      let l = 1 - Math.exp(-acc * 2.2);

      if (l < 0.05) {
        // fundo: estrelas distorcidas pela lente
        if (escaped) {
          const a = Math.atan2(vz, vx), e = Math.asin(vy);
          const hs = hash2(Math.floor(a * 70), Math.floor(e * 70));
          if (hs > 0.996) {
            const br = 0.35 + 0.65 * (hs - 0.996) / 0.004;
            ctx.fillStyle = `rgba(170,190,255,${(br * trans).toFixed(2)})`;
            ctx.fillText(hs > 0.9985 ? '*' : '.', i * CW, j * CH);
          }
        }
        continue;
      }

      ctx.fillStyle = LUT[Math.min(LEVELS - 1, (l * (LEVELS - 1)) | 0)];
      ctx.fillText(RAMP[Math.min(RAMP.length - 1, (l * (RAMP.length - 1) + 0.5) | 0)], i * CW, j * CH);
    }
  }

  // se estiver pesado, aumenta o tamanho das células automaticamente
  const dtms = now - last; last = now;
  ema = ema * 0.9 + dtms * 0.1;
  if (ema > 55 && CH < 20) { CW += 1; CH += 2; resize(); ema = 16; }

  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);