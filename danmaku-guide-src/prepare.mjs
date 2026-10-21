import { execFileSync } from 'node:child_process';
import { build } from 'esbuild';
import { mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const src = dirname(fileURLToPath(import.meta.url));
mkdirSync(join(src, 'dist'), { recursive: true });
await build({ entryPoints: [join(src, 'examples/foundations/viewer.mjs')], bundle: true, format: 'iife', target: 'es2022', outfile: join(src, 'dist/pattern-demo.js') });

execFileSync('bash', ['examples/canvas-ts/commands.sh', 'build'], { cwd: src, stdio: 'inherit' });

execFileSync('bash', ['examples/three-ts/commands.sh', 'build'], { cwd: src, stdio: 'inherit' });
