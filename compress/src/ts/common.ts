// compresslib — 압축 대백과사전의 TypeScript 구현.
//
// 바이트 열은 Uint8Array 하나로 통일한다. number[] 는 값이 0..255 를
// 벗어나도 조용히 담기고, Buffer 는 node 에만 있어서 덱 안 데모에서 못
// 쓴다.
//
// **이 언어에서 파서티가 깨지는 자리는 32비트 강제다** (SPEC §0.5).
// TS 의 수는 배정도 실수인데, 비트 연산자는 피연산자를 **부호 있는**
// 32비트로 바꾼다. 그래서
//   · 0x80000000 | 0 은 음수다
//   · x << 8 은 x 가 2^24 이상이면 값이 잘린다
//   · x >> 8 은 맨 위 비트가 켜져 있으면 부호 확장된다 (>>> 를 쓴다)
// 값이 2^31 을 넘을 수 있는 자리에서는 비트 연산자 대신 곱셈·나눗셈과
// % 0x100000000 을 쓴다. 2^53 까지는 배정도가 정확하므로 안전하다.

export type Bytes = Uint8Array;

// 손상된 입력은 예외다. 조용히 그럴듯한 바이트를 내놓는 복호기가
// 압축에서는 가장 위험하다 (SPEC §12).
export class CodecError extends Error {}

export function fail(msg: string): never {
  throw new CodecError(msg);
}

export function concat(parts: Bytes[]): Bytes {
  let total = 0;
  for (const p of parts) total += p.length;
  const out = new Uint8Array(total);
  let at = 0;
  for (const p of parts) {
    out.set(p, at);
    at += p.length;
  }
  return out;
}

// 늘어나는 바이트 버퍼. push 마다 배열을 다시 만들면 1 MiB 입력에서
// 눈에 띄게 느려진다.
export class ByteBuf {
  private buf = new Uint8Array(64);
  private len = 0;

  push(b: number): void {
    if (this.len === this.buf.length) this.grow(this.len * 2);
    this.buf[this.len++] = b;
  }

  extend(src: Bytes, from = 0, to = src.length): void {
    const need = this.len + (to - from);
    if (need > this.buf.length) this.grow(need * 2);
    this.buf.set(src.subarray(from, to), this.len);
    this.len = need;
  }

  at(i: number): number {
    return this.buf[i];
  }

  get size(): number {
    return this.len;
  }

  bytes(): Bytes {
    return this.buf.slice(0, this.len);
  }

  private grow(want: number): void {
    const next = new Uint8Array(Math.max(want, 64));
    next.set(this.buf.subarray(0, this.len));
    this.buf = next;
  }
}
