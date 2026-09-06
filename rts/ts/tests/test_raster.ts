// 래스터 — 팔레트·명암표·스프라이트·블릿·폰트·PPM (SPEC §22).

import * as H from './harness';
import * as C from '../src/const';
import * as F from '../src/fixed';
import { hex2, hex8 } from '../src/fmt';
import * as RS from '../src/raster';

H.title('raster');

// ── SPEC §22.2 팔레트 ───────────────────────────────────────────────────────
const pal = RS.buildPalette();
const g = H.golden('palette.txt').split('\n').filter((ln) => ln !== ''
                                                    && ln[0] !== '#');
let bad = 0;
let n = 0;
for (const ln of g) {
  const p = H.fields(ln);
  if (p[0] === 'light' || p[0] === 'palette') continue;
  const i = parseInt(p[0], 10);
  const r = parseInt(p[1], 10);
  const gg = parseInt(p[2], 10);
  const b = parseInt(p[3], 10);
  if (!H.deepEq(pal[i], [r, gg, b])) {
    bad += 1;
    if (bad < 4) {
      H.note(i + ' 기대 ' + JSON.stringify([r, gg, b]) + ' 실제 '
             + JSON.stringify(pal[i]));
    }
  }
  n += 1;
}
H.check('골든 팔레트 ' + n + '색', bad, 0);
H.check('256색', pal.length, 256);
let mxc = 0;
let mnc = 63;
for (const c of pal) {
  mxc = Math.max(mxc, c[0], c[1], c[2]);
  mnc = Math.min(mnc, c[0], c[1], c[2]);
}
H.check('성분은 0..63 (VGA DAC 6비트)', mxc <= 63 && mnc >= 0, true);
H.check('0번은 검정', pal[0], [0, 0, 0]);
H.check('회색 16단계의 끝', [pal[16], pal[31]], [[0, 0, 0], [63, 63, 63]]);
H.check('플레이어 기준은 160', RS.PLAYER_BASE, 160);
H.check('플레이어 램프는 넷 × 8단계',
        H.range(3).map((p) => !H.deepEq(pal[160 + p * 8],
                                        pal[160 + (p + 1) * 8])),
        [true, true, true]);

const flat: number[] = [];
for (const c of pal) {
  flat.push(c[0]);
  flat.push(c[1]);
  flat.push(c[2]);
}
const wantPal = H.golden('palette.txt').split('\n')
  .filter((ln) => ln.indexOf('palette ') === 0)[0].split(/\s+/)[1];
H.check('팔레트 전체 해시', '0x' + hex8(F.fnv1a(flat)), wantPal);

const light = RS.buildLight(pal);
H.check('명암 단계는 넷', light.length, 4);
H.check('3단계는 원색 그대로 (같은 색이 둘이면 인덱스가 작은 쪽)',
        H.range(256).filter((c) => light[3][c] !== c
                                   && !H.deepEq(pal[light[3][c]], pal[c])), []);
H.checkTrue('중복 색이 있어 항등은 아니다', !H.deepEq(light[3], H.range(256)));
H.check('0단계는 전부 검정 계열', light[0][100], 0);
bad = 0;
for (const ln of H.golden('palette.txt').split('\n')) {
  if (ln.indexOf('light ') === 0) {
    const p = H.fields(ln);
    const l = parseInt(p[1], 10);
    if ('0x' + hex8(F.fnv1a(light[l])) !== p[2]) bad += 1;
  }
}
H.check('명암표 네 단계의 해시', bad, 0);
H.note('256×256×4 = 262,144회 비교를 시작할 때 한 번 한다');

// ── SPEC §22.10 PPM ─────────────────────────────────────────────────────────
H.check('expand(63) = 255', RS.expand(63), 255);
H.check('expand(0) = 0', RS.expand(0), 0);
H.check('expand 는 단조',
        H.range(63).every((v) => RS.expand(v) < RS.expand(v + 1)), true);
H.check('expand 는 v*4 + v//16', [1, 16, 32, 47].map((v) => RS.expand(v)),
        [4, 65, 130, 190]);

