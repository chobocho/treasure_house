// arena.js — 8석짜리 화면. 캔버스 하나에 전부 그린다.
//
// 화면을 캔버스 하나로 몰아 넣은 이유는 접히는 화면 때문이다. DOM 으로 8개 판을
// 배치하면 374px(폴드 접힘)과 768px(펼침)에서 각각 다른 CSS 가 필요해지는데,
// 캔버스는 매 프레임 크기를 재서 칸 크기를 다시 계산하면 그만이다.
//
// 배치 규칙 하나: **내 판은 크게, 남의 판은 작게.** 8인 대전에서 남의 판을 보는
// 이유는 "누가 죽어 가는가"를 알기 위해서지 블록을 세기 위해서가 아니다.

const MINO_SIDE = 0.16;      // 블록 옆면 음영 비율

function shade(hex, amt) {
  const n = parseInt(hex.slice(1), 16);
  const c = [(n >> 16) & 255, (n >> 8) & 255, n & 255].map((v) =>
    Math.max(0, Math.min(255, Math.round(v + amt))));
  return `rgb(${c[0]},${c[1]},${c[2]})`;
}
function drawMino(g, px, py, s, color, dim) {
  if (s < 3) { g.fillStyle = color; g.fillRect(px, py, s, s); return; }
  const b = Math.max(1, Math.round(s * MINO_SIDE));
  g.fillStyle = dim ? shade(color, -60) : color;
  g.fillRect(px, py, s, s);
  g.fillStyle = shade(color, dim ? -20 : 55);
  g.fillRect(px, py, s, b);
  g.fillRect(px, py, b, s);
  g.fillStyle = shade(color, dim ? -90 : -45);
  g.fillRect(px, py + s - b, s, b);
  g.fillRect(px + s - b, py, b, s);
}

class Arena {
  constructor(host) {
    this.host = host;
    this.cv = document.createElement('canvas');
    this.cv.style.cssText = 'display:block;width:100%;height:100%;touch-action:none';
    host.appendChild(this.cv);
    this.g = this.cv.getContext('2d');
    this.seats = [];          // 서버가 알려 준 좌석 목록
    this.mine = [];           // 내 좌석 번호들 (최대 2)
    this.cores = {};          // 좌석 → 내 wasm 코어 (내 좌석만 있다)
    this.remote = {};         // 좌석 → {cells, s, at} 남의 판 스냅샷
    this.rects = {};          // 좌석 → 화면상의 사각형 (화살표를 그리려면 필요하다)
    this.arrows = [];         // 공격 화살표 애니메이션
    this.banner = '';
    this.W = 10; this.VIS = 20;
  }

  setSeats(seats, mine) {
    this.seats = seats;
    this.mine = mine.slice(0, 2);
    for (const s of seats) if (!this.remote[s.i]) this.remote[s.i] = { cells: new Uint8Array(200), s: null };
  }
  attach(i, core) { this.cores[i] = core; this.W = core.W; this.VIS = core.VIS; }
  // 서버가 중계해 준 남의 화면 (protocol.md §6)
  onState(i, b, s) {
    const r = this.remote[i] || (this.remote[i] = { cells: new Uint8Array(200), s: null });
    if (b) unsnapshot(b, r.cells);
    r.s = s;
  }
  onGarbage(i, n, from) { this.arrows.push({ from, to: i, n, t0: performance.now() }); }
  onKo(i, place) { const s = this.seats.find((x) => x.i === i); if (s) { s.alive = false; s.place = place; } }

  // ── 배치 ────────────────────────────────────────────────────────────
  layout() {
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    const w = this.host.clientWidth, h = this.host.clientHeight || 360;
    if (this.cv.width !== Math.round(w * dpr) || this.cv.height !== Math.round(h * dpr)) {
      this.cv.width = Math.round(w * dpr); this.cv.height = Math.round(h * dpr);
    }
    this.g.setTransform(dpr, 0, 0, dpr, 0, 0);
    const others = this.seats.filter((s) => !this.mine.includes(s.i));
    // 좁으면 위아래로, 넓으면 좌우로 나눈다. 경계는 560px —
    // 폴드 접힘(374)은 위아래, 펼침(768)은 좌우가 된다.
    const stacked = w < 560;
    const ownW = stacked ? w : Math.round(w * (this.mine.length > 1 ? 0.62 : 0.46));
    const ownH = stacked ? Math.round(h * 0.58) : h;
    return { w, h, others, stacked, ownW, ownH };
  }

