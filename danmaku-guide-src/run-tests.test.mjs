import { test } from 'node:test';
import assert from 'node:assert/strict';
import { copyFileSync, existsSync, mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync, chmodSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { setTimeout as sleep } from 'node:timers/promises';

// 실행기가 외부 신호로 끝나도 Xvfb가 고아로 남아 로그를 쏟아내지 않는지 가짜 Xvfb로 확인한다.
// PRoot의 Xvfb는 부모가 사라진 뒤 poll 오류를 무한히 출력해 /tmp 로그를 수십 GB로 키운 적이 있다.
const NOISE = 'poll: Function not implemented';

function alive(pid) {
  try { process.kill(pid, 0); } catch { return false; }
  // 끝났지만 아직 회수되지 않은 좀비는 아무것도 쓰지 못하므로 끝난 것으로 본다.
  try { return !/^\d+ \(.*\) Z/.test(readFileSync(`/proc/${pid}/stat`, 'utf8')); } catch { return false; }
}

async function waitFor(check, ms) {
  for (const end = Date.now() + ms; Date.now() < end; await sleep(50)) if (check()) return true;
  return check();
}

function sandbox(t, testBody) {
  const root = mkdtempSync(join(tmpdir(), 'danmaku-runner-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const bin = join(root, 'bin');
  mkdirSync(bin);
  const pidFile = join(root, 'xvfb.pid');
  // 표시 번호를 fd 3에 알린 뒤 실제 고장 난 Xvfb처럼 표준 에러에 같은 줄을 계속 쓴다.
  // 파일로 리다이렉트된 실제 상황처럼 읽는 쪽이 사라져도 SIGPIPE로 죽지 않게 한다.
  writeFileSync(join(bin, 'Xvfb'), `#!/bin/sh\ntrap '' PIPE\necho $$ > '${pidFile}'\necho 77 >&3\nexec 3>&-\nwhile :; do echo '${NOISE}' >&2; sleep 0.02; done\n`);
  chmodSync(join(bin, 'Xvfb'), 0o755);
  copyFileSync(new URL('run-tests.mjs', import.meta.url), join(root, 'run-tests.mjs'));
  writeFileSync(join(root, 'three.test.mjs'), `import { test } from 'node:test';\n${testBody}\n`);
  return { root, bin, pidFile };
}

function start(t, { root, bin }) {
  // 실행기를 별도 프로세스 그룹으로 띄워, 실패한 실행기가 남긴 고아까지 마지막에 그룹째 끝낸다.
  // 그러지 않으면 남은 프로세스가 파이프를 붙잡아 이 검사 자체가 멈춘다.
  // 바깥 node --test가 넘긴 NODE_TEST_CONTEXT가 남으면 안쪽 node --test가 자식 모드로 바로 끝나므로 지운다.
  const env = { ...process.env, PATH: bin + ':' + process.env.PATH };
  delete env.NODE_TEST_CONTEXT;
  const child = spawn(process.execPath, ['run-tests.mjs'], { cwd: root, detached: true, env, stdio: ['ignore', 'pipe', 'pipe'] });
  t.after(() => {
    try { process.kill(-child.pid, 'SIGKILL'); } catch {}
    child.stdout.destroy();
    child.stderr.destroy();
  });
  let output = '';
  child.stdout.on('data', (chunk) => { output += chunk; });
  child.stderr.on('data', (chunk) => { output += chunk; });
  return { child, output: () => output };
}

for (const signal of ['SIGTERM', 'SIGINT']) {
  test(`실행기가 ${signal}로 끝나면 Xvfb와 검사 프로세스를 함께 정리한다`, { skip: process.platform !== 'android', timeout: 20000 }, async (t) => {
    // 타이머가 없으면 node가 빈 이벤트 루프로 보고 검사를 먼저 끝내므로 실제로 붙잡아 둔다.
    const box = sandbox(t, "test('멈춘 검사', () => new Promise(() => { setInterval(() => {}, 1000); }));");
    const run = start(t, box);
    assert.ok(await waitFor(() => existsSync(box.pidFile), 10000), '가짜 Xvfb가 시작되어야 한다');
    const pid = Number(readFileSync(box.pidFile, 'utf8'));
    await sleep(300);
    assert.equal(run.child.exitCode, null, '신호를 보내기 전에 실행기가 끝나면 안 된다');
    run.child.kill(signal);
    const [code] = await once(run.child, 'exit');
    assert.ok(await waitFor(() => !alive(pid), 3000), 'Xvfb가 남아 있으면 안 된다: ' + (existsSync(`/proc/${pid}/stat`) ? readFileSync(`/proc/${pid}/stat`, 'utf8').slice(0, 60) : ''));
    assert.equal(code, 128 + (signal === 'SIGINT' ? 2 : 15), '신호 종료는 128+신호 번호로 보고해야 한다');
    assert.ok(!run.output().includes(NOISE), 'Xvfb 표준 에러가 실행기 출력으로 새면 안 된다');
  });
}

test('검사가 정상 종료되면 Xvfb도 끝나고 종료 코드는 0이다', { skip: process.platform !== 'android', timeout: 20000 }, async (t) => {
  const box = sandbox(t, "test('통과', () => {});");
  const run = start(t, box);
  const [code] = await once(run.child, 'exit');
  const pid = Number(readFileSync(box.pidFile, 'utf8'));
  assert.equal(code, 0, run.output());
  assert.ok(await waitFor(() => !alive(pid), 3000), 'Xvfb가 남아 있으면 안 된다');
  assert.ok(!run.output().includes(NOISE), 'Xvfb 표준 에러가 실행기 출력으로 새면 안 된다');
});
