/* ============================================================
   덱의 살아 있는 데모 여덟.

   규칙 하나: **숫자를 내는 계산은 전부 엔진이 한다.** 여기서 하는 일은 슬라이드가
   이미 갖고 있는 입력(data-dx·data-r·data-step…)을 읽어 window.__rts.require() 로
   꺼낸 진짜 모듈에 넘기고, 결과를 캔버스와 글로 옮기는 것뿐이다.
   데모가 제 나름의 A* 를 갖기 시작하면 그것은 덱이 설명하는 엔진이 아니게 되고,
   틀려도 아무도 모른다 — 거짓말하는 데모는 없는 데모보다 나쁘다.

   .out 패널은 두 테마 모두에서 어두운 색(#10222f)이다. 그래서 캔버스는 자기
   배경을 직접 칠하고, 글자 색은 데모 틀의 .ok/.bad/.dim 을 쓴다.
   ============================================================ */
(function () {
  'use strict';

  // ── 공용 ──────────────────────────────────────────────────────────────────
  // 이름 앞의 './' 는 장식이 아니다. 로더는 점으로 시작하지 않는 이름을 노드
  // 내장 모듈로 보고, 엔진에도 'path' 라는 모듈이 있다 — 그냥 'path' 를 부르면
  // 경로탐색이 아니라 경로 스텁이 돌아온다.
  function R(name) {
    if (!window.__rts) throw new Error('엔진 번들(deck/engine.js)이 없습니다');
    return window.__rts.require('./' + name);
  }

  // .out 패널을 비우고 돌려준다. 캔버스를 그 안에 넣으므로 api.w 는 쓰지 않는다.
  function panel(host, api) {
    var o = api && api.out ? api.out(host) : null;
    if (!o) {
      o = document.createElement('div');
      o.className = 'out';
      host.appendChild(o);
    }
    o.innerHTML = '';
    return o;
  }

  function canvas(o, w, h) {
    var cv = document.createElement('canvas');
    cv.width = w;
    cv.height = h;
    cv.style.width = '100%';
    cv.style.maxWidth = w + 'px';
    cv.style.display = 'block';
    cv.style.imageRendering = 'pixelated';
    cv.style.borderRadius = '6px';
    cv.style.touchAction = 'none';
    o.appendChild(cv);
    return cv;
  }

  function textBox(o) {
    var d = document.createElement('div');
    d.style.marginTop = '8px';
    d.style.whiteSpace = 'pre-wrap';
    o.appendChild(d);
    return d;
  }

  // 캔버스 좌표 — CSS 로 늘어난 만큼 되돌린다. 손가락도 마우스와 같은 길로.
  function at(cv, e) {
    var r = cv.getBoundingClientRect();
    var sx = r.width > 0 ? cv.width / r.width : 1;
    var sy = r.height > 0 ? cv.height / r.height : 1;
    return [Math.floor((e.clientX - r.left) * sx),
            Math.floor((e.clientY - r.top) * sy)];
  }

  function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  // 고정폭 글꼴에서 한글·한자는 두 칸을 먹는다. 글자 수로 채우면 표가 어긋난다.
  function width(s) {
    var n = 0;
    for (var i = 0; i < s.length; i += 1) {
      var c = s.charCodeAt(i);
      n += (c >= 0x1100 && c <= 0xD7A3) || (c >= 0x3000 && c <= 0x303F)
        || (c >= 0xFF00 && c <= 0xFF60) ? 2 : 1;
    }
    return n;
  }

  function pad(s, n) {
    var t = String(s);
    while (width(t) < n) t += ' ';
    return t;
  }

  function padL(s, n) {
    var t = String(s);
    while (width(t) < n) t = ' ' + t;
    return t;
  }

  // 어두운 패널 위에서 읽히는 색. 데모끼리 같은 뜻에 같은 색을 쓴다.
  var COL = {
    bg: '#0d1c27', grid: '#24455a', wall: '#16293a', floor: '#2c5670',
    open: '#4aa3d0', closed: '#8f7ad6', path: '#7ee2a8', mark: '#ffd479',
    txt: '#d6e9f5', bad: '#ff9d9d', dim: '#6f93a8', foe: '#e07a5f'
  };

  function clear(g, w, h) {
    g.fillStyle = COL.bg;
    g.fillRect(0, 0, w, h);
  }

  // 정수 값을 읽는다. 빈 칸이나 글자는 0 으로 본다.
  function intOf(el, lo, hi, dflt) {
    if (!el) return dflt;
    var v = Math.round(Number(el.value));
    if (!isFinite(v)) v = dflt;
    if (v < lo) v = lo;
    if (v > hi) v = hi;
    return v;
  }

  function on(el, type, fn) {
    if (el) el.addEventListener(type, fn);
  }

  function checked(el, dflt) {
    return el ? !!el.checked : dflt;
  }

  // 팔레트 번호 → CSS 색. 0…63 을 0…255 로 펴는 것은 엔진의 expand() 다 —
  // 화면 색과 out/frame_*.ppm 의 색이 같은 함수를 지난다.
  function palCss(RS, pal, idx) {
    var c = pal[idx];
    return 'rgb(' + RS.expand(c[0]) + ',' + RS.expand(c[1]) + ','
      + RS.expand(c[2]) + ')';
  }

  // ── 1. 거리 척도 다섯 ─────────────────────────────────────────────────────
  // §2.5 의 다섯 근사를 한 벡터에 동시에 걸고 유클리드와의 편차를 본다.
  // 값은 전부 fixed 모듈이 낸다 — 여기서 다시 유도하지 않는다.
  window.__demo('dist-metrics', function (host, api) {
    var F = R('fixed');
    var ix = host.querySelector('[data-dx]');
    var iy = host.querySelector('[data-dy]');
    var o = panel(host, api);
    var cv = canvas(o, 300, 124);
    var g = cv.getContext('2d');
    var txt = textBox(o);

    // [이름, 원값, 타일 환산]. doct 만 10/14 단위라 10 으로 나눈다.
    function rows(dx, dy) {
      var eu2 = dx * dx + dy * dy;
      return [
        ['d1   맨해튼', F.d1(dx, dy), F.d1(dx, dy)],
        ['dinf 체비셰프', F.dinf(dx, dy), F.dinf(dx, dy)],
        ['d83  3/8 근사', F.d83(dx, dy), F.d83(dx, dy)],
        ['doct 10/14', F.doct(dx, dy), F.doct(dx, dy) / 10],
        ['dab  α·max+β·min', F.dab(dx, dy), F.dab(dx, dy)],
        ['fpSqrt 유클리드', F.fpSqrt(F.fp(eu2)), F.fpSqrt(F.fp(eu2)) / 65536]
      ];
    }

    function bars(rs, eu) {
      clear(g, cv.width, cv.height);
      var mid = 168;
      var px = 5.6;                       // 1 % 당 픽셀 (±25 % 가 화면에 든다)
      g.fillStyle = COL.grid;
      g.fillRect(mid, 0, 1, cv.height);
      g.font = '10px monospace';
      for (var i = 0; i < rs.length; i += 1) {
        var y = 6 + i * 19;
        var dev = eu > 0 ? (rs[i][2] - eu) / eu * 100 : 0;
        var wdt = Math.max(-25, Math.min(25, dev)) * px;
        g.fillStyle = COL.dim;
        g.fillText(rs[i][0].slice(0, 16), 4, y + 11);
        g.fillStyle = dev >= 0 ? COL.open : COL.foe;
        if (wdt >= 0) g.fillRect(mid, y + 3, wdt, 11);
        else g.fillRect(mid + wdt, y + 3, -wdt, 11);
        g.fillStyle = COL.txt;
        g.fillText((dev >= 0 ? '+' : '') + dev.toFixed(1) + '%',
                   mid + (wdt >= 0 ? wdt + 4 : -4 - 40), y + 12);
      }
    }

    function run() {
      var dx = intOf(ix, -40, 40, 12);
      var dy = intOf(iy, -40, 40, 5);
      var eu = Math.sqrt(dx * dx + dy * dy);
      var rs = rows(dx, dy);
      bars(rs, eu);
      var out = [pad('척도', 18) + padL('원값', 8) + padL('타일', 10)
                 + padL('편차', 9)];
      for (var i = 0; i < rs.length; i += 1) {
        var dev = eu > 0 ? (rs[i][2] - eu) / eu * 100 : 0;
        out.push(pad(rs[i][0], 18) + padL(rs[i][1], 8)
                 + padL(rs[i][2].toFixed(3), 10)
                 + padL(eu > 0 ? (dev >= 0 ? '+' : '') + dev.toFixed(2) + '%'
                        : '-', 9));
      }
      out.push(pad('참유클리드', 18) + padL('', 8) + padL(eu.toFixed(3), 10)
               + padL('0%', 9));
      var note = (dx === 0 || dy === 0)
        ? '<span class="ok">축 위에서는 다섯이 모두 같습니다 — 근사할 것이 없습니다.</span>'
        : '<span class="dim">doct 는 10/14 단위라 10 으로 나눠 타일로 옮겼습니다.</span>';
      txt.innerHTML = esc(out.join('\n')) + '\n' + note;
    }

    on(host.querySelector('[data-run]'), 'click', run);
    on(ix, 'input', run);
    on(iy, 'input', run);
    run();
  });

  // ── 2. 원 마스크 ─────────────────────────────────────────────────────────
  // 행 span 원판(엔진이 쓰는 것)과 미드포인트 외곽선(쓰지 않는 것)을 겹쳐 본다.
  window.__demo('circle-mask', function (host, api) {
    var CI = R('circle');
    var ir = host.querySelector('[data-r]');
    var iout = host.querySelector('[data-outline]');
    var o = panel(host, api);
    var cv = canvas(o, 312, 312);
    var g = cv.getContext('2d');
    var txt = textBox(o);

    function run() {
      var r = intOf(ir, 1, 12, 5);
      var n = 2 * r + 1;
      var cell = Math.floor(300 / n);
      var size = cell * n;
      var off = Math.floor((cv.width - size) / 2);
      clear(g, cv.width, cv.height);
      var offs = CI.offsets(r);
      var i;
      // 원판 — 엔진의 시야·스플래시가 정확히 이 칸들이다.
      g.fillStyle = COL.floor;
      for (i = 0; i < offs.length; i += 1) {
        g.fillRect(off + (offs[i][0] + r) * cell + 1,
                   off + (offs[i][1] + r) * cell + 1, cell - 2, cell - 2);
      }
      // 격자
      g.fillStyle = COL.grid;
      for (i = 0; i <= n; i += 1) {
        g.fillRect(off + i * cell, off, 1, size);
        g.fillRect(off, off + i * cell, size, 1);
      }
      var outside = 0;
      if (checked(iout, false)) {
        var pts = CI.midpointOutline(r);
        for (i = 0; i < pts.length; i += 1) {
          var dx = pts[i][0];
          var dy = pts[i][1];
          var bad = !CI.inDisc(dx, dy, r);
          if (bad) outside += 1;
          g.fillStyle = bad ? COL.bad : COL.mark;
          g.fillRect(off + (dx + r) * cell + cell / 2 - 2,
                     off + (dy + r) * cell + cell / 2 - 2, 4, 4);
        }
      }
      var sp = CI.spans(r);
      var lines = ['반경 ' + r + ' · 원판 ' + CI.count(r) + '칸'
                   + '  (πr² ≈ ' + (Math.PI * r * r).toFixed(1) + ')',
                   'spans = [' + sp.join(', ') + ']'];
      if (checked(iout, false)) {
        lines.push('미드포인트 외곽선 ' + CI.midpointOutline(r).length + '점 중 '
                   + outside + '점이 원 **밖**입니다');
        lines.push(outside > 0
                   ? '붉은 점이 그것입니다 — 외곽선을 시야 마스크로 쓰면 안 되는 이유.'
                   : '이 반경에서는 어긋나지 않습니다. r 을 키워 보세요.');
      }
      txt.innerHTML = esc(lines.join('\n'));
    }

    on(ir, 'input', run);
    on(iout, 'change', run);
    run();
  });

  // ── 3. 오토타일 칠하기 ────────────────────────────────────────────────────
  // 진짜 TMap 을 3×3 으로 만들어 놓고 m.mask(1,1) 을 부른다. 마스크 계산도
  // 정규화도 클래스 번호도 tmap 모듈의 것이다 — 여기서 다시 세지 않는다.
  window.__demo('autotile-paint', function (host, api) {
    var T = R('tmap');
    var F = R('fixed');
    var icanon = host.querySelector('[data-canon]');
    var o = panel(host, api);
    var cv = canvas(o, 300, 200);
    var g = cv.getContext('2d');
    var txt = textBox(o);
    var CELL = 60;
    var OX = 60;
    var OY = 10;
    var painted = [1, 1, 0, 1, 0, 0, 0, 1, 0];   // 3×3, 가운데(4)는 언제나 1

    function mapOf() {
      var m = new T.TMap(3, 3);
      for (var y = 0; y < 3; y += 1) {
        for (var x = 0; x < 3; x += 1) {
          var k = y * 3 + x;
          // 칠한 칸 = 가운데와 **같은 지형**. 마스크는 그 동치가 전부다.
          m.setTerrain(x, y, painted[k] === 1 ? T.DIRT : T.SAND);
        }
      }
      return m;
    }

    function bits(v) {
      var s = '';
      for (var d = 7; d >= 0; d -= 1) s += F.bit(v, d);
      return s;
    }

    function draw(mask, cm) {
      clear(g, cv.width, cv.height);
      for (var d = -1; d <= 1; d += 1) {
        for (var e = -1; e <= 1; e += 1) {
          var x = e + 1;
          var y = d + 1;
          var k = y * 3 + x;
          var px = OX + x * CELL;
          var py = OY + y * CELL;
          g.fillStyle = painted[k] === 1 ? COL.floor : COL.wall;
          g.fillRect(px + 2, py + 2, CELL - 4, CELL - 4);
          g.fillStyle = COL.grid;
          g.fillRect(px, py, CELL, 1);
          g.fillRect(px, py, 1, CELL);
          if (k === 4) {                       // 가운데 — 마스크를 재는 칸
            g.strokeStyle = COL.mark;
            g.lineWidth = 2;
            g.strokeRect(px + 3, py + 3, CELL - 6, CELL - 6);
          }
        }
      }
      // 정규화가 떨어뜨린 모서리 비트에 X 를 긋는다.
      var dirs = [[0, -1], [1, -1], [1, 0], [1, 1], [0, 1], [-1, 1], [-1, 0],
                  [-1, -1]];
      g.strokeStyle = COL.bad;
      g.lineWidth = 2;
      for (var i = 0; i < 8; i += 1) {
        if (F.bit(mask, i) === 1 && F.bit(cm, i) === 0) {
          var cx = OX + (dirs[i][0] + 1) * CELL + CELL / 2;
          var cy = OY + (dirs[i][1] + 1) * CELL + CELL / 2;
          g.beginPath();
          g.moveTo(cx - 12, cy - 12);
          g.lineTo(cx + 12, cy + 12);
          g.moveTo(cx + 12, cy - 12);
          g.lineTo(cx - 12, cy + 12);
          g.stroke();
        }
      }
    }

    function run() {
      var m = mapOf();
      var mask = m.mask(1, 1);
      var cm = T.canon(mask);
      draw(mask, cm);
      var lines = ['이웃 마스크        0b' + bits(mask) + '  = ' + mask];
      if (checked(icanon, true)) {
        lines.push('정규화 canon(m)    0b' + bits(cm) + '  = ' + cm);
        lines.push('클래스 번호        ' + T.canonIndex(cm) + ' / '
                   + T.CLASS_COUNT + '  (m.tileIndex(1,1) = '
                   + m.tileIndex(1, 1) + ')');
        lines.push(mask === cm
                   ? '<span class="dim">떨어진 모서리 비트 없음.</span>'
                   : '<span class="ok">양옆 변이 없는 모서리 비트를 지웠습니다'
                     + ' — 붉은 X 자리.</span>');
      } else {
        lines.push('<span class="dim">정규화를 끄면 256가지가 그대로 남습니다.'
                   + ' 그림도 256장이 필요합니다.</span>');
      }
      txt.innerHTML = esc(lines[0]) + '\n'
        + lines.slice(1).map(function (s) {
          return s.indexOf('<span') === 0 ? s : esc(s);
        }).join('\n');
    }

    on(cv, 'click', function (e) {
      var p = at(cv, e);
      var x = Math.floor((p[0] - OX) / CELL);
      var y = Math.floor((p[1] - OY) / CELL);
      if (x < 0 || x > 2 || y < 0 || y > 2) return;
      var k = y * 3 + x;
      if (k === 4) return;                    // 가운데는 늘 칠해져 있다
      painted[k] = painted[k] === 1 ? 0 : 1;
      run();
    });
    on(host.querySelector('[data-clear]'), 'click', function () {
      painted = [0, 0, 0, 0, 1, 0, 0, 0, 0];
      run();
    });
    on(host.querySelector('[data-fill]'), 'click', function () {
      painted = [1, 1, 1, 1, 1, 1, 1, 1, 1];
      run();
    });
    on(icanon, 'change', run);
    run();
  });

  // ── 4. 안개 참조 카운트 ───────────────────────────────────────────────────
  // Fog·World 를 진짜로 만들어 addSight/removeSight 를 걸고, 검증은 엔진의
  // recount() 가 한다. 반경은 §25.1 의 유닛별 시야이므로 종류가 반경을 정한다.
  window.__demo('fog-refcount', function (host, api) {
    var C = R('const');
    var S = R('spatial');
    var FOG = R('fog');
    var LCG = R('rng').LCG;
    var W = 20;
    var H = 14;
    var CELL = 16;
    var ir = host.querySelector('[data-r]');
    var icnt = host.querySelector('[data-count]');
    if (ir) {                    // 반경은 유닛 종류가 정한다 — 3..6 만 있다
      ir.setAttribute('min', '3');
      ir.setAttribute('max', '6');
    }
    // 시야 반경 → 그 반경을 가진 유닛 종류. §25.1 의 SIGHT 표에서 뽑는다.
    var BY_SIGHT = {};
    for (var k = C.KIND_COUNT - 1; k >= 0; k -= 1) {
      if (C.NAME[k] !== '') BY_SIGHT[C.SIGHT[k]] = k;
    }
    var o = panel(host, api);
    var cv = canvas(o, W * CELL, H * CELL);
    var g = cv.getContext('2d');
    var txt = textBox(o);
    var world;
    var fog;
    var units;
    var rng;

    function reset() {
      world = new S.World(W, H);
      fog = new FOG.Fog(W, H, 1);
      units = [];
      rng = new LCG(7);                     // 결정론 — 같은 순서로 늘어난다
      add();
      add();
    }

    function kindNow() {
      var r = intOf(ir, 3, 6, 4);
      return BY_SIGHT[r] !== undefined ? BY_SIGHT[r] : C.INF;
    }

    function add() {
      var kind = kindNow();
      var tx = rng.roll(W);
      var ty = rng.roll(H);
      var h = world.spawn(0, kind, tx, ty);
      if (h === 0) return;
      fog.addSight(0, tx, ty, C.SIGHT[kind]);
      units.push([h, tx, ty, kind]);
    }

    function kill() {
      if (units.length === 0) return;
      var u = units.pop();
      fog.removeSight(0, u[1], u[2], C.SIGHT[u[3]]);
      world.kill(u[0]);
    }

    function draw() {
      clear(g, cv.width, cv.height);
      var shade = ['#0b141b', '#1b3040', '#2b4b60', '#3f7fa0'];
      var x, y, i;
      for (y = 0; y < H; y += 1) {
        for (x = 0; x < W; x += 1) {
          g.fillStyle = shade[fog.level(0, x, y)];
          g.fillRect(x * CELL, y * CELL, CELL - 1, CELL - 1);
        }
      }
      if (checked(icnt, false)) {
        g.font = '9px monospace';
        g.fillStyle = COL.txt;
        for (y = 0; y < H; y += 1) {
          for (x = 0; x < W; x += 1) {
            var c = fog.count[0][y * W + x];
            if (c > 0) g.fillText(String(c), x * CELL + 5, y * CELL + 11);
          }
        }
      }
      for (i = 0; i < units.length; i += 1) {
        g.fillStyle = COL.mark;
        g.fillRect(units[i][1] * CELL + 4, units[i][2] * CELL + 4, 7, 7);
      }
    }

    function run() {
      draw();
      var sum = 0;
      var vis = 0;
      var i;
      for (i = 0; i < W * H; i += 1) {
        sum += fog.count[0][i];
        if (fog.count[0][i] > 0) vis += 1;
      }
      var bad = fog.recount(world);
      var kind = kindNow();
      var lines = ['유닛 ' + units.length + '기 · 가시 ' + vis + '칸 · 참조 합계 '
                   + sum,
                   '다음에 놓을 것: ' + C.NAME[kind] + ' (시야 '
                   + C.SIGHT[kind] + ')  — 반경은 종류가 정합니다'];
      txt.innerHTML = esc(lines.join('\n')) + '\n'
        + (bad === 0
           ? '<span class="ok">recount: 어긋난 칸 0 — 증분 갱신이 새지 않았습니다.</span>'
           : '<span class="bad">recount: 어긋난 칸 ' + bad + ' — 버그입니다.</span>');
    }

    on(host.querySelector('[data-add]'), 'click', function () { add(); run(); });
    on(host.querySelector('[data-kill]'), 'click', function () { kill(); run(); });
    on(ir, 'input', run);
    on(icnt, 'change', run);
    reset();
    run();
  });

  // ── 5. A* 한 걸음씩 ───────────────────────────────────────────────────────
  // 자료구조는 전부 엔진의 것이다 — path.Heap, path.hOct, fixed.DX/DY/DCOST,
  // TMap.passableTerrain. 여기서 하는 일은 while 루프를 사람 손에 맡기는 것뿐이고,
  // 끝까지 돌린 결과가 path.astar() 와 같은지 매번 대조해 보여 준다.
  window.__demo('astar-step', function (host, api) {
    var T = R('tmap');
    var P = R('path');
    var F = R('fixed');
    var D = R('web/data');
    var KIND = 0;                            // 보병 통행
    var m = T.TMap.loadText(D.MAPS_TXT[3]);  // golden/map_4.txt — 방과 문
    var pr = m.pairs[0];
    var src = pr[0];
    var dst = pr[1];
    var ih = host.querySelector('[data-h]');
    var o = panel(host, api);
    var CELL = 9;
    var cv = canvas(o, m.w * CELL, m.h * CELL);
    var g = cv.getContext('2d');
    var txt = textBox(o);
    var st;

    function hOf(x, y) {
      return checked(ih, true) ? P.hOct(x, y, dst[0], dst[1]) : 0;
    }

    function reset() {
      var si = src[1] * m.w + src[0];
      var h0 = hOf(src[0], src[1]);
      st = { dist: new Map(), prev: new Map(), closed: new Set(),
             heap: new P.Heap(), expanded: 0, done: false, cost: -1,
             path: [], si: si, ti: dst[1] * m.w + dst[0] };
      st.dist.set(si, 0);
      st.heap.push(h0, h0, si);
    }

    // 한 걸음 = 닫히지 않은 노드 하나를 꺼내 이웃을 펴는 것. 엔진의 while 몸통과
    // 같은 순서다(닫힌 노드는 세지 않고 건너뛴다 — 재개방은 코드 자체가 없다).
    function step() {
      if (st.done) return;
      var p = -1;
      while (st.heap.length > 0) {
        var top = st.heap.pop()[2];
        if (!st.closed.has(top)) { p = top; break; }
      }
      if (p < 0) { st.done = true; return; }
      st.closed.add(p);
      st.expanded += 1;
      if (p === st.ti) {
        var out = [p];
        while (out[out.length - 1] !== st.si) {
          out.push(st.prev.get(out[out.length - 1]));
        }
        out.reverse();
        st.path = out;
        st.cost = st.dist.get(p);
        st.done = true;
        return;
      }
      var x = F.fmod(p, m.w);
      var y = F.floordiv(p, m.w);
      var dp = st.dist.get(p);
      for (var d = 0; d < 8; d += 1) {
        var u = x + F.DX[d];
        var v = y + F.DY[d];
        if (!m.passableTerrain(u, v, KIND)) continue;
        var j = v * m.w + u;
        var nd = dp + F.DCOST[d];
        var old = st.dist.has(j) ? st.dist.get(j) : P.INF;
        if (nd < old) {
          st.dist.set(j, nd);
          st.prev.set(j, p);
          var hn = hOf(u, v);
          st.heap.push(nd + hn, hn, j);
        }
      }
    }

    function draw() {
      clear(g, cv.width, cv.height);
      var x, y, i;
      for (y = 0; y < m.h; y += 1) {
        for (x = 0; x < m.w; x += 1) {
          var i2 = y * m.w + x;
          var col = m.passableTerrain(x, y, KIND) ? COL.floor : COL.wall;
          if (st.closed.has(i2)) col = COL.closed;
          else if (st.dist.has(i2)) col = COL.open;
          g.fillStyle = col;
          g.fillRect(x * CELL, y * CELL, CELL - 1, CELL - 1);
        }
      }
      for (i = 0; i < st.path.length; i += 1) {
        var q = st.path[i];
        g.fillStyle = COL.path;
        g.fillRect(F.fmod(q, m.w) * CELL + 2, F.floordiv(q, m.w) * CELL + 2,
                   CELL - 5, CELL - 5);
      }
      g.fillStyle = COL.mark;
      g.fillRect(src[0] * CELL, src[1] * CELL, CELL - 1, CELL - 1);
      g.fillStyle = COL.bad;
      g.fillRect(dst[0] * CELL, dst[1] * CELL, CELL - 1, CELL - 1);
    }

    function report() {
      draw();
      var lines = ['맵 golden/map_4.txt(방과 문) · (' + src[0] + ',' + src[1]
                   + ') → (' + dst[0] + ',' + dst[1] + ')',
                   (checked(ih, true) ? '휴리스틱 hOct — A*'
                    : '휴리스틱 0 — 다익스트라')
                   + ' · 닫은 칸 ' + st.expanded + ' · 열린 목록 '
                   + st.heap.length + ' · 손댄 칸 ' + st.dist.size];
      var tail;
      if (!st.done) {
        tail = '<span class="dim">한 걸음씩 눌러 보세요. 보라 = 닫힘, 파랑 = 열림.'
          + '</span>';
      } else if (st.cost < 0) {
        tail = '<span class="bad">도달 불가 — 열린 목록이 비었습니다.</span>';
      } else {
        var ref = P.astar(m, KIND, src, dst);
        var same = ref[0] === st.cost
          && (!checked(ih, true) || ref[2] === st.expanded);
        lines.push('경로 비용 ' + st.cost + ' · ' + st.path.length + '칸');
        tail = same
          ? '<span class="ok">엔진 path.astar() 와 같은 답: 비용 ' + ref[0]
            + ' · 닫은 칸 ' + ref[2] + '</span>'
          : '<span class="dim">엔진 astar 는 비용 ' + ref[0] + ' · 닫은 칸 '
            + ref[2] + ' (휴리스틱을 끄면 닫는 칸이 늘어납니다)</span>';
      }
      txt.innerHTML = esc(lines.join('\n')) + '\n' + tail;
    }

    on(host.querySelector('[data-step]'), 'click', function () {
      step();
      report();
    });
    on(host.querySelector('[data-run]'), 'click', function () {
      var guard = 0;
      while (!st.done && guard < 200000) { step(); guard += 1; }
      report();
    });
    on(host.querySelector('[data-reset]'), 'click', function () {
      reset();
      report();
    });
    on(ih, 'change', function () {           // 알고리즘이 바뀌므로 처음부터
      reset();
      report();
    });
    reset();
    report();
  });

  // ── 6. 기술 트리 ─────────────────────────────────────────────────────────
  // DAG 는 const.PREREQ 그대로다. "무엇이 잠겼는가" 는 econ.canBuild() 가,
  // 순서는 econ.topoOrder() 가 대답한다. 건물은 진짜 Sim 위에 세우고 부순다.
  window.__demo('tech-tree', function (host, api) {
    var C = R('const');
    var E = R('econ');
    var T = R('tmap');
    var SIM = R('sim');
    var D = R('web/data');
    var itopo = host.querySelector('[data-topo]');
    var o = panel(host, api);
    var cv = canvas(o, 320, 240);
    var g = cv.getContext('2d');
    var txt = textBox(o);

    var KINDS = [];
    var k;
    for (k = 0; k < C.KIND_COUNT; k += 1) if (C.NAME[k] !== '') KINDS.push(k);

    // 가장 긴 선행 사슬의 길이 = 그리는 층. PREREQ 가 DAG 이므로 끝난다.
    var LEVEL = {};
    function level(kind) {
      if (LEVEL[kind] !== undefined) return LEVEL[kind];
      var pre = C.PREREQ[kind];
      var best = 0;
      for (var i = 0; i < pre.length; i += 1) {
        var v = level(pre[i]) + 1;
        if (v > best) best = v;
      }
      LEVEL[kind] = best;
      return best;
    }
    for (k = 0; k < KINDS.length; k += 1) level(KINDS[k]);

    var rows = [];
    for (k = 0; k < KINDS.length; k += 1) {
      var lv = LEVEL[KINDS[k]];
      if (!rows[lv]) rows[lv] = [];
      rows[lv].push(KINDS[k]);
    }
    var BOX = {};                            // 종류 → [x, y, w, h]
    var NW = 66;
    var NH = 24;
    for (var r = 0; r < rows.length; r += 1) {
      var row = rows[r];
      var gap = Math.floor((cv.width - 8) / row.length);
      for (var i = 0; i < row.length; i += 1) {
        BOX[row[i]] = [4 + i * gap + Math.floor((gap - NW) / 2),
                       12 + r * 56, NW, NH];
      }
    }

    var sim;
    var handles;

    function reset() {
      var m = T.TMap.loadText(D.MAP_START_TXT);
      sim = new SIM.Sim(m, 1, 2);
      handles = {};
      var bs = [C.HQ, C.POW, C.REF, C.BARR, C.FACT, C.TOWER];
      for (var i = 0; i < bs.length; i += 1) {
        // 자리는 아무래도 좋다 — 이 데모가 묻는 것은 선행이지 배치가 아니다.
        handles[bs[i]] = sim.spawn(0, bs[i], 3 + i * 6, 40);
      }
    }

    function alive(kind) {
      return handles[kind] !== undefined && handles[kind] !== 0
        && sim.w.valid(handles[kind]);
    }

    function toggle(kind) {
      if (C.IS_BUILDING[kind] !== 1) return;
      if (alive(kind)) sim.w.kill(handles[kind]);
      else handles[kind] = sim.spawn(0, kind, 3 + KINDS.indexOf(kind) * 6, 44);
    }

    function draw() {
      clear(g, cv.width, cv.height);
      var i, j;
      g.lineWidth = 1.5;
      for (i = 0; i < KINDS.length; i += 1) {
        var kk = KINDS[i];
        var b = BOX[kk];
        for (j = 0; j < C.PREREQ[kk].length; j += 1) {
          var pb = BOX[C.PREREQ[kk][j]];
          if (!pb) continue;
          g.strokeStyle = alive(C.PREREQ[kk][j]) ? COL.grid : COL.bad;
          g.beginPath();
          g.moveTo(pb[0] + pb[2] / 2, pb[1] + pb[3]);
          g.lineTo(b[0] + b[2] / 2, b[1]);
          g.stroke();
        }
      }
      g.font = '11px monospace';
      g.textAlign = 'center';
      for (i = 0; i < KINDS.length; i += 1) {
        var kd = KINDS[i];
        var bx = BOX[kd];
        var isB = C.IS_BUILDING[kd] === 1;
        var ok = sim.ec.canBuild(sim.w, 0, kd);
        var dead = isB && !alive(kd);
        g.fillStyle = dead ? '#3a1f22' : (ok ? COL.floor : COL.wall);
        g.fillRect(bx[0], bx[1], bx[2], bx[3]);
        g.strokeStyle = dead ? COL.bad : (ok ? COL.path : COL.dim);
        g.strokeRect(bx[0] + 0.5, bx[1] + 0.5, bx[2] - 1, bx[3] - 1);
        g.fillStyle = ok && !dead ? COL.txt : COL.dim;
        g.fillText(C.NAME[kd], bx[0] + bx[2] / 2, bx[1] + 16);
      }
      g.textAlign = 'left';
    }

    function run() {
      draw();
      var locked = [];
      for (var i = 0; i < KINDS.length; i += 1) {
        if (!sim.ec.canBuild(sim.w, 0, KINDS[i])) locked.push(C.NAME[KINDS[i]]);
      }
      var lines = ['건물을 눌러 부수거나 다시 세웁니다. 초록 테두리 = 지금 가능.'];
      if (checked(itopo, false)) {
        var topo = E.topoOrder();
        var names = [];
        for (var t = 0; t < topo.length; t += 1) {
          if (C.NAME[topo[t]] !== '') names.push(C.NAME[topo[t]]);
        }
        lines.push('위상 정렬(번호 오름차순 타이브레이크): ' + names.join(' → '));
      }
      txt.innerHTML = esc(lines.join('\n')) + '\n'
        + (locked.length === 0
           ? '<span class="ok">잠긴 것 없음 — 선행이 모두 살아 있습니다.</span>'
           : '<span class="bad">잠김 ' + locked.length + '종: '
             + esc(locked.join(', ')) + '</span>');
    }

    on(cv, 'click', function (e) {
      var p = at(cv, e);
      for (var i = 0; i < KINDS.length; i += 1) {
        var b = BOX[KINDS[i]];
        if (p[0] >= b[0] && p[0] < b[0] + b[2] && p[1] >= b[1]
            && p[1] < b[1] + b[3]) {
          toggle(KINDS[i]);
          run();
          return;
        }
      }
    });
    on(host.querySelector('[data-reset]'), 'click', function () {
      reset();
      run();
    });
    on(itopo, 'change', run);
    reset();
    run();
  });

  // ── 7. 두 시뮬 나란히 ─────────────────────────────────────────────────────
  // 같은 명령을 서로 다른 지연·지터로 받는 두 기계. net.Net 이 도착 시각을 흔들고,
  // **실행 틱은 흔들지 않는다**(§19.2). 그래서 해시 띠는 초록으로 남는다.
  // float bug 를 켜면 곱셈 한 줄이 실수가 되고, 그때 몇 틱에 갈리는지 보인다.
  window.__demo('lockstep-two-sims', function (host, api) {
    var C = R('const');
    var T = R('tmap');
    var SIM = R('sim');
    var NET = R('net');
    var RS = R('raster');
    var RD = R('render');
    var CV = R('web/canvas');
    var D = R('web/data');
    var TICKS = 240;
    var PER = 4;                             // 한 프레임에 도는 틱 수
    var ilat = host.querySelector('[data-lat]');
    var ijit = host.querySelector('[data-jit]');
    var ibug = host.querySelector('[data-bug]');
    var o = panel(host, api);
    var pair = document.createElement('div');
    pair.style.display = 'flex';
    pair.style.flexWrap = 'wrap';
    pair.style.gap = '6px';
    o.appendChild(pair);
    var sa = new CV.Screen(1);
    var sb = new CV.Screen(1);
    sa.canvas.style.flex = '1 1 240px';
    sb.canvas.style.flex = '1 1 240px';
    pair.appendChild(sa.canvas);
    pair.appendChild(sb.canvas);
    var strip = canvas(o, TICKS, 20);
    var sg = strip.getContext('2d');
    var txt = textBox(o);
    var pal = RS.buildPalette();
    var light = RS.buildLight(pal);
    var fbA = new RS.Frame();
    var fbB = new RS.Frame();
    var sc = SIM.parseScript(D.SCRIPT_TXT);
    var st = null;
    var raf = 0;

    function mkSim(bug) {
      var m = T.TMap.loadText(D.MAP_START_TXT);
      var s = new SIM.Sim(m, 1, sc.players, bug);
      s.setupStart(false);
      var v = new RD.View();
      v.centerOn(m, m.starts[0][0], m.starts[0][1]);
      return { sim: s, view: v };
    }

    function start() {
      if (raf !== 0) { cancelAnimationFrame(raf); raf = 0; }
      var lat = intOf(ilat, 0, 6, 2);
      var jit = intOf(ijit, 0, 4, 0);
      var bug = checked(ibug, false);
      st = { a: mkSim(false), b: mkSim(bug), t: 0, diff: -1, dtile: -1,
             bug: bug, lat: lat, jit: jit, waitA: 0, waitB: 0,
             // 지터 씨앗이 서로 다르다 — 두 기계의 회선 사정은 같지 않다.
             na: new NET.Net(2, lat, 12345, jit),
             nb: new NET.Net(2, lat, 999, jit),
             marks: new Uint8Array(TICKS) };
      draw(true);
      raf = requestAnimationFrame(chunk);
    }

    function one() {
      var t = st.t + 1;
      st.t = t;
      // 명령은 t 틱에 사람의 기계(A)에서 나온다. 두 기계가 같은 것을 받는다.
      var os = st.a.sim.scriptOrders(sc, t);
      for (var i = 0; i < os.length; i += 1) {
        st.na.send(t, os[i][0], os[i]);
        st.nb.send(t, os[i][0], os[i]);
      }
      for (var p = 0; p < 2; p += 1) {
        st.na.flush(t, p);
        st.nb.flush(t, p);
      }
      // 벽시계 t 에 이 틱 몫이 다 왔는가. 안 왔으면 그 기계는 기다린다 —
      // 기다릴 뿐, 앞당겨 실행하는 경로는 없다.
      if (t > st.lat && !st.na.ready(t, t)) st.waitA += 1;
      if (t > st.lat && !st.nb.ready(t, t)) st.waitB += 1;
      var ha = st.a.sim.step(st.na.take(t));
      var hb = st.b.sim.step(st.nb.take(t));
      st.marks[t - 1] = ha === hb ? 1 : 2;
      if (ha !== hb && st.diff < 0) st.diff = t;
      // 해시가 갈린 것과 **화면이 갈린 것**은 다르다. 타일 좌표가 같으면
      // 사람 눈에는 같은 게임으로 보인다 — 그 틈이 §19.4 의 요점이다.
      if (st.dtile < 0) {
        var wa = st.a.sim.w;
        var wb = st.b.sim.w;
        for (var i = 1; i < C.MAX_ENT; i += 1) {
          if (wa.alive[i] !== wb.alive[i] || wa.tx[i] !== wb.tx[i]
              || wa.ty[i] !== wb.ty[i]) { st.dtile = t; break; }
        }
      }
    }

    function drawStrip() {
      sg.fillStyle = COL.bg;
      sg.fillRect(0, 0, strip.width, strip.height);
      for (var i = 0; i < TICKS; i += 1) {
        var v = st.marks[i];
        if (v === 0) continue;
        sg.fillStyle = v === 1 ? COL.path : COL.bad;
        sg.fillRect(i, 2, 1, 16);
      }
    }

    function draw(full) {
      if (full) {
        RD.draw(fbA.fb, st.a.sim, st.a.view, 0, pal, light, 0, [], 'A LOCAL');
        RD.draw(fbB.fb, st.b.sim, st.b.view, 0, pal, light, 0, [], 'B REMOTE');
        sa.paint(fbA.fb);
        sb.paint(fbB.fb);
      }
      drawStrip();
      var lines = ['지연 ' + st.lat + '틱 · 지터 ' + st.jit + '틱 · '
                   + st.t + '/' + TICKS + '틱',
                   '늦게 닿아 기다린 틱: A ' + st.waitA + ' · B ' + st.waitB
                   + '  (실행 틱은 보낼 때 고정 — 기다릴 뿐입니다)'];
      var tail;
      if (st.diff >= 0) {
        tail = '<span class="bad">해시가 ' + st.diff + '틱에서 갈렸습니다'
          + (st.bug ? ' — float bug 가 켜져 있습니다.'
             : ' — 이것은 버그입니다.') + '</span>'
          + '\n<span class="dim">타일 좌표가 갈린 틱: '
          + (st.dtile < 0 ? '없음 — ' + st.t + '틱 동안 화면에서는 같아'
             + ' 보였습니다' : String(st.dtile)) + '</span>';
      } else if (st.t >= TICKS) {
        tail = '<span class="ok">' + TICKS + '틱 내내 두 해시가 같습니다.'
          + (st.jit > 0 ? ' 지터는 도착만 늦췄습니다.' : '') + '</span>';
      } else {
        tail = '<span class="dim">도는 중…</span>';
      }
      txt.innerHTML = esc(lines.join('\n')) + '\n' + tail;
    }

    function chunk() {
      var n = 0;
      while (n < PER && st.t < TICKS) { one(); n += 1; }
      var done = st.t >= TICKS;
      draw(done || st.t % (PER * 4) < PER);
      if (done) { raf = 0; return; }
      raf = requestAnimationFrame(chunk);
    }

    on(host.querySelector('[data-run]'), 'click', start);
    on(ilat, 'change', start);
    on(ijit, 'change', start);
    on(ibug, 'change', start);
    st = { a: mkSim(false), b: mkSim(false), t: 0, diff: -1, dtile: -1,
           bug: false, lat: intOf(ilat, 0, 6, 2), jit: intOf(ijit, 0, 4, 0),
           waitA: 0, waitB: 0, na: new NET.Net(2, 2, 1, 0),
           nb: new NET.Net(2, 2, 2, 0), marks: new Uint8Array(TICKS) };
    draw(true);
    txt.innerHTML = '<span class="dim">돌리기를 누르면 두 시뮬이 '
      + TICKS + '틱을 함께 돕니다.</span>';
  });

  // ── 8. 미니맵 축소 ────────────────────────────────────────────────────────
  // 64칸 미니맵에 128·256 맵을 넣으면 무엇이 사라지는가. 두 표본화 방법은
  // render.minimapNearest / minimapMajority 다 — 여기서 다시 세지 않는다.
  window.__demo('minimap-scale', function (host, api) {
    var T = R('tmap');
    var RS = R('raster');
    var RD = R('render');
    var MG = R('mapgen');
    var LCG = R('rng').LCG;
    var isize = host.querySelector('[data-size]');
    var imaj = host.querySelector('[data-major]');
    var o = panel(host, api);
    var cv = canvas(o, 320, 150);
    var g = cv.getContext('2d');
    var txt = textBox(o);
    var pal = RS.buildPalette();
    var cache = {};

    // 크기만 다르고 모양은 같은 맵을 만든다 — 축소 손실만 남기기 위해서다.
    function mapOf(n) {
      if (cache[n]) return cache[n];
      var m = new T.TMap(n, n);
      var rock = MG.cellular(n, n, new LCG(3), 4, 45);
      var ore = new LCG(11);
      for (var y = 0; y < n; y += 1) {
        for (var x = 0; x < n; x += 1) {
          var t = T.SAND;
          if (rock[y * n + x] === 1) t = T.ROCK;
          else if (y * 8 > n * 7) t = T.WATER;
          else if (ore.roll(100) < 3) t = T.ORE;
          else if (x * 3 > n * 2) t = T.DIRT;
          m.setTerrain(x, y, t);
        }
      }
      cache[n] = m;
      return m;
    }

    // 슬라이드 제목이 "128 맵을 64 픽셀에" 다. 64 로 열면 1:1 이라 볼 것이 없다.
    if (isize && (isize.value === '' || isize.value === '64')) isize.value = '128';

    function run() {
      var n = isize ? Math.round(Number(isize.value) || 128) : 128;
      var m = mapOf(n);
      var major = checked(imaj, false);
      clear(g, cv.width, cv.height);
      var x, y;
      // 왼쪽 — 원본 맵 전체를 128칸 상자에 눌러 넣는다(그림용 축소).
      var s = 128 / n;
      for (y = 0; y < n; y += 1) {
        for (x = 0; x < n; x += 1) {
          g.fillStyle = palCss(RS, pal, T.MINI_COLOR[m.terrain[y * n + x]]);
          g.fillRect(6 + x * s, 12 + y * s, Math.max(1, s), Math.max(1, s));
        }
      }
      // 오른쪽 — 64×64 미니맵. 엔진이 쓰는 표본화 그대로.
      var diff = 0;
      for (y = 0; y < 64; y += 1) {
        for (x = 0; x < 64; x += 1) {
          var a = RD.minimapNearest(m, x, y);
          var b = RD.minimapMajority(m, x, y);
          if (a !== b) diff += 1;
          g.fillStyle = palCss(RS, pal, T.MINI_COLOR[major ? b : a]);
          g.fillRect(174 + x * 2, 12 + y * 2, 2, 2);
        }
      }
      g.font = '10px monospace';
      g.fillStyle = COL.dim;
      g.fillText('원본 ' + n + '×' + n, 6, 8);
      g.fillText('미니맵 64×64 · ' + (major ? '다수결' : '최근접'), 174, 8);
      txt.innerHTML = esc('맵 ' + n + '×' + n + ' → 미니맵 64×64  (한 픽셀이 '
                          + (n / 64) + '×' + (n / 64) + '칸)') + '\n'
        + (diff === 0
           ? '<span class="ok">두 방법이 같은 그림을 냅니다 — 1:1 이라 고를 것이'
             + ' 없습니다.</span>'
           : '<span class="bad">두 방법이 다른 픽셀 ' + diff + '개 / 4096'
             + ' — 최근접은 광맥 한 칸을 통째로 놓칩니다.</span>');
    }

    on(isize, 'change', run);
    on(imaj, 'change', run);
    run();
  });

  // ── 9. LCG 의 비트 ────────────────────────────────────────────────────────
  // 하위 비트의 주기가 짧다는 것을 눈으로. 상태는 rng.LCG 의 것이고, 비트를
  // 꺼내는 것도 fixed.bit 다 — 비트 연산자는 이 엔진에 없다(§1.1).
  window.__demo('lcg-bits', function (host, api) {
    var F = R('fixed');
    var LCG = R('rng').LCG;
    var iseed = host.querySelector('[data-seed]');
    var ibit = host.querySelector('[data-bit]');
    var o = panel(host, api);
    var cv = canvas(o, 288, 60);
    var g = cv.getContext('2d');
    var txt = textBox(o);

    function run() {
      var seed = intOf(iseed, 0, 99999, 1);
      var bit = intOf(ibit, 0, 31, 0);
      var r = new LCG(seed);
      var seq = [];
      var outs = [];
      for (var i = 0; i < 288; i += 1) {
        outs.push(r.next15());
        seq.push(F.bit(r.s, bit));
      }
      clear(g, cv.width, cv.height);
      for (i = 0; i < 288; i += 1) {
        g.fillStyle = seq[i] === 1 ? COL.open : COL.wall;
        g.fillRect(i, 8, 1, 40);
      }
      // 이 비트의 주기 — 앞 192개가 p 만큼 밀어도 같은 최소 p.
      var per = 0;
      for (var p = 1; p <= 64 && per === 0; p += 1) {
        var same = true;
        for (i = 0; i + p < 192; i += 1) {
          if (seq[i] !== seq[i + p]) { same = false; break; }
        }
        if (same) per = p;
      }
      var lines = ['씨앗 ' + seed + ' · 비트 ' + bit
                   + ' (0 = 최하위, 30..16 이 next15 가 쓰는 자리)',
                   'next15() 처음 여덟: ' + outs.slice(0, 8).join(', ')];
      txt.innerHTML = esc(lines.join('\n')) + '\n'
        + (per > 0
           ? '<span class="bad">이 비트의 주기 ' + per + ' — 줄무늬가 보입니다.'
             + ' 하위 비트를 그대로 쓰면 안 되는 이유입니다.</span>'
           : '<span class="ok">192개 안에서는 주기가 보이지 않습니다'
             + ' — 상위 비트입니다.</span>');
    }

    on(host.querySelector('[data-run]'), 'click', run);
    on(iseed, 'input', run);
    on(ibit, 'input', run);
    run();
  });

  // ── 10. 세포 자동자 맵 ────────────────────────────────────────────────────
  // mapgen.cellular 를 그대로 부른다. 세대를 늘리면 무엇이 사라지는지는
  // TMap.labels() 가 센 연결 성분 수로 말한다.
  window.__demo('ca-map', function (host, api) {
    var T = R('tmap');
    var MG = R('mapgen');
    var LCG = R('rng').LCG;
    var iseed = host.querySelector('[data-seed]');
    var ifill = host.querySelector('[data-fill]');
    var igen = host.querySelector('[data-gen]');
    var o = panel(host, api);
    var N = 64;
    var CELL = 4;
    var cv = canvas(o, N * CELL, N * CELL);
    var g = cv.getContext('2d');
    var txt = textBox(o);

    function run() {
      var seed = intOf(iseed, 0, 9999, 3);
      var fill = intOf(ifill, 30, 60, 45);
      var gen = intOf(igen, 0, 8, 4);
      var cur = MG.cellular(N, N, new LCG(seed), gen, fill);
      var m = new T.TMap(N, N);
      var rock = 0;
      var x, y;
      for (y = 0; y < N; y += 1) {
        for (x = 0; x < N; x += 1) {
          var isRock = cur[y * N + x] === 1;
          if (isRock) rock += 1;
          m.setTerrain(x, y, isRock ? T.ROCK : T.SAND);
        }
      }
      clear(g, cv.width, cv.height);
      for (y = 0; y < N; y += 1) {
        for (x = 0; x < N; x += 1) {
          g.fillStyle = cur[y * N + x] === 1 ? COL.wall : COL.floor;
          g.fillRect(x * CELL, y * CELL, CELL, CELL);
        }
      }
      // 열린 칸의 연결 성분 — 8방향 유니온–파인드는 엔진이 갖고 있다.
      var lab = m.labels(0);
      var sizes = {};
      var comps = 0;
      var big = 0;
      for (var i = 0; i < N * N; i += 1) {
        if (lab[i] < 0) continue;
        if (sizes[lab[i]] === undefined) { sizes[lab[i]] = 0; comps += 1; }
        sizes[lab[i]] += 1;
        if (sizes[lab[i]] > big) big = sizes[lab[i]];
      }
      var open = N * N - rock;
      var lines = ['씨앗 ' + seed + ' · 채움 ' + fill + '% · 세대 ' + gen,
                   '바위 ' + rock + '칸 (' + (100 * rock / (N * N)).toFixed(1)
                   + '%) · 열린 칸 ' + open,
                   '연결 성분 ' + comps + '개 · 가장 큰 성분 ' + big + '칸 ('
                   + (100 * big / Math.max(1, open)).toFixed(1) + '%)'];
      txt.innerHTML = esc(lines.join('\n')) + '\n'
        + (comps <= 3
           ? '<span class="ok">세대를 돌릴수록 외딴 섬이 사라집니다.</span>'
           : '<span class="dim">세대를 늘려 보세요 — 성분 수가 줄어듭니다.</span>');
    }

    on(iseed, 'input', run);
    on(ifill, 'input', run);
    on(igen, 'input', run);
    run();
  });

  // ── 11. 팔레트 재배치 ─────────────────────────────────────────────────────
  // 스프라이트는 한 벌이고 진영 색만 팔레트 번호로 옮긴다(§22.6). 그리기는
  // raster.blit 이 하고, 화면에 올리는 것은 web/canvas 다 — 미니 RTS 와 같은 길.
  window.__demo('palette-remap', function (host, api) {
    var RS = R('raster');
    var CV = R('web/canvas');
    var iowner = host.querySelector('[data-owner]');
    var idir = host.querySelector('[data-dir]');
    var icycle = host.querySelector('[data-cycle]');
    var o = panel(host, api);
    var screen = new CV.Screen(1);
    o.appendChild(screen.canvas);
    var txt = textBox(o);
    var pal = RS.buildPalette();
    var frame = new RS.Frame();
    var phase = 0;
    var raf = 0;
    var frames = 0;

    function paint() {
      var owner = intOf(iowner, 0, 3, 0);
      var dir = intOf(idir, 0, 7, 0);
      frame.clear(RS.SHADOW);
      var k, i;
      RS.text(frame.fb, 'OWNER ' + owner + '  DIR ' + dir + ' '
              + ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'][dir], 8, 8, 198);
      for (k = 0; k < 5; k += 1) {
        var got = RS.spriteFor(k, dir);
        if (got[0] === null) continue;
        RS.blit(frame.fb, got[0], 40 + k * 52, 60, owner, got[1], null, 3);
        RS.text(frame.fb, RS.UNIT_NAME[k].slice(0, 6), 26 + k * 52, 80, 197);
      }
      // 진영 램프 여덟 칸 — 스프라이트가 실제로 쓰는 번호들이다.
      for (i = 0; i < RS.PLAYER_SHADES; i += 1) {
        frame.rect(40 + i * 16, 106, 15, 14,
                   RS.PLAYER_BASE + owner * RS.PLAYER_SHADES + i);
      }
      RS.text(frame.fb, 'PLAYER RAMP '
              + (RS.PLAYER_BASE + owner * RS.PLAYER_SHADES), 40, 96, 197);
      for (i = 0; i < RS.WATER_N; i += 1) {
        frame.rect(40 + i * 16, 146, 15, 14, RS.WATER_BASE + i);
      }
      RS.text(frame.fb, 'WATER RAMP ' + RS.WATER_BASE, 40, 136, 197);
      screen.setPalette(checked(icycle, false) ? RS.cycleWater(pal, phase) : pal);
      screen.paint(frame.fb);
      var base = RS.PLAYER_BASE + owner * RS.PLAYER_SHADES;
      txt.innerHTML = esc('진영 ' + owner + ' 의 색 번호 ' + base + '…'
                          + (base + RS.PLAYER_SHADES - 1)
                          + ' · 스프라이트는 한 벌입니다')
        + '\n<span class="dim">방향 여덟 중 그린 것은 '
        + RS.DRAWN_DIRS + '개뿐 — 나머지 셋은 좌우 반전입니다'
        + (RS.spriteFor(0, dir)[1] ? ' (지금이 반전)' : '') + '.</span>';
    }

    // 물 색 순환은 팔레트만 바꾼다 — 그림은 그대로다(§22.3). 안 보이는
    // 슬라이드에서는 돌지 않는다. 1MB 문서에서 안 보는 애니메이션은 낭비다.
    function loop() {
      raf = requestAnimationFrame(loop);
      frames += 1;
      if (!checked(icycle, false)) return;
      if (screen.canvas.offsetParent === null) return;
      if (frames % 6 !== 0) return;
      phase = (phase + 1) % RS.WATER_N;
      paint();
    }

    on(iowner, 'input', paint);
    on(idir, 'input', paint);
    on(icycle, 'change', function () {
      phase = 0;
      paint();
    });
    paint();
    raf = requestAnimationFrame(loop);
  });

  // ── 12. 공간 버킷 ────────────────────────────────────────────────────────
  // World.query() 가 후보를 얼마나 줄이는지 센다. 전수 검사와 답이 같은지도
  // 함께 본다 — 줄이기만 하고 답이 달라지면 그것은 최적화가 아니라 버그다.
  window.__demo('spatial-grid', function (host, api) {
    var C = R('const');
    var F = R('fixed');
    var S = R('spatial');
    var LCG = R('rng').LCG;
    var inum = host.querySelector('[data-n]');
    var ir = host.querySelector('[data-r]');
    var o = panel(host, api);
    var N = 64;
    var CELL = 5;
    var cv = canvas(o, N * CELL, N * CELL);
    var g = cv.getContext('2d');
    var txt = textBox(o);
    var qx = 32;
    var qy = 32;

    function run() {
      var n = intOf(inum, 10, 250, 120);
      var r = intOf(ir, 1, 16, 4);
      var w = new S.World(N, N);
      var rand = new LCG(5);
      var i;
      for (i = 0; i < n; i += 1) w.spawn(0, C.INF, rand.roll(N), rand.roll(N));
      var cand = w.query(qx, qy, r);
      // query() 는 답을 이미 걸러서 준다. 아낀 것은 "몇 기를 들여다봤는가" 다 —
      // 겹치는 버킷 안의 것만 본다. 그 수를 여기서 센다(버킷은 공개 필드다).
      var bx0 = F.floordiv(Math.max(0, qx - r), C.BUCKET);
      var bx1 = F.floordiv(Math.min(N - 1, qx + r), C.BUCKET);
      var by0 = F.floordiv(Math.max(0, qy - r), C.BUCKET);
      var by1 = F.floordiv(Math.min(N - 1, qy + r), C.BUCKET);
      var scanned = 0;
      var nbuck = 0;
      for (var by = by0; by <= by1; by += 1) {
        for (var bx = bx0; bx <= bx1; bx += 1) {
          scanned += w.buckets[by * w.bw + bx].length;
          nbuck += 1;
        }
      }
      var hitAll = 0;
      var alive = 0;
      for (i = 1; i < C.MAX_ENT; i += 1) {
        if (w.alive[i] === 0) continue;
        alive += 1;
        if (F.dinf(w.tx[i] - qx, w.ty[i] - qy) <= r) hitAll += 1;
      }
      clear(g, cv.width, cv.height);
      var b = C.BUCKET;
      g.strokeStyle = COL.grid;
      for (i = 0; i <= N; i += b) {
        g.beginPath();
        g.moveTo(i * CELL, 0);
        g.lineTo(i * CELL, N * CELL);
        g.moveTo(0, i * CELL);
        g.lineTo(N * CELL, i * CELL);
        g.stroke();
      }
      g.strokeStyle = COL.mark;
      g.strokeRect((qx - r) * CELL, (qy - r) * CELL, (2 * r + 1) * CELL,
                   (2 * r + 1) * CELL);
      for (i = 1; i < C.MAX_ENT; i += 1) {
        if (w.alive[i] === 0) continue;
        var near = F.dinf(w.tx[i] - qx, w.ty[i] - qy) <= r;
        var inB = F.floordiv(w.tx[i], C.BUCKET) >= bx0
          && F.floordiv(w.tx[i], C.BUCKET) <= bx1
          && F.floordiv(w.ty[i], C.BUCKET) >= by0
          && F.floordiv(w.ty[i], C.BUCKET) <= by1;
        g.fillStyle = near ? COL.path : (inB ? COL.open : COL.dim);
        g.fillRect(w.tx[i] * CELL + 1, w.ty[i] * CELL + 1, CELL - 2, CELL - 2);
      }
      var lines = ['유닛 ' + alive + '기 · 질의 (' + qx + ',' + qy + ') 반경 '
                   + r + ' · 버킷 ' + b + '×' + b,
                   '훑은 버킷 ' + nbuck + '칸 · 들여다본 유닛 ' + scanned + '기 ('
                   + alive + '기 중 '
                   + (100 * scanned / Math.max(1, alive)).toFixed(0)
                   + '%) · 답 ' + cand.length + '기'];
      txt.innerHTML = esc(lines.join('\n')) + '\n'
        + (cand.length === hitAll
           ? '<span class="ok">전수 검사와 같은 답 ' + hitAll
             + '기 — 버킷은 답을 바꾸지 않고 볼 것만 줄입니다. 캔버스를 눌러'
             + ' 질의점을 옮겨 보세요.</span>'
           : '<span class="bad">전수 검사는 ' + hitAll + '기 — 버킷이 놓쳤습니다.'
             + '</span>');
    }

    on(cv, 'click', function (e) {
      var p = at(cv, e);
      qx = Math.max(0, Math.min(N - 1, Math.floor(p[0] / CELL)));
      qy = Math.max(0, Math.min(N - 1, Math.floor(p[1] / CELL)));
      run();
    });
    on(host.querySelector('[data-run]'), 'click', run);
    on(inum, 'input', run);
    on(ir, 'input', run);
    run();
  });

  // ── 13. 상자 선택 ─────────────────────────────────────────────────────────
  // 끌어서 고르는 규칙은 select.boxSelect 의 것이다 — 유닛이 하나라도 있으면
  // 건물은 빠지고, 남의 것은 애초에 후보가 아니며, 상한은 32기다(§12.2).
  window.__demo('box-select', function (host, api) {
    var C = R('const');
    var F = R('fixed');
    var S = R('spatial');
    var SEL = R('select');
    var LCG = R('rng').LCG;
    var imixed = host.querySelector('[data-mixed]');
    var ifoe = host.querySelector('[data-foe]');
    var o = panel(host, api);
    var cv = canvas(o, C.VIEW_W, C.VIEW_H);
    var g = cv.getContext('2d');
    var txt = textBox(o);
    var CAM = [0, 0];
    var w;
    var sel = [];
    var drag = null;
    var cur = null;

    function build() {
      w = new S.World(64, 64);
      var rand = new LCG(9);
      var i;
      for (i = 0; i < 14; i += 1) {
        w.spawn(0, C.INF, 1 + rand.roll(14), 1 + rand.roll(10));
      }
      if (checked(imixed, true)) {
        w.spawn(0, C.HQ, 2, 6);
        w.spawn(0, C.BARR, 11, 2);
      }
      if (checked(ifoe, false)) {
        for (i = 0; i < 6; i += 1) {
          w.spawn(1, C.TANK, 3 + rand.roll(10), 2 + rand.roll(8));
        }
      }
      sel = [];
    }

    function draw() {
      clear(g, cv.width, cv.height);
      var i;
      g.strokeStyle = COL.grid;
      for (i = 0; i <= C.VIEW_W; i += C.TILE) {
        g.beginPath();
        g.moveTo(i, 0);
        g.lineTo(i, C.VIEW_H);
        g.stroke();
      }
      for (i = 0; i <= C.VIEW_H; i += C.TILE) {
        g.beginPath();
        g.moveTo(0, i);
        g.lineTo(C.VIEW_W, i);
        g.stroke();
      }
      var picked = {};
      for (i = 0; i < sel.length; i += 1) picked[S.index(sel[i])] = 1;
      for (i = 1; i < C.MAX_ENT; i += 1) {
        if (w.alive[i] === 0) continue;
        var sz = C.TILE * C.FOOT[w.kind[i]];
        var x = F.fpFloor(w.px[i]) - CAM[0];
        var y = F.fpFloor(w.py[i]) - CAM[1];
        var isB = C.IS_BUILDING[w.kind[i]] === 1;
        g.fillStyle = w.owner[i] !== 0 ? COL.foe : (isB ? COL.closed : COL.floor);
        g.fillRect(x + 2, y + 2, sz - 4, sz - 4);
        if (picked[i]) {
          g.strokeStyle = COL.path;
          g.lineWidth = 2;
          g.strokeRect(x + 1, y + 1, sz - 2, sz - 2);
          g.lineWidth = 1;
        }
      }
      if (drag && cur) {
        g.strokeStyle = COL.mark;
        g.strokeRect(Math.min(drag[0], cur[0]), Math.min(drag[1], cur[1]),
                     Math.abs(cur[0] - drag[0]), Math.abs(cur[1] - drag[1]));
      }
    }

    function report() {
      draw();
      var units = 0;
      var blds = 0;
      for (var i = 0; i < sel.length; i += 1) {
        if (C.IS_BUILDING[w.kind[S.index(sel[i])]] === 1) blds += 1;
        else units += 1;
      }
      var lines = ['끌어서 상자를 그려 보세요 (상한 ' + SEL.SELECT_MAX + '기)',
                   '고른 것 ' + sel.length + '  유닛 ' + units + ' · 건물 '
                   + blds];
      txt.innerHTML = esc(lines.join('\n')) + '\n'
        + (units > 0 && blds > 0
           ? '<span class="bad">유닛과 건물이 섞였습니다 — 규칙 위반입니다.</span>'
           : '<span class="ok">유닛이 하나라도 있으면 건물은 빠집니다.'
             + ' 남의 것은 후보가 아닙니다.</span>');
    }

    on(cv, 'mousedown', function (e) {
      drag = at(cv, e);
      cur = drag;
      report();
    });
    on(cv, 'mousemove', function (e) {
      if (!drag) return;
      cur = at(cv, e);
      draw();
    });
    on(cv, 'mouseup', function (e) {
      if (!drag) return;
      cur = at(cv, e);
      sel = SEL.boxSelect(w, 0, CAM, drag[0], drag[1], cur[0], cur[1]);
      drag = null;
      cur = null;
      report();
    });
    on(cv, 'mouseleave', function () { drag = null; cur = null; draw(); });
    on(host.querySelector('[data-reset]'), 'click', function () {
      build();
      report();
    });
    on(imixed, 'change', function () { build(); report(); });
    on(ifoe, 'change', function () { build(); report(); });
    build();
    report();
  });

  // ── 14. 대형 이동 ─────────────────────────────────────────────────────────
  // move.formation 이 자리를 나눠 주고 move.Movement 가 실제로 걷는다.
  // 여덟 기를 한 점으로 보내면 무엇이 일어나는지는 엔진이 대답한다.
  window.__demo('group-move', function (host, api) {
    var C = R('const');
    var F = R('fixed');
    var S = R('spatial');
    var M = R('move');
    var SEL = R('select');
    var SIM = R('sim');
    var T = R('tmap');
    var D = R('web/data');
    var ishape = host.querySelector('[data-shape]');
    var inum = host.querySelector('[data-n]');
    var o = panel(host, api);
    var VIS = 30;
    var CELL = 8;
    var cv = canvas(o, VIS * CELL, VIS * CELL);
    var g = cv.getContext('2d');
    var txt = textBox(o);
    var m = T.TMap.loadText(D.MAP_START_TXT);
    var OX = Math.max(0, m.starts[0][0] - 6);
    var OY = Math.max(0, m.starts[0][1] - 6);
    // 기본 목표는 무리의 **정동쪽**이다. 대각 방향에서는 rot8 의 45° 근사가
    // 슬롯을 겹치게 만드는데(§13.5), 그것은 캔버스를 눌러 직접 보게 한다.
    var GX = OX + 22;
    var GY = OY + 4;
    var sim;
    var w;
    var mv;
    var ids;
    var hnds;
    var slots = [];
    var tick = 0;
    var raf = 0;

    // Sim 을 통째로 만들어 그 안의 Movement 만 돌린다. Sim.spawn 이 hp 와 예약을
    // 함께 세워 주므로 여기서 상태를 손으로 대입할 일이 없다 — 대입하는 순간
    // 이 데모는 엔진이 아니라 흉내가 된다.
    function build() {
      sim = new SIM.Sim(m, 1, 2);
      w = sim.w;
      mv = sim.mv;
      ids = [];
      hnds = [];
      slots = [];
      tick = 0;
      var n = intOf(inum, 1, 24, 8);
      var placed = 0;
      // 두 칸 띄워 세운다. 빽빽하게 세우면 서로 막다가 24틱 만에 전원이 명령을
      // 버린다(§13.3) — 그것도 엔진의 진짜 모습이지만, 대형을 보러 온 자리에서
      // 볼 그림은 아니다.
      for (var k = 0; k < 80 && placed < n; k += 1) {
        var x = OX + 1 + 2 * (k % 5);
        var y = OY + 2 + 2 * Math.floor(k / 5);
        if (!m.passableTerrain(x, y, C.MOVE_KIND[C.INF])) continue;
        var h = sim.spawn(0, C.INF, x, y);
        if (h === 0) continue;
        ids.push(S.index(h));
        hnds.push(h);
        placed += 1;
      }
    }

    function send() {
      var shape = ishape ? Math.round(Number(ishape.value) || 2) : 2;
      var cx = 0;
      var cy = 0;
      var i;
      for (i = 0; i < ids.length; i += 1) {
        cx += w.tx[ids[i]];
        cy += w.ty[ids[i]];
      }
      cx = F.floordiv(cx, Math.max(1, ids.length));
      cy = F.floordiv(cy, Math.max(1, ids.length));
      var d = F.atan8(GX - cx, GY - cy);
      slots = M.formation(ids.length, shape, d, GX, GY, m, C.MOVE_KIND[C.INF]);
      // 명령은 sim.step 을 지난다 — mv.order 를 직접 부르면 state 를 손으로
      // 세워야 하고, 그 순간 이 데모는 엔진 밖의 규칙을 하나 갖게 된다.
      var orders = [];
      for (i = 0; i < hnds.length; i += 1) {
        orders.push([0, hnds[i], SEL.MOVE, slots[i][0], slots[i][1], 0]);
      }
      orders.sort(function (a, b) {
        for (var k = 0; k < a.length; k += 1) {
          if (a[k] !== b[k]) return a[k] < b[k] ? -1 : 1;
        }
        return 0;
      });
      sim.step(orders);
      tick = 1;
      if (raf === 0) raf = requestAnimationFrame(loop);
    }

    function draw() {
      clear(g, cv.width, cv.height);
      var x, y, i;
      for (y = 0; y < VIS; y += 1) {
        for (x = 0; x < VIS; x += 1) {
          var ok = m.passableTerrain(OX + x, OY + y, C.MOVE_KIND[C.INF]);
          g.fillStyle = ok ? COL.floor : COL.wall;
          g.fillRect(x * CELL, y * CELL, CELL - 1, CELL - 1);
        }
      }
      g.fillStyle = COL.bad;
      g.fillRect((GX - OX) * CELL + 2, (GY - OY) * CELL + 2, CELL - 4, CELL - 4);
      for (i = 0; i < slots.length; i += 1) {
        g.strokeStyle = COL.mark;
        g.strokeRect((slots[i][0] - OX) * CELL, (slots[i][1] - OY) * CELL,
                     CELL - 1, CELL - 1);
      }
      for (i = 0; i < ids.length; i += 1) {
        var px = F.fpFloor(w.px[ids[i]]) / C.TILE - OX;
        var py = F.fpFloor(w.py[ids[i]]) / C.TILE - OY;
        g.fillStyle = COL.path;
        g.fillRect(px * CELL + 2, py * CELL + 2, CELL - 4, CELL - 4);
      }
    }

    function report() {
      draw();
      var arrived = 0;
      var seen = {};
      var uniq = 0;
      var i;
      for (i = 0; i < ids.length && i < slots.length; i += 1) {
        if (F.dinf(w.tx[ids[i]] - slots[i][0], w.ty[ids[i]] - slots[i][1])
            <= M.ARRIVE_R) arrived += 1;
        var key = slots[i][0] + ',' + slots[i][1];
        if (!seen[key]) { seen[key] = 1; uniq += 1; }
      }
      var names = ['LINE', 'COLUMN', 'BOX'];
      var shape = ishape ? Math.round(Number(ishape.value) || 2) : 2;
      var gave = 0;
      for (i = 0; i < ids.length && i < slots.length; i += 1) {
        if (mv.path[ids[i]].length === 0
            && F.dinf(w.tx[ids[i]] - slots[i][0], w.ty[ids[i]] - slots[i][1])
               > M.ARRIVE_R) gave += 1;
      }
      var lines = [ids.length + '기 · 대형 ' + names[shape] + ' · 목표 ('
                   + GX + ',' + GY + ') · ' + tick + '틱',
                   '자리에 닿은 유닛 ' + arrived + '/' + ids.length
                   + ' (도착 반경 ' + M.ARRIVE_R + ') · 서로 다른 슬롯 '
                   + uniq + '/' + slots.length];
      var tail;
      if (slots.length === 0) {
        tail = '<span class="dim">캔버스를 눌러 목표를 정하고 보내기를 누르세요.'
          + '</span>';
      } else if (gave > 0) {
        tail = '<span class="dim">' + gave + '기가 명령을 버렸습니다 — '
          + M.GIVEUP_TICKS + '틱 막히면 포기합니다(§13.3). 무리가 빽빽할수록'
          + ' 자주 일어납니다.</span>';
      } else if (uniq < slots.length) {
        tail = '<span class="bad">슬롯이 겹쳤습니다 — 대각 회전은 정수 격자를'
          + ' 보존하지 않습니다(§13.5). 목표를 정동·정남으로 옮기면 사라집니다.'
          + '</span>';
      } else {
        tail = '<span class="ok">한 점이 아니라 자리를 나눠 받습니다 — 그래서'
          + ' 서로 밀지 않습니다.</span>';
      }
      txt.innerHTML = esc(lines.join('\n')) + '\n' + tail;
    }

    function loop() {
      raf = requestAnimationFrame(loop);
      if (tick >= 300) { cancelAnimationFrame(raf); raf = 0; return; }
      for (var k = 0; k < 3 && tick < 300; k += 1) {
        sim.step([]);
        tick += 1;
      }
      report();
    }

    on(cv, 'click', function (e) {
      var p = at(cv, e);
      var gx = OX + Math.floor(p[0] / CELL);
      var gy = OY + Math.floor(p[1] / CELL);
      if (!m.passableTerrain(gx, gy, C.MOVE_KIND[C.INF])) return;
      GX = gx;
      GY = gy;
      report();
    });
    on(host.querySelector('[data-run]'), 'click', send);
    on(host.querySelector('[data-reset]'), 'click', function () {
      if (raf !== 0) { cancelAnimationFrame(raf); raf = 0; }
      build();
      report();
    });
    on(inum, 'input', function () { build(); report(); });
    build();
    report();
  });

  // ── 15. 발사체 ────────────────────────────────────────────────────────────
  // combat.Projectiles 를 그대로 한 발 쏜다. 궤적은 step() 이 낸 좌표를 이어
  // 그린 것이고, 중력 G 도 착탄 판정도 엔진의 것이다(§15.3·§15.4).
  window.__demo('projectile', function (host, api) {
    var F = R('fixed');
    var CB = R('combat');
    var id = host.querySelector('[data-d]');
    var isp = host.querySelector('[data-sp]');
    var iarc = host.querySelector('[data-arc]');
    var o = panel(host, api);
    var cv = canvas(o, 300, 150);
    var g = cv.getContext('2d');
    var txt = textBox(o);

    function run() {
      var d = intOf(id, 16, 240, 96);
      var sp = intOf(isp, 1, 12, 4);
      var arc = checked(iarc, false);
      var pj = new CB.Projectiles(64);
      var y0 = 120;
      var ok = pj.launch(arc ? CB.ARC : CB.STRAIGHT, F.fp(16), F.fp(y0),
                         F.fp(16 + d), F.fp(y0), F.fp(sp), 0, 10);
      var pts = [];
      var t = 0;
      var hit = null;
      while (ok && pj.n() > 0 && t < 900) {
        pts.push([F.fpFloor(pj.x[0]), F.fpFloor(pj.y[0])]);
        var hs = pj.step();
        t += 1;
        if (hs.length > 0) hit = hs[0];
      }
      clear(g, cv.width, cv.height);
      var i;
      var lo = y0;
      var hi = y0;
      for (i = 0; i < pts.length; i += 1) {
        if (pts[i][1] < lo) lo = pts[i][1];
        if (pts[i][1] > hi) hi = pts[i][1];
      }
      var span = Math.max(24, hi - lo);
      var sx = 290 / Math.max(32, 16 + d + 16);
      function cy(v) { return 130 - (y0 - v) * (110 / span); }
      g.fillStyle = COL.grid;
      g.fillRect(0, cy(y0) + 6, cv.width, 1);
      for (i = 0; i < pts.length; i += 1) {
        g.fillStyle = arc ? COL.mark : COL.open;
        g.fillRect(4 + pts[i][0] * sx, cy(pts[i][1]), 2, 2);
      }
      g.fillStyle = COL.path;
      g.fillRect(4 + 16 * sx - 2, cy(y0) - 2, 5, 5);
      g.fillStyle = COL.bad;
      g.fillRect(4 + (16 + d) * sx - 2, cy(y0) - 2, 5, 5);
      var apex = y0 - lo;
      var lines = ['거리 ' + d + 'px · 속도 ' + sp + 'px/틱 · '
                   + (arc ? '포물선(ARC)' : '직선(STRAIGHT)'),
                   '비행 ' + t + '틱' + (arc ? ' · 최고점 ' + apex + 'px' : '')
                   + (hit ? ' · 착탄 타일 ' + hit[2] : ' · 착탄 없음')];
      txt.innerHTML = esc(lines.join('\n')) + '\n'
        + (arc
           ? '<span class="ok">비행 시간은 거리/' + CB.ARC_DIV + ' 과 '
             + CB.ARC_MIN_TICKS + '틱 중 큰 것 — 속도를 올려도 줄지 않습니다.</span>'
           : '<span class="dim">직선은 속도가 비행 시간을 정합니다.'
             + ' 표적을 쫓지 않으므로 빠른 유닛은 피할 수 있습니다.</span>');
    }

    on(host.querySelector('[data-run]'), 'click', run);
    on(id, 'input', run);
    on(isp, 'input', run);
    on(iarc, 'change', run);
    run();
  });

  // ── 16. 란체스터 ─────────────────────────────────────────────────────────
  // combat.lanchesterSim 이 정수 이산으로 돌린다. 축차 투입은 같은 함수를
  // 두 번 부르는 것뿐이다 — 그 차이가 제곱 법칙의 값이다.
  window.__demo('lanchester', function (host, api) {
    var CB = R('combat');
    var ia = host.querySelector('[data-a]');
    var ib = host.querySelector('[data-b]');
    var isplit = host.querySelector('[data-split]');
    var o = panel(host, api);
    var cv = canvas(o, 300, 90);
    var g = cv.getContext('2d');
    var txt = textBox(o);
    var AL = 6554;                          // 0.1 · 16.16 (§15.6 의 기본값)

    function bar(y, label, a, b, mx) {
      g.font = '10px monospace';
      g.fillStyle = COL.dim;
      g.fillText(label, 4, y + 10);
      g.fillStyle = COL.open;
      g.fillRect(86, y, Math.max(1, 200 * a / mx), 12);
      g.fillStyle = COL.foe;
      g.fillRect(86, y + 14, Math.max(1, 200 * b / mx), 12);
      g.fillStyle = COL.txt;
      g.fillText('A ' + a + '  B ' + b, 292 - 76, y + 10);
    }

    function run() {
      var a0 = intOf(ia, 1, 100, 20);
      var b0 = intOf(ib, 1, 100, 10);
      var all = CB.lanchesterSim(a0, b0, AL, AL);
      var half = Math.floor(a0 / 2);
      var p1 = CB.lanchesterSim(half, b0, AL, AL);
      var p2 = CB.lanchesterSim(a0 - half + p1[1], p1[2], AL, AL);
      var mx = Math.max(a0, b0);
      clear(g, cv.width, cv.height);
      bar(6, '한꺼번에', all[1], all[2], mx);
      bar(48, '축차 투입', p2[1], p2[2], mx);
      var lines = ['A ' + a0 + ' vs B ' + b0 + ' · α = β = 0.1',
                   '한꺼번에: ' + all[0] + '틱 → A ' + all[1] + ' · B ' + all[2],
                   '축차 투입(' + half + ' 먼저, 나머지 나중): '
                   + (p1[0] + p2[0]) + '틱 → A ' + p2[1] + ' · B ' + p2[2]];
      var loss = all[1] - p2[1];
      txt.innerHTML = esc(lines.join('\n')) + '\n'
        + (checked(isplit, false)
           ? (loss > 0
              ? '<span class="bad">나눠 넣으면 생존이 ' + loss
                + '기 줄어듭니다 — 제곱 법칙의 대가입니다.</span>'
              : '<span class="dim">이 조합에서는 차이가 나지 않습니다.</span>')
           : '<span class="dim">체크를 켜면 축차 투입의 손해를 읽어 줍니다.'
             + ' 위 두 막대가 그 차이입니다.</span>');
    }

    on(host.querySelector('[data-run]'), 'click', run);
    on(ia, 'input', run);
    on(ib, 'input', run);
    on(isplit, 'change', run);
    run();
  });

  // ── 17. 영향 지도 ─────────────────────────────────────────────────────────
  // 씨앗은 ai.strength 가 매기고, 3회 확산의 정답은 ai.influence 가 낸다.
  // 확산 횟수를 슬라이더로 바꿔 보려면 반복 자체는 여기서 돌 수밖에 없다 —
  // ai.ts 의 spread 는 모듈 밖으로 나오지 않는다. 그래서 3에서는 엔진 결과와
  // 칸 단위로 대조해 보이고, 어긋나면 붉게 적는다.
  window.__demo('influence-map', function (host, api) {
    var C = R('const');
    var F = R('fixed');
    var S = R('spatial');
    var T = R('tmap');
    var AI = R('ai');
    var Fog = R('fog').Fog;
    var LCG = R('rng').LCG;
    var inum = host.querySelector('[data-n]');
    var o = panel(host, api);
    var GW = 32;
    var GH = 22;
    var CELL = 10;
    var cv = canvas(o, GW * CELL, GH * CELL);
    var g = cv.getContext('2d');
    var txt = textBox(o);
    var m;
    var w;
    var fog;
    var rand;

    function reset() {
      m = new T.TMap(GW, GH);
      w = new S.World(GW, GH);
      fog = new Fog(GW, GH, 2);
      rand = new LCG(4);
      // 이 데모는 전장이 다 보인다고 둔다 — 안 그러면 적의 씨앗이 0 이 되고
      // 지도가 내 쪽만 물든다. 한 번의 addSight 로 전체를 밝힌다.
      fog.addSight(0, Math.floor(GW / 2), Math.floor(GH / 2), GW + GH);
    }

    function put(owner, kind) {
      w.spawn(owner, kind, rand.roll(GW), rand.roll(GH));
    }

    // ai.ts 의 spread 와 같은 규칙: 자기 4배 + 이웃 8칸, 12 로 내림 나눗셈.
    function spread(seed, times) {
      var cur = seed;
      for (var k = 0; k < times; k += 1) {
        var nxt = new Array(GW * GH);
        for (var y = 0; y < GH; y += 1) {
          for (var x = 0; x < GW; x += 1) {
            var acc = 4 * cur[y * GW + x];
            for (var d = 0; d < 8; d += 1) {
              var u = x + F.DX[d];
              var v = y + F.DY[d];
              if (u >= 0 && u < GW && v >= 0 && v < GH) acc += cur[v * GW + u];
            }
            nxt[y * GW + x] = F.floordiv(acc, 12);
          }
        }
        cur = nxt;
      }
      return cur;
    }

    function seeds() {
      var seed = new Array(GW * GH);
      var i;
      for (i = 0; i < GW * GH; i += 1) seed[i] = 0;
      for (i = 1; i < C.MAX_ENT; i += 1) {
        if (w.alive[i] === 0 || w.hp[i] <= 0) continue;
        var t = w.ty[i] * GW + w.tx[i];
        if (w.owner[i] === 0) seed[t] += AI.strength(w, i);
        else if (fog.visible(0, t)) seed[t] -= AI.strength(w, i);
      }
      return seed;
    }

    function run() {
      var n = intOf(inum, 0, 6, 3);
      var mine = spread(seeds(), n);
      var ref = AI.influence(w, fog, 0, m);
      var same = 0;
      var i;
      for (i = 0; i < GW * GH; i += 1) if (mine[i] === ref[i]) same += 1;
      var mx = 1;
      for (i = 0; i < GW * GH; i += 1) {
        var a = mine[i] < 0 ? -mine[i] : mine[i];
        if (a > mx) mx = a;
      }
      clear(g, cv.width, cv.height);
      for (var y = 0; y < GH; y += 1) {
        for (var x = 0; x < GW; x += 1) {
          var v = mine[y * GW + x];
          var f = Math.min(1, (v < 0 ? -v : v) / mx);
          var c = v >= 0
            ? 'rgba(74,163,208,' + f.toFixed(3) + ')'
            : 'rgba(224,122,95,' + f.toFixed(3) + ')';
          g.fillStyle = COL.bg;
          g.fillRect(x * CELL, y * CELL, CELL - 1, CELL - 1);
          g.fillStyle = c;
          g.fillRect(x * CELL, y * CELL, CELL - 1, CELL - 1);
        }
      }
      for (i = 1; i < C.MAX_ENT; i += 1) {
        if (w.alive[i] === 0) continue;
        g.fillStyle = w.owner[i] === 0 ? COL.path : COL.bad;
        g.fillRect(w.tx[i] * CELL + 3, w.ty[i] * CELL + 3, 4, 4);
      }
      var lines = ['확산 ' + n + '회 · 파랑 = 내 영향, 붉음 = 적 영향'];
      txt.innerHTML = esc(lines.join('\n')) + '\n'
        + (n !== AI.SPREAD
           ? '<span class="dim">엔진이 실제로 쓰는 값은 ' + AI.SPREAD
             + '회입니다. 거기로 맞추면 ai.influence() 와 대조합니다.</span>'
           : (same === GW * GH
              ? '<span class="ok">' + AI.SPREAD
                + '회에서 ai.influence() 와 ' + same + '/' + (GW * GH)
                + '칸 모두 일치.</span>'
              : '<span class="bad">ai.influence() 와 ' + (GW * GH - same)
                + '칸 다릅니다 — 이 데모가 틀렸습니다.</span>'));
    }

    on(host.querySelector('[data-mine]'), 'click', function () {
      put(0, C.INF);
      run();
    });
    on(host.querySelector('[data-foe]'), 'click', function () {
      put(1, C.TANK);
      run();
    });
    on(host.querySelector('[data-clear]'), 'click', function () {
      reset();
      run();
    });
    on(inum, 'input', run);
    reset();
    put(0, C.INF);
    put(0, C.INF);
    put(1, C.TANK);
    run();
  });

  // ── 18. PC 스피커 분주값 ──────────────────────────────────────────────────
  // divisor·actual·square 는 speaker 모듈의 것이다. 소리 내기는 그 PCM 을
  // 그대로 WebAudio 버퍼에 붓는다 — 브라우저가 다시 합성하지 않는다.
  window.__demo('speaker-divisor', function (host, api) {
    var C = R('const');
    var SK = R('speaker');
    var inf = host.querySelector('[data-f]');
    var o = panel(host, api);
    var cv = canvas(o, 300, 80);
    var g = cv.getContext('2d');
    var txt = textBox(o);
    var ac = null;

    function nearestNote(hz) {
      var best = 0;
      var bd = 1e9;
      for (var i = 0; i < SK.NOTE_HZ.length; i += 1) {
        var d = Math.abs(SK.NOTE_HZ[i] - hz);
        if (d < bd) { bd = d; best = i; }
      }
      return SK.NOTE_NAME[best];
    }

    function run() {
      var f = intOf(inf, 20, 8000, 440);
      var dv = SK.divisor(f);
      var act = SK.actual(f);
      var a100 = SK.actual100(f);
      var real = a100 / 100;
      var cents = 1200 * Math.log(real / f) / Math.log(2);
      var pcm = SK.square(f, 300);
      clear(g, cv.width, cv.height);
      for (var i = 0; i < pcm.length && i < cv.width; i += 1) {
        var y = pcm[i] === SK.AMP_LO ? 56 : 20;
        g.fillStyle = COL.open;
        g.fillRect(i, y, 1, 6);
      }
      g.fillStyle = COL.grid;
      g.fillRect(0, 39, cv.width, 1);
      var lines = ['목표 ' + f + ' Hz → 분주값 ' + dv + '  ('
                   + C.PIT_HZ + ' / ' + dv + ')',
                   '실제 ' + (a100 / 100).toFixed(2) + ' Hz  (몫 ' + act[0]
                   + ' 나머지 ' + act[1] + ' · 100배 정수 ' + a100 + ')',
                   '반주기 ' + SK.halfPeriod(f) + '샘플 @ ' + SK.SAMPLE_RATE
                   + ' Hz · 가장 가까운 음 ' + nearestNote(f)];
      txt.innerHTML = esc(lines.join('\n')) + '\n'
        + '<span class="' + (Math.abs(cents) < 10 ? 'ok' : 'bad') + '">'
        + '오차 ' + (cents >= 0 ? '+' : '') + cents.toFixed(1)
        + ' 센트 — 높은 음일수록 분주값이 작아 오차가 커집니다.</span>';
    }

    // speaker.square() 가 낸 8비트 PCM 을 그대로 튼다. 합성은 엔진이 했다.
    function play() {
      var f = intOf(inf, 20, 8000, 440);
      try {
        var Ctor = window.AudioContext || window.webkitAudioContext;
        if (!Ctor) throw new Error('이 브라우저에는 WebAudio 가 없습니다');
        if (ac === null) ac = new Ctor();
        var n = Math.floor(SK.SAMPLE_RATE * 0.4);
        var pcm = SK.square(f, n);
        var buf = ac.createBuffer(1, n, SK.SAMPLE_RATE);
        var ch = buf.getChannelData(0);
        for (var i = 0; i < n; i += 1) ch[i] = (pcm[i] - SK.AMP_MID) / 128;
        var src = ac.createBufferSource();
        src.buffer = buf;
        src.connect(ac.destination);
        src.start();
      } catch (e) {
        txt.innerHTML += '\n<span class="bad">소리를 낼 수 없습니다: '
          + esc(e.message) + '</span>';
      }
    }

    on(host.querySelector('[data-run]'), 'click', run);
    on(host.querySelector('[data-play]'), 'click', play);
    on(inf, 'input', run);
    run();
  });
})();
