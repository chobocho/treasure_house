// ws.ts — RFC 6455 WebSocket 서버를 바닥부터. 런타임 의존성 0.
//
// 왜 직접 쓰는가: 이 게임이 웹소켓에게 요구하는 건 "텍스트 프레임을 주고받는다"
// 하나뿐이다. 그걸 위해 라이브러리를 넣으면, 정작 **무슨 일이 벌어지는지**가
// node_modules 안으로 숨는다. 확장·압축·서브프로토콜을 뺀 최소 구현은 300줄이면 되고,
// 그 300줄이 곧 프로토콜 설명이다. (라이브러리판은 부록 server_lib.ts 에 따로 뒀다.)
//
// 구현 범위:
//   O  핸드셰이크(101), 텍스트/바이너리 프레임, 조각화(continuation), ping/pong, close
//   X  permessage-deflate, 확장, 서브프로토콜 협상, 클라이언트 역할
//
// 가장 흔한 실수 두 가지를 미리 적어 둔다:
//   1. TCP 는 프레임 경계를 지켜 주지 않는다. 한 번의 'data' 에 프레임이 3개 올 수도,
//      헤더가 반만 올 수도 있다. 그래서 파서를 따로 뒀다(FrameParser).
//   2. 클라이언트 → 서버 프레임은 **반드시** 마스킹돼 있고, 서버 → 클라이언트는
//      **절대** 마스킹하면 안 된다. 방향이 다르다.

import { createHash } from 'node:crypto';
import type { IncomingMessage } from 'node:http';
import type { Duplex } from 'node:stream';
import type { Socket } from 'node:net';

/** RFC 6455 §1.3 이 못박아 둔 매직 문자열. 이유는 없다 — 규격이 그렇다. */
export const WS_GUID = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11';

/** Sec-WebSocket-Key 에 대한 응답값. sha1(key + GUID) 를 base64 로. */
export function acceptKey(key: string): string {
  return createHash('sha1').update(key + WS_GUID).digest('base64');
}

export const OP = {
  CONT: 0x0, TEXT: 0x1, BIN: 0x2, CLOSE: 0x8, PING: 0x9, PONG: 0xa,
} as const;

/** 한 메시지의 최대 크기. 없으면 악의적인 길이 헤더 하나로 서버 메모리를 말릴 수 있다. */
export const MAX_MESSAGE = 1 << 20; // 1 MiB

export interface Frame {
  fin: boolean;
  op: number;
  payload: Uint8Array;
}

export class WsProtocolError extends Error {
  constructor(message: string, readonly code = 1002) {
    super(message);
    this.name = 'WsProtocolError';
  }
}

/**
 * 바이트 스트림에서 프레임을 뽑아내는 파서.
 *
 * 상태는 "아직 다 못 읽은 바이트" 하나뿐이다. push() 는 지금까지 모인 바이트에서
 * **완성된 프레임만** 꺼내 주고 나머지는 다음 호출을 위해 남긴다.
 */
export class FrameParser {
  private buf: Uint8Array = new Uint8Array(0);

  private static concat(a: Uint8Array, b: Uint8Array): Uint8Array {
    const out = new Uint8Array(a.length + b.length);
    out.set(a, 0);
    out.set(b, a.length);
    return out;
  }

  push(chunk: Uint8Array): Frame[] {
    this.buf = this.buf.length ? FrameParser.concat(this.buf, chunk) : new Uint8Array(chunk);
    const frames: Frame[] = [];
    for (;;) {
      const f = this.take();
      if (!f) break;
      frames.push(f);
    }
    return frames;
  }

