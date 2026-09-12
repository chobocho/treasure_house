// TypeScript 시험 — node --test build/ts/src/ts/ 로 돈다.
//
// 파이썬 쪽보다 얇다. 진짜 문지기는 파서티 검사(골든 대조 + 5×5 교차
// 복호) 이고, 여기서는 그 검사가 못 보는 것만 본다 — 예외를 던져야 할
// 자리에서 진짜 던지는가, 그리고 명세의 표가 이 언어에서도 그대로
// 나오는가.
import assert from 'node:assert/strict';
import { test } from 'node:test';

import * as bitio from './bitio';
import * as bwt from './bwt';
import * as deflate from './deflate';
import * as huffman from './huffman';
import * as intcode from './intcode';
import * as lossy from './lossy';
import * as lzss from './lzss';
import * as lzw from './lzw';
import * as mtf from './mtf';
import * as rangecoder from './rangecoder';
import * as rle from './rle';
import * as varint from './varint';
import * as containers from './containers';
import { inflateRaw } from './inflate';
import { ENTRIES } from './registry';

const B = (...v: number[]): Uint8Array => Uint8Array.from(v);
const S = (s: string): Uint8Array =>
  Uint8Array.from([...s].map((c) => c.charCodeAt(0)));
const repeat = (b: number, n: number): Uint8Array =>
  new Uint8Array(n).fill(b);
const pseudo = (n: number, a: number, c: number): Uint8Array =>
  Uint8Array.from({ length: n }, (_v, i) => (i * a + c) & 0xff);

test('bitio — 첫 비트는 7번 비트에, 채움은 0', () => {
  const w = new bitio.MsbWriter();
  w.writeBit(1);
  w.flush();
  assert.deepEqual(w.bytes(), B(0x80));

  const w2 = new bitio.MsbWriter();
  w2.writeBits(0b111, 3);
  w2.flush();
  assert.deepEqual(w2.bytes(), B(0xe0));

  // 빈 DEFLATE 스트림 — BFINAL=1, BTYPE=01, 부호 256
  const w3 = new bitio.LsbWriter();
  w3.writeBits(1, 1);
  w3.writeBits(1, 2);
  w3.writeCode(0, 7);
  w3.flush();
  assert.deepEqual(w3.bytes(), B(0x03, 0x00));

  assert.deepEqual(bitio.encode(new Uint8Array(0)), B(0x00, 0x00));
});

test('intcode — varint·zigzag·gamma', () => {
  assert.deepEqual(varint.put(300), B(0xac, 0x02));
  for (const n of [-(2n ** 63n), 2n ** 63n - 1n, 0n, -1n, 1n]) {
    assert.equal(intcode.unzigzag(intcode.zigzag(n)), n);
  }
  const w = new bitio.MsbWriter();
  intcode.putGamma(w, 4); // 00100
  w.flush();
  assert.deepEqual(w.bytes(), B(0x20));
});

test('rle — 문턱 3, 상한 128, 제어 128 거절', () => {
  assert.deepEqual(rle.encode(S('AAA')), B(0x03, 0xfe, 0x41));
  assert.deepEqual(rle.encode(S('AB')), B(0x02, 0x01, 0x41, 0x42));
  assert.deepEqual(rle.encode(repeat(0x41, 128)), B(0x80, 0x01, 0x81, 0x41));
  assert.throws(() => rle.decode(B(0x03, 0x80, 0x41, 0x41, 0x41)));
  assert.deepEqual(rle.zeroRunEncode([0, 0, 0]), [0, 0]);
});

test('mtf — 옮기기지 바꿔치기가 아니다', () => {
  assert.deepEqual(mtf.transform(S('AAAA')), B(0x41, 0, 0, 0));
  assert.deepEqual(mtf.transform(S('CBAB')), B(0x43, 0x43, 0x43, 1));
});

test('huffman — package-merge 와 캐노니컬 부호', () => {
  const f = new Array<number>(256).fill(0);
  f[0] = 5;
  f[1] = 2;
  f[2] = 1;
  assert.deepEqual(huffman.codeLengths(f).slice(0, 3), [1, 2, 2]);

  const g = new Array<number>(256).fill(0);
  for (let i = 0; i < 7; i++) g[i] = 1;
  assert.deepEqual(huffman.codeLengths(g).slice(0, 7), [3, 3, 3, 3, 3, 3, 2]);

  // RFC 1951 §3.2.2 의 예
  const rfc = new Array<number>(256).fill(0);
  [3, 3, 3, 3, 3, 2, 4, 4].forEach((l, i) => {
    rfc[i] = l;
  });
  const codes = huffman.canonicalCodes(rfc);
  assert.equal(codes[0], 0b010);
  assert.equal(codes[5], 0b00);
  assert.equal(codes[7], 0b1111);
});

test('lzss — 최소 일치 3, 겹치는 일치', () => {
  assert.deepEqual(lzss.encode(S('A')), B(0x01, 0x00, 0x41));
  assert.deepEqual(lzss.encode(S('AAAA')),
                   B(0x04, 0x40, 0x41, 0x00, 0x00, 0x00));
  const run = repeat(0x41, 1000);
  assert.deepEqual(lzss.decode(lzss.encode(run)), run);
  assert.throws(() => lzss.decode(B(0x03, 0x80, 0x00, 0x01, 0x00)));
});

