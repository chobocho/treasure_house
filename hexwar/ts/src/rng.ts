// 난수와 해시 — SPEC §5, §10.4
//
// 32비트 곱셈이 이 파일의 전부이자 함정이다. `state * 1664525` 는 결과가
// 2^53 을 넘어 정밀도를 잃는다(state 가 2^32 에 가까우면 곱은 2^52 언저리라
// 아슬아슬하게 살아남지만, 그것을 믿는 코드는 언젠가 깨진다).
// Math.imul 은 두 수를 32비트로 자른 뒤 32비트 곱을 정확히 돌려준다.
// 마지막의 `>>> 0` 은 부호 없는 32비트로 되돌리는 관용구다.

const MUL = 1664525;
const ADD = 1013904223;

export class Rng {
  state: number;

  constructor(seed: number) {
    this.state = seed >>> 0;
  }

  next(): number {
    this.state = (Math.imul(this.state, MUL) + ADD) >>> 0;
    return this.state;
  }

  d6(): number {
    return ((this.next() >>> 16) % 6) + 1;
  }

  below(n: number): number {
    return (this.next() >>> 16) % n;
  }

  save(): number {
    return this.state;
  }

  restore(s: number): void {
    this.state = s >>> 0;
  }
}

export function fnv1a(data: Uint8Array): number {
  let h = 2166136261;
  for (let i = 0; i < data.length; i++) {
    h = Math.imul(h ^ data[i]!, 16777619) >>> 0;
  }
  return h >>> 0;
}

export function fnv1aStr(s: string): number {
  // 소스가 ASCII 범위를 벗어나지 않도록 UTF-8 로 바꿔서 먹인다.
  return fnv1a(new TextEncoder().encode(s));
}

export function hex8(v: number): string {
  return (v >>> 0).toString(16).padStart(8, '0');
}
