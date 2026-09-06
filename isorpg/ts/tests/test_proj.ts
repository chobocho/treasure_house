// 투영과 역투영 — 마스크 방식과 대수적 역이 화면 전체에서 같은가.
import * as H from './harness';
import * as P from '../src/proj';

export function run(): number {
  H.title('proj');

  // ---- 기저와 행렬식
  H.check('e_x', P.tileToScreen(1, 0, 0), [16, 8]);
  H.check('e_y', P.tileToScreen(0, 1, 0), [-16, 8]);
  H.check('det', 16 * 8 - -16 * 8, 256);
  H.check('높이 1단계', P.tileToScreen(5, 3, 1), [32, 56]);

  // ---- 타일 -> 화면 -> 타일 왕복 (중심 픽셀)
  let bad = 0;
  for (let tx = -8; tx < 56; tx++) {
    for (let ty = -8; ty < 56; ty++) {
      const [sx, sy] = P.tileToScreen(tx, ty, 0);
      const g = P.screenToTile(sx, sy + 8);
      if (g[0] !== tx || g[1] !== ty) bad += 1;
    }
  }
  H.check('타일 중심 왕복 64x64', bad, 0);

  // ---- 마름모 정의로 직접 찾은 것과 같은가
  bad = 0;
  for (let px = -64; px <= 64; px++) {
    for (let py = -40; py <= 40; py++) {
      const a = P.screenToTile(px, py);
      const b = P.screenToTileSlow(px, py);
      if (a[0] !== b[0] || a[1] !== b[1]) bad += 1;
    }
  }
  H.check('대수적 역 == 마름모 전수 탐색 (129x81)', bad, 0);

  // ---- 마스크가 골든과 같은가
  const want = H.golden('pick_mask.txt').replace(/\n+$/, '').split('\n');
  const gotRows: string[] = [];
  for (let oy = 0; oy < 16; oy++) {
    let s = '';
    for (let ox = 0; ox < 32; ox++) s += String(P.PICK_MASK[oy * 32 + ox]);
    gotRows.push(s);
  }
  H.check('pick_mask.txt', gotRows, want);
  H.check('마스크 값은 0..3 뿐',
    Array.from(new Set(P.PICK_MASK)).sort((a, b) => a - b), [0, 1, 2, 3]);

  // ---- 전수 확인: 화면 64,000픽셀 x 카메라 5개
  const CAMS: Array<[number, number]> = [
    [0, 0], [137, 91], [-137, -91], [768, 640], [-768, -120],
  ];
  bad = 0;
  for (const [cx, cy] of CAMS) {
    for (let py = 0; py < P.SCR_H; py++) {
      const base = py + cy;
      for (let px = 0; px < P.SCR_W; px++) {
        const a = P.pickMask(px + cx, base);
        const b = P.screenToTile(px + cx, base);
        if (a[0] !== b[0] || a[1] !== b[1]) bad += 1;
      }
    }
  }
  H.check('마스크 == 대수적 역 (카메라 ' + CAMS.length + '개 x 64,000픽셀)', bad, 0);

  // ---- 마름모가 평면을 빈틈없이 덮는가: 각 타일이 정확히 256픽셀
  // 파이썬은 튜플을 그대로 dict 키로 쓰지만 JS 의 Map 은 배열을 참조로 견주므로
  // 문자열 키로 접어야 한다. 이식에서 조용히 틀리기 쉬운 자리다.
  const cnt = new Map<string, number>();
  for (let py = 0; py < 160; py++) {
    for (let px = -160; px < 160; px++) {
      const t = P.screenToTile(px, py);
      const k = t[0] + ',' + t[1];
      cnt.set(k, (cnt.get(k) ?? 0) + 1);
    }
  }
  const inner: number[] = [];
  for (const [k, v] of cnt) {
    const parts = k.split(',');
    const tx = parseInt(parts[0] as string, 10);
    const ty = parseInt(parts[1] as string, 10);
    if (-160 <= 16 * (tx - ty) - 16 && 16 * (tx - ty) + 16 < 160
      && 0 <= 8 * (tx + ty) && 8 * (tx + ty) + 16 < 160) inner.push(v);
  }
  H.checkTrue('온전히 담긴 타일이 여럿', inner.length > 20);
  H.check('그 타일들은 모두 256픽셀',
    Array.from(new Set(inner)).sort((a, b) => a - b), [256]);

  // ---- 가시 범위: 무식하게 센 것과 같은가
  bad = 0;
  for (const [cx, cy] of ([[0, 0], [100, 50], [-200, 300], [-700, 100]] as Array<[number, number]>)) {
    const [tx0, ty0, tx1, ty1] = P.visibleRange(cx, cy, cx + P.SCR_W, cy + P.SCR_H);
    const seen = new Set<string>();
    for (let py = cy; py < cy + P.SCR_H; py++) {
      for (let px = cx; px < cx + P.SCR_W; px++) {
        const t = P.screenToTile(px, py);
        seen.add(t[0] + ',' + t[1]);
      }
    }
    for (const k of seen) {
      const parts = k.split(',');
      const tx = parseInt(parts[0] as string, 10);
      const ty = parseInt(parts[1] as string, 10);
      if (tx >= 0 && tx < 48 && ty >= 0 && ty < 48) {
        if (!(tx0 <= tx && tx <= tx1 && ty0 <= ty && ty <= ty1)) bad += 1;
      }
    }
  }
  H.check('가시 범위가 화면에 나오는 타일을 모두 담는가', bad, 0);

  return H.done();
}
