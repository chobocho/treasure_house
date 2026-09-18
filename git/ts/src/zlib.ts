// zlib 겉옷 (SPEC.md §3) — 느슨한 객체와 팩 항목이 입는 옷.
//
// TypeScript 는 node 의 표준 zlib 을 쓴다(SPEC.md §3.1 의 표). 이
// 모듈이 따로 있는 까닭은 둘이다. 하나, 다섯 언어가 같은 이름(compress·
// decompress·decompressPrefix·adler32)으로 부르게 하려고. 둘, 팩
// 안에서는 "스트림이 몇 바이트에서 끝나는가" 가 필요한데, 그 수는
// inflateSync 에 { info: true } 를 주어야 엔진의 bytesWritten 으로
// 얻는다 — 엔진은 스트림 끝에서 멈추고 뒤따르는 바이트를 먹지 않는다.
import * as z from 'node:zlib';
import { GitError } from './errors';

// git 의 느슨한 객체 기본값과 같은 "가장 빠르게"
export const LEVEL = 1;

export function compress(data: Uint8Array): Buffer {
  return z.deflateSync(data, { level: LEVEL });
}

// data[start:] 에서 zlib 스트림 하나를 풀어 [바이트, 먹은 수].
//
// 먹은 수에는 머리 2바이트와 Adler-32 꼬리 4바이트가 들어간다 —
// 다음 팩 항목은 정확히 거기서 시작한다. O(스트림 길이).
export function decompressPrefix(data: Buffer, start = 0):
  [Buffer, number] {
  try {
    // @types/node 는 info 를 준 꼴의 반환형을 모른다
    const r = z.inflateSync(data.subarray(start), { info: true }) as
      unknown as { buffer: Buffer; engine: z.Inflate };
    return [r.buffer, r.engine.bytesWritten];
  } catch (e) {
    // 스트림이 끝나기 전에 입력이 떨어지면 Z_BUF_ERROR 다
    const cut = (e as NodeJS.ErrnoException).code === 'Z_BUF_ERROR';
    throw new GitError(cut ? 'fatal: mygit: truncated zlib stream'
      : 'fatal: mygit: corrupt zlib stream');
  }
}

// 스트림 하나를 끝까지. 뒤에 남는 바이트가 있으면 오류다.
export function decompress(data: Buffer): Buffer {
  const [out, used] = decompressPrefix(data);
  if (used !== data.length) {
    throw new GitError('fatal: mygit: garbage after zlib stream');
  }
  return out;
}

// node 의 zlib 은 crc32 는 내놓지만 adler32 는 내놓지 않는다. RFC 1950
// §8.2 그대로 — 두 합을 65521(2¹⁶ 아래 가장 큰 소수)로 나눈 나머지.
export function adler32(data: Uint8Array): number {
  let a = 1;
  let b = 0;
  for (const byte of data) {
    a = (a + byte) % 65521;
    b = (b + a) % 65521;
  }
  return ((b << 16) | a) >>> 0;
}
