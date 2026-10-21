import { readdirSync } from 'node:fs';
import { spawn } from 'node:child_process';
import { once } from 'node:events';

// 실행 검증 목록을 소비하는 덱 검사보다 해당 목록의 생성을 먼저 완료한다.
const files = readdirSync(new URL('.', import.meta.url)).filter((name) => name.endsWith('.test.mjs'));
const producers = files.filter((name) => /^(pygame|canvas|three|wasm)\.test\.mjs$/.test(name));
const consumers = files.filter((name) => !producers.includes(name));
let display, current;

// 실행기가 신호로 끝나도 Xvfb와 검사 프로세스가 고아로 남지 않게 프로세스 그룹째 끝낸다.
// PRoot의 Xvfb는 부모가 사라지면 poll 오류를 끝없이 출력해 리다이렉트된 로그를 수십 GB로 키웠다.
// SIGKILL은 가로챌 수 없으므로 Xvfb의 표준 에러는 처음부터 버려 최악의 경우에도 디스크를 채우지 않게 한다.
function stop(child, signal = 'SIGTERM') {
  if (!child || child.exitCode !== null || child.signalCode !== null) return;
  try { process.kill(-child.pid, signal); } catch { child.kill(signal); }
}
function cleanup() {
  stop(current);
  // 종료 직전이라 기다릴 수 없고 PRoot는 SIGTERM을 드물게 잃으므로 Xvfb는 가로챌 수 없는 SIGKILL로 끝낸다.
  stop(display, 'SIGKILL');
}
process.on('exit', cleanup);
for (const [signal, number] of [['SIGHUP', 1], ['SIGINT', 2], ['SIGTERM', 15]]) {
  process.on(signal, () => {
    cleanup();
    process.exit(128 + number);
  });
}

try {
  // PRoot의 SwiftShader는 셰이더 실행 중 종료되므로 검증된 Mesa 소프트웨어 경로를 사용한다.
  if (process.platform === 'android' && files.includes('three.test.mjs')) {
    display = spawn('Xvfb', ['-displayfd', '3', '-screen', '0', '1280x900x24', '-nolisten', 'tcp', '-ac'],
      { detached: true, stdio: ['ignore', 'ignore', 'ignore', 'pipe'] });
    const number = await new Promise((resolve, reject) => {
      display.once('error', reject);
      display.once('exit', (code) => reject(new Error('Xvfb 초기화 종료: ' + code)));
      display.stdio[3].once('data', (chunk) => resolve(String(chunk).trim()));
    });
    process.env.DISPLAY = ':' + number;
    process.env.DANMAKU_WEBGL_DRIVER = 'mesa';
    process.env.LIBGL_ALWAYS_SOFTWARE = '1';
  }
  for (const batch of [producers, consumers]) {
    if (!batch.length) continue;
    // 동기 실행은 이벤트 루프를 막아 신호 처리기가 돌지 못하므로 비동기로 기다린다.
    current = spawn(process.execPath, ['--test', '--test-concurrency=1', ...batch],
      { cwd: new URL('.', import.meta.url), detached: true, stdio: 'inherit' });
    const [code] = await once(current, 'exit');
    current = undefined;
    if (code !== 0) { process.exitCode = code ?? 1; break; }
  }
} finally {
  if (display && display.exitCode === null && display.signalCode === null) {
    stop(display);
    // SIGTERM이 전달되지 않아도 무한히 기다리지 않게 2초 뒤에는 강제로 끝낸다.
    const timer = setTimeout(() => stop(display, 'SIGKILL'), 2000);
    await once(display, 'exit');
    clearTimeout(timer);
  }
}
