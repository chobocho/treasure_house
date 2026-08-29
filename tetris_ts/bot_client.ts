// bot_client.ts — 진짜 웹소켓으로 서버에 붙는 헤드리스 봇.
//
//   node dist/bot_client.js --match                8인 실측 대전(서버까지 이 프로세스가 띄운다)
//   node dist/bot_client.js --url ws://호스트:포트/ws --room ABCD --seats 2
//
// 브라우저 없이 8인 대전을 끝까지 돌려 보기 위한 물건이다. 덱에 싣는 순위표는
// 여기서 나온 **실제 출력**이지 지어낸 표가 아니다.
//
// 클라이언트 쪽 웹소켓은 Node 24 의 표준 WebSocket 전역을 쓴다. 우리가 직접 쓴 건
// 서버(ws.ts)뿐이다 — 양쪽 다 우리 구현이면 "우리끼리만 말이 통하는" 상태를
// 검증할 수 없다. 남의 클라이언트가 붙어야 핸드셰이크와 프레이밍이 증명된다.

import { Tetris, ST, STATE } from './src/core.js';
import { Ai, DEFAULT_WEIGHTS } from './src/ai.js';
import { snapshot, packState, PROTOCOL_VERSION, type RoomCfg, type ServerMsg } from './src/net/protocol.js';
import { createServer } from './src/net/server.js';

/** 난이도 프리셋 — weights.json 의 levels 와 같은 이름을 쓴다. */
export type Level = 'easy' | 'normal' | 'hard' | 'max';

/** 봇 좌석 하나. */
interface BotSeat {
  i: number;
  name: string;
  lv: Level;
  weights: readonly number[];
  intervalMs: number;
  game: Tetris;
  ai: Ai;
  acc: number;
  lastEvent: number;
  alive: boolean;
  sent: number;
  recv: number;
}

export interface BotOptions {
  url: string;
  name: string;
  seats: { name: string; lv: Level; weights: readonly number[]; intervalMs: number }[];
  /** 방을 만들 것인가(방장), 아니면 코드로 들어갈 것인가 */
  create?: RoomCfg | Partial<RoomCfg>;
  room?: string;
  /** 한 틱(ms). 브라우저의 rAF 대신 이 주기로 시간을 흘린다. */
  tickMs?: number;
  quiet?: boolean;
  /** 화면 상태를 보내는 주기(ms). 규격 권장은 초당 10회. */
  stMs?: number;
}

/**
 * PC 한 대(= 웹소켓 연결 하나) 몫의 봇.
 *
 * 규격상 한 연결은 좌석 2개까지 쥘 수 있다. 4대 × 2석 = 8석이 최대 구성이고,
 * `--match` 가 정확히 그 구성을 만든다.
 */
export class BotPeer {
  readonly ws: WebSocket;
  readonly seats: BotSeat[] = [];
  code = '';
  pid = 0;
  cfg: RoomCfg | null = null;
  started = false;
  finished = false;
  order: number[] = [];
  /**
   * 마지막 room 브로드캐스트의 좌석 목록.
   *
   * 사건(onRoom)만으로 자리가 찼는지 보면 안 된다 — 늦게 붙는 PC 를 기다리는 사이
   * 이미 지나간 브로드캐스트를 놓쳐서 "좌석이 다 안 찼다"로 영영 멈춘다.
   * 그래서 상태로 들고 있고, 기다리는 쪽이 먼저 현재 값을 본 뒤 사건을 건다.
   */
  roomSeats: { i: number; pid: number }[] = [];
  /**
   * 실측 트래픽. 세는 건 JSON 본문 바이트뿐이고 웹소켓 프레임 헤더(2~14바이트)와
   * TCP/IP 헤더는 빼고 센다 — 덱에 "PC 한 대당 몇 KB/s" 를 적을 때 이 기준을 밝힌다.
   */
  up = 0;
  down = 0;
  msgUp = 0;
  msgDown = 0;
  /** 보낸 공격 횟수 / 받은 가비지 소포 수. 둘의 총합이 맞아야 라우팅이 샌 데가 없다. */
  atkCount = 0;
  grbCount = 0;
  /** 방 전체의 탈락 기록(꼴찌부터). 브로드캐스트라 어느 PC 가 봐도 같아야 한다. */
  readonly kos: { i: number; place: number; by: number }[] = [];
  private timer: ReturnType<typeof setInterval> | null = null;
  private stAcc = 0;
  private readonly log: (...a: unknown[]) => void;

