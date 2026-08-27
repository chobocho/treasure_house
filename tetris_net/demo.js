// demo.js — 이 문서 안에서 도는 데모들. 슬라이드의 [data-demo] 를 보고 하나씩 붙인다.
//
// 데모가 진짜인 이유: 여기서 쓰는 room 엔진은 Go·파이썬 서버와 **같은 골든 벡터**를
// 통과한 room.mjs 그대로고, 판을 돌리는 wasm 도 서버에 붙을 때와 같은 것이다.
// 바뀌는 건 전송 계층 하나뿐 — WebSocket 대신 LoopbackTransport.

// 남의 PC 몫으로 도는 Match 는 그릴 필요가 없다. 화면은 1번 PC 시점 하나뿐이다.
class NullArena {
  constructor() { this.banner = ''; }
  setSeats() {} attach() {} onState() {} onGarbage() {} onKo() {} draw() {}
}

const LV_KO = { easy: '초보', normal: '보통', hard: '고수', max: '최강' };
const TARGET_KO = { random: '무작위', even: '분산', attackers: '반격', ko: '막타' };

// spec = { pcs, seats:[{pc,kind,lv}], target, latency, human:[좌석번호…], autoRestart }
async function buildDemo(host, spec) {
  host.innerHTML = '';
  host.style.cssText = 'display:flex;flex-direction:column;gap:6px;min-height:340px';
  const bar = document.createElement('div');
  bar.style.cssText = 'display:flex;gap:8px;flex-wrap:wrap;align-items:center;font-size:12px;color:#94a3b8';
  const field = document.createElement('div');
  field.style.cssText = 'flex:1 1 auto;min-height:280px;background:#020617;border-radius:8px;outline:none';
  field.tabIndex = 0;
  host.appendChild(bar); host.appendChild(field);

  const cfg = { max: spec.max || spec.seats.length, perPeer: 2, target: spec.target || 'random',
                delay: 900, cap: 8, hitTTL: 8000 };
  const seed = (Math.random() * 0x7fffffff) >>> 0 || 1;
  const hub = new LoopbackHub(cfg, seed, spec.latency || 0);
  const arena = new Arena(field);
  const keys = new LocalKeys(field);
  const pads = new Pads();
  const humans = new Set(spec.human || []);
  const ctl = { hub, arena, matches: [], clients: [], done: false, running: false };

  for (let pid = 1; pid <= spec.pcs; pid++) {
    const mine = spec.seats.map((s, i) => ({ ...s, i })).filter((s) => s.pc === pid);
    const c = new NetClient(hub.connect(pid), 'PC' + pid);
    const m = wireMatch(c, new Match({
      client: c, arena: pid === 1 ? arena : new NullArena(),
      wasmB64: WASM_B64, weights: NET_WEIGHTS,
      keys: pid === 1 ? keys : null, pads: pid === 1 ? pads : null,
      cfg, onEnd: (e) => onEnd(e),
    }));
    c.on('hi', () => { pid === 1 ? c.create(cfg) : c.join('LOCAL1'); });
    c.on('joined', () => {
      for (const s of mine) {
        const human = humans.has(s.i);
        c.takeSeat(s.i, human ? 'human' : 'ai', human ? (s.name || `${s.i + 1}P`) : `${LV_KO[s.lv] || s.lv}`, human ? '' : s.lv);
      }
      c.setReady(true);
    });
    c.on('start', (msg) => {
      let slot = 0;
      const plan = msg.seats.filter((s) => s.pid === c.pid).map((s) => ({
        i: s.i, kind: s.kind, lv: s.lv, name: s.name,
        slot: s.kind === 'human' ? slot++ : 0,
      }));
      m.begin(msg, plan);
    });
    c.open();
    ctl.clients.push(c); ctl.matches.push(m);
  }

  const status = document.createElement('span');
  bar.appendChild(status);
  const tick = setInterval(() => {
    const alive = hub.room.aliveSeats().length;
    status.textContent = `좌석 ${hub.room.occupied().length}석 · 생존 ${alive} · 타겟팅 ${TARGET_KO[cfg.target]}`
      + (spec.latency ? ` · 지연 ${spec.latency}ms` : '') + ` · 서버가 보낸 ${(hub.tx / 1024).toFixed(1)} KB`;
  }, 400);
  ctl.tick = tick;

  function onEnd() {
    if (!spec.autoRestart || ctl.done) return;
    setTimeout(() => { if (!ctl.done && ctl.running) ctl.restart(); }, 2600);
  }
  ctl.restart = () => {
    for (const m of ctl.matches) m.stop();
    hub.room = new Room(cfg, (Math.random() * 0x7fffffff) >>> 0 || 1);
    for (const c of ctl.clients) {
      const pid = c.pid;
      hub.room.handle(pid, { t: 'ping' }, 0);      // peers 에 다시 등록시킨다
    }
    for (const c of ctl.clients) c.emit('joined', { code: 'LOCAL1', cfg });
    setTimeout(() => ctl.clients[0].startRound(), 60);
  };
  ctl.start = () => {
    ctl.running = true;
    if (hub.room.phase === 'lobby') setTimeout(() => ctl.clients[0].startRound(), 120);
    else for (const m of ctl.matches) if (m.seats.size && !m.running) { m.running = true; m.last = performance.now(); requestAnimationFrame((t) => m.frame(t)); }
  };
  ctl.stop = () => { ctl.running = false; for (const m of ctl.matches) m.stop(); };
  return ctl;
}

