// 문맥 혼합 — SPEC §18.
//
// 여기까지의 모든 코덱은 모델을 **하나** 골랐다. 문맥 혼합은 고르지
// 않는다 — 여러 모델에게 묻고 **의견을 섞으며** 누구를 믿을지 배운다.
//
// 섞는 자리가 요점이다. 확률을 그냥 평균 내면 0.01 과 0.99 가 0.5 가
// 되어 두 모델의 확신이 사라진다. **로지스틱 영역** 에서 더해야 한다.
import { ByteBuf, Bytes, concat, fail } from './common';
import { Decoder, Encoder } from './rangecoder';
import * as varint from './varint';

export const TABLE_BITS = 20;
export const TABLE_SIZE = 1 << TABLE_BITS;
export const NUM_MODELS = 5;
export const PROB_ONE = 4096;
export const PROB_HALF = PROB_ONE / 2;
// 셈이 쌓일수록 천천히 움직인다. 처음 보는 문맥은 빨리 배우고 오래 본
// 문맥은 흔들리지 않아야 한다 — 고정 비율 하나로는 둘 다 못 한다.
export const COUNTER_RATES =
  [1, 1, 2, 2, 3, 3, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5];
export const COUNTER_LIMIT = 15;
export const MIXER_SHIFT = 16;
export const MIXER_INIT = 1 << 14;
// 믹서 갱신의 시프트. lpaq 과 같은 16이다. 10 으로 두면 가중치가 한
// 걸음에 5만씩 튀어 모델이 수렴하지 못한다.
export const MIXER_UPDATE_SHIFT = 16;
export const MIXER_LEARN = 16;
export const MIXER_CLAMP = 1 << 20;
export const APM_RATE = 7;
export const APM1_CONTEXTS = 256;
export const APM2_CONTEXTS = 1 << 16;
const HASH_A = 0x9e3779b1;
const HASH_B = 0x85ebca6b;

// SQUASH-TABLE-BEGIN — gen_tables.py 가 다섯을 대조한다 (§18.6)
export const SQUASH_TABLE = [
  1, 2, 3, 6, 10, 16, 27, 45, 73, 120, 194, 310, 488, 747, 1101,
  1546, 2047, 2549, 2994, 3348, 3607, 3785, 3901, 3975, 4024,
  4050, 4068, 4079, 4085, 4089, 4092, 4093, 4094];
// SQUASH-TABLE-END

// 로지스틱: -2047..2047 → 0..4095. 표 사이를 직선으로 잇는다.
export function squash(d: number): number {
  if (d > 2047) return 4095;
  if (d < -2047) return 0;
  const w = d & 127;
  const i = (d >> 7) + 16;
  return (SQUASH_TABLE[i] * (128 - w)
    + SQUASH_TABLE[i + 1] * w + 64) >> 7;
}

// squash 의 역. 표를 뒤집어 만든다 — 따로 적을 값이 아니다.
const STRETCH_TABLE = (() => {
  const table = new Int16Array(PROB_ONE);
  let pi = 0;
  for (let x = -2047; x <= 2047; x++) {
    const v = squash(x);
    for (let p = pi; p <= v; p++) table[p] = x;
    pi = v + 1;
  }
  for (let p = pi; p < PROB_ONE; p++) table[p] = 2047;
  return table;
})();

export function stretch(p: number): number {
  return STRETCH_TABLE[p];
}

function hashCtx(ctx: number, c0: number): number {
  // 곱이 2^53 을 넘으므로 Math.imul 이어야 한다 (SPEC §0.5).
  const h = (Math.imul(ctx, HASH_A) ^ Math.imul(c0, HASH_B)) >>> 0;
  return h >>> (32 - TABLE_BITS);
}

// 적응 확률 지도 — 믹서의 답을 문맥에 맞춰 한 번 더 고친다 (§18.5).
export class Apm {
  private t: Int32Array;
  private index = 0;

  constructor(contexts: number) {
    this.t = new Int32Array(contexts * 33);
    for (let i = 0; i < this.t.length; i++) {
      this.t[i] = squash(((i % 33) - 16) * 128) * 16;
    }
  }

  pp(pr: number, cx: number): number {
    // 곱수는 32 다. 표가 33칸이라 0..4095 를 0..32 로 펴야 끝까지
    // 쓴다. lpaq1 의 23 이면 위쪽 아홉 칸이 죽어 확률이 잘린다.
    const s = (stretch(pr) + 2048) * 32;
    const wt = s & 0xfff;
    const j = cx * 33 + (s >> 12);
    this.index = j + (wt >> 11);
    return (this.t[j] * (4096 - wt) + this.t[j + 1] * wt) >> 16;
  }

  update(bit: number): void {
    const g = (bit << 16) + (bit << APM_RATE) - bit - bit;
    this.t[this.index] += (g - this.t[this.index]) >> APM_RATE;
  }
}

