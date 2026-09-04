// 명령줄 진입점 — 파이썬·루아판과 같은 하위 명령.
//
//   node dist/src/main.js trace
//   node dist/src/main.js render out.ppm [스텝]
//   node dist/src/main.js bench

import * as fs from 'fs';
import * as path from 'path';

import * as ai from './ai';
import { Game } from './game';
import { Renderer } from './render';
import { fnv1a, fnv1aStr, hex8 } from './rng';
import { goldenDir, load } from './scenario';
import { Ui } from './ui';

export function loadScript(p?: string): string[] {
  const file = p ?? path.join(goldenDir(), 'script.txt');
  return fs.readFileSync(file, 'utf8').split('\n')
    .map((s) => s.trim())
    .filter((s) => s !== '' && !s.startsWith(';'));
}

export interface Digest {
  ev: string; fbHash?: string; fogHash: string; rng: number; sel: number;
  side: number; state: string; step: number; turn: number; ui: string; unitHash: string;
}

export function digestState(g: Game, ui: Ui, r: Renderer | null,
                            withFrame: boolean): Omit<Digest, 'ev' | 'step'> {
  const d: Omit<Digest, 'ev' | 'step'> = {
    fogHash: hex8(fnv1aStr(g.map.fogText())),
    rng: g.rng.save(),
    sel: ui.selUnit,
    side: g.side,
    state: ui.stateName(),
    turn: g.turn,
    ui: ui.digest(),
    unitHash: hex8(fnv1aStr(g.serializeUnits())),
  };
  if (withFrame && r) {
    r.draw(g, ui);
    (d as Digest).fbHash = hex8(fnv1a(r.fb.toPpm(r.pal)));
  }
  return d;
}

// 파이썬의 json.dumps(sort_keys=True, separators=(',',':')) 와 바이트 단위로
// 같아야 하므로 키 순서를 사전순으로 고정해 직접 찍는다.
// JSON.stringify 는 객체의 삽입 순서를 따르므로 여기서는 쓸 수 없다.
function jsonLine(d: Digest): string {
  const parts: string[] = [`"ev":${JSON.stringify(d.ev)}`];
  if (d.fbHash !== undefined) parts.push(`"fbHash":"${d.fbHash}"`);
  parts.push(`"fogHash":"${d.fogHash}"`);
  parts.push(`"rng":${d.rng}`);
  parts.push(`"sel":${d.sel}`);
  parts.push(`"side":${d.side}`);
  parts.push(`"state":"${d.state}"`);
  parts.push(`"step":${d.step}`);
  parts.push(`"turn":${d.turn}`);
  parts.push(`"ui":"${d.ui}"`);
  parts.push(`"unitHash":"${d.unitHash}"`);
  return `{${parts.join(',')}}`;
}

export function runTrace(renderFrames = true): string {
  const sc = load();
  const g = new Game(sc.map, sc.pool, sc.objectives);
  const ui = new Ui(g);
  const r = renderFrames ? new Renderer() : null;
  const out: string[] = [];
  const evs = loadScript();
  for (let n = 0; n < evs.length; n++) {
    const ev = evs[n]!;
    if (ev === 'ai') {
      ai.takeTurn(g);
      g.endTurn();
      ui.afterTurn();
    } else {
      ui.handle(ev);
    }
    const d = digestState(g, ui, r, ev === 'render') as Digest;
    d.step = n;
    d.ev = ev;
    out.push(jsonLine(d));
  }
  return out.join('\n') + '\n';
}

export function runRender(file: string, step?: number): number {
  const sc = load();
  const g = new Game(sc.map, sc.pool, sc.objectives);
  const ui = new Ui(g);
  const r = new Renderer();
  const evs = loadScript();
  const limit = step === undefined ? evs.length : Math.min(step, evs.length);
  for (let i = 0; i < limit; i++) {
    const ev = evs[i]!;
    if (ev === 'ai') {
      ai.takeTurn(g);
      g.endTurn();
      ui.afterTurn();
    } else {
      ui.handle(ev);
    }
  }
  r.draw(g, ui);
  const data = r.fb.toPpm(r.pal);
  fs.writeFileSync(file, data);
  process.stderr.write(`${file} · ${data.length}바이트 · FNV ${hex8(fnv1a(data))}\n`);
  return fnv1a(data);
}

export function runBench(): void {
  const P = require('./path') as typeof import('./path');
  const sc = load();
  const g = new Game(sc.map, sc.pool, sc.objectives);
  const u = g.pool.get(g.pool.aliveIds(0)[0]!)!;
  const n = 2000;
  const t0 = process.hrtime.bigint();
  for (let i = 0; i < n; i++) P.reachable(g.map, g.pool, u);
  const t1 = process.hrtime.bigint();
  const r = new Renderer();
  const ui = new Ui(g);
  const t2 = process.hrtime.bigint();
  for (let i = 0; i < 20; i++) r.draw(g, ui);
  const t3 = process.hrtime.bigint();
  const us = (a: bigint, b: bigint) => Number(b - a) / 1000;
  console.log(`reachable ${n}회 ${(us(t0, t1) / 1e6).toFixed(3)}초 ` +
              `(${(us(t0, t1) / n).toFixed(1)} us/회)`);
  console.log(`draw 20프레임 ${(us(t2, t3) / 1e6).toFixed(3)}초 ` +
              `(${(us(t2, t3) / 1000 / 20).toFixed(1)} ms/프레임)`);
}

if (require.main === module) {
  const cmd = process.argv[2] ?? 'trace';
  if (cmd === 'trace') process.stdout.write(runTrace(true));
  else if (cmd === 'render') {
    runRender(process.argv[3] ?? 'frame.ppm',
              process.argv[4] ? Number(process.argv[4]) : undefined);
  } else if (cmd === 'bench') runBench();
  else {
    process.stderr.write('사용법: trace | render <파일> [스텝] | bench\n');
    process.exit(2);
  }
}
