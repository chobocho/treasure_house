import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const src = fileURLToPath(new URL('.', import.meta.url));
process.env.PLAYWRIGHT_BROWSERS_PATH = resolve(src, '.cache/ms-playwright');
// Termux의 Node는 PRoot 내부에서도 android를 반환하므로 Ubuntu용 ARM64 바이너리를 선택한다.
if (process.platform === 'android' && process.arch === 'arm64') process.env.PLAYWRIGHT_HOST_PLATFORM_OVERRIDE ??= 'ubuntu24.04-arm64';

export const browserOptions = { headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage'], timeout: 30000 };

const mesa = process.env.DANMAKU_WEBGL_DRIVER === 'mesa';
export const webglBrowserOptions = {
  ...browserOptions,
  args: [...browserOptions.args, '--use-gl=angle', '--use-angle=' + (mesa ? 'gl' : 'swiftshader'), '--enable-unsafe-swiftshader', ...(mesa ? ['--ignore-gpu-blocklist', '--disable-gpu-watchdog'] : [])],
  env: mesa ? { ...process.env, LIBGL_ALWAYS_SOFTWARE: '1' } : process.env
};
