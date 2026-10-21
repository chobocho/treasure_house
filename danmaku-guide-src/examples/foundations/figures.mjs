import { dsin, dcos, direction, Pool, stepPool, emitPattern, PATTERN_PERIODS, Rng } from './core.mjs';

// 덱 그림은 손으로 그리지 않고 예제와 같은 함수로 좌표를 계산해 만든다.
// 그래야 공식을 바꾸면 그림도 함께 바뀌고 설명과 실제 동작이 어긋나지 않는다.
const C = { text: '#16283d', muted: '#55708f', accent: '#3a5c96', accent2: '#23375c', ok: '#2e9e5b', warn: '#d97706',
  bad: '#cb2c2c', special: '#7c3aed', grid: '#cfdaea', screen: '#081523', bullet: '#ff6e7c', player: '#6de3ff', panel: '#ffffff' };
const f = (n) => Number(n.toFixed(2));
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

function svg(w, h, body, label) {
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" role="img" aria-label="${esc(label)}" style="max-width:100%;height:auto;font-family:inherit">`
    + `<rect width="${w}" height="${h}" rx="10" fill="${C.panel}" stroke="${C.grid}"/>${body}</svg>`;
}
const text = (x, y, s, o = {}) => `<text x="${f(x)}" y="${f(y)}" font-size="${o.size ?? 15}" fill="${o.color ?? C.text}" text-anchor="${o.anchor ?? 'start'}"${o.weight ? ` font-weight="${o.weight}"` : ''}>${esc(s)}</text>`;
const line = (x1, y1, x2, y2, o = {}) => `<line x1="${f(x1)}" y1="${f(y1)}" x2="${f(x2)}" y2="${f(y2)}" stroke="${o.color ?? C.accent}" stroke-width="${o.width ?? 2}"${o.dash ? ` stroke-dasharray="${o.dash}"` : ''}${o.arrow ? ` marker-end="url(#${o.arrow})"` : ''}/>`;
const circle = (x, y, r, o = {}) => `<circle cx="${f(x)}" cy="${f(y)}" r="${f(r)}" fill="${o.fill ?? 'none'}" stroke="${o.color ?? 'none'}" stroke-width="${o.width ?? 2}"${o.dash ? ` stroke-dasharray="${o.dash}"` : ''}${o.opacity ? ` fill-opacity="${o.opacity}"` : ''}/>`;
const path = (pts, o = {}) => `<path d="${pts.map((p, i) => (i ? 'L' : 'M') + f(p[0]) + ' ' + f(p[1])).join('')}" fill="none" stroke="${o.color ?? C.accent}" stroke-width="${o.width ?? 2}"${o.dash ? ` stroke-dasharray="${o.dash}"` : ''}/>`;
// 그림마다 id가 겹치지 않도록 화살촉 정의에 접두어를 붙인다.
function arrows(prefix, colors) {
  return '<defs>' + Object.entries(colors).map(([k, c]) => `<marker id="${prefix}-${k}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="${c}"/></marker>`).join('') + '</defs>';
}

// 실제 탄환 풀을 돌려 화면 패널에 점으로 찍는다.
function screenPanel(x0, y0, w, h, title, run, scale = 1) {
  const pool = new Pool(4096);
  run(pool);
  let body = `<rect x="${x0}" y="${y0}" width="${w}" height="${h}" rx="6" fill="${C.screen}"/>`;
  for (let i = 0; i < pool.count; i++) {
    const x = x0 + pool.x[i] * scale, y = y0 + pool.y[i] * scale;
    if (x >= x0 && x <= x0 + w && y >= y0 && y <= y0 + h) body += circle(x, y, 2.4, { fill: C.bullet });
  }
  return body + text(x0 + 8, y0 + 20, title, { color: '#ffffff', size: 14 });
}
function simulate(pool, ticks, fire, width = 480, height = 640) {
  for (let t = 0; t < ticks; t++) { fire(t); stepPool(pool, width, height); }
}

