// diff (SPEC.md §11) — 두 줄 목록 사이의 가장 짧은 편집 스크립트.
//
// 세 단계다. (1) 앞뒤의 같은 줄을 떼어 둔다. (2) 남은 가운데서 Myers 의
// 탐욕 탐색으로 가장 짧은 스크립트를 찾는다. (3) 바뀐 줄 묶음을 git
// 처럼 위아래로 밀어 자리를 정한다 — 같은 줄이 되풀이되는 곳에서는
// 어디를 바뀐 줄로 칠지가 여럿이라, 이 단계가 없으면 git 과 덩어리
// 자리가 달라진다. 다섯 언어가 같은 세 단계를 밟는다.
//
// 줄은 바이트 문자열(latin1)이고 줄바꿈까지 품는다 — 끝 줄바꿈이 없는
// 줄은 있는 줄과 다른 줄이다. === 가 곧 바이트 비교다. rchg 는 줄마다
// "바뀌었나" 의 boolean 배열이다. 출력도 바이트 문자열이다.
import * as objects from './objects';
import { quotePath } from './worktree';

const CONTEXT = 3;
const BINARY_PROBE = 8000;

// 파일 하나의 한쪽 — [모드, blob 이름, 바이트]. 없으면 null.
export type Side = [mode: number, oid: string, data: Buffer];
// 바뀐 곳 — [a 자리, b 자리, a 줄 수, b 줄 수]
export type Change = [i1: number, i2: number, n1: number, n2: number];

// 바이트 → 줄 목록. 줄마다 '\n' 을 품고, 마지막 줄만 없을 수 있다.
export function splitLines(data: Buffer): string[] {
  if (!data.length) return [];
  const parts = data.toString('latin1').split('\n');
  const last = parts.pop()!;
  const lines = parts.map((p) => p + '\n');
  if (last) lines.push(last);
  return lines;
}

// ── 2 단계: Myers 앞방향 탐욕 탐색 (SPEC.md §11.2) ────────────────

// 가운데 a·b 의 [ra, rb]. 대각선 k 마다 가장 멀리 간 x 를 V[k] 에.
//
// k 는 −d‥d 라 배열 첨자로 쓰려고 off 만큼 민다. d 마다 V 의 사본을
// 남겨 두었다가 (N, M) 에서 거꾸로 같은 판정을 되밟아 편집을 표시한다.
// O((N+M)·D) 시간, O((N+M)·D) 공간.
function forward(a: string[], b: string[]): [boolean[], boolean[]] {
  const [n, m] = [a.length, b.length];
  const off = n + m + 1;
  const v = new Int32Array(2 * off + 1);
  const trace: Int32Array[] = [];
  for (let d = 0; d <= n + m; d++) {
    trace.push(v.slice());
    for (let k = -d; k <= d; k += 2) {
      let x = k === -d || (k !== d && v[off + k - 1] < v[off + k + 1])
        ? v[off + k + 1]                   // 아래로: b 의 줄을 끼움
        : v[off + k - 1] + 1;              // 오른쪽: a 의 줄을 지움
      let y = x - k;
      while (x < n && y < m && a[x] === b[y]) [x, y] = [x + 1, y + 1];
      v[off + k] = x;
      if (x >= n && y >= m) return backtrack(trace, n, m, d, off);
    }
  }
  throw new Error('Myers 탐색이 끝나지 않았다');
}

function backtrack(trace: Int32Array[], n: number, m: number,
  dfin: number, off: number): [boolean[], boolean[]] {
  const ra = new Array<boolean>(n).fill(false);
  const rb = new Array<boolean>(m).fill(false);
  let [x, y] = [n, m];
  for (let d = dfin; d > 0; d--) {
    const v = trace[d];
    const k = x - y;
    const down = k === -d ||
      (k !== d && v[off + k - 1] < v[off + k + 1]);
    const pk = down ? k + 1 : k - 1;
    const px = v[off + pk];
    const py = px - pk;
    if (down) rb[py] = true;
    else ra[px] = true;
    [x, y] = [px, py];
  }
  return [ra, rb];
}

// 1·2 단계 — 앞뒤를 깎고 가운데를 앞방향 Myers 로.
export function myers(a: string[], b: string[]):
  [boolean[], boolean[]] {
  const [n, m] = [a.length, b.length];
  let s = 0;
  while (s < n && s < m && a[s] === b[s]) s++;
  let e = 0;
  while (e < n - s && e < m - s && a[n - 1 - e] === b[m - 1 - e]) e++;
  const [ra, rb] = forward(a.slice(s, n - e), b.slice(s, m - e));
  const pad = (k: number) => new Array<boolean>(k).fill(false);
  return [[...pad(s), ...ra, ...pad(e)], [...pad(s), ...rb, ...pad(e)]];
}