  /** 완성된 프레임 하나를 떼어낸다. 아직 부족하면 null. */
  private take(): Frame | null {
    const b = this.buf;
    if (b.length < 2) return null;
    const b0 = b[0] as number, b1 = b[1] as number;
    const fin = (b0 & 0x80) !== 0;
    const rsv = b0 & 0x70;
    const op = b0 & 0x0f;
    const masked = (b1 & 0x80) !== 0;
    let len = b1 & 0x7f;
    let off = 2;

    // 확장·압축을 협상하지 않았으므로 RSV 비트는 0이어야 한다.
    if (rsv !== 0) throw new WsProtocolError(`RSV 비트가 켜져 있다: 0x${rsv.toString(16)}`);

    if (len === 126) {
      if (b.length < off + 2) return null;
      len = ((b[off] as number) << 8) | (b[off + 1] as number);
      off += 2;
    } else if (len === 127) {
      if (b.length < off + 8) return null;
      // 상위 4바이트는 0이어야 한다. 2^32 바이트짜리 메시지는 우리 상한을 한참 넘는다.
      const hi = ((b[off] as number) << 24) | ((b[off + 1] as number) << 16)
        | ((b[off + 2] as number) << 8) | (b[off + 3] as number);
      if (hi !== 0) throw new WsProtocolError('메시지가 너무 크다', 1009);
      len = ((b[off + 4] as number) * 0x1000000) + (((b[off + 5] as number) << 16)
        | ((b[off + 6] as number) << 8) | (b[off + 7] as number));
      off += 8;
    }
    if (len > MAX_MESSAGE) throw new WsProtocolError(`메시지가 너무 크다: ${len}`, 1009);

    // 제어 프레임(close/ping/pong)은 125바이트 이하이고 조각날 수 없다. RFC 6455 §5.5.
    if (op >= 0x8) {
      if (len > 125) throw new WsProtocolError('제어 프레임이 125바이트를 넘는다');
      if (!fin) throw new WsProtocolError('제어 프레임은 조각날 수 없다');
    }

    let maskKey: Uint8Array | null = null;
    if (masked) {
      if (b.length < off + 4) return null;
      maskKey = b.subarray(off, off + 4);
      off += 4;
    }
    if (b.length < off + len) return null;

    const payload = b.slice(off, off + len);
    if (maskKey) {
      for (let i = 0; i < payload.length; i++) {
        payload[i] = (payload[i] as number) ^ (maskKey[i & 3] as number);
      }
    }
    this.buf = b.subarray(off + len);
    return { fin, op, payload };
  }
}

/**
 * 프레임 하나를 바이트로.
 *
 * @param mask 서버는 절대 마스킹하지 않는다(RFC 6455 §5.1). 클라이언트 역할을
 *             흉내 낼 때만 true — 봇 클라이언트가 그 경로를 쓴다.
 */
export function encodeFrame(op: number, payload: Uint8Array, mask = false): Uint8Array {
  const len = payload.length;
  let headerLen = 2 + (mask ? 4 : 0);
  if (len >= 65536) headerLen += 8;
  else if (len >= 126) headerLen += 2;

  const out = new Uint8Array(headerLen + len);
  out[0] = 0x80 | op; // FIN=1, 조각내지 않는다
  let off = 2;
  if (len >= 65536) {
    out[1] = 127;
    // 상위 4바이트는 0 (우리가 보내는 메시지는 4 GiB 를 넘지 않는다)
    out[off + 4] = (len >>> 24) & 0xff;
    out[off + 5] = (len >>> 16) & 0xff;
    out[off + 6] = (len >>> 8) & 0xff;
    out[off + 7] = len & 0xff;
    off += 8;
  } else if (len >= 126) {
    out[1] = 126;
    out[off] = (len >>> 8) & 0xff;
    out[off + 1] = len & 0xff;
    off += 2;
  } else {
    out[1] = len;
  }
  if (mask) {
    out[1] = (out[1] as number) | 0x80;
    const key = new Uint8Array(4);
    for (let i = 0; i < 4; i++) key[i] = (Math.random() * 256) | 0;
    out.set(key, off);
    off += 4;
    for (let i = 0; i < len; i++) {
      out[off + i] = (payload[i] as number) ^ (key[i & 3] as number);
    }
  } else {
    out.set(payload, off);
  }
  return out;
}

const enc = new TextEncoder();
const dec = new TextDecoder();

/** 연결 하나. 조각난 메시지를 다시 붙이고 ping/pong·close 를 규격대로 처리한다. */
export class WsConn {
  private readonly parser = new FrameParser();
  /** 조각 모으는 중인 메시지 */
  private fragOp = -1;
  private fragParts: Uint8Array[] = [];
  private fragLen = 0;
  closed = false;

  onMessage: ((text: string) => void) | null = null;
  onClose: ((code: number, reason: string) => void) | null = null;

  constructor(readonly socket: Duplex, readonly req: IncomingMessage, head?: Uint8Array) {
    socket.on('data', (c: Buffer) => this.feed(c));
    socket.on('error', () => this.finish(1006, 'socket error'));
    socket.on('close', () => this.finish(1006, 'socket closed'));
    // 101 응답을 쓰기 전에 이미 도착해 있던 바이트가 head 로 넘어온다. 버리면 첫
    // 메시지를 잃는다. 다만 지금 바로 처리하면 호출자가 onMessage 를 붙이기 전이라,
    // 이번 틱이 끝난 뒤에 흘려 넣는다.
    if (head && head.length) setImmediate(() => this.feed(head));
  }

  private feed(chunk: Uint8Array): void {
    if (this.closed) return;
    let frames: Frame[];
    try {
      frames = this.parser.push(chunk);
    } catch (e) {
      const err = e as WsProtocolError;
      this.close(err.code ?? 1002, err.message);
      return;
    }
    for (const f of frames) {
      if (this.closed) return;
      this.onFrame(f);
    }
  }

