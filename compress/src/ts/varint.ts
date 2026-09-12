// LEB128 가변 길이 정수 — SPEC §2.1.
//
// 명세에서는 intcode 의 일부지만 파일을 갈랐다. 모든 코덱 헤더가 varint
// 로 시작하는데 intcode 는 비트 스트림을 쓰고 bitio 의 골든 코덱은 다시
// varint 를 쓴다. 다섯 언어 모두 같은 이유로 같게 갈라 뒀다.
//
// 여기서 다루는 값은 길이뿐이라 2^32 를 넘지 않는다. 그래서 number 로
// 두고 32비트를 넘는 시프트만 피한다 — >>> 7 은 2^32 미만에서 안전하다.
import { Bytes, fail } from './common';

export const MAX_BYTES = 10;
// 길이 칸의 상한. 손상된 헤더가 불가능한 할당을 요구하지 못하게 막는다.
export const MAX_LENGTH = 0xffffffff;

export function put(value: number): Bytes {
  const out: number[] = [];
  let v = value;
  for (;;) {
    const b = v % 128;
    v = Math.floor(v / 128);
    if (v !== 0) {
      out.push(b | 0x80);
    } else {
      out.push(b);
      return Uint8Array.from(out);
    }
  }
}

export function get(src: Bytes, pos: number): [number, number] {
  let value = 0;
  let scale = 1;
  for (let i = 0; i < MAX_BYTES; i++) {
    if (pos >= src.length) fail('varint 가 잘렸다');
    const b = src[pos++];
    value += (b & 0x7f) * scale;
    if ((b & 0x80) === 0) {
      if (!Number.isSafeInteger(value)) fail('varint 가 너무 크다');
      return [value, pos];
    }
    scale *= 128;
  }
  return fail(`varint 가 ${MAX_BYTES}바이트를 넘는다`);
}

export function getLength(src: Bytes, pos: number): [number, number] {
  const [v, next] = get(src, pos);
  if (v > MAX_LENGTH) fail(`길이 칸이 너무 크다: ${v}`);
  return [v, next];
}
