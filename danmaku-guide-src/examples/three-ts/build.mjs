import { build } from 'esbuild';
import { execFileSync } from 'node:child_process';
import { mkdirSync, readFileSync, writeFileSync, readdirSync, existsSync } from 'node:fs';
const src = new URL('../../', import.meta.url);
const license = readFileSync(new URL('LICENSE-THREE.txt', import.meta.url), 'utf8');
// #region strict-check
execFileSync(process.execPath, [new URL('tsc.mjs', src).pathname, '--strict', '--noEmit', '-p',
  new URL('./', import.meta.url).pathname], { stdio: 'inherit' });
// #endregion
// #region setup-bundle
const result = await build({ entryPoints: [new URL('main.ts', import.meta.url).pathname], bundle: true, loader: { '.glsl': 'text' },
  format: 'iife', target: 'es2022', supported: { 'template-literal': false }, minify: true, banner: { js: '/*\n' + license + '\n*/' }, write: false });
mkdirSync(new URL('dist/', src), { recursive: true });
writeFileSync(new URL('dist/three-setup.html', src),
  '<!doctype html><html lang="ko"><meta charset="utf-8"><title>Three 설치 확인</title>' +
  '<body style="margin:0;background:#081523"><script>' + result.outputFiles[0].text + '</script></body></html>');
console.log('Three 0.186.1: strict 검사와 오프라인 번들 생성 완료');
// #endregion

// #region level-build
for (const folder of readdirSync(new URL('./', import.meta.url)).filter((name) => /^lv[1-7]$/.test(name))) {
  const base = new URL(folder + '/', import.meta.url), label = 'three-' + folder;
  execFileSync(process.execPath, [new URL('tsc.mjs', src).pathname, '--strict', '--noEmit', '-p', base.pathname], { stdio: 'inherit' });
  const result = await build({ entryPoints: [new URL(existsSync(new URL('entry.ts', base)) ? 'entry.ts' : 'main.ts', base).pathname],
    bundle: true, loader: { '.glsl': 'text' }, format: 'iife', target: 'es2022', supported: { 'template-literal': false }, minify: true, banner: { js: '/*\n' + license + '\n*/' }, write: false });
  await build({ entryPoints: [new URL('game.ts', base).pathname], bundle: true, loader: { '.glsl': 'text' }, format: 'esm', platform: 'node',
    outfile: new URL('dist/' + label + '-logic.mjs', src).pathname });
  writeFileSync(new URL('dist/' + label + '.html', src), '<!doctype html><html lang="ko"><meta charset="utf-8"><title>' +
    label + '</title><body style="margin:0;background:#081523"><script>' + result.outputFiles[0].text + '</script></body></html>');
}
// #endregion

await build({ entryPoints: [new URL('demo.ts', import.meta.url).pathname], bundle: true, loader: { '.glsl': 'text' },
  format: 'iife', target: 'es2022', supported: { 'template-literal': false }, minify: true, banner: { js: '/*\n' + license + '\n*/' },
  outfile: new URL('dist/three-demo.js', src).pathname });

// #region performance-build
const performanceBundle = await build({ entryPoints: [new URL('performance/benchmark.ts', import.meta.url).pathname],
  bundle: true, format: 'iife', target: 'es2022', supported: { 'template-literal': false }, minify: true,
  banner: { js: '/*\n' + license + '\n*/' }, write: false });
writeFileSync(new URL('dist/three-performance.html', src),
  '<!doctype html><html lang="ko"><meta charset="utf-8"><title>Three 성능 측정</title><body><script>' +
  performanceBundle.outputFiles[0].text + '</script></body></html>');
// #endregion
