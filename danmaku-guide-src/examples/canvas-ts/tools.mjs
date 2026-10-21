import { copyFileSync, mkdirSync, readFileSync } from 'node:fs';
import { createServer } from 'node:http';
import { pathToFileURL } from 'node:url';

const src = new URL('../../', import.meta.url);

// #region deploy
export function deploy(target = new URL('dist/release/canvas.html', src)) {
  mkdirSync(new URL('./', target), { recursive: true });
  copyFileSync(new URL('dist/canvas-lv7.html', src), target);
  return { file: target.pathname, bytes: readFileSync(target).length };
}
// #endregion

// #region serve
export async function serve(port = 8000) {
  const html = readFileSync(new URL('dist/release/canvas.html', src));
  const server = createServer((request, response) => {
    if (request.url !== '/' && request.url !== '/index.html') {
      response.writeHead(404); response.end(); return;
    }
    response.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
    response.end(html);
  });
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(port, '127.0.0.1', resolve);
  });
  return server;
}
// #endregion

// #region profile-load
export async function profile(rounds = 5) {
  if (!Number.isInteger(rounds) || rounds < 1 || rounds > 20) throw new Error('반복 수는 1부터20까지 정수');
  const { Game } = await import(new URL('dist/canvas-lv7-logic.mjs', src));
  const stage = JSON.parse(readFileSync(new URL('lv7/stage.json', import.meta.url)));
  const inputs = JSON.parse(readFileSync(new URL('lv7/replay.json', import.meta.url)));
  const samplesMs = [];
  let finalGame;
  // #endregion
  // #region profile-run
  for (let round = -2; round < rounds; round++) {
    const game = new Game(undefined, stage);
    let cursor = 0, bits = 0;
    const start = performance.now();
    for (let frame = 0; frame < 1800; frame++) {
      if (cursor < inputs.length && inputs[cursor].frame === frame) bits = inputs[cursor++].bits;
      game.step(bits);
    }
    const elapsed = performance.now() - start;
    if (round >= 0) samplesMs.push(elapsed);
    finalGame = game;
  }
  // #endregion
  // #region profile-report
  const ordered = [...samplesMs].sort((a, b) => a - b);
  const middle = Math.floor(ordered.length / 2);
  const medianMs = ordered.length % 2 ? ordered[middle] : (ordered[middle - 1] + ordered[middle]) / 2;
  return { node: process.version, machine: process.arch, steps: 1800,
    activeSteps: finalGame.time, samplesMs, medianMs,
    method: '초기화 제외·준비2회·Node 로직만·프로파일러 없음·게임 오버 뒤 호출 포함',
    state: finalGame.snapshot() };
  // #endregion
}

// #region tool-entry
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const action = process.argv[2];
  if (action === 'deploy') console.log(JSON.stringify(deploy(), null, 2));
  else if (action === 'profile') console.log(JSON.stringify(await profile(), null, 2));
  else if (action === 'serve') {
    const server = await serve(Number(process.argv[3] ?? 8000));
    console.log('http://127.0.0.1:' + server.address().port);
    process.once('SIGINT', () => server.close());
    process.once('SIGTERM', () => server.close());
  } else throw new Error('알 수 없는 도구 항목');
}
// #endregion
