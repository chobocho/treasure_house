// 손실 압축 — SPEC §19.
//
// 여기까지는 한 비트도 안 버렸다. 이 모듈은 **일부러 버린다.** 버리는
// 자리는 딱 하나, 양자화다 — DCT 도 PNG 필터도 그 자체로는 안 버린다.
//
// **레지스트리에 오르는 코덱은 PNG 쪽** 이다. 왕복하는 것이 그것뿐이다.
// 손실 코덱에 골든 벡터를 붙이면 부호기만 못 박는 꼴이다.
import { ByteBuf, Bytes, concat, fail } from './common';
import * as deflate from './deflate';
import * as huffman from './huffman';
import * as varint from './varint';

export const DCT_SCALE = 13;
export const DCT_ROUND = 1 << (DCT_SCALE - 1);
export const BLOCK = 8;
export const PNG_WIDTH = 256;   // 골든 코덱이 쓰는 행 폭 (§19.5)
export const PNG_BPP = 1;
export const EOB = 255;

// DCT-TABLE-BEGIN — gen_tables.py 가 다섯 언어를 대조한다 (§19.2)
export const DCT = [
  2896, 2896, 2896, 2896, 2896, 2896, 2896, 2896,
  4017, 3406, 2276, 799, -799, -2276, -3406, -4017,
  3784, 1567, -1567, -3784, -3784, -1567, 1567, 3784,
  3406, -799, -4017, -2276, 2276, 4017, 799, -3406,
  2896, -2896, -2896, 2896, 2896, -2896, -2896, 2896,
  2276, -4017, 799, 3406, -3406, -799, 4017, -2276,
  1567, -3784, 3784, -1567, -1567, 3784, -3784, 1567,
  799, -2276, 3406, -4017, 4017, -3406, 2276, -799];
// DCT-TABLE-END

// JPEGQ-TABLE-BEGIN — gen_tables.py 가 다섯 언어를 대조한다 (§19.4)
export const JPEG_QUANT = [
  16, 11, 10, 16, 24, 40, 51, 61,
  12, 12, 14, 19, 26, 58, 60, 55,
  14, 13, 16, 24, 40, 57, 69, 56,
  14, 17, 22, 29, 51, 87, 80, 62,
  18, 22, 37, 56, 68, 109, 103, 77,
  24, 35, 55, 64, 81, 104, 113, 92,
  49, 64, 78, 87, 103, 121, 120, 101,
  72, 92, 95, 98, 112, 100, 103, 99];
// JPEGQ-TABLE-END

// ADPCMSTEP-TABLE-BEGIN — gen_tables.py 가 대조한다 (§19.6)
export const ADPCM_STEP = [
  7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 19, 21, 23, 25, 28, 31,
  34, 37, 41, 45, 50, 55, 60, 66, 73, 80, 88, 97, 107, 118, 130,
  143, 157, 173, 190, 209, 230, 253, 279, 307, 337, 371, 408, 449,
  494, 544, 598, 658, 724, 796, 876, 963, 1060, 1166, 1282, 1411,
  1552, 1707, 1878, 2066, 2272, 2499, 2749, 3024, 3327, 3660, 4026,
  4428, 4871, 5358, 5894, 6484, 7132, 7845, 8630, 9493, 10442, 11487,
  12635, 13899, 15289, 16818, 18500, 20350, 22385, 24623, 27086,
  29794, 32767];
// ADPCMSTEP-TABLE-END

// ADPCMINDEX-TABLE-BEGIN — gen_tables.py 가 대조한다 (§19.6)
export const ADPCM_INDEX = [-1, -1, -1, -1, 2, 4, 6, 8,
                            -1, -1, -1, -1, 2, 4, 6, 8];
// ADPCMINDEX-TABLE-END

// 8×8 을 대각선으로 훑는 순서. 표가 아니라 규칙이라 여기서 만든다.
export const ZIGZAG = (() => {
  const out: number[] = [];
  for (let s = 0; s < 15; s++) {
    const cells: Array<[number, number]> = [];
    for (let x = 0; x < 8; x++) {
      const y = s - x;
      if (y >= 0 && y < 8) cells.push([x, y]);
    }
    if (s % 2 === 1) cells.reverse();
    for (const [x, y] of cells) out.push(y * 8 + x);
  }
  return out;
})();