// ── 3 단계: 밀어 붙이기 (git 의 xdl_change_compact, 휴리스틱 없이) ─

// 바뀐 줄 묶음 [start, end). 빈 묶음(start == end)도 자리다. chg 끝에는
// 바뀌지 않은 가짜 줄이 하나 붙어 있다.
class Group {
  start = 0;
  end = 0;
  private n: number;

  constructor(private chg: boolean[]) {
    this.n = chg.length - 1;
    while (this.end < this.n && chg[this.end]) this.end++;
  }

  next(): boolean {
    if (this.end === this.n) return false;
    this.start = this.end = this.end + 1;
    while (this.end < this.n && this.chg[this.end]) this.end++;
    return true;
  }

  previous(): boolean {
    if (this.start === 0) return false;
    this.end = this.start = this.start - 1;
    while (this.start > 0 && this.chg[this.start - 1]) this.start--;
    return true;
  }

  slideDown(recs: string[]): boolean {
    if (this.end >= this.n || recs[this.start] !== recs[this.end]) {
      return false;
    }
    this.chg[this.start++] = false;
    this.chg[this.end++] = true;
    while (this.end < this.n && this.chg[this.end]) this.end++;
    return true;
  }

  slideUp(recs: string[]): boolean {
    const [s, e] = [this.start, this.end];
    if (s === 0 || recs[s - 1] !== recs[e - 1]) return false;
    this.chg[--this.start] = true;
    this.chg[--this.end] = false;
    while (this.start > 0 && this.chg[this.start - 1]) this.start--;
    return true;
  }
}

// 한 쪽 파일의 바뀐 줄 묶음을 밀어 자리를 정한다(SPEC.md §11.2).
//
// 묶음마다 위로 끝까지, 다시 아래로 끝까지 민다(밀다가 이웃 묶음과
// 붙으면 처음부터). 상대 파일의 바뀐 묶음과 끝이 맞는 자리가 있었으면
// 그리로 되올리고, 없으면 맨 아래에 둔다. 상대 쪽 묶음 표지 go 는
// 묶음과 발을 맞춰 움직인다 — 그래서 상대 쪽은 줄 내용이 아니라 바뀜
// 표시(ochg)만 있으면 된다. O(줄 수 × 미는 거리).
export function compact(recs: string[], rchg: boolean[],
  ochg: boolean[]): boolean[] {
  const chg = [...rchg, false];
  const g = new Group(chg);
  const go = new Group([...ochg, false]);
  for (;;) {
    if (g.end !== g.start) {
      let earliest: number;
      let matchEnd: number;
      let size: number;
      do {
        size = g.end - g.start;
        matchEnd = -1;
        while (g.slideUp(recs)) go.previous();
        earliest = g.end;
        if (go.end > go.start) matchEnd = g.end;
        while (g.slideDown(recs)) {
          go.next();
          if (go.end > go.start) matchEnd = g.end;
        }
      } while (size !== g.end - g.start);
      if (g.end !== earliest && matchEnd !== -1) {
        while (go.end === go.start) {
          g.slideUp(recs);
          go.previous();
        }
      }
    }
    if (!g.next()) break;
    go.next();
  }
  return chg.slice(0, -1);
}

// 세 단계를 다 거친 [ra, rb] — 계약의 전부(SPEC.md §11.2).
export function editFlags(a: string[], b: string[]):
  [boolean[], boolean[]] {
  let [ra, rb] = myers(a, b);
  ra = compact(a, ra, rb);
  rb = compact(b, rb, ra);
  return [ra, rb];
}

// 바뀐 곳들, 앞에서부터.
//
// 끝에서 앞으로 훑으며 같은 자리에서 만나는 지운 묶음과 끼운 묶음을
// 한 바뀐 곳으로 묶는다(git 의 xdl_build_script).
export function buildChanges(ra: boolean[], rb: boolean[]): Change[] {
  const out: Change[] = [];
  let [i1, i2] = [ra.length, rb.length];
  while (i1 > 0 || i2 > 0) {
    if ((i1 > 0 && ra[i1 - 1]) || (i2 > 0 && rb[i2 - 1])) {
      const [l1, l2] = [i1, i2];
      while (i1 > 0 && ra[i1 - 1]) i1--;
      while (i2 > 0 && rb[i2 - 1]) i2--;
      out.push([i1, i2, l1 - i1, l2 - i2]);
    } else {
      [i1, i2] = [i1 - 1, i2 - 1];
    }
  }
  return out.reverse();
}

