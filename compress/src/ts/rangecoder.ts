// 이진 레인지 코더 — SPEC §8. LZMA 의 것 그대로.
//
// **이 파일이 TypeScript 에서 가장 조심할 곳이다** (SPEC §8.4).
// low·range·code 는 전부 2^33 미만이라 배정도로 정확한데, 비트 연산자를
// 쓰면 32비트 부호 있는 정수로 잘린다. 그래서
//   · x << 8  대신  x * 256 % 0x100000000
//   · x >> 11 대신  Math.floor(x / 2048)
// 을 쓴다. >>> 는 2^32 미만에서 안전해 몇 군데만 쓴다.
// BigInt 는 필요 없다 — 값이 2^53 을 넘지 않는다.
import { ByteBuf, Bytes, concat, fail } from './common';
import * as varint from './varint';

export const PROB_BITS = 11;
export const PROB_TOTAL = 1 << PROB_BITS;
export const PROB_INIT = PROB_TOTAL / 2;
export const MOVE_BITS = 5;
export const TOP = 2 ** 24;
const U32 = 0x100000000;

export class Encoder {
  private low = 0; // 최대 2^33 — 32비트가 아니다
  private range = 0xffffffff;
  private cache = 0;
  private cacheSize = 1;
  private out = new ByteBuf();

  // 위 바이트 하나를 확정해 내보낸다. 캐리는 앞으로 전파한다.
  private shiftLow(): void {
    if (this.low >= U32 || this.low < 0xff000000) {
      const carry = Math.floor(this.low / U32);
      let temp = this.cache;
      do {
        this.out.push((temp + carry) & 0xff);
        temp = 0xff;
        this.cacheSize--;
      } while (this.cacheSize !== 0);
      this.cache = Math.floor((this.low % U32) / 0x1000000) & 0xff;
    }
    this.cacheSize++;
    this.low = (this.low % U32) * 256 % U32;
  }

  encodeBit(probs: Uint16Array, i: number, bit: number): void {
    const bound = Math.floor(this.range / PROB_TOTAL) * probs[i];
    if (bit === 0) {
      this.range = bound;
      probs[i] += (PROB_TOTAL - probs[i]) >> MOVE_BITS;
    } else {
      this.low += bound;
      this.range -= bound;
      probs[i] -= probs[i] >> MOVE_BITS;
    }
    while (this.range < TOP) {
      this.range = (this.range * 256) % U32;
      this.shiftLow();
    }
  }

  flush(): void {
    for (let i = 0; i < 5; i++) this.shiftLow();
  }

  bytes(): Bytes {
    return this.out.bytes();
  }
}

export class Decoder {
  private pos: number;
  private range = 0xffffffff;
  private code = 0;

  constructor(private src: Bytes, pos: number) {
    this.pos = pos;
    if (pos >= src.length) fail('레인지 코더 스트림이 비었다');
    if (src[pos] !== 0) fail(`첫 바이트가 0 이 아니다: ${src[pos]}`);
    this.pos++;
    for (let i = 0; i < 4; i++) {
      this.code = (this.code * 256 + this.nextByte()) % U32;
    }
  }

  private nextByte(): number {
    // 잘 만들어진 스트림도 마지막 판정에서 한 바이트쯤 더 읽는다.
    if (this.pos < this.src.length) return this.src[this.pos++];
    this.pos++;
    if (this.pos > this.src.length + 5) {
      fail('스트림 끝을 너무 많이 넘었다');
    }
    return 0;
  }

  decodeBit(probs: Uint16Array, i: number): number {
    const bound = Math.floor(this.range / PROB_TOTAL) * probs[i];
    let bit: number;
    if (this.code < bound) {
      this.range = bound;
      probs[i] += (PROB_TOTAL - probs[i]) >> MOVE_BITS;
      bit = 0;
    } else {
      this.code -= bound;
      this.range -= bound;
      probs[i] -= probs[i] >> MOVE_BITS;
      bit = 1;
    }
    while (this.range < TOP) {
      this.range = (this.range * 256) % U32;
      this.code = (this.code * 256 + this.nextByte()) % U32;
    }
    return bit;
  }
}

// 0차 적응 바이트 모델. 문맥은 1 에서 시작해 여덟 번 만에 256..511 이
// 되므로 실제로 쓰이는 자리는 1..255 뿐 — 배열이 257 이 아니라 256
// 이다.
export class ByteModel {
  probs = new Uint16Array(256).fill(PROB_INIT);

  encode(enc: Encoder, b: number): void {
    let ctx = 1;
    for (let i = 7; i >= 0; i--) {
      const bit = (b >> i) & 1;
      enc.encodeBit(this.probs, ctx, bit);
      ctx = ctx * 2 + bit;
    }
  }

  decode(dec: Decoder): number {
    let ctx = 1;
    for (let i = 0; i < 8; i++) {
      ctx = ctx * 2 + dec.decodeBit(this.probs, ctx);
    }
    return ctx - 256;
  }
}

export function encode(src: Bytes): Bytes {
  if (src.length === 0) return varint.put(0);
  const enc = new Encoder();
  const m = new ByteModel();
  for (const b of src) m.encode(enc, b);
  enc.flush();
  return concat([varint.put(src.length), enc.bytes()]);
}

export function decode(src: Bytes): Bytes {
  const [n, pos] = varint.getLength(src, 0);
  if (n === 0) {
    if (pos !== src.length) fail('빈 입력인데 뒤에 바이트가 있다');
    return new Uint8Array(0);
  }
  const dec = new Decoder(src, pos);
  const m = new ByteModel();
  const out = new Uint8Array(n);
  for (let i = 0; i < n; i++) out[i] = m.decode(dec);
  return out;
}
