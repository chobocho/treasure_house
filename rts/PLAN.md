# DOS-RTS — the mathematics and techniques of DOS-era real-time strategy games (deck + 3-language engine)

Agent-facing plan (for the Opus build session). Language: English here; **all
user-facing output and all deck body text is Korean.** Follow the global
`~/.claude/CLAUDE.md` (Korean reports, TDD RED→GREEN, one task = one commit) and
the repo `CLAUDE.md` (self-contained deck from `template.html`, Fold 374/768 px,
index + README cards). This plan is modelled on `isorpg/PLAN.md` (463 slides) and
`hexwar/PLAN.md` (544 slides) — **reuse their tooling verbatim** (build_deck,
verify_deck, chunks, check_demos, check_figs, ppm2png, gen_fullsrc, bundle_web).
Read `isorpg/PLAN.md` "Environment" and "Progress log" first: every trap listed
there applies here.

## Goal

One self-contained slide deck at repo root:

    도스_RTS_전략게임_수학_해부.html      target 940–980 slides, **hard minimum 900**

plus a committed, runnable 3-language implementation of the same 2D tile RTS
engine (Dune II / Warcraft I / Command & Conquer class: 320×200, 16×16 tiles;
Warcraft II itself ran at 640×480 SVGA — verify and say so in part 2) under `rts/`:

    rts/py/    Python 3.14 engine (pure stdlib) + pygame-ce front-end        (reference)
    rts/lua/   Lua 5.1-compatible engine (luajit AND love 11.5) + LÖVE front-end
    rts/ts/    TypeScript 5 engine (node tests) + Canvas front-end that also runs LIVE inside the deck

The deck teaches the **mathematics and engineering tricks** an RTS of 1992–1997
needed — integer geometry and distance metrics, autotiling as a function on
neighbour bitmasks, midpoint circles for sight radii, fixed point, LCG and
random maps (cellular automata, diamond-square), spatial hashing, BFS/Dijkstra/A*
with proofs, hierarchical A*, jump point search, flow fields (Dijkstra maps),
clearance/brushfire, reservation-based collision and group movement, fog as
reference-counted bit planes, combat probability and Lanchester's laws,
projectile ballistics in fixed point, harvest-rate economics, tech-tree DAGs,
finite-state-machine and influence-map AI, **deterministic lockstep networking
with state hashes**, replays, RLE/LZ compression, CRC, PIT timing, PC-speaker
frequency tables, lookup-table performance tricks — each theorem followed by
working code from the three ports and the captured output that proves it.

## Non-negotiables (identical to isorpg/hexwar)

1. Every code block in the deck comes from a real file under `rts/` and is verified
   byte-for-byte by `deck/verify_deck.py`. No hand-typed code in slides.
2. Every terminal/output block comes from a real run captured under `rts/out/`.
3. The three engines are proven equivalent by golden vectors: identical primitive
   report, identical scripted 2-player trace, identical per-tick state hashes,
   byte-identical 320×200 8-bit PPM frames.
4. Every historical/hardware claim (titles, years, studios, resolutions, tile sizes,
   IPX, the "1,500 archers on a 28.8 kbps modem" article, Lanchester 1916, Hull–Dobell
   1962, JPS 2011, HPA* 2004…) is verified with WebSearch before it goes in. Never
   invent a number. Keep `deck/claims.md`: claim → source URL → slide id.
5. Deck opens offline as a single file: no CDN, no web fonts, no external images.
6. Korean body text; Korean comments in all engine sources.
7. Deck HTML is a build artifact. Never edit it by hand — edit `deck/sections/*.html`
   and rebuild. **Always read the "오류 N건" line of the build output.**
8. 900 slides is a floor reached by depth (more worked examples, proofs, quizzes,
   measured comparisons), never by padding or by splitting one idea over two slides.
   Slide count is measured by `verify_deck.py`, never by hand.

## Environment (verified 2026-09-06 in isorpg — do not re-discover)

Same table as `isorpg/PLAN.md`: python3 3.14 + pygame-ce headless
(`SDL_VIDEODRIVER=dummy`), luajit 2.1 (Lua **5.1 syntax only**, never Termux `lua`
5.5), love 11.5 headless (no `love.graphics`, so **no LÖVE screenshots — say so**),
node 24 + `typescript@5` pinned (copy `isorpg/ts/node_modules` if npm has no
network), rsvg-convert for figures, Playwright unusable (use `check_demos.js`
DOM stub). RAM is tight: **≤ 2 subagents, ≤ 1 compiler at a time, `free -m`
before heavy steps, checkpoint after every part.** The OS may kill the session:
this file's progress log is the resume point.

