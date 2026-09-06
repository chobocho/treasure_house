// CLI — 세 언어가 같은 부명령을 갖는다 (SPEC §24).
//
//    `prim` 의 출력은 `golden/prim.txt` 와 **바이트 단위로 같아야 한다.** 절 구분
//    `== N. 제목 ==` 은 명세이며, 덱의 `<!--OUT sec=N-->` 지시자가 이 표시로 절을
//    잘라 온다.
//
//    여기에 박힌 시험 입력들(거리 쌍·제곱근 인자·피해 조합…)은 `tools/gen_prim.py`
//    의 것과 **같아야 한다.** 두 곳에 적히는 유일한 자료이며, 둘이 어긋나면
//    `cmp` 가 그 자리에서 잡는다 — 그래서 굳이 한 곳으로 합치지 않았다.
//    합치면 "둘 다 같은 실수를 했다"는 사고를 막을 수 없다.

import * as fs from 'fs';
import * as path from 'path';

import * as AI from './ai';
import * as CI from './circle';
import * as CB from './combat';
import * as C from './const';
import * as E from './econ';
import * as F from './fixed';
import * as FL from './flow';
import { Fog } from './fog';
import { fixed3, hex4, hex8, padLeft, padRight, pyRepr } from './fmt';
import * as HP from './hpa';
import * as JP from './jps';
import * as P from './path';
import * as RS from './raster';
import * as RD from './render';
import * as RP from './replay';
import { LCG } from './rng';
import * as SIM from './sim';
import * as SK from './speaker';
import * as T from './tmap';

// py/rts/main.py 와 같은 방식으로 저장소 뿌리를 찾는다: 이 파일에서 세 번 올라간다.
// (파이썬은 py/rts/main.py → py/rts → py → 뿌리, 여기는 ts/dist/src → ts/dist → ts → 뿌리)
const BASE = path.join(__dirname, '..', '..', '..');
const GOLDEN = path.join(BASE, 'golden');

const PAIRS_M: Array<[number, number]> = [
  [1, 0], [0, 1], [1, 1], [2, 1], [3, 1], [3, 2], [4, 3], [5, 5],
  [8, 3], [10, 0], [10, 10], [-7, 4], [-6, -6], [0, -9], [12, -5], [-3, 11]];
const SQ_N = [0, 1, 2, 3, 15, 16, 17, 99, 100, 65535, 65536, 1000000, 2147483647];
const ANG_V: Array<[number, number]> = [
  [12, 5], [12, -5], [12, 6], [5, 12], [12, 4], [-12, 5], [-5, -12],
  [0, 0], [1, 0], [0, -1], [7, 3], [3, 7], [-9, -4], [4, -9],
  [100, 41], [100, 42]];
const DMG_CASE: Array<[number, number, number]> = [
  [6, 3, 0], [6, 3, 2], [6, 3, 5], [6, 3, 9], [9, 1, 0], [9, 1, 4],
  [12, 8, 3], [12, 8, 11], [4, 0, 0], [4, 0, 3], [20, 12, 6], [2, 2, 4]];
const LAN_CASE: Array<[number, number, number, number]> = [
  [10, 10, 6554, 6554], [20, 10, 6554, 6554], [10, 20, 6554, 6554],
  [30, 20, 3277, 6554], [5, 5, 13107, 13107], [50, 40, 1311, 1311],
  [12, 8, 6554, 9830], [100, 100, 655, 655]];
const ECON_CASE: Array<[number, number]> = [
  [0, 6554], [4, 6554], [8, 6554], [16, 6554], [8, 13107], [8, 3277]];
const FOG_UNITS: Array<[[number, number], number]> = [
  [[10, 10], 3], [[12, 11], 5], [[30, 30], 8]];
const FLOWMAP = [
  '............',
  '.##########.',
  '.#........#.',
  '.#.######.#.',
  '.#.#....#.#.',
  '.#.#.##.#.#.',
  '.#.#.##.#.#.',
  '.#.#....#.#.',
  '.#.######.#.',
  '.#........#.',
  '.##########.',
  '............',
];