  private onFrame(f: Frame): void {
    switch (f.op) {
      case OP.PING:
        this.sendFrame(OP.PONG, f.payload);
        return;
      case OP.PONG:
        return;
      case OP.CLOSE: {
        const code = f.payload.length >= 2
          ? ((f.payload[0] as number) << 8) | (f.payload[1] as number)
          : 1005;
        // 규격대로 close 를 되돌려 준 뒤 끊는다 (닫기 핸드셰이크).
        this.sendFrame(OP.CLOSE, f.payload.subarray(0, 2));
        this.socket.end();
        this.finish(code, f.payload.length > 2 ? dec.decode(f.payload.subarray(2)) : '');
        return;
      }
      case OP.TEXT:
      case OP.BIN:
        if (this.fragOp >= 0) {
          this.close(1002, '앞 메시지가 끝나기 전에 새 메시지가 시작됐다');
          return;
        }
        if (f.fin) {
          this.deliver(f.op, f.payload);
          return;
        }
        this.fragOp = f.op;
        this.fragParts = [f.payload];
        this.fragLen = f.payload.length;
        return;
      case OP.CONT: {
        if (this.fragOp < 0) {
          this.close(1002, '이어붙일 메시지가 없는데 continuation 이 왔다');
          return;
        }
        this.fragParts.push(f.payload);
        this.fragLen += f.payload.length;
        if (this.fragLen > MAX_MESSAGE) {
          this.close(1009, '조각을 합치니 너무 크다');
          return;
        }
        if (!f.fin) return;
        const whole = new Uint8Array(this.fragLen);
        let off = 0;
        for (const p of this.fragParts) { whole.set(p, off); off += p.length; }
        const op = this.fragOp;
        this.fragOp = -1;
        this.fragParts = [];
        this.fragLen = 0;
        this.deliver(op, whole);
        return;
      }
      default:
        this.close(1002, `모르는 opcode: ${f.op}`);
    }
  }

  private deliver(op: number, payload: Uint8Array): void {
    // 이 프로토콜은 텍스트만 쓴다. 바이너리가 오면 규격 위반은 아니지만 우리 쪽 계약 위반이다.
    if (op !== OP.TEXT) {
      this.close(1003, '텍스트 프레임만 받는다');
      return;
    }
    this.onMessage?.(dec.decode(payload));
  }

  private sendFrame(op: number, payload: Uint8Array): void {
    if (this.socket.destroyed) return;
    this.socket.write(encodeFrame(op, payload));
  }

  send(text: string): void {
    if (this.closed) return;
    this.sendFrame(OP.TEXT, enc.encode(text));
  }

  sendJson(obj: unknown): void {
    this.send(JSON.stringify(obj));
  }

  ping(payload = new Uint8Array(0)): void {
    if (!this.closed) this.sendFrame(OP.PING, payload);
  }

  close(code = 1000, reason = ''): void {
    if (this.closed) {
      this.socket.destroy();
      return;
    }
    const r = enc.encode(reason);
    const payload = new Uint8Array(2 + r.length);
    payload[0] = (code >> 8) & 0xff;
    payload[1] = code & 0xff;
    payload.set(r, 2);
    this.sendFrame(OP.CLOSE, payload);
    this.socket.end();
    this.finish(code, reason);
  }

  /** 닫힘을 딱 한 번만 알린다. 소켓의 error 와 close 가 둘 다 오는 경우가 흔하다. */
  private finish(code: number, reason: string): void {
    if (this.closed) return;
    this.closed = true;
    this.onClose?.(code, reason);
  }
}

/** 업그레이드 요청이 규격에 맞는지 보고, 맞으면 101 을 보내고 연결을 만든다. */
export function upgrade(req: IncomingMessage, socket: Duplex, head: Uint8Array): WsConn | null {
  const h = req.headers;
  const key = h['sec-websocket-key'];
  const version = h['sec-websocket-version'];
  const upgradeHdr = String(h['upgrade'] ?? '').toLowerCase();
  const connectionHdr = String(h['connection'] ?? '').toLowerCase();

  if (upgradeHdr !== 'websocket' || !connectionHdr.includes('upgrade')
    || typeof key !== 'string' || version !== '13') {
    socket.end('HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n');
    return null;
  }

  socket.write(
    'HTTP/1.1 101 Switching Protocols\r\n' +
    'Upgrade: websocket\r\n' +
    'Connection: Upgrade\r\n' +
    `Sec-WebSocket-Accept: ${acceptKey(key)}\r\n\r\n`,
  );
  // TCP 의 Nagle 알고리즘을 끈다. 40바이트짜리 메시지를 초당 10번 보내는
  // 이 게임에서는 "작은 패킷을 모아서 보내는" 최적화가 그대로 지연이 된다.
  (socket as Socket).setNoDelay?.(true);
  return new WsConn(socket, req, head);
}
