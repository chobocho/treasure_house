// 프리미티브 보고서가 골든과 바이트 단위로 같은가.
import * as H from './harness';
import { primReport } from '../src/main';

export function run(): number {
  H.title('prim');

  const got = primReport();
  const want = H.golden('prim.txt');

  const gl = got.split('\n');
  const wl = want.split('\n');
  H.check('줄 수', gl.length, wl.length);
  let bad = 0;
  const n = Math.min(gl.length, wl.length);
  for (let i = 0; i < n; i++) {
    if (gl[i] !== wl[i]) {
      bad += 1;
      if (bad <= 5) {
        console.log('  ' + (i + 1) + '줄 다름');
        console.log('    기대 ' + H.show(wl[i]));
        console.log('    실제 ' + H.show(gl[i]));
      }
    }
  }
  H.check('다른 줄', bad, 0);
  H.check('전체 바이트', got === want, true);
  H.note('보고서 ' + gl.length + '줄 · ' + Buffer.byteLength(got, 'utf8') + '바이트');

  return H.done();
}
