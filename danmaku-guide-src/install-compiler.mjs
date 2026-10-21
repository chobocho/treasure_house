import { existsSync, mkdirSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
const src = new URL('.', import.meta.url);
// PRoot의 Node 플랫폼 값과 실행할 Linux 바이너리 플랫폼이 다르다.
if (process.platform === 'android' && process.arch === 'arm64') {
  const prefix = new URL('.cache/typescript-linux/', src);
  const binary = new URL('node_modules/@typescript/typescript-linux-arm64/lib/tsc', prefix);
  if (!existsSync(binary)) {
    mkdirSync(prefix, { recursive: true });
    execFileSync('npm', ['install', '--prefix', prefix.pathname, '--force', '--ignore-scripts',
      '--no-audit', '--no-fund', '--save-exact', '@typescript/typescript-linux-arm64@7.0.2'], { stdio: 'inherit' });
  }
}
