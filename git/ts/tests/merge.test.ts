// 3-way 파일 합치기의 시험 — SPEC.md §12.3, 10단계.
//
// 큰 오라클은 golden/scen/merge-*.scn 14장면(진짜 git merge 의 작업
// 트리 파일·인덱스·MERGE_MSG·머지 커밋 이름)이다. 여기서는 merge3
// 하나를 따로 부른다 — 장면의 세 판을 그대로 넣고, 장면에서 git 이
// 남긴 파일 내용과 같은지 본다. 규칙마다 한 장면이 증거다.
import * as assert from 'node:assert/strict';
import { describe, test } from 'node:test';
import * as merge from '../src/merge';
import * as golden from './golden';

function mergeCase(base: string, ours: string, theirs: string):
  [string, number] {
  const [text, n] = merge.merge3(golden.make(base), golden.make(ours),
    golden.make(theirs), 't');
  return [text.toString(), n];
}

describe('merge3', () => {
  test('s12_3 adjacent lines conflict', () => {
    // merge-adjacent.scn — 둘째 줄과 셋째 줄을 따로 고쳐도 충돌
    assert.deepEqual(mergeCase('text:a\\nb\\nc\\nd\\n',
      'text:a\\nB\\nc\\nd\\n', 'text:a\\nb\\nC\\nd\\n'),
    ['a\n<<<<<<< HEAD\nB\nc\n=======\nb\nC\n>>>>>>> t\nd\n', 1]);
  });

  test('s12_3 one line apart is clean', () => {
    assert.deepEqual(mergeCase('text:a\\nb\\nc\\nd\\ne\\n',
      'text:a\\nB\\nc\\nd\\ne\\n', 'text:a\\nb\\nc\\nD\\ne\\n'),
    ['a\nB\nc\nD\ne\n', 0]);
  });

  test('s12_3 refine keeps common lines outside', () => {
    const [text] = mergeCase('text:a\\nb\\nz\\n',
      'text:a\\nq\\nw\\ne\\nz\\n', 'text:a\\nq\\nr\\ne\\nz\\n');
    assert.equal(text,
      'a\nq\n<<<<<<< HEAD\nw\n=======\nr\n>>>>>>> t\ne\nz\n');
  });

  test('s12_3 three lines apart join four split', () => {
    let [, n] = mergeCase('text:a\\nb\\nm1\\nm2\\nm3\\nd\\ne\\n',
      'text:a\\n1\\nm1\\nm2\\nm3\\n2\\ne\\n',
      'text:a\\n3\\nm1\\nm2\\nm3\\n4\\ne\\n');
    assert.equal(n, 1);
    [, n] = mergeCase('text:a\\nb\\nm1\\nm2\\nm3\\nm4\\nd\\ne\\n',
      'text:a\\n1\\nm1\\nm2\\nm3\\nm4\\n2\\ne\\n',
      'text:a\\n3\\nm1\\nm2\\nm3\\nm4\\n4\\ne\\n');
    assert.equal(n, 2);
  });

  test('s12_3 identical change taken once', () => {
    assert.deepEqual(mergeCase('seq:1:5', 'text:1\\nX\\n3\\n4\\n5\\n',
      'text:1\\nX\\n3\\n4\\nY\\n'), ['1\nX\n3\n4\nY\n', 0]);
  });
});
