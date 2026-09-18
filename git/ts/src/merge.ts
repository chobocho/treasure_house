// merge (SPEC.md §12) — 공통 조상 B 에서 갈라진 O(우리)와 T(그들).
//
// 파일 하나의 합치기는 git 의 xdl_merge(ZEALOUS 수준)를 따른다:
//   1. B→O, B→T 의 바뀐 곳을 B 좌표로 짝지어 훑는다. 엄격히 앞선 쪽은
//      그대로 받고, 겹치거나 **맞닿으면** 충돌 후보다(같은 수정이면
//      한 번만).
//   2. 충돌마다 O 쪽과 T 쪽을 다시 diff 해 같은 줄을 표지 밖으로 뺀다.
//   3. 사이가 바뀌지 않은 줄 3개 이하인 이웃 충돌은 하나로 붙인다.
// 진짜 git merge 로 경계를 확인한 규칙들이다(golden/scen/merge-*.scn).
// 줄은 diff 와 같은 바이트 문자열이다.
import { buildChanges, Change, editFlags, splitLines } from './diff';
import { GitError } from './errors';
import * as objects from './objects';
import { same, Stat } from './worktree';

const JOIN = 3; // 이만큼 가까운 충돌은 하나로 붙인다

// 조각 — 바뀌지 않은 줄, 한쪽 변경을 받은 줄, 충돌(O 줄들, T 줄들)
type Piece = ['same' | 'clean', string[]] |
  ['conf', string[], string[]];
// 짝 맞추기의 한 칸 — 'o'(O 쪽 변경 받기)·'t'·'c'(충돌 후보)
type Pair = ['o' | 't' | 'c', number, number, string[], string[]];

const changes = (a: string[], b: string[]) =>
  buildChanges(...editFlags(a, b));

const eqLines = (a: string[], b: string[]) =>
  a.length === b.length && a.every((l, i) => l === b[i]);

// B 의 [start, end) 에 맞는 한쪽 파일의 범위.
//
// start 앞에서 시작한 바뀐 곳들의 길이 차를 더하면 시작 자리가, end
// 이하에서 시작한 것까지 더하면 끝 자리가 나온다 — 이 범위에 걸친
// 바뀐 곳은 짝 맞추기가 전부 이 범위에 넣어 두었다.
function sideRange(cs: Change[], start: number, end: number):
  [number, number] {
  const shift = (upto: (c: Change) => boolean) => cs.filter(upto)
    .reduce((s, c) => s + c[3] - c[2], 0);
  return [start + shift((c) => c[0] < start),
    end + shift((c) => c[0] <= end)];
}

// 1 단계 — [종류, B 시작, B 끝, O 줄들, T 줄들]. 바뀌지 않은 곳은
// 빠진다. 받지 않는 쪽의 줄들은 빈 배열이다.
function pair(base: string[], ours: string[], theirs: string[]):
  Pair[] {
  const [c1, c2] = [changes(base, ours), changes(base, theirs)];
  const out: Pair[] = [];
  let [i, j] = [0, 0];
  const oLines = (x: Change) => ours.slice(x[1], x[1] + x[3]);
  const tLines = (y: Change) => theirs.slice(y[1], y[1] + y[3]);
  while (i < c1.length || j < c2.length) {
    const x = c1[i];
    const y = c2[j];
    if (y === undefined || (x !== undefined && x[0] + x[2] < y[0])) {
      out.push(['o', x[0], x[0] + x[2], oLines(x), []]);
      i++;
      continue;
    }
    if (x === undefined || y[0] + y[2] < x[0]) {
      out.push(['t', y[0], y[0] + y[2], [], tLines(y)]);
      j++;
      continue;
    }
    if (x[0] === y[0] && x[2] === y[2] &&
      eqLines(oLines(x), tLines(y))) {
      out.push(['o', x[0], x[0] + x[2], oLines(x), []]); // 같은 수정
      [i, j] = [i + 1, j + 1];
      continue;
    }
    const start = Math.min(x[0], y[0]);
    let end = Math.max(x[0] + x[2], y[0] + y[2]);
    [i, j] = [i + 1, j + 1];
    for (;;) {                            // 맞닿는 것까지 넓힌다
      if (i < c1.length && c1[i][0] <= end) {
        end = Math.max(end, c1[i][0] + c1[i][2]);
        i++;
      } else if (j < c2.length && c2[j][0] <= end) {
        end = Math.max(end, c2[j][0] + c2[j][2]);
        j++;
      } else {
        break;
      }
    }
    const [os, oe] = sideRange(c1, start, end);
    const [ts, te] = sideRange(c2, start, end);
    out.push(['c', start, end, ours.slice(os, oe),
      theirs.slice(ts, te)]);
  }
  return out;
}

// 2 단계 — 충돌 하나를 O·T 의 diff 로 쪼갠다. 같은 줄은 표지 밖으로
// 나온다. O == T 면 충돌이 아니다.
function refine(o: string[], t: string[]): Piece[] {
  if (eqLines(o, t)) return [['same', o]];
  const out: Piece[] = [];
  let p1 = 0;
  for (const [i1, i2, n1, n2] of changes(o, t)) {
    if (i1 > p1) out.push(['same', o.slice(p1, i1)]);
    out.push(['conf', o.slice(i1, i1 + n1), t.slice(i2, i2 + n2)]);
    p1 = i1 + n1;
  }
  if (p1 < o.length) out.push(['same', o.slice(p1)]);
  return out;
}

