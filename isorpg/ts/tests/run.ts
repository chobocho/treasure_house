// 테스트 러너. 파이썬은 파일 하나에 프로세스 하나지만 여기서는 한 프로세스가
// 모듈을 차례로 돌린다 — Makefile 의 PYTESTS 와 같은 순서, 같은 출력 형식이다.
import { run as fixedRun } from './test_fixed';
import { run as projRun } from './test_proj';
import { run as sortRun } from './test_sort';
import { run as mapRun } from './test_map';
import { run as pathRun } from './test_path';
import { run as rasterRun } from './test_raster';
import { run as losRun } from './test_los';
import { run as diceRun } from './test_dice';
import { run as saveRun } from './test_save';
import { run as primRun } from './test_prim';
import { run as traceRun } from './test_trace';
import { run as engineRun } from './test_engine';

const MODULES: Array<() => number> = [
  fixedRun, projRun, sortRun, mapRun, pathRun, rasterRun,
  losRun, diceRun, saveRun, primRun, traceRun, engineRun,
];

let bad = 0;
for (const m of MODULES) bad += m();
process.exit(bad ? 1 : 0);
