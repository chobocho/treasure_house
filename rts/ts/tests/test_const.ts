// 상수표와 유닛·건물표 (SPEC §0, §25).
//
//    이 시험만 SPEC.md 를 **직접 읽어** 표와 코드를 대조한다. 손으로 옮겨 적은
//    숫자는 반드시 언젠가 한 자리가 틀리고, 그 한 자리는 1200틱 뒤 해시 불일치로만
//    드러난다. 파이썬 쪽과 같은 표를 같은 방법으로 파싱한다 — 마크다운 파싱을
//    포기하고 숫자를 손으로 옮겨 적으면 이 시험의 존재 이유가 사라진다.

import * as fs from 'fs';
import * as path from 'path';

import * as H from './harness';
import * as C from '../src/const';

H.title('const');

const SPEC = fs.readFileSync(path.join(H.BASE, 'SPEC.md'), 'utf8').split('\n');

// 이름으로 const 의 값을 꺼낸다 (파이썬 getattr 자리).
const CV = C as unknown as Record<string, unknown>;

function scalar(name: string): number | undefined {
  const v = CV[name];
  return typeof v === 'number' ? v : undefined;
}

function tableOf(name: string): number[] {
  return CV[name] as number[];
}

// 지정한 절 제목 뒤 첫 마크다운 표의 데이터 행을 셀 목록으로 돌려준다.
function tableRows(header: string): string[][] {
  let i = SPEC.indexOf(header);
  while (SPEC[i].indexOf('|') !== 0) i += 1;
  i += 2;                                   // 머리글과 구분선을 건너뛴다
  const out: string[][] = [];
  while (i < SPEC.length && SPEC[i].indexOf('|') === 0) {
    let ln = SPEC[i];
    while (ln.length > 0 && ln[0] === '|') ln = ln.slice(1);
    while (ln.length > 0 && ln[ln.length - 1] === '|') ln = ln.slice(0, -1);
    out.push(ln.split('|').map((c) => c.trim()));
    i += 1;
  }
  return out;
}

function num(s0: string): number {
  const s = s0.split('(')[0].trim().replace(/`/g, '');
  if (s === '—' || s === '-' || s === '') return 0;
  if (s.slice(0, 2).toLowerCase() === '0x') return parseInt(s.slice(2), 16);
  return parseInt(s, 10);
}

// ── §0 상수표 ───────────────────────────────────────────────────────────────
let bad = 0;
let n = 0;
for (const cells of tableRows('## 0. 상수')) {
  const name = cells[0].replace(/`/g, '').replace(/\\/g, '');
  const got = scalar(name);
  if (got === undefined) {
    H.note(name + ' 가 const 에 없다');
    bad += 1;
    continue;
  }
  n += 1;
  if (got !== num(cells[1])) {
    H.note(name + ' 기대 ' + cells[1] + ' 실제 ' + got);
    bad += 1;
  }
}
H.check('§0 상수 ' + n + '개가 표와 같다', bad, 0);

// ── §25.1 유닛표 ────────────────────────────────────────────────────────────
const COLS = ['HP', 'BASIC', 'PIERCE', 'ARMOUR', 'RANGE', 'RELOAD',
              'SPEED', 'SIGHT', 'COST', 'BUILD_TICKS', 'POP'];
bad = 0;
const kinds: number[] = [];
for (const cells of tableRows('### 25.1 유닛')) {
  const k = parseInt(cells[0], 10);
  kinds.push(k);
  const short = cells[1].split('`')[1];
  if (scalar(short) !== k) {
    H.note(short + ' 번호 기대 ' + k + ' 실제 ' + scalar(short));
    bad += 1;
  }
  for (let j = 0; j < COLS.length; j += 1) {
    const got = tableOf(COLS[j])[k];
    if (got !== num(cells[2 + j])) {
      H.note(short + '.' + COLS[j] + ' 기대 ' + cells[2 + j] + ' 실제 ' + got);
      bad += 1;
    }
  }
  if (C.NAME[k] !== cells[1].split('`')[0].trim()) bad += 1;
  if (C.FOOT[k] !== 1 || C.IS_BUILDING[k] !== 0) bad += 1;
}
H.check('§25.1 유닛 ' + kinds.length + '종 × ' + (COLS.length + 3) + '칸', bad, 0);
H.check('유닛 번호는 0..4', kinds, [0, 1, 2, 3, 4]);

// ── §25.2 건물표 ────────────────────────────────────────────────────────────
const BCOLS = ['HP', 'ARMOUR', 'SIGHT', 'COST', 'BUILD_TICKS', 'POP'];
bad = 0;
const bkinds: number[] = [];
for (const cells of tableRows('### 25.2 건물')) {
  const k = parseInt(cells[0], 10);
  bkinds.push(k);
  const short = cells[1].split('`')[1];
  if (scalar(short) !== k) bad += 1;
  if (C.FOOT[k] !== parseInt(cells[2].split('×')[0], 10)) {
    H.note(short + ' 발자국 기대 ' + cells[2] + ' 실제 ' + C.FOOT[k]);
    bad += 1;
  }
  for (let j = 0; j < BCOLS.length; j += 1) {
    if (tableOf(BCOLS[j])[k] !== num(cells[3 + j])) {
      H.note(short + '.' + BCOLS[j] + ' 기대 ' + cells[3 + j]
             + ' 실제 ' + tableOf(BCOLS[j])[k]);
      bad += 1;
    }
  }
  if (C.IS_BUILDING[k] !== 1) bad += 1;
}
H.check('§25.2 건물 ' + bkinds.length + '종 × ' + (BCOLS.length + 2) + '칸', bad, 0);
H.check('건물 번호는 10..15', bkinds, [10, 11, 12, 13, 14, 15]);