function golden(name: string): string {
  return fs.readFileSync(path.join(GOLDEN, name), 'utf8');
}

function maps(): T.TMap[] {
  const out: T.TMap[] = [];
  for (let i = 1; i <= 6; i += 1) {
    out.push(T.TMap.loadText(golden('map_' + i + '.txt')));
  }
  return out;
}

function flowmap(): T.TMap {
  const m = new T.TMap(FLOWMAP[0].length, FLOWMAP.length);
  for (let y = 0; y < FLOWMAP.length; y += 1) {
    for (let x = 0; x < FLOWMAP[y].length; x += 1) {
      m.terrain[y * m.w + x] = FLOWMAP[y][x] === '#' ? T.ROCK : T.DIRT;
      m.repass(y * m.w + x);
    }
  }
  m.bump();
  return m;
}

// ── prim 의 절들 ────────────────────────────────────────────────────────────
function sec1(o: string[]): void {
  o.push('== 1. 거리 척도 ==');
  o.push('  dx   dy     d1  dinf   d83   dab   doct     eu3  d83pm  dabpm'
         + ' doctpm');
  for (const [dx, dy] of PAIRS_M) {
    const eu = F.isqrt((dx * dx + dy * dy) * 1000000);
    o.push(padLeft(dx, 4) + ' ' + padLeft(dy, 4) + ' '
           + padLeft(F.d1(dx, dy), 6) + ' ' + padLeft(F.dinf(dx, dy), 5) + ' '
           + padLeft(F.d83(dx, dy), 5) + ' ' + padLeft(F.dab(dx, dy), 5) + ' '
           + padLeft(F.doct(dx, dy), 6) + ' ' + padLeft(eu, 7) + ' '
           + padLeft(F.floordiv(F.d83(dx, dy) * 1000000, eu) - 1000, 6) + ' '
           + padLeft(F.floordiv(F.dab(dx, dy) * 1000000, eu) - 1000, 6) + ' '
           + padLeft(F.floordiv(F.doct(dx, dy) * 100000, eu) - 1000, 6));
  }
  o.push('eu3 = floor(sqrt(dx^2+dy^2) * 1000)');
  o.push('d83pm dabpm = 유클리드 대비 천분율 편차');
  o.push('doctpm = 유클리드*10 대비. 옥타일은 유클리드 근사가 아니므로'
         + ' 참고값이며,');
  o.push('참 옥타일과의 비교는 out/analysis.txt 2절에 있다.');
}

function sec2(o: string[]): void {
  o.push('== 2. 정수 제곱근 ==');
  o.push('          n     isqrt          isqrt^2      (isqrt+1)^2');
  for (const n of SQ_N) {
    const r = F.isqrt(n);
    o.push(padLeft(n, 11) + ' ' + padLeft(r, 9) + ' ' + padLeft(r * r, 16)
           + ' ' + padLeft((r + 1) * (r + 1), 16));
  }
}

function sec3(o: string[]): void {
  o.push('== 3. 8방향 판별 ==');
  o.push('  dx   dy  12*mn  5*mx  대각  방향  이름');
  for (const [dx, dy] of ANG_V) {
    const ax = Math.abs(dx);
    const ay = Math.abs(dy);
    const mx = Math.max(ax, ay);
    const mn = Math.min(ax, ay);
    const d = F.atan8(dx, dy);
    o.push(padLeft(dx, 4) + ' ' + padLeft(dy, 4) + ' ' + padLeft(12 * mn, 6)
           + ' ' + padLeft(5 * mx, 5) + ' '
           + padLeft(12 * mn > 5 * mx ? 1 : 0, 5) + ' ' + padLeft(d, 5)
           + '  ' + F.DNAME[d]);
  }
}

