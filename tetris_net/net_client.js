// net_client.js — 프로토콜 v3 클라이언트. 전송 계층을 갈아 끼울 수 있게 만들었다.
//
//   WsTransport      진짜 서버 (Go 든 파이썬이든 구분하지 않는다)
//   LoopbackTransport 이 페이지 안에서 도는 세 번째 구현 (room.mjs)
//
// 이 문서 안의 데모가 실제로 도는 이유가 두 번째 전송 계층이다.
// 두 전송은 NetClient 입장에서 완전히 같다 — send(객체) 와 onmessage(객체) 뿐이다.

class WsTransport {
  constructor(url) { this.url = url; this.ws = null; this.onmessage = null; this.onopen = null;
                     this.onclose = null; this.tx = 0; this.rx = 0; }
  open() {
    this.ws = new WebSocket(this.url);
    this.ws.onopen = () => this.onopen && this.onopen();
    this.ws.onclose = () => this.onclose && this.onclose();
    this.ws.onerror = () => {};
    this.ws.onmessage = (ev) => {
      this.rx += ev.data.length;
      let m; try { m = JSON.parse(ev.data); } catch (_) { return; }
      this.onmessage && this.onmessage(m);
    };
  }
  send(o) {
    if (!this.ws || this.ws.readyState !== 1) return;
    const s = JSON.stringify(o);
    this.tx += s.length;
    this.ws.send(s);
  }
  close() { this.ws && this.ws.close(); }
}

// 이 페이지 안의 서버. room.mjs 를 그대로 쓴다 — Go·파이썬과 같은 골든 벡터를 통과한 그 파일이다.
// 가상 PC 를 여러 대 만들 수 있어서, "PC 4대 × 2석 = 8인"이라는 진짜 구성을 그대로 재현한다.
class LoopbackHub {
  constructor(cfg, seed, latency = 0) {
    this.room = new Room(cfg, seed);
    this.peers = new Map();
    this.t0 = performance.now();
    this.latency = latency;      // 편도 지연(ms) — 0이면 즉시
    this.tx = 0;
  }
  now() { return Math.round(performance.now() - this.t0); }
  connect(pid) {
    const t = new LoopbackTransport(this, pid);
    this.peers.set(pid, t);
    return t;
  }
  deliver(pid, m) {
    const outs = this.room.handle(pid, m, this.now());
    for (const o of outs) {
      const targets = o.to === 0 ? [...this.peers.keys()] : [o.to];
      for (const p of targets) {
        const t = this.peers.get(p);
        if (!t || !t.onmessage) continue;
        this.tx += JSON.stringify(o.m).length;
        if (this.latency > 0) setTimeout(() => t.onmessage(o.m), this.latency);
        else t.onmessage(o.m);
      }
    }
  }
}
class LoopbackTransport {
  constructor(hub, pid) { this.hub = hub; this.pid = pid; this.onmessage = null;
                          this.onopen = null; this.onclose = null; this.tx = 0; this.rx = 0; }
  open() { setTimeout(() => this.onopen && this.onopen(), 0); }
  send(o) {
    this.tx += JSON.stringify(o).length;
    // hub 는 hello/create/join 을 모른다 — 루프백에서는 이미 방이 하나뿐이므로
    // 그 셋만 여기서 흉내 내고 나머지는 그대로 room 으로 넘긴다.
    if (o.t === 'hello') { this.onmessage && this.onmessage({ t: 'hi', pid: this.pid, v: 3 }); return; }
    if (o.t === 'create' || o.t === 'join') {
      this.onmessage && this.onmessage({ t: 'joined', code: 'LOCAL1', cfg: this.hub.room.cfg, pid: this.pid });
      return;
    }
    if (o.t === 'ping') { this.onmessage && this.onmessage({ t: 'pong', c: o.c }); return; }
    if (this.hub.latency > 0) setTimeout(() => this.hub.deliver(this.pid, o), this.hub.latency);
    else this.hub.deliver(this.pid, o);
  }
  close() { this.hub.peers.delete(this.pid); }
}

// ── 클라이언트 본체 ──
class NetClient {
  constructor(transport, name) {
    this.tr = transport;
    this.name = name || '이름없음';
    this.pid = 0; this.code = ''; this.cfg = null;
    this.seats = [];            // 로비가 알려 준 좌석 목록
    this.handlers = {};
    this.pingSeq = 0; this.rtt = 0; this.pingTimer = 0;
    this.tr.onopen = () => this.send({ t: 'hello', v: 3, name: this.name });
    this.tr.onclose = () => this.emit('closed', {});
    this.tr.onmessage = (m) => this.onMessage(m);
  }
  on(t, fn) { (this.handlers[t] || (this.handlers[t] = [])).push(fn); return this; }
  emit(t, m) { for (const fn of this.handlers[t] || []) fn(m); }
  send(o) { this.tr.send(o); }
  open() { this.tr.open(); }
  close() { if (this.pingTimer) clearInterval(this.pingTimer); this.tr.close(); }

  onMessage(m) {
    switch (m.t) {
      case 'hi':
        this.pid = m.pid;
        // 왕복 지연은 1초에 한 번만 잰다. 이 게임은 지연에 민감하지 않다 —
        // 남의 판을 늦게 보는 것뿐이고, 내 판은 내 PC 에서 돈다.
        this.pingTimer = setInterval(() => {
          this.pingAt = performance.now();
          this.send({ t: 'ping', c: ++this.pingSeq });
        }, 1000);
        break;
      case 'pong':
        if (m.c === this.pingSeq) this.rtt = Math.round(performance.now() - this.pingAt);
        break;
      case 'joined': this.code = m.code; this.cfg = m.cfg; break;
      case 'room': this.seats = m.seats; break;
      case 'start': this.seats = m.seats; break;
    }
    this.emit(m.t, m);
  }

  // 프로토콜 §3 — 클라이언트가 보낼 수 있는 것 전부
  create(cfg) { this.send({ t: 'create', cfg }); }
  join(code) { this.send({ t: 'join', room: code }); }
  takeSeat(i, kind, name, lv) { this.send({ t: 'seat', i, kind, name, lv: lv || '' }); }
  dropSeat(i) { this.send({ t: 'unseat', i }); }
  setReady(v) { this.send({ t: 'ready', v: !!v }); }
  startRound() { this.send({ t: 'start' }); }
  attack(i, n) { this.send({ t: 'atk', i, n }); }
  report(i, b, s) { this.send({ t: 'st', i, b, s }); }
  died(i) { this.send({ t: 'ko', i }); }
  mySeats() { return this.seats.filter((s) => s.pid === this.pid).map((s) => s.i); }
}

// 오류 코드 → 사람이 읽는 말. 프로토콜은 코드만 보내고 번역은 여기서 한다(§9).
const ERR_KO = {
  ver: '서버와 프로토콜 버전이 다릅니다',
  phase: '지금은 할 수 없는 동작입니다',
  seat: '그 자리는 쓸 수 없습니다',
  full: '이 PC 는 이미 2석을 쥐고 있습니다',
  own: '내 좌석이 아닙니다',
  host: '방장만 할 수 있습니다',
  ready: '아직 준비하지 않은 사람이 있습니다',
  nosuch: '그런 방 코드가 없습니다',
  inroom: '이미 방에 들어와 있습니다',
  hello: '먼저 접속 인사를 해야 합니다',
  bad: '메시지를 이해하지 못했습니다',
};
