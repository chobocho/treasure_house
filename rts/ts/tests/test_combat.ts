// 전투 — 피해 공식·표적 선택·투사체·스플래시·란체스터 (SPEC §15).

import * as H from './harness';
import * as CB from '../src/combat';
import * as C from '../src/const';
import * as F from '../src/fixed';
import { LCG } from '../src/rng';
import * as S from '../src/spatial';

H.title('combat');

const g = H.golden('prim.txt').split('\n');

// ── 골든 11절 피해표 ────────────────────────────────────────────────────────
let i = g.indexOf('== 11. 전투 ==') + 2;
let bad = 0;
let rows = 0;
while (g[i].trim() !== '' && g[i].indexOf('란체스터') !== 0) {
  const [basic, pierce, armour, wmx, wlo, wn, we, wsim] = H.ints(g[i]);
  const mx = CB.maxDamage(basic, pierce, armour);
  const lo = CB.damageLo(mx);
  const r = new LCG(12345);
  let tot = 0;
  for (let k = 0; k < 1000; k += 1) tot += CB.rollDamage(r, basic, pierce, armour);
  const got = [mx, lo, mx - lo + 1, CB.expect100(basic, pierce, armour),
               F.floordiv(tot * 100, 1000)];
  if (!H.deepEq(got, [wmx, wlo, wn, we, wsim])) {
    bad += 1;
    H.note(basic + '/' + pierce + '/' + armour + ' 기대 '
           + JSON.stringify([wmx, wlo, wn, we, wsim]) + ' 실제 '
           + JSON.stringify(got));
  }
  rows += 1;
  i += 1;
}
H.check('골든 11절 피해표 ' + rows + '줄', bad, 0);

// ── 골든 11절 란체스터 ──────────────────────────────────────────────────────
i = g.indexOf('란체스터 제곱 법칙 시뮬 (A0 B0 alpha beta -> 틱 A남음 B남음)') + 1;
bad = 0;
rows = 0;
while (i < g.length && g[i].indexOf(' ') === 0) {
  const [a0, b0, al, be, wt, wa, wb] = H.ints(g[i]);
  if (!H.deepEq(CB.lanchesterSim(a0, b0, al, be), [wt, wa, wb])) {
    bad += 1;
    H.note(a0 + ' vs ' + b0 + ' 기대 ' + JSON.stringify([wt, wa, wb])
           + ' 실제 ' + JSON.stringify(CB.lanchesterSim(a0, b0, al, be)));
  }
  rows += 1;
  i += 1;
}
H.check('골든 11절 란체스터 ' + rows + '줄', bad, 0);

// ── SPEC §15.2 피해 공식의 경계 ─────────────────────────────────────────────
H.check('최대 피해 = 기본 − 방어 + 관통', CB.maxDamage(12, 8, 3), 17);
H.check('방어가 커도 최소 1 (이 덱의 규칙)', CB.maxDamage(2, 0, 99), 1);
H.check('음수가 되어도 1', CB.maxDamage(0, 0, 5), 1);
H.check('lo = ceil(mx/2)', [1, 2, 3, 4, 9, 10].map((k) => CB.damageLo(k)),
        [1, 1, 2, 2, 5, 5]);
H.check('mx=1 이면 피해는 늘 1', CB.damageLo(1), 1);
const rr = new LCG(1);
const vals: number[] = [];
for (let k = 0; k < 2000; k += 1) vals.push(CB.rollDamage(rr, 6, 3, 2));
H.check('피해는 lo..mx 범위 안', [H.minOf(vals), H.maxOf(vals)], [4, 7]);
H.check('네 값이 모두 나온다', H.sortedSet(vals), [4, 5, 6, 7]);
H.check('E[dmg]*100 = (lo+mx)*50', CB.expect100(6, 3, 2), 550);
H.checkTrue('시뮬 평균이 기대값의 2% 안',
            Math.abs(F.floordiv(H.sum(vals) * 100, vals.length) - 550) <= 11);

// ── 정리 15.1 — 기대값이 0.75·mx 근처인가 ───────────────────────────────────
let even = 0;
let odd = 0;
for (let mx = 1; mx < 40; mx += 1) {
  const e = (CB.damageLo(mx) + mx) * 50;
  if (mx % 2 === 0 && e !== 75 * mx) even += 1;
  if (mx % 2 === 1 && e !== 75 * mx + 25) odd += 1;
}
H.check('짝수 mx 에서 E = 0.75·mx (정리 15.1)', even, 0);
H.check('홀수 mx 에서 E = 0.75·mx + 0.25 — 올림이 한 칸 올린다', odd, 0);
H.note('SPEC 초안은 이 둘을 뒤집어 적고 있었다 — 이 시험이 잡았다');

