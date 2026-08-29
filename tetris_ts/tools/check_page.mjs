// tools/check_page.mjs — 진짜 서버에 진짜 브라우저로 붙어 본다.
//
// 덱 안의 루프백 데모는 전송 계층을 바꿔치기한 것이라, "소켓까지 포함해서 도는가"는
// 증명하지 못한다. 이 도구가 그 마지막 칸을 채운다:
//   서버를 띄우고 → 크로미움으로 페이지를 열고 → 로비 버튼을 눌러 방을 만들고
//   → AI 좌석을 채워 시작하고 → 판이 실제로 그려지는지 픽셀을 세어 확인한다.
//
//   node tools/check_page.mjs [--port 8899] [--shot 경로]

import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const PW = '/root/.npm/_npx/e41f203b7505f1fb/node_modules/playwright/index.mjs';
const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');

const arg = (name, dflt) => {
  const i = process.argv.indexOf('--' + name);
  return i >= 0 ? (process.argv[i + 1] ?? dflt) : dflt;
};
const PORT = Number(arg('port', 8899));
const SHOT = arg('shot', '');

const srv = spawn('node', [join(ROOT, 'dist', 'src', 'net', 'server.js'), '--port', String(PORT)],
  { cwd: ROOT, stdio: ['ignore', 'pipe', 'pipe'] });
const srvLog = [];
srv.stdout.on('data', (b) => srvLog.push(String(b)));
srv.stderr.on('data', (b) => srvLog.push(String(b)));

/** 서버가 포트를 열 때까지 기다린다. */
async function waitListen(ms = 8000) {
  const t0 = Date.now();
  while (Date.now() - t0 < ms) {
    if (srvLog.join('').includes(String(PORT))) return true;
    await new Promise((r) => setTimeout(r, 100));
  }
  return false;
}

let code = 0;
try {
  if (!await waitListen()) throw new Error(`서버가 안 떴다:\n${srvLog.join('')}`);
  const { chromium } = await import(PW);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 800, height: 900 } });
  const errs = [];
  page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  page.on('pageerror', (e) => errs.push(String(e)));

  await page.goto(`http://127.0.0.1:${PORT}/`);
  await page.waitForSelector('#app canvas');
  const click = async (label) => { await page.getByRole('button', { name: label }).click(); };
  await click('방 만들기');
  await page.waitForFunction(() => /방 [A-Z2-9]{4}/.test(document.querySelector('#app').textContent));
  // 규격상 한 PC 는 좌석 2석까지다(perPeer). 세 번째는 서버가 full 로 막는다 —
  // 일부러 세 번 눌러서 그 거절까지 확인한다.
  for (let i = 0; i < 3; i++) await click('AI 좌석 추가');
  await click('시작');
  await new Promise((r) => setTimeout(r, 6000));

  const st = await page.evaluate(() => {
    const c = document.querySelector('#app canvas');
    const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
    let lit = 0;
    for (let i = 0; i < d.length; i += 4) if (d[i] + d[i + 1] + d[i + 2] > 90) lit++;
    const app = window.__app;
    return {
      lit, code: app.client.code, seats: app.client.seats.length,
      mine: app.match.seats.length,
      pieces: app.match.seats.reduce((a, s) => a + s.game.stats[15], 0),
      text: document.querySelector('#app').textContent.replace(/\s+/g, ' ').slice(0, 120),
    };
  });
  if (SHOT) await page.screenshot({ path: SHOT });
  await browser.close();

  const ok = st.lit > 100 && st.seats === 2 && st.mine === 2 && st.pieces > 4 && errs.length === 0;
  console.log(`${ok ? '✔' : '✖'} 페이지 — 방 ${st.code}, 좌석 ${st.seats}석(내 몫 ${st.mine}), ` +
    `조각 ${st.pieces}개, 칠해진 픽셀 ${st.lit}, 콘솔 오류 ${errs.length}건 (PC 1대 = 2석 상한)`);
  console.log('   ' + st.text);
  for (const e of errs.slice(0, 5)) console.log('   콘솔: ' + e);
  if (!ok) code = 1;
} catch (e) {
  console.error('✖ ' + String(e));
  code = 1;
} finally {
  srv.kill('SIGTERM');
}
process.exit(code);
