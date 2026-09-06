// PC 스피커 — 분주값·음표표·사각파 (SPEC §21).

import * as H from './harness';
import * as C from '../src/const';
import * as F from '../src/fixed';
import * as SP from '../src/speaker';

H.title('speaker');

const g = H.golden('prim.txt').split('\n');

// ── 골든 14절 분주값 표 ─────────────────────────────────────────────────────
let i = g.indexOf('== 14. PIT 분주값 ==') + 2;
let bad = 0;
let n = 0;
while (i < g.length && g[i].trim() !== '') {
  const p = H.fields(g[i]);
  const name = p[0];
  const f = parseInt(p[1], 10);
  const div = parseInt(p[2], 10);
  const act = parseInt(p[3], 10);
  const diff = parseInt(p[4], 10);
  const got = [SP.NOTE_NAME[n], SP.NOTE_HZ[n], SP.divisor(f), SP.actual100(f)];
  if (!H.deepEq(got, [name, f, div, act])) {
    bad += 1;
    H.note(name + ' 기대 ' + JSON.stringify([name, f, div, act])
           + ' 실제 ' + JSON.stringify(got));
  }
  if (act - f * 100 !== diff) bad += 1;
  n += 1;
  i += 1;
}
H.check('골든 14절 ' + n + '음', bad, 0);
H.check('24음 (C4..B5)', n, 24);
H.check('A4 는 440 Hz', SP.NOTE_HZ[SP.NOTE_NAME.indexOf('A4')], 440);
H.check('C4 는 262 Hz (261.63 반올림)', SP.NOTE_HZ[0], 262);

// ── SPEC §21.1 분주값 ───────────────────────────────────────────────────────
H.check('분주값은 반올림 나눗셈', SP.divisor(440),
        F.floordiv(C.PIT_HZ + 220, 440));
H.check('1 Hz 는 분주값이 PIT 클럭 그대로', SP.divisor(1), C.PIT_HZ);
H.check('분주값은 1 아래로 내려가지 않는다', SP.divisor(10000000), 1);
H.check('실제 주파수는 몫과 나머지로만 낸다', SP.actual(440),
        [F.floordiv(C.PIT_HZ, SP.divisor(440)),
         F.fmod(C.PIT_HZ, SP.divisor(440))]);
H.checkTrue('440 Hz 의 실제 값은 439.96 Hz', SP.actual100(440) === 43996);
H.note('센트 오차는 로그가 필요해 엔진이 아니라 gen_prim 이 낸다');
H.check('PIT_HZ 는 반올림값 — 정확한 값은 14.31818MHz/12 = 1193181.8181…',
        C.PIT_HZ, 1193182);

// ── SPEC §21.3 사각파 ───────────────────────────────────────────────────────
H.check('샘플레이트', SP.SAMPLE_RATE, 22050);
const half = SP.halfPeriod(440);
H.check('반주기 = 22050 / (2 · 실제주파수)', half,
        F.floordiv(SP.SAMPLE_RATE, 2 * SP.actual(440)[0]));
const pcm = SP.square(440, 100);
H.check('요청한 만큼 샘플이 나온다', pcm.length, 100);
H.check('진폭은 두 값뿐 (듀티비 고정 — 음량 조절이 없었다)',
        H.sortedSet(pcm), [0x40, 0xC0]);
H.check('첫 반주기는 같은 값', H.sortedSet(pcm.slice(0, half)).length, 1);
H.check('반주기 뒤에 뒤집힌다', pcm[0] !== pcm[half], true);
H.check('쉼표는 무음 (0x80)', H.sortedSet(SP.square(0, 50)), [0x80]);
H.check('길이 0 이면 빈 소리', SP.square(440, 0), []);

// ── WAV ─────────────────────────────────────────────────────────────────────
const wav = SP.wav(pcm);
H.check('헤더는 44바이트', wav.length, 44 + pcm.length);
H.check('RIFF/WAVE', [wav.slice(0, 4), wav.slice(8, 12)],
        [F.ascii('RIFF'), F.ascii('WAVE')]);
H.check('fmt 청크', wav.slice(12, 16), F.ascii('fmt '));
H.check('data 청크', wav.slice(36, 40), F.ascii('data'));
H.check('PCM · 모노 · 8비트', [wav[20], wav[22], wav[34]], [1, 1, 8]);
H.check('샘플레이트가 머리에 들어간다',
        wav[24] + wav[25] * 256 + wav[26] * 65536 + wav[27] * 16777216,
        SP.SAMPLE_RATE);
H.check('RIFF 크기 = 전체 - 8',
        wav[4] + wav[5] * 256 + wav[6] * 65536 + wav[7] * 16777216,
        wav.length - 8);

const tune = SP.tune([[SP.NOTE_HZ[0], 20], [0, 5], [SP.NOTE_HZ[12], 20]]);
H.check('연속 연주는 이어 붙인 것', tune.length, 44 + 45);
H.checkTrue('바이트 해시가 결정론적 (' + F.fnv1a(tune).toString(16) + ')',
            F.fnv1a(tune) === F.fnv1a(SP.tune([[SP.NOTE_HZ[0], 20], [0, 5],
                                               [SP.NOTE_HZ[12], 20]])));
H.note('소리를 재생하지 않는다 — 헤드리스이고, 바이트가 같으면 소리도 같다');

H.done();