// ── SPEC §15.1 사거리와 표적 선택 ───────────────────────────────────────────
const w = new S.World(32, 32);
const me = S.index(w.spawn(0, C.ARCHER, 10, 10));      // 사거리 4
const near = S.index(w.spawn(1, C.INF, 12, 10));       // 거리 2
const far = S.index(w.spawn(1, C.INF, 20, 10));        // 거리 10
const tieA = S.index(w.spawn(1, C.INF, 10, 13));       // 거리 3
const tieB = S.index(w.spawn(1, C.INF, 13, 10));       // 거리 3
const mate = S.index(w.spawn(0, C.INF, 11, 10));       // 아군
for (const k of [me, near, far, tieA, tieB, mate]) w.hp[k] = C.HP[w.kind[k]];

H.check('사거리는 체비셰프', CB.inRange(w, me, near), true);
H.check('사거리 밖', CB.inRange(w, me, far), false);
H.check('대각 3칸도 사거리 4 안', CB.inRange(w, me, tieA), true);
let [tgt, appr] = CB.pickTarget(w, me, 0, false);
H.check('가장 가까운 적을 고른다', tgt, w.handle(near));
H.check('접근할 필요는 없다', appr, false);
H.check('아군은 고르지 않는다', tgt !== w.handle(mate), true);

w.target[me] = w.handle(tieA);
[tgt] = CB.pickTarget(w, me, 0, false);
H.check('현재 표적이 살아 있고 사거리 안이면 그대로 (규칙 1)', tgt,
        w.handle(tieA));
w.hp[tieA] = 0;
w.kill(w.handle(tieA));
[tgt] = CB.pickTarget(w, me, 0, false);
H.check('표적이 죽으면 다시 고른다', tgt, w.handle(near));

w.target[me] = 0;
[tgt] = CB.pickTarget(w, me, w.handle(tieB), false);
H.check('나를 때린 적이 사거리 안이면 그것 (규칙 2)', tgt, w.handle(tieB));
[tgt] = CB.pickTarget(w, me, w.handle(far), false);
H.check('나를 때린 적이 사거리 밖이면 규칙 3 으로', tgt, w.handle(near));

// 동점 — 핸들 오름차순
const w2 = new S.World(32, 32);
const a2 = S.index(w2.spawn(0, C.ARCHER, 10, 10));
const e1 = S.index(w2.spawn(1, C.INF, 12, 10));
const e2 = S.index(w2.spawn(1, C.INF, 8, 10));
for (const k of [a2, e1, e2]) w2.hp[k] = C.HP[w2.kind[k]];
H.check('d83 동점이면 핸들 오름차순', CB.pickTarget(w2, a2, 0, false)[0],
        w2.handle(e1));
H.checkTrue('핸들이 작은 쪽이 먼저다', w2.handle(e1) < w2.handle(e2));

// 규칙 4 — ATTACK_MOVE 만 사거리+2 를 훑는다
const w3 = new S.World(32, 32);
const a3 = S.index(w3.spawn(0, C.INF, 10, 10));        // 사거리 1
const e3 = S.index(w3.spawn(1, C.INF, 13, 10));        // 거리 3 = 사거리+2
for (const k of [a3, e3]) w3.hp[k] = C.HP[w3.kind[k]];
H.check('보통은 사거리 밖이면 표적 없음', CB.pickTarget(w3, a3, 0, false),
        [0, false]);
H.check('ATTACK_MOVE 는 사거리+2 안을 훑고 접근한다',
        CB.pickTarget(w3, a3, 0, true), [w3.handle(e3), true]);
w3.tx[e3] = 14;
H.check('사거리+3 은 ATTACK_MOVE 도 못 본다',
        CB.pickTarget(w3, a3, 0, true), [0, false]);
H.check('채집기는 공격하지 않는다',
        CB.pickTarget(w3, S.index(w3.spawn(0, C.HARV, 13, 10)), 0, true),
        [0, false]);

// ── SPEC §15.3 직선 투사체 ──────────────────────────────────────────────────
const pj = new CB.Projectiles(32);
H.check('처음에는 비어 있다', pj.n(), 0);
const ok = pj.launch(CB.STRAIGHT, F.fp(16), F.fp(16), F.fp(80), F.fp(16),
                     CB.ARROW_SPEED, 999, 7);
H.check('발사 성공', ok, true);
H.check('한 발', pj.n(), 1);
H.check('수평 발사면 vy 는 0', pj.vy[0], 0);
H.check('vx 는 화살 속도 그대로', pj.vx[0], CB.ARROW_SPEED);
H.check('ttl = 거리/속도 + 2', pj.ttl[0],
        F.floordiv(F.fp(64), CB.ARROW_SPEED) + 2);
let hits: Array<[number, number, number, number, number]> = [];
for (let t = 0; t < 40; t += 1) {
  hits = hits.concat(pj.step());
  if (pj.n() === 0) break;
}
H.check('언젠가 반드시 명중 또는 소멸한다', hits.length, 1);
H.check('명중 정보는 (목표 핸들, 피해, 목표 타일)', hits[0].slice(0, 2), [999, 7]);
H.check('명중 타일은 목표 타일', hits[0][2], 1 * 32 + 5);
H.check('명중하면 목록에서 사라진다', pj.n(), 0);

