// 통합 — 프레임 렌더, 정렬, 카메라, 화면이 실제로 그려지는가.
import * as H from './harness';
import * as C from '../src/camera';
import * as G from '../src/game';
import * as R from '../src/raster';

export function run(): number {
  H.title('engine');

  // ---- 카메라 클램프
  H.check('클램프 왼쪽', C.clampCam(-99999, 0)[0], C.WORLD_X0);
  H.check('클램프 오른쪽', C.clampCam(99999, 0)[0], C.WORLD_X1 - R.SCR_W);
  H.check('클램프 위', C.clampCam(0, -99999)[1], C.WORLD_Y0);
  H.check('클램프 아래', C.clampCam(0, 99999)[1], C.WORLD_Y1 - R.SCR_H);
  H.checkTrue('데드존 안에서는 안 움직인다',
    H.deepEq(C.follow(0, 0, R.SCR_W / 2 + 10, R.SCR_H / 2 + 5), C.clampCam(0, 0)));
  H.checkTrue('데드존 밖이면 따라간다',
    C.follow(0, 0, R.SCR_W / 2 + 200, R.SCR_H / 2)[0] !== C.clampCam(0, 0)[0]);

  // ---- 한 프레임 렌더
  const g = new G.Game();
  // render() 는 내부 버퍼를 그대로 돌려준다(복사하지 않는다). 비교하려면 스냅샷을 떠야 한다.
  const fb = Uint8Array.from(g.render());
  H.check('프레임버퍼 크기', fb.length, 320 * 200);
  H.checkTrue('화면이 비어 있지 않다', new Set(Array.from(fb)).size > 8);
  let drawn = 0;
  for (let i = 0; i < fb.length; i++) if (fb[i]) drawn += 1;
  H.checkTrue('그린 픽셀이 절반 넘는다', drawn > (320 * 200) / 2);

  // ---- 같은 상태면 같은 그림
  H.check('렌더는 순수하다 (같은 상태를 두 번 그리면 같다)', Uint8Array.from(g.render()), fb);

  // ---- 진행하면 그림이 바뀐다
  for (let i = 0; i < 40; i++) g.tick();
  H.checkTrue('40틱 뒤 화면이 달라진다', !H.deepEq(Uint8Array.from(g.render()), fb));

  // ---- 정렬 순환 절단이 폭주하지 않는가
  H.checkTrue('순환 절단 누적이 적다 (' + g.cycleBreaks + '회)', g.cycleBreaks < 50);

  // ---- 팔레트 사이클링은 프레임버퍼를 건드리지 않는다
  const before = Uint8Array.from(g.render());
  g.palPhase += 3;
  H.check('사이클링은 인덱스를 바꾸지 않는다', Uint8Array.from(g.render()), before);
  H.checkTrue('그런데 PPM 색은 바뀐다',
    !H.deepEq(g.renderPpm(), R.toPpm(g.render(), R.loadPalette())));

  // ---- PPM 저장
  H.check('PPM 크기', g.renderPpm().length, 192015);

  return H.done();
}
