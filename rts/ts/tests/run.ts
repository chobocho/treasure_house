// 모든 시험을 파이썬 Makefile 의 PYTESTS 순서대로 한 프로세스에서 돌린다.
// 순서는 SPEC.md 의 절 순서와 같고, 그것이 곧 의존 방향이다.

import * as H from './harness';

require('./test_const');
require('./test_fixed');
require('./test_rng');
require('./test_tmap');
require('./test_mapgen');
require('./test_circle');
require('./test_spatial');
require('./test_select');
require('./test_path');
require('./test_hpa');
require('./test_jps');
require('./test_flow');
require('./test_move');
require('./test_fog');
require('./test_combat');
require('./test_econ');
require('./test_ai');
require('./test_sim');
require('./test_net');
require('./test_replay');
require('./test_speaker');
require('./test_raster');
require('./test_render');
require('./test_prim');
require('./test_trace');

// 파이썬은 파일마다 프로세스가 따로라 각 파일이 sys.exit 로 결과를 알린다.
// 여기서는 한 프로세스이므로 종료 코드만 모아서 낸다 — 출력 줄을 더 찍으면
// py/tests 의 로그와 바이트가 어긋나고, 덱이 두 로그를 나란히 싣지 못한다.
const [, bad] = H.totals();
process.exit(bad > 0 ? 1 : 0);
