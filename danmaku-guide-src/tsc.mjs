import { spawnSync } from 'node:child_process';
import './install-compiler.mjs';
const androidLinux = process.platform === 'android' && process.arch === 'arm64';
const binary = new URL(androidLinux
  ? '.cache/typescript-linux/node_modules/@typescript/typescript-linux-arm64/lib/tsc'
  : 'node_modules/typescript/bin/tsc', import.meta.url);
const result = spawnSync(androidLinux ? binary.pathname : process.execPath,
  androidLinux ? process.argv.slice(2) : [binary.pathname, ...process.argv.slice(2)], { stdio: 'inherit' });
if (result.error) throw result.error;
process.exit(result.status ?? 1);
