// 원 마스크 — 시야·스플래시·자원 스탬프가 전부 이것을 쓴다 (SPEC §6).
//
//    고전 미드포인트 원 알고리즘은 여기에 쓰지 않는다. 그것은 *외곽선*을 그리는
//    알고리즘이라 참원에 가장 가까운 점을 고르고, 그 점이 원 안이라는 보장이 없다.
//    r=2 에서 (2,1) 을 찍는데 2²+1² = 5 > 4 다. 시야 마스크로 쓰면 격자점 개수가
//    가우스 원 문제의 값과 어긋난다 — 골든을 처음 만들 때 그 검사가 잡았다.

const spanCache = new Map<number, number[]>();
const offCache = new Map<number, Array<[number, number]>>();

// span[j] = 행 j 에서 원 안에 드는 최대 |i|. 덧셈과 뺄셈만 쓴다.
// 불변식은 t = r² − j² − x² >= 0 이고 x 가 그 조건을 만족하는 최대값이다.
// x 는 결코 늘지 않으므로 전체 비용이 O(r) 이다 (SPEC 정리 6.2).
export function spans(r: number): number[] {
  const hit = spanCache.get(r);
  if (hit !== undefined) return hit;
  const out = new Array<number>(r + 1).fill(0);
  out[0] = r;
  let x = r;
  let t = 0;
  for (let j = 1; j <= r; j += 1) {
    t -= 2 * (j - 1) + 1;
    while (t < 0) {
      t += 2 * x - 1;
      x -= 1;
    }
    out[j] = x;
  }
  spanCache.set(r, out);
  return out;
}

// (dx, dy) 목록. dy 오름차순, 같은 dy 안에서 dx 오름차순으로 **고정**한다.
// 순서가 다르면 참조 카운트 결과는 같지만 이벤트 로그의 순서가 달라지고,
// 그 차이가 상태 해시를 가른다(SPEC §6.3).
export function offsets(r: number): Array<[number, number]> {
  const hit = offCache.get(r);
  if (hit !== undefined) return hit;
  const sp = spans(r);
  const out: Array<[number, number]> = [];
  for (let j = -r; j <= r; j += 1) {
    const w = sp[j >= 0 ? j : -j];
    for (let i = -w; i <= w; i += 1) out.push([i, j]);
  }
  offCache.set(r, out);
  return out;
}

export function count(r: number): number {
  return offsets(r).length;
}

export function inDisc(dx: number, dy: number, r: number): boolean {
  return dx * dx + dy * dy <= r * r;
}

// 고전 미드포인트 '외곽선' — 엔진은 쓰지 않는다. 6부의 대조용으로만 있다.
export function midpointOutline(r: number): Array<[number, number]> {
  const seen = new Set<string>();
  const pts: Array<[number, number]> = [];
  let x = r;
  let y = 0;
  let d = 1 - r;
  const add = (a: number, b: number): void => {
    const key = a + ',' + b;
    if (!seen.has(key)) {
      seen.add(key);
      pts.push([a, b]);
    }
  };
  while (y <= x) {
    add(x, y); add(y, x); add(-x, y); add(-y, x);
    add(x, -y); add(y, -x); add(-x, -y); add(-y, -x);
    y += 1;
    if (d < 0) {
      d += 2 * y + 1;
    } else {
      x -= 1;
      d += 2 * (y - x) + 1;
    }
  }
  return pts;
}