  // 내 판 한 개: 필드 10칸 + 옆 패널 5칸
  drawOwn(i, x, y, boxW, boxH) {
    const g = this.g, core = this.cores[i];
    const cs = Math.max(3, Math.floor(Math.min(boxW / (this.W + 5.5), boxH / this.VIS)));
    const fw = cs * this.W, fh = cs * this.VIS;
    const ox = x + Math.round((boxW - fw - cs * 5.5) / 2), oy = y + Math.round((boxH - fh) / 2);
    this.rects[i] = { x: ox, y: oy, w: fw, h: fh };

    g.fillStyle = '#0b1020'; g.fillRect(ox, oy, fw, fh);
    g.strokeStyle = '#1e293b'; g.lineWidth = 1;
    for (let c = 1; c < this.W; c++) { g.beginPath(); g.moveTo(ox + c * cs, oy); g.lineTo(ox + c * cs, oy + fh); g.stroke(); }
    if (!core) return;
    const v = core.views;
    for (let k = 0; k < this.VIS * this.W; k++) {
      const val = v.cells[k]; if (!val) continue;
      drawMino(g, ox + (k % this.W) * cs, oy + ((k / this.W) | 0) * cs, cs, COLORS[val], false);
    }
    for (let k = 0; k < this.VIS * this.W; k++) {
      const val = v.overlay[k]; if (!val) continue;
      const ghost = val > 7;
      drawMino(g, ox + (k % this.W) * cs, oy + ((k / this.W) | 0) * cs, cs, COLORS[ghost ? val - 7 : val], ghost);
    }
    this.drawSide(i, ox + fw + cs * 0.4, oy, cs);
    const st = v.stats;
    if (st[ST.STATE] !== STATE.PLAY) this.drawDim(ox, oy, fw, fh, i);
  }

  // 옆 패널 — 홀드 · 다음 · 대기 게이지 · 숫자
  drawSide(i, x, y, cs) {
    const g = this.g, core = this.cores[i], v = core.views, st = v.stats;
    const s = Math.max(2, Math.round(cs * 0.45));
    g.font = `${Math.max(8, Math.round(cs * 0.62))}px system-ui,sans-serif`;
    g.textBaseline = 'top';
    g.fillStyle = '#94a3b8';
    g.fillText('HOLD', x, y);
    this.drawPiece(st[ST.HOLD], x, y + cs * 0.8, s);
    g.fillStyle = '#94a3b8';
    g.fillText('NEXT', x, y + cs * 3.2);
    for (let k = 0; k < 5; k++) this.drawPiece(st[ST.NEXT0 + k], x, y + cs * 4 + k * cs * 2.1, s);

    // 대기 게이지 — 덩어리마다 색이 다르다. "얼마나 묵었나"가 밝기로 보인다.
    const gx = x - cs * 0.35, gh = cs * this.VIS;
    g.fillStyle = '#1e293b'; g.fillRect(gx, y, cs * 0.28, gh);
    const q = v.queue, n = core.e.ng_queue_len();
    let acc = 0;
    for (let k = 0; k < n; k++) {
      const lines = q[k * 4], age = q[k * 4 + 3];
      const hgt = Math.min(gh, lines * cs);
      const hot = Math.min(1, age / 900);
      g.fillStyle = `rgb(${Math.round(180 + 75 * hot)},${Math.round(90 - 60 * hot)},60)`;
      g.fillRect(gx, y + gh - acc - hgt, cs * 0.28, hgt);
      acc += hgt;
      if (acc >= gh) break;
    }
    g.fillStyle = '#e2e8f0';
    g.fillText(`${st[ST.LINES]}줄`, x, y + cs * 15);
    g.fillText(`${st[ST.SCORE]}`, x, y + cs * 16.1);
    if (st[ST.COMBO] > 0) { g.fillStyle = '#fbbf24'; g.fillText(`${st[ST.COMBO]} COMBO`, x, y + cs * 17.2); }
  }

  drawPiece(p, x, y, s) {
    if (p < 0 || p === undefined) return;
    const m = SHAPES4[p];
    for (let k = 0; k < 16; k++) {
      if (!(m & (1 << k))) continue;
      drawMino(this.g, x + (k & 3) * s, y + (k >> 2) * s, s, COLORS[p + 1], false);
    }
  }

  // 남의 판 — 작게, 이름과 등수와 높이만.
  drawMini(seat, x, y, boxW, boxH) {
    const g = this.g, i = seat.i, r = this.remote[i];
    const cs = Math.max(1, Math.floor(Math.min((boxW - 6) / this.W, (boxH - 14) / this.VIS)));
    const fw = cs * this.W, fh = cs * this.VIS;
    const ox = x + Math.round((boxW - fw) / 2), oy = y + 12;
    this.rects[i] = { x: ox, y: oy, w: fw, h: fh };
    g.fillStyle = '#0b1020'; g.fillRect(ox, oy, fw, fh);
    if (r) {
      for (let k = 0; k < this.VIS * this.W; k++) {
        const val = r.cells[k]; if (!val) continue;
        drawMino(g, ox + (k % this.W) * cs, oy + ((k / this.W) | 0) * cs, cs, COLORS[val], false);
      }
      // 떨어지는 중인 조각은 스냅샷에 없다 — s[] 의 좌표로 직접 그린다(§5).
      if (r.s && r.s[S.STATE] === STATE.PLAY) {
        const m = SHAPES4R[r.s[S.PIECE]] ? SHAPES4R[r.s[S.PIECE]][r.s[S.ROT] & 3] : 0;
        for (let k = 0; k < 16; k++) {
          if (!(m & (1 << k))) continue;
          const bx = r.s[S.X] + (k & 3), by = r.s[S.Y] + (k >> 2);
          if (by < 0 || by >= this.VIS || bx < 0 || bx >= this.W) continue;
          drawMino(g, ox + bx * cs, oy + by * cs, cs, COLORS[r.s[S.PIECE] + 1], false);
        }
      }
    }
    g.font = '10px system-ui,sans-serif'; g.textBaseline = 'alphabetic';
    g.fillStyle = seat.kind === 'ai' ? '#a78bfa' : '#7dd3fc';
    const tag = seat.kind === 'ai' ? `🤖${seat.name}` : seat.name;
    g.fillText(tag.slice(0, 10), ox, oy - 2);
    if (r && r.s) {                       // 높이 막대 — 죽음에 얼마나 가까운가
      const hp = Math.min(1, r.s[S.HEIGHT] / 20);
      g.fillStyle = hp > 0.75 ? '#ef4444' : hp > 0.5 ? '#f59e0b' : '#22c55e';
      g.fillRect(ox + fw + 1, oy + fh * (1 - hp), 3, fh * hp);
    }
    if (!seat.alive) this.drawDim(ox, oy, fw, fh, i);
  }

