// room.mjs — 방 하나의 게임 규칙. **순수 상태 기계**다.
//
// 이 파일에는 소켓도, 타이머도, Date.now() 도 없다. 바깥에서 (pid, 메시지, now) 를
// 넣으면 (누구에게, 무엇을) 목록이 나온다. 그게 전부다.
// 그렇게 만든 이유는 하나다 — Go·파이썬 구현과 **같은 골든 벡터**로 검증하기 위해서.
// 시계나 난수를 스스로 읽는 순간 그 검증이 불가능해진다.
//
// 규격 전문은 protocol.md, 검증표는 protocol_vectors.json.

export const DEFAULTS = {
  max: 8,        // 좌석 수
  perPeer: 2,    // PC 1대가 쥘 수 있는 좌석 수 — "한 PC 에서 최대 2명"이 여기 한 줄이다
  target: 'random',
  delay: 900,    // 가비지 유예(ms). 서버는 중계만 하고 지키는 건 클라이언트다
  cap: 8,        // 한 락에서 솟을 수 있는 최대 줄
  hitTTL: 8000,  // "최근에 나를 때렸다"로 치는 시간
};

export class Room {
  constructor(cfg = {}, seed = 1) {
    this.cfg = { ...DEFAULTS, ...cfg };
    const n = this.cfg.max;
    this.seats = new Array(n).fill(null);
    this.phase = 'lobby';
    this.peers = new Set();
    this.state = new Array(n).fill(0);   // 좌석별 부가 상태
    this.rngState = (seed >>> 0) || 1;
    this.roundSeed = 0;
  }

  // 규격의 xorshift32. 세 구현이 여기서부터 갈리면 그 뒤는 볼 것도 없다.
  rng() {
    let x = this.rngState >>> 0;
    x ^= (x << 13) >>> 0; x >>>= 0;
    x ^= x >>> 17;
    x ^= (x << 5) >>> 0;  x >>>= 0;
    this.rngState = x;
    return x;
  }

  // ── 조회 헬퍼 ──
  host() { let h = 0; for (const p of this.peers) if (!h || p < h) h = p; return h; }
  occupied() { const o = []; for (let i = 0; i < this.seats.length; i++) if (this.seats[i]) o.push(i); return o; }
  aliveSeats() { return this.occupied().filter((i) => this.seats[i].alive); }
  mine(pid) { return this.occupied().filter((i) => this.seats[i].pid === pid); }

  // 로비에 뿌리는 좌석 목록. 내부 필드(recv/hits/height/place)는 내보내지 않는다.
  seatList() {
    return this.occupied().map((i) => {
      const s = this.seats[i];
      return { i, pid: s.pid, name: s.name, kind: s.kind, lv: s.lv, ready: s.ready, alive: s.alive };
    });
  }
  roomMsg()  { return [{ to: 0, m: { t: 'room', host: this.host(), seats: this.seatList() } }]; }
  err(pid, code) { return [{ to: pid, m: { t: 'err', code } }]; }

  // ── 진입점 ──
  handle(pid, msg, now) {
    const t = msg && msg.t;
    if (t === 'bye') return this.onBye(pid, now);
    this.peers.add(pid);
    switch (t) {
      case 'seat':   return this.onSeat(pid, msg);
      case 'unseat': return this.onUnseat(pid, msg);
      case 'ready':  return this.onReady(pid, msg);
      case 'start':  return this.onStart(pid);
      case 'atk':    return this.onAtk(pid, msg, now);
      case 'st':     return this.onSt(pid, msg);
      case 'ko':     return this.onKo(pid, msg, now);
      default:       return [];
    }
  }

  onSeat(pid, m) {
    if (this.phase !== 'lobby') return this.err(pid, 'phase');
    let i = (m.i === undefined || m.i === null) ? -1 : m.i | 0;
    if (i < 0) {                                   // 자동 배정 = 가장 앞의 빈 자리
      i = this.seats.findIndex((s) => s === null);
      if (i < 0) return this.err(pid, 'seat');
    } else if (i >= this.seats.length || this.seats[i]) {
      return this.err(pid, 'seat');
    }
    // 자리를 먼저 확정하고 그다음에 PC 당 좌석 수를 본다. 순서를 바꾸면
    // "빈 자리도 없고 내 몫도 찼을 때" 어느 오류가 나가는지가 구현마다 달라진다.
    if (this.mine(pid).length >= this.cfg.perPeer) return this.err(pid, 'full');
    this.seats[i] = {
      pid, name: m.name || '', kind: m.kind === 'ai' ? 'ai' : 'human', lv: m.lv || '',
      ready: false, alive: true, recv: 0, height: 0, place: 0, hits: [],
    };
    return this.roomMsg();
  }

  onUnseat(pid, m) {
    if (this.phase !== 'lobby') return this.err(pid, 'phase');
    const i = m.i | 0;
    if (i < 0 || i >= this.seats.length || !this.seats[i] || this.seats[i].pid !== pid)
      return this.err(pid, 'own');
    this.seats[i] = null;
    return this.roomMsg();
  }

  onReady(pid, m) {
    if (this.phase !== 'lobby') return this.err(pid, 'phase');
    const v = !!m.v;
    for (const i of this.mine(pid)) this.seats[i].ready = v;
    return this.roomMsg();
  }

