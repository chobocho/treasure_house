// 난이도 프리셋끼리 실제로 붙여 승률을 잰다 (덱에 적을 숫자를 확인하기 위해).
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
const SRC = new URL('.', import.meta.url).pathname;
const sandbox = {
  console, WebAssembly, Math, JSON, Date, Object, Array, Number, String, Promise,
  Uint8Array, Int32Array, Float32Array, Error, URL, Blob: class {}, Worker: class {},
  atob: (s) => Buffer.from(s, 'base64').toString('binary'),
  performance: { now: () => Date.now() }, requestAnimationFrame: () => 0, cancelAnimationFrame: () => {},
  ResizeObserver: class { observe() {} }, navigator: {}, devicePixelRatio: 1,
  innerWidth: 1280, innerHeight: 800, setTimeout, document: { createElement: () => ({}) },
  WASM_B64: readFileSync(SRC + 'tetris_ai.wasm').toString('base64'),   // 덱이 인라인하는 것과 같은 문자열
  GA_WEIGHTS: JSON.parse(readFileSync(SRC + 'weights.json', 'utf8')),
  GA_LOG: JSON.parse(readFileSync(SRC + 'ga_log.json', 'utf8')),
};
sandbox.window = sandbox; sandbox.globalThis = sandbox;
vm.createContext(sandbox);
for (const f of ['ga_core.mjs', 'battle.js']) {
  let c = readFileSync(SRC + f, 'utf8');
  if (f.endsWith('.mjs')) c = c.replace(/^export /gm, '');
  vm.runInContext(c, sandbox, { filename: f });
}
const res = await vm.runInContext(`(async () => {
  const pairs = [['easy','normal'],['normal','hard'],['hard','max'],['easy','max'],['normal','max'],['easy','hard']];
  const out = [];
  for (const [la, lb] of pairs) {
    let wa = 0, wb = 0, draw = 0, sa = 0, sb = 0;
    for (let m = 0; m < 24; m++) {
      const seed = (1000 + m * 7919) >>> 0;
      const a = await loadCore(WASM_B64, seed), b = await loadCore(WASM_B64, seed);
      const da = new AiDriver(a, levelOpts(la)), db = new AiDriver(b, levelOpts(lb));
      const ref = new Referee([{ core: a }, { core: b }], { bestOf: 1, onRound: () => {} });
      let i = 0;
      for (; i < 120000 && !ref.over; i++) {
        a.e.ts_update(16); da.step(16);
        b.e.ts_update(16); db.step(16);
        ref.route();
      }
      sa += ref.sent[0]; sb += ref.sent[1];
      if (!ref.over) draw++;
      else if (ref.wins[0]) wa++; else wb++;
    }
    out.push({ la, lb, wa, wb, draw, sa: (sa/24).toFixed(1), sb: (sb/24).toFixed(1) });
  }
  return out;
})()`, sandbox);
for (const r of res)
  console.log(`${r.la.padEnd(7)} vs ${r.lb.padEnd(7)}  ${r.wa}-${r.wb}${r.draw ? ' (무 ' + r.draw + ')' : ''}   평균 보낸 줄 ${r.sa} / ${r.sb}`);