// 세 판의 바이트 → [합친 바이트, 충돌 수]. SPEC.md §12.3.
//
// O(줄 수 × 편집 거리) — diff 두 번과 충돌마다 diff 한 번.
export function merge3(base: Buffer, ours: Buffer, theirs: Buffer,
  label: string): [Buffer, number] {
  if (ours.equals(theirs) || base.equals(theirs)) return [ours, 0];
  if (base.equals(ours)) return [theirs, 0];
  const b = splitLines(base);
  const [o, t] = [splitLines(ours), splitLines(theirs)];
  const pieces: Piece[] = [];
  let pos = 0;
  for (const [kind, s, e, olines, tlines] of pair(b, o, t)) {
    if (s > pos) pieces.push(['same', b.slice(pos, s)]);
    if (kind === 'o') pieces.push(['clean', olines]);
    else if (kind === 't') pieces.push(['clean', tlines]);
    else pieces.push(...refine(olines, tlines));
    pos = e;
  }
  if (pos < b.length) pieces.push(['same', b.slice(pos)]);
  // 3 단계 — 바뀌지 않은 줄 JOIN 개 이하로 떨어진 충돌을 붙인다
  const joined: Piece[] = [];
  for (let p of pieces) {
    const [prev, mid] = joined.slice(-2);
    const near = mid?.[0] === 'same' && prev?.[0] === 'conf' &&
      mid[1].length <= JOIN;
    if (p[0] === 'conf' && near) {
      joined.splice(-2);
      p = ['conf', [...prev[1], ...mid[1], ...p[1]],
        [...prev[2], ...mid[1], ...p[2]]];
    } else if (p[0] === 'same' && joined.at(-1)?.[0] === 'same') {
      p = ['same', [...joined.pop()![1], ...p[1]]];
    }
    joined.push(p);
  }
  const mark = Buffer.from(label).toString('latin1');
  const out: string[] = [];
  let n = 0;
  for (const p of joined) {
    if (p[0] === 'conf') {
      n++;
      out.push('<<<<<<< HEAD\n', ...p[1], '=======\n', ...p[2],
        `>>>>>>> ${mark}\n`);
    } else {
      out.push(...p[1]);
    }
  }
  return [Buffer.from(out.join(''), 'latin1'), n];
}

// 트리 단위 합치기의 결과 한 칸 — 깨끗함·지움·충돌(합친 바이트,
// 단계별 [모드, 이름], 작업 트리에 쓸 모드)
export type Outcome = ['clean', number, string] | ['gone'] |
  ['conflict', Buffer, Map<number, Stat>, number];

// 세 줄 규칙이 못 고름. 없음(undefined)도 값이라 따로 표지가 있어야
// 한다 — 한쪽만 지웠으면 지움이 이긴다.
const UNDECIDED = Symbol('undecided');

function pick<T>(bv: T | undefined, ov: T | undefined,
  tv: T | undefined, eq: (x?: T, y?: T) => boolean):
  T | undefined | typeof UNDECIDED {
  if (eq(ov, tv) || eq(bv, tv)) return ov;
  if (eq(bv, ov)) return tv;
  return UNDECIDED;
}

const utf8 = (p: string) => Buffer.from(p, 'latin1').toString('utf8');

// 트리 단위 합치기(SPEC.md §12.2). base·ours·theirs 는 {경로: [모드,
// 이름]}. → [결과 {경로: Outcome}, 안내 줄들, 충돌 경로들]. 모드는
// 내용과 따로 같은 세 줄 규칙.
export function mergeTrees(gitdir: string, base: Map<string, Stat>,
  ours: Map<string, Stat>, theirs: Map<string, Stat>, label: string):
  [Map<string, Outcome>, string[], string[]] {
  const result = new Map<string, Outcome>();
  const notes: string[] = [];
  const conflicts: string[] = [];
  const paths = [...new Set([...base.keys(), ...ours.keys(),
    ...theirs.keys()])].sort();
  for (const p of paths) {
    const [bv, ov, tv] = [base.get(p), ours.get(p), theirs.get(p)];
    const whole = pick(bv, ov, tv, same);
    if (whole !== UNDECIDED) {
      result.set(p, whole ? ['clean', ...whole] : ['gone']);
      continue;
    }
    if (!ov || !tv) {
      throw new GitError('fatal: mygit: unsupported merge case ' +
        `(modify/delete) in ${utf8(p)}`);
    }
    const mode = pick(bv?.[0], ov[0], tv[0], (x, y) => x === y);
    if (mode === UNDECIDED || mode === undefined) {
      throw new GitError('fatal: mygit: unsupported merge case ' +
        `(mode) in ${utf8(p)}`);
    }
    notes.push(`Auto-merging ${utf8(p)}`);
    const [data0, data1, data2] = [bv, ov, tv].map((v) => v
      ? objects.readObject(gitdir, v[1])[1] : Buffer.alloc(0));
    const [text, n] = merge3(data0, data1, data2, label);
    if (n) {
      notes.push(`CONFLICT (${bv ? 'content' : 'add/add'}): Merge ` +
        `conflict in ${utf8(p)}`);
      const stages = new Map<number, Stat>();
      ([[1, bv], [2, ov], [3, tv]] as const).forEach(([k, v]) => {
        if (v) stages.set(k, v);
      });
      result.set(p, ['conflict', text, stages, mode]);
      conflicts.push(p);
    } else {
      result.set(p, ['clean', mode,
        objects.writeObject(gitdir, 'blob', text)]);
    }
  }
  return [result, notes, conflicts];
}
