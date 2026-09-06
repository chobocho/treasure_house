// PC 스피커 — 분주값·음표표·사각파 (SPEC §21).
//
//    PIT 은 사각파만 낼 수 있었다. 음량 조절이 없었고 듀티비도 고정이라,
//    도스 게임의 스피커 음악은 전부 같은 음색이다. 여기서 하는 일은 그 제약을
//    그대로 흉내내는 것뿐이다. 소리를 재생하지 않는다 — 헤드리스 환경이고,
//    바이트가 같으면 소리도 같다.

import * as C from './const';
import * as F from './fixed';

export const SAMPLE_RATE = 22050;
export const AMP_LO = 0x40;
export const AMP_HI = 0xC0;
export const AMP_MID = 0x80;

// §21.2 A4 = 440 Hz 12평균율을 **정수 Hz 로 반올림해 박아 둔다.**
// 세 언어가 같은 표를 갖는 것이 실수 연산을 맞추는 것보다 싸고 확실하다.
export const NOTE_NAME = ['C4', 'C#4', 'D4', 'D#4', 'E4', 'F4', 'F#4', 'G4',
                          'G#4', 'A4', 'A#4', 'B4', 'C5', 'C#5', 'D5', 'D#5',
                          'E5', 'F5', 'F#5', 'G5', 'G#5', 'A5', 'A#5', 'B5'];
export const NOTE_HZ = [262, 277, 294, 311, 330, 349, 370, 392, 415, 440,
                        466, 494, 523, 554, 587, 622, 659, 698, 740, 784,
                        831, 880, 932, 988];

// ── SPEC §21.1 분주값 ───────────────────────────────────────────────────────
// 반올림 나눗셈. PIT_HZ 자체가 반올림값이라는 것을 22부가 따로 따진다.
export function divisor(f: number): number {
  if (f <= 0) return 0;
  const d = F.floordiv(C.PIT_HZ + F.floordiv(f, 2), f);
  return d < 1 ? 1 : d;
}

// 실제로 나는 주파수를 **정수 나눗셈의 몫과 나머지**로 낸다.
// 센트 오차는 로그가 필요하므로 엔진이 아니라 tools/gen_prim.py 가 낸다.
export function actual(f: number): [number, number] {
  const d = divisor(f);
  if (d === 0) return [0, 0];
  return [F.floordiv(C.PIT_HZ, d), F.fmod(C.PIT_HZ, d)];
}

export function actual100(f: number): number {
  const d = divisor(f);
  return d === 0 ? 0 : F.floordiv(C.PIT_HZ * 100, d);
}

// ── SPEC §21.3 사각파 합성 ──────────────────────────────────────────────────
export function halfPeriod(f: number): number {
  const q = actual(f)[0];
  if (q <= 0) return 0;
  return F.floordiv(SAMPLE_RATE, 2 * q);
}

// 8비트 부호 없는 모노 PCM n 샘플. f <= 0 이면 무음(쉼표).
export function square(f: number, n: number): number[] {
  if (n <= 0) return [];
  if (f <= 0) return new Array<number>(n).fill(AMP_MID);
  const half = halfPeriod(f);
  if (half <= 0) return new Array<number>(n).fill(AMP_MID);
  const out: number[] = [];
  for (let k = 0; k < n; k += 1) {
    out.push(F.fmod(F.floordiv(k, half), 2) === 0 ? AMP_LO : AMP_HI);
  }
  return out;
}

function le(out: number[], v0: number, n: number): void {
  let v = v0;
  for (let k = 0; k < n; k += 1) {
    out.push(F.fmod(v, 256));
    v = F.floordiv(v, 256);
  }
}

// 44바이트 헤더 + PCM. 전체 바이트의 FNV-1a 를 골든으로 둔다.
export function wav(pcm: ArrayLike<number>): number[] {
  const out: number[] = [];
  const push = (s: string): void => {
    for (const ch of s) out.push(ch.charCodeAt(0));
  };
  push('RIFF');
  le(out, 36 + pcm.length, 4);
  push('WAVE');
  push('fmt ');
  le(out, 16, 4);                    // fmt 청크 길이
  le(out, 1, 2);                     // PCM
  le(out, 1, 2);                     // 모노
  le(out, SAMPLE_RATE, 4);
  le(out, SAMPLE_RATE, 4);           // 바이트/초 = 레이트 × 1채널 × 1바이트
  le(out, 1, 2);                     // 블록 정렬
  le(out, 8, 2);                     // 비트/샘플
  push('data');
  le(out, pcm.length, 4);
  for (let i = 0; i < pcm.length; i += 1) out.push(pcm[i]);
  return out;
}

// (주파수, 샘플 수) 목록을 이어 붙여 WAV 로.
export function tune(notes: Array<[number, number]>): number[] {
  const pcm: number[] = [];
  for (const [f, n] of notes) {
    for (const v of square(f, n)) pcm.push(v);
  }
  return wav(pcm);
}