Deck size: isorpg (463 slides) is 1.2 MB; expect ≈ 2.5 MB here. Keep `demos.js` +
`engine.js` bundles under 400 KB combined; check the deck still opens on the Fold
(template's page-at-a-time rendering handles it, but measure once at 500 slides).

## Repository layout

    rts/
      PLAN.md              this file; append a dated progress log at the bottom
      SPEC.md              normative engine spec — written FIRST, fixes all three ports (Korean)
      Makefile             make all | py | lua | love | ts | web | demos | parity | lockstep | bench | frames | shots | golden
      golden/              prim.txt (hand-derived) autotile.txt circle.txt palette.txt sprites.rle
                           map_*.txt (fixed maps for path tests) script.txt (2-player scripted orders)
                           trace.jsonl hashes.txt (state hash per tick) replay.bin
      py/rts/              engine modules — stdlib only
      py/rts_pygame/       pygame-ce front-end: main.py, shots.py (headless screenshots)
      py/tests/            test_<module>.py …
      lua/rts/             engine (Lua 5.1)       lua/love/ main.lua conf.lua        lua/tests/
      lua/tools/           love_headless/ + gfx_recorder.lua (draw-call recorder stub)
      ts/src/              engine                 ts/src/web/  canvas front-end + deck demos
      ts/tests/  ts/package.json  ts/tsconfig.json  ts/tsconfig.web.json
      tools/               gen_prim.py gen_autotile.py gen_circle.py gen_palette.py gen_sprites.py
                           gen_maps.py gen_script.py gen_figs.py gen_fullsrc.py gen_webdata.py
                           bundle_web.py check_web.js check_demos.js check_figs.sh ppm2png.py measure.py
      out/                 *_prim.txt *_trace.jsonl *_hashes.txt parity.txt lockstep.txt bench.txt
                           frame_*.ppm/png shots/*.png check_*.txt
      deck/                sections/NN-*.html order.txt build_deck.py verify_deck.py chunks.py
                           demos.js engine.js figs/ claims.md

Copy `isorpg/deck/{build_deck.py,verify_deck.py,chunks.py}` and
`isorpg/tools/{ppm2png.py,check_figs.sh,check_demos.js,gen_fullsrc.py,bundle_web.py,check_web.js}`;
change only paths/target names. Directives (unchanged):

    <!--CODE file=py/rts/path.py sym=astar lang=py note=...-->      (sym=A..B ranges, Class.method)
    <!--OUT file=py_prim.txt sec=7 note=...-->
    <!--FULLSRC lang=py file=py/rts/path.py prefix=... title=...-->
    <div class="fig" data-svg="fig_autotile.svg"></div>
    <img class="shot" data-shot="shots/pygame_battle.png">

Never write line numbers by hand — `sym=` finds symbols by name.

## Engine design (one design, three ports)

**Decision (same as isorpg): the engines rasterise into an 8-bit indexed 320×200
framebuffer; pygame / LÖVE / Canvas front-ends only convert palette + blit +
scale + read input.** This is how the DOS originals worked, it makes the three
ports byte-comparable, and LÖVE cannot render headless here anyway. Part 26
compares the *native* draw paths of the three front-ends separately.

**Decision: the simulation is a deterministic lockstep core from day one.**
`sim.step(orders_for_this_tick)` is the only way state changes; rendering reads
state and never writes it. Every tick ends with `hash = fnv1a(state)`; two sims fed
the same order stream must produce identical hashes in all three languages. This
single design choice is what parts 19 (lockstep) and 20 (replay) are built on.

Fixed constants (SPEC §0, adjust only in SPEC): SCR 320×200; TILE 16; map 64×64;
viewport 256×176 px = 16×11 tiles at (0,0); right panel 64 px (minimap 64×64 at
top, then selection/command panel); bottom bar 24 px; FP 16.16; palette 256 with
6-bit DAC; 4 player colours via palette remap ranges; sight radius in tiles
(1..8, circle mask); SIM tick = 1 PIT tick (18.2 Hz nominal, TICK_US 54925);
order latency 2 ticks; max 256 entities (index + 8-bit generation → 16-bit handle);
unit footprints 1×1, buildings 2×2 / 3×3.

Engine modules (same names in all three languages):

| module | contents | key math |
|---|---|---|
| `fixed` | 16.16 add/mul/div, floordiv/fmod, isqrt, dist metrics (L1, L∞, octile 8/3 exact, alpha-max-beta-min), atan8 (8-dir from dx,dy by comparisons) | error bounds, Chebyshev/octile identities |
| `rng` | LCG (Borland constants, verified), seeded per game, `roll(n)` without modulo bias | Hull–Dobell, low-bit period, rejection sampling |
| `tmap` | 64×64 terrain byte + passability byte; autotile: 8-neighbour bitmask → 47-case index via canonical table; 4-corner (16-case) variant; RLE load/save; connected-component labels (union-find) | mask function, equivalence classes under D4, UF amortised |
| `mapgen` | cellular automata (B5678/S45678 style, verify rule), diamond-square → threshold to terrain, resource placement with integer Poisson-disc, 2-fold symmetric maps | fixed points of CA, midpoint displacement |
| `circle` | midpoint circle rasteriser → sight/splash masks r=1..8, offsets list, area counts | Bresenham/midpoint error term |
| `spatial` | uniform grid buckets (8×8 tile cells), entity handles with generation, neighbour query in radius | O(1) expected query |
| `select` | point pick (AABB then mask), box select, priority rules, control groups 0–9, order queue with shift-queue | AABB intersection |
| `path` | BFS, Dijkstra (bucket queue), A* octile with corner-cut rule, closest-reachable fallback via UF labels, path cache | admissibility/consistency proofs |
| `hpa` | 8×8 clusters, entrances, abstract graph, refine | two-level graph, bounded suboptimality measured |
| `jps` | jump point search on the same grid | pruning rules, equivalence to A* cost (proved by exhaustive test on golden maps) |
| `flow` | Dijkstra map (integration field) + 8-dir gradient field; clearance (brushfire) field for 2×2 units | distance transform |
| `move` | sub-tile FP motion, diagonal 46341/65536, tile reservation, push/yield rules, deadlock breaker, formation offsets (line/column/box) rotated to 8 dirs, arrival radius | reservation invariant, no two entities on one tile |
| `fog` | explored/visible bit planes, reference-counted visibility per player, incremental add/remove of circle masks, 4-level dim render | bit-plane algebra, refcount invariant |
| `combat` | range check (Chebyshev), target priority, damage = base+pierce−armour with half-random rule (WC2 style — verify and cite), projectiles: straight (Bresenham stepper) and ballistic (fixed-point parabola), splash via circle mask, Lanchester linear/square-law simulator | expectation/variance, Lanchester closed form vs sim |
| `econ` | resources, harvester FSM (go/mine/return), harvest rate formula (round-trip → income), build queue, placement validity (footprint + clearance), tech tree DAG with topo sort and prerequisite check, supply cap | rate = amount / (2·dist/speed + mine_time) |
| `ai` | unit FSM (idle/move/attack/flee/harvest), influence map (decayed sum over grid), threat map, scripted build order, rally/defend positions, scouting | discrete convolution / decay |
| `sim` | entities SoA, order decoding, tick loop, event log, FNV-1a state hash, trigger table (condition→action), victory check | fixed timestep |
| `net` | in-process lockstep: N sims, order delay queue, "network" with configurable latency/jitter, desync detector (hash mismatch → tick) | lockstep correctness argument |
| `replay` | order-log writer/reader, CRC-16, RLE + tiny LZ77 for map/replay bytes | polynomial division over GF(2) |
| `speaker` | PIT divisor table for notes (1193182 / f), square-wave PCM synthesis to WAV bytes (golden hashed) | frequency → divisor rounding error |
| `raster` | framebuffer, clipped blit, colour-key, RLE sprites, palette remap for player colour, palette cycling (water), mirroring 5→8 dirs, bitmap font 6×8, dirty rects | clipping algebra |
| `render` | terrain layer, minimap (nearest + majority downscale), fog overlay, sprites sorted by y, health bars, cursor, panel | |
| `main` | CLI: `prim | trace | hashes | render <ppm> [tick] | lockstep | replay | bench | play` | |

Budget ≈ 3,400 lines per language (≈ 11,000 total incl. front-ends). Full source
of all three is printed in the deck via FULLSRC + chunks.py (every line exactly once).

## Golden vectors (RED before any implementation)

- `prim.txt` (~300 lines, hand-derived or from independent float reference in
  `tools/gen_prim.py`): distance metrics for 16 (dx,dy) pairs incl. negatives;
  isqrt for 12 values; atan8 for 16 vectors on/near sector boundaries; autotile
  index for all 256 neighbour masks (47 classes) and all 16 corner masks; circle
  masks r=1..8 (cell counts: verify against Gauss circle-problem values);
  LCG first 10 outputs from seed 1 (verify vs documented Borland sequence);
  CA map 16×16 from seed after 4 generations; diamond-square 9×9 from seed;
  A* / Dijkstra / BFS / JPS / HPA* path costs on 6 fixed 32×32 maps (JPS == A*
  cost exactly; HPA* ≤ 1.2× measured); flow-field values on a 12×12 map;
  brushfire clearance on the same; damage formula 12 cases; Lanchester square-law
  closed form vs 8 simulated battles; harvest rate 6 cases; PIT divisors for
  C4..B5; CRC-16/CCITT-FALSE("123456789") = 0x29B1; FNV-1a of a fixed state.
- `autotile.txt`: canonical 256 → 47 table (generated, then frozen).
- `script.txt`: ~600-tick two-player scripted game: build barracks, harvest,
  train 6 units each, group move in formation, engage in fog, projectiles,
  splash, one base destroyed → victory trigger. Orders are issued by *both*
  players with 2-tick latency.
- `trace.jsonl` + `hashes.txt`: frozen from the Python reference once primitives pass.
  `hashes.txt` is one FNV-1a per tick; `make lockstep` runs two sims through the
  in-process network with latency 2 and jitter and must reproduce it byte for byte,
  then deliberately injects one float rounding into player 2's sim and must report
  the first diverging tick (the deck shows both runs).
- `replay.bin`: order log; replaying it must reproduce `hashes.txt`.
- Frames: PPM at ticks {1, 60, 150, 300, 450, final}, hashed and byte-compared.
- `speaker.wav` bytes hashed (FNV-1a) — the three ports synthesise the same bytes.

## Verification matrix

| layer | Python | Lua | TypeScript |
|---|---|---|---|
| unit tests | `python3 py/tests/*.py` (≈ 22 files) | `luajit lua/tests/run.lua` **and** `love lua/tools/love_headless` | `tsc && node dist/tests/run.js` |
| golden prim / trace / hashes / PPM | `make parity` — cmp bytes | same | same |
| lockstep + desync injection | `make lockstep` (py) | same | same, plus live demo |
| replay round trip | `make parity` | same | same |
| front-end | pygame headless → `out/shots/*.png` in deck | `luajit -bl` compiles + `gfx_recorder.lua` asserts draw-call sequence; **no screenshot — say so** | bundle in `deck/engine.js`; `check_web.js` replays golden trace in the bundle; `check_demos.js` runs every demo through the DOM stub |
| deck | `build_deck.py` → `verify_deck.py` (byte match, FULLSRC coverage 100 %, slide count ≥ 900, no external `<script src>`/`<link>`, theorem cross-refs resolve) |

Test runner must not swallow failures: `set -o pipefail` in every Makefile pipe
(isorpg lesson). Add `make verify-log` that greps `out/*.txt` for `FAIL|실패|Error`.

## Deck structure (target ≈ 950 slides)

Slide recipe per topic: 정의/정리 → 증명 스케치 or 도해 SVG → 코드(CODE) →
출력(OUT)/화면(shot) → 라이브 데모 → 함정/퀴즈. Section covers use
`article.section`. Every part ends with 정리표 1장 + 퀴즈 2장 (answers on the
next slide, verified against `out/`). Theorem labels `정의 N.M` / `정리 N.M`.

| 부 | 제목 | 내용 | 장 |
|---|---|---|---|
| 0 | 표지·안내 | 조작법(←→↑↓·게임패드)·읽는 법·세 언어·덱 지도 | 6 |
| 1 | 도스라는 무대 | 386/486·FPU 없음·Mode 13h·VESA 640×480(WC2)·마우스 INT 33h·키보드 INT 9·PIT·EMS/XMS·IPX/NetBIOS·시리얼 모뎀 | 22 |
| 2 | RTS 고증 | Herzog Zwei 1989·Dune II 1992·WC1 1994·WC2 1995·C&C 1995·Red Alert 1996·AoE 1997·SC 1998(Win)·국산(충무공전·임진록 — 연도·개발사 WebSearch) 타일 크기·해상도·유닛 수 표 | 20 |
| 3 | RTS 의 수학 지도 | 정수 격자·거리 척도·그래프·확률·비트 연산·결정론 — 이 덱에서 어느 부가 무엇을 쓰는지 | 16 |
| 4 | 타일 맵과 오토타일 | 16×16·바이트 팩·8이웃 비트마스크→47 클래스(D4 대칭으로 분류)·4모서리 16케이스·마칭 스퀘어 대응·왕 타일·전이 테이블 생성·RLE 맵 파일 | 36 |
| 5 | 스크롤·뷰포트·미니맵 | 타일 스크롤·오프셋 산술·가장자리 스크롤·미니맵 축소(최근접 vs 다수결)·미니맵 클릭 역변환·더티 렉트 | 24 |
| 6 | 고정소수점과 정수 기하 | 16.16·오버플로·isqrt·L1/L∞/옥타일/α-max β-min 오차 상계·atan8·미드포인트 원→시야 마스크·가우스 원 문제 | 38 |
| 7 | 난수와 랜덤 맵 | LCG·Hull–Dobell·하위 비트 함정·모듈로 편향·셀룰러 오토마타 동굴/섬·다이아몬드-스퀘어→지형·정수 포아송 디스크 자원 배치·대칭 맵 | 30 |
| 8 | 스프라이트·팔레트·플레이어 색 | 시트·컬러키·RLE·플레이어 색 팔레트 리맵·물 팔레트 사이클링·5장 그려 8방향(미러)·그림자·6×8 비트맵 폰트 | 32 |
| 9 | 지형·UI 렌더링 | 타일 블릿·y 정렬·안개 오버레이 4단계·체력바·커서·패널·미니맵 합성·더티 렉트 실측 | 26 |
| 10 | 엔티티와 공간 분할 | SoA·핸들=인덱스+세대·균일 격자 버킷·반경 질의·풋프린트 1×1/2×2/3×3 점유 | 26 |
| 11 | 선택과 명령 | 픽킹(AABB→마스크)·드래그 사각 선택·우선순위·컨트롤 그룹·명령 큐·시프트 큐·문맥 우클릭 | 22 |
| 12 | 경로 탐색 I | BFS·다익스트라·양동이 큐·이진 힙·A* 옥타일 허용성/일관성 증명·코너 컷·유니온파인드 연결성분·최근접 도달점·경로 캐시 | 40 |
| 13 | 경로 탐색 II | HPA*(클러스터·입구·추상 그래프·정련·상계 실측)·JPS(가지치기 규칙·A* 와 비용 동일 전수 증명)·흐름장(다익스트라 맵·그라디언트)·브러시파이어 클리어런스 | 40 |
| 14 | 이동·충돌·군집 | 서브타일 FP·대각 보정·타일 예약 불변식·밀치기/양보·교착 해소·대형 오프셋 8방향 회전·도착 반경·스티어링 정수판 | 34 |
| 15 | 시야와 안개 | 원 마스크 증분·탐험/가시 비트 플레인·참조 카운트 불변식·플레이어별 안개·비트보드 연산·렌더 | 28 |
| 16 | 전투의 수학 | 체비셰프 사거리·타깃 우선순위·피해식(출처 명시)·기대값/분산·투사체 직선(브레젠험 스테퍼)·포물선 고정소수점·스플래시·란체스터 선형/제곱 법칙 유도와 시뮬 대조·DPS | 42 |
| 17 | 경제·생산·기술 트리 | 채집 FSM·수입률 공식·건물 배치 판정·생산 큐·기술 트리 DAG·위상 정렬·선행 조건·공급 한계·비용 곡선 | 28 |
| 18 | AI | 유닛 FSM·영향 지도(감쇠 합성곱)·위협 지도·빌드 오더 스크립트·방어 위치·정찰·러시 타이밍 실측 | 30 |
| 19 | 결정론과 락스텝 | 왜 동기 시뮬인가(1,500 궁수 논문)·명령 지연 턴·입력 큐·상태 해시·디싱크 검출 실험(부동소수점 1개 주입)·RNG 동기·IPX/모뎀·2인 시뮬 라이브 | 38 |
| 20 | 시간·저장·리플레이·압축 | PIT·고정 틱·프레임 스킵·게임 속도·직렬화·CRC-16(GF(2))·리플레이=명령 로그·RLE·LZ77 미니·맵 파일 포맷 | 28 |
| 21 | 트리거와 미션 | 조건→액션 표·승리 조건·타이머·스크립트 시나리오 실행 | 16 |
| 22 | PC 스피커 | PIT 채널 2·분주값=1193182/f·반올림 오차·사각파 WAV 합성·세 언어 바이트 일치 | 14 |
| 23 | 성능 기법 | 룩업 테이블·비트 트릭·SoA vs AoS 실측·더티 렉트 실측·경로 캐시 적중률·프로파일 (`make bench`, 실측 그대로) | 24 |
| 24 | 파이썬 전문 (pygame-ce) | 엔진 전체 소스 + pygame 프런트엔드·헤드리스 스크린샷 | 88 |
| 25 | 루아 전문 (LÖVE) | 엔진 전체 소스(5.1 제약) + main.lua/conf.lua·헤드리스 로그·draw-call 기록기 | 82 |
| 26 | 타입스크립트 전문 (Canvas) | 엔진 전체 소스 + 캔버스 프런트엔드·**라이브 미니 RTS**·네이티브 그리기 경로 3종 비교 | 92 |
| 27 | 파리티 증명과 마무리 | 골든·PPM·해시·락스텝·성능 비교·현대 대응표(락스텝→롤백 넷코드, 흐름장→GPU, 안개→셰이더)·체크리스트·참고문헌 | 22 |
| | **합계** | | **≈ 944** |

Parts 24–26 sizes follow from `wc -l` (≈ 3,400 lines / 46 per slide + module
intro slides); recompute after the engines exist and rebalance parts 4–23 if the
total lands under 900 — by adding worked examples, not filler.

Live demos (TypeScript, compiled into `deck/demos.js`, registered with
`__demo(id, fn)` per template.html; arrow-key demos MUST `e.preventDefault()`):
`autotile-paint`, `minimap-scale`, `dist-metrics`, `circle-mask`, `lcg-bits`,
`ca-map`, `diamond-square`, `palette-remap`, `spatial-grid`, `box-select`,
`astar-step`, `hpa-clusters`, `jps-jumps`, `flow-field`, `group-move`,
`fog-refcount`, `projectile`, `lanchester`, `tech-tree`, `influence-map`,
`lockstep-two-sims` (two canvases, latency slider, hash strip, "float bug" toggle
shows the desync tick), `speaker-divisor`, `mini-rts` (playable: harvest, build,
train, select, move, fight, fog, win).

Figures: ~30 inline SVGs from `tools/gen_figs.py` (autotile classes, corner
cases, circle error term, HPA clusters, JPS pruning, flow gradient, reservation
timeline, fog bit planes, parabola, Lanchester curves, lockstep timeline…).
Render each with rsvg and look at it before use.

## Order of work (commit boundaries)

Each numbered step is one commit (Korean, no prefix, e.g. `도스 RTS 덱 — 12부 경로 탐색 I 38장`).
Append a dated line to the log at the bottom of this file at each step.
Skeleton first (repo `CLAUDE.md` §5): `deck/order.txt` + 28 section files with
placeholder covers exist and the deck builds and opens **before** any body is written.

1. `SPEC.md` (normative, every formula from the module table, Korean) + `deck/claims.md`
   with WebSearch sources for part 1–2 and all cited papers. Copy tooling from isorpg.
2. Golden generators + `golden/*` (prim, autotile, circle, maps, script). Python
   tests for every module written; RED.
3. `py/rts/` in dependency order (fixed → rng → tmap → circle → spatial → mapgen →
   path → hpa → jps → flow → move → fog → combat → econ → ai → select → sim → net →
   replay → speaker → raster → render → main). GREEN per module; commit per 3–4 modules.
4. Freeze `trace.jsonl`, `hashes.txt`, `replay.bin`, frames, `speaker.wav` hash. Commit.
5. `lua/rts/` (5.1) — luajit green, then `love` headless green. Commit.
6. `ts/src/` — node green; `make all` parity for all three. Commit.
   (Steps 5 ‖ 6 may run as the two subagents; the orchestrator owns SPEC/golden/Python.)
7. Front-ends: `py/rts_pygame` (+ shots), `lua/love` (+ recorder test), `ts/src/web`
   (+ bundle + check_web + check_demos). Commit each.
8. `tools/gen_figs.py`, `measure.py`, `make bench`, `make lockstep`. Commit.
9. Deck sections part by part in table order; rebuild after every part so the deck
   always opens; commit per part (short parts may pair). Two subagents may write
   disjoint part ranges (e.g. 4–9 ‖ 10–15) from the same SPEC + out/.
10. Full-source parts 24–26 via `gen_fullsrc.py` + FULLSRC; coverage 100 %. Commit.
11. `verify_deck.py` clean (≥ 900 counted by script), `index.html` card + `README.md`
    entry with real slide count, demo count and `wc -l` totals. One commit.
12. Review pass as a separate commit, repo style:
    `도스 RTS 덱 리뷰 — 데모 버그 N종·표기 N건·사실오류 N건 정정`.
    Then a second review that greps every number in the deck against `out/`.

## Content rules for the deck body

- Korean, 서술체 (match isorpg). One idea per slide; ≤ 46 code lines per slide;
  tables ≤ 6 columns for Fold 374 px; SVG `viewBox` + `width:100%`.
- Every measured number in prose comes from `out/`; quote timings as ranges.
- Do not oversell: LÖVE has no screenshot here; HPA* is *not* optimal — print the
  measured ratio; the "float bug" desync demo is an injected bug, say so.
- Cite the damage formula, tile sizes and resolutions per game with sources; where
  a game's internals are undocumented, label the deck's rule as "이 덱의 규칙".
- `index.html` card: emoji ⚔, title `도스 RTS 전략게임 수학 해부`, desc names the
  three languages, total source lines, slide count, demo count — all from scripts.

## Claims to verify (starter list — add as you go)

Dune II 1992 Westwood 320×200 16×16 tiles; Warcraft: Orcs & Humans 1994 Blizzard
320×200; Warcraft II 1995 DOS **640×480 SVGA**, 32×32 tiles, map 32–128, damage =
(basic+piercing−armour) with random reduction (verify exact rule and source);
Command & Conquer 1995 320×200 (Gold 640×400); Red Alert 1996; Age of Empires 1997
Win95 only; StarCraft 1998 Win; Herzog Zwei 1989 Mega Drive; 충무공전 1996 (Trigger
Soft?) and 임진록 1997 (HQ Team?) — verify; "1500 Archers on a 28.8: Network
Programming in Age of Empires" (Bettner & Terrano, GDC 2001); Lanchester 1916;
Hull–Dobell 1962; Borland `rand()` LCG 22695477/1; HPA* Botea–Müller–Schaeffer 2004;
JPS Harabor–Grastien 2011; Fournier–Fussell–Carpenter 1982; midpoint circle
Bresenham 1977; Gauss circle counts N(r) for r=1..8; PIT 1,193,182 Hz; INT 33h
mouse; IPX/SPX Novell; CRC-16/CCITT-FALSE 0x29B1; FNV-1a 32-bit offset 2166136261,
prime 16777619.

## Progress log
(append below: `- YYYY-MM-DD HH:MM — step N: what, commit hash`)
- 2026-09-06 05:42 — plan approved by the user as written (320×200/16×16, deck name, rts/ dir, LÖVE no-screenshot limitation accepted). Next: step 1 (SPEC.md + claims.md).
- 2026-09-06 06:05 — step 1 done: `SPEC.md` (2,022 lines, §0–§25, 29 theorems), `deck/claims.md`
  (32 claims verified by WebSearch: 21 확인 / 6 부분 확인 / 5 정정), tooling copied from isorpg
  (`build_deck.py`, `verify_deck.py`, `chunks.py`, base head/tail, `ppm2png.py`, `check_figs.sh`,
  `check_demos.js`, `gen_fullsrc.py`, `bundle_web.py`, `check_web.js` — renamed to rts/`__rts`),
  `Makefile`, and the 28-section skeleton. Deck builds: **56 slides, 89 KB, 0 errors**, verify clean.
  Ledger corrections folded into SPEC: WC2 damage formula is officially documented
  (max = basic − armour + pierce, actual = 50–100 % of max) so §15.2 now uses it instead of an
  invented rule; Borland LCG modulus is disputed (2^32 vs 2^31) so §3.1 states the caveat;
  PIT 1,193,182 Hz is a rounded value. **임진록 is a Windows game, not DOS** — part 2 must not
  call it a DOS title; 충무공전 has only namu.wiki as a source. Bettner is the first author of
  "1500 Archers", not Terrano. Dune II / Warcraft I tile pixel sizes could NOT be confirmed —
  do not state them as fact in part 2.
  Next: step 2 (golden generators + `golden/*` + python tests, RED).
- 2026-09-06 06:35 — step 2 done: golden generators (`gen_maps.py`, `gen_autotile.py`,
  `gen_circle.py`, `gen_prim.py`, `gen_script.py`) + `golden/` (prim.txt 294 lines, autotile.txt,
  circle.txt, map_1..6, map_start, script.txt) + `out/analysis.txt` (float-only analysis the engine
  must NOT produce). `gen_prim.py` imports nothing from the engine — it is the independent reference.
  Verified across 6 maps × 24 pairs: Dijkstra == A* == JPS cost everywhere; HPA* measures 1.000–1.321×
  optimal (do NOT quote the paper's "1 %"). Three SPEC bugs found while generating and fixed:
  classic midpoint *outline* plots points outside the disc (r=2 → (2,1)) so §6.2 is now an
  addition-only exact row-span scan; α-max-β-min needed rounding (`dab(1,0)` was 0); the Lanchester
  loop must stop at `>= FP_ONE` or it never terminates (floor makes the decrement 0). All three are
  deck material. Added SPEC §25 (unit/building table, tech DAG, start conditions) and §18.6
  (scenario selector format). Scenario is **1200 ticks**, not 600 — a 47-tile diagonal takes an
  infantryman ~500 ticks. Tests are NOT written yet: an ImportError is not RED, so per-module
  tests are written in step 3 immediately before each module.
  Next: step 3 (py/rts in dependency order, RED→GREEN per module, commit per 3–4 modules).
- 2026-09-06 07:10 — step 3 in progress. Python engine modules done, each written test-first with a
  confirmed RED: `fixed` (43 checks), `rng` (15), `circle` (12), `tmap` (48), `mapgen` (22),
  `spatial` (23), `path` (16), `jps` (6), `hpa` (17) — 202 checks, 0 failures, all cross-checked
  against `golden/prim.txt`. Commits: 5beef90 (fixed/rng/circle), e70cef1 (tmap/mapgen/spatial).
  Notes for the remaining ports: `crc16` lives in `fixed`, not `replay` (both `tmap` and `replay`
  need it and `fixed` has no deps — SPEC §20.1 updated). Vehicles cannot enter HILL, so `labels()`
  keeps two union-find passes (SPEC §4.3 updated). `path.Heap` is hand-written because heapq /
  table.sort / Array.sort do not agree on order; the comparator (f, h, idx) is a total order so all
  three languages pop the same sequence. JPS == A* verified on 720 random pairs, not just the 24
  golden ones. HPA* measures 1.000–1.321× optimal (mean 1.082).
  Next: `flow` → `move` → `fog` → `combat` → `econ` → `ai` → `select` → `sim` → `net` → `replay`
  → `speaker` → `raster` → `render` → `main`.
- 2026-09-06 07:30 — step 3 계속: `const`, `flow`, `move`, `fog` 넷 추가, 각각 RED 확인 후 GREEN.
  누적 356 checks / 0 failures (const 22 · flow 26 · move 64 · fog 35 포함). SPEC 선행 수정:
  §11.1 INF=65535 고정 + 막힌 목표는 무시, §11.2 INF 칸도 후보에서 제외, §11.3 맵 밖은 0,
  §11.4 **맵 밖은 막힌 칸**(가장자리 fire=10)이고 확장은 통행 가능 칸으로만, §13.2 STOP 은
  걷던 걸음을 마친 뒤 멈춘다, §13.5 LINE/COLUMN/BOX 슬롯 공식과 접기 규칙, §25.1 이동 종류
  (TANK·HARV 만 차량), §0·§25 는 `const` 모듈이 소유(§26 파일 목록에 추가).
  §4.3 에 **건물은 통행 비트를 내린다**(`tmap.set_building`)를 못 박았다 — 예약만으로 막으면
  유닛이 건물을 향해 24틱을 두드리다 포기한다. `test_const` 는 SPEC.md 의 마크다운 표를 직접
  파싱해 대조한다(손으로 옮긴 숫자는 반드시 한 자리가 틀린다). 좁은 통로 정면 교착은 45틱에
  포기로 풀리는 것을 트레이스로 확인 — 해결이 아니라 포기이며 14부에 그렇게 적는다.
  Next: `combat` → `econ` → `ai` → `select` → `sim`.
- 2026-09-06 07:55 — step 3 계속: `combat`(61) `econ`(65) 추가, 누적 482 checks / 0 failures.
  골든 11절(피해표 12줄·란체스터 8줄)·12절(수입률 6줄) 전부 일치. 시험이 SPEC 오류 하나를
  잡았다 — §15.1 의 "짝수 mx 에서 E = 0.75·mx + 0.25" 는 **홀수**의 이야기다(올림이 홀수에서만
  한 칸 올린다). 정정하고 짝·홀 양쪽을 시험에 넣었다. SPEC 선행 수정: §15.3 에 `ttl = fp(d)/speed
  + 2` 와 `ARROW_SPEED = fp(4)`, d=0 이면 발사하지 않음; §18.4 해시 바이트열에 `cool`·`timer`·
  생산 큐·광맥 잔량 추가(빠져 있으면 재장전이 한 틱 어긋나도 해시가 같다 — 골든 해시를 아직
  만들지 않은 지금이 고칠 수 있는 마지막 시점이었다). 실측 수입률 3333/10000 vs 이론 3676/10000
  — 차이는 채집기끼리의 길막이며 17부에 그대로 싣는다.
  Next: `ai` → `select` → `sim` → `net` → `replay`.