// ── 데모 목록 ────────────────────────────────────────────────────────
const DEMOS = {};

// 1인용 — 서버 없이도 같은 코드가 돈다. 좌석 1석이면 그게 1인용이다.
DEMOS.solo = (host) => buildDemo(host, { pcs: 1, max: 1, seats: [{ pc: 1 }], human: [0] });

// 한 PC 에 두 명 — 키맵 두 벌이 전부다.
DEMOS.local2 = (host) => buildDemo(host, {
  pcs: 1, max: 2, seats: [{ pc: 1 }, { pc: 1 }], human: [0, 1], autoRestart: true });

// 8인 AI 대전 — PC 4대 × 2석. 진짜 대전과 같은 구성이다.
DEMOS.arena8 = (host) => buildDemo(host, {
  pcs: 4, max: 8, target: host.dataset.target || 'random', autoRestart: true,
  seats: [{ pc: 1, lv: 'max' }, { pc: 1, lv: 'hard' }, { pc: 2, lv: 'hard' }, { pc: 2, lv: 'normal' },
          { pc: 3, lv: 'max' }, { pc: 3, lv: 'normal' }, { pc: 4, lv: 'hard' }, { pc: 4, lv: 'easy' }] });

// 사람 1명 + AI 7명 — 요구사항 그대로의 판.
DEMOS.mixed = (host) => buildDemo(host, {
  pcs: 4, max: 8, human: [0], autoRestart: true, target: host.dataset.target || 'even',
  seats: [{ pc: 1 }, { pc: 1, lv: 'hard' }, { pc: 2, lv: 'hard' }, { pc: 2, lv: 'normal' },
          { pc: 3, lv: 'max' }, { pc: 3, lv: 'normal' }, { pc: 4, lv: 'hard' }, { pc: 4, lv: 'easy' }] });

// 지연을 넣어 본다 — 내 조작은 그대로고 남의 판만 늦게 보인다는 걸 눈으로 확인한다.
DEMOS.lag = (host) => buildDemo(host, {
  pcs: 4, max: 8, latency: parseInt(host.dataset.latency || '150', 10), autoRestart: true,
  human: [0],
  seats: [{ pc: 1 }, { pc: 1, lv: 'hard' }, { pc: 2, lv: 'hard' }, { pc: 2, lv: 'normal' },
          { pc: 3, lv: 'max' }, { pc: 3, lv: 'normal' }, { pc: 4, lv: 'hard' }, { pc: 4, lv: 'easy' }] });

