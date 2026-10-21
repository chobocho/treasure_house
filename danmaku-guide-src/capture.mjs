import { mkdirSync, writeFileSync, readdirSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const src = dirname(fileURLToPath(import.meta.url));
const env = { ...process.env, SDL_VIDEODRIVER: 'dummy', SDL_AUDIODRIVER: 'dummy', PYGAME_HIDE_SUPPORT_PROMPT: '1' };
mkdirSync(join(src, 'captures'), { recursive: true });
const result = execFileSync('bash', ['examples/pygame/commands.sh', 'setup', '--frames', '2'], { cwd: src, env, encoding: 'utf8' });
writeFileSync(join(src, 'captures/pygame-setup.txt'), result, 'utf8');
const paths = ['captures/pygame-setup.txt'];
// 수학 슬라이드의 수치 예시는 손으로 쓰지 않고 실제 실행 출력만 싣는다.
for (const topic of ['vectors', 'angles', 'rotation', 'patterns', 'loop', 'collision', 'random']) {
  const output = execFileSync(process.execPath, ['examples/foundations/math.mjs', topic], { cwd: src, env, encoding: 'utf8' });
  const target = 'captures/math-' + topic + '.txt';
  writeFileSync(join(src, target), output, 'utf8');
  paths.push(target);
}
for (const name of readdirSync(join(src, 'examples/pygame')).filter((name) => /^lv[1-7]$/.test(name)).sort()) {
  const output = execFileSync('bash', ['examples/pygame/commands.sh', name, '--headless', '--frames', '1800'], { cwd: src, env, encoding: 'utf8' });
  const target = `captures/pygame-${name}.txt`;
  writeFileSync(join(src, target), output, 'utf8');
  paths.push(target);
}
for (const action of ['package', 'profile', 'diagnose']) {
  const output = execFileSync('bash', ['examples/pygame/commands.sh', action], { cwd: src, env, encoding: 'utf8' });
  const target = 'captures/pygame-' + action + '.txt';
  writeFileSync(join(src, target), output, 'utf8');
  paths.push(target);
}
for (const action of ['version', 'build', 'deploy', 'profile']) {
  const output = execFileSync('bash', ['examples/canvas-ts/commands.sh', action], { cwd: src, env, encoding: 'utf8' });
  const target = 'captures/canvas-' + action + '.txt';
  writeFileSync(join(src, target), output, 'utf8');
  paths.push(target);
}
for (const name of readdirSync(join(src, 'examples/canvas-ts')).filter((name) => /^lv[1-7]$/.test(name)).sort()) {
  const output = execFileSync('bash', ['examples/canvas-ts/commands.sh', name], { cwd: src, env, encoding: 'utf8' });
  const target = 'captures/canvas-' + name + '.txt';
  writeFileSync(join(src, target), output, 'utf8');
  paths.push(target);
}
for (const action of ['version', 'build', 'profile']) {
  const output = execFileSync('bash', ['examples/three-ts/commands.sh', action], { cwd: src, env, encoding: 'utf8' });
  const target = 'captures/three-' + action + '.txt';
  writeFileSync(join(src, target), output, 'utf8');
  paths.push(target);
}
for (const name of readdirSync(join(src, 'examples/three-ts')).filter((name) => /^lv[1-7]$/.test(name)).sort()) {
  const output = execFileSync('bash', ['examples/three-ts/commands.sh', name], { cwd: src, env, encoding: 'utf8' });
  const target = 'captures/three-' + name + '.txt';
  writeFileSync(join(src, target), output, 'utf8');
  paths.push(target);
}
execFileSync(process.execPath, ['examples/cpp-wasm/lv7/build.mjs'], { cwd: src, env, stdio: 'inherit' });
const wasmReport = execFileSync(process.execPath, ['examples/cpp-wasm/inspect.mjs', 'dist/wasm-lv7.wasm', '--summary'], { cwd: src, env, encoding: 'utf8' });
writeFileSync(join(src, 'captures/wasm-inspect.txt'), wasmReport, 'utf8');
paths.push('captures/wasm-inspect.txt');
writeFileSync(join(src, 'captures/TESTED.txt'), paths.join('\n') + '\n', 'utf8');