function sec4(o: string[]): void {
  o.push('== 4. LCG ==');
  const r = new LCG(1);
  o.push('  i           상태   next15');
  for (let i = 0; i < 10; i += 1) {
    const v = r.next15();
    o.push(padLeft(i + 1, 3) + ' ' + padLeft(r.s, 14) + ' ' + padLeft(v, 8));
  }
  o.push('하위 비트의 짧은 주기 — 상태의 최하위 1·2비트');
  const r2 = new LCG(1);
  const b1: number[] = [];
  const b2: number[] = [];
  for (let k = 0; k < 16; k += 1) {
    r2.next15();
    b1.push(F.fmod(r2.s, 2));
    b2.push(F.fmod(r2.s, 4));
  }
  o.push('  bit0: ' + b1.join(' '));
  o.push('  bit10: ' + b2.join(' '));
  const r3 = new LCG(2026);
  const v20: number[] = [];
  for (let k = 0; k < 20; k += 1) v20.push(r3.roll(6));
  o.push('roll(6) x20: ' + v20.join(' '));
  o.push('기각 횟수 ' + r3.rejects);
  const r4 = new LCG(2026);
  const hist = [0, 0, 0, 0, 0, 0];
  for (let k = 0; k < 6000; k += 1) hist[r4.roll(6)] += 1;
  o.push('roll(6) x6000 도수: ' + hist.join(' '));
  o.push('기각 횟수 ' + r4.rejects);
}

function sec5(o: string[]): void {
  o.push('== 5. 오토타일 ==');
  o.push('클래스 ' + T.CLASS_COUNT + '개');
  o.push('정규화 인덱스 (마스크 0..255, 16개씩)');
  for (let row = 0; row < 16; row += 1) {
    const cells: string[] = [];
    for (let c = 0; c < 16; c += 1) {
      cells.push(padLeft(T.canonIndex(T.canon(row * 16 + c)), 3));
    }
    o.push('  ' + cells.join(' '));
  }
  o.push('클래스별 마스크 개수');
  const cls = T.classes();
  for (let row = 0; row < cls.length; row += 8) {
    const cells: string[] = [];
    for (let i = row; i < Math.min(row + 8, cls.length); i += 1) {
      let n = 0;
      for (let k = 0; k < 256; k += 1) {
        if (T.canon(k) === cls[i]) n += 1;
      }
      cells.push(padLeft(cls[i], 3) + ':' + padRight(n, 3));
    }
    o.push('  ' + cells.join(' '));
  }
}

function sec6(o: string[]): void {
  o.push('== 6. 원 마스크 ==');
  o.push(' r    개수  span');
  for (let r = 1; r <= 8; r += 1) {
    o.push(padLeft(r, 2) + ' ' + padLeft(CI.count(r), 7) + '  '
           + CI.spans(r).join(' '));
  }
}

function sec7(o: string[], ms: T.TMap[]): void {
  o.push('== 7. 경로 탐색 ==');
  o.push('맵 출발      도착      BFS걸음  다익스트라   A*비용  A*연노드');
  for (let i = 0; i < ms.length; i += 1) {
    const m = ms[i];
    for (const [s, t] of m.pairs) {
      const b = P.bfs(m, 0, s, t);
      let dj = P.dijkstra(m, 0, [s[1] * m.w + s[0]],
                          t[1] * m.w + t[0])[t[1] * m.w + t[0]];
      if (dj >= P.INF) dj = -1;
      const [a, , ex] = P.astar(m, 0, s, t);
      o.push(padLeft(i + 1, 2) + ' (' + padLeft(s[0], 2) + ','
             + padLeft(s[1], 2) + ') -> (' + padLeft(t[0], 2) + ','
             + padLeft(t[1], 2) + ') ' + padLeft(b, 8) + ' ' + padLeft(dj, 11)
             + ' ' + padLeft(a, 8) + ' ' + padLeft(ex, 9));
    }
  }
  o.push('다익스트라와 A* 의 비용은 모든 줄에서 같아야 한다 (정리 8.1)');
}

