// 시야와 안개 — 참조 카운트 세 평면 (SPEC §14).
//
//    안개는 **그리기 단계에서만** 쓰인다. 시뮬레이션은 안개를 무시한다 —
//    안개를 시뮬레이션의 일부로 만들면 플레이어마다 상태가 갈리고, 그러면
//    락스텝의 전제가 무너진다(§14.5).
//
//    칸당 1바이트를 쓴다. 비트 플레인이 8배 작지만 참조 카운트는 비트로 담을 수
//    없다. 비트 플레인은 저장·전송용 `packBits` 로만 남겼다(§14.2).

import * as CI from './circle';
import * as C from './const';
import * as F from './fixed';
import * as S from './spatial';

// 플레이어마다 explored·count 두 평면. visible 은 count > 0 의 별칭이다.
export class Fog {
  w: number;
  h: number;
  count: number[][];
  explored: number[][];

  constructor(w: number, h: number, players = C.MAX_PLAYER) {
    this.w = w;
    this.h = h;
    this.count = [];
    this.explored = [];
    for (let p = 0; p < players; p += 1) {
      this.count.push(new Array<number>(w * h).fill(0));
      this.explored.push(new Array<number>(w * h).fill(0));
    }
  }

  visible(p: number, i: number): boolean {
    return this.count[p][i] > 0;
  }

  // ── SPEC §14.3 증분 갱신 ─────────────────────────────────────────────────
  // O(r²) — 원 안의 칸마다 카운트 +1 과 탐험 표시.
  addSight(p: number, tx: number, ty: number, r: number): void {
    const cnt = this.count[p];
    const exp = this.explored[p];
    for (const [dx, dy] of CI.offsets(r)) {
      const x = tx + dx;
      const y = ty + dy;
      if (x >= 0 && x < this.w && y >= 0 && y < this.h) {
        const i = y * this.w + x;
        cnt[i] += 1;
        exp[i] = 1;
      }
    }
  }

  // 카운트 −1. 0 아래로는 내려가지 않는다 — 내려간다면 그것은 버그다.
  removeSight(p: number, tx: number, ty: number, r: number): void {
    const cnt = this.count[p];
    for (const [dx, dy] of CI.offsets(r)) {
      const x = tx + dx;
      const y = ty + dy;
      if (x >= 0 && x < this.w && y >= 0 && y < this.h) {
        const i = y * this.w + x;
        if (cnt[i] > 0) cnt[i] -= 1;
      }
    }
  }

  // 타일을 넘을 때 — **빼기가 먼저다**(§14.3).
  moveSight(p: number, ox: number, oy: number, nx: number, ny: number,
            r: number): void {
    this.removeSight(p, ox, oy, r);
    this.addSight(p, nx, ny, r);
  }

  // 불변식 F 를 전수로 검증하고 **어긋난 칸 수만** 돌려준다.
  // 고치지 않는 이유는 하나다. 증분 갱신이 새면 그것은 버그이고,
  // 조용히 고쳐 버리면 그 버그는 영원히 드러나지 않는다.
  recount(world: S.World): number {
    const want: number[][] = [];
    for (let p = 0; p < this.count.length; p += 1) {
      want.push(new Array<number>(this.w * this.h).fill(0));
    }
    for (let i = 1; i < C.MAX_ENT; i += 1) {
      if (world.alive[i] === 0) continue;
      const r = C.SIGHT[world.kind[i]];
      const p = world.owner[i];
      if (p >= want.length) continue;
      for (const [dx, dy] of CI.offsets(r)) {   // 건물의 시야 중심은 좌상단이다
        const x = world.tx[i] + dx;
        const y = world.ty[i] + dy;
        if (x >= 0 && x < this.w && y >= 0 && y < this.h) {
          want[p][y * this.w + x] += 1;
        }
      }
    }
    let bad = 0;
    for (let p = 0; p < this.count.length; p += 1) {
      for (let i = 0; i < this.w * this.h; i += 1) {
        if (this.count[p][i] !== want[p][i]) bad += 1;
      }
    }
    return bad;
  }

  // ── SPEC §14.4 4단계 렌더 ────────────────────────────────────────────────
  // 0 미탐험 · 1 탐험 · 2 경계 · 3 가시.
  // 2단계는 순전히 눈을 위한 것이다. 1과 3만 있으면 안개 경계가 계단처럼 보인다.
  level(p: number, x: number, y: number): number {
    if (!(x >= 0 && x < this.w && y >= 0 && y < this.h)) return 0;
    const i = y * this.w + x;
    if (this.count[p][i] > 0) return 3;
    if (this.explored[p][i] === 0) return 0;
    for (const dy of [-1, 0, 1]) {
      for (const dx of [-1, 0, 1]) {
        const u = x + dx;
        const v = y + dy;
        if (u >= 0 && u < this.w && v >= 0 && v < this.h
            && this.count[p][v * this.w + u] > 0) return 2;
      }
    }
    return 1;
  }

  // ── SPEC §14.2 비트 플레인 (저장·전송용) ─────────────────────────────────
  // 탐험 평면 8칸을 1바이트로. 칸 i 는 바이트 i//8 의 2^(i%8) 자리다.
  // 비트 연산자를 쓰지 않는다(§1.1) — 곱셈과 덧셈이면 충분하다.
  packBits(p: number): number[] {
    const n = this.w * this.h;
    const out = new Array<number>(Math.floor((n + 7) / 8)).fill(0);
    const exp = this.explored[p];
    for (let i = 0; i < n; i += 1) {
      if (exp[i] !== 0) out[F.floordiv(i, 8)] += F.pow2(F.fmod(i, 8));
    }
    return out;
  }

  unpackBits(p: number, data: number[]): void {
    const n = this.w * this.h;
    const exp = this.explored[p];
    for (let i = 0; i < n; i += 1) {
      exp[i] = F.fmod(F.floordiv(data[F.floordiv(i, 8)], F.pow2(F.fmod(i, 8))), 2);
    }
  }
}
