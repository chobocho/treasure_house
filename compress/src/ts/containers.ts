// zlib 과 gzip 컨테이너 — SPEC §10.8 (RFC 1950, RFC 1952).
//
// gzip 머리의 MTIME 을 **0 으로 못 박는다.** 진짜 gzip 은 파일의 수정
// 시각을 적어서 같은 입력에 같은 바이트가 안 나온다 — 재현이 안 된다.
import { Bytes, concat, fail } from './common';
import { adler32, crc32 } from './checksums';
import { deflateRaw } from './deflate';
import { inflateRaw } from './inflate';

export const ZLIB_CMF = 0x78; // CM 8 = deflate, CINFO 7 = 32 KiB 창
// FDICT 0, FLEVEL 2, 그리고 (CMF<<8|FLG) 가 31 의 배수
export const ZLIB_FLG = 0x9c;
export const GZIP_DEFLATE = 8;
export const GZIP_OS_UNKNOWN = 255;

function be32(v: number): Bytes {
  return Uint8Array.of((v >>> 24) & 0xff, (v >>> 16) & 0xff,
                       (v >>> 8) & 0xff, v & 0xff);
}

function le32(v: number): Bytes {
  return Uint8Array.of(v & 0xff, (v >>> 8) & 0xff,
                       (v >>> 16) & 0xff, (v >>> 24) & 0xff);
}

export function zlibCompress(src: Bytes): Bytes {
  return concat([Uint8Array.of(ZLIB_CMF, ZLIB_FLG), deflateRaw(src),
                 be32(adler32(src))]);
}

export function zlibDecompress(src: Bytes): Bytes {
  if (src.length < 6) fail('zlib 스트림이 너무 짧다');
  const cmf = src[0];
  const flg = src[1];
  if ((cmf & 0x0f) !== 8) fail(`zlib CM 이 8 이 아니다: ${cmf & 0x0f}`);
  if (((cmf << 8) | flg) % 31) {
    fail('zlib 머리의 검사식이 31 로 안 나눠진다');
  }
  if (flg & 0x20) fail('미리 정한 사전(FDICT)은 지원하지 않는다');
  const out = inflateRaw(src.subarray(2, src.length - 4));
  const tail = src.subarray(src.length - 4);
  const want = (tail[0] * 16777216 + tail[1] * 65536 +
                tail[2] * 256 + tail[3]) >>> 0;
  if (adler32(out) !== want) fail('Adler-32 가 다르다');
  return out;
}

export function gzipCompress(src: Bytes): Bytes {
  const head = Uint8Array.of(0x1f, 0x8b, GZIP_DEFLATE, 0,
                             0, 0, 0, 0, 0, GZIP_OS_UNKNOWN);
  return concat([head, deflateRaw(src), le32(crc32(src)),
                 le32(src.length >>> 0)]);
}

export function gzipDecompress(src: Bytes): Bytes {
  if (src.length < 18) fail('gzip 스트림이 너무 짧다');
  if (src[0] !== 0x1f || src[1] !== 0x8b) fail('gzip 매직이 아니다');
  if (src[2] !== GZIP_DEFLATE) {
    fail(`gzip CM 이 8 이 아니다: ${src[2]}`);
  }
  const flg = src[3];
  let pos = 10;
  if (flg & 0x04) {
    // FEXTRA
    pos += 2 + (src[pos] | (src[pos + 1] << 8));
  }
  for (const bit of [0x08, 0x10]) {
    // FNAME, FCOMMENT
    if (flg & bit) {
      while (pos < src.length && src[pos]) pos++;
      pos++;
    }
  }
  if (flg & 0x02) pos += 2; // FHCRC
  if (pos + 8 >= src.length) fail('gzip 머리가 잘렸다');
  const out = inflateRaw(src.subarray(pos, src.length - 8));
  const tail = src.subarray(src.length - 8);
  const crc = (tail[0] + tail[1] * 256 + tail[2] * 65536 +
               tail[3] * 16777216) >>> 0;
  const size = (tail[4] + tail[5] * 256 + tail[6] * 65536 +
                tail[7] * 16777216) >>> 0;
  if (crc32(out) !== crc) fail('CRC-32 가 다르다');
  if ((out.length >>> 0) !== size) fail('ISIZE 가 푼 길이와 다르다');
  return out;
}