export const figures = {
  axes() {
    const a = arrows('axes', { a: C.accent, s: C.special });
    const ox = 60, oy = 40, s = 1.2;
    let b = a + line(ox, oy, 430, oy, { arrow: 'axes-a' }) + line(ox, oy, ox, 300, { arrow: 'axes-a' });
    b += text(438, oy + 5, 'x') + text(ox - 5, 318, 'y', { anchor: 'middle' }) + text(ox - 8, oy - 12, '(0, 0)', { anchor: 'middle', color: C.muted, size: 13 });
    for (let x = 100; x <= 300; x += 100) b += line(ox + x * s, oy - 4, ox + x * s, oy + 4, { color: C.muted, width: 1 }) + text(ox + x * s, oy - 9, x, { anchor: 'middle', size: 12, color: C.muted });
    for (let y = 100; y <= 200; y += 100) b += line(ox - 4, oy + y * s, ox + 4, oy + y * s, { color: C.muted, width: 1 }) + text(ox - 10, oy + y * s + 4, y, { anchor: 'end', size: 12, color: C.muted });
    const px = ox + 100 * s, py = oy + 200 * s;
    b += line(ox, oy, px, py, { color: C.muted, dash: '5 4', width: 1.5 }) + circle(px, py, 5, { fill: C.accent });
    b += text(px + 10, py + 18, '위치 (100, 200)', { size: 14 });
    b += line(px, py, px + 4 * 12, py - 2 * 12, { color: C.special, arrow: 'axes-s', width: 2.5 });
    b += text(px + 58, py - 28, '변위 (4, −2) ×12배 확대', { color: C.special, size: 13 });
    b += text(250, 130, 'y가 커질수록 아래로 내려간다', { color: C.bad, size: 14 });
    return svg(470, 330, b, '화면 좌표계: 원점은 왼쪽 위, y축은 아래쪽');
  },
  length() {
    const a = arrows('len', { a: C.accent, s: C.special });
    const ox = 70, oy = 250, u = 50;
    let b = a + line(ox, oy, ox + 3 * u, oy, { color: C.ok, width: 3 }) + line(ox + 3 * u, oy, ox + 3 * u, oy - 4 * u, { color: C.warn, width: 3 });
    b += line(ox, oy, ox + 3 * u, oy - 4 * u, { color: C.special, width: 3, arrow: 'len-s' });
    b += `<rect x="${ox + 3 * u - 12}" y="${oy - 12}" width="12" height="12" fill="none" stroke="${C.muted}"/>`;
    b += text(ox + 1.5 * u, oy + 22, 'x = 3', { anchor: 'middle', color: C.ok }) + text(ox + 3 * u + 10, oy - 2 * u, 'y = 4', { color: C.warn });
    b += text(ox + 40, oy - 2.6 * u, '|v| = √(3² + 4²) = 5', { color: C.special, size: 15 });
    b += text(300, 70, '피타고라스 정리', { weight: 700 }) + text(300, 96, '빗변² = 밑변² + 높이²', { color: C.muted, size: 14 });
    b += text(300, 140, '정규화', { weight: 700 }) + text(300, 166, 'u = v / |v| = (0.6, 0.8)', { color: C.muted, size: 14 }) + text(300, 190, '|u| = 1, 방향은 그대로', { color: C.muted, size: 14 });
    return svg(520, 290, b, '벡터 (3, 4)의 길이는 5이고 정규화하면 (0.6, 0.8)');
  },
  diagonal() {
    const a = arrows('diag', { r: C.bad, o: C.ok, m: C.muted });
    const ox = 120, oy = 150, s = 22;
    let b = a + circle(ox, oy, 4 * s, { color: C.muted, dash: '4 4', width: 1.5 });
    b += line(ox, oy, ox + 4 * s, oy, { color: C.muted, arrow: 'diag-m' }) + line(ox, oy, ox + 4 * s, oy - 4 * s, { color: C.bad, arrow: 'diag-r', width: 2.5 });
    const [ux, uy] = direction(1, -1);
    b += line(ox, oy, ox + ux * 4 * s, oy + uy * 4 * s, { color: C.ok, arrow: 'diag-o', width: 2.5 });
    b += text(ox + 4 * s + 8, oy + 5, '오른쪽 4', { color: C.muted, size: 13 });
    b += text(ox + 4 * s + 6, oy - 4 * s + 12, '5.657', { color: C.bad, size: 13 });
    b += text(ox - 20, oy - 4 * s - 2, '4', { color: C.ok, size: 13 });
    b += text(345, 70, '대각선 입력 (1, −1)', { weight: 700 }) + text(345, 96, '정규화 없이 ×4 → 길이 4√2 ≈ 5.657', { color: C.bad, size: 13 });
    b += text(345, 120, '정규화 뒤 ×4 → (2.828, −2.828)', { color: C.ok, size: 13 }) + text(345, 144, '점선 원: 어느 방향이든 한 스텝 거리 4', { color: C.muted, size: 13 });
    return svg(610, 270, b, '대각선 이동을 정규화하지 않으면 1.414배 빨라진다');
  },
  turns() {
    const cx = 170, cy = 165, r = 110;
    let b = circle(cx, cy, r, { color: C.accent }) + line(cx - r - 20, cy, cx + r + 20, cy, { color: C.grid, width: 1 }) + line(cx, cy - r - 20, cx, cy + r + 20, { color: C.grid, width: 1 });
    const marks = [[0, '0', '0'], [.25, '0.25', 'π/2'], [.5, '0.5', 'π'], [.75, '0.75', '3π/2']];
    for (const [t, turn, rad] of marks) {
      const x = cx + dcos(t) * r, y = cy + dsin(t) * r;
      b += circle(x, y, 5, { fill: C.special });
      const lx = cx + dcos(t) * (r + 34), ly = cy + dsin(t) * (r + 30) + 5;
      b += text(lx, ly - 7, turn + '바퀴', { anchor: 'middle', size: 13, color: C.special }) + text(lx, ly + 9, rad, { anchor: 'middle', size: 13, color: C.muted });
    }
    let arc = [];
    for (let i = 0; i <= 20; i++) arc.push([cx + dcos(i / 80) * 40, cy + dsin(i / 80) * 40]);
    b += path(arc, { color: C.ok }) + text(cx + 34, cy + 40, '증가 방향', { color: C.ok, size: 12 });
    b += text(360, 60, 'θ(라디안) = 2π × 회전수', { weight: 700 }) + text(360, 90, '1바퀴 = 2π ≈ 6.2832', { color: C.muted, size: 14 });
    b += text(360, 130, 'y축이 아래라서', { color: C.bad, size: 14 }) + text(360, 152, '0.25바퀴가 화면 아래쪽,', { color: C.bad, size: 14 }) + text(360, 174, '증가 방향은 시계 방향', { color: C.bad, size: 14 });
    b += text(360, 214, '회전수는 1로 나눈 나머지만', { color: C.muted, size: 14 }) + text(360, 236, '보면 되므로 주기 처리가 쉽다', { color: C.muted, size: 14 });
    return svg(600, 330, b, '회전수와 라디안의 대응, 화면 좌표에서는 시계 방향');
  },
  unitCircle() {
    const cx = 160, cy = 160, r = 120, t = .1;
    const x = cx + dcos(t) * r, y = cy + dsin(t) * r;
    let b = circle(cx, cy, r, { color: C.accent }) + line(cx - r - 15, cy, cx + r + 15, cy, { color: C.grid, width: 1 }) + line(cx, cy - r - 15, cx, cy + r + 15, { color: C.grid, width: 1 });
    b += line(cx, cy, x, y, { color: C.special, width: 2.5 }) + line(x, cy, x, y, { color: C.warn, dash: '4 3' }) + line(cx, cy, x, cy, { color: C.ok, width: 3 });
    b += circle(x, y, 5, { fill: C.special });
    b += text(cx + (x - cx) / 2, cy - 8, 'cos', { color: C.ok, anchor: 'middle', size: 14 }) + text(x + 8, (cy + y) / 2 + 4, 'sin', { color: C.warn, size: 14 });
    b += text(x - 6, y + 22, `(${dcos(t).toFixed(3)}, ${dsin(t).toFixed(3)})`, { color: C.special, size: 13, anchor: 'end' });
    b += text(345, 70, '반지름 1인 원 위의 점', { weight: 700 }) + text(345, 98, '(cos θ, sin θ)', { color: C.muted, size: 15 });
    b += text(345, 138, '예: 0.1바퀴', { color: C.special, size: 14 }) + text(345, 162, 'vx = cos × 탄속', { color: C.ok, size: 14 }) + text(345, 186, 'vy = sin × 탄속', { color: C.warn, size: 14 });
    b += text(345, 226, '길이가 항상 1이므로 탄속은', { color: C.muted, size: 13 }) + text(345, 246, '방향과 무관하게 같다', { color: C.muted, size: 13 });
    return svg(560, 320, b, '단위원 위의 점 좌표가 코사인과 사인');
  },
  fold() {
    const x0 = 50, y0 = 150, w = 480, h = 100;
    let b = line(x0, y0, x0 + w, y0, { color: C.grid, width: 1 });
    const pts = [];
    for (let i = 0; i <= 200; i++) { const t = i / 200; pts.push([x0 + t * w, y0 - Math.sin(t * 2 * Math.PI) * h]); }
    b += `<rect x="${x0 + .25 * w}" y="${y0 - h - 12}" width="${.5 * w}" height="${2 * h + 24}" fill="${C.warn}" fill-opacity=".08"/>`;
    b += `<rect x="${x0 + .75 * w}" y="${y0 - h - 12}" width="${.25 * w}" height="${2 * h + 24}" fill="${C.special}" fill-opacity=".08"/>`;
    b += path(pts, { color: C.accent, width: 2.5 });
    for (const t of [0, .25, .5, .75, 1]) b += line(x0 + t * w, y0 - 4, x0 + t * w, y0 + 4, { color: C.muted, width: 1 }) + text(x0 + t * w, y0 + h + 32, t, { anchor: 'middle', size: 12, color: C.muted });
    // 접기 예: 0.4 → 0.1 (같은 사인 값)
    const s1 = [x0 + .4 * w, y0 - Math.sin(.4 * 2 * Math.PI) * h], s2 = [x0 + .1 * w, y0 - Math.sin(.1 * 2 * Math.PI) * h];
    b += line(s1[0], s1[1], s2[0], s2[1], { color: C.warn, dash: '5 4' }) + circle(s1[0], s1[1], 5, { fill: C.warn }) + circle(s2[0], s2[1], 5, { fill: C.ok });
    b += text(s1[0] + 8, s1[1] - 8, '0.4 → 0.5 − 0.4 = 0.1', { color: C.warn, size: 13 });
    b += text(x0 + .5 * w, 30, '(0.25, 0.75]: t → 0.5 − t', { anchor: 'middle', color: C.warn, size: 13 });
    b += text(x0 + .875 * w, 30, 't > 0.75: t → t − 1', { anchor: 'middle', color: C.special, size: 13 });
    b += text(x0 + .125 * w, 30, '[0, 0.25] 그대로', { anchor: 'middle', color: C.ok, size: 13 });
    return svg(580, 290, b, '사인 곡선의 대칭을 이용해 모든 입력을 -0.25~0.25바퀴로 접는다');
  },
  taylor() {
    const x0 = 60, y0 = 150, w = 460, h = 100;
    const X = (x) => x0 + (x + Math.PI / 2) / Math.PI * w, Y = (v) => y0 - v * h;
    let b = line(x0, y0, x0 + w, y0, { color: C.grid, width: 1 }) + line(X(0), y0 - h - 20, X(0), y0 + h + 20, { color: C.grid, width: 1 });
    const curve = (fn) => { const pts = []; for (let i = 0; i <= 120; i++) { const x = -Math.PI / 2 + i / 120 * Math.PI; if (Math.abs(fn(x)) <= 1.2) pts.push([X(x), Y(fn(x))]); } return pts; };
    b += path(curve((x) => x), { color: C.muted, dash: '4 4' });
    b += path(curve((x) => x - x ** 3 / 6), { color: C.warn, width: 2 });
    b += path(curve((x) => dsin(x / (2 * Math.PI))), { color: C.accent, width: 3 });
    b += text(X(1.15) - 6, Y(1.15), 'x (1항)', { color: C.muted, size: 13, anchor: 'end' }) + text(X(.9), Y(-.95) + 30, 'x − x³/3! (2항)', { color: C.warn, size: 13 });
    b += text(X(-1.5), Y(1.1), 'dsin: 7항 다항식', { color: C.accent, size: 13 });
    b += text(X(-Math.PI / 2), y0 + h + 36, '−π/2', { anchor: 'middle', size: 12, color: C.muted }) + text(X(Math.PI / 2), y0 + h + 36, 'π/2', { anchor: 'middle', size: 12, color: C.muted });
    let max = 0;
    for (let i = -250; i <= 250; i++) { const t = i / 1000; max = Math.max(max, Math.abs(dsin(t) - Math.sin(t * 2 * Math.PI))); }
    b += text(x0 + w, y0 + h + 56, `[−0.25, 0.25]바퀴 1001점 최대 오차 ${max.toExponential(1)}`, { anchor: 'end', size: 13, color: C.ok });
    return svg(580, 320, b, '항을 늘릴수록 테일러 다항식이 사인 곡선에 붙는다');
  },
  rotation() {
    const a = arrows('rot', { u: C.accent, r: C.special });
    const cx = 130, cy = 30, r = 170, d = .06;
    const u = [0, 1];
    const c = dcos(d), s = dsin(d);
    const v = [u[0] * c - u[1] * s, u[0] * s + u[1] * c];
    let b = a + line(cx, cy, cx + u[0] * r, cy + u[1] * r, { color: C.accent, width: 2.5, arrow: 'rot-u' });
    b += line(cx, cy, cx + v[0] * r, cy + v[1] * r, { color: C.special, width: 2.5, arrow: 'rot-r' });
    const arc = []; for (let i = 0; i <= 12; i++) { const t = .25 + d * i / 12; arc.push([cx + dcos(t) * 70, cy + dsin(t) * 70]); }
    b += path(arc, { color: C.warn }) + text(cx - 52, cy + 92, 'Δ', { color: C.warn, size: 15 });
    b += text(cx + 8, cy + r + 2, 'u = (0, 1)', { color: C.accent, size: 13 });
    b += text(cx + v[0] * r + 12, cy + v[1] * r + 26, `u′ = (${v[0].toFixed(3)}, ${v[1].toFixed(3)})`, { color: C.special, size: 13 });
    b += text(260, 70, '회전 행렬', { weight: 700 }) + text(260, 100, 'x′ = x·cos Δ − y·sin Δ', { color: C.muted, size: 14 }) + text(260, 124, 'y′ = x·sin Δ + y·cos Δ', { color: C.muted, size: 14 });
    b += text(260, 164, `예: Δ = ${d}바퀴`, { color: C.special, size: 14 }) + text(260, 188, '길이는 1로 그대로 유지', { color: C.muted, size: 14 });
    b += text(260, 212, '각도를 되돌려 구할 필요가 없다', { color: C.muted, size: 14 });
    return svg(540, 250, b, '회전 행렬로 조준 벡터를 작은 각도만큼 돌린다');
  },
  ring() {
    const a = arrows('ring', { a: C.accent, s: C.special });
    let b = a;
    const draw = (cx, cy, t0, color, mk) => { let s = ''; for (let i = 0; i < 8; i++) { const t = t0 + i / 8; s += line(cx, cy, cx + dcos(t) * 80, cy + dsin(t) * 80, { color, arrow: mk, width: i === 0 ? 3 : 1.8 }); } return s; };
    b += draw(130, 140, 0, C.accent, 'ring-a') + draw(380, 140, .04, C.special, 'ring-s');
    b += text(130, 260, 'θᵢ = i / 8 (t₀ = 0)', { anchor: 'middle', color: C.accent, size: 14 }) + text(380, 260, 'θᵢ = 0.04 + i / 8', { anchor: 'middle', color: C.special, size: 14 });
    b += text(255, 30, '굵은 화살표가 i = 0인 첫 탄환', { anchor: 'middle', color: C.muted, size: 13 });
    return svg(510, 280, b, '링: 한 바퀴를 n등분하고 시작 회전수 t0만큼 전체를 돌린다');
  },
  fan() {
    const a = arrows('fan', { a: C.accent, t: C.ok });
    const draw = (cx, cy, n, title) => {
      const gap = Math.min(.025, .5 / n);
      let s = line(cx, cy, cx, cy + 150, { color: C.ok, dash: '5 4', arrow: 'fan-t' });
      for (let i = 0; i < n; i++) { const t = .25 + (i - (n - 1) / 2) * gap; s += line(cx, cy, cx + dcos(t) * 120, cy + dsin(t) * 120, { color: C.accent, width: n > 20 ? 1 : 1.8 }); }
      return s + text(cx, cy + 180, title, { anchor: 'middle', size: 13 }) + text(cx, cy + 200, `간격 ${gap.toFixed(4)}바퀴, 폭 ${((n - 1) * gap).toFixed(3)}바퀴`, { anchor: 'middle', size: 12, color: C.muted });
    };
    let b = a + draw(140, 40, 7, '7발: 간격 0.025') + draw(420, 40, 64, '64발: 간격 0.5/64로 줄임');
    b += text(280, 270, '초록 점선: 목표 방향, 탄수가 많아도 전체 폭은 반 바퀴 미만', { anchor: 'middle', size: 13, color: C.muted });
    return svg(560, 290, b, '부채꼴: 목표 방향을 중심으로 좌우 대칭, 탄수가 많으면 간격을 줄인다');
  },
  spiralCancel() {
    const w = 240, h = 300, sc = .4;
    let b = screenPanel(20, 20, w, h, '예전: 8발 링을 60스텝마다', (pool) => simulate(pool, 150, (t) => { if (t % 60 === 0) emitPattern(pool, 'spiral', 8, 2.5, 300, 375, t, 0, 0); }, 600, 750), sc);
    b += screenPanel(280, 20, w, h, '지금: 2팔을 6스텝마다', (pool) => simulate(pool, 150, (t) => { if (t % 6 === 0) emitPattern(pool, 'spiral', 2, 2.5, 300, 375, t, 0, 0); }, 600, 750), sc);
    b += text(140, 345, '링 사이 회전 0.045바퀴뿐', { anchor: 'middle', size: 13, color: C.bad });
    b += text(400, 345, '6 × 0.007 = 0.042바퀴씩 이어짐', { anchor: 'middle', size: 13, color: C.ok });
    return svg(540, 365, b, '링 전체를 드물게 쏘면 회전이 대칭에 묻히고, 몇 팔을 이어 쏘면 나선이 보인다');
  },
  waveCenter() {
    const x0 = 60, y0 = 140, w = 460, h = 90;
    let b = line(x0, y0, x0 + w, y0, { color: C.grid, width: 1 });
    const pts = []; for (let t = 0; t <= 360; t += 3) pts.push([x0 + t / 360 * w, y0 - dsin(t / 180) * h]);
    b += path(pts, { color: C.accent, width: 2.5 });
    for (let t = 0; t <= 360; t += 60) { const v = dsin(t / 180); b += circle(x0 + t / 360 * w, y0 - v * h, 5, { fill: C.special }) + text(x0 + t / 360 * w, y0 + h + 30, t, { anchor: 'middle', size: 12, color: C.muted }); }
    b += text(x0 + w, y0 + h + 48, '논리 틱', { anchor: 'end', size: 12, color: C.muted });
    b += text(x0, 26, '중심 회전수 = 0.25 + 0.12 × sin(2π × 틱 / 180)', { size: 14, weight: 700 });
    b += text(x0 + w, y0 - h - 6, '+0.12', { anchor: 'end', size: 12, color: C.muted }) + text(x0 + w, y0 + h + 12, '−0.12', { anchor: 'end', size: 12, color: C.muted });
    b += text(x0, y0 + h + 64, '보라 점: 적이 60스텝마다 쏘는 시점 → 중심 0, +0.104, −0.104를 돈다', { size: 13, color: C.special });
    return svg(560, 300, b, '파동의 부채꼴 중심은 180스텝 주기로 좌우를 오간다');
  },
  waveCompare() {
    const w = 240, h = 300, sc = .5;
    const old = (pool, t) => { for (let i = 0; i < 8; i++) { const turn = .25 + dsin(t / 180 + i / 8) * .12; pool.add(240, 120, dcos(turn) * 2.5, dsin(turn) * 2.5); } };
    let b = screenPanel(20, 20, w, h, '예전: 위상에 i/n을 더함', (pool) => simulate(pool, 300, (t) => { if (t % 60 === 0) old(pool, t); }), sc);
    b += screenPanel(280, 20, w, h, '지금: 위상은 시간만', (pool) => simulate(pool, 300, (t) => { if (t % 60 === 0) emitPattern(pool, 'wave', 8, 2.5, 240, 120, t, 0, 0); }), sc);
    b += text(140, 345, '매번 같은 호, 대칭 두 발이 겹침', { anchor: 'middle', size: 13, color: C.bad });
    b += text(400, 345, '묶음 전체가 좌우로 흔들림', { anchor: 'middle', size: 13, color: C.ok });
    return svg(540, 365, b, '파동의 위상에 탄환 번호를 넣으면 흔들리지 않는다');
  },
  timeline() {
    const x0 = 40, w = 500;
    const ms = (v) => x0 + v / 100 * w;
    let b = text(x0, 30, '렌더 30Hz와 논리 60Hz (100ms 구간)', { weight: 700 });
    b += line(x0, 70, x0 + w, 70, { color: C.grid }) + text(x0, 60, '렌더', { size: 13, color: C.accent });
    for (let t = 0; t <= 100; t += 1000 / 30) b += line(ms(t), 64, ms(t), 76, { color: C.accent, width: 3 });
    b += line(x0, 130, x0 + w, 130, { color: C.grid }) + text(x0, 120, '논리 스텝 (h = 1/60초)', { size: 13, color: C.ok });
    for (let t = 1000 / 60; t <= 100.01; t += 1000 / 60) b += circle(ms(t), 130, 5, { fill: C.ok });
    b += text(x0, 175, '렌더 한 번에 누적 시간 33.3ms가 들어오면 스텝 2번을 진행한다', { size: 13, color: C.muted });
    b += text(x0, 198, '남은 시간 / h = α는 다음 렌더까지 넘기고 보간에만 쓴다', { size: 13, color: C.muted });
    return svg(580, 225, b, '렌더 주기와 무관하게 논리 스텝은 1/60초 간격');
  },
  lerp() {
    const a = arrows('lerp', { a: C.muted });
    const x1 = 80, x2 = 460, y = 90;
    let b = line(x1, y, x2, y, { color: C.grid, width: 2 }) + circle(x1, y, 9, { fill: C.muted }) + circle(x2, y, 9, { fill: C.accent });
    const al = .4, xm = x1 + (x2 - x1) * al;
    b += circle(xm, y, 9, { fill: C.special }) + text(x1, y + 32, '이전 상태 p₀', { anchor: 'middle', size: 13 }) + text(x2, y + 32, '현재 상태 p₁', { anchor: 'middle', size: 13 });
    b += text(xm, y - 20, 'α = 0.4 위치에 그림', { anchor: 'middle', size: 13, color: C.special });
    b += text(270, 170, '표시 위치 = p₀ + (p₁ − p₀) × α', { anchor: 'middle', size: 15, weight: 700 });
    b += text(270, 196, '게임 상태에는 저장하지 않는다', { anchor: 'middle', size: 13, color: C.bad });
    return svg(540, 230, b, '보간: 이전과 현재 상태 사이를 남은 시간 비율로 그린다');
  },
  collision() {
    const ax = 150, ay = 130, ar = 60, bx = 290, by = 170, br = 40;
    let b = circle(ax, ay, ar, { color: C.accent, fill: C.accent, opacity: .1 }) + circle(bx, by, br, { color: C.special, fill: C.special, opacity: .1 });
    b += line(ax, ay, bx, by, { color: C.warn, width: 2.5 }) + line(ax, ay, bx, ay, { color: C.ok, dash: '4 3' }) + line(bx, ay, bx, by, { color: C.ok, dash: '4 3' });
    b += circle(ax, ay, 4, { fill: C.accent }) + circle(bx, by, 4, { fill: C.special });
    b += text(ax - 30, ay - 10, 'r₁', { color: C.accent }) + text(bx + 12, by + 24, 'r₂', { color: C.special }) + text((ax + bx) / 2, ay - 8, 'dx', { color: C.ok, size: 13 }) + text(bx + 6, (ay + by) / 2 + 4, 'dy', { color: C.ok, size: 13 });
    b += text(380, 70, '겹침 조건', { weight: 700 }) + text(380, 98, 'dx² + dy² ≤ (r₁ + r₂)²', { size: 15, color: C.warn });
    b += text(380, 136, '양변 모두 0 이상이라', { size: 13, color: C.muted }) + text(380, 156, '제곱한 채 비교해도 같다', { size: 13, color: C.muted }) + text(380, 176, '→ 제곱근 계산이 필요 없다', { size: 13, color: C.muted });
    return svg(620, 270, b, '두 원은 중심 거리의 제곱이 반지름 합의 제곱 이하일 때 겹친다');
  },
  graze() {
    const cx = 200, cy = 150, s = 6;
    let b = circle(cx, cy, 20 * s, { color: C.warn, fill: C.warn, opacity: .08, dash: '6 4' }) + circle(cx, cy, 6.5 * s, { color: C.bad, fill: C.bad, opacity: .12 });
    b += circle(cx, cy, 2.5 * s, { fill: C.player }) + text(cx, cy + 4, '자기', { anchor: 'middle', size: 11 });
    b += circle(cx + 13 * s, cy, 4 * s, { fill: C.bullet, opacity: .8 }) + text(cx + 13 * s, cy + 46, '그레이즈', { anchor: 'middle', size: 12, color: C.warn });
    b += text(cx, cy - 6.5 * s - 8, '피격: d ≤ 2.5 + 4 = 6.5', { anchor: 'middle', size: 13, color: C.bad });
    b += text(cx, cy - 20 * s - 8, '그레이즈: 6.5 < d ≤ 16 + 4 = 20', { anchor: 'middle', size: 13, color: C.warn });
    b += text(360, 120, '피격 원 2.5 · 그레이즈 원 16', { size: 13, color: C.muted }) + text(360, 144, '적탄 반지름 4를 더해', { size: 13, color: C.muted }) + text(360, 168, '중심 거리로 판정한다', { size: 13, color: C.muted });
    return svg(560, 300, b, '피격 원과 그레이즈 원의 반지름 합으로 거리 구간을 나눈다');
  },
  tunnel() {
    let b = text(30, 30, '스텝마다 위치만 보는 이산 검사', { weight: 700 });
    const draw = (y, v, label, color) => {
      let s = circle(330, y, 12 * 1.6, { color: C.accent, fill: C.accent, opacity: .12 }) + text(330, y + 38, '적 r = 12', { anchor: 'middle', size: 12, color: C.muted });
      for (let k = 0; k < 7; k++) { const x = 330 - 3.5 * v * 1.6 + k * v * 1.6; s += circle(x, y, 3 * 1.6, { fill: color, opacity: .85 }); }
      return s + text(30, y - 26, label, { size: 13, color });
    };
    b += draw(100, 8, '아군탄 8/스텝: 두세 번 겹친다', C.ok) + draw(200, 40, '가상 40/스텝: 앞뒤 위치가 모두 밖이라 놓친다', C.bad);
    b += text(30, 262, '중심을 지나는 경로는 한 스텝 이동이 2×(12+3) = 30 이하이면 반드시 한 번 겹친다.', { size: 13, color: C.muted }) + text(30, 282, '스치는 경로는 겹치는 구간이 짧아 더 느려도 놓칠 수 있다.', { size: 13, color: C.muted });
    return svg(600, 300, b, '빠른 탄은 스텝 사이에 적을 건너뛸 수 있다');
  },
  xorshift() {
    const rng = new Rng(1);
    const bits = (v) => (v >>> 0).toString(2).padStart(32, '0');
    let x = 1;
    const rows = [['x', x]];
    x = (x ^ (x << 13)) >>> 0; rows.push(['x ^= x << 13', x]);
    x = (x ^ (x >>> 17)) >>> 0; rows.push(['x ^= x >>> 17', x]);
    x = (x ^ (x << 5)) >>> 0; rows.push(['x ^= x << 5', x]);
    const first = rng.next();
    let b = text(20, 30, `시드 1에서 첫 값: ${first}`, { weight: 700 });
    rows.forEach(([label, v], r) => {
      const y = 60 + r * 40;
      b += text(20, y + 15, label, { size: 13, color: C.special });
      [...bits(v)].forEach((bit, i) => { b += `<rect x="${140 + i * 13}" y="${y}" width="12" height="22" fill="${bit === '1' ? C.accent : '#eef3fa'}"/>`; });
      b += text(140 + 32 * 13 + 8, y + 15, v, { size: 12, color: C.muted });
    });
    b += text(20, 240, '왼쪽 시프트는 32비트를 넘는 비트를 버리고(>>> 0), 오른쪽 시프트는 위를 0으로 채운다', { size: 12, color: C.muted });
    return svg(640, 260, b, 'xorshift32가 시프트와 배타적 논리합으로 비트를 섞는 과정');
  },
  bossPath() {
    const x0 = 60, y0 = 40, w = 460, h = 180;
    const X = (age) => x0 + age / 480 * w, Y = (x) => y0 + (x - 80) / 320 * h;
    let b = `<rect x="${x0}" y="${y0}" width="${w}" height="${h}" fill="#f6f9fd" stroke="${C.grid}"/>`;
    for (const v of [100, 240, 380]) b += line(x0, Y(v), x0 + w, Y(v), { color: C.grid, width: 1, dash: v === 240 ? '' : '3 3' }) + text(x0 - 6, Y(v) + 4, v, { anchor: 'end', size: 12, color: C.muted });
    const pts = []; for (let age = 0; age <= 480; age += 4) pts.push([X(age), Y(240 + 140 * dsin(age / 240))]);
    b += path(pts, { color: C.special, width: 3 });
    for (const age of [0, 60, 120, 180, 240, 300, 360, 420, 480]) b += text(X(age), y0 + h + 18, age, { anchor: 'middle', size: 12, color: C.muted });
    b += text(x0 + w, y0 + h + 36, '보스 나이(스텝)', { anchor: 'end', size: 12, color: C.muted });
    b += text(x0, y0 - 14, 'x = 240 + 140 × sin(2π × 나이 / 240)   (세로축: x 좌표)', { size: 14, weight: 700 });
    return svg(560, 280, b, '보스는 240스텝 주기로 x 100과 380 사이를 오간다');
  },
  bossTimeline() {
    const x0 = 180, w = 380;
    const X = (t) => x0 + t / 100 * w;
    let b = text(20, 28, '단계별 공격 시점 (단계 시작부터 100스텝)', { weight: 700 });
    const rows = [['단계 1 링 12발', 45, C.accent], ['단계 2 부채꼴 7발', 32, C.ok], ['단계 3 나선 3팔', 4, C.special], ['단계 3 파동 6발', 20, C.warn]];
    rows.forEach(([label, p, color], r) => {
      const y = 60 + r * 40;
      b += text(20, y + 5, label, { size: 13, color }) + line(x0, y, x0 + w, y, { color: C.grid, width: 1 });
      for (let t = 0; t <= 100; t += p) b += circle(X(t), y, p === 4 ? 3 : 6, { fill: color });
    });
    for (const t of [0, 20, 40, 60, 80, 100]) b += text(X(t), 230, t, { anchor: 'middle', size: 12, color: C.muted });
    return svg(580, 250, b, '보스 단계마다 공격 간격이 다르고 마지막 단계는 나선과 파동을 겹친다');
  },
  patterns4() {
    const w = 120, h = 160, sc = .25;
    const panels = [
      ['링', (pool) => simulate(pool, 240, (t) => { if (t % 60 === 0) emitPattern(pool, 'ring', 8, 2.5, 240, 100, t, 240, 600); })],
      ['조준 부채꼴', (pool) => simulate(pool, 240, (t) => { if (t % 60 === 0) emitPattern(pool, 'fan', 8, 2.5, 240, 100, t, 240, 600); })],
      ['나선', (pool) => simulate(pool, 240, (t) => { if (t % 6 === 0) emitPattern(pool, 'spiral', 2, 2.5, 240, 100, t, 240, 600); })],
      ['파동', (pool) => simulate(pool, 240, (t) => { if (t % 60 === 0) emitPattern(pool, 'wave', 8, 2.5, 240, 100, t, 240, 600); })]
    ];
    let b = '';
    panels.forEach(([title, run], i) => { b += screenPanel(15 + i * (w + 10), 15, w, h, title, run, sc); });
    return svg(15 + 4 * (w + 10) + 5, h + 30, b, '적 패턴 네 가지의 240스텝 궤적');
  }
};

export function figureSvg(name) {
  if (!Object.hasOwn(figures, name)) throw new Error('없는 그림: ' + name);
  return figures[name]();
}
