// 브라우저 번들이 정말 같은 엔진인지 확인한다.
//
// 묶는 과정(tools/bundle_web.py)에서 무언가 어긋났을 수 있다. 확인 방법은 하나다 —
// 번들로 골든 트레이스를 다시 만들어 바이트로 대조하는 것.
'use strict';
const fs = require('fs');
const path = require('path');

const vm = require('vm');

const ROOT = path.resolve(__dirname, '..');

// require() 로 부르면 안 된다. 노드의 모듈 스코프는 __dirname 과 process 를 주는데
// 브라우저에는 그런 것이 없다. require 로 검사하면 브라우저에서만 터지는 버그를 놓친다.
// (실제로 놓쳤다 — raster 와 game 이 최상위에서 __dirname 을 쓰고 있었다.)
const win = { addEventListener() {}, setTimeout: setTimeout, clearTimeout: clearTimeout };
win.window = win;
win.globalThis = win;
const ctx = vm.createContext(win);
vm.runInContext(fs.readFileSync(path.join(ROOT, 'deck', 'engine.js'), 'utf8'), ctx,
                { filename: 'deck/engine.js' });

const R = win.__rts.require;
const RA = R('raster');
const G = R('game');
const D = R('web/data');

RA.setLight(RA.buildLight(RA.parsePalette(D.PALETTE_TXT)));
const g = new G.Game();
g.setSprites(RA.parseSprites(D.TILES_RLE));

const out = [];
g.runScriptText(D.SCRIPT_TXT, (l) => out.push(l));
const got = out.join('\n') + '\n';
const want = fs.readFileSync(path.join(ROOT, 'golden', 'trace.jsonl'), 'utf8');

let bad = 0;
if (got === want) {
  console.log('  브라우저 번들 트레이스 ' + out.length + '줄 == golden/trace.jsonl   OK');
} else {
  const a = got.split('\n');
  const b = want.split('\n');
  for (let i = 0; i < Math.max(a.length, b.length); i++) {
    if (a[i] !== b[i]) { console.log('  ' + (i + 1) + '줄 다름\n    기대 ' + b[i] + '\n    실제 ' + a[i]); break; }
  }
  bad++;
}

const fb = g.render();
const kinds = new Set(fb).size;
if (fb.length === 64000 && kinds > 8) {
  console.log('  프레임버퍼 ' + fb.length + '바이트 · 색 ' + kinds + '종                     OK');
} else {
  console.log('  프레임버퍼가 이상하다: ' + fb.length + '바이트 · 색 ' + kinds + '종');
  bad++;
}

// 파일을 읽으려 하면 조용히 넘어가지 않고 터져야 한다
try {
  RA.loadPalette();
  console.log('  fs 스텁이 터지지 않았다 — 브라우저에서 조용히 빈 값이 나올 수 있다');
  bad++;
} catch (e) {
  console.log('  fs 스텁 확인: ' + e.message.slice(0, 30) + '…             OK');
}

process.exit(bad ? 1 : 0);
