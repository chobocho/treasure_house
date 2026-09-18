// SHA-1 을 손으로 (SPEC.md §2 · FIPS 180-4).
//
// git 의 모든 객체 이름이 이 함수의 출력이다. node:crypto 를 부르면 한
// 줄이지만 그러면 "40글자 이름이 어디서 오나" 가 가려진다. 한 블록
// (64바이트) = 80라운드, 전체 O(n) 시간, O(1) 추가 공간.
//
// JS 의 수는 64비트 실수라 32비트 덧셈이 저절로 넘치지 않는다. 비트
// 연산자(| ^ << >>>)가 피연산자를 32비트 정수로 자른다는 점을 써서,
// 덧셈 뒤에 `| 0` 을 붙여 mod 2³² 를 흉내 낸다 — Python 의 & MASK 자리.

// 초기값 — FIPS 180-4 §5.3.1. 라운드 상수는 compress 안에.
const H0 = [0x67452301, 0xefcdab89, 0x98badcfe, 0x10325476,
  0xc3d2e1f0];

const rotl = (x: number, n: number) => (x << n) | (x >>> (32 - n));

// 80칸 일정표는 블록마다 새로 만들지 않고 하나를 돌려 쓴다
const W = new Int32Array(80);

// 64바이트 한 블록으로 상태 다섯 개를 갱신한다.
function compress(h: Int32Array, b: Uint8Array): void {
  for (let t = 0; t < 16; t++) {
    W[t] = (b[4 * t] << 24) | (b[4 * t + 1] << 16) |
      (b[4 * t + 2] << 8) | b[4 * t + 3];
  }
  for (let t = 16; t < 80; t++) {
    W[t] = rotl(W[t - 3] ^ W[t - 8] ^ W[t - 14] ^ W[t - 16], 1);
  }
  let [a, bb, c, d, e] = h;
  for (let t = 0; t < 80; t++) {
    let f: number, k: number;
    if (t < 20) [f, k] = [(bb & c) | (~bb & d), 0x5a827999];
    else if (t < 40) [f, k] = [bb ^ c ^ d, 0x6ed9eba1];
    else if (t < 60) {
      [f, k] = [(bb & c) | (bb & d) | (c & d), 0x8f1bbcdc];
    }
    else [f, k] = [bb ^ c ^ d, 0xca62c1d6];
    const tmp = (rotl(a, 5) + f + e + k + W[t]) | 0;
    [a, bb, c, d, e] = [tmp, a, rotl(bb, 30), c, d];
  }
  [a, bb, c, d, e].forEach((v, i) => { h[i] = (h[i] + v) | 0; });
}

// 스트리밍 SHA-1. 인덱스와 팩의 끝 체크섬을 파일을 읽어 가며 셀 때
// 쓴다 — 전체를 한 번에 메모리에 올리지 않아도 된다.
export class Sha1 {
  private h = Int32Array.from(H0);
  private buf = new Uint8Array(64);
  private used = 0;
  private total = 0;

  update(data: Uint8Array): this {
    this.total += data.length;
    for (let i = 0; i < data.length;) {
      const n = Math.min(64 - this.used, data.length - i);
      this.buf.set(data.subarray(i, i + n), this.used);
      this.used += n;
      i += n;
      if (this.used === 64) {
        compress(this.h, this.buf);
        this.used = 0;
      }
    }
    return this;
  }

  // 덧붙임: 0x80, 0 들, 비트 길이(빅 엔디언 64비트). 상태를 건드리지
  // 않는 사본에서 마무리하므로 두 번 불러도 같다. 55바이트까지는
  // 덧붙임이 한 블록에, 56바이트부터는 두 블록에 들어간다.
  digest(): Buffer {
    const h = Int32Array.from(this.h);
    const tail = Buffer.alloc(this.used < 56 ? 64 : 128);
    tail.set(this.buf.subarray(0, this.used));
    tail[this.used] = 0x80;
    tail.writeBigUInt64BE(BigInt(this.total) * 8n, tail.length - 8);
    for (let k = 0; k < tail.length; k += 64) {
      compress(h, tail.subarray(k, k + 64));
    }
    const out = Buffer.alloc(20);
    h.forEach((v, i) => out.writeInt32BE(v, 4 * i));
    return out;
  }
}

// 바이트열의 SHA-1, 20바이트.
export function sha1(data: Uint8Array): Buffer {
  return new Sha1().update(data).digest();
}

// 소문자 16진 40글자 — git 이 화면에 찍는 객체 이름의 꼴.
export function sha1Hex(data: Uint8Array): string {
  return sha1(data).toString('hex');
}
