// demo.js — 덱 안의 데모 여섯 (PLAN.md §3.7, 15부).
//
// 조립기가 droneshow.js, 자료(DS_DATA: 기준 쿼드로터 표와 쇼 파일),
// 이 파일을 차례로 덱 끝의 <script> 에 넣는다. 계산은 전부 droneshow.js
// 가 하고, 여기는 입력칸을 읽고 캔버스에 그리고 요약을 글로 쓴다.
// 요약 글의 숫자는 파이썬 캡처와 같은 형식이라 check_deck.js 가 둘을
// 맞춰 본다. 캔버스가 없는 곳(검사용 DOM 스텁)에서는 그리기만 건너뛴다.
(function () {
  'use strict';
  const D = window.DS;
  const P = D.loadParams(window.DS_DATA.params);

  // ─── 입력칸과 캔버스 ──────────────────────────────────────────────
  function val(host, name, dflt) {
    const el = host.querySelector('[data-' + name + ']');
    const v = el && el.value;
    return v === undefined || v === null || v === '' ? dflt : String(v);
  }
  const num = (host, name, dflt) => {
    const x = parseFloat(val(host, name, String(dflt)));
    return isFinite(x) ? x : dflt;
  };
  function flag(host, name, dflt) {
    const el = host.querySelector('[data-' + name + ']');
    if (!el || el.checked === undefined) return dflt;
    return !!el.checked;
  }
  function bind(host, run) {
    const ins = host.querySelectorAll('input, select, textarea');
    for (let i = 0; i < ins.length; i++) {
      ins[i].addEventListener('input', run);
      ins[i].addEventListener('change', run);
    }
    const bs = host.querySelectorAll('button');
    for (let i = 0; i < bs.length; i++) {
      bs[i].addEventListener('click', run);
    }
    run();
  }
  function canvas(host) {
    const c = host.querySelector('canvas');
    const g = c && c.getContext ? c.getContext('2d') : null;
    return g ? { c, g, w: c.width, h: c.height } : null;
  }
  const f3 = (x) => (Math.round(x * 1000) / 1000).toFixed(3);

  // 선 그래프 — series: [{ys, colour, label}], 가로축은 표본 번호.
  function plot(cv, series, lo, hi, marks) {
    if (!cv) return;
    const { g, w, h } = cv;
    g.fillStyle = '#05081a';
    g.fillRect(0, 0, w, h);
    const y = (v) => h - 12 - (v - lo) / (hi - lo || 1) * (h - 24);
    g.strokeStyle = '#26314f';
    g.beginPath();
    g.moveTo(0, y(0));
    g.lineTo(w, y(0));
    g.stroke();
    for (const m of marks || []) {
      g.strokeStyle = m.colour;
      g.setLineDash([4, 3]);
      g.beginPath();
      g.moveTo(0, y(m.v));
      g.lineTo(w, y(m.v));
      g.stroke();
      g.setLineDash([]);
    }
    for (const s of series) {
      g.strokeStyle = s.colour;
      g.lineWidth = 1.6;
      g.beginPath();
      s.ys.forEach((v, i) => {
        const x = i / (s.ys.length - 1) * (w - 1);
        if (i) g.lineTo(x, y(v)); else g.moveTo(x, y(v));
      });
      g.stroke();
    }
  }

  // ─── 1 쇼 재생기 ──────────────────────────────────────────────────
  // 궤도 카메라: 방위각·고도각·거리로 중심을 본다. 관객 시점은 T33 의
  // "멀리서 거의 수평으로" 에 해당하는 값으로 둔다.
  function camera(az, el, dist, c) {
    const ce = dist * Math.cos(el);
    const pos = [c[0] + ce * Math.sin(az), c[1] - ce * Math.cos(az),
      c[2] + dist * Math.sin(el)];
    const f = D.normalize(D.sub(c, pos));
    const r = D.normalize(D.cross(f, [0, 0, 1]));
    return { pos, f, r, u: D.cross(r, f) };
  }
  function project(cam, p) {
    const q = D.sub(p, cam.pos);
    const z = D.dot(q, cam.f);
    return [D.dot(q, cam.r) / z, D.dot(q, cam.u) / z, z];
  }
  function drawShow(cv, show, t, cam, glow) {
    if (!cv) return;
    const { g, w, h } = cv;
    g.fillStyle = '#05081a';
    g.fillRect(0, 0, w, h);
    const scale = w * 1.6;
    const pts = show.drones.map((d) => ({
      p: project(cam, D.position(show, d, t)), c: D.colour(show, d, t),
    })).sort((a, b) => b.p[2] - a.p[2]);          // 먼 것부터
    g.globalCompositeOperation = glow ? 'lighter' : 'source-over';
    for (const { p, c } of pts) {
      if (p[2] <= 0) continue;
      const x = w / 2 + p[0] * scale;
      const y = h / 2 - p[1] * scale;
      const col = 'rgb(' + c.join(',') + ')';
      if (glow && c.some((v) => v > 0)) {
        g.globalAlpha = 0.25;
        g.fillStyle = col;
        g.beginPath();
        g.arc(x, y, 6, 0, 2 * Math.PI);
        g.fill();
      }
      g.globalAlpha = 1;
      g.fillStyle = c.some((v) => v > 0) ? col : '#26314f';
      g.beginPath();
      g.arc(x, y, 1.8, 0, 2 * Math.PI);
      g.fill();
    }
    g.globalCompositeOperation = 'source-over';
  }
  function centreOf(show) {
    const pts = show.drones.map((d) => d.keyframes[0].slice(1, 4));
    return [0, 1, 2].map((k) =>
      D.total(pts.map((p) => p[k])) / pts.length);
  }
  window.__demo('showplayer', function (host, api) {
    const show = window.DS_DATA.shows.player;
    const cv = canvas(host);
    let playing = false;
    let t0 = 0;
    const draw = () => {
      const t = Math.min(show.duration, num(host, 'time', 0));
      const aud = flag(host, 'audience', false);
      const az = aud ? 0 : num(host, 'az', 30) * Math.PI / 180;
      const el = aud ? 0.02 : num(host, 'el', 15) * Math.PI / 180;
      const cam = camera(az, el, aud ? 150 : 80, centreOf(show));
      drawShow(cv, show, t, cam, flag(host, 'glow', true));
      const scene = show.scenes.filter((s) => t >= s.t0 && t <= s.t1)
        .map((s) => s.name)[0] || '전환 중';
      const dur = show.duration.toFixed(2);
      api.w(host, '드론 ' + show.drones.length + '대 · ' +
        t.toFixed(2) + ' / ' + dur + '초 · ' + scene);
    };
    const tick = (ms) => {
      if (!playing) return;
      if (!t0) t0 = ms;
      const el = host.querySelector('[data-time]');
      if (el) el.value = String(((ms - t0) / 1000) % show.duration);
      draw();
      window.requestAnimationFrame(tick);
    };
    const btn = host.querySelector('button');
    if (btn) {
      btn.addEventListener('click', () => {
        playing = !playing;
        t0 = 0;
        if (playing) window.requestAnimationFrame(tick);
      });
    }
    const ins = host.querySelectorAll('input');
    for (let i = 0; i < ins.length; i++) {
      ins[i].addEventListener('input', draw);
    }
    draw();
  });

  // ─── 2 실시간 물리 ────────────────────────────────────────────────
  // 9부 시간 척도 실험의 한 줄을 브라우저에서 — 1 m 계단을 4 초.
  window.__demo('physics', function (host, api) {
    const cv = canvas(host);
    bind(host, () => {
      const cfg = {
        kp_rate: num(host, 'kprate', P.kp_rate),
        k_att_xy: num(host, 'katt', P.k_att_xy),
        tau_m: num(host, 'taum', P.tau_m),
      };
      if (cfg.kp_rate !== P.kp_rate) {
        cfg.ki_rate = 0.0;
        cfg.kd_rate = 0.0;
      }
      const wx = num(host, 'wind', 0);
      const rows = D.fly(P, () => ({ p: [1, 0, 5] }), 4.0,
        { start: [0, 0, 5], cfg, wind: () => [wx, 0, 0] });
      const tilt = rows.map((r) => {
        const z = D.qrotate(r.s.slice(6, 10), [0, 0, 1]);
        const c = Math.max(-1, Math.min(1, z[2]));
        return Math.acos(c) * 180 / Math.PI;
      });
      const xs = rows.map((r) => r.s[0]);
      plot(cv, [{ ys: xs, colour: '#22d3ee' },
        { ys: tilt.map((v) => v / 45), colour: '#f472b6' }], -0.5, 2.2,
      [{ v: 1, colour: '#f59e0b' }]);
      const top = Math.max(...xs).toFixed(3);
      api.w(host, '최대 기울기 ' + Math.max(...tilt).toFixed(1) +
        '° · x 최댓값 ' + top + ' m · 4초 뒤 x ' +
        xs[xs.length - 1].toFixed(3) + ' m');
    });
  });

  // ─── 3 자세 놀이터 ────────────────────────────────────────────────
  // 원하는 자세를 롤·피치·요로 정하면 오차 쿼터니언과 축·각, 그리고
  // T18 의 P 법칙이 각을 줄이는 모습(운동학 모델)을 닫힌 해와 함께.
  window.__demo('attitude', function (host, api) {
    const cv = canvas(host);
    bind(host, () => {
      const r = (k) => num(host, k, 0) * Math.PI / 180;
      const qd = D.qFromEuler(r('roll'), r('pitch'), r('yaw'));
      const k = num(host, 'k', 3);
      const [axis, th0] = D.qToAxisAngle(qd);
      let q = [1, 0, 0, 0];
      const f = (x) => D.qdot(x, D.attLaw(x, qd, [k, k, k], 1.0));
      const ths = [th0];
      for (let n = 0; n < 2000; n++) {
        q = D.qnormalize(D.rk4(f, q, 0.001));
        if ((n + 1) % 20 === 0) {
          ths.push(D.qToAxisAngle(D.qmul(D.qconj(q), qd))[1]);
        }
      }
      const closed = (t) =>
        4 * Math.atan(Math.tan(th0 / 4) * Math.exp(-k * t));
      plot(cv, [{ ys: ths, colour: '#22d3ee' },
        { ys: ths.map((_, i) => closed(i * 0.02)), colour: '#f59e0b' }],
      0, Math.max(0.1, th0));
      const qe = D.qCanonical(qd);
      const fx = (xs, n) => xs.map((v) => v.toFixed(n)).join(', ');
      api.w(host, 'q_e = (' + fx(qe, 4) +
        ')\n축 (' + fx(axis, 3) + ') · 각 ' +
        (th0 * 180 / Math.PI).toFixed(2) + '°\n1초 뒤 ' +
        (ths[50] * 180 / Math.PI).toFixed(4) + '° · 닫힌 해 ' +
        (closed(1.0) * 180 / Math.PI).toFixed(4) + '°');
    });
  });

  // ─── 4 편대 실험실 ────────────────────────────────────────────────
  // 격자 → 글자, 제곱 거리와 그냥 거리의 할당을 비교(T30·T31).
  window.__demo('formation', function (host, api) {
    const cv = canvas(host);
    bind(host, () => {
      const word = val(host, 'word', 'HI').toUpperCase()
        .replace(/[^A-Z0-9 !-]/g, '');
      const d = num(host, 'd', 1.5);
      let b = D.text(word || 'HI', d * Math.SQRT2, 10.0);
      const n = b.length;
      const a = D.grid(n, d * Math.SQRT2, 'xz', 10.0);
      const sq = !flag(host, 'plain', false);
      const [perm, total] = D.hungarian(D.costMatrix(a, b, sq));
      const cross = D.crossings(a, b, perm);
      let dmin = Infinity;
      for (let k = 0; k <= 100; k++) {
        const u = k / 100;
        const x = a.map((p, i) => [0, 1, 2].map((c) =>
          p[c] + u * (b[perm[i]][c] - p[c])));
        dmin = Math.min(dmin, D.minDistance(x)[0]);
      }
      if (cv) {
        const { g, w, h } = cv;
        g.fillStyle = '#05081a';
        g.fillRect(0, 0, w, h);
        const all = a.concat(b);
        const xs = all.map((p) => p[0]);
        const zs = all.map((p) => p[2]);
        const x0 = Math.min(...xs);
        const z0 = Math.min(...zs);
        const s = Math.min((w - 20) / (Math.max(...xs) - x0 || 1),
          (h - 20) / (Math.max(...zs) - z0 || 1));
        const X = (p) => 10 + (p[0] - x0) * s;
        const Z = (p) => h - 10 - (p[2] - z0) * s;
        g.strokeStyle = 'rgba(244,114,182,0.5)';
        a.forEach((p, i) => {
          g.beginPath();
          g.moveTo(X(p), Z(p));
          g.lineTo(X(b[perm[i]]), Z(b[perm[i]]));
          g.stroke();
        });
        g.fillStyle = '#22d3ee';
        b.forEach((p) => g.fillRect(X(p) - 1.5, Z(p) - 1.5, 3, 3));
      }
      api.w(host, (sq ? '제곱 거리' : '그냥 거리') + ' 합 최소 · ' + n +
        '대 · 합 ' + total.toFixed(3) + '\n엇갈린 쌍 ' + cross +
        ' · 이동 중 최소 간격 ' + dmin.toFixed(3) + ' m (한계 δ/√2 = ' +
        f3(d) + ' m)');
    });
  });

  // ─── 5 궤적 실험실 ────────────────────────────────────────────────
  // 같은 거리를 사다리꼴과 최소 스냅으로 — 속도·가속도(T27·T28).
  window.__demo('trajectory', function (host, api) {
    const cv = canvas(host);
    bind(host, () => {
      const d = num(host, 'dist', 12);
      const vmax = num(host, 'vmax', 3);
      const amax = num(host, 'amax', 2);
      const pr = D.trapezoid(d, vmax, amax);
      const [s1, s2] = D.limits('S', 0.25);
      const ts = Math.max(d * s1 / vmax, Math.sqrt(d * s2 / amax));
      const vt = [];
      const vs = [];
      const at = [];
      const as = [];
      for (let k = 0; k <= 200; k++) {
        const u = k / 200;
        const [, v, a] = D.sample(pr, u * Math.max(pr.T, ts));
        vt.push(v);
        at.push(a);
        const tt = Math.min(1, u * Math.max(pr.T, ts) / ts);
        const b = D.beta('S', tt, 0.25);
        const on = u * Math.max(pr.T, ts) <= ts;
        vs.push(on ? b[1] * d / ts : 0);
        as.push(on ? b[2] * d / (ts * ts) : 0);
      }
      plot(cv, [{ ys: vt, colour: '#22d3ee' },
        { ys: vs, colour: '#f472b6' },
        { ys: at, colour: 'rgba(34,211,238,0.45)' },
        { ys: as, colour: 'rgba(244,114,182,0.45)' }],
      -amax * 1.1, Math.max(vmax, amax) * 1.1,
      [{ v: vmax, colour: '#f59e0b' }]);
      api.w(host, '사다리꼴 T ' + pr.T.toFixed(3) + '초 (' +
        (pr.triangular ? '삼각' : '사다리꼴') + ') · 최소 스냅 T ' +
        ts.toFixed(3) + '초 · 비 ' + (ts / pr.T).toFixed(3));
    });
  });

  // ─── 6 PID 튜너 ───────────────────────────────────────────────────
  // 이중 적분기 + PD 의 계단 응답, 측정한 초과량과 T14 의 공식, 극.
  window.__demo('pidtune', function (host, api) {
    const cv = canvas(host);
    bind(host, () => {
      const kp = num(host, 'kp', 4);
      const kd = num(host, 'kd', 0.8);
      const f = (s) => [s[1], kp * (1 - s[0]) - kd * s[1]];
      let s = [0, 0];
      let top = 0;
      const ys = [];
      for (let k = 0; k < 20000; k++) {
        s = D.rk4(f, s, 1e-3);
        top = Math.max(top, s[0]);
        if (k % 100 === 99) ys.push(s[0]);
      }
      plot(cv, [{ ys, colour: '#22d3ee' }], -0.1,
        Math.max(1.6, top * 1.05), [{ v: 1, colour: '#f59e0b' }]);
      const wn = Math.sqrt(kp);
      const z = kd / (2 * wn);
      const formula = z >= 1 ? 0 : Math.exp(-Math.PI * z /
        Math.sqrt(1 - z * z));
      const disc = kd * kd - 4 * kp;
      const pole = disc >= 0
        ? [(-kd + Math.sqrt(disc)) / 2, (-kd - Math.sqrt(disc)) / 2]
          .map((v) => v.toFixed(3)).join(', ')
        : (-kd / 2).toFixed(3) + ' ± ' +
          (Math.sqrt(-disc) / 2).toFixed(3) + 'i';
      api.w(host, 'ζ = ' + z.toFixed(3) + ' · ωn = ' + wn.toFixed(3) +
        '\n초과량 측정 ' + Math.max(0, top - 1).toFixed(5) +
        ' · 공식 ' + formula.toFixed(5) + '\n극 ' + pole);
    });
  });
}());
