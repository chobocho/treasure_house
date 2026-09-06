// 시나리오 트레이스 — 골든과 한 줄도 어긋나지 않는가.
import * as H from './harness';
import { runScriptTrace } from '../src/game';

interface TickRow {
  t: number; px: number; py: number; lv: number; mon: number; seen: number;
}

export function run(): number {
  H.title('trace');

  const got = runScriptTrace();
  const want = H.golden('trace.jsonl');
  const gl = got.replace(/\n+$/, '').split('\n');
  const wl = want.replace(/\n+$/, '').split('\n');

  H.check('줄 수', gl.length, wl.length);
  let bad = 0;
  const n = Math.min(gl.length, wl.length);
  for (let i = 0; i < n; i++) {
    if (gl[i] !== wl[i]) {
      bad += 1;
      if (bad <= 3) {
        console.log('  ' + (i + 1) + '줄 다름');
        console.log('    기대 ' + wl[i]);
        console.log('    실제 ' + gl[i]);
      }
    }
  }
  H.check('다른 줄', bad, 0);

  // ---- 두 번 돌려도 같은가
  H.check('재현성', runScriptTrace(), got);

  // ---- 트레이스가 실제로 뭔가를 했는가 (빈 시나리오 방지)
  const ticks: TickRow[] = gl.filter((l) => l.startsWith('{"t"'))
    .map((l) => JSON.parse(l) as TickRow);
  const marks = gl.filter((l) => l.startsWith('{"mark"'));
  H.check('표식 개수', marks.length, 11);
  H.checkTrue('222줄의 틱 (되돌린 뒤 다시 진행한 몫 포함)', ticks.length === 222);
  const first = ticks[0] as TickRow;
  const last = ticks[ticks.length - 1] as TickRow;
  H.checkTrue('몬스터가 줄었다', last.mon < first.mon);
  H.checkTrue('레벨이 올랐다', last.lv > first.lv);
  let rewound = false;
  for (let i = 0; i < ticks.length - 1; i++) {
    if ((ticks[i + 1] as TickRow).t < (ticks[i] as TickRow).t) rewound = true;
  }
  H.checkTrue('되돌리기가 실제로 시간을 되돌렸다', rewound);
  H.checkTrue('플레이어가 움직였다', first.px !== last.px || first.py !== last.py);
  H.checkTrue('본 칸이 늘었다', last.seen > first.seen);
  // 숫자 자리에 부동소수점 표기가 섞이면 언어마다 자릿수가 달라져 파리티가 깨진다.
  // TS 는 String(1e21) 이 "1e+21" 이라 특히 조심해야 하는 자리다.
  const numpat = /^-?\d+$/;
  bad = 0;
  for (const l of gl) {
    if (!l.startsWith('{"t"')) continue;
    const toks = l.match(/:\s*-?[\d.eE+]+/g) ?? [];
    for (const raw of toks) {
      const tok = raw.replace(/^:\s*/, '');
      if (!numpat.test(tok)) bad += 1;
    }
  }
  H.check('정수가 아닌 숫자 토큰', bad, 0);

  return H.done();
}
