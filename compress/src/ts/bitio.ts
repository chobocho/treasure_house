// 비트 writer/reader — SPEC §1.
//
// 우리 형식은 전부 MSB 먼저이고 DEFLATE 만 LSB 먼저다. 가장 자주
// 갈라지는 자리는 flush 의 채움이다 — **채움은 0** 이고, 쌓인 비트가
// 없으면 바이트를 내보내지 않는다.
//
// writeBits 가 시프트 대신 Math.floor(v / 2**i) 를 쓰는 이유: TS 의
// 비트 연산자는 32비트로 자른다. 64비트 값을 다루는 자리(엘리아스
// 부호)가 있어 시프트로 쓰면 조용히 값이 잘린다.
import { ByteBuf, Bytes, concat, fail } from './common';
import * as varint from './varint';

export class MsbWriter {
  private out = new ByteBuf();
  private buf = 0;
  private n = 0;

  writeBit(bit: number): void {
    this.buf |= (bit & 1) << (7 - this.n);
    if (++this.n === 8) {
      this.out.push(this.buf);
      this.buf = 0;
      this.n = 0;
    }
  }

  writeBits(v: number, count: number): void {
    for (let i = count - 1; i >= 0; i--) {
      this.writeBit(Math.floor(v / 2 ** i) & 1);
    }
  }

  // MSB 스트림에서는 값도 부호도 같은 순서다. 이름만 따로 둔 것은
  // LsbWriter 와 부르는 쪽 코드를 똑같이 만들기 위해서다.
  writeCode(code: number, count: number): void {
    this.writeBits(code, count);
  }

  bitPos(): number {
    return this.out.size * 8 + this.n;
  }

  flush(): void {
    if (this.n > 0) {
      this.out.push(this.buf);
      this.buf = 0;
      this.n = 0;
    }
  }

  bytes(): Bytes {
    return this.out.bytes();
  }
}

export class MsbReader {
  pos: number;
  private buf = 0;
  private n = 0;

  constructor(private src: Bytes, pos = 0) {
    this.pos = pos;
  }

  readBit(): number {
    if (this.n === 0) {
      if (this.pos >= this.src.length) fail('비트 스트림이 바닥났다');
      this.buf = this.src[this.pos++];
      this.n = 8;
    }
    this.n--;
    return (this.buf >> this.n) & 1;
  }

  readBits(count: number): number {
    let v = 0;
    for (let i = 0; i < count; i++) v = v * 2 + this.readBit();
    return v;
  }

  align(): void {
    this.n = 0;
  }
}

export class LsbWriter {
  private out = new ByteBuf();
  private buf = 0;
  private n = 0;

  writeBit(bit: number): void {
    this.buf |= (bit & 1) << this.n;
    if (++this.n === 8) {
      this.out.push(this.buf);
      this.buf = 0;
      this.n = 0;
    }
  }

  writeBits(v: number, count: number): void {
    for (let i = 0; i < count; i++) {
      this.writeBit(Math.floor(v / 2 ** i) & 1);
    }
  }

  // 허프만 부호만 같은 LSB 스트림에 높은 비트부터 넣는다 (RFC 1951).
  writeCode(code: number, count: number): void {
    for (let i = count - 1; i >= 0; i--) {
      this.writeBit(Math.floor(code / 2 ** i) & 1);
    }
  }

  bitPos(): number {
    return this.out.size * 8 + this.n;
  }

  flush(): void {
    if (this.n > 0) {
      this.out.push(this.buf);
      this.buf = 0;
      this.n = 0;
    }
  }

  align(): void {
    this.flush();
  }

  bytes(): Bytes {
    return this.out.bytes();
  }
}

export class LsbReader {
  pos: number;
  private buf = 0;
  private n = 0;

  constructor(private src: Bytes, pos = 0) {
    this.pos = pos;
  }

  readBit(): number {
    if (this.n === 0) {
      if (this.pos >= this.src.length) fail('비트 스트림이 바닥났다');
      this.buf = this.src[this.pos++];
      this.n = 8;
    }
    const bit = this.buf & 1;
    this.buf >>= 1;
    this.n--;
    return bit;
  }

  readBits(count: number): number {
    let v = 0;
    for (let i = 0; i < count; i++) v += this.readBit() * 2 ** i;
    return v;
  }

  align(): void {
    this.n = 0;
  }
}

// 골든 코덱 (SPEC §1.4). 앞의 0비트 셋이 요점 — 모든 바이트를 바이트
// 경계 밖으로 밀어내므로, 몰래 복사하는 구현은 다른 파일을 낸다.
export const PAD_BITS = 3;

export function encode(src: Bytes): Bytes {
  const w = new MsbWriter();
  w.writeBits(0, PAD_BITS);
  for (const b of src) w.writeBits(b, 8);
  w.flush();
  return concat([varint.put(src.length), w.bytes()]);
}

export function decode(src: Bytes): Bytes {
  const [n, pos] = varint.getLength(src, 0);
  const r = new MsbReader(src, pos);
  r.readBits(PAD_BITS);
  const out = new Uint8Array(n);
  for (let i = 0; i < n; i++) out[i] = r.readBits(8);
  return out;
}
