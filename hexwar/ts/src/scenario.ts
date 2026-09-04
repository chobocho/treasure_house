// 시나리오 로더 — golden/scenario.txt

import * as fs from 'fs';
import * as path from 'path';

import * as H from './hexcoord';
import { CHAR_TO_TERRAIN, HexMap, MAP_H, MAP_W } from './hexmap';
import { UnitPool } from './units';

export function goldenDir(): string {
  return process.env['HEXWAR_GOLDEN'] ?? path.join(__dirname, '..', '..', '..', 'golden');
}

export function parse(text: string): Map<string, string[]> {
  const blocks = new Map<string, string[]>();
  let cur: string | null = null;
  for (const raw of text.split('\n')) {
    const line = raw.replace(/\r$/, '');
    if (line === '' || line.startsWith(';')) continue;
    if (line.startsWith('[') && line.endsWith(']')) {
      cur = line.slice(1, -1);
      blocks.set(cur, []);
      continue;
    }
    if (cur === null) throw new Error(`블록 밖의 줄: ${line}`);
    blocks.get(cur)!.push(line);
  }
  return blocks;
}

export interface Scenario {
  map: HexMap;
  pool: UnitPool;
  objectives: Array<[number, number]>;
}

export function load(file?: string): Scenario {
  const p = file ?? path.join(goldenDir(), 'scenario.txt');
  const blocks = parse(fs.readFileSync(p, 'utf8'));
  const terr = blocks.get('terrain')!;
  const elev = blocks.get('elev')!;
  const road = blocks.get('road')!;
  if (terr.length !== MAP_H || elev.length !== MAP_H || road.length !== MAP_H) {
    throw new Error(`맵 높이가 ${MAP_H} 이 아니다`);
  }

  const m = new HexMap();
  for (let row = 0; row < MAP_H; row++) {
    const tl = terr[row]!, el = elev[row]!, rl = road[row]!;
    if (tl.length !== MAP_W || el.length !== MAP_W || rl.length !== MAP_W) {
      throw new Error(`${row}행의 너비가 ${MAP_W} 이 아니다`);
    }
    for (let col = 0; col < MAP_W; col++) {
      const t = CHAR_TO_TERRAIN.get(tl[col]!)!;
      m.setCell(col, row, t, Number(el[col]!), rl[col] === 'R' ? 1 : 0);
    }
  }

  const pool = new UnitPool();
  for (const line of blocks.get('units')!) {
    const [side, kind, col, row] = line.split(/\s+/).map(Number) as [number, number, number, number];
    const [q, r] = H.oddrToAxial(col, row);
    const uid = pool.spawn(side, kind, q, r);
    m.occupant[m.idx(col, row)] = uid;
  }

  const objectives: Array<[number, number]> = [];
  for (const line of blocks.get('objectives')!) {
    const [col, row] = line.split(/\s+/).map(Number) as [number, number];
    objectives.push(H.oddrToAxial(col, row));
  }
  return { map: m, pool, objectives };
}
