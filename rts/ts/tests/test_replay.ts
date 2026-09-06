// 저장·리플레이·압축 (SPEC §20).

import * as H from './harness';
import * as F from '../src/fixed';
import * as RP from '../src/replay';
import * as SEL from '../src/select';
import * as T from '../src/tmap';

H.title('replay');

const LOG: RP.LogEntry[] = [
  [1, [[0, 256, SEL.MOVE, 3, 4, 0]]],
  [4, [[0, 256, SEL.BUILD, 12, 6, 10], [1, 512, SEL.TRAIN, 4, 0, 0]]],
  [9, [[1, 65535, SEL.ATTACK, 30, 30, 65280]]]];

// 바이트열 안에 짧은 바이트열이 들어 있는가 (파이썬 `in` 자리).
function contains(hay: number[], needle: number[]): boolean {
  for (let i = 0; i + needle.length <= hay.length; i += 1) {
    let ok = true;
    for (let k = 0; k < needle.length; k += 1) {
      if (hay[i + k] !== needle[k]) {
        ok = false;
        break;
      }
    }
    if (ok) return true;
  }
  return false;
}

// ── SPEC §20.2 리플레이 = 명령 로그 ─────────────────────────────────────────
const blob = RP.save(12345, 2, 1200, LOG);
H.check('머리는 RTSR', blob.slice(0, 4), F.ascii('RTSR'));
H.check('버전', blob[4], RP.VERSION);
const [seed, players, ticks, log] = RP.load(blob);
H.check('머리를 그대로 읽는다', [seed, players, ticks], [12345, 2, 1200]);
H.check('본문을 그대로 읽는다', log, LOG);
H.check('꼬리는 CRC-16 두 바이트',
        blob[blob.length - 2] * 256 + blob[blob.length - 1],
        F.crc16(blob.slice(0, blob.length - 2)));

const broken = blob.slice();
broken[10] = (broken[10] + 1) % 256;
let err = 0;
try {
  RP.load(broken);
} catch (e) {
  err = 1;
}
H.check('한 바이트만 바뀌어도 CRC 가 잡는다', err, 1);
err = 0;
try {
  RP.load(F.ascii('XXXX').concat(blob.slice(4)));
} catch (e) {
  err = 1;
}
H.check('머리가 다르면 거부', err, 1);
H.check('빈 로그도 왕복한다', RP.load(RP.save(1, 2, 0, []))[3], []);
H.check('틱은 오름차순으로 저장한다',
        RP.load(RP.save(1, 2, 10, [[5, []], [2, []]]))[3].map((e) => e[0]),
        [2, 5]);

H.checkTrue('1200틱 리플레이는 수백 바이트 (' + blob.length + ')',
            blob.length < 1000);
const snap = 4096;
H.note('같은 게임의 상태 스냅샷은 틱당 약 ' + snap + '바이트 — 1200틱이면 '
       + Math.floor(snap * 1200 / 1024) + ' KB');
H.check('상태는 한 바이트도 저장하지 않는다', contains(blob, F.ascii('hp')),
        false);

// ── SPEC §20.3 RLE ──────────────────────────────────────────────────────────
H.check('빈 입력', RP.rleEncode([]), []);
H.check('한 바이트', RP.rleEncode(F.ascii('A')), [1, 65]);
H.check('세 번 반복', RP.rleEncode(F.ascii('AAA')), [3, 65]);
H.check('바뀌면 새 쌍', RP.rleEncode(F.ascii('AAB')), [2, 65, 1, 66]);
H.check('255 를 넘으면 쌍을 나눈다',
        RP.rleEncode(F.ascii('A'.repeat(300))).length, 4);
H.check('왕복', RP.rleDecode(RP.rleEncode(F.ascii('A'.repeat(300) + 'BC'))),
        F.ascii('A'.repeat(300) + 'BC'));
const data = H.range(1000).map((k) => k % 7);
H.check('반복이 없으면 두 배로 늘어난다', RP.rleEncode(data).length, 2000);
H.check('그래도 왕복한다', RP.rleDecode(RP.rleEncode(data)), data);

// ── SPEC §20.4 LZSS ─────────────────────────────────────────────────────────
H.check('빈 입력', RP.lzssEncode([]), []);
H.check('짧은 입력은 전부 리터럴', RP.lzssEncode(F.ascii('AB')),
        [3, 65, 66]);
H.check('AAAAAAAA 는 리터럴 하나 + 토큰 하나',
        RP.lzssEncode(F.ascii('A'.repeat(8))), [1, 65, 0, 4]);
H.note('플래그 1바이트 · 리터럴 A · (offset-1=0, len-3=4) 두 바이트 = 4바이트');
H.check('왕복', RP.lzssDecode(RP.lzssEncode(F.ascii('A'.repeat(8)))),
        F.ascii('A'.repeat(8)));
H.check('최대 일치는 18', RP.lzssDecode(RP.lzssEncode(F.ascii('B'.repeat(40)))),
        F.ascii('B'.repeat(40)));

const SAMPLES: number[][] = [
  [], F.ascii('A'), F.ascii('AB'), F.ascii('ABABABABABAB'),
  F.ascii('A'.repeat(5000)),
  H.range(3000).map((k) => (k * 37) % 251),
  H.range(4200).map((k) => k % 3)];
for (const sample of SAMPLES) {
  if (!H.deepEq(RP.lzssDecode(RP.lzssEncode(sample)), sample)) {
    H.check('왕복 실패 (길이 ' + sample.length + ')', false, true);
  }
}
H.check('여러 표본에서 왕복', true, true);

H.checkTrue('창은 4096, 최소 일치 3, 최대 일치 18',
            RP.WINDOW === 4096 && RP.MIN_MATCH === 3 && RP.MAX_MATCH === 18);

// 동점이면 가장 가까운 일치 (탐욕적)
const enc = RP.lzssEncode(F.ascii('XYZ' + 'Q'.repeat(3) + 'XYZ' + 'XYZ'));
H.check('탐욕 일치도 왕복한다', RP.lzssDecode(enc), F.ascii('XYZQQQXYZXYZ'));

// 실제 맵으로 압축률을 잰다 — "보통 절반" 같은 문장은 쓰지 않는다
const m = T.TMap.loadText(H.golden('map_start.txt'));
const plane = m.terrain.slice();
const rRle = RP.rleEncode(plane).length;
const rLz = RP.lzssEncode(plane).length;
H.check('맵 지형 평면 왕복 (RLE)', RP.rleDecode(RP.rleEncode(plane)), plane);
H.check('맵 지형 평면 왕복 (LZSS)', RP.lzssDecode(RP.lzssEncode(plane)), plane);
H.note('64x64 지형 평면 ' + plane.length + '바이트 → RLE ' + rRle
       + ' · LZSS ' + rLz);
H.checkTrue('둘 다 원본보다 작다', rRle < plane.length && rLz < plane.length);

H.done();
