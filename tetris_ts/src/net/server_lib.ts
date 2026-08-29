// server_lib.ts — 같은 서버를 ws 라이브러리로 다시 만든 것. **부록 전용**이다.
//
// 본편(server.ts)은 RFC 6455 를 직접 구현했다(파트 12). 그 300줄이 정말 필요했는지,
// 라이브러리를 쓰면 무엇이 줄고 무엇이 늘어나는지를 재려면 같은 서버를 두 벌 만들어
// 맞대어 보는 수밖에 없다.
//
// 규칙은 한 줄도 안 바뀐다. 허브도 룸도 프로토콜도 그대로다 — 바뀌는 건 "소켓에서
// 프레임을 꺼내는 방법" 하나뿐이고, 그게 정확히 라이브러리가 해 주는 일이다.
//
// 이 파일은 tsconfig 의 exclude 에 있다. `make lib` 가 ws 를 설치하고 따로 컴파일한다.
//
//   make lib          ws 설치 → 컴파일 → 라이브러리판으로 실측 대전

import { createServer as createHttpServer, type IncomingMessage, type ServerResponse } from 'node:http';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { dirname, join, extname } from 'node:path';
import { WebSocketServer, type WebSocket } from 'ws';

import { Hub } from './hub.js';
import { safeJoin, MIME, type ServerOptions } from './server.js';
import type { ClientMsg } from './protocol.js';

/**
 * 본편과 같은 모양의 서버.
 *
 * 눈에 띄게 짧아진 건 두 군데다: 업그레이드 처리(핸드셰이크·accept 키 계산이 사라졌다)와
 * 메시지 수신(프레임 파서·조각 모으기·마스킹 해제가 전부 라이브러리 안으로 들어갔다).
 * 대신 의존성이 하나 생겼고, 무슨 일이 벌어지는지는 node_modules 안으로 숨었다.
 */
export function createLibServer(opts: ServerOptions = {}): {
  listen: (port: number) => Promise<number>;
  close: () => Promise<void>;
  hub: Hub;
} {
  const HERE = dirname(fileURLToPath(import.meta.url));
  const webRoot = opts.webRoot ?? join(HERE, '..', '..', '..', 'web');
  const hub = new Hub(opts.seed);
  const log = opts.quiet ? (): void => {} : (...a: unknown[]): void => console.log(...a);
  const conns = new Map<number, WebSocket>();

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

  // 여기가 본편의 upgrade 핸들러 자리다. 핸드셰이크·accept 키·프레임 파서가
  // 전부 이 한 줄로 대체된다.
  const wss = new WebSocketServer({ server: http, path: '/ws' });

  const deliver = (outs: { to: number; m: unknown }[]): void => {
    for (const o of outs) {
      const ws = conns.get(o.to);
      if (ws && ws.readyState === 1) ws.send(JSON.stringify(o.m));
    }
  };

  wss.on('connection', (ws: WebSocket) => {
    const pid = hub.connect();
    conns.set(pid, ws);
    log(`[+] pid ${pid} 접속 (ws 라이브러리판)`);
    ws.on('message', (data: unknown) => {
      let msg: ClientMsg;
      try {
        msg = JSON.parse(String(data)) as ClientMsg;
      } catch {
        return; // 본편과 같은 규칙 — 깨진 메시지는 조용히 버린다
      }
      deliver(hub.handle(pid, msg, Date.now()));
    });
    ws.on('close', () => {
      conns.delete(pid);
      deliver(hub.disconnect(pid, Date.now()));
      log(`[-] pid ${pid} 종료`);
    });
    ws.on('error', () => { /* close 가 뒤따른다 */ });
  });

  return {
    hub,
    listen: (port: number): Promise<number> =>
      new Promise((resolve) => {
        http.listen(port, () => {
          const a = http.address();
          const p = typeof a === 'object' && a ? a.port : port;
          log(`서버 시작(ws 라이브러리판) — http://localhost:${p}  (web/ + /ws)`);
          resolve(p);
        });
      }),
    close: (): Promise<void> =>
      new Promise((resolve) => {
        for (const ws of conns.values()) { try { ws.close(); } catch { /* 이미 닫혔다 */ } }
        wss.close(() => http.close(() => resolve()));
      }),
  };
}
