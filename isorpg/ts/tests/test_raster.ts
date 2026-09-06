// 래스터 — 클리핑, 광원표, 더티 렉트, PPM.
import * as H from './harness';
import * as R from '../src/raster';

function sumFb(fb: Uint8Array): number {
  let s = 0;
  for (let i = 0; i < fb.length; i++) s += fb[i] as number;
  return s;
}

function countNonZero(fb: Uint8Array): number {
  let s = 0;
  for (let i = 0; i < fb.length; i++) if (fb[i]) s += 1;
  return s;
}

export function run(): number {
  H.title('raster');

  const pal = R.loadPalette();
  H.check('팔레트 256색', pal.length, 256);
  // 파이썬은 (r,g,b) 튜플을 그대로 집합에 넣는다. JS 의 Set 은 배열을 참조로
  // 견주므로 문자열로 접어야 같은 뜻이 된다.
  H.check('중복된 색이 없다 (명암표 항등을 깨뜨린다)',
    new Set(pal.map((c) => c.join(','))).size, 256);
  H.checkTrue('DAC 는 6비트', pal.every((c) => c.every((v) => v >= 0 && v <= 63)));
  H.check('0번은 검정', pal[0], [0, 0, 0]);

  const light = R.buildLight(pal);
  H.check('광원표 크기', light.length, 16 * 256);
  let ident = true;
  for (let c = 0; c < 256; c++) if (light[15 * 256 + c] !== c) ident = false;
  H.checkTrue('15단계는 항등', ident);
  const zeroSet = new Set<number>();
  for (let c = 0; c < 256; c++) zeroSet.add(light[c] as number);
  H.checkTrue('0단계는 전부 검정에 가장 가까운 색', zeroSet.size <= 4);
  const lumSum = (l: number): number => {
    let s = 0;
    for (let c = 0; c < 256; c++) {
      const q = pal[light[l * 256 + c] as number] as R.Rgb;
      s += q[0] + q[1] + q[2];
    }
    return s;
  };
  let mono = true;
  for (let l = 0; l < 15; l++) if (!(lumSum(l) <= lumSum(l + 1))) mono = false;
  H.checkTrue('단계가 낮을수록 밝기 합이 줄어든다', mono);

  const spr = R.loadSprites();
  H.check('스프라이트 48개', spr.length, 48);
  const s0 = spr[0] as R.Sprite;
  H.check('0번은 tile_0', [s0.name, s0.w, s0.h, s0.ox, s0.oy], ['tile_0', 32, 16, 16, 0]);
  H.checkTrue('모든 런의 합이 폭과 같다',
    spr.every((s) => s.rows.every((row) => row.reduce((a, r) => a + r[0], 0) === s.w)));
  let dia = 0;
  for (const row of s0.rows) for (const [c, v] of row) if (v) dia += c;
  H.check('마름모 픽셀 수 256', dia, 256);

  // ---- 클리핑: 화면 밖, 걸침, 완전히 안
  const f = new R.Frame();
  f.clear(0);
  f.blitRle(s0, -1000, -1000, 15);
  H.check('완전히 밖 (왼위)', sumFb(f.fb), 0);
  f.blitRle(s0, 1000, 1000, 15);
  H.check('완전히 밖 (오른아래)', sumFb(f.fb), 0);
  f.blitRle(s0, 16, 0, 15);
  H.check('안쪽 블릿 픽셀 수', countNonZero(f.fb), 256);
  f.clear(0);
  f.blitRle(s0, 0, 0, 15);
  H.checkTrue('왼쪽으로 걸치면 잘린다', countNonZero(f.fb) > 0 && countNonZero(f.fb) < 256);
  f.clear(0);
  f.blitRle(s0, 16, R.SCR_H - 4, 15);
  H.checkTrue('아래로 걸치면 잘린다', countNonZero(f.fb) > 0 && countNonZero(f.fb) < 256);
  let bad = 0;
  for (let x = -40; x < R.SCR_W + 40; x += 7) {
    for (let y = -20; y < R.SCR_H + 20; y += 5) {
      f.clear(0);
      f.blitRle(s0, x, y, 15);
      if (f.fb.length !== R.SCR_W * R.SCR_H) bad += 1;
    }
  }
  H.check('클리핑 중 버퍼 크기 불변', bad, 0);

  // ---- 색 0 은 투명
  f.clear(7);
  f.blitRle(s0, 16, 0, 15);
  H.checkTrue('투명 픽셀은 배경이 남는다', f.px(0, 0) === 7);

  // ---- 명암: 인덱스 합이 아니라 실제 밝기(팔레트 값)로 재야 한다
  const brightness = (frame: R.Frame): number => {
    let s = 0;
    for (let i = 0; i < frame.fb.length; i++) {
      const q = pal[frame.fb[i] as number] as R.Rgb;
      s += q[0] + q[1] + q[2];
    }
    return s;
  };
  const s3 = spr[3] as R.Sprite;
  f.clear(0);
  f.blitRle(s3, 16, 0, 15);
  const bright = brightness(f);
  f.clear(0);
  f.blitRle(s3, 16, 0, 8);
  const mid = brightness(f);
  f.clear(0);
  f.blitRle(s3, 16, 0, 2);
  const dark = brightness(f);
  H.note('같은 타일 밝기 합 — 15단계 ' + bright + ', 8단계 ' + mid + ', 2단계 ' + dark);
  H.checkTrue('단계가 낮을수록 어둡다', dark < mid && mid < bright);

  // ---- 더티 렉트
  let d = new R.Dirty();
  d.add(10, 10, 20, 20);
  d.add(15, 15, 20, 20);
  d.merge();
  H.check('겹치는 둘은 하나로', d.rects.length, 1);
  d = new R.Dirty();
  d.add(0, 0, 10, 10);
  d.add(300, 190, 40, 40);
  d.merge();
  H.check('먼 둘은 그대로', d.rects.length, 2);
  H.check('화면 밖은 잘린다', d.rects[1], [300, 190, 20, 10]);
  d = new R.Dirty();
  d.add(-50, -50, 10, 10);
  d.merge();
  H.check('완전히 밖이면 버린다', d.rects.length, 0);

  // ---- 팔레트 사이클링
  const p2 = R.cyclePalette(pal, 1);
  H.check('물 구간이 한 칸 돈다', p2[R.WATER_LO], pal[R.WATER_LO + 1]);
  H.check('물 구간 끝이 앞으로', p2[R.WATER_HI], pal[R.WATER_LO]);
  H.check('물 밖은 그대로', p2.slice(0, R.WATER_LO), pal.slice(0, R.WATER_LO));
  H.check('한 바퀴 돌면 원래대로', R.cyclePalette(pal, 16), pal);

  // ---- PPM
  f.clear(15);
  const ppm = R.toPpm(f.fb, pal);
  H.check('PPM 크기', ppm.length, 192015);
  H.check('PPM 머리말', Array.from(ppm.subarray(0, 15)),
    Array.from(Buffer.from('P6\n320 200\n255\n', 'latin1')));
  H.check('흰색은 255,255,255', Array.from(ppm.subarray(15, 18)), [255, 255, 255]);
  f.clear(0);
  H.check('검정은 0,0,0', Array.from(R.toPpm(f.fb, pal).subarray(15, 18)), [0, 0, 0]);

  return H.done();
}
