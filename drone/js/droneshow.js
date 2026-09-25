// droneshow.js — 드론쇼 시뮬레이터의 자바스크립트 판 (SPEC.md).
//
// 파이썬 판(py/droneshow/)과 같은 스펙을 따르고, 파이썬이 낸 골든
// 벡터(golden/*.json)와 1e-9 안에서 같은 값을 낸다(js/test/).
// 라이브러리 없이 순수 ES2020 한 파일이라, 덱 안(브라우저)과
// node 에서 그대로 돈다.
//
// 옮기는 규칙 하나: **연산 순서까지 파이썬과 같게.** 실수 덧셈은 결합
// 법칙이 성립하지 않는다 — (a + b) + c 와 a + (b + c) 는 끝자리가
// 다를 수 있다. 그래서 식의 괄호와 더하는 차례를 파이썬 쪽과 맞춘다.
// 절(─── 이름 ───)은 파이썬 모듈 하나씩이다.
(function (root) {
  'use strict';
  const DS = {};

  // ─── rng (SPEC §2) ────────────────────────────────────────────────
  // 마사글리아의 xorshift128. 32비트 부호 없는 정수만 쓰므로 >>> 0 으로
  // 부호를 떼면 파이썬의 & 0xffffffff 와 비트까지 같다.
  class Rng {
    constructor(seed = 0) {
      this.s = [123456789, 362436069, 521288629, 88675123];
      this.s[0] = (this.s[0] ^ (seed & 0xffffffff)) >>> 0;
      for (let i = 0; i < 16; i++) this.next();
    }

    next() {
      const [x, y, z, w] = this.s;
      const t = (x ^ (x << 11)) >>> 0;
      const nw = (w ^ (w >>> 19) ^ t ^ (t >>> 8)) >>> 0;
      this.s = [y, z, w, nw];
      return nw;
    }

    uniform() {
      return this.next() / 4294967296.0;
    }

    normal() {
      const u1 = 1.0 - this.uniform();
      const u2 = this.uniform();
      return Math.sqrt(-2.0 * Math.log(u1))
        * Math.cos(2.0 * Math.PI * u2);
    }
  }
  DS.Rng = Rng;

  // ─── vec3 ─────────────────────────────────────────────────────────
  const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
  const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
  const scale = (a, k) => [a[0] * k, a[1] * k, a[2] * k];
  const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  const cross = (a, b) => [a[1] * b[2] - a[2] * b[1],
    a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
  const norm = (a) => Math.sqrt(dot(a, a));
  function normalize(a) {
    const n = norm(a);
    return [a[0] / n, a[1] / n, a[2] / n];
  }
  const dist = (a, b) => norm(sub(a, b));
  // 앞에서부터 차례로 더한다(파이썬 vec3.total 과 같은 차례).
  function total(xs) {
    let s = 0.0;
    for (const x of xs) s += x;
    return s;
  }
  const eye3 = () => [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
  const fromCols = (a, b, c) => [[a[0], b[0], c[0]], [a[1], b[1], c[1]],
    [a[2], b[2], c[2]]];
  const transpose = (m) => [0, 1, 2].map((i) => [0, 1, 2].map((j) =>
    m[j][i]));
  const matvec = (m, v) => [dot(m[0], v), dot(m[1], v), dot(m[2], v)];
  function matmul(a, b) {
    const bt = transpose(b);
    return [0, 1, 2].map((i) => [0, 1, 2].map((j) => dot(a[i], bt[j])));
  }
  function det3(m) {
    return (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
      - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
      + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]));
  }
  Object.assign(DS, { add, sub, scale, dot, cross, norm, normalize,
    dist, total, eye3, fromCols, transpose, matvec, matmul, det3 });

  // ─── quat (SPEC §1.5–1.6) ─────────────────────────────────────────
  function qmul(a, b) {
    const [aw, ax, ay, az] = a;
    const [bw, bx, by, bz] = b;
    return [aw * bw - ax * bx - ay * by - az * bz,
      aw * bx + ax * bw + ay * bz - az * by,
      aw * by - ax * bz + ay * bw + az * bx,
      aw * bz + ax * by - ay * bx + az * bw];
  }
  const qconj = (q) => [q[0], -q[1], -q[2], -q[3]];
  const qnorm = (q) => Math.sqrt(q[0] * q[0] + q[1] * q[1] + q[2] * q[2]
    + q[3] * q[3]);
  function qnormalize(q) {
    const n = qnorm(q);
    return [q[0] / n, q[1] / n, q[2] / n, q[3] / n];
  }
  const qCanonical = (q) => (q[0] >= 0 ? q.slice()
    : [-q[0], -q[1], -q[2], -q[3]]);
  const qrotate = (q, v) => qmul(qmul(q, [0.0, v[0], v[1], v[2]]),
    qconj(q)).slice(1);
  function qToMatrix(q) {
    const [w, x, y, z] = q;
    return [[1 - 2 * (y * y + z * z), 2 * (x * y - w * z),
      2 * (x * z + w * y)],
    [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
    [2 * (x * z - w * y), 2 * (y * z + w * x),
      1 - 2 * (x * x + y * y)]];
  }
  // 셰퍼드 방법 — 넷 가운데 가장 큰 성분으로 나눈다
  // (파이썬 판 주석 참고).
  function qFromMatrix(m) {
    const t = m[0][0] + m[1][1] + m[2][2];
    const cand = [t, m[0][0], m[1][1], m[2][2]];
    let k = 0;
    for (let i = 1; i < 4; i++) if (cand[i] > cand[k]) k = i;
    let s;
    let q;
    if (k === 0) {
      s = 2.0 * Math.sqrt(1.0 + t);
      q = [s / 4, (m[2][1] - m[1][2]) / s, (m[0][2] - m[2][0]) / s,
        (m[1][0] - m[0][1]) / s];
    } else if (k === 1) {
      s = 2.0 * Math.sqrt(1.0 + m[0][0] - m[1][1] - m[2][2]);
      q = [(m[2][1] - m[1][2]) / s, s / 4, (m[0][1] + m[1][0]) / s,
        (m[0][2] + m[2][0]) / s];
    } else if (k === 2) {
      s = 2.0 * Math.sqrt(1.0 - m[0][0] + m[1][1] - m[2][2]);
      q = [(m[0][2] - m[2][0]) / s, (m[0][1] + m[1][0]) / s, s / 4,
        (m[1][2] + m[2][1]) / s];
    } else {
      s = 2.0 * Math.sqrt(1.0 - m[0][0] - m[1][1] + m[2][2]);
      q = [(m[1][0] - m[0][1]) / s, (m[0][2] + m[2][0]) / s,
        (m[1][2] + m[2][1]) / s, s / 4];
    }
    return qnormalize(q);
  }
  function qFromAxisAngle(axis, angle) {
    const a = normalize(axis);
    const s = Math.sin(angle / 2);
    return [Math.cos(angle / 2), a[0] * s, a[1] * s, a[2] * s];
  }
  function qToAxisAngle(q) {
    q = qCanonical(q);
    const s = Math.sqrt(q[1] * q[1] + q[2] * q[2] + q[3] * q[3]);
    if (s < 1e-15) return [[1.0, 0.0, 0.0], 0.0];
    return [[q[1] / s, q[2] / s, q[3] / s], 2 * Math.atan2(s, q[0])];
  }
  function qFromTwoVectors(a, b) {
    const d = dot(a, b);
    if (d < -1.0 + 1e-12) {
      let axis = cross(a, [1.0, 0.0, 0.0]);
      if (norm(axis) < 1e-6) axis = cross(a, [0.0, 1.0, 0.0]);
      return qFromAxisAngle(axis, Math.PI);
    }
    const c = cross(a, b);
    return qnormalize([1.0 + d, c[0], c[1], c[2]]);
  }
  function qFromEuler(roll, pitch, yaw) {
    const qx = qFromAxisAngle([1.0, 0.0, 0.0], roll);
    const qy = qFromAxisAngle([0.0, 1.0, 0.0], pitch);
    const qz = qFromAxisAngle([0.0, 0.0, 1.0], yaw);
    return qmul(qz, qmul(qy, qx));
  }
  function qToEuler(q) {
    const [w, x, y, z] = q;
    const sp = Math.max(-1.0, Math.min(1.0, 2 * (w * y - z * x)));
    return [Math.atan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y)),
      Math.asin(sp),
      Math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))];
  }
  const qdot = (q, w) => qmul(q, [0.0, w[0], w[1], w[2]]).map((c) =>
    0.5 * c);
  Object.assign(DS, { qmul, qconj, qnorm, qnormalize, qCanonical,
    qrotate, qToMatrix, qFromMatrix, qFromAxisAngle, qToAxisAngle,
    qFromTwoVectors, qFromEuler, qToEuler, qdot });

  // ─── params (SPEC §3) ─────────────────────────────────────────────
  // 덱 안에서는 조립기가 data/params.tsv 의 글을 그대로 넣어 준다.
  function loadParams(text) {
    const out = {};
    const rows = text.split('\n').filter((l) => l.trim() &&
      !l.startsWith('#')).map((l) => l.split('\t'));
    for (const [name, value] of rows.slice(1)) {
      out[name] = parseFloat(value);
    }
    return out;
  }
  function derived(p) {
    const tH = p.m * p.g / 4;
    return {
      a: p.L / Math.sqrt(2), c: p.kQ / p.kT, T_hover: tH,
      omega_hover: Math.sqrt(tH / p.kT),
      T_max: p.kT * (p.omega_max * p.omega_max),
      T_min: p.kT * (p.omega_min * p.omega_min),
      twr: 4 * p.kT * (p.omega_max * p.omega_max) / (p.m * p.g),
      area: Math.PI * (p.r_prop * p.r_prop),
    };
  }
  Object.assign(DS, { loadParams, derived });

  // ─── linalg ───────────────────────────────────────────────────────
  // 부분 피벗팅 가우스 소거. 같은 크기의 피벗이 둘이면 먼저 나온 행 —
  // 파이썬의 max(…, key=…) 가 그렇게 고른다.
  function solve(a, b) {
    const m = a.map((r) => r.map(Number));
    const x = b.map(Number);
    const n = m.length;
    for (let col = 0; col < n; col++) {
      let piv = col;
      for (let r = col + 1; r < n; r++) {
        if (Math.abs(m[r][col]) > Math.abs(m[piv][col])) piv = r;
      }
      if (Math.abs(m[piv][col]) < 1e-14) throw new Error('특이 행렬');
      [m[col], m[piv]] = [m[piv], m[col]];
      [x[col], x[piv]] = [x[piv], x[col]];
      for (let r = col + 1; r < n; r++) {
        const f = m[r][col] / m[col][col];
        if (f) {
          for (let k = col; k < n; k++) m[r][k] -= f * m[col][k];
          x[r] -= f * x[col];
        }
      }
    }
    for (let r = n - 1; r >= 0; r--) {
      let s = x[r];
      for (let k = r + 1; k < n; k++) s -= m[r][k] * x[k];
      x[r] = s / m[r][r];
    }
    return x;
  }
  DS.solve = solve;

  // ─── rigidbody (SPEC §4.4) ────────────────────────────────────────
  function rk4(f, x, dt) {
    const n = x.length;
    const k1 = f(x);
    const k2 = f(x.map((v, i) => v + 0.5 * dt * k1[i]));
    const k3 = f(x.map((v, i) => v + 0.5 * dt * k2[i]));
    const k4 = f(x.map((v, i) => v + dt * k3[i]));
    const out = new Array(n);
    for (let i = 0; i < n; i++) {
      out[i] = x[i] + dt / 6.0
        * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i]);
    }
    return out;
  }
  // J ω̇ = τ − ω × (J ω), J 는 대각 성분 셋.
  function omegaDot(j, w, tau) {
    const jw = [j[0] * w[0], j[1] * w[1], j[2] * w[2]];
    const g = cross(w, jw);
    return [(tau[0] - g[0]) / j[0], (tau[1] - g[1]) / j[1],
      (tau[2] - g[2]) / j[2]];
  }
  Object.assign(DS, { rk4, omegaDot });

  // ─── mixer (SPEC §4.1–4.2) ────────────────────────────────────────
  function mixerMatrix(p) {
    const d = derived(p);
    const a = d.a;
    const c = d.c;
    return [[1.0, 1.0, 1.0, 1.0], [a, a, -a, -a], [-a, a, a, -a],
      [-c, c, -c, c]];
  }
  function mixerInverse(p) {
    const m = mixerMatrix(p);
    const d = m.map((row) => total(row.map((x) => x * x)));
    return [0, 1, 2, 3].map((i) =>
      [0, 1, 2, 3].map((j) => m[j][i] / d[j]));
  }
  const forward = (p, t) => mixerMatrix(p).map((r) =>
    total([0, 1, 2, 3].map((k) => r[k] * t[k])));
  const apply4 = (mi, u) => [0, 1, 2, 3].map((i) =>
    total([0, 1, 2, 3].map((k) => mi[i][k] * u[k])));
  const inside = (t, lo, hi) => t.every((x) => lo - 1e-12 <= x &&
    x <= hi + 1e-12);
  // 우선순위 롤·피치 > 총추력 > 요
  // (파이썬 mixer.allocate 와 같은 차례).
  function allocate(p, u, lo, hi) {
    const mi = mixerInverse(p);
    const flags = [];
    let t = apply4(mi, u);
    if (inside(t, lo, hi)) return [t, flags];
    if (u[3] !== 0.0) {
      flags.push('yaw_scaled');
      const base = apply4(mi, [u[0], u[1], u[2], 0.0]);
      if (inside(base, lo, hi)) {
        let k0 = 0.0;
        let k1 = 1.0;
        for (let i = 0; i < 30; i++) {
          const k = 0.5 * (k0 + k1);
          const tk = apply4(mi, [u[0], u[1], u[2], k * u[3]]);
          if (inside(tk, lo, hi)) {
            k0 = k;
          } else {
            k1 = k;
          }
        }
        return [apply4(mi, [u[0], u[1], u[2], k0 * u[3]]), flags];
      }
      t = base;
    }
    flags.push('shifted');
    const mn = Math.min(...t);
    const delta = mn < lo ? lo - mn : hi - Math.max(...t);
    t = t.map((x) => x + delta);
    if (!inside(t, lo, hi)) {
      flags.push('clamped');
      t = t.map((x) => Math.min(hi, Math.max(lo, x)));
    }
    return [t, flags];
  }
  Object.assign(DS, { mixerMatrix, mixerInverse, forward, allocate });

  // ─── quadrotor (SPEC §4.3) ────────────────────────────────────────
  // 상태 17개: p(3) v(3) q(4) ω(3) Ω(4).
  function hoverState(p, where) {
    const oh = derived(p).omega_hover;
    return [...where.map(Number), 0, 0, 0, 1, 0, 0, 0, 0, 0, 0,
      oh, oh, oh, oh];
  }
  function deriv(p, s, cmd, wind = [0, 0, 0]) {
    const thrust = s.slice(13, 17).map((w) => p.kT * w * w);
    const u = forward(p, thrust);
    const q = s.slice(6, 10);
    const fb = qrotate(q, [0.0, 0.0, u[0]]);
    const v = s.slice(3, 6);
    const acc = [0, 1, 2].map((i) =>
      (fb[i] - p.c_drag * v[i] + wind[i]) / p.m);
    acc[2] -= p.g;
    const wd = omegaDot([p.Jxx, p.Jyy, p.Jzz], s.slice(10, 13),
      u.slice(1));
    const md = [0, 1, 2, 3].map((i) => (cmd[i] - s[13 + i]) / p.tau_m);
    return [...v, ...acc, ...qdot(q, s.slice(10, 13)), ...wd, ...md];
  }
  function step(p, s, cmd, dt, wind = [0, 0, 0]) {
    const n = rk4((x) => deriv(p, x, cmd, wind), s, dt);
    const q = qnormalize(n.slice(6, 10));
    for (let i = 0; i < 4; i++) n[6 + i] = q[i];
    return n;
  }
  Object.assign(DS, { hoverState, deriv, step });

  // ─── pid (SPEC §5.1) ──────────────────────────────────────────────
  // D 는 측정값을 미분하고 1차 저역 통과로 누른다.
  class PID {
    constructor(kp, ki, kd, iMax = Infinity, tauD = 0.0) {
      Object.assign(this, { kp, ki, kd, iMax, tauD });
      this.reset();
    }

    reset() {
      this.i = 0.0;
      this.d = 0.0;
      this.yPrev = null;
    }

    update(ref, y, dt) {
      const e = ref - y;
      this.i = Math.max(-this.iMax,
        Math.min(this.iMax, this.i + e * dt));
      const raw = this.yPrev === null ? 0.0 : -(y - this.yPrev) / dt;
      this.yPrev = y;
      this.d += (raw - this.d) * dt / (this.tauD + dt);
      return this.kp * e + this.ki * this.i + this.kd * this.d;
    }
  }
  class VecPID {
    constructor(kp, ki, kd, iMax = Infinity, tauD = 0.0) {
      this.axes = [0, 1, 2].map((k) =>
        new PID(kp[k], ki[k], kd[k], iMax, tauD));
    }

    update(ref, y, dt) {
      return [0, 1, 2].map((k) =>
        this.axes[k].update(ref[k], y[k], dt));
    }
  }
  Object.assign(DS, { PID, VecPID });

  // ─── attitude (SPEC §5.3–5.4) ─────────────────────────────────────
  function axes(f, yaw) {
    const z = normalize(f);
    const xc = [Math.cos(yaw), Math.sin(yaw), 0.0];
    const y = normalize(cross(z, xc));
    return [cross(y, z), y, z];
  }
  function desiredAttitude(f, yaw) {
    const [x, y, z] = axes(f, yaw);
    return qFromMatrix(fromCols(x, y, z));
  }
  // 평탄성: 가속도·가가속도·요 → 몸체 각속도
  // (T12, 파이썬 판 주석 참고).
  function flatRates(a, j, yaw, yawRate, g) {
    const f = [a[0], a[1], a[2] + g];
    const [x, y, z] = axes(f, yaw);
    const h = scale(sub(j, scale(z, dot(z, j))), 1.0 / norm(f));
    const p = -dot(h, y);
    const q = dot(h, x);
    const xc = [Math.cos(yaw), Math.sin(yaw), 0.0];
    const yc = [-Math.sin(yaw), Math.cos(yaw), 0.0];
    const r = (dot(xc, z) * p + yawRate * dot(y, yc)) / dot(xc, x);
    return [p, q, r];
  }
  // PX4 식: 기울기 먼저(q_red), 요는 yawW 만큼만 섞는다.
  function attLaw(q, qd, k, yawW) {
    const ez = qrotate(q, [0.0, 0.0, 1.0]);
    const ezd = qrotate(qd, [0.0, 0.0, 1.0]);
    const qred = dot(ez, ezd) < -1.0 + 1e-5 ? qd.slice()
      : qmul(qFromTwoVectors(ez, ezd), q);
    const qmix = qCanonical(qmul(qconj(qred), qd));
    const w0 = Math.max(-1.0, Math.min(1.0, qmix[0]));
    const z0 = Math.max(-1.0, Math.min(1.0, qmix[3]));
    const qd2 = qmul(qred, [Math.cos(yawW * Math.acos(w0)), 0.0, 0.0,
      Math.sin(yawW * Math.asin(z0))]);
    const qe = qCanonical(qmul(qconj(q), qd2));
    return [0, 1, 2].map((i) => 2.0 * k[i] * qe[i + 1]);
  }
  Object.assign(DS, { desiredAttitude, flatRates, attLaw });

  // ─── cascade (SPEC §5) ────────────────────────────────────────────
  const PHYS_HZ = 500;
  class Controller {
    constructor(p, cfg) {
      this.p = p = { ...p, ...(cfg || {}) };
      this.d = derived(p);
      this.div = {};
      for (const k of ['rate_hz', 'att_hz', 'pos_hz']) {
        this.div[k] = Math.round(PHYS_HZ / p[k]);
        if (this.div[k] * p[k] !== PHYS_HZ) {
          throw new Error(k + ' 는 500 의 약수여야 한다');
        }
      }
      const three = (x) => [x, x, x];
      this.vel = new VecPID(three(p.kp_vel), three(p.ki_vel),
        three(p.kd_vel), p.i_max_vel, p.tau_d_vel);
      this.rate = new VecPID(three(p.kp_rate), three(p.ki_rate),
        three(p.kd_rate), p.i_max_rate, p.tau_d_rate);
      this.kAtt = [p.k_att_xy, p.k_att_xy, p.k_att_z];
      this.fDes = [0.0, 0.0, p.m * p.g];
      this.qD = [1.0, 0.0, 0.0, 0.0];
      this.wSp = [0.0, 0.0, 0.0];
      this.wFf = [0.0, 0.0, 0.0];
      this.cmd = [0, 1, 2, 3].map(() => this.d.omega_hover);
    }

    position(s, ref) {
      const p = this.p;
      const dt = this.div.pos_hz / PHYS_HZ;
      const e = sub(ref.p, s.slice(0, 3));
      let vsp = add(scale(e, p.kp_pos), ref.v || [0.0, 0.0, 0.0]);
      const n = norm(vsp);
      if (n > p.vmax_ctrl) vsp = scale(vsp, p.vmax_ctrl / n);
      const asp = add(this.vel.update(vsp, s.slice(3, 6), dt),
        ref.a || [0.0, 0.0, 0.0]);
      const f = scale([asp[0], asp[1], asp[2] + p.g], p.m);
      f[2] = Math.max(f[2], 0.1 * p.m * p.g);
      const lim = Math.tan(p.tilt_max_deg * (Math.PI / 180)) * f[2];
      const h = Math.sqrt(f[0] * f[0] + f[1] * f[1]);
      if (h > lim) {
        f[0] = f[0] * lim / h;
        f[1] = f[1] * lim / h;
      }
      this.fDes = f;
      this.qD = desiredAttitude(f, ref.yaw || 0.0);
      this.wFf = ref.j ? flatRates(ref.a || [0.0, 0.0, 0.0], ref.j,
        ref.yaw || 0.0, ref.yaw_rate || 0.0, p.g) : [0.0, 0.0, 0.0];
    }

    attitude(s) {
      const w = add(attLaw(s.slice(6, 10), this.qD, this.kAtt,
        this.p.yaw_w), this.wFf);
      const lim = this.p.rate_max;
      this.wSp = w.map((x) => Math.max(-lim, Math.min(lim, x)));
    }

    rates(s) {
      const p = this.p;
      const dt = this.div.rate_hz / PHYS_HZ;
      const al = this.rate.update(this.wSp, s.slice(10, 13), dt);
      const tau = [p.Jxx * al[0], p.Jyy * al[1], p.Jzz * al[2]];
      const zb = qrotate(s.slice(6, 10), [0.0, 0.0, 1.0]);
      const u = [Math.max(0.0, dot(this.fDes, zb)), ...tau];
      const [t] = allocate(p, u, this.d.T_min, this.d.T_max);
      this.cmd = t.map((x) => Math.min(p.omega_max,
        Math.max(p.omega_min, Math.sqrt(x / p.kT))));
    }

    update(k, s, ref) {
      if (k % this.div.pos_hz === 0) this.position(s, ref);
      if (k % this.div.att_hz === 0) this.attitude(s);
      if (k % this.div.rate_hz === 0) this.rates(s);
      return this.cmd;
    }
  }
  DS.Controller = Controller;

  // ─── sim ──────────────────────────────────────────────────────────
  // ref(t) 를 secs 초 동안 따라 난다.
  // opts: start, cfg, wind, every, state.
  function fly(p, ref, secs, opts = {}) {
    const dt = 1.0 / PHYS_HZ;
    const ctl = new Controller(p, opts.cfg);
    let s = opts.state ? opts.state.slice()
      : hoverState(p, opts.start || [0, 0, 0]);
    const every = opts.every || 10;
    const rows = [];
    const zero = [0.0, 0.0, 0.0];
    const n = Math.round(secs / dt);
    for (let k = 0; k < n; k++) {
      const t = k * dt;
      const cmd = ctl.update(k, s, ref(t));
      s = step(ctl.p, s, cmd, dt, opts.wind ? opts.wind(t) : zero);
      if ((k + 1) % every === 0) {
        rows.push({ t: (k + 1) * dt, s, cmd: cmd.slice() });
      }
    }
    return rows;
  }
  DS.fly = fly;

  // ─── poly (SPEC §7, T27) ──────────────────────────────────────────
  function pval(c, t) {
    let s = 0.0;
    for (let i = c.length - 1; i >= 0; i--) s = s * t + c[i];
    return s;
  }
  function pderiv(c, k = 1) {
    for (let n = 0; n < k; n++) {
      const d = [];
      for (let i = 1; i < c.length; i++) d.push(i * c[i]);
      c = d.length ? d : [0.0];
    }
    return c;
  }
  const fact = (n) => (n <= 1 ? 1 : n * fact(n - 1));
  function prow(deg, t, d) {
    const row = [];
    for (let i = 0; i <= deg; i++) {
      row.push(i < d ? 0.0 : fact(i) / fact(i - d) * t ** (i - d));
    }
    return row;
  }
  function restToRest(n) {
    const deg = 2 * n - 1;
    const rows = [];
    const rhs = [];
    for (let d = 0; d < n; d++) {
      rows.push(prow(deg, 0.0, d));
      rhs.push(0.0);
      rows.push(prow(deg, 1.0, d));
      rhs.push(d === 0 ? 1.0 : 0.0);
    }
    return solve(rows, rhs);
  }
  // 경유점 N+1, 구간 시간 N → 7차식 N 개 (8N×8N 연립 하나).
  function minSnap(wp, times) {
    const n = times.length;
    const size = 8 * n;
    const rows = [];
    const rhs = [];
    const put = (seg, r) => {
      const full = new Array(size).fill(0.0);
      for (let i = 0; i < 8; i++) full[8 * seg + i] = r[i];
      return full;
    };
    for (let d = 0; d < 4; d++) {
      rows.push(put(0, prow(7, 0.0, d)));
      rhs.push(d === 0 ? wp[0] : 0.0);
      rows.push(put(n - 1, prow(7, times[n - 1], d)));
      rhs.push(d === 0 ? wp[wp.length - 1] : 0.0);
    }
    for (let k = 1; k < n; k++) {
      rows.push(put(k - 1, prow(7, times[k - 1], 0)));
      rhs.push(wp[k]);
      rows.push(put(k, prow(7, 0.0, 0)));
      rhs.push(wp[k]);
      for (let d = 1; d < 7; d++) {
        const a = put(k - 1, prow(7, times[k - 1], d));
        const b = put(k, prow(7, 0.0, d));
        rows.push(a.map((x, i) => x - b[i]));
        rhs.push(0.0);
      }
    }
    const x = solve(rows, rhs);
    const out = [];
    for (let k = 0; k < n; k++) out.push(x.slice(8 * k, 8 * k + 8));
    return out;
  }
  Object.assign(DS, { pval, pderiv, restToRest, minSnap });

  // ─── profile (SPEC §7, T28) ───────────────────────────────────────
  function trapezoid(d, vmax, amax) {
    if (d <= vmax * vmax / amax) {
      const vp = Math.sqrt(d * amax);
      const ta = vp / amax;
      return { d, a: amax, T: 2 * ta, t_acc: ta, v_peak: vp,
        triangular: d < vmax * vmax / amax };
    }
    const ta = vmax / amax;
    return { d, a: amax, T: d / vmax + ta, t_acc: ta, v_peak: vmax,
      triangular: false };
  }
  function sample(pr, t) {
    const T = pr.T;
    const ta = pr.t_acc;
    const vp = pr.v_peak;
    const a = pr.a;
    t = Math.min(Math.max(t, 0.0), T);
    if (t < ta) return [0.5 * a * t * t, a * t, a];
    if (t <= T - ta) {
      return [0.5 * a * ta * ta + vp * (t - ta), vp, 0.0];
    }
    const r = T - t;
    return [pr.d - 0.5 * a * r * r, a * r, -a];
  }
  function polyLimits(c, n = 10000) {
    const d1 = pderiv(c, 1);
    const d2 = pderiv(c, 2);
    let m1 = 0;
    let m2 = 0;
    for (let k = 0; k <= n; k++) {
      m1 = Math.max(m1, Math.abs(pval(d1, k / n)));
      m2 = Math.max(m2, Math.abs(pval(d2, k / n)));
    }
    return [m1, m2];
  }
  Object.assign(DS, { trapezoid, sample, polyLimits });

  // ─── collide (SPEC §8) ────────────────────────────────────────────
  // x 순으로 줄 세워 훑고, x 차가 최솟값보다 크면 안쪽 고리를 끊는다.
  function minDistance(pts) {
    const order = pts.map((_, k) => k).sort((a, b) =>
      pts[a][0] - pts[b][0] || a - b);
    let best = Infinity;
    let bi = -1;
    let bj = -1;
    for (let a = 0; a < order.length; a++) {
      const i = order[a];
      const pi = pts[i];
      for (let b = a + 1; b < order.length; b++) {
        const j = order[b];
        const pj = pts[j];
        if (pj[0] - pi[0] >= best) break;
        const d = dist(pi, pj);
        if (d < best) {
          best = d;
          bi = Math.min(i, j);
          bj = Math.max(i, j);
        }
      }
    }
    return [best, bi, bj];
  }
  const cellOf = (p, d) => [Math.floor(p[0] / d), Math.floor(p[1] / d),
    Math.floor(p[2] / d)].join(',');
  function farEnough(grid, p, d) {
    const cx = Math.floor(p[0] / d);
    const cy = Math.floor(p[1] / d);
    const cz = Math.floor(p[2] / d);
    for (let dx = -1; dx <= 1; dx++) {
      for (let dy = -1; dy <= 1; dy++) {
        for (let dz = -1; dz <= 1; dz++) {
          const cell = grid.get([cx + dx, cy + dy, cz + dz].join(','));
          if (!cell) continue;
          for (const q of cell) if (dist(p, q) < d) return false;
        }
      }
    }
    return true;
  }
  function gridAdd(grid, p, d) {
    const k = cellOf(p, d);
    if (!grid.has(k)) grid.set(k, []);
    grid.get(k).push(p);
  }
  const orient = (a, b, c) => (b[0] - a[0]) * (c[2] - a[2]) -
    (b[2] - a[2]) * (c[0] - a[0]);
  function crossings(a, b, perm) {
    let n = 0;
    for (let i = 0; i < a.length; i++) {
      for (let j = i + 1; j < a.length; j++) {
        const [p1, p2, q1, q2] = [a[i], b[perm[i]], a[j], b[perm[j]]];
        if (orient(q1, q2, p1) * orient(q1, q2, p2) < 0 &&
            orient(p1, p2, q1) * orient(p1, p2, q2) < 0) n++;
      }
    }
    return n;
  }
  Object.assign(DS, { minDistance, crossings });

  // ─── assign (SPEC §8, T29) ────────────────────────────────────────
  function costMatrix(a, b, squared = true) {
    return a.map((p) => b.map((q) =>
      (squared ? dot(sub(p, q), sub(p, q)) : dist(p, q))));
  }
  const assignTotal = (c, perm) => total(perm.map((j, i) => c[i][j]));
  // 쿤-먼크레스(잠재값 판) — 파이썬 assign.hungarian 과 한 줄씩 같다.
  function hungarian(c) {
    const n = c.length;
    const u = new Array(n + 1).fill(0.0);
    const v = new Array(n + 1).fill(0.0);
    const p = new Array(n + 1).fill(0);
    const way = new Array(n + 1).fill(0);
    let ops = 0;
    for (let i = 1; i <= n; i++) {
      p[0] = i;
      let j0 = 0;
      const minv = new Array(n + 1).fill(Infinity);
      const used = new Array(n + 1).fill(false);
      for (;;) {
        used[j0] = true;
        const i0 = p[j0];
        let delta = Infinity;
        let j1 = 0;
        for (let j = 1; j <= n; j++) {
          if (!used[j]) {
            ops++;
            const cur = c[i0 - 1][j - 1] - u[i0] - v[j];
            if (cur < minv[j]) {
              minv[j] = cur;
              way[j] = j0;
            }
            if (minv[j] < delta) {
              delta = minv[j];
              j1 = j;
            }
          }
        }
        for (let j = 0; j <= n; j++) {
          if (used[j]) {
            u[p[j]] += delta;
            v[j] -= delta;
          } else {
            minv[j] -= delta;
          }
        }
        j0 = j1;
        if (p[j0] === 0) break;
      }
      while (j0) {
        const j1 = way[j0];
        p[j0] = p[j1];
        j0 = j1;
      }
    }
    const perm = new Array(n).fill(0);
    for (let j = 1; j <= n; j++) perm[p[j] - 1] = j - 1;
    return [perm, assignTotal(c, perm), ops];
  }
  Object.assign(DS, { costMatrix, hungarian });

  // ─── font5x7 — 파이썬 font5x7.py 와 같은 표 ─────────────────────
  const GLYPHS = {
    'A': '.###. #...# #...# ##### #...# #...# #...#',
    'B': '####. #...# #...# ####. #...# #...# ####.',
    'C': '.###. #...# #.... #.... #.... #...# .###.',
    'D': '####. #...# #...# #...# #...# #...# ####.',
    'E': '##### #.... #.... ####. #.... #.... #####',
    'F': '##### #.... #.... ####. #.... #.... #....',
    'G': '.###. #...# #.... #.### #...# #...# .####',
    'H': '#...# #...# #...# ##### #...# #...# #...#',
    'I': '.###. ..#.. ..#.. ..#.. ..#.. ..#.. .###.',
    'J': '..### ...#. ...#. ...#. ...#. #..#. .##..',
    'K': '#...# #..#. #.#.. ##... #.#.. #..#. #...#',
    'L': '#.... #.... #.... #.... #.... #.... #####',
    'M': '#...# ##.## #.#.# #.#.# #...# #...# #...#',
    'N': '#...# #...# ##..# #.#.# #..## #...# #...#',
    'O': '.###. #...# #...# #...# #...# #...# .###.',
    'P': '####. #...# #...# ####. #.... #.... #....',
    'Q': '.###. #...# #...# #...# #.#.# #..#. .##.#',
    'R': '####. #...# #...# ####. #.#.. #..#. #...#',
    'S': '.#### #.... #.... .###. ....# ....# ####.',
    'T': '##### ..#.. ..#.. ..#.. ..#.. ..#.. ..#..',
    'U': '#...# #...# #...# #...# #...# #...# .###.',
    'V': '#...# #...# #...# #...# #...# .#.#. ..#..',
    'W': '#...# #...# #...# #.#.# #.#.# #.#.# .#.#.',
    'X': '#...# #...# .#.#. ..#.. .#.#. #...# #...#',
    'Y': '#...# #...# .#.#. ..#.. ..#.. ..#.. ..#..',
    'Z': '##### ....# ...#. ..#.. .#... #.... #####',
    '0': '.###. #...# #..## #.#.# ##..# #...# .###.',
    '1': '..#.. .##.. ..#.. ..#.. ..#.. ..#.. .###.',
    '2': '.###. #...# ....# ...#. ..#.. .#... #####',
    '3': '##### ...#. ..#.. ...#. ....# #...# .###.',
    '4': '...#. ..##. .#.#. #..#. ##### ...#. ...#.',
    '5': '##### #.... ####. ....# ....# #...# .###.',
    '6': '..##. .#... #.... ####. #...# #...# .###.',
    '7': '##### ....# ...#. ..#.. .#... .#... .#...',
    '8': '.###. #...# #...# .###. #...# #...# .###.',
    '9': '.###. #...# #...# .#### ....# ...#. .##..',
    ' ': '..... ..... ..... ..... ..... ..... .....',
    '-': '..... ..... ..... ##### ..... ..... .....',
    '!': '..#.. ..#.. ..#.. ..#.. ..#.. ..... ..#..',
  };

  // ─── formation (SPEC §8, T32) ─────────────────────────────────────
  const GOLDEN = Math.PI * (3.0 - Math.sqrt(5.0));
  function place(pts, z0) {
    const xs = pts.map((p) => p[0]);
    const cx = (Math.min(...xs) + Math.max(...xs)) / 2;
    const zb = Math.min(...pts.map((p) => p[2]));
    return pts.map((p) => [p[0] - cx, p[1], p[2] - zb + z0]);
  }
  function fit(pts, d) {
    const m = minDistance(pts)[0];
    return pts.map((p) => p.map((c) => c * d / m));
  }
  function grid(n, d, plane = 'xz', z0 = 0.0) {
    const cols = Math.ceil(Math.sqrt(n));
    let pts = [];
    for (let k = 0; k < n; k++) {
      const r = Math.floor(k / cols);
      const c = k % cols;
      pts.push(plane === 'xy' ? [c * d, r * d, 0.0]
        : [c * d, 0.0, r * d]);
    }
    if (plane === 'xy') {
      const ys = pts.map((p) => p[1]);
      const cy = (Math.min(...ys) + Math.max(...ys)) / 2;
      pts = pts.map((p) => [p[0], p[1] - cy, 0.0]);
    }
    return place(pts, z0);
  }
  function circle(n, d, z0 = 0.0) {
    const r = d / (2 * Math.sin(Math.PI / n));
    const pts = [];
    for (let k = 0; k < n; k++) {
      pts.push([r * Math.cos(2 * Math.PI * k / n), 0.0,
        r * Math.sin(2 * Math.PI * k / n)]);
    }
    return place(pts, z0);
  }
  function rings(n, d, layers = 3, z0 = 0.0) {
    const pts = [];
    for (let L = 0; L < layers; L++) {
      const m = Math.floor(n / layers) + (L < n % layers ? 1 : 0);
      const r = d / (2 * Math.sin(Math.PI / Math.max(m, 3)));
      for (let k = 0; k < m; k++) {
        const a = 2 * Math.PI * k / m + L * 0.5;
        pts.push([r * Math.cos(a), r * Math.sin(a), L * d]);
      }
    }
    return place(pts, z0);
  }
  function fibonacciUnit(n) {
    const out = [];
    for (let i = 0; i < n; i++) {
      const z = 1.0 - 2.0 * (i + 0.5) / n;
      const r = Math.sqrt(1.0 - z * z);
      const a = GOLDEN * i;
      out.push([r * Math.cos(a), r * Math.sin(a), z]);
    }
    return out;
  }
  const sphere = (n, d, z0 = 0.0) =>
    place(fit(fibonacciUnit(n), d), z0);
  // 곡선 위에 간격 d 로 n 개 — 배율을 이분법으로 (파이썬 _on_curves).
  // 제안은 호 길이가 아니라 직전 제안점에서 현이 d 가 되는 자리마다.
  function onCurves(curves, n, d) {
    const step = d * (1 + 1e-9);
    // a + f·u 가 c 중심 반지름 step 공을 나가는 f (> f0), 없으면 null
    const exitBall = (a, u, c, f0) => {
      const w = [a[0] - c[0], a[1] - c[1], a[2] - c[2]];
      const uu = dot(u, u);
      if (uu === 0.0) return null;
      const b = dot(w, u);
      const disc = b * b - uu * (dot(w, w) - step * step);
      if (disc < 0.0) return null;
      const f = (-b + Math.sqrt(disc)) / uu;
      return f > f0 ? f : null;
    };
    const accept = (s) => {
      const got = [];
      const g = new Map();
      const offer = (p) => {
        if (farEnough(g, p, d)) {
          gridAdd(g, p, d);
          got.push(p);
        }
      };
      for (const poly of curves) {
        let prev = poly[0].map((c) => c * s);
        offer(prev);
        for (let i = 0; i + 1 < poly.length; i++) {
          const a = poly[i].map((c) => c * s);
          const b = poly[i + 1].map((c) => c * s);
          const u = [b[0] - a[0], b[1] - a[1], b[2] - a[2]];
          let f = exitBall(a, u, prev, 0.0);
          while (f !== null && f <= 1.0) {
            prev = [0, 1, 2].map((k) => a[k] + u[k] * f);
            offer(prev);
            f = exitBall(a, u, prev, f);
          }
        }
      }
      return got;
    };
    let lo = 1e-3;
    let hi = 1.0;
    while (accept(hi).length < n) hi *= 2;
    for (let i = 0; i < 40; i++) {
      const mid = (lo + hi) / 2;
      if (accept(mid).length >= n) hi = mid; else lo = mid;
    }
    const pts = accept(hi);
    const m = pts.length;
    return Array.from({ length: n },
      (_, k) => pts[Math.floor(k * m / n)]);
  }
  function heart(n, d, z0 = 0.0) {
    const curve = [];
    for (let k = 0; k <= 2000; k++) {
      const t = 2 * Math.PI * k / 2000;
      const s = Math.sin(t);
      curve.push([16 * s * s * s, 0.0,
        13 * Math.cos(t) - 5 * Math.cos(2 * t)
        - 2 * Math.cos(3 * t) - Math.cos(4 * t)]);
    }
    return place(onCurves([curve], n, d), z0);
  }
  function globe(n, d, z0 = 0.0, meridians = 6,
    parallels = [-45, 0, 45]) {
    const curves = [];
    const ts = Array.from({ length: 401 },
      (_, j) => 2 * Math.PI * j / 400);
    for (let k = 0; k < meridians; k++) {
      const a = Math.PI * k / meridians;
      curves.push(ts.map((t) => [Math.cos(a) * Math.sin(t),
        Math.sin(a) * Math.sin(t), Math.cos(t)]));
    }
    for (const lat of parallels) {
      const r = Math.cos(lat * (Math.PI / 180));
      const z = Math.sin(lat * (Math.PI / 180));
      curves.push(ts.map((t) => [r * Math.cos(t), r * Math.sin(t), z]));
    }
    return place(onCurves(curves, n, d), z0);
  }
  const glyphCount = (ch) => GLYPHS[ch].split('#').length - 1;
  function text(s, d, z0 = 0.0) {
    const pts = [];
    [...s].forEach((ch, i) => {
      GLYPHS[ch].split(' ').forEach((row, r) => {
        [...row].forEach((cell, c) => {
          if (cell === '#') {
            pts.push([(6 * i + c) * d, 0.0, (6 - r) * d]);
          }
        });
      });
    });
    return place(pts, z0);
  }
  const digit = (k, d, z0 = 0.0) => text(String(k), d, z0);
  Object.assign(DS, { GLYPHS, grid, circle, rings, fibonacciUnit,
    sphere, heart, globe, glyphCount, text, digit });

  // ─── show (SPEC §9) ───────────────────────────────────────────────
  const KIND = { trapezoid: 'T', minsnap: 'S', minjerk: 'J',
    linear: 'L' };
  const POLY = { S: restToRest(4), J: restToRest(3) };
  const POLYD = {};
  for (const k of ['S', 'J']) POLYD[k] = [pderiv(POLY[k], 1),
    pderiv(POLY[k], 2)];
  // 파이썬 round(x, 9) 에 해당. 끝자리 한 칸이 다를 수 있어
  // 비교는 1e-9 로 한다.
  const r9 = (x) => Math.round(x * 1e9) / 1e9 + 0.0;
  // floor(x + ½) — 파이썬 판 show.rnd 와 같은 반올림.
  const rnd = (x) => Math.floor(x + 0.5);
  function beta(kind, u, ramp) {
    u = Math.min(1.0, Math.max(0.0, u));
    if (kind === 'L') return [u, 1.0, 0.0];
    if (kind === 'T') {
      const vh = 1.0 / (1.0 - ramp);
      if (u <= ramp) {
        return [vh * u * u / (2 * ramp), vh * u / ramp, vh / ramp];
      }
      if (u < 1 - ramp) return [vh * (u - ramp / 2), vh, 0.0];
      const w = 1 - u;
      return [1 - vh * w * w / (2 * ramp), vh * w / ramp, -vh / ramp];
    }
    const [d1, d2] = POLYD[kind];
    return [pval(POLY[kind], u), pval(d1, u), pval(d2, u)];
  }
  function limits(kind, ramp) {
    if (kind === 'L') return [1.0, 0.0];
    if (kind === 'T') {
      return [1.0 / (1.0 - ramp), 1.0 / (ramp * (1.0 - ramp))];
    }
    return polyLimits(POLY[kind]);
  }
  const sceneRgb = (sc, slot) => (typeof sc.rgb[0] === 'number'
    ? sc.rgb.slice() : sc.rgb[slot].slice());
  // 장면 → 제곱 거리 헝가리안 → 동기 직선 이동 (파이썬 show.plan).
  function plan(scenes, p, profile, fps = 25, seed = 7) {
    profile = profile || { kind: 'trapezoid', ramp: 0.25 };
    const k = KIND[profile.kind];
    const ramp = profile.ramp === undefined ? 0.25 : profile.ramp;
    const [d1, d2] = limits(k, ramp);
    const n = scenes[0].points.length;
    let where = scenes[0].points.map((q) => q.slice());
    let slot = where.map((_, i) => i);
    const rows = where.map(() => []);
    const meta = [];
    let t = 0.0;
    const mark = (tt, sc, kind) => {
      for (let i = 0; i < n; i++) {
        const row = [r9(tt), ...where[i].map(r9),
          ...sceneRgb(sc, slot[i])];
        rows[i].push(kind ? [...row, kind] : row);
      }
    };
    scenes.forEach((sc, si) => {
      if (si) {
        const [perm] = hungarian(costMatrix(where, sc.points, true));
        const dmax = Math.max(...where.map((w, i) =>
          dist(w, sc.points[perm[i]])));
        let bigT = Math.max(dmax * d1 / p.vmax,
          Math.sqrt(dmax * d2 / p.amax));
        bigT = Math.ceil(bigT * fps - 1e-9) / fps;
        mark(t, scenes[si - 1], k);
        where = where.map((_, i) => sc.points[perm[i]].slice());
        slot = perm;
        t += bigT;
      }
      meta.push({ name: sc.name, t0: r9(t) });
      mark(t, sc, 'L');
      t += sc.hold;
      meta[meta.length - 1].t1 = r9(t);
    });
    mark(t, scenes[scenes.length - 1], null);
    return { format: 'droneshow/1', fps, dmin: p.dmin, seed,
      profile: { kind: profile.kind, ramp }, duration: r9(t),
      scenes: meta,
      drones: rows.map((kf, i) => ({ id: i, keyframes: kf })) };
  }
  function seg(d, t) {
    const kf = d.keyframes;
    if (t <= kf[0][0]) return [kf[0], kf[0], 0.0, 1.0];
    for (let i = 0; i + 1 < kf.length; i++) {
      const a = kf[i];
      const b = kf[i + 1];
      if (t <= b[0]) {
        const span = b[0] - a[0];
        return [a, b, span ? (t - a[0]) / span : 1.0, span];
      }
    }
    const z = kf[kf.length - 1];
    return [z, z, 1.0, 1.0];
  }
  const kindOf = (show, a) => (a.length > 7 ? a[7]
    : KIND[show.profile.kind]);
  function position(show, d, t) {
    const [a, b, u] = seg(d, t);
    const s = beta(kindOf(show, a), u, show.profile.ramp)[0];
    return [0, 1, 2].map((k) => a[1 + k] + s * (b[1 + k] - a[1 + k]));
  }
  function velocity(show, d, t) {
    const [a, b, u, span] = seg(d, t);
    const s1 = beta(kindOf(show, a), u, show.profile.ramp)[1];
    return [0, 1, 2].map((k) => s1 / span * (b[1 + k] - a[1 + k]));
  }
  function acceleration(show, d, t) {
    const [a, b, u, span] = seg(d, t);
    const s2 = beta(kindOf(show, a), u, show.profile.ramp)[2];
    return [0, 1, 2].map((k) =>
      s2 / (span * span) * (b[1 + k] - a[1 + k]));
  }
  function colour(show, d, t) {
    const tr = d.lights
      || d.keyframes.map((k) => [k[0], ...k.slice(4, 7)]);
    if (t <= tr[0][0]) return tr[0].slice(1, 4).map(Math.trunc);
    for (let i = 0; i + 1 < tr.length; i++) {
      const a = tr[i];
      const b = tr[i + 1];
      if (t <= b[0]) {
        const u = b[0] > a[0] ? (t - a[0]) / (b[0] - a[0]) : 1.0;
        return [0, 1, 2].map((k) =>
          rnd(a[1 + k] + u * (b[1 + k] - a[1 + k])));
      }
    }
    return tr[tr.length - 1].slice(1, 4).map(Math.trunc);
  }
  function frame(show, f) {
    const t = f / show.fps;
    return show.drones.map((d) =>
      [position(show, d, t), colour(show, d, t)]);
  }
  Object.assign(DS, { r9, rnd, beta, limits, plan, position, velocity,
    acceleration, colour, frame });

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = DS;
  } else {
    root.DS = DS;
  }
  // 덱 안에서는 window(검사 스텁이면 그 가짜 window)에, node 에서는
  // module.exports 로 내보낸다.
}(typeof window !== 'undefined' ? window
  : typeof globalThis !== 'undefined' ? globalThis : this));
