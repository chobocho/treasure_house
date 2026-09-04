// 골든 프리미티브 대조 (타입스크립트) — 파이썬·루아판과 같은 파일, 같은 순서.

import * as fs from 'fs';
import * as path from 'path';

import * as H from '../src/hexcoord';
import * as M from '../src/hexmap';
import * as PK from '../src/picker';
import { Rng, fnv1a } from '../src/rng';

const GOLDEN = process.env['HEXWAR_GOLDEN'] ?? path.join(__dirname, '..', '..', '..', 'golden');
const fails: string[] = [];

function eq(name: string, got: unknown, want: unknown): void {
  if (got !== want) fails.push(`${name}: got ${String(got)} want ${String(want)}`);
}

function eqList(name: string, got: number[], want: number[], from = 0, n?: number): void {
  const count = n ?? want.length - from;
  if (got.length !== count) {
    fails.push(`${name}: 길이 ${got.length} != ${count}`);
    return;
  }
  for (let i = 0; i < got.length; i++) {
    if (got[i] !== want[from + i]) {
      fails.push(`${name}: [${i}] ${got[i]} != ${want[from + i]}`);
      return;
    }
  }
}

function unhex(s: string): Uint8Array {
  if (s === '-') return new Uint8Array(0);
  const out = new Uint8Array(s.length / 2);
  for (let i = 0; i < out.length; i++) out[i] = parseInt(s.slice(i * 2, i * 2 + 2), 16);
  return out;
}

let nline = 0;
for (const raw of fs.readFileSync(path.join(GOLDEN, 'prim.txt'), 'utf8').split('\n')) {
  const line = raw.trim();
  if (!line || line.startsWith(';')) continue;
  nline++;
  const parts = line.split(/\s+/);
  const key = parts[0]!;
  if (key === 'fnv') {
    eq(`fnv ${parts[1]}`, fnv1a(unhex(parts[1]!)), Number(parts[2]));
    continue;
  }
  const v = parts.slice(1).map(Number);
  switch (key) {
    case 'dirs':
      eqList('dirs', H.DIRS.flatMap((d) => [d[0], d[1]]), v);
      break;
    case 'oddr':
      eqList('axialToOddr', [...H.axialToOddr(v[0]!, v[1]!)], v, 2);
      eqList('oddrToAxial', [...H.oddrToAxial(v[2]!, v[3]!)], v, 0, 2);
      break;
    case 'oddq':
      eqList('axialToOddq', [...H.axialToOddq(v[0]!, v[1]!)], v, 2);
      eqList('oddqToAxial', [...H.oddqToAxial(v[2]!, v[3]!)], v, 0, 2);
      break;
    case 'dist':
      eq('distance', H.distance(v[0]!, v[1]!, v[2]!, v[3]!), v[4]);
      break;
    case 'neighbors':
      eqList('neighbors', H.neighbors(v[0]!, v[1]!).flatMap((h) => [h[0], h[1]]), v, 2);
      break;
    case 'ring':
      eqList(`ring${v[0]}`, H.ring(0, 0, v[0]!).flatMap((h) => [h[0], h[1]]), v, 1);
      break;
    case 'spiral':
      eq(`spiral${v[0]}`, H.spiral(0, 0, v[0]!).length, v[1]);
      break;
    case 'line': {
      const hexes = H.line(v[0]!, v[1]!, v[2]!, v[3]!);
      eqList('line', [hexes.length, ...hexes.flatMap((h) => [h[0], h[1]])], v, 4);
      break;
    }
    case 'pick': {
      const p = PK.pick(v[0]!, v[1]!, v[2]!, v[3]!);
      eqList('pick', p ? [p[0], p[1]] : [-1, -1], v, 4);
      break;
    }
    case 'lcg': {
      const st = new Rng(v[0]!);
      eqList('lcg', v.slice(1).map(() => st.next()), v, 1);
      break;
    }
    case 'd6': {
      const st = new Rng(0x1badb002);
      eqList('d6', v.map(() => st.d6()), v);
      break;
    }
    case 'cell':
      eq('pack', M.packCell(v[0]!, v[1]!, v[2]!), v[3]);
      eqList('unpack', [M.cellTerrain(v[3]!), M.cellElev(v[3]!), M.cellRoad(v[3]!)], v, 0, 3);
      break;
    default:
      fails.push(`알 수 없는 키: ${key}`);
  }
}

// 마스크 표가 golden/pick_mask.txt 와 같은지도 본다
{
  const lines = fs.readFileSync(path.join(GOLDEN, 'pick_mask.txt'), 'utf8')
    .split('\n').filter((s) => s !== '');
  eq('mask 행 수', lines.length, 24);
  for (let oy = 0; oy < lines.length; oy++) {
    for (let ox = 0; ox < 32; ox++) {
      eq(`mask[${oy}][${ox}]`, PK.PICK_MASK[oy * 32 + ox], Number(lines[oy]![ox]));
    }
  }
}

if (fails.length > 0) {
  console.log(`FAIL ${fails.length} / ${nline}줄`);
  for (const f of fails.slice(0, 20)) console.log('  ' + f);
  process.exit(1);
}
console.log(`prim OK (ts) — ${nline}줄 + 마스크 768칸 전부 일치`);
