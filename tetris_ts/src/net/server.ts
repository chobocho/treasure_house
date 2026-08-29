// server.ts — 8인 온라인 서버. web/ 정적 파일 + /ws 엔드포인트.
//
//   node dist/src/net/server.js --port 8787
//
// 층이 셋이다. 아래로 갈수록 순수해진다.
//   Server : 소켓·파일·시계를 만지는 유일한 층 (이 파일의 아래쪽 절반)
//   Hub    : 방 코드·pid 배정·라우팅. 소켓은 모르고 메시지만 안다
//   Room   : 게임 규칙. 시계도 난수도 주입받는 순수 상태 기계 (room.ts)
//
// Hub 를 소켓에서 떼어 놓은 덕에 "8명이 붙었다 나갔다" 하는 시나리오를
// 소켓 없이 테스트로 재현할 수 있다.

import { createServer as createHttpServer, type IncomingMessage, type ServerResponse } from 'node:http';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { dirname, join, normalize, extname } from 'node:path';

import { Room } from './room.js';
import { upgrade, type WsConn } from './ws.js';
import {
  PROTOCOL_VERSION, mergeCfg,
  type ClientMsg, type ServerMsg, type Outbound,
} from './protocol.js';

// ── 허브 ──────────────────────────────────────────────────────────────

/** 방 코드에 쓰는 글자. 헷갈리는 0/O/1/I/L 을 뺐다 — 코드를 전화로 불러 줘야 한다. */
const CODE_ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789';
export const CODE_LEN = 4;

export interface HubPeer {
  pid: number;
  name: string;
  /** hello 를 마쳤는가 */
  greeted: boolean;
  /** 들어가 있는 방 코드. 없으면 '' */
  room: string;
}

/**
 * 방 코드·pid 배정·라우팅.
 *
 * 소켓을 모른다. handle() 은 **받는 사람이 확정된** 메시지 목록을 돌려주므로
 * 바깥 층은 그대로 write 하기만 하면 된다 (to === 0 을 여기서 이미 풀어 준다).
 */
export class Hub {
  readonly peers = new Map<number, HubPeer>();
  readonly rooms = new Map<string, Room>();
  private nextPid = 1;
  private rngState: number;

  constructor(seed = 0x1234abcd) {
    this.rngState = (seed >>> 0) || 1;
  }

  private rng(): number {
    let x = this.rngState >>> 0;
    x ^= x << 13; x >>>= 0;
    x ^= x >>> 17;
    x ^= x << 5; x >>>= 0;
    this.rngState = x;
    return x;
  }

  /** 안 쓰는 방 코드 하나. 충돌하면 다시 뽑는다. */
  newCode(): string {
    for (let tries = 0; tries < 1000; tries++) {
      let c = '';
      for (let i = 0; i < CODE_LEN; i++) c += CODE_ALPHABET[this.rng() % CODE_ALPHABET.length];
      if (!this.rooms.has(c)) return c;
    }
    throw new Error('방 코드가 동났다');
  }

  connect(): number {
    const pid = this.nextPid++;
    this.peers.set(pid, { pid, name: '', greeted: false, room: '' });
    return pid;
  }

  /** 방 하나의 접속자들. to === 0 을 풀 때 쓴다. */
  private roomPeers(code: string): number[] {
    const out: number[] = [];
    for (const p of this.peers.values()) if (p.room === code) out.push(p.pid);
    return out.sort((a, b) => a - b);
  }

  /** room 이 낸 {to:0} 브로드캐스트를 실제 받는 사람들로 펼친다. */
  private fan(code: string, outs: Outbound[]): Outbound[] {
    const res: Outbound[] = [];
    for (const o of outs) {
      if (o.to !== 0) { res.push(o); continue; }
      for (const pid of this.roomPeers(code)) res.push({ to: pid, m: o.m });
    }
    return res;
  }

  private one(pid: number, m: ServerMsg): Outbound[] {
    return [{ to: pid, m }];
  }

  /**
   * 메시지 하나를 처리한다.
   *
   * 분기 순서가 규격이다 — 부 3 의 Go·파이썬 허브와 **같은 순서**로 본다:
   *   hello → (인사 안 했으면 err hello) → ping → create/join → (방 없으면 err nosuch) → room
   * 순서를 바꾸면 "인사 전에 ping" 같은 경우에 다른 오류가 나가고,
   * 기존 클라이언트가 그 차이에 걸린다.
   */
  handle(pid: number, msg: ClientMsg, now: number): Outbound[] {
    const peer = this.peers.get(pid);
    if (!peer) return [];
    if (!msg || typeof msg.t !== 'string') return [];

    if (msg.t === 'hello') {
      // 버전이 다르면 여기서 끝. 규격이 바뀐 클라이언트를 방에 들이면
      // 그 방의 다른 사람들까지 이상한 상태에 빠진다.
      if (msg.v !== PROTOCOL_VERSION) return this.one(pid, { t: 'err', code: 'ver' });
      peer.greeted = true;
      peer.name = msg.name ?? '';
      return this.one(pid, { t: 'hi', pid, v: PROTOCOL_VERSION });
    }
    if (!peer.greeted) return this.one(pid, { t: 'err', code: 'hello' });

    if (msg.t === 'ping') return this.one(pid, { t: 'pong', c: msg.c });

    if (msg.t === 'create' || msg.t === 'join') {
      if (peer.room) return this.one(pid, { t: 'err', code: 'inroom' });
      let code: string;
      let room: Room;
      if (msg.t === 'create') {
        const cfg = mergeCfg(msg.cfg);
        cfg.perPeer = Math.min(cfg.perPeer, cfg.max);
        code = this.newCode();
        // 방의 난수 시드는 허브의 난수에서 뽑는다. 방마다 다른 조각 순서가 나온다.
        room = new Room(cfg, this.rng());
        this.rooms.set(code, room);
      } else {
        code = String(msg.room ?? '').toUpperCase();
        const found = this.rooms.get(code);
        if (!found) return this.one(pid, { t: 'err', code: 'nosuch' });
        room = found;
      }
      peer.room = code;
      return this.one(pid, { t: 'joined', code, cfg: room.cfg, pid });
    }

    // 나머지는 전부 room 층의 메시지다.
    const room = peer.room ? this.rooms.get(peer.room) : undefined;
    if (!room) return this.one(pid, { t: 'err', code: 'nosuch' });
    return this.fan(peer.room, room.handle(pid, msg, now));
  }

