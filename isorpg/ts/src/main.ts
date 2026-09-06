// CLI — SPEC §13.
//
// prim / trace / render 의 출력은 세 언어에서 바이트 단위로 같아야 한다.
// 그래서 이 파일의 서식 하나하나가 명세다. TS 에는 printf 가 없으므로
// %4d, %-22s, %8.1f 에 해당하는 자리맞춤 도우미를 직접 만든다.
// 칸 맞춤에 한글을 쓰지 않는 것도 명세다 — 루아의 %-22s 는 바이트로 채운다.
import * as fs from 'fs';
import * as path from 'path';

import * as DICE from './dice';
import * as F from './fixed';
import * as M from './gamemap';
import * as P from './path';
import * as PR from './proj';
import * as SV from './save';
import * as SD from './sortdag';
import { Game, runScriptTrace } from './game';
import { Rng } from './rng';

const ROOT = path.resolve(__dirname, '..', '..', '..');
const GOLDEN = path.join(ROOT, 'golden');

/** %*d. 값이 항상 정수이고 |v| < 2^31 이라 String(v) 가 지수 표기로 새지 않는다.
 *  (1e21 부터는 String 이 "1e+21" 을 내놓는다 — 그래서 상계를 지키는 것이 중요하다.) */
function padLeft(s: string, n: number): string {
  let out = s;
  while (out.length < n) out = ' ' + out;
  return out;
}

function padRight(s: string, n: number): string {
  let out = s;
  while (out.length < n) out += ' ';
  return out;
}

function fmtInt(v: number, width: number): string {
  return padLeft(String(v), width);
}

/** %0*X — 대문자 16진, 왼쪽을 0으로 채운다. */
function hexUp(v: number, width: number): string {
  let s = v.toString(16).toUpperCase();
  while (s.length < width) s = '0' + s;
  return s;
}