function sec8(o: string[], ms: T.TMap[]): void {
  o.push('== 8. HPA* 와 JPS ==');
  o.push('맵 출발      도착        A*   JPS  JPS연노드   HPA*  HPA*/A*(pm)');
  for (let i = 0; i < ms.length; i += 1) {
    const m = ms[i];
    for (const [s, t] of m.pairs) {
      const a = P.astar(m, 0, s, t)[0];
      const [j, , jx] = JP.search(m, 0, s, t);
      const hp = HP.search(m, 0, s, t)[0];
      const ratio = (a <= 0 || hp <= 0) ? -1 : F.floordiv(hp * 1000, a);
      o.push(padLeft(i + 1, 2) + ' (' + padLeft(s[0], 2) + ','
             + padLeft(s[1], 2) + ') -> (' + padLeft(t[0], 2) + ','
             + padLeft(t[1], 2) + ') ' + padLeft(a, 6) + ' ' + padLeft(j, 5)
             + ' ' + padLeft(jx, 10) + ' ' + padLeft(hp, 6) + ' '
             + padLeft(ratio, 12));
    }
  }
  o.push('JPS 비용은 모든 줄에서 A* 와 같아야 한다 (정리 10.1)');
}

function sec9(o: string[]): void {
  o.push('== 9. 흐름장과 클리어런스 ==');
  const m = flowmap();
  const integ = FL.integration(m, 0, [[4, 4]]);
  const fl = FL.flowDirs(m, 0, integ);
  const cl = FL.clearance(m, 0);
  o.push('목표 (4,4) · 적분장');
  for (let y = 0; y < m.h; y += 1) {
    const cells: string[] = [];
    for (let x = 0; x < m.w; x += 1) cells.push(padLeft(integ[y * m.w + x], 5));
    o.push('  ' + cells.join(' '));
  }
  o.push('경사장 (방향 번호, 255=정지)');
  for (let y = 0; y < m.h; y += 1) {
    const cells: string[] = [];
    for (let x = 0; x < m.w; x += 1) cells.push(padLeft(fl[y * m.w + x], 3));
    o.push('  ' + cells.join(' '));
  }
  o.push('클리어런스 (좌상단 기준 정사각 여유)');
  for (let y = 0; y < m.h; y += 1) {
    const cells: string[] = [];
    for (let x = 0; x < m.w; x += 1) cells.push(padLeft(cl[y * m.w + x], 2));
    o.push('  ' + cells.join(' '));
  }
}

function sec10(o: string[]): void {
  o.push('== 10. 안개 참조 카운트 ==');

  const report = (tag: string, us: Array<[[number, number], number]>): void => {
    const fg = new Fog(64, 64, 1);
    for (const [[x, y], r] of us) fg.addSight(0, x, y, r);
    const cnt = fg.count[0];
    let tot = 0;
    let vis = 0;
    let mx = 0;
    for (const v of cnt) {
      tot += v;
      if (v > 0) vis += 1;
      if (v > mx) mx = v;
    }
    const hist = new Array<number>(mx + 1).fill(0);
    for (const v of cnt) {
      if (v !== 0) hist[v] += 1;
    }
    o.push(tag + ' 가시 칸 ' + vis + ' · 카운트 합 ' + tot + ' · 최대 ' + mx);
    const parts: string[] = [];
    for (let k = 1; k <= mx; k += 1) parts.push(k + ':' + hist[k]);
    o.push('  도수: ' + parts.join(' '));
  };

  report('초기', FOG_UNITS);
  const moved: Array<[[number, number], number]> =
    ([[[11, 10], 3]] as Array<[[number, number], number]>)
      .concat(FOG_UNITS.slice(1));
  report('1번 유닛 (10,10)->(11,10)', moved);
  report('3번 유닛 사망', moved.slice(0, 2));
  const fg = new Fog(64, 64, 1);
  let tot = 0;
  for (const v of fg.count[0]) tot += v;
  o.push('전원 제거 후 카운트 합 ' + tot);
}