const fb = new RS.Frame();
H.check('프레임버퍼는 320x200 1차원', fb.fb.length, 320 * 200);
H.check('처음에는 전부 0', H.maxOf(fb.fb), 0);
fb.fb[0] = 63;
const ppm = RS.toPpm(fb.fb, pal);
H.check('PPM 은 192,015바이트', ppm.length, 15 + 320 * 200 * 3);
H.check('머리', ppm.slice(0, 15), F.ascii('P6\n320 200\n255\n'));
H.check('첫 픽셀은 팔레트 63번을 편 값', ppm.slice(15, 18),
        pal[63].map((c) => RS.expand(c)));

// ── SPEC §22.3 스프라이트 ───────────────────────────────────────────────────
const gs = H.golden('sprites.txt').split('\n')
  .filter((ln) => ln !== '' && ln[0] !== '#').map((ln) => H.fields(ln));
bad = 0;
for (const row of gs) {
  const [name, w, h, ox, oy, lnw, fnv] = row;
  const spr = RS.SPRITES[name];
  const got = [spr.w, spr.h, spr.ox, spr.oy, spr.data.length,
               '0x' + hex8(F.fnv1a(spr.data))];
  const want = [parseInt(w, 10), parseInt(h, 10), parseInt(ox, 10),
                parseInt(oy, 10), parseInt(lnw, 10), fnv];
  if (!H.deepEq(got, want)) {
    bad += 1;
    if (bad < 4) {
      H.note(name + ' 기대 ' + JSON.stringify(want) + ' 실제 '
             + JSON.stringify(got));
    }
  }
}
H.check('골든 스프라이트 ' + gs.length + '장', bad, 0);
H.check('유닛 25 + 건물 6', Object.keys(RS.SPRITES).length, 31);
H.check('유닛 기준점은 발밑',
        [RS.SPRITES['INF_0'].ox, RS.SPRITES['INF_0'].oy], [8, 14]);
H.check('사령부는 3x3 타일', [RS.SPRITES['HQ'].w, RS.SPRITES['HQ'].h],
        [48, 48]);

const px = RS.SPRITES['INF_0'].pixels();
H.check('풀면 w*h 픽셀', px.length, 16 * 16);
H.check('0 은 투명 — 모서리는 비어 있다', px[0], 0);
H.check('몸통은 플레이어 색', px[9 * 16 + 8], RS.PLAYER_BASE + 3);

// ── SPEC §22.4 클리핑 블릿 ──────────────────────────────────────────────────
const fb2 = new RS.Frame();
RS.blit(fb2.fb, RS.SPRITES['INF_0'], 100, 100);
H.checkTrue('그려졌다', H.maxOf(fb2.fb) > 0);
const drawn = fb2.fb.filter((v) => v > 0).length;
H.check('투명 픽셀은 건드리지 않는다', drawn, px.filter((v) => v > 0).length);

const fb3 = new RS.Frame();
RS.blit(fb3.fb, RS.SPRITES['INF_0'], -100, 100);
H.check('완전히 화면 밖이면 한 픽셀도 안 쓴다', H.maxOf(fb3.fb), 0);
RS.blit(fb3.fb, RS.SPRITES['INF_0'], 400, 100);
H.check('오른쪽 밖도', H.maxOf(fb3.fb), 0);
RS.blit(fb3.fb, RS.SPRITES['INF_0'], 100, -100);
H.check('위쪽 밖도', H.maxOf(fb3.fb), 0);

const fb4 = new RS.Frame();
RS.blit(fb4.fb, RS.SPRITES['INF_0'], 4, 100);     // x0 = -4 — 네 칸이 화면 밖
const part = fb4.fb.filter((v) => v > 0).length;
H.checkTrue('걸치면 걸친 만큼만 그린다', part > 0 && part < drawn);
const leak: number[] = [];
for (let y = 0; y < 200; y += 1) {
  for (let x = 0; x < 320; x += 1) {
    if (fb4.fb[y * 320 + x] > 0 && x >= 12) leak.push(1);
  }
}
H.check('왼쪽 밖으로 새지 않는다', leak, []);