const TILE_CASES: Array<[number, number, number]> = [
  [0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0], [2, 0, 0], [0, 2, 0],
  [5, 3, 0], [5, 3, 1], [5, 3, 7], [47, 47, 0], [-1, -1, 0], [24, 24, 15],
];
const PIX_CASES: Array<[number, number]> = [
  [0, 8], [15, 8], [16, 8], [17, 8], [0, 0], [31, 15], [32, 16],
  [-1, 0], [-1, -1], [-16, 8], [-17, 8], [16, 0], [16, 15],
  [159, 99], [319, 199], [-320, -200], [7, 3], [8, 4], [9, 4], [0, 16],
];
const CAM_CASES: Array<[number, number]> = [
  [0, 0], [137, 91], [-137, -91], [768, 640], [-768, -120],
];
const VIS_CASES: Array<[number, number]> = [
  [0, 0], [100, 50], [-200, 300], [700, 700], [-768, -120],
];
const FP_CASES: Array<[number, number]> = [
  [65536, 65536], [65536, 32768], [98304, 98304], [-65536, 32768],
  [-98304, 98304], [1, 65536], [65535, 65535], [46341, 46341],
  [3277, 46341], [-1, 65536], [123456, -654321], [2147483647, 3],
];
const SQRT_N: number[] = [
  0, 1, 2, 3, 4, 8, 15, 16, 17, 1000, 65535, 65536, 1000000,
  4294967295, 8796093022207,
];
const SQRT_X: number[] = [65536, 131072, 196608, 262144, 32768, 6553600];
const TRIG_A: number[] = [0, 8, 16, 24, 32, 40, 48, 56, 64, 96, 128, 160, 192, 224, 255];
const OCT_CASES: Array<[number, number]> = [
  [3, 4], [100, 0], [0, 100], [100, 100], [1000, 414], [-7, 24],
  [65, 72], [1, 1], [0, 0],
];
const OCTILE_CASES: Array<[number, number, number, number]> = [
  [0, 0, 0, 0], [0, 0, 1, 0], [0, 0, 1, 1], [0, 0, 3, 0],
  [0, 0, 3, 3], [0, 0, 5, 2], [10, 10, 2, 7], [0, 0, 47, 47],
];
const CRC_CASES: number[][] = [
  [],
  [0x41],
  [0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39],
  [0x49, 0x53, 0x4f, 0x52, 0x50, 0x47],
  [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
];

/** 골든 프리미티브 보고서. golden/prim.txt 와 한 글자도 달라선 안 된다. */
export function primReport(): string {
  const L: string[] = [];
  const w = (s: string): void => { L.push(s); };

  w('== 1. 타일 -> 화면 ==');
  w('tx ty h  sx sy');
  for (const [tx, ty, h] of TILE_CASES) {
    const s = PR.tileToScreen(tx, ty, h);
    w(tx + ' ' + ty + ' ' + h + '  ' + s[0] + ' ' + s[1]);
  }
  w('');
  w('기저 e_x = (16, 8)   e_y = (-16, 8)   det = 256');
  w('역행렬 * 256 = [[8, 16], [-8, 16]]');
  w('');

  w('== 2. 화면 -> 타일 (대수적 역) ==');
  w('px py  tx ty');
  let same = true;
  for (const [px, py] of PIX_CASES) {
    const t = PR.screenToTile(px, py);
    const q = PR.screenToTileSlow(px, py);
    if (q[0] !== t[0] || q[1] !== t[1]) same = false;
    w(px + ' ' + py + '  ' + t[0] + ' ' + t[1]);
  }
  w('');
  w('마름모 정의(|u| + 2|v| <= 16)로 직접 찾은 타일과 ' + (same ? '전부 일치' : '어긋남'));
  w('');

  w('== 3. 모서리 마스크 32x16 ==');
  for (let oy = 0; oy < 16; oy++) {
    let row = '';
    for (let ox = 0; ox < 32; ox++) row += String(PR.PICK_MASK[oy * 32 + ox]);
    w(row);
  }
  w('');
  const cnt = [0, 0, 0, 0];
  for (const v of PR.PICK_MASK) cnt[v] = (cnt[v] as number) + 1;
  w('값 분포  0:' + cnt[0] + ' 1:' + cnt[1] + ' 2:' + cnt[2] + ' 3:' + cnt[3]
    + '  합 ' + ((cnt[0] as number) + (cnt[1] as number) + (cnt[2] as number) + (cnt[3] as number)));
  let bad = 0;
  for (const [cx, cy] of CAM_CASES) {
    for (let py = 0; py < PR.SCR_H; py++) {
      for (let px = 0; px < PR.SCR_W; px++) {
        const a = PR.pickMask(px + cx, py + cy);
        const b = PR.screenToTile(px + cx, py + cy);
        if (a[0] !== b[0] || a[1] !== b[1]) bad += 1;
      }
    }
  }
  w('전수 확인  카메라 ' + CAM_CASES.length + '개 x ' + PR.SCR_W * PR.SCR_H + '픽셀 = '
    + CAM_CASES.length * PR.SCR_W * PR.SCR_H + '  불일치 ' + bad);
  w('');

  w('== 4. 가시 타일 범위 ==');
  w('camX camY  tx0 ty0 tx1 ty1');
  for (const [cx, cy] of VIS_CASES) {
    const r = PR.visibleRange(cx, cy, cx + PR.SCR_W, cy + PR.SCR_H);
    w(cx + ' ' + cy + '  ' + r[0] + ' ' + r[1] + ' ' + r[2] + ' ' + r[3]);
  }
  w('');

  w('== 5. 고정소수점 16.16 ==');
  w('a b  fp_mul fp_div');
  for (const [a, b] of FP_CASES) {
    w(a + ' ' + b + '  ' + F.fpMul(a, b) + ' ' + F.fpDiv(a, b));
  }
  w('');
  w('fp_floor  ' + F.fpFloor(65536) + ' ' + F.fpFloor(-1) + ' ' + F.fpFloor(-65536)
    + ' ' + F.fpFloor(-65537) + ' ' + F.fpFloor(131071));
  w('');

  w('== 6. 정수 제곱근 ==');
  w('n  isqrt(n)');
  for (const n of SQRT_N) w(n + '  ' + F.isqrt(n));
  w('');
  w('x  fp_sqrt(x)');
  for (const x of SQRT_X) w(x + '  ' + F.fpSqrt(x));
  w('');

  w('== 7. CORDIC 사인/코사인 표 ==');
  w('a  COS SIN');
  for (const a of TRIG_A) w(a + '  ' + F.COS[a] + ' ' + F.SIN[a]);
  w('');
  let sc = 0;
  let ss = 0;
  for (let a = 0; a < 256; a++) {
    sc += F.COS[a] as number;
    ss += F.SIN[a] as number;
  }
  w('sum COS = ' + sc + '   sum SIN = ' + ss);
  let mx = 0;
  for (let a = 0; a < 256; a++) {
    const s = F.SIN[a] as number;
    const c = F.COS[a] as number;
    let e = F.fpMul(s, s) + F.fpMul(c, c) - 65536;
    if (e < 0) e = -e;
    if (e > mx) mx = e;
  }
  w('max |sin^2 + cos^2 - 1| = ' + mx + ' / 65536');
  w('');

  w('== 8. 팔각 거리 근사 ==');
  w('dx dy  oct exact');
  for (const [dx, dy] of OCT_CASES) {
    w(dx + ' ' + dy + '  ' + F.octDist(dx, dy) + ' ' + F.isqrt(dx * dx + dy * dy));
  }
  w('');
  let lo = 1000000000;
  let hi = -1000000000;
  for (let a = 0; a < 256; a++) {
    const dx = F.floordiv(1000 * (F.COS[a] as number), 65536);
    const dy = F.floordiv(1000 * (F.SIN[a] as number), 65536);
    const ex = F.isqrt(dx * dx + dy * dy);
    if (ex === 0) continue;
    const e = F.floordiv((F.octDist(dx, dy) - ex) * 1000000, ex);
    if (e < lo) lo = e;
    if (e > hi) hi = e;
  }
  w('반지름 1000, 256방향  상대오차 ' + lo + ' ~ ' + hi + ' ppm');
  w('');

  w('== 9. LCG (a=22695477, c=1, m=2^32) ==');
  w('i  state rand15');
  let r = new Rng(1);
  for (let i = 0; i < 8; i++) {
    const v = r.next();
    w((i + 1) + '  ' + r.s + ' ' + v);
  }
  w('');
  r = new Rng(12345);
  const eight: string[] = [];
  for (let i = 0; i < 8; i++) eight.push(String(r.next()));
  w('seed 12345 의 처음 8개 rand15: ' + eight.join(' '));
  w('');

  w('== 10. 다이아몬드-스퀘어 5x5 (n=4, seed=1, scale=100, rough 58/100, '
    + 'corners 50/60/70/80) ==');
  for (const row of M.genHeight(4, [50, 60, 70, 80], 100, 1)) {
    w(row.map((v) => fmtInt(v, 4)).join(' '));
  }
  w('');

  w('== 11. 옥타일 휴리스틱 (MIN_MOVE=8) ==');
  w('ax ay bx by  h');
  for (const [ax, ay, bx, by] of OCTILE_CASES) {
    w(ax + ' ' + ay + ' ' + bx + ' ' + by + '  ' + P.octile(ax, ay, bx, by));
  }
  w('');

  w('== 12. 주사위 분포 ==');
  for (const [n, m] of ([[1, 6], [2, 6], [3, 6], [2, 20]] as Array<[number, number]>)) {
    const d = DICE.dist(n, m);
    let tot = 0;
    let esum = 0;
    for (let s = 0; s < d.length; s++) {
      tot += d[s] as number;
      esum += s * (d[s] as number);
    }
    w(n + 'd' + m + '  경우의 수 ' + tot + ' = ' + m + '^' + n
      + '  합계기대값*' + tot + ' = ' + esum);
  }
  w('');
  w('2d6 분포: ' + DICE.dist(2, 6).slice(2).join(' '));
  w('3d6 분포: ' + DICE.dist(3, 6).slice(3).join(' '));
  w('');

  w('== 13. CRC-16/CCITT-FALSE ==');
  w('표 앞 4개: ' + SV.CRC_TBL.slice(0, 4).join(' '));
  w('표 뒤 4개: ' + SV.CRC_TBL.slice(252).join(' '));
  for (const data of CRC_CASES) {
    const hexs = data.map((b) => hexUp(b, 2)).join('');
    w('crc16 [' + hexs + '] = 0x' + hexUp(SV.crc16(data), 4));
  }
  w('');

  w('== 14. 상자 정렬 사례 ==');
  w('case name  겹침쌍 상호쌍 순서 절단');
  const rows = fs.readFileSync(path.join(GOLDEN, 'sortcase.txt'), 'utf8')
    .trim().split('\n').map((l) => l.split(/\s+/));
  let i = 1;
  while (i < rows.length) {
    const head = rows[i] as string[];
    const num = head[1] as string;
    const name = head[2] as string;
    const n = parseInt(head[3] as string, 10);
    i += 1;
    const items: SD.Box[] = [];
    for (let k = 0; k < n; k++) {
      items.push((rows[i + k] as string[]).map((v) => parseInt(v, 10)));
    }
    i += n;
    const [order, br] = SD.topoSort(items);
    const bb = items.map(SD.boxBbox);
    let ov = 0;
    let mu = 0;
    for (let a = 0; a < n; a++) {
      for (let b = a + 1; b < n; b++) {
        if (SD.bboxOverlap(bb[a] as SD.BBox, bb[b] as SD.BBox)) ov += 1;
        if (SD.behind(items[a] as SD.Box, items[b] as SD.Box)
          && SD.behind(items[b] as SD.Box, items[a] as SD.Box)) mu += 1;
      }
    }
    w(num + ' ' + name + '  ' + ov + ' ' + mu + '  ' + order.join(' ') + '  ' + br);
  }
  w('');
  return L.join('\n').replace(/\n+$/, '') + '\n';
}

/** %8.1f 자리. 소수 첫째 자리 반올림은 toFixed(1) 이 해 준다. */
function fmtFixed1(v: number, width: number): string {
  return padLeft(v.toFixed(1), width);
}

/** 구간별 성능. 기계마다 다르므로 파리티 대상이 아니다. */
export function bench(): string {
  const out: string[] = [];
  const t = (name: string, fn: () => void, n: number): void => {
    const s = Date.now();
    for (let i = 0; i < n; i++) fn();
    const d = (Date.now() - s) / 1000;
    out.push(padRight(name, 22) + ' ' + fmtInt(n, 6) + ' x  '
      + fmtFixed1(d * 1000, 8) + ' ms  ' + fmtFixed1((d * 1000000) / n, 10) + ' us/call');
  };
  const g = new Game();
  const m = g.map;
  t('screen_to_tile x1000', () => {
    for (let x = 0; x < 1000; x++) PR.screenToTile(x, x % 200);
  }, 20);
  t('pick_mask x1000', () => {
    for (let x = 0; x < 1000; x++) PR.pickMask(x, x % 200);
  }, 20);
  t('fp_mul x1000', () => {
    for (let x = 0; x < 1000; x++) F.fpMul(x * 7919, 46341);
  }, 20);
  t('isqrt x1000', () => {
    for (let x = 0; x < 1000; x++) F.isqrt(x * 104729);
  }, 20);
  t('astar (24,34)->(24,20)', () => { P.astar(m, 24, 34, 24, 20); }, 50);
  t('dijkstra 48x48', () => { P.dijkstra(m, 24, 34); }, 10);
  t('fog update r=9', () => { g.fog.update(m, 24, 25); }, 100);
  t('game tick', () => { g.tick(); }, 200);
  t('render frame', () => { g.render(); }, 20);
  t('pack_state + crc16', () => { SV.packState(g); }, 100);
  return out.join('\n') + '\n';
}

export function main(argv: string[]): number {
  const cmd = argv.length > 2 ? (argv[2] as string) : 'prim';
  if (cmd === 'prim') {
    process.stdout.write(primReport());
    return 0;
  }
  if (cmd === 'trace') {
    process.stdout.write(runScriptTrace());
    return 0;
  }
  if (cmd === 'render') {
    const out = argv[3] as string;
    const steps = argv.length > 4 ? parseInt(argv[4] as string, 10) : -1;
    const g = new Game();
    g.runScript(null, null, steps < 0 ? null : steps);
    fs.writeFileSync(out, Buffer.from(g.renderPpm()));
    return 0;
  }
  if (cmd === 'bench') {
    process.stdout.write(bench());
    return 0;
  }
  process.stderr.write('모르는 명령: ' + cmd + '\n');
  return 1;
}

if (require.main === module) {
  process.exitCode = main(process.argv);
}
