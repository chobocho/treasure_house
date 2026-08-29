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

import { upgrade, type WsConn } from './ws.js';
import type { ClientMsg, Outbound } from './protocol.js';

// 허브는 소켓을 모르는 순수 층이라 따로 뒀다(hub.ts). 여기서 다시 내보내는 건
// 이 모듈만 임포트하던 기존 코드와 테스트를 그대로 두기 위해서다.
export { Hub, CODE_LEN, type HubPeer } from './hub.js';
import { Hub } from './hub.js';

// ── 정적 파일 ─────────────────────────────────────────────────────────

/** 부록의 라이브러리판 서버도 같은 표를 쓴다 — 정적 파일 규칙이 갈라질 이유가 없다. */
export const MIME: Record<string, string> = {
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