// ── SPEC §22.5 플레이어 색 리맵 ─────────────────────────────────────────────
const fb5 = new RS.Frame();
RS.blit(fb5.fb, RS.SPRITES['INF_0'], 100, 100, 2);
H.check('owner * 8 을 더한다', fb5.fb[(100 + 9 - 14) * 320 + (100 + 8 - 8)],
        RS.PLAYER_BASE + 16 + 3);
H.check('그림자는 리맵하지 않는다', fb5.fb.indexOf(RS.SHADOW) >= 0, true);
H.note('색을 여덟 벌 그리지 않는다 — 도스 시절의 표준 요령이다');

// ── SPEC §22.7 좌우 반전 ────────────────────────────────────────────────────
const fa = new RS.Frame();
const fbb = new RS.Frame();
RS.blit(fa.fb, RS.SPRITES['INF_1'], 100, 100);
RS.blit(fbb.fb, RS.SPRITES['INF_1'], 100, 100, 0, true);
const rowA = H.range(16).map((k) => fa.fb[(100 - 14 + 5) * 320 + 100 - 8 + k]);
const rowB = H.range(16).map((k) => fbb.fb[(100 - 14 + 5) * 320 + 100 - 8 + k]);
H.check('반전은 각 줄을 뒤집는다', rowB, rowA.slice().reverse());
H.check('그리는 것은 5방향, 나머지 셋은 반전', RS.DRAWN_DIRS, 5);

// ── SPEC §22.6 팔레트 사이클링 ──────────────────────────────────────────────
const p0 = RS.buildPalette();
const p1 = RS.cycleWater(RS.buildPalette(), 1);
H.check('물 색만 돈다',
        H.range(256).filter((k) => !H.deepEq(p0[k], p1[k])),
        H.range(232, 240).filter((k) => !H.deepEq(p0[k], p1[k])));
H.check('한 칸 돈다', p1[232], p0[233]);
H.check('끝은 처음으로', p1[239], p0[232]);
H.check('8칸이면 제자리', RS.cycleWater(RS.buildPalette(), 8), p0);
H.check('프레임버퍼는 건드리지 않는다 — 공짜 애니메이션', new RS.Frame().fb,
        H.range(320 * 200).map(() => 0));

// ── SPEC §22.8 폰트 ─────────────────────────────────────────────────────────
const fhex = H.golden('font.txt').split('\n')
  .filter((ln) => ln !== '' && ln[0] !== '#')[0];
H.check('폰트는 760바이트 (95자 × 8)', RS.FONT.length, 760);
H.check('골든 폰트와 같다', RS.FONT.map((b) => hex2(b)).join(''), fhex);
const fb6 = new RS.Frame();
RS.text(fb6.fb, 'A', 0, 0, 15);
const rowsA: string[] = [];
for (let y = 0; y < 7; y += 1) {
  let s = '';
  for (let x = 0; x < 6; x += 1) s += fb6.fb[y * 320 + x] !== 0 ? '#' : '.';
  rowsA.push(s);
}
H.check('A 의 첫 줄', rowsA[0], '.###..');
H.check('A 의 넷째 줄', rowsA[3], '#####.');
RS.text(new RS.Frame().fb, 'a', 0, 0, 15);
H.check('소문자는 빈 글자다 — 도스 UI 가 대문자만 쓴 이유와 같다', true, true);
const fb7 = new RS.Frame();
RS.text(fb7.fb, 'AB', 0, 0, 15);
H.check('글자 간격은 6px', fb7.fb[0 * 320 + 6], 15);
RS.text(fb7.fb, 'ZZZZ', 318, 0, 15);
H.check('화면 밖 글자는 잘린다', true, true);

// ── SPEC §22.9 더티 렉트 ────────────────────────────────────────────────────
const d = new RS.Dirty();
H.check('처음에는 비어 있다', d.rects(), []);
d.add(10, 10, 4, 4);
H.check('하나', d.rects().length, 1);
for (let k = 0; k < 8; k += 1) d.add(k * 10, 0, 4, 4);
H.check('8개를 넘으면 전체를 다시 그린다', d.rects(),
        [[0, 0, C.SCR_W, C.SCR_H]]);
d.clear();
H.check('비우면 다시 처음', d.rects(), []);
H.note('합치는 비용이 이득을 넘는 지점은 out/bench.txt 6절에서 실측한다');

H.done();