function sec11(o: string[]): void {
  o.push('== 11. 전투 ==');
  o.push('기본 관통 방어    mx    lo    n   E*100  모의평균*100');
  for (const [basic, pierce, armour] of DMG_CASE) {
    const mx = CB.maxDamage(basic, pierce, armour);
    const lo = CB.damageLo(mx);
    const r = new LCG(12345);
    let tot = 0;
    for (let k = 0; k < 1000; k += 1) {
      tot += CB.rollDamage(r, basic, pierce, armour);
    }
    o.push(padLeft(basic, 4) + ' ' + padLeft(pierce, 4) + ' '
           + padLeft(armour, 4) + ' ' + padLeft(mx, 5) + ' ' + padLeft(lo, 5)
           + ' ' + padLeft(mx - lo + 1, 4) + ' '
           + padLeft(CB.expect100(basic, pierce, armour), 7) + ' '
           + padLeft(F.floordiv(tot * 100, 1000), 13));
  }
  o.push('란체스터 제곱 법칙 시뮬 (A0 B0 alpha beta -> 틱 A남음 B남음)');
  for (const [a0, b0, al, be] of LAN_CASE) {
    const [t, a, b] = CB.lanchesterSim(a0, b0, al, be);
    o.push(padLeft(a0, 4) + ' ' + padLeft(b0, 4) + ' ' + padLeft(al, 6) + ' '
           + padLeft(be, 6) + ' ' + padLeft(t, 8) + ' ' + padLeft(a, 8) + ' '
           + padLeft(b, 8));
  }
}

function sec12(o: string[]): void {
  o.push('== 12. 경제 ==');
  o.push('왕복타일 속도(fp)   총틱   수입*10000');
  for (const [d, v] of ECON_CASE) {
    o.push(padLeft(d, 8) + ' ' + padLeft(v, 10) + ' '
           + padLeft(E.roundTripTicks(d, v), 6) + ' '
           + padLeft(E.income10000(d, v), 12));
  }
  o.push('적재 ' + E.LOAD_MAX + ' · 틱당 채굴 ' + E.MINE_PER_TICK
         + ' · 반납 ' + E.UNLOAD_TICKS + '틱');
}

function sec13(o: string[]): void {
  o.push('== 13. CRC 와 FNV ==');
  for (const s of ['123456789', '', 'A', 'RTSM', 'the quick brown fox']) {
    const b = F.ascii(s);
    o.push('crc16 ' + padRight(pyRepr(s), 20) + ' ' + padLeft(F.crc16(b), 6)
           + ' 0x' + hex4(F.crc16(b)));
  }
  for (const s of ['', 'a', 'foobar', 'RTSM']) {
    const b = F.ascii(s);
    o.push('fnv1a ' + padRight(pyRepr(s), 20) + ' ' + padLeft(F.fnv1a(b), 12)
           + ' 0x' + hex8(F.fnv1a(b)));
  }
  const b16: number[] = [];
  for (let k = 0; k < 16; k += 1) b16.push(k);
  o.push('fnv1a bytes(0..15) ' + padLeft(F.fnv1a(b16), 12) + ' 0x'
         + hex8(F.fnv1a(b16)));
}

function sec14(o: string[]): void {
  o.push('== 14. PIT 분주값 ==');
  o.push('음   목표Hz  분주값   실제Hz*100   차이*100');
  for (let k = 0; k < SK.NOTE_NAME.length; k += 1) {
    const f = SK.NOTE_HZ[k];
    const div = SK.divisor(f);
    const act = SK.actual100(f);
    o.push(padRight(SK.NOTE_NAME[k], 4) + ' ' + padLeft(f, 6) + ' '
           + padLeft(div, 7) + ' ' + padLeft(act, 12) + ' '
           + padLeft(act - f * 100, 10));
  }
}

export function cmdPrim(): string {
  const ms = maps();
  const o: string[] = [];
  sec1(o); o.push('');
  sec2(o); o.push('');
  sec3(o); o.push('');
  sec4(o); o.push('');
  sec5(o); o.push('');
  sec6(o); o.push('');
  sec7(o, ms); o.push('');
  sec8(o, ms); o.push('');
  sec9(o); o.push('');
  sec10(o); o.push('');
  sec11(o); o.push('');
  sec12(o); o.push('');
  sec13(o); o.push('');
  sec14(o);
  return o.join('\n') + '\n';
}

