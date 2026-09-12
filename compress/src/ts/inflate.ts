// inflate — RFC 1951 복호기 (SPEC §10.7).
//
// 부호기보다 복호기가 먼저다. 형식을 읽을 줄 알아야 내가 쓴 것이 맞는지
// 알 수 있고, 무엇보다 진짜 gzip 이 만든 파일을 풀 수 있어야 한다.
//
// 예외 하나: 거리 부호가 하나뿐인 표는 크래프트 합이 1/2 라 "모자란"
// 표인데, RFC 가 허용하고 zlib 도 낸다. 일치 없는 블록에서 나온다.
import { ByteBuf, Bytes, fail } from './common';
import { LsbReader } from './bitio';
import { Decoder, checkComplete } from './huffman';
import * as T from './deflateTables';

function table(lengths: number[]): Decoder {
  checkComplete(lengths);
  return new Decoder(lengths);
}

function readBody(r: LsbReader, out: ByteBuf, litlen: Decoder,
                  dist: Decoder): void {
  for (;;) {
    const sym = litlen.read(r);
    if (sym < 256) {
      out.push(sym);
      continue;
    }
    if (sym === T.END_OF_BLOCK) return;
    const idx = sym - 257;
    if (idx >= T.LENGTH_BASE.length) fail(`길이 부호 ${sym} 는 없다`);
    const length = T.LENGTH_BASE[idx] + r.readBits(T.LENGTH_EXTRA[idx]);
    const dcode = dist.read(r);
    if (dcode >= T.DIST_SYMBOLS) {
      fail(`거리 부호 ${dcode} 는 안 쓰인다`);
    }
    const d = T.DIST_BASE[dcode] + r.readBits(T.DIST_EXTRA[dcode]);
    if (d > out.size) fail(`거리 ${d} 가 지금까지 낸 것보다 멀다`);
    const at = out.size - d;
    // 한 바이트씩 앞으로. 거리 1 짜리 긴 일치가 여기 기댄다.
    for (let k = 0; k < length; k++) out.push(out.at(at + k));
  }
}

function readDynamic(r: LsbReader): [Decoder, Decoder] {
  const hlit = r.readBits(5) + 257;
  const hdist = r.readBits(5) + 1;
  const hclen = r.readBits(4) + 4;
  if (hlit > T.LITLEN_SYMBOLS || hdist > T.DIST_SYMBOLS) {
    fail('HLIT/HDIST 가 알파벳을 넘는다');
  }
  const clLengths = new Array<number>(T.CL_SYMBOLS).fill(0);
  for (let i = 0; i < hclen; i++) {
    clLengths[T.CL_ORDER[i]] = r.readBits(3);
  }
  const cl = table(clLengths);

  const lengths: number[] = [];
  const want = hlit + hdist;
  while (lengths.length < want) {
    const sym = cl.read(r);
    if (sym < 16) {
      lengths.push(sym);
    } else if (sym === T.CL_REPEAT) {
      if (lengths.length === 0) fail('부호 16 이 맨 앞에 왔다');
      const prev = lengths[lengths.length - 1];
      for (let i = r.readBits(2) + 3; i > 0; i--) lengths.push(prev);
    } else if (sym === T.CL_ZERO_SHORT) {
      for (let i = r.readBits(3) + 3; i > 0; i--) lengths.push(0);
    } else {
      for (let i = r.readBits(7) + 11; i > 0; i--) lengths.push(0);
    }
  }
  if (lengths.length !== want) {
    fail('부호 길이 되풀이가 표 끝을 넘었다');
  }
  return [table(lengths.slice(0, hlit)), table(lengths.slice(hlit))];
}

export function inflateRaw(src: Bytes): Bytes {
  const r = new LsbReader(src);
  const out = new ByteBuf();
  let fixedLit: Decoder | null = null;
  let fixedDst: Decoder | null = null;
  for (;;) {
    const final = r.readBit();
    const btype = r.readBits(2);
    if (btype === 0) {
      r.align();
      let p = r.pos;
      if (p + 4 > src.length) fail('stored 블록 머리가 잘렸다');
      const ln = src[p] | (src[p + 1] << 8);
      const nln = src[p + 2] | (src[p + 3] << 8);
      p += 4;
      if (ln !== (nln ^ 0xffff)) fail('NLEN 이 LEN 의 보수가 아니다');
      if (p + ln > src.length) fail('stored 블록 몸통이 잘렸다');
      out.extend(src, p, p + ln);
      r.pos = p + ln;
    } else if (btype === 1) {
      if (fixedLit === null) {
        fixedLit = table(T.FIXED_LITLEN);
        fixedDst = table(T.FIXED_DIST);
      }
      readBody(r, out, fixedLit, fixedDst as Decoder);
    } else if (btype === 2) {
      const [lit, dst] = readDynamic(r);
      readBody(r, out, lit, dst);
    } else {
      fail('BTYPE 11 은 없는 블록 종류다');
    }
    if (final) return out.bytes();
  }
}
