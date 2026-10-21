import { test } from 'node:test';
import assert from 'node:assert/strict';
import { extractRegion, renderSnippet } from './snippets.mjs';

test('중첩 영역은 선택한 범위만 추출하고 표식을 제거한다', () => {
  const source = '// #region outer\n  alpha\n  // #region inner\n  beta\n  // #endregion\n  gamma  \n// #endregion\n';
  assert.equal(extractRegion(source, 'outer'), 'alpha\nbeta\ngamma');
  assert.equal(extractRegion(source, 'inner'), 'beta');
});

test('누락·중복·닫히지 않은 영역을 거부한다', () => {
  assert.throws(() => extractRegion('hello', 'x'), /영역을 찾을 수 없다/);
  assert.throws(() => extractRegion('# region x\na\n# endregion\n# region x\nb\n# endregion', 'x'), /중복/);
  assert.throws(() => extractRegion('# region x\na', 'x'), /닫히지/);
});

test('코드는 HTML 이스케이프하고 30줄 상한을 적용한다', () => {
  assert.equal(renderSnippet('<span>&"'), '&lt;span&gt;&amp;"');
  assert.throws(() => renderSnippet(Array(31).fill('x').join('\n')), /30줄/);
});
