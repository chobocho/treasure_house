// 골든 트레이스 대조 (타입스크립트) — 파이썬이 얼려 둔 파일과 한 바이트라도 다르면 실패.

import * as fs from 'fs';
import * as path from 'path';

import { runTrace } from '../src/main';

const GOLDEN = process.env['HEXWAR_GOLDEN'] ?? path.join(__dirname, '..', '..', '..', 'golden');
const want = fs.readFileSync(path.join(GOLDEN, 'trace.jsonl'), 'utf8')
  .split('\n').filter((s) => s !== '');
const got = runTrace(true).split('\n').filter((s) => s !== '');

if (got.length !== want.length) {
  console.log(`스텝 수 불일치: ${got.length} != ${want.length}`);
  process.exit(1);
}
let bad = 0;
for (let i = 0; i < want.length; i++) {
  if (got[i] !== want[i]) {
    if (bad < 5) console.log(`스텝 ${i} 불일치\n  got  ${got[i]}\n  want ${want[i]}`);
    bad++;
  }
}
if (bad > 0) {
  console.log(`FAIL — ${bad}스텝 불일치`);
  process.exit(1);
}
const frames = want.filter((l) => l.includes('fbHash')).length;
console.log(`trace OK (ts) — ${want.length}스텝 · 프레임 해시 ${frames}개 일치`);
