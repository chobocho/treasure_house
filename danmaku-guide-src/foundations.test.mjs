import { test } from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { inspectDeck, checkRule } from './validate.mjs';

const url = new URL('examples/foundations/core.mjs', import.meta.url);
const core = existsSync(url) ? await import(url) : {};

test('사분파 다항식은 사분면·음수·회전 경계에서 정확하다', () => {
  assert.equal(typeof core.dsin, 'function');
  for (let i = -360; i <= 720; i++) {
    const t = i / 360;
    assert.ok(Math.abs(core.dsin(t) - Math.sin(t * Math.PI * 2)) < 1e-8);
    assert.ok(Math.abs(core.dcos(t) - Math.cos(t * Math.PI * 2)) < 1e-8);
  }
});
test('정규화는 영벡터·축·대각선에서 속도를 보존한다', () => {
  assert.equal(typeof core.direction, 'function');
  assert.deepEqual(core.direction(0, 0), [0, 0]);
  assert.deepEqual(core.direction(3, 4), [.6, .8]);
  assert.ok(Math.abs(Math.hypot(...core.direction(1, 1)) - 1) < 1e-12);
});
test('원 충돌은 접선·미세한 이격·음수 좌표를 구분한다', () => {
  assert.equal(typeof core.overlaps, 'function');
  assert.ok(core.overlaps(0, 0, 2, 5, 0, 3));
  assert.equal(core.overlaps(0, 0, 2, 5.001, 0, 3), false);
  assert.ok(core.overlaps(-5, -5, 2, -5, -5, 0));
});
test('풀은 0·가득 참·중간 삭제를 처리하고 모든 열을 교환한다', () => {
  assert.equal(typeof core.Pool, 'function');
  assert.equal(new core.Pool(0).add(0, 0, 0, 0), -1);
  const p = new core.Pool(2);
  assert.equal(p.add(1, 2, 3, 4), 0);
  assert.equal(p.add(5, 6, 7, 8), 1);
  assert.equal(p.add(9, 9, 9, 9), -1);
  assert.ok(p.erase(0));
  assert.equal(p.count, 1);
  assert.deepEqual([p.x[0], p.y[0], p.vx[0], p.vy[0]], [5, 6, 7, 8]);
  assert.equal(p.erase(-1), false);
  assert.ok(p.erase(0));
  assert.equal(p.erase(0), false);
  assert.throws(() => new core.Pool(-1), /용량/);
});
test('네 패턴이 유한한 속도로 탄환을 만든다', () => {
  assert.equal(typeof core.emitPattern, 'function');
  for (const mode of ['ring', 'fan', 'spiral', 'wave']) {
    const p = new core.Pool(64);
    core.emitPattern(p, mode, 8, 2, 20, 30, 7, 240, 600);
    assert.equal(p.count, 8);
    for (let i = 0; i < p.count; i++) assert.ok(Math.abs(Math.hypot(p.vx[i], p.vy[i]) - 2) < 1e-7);
  }
});
test('파동은 시간에 따라 흔들리고 한 발사 안에서 겹치지 않는다', () => {
  const turns = (tick) => {
    const p = new core.Pool(16);
    core.emitPattern(p, 'wave', 6, 2, 0, 0, tick, 0, 100);
    return Array.from({ length: 6 }, (_, i) => Math.atan2(p.vy[i], p.vx[i]) / (2 * Math.PI));
  };
  const first = turns(0), quarter = turns(45);
  for (let i = 1; i < 6; i++) assert.ok(Math.abs(first[i] - first[i - 1] - .025) < 1e-6);
  for (let i = 0; i < 6; i++) assert.ok(Math.abs(quarter[i] - first[i] - .12) < 1e-6);
});
test('부채꼴은 탄수가 많아도 반 바퀴 안에서 겹치지 않는다', () => {
  for (const n of [1, 7, 20, 21, 64]) {
    const p = new core.Pool(64);
    core.emitPattern(p, 'fan', n, 2, 0, 0, 0, 0, 100);
    const turns = Array.from({ length: n }, (_, i) => Math.atan2(p.vy[i], p.vx[i]) / (2 * Math.PI));
    assert.ok(turns.at(-1) - turns[0] <= .5 + 1e-9, `탄수 ${n}`);
    for (let i = 1; i < n; i++) assert.ok(turns[i] > turns[i - 1], `탄수 ${n}`);
    if (n > 1 && n <= 20) assert.ok(Math.abs(turns[1] - turns[0] - .025) < 1e-6);
  }
});
test('나선만 짧은 주기로 이어 쏘아 회전 궤적을 만든다', () => {
  assert.deepEqual(core.PATTERN_PERIODS, { ring: 48, fan: 48, spiral: 4, wave: 48 });
});
test('고정 스텝은 렌더 빈도에 무관하고 긴 정지를 제한한다', () => {
  assert.equal(typeof core.FixedStep, 'function');
  const a = new core.FixedStep(), b = new core.FixedStep();
  let ax = 0, bx = 0;
  for (let i = 0; i < 30; i++) a.advance(1 / 30, () => ax += 4);
  for (let i = 0; i < 144; i++) b.advance(1 / 144, () => bx += 4);
  assert.equal(ax, 240);
  assert.equal(bx, 240);
  const c = new core.FixedStep();
  c.advance(10, () => {});
  assert.equal(c.frame, 15);
  assert.throws(() => c.advance(-1, () => {}), /시간/);
});
test('xorshift32는 알려진 수열과 영 시드 고정점을 재현한다', () => {
  assert.equal(typeof core.Rng, 'function');
  const rng = new core.Rng(1);
  assert.deepEqual([rng.next(), rng.next(), rng.next()], [270369, 67634689, 2647435461]);
  assert.equal(new core.Rng(0).next(), 0);
});
test('체크섬은 음수를 내림하고 32비트로 감싼다', () => {
  assert.equal(typeof core.checksum, 'function');
  const p = new core.Pool(2);
  p.add(-.01, -.01, 0, 0);
  assert.equal(core.checksum(p), 4294967264);
});
test('나쁜 예제는 프레임 의존 이동의 차이를 드러낸다', async () => {
  const badUrl = new URL('examples/foundations/antipatterns/frame-dependent.mjs', import.meta.url);
  assert.ok(existsSync(badUrl), '나쁜 예제의 실행 파일이 있어야 한다');
  const { move } = await import(badUrl);
  assert.notEqual(move(30), move(144));
});
test('1부의 장별 최소 분량과 패턴 뷰어를 확인한다', () => {
  const partUrl = new URL('parts/10-foundations.html', import.meta.url);
  assert.ok(existsSync(partUrl), '1부 조각이 있어야 한다');
  const d = inspectDeck('<main class="prose">' + readFileSync(partUrl, 'utf8') + '</main>');
  const nav = JSON.parse(readFileSync(new URL('nav.json', import.meta.url), 'utf8')).filter((n) => n.id === 'part1' || n.id.startsWith('ch1-'));
  assert.equal(nav.filter((n) => n.kind === 'chapter').length, 7);
  assert.deepEqual(checkRule('V21', d, nav), []);
  assert.ok(d.slides.length >= 111);
  assert.ok(d.main.includes('data-demo="pattern-viewer"'));
});
const mathUrl = new URL('examples/foundations/math.mjs', import.meta.url);
const figureUrl = new URL('examples/foundations/figures.mjs', import.meta.url);
test('수치 예시는 공식대로 계산한 값을 출력한다', async () => {
  assert.ok(existsSync(mathUrl), '수치 예시 파일이 있어야 한다');
  const { topics } = await import(mathUrl);
  const out = (topic) => topics[topic]().join('\n');
  assert.match(out('vectors'), /\(0\.6, 0\.8\), 길이 1/);
  assert.match(out('vectors'), /길이 5\.656854/);
  assert.match(out('angles'), /회전수 0\.4 = .*접은 값 0\.1, dsin 0\.587785/);
  assert.match(out('angles'), /회전수 0\.9 = .*접은 값 -0\.1, dsin -0\.587785/);
  assert.match(out('rotation'), /\(-0\.156434, 0\.987688\), 길이 1$/m);
  assert.match(out('patterns'), /보이는 회전 0\.045/);
  assert.match(out('patterns'), /틱 60: 0\.3539/);
  assert.match(out('loop'), /논리 스텝 60번/);
  assert.match(out('loop'), /α = 0\.5, 0, 0\.5/);
  assert.match(out('collision'), /피격 true[\s\S]*피격 false[\s\S]*그레이즈 true/);
  assert.match(out('random'), /270369, 67634689, 2647435461/);
  assert.match(out('random'), /416 × 10324440 \+ 256/);
});
test('그림 모듈은 외부 참조 없는 SVG를 만들고 화살촉 id가 겹치지 않는다', async () => {
  assert.ok(existsSync(figureUrl), '그림 모듈이 있어야 한다');
  const { figures, figureSvg } = await import(figureUrl);
  const ids = [];
  for (const name of Object.keys(figures)) {
    const svg = figureSvg(name);
    assert.match(svg, /^<svg xmlns="http:\/\/www\.w3\.org\/2000\/svg" viewBox="0 0 \d+ \d+"/, name);
    assert.ok(svg.endsWith('</svg>'), name);
    assert.ok(!/<script|\bhref=|url\(\s*['"]?https?:|NaN|undefined|Infinity/.test(svg), name);
    assert.match(svg, /aria-label="[^"]{5,}"/, name);
    ids.push(...[...svg.matchAll(/ id="([^"]+)"/g)].map((m) => m[1]));
  }
  assert.equal(new Set(ids).size, ids.length);
  assert.ok(Object.keys(figures).length >= 20);
  assert.throws(() => figureSvg('없음'));
});
test('공통 예제의 실행 검증 목록을 기록한다', () => {
  assert.ok(existsSync(url));
  writeFileSync(new URL('examples/foundations/TESTED.txt', import.meta.url), 'foundations/core.mjs\nfoundations/viewer.mjs\nfoundations/antipatterns/frame-dependent.mjs\nfoundations/math.mjs\nfoundations/figures.mjs\n');
});
