// match.js — 한 판이 도는 동안의 클라이언트 루프. 브라우저에서 도는 코드의 심장이다.
//
// 하는 일은 프레임마다 딱 다섯 가지다.
//   1. ng_update — 내 좌석들의 wasm 을 dt 만큼 진행시킨다
//   2. ng_step   — AI 좌석이면 한 수 둘 때가 됐는지 본다
//   3. atk       — 쌓인 공격이 있으면 서버로 보낸다
//   4. st        — 10Hz 로 내 화면을 접어서 보낸다
//   5. ko        — 죽었으면 알린다
// 남의 판은 서버가 중계해 준 st 를 그대로 그린다 — 계산하지 않는다.
//
// 이 구조의 핵심은 **내 판은 내 PC 에서만 돈다**는 것이다. 서버는 규칙을 다시 돌리지 않고,
// 다른 PC 의 입력이 내 판에 영향을 주는 경로는 오직 가비지 줄 수 하나뿐이다.
// 그래서 지연이 200ms 여도 내 조작은 0ms 다.

const ST_HZ = 10;                       // 화면 중계 빈도. 8석 × 10Hz ≈ 7KB/s (§6)

class Match {
  constructor(opt) {
    this.client = opt.client;
    this.arena = opt.arena;
    this.wasmB64 = opt.wasmB64;
    this.weights = opt.weights;
    this.keys = opt.keys || null;
    this.pads = opt.pads || null;
    this.cfg = opt.cfg || { delay: 900, cap: 8 };
    this.seats = new Map();             // 내 좌석만. 남의 좌석은 arena.remote 에 있다
    this.raf = 0; this.last = 0; this.stAcc = 0;
    this.onEnd = opt.onEnd || (() => {});
    this.running = false;
  }

  // startMsg = 서버의 start. plan = [{i, kind, lv, slot}] — 내 좌석을 어떻게 굴릴지.
  async begin(startMsg, plan) {
    this.stop();
    this.seats.clear();
    const seed = startMsg.seed >>> 0;
    for (const p of plan) {
      // 모든 좌석이 **같은 시드**를 쓴다. 조각 순서가 같아야 대전이 공평하다.
      const core = await loadNet(this.wasmB64, seed);
      core.e.ng_set_delay(this.cfg.delay | 0);
      core.e.ng_set_cap(this.cfg.cap | 0);
      const seat = new Seat(p.i, core, p.kind, p.name || '', p.lv);
      if (p.kind === 'ai') makeAiSeat(seat, p.lv || 'hard', this.weights);
      else if (this.keys) this.keys.bind(p.slot | 0, seat);
      if (p.kind === 'human' && this.pads) this.pads.bind(p.slot | 0, seat);
      this.seats.set(p.i, seat);
      this.arena.attach(p.i, core);
    }
    this.arena.setSeats(startMsg.seats.map((s) => ({ ...s, alive: true, place: 0 })),
                        [...this.seats.keys()]);
    this.arena.banner = '';
    this.running = true;
    this.last = performance.now();
    this.raf = requestAnimationFrame((t) => this.frame(t));
  }

  stop() {
    if (this.raf) cancelAnimationFrame(this.raf);
    this.raf = 0; this.running = false;
  }

  // 서버가 배달한 가비지. 구멍 위치까지 서버가 정해 줬으므로
  // 관전 중인 다른 PC 도 똑같은 판을 그리게 된다.
  onGarbage(m) {
    const seat = this.seats.get(m.i);
    if (seat && seat.alive) { seat.core.e.ng_queue(m.n, m.from, m.hole); seat.core.refresh(); }
    this.arena.onGarbage(m.i, m.n, m.from);
  }
  onState(m) { if (!this.seats.has(m.i)) this.arena.onState(m.i, m.b, m.s); }
  onKo(m) { this.arena.onKo(m.i, m.place); const s = this.seats.get(m.i); if (s) s.alive = false; }
  onEndMsg(m) {
    this.stop();
    const mineBest = [...this.seats.keys()].map((i) => m.order.indexOf(i) + 1).filter((x) => x > 0);
    const place = mineBest.length ? Math.min(...mineBest) : 0;
    this.arena.banner = place === 1 ? '🏆 우승!' : place ? `${place}등` : '관전 종료';
    for (const [i, s] of this.seats) { s.alive = false; this.arena.onKo(i, m.order.indexOf(i) + 1); }
    this.arena.draw();
    this.onEnd(m);
  }

  frame(t) {
    if (!this.running) return;
    let dt = t - this.last;
    this.last = t;
    if (dt > 100) dt = 100;               // 탭을 다시 열었을 때 거대한 dt 를 막는다
    if (this.pads) this.pads.poll();

    for (const [i, seat] of this.seats) {
      if (!seat.alive) continue;
      const core = seat.core;
      core.e.ng_update(Math.round(dt));
      core.refresh();
      if (seat.kind === 'ai') stepAi(seat, dt);
      const atk = core.e.ng_take_attack();
      if (atk > 0) this.client.attack(i, atk);
      if (core.views.stats[ST.STATE] === STATE.OVER) {
        seat.alive = false;
        this.client.died(i);
      }
    }
    this.stAcc += dt;
    if (this.stAcc >= 1000 / ST_HZ) {
      this.stAcc = 0;
      for (const [i, seat] of this.seats) {
        if (seat.core) this.client.report(i, snapshot(seat.core), packState(seat.core));
      }
    }
    this.arena.draw();
    this.raf = requestAnimationFrame((x) => this.frame(x));
  }
}

// 클라이언트 한 벌을 통째로 배선한다. app.js(진짜 페이지)와 demo.js(이 문서 안)가
// 둘 다 이 함수를 쓴다 — 두 곳의 동작이 갈리지 않게 하는 가장 싼 방법이다.
function wireMatch(client, match) {
  client.on('grb', (m) => match.onGarbage(m));
  client.on('st', (m) => match.onState(m));
  client.on('ko', (m) => match.onKo(m));
  client.on('end', (m) => match.onEndMsg(m));
  return match;
}
