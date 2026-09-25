// parity.test.js — 자바스크립트 판이 파이썬 판의 골든 벡터와 같은가.
//
//   node --test js/test/*.test.js   (make test-js · make parity)
//
// 기준은 파이썬이 낸 golden/*.json 이다(SPEC §10). 파이썬 쪽은 이미
// round(·, 9) 해 두었으므로, 이쪽은 날것 그대로 재어 차가 1e-9 이내면
// 같다고 본다. 정수(난수·순열·개수)는 정확히 같아야 한다.
'use strict';
const test = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const path = require('path');
const DS = require('../droneshow.js');

const ROOT = path.join(__dirname, '..', '..');
const gold = (n) => JSON.parse(fs.readFileSync(
  path.join(ROOT, 'golden', n + '.json'), 'utf8'));
const P = DS.loadParams(fs.readFileSync(
  path.join(ROOT, 'data', 'params.tsv'), 'utf8'));
const TOL = 1e-9;

// got 과 want 를 끝까지 따라 내려가며 비교한다. 어디서 틀렸는지
// 경로(a.b[3])를 메시지에 남긴다.
function close(got, want, where = '') {
  if (Array.isArray(want)) {
    assert.ok(Array.isArray(got), `${where}: 배열이 아니다`);
    assert.strictEqual(got.length, want.length, `${where}: 길이`);
    want.forEach((w, i) => close(got[i], w, `${where}[${i}]`));
  } else if (want !== null && typeof want === 'object') {
    for (const k of Object.keys(want)) {
      close(got[k], want[k], `${where}.${k}`);
    }
  } else if (typeof want === 'number') {
    assert.strictEqual(typeof got, 'number', `${where}: 수가 아니다`);
    if (Number.isInteger(want) && Number.isInteger(got) &&
        Math.abs(want) > 1e6) {
      assert.strictEqual(got, want, where);
    } else {
      assert.ok(Math.abs(got - want) <= TOL,
        `${where}: ${got} ≠ ${want}`);
    }
  } else {
    assert.strictEqual(got, want, where);
  }
}

test('rng — xorshift128 수열이 비트까지 같다', () => {
  const g = gold('rng');
  for (const s of [0, 1, 7, 2026]) {
    const r = new DS.Rng(s);
    assert.deepStrictEqual(
      Array.from({ length: 20 }, () => r.next()), g['next_' + s]);
  }
  const r = new DS.Rng(7);
  close(Array.from({ length: 10 }, () => r.normal()), g.normal_7);
});

test('quat — 곱·회전·행렬·축각·오일러', () => {
  for (const c of gold('quat').cases) {
    close(DS.qmul(c.a, c.b), c.mul, 'mul');
    close(DS.qrotate(c.a, c.v), c.rotate, 'rotate');
    close(DS.qToMatrix(c.a), c.matrix, 'matrix');
    close(DS.qCanonical(DS.qFromMatrix(DS.qToMatrix(c.a))),
      c.from_matrix, 'from_matrix');
    close(DS.qFromAxisAngle(c.axis, c.angle), c.axis_angle, 'axis');
    close(DS.qToEuler(c.a), c.euler, 'euler');
  }
});

test('mixer — M, M⁻¹, 포화 처리', () => {
  const g = gold('mixer');
  close(DS.mixerMatrix(P), g.M, 'M');
  close(DS.mixerInverse(P), g.Minv, 'Minv');
  const d = DS.derived(P);
  for (const c of g.cases) {
    const [t, flags] = DS.allocate(P, c.u, d.T_min, d.T_max);
    close(t, c.T, 'T');
    assert.deepStrictEqual(flags, c.flags);
  }
});

test('hover — 표에서 계산한 값', () => {
  close(DS.derived(P), gold('hover'));
});

test('pid — 계단 입력의 출력 열', () => {
  const g = gold('pid');
  for (const s of g.seqs) {
    const [kp, ki, kd, imax, tau] = s.gains;
    const c = new DS.PID(kp, ki, kd, imax, tau);
    let y = 0;
    const out = [];
    for (let k = 0; k < 50; k++) {
      const u = c.update(1.0, y, g.dt);
      y += g.dt * (u - 0.3 * y);
      out.push(u);
    }
    close(out, s.u);
  }
});