// 방어탑의 공격 수치는 비고 칸에만 있다 — 거기서도 읽어 온다
const tower = tableRows('### 25.2 건물').filter((c) => c[0] === '15')[0][9];
const vals = tower.split('·').map(
  (part) => parseInt(part.replace(/[^0-9]/g, ''), 10));
H.check('방어탑 기본·관통·사거리·재장전',
        [C.BASIC[C.TOWER], C.PIERCE[C.TOWER],
         C.RANGE[C.TOWER], C.RELOAD[C.TOWER]], vals);

// ── 표의 내부 정합성 ────────────────────────────────────────────────────────
H.check('빈 번호 5..9 는 전부 0', H.range(5, 10).map((k) => C.HP[k]),
        [0, 0, 0, 0, 0]);
H.check('표 길이는 16',
        COLS.concat(['FOOT']).map((c) => tableOf(c).length).concat([C.NAME.length]),
        H.range(COLS.length + 2).map(() => 16));
H.check('공격하지 않는 것은 채집기뿐',
        H.range(16).filter((k) => C.IS_BUILDING[k] === 0 && C.HP[k] !== 0
                                  && C.BASIC[k] === 0), [C.HARV]);
H.checkTrue('사거리가 0 인 유닛은 공격력도 0',
            H.range(16).every((k) => !(C.RANGE[k] === 0 && C.HP[k] !== 0)
                                     || C.BASIC[k] === 0));
H.checkTrue('모든 유닛의 시야는 SIGHT_MAX 이하',
            H.range(16).every((k) => C.SIGHT[k] <= C.SIGHT_MAX));

// 이동 종류는 §25.1 아래 문단에만 있다 — 표가 아니라 산문이라 여기에 옮겨 적는다
H.check('차량은 전차와 채집기뿐 (SPEC §25.1)',
        H.range(16).filter((k) => C.MOVE_KIND[k] === 1), [C.TANK, C.HARV]);
H.check('건물의 이동 종류는 0', H.range(10, 16).map((k) => C.MOVE_KIND[k]),
        [0, 0, 0, 0, 0, 0]);

// ── §25.3 기술 트리 ─────────────────────────────────────────────────────────
H.check('HQ 는 선행 조건이 없다', C.PREREQ[C.HQ], []);
H.check('공장만 선행 조건이 둘',
        H.range(16).filter((k) => C.PREREQ[k].length > 1), [C.FACT]);
H.check('공장의 선행은 발전소와 병영 (번호 오름차순)',
        C.PREREQ[C.FACT], [C.BARR, C.POW]);
H.check('전차·박격포는 공장에서', [C.PREREQ[C.TANK], C.PREREQ[C.MORTAR]],
        [[C.FACT], [C.FACT]]);
bad = 0;
for (let k = 0; k < 16; k += 1) {
  for (const p of C.PREREQ[k]) {
    if (C.IS_BUILDING[p] !== 1) bad += 1;
  }
}
H.check('선행 조건은 전부 건물', bad, 0);

// DAG 확인 — 순환이 있으면 위상 정렬이 멈춘다 (§16.6)
function hasCycle(): boolean {
  const seen = H.range(16).map(() => 0);
  function visit(k: number): boolean {
    if (seen[k] === 1) return true;
    if (seen[k] === 2) return false;
    seen[k] = 1;
    for (const p of C.PREREQ[k]) {
      if (visit(p)) return true;
    }
    seen[k] = 2;
    return false;
  }
  return H.range(16).some((k) => visit(k));
}

H.check('기술 트리는 순환이 없다', hasCycle(), false);

// ── §17.1 FSM 상태 번호표 ───────────────────────────────────────────────────
bad = 0;
const names: string[] = [];
for (const cells of tableRows('### 17.1 유닛 FSM')) {
  const name = cells[1].replace(/`/g, '');
  names.push(name);
  if (scalar(name) !== parseInt(cells[0], 10)) {
    H.note(name + ' 기대 ' + cells[0] + ' 실제 ' + scalar(name));
    bad += 1;
  }
}
H.check('§17.1 상태 번호 ' + names.length + '개', bad, 0);
H.check('상태 번호는 0..9 로 겹치지 않는다',
        H.sortedNums(names.map((s) => scalar(s) as number)), H.range(10));

// ── §25.4 시작 조건 ─────────────────────────────────────────────────────────
H.check('시작 크레딧 1000', C.START_CREDITS, 1000);
H.check('시작 채집기 2기', C.START_HARV, 2);
H.check('시나리오 길이 1200틱', C.SCENARIO_TICKS, 1200);

H.done();
