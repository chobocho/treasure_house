// tools/check_lib.mjs — 라이브러리판 서버(server_lib.ts)에 봇을 붙여 본편과 맞대어 본다.
//
// 확인하는 건 하나다: **클라이언트는 두 서버를 구분하지 못한다.**
// 같은 봇 코드로 같은 구성(PC 4대 × 2석)을 붙여 한 판을 끝까지 돌린다.
//
//   make lib

import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { readFileSync } from 'node:fs';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');
const PORT = 8911;

const { BotPeer } = await import(join(ROOT, 'dist', 'bot_client.js'));
const { createLibServer } = await import(join(ROOT, 'dist', 'src', 'net', 'server_lib.js'));
const levels = JSON.parse(readFileSync(join(ROOT, 'weights.json'), 'utf8')).levels;

const srv = createLibServer({ quiet: true, seed: 0xc0ffee, webRoot: '/dev/null' });
const port = await srv.listen(PORT);
const url = `ws://127.0.0.1:${port}/ws`;
console.log(`라이브러리판 서버 기동 — ${url}`);

const LV = ['max', 'hard', 'normal', 'easy'];
const INTERVAL = { max: 120, hard: 160, normal: 220, easy: 300 };
const peers = [];
const t0 = Date.now();
try {
  for (let pc = 1; pc <= 4; pc++) {
    const base = (pc - 1) * 2;
    const p = new BotPeer({
      url, name: `PC${pc}`, quiet: true, tickMs: 50,
      ...(pc === 1
        ? { create: { max: 8, perPeer: 2, target: 'random' } }
        : { room: peers[0].code }),
      seats: [0, 1].map((k) => {
        const lv = LV[(base + k) % 4];
        return { name: `s${base + k}`, lv, weights: levels[lv], intervalMs: INTERVAL[lv] };
      }),
    });
    peers.push(p);
    await p.ready();
  }
  await peers[0].waitSeats(8);
  peers[0].start();
  const order = await peers[0].waitEnd();
  await Promise.all(peers.map((p) => p.waitEnd(5000).catch(() => undefined)));

  const kos = peers[0].kos.length;
  const up = peers.reduce((a, p) => a + p.up, 0);
  const down = peers.reduce((a, p) => a + p.down, 0);
  const atk = peers.reduce((a, p) => a + p.atkCount, 0);
  const grb = peers.reduce((a, p) => a + p.grbCount, 0);
  const secs = (Date.now() - t0) / 1000;
  const ok = order.length === 8 && kos === 7 && atk > 0 && grb === atk;
  console.log(
    `${ok ? '✔' : '✖'} ws 라이브러리판 — 8석 완주, 탈락 ${kos}번, 공격 ${atk}회 → 배달 ${grb}회, ` +
    `보냄 ${(up / 1024).toFixed(1)} KB / 받음 ${(down / 1024).toFixed(1)} KB, ${secs.toFixed(1)}초`,
  );
  console.log(`   등수 순 좌석: ${order.join(', ')}`);
  process.exitCode = ok ? 0 : 1;
} finally {
  for (const p of peers) p.close();
  await srv.close();
}