// 버리는 곳은 여기 하나뿐이다 (§19.3).
export function quantise(v: number, q: number,
                         deadZone = false): number {
  if (deadZone) {
    return v < 0 ? -Math.floor(-v / q) : Math.floor(v / q);
  }
  if (v < 0) return -Math.floor((-v * 2 + q) / (2 * q));
  return Math.floor((v * 2 + q) / (2 * q));
}

export function dequantise(v: number, q: number): number {
  return v * q;
}

// 8×8 정수 DCT. 1차원 변환 두 번, 각각 반올림 (§19.2).
export function fdct8(block: number[]): number[] {
  const tmp = new Array<number>(64).fill(0);
  const out = new Array<number>(64).fill(0);
  for (let u = 0; u < 8; u++) {
    for (let y = 0; y < 8; y++) {
      let s = 0;
      for (let x = 0; x < 8; x++) {
        s += DCT[u * 8 + x] * block[x * 8 + y];
      }
      tmp[u * 8 + y] = (s + DCT_ROUND) >> DCT_SCALE;
    }
  }
  for (let u = 0; u < 8; u++) {
    for (let v = 0; v < 8; v++) {
      let s = 0;
      for (let y = 0; y < 8; y++) s += DCT[v * 8 + y] * tmp[u * 8 + y];
      out[u * 8 + v] = (s + DCT_ROUND) >> DCT_SCALE;
    }
  }
  return out;
}

export function idct8(coef: number[]): number[] {
  const tmp = new Array<number>(64).fill(0);
  const out = new Array<number>(64).fill(0);
  for (let x = 0; x < 8; x++) {
    for (let v = 0; v < 8; v++) {
      let s = 0;
      for (let u = 0; u < 8; u++) s += DCT[u * 8 + x] * coef[u * 8 + v];
      tmp[x * 8 + v] = (s + DCT_ROUND) >> DCT_SCALE;
    }
  }
  for (let x = 0; x < 8; x++) {
    for (let y = 0; y < 8; y++) {
      let s = 0;
      for (let v = 0; v < 8; v++) s += DCT[v * 8 + y] * tmp[x * 8 + v];
      out[x * 8 + y] = (s + DCT_ROUND) >> DCT_SCALE;
    }
  }
  return out;
}

// 품질 1~100 로 JPEG 표준표를 늘리고 줄인다 (§19.4).
export function quantTable(quality: number): number[] {
  if (quality < 1 || quality > 100) {
    fail(`품질은 1~100 이다: ${quality}`);
  }
  const scale = quality < 50
    ? Math.floor(5000 / quality) : 200 - 2 * quality;
  return JPEG_QUANT.map((base) =>
    Math.max(1, Math.min(255, Math.floor((base * scale + 50) / 100))));
}

// jpeglite — 우리 형식이다. JPEG 이 아니다 (§19.4).
export function jpegliteEncode(pixels: Bytes, width: number,
                               height: number,
                               quality: number): Bytes {
  if (width * height !== pixels.length) {
    fail('픽셀 수가 너비×높이와 다르다');
  }
  if (width <= 0 || height <= 0 || width > 0xffff || height > 0xffff) {
    fail('크기가 범위를 벗어났다');
  }
  const qt = quantTable(quality);
  const stream = new ByteBuf();
  for (let by = 0; by < height; by += BLOCK) {
    for (let bx = 0; bx < width; bx += BLOCK) {
      const block = new Array<number>(64).fill(0);
      for (let y = 0; y < BLOCK; y++) {
        const sy = Math.min(by + y, height - 1);
        for (let x = 0; x < BLOCK; x++) {
          const sx = Math.min(bx + x, width - 1);
          block[x * 8 + y] = pixels[sy * width + sx] - 128;
        }
      }
      const coef = fdct8(block);
      let run = 0;
      for (let k = 0; k < 64; k++) {
        const idx = ZIGZAG[k];
        const v = quantise(coef[idx], qt[idx], k > 0);
        if (v === 0 && k > 0) {
          run++;
          continue;
        }
        while (run >= EOB) {
          stream.push(EOB - 1);
          stream.push(0);
          run -= EOB - 1;
        }
        stream.push(run);
        stream.extend(varint.put(v >= 0 ? v * 2 : -v * 2 - 1));
        run = 0;
      }
      stream.push(EOB);
    }
  }
  const head = Uint8Array.of(0x4a, 0x4c, 0x31, width & 0xff, width >> 8,
                             height & 0xff, height >> 8, quality);
  return concat([head, huffman.encode(stream.bytes())]);
}