  onRoom: ((seats: { i: number; pid: number }[]) => void) | null = null;
  onEnd: ((order: number[]) => void) | null = null;

  constructor(readonly opts: BotOptions) {
    this.log = opts.quiet ? (): void => {} : (...a: unknown[]): void => console.log(...a);
    this.ws = new WebSocket(opts.url);
    this.ws.addEventListener('open', () => {
      this.send({ t: 'hello', v: PROTOCOL_VERSION, name: opts.name });
    });
    this.ws.addEventListener('message', (e) => {
      const raw = String((e as MessageEvent).data);
      this.down += Buffer.byteLength(raw);
      this.msgDown++;
      this.onMsg(JSON.parse(raw) as ServerMsg);
    });
  }

  private send(m: unknown): void {
    if (this.ws.readyState !== WebSocket.OPEN) return;
    const s = JSON.stringify(m);
    this.up += Buffer.byteLength(s);
    this.msgUp++;
    this.ws.send(s);
  }

  /** 접속·입장이 끝날 때까지 기다린다. */
  ready(): Promise<void> {
    return new Promise((resolve, reject) => {
      const t = setTimeout(() => reject(new Error(`${this.opts.name}: 입장 시간 초과`)), 10000);
      const check = (): void => {
        if (this.code) { clearTimeout(t); resolve(); return; }
        setTimeout(check, 10);
      };
      check();
    });
  }

  /** 좌석이 n 개 찰 때까지 기다린다. 이미 차 있으면 곧바로 돌아온다. */
  waitSeats(n: number, timeoutMs = 10000): Promise<void> {
    if (this.roomSeats.length >= n) return Promise.resolve();
    return new Promise((resolve, reject) => {
      const t = setTimeout(
        () => reject(new Error(`좌석이 다 안 찼다 (${this.roomSeats.length}/${n})`)),
        timeoutMs,
      );
      this.onRoom = (seats): void => {
        if (seats.length < n) return;
        clearTimeout(t);
        this.onRoom = null;
        resolve();
      };
    });
  }

  /** 경기가 끝날 때까지 기다려 등수 순 좌석을 준다. 이미 끝났으면 곧바로. */
  waitEnd(timeoutMs = 5 * 60 * 1000): Promise<number[]> {
    if (this.finished) return Promise.resolve(this.order);
    return new Promise((resolve, reject) => {
      const t = setTimeout(() => reject(new Error('경기가 안 끝난다')), timeoutMs);
      this.onEnd = (o): void => { clearTimeout(t); this.onEnd = null; resolve(o); };
    });
  }

  private onMsg(m: ServerMsg): void {
    switch (m.t) {
      case 'hi':
        this.pid = m.pid;
        if (this.opts.create) this.send({ t: 'create', cfg: this.opts.create });
        else this.send({ t: 'join', room: this.opts.room });
        return;

      case 'joined': {
        this.code = m.code;
        this.cfg = m.cfg;
        // 좌석을 잡는다. i 를 지정하지 않고 빈 자리를 자동 배정받는다 —
        // 어느 PC 가 어느 번호를 갖는지는 붙는 순서가 정한다.
        for (const s of this.opts.seats) {
          this.send({ t: 'seat', i: -1, kind: 'ai', name: s.name, lv: s.lv });
        }
        this.send({ t: 'ready', v: true });
        return;
      }

      case 'room':
        this.roomSeats = m.seats;
        this.onRoom?.(m.seats);
        return;

      case 'start': {
        // 규격 §4: seed 하나를 전원이 공유한다. 조각 운이 갈리면 실력 겨루기가 안 된다.
        const mine = m.seats.filter((s) => s.pid === this.pid);
        this.seats.length = 0;
        mine.forEach((s, k) => {
          const spec = this.opts.seats[k] ?? this.opts.seats[0]!;
          const game = new Tetris(m.seed >>> 0);
          this.seats.push({
            i: s.i, name: s.name, lv: spec.lv, weights: spec.weights,
            intervalMs: spec.intervalMs, game, ai: new Ai(game, spec.weights),
            acc: 0, lastEvent: game.stats[ST.EVENT] as number, alive: true, sent: 0, recv: 0,
          });
        });
        this.started = true;
        this.log(`  ${this.opts.name}: 좌석 ${this.seats.map((s) => s.i).join(',')} 시작 (시드 ${m.seed >>> 0})`);
        this.startLoop();
        return;
      }

      case 'grb': {
        const seat = this.seats.find((s) => s.i === m.i);
        if (!seat || !seat.alive) return;
        seat.recv += m.n;
        this.grbCount++;
        // 규격의 유예(cfg.delay)를 지키는 건 서버가 아니라 **클라이언트**다.
        // 그래야 맞은 쪽이 상쇄할 시간을 갖는다.
        //
        // 서버가 실어 보낸 hole 은 쓰지 않는다. 코어의 pushRows 가 자기 RNG 로
        // 구멍을 고르고, 관전 화면은 어차피 내가 보내는 스냅샷을 그대로 그리므로
        // 어긋날 데가 없다. hole 은 공격 연출용 정보다.
        setTimeout(() => {
          if (seat.alive) seat.game.queueGarbage(m.n);
        }, this.cfg?.delay ?? 900);
        return;
      }

      case 'ko': {
        const seat = this.seats.find((s) => s.i === m.i);
        if (seat) seat.alive = false;
        this.kos.push({ i: m.i, place: m.place, by: m.by });
        // 탈락은 방 전체에 뿌려진다. 네 대가 다 찍으면 같은 줄이 네 번 나오므로
        // 자기 좌석일 때만 찍는다 — 로그 한 줄 = 실제 탈락 한 번.
        if (seat) this.log(`  KO 좌석 ${m.i} → ${m.place}등 (막타 ${m.by < 0 ? '자멸' : `좌석 ${m.by}`})`);
        return;
      }

      case 'end':
        this.order = m.order;
        this.finished = true;
        this.stopLoop();
        this.onEnd?.(m.order);
        return;

      case 'err':
        this.log(`  ${this.opts.name}: 오류 ${m.code}`);
        return;

      default:
        return;
    }
  }