// 스냅샷 인코딩을 눈으로 — 판을 바꾸면 바이트 수가 어떻게 변하는지.
DEMOS.rle = async (host) => {
  host.innerHTML = '<div class="rle-out" style="font:12px/1.6 ui-monospace,monospace;color:#94a3b8;'
    + 'white-space:pre-wrap;word-break:break-all"></div>';
  const out = host.querySelector('.rle-out');
  const core = await loadNet(WASM_B64, 12345);
  let n = 0, timer = 0;
  const render = () => {
    const bytes = core.e.ng_snapshot();
    const b64 = snapshot(core);
    const raw = [];
    for (let i = 0; i < Math.min(bytes, 14); i++) {
      const v = core.views.snap[i];
      raw.push(`${((v >> 4) + 1)}×${v & 15}`);
    }
    out.textContent =
      `굳은 블록 ${core.views.cells.reduce((a, b) => a + (b ? 1 : 0), 0)}칸\n`
      + `런렝스 ${bytes}바이트  →  base64 ${b64.length}자\n`
      + `앞부분: ${raw.join(' ')}${bytes > 14 ? ' …' : ''}\n`
      + `b64: ${b64.slice(0, 96)}${b64.length > 96 ? '…' : ''}\n\n`
      + `좌석 8석 × 초당 10회 = ${(b64.length * 8 * 10 / 1024).toFixed(1)} KB/s`;
  };
  const step = () => {
    n++;
    if (n % 7 === 0) { core.e.ng_init(12345 + n); }
    else { core.e.ts_garbage(1, (n * 3) % 10); }
    core.refresh(); render();
  };
  render();
  return { start() { timer = setInterval(step, 900); }, stop() { clearInterval(timer); } };
};

// 실제 오가는 메시지를 그대로 보여 준다 — 프로토콜이 정말 이게 다인지 확인용.
DEMOS.wire = async (host) => {
  host.innerHTML = '<div class="wire-log" style="font:11px/1.5 ui-monospace,monospace;color:#cbd5e1;'
    + 'height:300px;overflow:auto;background:#020617;border-radius:8px;padding:8px"></div>';
  const log = host.querySelector('.wire-log');
  const cfg = { max: 4, perPeer: 2, target: 'attackers', delay: 900, cap: 8, hitTTL: 8000 };
  const hub = new LoopbackHub(cfg, 20260827, 0);
  const put = (dir, pid, m) => {
    const row = document.createElement('div');
    row.textContent = `${dir === 'up' ? '▲' : '▼'} PC${pid}  ${JSON.stringify(m).slice(0, 150)}`;
    row.style.color = dir === 'up' ? '#7dd3fc' : '#fbbf24';
    log.appendChild(row); log.scrollTop = log.scrollHeight;
    while (log.children.length > 300) log.removeChild(log.firstChild);
  };
  const clients = [], matches = [];
  for (let pid = 1; pid <= 2; pid++) {
    const tr = hub.connect(pid);
    const origSend = tr.send.bind(tr);
    tr.send = (o) => { put('up', pid, o); origSend(o); };
    const c = new NetClient(tr, 'PC' + pid);
    const om = c.onMessage.bind(c);
    c.onMessage = (m) => { if (m.t !== 'st' && m.t !== 'pong') put('down', pid, m); om(m); };
    const m = wireMatch(c, new Match({ client: c, arena: new NullArena(), wasmB64: WASM_B64,
      weights: NET_WEIGHTS, cfg, onEnd: () => {} }));
    c.on('hi', () => { pid === 1 ? c.create(cfg) : c.join('LOCAL1'); });
    c.on('joined', () => {
      c.takeSeat((pid - 1) * 2, 'ai', '봇' + (pid * 2 - 1), 'hard');
      c.takeSeat((pid - 1) * 2 + 1, 'ai', '봇' + (pid * 2), 'normal');
      c.setReady(true);
    });
    c.on('start', (msg) => m.begin(msg, msg.seats.filter((s) => s.pid === c.pid)
      .map((s) => ({ i: s.i, kind: 'ai', lv: s.lv, name: s.name, slot: 0 }))));
    c.open();
    clients.push(c); matches.push(m);
  }
  return {
    start() { setTimeout(() => clients[0].startRound(), 150); },
    stop() { for (const m of matches) m.stop(); },
  };
};

window.__mountDemo = async function (host) {
  const kind = host.dataset.demo || 'arena8';
  const fn = DEMOS[kind];
  if (!fn) throw new Error('알 수 없는 데모: ' + kind);
  return await fn(host);
};
