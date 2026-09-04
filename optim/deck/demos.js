(function () {
  'use strict';

  // ── 공용: 2변수 함수의 등고선을 캔버스에 그린다 ──────────────────────
  // 왜 직접 그리는가: 외부 라이브러리를 쓸 수 없는 단일 파일 덱이기 때문이다.
  // 방법은 가장 단순한 것 — 픽셀마다 f 를 재고 log 스케일로 색을 입힌 뒤,
  // 등고선 값 목록을 정해 그 값을 가로지르는 픽셀만 진하게 칠한다.
  function Plot(cv, opt) {
    this.cv = cv;
    this.ctx = cv.getContext('2d');
    this.f = opt.f;
    this.xr = opt.xr;            // [xmin, xmax]
    this.yr = opt.yr;
    this.levels = opt.levels || null;
    this.dpr = Math.min(2, window.devicePixelRatio || 1);
  }
  Plot.prototype.resize = function () {
    var w = this.cv.clientWidth || 320, h = this.cv.clientHeight || 220;
    this.cv.width = Math.round(w * this.dpr);
    this.cv.height = Math.round(h * this.dpr);
    this.w = w; this.h = h;
  };
  Plot.prototype.toPix = function (x, y) {
    return [(x - this.xr[0]) / (this.xr[1] - this.xr[0]) * this.w,
            this.h - (y - this.yr[0]) / (this.yr[1] - this.yr[0]) * this.h];
  };
  Plot.prototype.toXY = function (px, py) {
    return [this.xr[0] + px / this.w * (this.xr[1] - this.xr[0]),
            this.yr[0] + (this.h - py) / this.h * (this.yr[1] - this.yr[0])];
  };
  Plot.prototype.field = function () {
    var ctx = this.ctx, W = this.cv.width, H = this.cv.height;
    var img = ctx.createImageData(W, H);
    var d = img.data, i, j, vmin = Infinity, vmax = -Infinity;
    var vals = new Float64Array(W * H);
    for (j = 0; j < H; j++) {
      for (i = 0; i < W; i++) {
        var p = this.toXY(i / this.dpr, j / this.dpr);
        var v = this.f(p[0], p[1]);
        if (!isFinite(v)) v = 1e30;
        vals[j * W + i] = v;
        if (v < vmin) vmin = v;
        if (v > vmax) vmax = v;
      }
    }
    var lo = Math.log1p(Math.max(0, vmin)), hi = Math.log1p(Math.max(1e-9, vmax));
    for (j = 0; j < H; j++) {
      for (i = 0; i < W; i++) {
        var t = (Math.log1p(Math.max(0, vals[j * W + i])) - lo) / (hi - lo || 1);
        t = Math.max(0, Math.min(1, t));
        var k = (j * W + i) * 4;
        // 낮은 곳은 짙은 남색, 높은 곳은 옅은 회백색
        d[k] = 232 - 150 * (1 - t);
        d[k + 1] = 238 - 140 * (1 - t);
        d[k + 2] = 246 - 90 * (1 - t);
        d[k + 3] = 255;
      }
    }
    ctx.putImageData(img, 0, 0);
    this.vals = vals; this.W = W; this.H = H;
  };
  Plot.prototype.contours = function (levels) {
    // 값이 level 을 가로지르는 자리를 찍는다 — marching squares 없이도 충분히 보인다.
    var ctx = this.ctx, W = this.W, H = this.H, vals = this.vals;
    ctx.save();
    ctx.fillStyle = 'rgba(35,55,92,.55)';
    for (var j = 1; j < H; j++) {
      for (var i = 1; i < W; i++) {
        var a = vals[j * W + i], b = vals[j * W + i - 1], c = vals[(j - 1) * W + i];
        for (var L = 0; L < levels.length; L++) {
          var v = levels[L];
          if ((a - v) * (b - v) < 0 || (a - v) * (c - v) < 0) {
            ctx.fillRect(i, j, 1, 1);
            break;
          }
        }
      }
    }
    ctx.restore();
  };
  Plot.prototype.arrow = function (x0, y0, x1, y1, color, width) {
    var ctx = this.ctx, d = this.dpr;
    var a = this.toPix(x0, y0), b = this.toPix(x1, y1);
    ctx.save();
    ctx.scale(d, d);
    ctx.strokeStyle = color; ctx.fillStyle = color; ctx.lineWidth = width || 2;
    ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke();
    var ang = Math.atan2(b[1] - a[1], b[0] - a[0]), s = 8;
    ctx.beginPath();
    ctx.moveTo(b[0], b[1]);
    ctx.lineTo(b[0] - s * Math.cos(ang - 0.4), b[1] - s * Math.sin(ang - 0.4));
    ctx.lineTo(b[0] - s * Math.cos(ang + 0.4), b[1] - s * Math.sin(ang + 0.4));
    ctx.closePath(); ctx.fill();
    ctx.restore();
  };
  Plot.prototype.dot = function (x, y, color, r) {
    var ctx = this.ctx, d = this.dpr, p = this.toPix(x, y);
    ctx.save(); ctx.scale(d, d);
    ctx.fillStyle = color;
    ctx.beginPath(); ctx.arc(p[0], p[1], r || 4, 0, 6.2832); ctx.fill();
    ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.5; ctx.stroke();
    ctx.restore();
  };
  Plot.prototype.path = function (pts, color, width) {
    if (pts.length < 2) return;
    var ctx = this.ctx, d = this.dpr;
    ctx.save(); ctx.scale(d, d);
    ctx.strokeStyle = color; ctx.lineWidth = width || 1.6;
    ctx.beginPath();
    for (var i = 0; i < pts.length; i++) {
      var p = this.toPix(pts[i][0], pts[i][1]);
      if (i === 0) ctx.moveTo(p[0], p[1]); else ctx.lineTo(p[0], p[1]);
    }
    ctx.stroke();
    ctx.restore();
  };

  // ── 시험함수 (파이썬 구현과 같은 식) ──────────────────────────────
  var FN = {
    quad: {
      name: '이차함수 (κ = 20)',
      f: function (x, y) { return 0.5 * (1 * x * x + 20 * y * y); },
      g: function (x, y) { return [x, 20 * y]; },
      xr: [-3, 3], yr: [-1.2, 1.2],
      levels: [0.05, 0.2, 0.5, 1, 2, 4, 7, 11]
    },
    rosen: {
      name: '로젠브록',
      f: function (x, y) { var t = y - x * x; return 100 * t * t + (1 - x) * (1 - x); },
      g: function (x, y) {
        var t = y - x * x;
        return [-400 * x * t - 2 * (1 - x), 200 * t];
      },
      xr: [-2, 2], yr: [-0.8, 3],
      levels: [0.5, 2, 8, 25, 80, 250, 700]
    },
    himmel: {
      name: '히멜블라우 (최소 4개)',
      f: function (x, y) {
        var a = x * x + y - 11, b = x + y * y - 7;
        return a * a + b * b;
      },
      g: function (x, y) {
        var a = x * x + y - 11, b = x + y * y - 7;
        return [4 * x * a + 2 * b, 2 * a + 4 * y * b];
      },
      xr: [-5.5, 5.5], yr: [-5.5, 5.5],
      levels: [1, 5, 20, 60, 150, 350, 700]
    }
  };

  // ── 데모 1 · 방향도함수 탐색기 ─────────────────────────────────────
  __demo('dirderiv', function (host, api) {
    var cv = host.querySelector('canvas');
    var sel = host.querySelector('[data-fn]');
    var ang = host.querySelector('[data-ang]');
    var pt = [-1.2, 0.9], plot = null;

    function build() {
      var F = FN[sel.value];
      plot = new Plot(cv, F);
      plot.resize();
      plot.field();
      plot.contours(F.levels);
      return F;
    }

    function draw() {
      var F = build();
      var g = F.g(pt[0], pt[1]);
      var gn = Math.hypot(g[0], g[1]) || 1e-12;
      var span = (F.xr[1] - F.xr[0]);
      var s = span * 0.16;                       // 화살표 길이(좌표 단위)
      var th = +ang.value * Math.PI / 180;
      var d = [Math.cos(th), Math.sin(th)];
      var dd = g[0] * d[0] + g[1] * d[1];        // 방향도함수 ∇fᵀd

      // 최급강하 방향(초록) · 고른 방향(주황) · 기울기(파랑)
      plot.arrow(pt[0], pt[1], pt[0] + s * g[0] / gn, pt[1] + s * g[1] / gn, '#3a5c96', 2.2);
      plot.arrow(pt[0], pt[1], pt[0] - s * g[0] / gn, pt[1] - s * g[1] / gn, '#2e9e5b', 2.2);
      plot.arrow(pt[0], pt[1], pt[0] + s * d[0], pt[1] + s * d[1], '#d97706', 2.2);
      plot.dot(pt[0], pt[1], '#cb2c2c', 4.5);

      var best = -gn;
      api.w(host,
        '<b>점</b> (' + pt[0].toFixed(3) + ', ' + pt[1].toFixed(3) + ')' +
        ' · <b>f</b> = ' + F.f(pt[0], pt[1]).toFixed(4) +
        '<br><b>∇f</b> = (' + g[0].toFixed(3) + ', ' + g[1].toFixed(3) + ')' +
        ' · ‖∇f‖ = ' + gn.toFixed(4) +
        '<br><b>방향 d</b> = (' + d[0].toFixed(3) + ', ' + d[1].toFixed(3) + ')' +
        ' · <b>∇fᵀd = ' + dd.toFixed(4) + '</b>' +
        (dd < 0 ? ' → 하강 방향' : (dd > 0 ? ' → 상승 방향' : ' → 접선 방향')) +
        '<br>가능한 최솟값 −‖∇f‖ = ' + best.toFixed(4) +
        ' · 현재는 그 <b>' + (100 * dd / best).toFixed(1) + '%</b>',
        dd < 0 ? 'ok' : 'bad');
    }

    cv.addEventListener('click', function (e) {
      var r = cv.getBoundingClientRect();
      var F = FN[sel.value];
      var p = new Plot(cv, F);
      p.w = cv.clientWidth; p.h = cv.clientHeight;
      pt = p.toXY(e.clientX - r.left, e.clientY - r.top);
      draw();
    });
    sel.addEventListener('change', function () {
      var F = FN[sel.value];
      pt = [(F.xr[0] + F.xr[1]) / 2 - (F.xr[1] - F.xr[0]) * 0.2,
            (F.yr[0] + F.yr[1]) / 2 + (F.yr[1] - F.yr[0]) * 0.2];
      draw();
    });
    ang.addEventListener('input', draw);
    window.addEventListener('resize', function () { draw(); });
    draw();
  });

  window.__optimPlot = Plot;
  window.__optimFN = FN;
})();

