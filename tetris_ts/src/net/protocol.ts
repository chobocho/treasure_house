// protocol.ts — 테트리스 온라인 프로토콜 v3.
//
// 규격 전문은 ../../tetris_net/protocol.md, 검증표는 ../../tetris_net/protocol_vectors.json.
// **규격을 새로 만들지 않았다.** 부 3 에서 JS·Go·파이썬 세 구현이 이미 같은 표를
// 재현하도록 맞춰 놨고, 이 파일은 그 표에 맞추는 네 번째 구현이다.
// 그래서 여기서 마음대로 필드를 늘리거나 이름을 바꾸면 안 된다 — 기존 서버와 못 붙는다.
//
// WebSocket 텍스트 프레임 1개 = JSON 객체 1개. 바이너리 프레임은 쓰지 않는다.
// 보드 스냅샷만 RLE 후 base64 로 접어 문자열 필드에 넣는다.

import { W, VIS, ST, type Tetris } from '../core.js';

export const PROTOCOL_VERSION = 3;

/** 프로토콜의 s[] 12칸 — protocol.md §5 와 같은 표다. */
export const S = {
  STATE: 0, SCORE: 1, LINES: 2, PIECES: 3, HEIGHT: 4, PENDING: 5,
  PIECE: 6, ROT: 7, X: 8, Y: 9, GHOST: 10, HOLD: 11, COUNT: 12,
} as const;

/** 방 설정. protocol.md §2. */
export interface RoomCfg {
  max: number;
  perPeer: number;
  target: 'random' | 'even' | 'attackers' | 'ko';
  delay: number;
  cap: number;
  hitTTL: number;
}

export const CFG_DEFAULTS: RoomCfg = {
  max: 8,
  perPeer: 2, // "한 PC 에서 최대 2명"이 이 한 줄이다
  target: 'random',
  delay: 900,
  cap: 8,
  hitTTL: 8000,
};

/** 로비에 뿌리는 좌석 하나. 내부 필드(recv/hits/height/place)는 내보내지 않는다. */
export interface SeatInfo {
  i: number;
  pid: number;
  name: string;
  kind: 'human' | 'ai';
  lv: string;
  ready: boolean;
  alive: boolean;
}

/** 클라이언트 → 서버. */
export type ClientMsg =
  | { t: 'hello'; v: number; name?: string }
  | { t: 'create'; cfg?: Partial<RoomCfg> }
  | { t: 'join'; room: string }
  | { t: 'seat'; i?: number | null; kind?: string; name?: string; lv?: string }
  | { t: 'unseat'; i: number }
  | { t: 'ready'; v: boolean }
  | { t: 'start' }
  | { t: 'atk'; i: number; n: number }
  | { t: 'st'; i: number; b: string; s: number[] }
  | { t: 'ko'; i: number }
  | { t: 'ping'; c: number }
  | { t: 'bye' };

/** 서버 → 클라이언트.
 *
 *  주의: protocol.md §4 의 표는 `hi` 가 code·cfg 까지 싣는다고 적어 놨지만,
 *  부 3 의 세 구현(Go·파이썬·JS 클라이언트)은 전부 **둘로 나눠** 쓴다.
 *    hello       → hi     {pid, v}
 *    create/join → joined {code, cfg, pid}
 *  실제로 통신하는 상대는 문서가 아니라 그 구현들이므로 구현 쪽에 맞췄다.
 *  (규격서의 이 대목은 부정확하다 — 덱에도 그렇게 적는다.) */
export type ServerMsg =
  | { t: 'hi'; pid: number; v: number }
  | { t: 'joined'; code: string; cfg: RoomCfg; pid: number }
  | { t: 'room'; host: number; seats: SeatInfo[] }
  | { t: 'err'; code: ErrCode }
  | { t: 'start'; seed: number; seats: SeatInfo[] }
  | { t: 'grb'; i: number; n: number; from: number; hole: number }
  | { t: 'st'; i: number; b: string; s: number[] }
  | { t: 'ko'; i: number; place: number; by: number }
  | { t: 'end'; order: number[] }
  | { t: 'pong'; c: number };