// ── 시나리오 ────────────────────────────────────────────────────────────────
function scenario(ticks?: number | null,
                  floatBug = false): [SIM.Sim, SIM.Script, number] {
  const m = T.TMap.loadText(golden('map_start.txt'));
  const sc = SIM.parseScript(golden('script.txt'));
  const s = new SIM.Sim(m, 1, sc.players, floatBug);
  s.setupStart(false);                 // §18.6 — 스크립트가 몬다
  return [s, sc, (ticks === undefined || ticks === null) ? sc.ticks : ticks];
}

// §17.5 의 러시 타이밍을 재는 별도 실행. 스크립트 없이 AI 끼리 붙인다.
function aiGame(ticks: number, seed = 1, seven = false): [SIM.Sim, number] {
  const m = T.TMap.loadText(golden('map_start.txt'));
  const s = new SIM.Sim(m, seed, 2);
  s.setupStart(true);
  if (seven) s.aiRules = AI.RULES7;
  return [s, ticks];
}

function evJson(e: number[]): string {
  const v = e.concat([0, 0, 0, 0]);
  return '[' + v[0] + ',' + v[1] + ',' + v[2] + ',' + v[3] + ']';
}

// §18.3 — 키 순서와 공백까지 명세다. JSON 직렬화기를 믿지 않는다.
export function cmdTrace(ticks?: number | null): string {
  const [s, sc, n] = scenario(ticks);
  const out: string[] = [];
  for (let t = 1; t <= n; t += 1) {
    const h = s.step(s.scriptOrders(sc, t));
    let alive = 0;
    for (let i = 1; i < C.MAX_ENT; i += 1) {
      if (s.w.alive[i] !== 0) alive += 1;
    }
    const cr: string[] = [];
    const su: string[] = [];
    const scp: string[] = [];
    for (let p = 0; p < sc.players; p += 1) {
      cr.push(String(s.ec.credits[p]));
      su.push(String(s.ec.supplyUsed[p]));
      scp.push(String(s.ec.supplyCap[p]));
    }
    out.push('{"t":' + t + ',"h":"' + hex8(h) + '","cr":[' + cr.join(',')
             + '],"su":[' + su.join(',') + '],"sc":[' + scp.join(',')
             + '],"n":' + alive + ',"ev":['
             + s.events.map((e) => evJson(e)).join(',') + ']}');
  }
  return out.join('\n') + '\n';
}

export function cmdAigame(ticks = 1200, seven = false): string {
  const [s, n] = aiGame(ticks, 1, seven);
  const out: string[] = [];
  for (let t = 1; t <= n; t += 1) {
    const h = s.step([]);
    let alive = 0;
    for (let i = 1; i < C.MAX_ENT; i += 1) {
      if (s.w.alive[i] !== 0) alive += 1;
    }
    out.push('{"t":' + t + ',"h":"' + hex8(h) + '","cr":[' + s.ec.credits[0]
             + ',' + s.ec.credits[1] + '],"su":[' + s.ec.supplyUsed[0] + ','
             + s.ec.supplyUsed[1] + '],"sc":[' + s.ec.supplyCap[0] + ','
             + s.ec.supplyCap[1] + '],"n":' + alive + ',"ev":['
             + s.events.map((e) => evJson(e)).join(',') + ']}');
  }
  return out.join('\n') + '\n';
}

export function cmdHashes(ticks?: number | null): string {
  const [s, sc, n] = scenario(ticks);
  const out: string[] = [];
  for (let t = 1; t <= n; t += 1) {
    out.push(t + ' ' + hex8(s.step(s.scriptOrders(sc, t))));
  }
  return out.join('\n') + '\n';
}