  disconnect(pid: number, now: number): Outbound[] {
    const peer = this.peers.get(pid);
    if (!peer) return [];
    this.peers.delete(pid);
    const code = peer.room;
    const room = code ? this.rooms.get(code) : undefined;
    if (!room) return [];
    const outs = this.fan(code, room.handle(pid, { t: 'bye' }, now));
    // 아무도 안 남은 방은 치운다. 안 그러면 방 코드가 영원히 쌓인다.
    if (this.roomPeers(code).length === 0) this.rooms.delete(code);
    return outs;
  }
}

// ── 정적 파일 ─────────────────────────────────────────────────────────

const MIME: Record<string, string> = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.ico': 'image/x-icon',
};

/** web/ 안의 파일만 내보낸다. `..` 로 상위 디렉터리를 훑는 요청을 막는 게 요점이다. */
export function safeJoin(root: string, urlPath: string): string | null {
  const clean = normalize(decodeURIComponent(urlPath.split('?')[0] as string));
  if (clean.includes('\0')) return null;
  const rel = clean.replace(/^(\.\.[/\\])+/, '').replace(/^[/\\]+/, '');
  const full = join(root, rel === '' ? 'index.html' : rel);
  if (!full.startsWith(root)) return null;
  return full;
}

// ── 서버 ──────────────────────────────────────────────────────────────

export interface ServerOptions {
  port?: number;
  /** 정적 파일 루트. 기본은 이 파일 기준 ../../../web */
  webRoot?: string;
  seed?: number;
  quiet?: boolean;
}

export function createServer(opts: ServerOptions = {}): {
  http: ReturnType<typeof createHttpServer>;
  hub: Hub;
  listen: (port: number) => Promise<number>;
  close: () => Promise<void>;
} {
  const HERE = dirname(fileURLToPath(import.meta.url));
  const webRoot = opts.webRoot ?? join(HERE, '..', '..', '..', 'web');
  const hub = new Hub(opts.seed);
  const log = opts.quiet ? (): void => {} : (...a: unknown[]): void => console.log(...a);
  const conns = new Map<number, WsConn>();

  const http = createHttpServer((req: IncomingMessage, res: ServerResponse) => {
    const path = safeJoin(webRoot, req.url ?? '/');
    if (!path) {
      res.writeHead(400).end('bad path');
      return;
    }
    readFile(path).then(
      (buf) => {
        res.writeHead(200, { 'content-type': MIME[extname(path)] ?? 'application/octet-stream' });
        res.end(buf);
      },
      () => {
        res.writeHead(404, { 'content-type': 'text/plain; charset=utf-8' });
        res.end('없는 파일');
      },
    );
  });

  http.on('upgrade', (req, socket, head) => {
    if (!(req.url ?? '').startsWith('/ws')) {
      socket.end('HTTP/1.1 404 Not Found\r\n\r\n');
      return;
    }
    const conn = upgrade(req, socket, head);
    if (!conn) return;
    const pid = hub.connect();
    conns.set(pid, conn);
    log(`[+] pid ${pid} 접속 (${req.socket.remoteAddress ?? '?'})`);

    const deliver = (outs: Outbound[]): void => {
      for (const o of outs) conns.get(o.to)?.sendJson(o.m);
    };

    conn.onMessage = (text: string): void => {
      let msg: ClientMsg;
      try {
        msg = JSON.parse(text) as ClientMsg;
      } catch {
        return; // 깨진 JSON 은 조용히 버린다. 끊으면 오히려 디버깅이 어렵다.
      }
      deliver(hub.handle(pid, msg, Date.now()));
    };
    conn.onClose = (): void => {
      conns.delete(pid);
      deliver(hub.disconnect(pid, Date.now()));
      log(`[-] pid ${pid} 종료`);
    };
  });

  return {
    http,
    hub,
    listen: (port: number): Promise<number> =>
      new Promise((resolve) => {
        http.listen(port, () => {
          const addr = http.address();
          const got = typeof addr === 'object' && addr ? addr.port : port;
          log(`테트리스 8인 서버 — http://localhost:${got}/  (ws://localhost:${got}/ws)`);
          resolve(got);
        });
      }),
    close: (): Promise<void> =>
      new Promise((resolve) => {
        for (const c of conns.values()) c.close(1001, 'server closing');
        http.close(() => resolve());
      }),
  };
}

// ── CLI ───────────────────────────────────────────────────────────────
function argInt(name: string, dflt: number): number {
  const i = process.argv.indexOf('--' + name);
  if (i < 0) return dflt;
  const v = parseInt(process.argv[i + 1] as string, 10);
  return Number.isFinite(v) ? v : dflt;
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const srv = createServer();
  await srv.listen(argInt('port', 8787));
}