  private startLoop(): void {
    if (this.timer) return;
    const tick = this.opts.tickMs ?? 50;
    this.timer = setInterval(() => this.tick(tick), tick);
  }

  private stopLoop(): void {
    if (this.timer) clearInterval(this.timer);
    this.timer = null;
  }

  /** 한 틱: 좌석마다 AI 를 돌리고, 공격·상태·사망을 서버에 보고한다. */
  private tick(dtMs: number): void {
    if (!this.started || this.finished) return;
    for (const s of this.seats) {
      if (!s.alive) continue;
      s.acc += dtMs;
      while (s.acc >= s.intervalMs && (s.game.stats[ST.STATE] as number) === STATE.PLAY) {
        s.acc -= s.intervalMs;
        s.ai.step();
        const ev = s.game.stats[ST.EVENT] as number;
        if (ev !== s.lastEvent) {
          s.lastEvent = ev;
          const atk = s.game.stats[ST.ATTACK] as number;
          if (atk > 0) {
            s.sent += atk;
            this.atkCount++;
            this.send({ t: 'atk', i: s.i, n: atk });
          }
        }
      }
      if ((s.game.stats[ST.STATE] as number) !== STATE.PLAY) {
        s.alive = false;
        this.send({ t: 'ko', i: s.i });
      }
    }

    this.stAcc += dtMs;
    const stEvery = this.opts.stMs ?? 100;
    if (this.stAcc >= stEvery) {
      this.stAcc = 0;
      for (const s of this.seats) {
        if (!s.alive) continue;
        this.send({ t: 'st', i: s.i, b: snapshot(s.game), s: packState(s.game) });
      }
    }
  }

  /** 방장이 경기를 시작한다. 좌석이 다 찬 뒤에 부를 것. */
  start(): void {
    this.send({ t: 'start' });
  }

  close(): void {
    this.stopLoop();
    try { this.ws.close(); } catch { /* 이미 닫혔으면 그만 */ }
  }

  summary(): { i: number; name: string; lv: Level; sent: number; recv: number; lines: number; score: number }[] {
    return this.seats.map((s) => ({
      i: s.i, name: s.name, lv: s.lv, sent: s.sent, recv: s.recv,
      lines: s.game.stats[ST.LINES] as number,
      score: s.game.stats[ST.SCORE] as number,
    }));
  }
}

// ── make match: PC 4대 × 좌석 2석 = 8석 실측 대전 ──────────────────────

