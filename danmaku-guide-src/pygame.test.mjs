import { test } from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync, writeFileSync, readdirSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { inspectDeck, checkRule } from './validate.mjs';

test('pygame의 모든 Python 단위·렌더·기준 기록 검사를 실행한다', { timeout: 120000 }, () => {
  const dir = new URL('examples/pygame', import.meta.url);
  assert.ok(existsSync(dir), 'pygame 예제와 테스트가 있어야 한다');
  const venv = new URL('.cache/pygame-venv/bin/python', import.meta.url);
  const python = existsSync(venv) ? venv.pathname : 'python3';
  const result = spawnSync(python, ['-m', 'unittest', 'discover', 'examples/pygame', '-v'], { cwd: new URL('.', import.meta.url), env: { ...process.env, SDL_VIDEODRIVER: 'dummy', SDL_AUDIODRIVER: 'dummy', PYGAME_HIDE_SUPPORT_PROMPT: '1' }, encoding: 'utf8', timeout: 110000 });
  assert.equal(result.status, 0, result.stdout + result.stderr);
  assert.match(result.stderr, /Ran [1-9][0-9]* tests?/);
  const paths = readdirSync(dir, { recursive: true }).filter((name) => /\.(py|json|sh)$/.test(name) || name === 'requirements.txt').sort().map((name) => 'pygame/' + name);
  writeFileSync(new URL('examples/pygame/TESTED.txt', import.meta.url), paths.join('\n') + '\n');
});

test('pygame의 각 완료 단계는 독립된 40장 장과 실행 안내를 제공한다', () => {
  for (const level of [1, 2, 3, 4, 5, 6, 7]) {
    const file = new URL(`parts/2${level}-pygame-lv${level}.html`, import.meta.url);
    assert.ok(existsSync(file), `Lv${level} 장이 있어야 한다`);
    const html = readFileSync(file, 'utf8');
    const d = inspectDeck('<main class="prose">' + html + '</main>');
    assert.ok(d.slides.length >= 40);
    assert.ok(html.includes(`pygame/commands.sh#pygame-lv${level}`));
    assert.ok(html.includes(`captures/pygame-lv${level}.txt`));
  }
});

test('pygame 설치 장의 최소 분량과 실행 출처를 검사한다', () => {
  const part = new URL('parts/20-pygame-setup.html', import.meta.url);
  assert.ok(existsSync(part), '설치 장이 있어야 한다');
  const d = inspectDeck('<main class="prose">' + readFileSync(part, 'utf8') + '</main>');
  const nav = JSON.parse(readFileSync(new URL('nav.json', import.meta.url), 'utf8')).filter((n) => ['part2', 'ch2-setup'].includes(n.id));
  assert.equal(nav.length, 2);
  // 부 목표는 이후 단계와 함께 늘어나므로 부 검사는 pygame 조각 전체에 적용한다.
  const parts = readdirSync(new URL('parts/', import.meta.url)).filter((name) => /^2\d-.*\.html$/.test(name)).sort().map((name) => readFileSync(new URL('parts/' + name, import.meta.url), 'utf8')).join('\n');
  assert.deepEqual(checkRule('V21', inspectDeck('<main class="prose">' + parts + '</main>'), nav), []);
  assert.ok(d.slides.length >= 21);
});

test('pygame 마무리는 배포·측정 실행 출처와 25장을 갖춘다', () => {
  const file = new URL('parts/28-pygame-wrap.html', import.meta.url);
  assert.ok(existsSync(file), '배포·디버깅 장이 있어야 한다');
  const html = readFileSync(file, 'utf8');
  assert.equal(inspectDeck('<main class="prose">' + html + '</main>').slides.length, 25);
  assert.ok(html.includes('pygame/tools.py#profile-run'));
  assert.ok(html.includes('captures/pygame-profile.txt'));
});