  drawDim(x, y, w, h, i) {
    const g = this.g, seat = this.seats.find((s) => s.i === i);
    g.fillStyle = 'rgba(2,6,23,.72)'; g.fillRect(x, y, w, h);
    g.fillStyle = '#f8fafc';
    g.textAlign = 'center';
    g.font = `bold ${Math.max(11, Math.round(w / 5))}px system-ui,sans-serif`;
    g.fillText(seat && seat.place ? `${seat.place}등` : 'OVER', x + w / 2, y + h / 2);
    g.textAlign = 'left';
  }

  // 공격 화살표 — 누가 누구를 때렸는지가 8인 대전에서 가장 중요한 정보다.
  drawArrows() {
    const g = this.g, now = performance.now();
    this.arrows = this.arrows.filter((a) => now - a.t0 < 700);
    for (const a of this.arrows) {
      const p = this.rects[a.from], q = this.rects[a.to];
      if (!p || !q) continue;
      const t = (now - a.t0) / 700, alpha = 1 - t;
      g.strokeStyle = `rgba(248,113,113,${alpha.toFixed(2)})`;
      g.lineWidth = 1 + Math.min(4, a.n);
      g.beginPath();
      g.moveTo(p.x + p.w / 2, p.y + p.h / 2);
      g.lineTo(q.x + q.w / 2, q.y + q.h / 2);
      g.stroke();
    }
  }

  draw() {
    const { w, h, others, stacked, ownW, ownH } = this.layout();
    const g = this.g;
    g.fillStyle = '#020617'; g.fillRect(0, 0, w, h);
    this.rects = {};

    // 내 좌석 (1석 또는 2석)
    const n = Math.max(1, this.mine.length);
    for (let k = 0; k < this.mine.length; k++) {
      this.drawOwn(this.mine[k], Math.round(k * ownW / n), 0, Math.round(ownW / n), ownH);
    }
    // 남의 좌석 격자
    const gx = stacked ? 0 : ownW, gy = stacked ? ownH : 0;
    const gw = stacked ? w : w - ownW, gh = stacked ? h - ownH : h;
    if (others.length) {
      const cols = Math.min(others.length, Math.max(1, Math.round(Math.sqrt(others.length * gw / Math.max(1, gh)))));
      const rows = Math.ceil(others.length / cols);
      const cw = gw / cols, ch = gh / rows;
      others.forEach((s, k) => this.drawMini(s, gx + (k % cols) * cw, gy + ((k / cols) | 0) * ch, cw, ch));
    }
    this.drawArrows();
    if (this.banner) {
      g.fillStyle = 'rgba(2,6,23,.8)'; g.fillRect(0, h / 2 - 22, w, 44);
      g.fillStyle = '#f8fafc'; g.textAlign = 'center';
      g.font = 'bold 18px system-ui,sans-serif';
      g.fillText(this.banner, w / 2, h / 2 + 6);
      g.textAlign = 'left';
    }
  }
}

// 조각 모양 — 스폰 상태(회전 0)만. 홀드/넥스트 미리보기용이다.
const SHAPES4 = [0x00F0, 0x0071, 0x0074, 0x0066, 0x0036, 0x0072, 0x0063];
// 회전 4가지 전부 — 남의 판에서 떨어지는 조각을 그리려면 필요하다. tetris.cpp 의 표와 같다.
const SHAPES4R = [
  [0x00F0, 0x2222, 0x0F00, 0x4444], [0x0071, 0x0226, 0x0470, 0x0322],
  [0x0074, 0x0622, 0x0170, 0x0223], [0x0066, 0x0066, 0x0066, 0x0066],
  [0x0036, 0x0231, 0x0360, 0x0462], [0x0072, 0x0262, 0x0270, 0x0232],
  [0x0063, 0x0132, 0x0630, 0x0264],
];