/** weights.json 의 난이도 프리셋. 없으면 학습된 기본값으로 4종을 만든다. */
async function loadLevels(): Promise<Record<Level, readonly number[]>> {
  const { readFile } = await import('node:fs/promises');
  const { fileURLToPath } = await import('node:url');
  const { dirname, join } = await import('node:path');
  const root = join(dirname(fileURLToPath(import.meta.url)), '..');
  try {
    const j = JSON.parse(await readFile(join(root, 'weights.json'), 'utf8')) as {
      levels: Record<Level, number[]>;
    };
    return j.levels;
  } catch {
    return { easy: DEFAULT_WEIGHTS, normal: DEFAULT_WEIGHTS, hard: DEFAULT_WEIGHTS, max: DEFAULT_WEIGHTS };
  }
}

const SEAT_NAMES = ['보라', '다온', '아라', '해든', '나린', '가온', '시우', '지호'];

export interface MatchResult {
  order: number[];
  seats: { i: number; name: string; lv: Level; sent: number; recv: number; lines: number; score: number }[];
  ms: number;
  /** 실측 트래픽 합계(JSON 본문 바이트 기준, 프레임 헤더 제외) */
  net: { up: number; down: number; msgUp: number; msgDown: number; pcs: number };
  /** 공격 횟수 / 가비지 배달 횟수 */
  atk: number;
  grb: number;
  /** 탈락 기록(꼴찌부터) — 누가 몇 등으로, 누구의 막타에 죽었는가 */
  kos: { i: number; place: number; by: number }[];
}

/** 서버를 띄우고 봇을 붙여 끝까지 돌린다. 기본 구성은 PC 4대 × 2석 = 8석. */
export async function runMatch(opts: {
  port?: number;
  target?: RoomCfg['target'];
  quiet?: boolean;
  tickMs?: number;
  /** PC(= 웹소켓 연결) 수. 규격상 한 PC 가 쥘 수 있는 좌석은 perPc 까지다. */
  pcs?: number;
  perPc?: number;
  /**
   * 착수 간격 배율. 1 이 실시간이고 작을수록 빨리 둔다.
   *
   * 규칙은 그대로 두고 시계만 당기는 손잡이다. 테스트는 0.1 쯤으로 돌려 한 판을
   * 몇 초에 끝낸다 — 실측 대전(`make match`)은 1 로 두어야 사람이 보는 속도와 같다.
   */
  speed?: number;
} = {}): Promise<MatchResult> {
  const levels = await loadLevels();
  const quiet = opts.quiet ?? false;
  const log = quiet ? (): void => {} : (...a: unknown[]): void => console.log(...a);
  const pcs = Math.max(1, opts.pcs ?? 4);
  const perPc = Math.max(1, opts.perPc ?? 2);
  const total = pcs * perPc;
  const speed = opts.speed ?? 1;

  const srv = createServer({ quiet: true, seed: 0xc0ffee, webRoot: '/dev/null' });
  const port = await srv.listen(opts.port ?? 0);
  const url = `ws://127.0.0.1:${port}/ws`;
  log(`서버 기동 — ${url}`);

  // 난이도를 좌석마다 섞는다. 전원이 같은 세기면 순위표가 그냥 좌석 번호 순이 된다.
  const lvOf = (k: number): Level => (['max', 'hard', 'normal', 'easy'] as Level[])[k % 4]!;
  const intervalOf = (lv: Level): number =>
    Math.max(1, Math.round({ max: 120, hard: 160, normal: 220, easy: 300 }[lv] * speed));
  const specOf = (k: number): BotOptions['seats'][number] => {
    const lv = lvOf(k);
    return { name: SEAT_NAMES[k] ?? `봇${k + 1}`, lv, weights: levels[lv], intervalMs: intervalOf(lv) };
  };

  const peers: BotPeer[] = [];
  const t0 = Date.now();
  try {
    // PC1 이 방을 만들고 나머지는 그 코드로 들어간다. 한 대씩 순서대로 붙이는 건
    // 좌석 번호를 붙는 순서로 고정해 순위표를 재현 가능하게 두기 위해서다.
    for (let pc = 1; pc <= pcs; pc++) {
      const base = (pc - 1) * perPc;
      const p = new BotPeer({
        url, name: `PC${pc}`, quiet,
        tickMs: opts.tickMs ?? 50,
        ...(pc === 1
          ? { create: { max: total, perPeer: perPc, target: opts.target ?? 'random' } }
          : { room: peers[0]!.code }),
        seats: Array.from({ length: perPc }, (_, k) => specOf(base + k)),
      });
      peers.push(p);
      await p.ready();
      if (pc === 1) log(`방 개설 — 코드 ${p.code}`);
    }
    const host = peers[0]!;

    // 자리가 다 찰 때까지 기다렸다가 방장이 start 를 누른다.
    await host.waitSeats(total);
    log(`좌석 ${total}석 완료 — 시작`);
    host.start();

    const order = await host.waitEnd();
    // 방장이 end 를 받았다고 곧장 끊으면 안 된다. 다른 PC 의 소켓에는 아직 읽지 않은
    // ko/end 가 남아 있을 수 있고, 그대로 close 하면 마지막 탈락이 통계에서 사라진다.
    await Promise.all(peers.map((p) => p.waitEnd(5000).catch(() => undefined)));

    const seats = peers.flatMap((p) => p.summary()).sort((a, b) => a.i - b.i);
    const sum = (f: (p: BotPeer) => number): number => peers.reduce((a, p) => a + f(p), 0);
    return {
      order, seats, ms: Date.now() - t0,
      net: {
        up: sum((p) => p.up), down: sum((p) => p.down),
        msgUp: sum((p) => p.msgUp), msgDown: sum((p) => p.msgDown), pcs,
      },
      atk: sum((p) => p.atkCount),
      grb: sum((p) => p.grbCount),
      kos: host.kos.slice(),
    };
  } finally {
    for (const p of peers) p.close();
    await srv.close();
  }
}

