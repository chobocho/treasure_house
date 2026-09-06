// 저장 — CRC 검증값, 왕복, 손상 검출.
import * as H from './harness';
import * as G from '../src/game';
import * as S from '../src/save';

function bytesOf(s: string): number[] {
  const out: number[] = [];
  for (let i = 0; i < s.length; i++) out.push(s.charCodeAt(i));
  return out;
}

export function run(): number {
  H.title('save');

  H.check('crc16 빈 입력', S.crc16([]), 0xffff);
  H.check('crc16 "123456789"', S.crc16(bytesOf('123456789')), 0x29b1);
  H.check('crc16 "A"', S.crc16(bytesOf('A')), 0xb915);
  const r16: number[] = [];
  for (let i = 0; i < 16; i++) r16.push(i);
  H.check('crc16 0x00..0F', S.crc16(r16), 0x3b37);
  H.check('표 크기', S.CRC_TBL.length, 256);
  H.check('표 앞 4개', S.CRC_TBL.slice(0, 4), [0, 4129, 8258, 12387]);

  // 한 비트만 바꿔도 값이 바뀌는가
  const base = S.crc16(bytesOf('ISORPG-SAVE'));
  let diff = 0;
  for (let i = 0; i < 11; i++) {
    for (let b = 0; b < 8; b++) {
      const d = bytesOf('ISORPG-SAVE');
      // 8비트 값이라 여기서는 JS 의 ^ 가 안전하다
      d[i] = (d[i] as number) ^ (1 << b);
      if (S.crc16(d) !== base) diff += 1;
    }
  }
  H.check('1비트 변화 88가지 모두 다른 CRC', diff, 88);

  // ---- 상태 왕복
  const g = new G.Game();
  for (let i = 0; i < 30; i++) g.tick();
  const blob = S.packState(g);
  H.check('매직', Array.from(blob.subarray(0, 4)), S.MAGIC);
  H.checkTrue('CRC 가 뒤에 붙는다',
    S.crc16(blob.subarray(0, blob.length - 2))
    === (blob[blob.length - 2] as number) * 256 + (blob[blob.length - 1] as number));

  const g2 = new G.Game();
  S.unpackState(blob, g2);
  H.check('왕복 후 다시 저장한 바이트가 같다', S.packState(g2), blob);
  H.check('틱', g2.tickN, g.tickN);
  H.check('난수 상태', g2.rng.s, g.rng.s);
  const p1 = g.ents[0] as G.Entity;
  const p2 = g2.ents[0] as G.Entity;
  H.check('플레이어 좌표', [p2.fx, p2.fy], [p1.fx, p1.fy]);
  H.check('안개', g2.fog.bits, g.fog.bits);

  // ---- 복원한 뒤 이어서 돌리면 같은 결과인가
  for (let i = 0; i < 20; i++) {
    g.tick();
    g2.tick();
  }
  H.check('복원 후 20틱 진행 결과가 같다', S.packState(g2), S.packState(g));

  // ---- 손상 검출
  const badBlob = Uint8Array.from(blob);
  badBlob[10] = (badBlob[10] as number) ^ 0xff;
  const g3 = new G.Game();
  try {
    S.unpackState(badBlob, g3);
    H.check('손상된 세이브를 거부', 'no error', 'Error');
  } catch {
    H.check('손상된 세이브를 거부', 'Error', 'Error');
  }

  // ---- 음수 좌표 (i32 2의 보수)
  H.check('u32 왕복 -1', S.i32ToU32(-1), 4294967295);
  H.check('u32 왕복 -65536', S.u32ToI32(S.i32ToU32(-65536)), -65536);
  H.check('u32 왕복 최대', S.u32ToI32(S.i32ToU32(2147483647)), 2147483647);
  H.check('u32 왕복 최소', S.u32ToI32(S.i32ToU32(-2147483648)), -2147483648);

  return H.done();
}
