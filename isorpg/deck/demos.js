/* ============================================================
   덱 안에서 도는 데모들.

   본문이 설명하는 식을 그대로 옮겼다. 화면에 뜨는 숫자가 본문의 숫자와
   다르면 데모가 없느니만 못하므로, 좌표·마스크·LCG·다이아몬드 스퀘어·
   옥타일·브레젠험은 전부 py/isorpg 의 구현과 같은 순서로 계산한다.

   자바스크립트의 정수는 배정밀도 실수다. 그래서 16.16 값과 2^32 LCG 에는
   >>, <<, &, | 를 쓰지 않는다 — 32비트로 잘려 조용히 틀린 답이 나온다.
   나눗셈은 Math.floor 로만 한다.
   ============================================================ */
(function () {
  'use strict';

  /* ---------- 팔레트 (CSS 변수는 캔버스 안에서 못 쓴다) ---------- */
  var C = {
    bg: '#f6f1e6', tile: '#e6dcc6', stroke: '#8a5a2b', hi: '#f4d98a',
    hot: '#e8a37a', cool: '#b9cbdc', dim: '#d6cdb8', text: '#2a2118',
    muted: '#6b5b46', line: '#b04a2a', black: '#2a2118'
  };

  /* ---------- 정수 연산 규약 (SPEC §1) ---------- */
  function fdiv(a, b) { return Math.floor(a / b); }
  function fmod(a, b) { return a - b * Math.floor(a / b); }

  function fmt(n, k) {
    // 지수 표기 없이 고정 소수점으로. 다만 자릿수가 터지면 유효숫자로 돌린다 —
    // 1.95^500 같은 값을 toFixed 로 찍으면 백 자리가 넘는 줄이 나온다.
    if (typeof n !== 'number' || !isFinite(n)) return String(n);
    if (k === undefined) return String(n);
    if (n !== 0 && (Math.abs(n) >= 1e9 || Math.abs(n) < 1e-9)) return n.toPrecision(6);
    return n.toFixed(k);
  }
  function comma(n) {
    var s = String(n), out = '', i, c = 0, neg = s.charAt(0) === '-';
    if (neg) s = s.slice(1);
    for (i = s.length - 1; i >= 0; i--) {
      out = s.charAt(i) + out;
      if (++c % 3 === 0 && i > 0) out = ',' + out;
    }
    return (neg ? '-' : '') + out;
  }
  function span(cls, s) { return '<span class="' + cls + '">' + s + '</span>'; }
  function put(host, api, lines) { api.w(host, lines.join('\n')); }

  /* ---------- 컨트롤 읽기 — 없는 컨트롤은 언제나 null 일 수 있다 ---------- */
  function q(host, sel) { return host.querySelector ? host.querySelector(sel) : null; }
  function numOf(el, dflt, lo, hi) {
    if (!el) return dflt;
    var v = parseFloat(el.value);
    if (!isFinite(v)) return dflt;
    if (v < lo) v = lo;
    if (v > hi) v = hi;
    return v;
  }
  function checked(el, dflt) { return el ? !!el.checked : dflt; }
  function on(el, type, fn) { if (el && el.addEventListener) el.addEventListener(type, fn); }

  /* ---------- 캔버스 무대 ----------
     접힌 갤럭시 폴드(374px)에서도 잘리지 않게 CSS 폭을 340px 이하로 묶고,
     내부 해상도는 devicePixelRatio 만큼 키워 선이 뭉개지지 않게 한다. */
  function stage(host, lw, lh) {
    var cv = document.createElement('canvas');
    cv.style.display = 'block';
    cv.style.margin = '8px auto';
    cv.style.borderRadius = '8px';
    cv.style.border = '1px solid rgba(138,90,43,.35)';
    cv.style.background = C.bg;
    cv.style.touchAction = 'none';
    var out = q(host, '.out');
    if (out && host.insertBefore) host.insertBefore(cv, out);
    else if (host.appendChild) host.appendChild(cv);
    var ctx = cv.getContext('2d');
    var st = { cv: cv, ctx: ctx, lw: lw, lh: lh, scale: 1, draw: null };

    st.fit = function () {
      // clientWidth 는 패딩을 포함한다(box-sizing: border-box). 그대로 쓰면
      // 접힌 폴드(374px)에서 캔버스가 .demo 상자를 22픽셀 삐져나간다.
      var w = host.clientWidth || 320;
      var pad = 0;
      try {
        var cs = window.getComputedStyle(host);
        pad = (parseFloat(cs.paddingLeft) || 0) + (parseFloat(cs.paddingRight) || 0);
      } catch (err) { pad = 26; }
      w = w - pad - 2;
      if (w > 340) w = 340;
      if (w < 200) w = 200;
      var h = Math.round(w * lh / lw);
      var dpr = window.devicePixelRatio || 1;
      if (dpr > 3) dpr = 3;
      cv.style.width = w + 'px';
      cv.style.height = h + 'px';
      cv.width = Math.round(w * dpr);
      cv.height = Math.round(h * dpr);
      st.scale = cv.width / lw;
    };
    st.begin = function () {
      ctx.setTransform(st.scale, 0, 0, st.scale, 0, 0);
      ctx.clearRect(0, 0, lw, lh);
      ctx.fillStyle = C.bg;
      ctx.fillRect(0, 0, lw, lh);
      ctx.lineJoin = 'round';
      ctx.textAlign = 'left';
      ctx.textBaseline = 'alphabetic';
    };
    st.pos = function (e) {
      var r = cv.getBoundingClientRect();
      var rw = r.width || lw, rh = r.height || lh;
      return { x: (e.clientX - r.left) * lw / rw, y: (e.clientY - r.top) * lh / rh };
    };
    st.fit();
    // 리사이즈 리스너를 데모마다 하나씩 달면 슬라이드 463장짜리 문서에서
    // 열어 본 데모 수만큼 쌓인다. 하나만 달고 명부를 훑는다.
    STAGES.push(st);
    installResize();
    // 슬라이드가 막 열린 순간에는 clientWidth 가 0 일 수 있다 — 한 프레임 뒤 다시 맞춘다
    if (window.requestAnimationFrame) {
      window.requestAnimationFrame(function () {
        st.fit();
        if (st.draw) st.draw();
      });
    }
    return st;
  }

  // 살아 있는 캔버스 명부. 리사이즈 한 번에 전부 다시 맞춘다.
  var STAGES = [];
  var resizeBound = false;
  function installResize() {
    if (resizeBound || !window.addEventListener) return;
    resizeBound = true;
    window.addEventListener('resize', function () {
      for (var i = 0; i < STAGES.length; i++) {
        var st = STAGES[i];
        // 숨은 슬라이드에서는 clientWidth 가 0 이라 엉뚱한 폭이 박힌다. 건너뛴다.
        if (!st.cv || !st.cv.parentNode) continue;
        var before = st.cv.style.width;
        st.fit();
        if (st.cv.style.width === '0px') { st.cv.style.width = before; continue; }
        if (st.draw) st.draw();
      }
    });
  }

  /* ---------- 포인터 ----------
     터치에서 슬라이드가 같이 스크롤되지 않게 드래그 중에는 preventDefault 한다.
     PointerEvent 가 없는 환경(검증 스텁 포함)에서는 마우스 이벤트로 떨어진다. */
  function bindPointer(st, h) {
    var down = false, cv = st.cv;
    function pd(e) { if (e && e.preventDefault) e.preventDefault(); }
    function onDown(e) {
      pd(e);
      down = true;
      if (cv.setPointerCapture && e.pointerId !== undefined && e.pointerId !== null) {
        try { cv.setPointerCapture(e.pointerId); } catch (err) { /* 캡처 실패는 무시 */ }
      }
      if (h.down) h.down(st.pos(e), e);
    }
    function onMove(e) {
      if (h.hover) h.hover(st.pos(e), e);
      if (!down) return;
      pd(e);
      if (h.move) h.move(st.pos(e), e);
    }
    function onUp(e) {
      if (!down) return;
      down = false;
      if (h.up) h.up(st.pos(e), e);
    }
    cv.addEventListener('pointerdown', onDown);
    cv.addEventListener('pointermove', onMove);
    cv.addEventListener('pointerup', onUp);
    // 캔버스 밖에서 손을 떼거나 브라우저가 스크롤을 가져가면 여기로 온다.
    // 이것이 없으면 down 이 참으로 남아 버튼을 뗀 뒤에도 드래그가 이어진다.
    if (window.addEventListener) {
      window.addEventListener('pointerup', onUp);
      window.addEventListener('pointercancel', onUp);
      window.addEventListener('mouseup', onUp);
    }
    cv.addEventListener('pointercancel', onUp);
    if (!window.PointerEvent) {
      cv.addEventListener('mousedown', onDown);
      cv.addEventListener('mousemove', onMove);
      cv.addEventListener('mouseup', onUp);
    }
  }

  /* ============================================================
     3·4·6부 — 투영과 역투영 (py/isorpg/proj.py 와 같은 식)
     ============================================================ */
  var TW = 32, TH = 16, TZ = 8, HW = 16, HH = 8;
  var SCR_W = 320, SCR_H = 200, MAP_W = 48, MAP_H = 48, MAXH = 15;

  function tileToScreen(tx, ty, h) { return [HW * (tx - ty), HH * (tx + ty) - h * TZ]; }
  function screenToTile(px, py) { return [fdiv(px + 2 * py, 32), fdiv(2 * py - px, 32)]; }

  // 32x16 모서리 마스크. 값은 2A + (B+1) 로 0..3 네 가지뿐이다.
  var PICK_MASK = (function () {
    var m = new Array(TW * TH), ox, oy, a, b;
    for (oy = 0; oy < TH; oy++) {
      for (ox = 0; ox < TW; ox++) {
        a = fdiv(ox + 2 * oy, 32);
        b = fdiv(2 * oy - ox, 32);
        m[oy * TW + ox] = 2 * a + (b + 1);
      }
    }
    return m;
  })();

  function pickMask(px, py) {
    var rc = fdiv(px, TW), rr = fdiv(py, TH);
    var ox = px - TW * rc, oy = py - TH * rr;
    var m = PICK_MASK[oy * TW + ox];
    return { tx: rc + rr + fdiv(m, 2), ty: rr - rc + fmod(m, 2) - 1,
             rc: rc, rr: rr, ox: ox, oy: oy, m: m };
  }

  var MARGIN_X = HW;
  var MARGIN_Y = HH + MAXH * TZ + 32;          // 8 + 120 + 32 = 160

  function visibleRange(x0, y0, x1, y1, margin) {
    var mx = margin ? MARGIN_X : 0, my = margin ? MARGIN_Y : 0;
    var ax0 = x0 - mx, ax1 = x1 + mx, ay0 = y0 - my, ay1 = y1 + my;
    var tx0 = fdiv(ax0 + 2 * ay0, 32), tx1 = fdiv(ax1 + 2 * ay1, 32);
    var ty0 = fdiv(2 * ay0 - ax1, 32), ty1 = fdiv(2 * ay1 - ax0, 32);
    if (tx0 < 0) tx0 = 0;
    if (ty0 < 0) ty0 = 0;
    if (tx1 > MAP_W - 1) tx1 = MAP_W - 1;
    if (ty1 > MAP_H - 1) ty1 = MAP_H - 1;
    return [tx0, ty0, tx1, ty1];
  }

  /* ============================================================
     5부 — 16.16 고정소수점 (py/isorpg/fixed.py)
     ============================================================ */
  var FP_ONE = 65536;
  function fpMul(a, b) {
    // a 를 상·하위 16비트로 쪼개 중간값을 2^53 아래로 묶는다 (정리 2.1)
    var ah = fdiv(a, FP_ONE);
    var al = a - ah * FP_ONE;
    return ah * b + fdiv(al * b, FP_ONE);
  }

  /* ============================================================
     9부 — 볼랜드 LCG (py/isorpg/rng.py)
     22695477 * 2^32 은 2^57 이라 배정밀도 가수를 넘는다. 상태를 16/16 으로
     쪼개 두 번 곱한 뒤 다시 합친다.
     ============================================================ */
  var LCG_A = 22695477, LCG_M = 4294967296;
  function Rng(seed) {
    this.s = fmod(seed, LCG_M);
  }
  Rng.prototype.step = function () {
    var s = this.s;
    var sh = fdiv(s, 65536);
    var sl = s - sh * 65536;
    var lo = LCG_A * sl + 1;                   // < 2^51
    var hi = LCG_A * sh;                       // < 2^51
    this.s = fmod(fmod(hi, 65536) * 65536 + lo, LCG_M);
    return this.s;
  };
  Rng.prototype.next = function () {
    // 비트 30..16 만 꺼내 쓴다 — 하위 비트는 주기가 짧다
    return fmod(fdiv(this.step(), 65536), 32768);
  };

  /* ============================================================
     9부 — 다이아몬드-스퀘어와 지형 (py/isorpg/gamemap.py)
     ============================================================ */
  var DS_N = 64, DS_CORNER = [520, 300, 700, 420], DS_SCALE = 560;
  var DS_OFF = fdiv(DS_N + 1 - MAP_W, 2);      // 8

  function genHeight(n, corners, scale, seed, roughNum, roughDen) {
    var size = n + 1, h = [], y, x, i;
    for (y = 0; y < size; y++) {
      h.push(new Array(size));
      for (x = 0; x < size; x++) h[y][x] = 0;
    }
    h[0][0] = corners[0];
    h[0][n] = corners[1];
    h[n][0] = corners[2];
    h[n][n] = corners[3];
    var r = new Rng(seed), step = n, half, s, cnt;
    // 반복 순서가 곧 난수 소비 순서다 — 여기가 어긋나면 맵이 통째로 달라진다
    while (step > 1) {
      half = fdiv(step, 2);
      for (y = half; y < size; y += step) {
        for (x = half; x < size; x += step) {
          s = h[y - half][x - half] + h[y - half][x + half]
            + h[y + half][x - half] + h[y + half][x + half];
          h[y][x] = fdiv(s, 4) + (fmod(r.next(), 2 * scale + 1) - scale);
        }
      }
      for (y = 0; y < size; y += half) {
        for (x = (fmod(fdiv(y, half), 2) === 0 ? half : 0); x < size; x += step) {
          s = 0; cnt = 0;
          if (x - half >= 0) { s += h[y][x - half]; cnt++; }
          if (x + half < size) { s += h[y][x + half]; cnt++; }
          if (y - half >= 0) { s += h[y - half][x]; cnt++; }
          if (y + half < size) { s += h[y + half][x]; cnt++; }
          h[y][x] = fdiv(s, cnt) + (fmod(r.next(), 2 * scale + 1) - scale);
        }
      }
      step = half;
      scale = fdiv(scale * roughNum, roughDen);
    }
    for (y = 0; y < size; y++) {
      for (i = 0; i < size; i++) {
        var v = h[y][i];
        h[y][i] = v < 0 ? 0 : (v > 1023 ? 1023 : v);
      }
    }
    return h;
  }

  function smooth(h, times) {
    var n = h.length, t, y, x, dy, dx, yy, xx, s, c, g, row;
    for (t = 0; t < times; t++) {
      g = [];
      for (y = 0; y < n; y++) {
        g.push(new Array(n));
        for (x = 0; x < n; x++) {
          s = 0; c = 0;
          for (dy = -1; dy <= 1; dy++) {
            yy = y + dy;
            if (yy < 0 || yy >= n) continue;
            row = h[yy];
            for (dx = -1; dx <= 1; dx++) {
              xx = x + dx;
              if (xx >= 0 && xx < n) { s += row[xx]; c++; }
            }
          }
          g[y][x] = fdiv(s, c);
        }
      }
      h = g;
    }
    return h;
  }

  var T_DEEP = 0, T_WATER = 1, T_SAND = 2, T_GRASS = 3, T_DIRT = 4, T_ROCK = 5,
      T_FOREST = 6, T_MOUNTAIN = 7, T_ROAD = 8, T_FLOOR = 9, T_WALL = 10;
  var MOVE = [0, 0, 12, 10, 10, 14, 16, 0, 8, 10, 0, 10, 13, 20, 0, 0];
  var OPAQUE = [false, false, false, false, false, false, true, true,
                false, false, true, false, false, false, false, true];
  var TER_COL = ['#2c4763', '#4f7fa6', '#ddca92', '#8fa860', '#a8875c', '#9b937f',
                 '#4d6f47', '#8d8478', '#b08f5e', '#c9bfa6', '#6b5b46', '#a8875c',
                 '#e6e6ea', '#5d6b4a', '#c05a2a', '#3a3a3a'];

  function terrainOfValue(v) {
    if (v < 100) return T_DEEP;
    if (v < 205) return T_WATER;
    if (v < 240) return T_SAND;
    if (v < 460) return T_GRASS;
    if (v < 630) return T_FOREST;
    if (v < 800) return T_ROCK;
    return T_MOUNTAIN;
  }
  function heightOfValue(v) {
    if (v < 205) return 0;
    var hh = fdiv(v - 205, 90);
    return hh > 12 ? 12 : hh;
  }

  var TOWN_X0 = 18, TOWN_Y0 = 18, TOWN_X1 = 30, TOWN_Y1 = 30;
  var TOWN_MID = 24, TOWN_H = 2, TOWN_WALL_H = 4;

  function stampTown(cells) {
    var tx, ty, i, t;
    for (ty = TOWN_Y0; ty < TOWN_Y1; ty++) {
      for (tx = TOWN_X0; tx < TOWN_X1; tx++) {
        if (tx === TOWN_X0 || tx === TOWN_X1 - 1 || ty === TOWN_Y0 || ty === TOWN_Y1 - 1) {
          cells[ty * MAP_W + tx] = T_WALL + TOWN_WALL_H * 16;
          continue;
        }
        t = (tx === TOWN_MID || ty === TOWN_MID) ? T_ROAD : T_FLOOR;
        cells[ty * MAP_W + tx] = t + TOWN_H * 16;
      }
    }
    var gates = [[TOWN_MID, TOWN_Y0], [TOWN_MID, TOWN_Y1 - 1],
                 [TOWN_X0, TOWN_MID], [TOWN_X1 - 1, TOWN_MID]];
    for (i = 0; i < gates.length; i++) {
      cells[gates[i][1] * MAP_W + gates[i][0]] = T_ROAD + TOWN_H * 16;
    }
    for (ty = 0; ty < TOWN_Y0; ty++) cells[ty * MAP_W + TOWN_MID] = T_ROAD + TOWN_H * 16;
    for (ty = TOWN_Y1; ty < MAP_H; ty++) cells[ty * MAP_W + TOWN_MID] = T_ROAD + TOWN_H * 16;
  }

  function cellsFrom(hg, town) {
    var cells = new Uint8Array(MAP_W * MAP_H), tx, ty, row, v;
    for (ty = 0; ty < MAP_H; ty++) {
      row = hg[ty + DS_OFF];
      for (tx = 0; tx < MAP_W; tx++) {
        v = row[tx + DS_OFF];
        cells[ty * MAP_W + tx] = terrainOfValue(v) + heightOfValue(v) * 16;
      }
    }
    if (town) stampTown(cells);
    return cells;
  }

  function terrainAt(cells, x, y) { return fmod(cells[y * MAP_W + x], 16); }
  function heightAt(cells, x, y) { return fdiv(cells[y * MAP_W + x], 16); }
  function inside(x, y) { return x >= 0 && x < MAP_W && y >= 0 && y < MAP_H; }

  function runCount(cells) {
    // save_rle 과 같은 규칙 — 행 우선, 런 하나는 최대 255칸
    var n = cells.length, i = 0, r = 0, j, v;
    while (i < n) {
      v = cells[i];
      j = i;
      while (j < n && cells[j] === v && j - i < 255) j++;
      r++;
      i = j;
    }
    return r;
  }

  // 골든 맵 — 씨앗 1, 거칠기 58/100, 평활 2회. 여러 데모가 함께 쓰므로 한 번만 만든다.
  var GOLD = null;
  function goldMap() {
    if (!GOLD) GOLD = cellsFrom(smooth(genHeight(DS_N, DS_CORNER, DS_SCALE, 1, 58, 100), 2), true);
    return GOLD;
  }

  /* ============================================================
     10부 — 경로 (py/isorpg/path.py)
     ============================================================ */
  var DIRX = [1, 1, 0, -1, -1, -1, 0, 1];
  var DIRY = [0, 1, 1, 1, 0, -1, -1, -1];
  var DIAG = [false, true, false, true, false, true, false, true];
  var STEP_BASE = [10, 14, 10, 14, 10, 14, 10, 14];
  var CLIMB_MAX = 1, MIN_MOVE = 8, BUCKET_N = 64;
  var STRAIGHT_MIN = fdiv(10 * MIN_MOVE, 10);  // 8
  var DIAG_MIN = fdiv(14 * MIN_MOVE, 10);      // 11

  function passable(cells, x, y) { return inside(x, y) && MOVE[terrainAt(cells, x, y)] > 0; }

  function stepOk(cells, x, y, d, noCut) {
    var nx = x + DIRX[d], ny = y + DIRY[d];
    if (!passable(cells, nx, ny)) return false;
    var dh = heightAt(cells, nx, ny) - heightAt(cells, x, y);
    if (dh > CLIMB_MAX || dh < -CLIMB_MAX) return false;
    if (DIAG[d] && noCut) {
      // 모서리 자르기 금지 — 두 직교 이웃이 모두 열려야 대각으로 지나간다
      if (!passable(cells, nx, y) || !passable(cells, x, ny)) return false;
    }
    return true;
  }
  function stepCost(cells, nx, ny, d) {
    return fdiv(STEP_BASE[d] * MOVE[terrainAt(cells, nx, ny)], 10);
  }
  function octile(ax, ay, bx, by) {
    var dx = ax - bx, dy = ay - by, hi, lo;
    if (dx < 0) dx = -dx;
    if (dy < 0) dy = -dy;
    if (dx < dy) { hi = dy; lo = dx; } else { hi = dx; lo = dy; }
    return STRAIGHT_MIN * hi + (DIAG_MIN - STRAIGHT_MIN) * lo;
  }

  function Bucket() {
    this.b = [];
    for (var i = 0; i < BUCKET_N; i++) this.b.push([]);
    this.cur = 0;
    this.n = 0;
  }
  Bucket.prototype.push = function (key, node) {
    this.b[fmod(key, BUCKET_N)].push([key, node]);
    this.n++;
  };
  Bucket.prototype.popMin = function () {
    if (this.n === 0) return null;
    for (var i = 0; i < BUCKET_N; i++) {
      var qb = this.b[this.cur];
      if (qb.length) { this.n--; return qb.pop(); }
      this.cur = fmod(this.cur + 1, BUCKET_N);
    }
    return null;
  };

  function dijkstra(cells, sx, sy, noCut) {
    var N = MAP_W * MAP_H, dist = new Int32Array(N), i, settled = 0;
    for (i = 0; i < N; i++) dist[i] = -1;
    if (!passable(cells, sx, sy)) return { dist: dist, settled: 0 };
    dist[sy * MAP_W + sx] = 0;
    var qb = new Bucket();
    qb.push(0, sy * MAP_W + sx);
    for (;;) {
      var it = qb.popMin();
      if (it === null) break;
      var g = it[0], idx = it[1];
      if (dist[idx] >= 0 && g > dist[idx]) continue;
      settled++;
      var x = fmod(idx, MAP_W), y = fdiv(idx, MAP_W);
      for (var d = 0; d < 8; d++) {
        if (!stepOk(cells, x, y, d, noCut)) continue;
        var nx = x + DIRX[d], ny = y + DIRY[d];
        var ng = g + stepCost(cells, nx, ny, d), ni = ny * MAP_W + nx;
        if (dist[ni] < 0 || ng < dist[ni]) { dist[ni] = ng; qb.push(ng, ni); }
      }
    }
    var reach = 0;
    for (i = 0; i < N; i++) if (dist[i] >= 0) reach++;
    return { dist: dist, settled: settled, reach: reach };
  }

  function astar(cells, sx, sy, gx, gy, noCut) {
    var N = MAP_W * MAP_H;
    var gcost = new Int32Array(N), prev = new Int32Array(N), closed = new Uint8Array(N), i;
    for (i = 0; i < N; i++) { gcost[i] = -1; prev[i] = -1; }
    if (!passable(cells, sx, sy) || !passable(cells, gx, gy)) {
      return { path: null, cost: -1, expanded: 0, closed: closed };
    }
    var si = sy * MAP_W + sx, gi = gy * MAP_W + gx, expanded = 0, found = false;
    gcost[si] = 0;
    var qb = new Bucket();
    qb.push(octile(sx, sy, gx, gy), si);
    for (;;) {
      var it = qb.popMin();
      if (it === null) break;
      var idx = it[1];
      if (closed[idx]) continue;
      closed[idx] = 1;
      expanded++;
      if (idx === gi) { found = true; break; }
      var x = fmod(idx, MAP_W), y = fdiv(idx, MAP_W), g = gcost[idx];
      for (var d = 0; d < 8; d++) {
        if (!stepOk(cells, x, y, d, noCut)) continue;
        var nx = x + DIRX[d], ny = y + DIRY[d], ni = ny * MAP_W + nx;
        if (closed[ni]) continue;
        var ng = g + stepCost(cells, nx, ny, d);
        if (gcost[ni] < 0 || ng < gcost[ni]) {
          gcost[ni] = ng;
          prev[ni] = idx;
          qb.push(ng + octile(nx, ny, gx, gy), ni);
        }
      }
    }
    if (!found) return { path: null, cost: -1, expanded: expanded, closed: closed };
    var path = [], j = gi;
    while (j !== -1) { path.push([fmod(j, MAP_W), fdiv(j, MAP_W)]); j = prev[j]; }
    path.reverse();
    return { path: path, cost: gcost[gi], expanded: expanded, closed: closed };
  }

  /* ============================================================
     11부 — 브레젠험·시야·안개 (py/isorpg/los.py)
     ============================================================ */
  var EYE = 2;
  function bresenham(x0, y0, x1, y1) {
    var dx = x1 - x0; if (dx < 0) dx = -dx;
    var dy = y1 - y0; if (dy < 0) dy = -dy;
    dy = -dy;
    var sx = x0 < x1 ? 1 : -1, sy = y0 < y1 ? 1 : -1;
    var err = dx + dy, x = x0, y = y0, out = [], e2;
    for (;;) {
      out.push([x, y]);
      if (x === x1 && y === y1) return out;
      e2 = 2 * err;
      if (e2 >= dy) { err += dy; x += sx; }
      if (e2 <= dx) { err += dx; y += sy; }
    }
  }
  function visibleTile(cells, sx, sy, gx, gy) {
    if (sx === gx && sy === gy) return true;
    if (!inside(gx, gy)) return false;
    var hs = heightAt(cells, sx, sy), hg = heightAt(cells, gx, gy);
    var top = (hs > hg ? hs : hg) + EYE - 1;
    var pts = bresenham(sx, sy, gx, gy), i, x, y;
    for (i = 1; i < pts.length - 1; i++) {
      x = pts[i][0]; y = pts[i][1];
      if (!inside(x, y)) return false;
      if (OPAQUE[terrainAt(cells, x, y)]) return false;
      if (heightAt(cells, x, y) > top) return false;
    }
    return true;
  }
  // 팔각 거리 근사 (fixed.oct_dist) — 조명 감쇠에만 쓴다
  function octDist(dx, dy) {
    var ax = dx < 0 ? -dx : dx, ay = dy < 0 ? -dy : dy;
    var hi = ax > ay ? ax : ay, lo = ax > ay ? ay : ax;
    return fdiv(983 * hi + 407 * lo, 1024);
  }
  function fogUpdate(cells, bits, px, py, R) {
    var i, x, y, dx, dy, row, seen = 0, vis = 0, checked = 0;
    for (i = 0; i < bits.length; i++) bits[i] = fmod(bits[i], 2);
    for (i = 0; i < bits.length; i++) if (bits[i]) seen++;
    var x0 = px - R, x1 = px + R, y0 = py - R, y1 = py + R;
    if (x0 < 0) x0 = 0;
    if (y0 < 0) y0 = 0;
    if (x1 > MAP_W - 1) x1 = MAP_W - 1;
    if (y1 > MAP_H - 1) y1 = MAP_H - 1;
    var rr = R * R;
    for (y = y0; y <= y1; y++) {
      dy = y - py;
      row = y * MAP_W;
      for (x = x0; x <= x1; x++) {
        dx = x - px;
        // 정사각형이 아니라 원 안만 본다 — 모서리는 반경 밖이다
        if (dx * dx + dy * dy > rr) continue;
        checked++;
        if (visibleTile(cells, px, py, x, y)) {
          if (bits[row + x] === 0) seen++;
          bits[row + x] = 3;
          vis++;
        }
      }
    }
    // 맵 가장자리에서는 사각형이 잘린다. 절약률을 원 덕분이라고 말하려면
    // 잘린 사각형과 비교해야 한다 — 잘린 몫까지 원의 공으로 돌리면 거짓말이 된다.
    return { seen: seen, vis: vis, checked: checked,
             square: (x1 - x0 + 1) * (y1 - y0 + 1) };
  }
  function lightOf(bits, x, y, px, py, R) {
    var v = bits[y * MAP_W + x];
    if (fmod(fdiv(v, 2), 2) === 1) {
      var d = octDist((x - px) * 256, (y - py) * 256);
      var l = 15 - fdiv(8 * d, R * 256);
      return l < 7 ? 7 : (l > 15 ? 15 : l);
    }
    if (fmod(v, 2) === 1) return 4;
    return 0;
  }

  /* ============================================================
     12부 — 주사위 분포 (py/isorpg/dice.py)
     ============================================================ */
  function diceDist(n, m) {
    var c = [1], k, s, f, c2, v;
    for (k = 0; k < n; k++) {
      c2 = new Array(c.length + m);
      for (s = 0; s < c2.length; s++) c2[s] = 0;
      for (s = 0; s < c.length; s++) {
        v = c[s];
        if (v) for (f = 1; f <= m; f++) c2[s + f] += v;
      }
      c = c2;
    }
    return c;
  }

  /* ============================================================
     7부 — 상자 부분순서와 위상 정렬 (py/isorpg/sortdag.py)
     상자 = [id, x0, y0, z0, x1, y1, z1]
     ============================================================ */
  function boxBbox(b) {
    var minx = 1e9, miny = 1e9, maxx = -1e9, maxy = -1e9, i, j, k, x, y, z, sx, sy;
    for (i = 1; i <= 4; i += 3) {
      x = b[i];
      for (j = 2; j <= 5; j += 3) {
        y = b[j];
        for (k = 3; k <= 6; k += 3) {
          z = b[k];
          sx = HW * (x - y);
          sy = HH * (x + y) - z * TZ;
          if (sx < minx) minx = sx;
          if (sx > maxx) maxx = sx;
          if (sy < miny) miny = sy;
          if (sy > maxy) maxy = sy;
        }
      }
    }
    return [minx, miny, maxx, maxy];
  }
  function behind(a, b) {
    // 셋 중 하나만 성립해도 참 — 이 느슨함이 순환을 만든다
    return a[4] <= b[1] || a[5] <= b[2] || a[6] <= b[3];
  }
  function depthKeyCmp(a, b) {
    var ka = a[1] + a[2], kb = b[1] + b[2];
    if (ka !== kb) return ka - kb;
    if (a[3] !== b[3]) return a[3] - b[3];
    return a[0] - b[0];
  }
  function topoSort(items) {
    var n = items.length, bb = [], adj = [], indeg = [], i, j, a, b;
    for (i = 0; i < n; i++) { bb.push(boxBbox(items[i])); adj.push([]); indeg.push(0); }
    var idx = [];
    for (i = 0; i < n; i++) idx.push(i);
    idx.sort(function (p, r) { return bb[p][0] - bb[r][0] || p - r; });
    var edges = 0;
    // 화면 x 로 훑는 쓸어내기 — 겹칠 수 없는 쌍은 아예 보지 않는다
    for (a = 0; a < n; a++) {
      i = idx[a];
      var ri = bb[i][2];
      for (b = a + 1; b < n; b++) {
        j = idx[b];
        if (bb[j][0] >= ri) break;
        if (bb[i][3] <= bb[j][1] || bb[j][3] <= bb[i][1]) continue;
        var aij = behind(items[i], items[j]), aji = behind(items[j], items[i]);
        // 양쪽 다 참이면 화면에서 겹칠 수 없다 (보조정리 6.2) — 간선을 걸지 않는다
        if (aij && !aji) { adj[i].push(j); indeg[j]++; edges++; }
        else if (aji && !aij) { adj[j].push(i); indeg[i]++; edges++; }
      }
    }
    var keep = [];
    for (i = 0; i < n; i++) keep.push(adj[i].slice());
    var ready = [], done = [], order = [], breaks = 0, left = n;
    for (i = 0; i < n; i++) done.push(false);
    for (i = 0; i < n; i++) if (indeg[i] === 0) ready.push(i);
    while (left > 0) {
      var pick = -1, at = -1;
      for (i = 0; i < ready.length; i++) {
        if (done[ready[i]]) continue;
        if (pick < 0 || depthKeyCmp(items[ready[i]], items[pick]) < 0) { pick = ready[i]; at = i; }
      }
      if (pick >= 0) {
        ready.splice(at, 1);
      } else {
        // 순환이다. 남은 것 중 깊이 키가 가장 작은 것을 강제로 방출한다
        breaks++;
        for (i = 0; i < n; i++) {
          if (done[i]) continue;
          if (pick < 0 || depthKeyCmp(items[i], items[pick]) < 0) pick = i;
        }
        for (i = 0; i < n; i++) {
          if (done[i]) continue;
          var at2 = adj[i].indexOf(pick);
          if (at2 >= 0) { adj[i].splice(at2, 1); indeg[pick]--; }
        }
      }
      done[pick] = true;
      left--;
      order.push(pick);
      for (i = 0; i < adj[pick].length; i++) {
        j = adj[pick][i];
        indeg[j]--;
        if (indeg[j] === 0 && !done[j]) ready.push(j);
      }
      adj[pick] = [];
    }
    return { order: order, breaks: breaks, edges: keep, nedges: edges, bbox: bb };
  }

  /* ============================================================
     3부 — 투영 실험실
     ============================================================ */
  window.__demo('proj-playground', function (host, api) {
    var st = stage(host, 320, 200);
    var ctx = st.ctx;
    var eTx = q(host, '[data-tx]'), eTy = q(host, '[data-ty]');
    var eH = q(host, '[data-h]'), eTw = q(host, '[data-tw]'), eTh = q(host, '[data-th]');

    function pow2(n) {
      // det 를 2^k · odd 로 갈라 본다. odd 가 1 이면 역행렬이 시프트로 끝난다.
      var k = 0, v = n;
      while (v > 0 && fmod(v, 2) === 0) { v = fdiv(v, 2); k++; }
      return { k: k, odd: v };
    }

    function draw() {
      var tw = Math.round(numOf(eTw, 32, 8, 64) / 2) * 2;
      var th = Math.round(numOf(eTh, 16, 4, 32) / 2) * 2;
      var w = fdiv(tw, 2), h = fdiv(th, 2);
      if (w < 2) w = 2;
      if (h < 1) h = 1;
      var tx = Math.round(numOf(eTx, 2, -4, 8));
      var ty = Math.round(numOf(eTy, 1, -4, 8));
      var hh = Math.round(numOf(eH, 0, 0, 6));
      var sx = w * (tx - ty), sy = h * (tx + ty) - hh * TZ;

      st.begin();
      var ox = 160 - w * (tx - ty), oy = 110 - h * (tx + ty);
      var i, j, vx, vy;
      function dia(vx0, vy0) {
        ctx.beginPath();
        ctx.moveTo(vx0, vy0);
        ctx.lineTo(vx0 + w, vy0 + h);
        ctx.lineTo(vx0, vy0 + 2 * h);
        ctx.lineTo(vx0 - w, vy0 + h);
        ctx.closePath();
      }
      ctx.lineWidth = 1;
      for (j = ty - 6; j <= ty + 6; j++) {
        for (i = tx - 6; i <= tx + 6; i++) {
          vx = ox + w * (i - j);
          vy = oy + h * (i + j);
          if (vx < -w - 4 || vx > 324 + w || vy < -2 * h - 4 || vy > 204 + 2 * h) continue;
          dia(vx, vy);
          ctx.fillStyle = (i === tx && j === ty) ? C.dim
                        : ((i + j) % 2 === 0 ? C.tile : '#efe7d4');
          ctx.fill();
          ctx.strokeStyle = 'rgba(138,90,43,.45)';
          ctx.stroke();
        }
      }
      // 고른 타일 — 높이만큼 기둥을 세워 h·TZ 픽셀이 어디로 가는지 보인다
      var bx = ox + w * (tx - ty), by = oy + h * (tx + ty);
      var ty0 = by - hh * TZ;
      if (hh > 0) {
        ctx.fillStyle = C.hot;
        ctx.beginPath();
        ctx.moveTo(bx - w, ty0 + h);
        ctx.lineTo(bx, ty0 + 2 * h);
        ctx.lineTo(bx, by + 2 * h);
        ctx.lineTo(bx - w, by + h);
        ctx.closePath();
        ctx.fill();
        ctx.fillStyle = '#d8916a';
        ctx.beginPath();
        ctx.moveTo(bx + w, ty0 + h);
        ctx.lineTo(bx, ty0 + 2 * h);
        ctx.lineTo(bx, by + 2 * h);
        ctx.lineTo(bx + w, by + h);
        ctx.closePath();
        ctx.fill();
      }
      dia(bx, ty0);
      ctx.fillStyle = C.hi;
      ctx.fill();
      ctx.strokeStyle = C.line;
      ctx.lineWidth = 2;
      ctx.stroke();

      // 기저 벡터 — 원점 타일의 꼭대기 꼭짓점에서 뻗는다
      function arrow(x0, y0, x1, y1, col, label) {
        ctx.strokeStyle = col;
        ctx.fillStyle = col;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(x0, y0);
        ctx.lineTo(x1, y1);
        ctx.stroke();
        var a = Math.atan2(y1 - y0, x1 - x0);
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x1 - 6 * Math.cos(a - 0.4), y1 - 6 * Math.sin(a - 0.4));
        ctx.lineTo(x1 - 6 * Math.cos(a + 0.4), y1 - 6 * Math.sin(a + 0.4));
        ctx.closePath();
        ctx.fill();
        ctx.font = 'bold 10px system-ui, sans-serif';
        ctx.fillText(label, x1 + 3, y1 + 3);
      }
      arrow(bx, ty0, bx + w, ty0 + h, C.line, 'e_x');
      arrow(bx, ty0, bx - w, ty0 + h, '#3a6ea5', 'e_y');
      if (hh > 0) arrow(bx, by, bx, by - hh * TZ, '#2e7d4f', 'h');

      ctx.font = '10px system-ui, sans-serif';
      ctx.fillStyle = C.muted;
      ctx.fillText('TW=' + tw + ' TH=' + th + ' · 화면 좌표 (' + sx + ', ' + sy + ')', 6, 14);

      var det = 2 * w * h, p = pow2(det);
      var lines = [];
      lines.push('tile_to_screen(' + tx + ', ' + ty + ', ' + hh + ') = '
                 + span('ok', '(' + sx + ', ' + sy + ')'));
      lines.push('  Vx = ' + w + '·(' + tx + ' − ' + ty + ') = ' + sx);
      lines.push('  Vy = ' + h + '·(' + tx + ' + ' + ty + ') − 8·' + hh + ' = ' + sy);
      lines.push('기저  e_x = (' + w + ', ' + h + ')   e_y = (−' + w + ', ' + h + ')   e_h = (0, −8)');
      lines.push('det M = 2·' + w + '·' + h + ' = ' + det
                 + (p.odd === 1 ? ' = 2^' + p.k : ' = 2^' + p.k + '·' + p.odd));
      lines.push('M⁻¹·det = [[' + h + ', ' + w + '], [−' + h + ', ' + w + ']]');
      if (p.odd === 1) {
        lines.push(span('ok', '역행렬 성분이 전부 2의 거듭제곱 배수 — 나눗셈이 시프트로 끝난다'));
      } else {
        lines.push(span('bad', 'det 가 2의 거듭제곱이 아니다 — ' + p.odd + ' 로 나누는 연산이 붙는다'));
      }
      lines.push(tw === 2 * th ? span('dim', 'TW = 2·TH — 화면 각도 arctan(1/2) = 26.565°')
                               : span('dim', 'TW ≠ 2·TH — 마름모 비율이 2:1 이 아니다'));
      put(host, api, lines);
    }
    st.draw = draw;
    [eTx, eTy, eH, eTw, eTh].forEach(function (el) {
      on(el, 'input', draw);
      on(el, 'change', draw);
    });
    draw();
  });

  /* ============================================================
     4부 — 픽킹
     ============================================================ */
  window.__demo('pick', function (host, api) {
    var LW = 320, LH = 176;
    var OX = 160, OY = 16;                     // 월드 (0,0) 이 놓이는 논리 좌표
    var st = stage(host, LW, LH), ctx = st.ctx;
    var cRect = q(host, '[data-rect]'), cMask = q(host, '[data-mask]');
    var mx = 40, my = 60;                      // 논리 좌표 기준 커서

    function draw() {
      var px = Math.round(mx - OX), py = Math.round(my - OY);
      var t = screenToTile(px, py);
      var pm = pickMask(px, py);
      st.begin();

      // 보이는 타일 범위 — 네 모서리를 역투영하면 된다 (정리 3.3 과 같은 논리)
      var c0 = screenToTile(-OX, -OY), c1 = screenToTile(LW - OX, -OY);
      var c2 = screenToTile(-OX, LH - OY), c3 = screenToTile(LW - OX, LH - OY);
      var tx0 = Math.min(c0[0], c1[0], c2[0], c3[0]) - 1;
      var tx1 = Math.max(c0[0], c1[0], c2[0], c3[0]) + 1;
      var ty0 = Math.min(c0[1], c1[1], c2[1], c3[1]) - 1;
      var ty1 = Math.max(c0[1], c1[1], c2[1], c3[1]) + 1;
      var i, j, vx, vy;
      ctx.lineWidth = 1;
      for (j = ty0; j <= ty1; j++) {
        for (i = tx0; i <= tx1; i++) {
          vx = OX + HW * (i - j);
          vy = OY + HH * (i + j);
          if (vx < -20 || vx > LW + 20 || vy < -20 || vy > LH + 20) continue;
          ctx.beginPath();
          ctx.moveTo(vx, vy);
          ctx.lineTo(vx + HW, vy + HH);
          ctx.lineTo(vx, vy + TH);
          ctx.lineTo(vx - HW, vy + HH);
          ctx.closePath();
          if (i === t[0] && j === t[1]) { ctx.fillStyle = C.hi; ctx.fill(); }
          else { ctx.fillStyle = C.tile; ctx.fill(); }
          ctx.strokeStyle = 'rgba(138,90,43,.5)';
          ctx.stroke();
        }
      }

      // 마스크 색칠 — 두 직선이 사각형 중심에서 만나 넷으로 자른다
      if (checked(cMask, false)) {
        var rc0 = fdiv(-OX, TW), rc1 = fdiv(LW - OX, TW);
        var rr0 = fdiv(-OY, TH), rr1 = fdiv(LH - OY, TH);
        var COLM = { 0: C.cool, 1: C.hi, 2: C.dim, 3: C.hot };
        ctx.globalAlpha = 0.5;
        for (var rr = rr0; rr <= rr1; rr++) {
          for (var rcc = rc0; rcc <= rc1; rcc++) {
            var bx = OX + rcc * TW, by = OY + rr * TH;
            var tri = [
              [[0, 0], [TW, 0], [HW, HH], 0],          // 위    A=0 B=-1
              [[0, 0], [0, TH], [HW, HH], 1],          // 왼쪽  A=0 B=0
              [[TW, 0], [TW, TH], [HW, HH], 2],        // 오른쪽 A=1 B=-1
              [[0, TH], [TW, TH], [HW, HH], 3]         // 아래  A=1 B=0
            ];
            for (var k = 0; k < 4; k++) {
              ctx.beginPath();
              ctx.moveTo(bx + tri[k][0][0], by + tri[k][0][1]);
              ctx.lineTo(bx + tri[k][1][0], by + tri[k][1][1]);
              ctx.lineTo(bx + tri[k][2][0], by + tri[k][2][1]);
              ctx.closePath();
              ctx.fillStyle = COLM[tri[k][3]];
              ctx.fill();
            }
          }
        }
        ctx.globalAlpha = 1;
      }

      if (checked(cRect, true)) {
        ctx.strokeStyle = 'rgba(176,74,42,.7)';
        ctx.lineWidth = 1;
        if (ctx.setLineDash) ctx.setLineDash([3, 3]);
        var gx, gy;
        for (gx = fmod(OX, TW) - TW; gx <= LW; gx += TW) {
          ctx.beginPath(); ctx.moveTo(gx, 0); ctx.lineTo(gx, LH); ctx.stroke();
        }
        for (gy = fmod(OY, TH) - TH; gy <= LH; gy += TH) {
          ctx.beginPath(); ctx.moveTo(0, gy); ctx.lineTo(LW, gy); ctx.stroke();
        }
        if (ctx.setLineDash) ctx.setLineDash([]);
      }

      // 커서와 고른 타일 표시
      var svx = OX + HW * (t[0] - t[1]), svy = OY + HH * (t[0] + t[1]);
      ctx.strokeStyle = C.line;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(svx, svy);
      ctx.lineTo(svx + HW, svy + HH);
      ctx.lineTo(svx, svy + TH);
      ctx.lineTo(svx - HW, svy + HH);
      ctx.closePath();
      ctx.stroke();
      ctx.fillStyle = C.line;
      ctx.beginPath();
      ctx.arc(mx, my, 3, 0, 6.2832);
      ctx.fill();
      ctx.font = 'bold 10px system-ui, sans-serif';
      ctx.fillStyle = C.text;
      ctx.fillText('(' + t[0] + ', ' + t[1] + ')', svx - 14, svy + HH + 4);

      var a = px + 2 * py, b = 2 * py - px;
      var name = ['위', '왼쪽', '오른쪽', '아래'][pm.m];
      var same = (pm.tx === t[0] && pm.ty === t[1]);
      put(host, api, [
        '픽셀 (' + px + ', ' + py + ')   a = px+2py = ' + a + '   b = 2py−px = ' + b,
        '대수적 역   tx = ⌊' + a + '/32⌋ = ' + t[0] + '   ty = ⌊' + b + '/32⌋ = ' + t[1],
        '사각형 (' + pm.rc + ', ' + pm.rr + ') 안 (' + pm.ox + ', ' + pm.oy + ')'
          + '   마스크 ' + pm.m + ' (' + name + ')',
        '표 조회   → (' + pm.tx + ', ' + pm.ty + ')',
        same ? span('ok', '두 방식이 같은 타일을 가리킨다')
             : span('bad', '두 방식이 갈렸다 — 있을 수 없는 일이다')
      ]);
    }
    st.draw = draw;
    on(cRect, 'change', draw);
    on(cMask, 'change', draw);
    bindPointer(st, {
      hover: function (p) { mx = p.x; my = p.y; draw(); },
      down: function (p) { mx = p.x; my = p.y; draw(); },
      move: function (p) { mx = p.x; my = p.y; draw(); }
    });
    draw();
  });

  /* ============================================================
     5부 — 고정소수점 오차
     ============================================================ */
  window.__demo('fixed-error', function (host, api) {
    var LW = 320, LH = 150;
    var st = stage(host, LW, LH), ctx = st.ctx;
    var eV = q(host, '[data-v]'), eN = q(host, '[data-n]'), bRun = q(host, '[data-run]');
    var LIMIT = 2147483648;                    // fp_mul 의 범위 조건 |a| < 2^31

    function run() {
      var v = numOf(eV, 0.9, 0.05, 1.95);
      var n = Math.round(numOf(eN, 50, 1, 500));
      var x = Math.round(v * FP_ONE);          // 16.16 로 옮긴 값
      var vx = x / FP_ONE;                     // 실수 쪽도 같은 값에서 출발해야 공평하다
      var y = FP_ONE, f = 1.0, i, over = -1;
      var fixSeq = [], fltSeq = [], drift = [], amax = 0;
      for (i = 0; i < n; i++) {
        y = fpMul(y, x);
        f *= vx;
        if (over < 0 && (y >= LIMIT || y <= -LIMIT)) over = i + 1;
        fixSeq.push(y / FP_ONE);
        fltSeq.push(f);
        var d = y / FP_ONE - f;
        drift.push(d);
        if (Math.abs(d) * FP_ONE > amax) amax = Math.abs(d) * FP_ONE;
      }
      var fixed = y / FP_ONE;
      var ulp = (fixed - f) * FP_ONE;

      st.begin();
      var pad = 26, gw = LW - pad - 8, gh = LH - 34;
      ctx.strokeStyle = 'rgba(138,90,43,.35)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(pad, 8);
      ctx.lineTo(pad, 8 + gh);
      ctx.lineTo(pad + gw, 8 + gh);
      ctx.stroke();
      var scale = amax > 0 ? amax : 1;
      var mid = 8 + gh / 2;
      ctx.strokeStyle = 'rgba(138,90,43,.25)';
      ctx.beginPath();
      ctx.moveTo(pad, mid);
      ctx.lineTo(pad + gw, mid);
      ctx.stroke();
      ctx.strokeStyle = C.line;
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      for (i = 0; i < drift.length; i++) {
        var gx = pad + (drift.length === 1 ? gw : gw * i / (drift.length - 1));
        var gy = mid - (drift[i] * FP_ONE) / scale * (gh / 2 - 4);
        if (i === 0) ctx.moveTo(gx, gy); else ctx.lineTo(gx, gy);
      }
      ctx.stroke();
      ctx.font = '9px system-ui, sans-serif';
      ctx.fillStyle = C.muted;
      ctx.fillText('16.16 − 실수, 단위 = 1/65536', pad + 4, 18);
      ctx.fillText('0', pad - 10, mid + 3);
      ctx.fillText('+' + fmt(scale, 1), 2, 14);
      ctx.fillText('−' + fmt(scale, 1), 2, 8 + gh - 2);
      ctx.fillText('반복 ' + n + '회', pad + gw - 46, 8 + gh - 4);

      var lines = [];
      lines.push('값 ' + fmt(vx, 6) + ' (16.16 으로 ' + x + ') 을 ' + n + '번 곱한다');
      lines.push('16.16 내림 곱  ' + span('ok', fmt(fixed, 9)));
      lines.push('실수 곱        ' + fmt(f, 9));
      lines.push('차이 ' + fmt(fixed - f, 9) + '  = ' + fmt(ulp, 2) + ' ulp (1 ulp = 1/65536)');
      if (y === 0) {
        lines.push(span('bad', '16.16 값이 0 으로 죽었다 — 65536 분의 1 아래는 표현할 수 없다'));
      }
      if (over > 0) {
        lines.push(span('bad', over + '회째에 |x| ≥ 2³¹ — fp_mul 의 범위 조건을 벗어났다'));
      }
      lines.push(span('dim', '내림은 매번 최대 1 ulp 를 깎는다. 값이 1 에 가까울수록 결과가'
                 + ' 오래 살아남아 그 깎임이 쌓인다.'));
      put(host, api, lines);
    }
    st.draw = run;
    on(bRun, 'click', run);
    on(eV, 'change', run);
    on(eN, 'change', run);
    run();
  });

  /* ============================================================
     6부 — 가시 범위
     ============================================================ */
  window.__demo('viewport-range', function (host, api) {
    var LW = 300, LH = 300, CS = 6, PAD = 6;
    var st = stage(host, LW, LH), ctx = st.ctx;
    var cMargin = q(host, '[data-margin]'), cReal = q(host, '[data-real]');
    // 맵 전체가 차지하는 월드 픽셀 범위 (camera.py 의 WORLD_*)
    var WX0 = -HW * (MAP_H - 1) - HW, WX1 = HW * (MAP_W - 1) + HW;
    var WY0 = -MAXH * TZ, WY1 = 8 * (MAP_W + MAP_H - 2) + 16;
    var cam = [0, 0];

    function clampCam(cx, cy) {
      var lox = WX0, hix = WX1 - SCR_W, loy = WY0, hiy = WY1 - SCR_H;
      if (cx < lox) cx = lox;
      if (cx > hix) cx = hix;
      if (cy < loy) cy = loy;
      if (cy > hiy) cy = hiy;
      return [cx, cy];
    }
    function gx(tx) { return PAD + tx * CS; }
    function gy(ty) { return PAD + ty * CS; }

    function draw() {
      var cells = goldMap();
      var margin = checked(cMargin, true);
      var vr = visibleRange(cam[0], cam[1], cam[0] + SCR_W, cam[1] + SCR_H, margin);
      st.begin();
      var tx, ty, i;
      // 맵 자체
      for (ty = 0; ty < MAP_H; ty++) {
        for (tx = 0; tx < MAP_W; tx++) {
          ctx.fillStyle = TER_COL[terrainAt(cells, tx, ty)];
          ctx.fillRect(gx(tx), gy(ty), CS, CS);
        }
      }
      ctx.globalAlpha = 0.55;
      ctx.fillStyle = '#efe7d4';
      ctx.fillRect(PAD, PAD, MAP_W * CS, MAP_H * CS);
      ctx.globalAlpha = 1;

      // visible_range 가 돌려준 직사각 범위
      var empty = vr[0] > vr[2] || vr[1] > vr[3];
      var rect = 0;
      if (!empty) {
        rect = (vr[2] - vr[0] + 1) * (vr[3] - vr[1] + 1);
        ctx.fillStyle = 'rgba(244,217,138,.55)';
        ctx.fillRect(gx(vr[0]), gy(vr[1]), (vr[2] - vr[0] + 1) * CS, (vr[3] - vr[1] + 1) * CS);
        ctx.strokeStyle = C.stroke;
        ctx.lineWidth = 1.5;
        ctx.strokeRect(gx(vr[0]), gy(vr[1]), (vr[2] - vr[0] + 1) * CS, (vr[3] - vr[1] + 1) * CS);
      }

      // 정말 화면에 픽셀이 남는 타일 — 기둥(높이 h)까지 포함한 그리기 영역으로 판정한다
      var touch = 0;
      if (!empty) {
        for (ty = vr[1]; ty <= vr[3]; ty++) {
          for (tx = vr[0]; tx <= vr[2]; tx++) {
            var hgt = heightAt(cells, tx, ty);
            var vx = HW * (tx - ty), vy = HH * (tx + ty);
            var bx0 = vx - HW, bx1 = vx + HW, by0 = vy - hgt * TZ, by1 = vy + TH;
            if (bx1 <= cam[0] || bx0 >= cam[0] + SCR_W
                || by1 <= cam[1] || by0 >= cam[1] + SCR_H) continue;
            touch++;
            if (checked(cReal, false)) {
              ctx.fillStyle = 'rgba(232,163,122,.85)';
              ctx.fillRect(gx(tx), gy(ty), CS, CS);
            }
          }
        }
      }

      // 화면 사각형을 타일 좌표로 되돌린 모양 — 직사각형이 아니라 마름모다
      var cs = [[cam[0], cam[1]], [cam[0] + SCR_W, cam[1]],
                [cam[0] + SCR_W, cam[1] + SCR_H], [cam[0], cam[1] + SCR_H]];
      ctx.beginPath();
      for (i = 0; i < 4; i++) {
        var ftx = (cs[i][0] + 2 * cs[i][1]) / 32, fty = (2 * cs[i][1] - cs[i][0]) / 32;
        var lx = PAD + ftx * CS, ly = PAD + fty * CS;
        if (i === 0) ctx.moveTo(lx, ly); else ctx.lineTo(lx, ly);
      }
      ctx.closePath();
      ctx.strokeStyle = C.line;
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.fillStyle = 'rgba(176,74,42,.12)';
      ctx.fill();

      ctx.font = '9px system-ui, sans-serif';
      ctx.fillStyle = C.muted;
      ctx.fillText('타일 좌표 48×48 · 붉은 마름모가 320×200 화면', 6, LH - 3);

      var lines = [];
      lines.push('카메라 (' + cam[0] + ', ' + cam[1] + ')  여백 '
                 + (margin ? 'MARGIN_X=16 MARGIN_Y=160' : '없음'));
      if (empty) {
        lines.push(span('bad', 'visible_range = (' + vr.join(', ') + ') — 빈 범위다'));
      } else {
        lines.push('visible_range → tx ' + vr[0] + '..' + vr[2] + ', ty ' + vr[1] + '..' + vr[3]
                   + '  = ' + (vr[2] - vr[0] + 1) + '×' + (vr[3] - vr[1] + 1)
                   + ' = ' + span('ok', comma(rect) + '타일'));
        lines.push('실제로 화면에 픽셀이 있는 타일  ' + span('ok', comma(touch) + '타일')
                   + '  (범위의 ' + Math.round(100 * touch / rect) + '%)');
        lines.push('맵 전체 2,304 타일 대비 — 범위 ' + Math.round(100 * rect / 2304)
                   + '% · 실제 ' + Math.round(100 * touch / 2304) + '%');
      }
      lines.push(span('dim', '네 모서리를 역투영한 직사각 근사다. 정확한 마름모 판정을 넣으면'
                 + ' 판정 비용이 절약분을 먹는다.'));
      put(host, api, lines);
    }
    st.draw = draw;
    on(cMargin, 'change', draw);
    on(cReal, 'change', draw);
    function setCam(p) {
      var ftx = (p.x - PAD) / CS, fty = (p.y - PAD) / CS;
      var wx = HW * (ftx - fty), wy = HH * (ftx + fty);
      cam = clampCam(Math.round(wx - SCR_W / 2), Math.round(wy - SCR_H / 2));
      draw();
    }
    bindPointer(st, { down: setCam, move: setCam });
    draw();
  });

  /* ============================================================
     7부 — 상자 정렬
     ============================================================ */
  window.__demo('painter-sort', function (host, api) {
    var LW = 320, LH = 230, S = 1.2, OX = 160, OY = 78;
    var st = stage(host, LW, LH), ctx = st.ctx;
    var bAdd = q(host, '[data-add]'), bCycle = q(host, '[data-cycle]'), bReset = q(host, '[data-reset]');
    // 골든 벡터 4번 wall-and-actor — 3칸 성벽과 캐릭터 둘
    function sceneWall() {
      return [[0, 4, 2, 0, 5, 6, 3], [1, 5, 3, 0, 6, 4, 2], [2, 3, 3, 0, 4, 4, 2]];
    }
    // 골든 벡터 6번 three-cycle — 정확히 한 방향씩만 성립해 순환이 닫힌다
    function sceneCycle() {
      return [[0, 3, 1, 1, 6, 4, 3], [1, 2, 4, 0, 5, 6, 2], [2, 2, 3, 2, 3, 5, 4]];
    }
    var boxes = sceneWall(), drag = null;
    var HUE = ['#c98b52', '#7f9ec4', '#8fae74', '#c47f7f', '#a98fc4', '#b3a05e'];

    function P(x, y, z) { return [OX + S * HW * (x - y), OY + S * (HH * (x + y) - z * TZ)]; }
    function facePath(pts) {
      ctx.beginPath();
      ctx.moveTo(pts[0][0], pts[0][1]);
      for (var i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]);
      ctx.closePath();
    }
    function faces(b) {
      var x0 = b[1], y0 = b[2], z0 = b[3], x1 = b[4], y1 = b[5], z1 = b[6];
      return [
        [P(x0, y0, z1), P(x1, y0, z1), P(x1, y1, z1), P(x0, y1, z1)],   // 윗면
        [P(x1, y0, z0), P(x1, y1, z0), P(x1, y1, z1), P(x1, y0, z1)],   // x=x1 면
        [P(x0, y1, z0), P(x1, y1, z0), P(x1, y1, z1), P(x0, y1, z1)]    // y=y1 면
      ];
    }
    function inPoly(pt, poly) {
      var c = false, i, j;
      for (i = 0, j = poly.length - 1; i < poly.length; j = i++) {
        if ((poly[i][1] > pt.y) !== (poly[j][1] > pt.y)
            && pt.x < (poly[j][0] - poly[i][0]) * (pt.y - poly[i][1])
                      / (poly[j][1] - poly[i][1]) + poly[i][0]) c = !c;
      }
      return c;
    }
    function centerOf(b) {
      return P((b[1] + b[4]) / 2, (b[2] + b[5]) / 2, (b[3] + b[6]) / 2);
    }

    function draw() {
      var res = topoSort(boxes);
      var pos = [], i, j, k;
      for (i = 0; i < boxes.length; i++) pos.push(0);
      for (i = 0; i < res.order.length; i++) pos[res.order[i]] = i;
      st.begin();
      // 바닥 격자 — 타일 좌표 0..7
      ctx.strokeStyle = 'rgba(138,90,43,.25)';
      ctx.lineWidth = 1;
      for (i = 0; i <= 7; i++) {
        var a1 = P(i, 0, 0), a2 = P(i, 7, 0), b1 = P(0, i, 0), b2 = P(7, i, 0);
        ctx.beginPath(); ctx.moveTo(a1[0], a1[1]); ctx.lineTo(a2[0], a2[1]); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(b1[0], b1[1]); ctx.lineTo(b2[0], b2[1]); ctx.stroke();
      }
      // 위상 정렬이 내놓은 순서 그대로 덮어 그린다 — 결과가 눈에 보인다
      for (k = 0; k < res.order.length; k++) {
        var b = boxes[res.order[k]];
        var fs = faces(b), col = HUE[fmod(b[0], HUE.length)];
        var shade = ['', 'rgba(0,0,0,.18)', 'rgba(0,0,0,.32)'];
        for (i = 0; i < 3; i++) {
          facePath(fs[i]);
          ctx.fillStyle = col;
          ctx.fill();
          if (i > 0) { ctx.fillStyle = shade[i]; ctx.fill(); }
          ctx.strokeStyle = C.stroke;
          ctx.lineWidth = 1;
          ctx.stroke();
        }
        var c = centerOf(b);
        ctx.font = 'bold 11px system-ui, sans-serif';
        ctx.fillStyle = C.text;
        ctx.fillText(String(b[0]), c[0] - 3, c[1] + 4);
      }
      // 간선 — 순서를 어긴 간선(=끊긴 순환)은 붉게
      var broken = 0;
      for (i = 0; i < boxes.length; i++) {
        for (j = 0; j < res.edges[i].length; j++) {
          var t = res.edges[i][j];
          var p1 = centerOf(boxes[i]), p2 = centerOf(boxes[t]);
          var bad = pos[i] > pos[t];
          if (bad) broken++;
          ctx.strokeStyle = bad ? C.line : 'rgba(42,33,24,.55)';
          ctx.lineWidth = bad ? 2 : 1;
          var dx = p2[0] - p1[0], dy = p2[1] - p1[1];
          var len = Math.sqrt(dx * dx + dy * dy) || 1;
          var ex = p2[0] - dx / len * 9, ey = p2[1] - dy / len * 9;
          ctx.beginPath();
          ctx.moveTo(p1[0] + dx / len * 9, p1[1] + dy / len * 9);
          ctx.lineTo(ex, ey);
          ctx.stroke();
          var an = Math.atan2(dy, dx);
          ctx.fillStyle = bad ? C.line : 'rgba(42,33,24,.55)';
          ctx.beginPath();
          ctx.moveTo(ex, ey);
          ctx.lineTo(ex - 6 * Math.cos(an - 0.4), ey - 6 * Math.sin(an - 0.4));
          ctx.lineTo(ex - 6 * Math.cos(an + 0.4), ey - 6 * Math.sin(an + 0.4));
          ctx.closePath();
          ctx.fill();
        }
      }
      var ids = [];
      for (i = 0; i < res.order.length; i++) ids.push(boxes[res.order[i]][0]);
      var lines = [];
      lines.push('상자 ' + boxes.length + '개 · 간선 ' + res.nedges + '개');
      lines.push('그리는 순서  ' + span('ok', ids.join(' → ')));
      lines.push('순환 절단  ' + (res.breaks === 0
                 ? span('ok', '0회 — 부분순서에 순환이 없다')
                 : span('bad', res.breaks + '회 — 어떤 순서로 그려도 ' + broken
                        + '개 간선이 틀린다')));
      lines.push(span('dim', '상자를 끌어 옮겨 보라. 붉은 화살표가 끊긴 간선이다.'));
      put(host, api, lines);
    }
    st.draw = draw;

    function hit(p) {
      var res = topoSort(boxes), k, i;
      // 위에 그려진 것부터 찾는다
      for (k = res.order.length - 1; k >= 0; k--) {
        var b = boxes[res.order[k]], fs = faces(b);
        for (i = 0; i < 3; i++) if (inPoly(p, fs[i])) return res.order[k];
      }
      return -1;
    }
    bindPointer(st, {
      down: function (p) {
        var i = hit(p);
        if (i < 0) { drag = null; return; }
        drag = { i: i, p: p, x0: boxes[i][1], y0: boxes[i][2] };
      },
      move: function (p) {
        // 드래그 중에 초기화/순환 버튼을 누르면 boxes 가 통째로 바뀐다.
        // 옛 인덱스를 그대로 쓰면 undefined 를 짚고 터진다.
        if (!drag || !boxes[drag.i]) { drag = null; return; }
        var dsx = (p.x - drag.p.x) / S, dsy = (p.y - drag.p.y) / S;
        var dtx = Math.round((dsx + 2 * dsy) / 32), dty = Math.round((2 * dsy - dsx) / 32);
        var b = boxes[drag.i];
        var w = b[4] - b[1], h = b[5] - b[2];
        var nx = drag.x0 + dtx, ny = drag.y0 + dty;
        if (nx < 0) nx = 0;
        if (ny < 0) ny = 0;
        if (nx + w > 8) nx = 8 - w;
        if (ny + h > 8) ny = 8 - h;
        b[1] = nx; b[4] = nx + w;
        b[2] = ny; b[5] = ny + h;
        draw();
      },
      up: function () { drag = null; }
    });
    on(bAdd, 'click', function () {
      var n = boxes.length;
      // 배치는 결정적으로 — 난수를 쓰면 같은 화면이 두 번 나오지 않는다
      var x = fmod(n * 3 + 1, 7), y = fmod(n * 5 + 2, 7), z = fmod(n, 3);
      boxes.push([n, x, y, z, x + 1, y + 1, z + 2]);
      draw();
    });
    on(bCycle, 'click', function () { drag = null; boxes = sceneCycle(); draw(); });
    on(bReset, 'click', function () { drag = null; boxes = sceneWall(); draw(); });
    draw();
  });

  /* ============================================================
     8부 — RLE 블릿
     명암표와 팔레트는 엔진과 같은 방식으로 만든다. 램프 세 줄(각 16단계)에
     build_light 과 똑같은 최근접 색 탐색을 돌린다 — 그래서 15단계는 항등이다.
     ============================================================ */
  window.__demo('rle-blit', function (host, api) {
    var LW = 420, LH = 300, SX = 50, SY = 50;
    var st = stage(host, LW, LH), ctx = st.ctx;
    var eLight = q(host, '[data-light]'), cRuns = q(host, '[data-runs]');

    var PAL_N = 49, LEVELS = 16;
    var PAL = (function () {
      // 6비트 DAC 값. 램프의 어두운 끝이 0 이 아니라 검은색과는 거리가 남는다.
      var ramps = [[[7, 12, 5], [33, 51, 23]], [[9, 9, 11], [43, 43, 47]],
                   [[3, 7, 19], [19, 33, 55]]];
      var p = [[0, 0, 0]], r, s, k, a, b;
      for (r = 0; r < 3; r++) {
        a = ramps[r][0]; b = ramps[r][1];
        for (s = 0; s < 16; s++) {
          p.push([fdiv(a[0] * (15 - s) + b[0] * s, 15),
                  fdiv(a[1] * (15 - s) + b[1] * s, 15),
                  fdiv(a[2] * (15 - s) + b[2] * s, 15)]);
        }
      }
      return p;
    })();
    var LIGHT = (function () {
      var t = new Uint8Array(LEVELS * PAL_N), l, c, k, best, bd, d, dr, dg, db, tr, tg, tb;
      for (l = 0; l < LEVELS; l++) {
        for (c = 0; c < PAL_N; c++) {
          tr = fdiv(PAL[c][0] * l, 15);
          tg = fdiv(PAL[c][1] * l, 15);
          tb = fdiv(PAL[c][2] * l, 15);
          best = 0; bd = 1e9;
          for (k = 0; k < PAL_N; k++) {
            dr = PAL[k][0] - tr; dg = PAL[k][1] - tg; db = PAL[k][2] - tb;
            d = dr * dr + dg * dg + db * db;
            if (d < bd) { bd = d; best = k; if (d === 0) break; }
          }
          t[l * PAL_N + c] = best;
        }
      }
      return t;
    })();
    var IDENT = (function () { for (var c = 0; c < PAL_N; c++) if (LIGHT[15 * PAL_N + c] !== c) return false; return true; })();
    function css(c) {
      // 6→8비트 확장은 v*4 + v/16 — 0 은 0, 63 은 정확히 255
      function e6(v) { return v * 4 + fdiv(v, 16); }
      var p = PAL[c];
      return 'rgb(' + e6(p[0]) + ',' + e6(p[1]) + ',' + e6(p[2]) + ')';
    }

    // 마름모 행 범위를 픽킹 규칙에서 그대로 뽑는다 (tools/gen_tiles.diamond_rows)
    var DIA = (function () {
      var rows = [], y, x, mn, mx;
      for (y = 0; y < TH; y++) {
        mn = -1; mx = -1;
        for (x = 0; x < TW; x++) {
          if (fdiv(x - 16 + 2 * y, 32) === 0 && fdiv(2 * y - x + 16, 32) === 0) {
            if (mn < 0) mn = x;
            mx = x;
          }
        }
        rows.push([mn, mx]);
      }
      return rows;
    })();
    var BAYER = [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5];
    var STEPS = 4;                                   // 큐브 넉 장을 쌓은 기둥
    var SPR = (function () {
      var h = TH + TZ * STEPS, px = [], y, x, k, last, lv;
      for (y = 0; y < h; y++) {
        px.push(new Array(TW));
        for (x = 0; x < TW; x++) px[y][x] = 0;
      }
      for (y = 0; y < TH; y++) {
        if (DIA[y][0] < 0) continue;
        for (x = DIA[y][0]; x <= DIA[y][1]; x++) {
          // 베이어 4x4 디더 — 두 단계를 섞어 한 행에 런이 여럿 생긴다
          px[y][x] = 1 + 11 + (BAYER[fmod(y, 4) * 4 + fmod(x, 4)] < 8 ? 1 : 0);
        }
      }
      for (x = 0; x < TW; x++) {
        last = -1;
        for (y = 0; y < TH; y++) if (px[y][x]) last = y;
        if (last < 0) continue;
        for (k = 1; k <= TZ * STEPS; k++) {
          // 왼쪽 면을 더 어둡게 — 광원이 왼쪽 위에 있다고 본다
          lv = x < TW / 2 ? 7 : 9;
          if (k === TZ * STEPS) lv -= 1;
          px[last + k][x] = 1 + lv;
        }
      }
      var rows = [], total = 0, opaque = 0, run, c;
      for (y = 0; y < h; y++) {
        run = [];
        var cnt = 0;
        c = px[y][0];
        for (x = 0; x < TW; x++) {
          if (px[y][x] === c) { cnt++; continue; }
          run.push([cnt, c]);
          c = px[y][x];
          cnt = 1;
        }
        run.push([cnt, c]);
        for (x = 0; x < run.length; x++) { total++; if (run[x][1]) opaque++; }
        rows.push(run);
      }
      return { w: TW, h: h, ox: 16, oy: 0, rows: rows, runs: total, opaque: opaque };
    })();

    var sx = 160, sy = 70;                            // 스프라이트 기준점 (화면 좌표)

    function blit(level) {
      var top = sy - SPR.oy, left = sx - SPR.ox;
      var out = [], r, py, px, i, count, color, a, b, v;
      var rows = 0, skipped = 0, drawn = 0, clipped = 0, pixels = 0;
      for (r = 0; r < SPR.h; r++) {
        py = top + r;
        if (py < 0 || py >= SCR_H) { skipped++; continue; }
        rows++;
        px = left;
        var rr = SPR.rows[r];
        for (i = 0; i < rr.length; i++) {
          count = rr[i][0];
          color = rr[i][1];
          if (color) {
            a = px > 0 ? px : 0;
            b = px + count;
            if (b > SCR_W) b = SCR_W;
            if (a < b) {
              v = LIGHT[level * PAL_N + color];
              out.push([a, py, b - a, v]);
              drawn++;
              pixels += b - a;
              if (a !== px || b !== px + count) clipped++;
            }
          }
          px += count;
          if (px >= SCR_W) break;
        }
      }
      return { out: out, rows: rows, skipped: skipped, drawn: drawn,
               clipped: clipped, pixels: pixels };
    }

    function draw() {
      var level = Math.round(numOf(eLight, 15, 0, 15));
      var res = blit(level);
      st.begin();
      // 화면 밖에서 잘려 나간 부분을 흐리게 보여 준다
      var y, x, i, run, px;
      ctx.globalAlpha = 0.22;
      for (y = 0; y < SPR.h; y++) {
        px = sx - SPR.ox;
        run = SPR.rows[y];
        for (i = 0; i < run.length; i++) {
          if (run[i][1]) {
            ctx.fillStyle = css(LIGHT[level * PAL_N + run[i][1]]);
            ctx.fillRect(SX + px, SY + sy - SPR.oy + y, run[i][0], 1);
          }
          px += run[i][0];
        }
      }
      ctx.globalAlpha = 1;
      // 프레임버퍼 — 모드 13h 의 320x200
      ctx.fillStyle = C.black;
      ctx.fillRect(SX, SY, SCR_W, SCR_H);
      for (i = 0; i < res.out.length; i++) {
        ctx.fillStyle = css(res.out[i][3]);
        ctx.fillRect(SX + res.out[i][0], SY + res.out[i][1], res.out[i][2], 1);
      }
      if (checked(cRuns, false)) {
        ctx.fillStyle = C.line;
        for (i = 0; i < res.out.length; i++) {
          ctx.fillRect(SX + res.out[i][0], SY + res.out[i][1], 1, 1);
          ctx.fillRect(SX + res.out[i][0] + res.out[i][2] - 1, SY + res.out[i][1], 1, 1);
        }
      }
      ctx.strokeStyle = C.stroke;
      ctx.lineWidth = 1.5;
      ctx.strokeRect(SX - 0.5, SY - 0.5, SCR_W + 1, SCR_H + 1);
      ctx.font = '10px system-ui, sans-serif';
      ctx.fillStyle = C.muted;
      ctx.fillText('320 × 200 (모드 13h)', SX, SY - 6);
      ctx.fillText('바깥의 흐린 부분이 잘려 나간 픽셀', SX, SY + SCR_H + 14);

      put(host, api, [
        '스프라이트 ' + SPR.w + '×' + SPR.h + ' · 런 ' + SPR.runs + '개 (불투명 ' + SPR.opaque + ')',
        '기준점 (' + sx + ', ' + sy + ') → 왼쪽 위 (' + (sx - SPR.ox) + ', ' + (sy - SPR.oy) + ')',
        '그린 행 ' + span('ok', res.rows + '/' + SPR.h) + ' · 건너뛴 행 '
          + span(res.skipped ? 'bad' : 'dim', String(res.skipped))
          + ' · 그린 런 ' + res.drawn + ' · 잘린 런 '
          + span(res.clipped ? 'bad' : 'dim', String(res.clipped)),
        '그린 픽셀 ' + span('ok', comma(res.pixels) + '개'),
        '명암 ' + level + ' — LIGHT[' + level + '][c] 조회 한 번'
          + (level === 15 ? (IDENT ? span('ok', ' · 15단계는 항등이다') : '') : ''),
        span('dim', '픽셀마다 화면 안인지 묻지 않는다. 행은 통째로 건너뛰고 런은 [a,b) 로 자른다.')
      ]);
    }
    st.draw = draw;
    on(eLight, 'input', draw);
    on(eLight, 'change', draw);
    on(cRuns, 'change', draw);
    function setPos(p) {
      sx = Math.round(p.x - SX);
      sy = Math.round(p.y - SY);
      draw();
    }
    bindPointer(st, { down: setPos, move: setPos });
    draw();
  });

  /* ============================================================
     9부 — 다이아몬드-스퀘어
     ============================================================ */
  window.__demo('diamond-square', function (host, api) {
    var LW = 300, LH = 300, CS = 6, PAD = 6;
    var st = stage(host, LW, LH), ctx = st.ctx;
    var eSeed = q(host, '[data-seed]'), eRough = q(host, '[data-rough]');
    var eBlur = q(host, '[data-blur]'), bRun = q(host, '[data-run]'), cTer = q(host, '[data-terrain]');
    var cache = null;

    function build() {
      var seed = Math.round(numOf(eSeed, 1, 1, 9999));
      var rough = Math.round(numOf(eRough, 58, 30, 80));
      var blur = Math.round(numOf(eBlur, 2, 0, 4));
      var hg = smooth(genHeight(DS_N, DS_CORNER, DS_SCALE, seed, rough, 100), blur);
      var cells = cellsFrom(hg, true);
      var lo = 1e9, hi = -1e9, tx, ty, v;
      for (ty = 0; ty < MAP_H; ty++) {
        for (tx = 0; tx < MAP_W; tx++) {
          v = hg[ty + DS_OFF][tx + DS_OFF];
          if (v < lo) lo = v;
          if (v > hi) hi = v;
        }
      }
      cache = { cells: cells, hg: hg, seed: seed, rough: rough, blur: blur,
                lo: lo, hi: hi, runs: runCount(cells) };
    }

    function draw() {
      if (!cache) build();
      var cells = cache.cells, tx, ty, v, g;
      st.begin();
      for (ty = 0; ty < MAP_H; ty++) {
        for (tx = 0; tx < MAP_W; tx++) {
          if (checked(cTer, true)) {
            ctx.fillStyle = TER_COL[terrainAt(cells, tx, ty)];
          } else {
            v = cache.hg[ty + DS_OFF][tx + DS_OFF];
            g = fdiv(v * 255, 1023);
            ctx.fillStyle = 'rgb(' + g + ',' + g + ',' + g + ')';
          }
          ctx.fillRect(PAD + tx * CS, PAD + ty * CS, CS, CS);
        }
      }
      ctx.strokeStyle = C.stroke;
      ctx.lineWidth = 1;
      ctx.strokeRect(PAD - 0.5, PAD - 0.5, MAP_W * CS + 1, MAP_H * CS + 1);
      ctx.font = '9px system-ui, sans-serif';
      ctx.fillStyle = C.muted;
      ctx.fillText('65×65 격자에서 가운데 48×48 을 오려 냈다', PAD, LH - 3);

      var lines = [];
      lines.push('씨앗 ' + cache.seed + ' · 거칠기 ' + cache.rough + '/100 · 평활 ' + cache.blur + '회');
      lines.push('높이값 ' + cache.lo + ' .. ' + cache.hi + ' (0..1023 으로 자른 뒤)');
      lines.push('RLE 런 ' + span('ok', comma(cache.runs) + '개')
                 + ' — 2,304칸, 평균 런 길이 ' + fmt(2304 / cache.runs, 1));
      if (cache.seed === 1 && cache.rough === 58 && cache.blur === 2) {
        lines.push(span('ok', '이 설정이 golden/map.txt 다 — 런 794개, 값 29..942'));
      }
      lines.push(span('dim', '거칠기가 진폭 감쇠율이다. 100 이면 감쇠가 없어 백색 잡음에 가까워지고,'
                 + ' 평활 0 이면 타일 눈금에서 잡음처럼 보인다.'));
      put(host, api, lines);
    }
    st.draw = draw;
    function regen() { build(); draw(); }
    on(bRun, 'click', regen);
    on(eSeed, 'change', regen);
    on(eRough, 'change', regen);
    on(eRough, 'input', regen);
    on(eBlur, 'change', regen);
    on(eBlur, 'input', regen);
    on(cTer, 'change', draw);
    draw();
  });

  /* ============================================================
     10부 — A* 옥타일
     ============================================================ */
  window.__demo('astar-octile', function (host, api) {
    var LW = 300, LH = 300, CS = 6, PAD = 6;
    var st = stage(host, LW, LH), ctx = st.ctx;
    var cVis = q(host, '[data-visited]'), cDij = q(host, '[data-dij]'), cCut = q(host, '[data-cut]');
    var s = [24, 34], g = [24, 20], grab = 0;    // 골든 시나리오의 플레이어 출발점

    function draw() {
      var cells = goldMap();
      var noCut = checked(cCut, true);
      var res = astar(cells, s[0], s[1], g[0], g[1], noCut);
      var dij = checked(cDij, false) ? dijkstra(cells, s[0], s[1], noCut) : null;
      st.begin();
      var tx, ty, i;
      for (ty = 0; ty < MAP_H; ty++) {
        for (tx = 0; tx < MAP_W; tx++) {
          ctx.fillStyle = TER_COL[terrainAt(cells, tx, ty)];
          ctx.fillRect(PAD + tx * CS, PAD + ty * CS, CS, CS);
          if (!passable(cells, tx, ty)) {
            ctx.fillStyle = 'rgba(42,33,24,.45)';
            ctx.fillRect(PAD + tx * CS, PAD + ty * CS, CS, CS);
          }
        }
      }
      if (dij) {
        ctx.fillStyle = 'rgba(185,203,220,.55)';
        for (i = 0; i < dij.dist.length; i++) {
          if (dij.dist[i] >= 0) {
            ctx.fillRect(PAD + fmod(i, MAP_W) * CS, PAD + fdiv(i, MAP_W) * CS, CS, CS);
          }
        }
      }
      if (checked(cVis, true)) {
        ctx.fillStyle = 'rgba(244,217,138,.8)';
        for (i = 0; i < res.closed.length; i++) {
          if (res.closed[i]) {
            ctx.fillRect(PAD + fmod(i, MAP_W) * CS, PAD + fdiv(i, MAP_W) * CS, CS, CS);
          }
        }
      }
      if (res.path) {
        ctx.strokeStyle = C.line;
        ctx.lineWidth = 2;
        ctx.beginPath();
        for (i = 0; i < res.path.length; i++) {
          var lx = PAD + res.path[i][0] * CS + CS / 2, ly = PAD + res.path[i][1] * CS + CS / 2;
          if (i === 0) ctx.moveTo(lx, ly); else ctx.lineTo(lx, ly);
        }
        ctx.stroke();
      }
      function mark(p, col, label) {
        ctx.fillStyle = col;
        ctx.fillRect(PAD + p[0] * CS - 1, PAD + p[1] * CS - 1, CS + 2, CS + 2);
        ctx.strokeStyle = C.text;
        ctx.lineWidth = 1;
        ctx.strokeRect(PAD + p[0] * CS - 1.5, PAD + p[1] * CS - 1.5, CS + 3, CS + 3);
        ctx.font = 'bold 9px system-ui, sans-serif';
        ctx.fillStyle = C.text;
        ctx.fillText(label, PAD + p[0] * CS + CS + 2, PAD + p[1] * CS + CS);
      }
      mark(s, '#2e7d4f', '출발');
      mark(g, '#b04a2a', '목표');
      ctx.strokeStyle = C.stroke;
      ctx.strokeRect(PAD - 0.5, PAD - 0.5, MAP_W * CS + 1, MAP_H * CS + 1);

      var h = octile(s[0], s[1], g[0], g[1]);
      var lines = [];
      lines.push('출발 (' + s[0] + ', ' + s[1] + ') → 목표 (' + g[0] + ', ' + g[1] + ')'
                 + '   모서리 자르기 ' + (noCut ? '금지' : span('bad', '허용')));
      lines.push('h = 8·max + 3·min = ' + h + (res.cost >= 0
                 ? '   실제 비용 ' + res.cost
                   + (h === res.cost ? span('ok', '  — 휴리스틱이 정확하다') : '') : ''));
      if (res.path) {
        lines.push('A*  경로 ' + res.path.length + '칸 · 비용 ' + res.cost
                   + ' · 본 칸 ' + span('ok', comma(res.expanded) + '개'));
      } else {
        lines.push(span('bad', 'A* 실패 — 갈 수 없는 곳이다 (본 칸 ' + res.expanded + ')'));
      }
      if (dij) {
        lines.push('다익스트라 도달 가능 ' + comma(dij.reach) + '칸 (꺼낸 노드 '
                   + comma(dij.settled) + ')'
                   + (res.expanded ? ' — A* 의 ' + Math.round(dij.reach / res.expanded) + '배' : ''));
      } else {
        lines.push(span('dim', '"다익스트라와 비교"를 켜면 목표를 모르는 쪽이 얼마나 보는지 나온다.'));
      }
      lines.push(span('dim', '출발점이나 목표를 끌어 옮겨 보라. 지형이 섞일수록 A* 가 옆으로 퍼진다.'));
      put(host, api, lines);
    }
    st.draw = draw;
    on(cVis, 'change', draw);
    on(cDij, 'change', draw);
    on(cCut, 'change', draw);
    function cellAt(p) {
      var tx = Math.floor((p.x - PAD) / CS), ty = Math.floor((p.y - PAD) / CS);
      if (tx < 0) tx = 0;
      if (ty < 0) ty = 0;
      if (tx > MAP_W - 1) tx = MAP_W - 1;
      if (ty > MAP_H - 1) ty = MAP_H - 1;
      return [tx, ty];
    }
    bindPointer(st, {
      down: function (p) {
        var c = cellAt(p);
        var ds = (c[0] - s[0]) * (c[0] - s[0]) + (c[1] - s[1]) * (c[1] - s[1]);
        var dg = (c[0] - g[0]) * (c[0] - g[0]) + (c[1] - g[1]) * (c[1] - g[1]);
        grab = ds <= dg ? 0 : 1;
        if (passable(goldMap(), c[0], c[1])) {
          if (grab === 0) s = c; else g = c;
          draw();
        }
      },
      move: function (p) {
        var c = cellAt(p);
        if (!passable(goldMap(), c[0], c[1])) return;
        if (grab === 0) s = c; else g = c;
        draw();
      }
    });
    draw();
  });

  /* ============================================================
     11부 — 시야와 안개
     ============================================================ */
  window.__demo('los-fog', function (host, api) {
    var LW = 300, LH = 300, CS = 6, PAD = 6;
    var st = stage(host, LW, LH), ctx = st.ctx;
    var eR = q(host, '[data-r]'), cMem = q(host, '[data-mem]'), cRays = q(host, '[data-rays]');
    var p = [24, 34], bits = new Uint8Array(MAP_W * MAP_H);

    function shade(col, l) {
      // 조명 단계 l/15 로 어둡게. 명암표가 램프 안에서 하는 일을 색으로 흉내낸 것이다.
      var r = parseInt(col.slice(1, 3), 16), g = parseInt(col.slice(3, 5), 16);
      var b = parseInt(col.slice(5, 7), 16);
      return 'rgb(' + fdiv(r * l, 15) + ',' + fdiv(g * l, 15) + ',' + fdiv(b * l, 15) + ')';
    }
    function draw() {
      var cells = goldMap();
      var R = Math.round(numOf(eR, 9, 3, 14));
      if (!checked(cMem, true)) bits = new Uint8Array(MAP_W * MAP_H);
      var st2 = fogUpdate(cells, bits, p[0], p[1], R);
      st.begin();
      var tx, ty, l, i;
      for (ty = 0; ty < MAP_H; ty++) {
        for (tx = 0; tx < MAP_W; tx++) {
          l = lightOf(bits, tx, ty, p[0], p[1], R);
          ctx.fillStyle = l === 0 ? C.black : shade(TER_COL[terrainAt(cells, tx, ty)], l);
          ctx.fillRect(PAD + tx * CS, PAD + ty * CS, CS, CS);
        }
      }
      if (checked(cRays, false)) {
        // 원 둘레 칸까지의 브레젠험 선 — 벽 뒤 그림자가 부채꼴이 아니라 계단이다
        ctx.strokeStyle = 'rgba(244,217,138,.55)';
        ctx.lineWidth = 1;
        for (ty = -R; ty <= R; ty++) {
          for (tx = -R; tx <= R; tx++) {
            var d2 = tx * tx + ty * ty;
            if (d2 > R * R || d2 <= (R - 1) * (R - 1)) continue;
            var pts = bresenham(p[0], p[1], p[0] + tx, p[1] + ty);
            ctx.beginPath();
            for (i = 0; i < pts.length; i++) {
              var lx = PAD + pts[i][0] * CS + CS / 2, ly = PAD + pts[i][1] * CS + CS / 2;
              if (i === 0) ctx.moveTo(lx, ly); else ctx.lineTo(lx, ly);
            }
            ctx.stroke();
          }
        }
      }
      ctx.fillStyle = '#f4d98a';
      ctx.beginPath();
      ctx.arc(PAD + p[0] * CS + CS / 2, PAD + p[1] * CS + CS / 2, 3.5, 0, 6.2832);
      ctx.fill();
      ctx.strokeStyle = C.text;
      ctx.lineWidth = 1;
      ctx.stroke();
      ctx.strokeStyle = C.stroke;
      ctx.strokeRect(PAD - 0.5, PAD - 0.5, MAP_W * CS + 1, MAP_H * CS + 1);

      // 맵 가장자리에서는 훑는 사각형이 잘린다. 잘린 몫까지 원의 공으로 돌리면 거짓말이 된다.
      var sq = st2.square;
      put(host, api, [
        '관찰자 (' + p[0] + ', ' + p[1] + ') · 시야 반경 ' + R
          + ' · 기억 ' + (checked(cMem, true) ? '남김' : span('bad', '안 남김')),
        '검사한 칸 ' + span('ok', st2.checked + '개')
          + ' — 반경 ' + R + ' 정사각형은 ' + sq + '칸이다 ('
          + Math.round(100 - 100 * st2.checked / sq) + '% 절약)',
        '지금 보이는 칸 ' + span('ok', comma(st2.vis) + '개')
          + ' · 본 적 있는 칸 ' + comma(st2.seen) + '개 (맵 2,304칸)',
        '조명 l = 15 − ⌊8·d / (' + R + '·256)⌋ 를 [7,15] 로 자름 · 기억만 있으면 4 고정',
        span('dim', '벽 뒤 그림자가 부채꼴이 아니라 계단이다 — 타일 시야의 특징이다.')
      ]);
    }
    st.draw = draw;
    on(eR, 'input', draw);
    on(eR, 'change', draw);
    on(cMem, 'change', function () {
      if (!checked(cMem, true)) bits = new Uint8Array(MAP_W * MAP_H);
      draw();
    });
    on(cRays, 'change', draw);
    function setP(pt) {
      var tx = Math.floor((pt.x - PAD) / CS), ty = Math.floor((pt.y - PAD) / CS);
      if (tx < 0) tx = 0;
      if (ty < 0) ty = 0;
      if (tx > MAP_W - 1) tx = MAP_W - 1;
      if (ty > MAP_H - 1) ty = MAP_H - 1;
      p = [tx, ty];
      draw();
    }
    bindPointer(st, { down: setP, move: setP });
    draw();
  });

  /* ============================================================
     12부 — 주사위 분포
     ============================================================ */
  window.__demo('dice-dist', function (host, api) {
    var LW = 320, LH = 170;
    var st = stage(host, LW, LH), ctx = st.ctx;
    var eN = q(host, '[data-n]'), eM = q(host, '[data-m]'), cNorm = q(host, '[data-norm]');

    function draw() {
      var n = Math.round(numOf(eN, 2, 1, 8));
      var m = Math.round(numOf(eM, 6, 2, 20));
      var c = diceDist(n, m);
      var lo = n, hi = n * m, i, total = 0, mx = 0, mode = lo;
      for (i = lo; i <= hi; i++) {
        total += c[i];
        if (c[i] > mx) { mx = c[i]; mode = i; }
      }
      var pow = 1;
      for (i = 0; i < n; i++) pow *= m;
      var mean = n * (m + 1) / 2;
      var vari = n * (m * m - 1) / 12;
      var sd = Math.sqrt(vari);

      st.begin();
      var pad = 8, base = LH - 22, gw = LW - pad * 2, gh = base - 16;
      var k = hi - lo + 1;
      var bw = gw / k;
      for (i = lo; i <= hi; i++) {
        var h = c[i] / mx * gh;
        var x = pad + (i - lo) * bw;
        ctx.fillStyle = (i === mode) ? C.hot : C.hi;
        ctx.fillRect(x + 0.5, base - h, bw > 2 ? bw - 1 : bw, h);
        ctx.strokeStyle = 'rgba(138,90,43,.5)';
        ctx.lineWidth = 0.5;
        ctx.strokeRect(x + 0.5, base - h, bw > 2 ? bw - 1 : bw, h);
      }
      if (checked(cNorm, false) && vari > 0) {
        // 정규 근사 — 막대와 같은 축척으로 겹쳐 그린다
        ctx.strokeStyle = C.line;
        ctx.lineWidth = 1.8;
        ctx.beginPath();
        var steps = 160, t;
        for (t = 0; t <= steps; t++) {
          var s = lo + (hi - lo) * t / steps;
          var pdf = Math.exp(-(s - mean) * (s - mean) / (2 * vari)) / Math.sqrt(2 * Math.PI * vari);
          var y = base - pdf * pow / mx * gh;
          var xx = pad + (s - lo + 0.5) * bw;
          if (t === 0) ctx.moveTo(xx, y); else ctx.lineTo(xx, y);
        }
        ctx.stroke();
      }
      ctx.strokeStyle = 'rgba(138,90,43,.5)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(pad, base);
      ctx.lineTo(pad + gw, base);
      ctx.stroke();
      ctx.font = '9px system-ui, sans-serif';
      ctx.fillStyle = C.muted;
      ctx.fillText(String(lo), pad, base + 11);
      ctx.fillText(String(hi), pad + gw - 14, base + 11);
      ctx.fillText(n + 'd' + m + ' — 합성곱으로 센 경우의 수', pad, 12);

      put(host, api, [
        n + 'd' + m + ' · 합 ' + lo + ' .. ' + hi + ' (' + k + '가지)',
        '경우의 수 총합 ' + comma(total) + (total === pow
          ? span('ok', ' = ' + m + '^' + n) : span('bad', ' ≠ ' + m + '^' + n)),
        '최빈값 ' + mode + ' (' + comma(mx) + '가지, ' + fmt(100 * mx / total, 2) + '%)',
        '기대값 ' + fmt(mean, 3) + ' = n(m+1)/2 · 분산 ' + fmt(vari, 3)
          + ' = n(m²−1)/12 · 표준편차 ' + fmt(sd, 3),
        span('dim', '몬테카를로가 아니라 경우의 수다. 그래서 기대값과 분산을 정수 항등식으로'
             + ' 검사할 수 있다.')
      ]);
    }
    st.draw = draw;
    on(eN, 'change', draw);
    on(eN, 'input', draw);
    on(eM, 'change', draw);
    on(eM, 'input', draw);
    on(cNorm, 'change', draw);
    draw();
  });

  /* ============================================================
     12부 — LCG 하위 비트
     ============================================================ */
  window.__demo('lcg-bits', function (host, api) {
    var LW = 320, LH = 200;
    var st = stage(host, LW, LH), ctx = st.ctx;
    var eBit = q(host, '[data-bit]'), eN = q(host, '[data-n]');
    // 주기 관측용 상태열. 씨앗 1 은 골든 맵과 같은 씨앗이다.
    var STATES = (function () {
      var r = new Rng(1), out = [], i;
      for (i = 0; i < 4096; i++) out.push(r.step());
      return out;
    })();
    function bitAt(s, k) {
      // 2^k 로 나눠 홀짝을 본다. >> 는 32비트로 잘려 비트 31 에서 부호가 뒤집힌다.
      return fmod(fdiv(s, Math.pow(2, k)), 2);
    }
    function periodOf(k) {
      var cand, i, ok;
      for (cand = 1; cand <= 2048; cand *= 2) {
        ok = true;
        for (i = 0; i + cand < 4096; i++) {
          if (bitAt(STATES[i], k) !== bitAt(STATES[i + cand], k)) { ok = false; break; }
        }
        if (ok) return cand;
      }
      return -1;
    }

    function draw() {
      var k = Math.round(numOf(eBit, 0, 0, 31));
      var n = Math.round(numOf(eN, 64, 16, 256));
      n = Math.round(n / 16) * 16;
      if (n < 16) n = 16;
      st.begin();
      var cols = 16, rowsN = n / cols;
      var cell = Math.min(fdiv(LW - 24, cols), fdiv(LH - 40, rowsN));
      if (cell < 3) cell = 3;
      var ox = (LW - cols * cell) / 2, oy = 24;
      var i, ones = 0;
      for (i = 0; i < n; i++) {
        var b = bitAt(STATES[i], k);
        ones += b;
        ctx.fillStyle = b ? C.hot : C.cool;
        ctx.fillRect(ox + fmod(i, cols) * cell, oy + fdiv(i, cols) * cell,
                     cell - 1, cell - 1);
      }
      ctx.font = '10px system-ui, sans-serif';
      ctx.fillStyle = C.muted;
      ctx.fillText('비트 ' + k + ' · 상태 ' + n + '개 (왼쪽 위부터 차례대로)', 8, 14);
      ctx.fillStyle = C.hot;
      ctx.fillRect(8, oy + rowsN * cell + 8, 9, 9);
      ctx.fillStyle = C.muted;
      ctx.fillText('1', 21, oy + rowsN * cell + 16);
      ctx.fillStyle = C.cool;
      ctx.fillRect(36, oy + rowsN * cell + 8, 9, 9);
      ctx.fillStyle = C.muted;
      ctx.fillText('0', 49, oy + rowsN * cell + 16);

      var p = periodOf(k), th = Math.pow(2, k + 1);
      var lines = [];
      lines.push('s ← (22695477·s + 1) mod 2³²  ·  씨앗 1  ·  비트 ' + k);
      lines.push('관측 주기 ' + (p > 0 ? span(p <= 64 ? 'bad' : 'ok', comma(p))
                 : span('ok', '4,096 안에서 안 보임'))
                 + '   이론값 2^' + (k + 1) + ' = ' + comma(th));
      lines.push('1 이 나온 비율 ' + fmt(100 * ones / n, 1) + '% (' + ones + '/' + n + ')');
      if (k <= 3) {
        lines.push(span('bad', '주기가 ' + (p > 0 ? p : th) + ' 이다 — 이 비트로 주사위를 굴리면'
                   + ' 같은 무늬가 끝없이 반복된다'));
      } else if (k >= 16 && k <= 30) {
        lines.push(span('ok', '도스 rand() 가 꺼내 쓰던 구간(비트 30..16)이다 — 눈에 띄는 규칙이 없다'));
      }
      lines.push(span('dim', 'Hull–Dobell 세 조건을 만족해 상태 전체의 주기는 2³² 이다.'
                 + ' 그래도 하위 비트는 짧다 — % 2 로 동전을 던지면 안 되는 이유다.'));
      put(host, api, lines);
    }
    st.draw = draw;
    on(eBit, 'input', draw);
    on(eBit, 'change', draw);
    on(eN, 'input', draw);
    on(eN, 'change', draw);
    draw();
  });

})();
