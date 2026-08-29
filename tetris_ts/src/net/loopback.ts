// loopback.ts — 소켓 없이 같은 페이지 안에서 서버에 붙는다.
//
// 덱 안의 8인 대전 데모가 이걸 쓴다. 바뀌는 건 전송 계층 하나뿐이고, 허브도 룸도
// 클라이언트도 서버에 붙을 때와 **같은 코드**다. 그래서 이 데모가 "그럴듯한 흉내"가
// 아니라 실제 프로토콜을 지나간다 — 좌석 배정도, 공격 라우팅도, 탈락 처리도.
//
// 지연(latency)을 줄 수 있다. 0이면 즉시, 아니면 setTimeout 으로 미룬다.

import { Hub } from './hub.js';
import type { ClientMsg } from './protocol.js';
import type { Transport } from './client.js';

export class LoopbackHub {
  readonly hub: Hub;
  private readonly conns = new Map<number, Transport>();
  private t = 0;

  constructor(seed = 0x1234abcd, readonly latency = 0) {
    this.hub = new Hub(seed);
  }

  /** 시계 — 룸이 hitTTL·유예를 잴 때 쓴다. 데모는 프레임마다 밀어 준다. */
  now(): number {
    return this.t;
  }

  advance(dtMs: number): void {
    this.t += dtMs;
  }

  /** 클라이언트 하나가 붙는다. 돌려주는 것이 그 클라이언트의 전송 계층이다. */
  connect(): Transport {
    const pid = this.hub.connect();
    const conn: Transport = {
      onMessage: null, onOpen: null, onClose: null,
      send: (text: string): void => {
        let msg: ClientMsg;
        try {
          msg = JSON.parse(text) as ClientMsg;
        } catch {
          return;
        }
        this.deliver(this.hub.handle(pid, msg, this.t));
      },
      close: (): void => {
        if (!this.conns.has(pid)) return;
        this.conns.delete(pid);
        this.deliver(this.hub.disconnect(pid, this.t));
        conn.onClose?.();
      },
    };
    this.conns.set(pid, conn);
    // onOpen 은 다음 틱에 부른다 — 생성자가 돌아가기 전에 부르면 구독자가 없다.
    setTimeout(() => conn.onOpen?.(), 0);
    return conn;
  }

  /** 허브가 낸 결과를 받는 사람에게 흘려 넣는다. */
  private deliver(outs: { to: number; m: unknown }[]): void {
    for (const o of outs) {
      const c = this.conns.get(o.to);
      if (!c) continue;
      const text = JSON.stringify(o.m);
      if (this.latency > 0) setTimeout(() => c.onMessage?.(text), this.latency);
      else c.onMessage?.(text);
    }
  }
}
