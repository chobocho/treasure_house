// sha1 의 시험 — SPEC.md §2 · 부록 A 1단계.
//
// 기준은 golden/sha1.tsv 100줄이다. sha1 칸은 coreutils sha1sum 이,
// blob 칸은 진짜 git hash-object 가 낸 값이다. node 의 crypto 는 답을
// 맞춰 보는 두 번째 증인으로만 쓴다 — 구현이 그것을 부르면 이 시험은
// 아무것도 증명하지 않는다(SPEC.md §2 첫 문단).
import * as assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { describe, test } from 'node:test';
import { Sha1, sha1, sha1Hex } from '../src/sha1';
import * as golden from './golden';

const VECTORS = golden.tsv('sha1.tsv');
const witness = (d: Uint8Array) =>
  createHash('sha1').update(d).digest();

describe('vectors', () => {
  test('s2 hundred vectors match sha1sum', () => {
    assert.equal(VECTORS.length, 100);
    for (const row of VECTORS) {
      const data = golden.make(row.recipe);
      assert.equal(data.length, Number(row.len), row.name);
      assert.equal(sha1Hex(data), row.sha1, row.name);
    }
  });

  test('s2 raw digest is twenty bytes', () => {
    const d = sha1(Buffer.from('abc'));
    assert.equal(d.length, 20);
    assert.deepEqual(d, witness(Buffer.from('abc')));
  });

  test('s2 padding boundaries agree with crypto', () => {
    // 55 바이트까지는 덧붙임이 한 블록에 들어가고 56 부터 넘친다.
    for (let n = 0; n < 200; n++) {
      const data = Buffer.from(
        Array.from({ length: n }, (_, i) => (i * 7) % 256));
      assert.deepEqual(sha1(data), witness(data), String(n));
    }
  });
});

describe('streaming', () => {
  test('s2 update in odd chunks equals one shot', () => {
    const data = golden.make('counter:100000');
    for (const size of [1, 3, 63, 64, 65, 1000, 99999]) {
      const h = new Sha1();
      for (let k = 0; k < data.length; k += size) {
        h.update(data.subarray(k, k + size));
      }
      assert.deepEqual(h.digest(), sha1(data), String(size));
    }
  });

  test('s2 digest twice is stable', () => {
    const h = new Sha1().update(Buffer.from('git'));
    assert.deepEqual(h.digest(), h.digest());
  });
});

describe('blob column', () => {
  test('s2 header plus body is the blob name', () => {
    // blob 이름 = SHA-1("blob <크기>\0" + 몸) — 머리를 붙이는 일은
    // §4 의 몫이지만, 여기서 숫자가 맞으면 SHA-1 쪽은 끝난 것이다.
    for (const row of VECTORS) {
      const data = golden.make(row.recipe);
      const head = Buffer.from(`blob ${data.length}\0`);
      assert.equal(sha1Hex(Buffer.concat([head, data])), row.blob,
        row.name);
    }
  });
});
