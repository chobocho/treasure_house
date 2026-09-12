// PPM — 부분 일치 예측 — SPEC §17.
//
// 앞 두 바이트로 다음 바이트를 찍는다. 틀리면 "틀렸다"(탈출) 고 말하고
// 앞 한 바이트로, 또 틀리면 맨손으로 찍는다. 탈출값은 방법 C 다
// — 문맥에서 본 서로 다른 기호의 수가 곧 탈출의 빈도다.
//
// **모든 기호가 배제된 문맥은 건너뛴다.** 탈출이 확실해 비트가 0이다.
// 이걸 잊으면 부호기만 탈출을 적어 거기서 어긋난다 — 고전 버그다.
import { ByteBuf, Bytes, concat, fail } from './common';
import { Decoder, Encoder } from './rangecoder';
import * as varint from './varint';

export const MAX_ORDER = 2;
export const ALPHABET = 256;
// 문맥의 합계가 이 값에 닿으면 모든 셈을 반으로 줄인다.
export const MAX_TOTAL = 8192;

// 문맥 열쇠는 문자열이다 — 길이를 앞에 붙여 ()·(a)·(a,b) 를 가른다.
type Table = Map<number, number>;
type Model = Map<string, Table>;

export function contextKeys(history: number[]): string[] {
  const keys: string[] = [];
  for (let order = MAX_ORDER; order >= 0; order--) {
    if (order > history.length) continue;
    let key = String(order);
    for (let i = history.length - order; i < history.length; i++) {
      key += ',' + history[i];
    }
    keys.push(key);
  }
  return keys;
}

function update(model: Model, key: string, sym: number): void {
  let table = model.get(key);
  if (table === undefined) {
    table = new Map<number, number>();
    model.set(key, table);
  }
  table.set(sym, (table.get(sym) ?? 0) + 1);
  let total = 0;
  for (const v of table.values()) total += v;
  if (total >= MAX_TOTAL) {
    for (const [s, v] of table) table.set(s, Math.max(1, v >> 1));
  }
}

// 배제되지 않은 기호를 번호 오름차순으로. 누적합의 순서가 곧 이것이다.
function visible(table: Table, excluded: boolean[]): number[] {
  const syms: number[] = [];
  for (const s of table.keys()) {
    if (!excluded[s]) syms.push(s);
  }
  syms.sort((a, b) => a - b);
  return syms;
}

function pushHistory(history: number[], b: number): void {
  history.push(b);
  if (history.length > MAX_ORDER) history.shift();
}

export function encode(src: Bytes): Bytes {
  if (src.length === 0) return varint.put(0);
  const enc = new Encoder();
  const model: Model = new Map();
  const history: number[] = [];
  for (const b of src) {
    const excluded = new Array<boolean>(ALPHABET).fill(false);
    let coded = false;
    for (const key of contextKeys(history)) {
      const table = model.get(key);
      if (table === undefined) continue;
      const syms = visible(table, excluded);
      // 모두 배제 — 아무것도 안 적는다
      if (syms.length === 0) continue;
      const esc = syms.length;
      let tot = esc;
      for (const s of syms) tot += table.get(s) as number;
      if (!excluded[b] && table.has(b)) {
        let cum = 0;
        for (const s of syms) {
          if (s === b) break;
          cum += table.get(s) as number;
        }
        enc.encodeFreq(cum, table.get(b) as number, tot);
        coded = true;
        break;
      }
      enc.encodeFreq(tot - esc, esc, tot);
      for (const s of syms) excluded[s] = true;
    }
    if (!coded) {
      // -1차 — 남은 기호에 균등하게 (§17.4)
      let rest = 0;
      let index = 0;
      for (let s = 0; s < ALPHABET; s++) {
        if (excluded[s]) continue;
        if (s < b) index++;
        rest++;
      }
      enc.encodeFreq(index, 1, rest);
    }
    for (const key of contextKeys(history)) update(model, key, b);
    pushHistory(history, b);
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
  const model: Model = new Map();
  const history: number[] = [];
  const out = new ByteBuf();
  for (let k = 0; k < n; k++) {
    const excluded = new Array<boolean>(ALPHABET).fill(false);
    let found = -1;
    for (const key of contextKeys(history)) {
      const table = model.get(key);
      if (table === undefined) continue;
      const syms = visible(table, excluded);
      if (syms.length === 0) continue;
      const esc = syms.length;
      let tot = esc;
      for (const s of syms) tot += table.get(s) as number;
      const v = dec.decodeFreq(tot);
      let cum = 0;
      let hit = -1;
      for (const s of syms) {
        const c = table.get(s) as number;
        if (v >= cum && v < cum + c) {
          hit = s;
          break;
        }
        cum += c;
      }
      if (hit >= 0) {
        dec.decodeUpdate(cum, table.get(hit) as number, tot);
        found = hit;
        break;
      }
      dec.decodeUpdate(tot - esc, esc, tot);
      for (const s of syms) excluded[s] = true;
    }
    if (found < 0) {
      const rest: number[] = [];
      for (let s = 0; s < ALPHABET; s++) {
        if (!excluded[s]) rest.push(s);
      }
      const v = dec.decodeFreq(rest.length);
      found = rest[v];
      dec.decodeUpdate(v, 1, rest.length);
    }
    out.push(found);
    for (const key of contextKeys(history)) update(model, key, found);
    pushHistory(history, found);
  }
  return out.bytes();
}
