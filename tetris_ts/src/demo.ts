// demo.ts — 이 문서 안에서 도는 데모들. 슬라이드의 [data-demo] 를 보고 하나씩 붙인다.
//
// 덱의 슬라이드 엔진은 보이는 슬라이드에 [data-demo] 가 있으면 window.__mountDemo(host)
// 를 부르고, 돌려받은 객체의 start()/stop() 으로 수명을 관리한다. 여기 있는 건 그
// 규약을 맞추는 얇은 층뿐이다 — 게임도 AI 도 슬라이드에 실린 그 코드 그대로다.
//
// 데모가 진짜인 이유: 여기서 만드는 Tetris 는 테스트가 C++ wasm 과 대조한 바로 그
// 클래스다. 데모용으로 규칙을 흉내 낸 코드는 한 줄도 없다.

import { Tetris } from './core.js';
import { TetrisView, fillRows, type ViewOptions } from './view.js';

export interface Demo {
  start: () => void;
  stop: () => void;
}

/** 시드는 매번 새로 뽑는다 — 같은 슬라이드를 두 번 봐도 같은 판이 나오면 재미가 없다. */
function seed(): number {
  return ((Math.random() * 0xffffffff) >>> 0) || 1;
}

/** 사람이 직접 하는 판 하나. 덱에서 가장 많이 쓰는 데모다. */
function play(host: HTMLElement, opts: ViewOptions): Demo {
  const game = new Tetris(seed());
  return new TetrisView(host, game, opts);
}

/** AI 가 스스로 두는 어트랙트 모드. 표지·설명 슬라이드에서 배경처럼 돌린다. */
function bot(host: HTMLElement, opts: ViewOptions): Demo {
  const game = new Tetris(seed());
  return new TetrisView(host, game, { ...opts, bot: true, botMs: opts.botMs ?? 260 });
}

/** 가비지가 올라온 판 — 대전 규칙을 설명하는 슬라이드용. */
function garbage(host: HTMLElement, opts: ViewOptions): Demo {
  const game = new Tetris(seed());
  game.garbage(5, 3);
  return new TetrisView(host, game, opts);
}

/** T스핀 자리를 미리 세워 둔 판. 사람이 직접 T 를 꽂아 볼 수 있다. */
function tspin(host: HTMLElement, opts: ViewOptions): Demo {
  const game = new Tetris(seed());
  fillRows(game, [
    '#######...',
    '######....',
    '#####..###',
    '#####.####',
  ]);
  game.setPiece(5); // T
  return new TetrisView(host, game, opts);
}

export const DEMOS: Record<string, (host: HTMLElement, opts: ViewOptions) => Demo> = {
  play, bot, garbage, tspin,
};

/**
 * 호스트 하나에 데모를 붙인다.
 *
 * 모르는 이름이면 기본(play)으로 떨어진다. 슬라이드에 오타가 났다고 덱이 죽는 것보다는
 * 엉뚱한 데모라도 도는 편이 낫다 — 어차피 슬라이드 제목이 무엇을 봐야 하는지 말해 준다.
 */
export function mountDemo(host: HTMLElement, opts: ViewOptions = {}): Promise<Demo> {
  const name = (host as unknown as { dataset?: Record<string, string> }).dataset?.['demo'] ?? 'play';
  const make = DEMOS[name] ?? (DEMOS['play'] as (h: HTMLElement, o: ViewOptions) => Demo);
  // 덱 엔진이 프로미스를 기대한다(원래는 wasm 을 올리느라 비동기였다). 모양을 맞춘다.
  return Promise.resolve(make(host, opts));
}

// 브라우저에서만 전역에 건다. 노드에서 임포트할 때는 아무 일도 일어나지 않는다.
const w = globalThis as unknown as { __mountDemo?: (h: HTMLElement) => Promise<Demo>; document?: unknown };
if (w.document) {
  w.__mountDemo = (host: HTMLElement): Promise<Demo> => mountDemo(host);
}