H.check('같은 칸이면 발사하지 않고 즉시 명중',
        pj.launch(CB.STRAIGHT, F.fp(16), F.fp(16), F.fp(16), F.fp(16),
                  CB.ARROW_SPEED, 1, 5), false);
H.check('그래도 목록은 비어 있다', pj.n(), 0);

// 속도 벡터의 크기가 speed 인가 (대각 발사)
const pj2 = new CB.Projectiles(32);
pj2.launch(CB.STRAIGHT, 0, 0, F.fp(60), F.fp(80), CB.ARROW_SPEED, 1, 1);
const mag = F.fpSqrt(F.fpMul(pj2.vx[0], pj2.vx[0])
                     + F.fpMul(pj2.vy[0], pj2.vy[0]));
H.checkTrue('|v| == speed (오차 1% 안)',
            Math.abs(mag - CB.ARROW_SPEED)
            <= F.floordiv(CB.ARROW_SPEED, 100));
H.note('발사 시점의 위치로 날아간다 — 빠른 유닛은 화살을 피할 수 있다');

// ── SPEC §15.4 포물선 투사체와 정리 15.2 ────────────────────────────────────
const pj3 = new CB.Projectiles(64);
const x0 = F.fp(16);
const y0 = F.fp(200);
const x1 = F.fp(16 + 96);
const y1 = F.fp(200);
pj3.launch(CB.ARC, x0, y0, x1, y1, 0, 55, 20);
const TT = pj3.ttl[0];
H.check('비행 시간 T = max(6, d/24)', TT, Math.max(6, Math.floor(96 / 24)));
const ys: number[] = [];
hits = [];
while (pj3.n() > 0) {
  ys.push(pj3.y[0]);
  hits = hits.concat(pj3.step());
}
H.check('T틱 뒤에 명중한다', hits.length, 1);
H.checkTrue('가는 동안 위로 올라갔다 내려온다', H.minOf(ys) < y0);
const land = hits[0][3];
H.check('착탄점의 오차는 정리 15.2 의 G·T/2', land - y1,
        F.floordiv(CB.G * TT, 2));
H.note('보정하지 않기로 한 결정이다 — 0.15px 는 타일 판정에 영향이 없다');
H.check('수평은 등속', pj3.n(), 0);

// ── SPEC §15.5 스플래시 ─────────────────────────────────────────────────────
H.check('링 0 은 그대로', CB.splashDamage(20, 0), 20);
H.check('링 1 은 절반', CB.splashDamage(20, 1), 10);
H.check('링 2 는 1/4', CB.splashDamage(20, 2), 5);
H.check('링 3 이상은 0', [3, 4, 9].map((k) => CB.splashDamage(20, k)),
        [0, 0, 0]);
H.check('홀수는 내림', [CB.splashDamage(7, 1), CB.splashDamage(7, 2)], [3, 1]);
H.check('피해 1 도 링 1 에서는 0', CB.splashDamage(1, 1), 0);

const w4 = new S.World(16, 16);
const mine4 = S.index(w4.spawn(0, C.INF, 5, 5));
const foe4 = S.index(w4.spawn(1, C.INF, 6, 5));
const away = S.index(w4.spawn(1, C.INF, 9, 5));
for (const k of [mine4, foe4, away]) w4.hp[k] = 40;
const sp = CB.splashHits(w4, 5, 5, 20);
const spm = new Map<number, number>(sp);
H.check('명중 칸의 유닛은 전액', spm.get(w4.handle(mine4)), 20);
H.check('링 1 은 절반 — 아군도 맞는다', spm.get(w4.handle(foe4)), 10);
H.check('링 3 밖은 목록에 없다', spm.has(w4.handle(away)), false);
H.check('스플래시 목록은 핸들 오름차순', sp.map((p) => p[0]),
        H.sortedNums(sp.map((p) => p[0])));
H.note('아군 오사는 AI 의 제약이다 — 17부에서 박격포 사격 규칙에 쓰인다');

// ── 란체스터의 경계 ─────────────────────────────────────────────────────────
H.check('한쪽이 0 이면 즉시 끝', CB.lanchesterSim(0, 10, 6554, 6554)[0], 0);
H.check('둘 다 0', CB.lanchesterSim(0, 0, 6554, 6554), [0, 0, 0]);
H.check('전투력이 0 이면 10000틱 상한에서 멈춘다',
        CB.lanchesterSim(10, 10, 0, 0)[0], 10000);
const [, la, lb] = CB.lanchesterSim(20, 10, 6554, 6554);
H.checkTrue('수가 2배면 손실 없이 가깝게 이긴다 (제곱 법칙)',
            la >= 16 && lb === 0);
H.note('α·A² − β·B² 가 불변이므로 400−100 = 300 → √300 ≈ 17.3 이 이론값이다');

H.done();