test('lzw — 폭 확장의 한 칸 지연', () => {
  assert.deepEqual(lzw.encode(S('A')), B(0x01, 0x20, 0xc0, 0x40));
  // 사전이 두 번 넘게 꽉 차는 크기 — 작은 시험으로는 안 잡히는 자리다
  const big = pseudo(200000, 131, 7);
  assert.deepEqual(lzw.decode(lzw.encode(big)), big);
});

test('rangecoder — 첫 바이트는 늘 0', () => {
  const src = pseudo(1000, 37, 11);
  const out = rangecoder.encode(src);
  const head = varint.put(src.length).length;
  assert.equal(out[head], 0);
  assert.deepEqual(rangecoder.decode(out), src);
  const bad = Uint8Array.from(out);
  bad[head] = 1;
  assert.throws(() => rangecoder.decode(bad));
});

test('bwt — banana 와 동점 규칙', () => {
  const [l, primary] = bwt.transformBlock(S('banana'));
  assert.deepEqual(l, S('nnbaaa'));
  assert.equal(primary, 3);
  assert.deepEqual(bwt.inverseBlock(l, primary), S('banana'));
  // 모든 회전이 같다 — 동점은 시작 위치 오름차순이라 primary 가 0
  const [, p2] = bwt.transformBlock(repeat(0, 64));
  assert.equal(p2, 0);
});

test('deflate — 빈 스트림·손상 거절·gzip MTIME', () => {
  assert.deepEqual(deflate.deflateRaw(new Uint8Array(0)), B(0x03, 0x00));
  assert.throws(() => inflateRaw(B(0x07, 0x00)));
  assert.throws(() => inflateRaw(B(0x01, 0x01, 0x00, 0x00, 0x00, 0x41)));
  const src = pseudo(50000, 37, 11);
  assert.deepEqual(inflateRaw(deflate.deflateRaw(src)), src);
  assert.deepEqual(containers.zlibDecompress(containers.zlibCompress(src)),
                   src);
  const gz = containers.gzipCompress(S('hi'));
  assert.deepEqual(gz.subarray(4, 8), B(0, 0, 0, 0));
  const broken = Uint8Array.from(gz);
  broken[broken.length - 5] ^= 0xff;
  assert.throws(() => containers.gzipDecompress(broken));
});

test('모든 모듈이 왕복한다', () => {
  const cases = [new Uint8Array(0), S('A'), repeat(0, 5000),
                 pseudo(20000, 37, 11), pseudo(70000, 131, 3)];
  for (const e of ENTRIES) {
    if (e.encode === null) continue;   // 복호기만 있는 모듈은 건너뛴다
    for (const src of cases) {
      assert.deepEqual(e.decode(e.encode(src)), src,
                       `${e.name} ${src.length}`);
    }
  }
});

// 그림판 하나로 다섯 언어를 맞춘다. 숫자는 파이썬 기준 (§19.4·§19.6).
function testImage(): Uint8Array {
  const px = new Uint8Array(37 * 40);
  for (let y = 0; y < 40; y++) {
    for (let x = 0; x < 37; x++) {
      px[y * 37 + x] = (x * 7 + y * 13 + ((x * y) >> 3)) & 0xff;
    }
  }
  return px;
}

test('lossy — paeth·지그재그·양자화', () => {
  assert.equal(lossy.paeth(10, 20, 15), 15);
  assert.equal(lossy.paeth(200, 100, 150), 150);
  assert.deepEqual(lossy.ZIGZAG.slice(0, 4), [0, 1, 8, 16]);
  // 데드존이 있는 쪽이 0 에 더 가깝게 깎인다.
  assert.equal(lossy.quantise(7, 4), 2);
  assert.equal(lossy.quantise(7, 4, true), 1);
});

test('lossy — jpeglite 는 품질을 올리면 오차가 준다', () => {
  const px = testImage();
  const wantLen = [272, 537, 1086];
  const wantErr = [28002, 16409, 5151];
  [10, 50, 90].forEach((q, i) => {
    const enc = lossy.jpegliteEncode(px, 37, 40, q);
    assert.equal(enc.length, wantLen[i]);
    const img = lossy.jpegliteDecode(enc);
    assert.equal(img.width, 37);
    assert.equal(img.height, 40);
    let sum = 0;
    for (let j = 0; j < px.length; j++) {
      sum += Math.abs(img.pixels[j] - px[j]);
    }
    assert.equal(sum, wantErr[i]);
  });
});

test('lossy — IMA ADPCM 은 예측기를 안 보낸다', () => {
  const samples: number[] = [];
  for (let i = 0; i < 200; i++) {
    samples.push(Math.trunc((3000 * (((i * 37) % 101) - 50)) / 50));
  }
  const a = lossy.adpcmEncode(samples);
  assert.equal(a.length, 100);
  assert.equal(a[0], 255);
  const sum = lossy.adpcmDecode(a, 200).reduce((x, y) => x + y, 0);
  assert.equal(sum, -1515);
});
