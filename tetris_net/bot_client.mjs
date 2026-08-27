// bot_client.mjs — 화면 없이 도는 대전 클라이언트.
//
//   node bot_client.mjs --url ws://127.0.0.1:8787/ws --pcs 4 --seats 2
//
// PC 4대가 각각 2석씩 쥐고 붙는 8인 대전을, 진짜 웹소켓으로, 진짜 wasm AI 로 돌린다.
// 브라우저 클라이언트와 **같은 프로토콜만** 쓴다. 서버는 이게 사람인지 봇인지,
// 브라우저인지 Node 인지 알지 못하고 알 필요도 없다.
//
// 솔직한 단서 하나: 진짜 PC 4대가 아니라 한 프로세스 안의 연결 4개다.
// 프로토콜과 서버 쪽 코드 경로는 완전히 같지만, 네트워크 지연은 루프백 값이다.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { loadNet, ST, STATE, snapshot, packState } from './net_core.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const WEIGHTS = JSON.parse(readFileSync(join(HERE, '..', 'tetris_ai', 'weights.json'), 'utf8'));

// 난이도 = GA 가 실제로 학습시킨 가중치 + 생각하는 속도.
// 가중치는 2편에서 뽑은 그대로다(weights.json). 여기서 새로 만든 값이 하나도 없다.
const LEVELS = {
  easy:   { w: WEIGHTS.levels.easy,   ms: 520 },
  normal: { w: WEIGHTS.levels.normal, ms: 300 },
  hard:   { w: WEIGHTS.levels.hard,   ms: 180 },
  max:    { w: WEIGHTS.levels.max,    ms: 110 },
};

function args(argv) {
  const o = { url: 'ws://127.0.0.1:8787/ws', pcs: 4, seats: 2, target: 'random',
              level: 'hard', max: 8, quiet: false, limit: 300000 };
  for (let i = 2; i < argv.length; i++) {
    const k = argv[i].replace(/^--/, '');
    if (k === 'quiet') { o.quiet = true; continue; }
    const v = argv[++i];
    o[k] = /^\d+$/.test(v) ? parseInt(v, 10) : v;
  }
  return o;
}
const A = args(process.argv);
const log = (...x) => { if (!A.quiet) console.log(...x); };

// ── PC 1대 ───────────────────────────────────────────────────────────
class Pc {
  constructor(n, opt) {
    this.n = n; this.opt = opt;
    this.pid = 0; this.code = ''; this.seats = new Map();   // seatIndex → {core, alive, lv}
    this.tx = 0; this.rx = 0; this.txMsg = 0; this.rxMsg = 0;
    this.pending = [];
    this.ws = new WebSocket(opt.url);
    this.ready = new Promise((res) => { this.onReady = res; });
    this.ws.onopen = () => this.send({ t: 'hello', v: 3, name: `PC${n}` });
    this.ws.onmessage = (ev) => this.recv(ev.data);
    this.ws.onerror = (e) => { console.error(`PC${n} 오류`, e.message || e); };
  }
  send(o) {
    const s = JSON.stringify(o);
    this.tx += Buffer.byteLength(s); this.txMsg++;
    this.ws.send(s);
  }
  recv(raw) {
    this.rx += Buffer.byteLength(raw); this.rxMsg++;
    const m = JSON.parse(raw);
    (this.onMsg || (() => {}))(m, this);
  }
}