  onStart(pid) {
    if (this.phase !== 'lobby') return this.err(pid, 'phase');
    if (pid !== this.host()) return this.err(pid, 'host');
    const occ = this.occupied();
    if (!occ.length) return this.err(pid, 'seat');
    // AI 좌석은 준비를 기다리지 않는다 — 누를 사람이 없다.
    for (const i of occ) if (this.seats[i].kind === 'human' && !this.seats[i].ready) return this.err(pid, 'ready');

    this.roundSeed = this.rng();
    this.phase = 'play';
    for (const i of occ) {
      const s = this.seats[i];
      s.alive = true; s.recv = 0; s.height = 0; s.place = 0; s.hits = [];
    }
    return [{ to: 0, m: { t: 'start', seed: this.roundSeed, seats: this.seatList() } }];
  }

  // ── 공격 라우팅 — 이 게임에서 서버가 하는 유일한 판단 ──
  pickTarget(from, now) {
    const cand = this.aliveSeats().filter((j) => j !== from);
    if (!cand.length) return -1;
    const mode = this.cfg.target;
    if (mode === 'even') {                       // 가장 덜 맞은 쪽 — 난수를 쓰지 않는다
      let best = cand[0];
      for (const j of cand) if (this.seats[j].recv < this.seats[best].recv) best = j;
      return best;
    }
    if (mode === 'ko') {                         // 가장 높이 쌓인 쪽 = 죽기 직전
      let best = cand[0];
      for (const j of cand) if (this.seats[j].height > this.seats[best].height) best = j;
      return best;
    }
    if (mode === 'attackers') {                  // 최근에 나를 때린 쪽에 반격
      const hits = this.seats[from].hits;
      for (let k = hits.length - 1; k >= 0; k--) {
        const h = hits[k];
        if (now - h.at > this.cfg.hitTTL) break; // hits 는 시간순이라 여기서 끊으면 된다
        if (h.from !== from && this.seats[h.from] && this.seats[h.from].alive) return h.from;
      }
      // 기억이 없으면 random 으로 떨어진다 — 이때만 난수를 쓴다
    }
    return cand[this.rng() % cand.length];
  }

  onAtk(pid, m, now) {
    if (this.phase !== 'play') return this.err(pid, 'phase');
    const i = m.i | 0;
    if (i < 0 || i >= this.seats.length || !this.seats[i]) return this.err(pid, 'own');
    if (this.seats[i].pid !== pid) return this.err(pid, 'own');
    const n = m.n | 0;
    if (n <= 0 || !this.seats[i].alive) return [];

    const j = this.pickTarget(i, now);
    if (j < 0) return [];                        // 혼자 남았거나 1인용 — 공격은 허공으로
    const hole = this.rng() % 10;
    const tgt = this.seats[j];
    tgt.recv += n;
    tgt.hits.push({ from: i, at: now });
    // 관전 화면이 "누가 누구를" 화살표로 그려야 하므로 피해자에게만 보내지 않는다.
    return [{ to: 0, m: { t: 'grb', i: j, n, from: i, hole } }];
  }

  onSt(pid, m) {
    if (this.phase !== 'play') return this.err(pid, 'phase');
    const i = m.i | 0;
    if (i < 0 || i >= this.seats.length || !this.seats[i] || this.seats[i].pid !== pid)
      return this.err(pid, 'own');
    const s = Array.isArray(m.s) ? m.s : [];
    if (s.length > 4) this.seats[i].height = s[4] | 0;   // 서버가 읽는 칸은 s[0], s[4] 뿐
    const out = [];
    for (const p of [...this.peers].sort((a, b) => a - b)) {
      if (p !== pid) out.push({ to: p, m: { t: 'st', i, b: m.b, s: m.s } });
    }
    return out;
  }

  // 좌석 하나를 탈락시킨다. end 까지 낼 수 있으므로 out 을 받아 이어 붙인다.
  kill(i, now, out) {
    if (this.phase !== 'play') return;
    const s = this.seats[i];
    if (!s || !s.alive) return;
    const place = this.aliveSeats().length;     // 지금 살아 있는 수 = 그대로 등수
    s.alive = false;
    s.place = place;
    let by = -1;
    for (let k = s.hits.length - 1; k >= 0; k--) {
      if (now - s.hits[k].at > this.cfg.hitTTL) break;
      if (s.hits[k].from !== i) { by = s.hits[k].from; break; }
    }
    out.push({ to: 0, m: { t: 'ko', i, place, by } });

    const left = this.aliveSeats();
    if (left.length <= 1) {
      if (left.length === 1) this.seats[left[0]].place = 1;
      this.phase = 'over';
      const occ = this.occupied().slice().sort((a, b) => this.seats[a].place - this.seats[b].place);
      out.push({ to: 0, m: { t: 'end', order: occ } });
    }
  }

  onKo(pid, m, now) {
    if (this.phase !== 'play') return this.err(pid, 'phase');
    const i = m.i | 0;
    if (i < 0 || i >= this.seats.length || !this.seats[i] || this.seats[i].pid !== pid)
      return this.err(pid, 'own');
    const out = [];
    this.kill(i, now, out);
    return out;
  }

  // PC 가 끊겼다. 로비면 자리를 비우고, 대전 중이면 그 PC 의 좌석이 번호 순으로 전멸한다.
  onBye(pid, now) {
    if (!this.peers.has(pid)) return [];
    this.peers.delete(pid);
    const held = this.mine(pid);
    if (this.phase === 'play') {
      const out = [];
      for (const i of held) this.kill(i, now, out);   // kill() 이 phase 를 over 로 바꾸면 뒤는 무시된다
      return out;
    }
    for (const i of held) this.seats[i] = null;
    return this.roomMsg();                            // 방장이 바뀔 수 있으므로 항상 알린다
  }
}