/** 순위표를 사람이 읽을 수 있게 찍는다. */
export function printMatch(r: MatchResult): void {
  const byPlace = r.order.map((i, k) => ({ place: k + 1, ...r.seats.find((s) => s.i === i)! }));
  console.log('\n등수 | 좌석 | 이름   | 난이도  | 보낸줄 | 맞은줄 | 지운줄 | 점수');
  console.log('-----+------+--------+---------+--------+--------+--------+--------');
  for (const s of byPlace) {
    console.log(
      `${String(s.place).padStart(4)} | ${String(s.i).padStart(4)} | ${s.name.padEnd(6)} | ` +
      `${s.lv.padEnd(7)} | ${String(s.sent).padStart(6)} | ${String(s.recv).padStart(6)} | ` +
      `${String(s.lines).padStart(6)} | ${String(s.score).padStart(6)}`,
    );
  }
  const kb = (b: number): string => (b / 1024).toFixed(1) + ' KB';
  const secs = r.ms / 1000;
  console.log(`\n공격 ${r.atk}회 → 가비지 배달 ${r.grb}회`);
  console.log(
    `보냄 ${r.net.msgUp}개 / ${kb(r.net.up)}   받음 ${r.net.msgDown}개 / ${kb(r.net.down)}` +
    '  (JSON 본문 기준, 프레임 헤더 제외)',
  );
  console.log(
    `PC 1대당 평균 ${(r.net.up / r.net.pcs / secs / 1024).toFixed(2)} KB/s 업 · ` +
    `${(r.net.down / r.net.pcs / secs / 1024).toFixed(2)} KB/s 다운`,
  );
  console.log(`경기 시간 ${secs.toFixed(1)}초, 우승 좌석 ${r.order[0]}`);
}

// ── CLI ───────────────────────────────────────────────────────────────
function argStr(name: string, dflt: string): string {
  const i = process.argv.indexOf('--' + name);
  return i >= 0 ? (process.argv[i + 1] ?? dflt) : dflt;
}
function argInt(name: string, dflt: number): number {
  const v = parseInt(argStr(name, String(dflt)), 10);
  return Number.isFinite(v) ? v : dflt;
}

if (process.argv[1] && (await import('node:url')).fileURLToPath(import.meta.url) === process.argv[1]) {
  if (process.argv.includes('--match')) {
    const r = await runMatch({
      port: argInt('port', 0),
      target: argStr('target', 'random') as RoomCfg['target'],
    });
    printMatch(r);
    process.exit(0);
  } else {
    const levels = await loadLevels();
    const lv = argStr('lv', 'max') as Level;
    const n = argInt('seats', 2);
    const p = new BotPeer({
      url: argStr('url', 'ws://127.0.0.1:8787/ws'),
      name: argStr('name', '봇PC'),
      room: argStr('room', ''),
      seats: Array.from({ length: n }, (_, k) => ({
        name: SEAT_NAMES[k] ?? `봇${k}`, lv, weights: levels[lv], intervalMs: 150,
      })),
    });
    p.onEnd = (o): void => {
      console.log('종료 — 등수 순 좌석:', o.join(', '));
      p.close();
      process.exit(0);
    };
  }
}
