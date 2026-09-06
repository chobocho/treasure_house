// 엔티티와 공간 분할 — SoA·세대 핸들·균일 격자 버킷 (SPEC §7).
//
//    엔티티를 구조체의 배열이 아니라 배열의 구조체로 담는다. 성능도 이유지만
//    더 큰 이유는 **직렬화 순서가 배열 순서로 자동으로 고정**된다는 것이다.
//    상태 해시(SPEC §18.4)가 언어별 필드 순서에 영향을 받지 않는다.
//    그래서 여기서는 객체 배열도, 타입 배열도 쓰지 않는다 — px·py 는 16.16
//    이라 Int32Array 로도 넘칠 수 있고, §19.4 의 주입 버그에서는 실수가 된다.

import * as F from './fixed';

export const MAX_ENT = 256;
export const GEN_MOD = 256;
export const BUCKET = 8;

export function index(h: number): number {
  return F.floordiv(h, 256);
}

export function generation(h: number): number {
  return F.fmod(h, 256);
}

function zeros(n: number): number[] {
  return new Array<number>(n).fill(0);
}

// 엔티티 배열과 버킷. 시뮬레이션 규칙은 여기 없다 — 담는 그릇일 뿐이다.
export class World {
  w: number;
  h: number;
  bw: number;
  bh: number;
  alive: number[];
  gen: number[];
  owner: number[];
  kind: number[];
  tx: number[];
  ty: number[];
  px: number[];
  py: number[];
  hp: number[];
  dir: number[];
  state: number[];
  target: number[];
  load: number[];
  prog: number[];
  from_t: number[];
  to_t: number[];
  cool: number[];
  timer: number[];
  buckets: number[][];

  constructor(w: number, h: number) {
    this.w = w;
    this.h = h;
    this.bw = Math.floor((w + BUCKET - 1) / BUCKET);
    this.bh = Math.floor((h + BUCKET - 1) / BUCKET);
    const n = MAX_ENT;
    this.alive = zeros(n);
    this.gen = zeros(n);
    this.owner = zeros(n);
    this.kind = zeros(n);
    this.tx = zeros(n);
    this.ty = zeros(n);
    this.px = zeros(n);
    this.py = zeros(n);
    this.hp = zeros(n);
    this.dir = zeros(n);
    this.state = zeros(n);
    this.target = zeros(n);
    this.load = zeros(n);
    this.prog = zeros(n);
    this.from_t = zeros(n);
    this.to_t = zeros(n);
    this.cool = zeros(n);
    this.timer = zeros(n);
    this.buckets = [];
    for (let i = 0; i < this.bw * this.bh; i += 1) this.buckets.push([]);
  }

  // ── SPEC §7.2 핸들 ───────────────────────────────────────────────────────
  handle(i: number): number {
    return i * 256 + this.gen[i];
  }

  valid(h: number): boolean {
    if (h === 0) return false;
    const i = index(h);
    return i > 0 && i < MAX_ENT && this.alive[i] === 1
      && generation(h) === this.gen[i];
  }

  bucketOf(tx: number, ty: number): number {
    return F.floordiv(ty, BUCKET) * this.bw + F.floordiv(tx, BUCKET);
  }

  // ── 생성·소멸 ────────────────────────────────────────────────────────────
  // 슬롯 0 은 절대 쓰지 않는다 — 핸들 0 이 "없음"을 뜻해야 하기 때문이다.
  spawn(owner: number, kind: number, tx: number, ty: number): number {
    for (let i = 1; i < MAX_ENT; i += 1) {
      if (this.alive[i] === 0) {
        this.alive[i] = 1;
        this.owner[i] = owner;
        this.kind[i] = kind;
        this.tx[i] = tx;
        this.ty[i] = ty;
        this.px[i] = F.fp(tx * 16);
        this.py[i] = F.fp(ty * 16);
        this.dir[i] = 4;
        this.state[i] = 0;
        this.target[i] = 0;
        this.load[i] = 0;
        this.prog[i] = 0;
        this.from_t[i] = ty * this.w + tx;
        this.to_t[i] = ty * this.w + tx;
        this.cool[i] = 0;
        this.timer[i] = 0;
        this.bucketAdd(i);
        return this.handle(i);
      }
    }
    return 0;                          // 상한 초과 — 조용히 실패한다
  }

  kill(h: number): boolean {
    if (!this.valid(h)) return false;
    const i = index(h);
    this.bucketDel(i);
    this.alive[i] = 0;
    this.gen[i] = F.fmod(this.gen[i] + 1, GEN_MOD);
    return true;
  }

  // ── SPEC §7.3 버킷 ───────────────────────────────────────────────────────
  private bucketAdd(i: number): void {
    const b = this.buckets[this.bucketOf(this.tx[i], this.ty[i])];
    let k = 0;
    while (k < b.length && b[k] < i) k += 1;   // 오름차순 유지 — 결정론을 위해서다
    b.splice(k, 0, i);
  }

  private bucketDel(i: number): void {
    const b = this.buckets[this.bucketOf(this.tx[i], this.ty[i])];
    const k = b.indexOf(i);
    if (k >= 0) b.splice(k, 1);
  }

  // 타일을 넘을 때만 부른다. 픽셀 이동마다 부르는 것이 아니다.
  moveTile(i: number, tx: number, ty: number): void {
    if (this.bucketOf(this.tx[i], this.ty[i]) !== this.bucketOf(tx, ty)) {
      this.bucketDel(i);
      this.tx[i] = tx;
      this.ty[i] = ty;
      this.bucketAdd(i);
    } else {
      this.tx[i] = tx;
      this.ty[i] = ty;
    }
  }

  // 반경 r(체비셰프) 안의 엔티티 인덱스. 오름차순으로 돌려준다.
  query(tx: number, ty: number, r: number): number[] {
    const out: number[] = [];
    const x0 = F.floordiv(Math.max(0, tx - r), BUCKET);
    const x1 = F.floordiv(Math.min(this.w - 1, tx + r), BUCKET);
    const y0 = F.floordiv(Math.max(0, ty - r), BUCKET);
    const y1 = F.floordiv(Math.min(this.h - 1, ty + r), BUCKET);
    for (let by = y0; by <= y1; by += 1) {
      for (let bx = x0; bx <= x1; bx += 1) {
        for (const i of this.buckets[by * this.bw + bx]) {
          if (F.dinf(this.tx[i] - tx, this.ty[i] - ty) <= r) out.push(i);
        }
      }
    }
    out.sort((a, b) => a - b);
    return out;
  }
}