export function cmdRender(p: string, tick = 1): string {
  const [s, sc] = scenario();
  for (let t = 1; t <= tick; t += 1) s.step(s.scriptOrders(sc, t));
  const pal = RS.buildPalette();
  const light = RS.buildLight(pal);
  const view = new RD.View();
  view.centerOn(s.m, s.m.starts[0][0], s.m.starts[0][1]);
  const fb = new RS.Frame();
  RD.draw(fb.fb, s, view, 0, pal, light, 0, [], 'TICK ' + tick);
  fs.writeFileSync(p, Buffer.from(RS.toPpm(fb.fb, pal)));
  return p + ' — 틱 ' + tick + '\n';
}

// §19.3·§19.4 — 두 시뮬 대조와 부동소수점 주입 실험.
export function cmdLockstep(ticks = 300): string {
  const out: string[] = [];
  const [a, sc] = scenario(ticks);
  const [b, sc2] = scenario(ticks);
  let same = true;
  for (let t = 1; t <= ticks; t += 1) {
    const ha = a.step(a.scriptOrders(sc, t));
    const hb = b.step(b.scriptOrders(sc2, t));
    if (ha !== hb) {
      same = false;
      out.push(t + '틱에서 갈렸다 ' + hex8(ha) + ' vs ' + hex8(hb));
      break;
    }
  }
  if (same) out.push('락스텝 ' + ticks + '틱 일치');
  const [c, sc3] = scenario(ticks);
  const [d, sc4] = scenario(ticks, true);
  let firstHash = -1;
  let firstTile = -1;
  for (let t = 1; t <= ticks; t += 1) {
    const hc = c.step(c.scriptOrders(sc3, t));
    const hd = d.step(d.scriptOrders(sc4, t));
    if (firstHash < 0 && hc !== hd) firstHash = t;
    if (firstTile < 0) {
      let diff = false;
      for (let i = 1; i < C.MAX_ENT; i += 1) {
        if (c.w.alive[i] !== d.w.alive[i] || c.w.tx[i] !== d.w.tx[i]
            || c.w.ty[i] !== d.w.ty[i]) {
          diff = true;
          break;
        }
      }
      if (diff) firstTile = t;
    }
  }
  out.push('float_bug: 해시가 갈린 틱 ' + firstHash + ' · 타일 좌표가 갈린 틱 '
           + firstTile);
  out.push('타일이 -1 이면 ' + ticks + '틱 동안 화면에서는 같아 보였다는 뜻이다');
  return out.join('\n') + '\n';
}

// §20.2 — **상태는 한 바이트도 저장하지 않는다.** 명령이 없는 틱은 아예
// 적지 않고, 재생은 머리의 총 틱 수만큼 돌면서 해당 틱에만 명령을 먹인다.
export function cmdReplay(p: string, ticks?: number | null): string {
  const [s, sc, n] = scenario(ticks);
  const log: RP.LogEntry[] = [];
  for (let t = 1; t <= n; t += 1) {
    const orders = s.scriptOrders(sc, t);
    if (orders.length > 0) log.push([t, orders]);
    s.step(orders);
  }
  const blob = RP.save(1, sc.players, n, log);
  fs.writeFileSync(p, Buffer.from(blob));
  const [seed, players, tk, log2] = RP.load(blob);
  const s2 = new SIM.Sim(T.TMap.loadText(golden('map_start.txt')), seed,
                         players);
  s2.setupStart(false);                // 원본과 같은 조건이어야 한다
  const at = new Map<number, number[][]>();
  for (const [t, orders] of log2) at.set(t, orders);
  for (let t = 1; t <= tk; t += 1) {
    const o = at.get(t);
    s2.step(o === undefined ? [] : o);
  }
  const same = s2.stateHash() === s.stateHash();
  let nOrders = 0;
  for (const [, o] of log2) nOrders += o.length;
  return '리플레이 ' + blob.length + '바이트 · ' + tk + '틱 · 명령 ' + nOrders
    + '줄 · 재생 해시 ' + hex8(s2.stateHash()) + ' '
    + (same ? '일치' : '불일치') + '\n';
}

