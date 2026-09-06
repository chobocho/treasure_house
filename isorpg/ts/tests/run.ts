// 테스트 러너. 파이썬은 파일 하나에 프로세스 하나지만 여기서는 한 프로세스가
// 모듈을 차례로 돌린다 — 출력 형식은 py/tests 와 같게 유지한다.
import { run as fixedRun } from './test_fixed';
import { run as mapRun } from './test_map';

const MODULES: Array<() => number> = [fixedRun, mapRun];

let bad = 0;
for (const m of MODULES) bad += m();
process.exit(bad ? 1 : 0);
