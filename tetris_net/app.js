// app.js — 진짜로 여럿이 붙을 때 쓰는 페이지의 배선. web/index.html 이 이걸 부른다.
//
// 화면은 로비와 대전 둘뿐이다. 로비에서 좌석을 고르고, 시작하면 arena 가 그린다.
// 서버가 Go 든 파이썬이든 이 파일은 달라지지 않는다 — 주소만 바뀐다.

const $ = (id) => document.getElementById(id);
const LEVEL_KO = { easy: '초보', normal: '보통', hard: '고수', max: '최강' };

const App = {
  client: null, match: null, arena: null, keys: null, pads: null,
  cfg: null, wasm: null, weights: null, myPlan: [],

  async boot() {
    // wasm 은 페이지와 같은 폴더에서 받아 온다. 서버(-dir)가 그대로 내준다.
    const res = await fetch('tetris_net.wasm');
    this.wasm = new Uint8Array(await res.arrayBuffer());
    this.weights = (await (await fetch('weights.json')).json()).levels;
    this.arena = new Arena($('field'));
    this.keys = new LocalKeys($('field'));
    this.pads = new Pads();
    $('url').value = (location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/ws';
    $('btnCreate').onclick = () => this.connect(true);
    $('btnJoin').onclick = () => this.connect(false);
    $('btnReady').onclick = () => this.client.setReady(!this.iAmReady());
    $('btnStart').onclick = () => this.client.startRound();
    $('btnSolo').onclick = () => this.solo();
    addEventListener('resize', () => this.arena && this.arena.draw());
    this.say('서버 주소를 확인하고 방을 만들거나 코드로 들어가세요.');
  },

  say(t) { $('msg').textContent = t; },
  iAmReady() {
    const mine = this.client.seats.filter((s) => s.pid === this.client.pid);
    return mine.length > 0 && mine.every((s) => s.ready);
  },

  connect(create) {
    const tr = new WsTransport($('url').value.trim());
    this.client = new NetClient(tr, $('name').value.trim() || '이름없음');
    this.client
      .on('hi', () => { create ? this.client.create(this.readCfg()) : this.client.join($('code').value.trim().toUpperCase()); })
      .on('joined', (m) => { this.cfg = m.cfg; $('code').value = m.code; this.say(`방 ${m.code} — 좌석을 고르세요`); this.renderSeats(); })
      .on('room', () => this.renderSeats())
      .on('err', (m) => this.say('⚠ ' + (ERR_KO[m.code] || m.code)))
      .on('start', (m) => this.onStart(m))
      .on('closed', () => this.say('연결이 끊어졌습니다'));
    this.match = wireMatch(this.client, new Match({
      client: this.client, arena: this.arena, wasmB64: this.wasm,
      weights: this.weights, keys: this.keys, pads: this.pads,
      cfg: this.cfg || {}, onEnd: () => { $('lobby').hidden = false; },
    }));
    this.client.open();
  },

  readCfg() {
    return { max: parseInt($('cfgMax').value, 10), target: $('cfgTarget').value,
             delay: parseInt($('cfgDelay').value, 10) };
  },

  // 좌석표 — 클릭하면 잡고, 다시 클릭하면 놓는다. 내 좌석은 최대 2석(§2 perPeer).
  renderSeats() {
    const box = $('seats'), c = this.client;
    const max = (this.cfg && this.cfg.max) || 8;
    box.innerHTML = '';
    for (let i = 0; i < max; i++) {
      const s = c.seats.find((x) => x.i === i);
      const el = document.createElement('button');
      el.className = 'seat' + (s ? (s.pid === c.pid ? ' mine' : ' taken') : '');
      el.innerHTML = s
        ? `<b>${i + 1}</b>${s.kind === 'ai' ? '🤖' : '🧑'} ${s.name}<small>${s.ready ? '준비✓' : (s.lv ? LEVEL_KO[s.lv] || s.lv : '대기')}</small>`
        : `<b>${i + 1}</b><small>빈 자리</small>`;
      el.onclick = () => {
        if (s && s.pid === c.pid) c.dropSeat(i);
        else if (!s) c.takeSeat(i, $('kind').value, $('name').value.trim() || `P${i + 1}`, $('lv').value);
      };
      box.appendChild(el);
    }
    const mine = c.seats.filter((x) => x.pid === c.pid);
    $('hint').textContent = mine.length === 2
      ? '이 PC 에 2명 — 1P는 방향키/Space, 2P는 WASD/F' : '이 PC 에 1명 — 방향키/Space';
    $('btnStart').hidden = c.seats.length === 0 || c.pid !== (c.seats[0] && c.seats[0].pid && Math.min(...c.seats.map((x) => x.pid)));
  },

  onStart(m) {
    const mine = m.seats.filter((s) => s.pid === this.client.pid);
    let slot = 0;
    this.myPlan = mine.map((s) => ({ i: s.i, kind: s.kind, lv: s.lv, name: s.name,
                                     slot: s.kind === 'human' ? slot++ : 0 }));
    $('lobby').hidden = true;
    $('field').focus({ preventScroll: true });
    this.match.cfg = this.cfg || { delay: 900, cap: 8 };
    this.match.begin(m, this.myPlan);
  },

  // 1인용 — 서버가 필요 없다. 이 페이지 안의 room 엔진(=Go·파이썬과 같은 규칙)에 붙는다.
  solo() {
    const hub = new LoopbackHub({ max: 1, perPeer: 1, target: 'random' }, (Math.random() * 2 ** 31) | 1);
    this.cfg = hub.room.cfg;
    this.client = new NetClient(hub.connect(1), $('name').value.trim() || '혼자');
    this.client
      .on('hi', () => this.client.create({}))
      .on('joined', () => { this.client.takeSeat(0, 'human', '혼자'); this.client.setReady(true); this.client.startRound(); })
      .on('start', (m) => this.onStart(m))
      .on('err', (m) => this.say('⚠ ' + (ERR_KO[m.code] || m.code)));
    this.match = wireMatch(this.client, new Match({
      client: this.client, arena: this.arena, wasmB64: this.wasm, weights: this.weights,
      keys: this.keys, pads: this.pads, cfg: { delay: 900, cap: 8 },
      onEnd: () => { $('lobby').hidden = false; },
    }));
    this.client.open();
  },
};

addEventListener('DOMContentLoaded', () => App.boot());