// 문맥 모델 다섯 + 믹서 + APM 둘. 부호기와 복호기가 똑같이 쓴다.
export class Model {
  private order0 = new Uint16Array(256).fill(PROB_HALF);
  private order0n = new Uint8Array(256);
  private tables: Uint16Array[] = [];
  private counts: Uint8Array[] = [];
  private weights = new Int32Array(256 * NUM_MODELS).fill(MIXER_INIT);
  private apm1 = new Apm(APM1_CONTEXTS);
  private apm2 = new Apm(APM2_CONTEXTS);
  private history = 0;
  private c0 = 1;
  private slots = new Int32Array(NUM_MODELS);
  private st = new Int32Array(NUM_MODELS);
  private pMix = PROB_HALF;

  constructor() {
    for (let k = 0; k < 4; k++) {
      this.tables.push(new Uint16Array(TABLE_SIZE).fill(PROB_HALF));
      this.counts.push(new Uint8Array(TABLE_SIZE));
    }
  }

  predict(): number {
    const c0 = this.c0;
    const h = this.history;
    this.slots[0] = c0 & 0xff;
    for (let k = 0; k < 4; k++) {
      const mask = k < 3 ? (1 << (8 * (k + 1))) - 1 : 0xffffffff;
      const ctx = (h & mask) >>> 0;
      const salt = ((k + 1) * 0x01000193) >>> 0;
      this.slots[k + 1] = hashCtx((ctx + salt) >>> 0, c0);
    }
    const probs = new Int32Array(NUM_MODELS);
    probs[0] = this.order0[this.slots[0]];
    for (let k = 0; k < 4; k++) {
      probs[k + 1] = this.tables[k][this.slots[k + 1]];
    }
    const wbase = (c0 & 0xff) * NUM_MODELS;
    let dot = 0;
    for (let i = 0; i < NUM_MODELS; i++) {
      this.st[i] = stretch(probs[i]);
      dot += this.weights[wbase + i] * this.st[i];
    }
    dot = Math.floor(dot / 2 ** MIXER_SHIFT);
    if (dot > 2047) dot = 2047;
    if (dot < -2047) dot = -2047;
    this.pMix = squash(dot);
    let p = (this.pMix + 3 * this.apm1.pp(this.pMix, c0 & 0xff)) >> 2;
    const cx2 = ((c0 & 0xff) << 8) | (h & 0xff);
    p = (p + 3 * this.apm2.pp(p, cx2)) >> 2;
    if (p < 1) p = 1;
    if (p > 4094) p = 4094;
    return p;
  }

  update(bit: number): void {
    const target = bit << 12;
    const i0 = this.slots[0];
    this.order0[i0] +=
      (target - this.order0[i0]) >> COUNTER_RATES[this.order0n[i0]];
    if (this.order0n[i0] < COUNTER_LIMIT) this.order0n[i0] += 1;
    for (let k = 0; k < 4; k++) {
      const i = this.slots[k + 1];
      const t = this.tables[k];
      const c = this.counts[k];
      t[i] += (target - t[i]) >> COUNTER_RATES[c[i]];
      if (c[i] < COUNTER_LIMIT) c[i] += 1;
    }
    const err = (target - this.pMix) * MIXER_LEARN;
    const wbase = (this.c0 & 0xff) * NUM_MODELS;
    for (let i = 0; i < NUM_MODELS; i++) {
      let v = this.weights[wbase + i] +
        ((this.st[i] * err) >> MIXER_UPDATE_SHIFT);
      if (v > MIXER_CLAMP) v = MIXER_CLAMP;
      if (v < -MIXER_CLAMP) v = -MIXER_CLAMP;
      this.weights[wbase + i] = v;
    }
    this.apm1.update(bit);
    this.apm2.update(bit);
    this.c0 = (this.c0 << 1) | bit;
    if (this.c0 >= 256) {
      this.history = (((this.history << 8) | (this.c0 & 0xff)) >>> 0);
      this.c0 = 1;
    }
  }
}

export function encode(src: Bytes): Bytes {
  if (src.length === 0) return varint.put(0);
  const enc = new Encoder();
  const model = new Model();
  for (const b of src) {
    for (let i = 7; i >= 0; i--) {
      const bit = (b >> i) & 1;
      const p = model.predict();
      // 코더는 P(0) 을 받는다. 모델은 P(1) 을 내므로 뒤집는다.
      enc.encodeBitP0(PROB_ONE - p, bit);
      model.update(bit);
    }
  }
  enc.flush();
  return concat([varint.put(src.length), enc.bytes()]);
}

export function decode(src: Bytes): Bytes {
  const [n, pos] = varint.getLength(src, 0);
  if (n === 0) {
    if (pos !== src.length) fail('빈 입력인데 뒤에 바이트가 있다');
    return new Uint8Array(0);
  }
  const dec = new Decoder(src, pos);
  const model = new Model();
  const out = new ByteBuf();
  for (let k = 0; k < n; k++) {
    let byte = 0;
    for (let i = 0; i < 8; i++) {
      const p = model.predict();
      const bit = dec.decodeBitP0(PROB_ONE - p);
      model.update(bit);
      byte = (byte << 1) | bit;
    }
    out.push(byte);
  }
  return out.bytes();
}