export interface Image {
  pixels: Bytes;
  width: number;
  height: number;
}

// 원본과 같지 않다 — 그게 이 형식의 약속이다.
export function jpegliteDecode(src: Bytes): Image {
  if (src.length < 8 || src[0] !== 0x4a || src[1] !== 0x4c ||
      src[2] !== 0x31) {
    fail('jpeglite 매직이 아니다');
  }
  const width = src[3] | (src[4] << 8);
  const height = src[5] | (src[6] << 8);
  const qt = quantTable(src[7]);
  const stream = huffman.decode(src.subarray(8));
  let pos = 0;
  const pixels = new Uint8Array(width * height);
  for (let by = 0; by < height; by += BLOCK) {
    for (let bx = 0; bx < width; bx += BLOCK) {
      const coef = new Array<number>(64).fill(0);
      let k = 0;
      // 끝 표시는 반드시 읽어 치운다 — 64개가 다 실린 블록에서 안 먹고
      // 나가면 다음 블록이 그 255 를 자기 EOB 로 읽는다.
      for (;;) {
        if (pos >= stream.length) fail('계수 스트림이 잘렸다');
        const run = stream[pos++];
        if (run === EOB) break;
        k += run;
        if (k >= 64) fail('0 런이 블록을 넘는다');
        const [z, next] = varint.get(stream, pos);
        pos = next;
        const v = (z & 1) ? -((z + 1) / 2) : z / 2;
        coef[ZIGZAG[k]] = dequantise(v, qt[ZIGZAG[k]]);
        k++;
      }
      const block = idct8(coef);
      for (let y = 0; y < BLOCK; y++) {
        const sy = by + y;
        if (sy >= height) break;
        for (let x = 0; x < BLOCK; x++) {
          const sx = bx + x;
          if (sx >= width) break;
          const p = block[x * 8 + y] + 128;
          pixels[sy * width + sx] = Math.max(0, Math.min(255, p));
        }
      }
    }
  }
  return { pixels, width, height };
}

// 왼쪽·위·왼쪽위 가운데 a+b-c 에 가장 가까운 것. 동점은 a, 그다음 b.
export function paeth(a: number, b: number, c: number): number {
  const p = a + b - c;
  const pa = Math.abs(p - a);
  const pb = Math.abs(p - b);
  const pc = Math.abs(p - c);
  if (pa <= pb && pa <= pc) return a;
  if (pb <= pc) return b;
  return c;
}

function filterRow(row: Bytes, prev: Bytes, kind: number,
                   bpp: number): Bytes {
  const out = new Uint8Array(row.length);
  for (let i = 0; i < row.length; i++) {
    const v = row[i];
    const left = i >= bpp ? row[i - bpp] : 0;
    const up = i < prev.length ? prev[i] : 0;
    const near = i >= bpp && i - bpp < prev.length;
    const upleft = near ? prev[i - bpp] : 0;
    let d: number;
    if (kind === 0) d = v;
    else if (kind === 1) d = v - left;
    else if (kind === 2) d = v - up;
    else if (kind === 3) d = v - ((left + up) >> 1);
    else d = v - paeth(left, up, upleft);
    out[i] = d & 0xff;
  }
  return out;
}

function unfilterRow(row: Bytes, prev: Bytes, kind: number,
                     bpp: number): Bytes {
  const out = new Uint8Array(row.length);
  for (let i = 0; i < row.length; i++) {
    const d = row[i];
    const left = i >= bpp ? out[i - bpp] : 0;
    const up = i < prev.length ? prev[i] : 0;
    const near = i >= bpp && i - bpp < prev.length;
    const upleft = near ? prev[i - bpp] : 0;
    let v: number;
    if (kind === 0) v = d;
    else if (kind === 1) v = d + left;
    else if (kind === 2) v = d + up;
    else if (kind === 3) v = d + ((left + up) >> 1);
    else if (kind === 4) v = d + paeth(left, up, upleft);
    else return fail(`없는 필터 종류: ${kind}`);
    out[i] = v & 0xff;
  }
  return out;
}