// git 기본 드라이버의 함수 줄 — 첫 바이트가 영문자·'_'·'$'.
const isFunc = (line: string) => /^[A-Za-z_$]/.test(line);

// ASCII 공백만 뗀다(Python 의 bytes.rstrip). trimEnd 는 0xA0 도 떼는데,
// 바이트 문자열에서 0xA0 은 UTF-8 한 글자의 한 조각일 수 있다.
const rstrip = (s: string) => s.replace(/[ \t\n\v\f\r]+$/, '');

function span(start: number, count: number): string {
  const first = count ? start + 1 : start;
  return count === 1 ? `${first}` : `${first},${count}`;
}

// 덩어리들(SPEC.md §11.3). 같으면 ''.
export function unifiedDiff(a: string[], b: string[]): string {
  const ch = buildChanges(...editFlags(a, b));
  const out: string[] = [];
  for (let i = 0; i < ch.length;) {
    let j = i;
    while (j + 1 < ch.length &&
      ch[j + 1][0] - (ch[j][0] + ch[j][2]) <= 2 * CONTEXT) j++;
    const [first, last] = [ch[i], ch[j]];
    const s1 = Math.max(first[0] - CONTEXT, 0);
    const s2 = Math.max(first[1] - CONTEXT, 0);
    const e1 = Math.min(last[0] + last[2] + CONTEXT, a.length);
    const e2 = Math.min(last[1] + last[3] + CONTEXT, b.length);
    let func = '';
    for (let q = s1 - 1; q >= 0; q--) {
      if (isFunc(a[q])) {
        func = ' ' + rstrip(rstrip(a[q]).slice(0, 80));
        break;
      }
    }
    out.push(`@@ -${span(s1, e1 - s1)} +${span(s2, e2 - s2)} @@` +
      `${func}\n`);
    let p1 = s1;
    for (const [c1, c2, n1, n2] of ch.slice(i, j + 1)) {
      out.push(...a.slice(p1, c1).map((l) => ' ' + l),
        ...a.slice(c1, c1 + n1).map((l) => '-' + l),
        ...b.slice(c2, c2 + n2).map((l) => '+' + l));
      p1 = c1 + n1;
    }
    out.push(...a.slice(p1, e1).map((l) => ' ' + l));
    i = j + 1;
  }
  return out.map((line) => line.endsWith('\n') ? line
    : line + '\n\\ No newline at end of file\n').join('');
}

const q = (prefix: string, p: string) => quotePath(prefix + p);
const octal = (mode: number) => mode.toString(8).padStart(6, '0');

// 파일 하나의 diff 전체(SPEC.md §11.4). old·new 는 Side 또는
// null(새로 생김·지워짐). 경로는 바이트 문자열. 같으면 ''.
export function fileDiff(pathA: string, pathB: string, old: Side | null,
  nu: Side | null): string {
  if (old && nu && old[0] === nu[0] && old[1] === nu[1]) return '';
  const rows = [`diff --git ${q('a/', pathA)} ${q('b/', pathB)}`];
  const z = '0000000';
  if (old === null) {
    rows.push(`new file mode ${octal(nu![0])}`,
      `index ${z}..${nu![1].slice(0, 7)}`);
  } else if (nu === null) {
    rows.push(`deleted file mode ${octal(old[0])}`,
      `index ${old[1].slice(0, 7)}..${z}`);
  } else {
    if (old[0] !== nu[0]) {
      rows.push(`old mode ${octal(old[0])}`,
        `new mode ${octal(nu[0])}`);
    }
    if (old[1] === nu[1]) return rows.join('\n') + '\n'; // 모드만 바뀜
    let idx = `index ${old[1].slice(0, 7)}..${nu[1].slice(0, 7)}`;
    if (old[0] === nu[0]) idx += ` ${octal(old[0])}`;
    rows.push(idx);
  }
  const da = old ? old[2] : Buffer.alloc(0);
  const db = nu ? nu[2] : Buffer.alloc(0);
  const nameA = old ? q('a/', pathA) : '/dev/null';
  const nameB = nu ? q('b/', pathB) : '/dev/null';
  if (da.subarray(0, BINARY_PROBE).includes(0) ||
    db.subarray(0, BINARY_PROBE).includes(0)) {
    rows.push(`Binary files ${nameA} and ${nameB} differ`);
    return rows.join('\n') + '\n';
  }
  rows.push(`--- ${nameA}`, `+++ ${nameB}`);
  return rows.join('\n') + '\n' +
    unifiedDiff(splitLines(da), splitLines(db));
}

// [모드, 이름, 바이트] — 저장소의 blob 에서.
export function blobSide(gitdir: string, mode: number, oid: string):
  Side {
  return [mode, oid, objects.readObject(gitdir, oid)[1]];
}