(function () {
  'use strict';

  // ── 데모 2 · 젠센 부등식 시각화 ────────────────────────────────────
  // 볼록성의 정의를 그림 하나로 만든다: 현이 곡선 위에 있는가.
  var F1 = {
    sq:      { f: function (x) { return x * x; },                 label: 'x²',    yr: [-0.3, 4.2] },
    abs:     { f: function (x) { return Math.abs(x); },           label: '|x|',   yr: [-0.3, 2.2] },
    exp:     { f: function (x) { return Math.exp(x); },           label: 'eˣ',    yr: [-0.5, 7.5] },
    sin:     { f: function (x) { return Math.sin(3 * x); },       label: 'sin 3x', yr: [-1.4, 1.4] },
    sqrtabs: { f: function (x) { return Math.sqrt(Math.abs(x)); },label: '√|x|',  yr: [-0.2, 1.6] },
    cube:    { f: function (x) { return x * x * x; },             label: 'x³',    yr: [-8.5, 8.5] }
  };

  __demo('jensen', function (host, api) {
    var cv = host.querySelector('canvas');
    var sel = host.querySelector('[data-fn2]');
    var s1 = host.querySelector('[data-x1]');
    var s2 = host.querySelector('[data-x2]');
    var XR = [-2, 2];

    function draw() {
      var spec = F1[sel.value];
      var f = spec.f, YR = spec.yr;
      var dpr = Math.min(2, window.devicePixelRatio || 1);
      var w = cv.clientWidth || 320, h = cv.clientHeight || 220;
      cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr);
      var ctx = cv.getContext('2d');
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, w, h);
      ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, w, h);

      function px(x) { return (x - XR[0]) / (XR[1] - XR[0]) * w; }
      function py(y) { return h - (y - YR[0]) / (YR[1] - YR[0]) * h; }

      // 축
      ctx.strokeStyle = 'rgba(58,92,150,.25)'; ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(px(XR[0]), py(0)); ctx.lineTo(px(XR[1]), py(0));
      ctx.moveTo(px(0), 0); ctx.lineTo(px(0), h);
      ctx.stroke();

      // 곡선
      ctx.strokeStyle = '#23375c'; ctx.lineWidth = 2;
      ctx.beginPath();
      for (var i = 0; i <= 400; i++) {
        var x = XR[0] + (XR[1] - XR[0]) * i / 400, y = f(x);
        if (i === 0) ctx.moveTo(px(x), py(y)); else ctx.lineTo(px(x), py(y));
      }
      ctx.stroke();

      var x1 = XR[0] + (XR[1] - XR[0]) * (+s1.value + 100) / 200;
      var x2 = XR[0] + (XR[1] - XR[0]) * (+s2.value + 100) / 200;
      var y1 = f(x1), y2 = f(x2);

      // 현 — 위반 구간은 붉게
      var N = 200, worst = 0, worstT = 0;
      for (var k = 0; k <= N; k++) {
        var t = k / N;
        var xm = (1 - t) * x1 + t * x2;
        var chord = (1 - t) * y1 + t * y2;
        var gap = chord - f(xm);          // 볼록이면 ≥ 0
        if (gap < worst) { worst = gap; worstT = t; }
      }
      ctx.lineWidth = 3;
      for (var k2 = 0; k2 < N; k2++) {
        var ta = k2 / N, tb = (k2 + 1) / N;
        var xa = (1 - ta) * x1 + ta * x2, xb = (1 - tb) * x1 + tb * x2;
        var ca = (1 - ta) * y1 + ta * y2, cb = (1 - tb) * y1 + tb * y2;
        var bad = (ca - f(xa) < -1e-12) || (cb - f(xb) < -1e-12);
        ctx.strokeStyle = bad ? '#cb2c2c' : '#2e9e5b';
        ctx.beginPath(); ctx.moveTo(px(xa), py(ca)); ctx.lineTo(px(xb), py(cb)); ctx.stroke();
      }

      // 끝점
      [[x1, y1], [x2, y2]].forEach(function (p) {
        ctx.fillStyle = '#3a5c96';
        ctx.beginPath(); ctx.arc(px(p[0]), py(p[1]), 4.5, 0, 6.2832); ctx.fill();
        ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.5; ctx.stroke();
      });

      var xw = (1 - worstT) * x1 + worstT * x2;
      api.w(host,
        '<b>f</b> = ' + spec.label +
        ' · x₁ = ' + x1.toFixed(3) + ', x₂ = ' + x2.toFixed(3) +
        '<br>최악의 젠센 간격 &nbsp;min<sub>t</sub> [ t·f(x₁)+(1−t)·f(x₂) − f(tx₁+(1−t)x₂) ] = <b>' +
        worst.toFixed(6) + '</b>' +
        (worst < -1e-9
          ? '<br>→ <b>반례</b>: t = ' + worstT.toFixed(3) + ' (x = ' + xw.toFixed(3) + ') 에서 현이 곡선 아래로 내려간다'
          : '<br>→ 이 현에서는 위반 없음 (현이 곡선 위에 있다)'),
        worst < -1e-9 ? 'bad' : 'ok');
    }

    sel.addEventListener('change', draw);
    s1.addEventListener('input', draw);
    s2.addEventListener('input', draw);
    window.addEventListener('resize', draw);
    draw();
  });
})();