test('physics — 세 대의 폐루프 비행', () => {
  const g = gold('physics');
  const refs = {
    hold: () => ({ p: [0, 0, 5] }),
    step: () => ({ p: [1, 0.5, 6], yaw: 0.5 }),
    circle: (t) => ({
      p: [2 * Math.cos(0.8 * t), 2 * Math.sin(0.8 * t), 5.0],
      v: [-1.6 * Math.sin(0.8 * t), 1.6 * Math.cos(0.8 * t), 0.0],
      a: [-1.28 * Math.cos(0.8 * t), -1.28 * Math.sin(0.8 * t), 0.0],
    }),
  };
  const starts = { hold: [0, 0, 5], step: [0, 0, 5],
    circle: [2, 0, 5] };
  for (const name of ['hold', 'step', 'circle']) {
    const rows = DS.fly(P, refs[name], 5.0, { start: starts[name],
      every: 1 });
    for (const tt of ['0.5', '1.0', '2.0', '5.0']) {
      const k = Math.round(Number(tt) * 500) - 1;
      close(rows[k].s, g[name][tt], `${name}@${tt}`);
    }
  }
});

test('poly — 최소 스냅 계수와 β', () => {
  const g = gold('poly');
  for (const c of g.min_snap) close(DS.minSnap(c.wp, c.times), c.coef);
  close(DS.restToRest(3), g.rest3);
  close(DS.restToRest(4), g.rest4);
  for (const k of ['T', 'S', 'J', 'L']) {
    const got = [];
    for (let u = 0; u <= 20; u++) got.push(DS.beta(k, u / 20, 0.25));
    close(got, g.beta[k], 'beta ' + k);
  }
});

test('assign — 헝가리안 순열과 합', () => {
  for (const c of gold('assign').cases) {
    const [perm, total] = DS.hungarian(DS.costMatrix(c.a, c.b, true));
    assert.deepStrictEqual(perm, c.perm);
    close(total, c.total);
  }
});

test('profile — 사다리꼴 표본', () => {
  for (const c of gold('profile').cases) {
    const pr = DS.trapezoid(c.d, 3.0, 2.0);
    close(pr.T, c.T);
    const got = [];
    for (let k = 0; k <= 20; k++) {
      got.push(DS.sample(pr, pr.T * k / 20));
    }
    close(got, c.samples);
  }
});

test('formation — 모양 아홉 가지', () => {
  const g = gold('formation');
  const d = 1.5;
  close(DS.grid(10, d, 'xz', 5.0), g.grid, 'grid');
  close(DS.grid(7, d, 'xy', 0.0), g.grid_xy, 'grid_xy');
  close(DS.circle(16, d, 5.0), g.circle, 'circle');
  close(DS.rings(20, d, 3, 5.0), g.rings, 'rings');
  close(DS.sphere(40, d, 5.0), g.sphere, 'sphere');
  close(DS.heart(30, d, 5.0), g.heart, 'heart');
  close(DS.globe(48, d, 5.0), g.globe, 'globe');
  close(DS.text('DRONE', d, 5.0), g.text, 'text');
  close(DS.digit(7, d, 5.0), g.digit, 'digit');
});

test('show12 — 12대 쇼 전체와 10프레임마다의 위치·색', () => {
  const g = gold('show12');
  const d = 3.0;
  const s = DS.plan([
    { name: 'grid', points: DS.grid(12, d, 'xz', 10.0), hold: 2.0,
      rgb: [255, 255, 255] },
    { name: 'heart', points: DS.heart(12, d, 10.0), hold: 3.0,
      rgb: [255, 0, 64] },
    { name: 'circle', points: DS.circle(12, d, 10.0), hold: 2.0,
      rgb: [0, 200, 255] }], P);
  close(s, g.show, 'show');
  const frames = [];
  const last = Math.round(g.show.duration * g.show.fps);
  for (let f = 0; f <= last; f += 10) {
    frames.push(DS.frame(g.show, f));
  }
  close(frames, g.frames_every10, 'frames');
});