// ── 한 판 ────────────────────────────────────────────────────────────
async function run() {
  const t0 = Date.now();
  const pcs = [];
  const world = { seats: [], order: null, startedAt: 0, seed: 0, grbCount: 0, atkCount: 0 };

  const onMsg = (m, pc) => {
    switch (m.t) {
      case 'hi': pc.pid = m.pid; pc.onReady(); break;
      case 'joined': pc.code = m.code; pc.joined && pc.joined(); break;
      case 'err': console.error(`PC${pc.n} 거절: ${m.code}`); break;
      case 'room': world.lobby = m.seats; break;
      case 'start': onStart(m, pc); break;
      case 'grb': {
        if (pc.n === 1) world.grbCount++;   // 브로드캐스트라 PC 수만큼 중복해 도착한다
        const s = pc.seats.get(m.i);
        if (s && s.alive) { s.core.e.ng_queue(m.n, m.from, m.hole); s.core.refresh(); }
        break;
      }
      case 'ko': {
        const w = world.seats[m.i];
        if (w) { w.place = m.place; w.by = m.by; w.alive = false; }
        // 브로드캐스트라 PC 4대가 다 받는다. 로그는 한 대만 찍는다.
        if (pc.n === 1) log(`  ☠ 좌석 ${m.i} 탈락 — ${m.place}등` + (m.by >= 0 ? ` (막타: 좌석 ${m.by})` : ' (자멸)'));
        break;
      }
      case 'end':
        if (world.order) break;
        world.order = m.order;
        // 우승자는 ko 를 받지 않는다 — 등수는 end 의 순서표에만 있다.
        m.order.forEach((seat, k) => { if (world.seats[seat]) world.seats[seat].place = k + 1; });
        break;
    }
  };

  const onStart = (m, pc) => {
    if (world.startedAt) return;
    world.startedAt = Date.now();
    world.seed = m.seed;
    world.seats = m.seats.map((s) => ({ ...s, alive: true, place: 0, by: -1 }));
    log(`\n▶ 라운드 시작 — 시드 ${m.seed}, 좌석 ${m.seats.length}석`);
  };

  // 1) PC 들을 띄우고 방을 만든다
  for (let i = 1; i <= A.pcs; i++) {
    const pc = new Pc(i, A);
    pc.onMsg = onMsg;
    pcs.push(pc);
    await pc.ready;
    if (i === 1) {
      const p = new Promise((r) => { pc.joined = r; });
      pc.send({ t: 'create', cfg: { max: A.max, target: A.target } });
      await p;
      log(`방 코드: ${pc.code}  (서버 ${A.url}, 타겟팅 ${A.target})`);
    } else {
      const p = new Promise((r) => { pc.joined = r; });
      pc.send({ t: 'join', room: pcs[0].code });
      await p;
    }
  }

  // 2) 좌석을 잡는다 — PC 1대당 최대 2석
  const levels = ['max', 'hard', 'hard', 'normal', 'normal', 'hard', 'max', 'normal'];
  let seatNo = 0;
  for (const pc of pcs) {
    for (let k = 0; k < A.seats && seatNo < A.max; k++, seatNo++) {
      const lv = A.level === 'mix' ? levels[seatNo % levels.length] : A.level;
      // 좌석 번호를 **명시**한다. i:-1(자동 배정)은 연결 4개가 동시에 요청하면
      // 서버 도착 순서에 따라 누가 몇 번을 받을지 달라진다 — 그러면 이쪽의
      // seatNo 장부와 어긋나 자기 좌석이 아닌 곳에 atk 를 쏘고 err own 을 받는다.
      pc.send({ t: 'seat', i: seatNo, kind: 'ai', name: `${lv}#${seatNo}`, lv });
      pc.seats.set(seatNo, { core: null, alive: true, lv });
    }
    pc.send({ t: 'ready', v: true });
  }
  await new Promise((r) => setTimeout(r, 200));

  // 3) 시작 — 모든 좌석이 같은 시드를 받는다(같은 조각 순서 = 공평한 대전)
  pcs[0].send({ t: 'start' });
  await new Promise((r) => setTimeout(r, 300));
  if (!world.startedAt) throw new Error('서버가 start 를 내리지 않았다');

  for (const pc of pcs) {
    for (const [i, s] of pc.seats) {
      s.core = await loadNet(world.seed);
      s.core.views.weights.set(Float32Array.from(LEVELS[s.lv].w));
      s.core.e.ng_set_delay(900);
      s.think = 0;
      s.thinkMs = LEVELS[s.lv].ms;
      s.i = i;
    }
  }

  // 4) 게임 루프. 진짜 PC 라면 각자의 rAF 가 돌겠지만, 여기서는 하나의 타이머가
  //    모든 좌석을 16ms 씩 밀어 준다. 프로토콜과 서버 코드 경로는 똑같다.
  const DT = 16, ST_EVERY = 6;                     // 상태 전송 = 약 10Hz
  let frame = 0;
  const deadline = Date.now() + A.limit;
  await new Promise((resolve) => {
    const timer = setInterval(() => {
      frame++;
      for (const pc of pcs) {
        for (const [i, s] of pc.seats) {
          if (!s.alive || !s.core) continue;
          const c = s.core;
          c.e.ng_update(DT); c.refresh();
          s.think += DT;
          if (s.think >= s.thinkMs && c.views.stats[ST.STATE] === STATE.PLAY) {
            s.think = 0; c.e.ng_step(); c.refresh();
          }
          const atk = c.e.ng_take_attack();
          if (atk > 0) { world.atkCount++; pc.send({ t: 'atk', i, n: atk }); }
          if (frame % ST_EVERY === 0) pc.send({ t: 'st', i, b: snapshot(c), s: packState(c) });
          if (c.views.stats[ST.STATE] !== STATE.PLAY) {
            s.alive = false;
            pc.send({ t: 'ko', i });
          }
        }
      }
      if (world.order || Date.now() > deadline) { clearInterval(timer); resolve(); }
    }, DT);
  });

  // 5) 결과
  const secs = (Date.now() - world.startedAt) / 1000;
  const rows = [];
  for (const pc of pcs) {
    for (const [i, s] of pc.seats) {
      const st = s.core.views.stats;
      rows.push({ seat: i, pc: pc.n, lv: s.lv, place: world.seats[i]?.place || 0,
        lines: st[ST.LINES], pieces: st[ST.PIECES], recv: st[ST.GARBAGE_RECV], score: st[ST.SCORE] });
    }
  }
  rows.sort((a, b) => (a.place || 99) - (b.place || 99));
  const tx = pcs.reduce((a, p) => a + p.tx, 0), rx = pcs.reduce((a, p) => a + p.rx, 0);
  const txM = pcs.reduce((a, p) => a + p.txMsg, 0), rxM = pcs.reduce((a, p) => a + p.rxMsg, 0);

  console.log(`\n── 결과 (${secs.toFixed(1)}초, ${frame}프레임) ──`);
  console.log('등수  좌석  PC  난이도    줄   조각   맞은줄     점수');
  for (const r of rows) {
    console.log(`${String(r.place).padStart(3)}   ${String(r.seat).padStart(3)}  ${r.pc}   ${r.lv.padEnd(7)}` +
      `${String(r.lines).padStart(5)}${String(r.pieces).padStart(7)}${String(r.recv).padStart(9)}${String(r.score).padStart(9)}`);
  }
  console.log(`\n공격 ${world.atkCount}회 → 가비지 배달 ${world.grbCount}회`);
  console.log(`보냄 ${txM}개 / ${(tx / 1024).toFixed(1)} KB   받음 ${rxM}개 / ${(rx / 1024).toFixed(1)} KB`);
  console.log(`PC 1대당 평균 ${(tx / A.pcs / secs / 1024).toFixed(2)} KB/s 업 · ${(rx / A.pcs / secs / 1024).toFixed(2)} KB/s 다운`);
  console.log(`전체 걸린 시간 ${((Date.now() - t0) / 1000).toFixed(1)}초`);

  for (const pc of pcs) pc.ws.close();
  return { rows, secs, tx, rx, txM, rxM, frame, atk: world.atkCount, grb: world.grbCount,
           order: world.order, seed: world.seed };
}

const out = await run();
if (process.env.BOT_JSON) {
  const { writeFileSync } = await import('node:fs');
  writeFileSync(process.env.BOT_JSON, JSON.stringify(out, null, 1));
}
process.exit(out.order ? 0 : 1);