// 줄마다 다섯 후보 가운데 절댓값 합이 가장 작은 것을 고른다 (§19.5).
export function pngFilter(data: Bytes, width: number,
                          bpp = PNG_BPP): Bytes {
  const out = new ByteBuf();
  let prev: Bytes = new Uint8Array(0);
  for (let off = 0; off < data.length; off += width) {
    const row = data.subarray(off, Math.min(off + width, data.length));
    let bestKind = 0;
    let bestRow: Bytes = new Uint8Array(0);
    let bestScore = -1;
    for (let kind = 0; kind < 5; kind++) {
      const cand = filterRow(row, prev, kind, bpp);
      let score = 0;
      for (const b of cand) score += b < 128 ? b : 256 - b;
      if (bestScore < 0 || score < bestScore) {
        bestKind = kind;
        bestRow = cand;
        bestScore = score;
      }
    }
    out.push(bestKind);
    out.extend(bestRow);
    prev = row;
  }
  return out.bytes();
}

export function pngUnfilter(data: Bytes, width: number,
                            bpp = PNG_BPP): Bytes {
  const out = new ByteBuf();
  let prev: Bytes = new Uint8Array(0);
  let pos = 0;
  while (pos < data.length) {
    const kind = data[pos++];
    const n = Math.min(width, data.length - pos);
    const part = data.subarray(pos, pos + n);
    const row = unfilterRow(part, prev, kind, bpp);
    pos += n;
    out.extend(row);
    prev = row;
  }
  return out.bytes();
}

// 골든 코덱 — 이 모듈에서 유일하게 왕복한다 (§19.1).
export function encode(src: Bytes): Bytes {
  if (src.length === 0) return varint.put(0);
  return concat([varint.put(src.length),
                 deflate.encode(pngFilter(src, PNG_WIDTH))]);
}

export function decode(src: Bytes): Bytes {
  const [n, pos] = varint.getLength(src, 0);
  if (n === 0) {
    if (pos !== src.length) fail('빈 입력인데 뒤에 바이트가 있다');
    return new Uint8Array(0);
  }
  const out = pngUnfilter(deflate.decode(src.subarray(pos)), PNG_WIDTH);
  if (out.length !== n) {
    fail(`푼 길이가 헤더와 다르다: ${out.length} != ${n}`);
  }
  return out;
}

// IMA ADPCM — 예측기를 안 보내는 것이 요점이다 (§19.6).
export function adpcmEncode(samples: number[]): Bytes {
  const out = new ByteBuf();
  let predictor = 0;
  let index = 0;
  let half = -1;
  for (const s of samples) {
    const step = ADPCM_STEP[index];
    let diff = s - predictor;
    let code = 0;
    if (diff < 0) {
      code = 8;
      diff = -diff;
    }
    const mag = Math.min(7, Math.floor((diff * 4) / step));
    code |= mag;
    let delta = step >> 3;
    if (mag & 4) delta += step;
    if (mag & 2) delta += step >> 1;
    if (mag & 1) delta += step >> 2;
    predictor += (code & 8) ? -delta : delta;
    predictor = Math.max(-32768, Math.min(32767, predictor));
    index = Math.max(0, Math.min(88, index + ADPCM_INDEX[code & 7]));
    if (half < 0) {
      half = code;
    } else {
      out.push((half << 4) | code);
      half = -1;
    }
  }
  if (half >= 0) out.push(half << 4);
  return out.bytes();
}

export function adpcmDecode(data: Bytes, count: number): number[] {
  const out: number[] = [];
  let predictor = 0;
  let index = 0;
  for (let i = 0; i < count; i++) {
    if (i >> 1 >= data.length) fail('ADPCM 스트림이 잘렸다');
    const byte = data[i >> 1];
    const code = (i & 1) === 0 ? byte >> 4 : byte & 0x0f;
    const step = ADPCM_STEP[index];
    const mag = code & 7;
    let delta = step >> 3;
    if (mag & 4) delta += step;
    if (mag & 2) delta += step >> 1;
    if (mag & 1) delta += step >> 2;
    predictor += (code & 8) ? -delta : delta;
    predictor = Math.max(-32768, Math.min(32767, predictor));
    index = Math.max(0, Math.min(88, index + ADPCM_INDEX[code & 7]));
    out.push(predictor);
  }
  return out;
}