/** 오류 코드. protocol.md §9 + 구현이 실제로 쓰는 두 개(hello·inroom).
 *  사람이 읽을 문구는 클라이언트가 코드로 찾는다. */
export type ErrCode =
  | 'ver' | 'phase' | 'seat' | 'full' | 'own' | 'host' | 'ready' | 'nosuch'
  | 'hello'   // 접속 인사(hello) 전에 다른 걸 했다 — 규격서 §9 에는 빠져 있다
  | 'inroom'; // 이미 방에 들어와 있는데 또 create/join 했다 — 이것도 빠져 있다

/** 클라이언트가 보낸 cfg 에서 0(또는 빈 문자열)인 칸은 기본값을 그대로 둔다.
 *  "안 적었다"와 "0 을 적었다"를 JSON 만으로는 못 가리므로, 0 은 안 적은 것으로 본다.
 *  Go 의 mergeCfg / 파이썬의 merge_cfg 와 같은 규칙이다. */
export function mergeCfg(inCfg: Partial<RoomCfg> | undefined): RoomCfg {
  const out: RoomCfg = { ...CFG_DEFAULTS };
  const c = inCfg ?? {};
  if (c.max && c.max > 0) out.max = Math.min(8, c.max | 0);
  if (c.perPeer && c.perPeer > 0) out.perPeer = c.perPeer | 0;
  if (c.target) out.target = c.target;
  if (c.delay && c.delay > 0) out.delay = c.delay | 0;
  if (c.cap && c.cap > 0) out.cap = c.cap | 0;
  if (c.hitTTL && c.hitTTL > 0) out.hitTTL = c.hitTTL | 0;
  return out;
}

/** room.handle 이 내놓는 한 통. to === 0 이면 방 전체 브로드캐스트. */
export interface Outbound {
  to: number;
  m: ServerMsg;
}

// ── 보드 스냅샷 (protocol.md §6) ───────────────────────────────────────
//
// 보이는 필드 20×10 = 200칸을 위에서 아래로, 왼쪽에서 오른쪽으로 훑어 런렝스로 접는다.
//   바이트 = (런길이 - 1) << 4 | 칸값        런길이 1‥16, 칸값 0‥8
// 빈 판은 200칸 = 16×12 + 8 → 13바이트 → base64 20자.
//
// 실측(AI 가 둔 판 1200개): 평균 70바이트, 최악 118바이트.
// 규격서 §6 은 "꽉 찬 판도 100바이트를 넘지 않는다"고 적었지만 그건 사실이 아니다 —
// 실전에서 118바이트가 나오고, 200칸이 전부 교대로 다른 색이면 이론적 최악은
// 200바이트다(런 길이가 전부 1). test/room.test.ts 가 이 수치를 매번 다시 잰다.
// 대역폭은 좌석 8석 × 초당 10회 × (base64 ~95자 + JSON 껍데기) ≒ 10 KB/s 안팎이다.

const B64 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';

/** Buffer 없이 base64 로. 브라우저와 Node 가 같은 코드를 쓰게 하려는 것이다
 *  (btoa 는 Node 에 없던 시절이 길었고, Buffer 는 브라우저에 없다). */
export function toBase64(bytes: Uint8Array): string {
  let out = '';
  let i = 0;
  for (; i + 2 < bytes.length; i += 3) {
    const n = ((bytes[i] as number) << 16) | ((bytes[i + 1] as number) << 8) | (bytes[i + 2] as number);
    out += B64[(n >> 18) & 63]! + B64[(n >> 12) & 63]! + B64[(n >> 6) & 63]! + B64[n & 63]!;
  }
  const rest = bytes.length - i;
  if (rest === 1) {
    const n = (bytes[i] as number) << 16;
    out += B64[(n >> 18) & 63]! + B64[(n >> 12) & 63]! + '==';
  } else if (rest === 2) {
    const n = ((bytes[i] as number) << 16) | ((bytes[i + 1] as number) << 8);
    out += B64[(n >> 18) & 63]! + B64[(n >> 12) & 63]! + B64[(n >> 6) & 63]! + '=';
  }
  return out;
}

