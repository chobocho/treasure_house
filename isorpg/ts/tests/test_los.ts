// 시야 — 브레젠험, 대칭성, 안개, 조명 단계.
import * as H from './harness';
import * as M from '../src/gamemap';
import * as L from '../src/los';

export function run(): number {
  H.title('los');

  // ---- 브레젠험 기본 성질
  H.check('한 점', L.line(3, 3, 3, 3), [[3, 3]]);
  H.check('가로', L.line(0, 0, 4, 0), [[0, 0], [1, 0], [2, 0], [3, 0], [4, 0]]);
  H.check('대각', L.line(0, 0, 3, 3), [[0, 0], [1, 1], [2, 2], [3, 3]]);
  let bad = 0;
  for (let x1 = -12; x1 <= 12; x1++) {
    for (let y1 = -12; y1 <= 12; y1++) {
      const pts = L.line(0, 0, x1, y1);
      const first = pts[0] as L.Pt;
      const last = pts[pts.length - 1] as L.Pt;
      if (first[0] !== 0 || first[1] !== 0 || last[0] !== x1 || last[1] !== y1) bad += 1;
      for (let i = 0; i < pts.length - 1; i++) {
        const a = pts[i] as L.Pt;
        const b = pts[i + 1] as L.Pt;
        const dx = Math.abs(b[0] - a[0]);
        const dy = Math.abs(b[1] - a[1]);
        if (dx > 1 || dy > 1 || (dx === 0 && dy === 0)) bad += 1;
      }
      if (pts.length !== Math.max(Math.abs(x1), Math.abs(y1)) + 1) bad += 1;
    }
  }
  H.check('브레젠험 25x25 성질 (끝점·연결성·길이)', bad, 0);

  // ---- 뒤집으면 같은 점 집합인가 (대칭성은 보장되지 않는다 — 실제로 세어 본다)
  let asym = 0;
  for (let x1 = -12; x1 <= 12; x1++) {
    for (let y1 = -12; y1 <= 12; y1++) {
      const a = new Set(L.line(0, 0, x1, y1).map((p) => p[0] + ',' + p[1]));
      const b = new Set(L.line(x1, y1, 0, 0).map((p) => p[0] + ',' + p[1]));
      let eq = a.size === b.size;
      if (eq) for (const k of a) if (!b.has(k)) eq = false;
      if (!eq) asym += 1;
    }
  }
  H.note('브레젠험 역방향과 다른 선 ' + asym + '개 / 625');

  const m = M.genMap();

  // ---- 벽 너머는 안 보인다
  H.checkTrue('자기 자신은 보인다', L.visible(m, 24, 25, 24, 25));
  H.checkTrue('북문(24,18)은 길이라 그 너머가 보인다', L.visible(m, 24, 25, 24, 17));
  H.checkTrue('벽(22,18) 너머는 안 보인다', !L.visible(m, 22, 25, 22, 16));

  // ---- 안개
  const fog = new L.Fog(48, 48);
  H.check('처음엔 아무것도 안 봤다', fog.countSeen(), 0);
  fog.update(m, 24, 34);
  const seen1 = fog.countSeen();
  const vis1 = fog.countVisible();
  H.checkTrue('갱신하면 주변이 보인다 (' + vis1 + '칸)', vis1 > 0);
  H.checkTrue('본 칸 >= 보이는 칸', seen1 >= vis1);
  let inR = true;
  for (let y = 0; y < 48; y++) {
    for (let x = 0; x < 48; x++) {
      if (fog.isVisible(x, y)
        && !(Math.abs(x - 24) <= L.SIGHT_R && Math.abs(y - 34) <= L.SIGHT_R)) inR = false;
    }
  }
  H.checkTrue('시야 반경 안에만 보인다', inR);
  fog.update(m, 24, 30);
  H.checkTrue('한 번 본 칸은 기억한다', fog.countSeen() >= seen1);
  H.checkTrue('시야 반경 밖은 보이지 않는다', !fog.isVisible(24, 45));
  fog.update(m, 24, 20);
  H.checkTrue('멀어져도 기억은 남는다 (' + fog.countSeen() + '칸)',
    fog.isSeen(24, 34) && !fog.isVisible(24, 34));

  // ---- 조명 단계
  fog.update(m, 24, 34);
  H.check('발밑은 가장 밝다', fog.lightOf(24, 34, 24, 34), 15);
  H.checkTrue('멀수록 어둡다',
    fog.lightOf(30, 34, 24, 34) < fog.lightOf(25, 34, 24, 34));
  let inRange = true;
  for (let y = 0; y < 48; y++) {
    for (let x = 0; x < 48; x++) {
      if (fog.isVisible(x, y)) {
        const l = fog.lightOf(x, y, 24, 34);
        if (!(l >= 7 && l <= 15)) inRange = false;
      }
    }
  }
  H.checkTrue('보이는 칸의 조명은 7..15', inRange);
  H.check('안 본 칸은 0', fog.lightOf(0, 0, 24, 34), 0);

  return H.done();
}
