// make test-ts 는 `node --test build/ts/tests/` 를 부른다. node 22
// 부터 --test 의 인자는 파일 패턴이라, 디렉터리를 주면 그 디렉터리를
// 모듈로 연다 — 곧 이 index.js 다. 그래서 여기서 *.test.js 를 전부
// 불러 한 과정 안에서 돌린다(이 기계는 메모리가 빠듯하기도 하다).
import * as fs from 'node:fs';

for (const f of fs.readdirSync(__dirname).sort()) {
  if (f.endsWith('.test.js')) require(`./${f}`);
}