const B64REV = (() => {
  const m = new Int8Array(128).fill(-1);
  for (let i = 0; i < B64.length; i++) m[B64.charCodeAt(i)] = i;
  return m;
})();

export function fromBase64(s: string): Uint8Array {
  const clean = s.replace(/=+$/, '');
  const out = new Uint8Array((clean.length * 3) >> 2);
  let acc = 0, bits = 0, k = 0;
  for (let i = 0; i < clean.length; i++) {
    const v = B64REV[clean.charCodeAt(i)] as number;
    if (v < 0) continue;
    acc = (acc << 6) | v;
    bits += 6;
    if (bits >= 8) {
      bits -= 8;
      out[k++] = (acc >> bits) & 0xff;
    }
  }
  return out.subarray(0, k);
}

/** 보이는 20×10 칸 배열 → RLE 바이트열. */
export function rleEncode(cells: Uint8Array): Uint8Array {
  const out: number[] = [];
  let i = 0;
  while (i < cells.length) {
    const v = (cells[i] as number) & 15;
    let run = 1;
    // 런 길이는 4비트에 담으므로 16이 상한이다. 그 이상은 끊어서 다음 바이트로.
    while (run < 16 && i + run < cells.length && ((cells[i + run] as number) & 15) === v) run++;
    out.push(((run - 1) << 4) | v);
    i += run;
  }
  return Uint8Array.from(out);
}

/** RLE 바이트열 → 칸 배열. out 을 채우고 채운 칸 수를 반환한다. */
export function rleDecode(raw: Uint8Array, out: Uint8Array): number {
  let k = 0;
  for (const byte of raw) {
    const run = (byte >> 4) + 1;
    const v = byte & 15;
    for (let i = 0; i < run && k < out.length; i++) out[k++] = v;
  }
  return k;
}

/** 코어의 화면 버퍼(굳은 블록 + 현재 조각)를 스냅샷 문자열로. */
export function snapshot(g: Tetris): string {
  const cells = new Uint8Array(VIS * W);
  cells.set(g.cells);
  // 오버레이의 현재 조각(1~7)만 덮어 그린다. 고스트(8~14)는 관전 화면에서 빼도 된다 —
  // 매 프레임 바뀌는 값이라 RLE 효율을 떨어뜨리는 것에 비해 정보가 적다.
  for (let i = 0; i < cells.length; i++) {
    const o = g.overlay[i] as number;
    if (o >= 1 && o <= 7) cells[i] = o;
  }
  return toBase64(rleEncode(cells));
}

export function unsnapshot(b64: string, out: Uint8Array): number {
  return rleDecode(fromBase64(b64), out);
}

/** 가장 높이 쌓인 열의 높이(칸). 서버가 읽는 두 칸 중 하나(s[4])다. */
export function heightOf(g: Tetris): number {
  const b = g.board;
  const rows = b.length / W;
  for (let y = 0; y < rows; y++) {
    for (let x = 0; x < W; x++) if (b[y * W + x]) return rows - y;
  }
  return 0;
}

/** 상태 12칸 만들기 — 서버가 읽는 건 s[0] 과 s[4] 뿐이지만 나머지는 관전용이다. */
export function packState(g: Tetris): number[] {
  const s = g.stats;
  return [
    s[ST.STATE] as number, s[ST.SCORE] as number, s[ST.LINES] as number, s[ST.PIECES] as number,
    heightOf(g), s[ST.PENDING] as number,
    s[ST.PIECE] as number, s[ST.ROT] as number, s[ST.X] as number, s[ST.Y] as number,
    s[ST.GHOST] as number, s[ST.HOLD] as number,
  ];
}
