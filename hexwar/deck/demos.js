/* ============================================================
   덱 안에서 도는 데모들 — 본문의 알고리즘을 그대로 옮긴 자바스크립트.
   외부 라이브러리를 쓰지 않고, 좌표·거리·라인·경로는 3·8·9부의 식과 같다.
   ============================================================ */
(function () {
  'use strict';

  /* ---------- 3부의 좌표 함수들 (같은 식) ---------- */
  var DIRS = [[1, 0], [1, -1], [0, -1], [-1, 0], [-1, 1], [0, 1]];
  var DIRN = ['E', 'NE', 'NW', 'W', 'SW', 'SE'];

  function dist(aq, ar, bq, br) {
    var dq = aq - bq, dr = ar - br;
    return (Math.abs(dq) + Math.abs(dr) + Math.abs(dq + dr)) >> 1;
  }
  function axialToOddr(q, r) { return [q + ((r - (r & 1)) >> 1), r]; }
  function oddrToAxial(c, w) { return [c - ((w - (w & 1)) >> 1), w]; }
  function roundDiv(n, d) {
    return n >= 0 ? Math.floor((2 * n + d) / (2 * d)) : -Math.floor((-2 * n + d) / (2 * d));
  }
  function cubeRound(xf, yf, zf, s) {
    var rx = roundDiv(xf, s), ry = roundDiv(yf, s), rz = roundDiv(zf, s);
    var dx = Math.abs(rx * s - xf), dy = Math.abs(ry * s - yf), dz = Math.abs(rz * s - zf);
    if (dx > dy && dx > dz) rx = -ry - rz;
    else if (dy > dz) ry = -rx - rz;
    else rz = -rx - ry;
    return [rx, rz];
  }
  function hexLine(aq, ar, bq, br) {
    var S = 1024, n = dist(aq, ar, bq, br);
    var ax = aq * S + 1, ay = (-aq - ar) * S + 1, az = ar * S - 2;
    var bx = bq * S, by = (-bq - br) * S, bz = br * S;
    if (n === 0) return [cubeRound(ax, ay, az, S)];
    var out = [], i, ti;
    for (i = 0; i <= n; i++) {
      ti = Math.floor(i * S / n);
      out.push(cubeRound(ax + Math.floor((bx - ax) * ti / S),
                         ay + Math.floor((by - ay) * ti / S),
                         az + Math.floor((bz - az) * ti / S), S));
    }
    return out;
  }

  /* ---------- 화면 배치 (4부와 같은 상수, 데모용으로 축소 가능) ---------- */
  function layout(hw, hh, step) {
    return {
      HEX_W: hw, HEX_H: hh, ROW_STEP: step, ODD_SHIFT: hw / 2,
      origin: function (col, row) { return [col * hw + (row & 1) * (hw / 2), row * step]; },
      center: function (col, row) { var o = this.origin(col, row); return [o[0] + hw / 2, o[1] + hh / 2]; }
    };
  }

  function hexPath(ctx, x, y, L) {
    var q = L.HEX_W / 2, e = L.HEX_H / 4;
    ctx.beginPath();
    ctx.moveTo(x + q, y);
    ctx.lineTo(x + L.HEX_W, y + e);
    ctx.lineTo(x + L.HEX_W, y + L.HEX_H - e);
    ctx.lineTo(x + q, y + L.HEX_H);
    ctx.lineTo(x, y + L.HEX_H - e);
    ctx.lineTo(x, y + e);
    ctx.closePath();
  }

  function mkCanvas(host, w, h) {
    var c = document.createElement('canvas');
    c.width = w; c.height = h;
    c.style.width = '100%';
    c.style.maxWidth = w + 'px';
    c.style.height = 'auto';
    c.style.display = 'block';
    c.style.margin = '8px auto';
    c.style.border = '1px solid rgba(74,107,52,.4)';
    c.style.borderRadius = '6px';
    c.style.background = '#f4f6ec';
    c.style.touchAction = 'none';
    host.insertBefore(c, host.querySelector('.out'));
    return c;
  }

  function relPos(c, ev) {
    var r = c.getBoundingClientRect();
    var t = (ev.touches && ev.touches[0]) || ev;
    return [Math.round((t.clientX - r.left) * c.width / r.width),
            Math.round((t.clientY - r.top) * c.height / r.height)];
  }

  /* ============================================================
     1. 좌표계 — 세 표기를 오가며 본다
     ============================================================ */
  window.__demo('coords', function (host, api) {
    var L = layout(46, 46, 34), R = 3;
    var c = mkCanvas(host, 460, 300), ctx = c.getContext('2d');
    var mode = 'axial', hover = null;
    var buttons = host.querySelectorAll('[data-mode]');
    Array.prototype.forEach.call(buttons, function (b) {
      b.onclick = function () { mode = b.getAttribute('data-mode'); draw(); };
    });

    function cells() {
      var out = [], q, r;
      for (r = -R; r <= R; r++) {
        for (q = -R; q <= R; q++) {
          if (Math.abs(q) + Math.abs(r) + Math.abs(q + r) <= 2 * R) out.push([q, r]);
        }
      }
      return out;
    }
    function pos(q, r) {
      return [230 + (q + r / 2) * L.HEX_W - L.HEX_W / 2, 150 + r * L.ROW_STEP - L.HEX_H / 2];
    }
    function draw() {
      ctx.clearRect(0, 0, c.width, c.height);
      ctx.font = '11px system-ui, sans-serif';
      ctx.textAlign = 'center';
      cells().forEach(function (h) {
        var p = pos(h[0], h[1]), d = dist(0, 0, h[0], h[1]);
        hexPath(ctx, p[0], p[1], L);
        ctx.fillStyle = (hover && hover[0] === h[0] && hover[1] === h[1]) ? '#e8a37a'
                      : (d === 0 ? '#f4d98a' : ['#dfe6cd', '#d7e0c2', '#cfd9b7'][d % 3]);
        ctx.fill();
        ctx.strokeStyle = '#4a6b34'; ctx.lineWidth = 1; ctx.stroke();
        var t;
        if (mode === 'axial') t = h[0] + ',' + h[1];
        else if (mode === 'cube') t = h[0] + ',' + (-h[0] - h[1]) + ',' + h[1];
        else { var o = axialToOddr(h[0], h[1]); t = o[0] + ',' + o[1]; }
        ctx.fillStyle = '#23301c';
        ctx.fillText(t, p[0] + L.HEX_W / 2, p[1] + L.HEX_H / 2 + 4);
        if (mode !== 'cube') {
          ctx.fillStyle = '#7a8a6a';
          ctx.font = '9px system-ui, sans-serif';
          ctx.fillText('d=' + d, p[0] + L.HEX_W / 2, p[1] + L.HEX_H / 2 + 15);
          ctx.font = '11px system-ui, sans-serif';
        }
      });
      var label = { axial: '축좌표 (q, r)', cube: '큐브 (x, y, z) — 합이 언제나 0',
                    oddr: 'odd-r 오프셋 (col, row) — 배열 첨자' }[mode];
      api.w(host, label + (hover ? ' · 가리킨 칸 거리 ' + dist(0, 0, hover[0], hover[1]) : ''), 'ok');
    }
    function findHex(mx, my) {
      var best = null, bd = 1e9;
      cells().forEach(function (h) {
        var p = pos(h[0], h[1]);
        var dx = mx - (p[0] + L.HEX_W / 2), dy = my - (p[1] + L.HEX_H / 2);
        var d2 = dx * dx + dy * dy;
        if (d2 < bd) { bd = d2; best = h; }
      });
      return bd < 600 ? best : null;
    }
    c.addEventListener('mousemove', function (e) {
      var p = relPos(c, e); hover = findHex(p[0], p[1]); draw();
    });
    c.addEventListener('mouseleave', function () { hover = null; draw(); });
    draw();
  });

  /* ============================================================
     2. 픽킹 — 벽돌과 마스크가 실제로 하는 일
     ============================================================ */
  window.__demo('pick', function (host, api) {
    var L = layout(64, 64, 48), c = mkCanvas(host, 460, 300), ctx = c.getContext('2d');
    var showBrick = true, showMask = true, mouse = [230, 150];
    var cb = host.querySelector('[data-brick]'), cm = host.querySelector('[data-mask]');
    if (cb) cb.onchange = function () { showBrick = cb.checked; draw(); };
    if (cm) cm.onchange = function () { showMask = cm.checked; draw(); };

    function maskAt(ox, oy) {
      var q = L.HEX_H / 4, half = L.HEX_W / 2;
      if (oy < q && ox < half - 2 * oy) return 1;
      if (oy < q && ox >= half + 2 * oy) return 2;
      return 0;
    }
    function pick(mx, my) {
      var by = Math.floor(my / L.ROW_STEP), oy = my - by * L.ROW_STEP;
      var xx = mx - (by & 1) * L.ODD_SHIFT;
      var bx = Math.floor(xx / L.HEX_W), ox = xx - bx * L.HEX_W;
      var v = maskAt(ox, oy), col, row;
      if (v === 0) { col = bx; row = by; }
      else if (v === 1) { col = bx - 1 + (by & 1); row = by - 1; }
      else { col = bx + (by & 1); row = by - 1; }
      return { col: col, row: row, bx: bx, by: by, ox: ox, oy: oy, v: v };
    }
    function draw() {
      ctx.clearRect(0, 0, c.width, c.height);
      var got = pick(mouse[0], mouse[1]);
      var row, col;
      for (row = -1; row < 8; row++) {
        for (col = -1; col < 9; col++) {
          var o = L.origin(col, row);
          if (o[0] > c.width || o[1] > c.height) continue;
          hexPath(ctx, o[0], o[1], L);
          ctx.fillStyle = (col === got.col && row === got.row) ? '#f4d98a' : '#dfe6cd';
          ctx.fill();
          ctx.strokeStyle = '#4a6b34'; ctx.lineWidth = 1; ctx.stroke();
        }
      }
      if (showMask) {
        var q = L.HEX_H / 4, half = L.HEX_W / 2, oy2;
        ctx.globalAlpha = 0.45;
        for (row = 0; row < 7; row++) {
          for (col = 0; col < 8; col++) {
            var bxp = col * L.HEX_W + (row & 1) * L.ODD_SHIFT, byp = row * L.ROW_STEP;
            for (oy2 = 0; oy2 < q; oy2++) {
              ctx.fillStyle = '#e8a37a';
              ctx.fillRect(bxp, byp + oy2, Math.max(0, half - 2 * oy2), 1);
              ctx.fillStyle = '#8fb0d4';
              ctx.fillRect(bxp + half + 2 * oy2, byp + oy2, Math.max(0, half - 2 * oy2), 1);
            }
          }
        }
        ctx.globalAlpha = 1;
      }
      if (showBrick) {
        ctx.strokeStyle = 'rgba(176,74,42,.75)';
        ctx.setLineDash([4, 3]); ctx.lineWidth = 1;
        for (row = 0; row < 7; row++) {
          for (col = 0; col < 8; col++) {
            ctx.strokeRect(col * L.HEX_W + (row & 1) * L.ODD_SHIFT, row * L.ROW_STEP,
                           L.HEX_W, L.ROW_STEP);
          }
        }
        ctx.setLineDash([]);
      }
      ctx.fillStyle = '#b04a2a';
      ctx.beginPath(); ctx.arc(mouse[0], mouse[1], 4, 0, 6.2832); ctx.fill();
      api.w(host,
        '벽돌 (' + got.bx + ',' + got.by + ') · 벽돌 안 (' + got.ox + ',' + got.oy + ')' +
        ' · 마스크 ' + got.v + ' (' + ['자기 칸', 'NW 이웃', 'NE 이웃'][got.v] + ')' +
        ' → 헥스 (' + got.col + ',' + got.row + ')', 'ok');
    }
    function onMove(e) { mouse = relPos(c, e); draw(); e.preventDefault(); }
    c.addEventListener('mousemove', onMove);
    c.addEventListener('touchmove', onMove, { passive: false });
    draw();
  });

  /* ============================================================
     3. 이동 범위 — 양동이 큐를 직접 돌린다
     ============================================================ */
  window.__demo('reach', function (host, api) {
    var W = 13, H = 9, L = layout(34, 34, 26);
    var c = mkCanvas(host, 460, 260), ctx = c.getContext('2d');
    var TER = [
      { n: '평지', cost: 2, col: '#cfe0c0' },
      { n: '숲', cost: 4, col: '#8fb08f' },
      { n: '언덕', cost: 4, col: '#cbb98a' },
      { n: '산', cost: 6, col: '#b8b8bc' },
      { n: '바다', cost: -1, col: '#7aa0c8' }
    ];
    var cells = new Int8Array(W * H);
    var start = 4 * W + 3, mp = 12, cur = 1, hover = -1;
    var i;
    for (i = 0; i < W * H; i++) cells[i] = ((i * 7) % 11 === 0) ? 1 : 0;

    var slider = host.querySelector('[data-mp]');
    var out2 = host.querySelector('[data-mpval]');
    if (slider) slider.oninput = function () { mp = +slider.value; if (out2) out2.textContent = mp; draw(); };
    Array.prototype.forEach.call(host.querySelectorAll('[data-ter]'), function (b) {
      b.onclick = function () { cur = +b.getAttribute('data-ter'); paintLabel(); };
    });
    function paintLabel() {
      Array.prototype.forEach.call(host.querySelectorAll('[data-ter]'), function (b) {
        b.style.outline = (+b.getAttribute('data-ter') === cur) ? '2px solid #b04a2a' : 'none';
      });
    }
    function nbrs(idx) {
      var row = Math.floor(idx / W), col = idx - row * W, out = [];
      var D = (row & 1) ? [[1, 0], [1, -1], [0, -1], [-1, 0], [0, 1], [1, 1]]
                        : [[1, 0], [0, -1], [-1, -1], [-1, 0], [-1, 1], [0, 1]];
      for (var d = 0; d < 6; d++) {
        var cc = col + D[d][0], rr = row + D[d][1];
        if (cc >= 0 && cc < W && rr >= 0 && rr < H) out.push(rr * W + cc);
      }
      return out;
    }
    function reachable() {
      var best = new Int32Array(W * H).fill(1 << 30), buckets = [], k;
      for (k = 0; k <= mp; k++) buckets.push([]);
      best[start] = 0; buckets[0].push(start);
      var visited = 0;
      for (k = 0; k <= mp; k++) {
        var b = buckets[k];
        for (var bi = 0; bi < b.length; bi++) {
          var curi = b[bi];
          if (best[curi] !== k) continue;
          visited++;
          var ns = nbrs(curi);
          for (var j = 0; j < ns.length; j++) {
            var cst = TER[cells[ns[j]]].cost;
            if (cst < 0) continue;
            var nc = k + cst;
            if (nc <= mp && nc < best[ns[j]]) { best[ns[j]] = nc; buckets[nc].push(ns[j]); }
          }
        }
      }
      return { best: best, visited: visited };
    }
    function draw() {
      ctx.clearRect(0, 0, c.width, c.height);
      var r = reachable(), n = 0;
      ctx.font = '10px system-ui, sans-serif'; ctx.textAlign = 'center';
      for (var idx = 0; idx < W * H; idx++) {
        var row = Math.floor(idx / W), col = idx - row * W, o = L.origin(col, row);
        hexPath(ctx, o[0] + 4, o[1] + 4, L);
        ctx.fillStyle = TER[cells[idx]].col;
        ctx.fill();
        if (r.best[idx] <= mp) {
          n++;
          ctx.fillStyle = 'rgba(244,217,138,.6)'; ctx.fill();
        }
        ctx.strokeStyle = (idx === hover) ? '#b04a2a' : '#4a6b34';
        ctx.lineWidth = (idx === hover) ? 2 : 1; ctx.stroke();
        if (idx === start) {
          ctx.fillStyle = '#1c3f7a';
          ctx.fillRect(o[0] + 4 + 11, o[1] + 4 + 11, 12, 12);
        } else if (r.best[idx] <= mp) {
          ctx.fillStyle = '#3a4a2a';
          ctx.fillText(r.best[idx], o[0] + 4 + 17, o[1] + 4 + 21);
        }
      }
      api.w(host, '이동력 ' + mp + ' · 닿는 칸 ' + n + '개 · 확장한 정점 ' + r.visited +
                  '개 · 지형을 클릭해 칠하고, 파란 칸을 옮기려면 우클릭', 'ok');
    }
    function hit(mx, my) {
      var by = Math.floor((my - 4) / L.ROW_STEP), oy = (my - 4) - by * L.ROW_STEP;
      var xx = (mx - 4) - (by & 1) * L.ODD_SHIFT;
      var bx = Math.floor(xx / L.HEX_W), ox = xx - bx * L.HEX_W;
      var q = L.HEX_H / 4, half = L.HEX_W / 2, v = 0, col, row;
      if (oy < q && ox < half - 2 * oy) v = 1;
      else if (oy < q && ox >= half + 2 * oy) v = 2;
      if (v === 0) { col = bx; row = by; }
      else if (v === 1) { col = bx - 1 + (by & 1); row = by - 1; }
      else { col = bx + (by & 1); row = by - 1; }
      return (col >= 0 && col < W && row >= 0 && row < H) ? row * W + col : -1;
    }
    c.addEventListener('mousemove', function (e) {
      var p = relPos(c, e); var h = hit(p[0], p[1]);
      if (h !== hover) { hover = h; draw(); }
    });
    c.addEventListener('click', function (e) {
      var p = relPos(c, e); var h = hit(p[0], p[1]);
      if (h >= 0) { cells[h] = cur; draw(); }
    });
    c.addEventListener('contextmenu', function (e) {
      var p = relPos(c, e); var h = hit(p[0], p[1]);
      if (h >= 0 && TER[cells[h]].cost > 0) { start = h; draw(); }
      e.preventDefault();
    });
    paintLabel();
    draw();
  });

  /* ============================================================
     4. 시야선 — 라인과 고도 판정
     ============================================================ */
  window.__demo('los', function (host, api) {
    var W = 13, H = 9, L = layout(34, 34, 26);
    var c = mkCanvas(host, 460, 260), ctx = c.getContext('2d');
    var elev = new Int8Array(W * H), block = new Int8Array(W * H);
    var a = 4 * W + 1, b = 4 * W + 11, dragging = null;
    var i;
    for (i = 0; i < W * H; i++) { elev[i] = ((i * 5) % 13 === 0) ? 2 : 0; }
    elev[4 * W + 6] = 3; block[4 * W + 6] = 1;

    function idxAxial(i2) { var row = Math.floor(i2 / W); return oddrToAxial(i2 - row * W, row); }
    function axIdx(q, r) {
      var o = axialToOddr(q, r);
      return (o[0] >= 0 && o[0] < W && o[1] >= 0 && o[1] < H) ? o[1] * W + o[0] : -1;
    }
    function height(i2) { return elev[i2] + (block[i2] ? 1 : 0); }
    function los() {
      var A = idxAxial(a), B = idxAxial(b);
      var n = dist(A[0], A[1], B[0], B[1]);
      var pts = hexLine(A[0], A[1], B[0], B[1]);
      var ha = height(a) + 1, hb = height(b), blockedAt = -1;
      for (var k = 1; k < n; k++) {
        var im = axIdx(pts[k][0], pts[k][1]);
        if (im < 0) { blockedAt = k; break; }
        var hm = height(im), lh = ha * (n - k) + hb * k;
        if (hm * n > lh || (block[im] && hm * n >= lh)) { blockedAt = k; break; }
      }
      return { pts: pts, n: n, blockedAt: blockedAt };
    }
    function draw() {
      ctx.clearRect(0, 0, c.width, c.height);
      var r = los(), onLine = {};
      r.pts.forEach(function (p, k) { var im = axIdx(p[0], p[1]); if (im >= 0) onLine[im] = k; });
      ctx.font = '10px system-ui, sans-serif'; ctx.textAlign = 'center';
      for (var idx = 0; idx < W * H; idx++) {
        var row = Math.floor(idx / W), col = idx - row * W, o = L.origin(col, row);
        hexPath(ctx, o[0] + 4, o[1] + 4, L);
        var e = elev[idx];
        ctx.fillStyle = block[idx] ? '#5f7a4a' : ['#e2e8d4', '#cbd8b8', '#b3c69c', '#9db487'][Math.min(3, e)];
        ctx.fill();
        if (idx in onLine) {
          ctx.fillStyle = (r.blockedAt >= 0 && onLine[idx] >= r.blockedAt)
            ? 'rgba(203,44,44,.45)' : 'rgba(244,217,138,.75)';
          ctx.fill();
        }
        ctx.strokeStyle = '#4a6b34'; ctx.lineWidth = 1; ctx.stroke();
        ctx.fillStyle = '#3a4a2a';
        ctx.fillText(e + (block[idx] ? '*' : ''), o[0] + 4 + 17, o[1] + 4 + 21);
        if (idx === a || idx === b) {
          ctx.fillStyle = idx === a ? '#1c3f7a' : '#8a1c1c';
          ctx.beginPath(); ctx.arc(o[0] + 4 + 17, o[1] + 4 + 17, 7, 0, 6.2832); ctx.fill();
        }
      }
      api.w(host, '거리 ' + r.n + ' · ' +
        (r.blockedAt < 0 ? '보인다' : (r.blockedAt + '번째 칸에서 막힌다')) +
        ' · 칸을 클릭하면 고도가 오르고, 시프트+클릭이면 숲(*)이 된다', r.blockedAt < 0 ? 'ok' : 'bad');
    }
    function hit(mx, my) {
      var by = Math.floor((my - 4) / L.ROW_STEP), oy = (my - 4) - by * L.ROW_STEP;
      var xx = (mx - 4) - (by & 1) * L.ODD_SHIFT;
      var bx = Math.floor(xx / L.HEX_W), ox = xx - bx * L.HEX_W;
      var q = L.HEX_H / 4, half = L.HEX_W / 2, v = 0, col, row;
      if (oy < q && ox < half - 2 * oy) v = 1;
      else if (oy < q && ox >= half + 2 * oy) v = 2;
      if (v === 0) { col = bx; row = by; }
      else if (v === 1) { col = bx - 1 + (by & 1); row = by - 1; }
      else { col = bx + (by & 1); row = by - 1; }
      return (col >= 0 && col < W && row >= 0 && row < H) ? row * W + col : -1;
    }
    c.addEventListener('mousedown', function (e) {
      var p = relPos(c, e), h = hit(p[0], p[1]);
      if (h < 0) return;
      if (h === a) dragging = 'a';
      else if (h === b) dragging = 'b';
      else if (e.shiftKey) { block[h] = block[h] ? 0 : 1; draw(); }
      else { elev[h] = (elev[h] + 1) % 4; draw(); }
    });
    c.addEventListener('mousemove', function (e) {
      if (!dragging) return;
      var p = relPos(c, e), h = hit(p[0], p[1]);
      if (h >= 0) { if (dragging === 'a') a = h; else b = h; draw(); }
    });
    window.addEventListener('mouseup', function () { dragging = null; });
    draw();
  });

  /* ============================================================
     5. 전투 결과표 — 전력 차가 만드는 분포
     ============================================================ */
  window.__demo('crt', function (host, api) {
    var c = mkCanvas(host, 460, 220), ctx = c.getContext('2d');
    var d = 0;
    var s = host.querySelector('[data-diff]'), lab = host.querySelector('[data-diffval]');
    if (s) s.oninput = function () { d = +s.value; if (lab) lab.textContent = (d >= 0 ? '+' : '') + d; draw(); };
    function draw() {
      ctx.clearRect(0, 0, c.width, c.height);
      var cnt = [0, 0, 0, 0], a, b2, sc;
      for (a = 1; a <= 6; a++) {
        for (b2 = 1; b2 <= 6; b2++) {
          sc = d + a + b2 - 7;
          if (sc >= 4) cnt[0]++; else if (sc >= 1) cnt[1]++; else if (sc >= -2) cnt[2]++; else cnt[3]++;
        }
      }
      var names = ['방어측 -3', '방어측 -2 / 공격측 -1', '방어측 -1 / 공격측 -1', '방어측 0 / 공격측 -2'];
      var cols = ['#4a6b34', '#8fb08f', '#cbb98a', '#cb2c2c'];
      ctx.font = '12px system-ui, sans-serif'; ctx.textAlign = 'left';
      for (var i = 0; i < 4; i++) {
        var pct = cnt[i] / 36;
        ctx.fillStyle = cols[i];
        ctx.fillRect(150, 20 + i * 44, Math.round(pct * 280), 26);
        ctx.fillStyle = '#23301c';
        ctx.fillText(names[i], 8, 38 + i * 44);
        ctx.fillText((pct * 100).toFixed(1) + '%', 155 + Math.round(pct * 280), 38 + i * 44);
      }
      var exp = (cnt[0] * 3 + cnt[1] * 2 + cnt[2]) / 36;
      api.w(host, '전력 차 ' + (d >= 0 ? '+' : '') + d +
                  ' · 방어측 기대 손실 ' + exp.toFixed(2) + ' · 2d6 삼각분포', 'ok');
    }
    draw();
  });

  /* ============================================================
     6. 미니 전술 게임 — 본문 규칙의 축소판
     ============================================================ */
  window.__demo('game', function (host, api) {
    var W = 11, H = 8, L = layout(36, 36, 27);
    var c = mkCanvas(host, 440, 250), ctx = c.getContext('2d');
    var TER = [{ n: '평지', c: 2, col: '#cfe0c0', def: 0 },
               { n: '숲', c: 4, col: '#7f9e7f', def: 2 },
               { n: '언덕', c: 4, col: '#cbb98a', def: 1 }];
    var cells = new Int8Array(W * H), units = [], sel = -1, state = 'IDLE', turn = 1, msg = '';
    var seed = 0x1BADB002;
    function rnd() { seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0; return seed; }
    function d6() { return ((rnd() >>> 16) % 6) + 1; }

    function reset() {
      var i;
      for (i = 0; i < W * H; i++) cells[i] = ((i * 7) % 9 === 0) ? 1 : (((i * 5) % 11 === 0) ? 2 : 0);
      units = [
        { s: 0, i: 3 * W + 1, hp: 10, mp: 6, atk: 5, def: 5, alive: true },
        { s: 0, i: 4 * W + 1, hp: 10, mp: 8, atk: 7, def: 5, alive: true },
        { s: 1, i: 3 * W + 9, hp: 10, mp: 6, atk: 5, def: 5, alive: true },
        { s: 1, i: 4 * W + 9, hp: 10, mp: 8, atk: 7, def: 5, alive: true }
      ];
      sel = -1; state = 'IDLE'; turn = 1; seed = 0x1BADB002; msg = '아군(파랑)을 클릭하세요';
      draw();
    }
    function at(i) { for (var k = 0; k < units.length; k++) if (units[k].alive && units[k].i === i) return k; return -1; }
    function nbrs(idx) {
      var row = Math.floor(idx / W), col = idx - row * W, out = [];
      var D = (row & 1) ? [[1, 0], [1, -1], [0, -1], [-1, 0], [0, 1], [1, 1]]
                        : [[1, 0], [0, -1], [-1, -1], [-1, 0], [-1, 1], [0, 1]];
      for (var d = 0; d < 6; d++) {
        var cc = col + D[d][0], rr = row + D[d][1];
        if (cc >= 0 && cc < W && rr >= 0 && rr < H) out.push(rr * W + cc);
      }
      return out;
    }
    function reach(u) {
      var best = new Int32Array(W * H).fill(1 << 30), bk = [], k;
      for (k = 0; k <= u.mp; k++) bk.push([]);
      best[u.i] = 0; bk[0].push(u.i);
      for (k = 0; k <= u.mp; k++) {
        for (var bi = 0; bi < bk[k].length; bi++) {
          var cu = bk[k][bi];
          if (best[cu] !== k) continue;
          var ns = nbrs(cu);
          for (var j = 0; j < ns.length; j++) {
            if (at(ns[j]) >= 0) continue;
            var nc = k + TER[cells[ns[j]]].c;
            if (nc <= u.mp && nc < best[ns[j]]) { best[ns[j]] = nc; bk[nc].push(ns[j]); }
          }
        }
      }
      return best;
    }
    function fight(ai2, di) {
      var A = units[ai2], D = units[di];
      var atk = Math.floor(A.atk * A.hp / 10);
      var dfn = Math.floor(D.def * D.hp / 10) + TER[cells[D.i]].def;
      var roll = d6() + d6(), sc = atk - dfn + roll - 7;
      var dl = sc >= 4 ? 3 : sc >= 1 ? 2 : sc >= -2 ? 1 : 0;
      var al = sc >= 4 ? 0 : sc >= -2 ? 1 : 2;
      D.hp -= dl; A.hp -= al; A.mp = 0;
      if (D.hp <= 0) D.alive = false;
      if (A.hp <= 0) A.alive = false;
      msg = '2d6=' + roll + ' 점수' + (sc >= 0 ? '+' : '') + sc + ' · 피해 ' + dl + '/' + al;
    }
    function aiTurn() {
      for (var k = 0; k < units.length; k++) {
        var u = units[k];
        if (!u.alive || u.s !== 1) continue;
        var target = -1, bd = 1e9, j;
        for (j = 0; j < units.length; j++) {
          if (!units[j].alive || units[j].s !== 1 - u.s) continue;
          var rowa = Math.floor(u.i / W), rowb = Math.floor(units[j].i / W);
          var A = oddrToAxial(u.i - rowa * W, rowa), B = oddrToAxial(units[j].i - rowb * W, rowb);
          var dd = dist(A[0], A[1], B[0], B[1]);
          if (dd < bd) { bd = dd; target = j; }
        }
        if (target < 0) continue;
        if (bd === 1) { fight(k, target); continue; }
        var best = reach(u), goal = -1, gs = 1e9;
        for (var i2 = 0; i2 < W * H; i2++) {
          if (best[i2] > u.mp || at(i2) >= 0) continue;
          var r2 = Math.floor(i2 / W), t2 = Math.floor(units[target].i / W);
          var P = oddrToAxial(i2 - r2 * W, r2), Q = oddrToAxial(units[target].i - t2 * W, t2);
          var key = dist(P[0], P[1], Q[0], Q[1]) * 100 + best[i2];
          if (key < gs) { gs = key; goal = i2; }
        }
        if (goal >= 0) u.i = goal;
        for (j = 0; j < units.length; j++) {
          if (units[j].alive && units[j].s === 0 && nbrs(u.i).indexOf(units[j].i) >= 0) { fight(k, j); break; }
        }
      }
      turn++;
      for (var m = 0; m < units.length; m++) units[m].mp = units[m].atk === 7 ? 8 : 6;
      sel = -1; state = 'IDLE';
    }
    function draw() {
      ctx.clearRect(0, 0, c.width, c.height);
      var best = (sel >= 0) ? reach(units[sel]) : null;
      ctx.font = '10px system-ui, sans-serif'; ctx.textAlign = 'center';
      for (var idx = 0; idx < W * H; idx++) {
        var row = Math.floor(idx / W), col = idx - row * W, o = L.origin(col, row);
        hexPath(ctx, o[0] + 3, o[1] + 3, L);
        ctx.fillStyle = TER[cells[idx]].col; ctx.fill();
        if (best && best[idx] <= units[sel].mp && at(idx) < 0) {
          ctx.fillStyle = 'rgba(244,217,138,.6)'; ctx.fill();
        }
        ctx.strokeStyle = '#4a6b34'; ctx.lineWidth = 1; ctx.stroke();
        var ui = at(idx);
        if (ui >= 0) {
          var u = units[ui];
          ctx.fillStyle = u.s === 0 ? '#1c3f7a' : '#8a1c1c';
          ctx.fillRect(o[0] + 3 + 10, o[1] + 3 + 9, 16, 14);
          if (ui === sel) { ctx.strokeStyle = '#f4d98a'; ctx.lineWidth = 2; ctx.strokeRect(o[0] + 3 + 9, o[1] + 3 + 8, 18, 16); }
          ctx.fillStyle = '#fff';
          ctx.fillText(u.hp, o[0] + 3 + 18, o[1] + 3 + 20);
        }
      }
      var mine = units.filter(function (u) { return u.alive && u.s === 0; }).length;
      var foe = units.filter(function (u) { return u.alive && u.s === 1; }).length;
      var over = (mine === 0) ? ' — 패배' : (foe === 0 ? ' — 승리' : '');
      api.w(host, turn + '턴 · 아군 ' + mine + ' 적군 ' + foe + over + (msg ? ' · ' + msg : ''),
            over === ' — 승리' ? 'ok' : (over ? 'bad' : ''));
    }
    function hit(mx, my) {
      var by = Math.floor((my - 3) / L.ROW_STEP), oy = (my - 3) - by * L.ROW_STEP;
      var xx = (mx - 3) - (by & 1) * L.ODD_SHIFT;
      var bx = Math.floor(xx / L.HEX_W), ox = xx - bx * L.HEX_W;
      var q = L.HEX_H / 4, half = L.HEX_W / 2, v = 0, col, row;
      if (oy < q && ox < half - 2 * oy) v = 1;
      else if (oy < q && ox >= half + 2 * oy) v = 2;
      if (v === 0) { col = bx; row = by; }
      else if (v === 1) { col = bx - 1 + (by & 1); row = by - 1; }
      else { col = bx + (by & 1); row = by - 1; }
      return (col >= 0 && col < W && row >= 0 && row < H) ? row * W + col : -1;
    }
    c.addEventListener('click', function (e) {
      var p = relPos(c, e), h = hit(p[0], p[1]);
      if (h < 0) return;
      var mine = units.filter(function (u) { return u.alive && u.s === 0; }).length;
      var foe = units.filter(function (u) { return u.alive && u.s === 1; }).length;
      if (mine === 0 || foe === 0) { reset(); return; }
      var ui = at(h);
      if (sel >= 0) {
        var u = units[sel];
        if (ui >= 0 && units[ui].s === 1 && nbrs(u.i).indexOf(h) >= 0 && u.mp > 0) {
          fight(sel, ui); sel = -1; draw(); return;
        }
        var best = reach(u);
        if (ui < 0 && best[h] <= u.mp) { u.mp -= best[h]; u.i = h; msg = ''; draw(); return; }
      }
      if (ui >= 0 && units[ui].s === 0) { sel = ui; msg = ''; }
      else sel = -1;
      draw();
    });
    var endBtn = host.querySelector('[data-end]');
    if (endBtn) endBtn.onclick = function () { aiTurn(); draw(); };
    var resetBtn = host.querySelector('[data-reset]');
    if (resetBtn) resetBtn.onclick = reset;
    reset();
  });
})();
