// 역사 걷기와 merge-base (SPEC.md §10).
//
// git 의 기본 log 차례는 "커미터 날짜가 늦은 것부터" 인데, 날짜가 같을
// 때의 규칙까지 정해져 있다 — 날짜 차례로 정렬된 목록에 새 커밋을 끼울
// 때 **같은 날짜들 가운데 맨 뒤에** 끼운다(git 의 commit_list_insert_
// by_date). 이 덱의 저장소는 모든 커밋의 날짜가 같게 만들어지므로, 이
// 한 줄이 차례의 전부를 정한다(golden/dag/equal 이 그것을 확인한다).
import * as commit from './commit';
import * as objects from './objects';

const CACHE = new Map<string, [string[], number]>();

// [부모 목록, 커미터 날짜 초]. 한 번 읽은 커밋은 기억한다 — 객체는
// 이름이 곧 내용이라 바뀌지 않는다.
function parentsAndDate(gitdir: string, oid: string):
  [string[], number] {
  const key = `${gitdir}\0${oid}`;
  let hit = CACHE.get(key);
  if (hit === undefined) {
    const c = commit.parseCommit(objects.readObject(gitdir, oid)[1]);
    hit = [c.parents, commit.parseIdent(c.committer)[2]];
    CACHE.set(key, hit);
  }
  return hit;
}

// 정렬된 keys 에서 k 를 끼울 자리 — 같은 값들의 맨 뒤(bisect_right).
function bisectRight(keys: number[], k: number): number {
  let [lo, hi] = [0, keys.length];
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (k < keys[mid]) hi = mid;
    else lo = mid + 1;
  }
  return lo;
}

// 시작 커밋들에서 닿는 커밋 전부, git log 의 기본 차례로.
//
// 큐는 날짜 내림차순 목록이다(열쇠 = −날짜 의 오름차순). 끼울 자리는
// "날짜가 같거나 늦은 것들 바로 뒤" — 그래서 같은 날짜라면 먼저 들어온
// 것이 먼저 나간다. O(커밋 수 × log(큐 길이)) 비교, 끼우기는 배열이라
// O(큐 길이).
export function walkLog(gitdir: string, starts: string[]): string[] {
  const queue: string[] = [];
  const keys: number[] = [];
  const seen = new Set<string>();
  const out: string[] = [];
  const push = (oid: string): void => {
    if (seen.has(oid)) return;
    seen.add(oid);
    const k = -parentsAndDate(gitdir, oid)[1];
    const at = bisectRight(keys, k);
    keys.splice(at, 0, k);
    queue.splice(at, 0, oid);
  };
  starts.forEach(push);
  while (queue.length) {
    keys.shift();
    const oid = queue.shift()!;
    out.push(oid);
    parentsAndDate(gitdir, oid)[0].forEach(push);
  }
  return out;
}

// oid 와 그 조상 전부의 집합. O(커밋 수).
function ancestors(gitdir: string, oid: string): Set<string> {
  const seen = new Set<string>();
  const stack = [oid];
  while (stack.length) {
    const c = stack.pop()!;
    if (seen.has(c)) continue;
    seen.add(c);
    stack.push(...parentsAndDate(gitdir, c)[0]);
  }
  return seen;
}

// a 가 b 이거나 b 의 조상인가.
export function isAncestor(gitdir: string, a: string, b: string):
  boolean {
  return ancestors(gitdir, b).has(a);
}

// 가장 좋은 공통 조상들(SPEC.md §10.2), 커미터 날짜 내림차순.
//
// 공통 조상 가운데 다른 공통 조상의 조상이 아닌 것만 남긴다. 작은
// 저장소를 위한 곧은 방법이다 — git 은 날짜로 칠하며 내려가는 더 빠른
// 길(paint_down_to_common)을 쓴다. O(커밋 수²) 최악.
export function mergeBases(gitdir: string, a: string, b: string):
  string[] {
  const inB = ancestors(gitdir, b);
  const common = [...ancestors(gitdir, a)].filter((c) => inB.has(c));
  const below = new Set<string>();
  for (const c of common) {
    for (const p of parentsAndDate(gitdir, c)[0]) {
      ancestors(gitdir, p).forEach((x) => below.add(x));
    }
  }
  const date = (c: string) => parentsAndDate(gitdir, c)[1];
  return common.filter((c) => !below.has(c))
    .sort((x, y) => date(y) - date(x));
}