export function cmdBench(): string {
  const out: string[] = [];
  const ms = maps();
  let t0 = Date.now();
  for (let k = 0; k < 20; k += 1) {
    for (const m of ms) {
      for (const [s, t] of m.pairs) P.astar(m, 0, s, t);
    }
  }
  out.push('1. A* ' + (20 * 6 * 4) + '회 ' + fixed3((Date.now() - t0) / 1000)
           + '초');
  t0 = Date.now();
  for (let k = 0; k < 20; k += 1) {
    for (const m of ms) {
      for (const [s, t] of m.pairs) JP.search(m, 0, s, t);
    }
  }
  out.push('2. JPS ' + (20 * 6 * 4) + '회 ' + fixed3((Date.now() - t0) / 1000)
           + '초');
  const m0 = T.TMap.loadText(golden('map_start.txt'));
  t0 = Date.now();
  for (let k = 0; k < 5; k += 1) FL.integration(m0, 0, [[32, 32]]);
  out.push('3. 흐름장 5회 ' + fixed3((Date.now() - t0) / 1000) + '초');
  t0 = Date.now();
  const [s, sc] = scenario(200);
  for (let t = 1; t <= 200; t += 1) s.step(s.scriptOrders(sc, t));
  out.push('4. 시뮬 200틱 ' + fixed3((Date.now() - t0) / 1000) + '초');
  const pal = RS.buildPalette();
  t0 = Date.now();
  RS.buildLight(pal);
  out.push('5. 명암표 1회 ' + fixed3((Date.now() - t0) / 1000) + '초');
  const fb = new RS.Frame();
  const light = RS.buildLight(pal);
  t0 = Date.now();
  for (let k = 0; k < 10; k += 1) {
    RD.draw(fb.fb, s, new RD.View(), 0, pal, light, 0, [], '');
  }
  out.push('6. 렌더 10프레임 ' + fixed3((Date.now() - t0) / 1000) + '초');
  return out.join('\n') + '\n';
}

export function cmdSpeaker(p: string): string {
  const notes: Array<[number, number]> = [0, 4, 7, 12].map(
    (k) => [SK.NOTE_HZ[k], 2200] as [number, number]);
  const blob = SK.tune(notes);
  fs.writeFileSync(p, Buffer.from(blob));
  return p + ' — ' + blob.length + '바이트 · FNV ' + hex8(F.fnv1a(blob)) + '\n';
}

export function main(argv: string[]): number {
  if (argv.length === 0) {
    process.stdout.write('부명령: prim trace hashes aigame render lockstep'
                         + ' replay bench speaker\n');
    return 1;
  }
  const cmd = argv[0];
  const arg1 = argv.length > 1 ? parseInt(argv[1], 10) : null;
  if (cmd === 'prim') process.stdout.write(cmdPrim());
  else if (cmd === 'trace') process.stdout.write(cmdTrace(arg1));
  else if (cmd === 'aigame') {
    process.stdout.write(cmdAigame(arg1 === null ? 1200 : arg1));
  } else if (cmd === 'aigame7') {
    process.stdout.write(cmdAigame(arg1 === null ? 1200 : arg1, true));
  } else if (cmd === 'hashes') process.stdout.write(cmdHashes(arg1));
  else if (cmd === 'render') {
    process.stdout.write(cmdRender(argv[1],
                                   argv.length > 2 ? parseInt(argv[2], 10) : 1));
  } else if (cmd === 'lockstep') {
    process.stdout.write(cmdLockstep(arg1 === null ? 300 : arg1));
  } else if (cmd === 'replay') {
    process.stdout.write(cmdReplay(argv[1],
                                   argv.length > 2 ? parseInt(argv[2], 10) : null));
  } else if (cmd === 'bench') process.stdout.write(cmdBench());
  else if (cmd === 'speaker') process.stdout.write(cmdSpeaker(argv[1]));
  else {
    process.stdout.write('모르는 부명령: ' + cmd + '\n');
    return 1;
  }
  return 0;
}

if (require.main === module) {
  process.exitCode = main(process.argv.slice(2));
}