(function () {
  'use strict';

  // ── 데모 3 · 경사하강 궤적 ─────────────────────────────────────────
  // 보폭 하나로 수렴·지그재그·발산이 갈리는 것을 눈으로 본다.
  var Plot = window.__optimPlot, FN = window.__optimFN;

  // 2×2 헤세 (뉴턴 데모용) — 파이썬 funcs.py 의 식과 같다.
  var HESS = {
    quad: function () { return [[1, 0], [0, 20]]; },
    rosen: function (x, y) {
      return [[-400 * (y - x * x) + 800 * x * x + 2, -400 * x], [-400 * x, 200]];
    },
    himmel: function (x, y) {
      return [[12 * x * x + 4 * y - 42, 4 * x + 4 * y],
              [4 * x + 4 * y, 4 * x + 12 * y * y - 26]];
    }
  };

  function solve2(H, b) {                   // 2×2 연립방정식, 특이하면 null
    var det = H[0][0] * H[1][1] - H[0][1] * H[1][0];
    if (Math.abs(det) < 1e-14) return null;
    return [(b[0] * H[1][1] - H[0][1] * b[1]) / det,
            (H[0][0] * b[1] - b[0] * H[1][0]) / det];
  }

  __demo('gdpath', function (host, api) {
    var cv = host.querySelector('canvas');
    var selF = host.querySelector('[data-fn3]');
    var selM = host.querySelector('[data-method]');
    var slA = host.querySelector('[data-alpha]');
    var start = [-1.5, 0.9];

    function run(F, method, alpha) {
      var x = start.slice(), pts = [x.slice()], k = 0, v = [0, 0];
      var MAX = 400;
      for (k = 0; k < MAX; k++) {
        var g = F.g(x[0], x[1]);
        if (!isFinite(g[0]) || !isFinite(g[1])) break;
        if (Math.hypot(g[0], g[1]) < 1e-10) break;
        var d;
        if (method === 'newton') {
          var H = HESS[selF.value](x[0], x[1]);
          var s = solve2(H, [-g[0], -g[1]]);
          d = s || [-g[0], -g[1]];
          if (d[0] * g[0] + d[1] * g[1] > 0) d = [-g[0], -g[1]];   // 오르막이면 물러선다
        } else {
          d = [-g[0], -g[1]];
        }
        var a = alpha;
        if (method === 'gdls' || method === 'newton') {            // Armijo 되추적
          a = method === 'newton' ? 1 : alpha;
          var f0 = F.f(x[0], x[1]), gtd = g[0] * d[0] + g[1] * d[1];
          for (var t = 0; t < 40; t++) {
            if (F.f(x[0] + a * d[0], x[1] + a * d[1]) <= f0 + 1e-4 * a * gtd) break;
            a *= 0.5;
          }
        }
        if (method === 'mom') {
          v = [0.9 * v[0] + d[0], 0.9 * v[1] + d[1]];
          d = v;
        }
        x = [x[0] + a * d[0], x[1] + a * d[1]];
        if (!isFinite(x[0]) || !isFinite(x[1]) || Math.hypot(x[0], x[1]) > 1e6) {
          pts.push(x.slice());
          break;
        }
        pts.push(x.slice());
      }
      return pts;
    }

    function draw() {
      var F = FN[selF.value];
      var plot = new Plot(cv, F);
      plot.resize(); plot.field(); plot.contours(F.levels);

      var alpha = Math.pow(10, +slA.value / 10);
      var method = selM.value;
      var pts = run(F, method, alpha);
      var last = pts[pts.length - 1];
      var diverged = !isFinite(last[0]) || Math.hypot(last[0], last[1]) > 1e5;

      plot.path(pts, diverged ? '#cb2c2c' : '#7c3aed', 1.8);
      for (var i = 0; i < pts.length; i += Math.max(1, Math.floor(pts.length / 40))) {
        plot.dot(pts[i][0], pts[i][1], 'rgba(124,58,237,.85)', 2.4);
      }
      plot.dot(start[0], start[1], '#cb2c2c', 4.5);
      if (!diverged) plot.dot(last[0], last[1], '#2e9e5b', 4.5);

      var g = F.g(last[0], last[1]);
      api.w(host,
        '<b>방법</b> ' + selM.options[selM.selectedIndex].text +
        ' · <b>α</b> = ' + alpha.toExponential(3) +
        ' · <b>반복</b> ' + (pts.length - 1) +
        '<br>' + (diverged
          ? '<b>발산</b> — 보폭이 2/L 을 넘었다. 가장 가파른 좌표의 증폭 인자 |1−αL| 이 1 을 넘는다.'
          : '<b>도착</b> (' + last[0].toFixed(4) + ', ' + last[1].toFixed(4) + ')' +
            ' · f = ' + F.f(last[0], last[1]).toExponential(3) +
            ' · ‖∇f‖ = ' + Math.hypot(g[0], g[1]).toExponential(3)),
        diverged ? 'bad' : 'ok');
    }

    cv.addEventListener('click', function (e) {
      var r = cv.getBoundingClientRect();
      var F = FN[selF.value];
      var p = new Plot(cv, F);
      p.w = cv.clientWidth; p.h = cv.clientHeight;
      start = p.toXY(e.clientX - r.left, e.clientY - r.top);
      draw();
    });
    selF.addEventListener('change', function () {
      var F = FN[selF.value];
      start = [F.xr[0] + (F.xr[1] - F.xr[0]) * 0.2, F.yr[0] + (F.yr[1] - F.yr[0]) * 0.75];
      draw();
    });
    selM.addEventListener('change', draw);
    slA.addEventListener('input', draw);
    window.addEventListener('resize', draw);
    draw();
  });
})();
