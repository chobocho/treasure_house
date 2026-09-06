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
- 2026-09-06 08:20 — step 3 계속: `select`(49) `ai`(47) 추가, 누적 580 checks / 0 failures.
  SPEC 선행 수정: §12.4 우클릭 문맥은 "정제소"가 아니라 **반납처**(사령부·정제소)이고 판정
  순서도 명세(적 정제소는 반납이 아니라 공격); §17.1 에 FSM 상태 번호표 추가 — 전투 유닛과
  채집기가 `state` 바이트 하나를 나눠 쓰므로 번호가 겹치면 해시가 같은 값을 두 뜻으로 읽는다.
  번호는 `const` 가 소유하고 `test_const` 가 SPEC 표와 대조한다. 덱 소재 하나: 영향 지도는
  보병 한 기(전력 19)를 3회 확산 만에 0 으로 만든다 — 12로 나누는 내림이 밀집만 남긴다.
  전차(전력 42)는 이웃까지 번진다. 시험에 둘 다 넣었다.
  Next: `sim` → `net` → `replay` → `speaker` → `raster` → `render` → `main`.
- 2026-09-06 08:55 — step 3 계속: `sim`(71) 추가 + `fixed.fnv1a`(골든 13절로 검증),
  `move.crossed`, 투사체 명중 튜플에 종류 추가. 누적 658 checks / 0 failures, 전체 11초.
  SPEC 선행 수정: §18.1 Order 는 여섯 칸이고 정렬 안 된 목록은 **그 자리에서 터진다**;
  §12.4 명령 종류에 `TRAIN` 추가(건물에게 내리는 유일한 명령 — UI·AI·스크립트가 같은
  자료형으로 sim.step 에 들어와야 락스텝이 성립한다); §16.4 BUILD 는 그 자리에 즉시
  엔티티를 만들고 ST_BUILD 로 짓는다(짓는 중에도 발자국을 막으므로 경로가 돌아간다);
  §17.5 빌드 오더는 AI_PERIOD=15틱마다.
  설계 함정 하나를 기록해 둔다: 6단계(사망)에서 시야를 반납할 때 **엔티티의 현재 타일이
  아니라 안개가 알고 있는 타일**에서 빼야 한다. 4단계에서 이미 움직였고 7단계가 아직
  안 돌았기 때문이다. `sight_at[i]` 를 따로 둔 이유이며 14부 소재다.
  64x64 시작 맵 120틱 2회 재현: 해시열 완전 일치, 불변식 R·F 유지.
  Next: `net` → `replay` → `speaker` → `raster` → `render` → `main`.
- 2026-09-06 09:20 — step 3 계속: `net`(22) `replay`(30) 추가. 누적 710 checks / 0 failures, 14초.
  **SPEC §19.4 를 실측으로 정정했다.** 초안의 "fpmul 을 실수로 하면 디싱크한다"는 이 엔진에서
  **거짓**이다 — 16.16 곱은 커야 2^42, 배정밀도 가수는 53비트, 65536 은 2의 거듭제곱이라
  실수 계산이 정수와 비트 단위로 같다(시험으로 24쌍 확인). 실제로 어긋나는 것은 **누적**이라
  주입 버그를 "대각 진행량 = st/√2 를 실수로 누적"으로 바꿨다. 측정: 해시는 **1틱**에 갈리는데
  타일 좌표는 **600틱까지 한 칸도** 안 갈린다 — 상태 해시가 없으면 이 버그를 못 본다는
  19부의 논지가 실측으로 선다. §20.2 리플레이 본문에 틱 번호(4)를 넣고 명령 칸 이름을
  §18.1 의 a·b·c 로 맞췄다. 64x64 지형 평면 4096B → RLE 1090 · LZSS 697 (실측만 쓴다).
  Next: `speaker` → `raster` → `render` → `main`, 그다음 4단계(골든 동결).
- 2026-09-06 09:35 — step 3 계속: `speaker`(27) 추가. 누적 737 checks / 0 failures.
  골든 14절 24음 전수 대조. 음표표는 실수 계산 대신 **정수 Hz 반올림 표를 소스에 박았다** —
  세 언어가 같은 표를 갖는 편이 실수 연산을 맞추는 것보다 싸고 확실하다.
  Next: `raster`(팔레트·명암표·스프라이트가 절차적으로 생성되어야 하므로 SPEC §22.2/§22.3 에
  레이아웃 표를 먼저 추가할 것) → `render` → `main`.
- 2026-09-06 10:05 — step 3 계속: `raster`(56) 추가 + 골든 생성기 셋(`gen_palette` `gen_sprites`
  `gen_font`) 과 `golden/palette.txt` `sprites.txt` `font.txt`. 누적 793 checks / 0 failures.
  SPEC 보강: §22.2 팔레트 레이아웃 표(램프 식 `c0 + (c1-c0)*i//7`, 지형 램프 6벌과 MINI_COLOR
  대응), §22.3 스프라이트 작도 규칙(유닛 16x16 정수 원 + 방향 표시, 건물 발자국 크기),
  §22.8 폰트는 **49자만 그린다**(공백·대문자·숫자·기호 12자, 소문자 없음 — 도스 UI 가 대문자만
  쓴 이유를 덱에 적는다). 폰트는 획 정의에서 만들어 16진 문자열 하나로 얼리고 세 언어가
  그 문자열을 박는다 — 760바이트를 세 번 옮겨 적는 것보다 틀릴 자리가 적다.
  gen_palette/gen_sprites/gen_font 는 **독립 구현이 아니라 동결기**라고 파일 첫머리에 적었다.
  다만 스프라이트 몸통 원만은 정의(dx²+dy²<=r²)로 그려서 엔진의 §6.2 span 알고리즘을 검증한다.
  블릿의 좌우 반전은 상자 안에서 뒤집는다 — 기준점이 1px 옮겨지지만 세 언어가 같은 자리에
  그리는 것이 그보다 중요하다(주석에 적음). 렌더 결과를 PNG 로 눈으로 확인했다.
  Next: `render` → `main`, 그다음 4단계(골든 동결).
- 2026-09-06 10:40 — **step 3 완료**: `render`(39) `main`(7+16) 추가. 25개 시험 855 checks /
  0 failures, 전체 21초. `python3 -m rts.main prim` 이 `golden/prim.txt` 를 **바이트 단위로
  재현**한다(첫 시도에 일치) — 이것이 엔진 전체와 독립 참조 구현의 대조다.
  SPEC 보강: §23.1 에 **유닛 숨기기는 5단계(안개)가 못 한다**를 적었다. 명암표는 어둡게 만들
  뿐이라 탐험된 칸의 유닛이 비쳐 보인다 — 2단계에서 visible 인 칸만 그린다. 초안이 틀렸고
  23부에 그대로 싣는다. 지형 타일은 그림이 아니라 색이며, 오토타일 마스크는 "다른 지형 쪽
  가장자리 1px" 로만 보인다(5부의 그림). §18.3 에 trace.jsonl 의 키 순서·공백을 못 박았다 —
  세 언어의 JSON 직렬화기를 믿지 않고 문자열을 손으로 만든다.
  실측: 리플레이 200틱 1130바이트(재생 해시 일치) · lockstep 200틱 일치 · float_bug 는 해시
  1틱/타일 -1 · bench(A* 480회 0.64초 · JPS 0.43초 · 시뮬 200틱 1.43초 · 렌더 10프레임 0.12초).
  Next: **4단계** — trace.jsonl·hashes.txt·replay.bin·프레임·speaker 해시 동결.
- 2026-09-06 11:20 — **4단계 완료**: `golden/trace.jsonl`(1200줄) `hashes.txt` `replay.bin`(1153B)
  동결, `make py` 가 prim·trace·hashes 세 개를 골든과 바이트 비교해 통과. 시험 871 checks / 0.
  시나리오를 실제로 굴려 보니 **버그가 다섯 개 나왔다.** 전부 시험으로 못 박았다.
  (1) 채집기가 건물 **원점**으로 명령받으면 §8.6 의 대체 목표가 "지금 서 있는 칸"을 돌려줄 수
      있다(d83 동점, 타일 번호 작은 쪽 승). 플레이어 0 의 수입이 게임 내내 **0** 이었다.
      → `econ.dock()` 으로 발자국에 접한 칸을 골라 명령한다. SPEC §16.2 에 규칙을 적었다.
  (2) `nearest_ore` 가 도달 불가 광맥을 고를 수 있었다 → 연결 성분(§4.6)으로 걸러낸다.
  (3) 채집 경로 위에 잡힌 건물 자리는 **영원히** 실패한다 → §16.5 에 "내 유닛이 막았으면
      비키게 한다"를 넣고 `sim._shove` 구현. 밀면서 동시에 짓지는 않는다(불변식 R).
  (4) 스크립트와 AI 가 한 지갑을 쓰면 서로의 건설을 굶긴다 → 골든 시나리오는 **AI 끄기**,
      AI 러시 타이밍은 `main aigame` 별도 실행(§18.6).
  (5) 큐에 든 유닛이 인구를 예약하지 않아 상한이 헐거웠다(16/10) → `econ.reserved()`.
  그 밖에: 건설 명령은 다섯 번 재시도(§18.6), 건물 자리는 플레이어 0 것만 고르고 1 은 2회
  대칭으로 뒤집는다(각자 고르면 정제소–광맥 거리가 달라 360틱에 560 대 1460 이 됐다),
  정찰을 §17.5 여섯째 줄(방어)에 붙였다 — 없으면 적 기지를 영영 몰라 다섯째 줄이 발화하지
  않는다(명중 0건이었다).
  덱 소재로 남는 실측: 시나리오는 첫 명중 970틱·첫 사망 984틱, 양쪽 5건물 완성.
  AI 게임은 여섯 줄이면 인구 10 에서 멈추고 첫 접촉 1178틱, 일곱째 줄(발전소)을 더하면
  병력은 두 배(인구 18)가 되는데 첫 접촉은 1193틱으로 **거의 그대로** — 러시 타이밍을 정하는
  것은 생산이 아니라 정찰과 이동 거리다. `main aigame7` 로 재현한다.
  리플레이 1153바이트 vs 상태 스냅샷 1200틱 × 4KB. bench: A* 480회 0.55초 · 시뮬 200틱 1.03초.
  Next: 5단계(lua/rts) · 6단계(ts/src) — 두 서브에이전트로 병렬 가능.
- 2026-09-06 12:40 — **5단계 완료 (서브에이전트)**: `lua/rts` 24파일 7,596줄 + `lua/tests` 27파일
  5,161줄 + `lua/tools/love_headless`. `make lua` 871 checks / 0, `make love` 동일.
  prim·trace·hashes 세 골든 모두 **바이트 일치**(오케스트레이터가 직접 cmp 로 확인).
  덤: `out/py_tests.txt` 와 `out/lua_tests.txt` 가 **바이트 단위로 같다** — 두 언어의 시험
  로그를 줄 단위로 diff 할 수 있다. LuaJIT·Lua 5.5·LÖVE 11.5 셋 다 통과.
  제약 감사 통과: `lua/rts` 에 비트 연산자·bit 라이브러리·goto·정수나눗셈 연산자 없음,
  실수는 `move.lua` 의 `SQRT2`(주입 버그 전용) 하나뿐, UTF-8 no BOM·LF.
  포팅에서 나온 발견 하나: `raster.text()` 는 **UTF-8 코드포인트** 단위로 돌아야 한다.
  파이썬의 `for ch in s` 가 글자당 6px 를 전진하는데 바이트로 돌면 한글 한 글자에서
  12px 가 밀려 PPM 파리티가 깨진다.
- 2026-09-06 13:05 — **6단계 완료 (서브에이전트)**: `ts/src` 25파일 6,593줄 + `ts/tests` 27파일
  4,319줄. `make ts` 871 checks / 0, `tsc --strict` 오류 0(noUnusedLocals·noImplicitReturns 포함).
  prim·trace·hashes 세 골든 **바이트 일치**. `out/ts_tests.txt` 도 `py_tests.txt` 와 바이트 일치.
  **세 언어 파리티 전부 통과**(out/parity.txt): 골든 셋 × 3언어, 렌더 PPM 192,015바이트가
  py == lua == ts, 시험 로그도 셋이 같다.
  TS 쪽 발견: `Math.floor(a/b)` 는 2^53 근처에서 한 단위를 잃는다 — CPython 의 float_divmod
  알고리즘을 그대로 옮겼다. 비트 연산자는 `ts/src` 전체에 없고 `1 << k` 는 POW2 표로 대체.
  printf 가 없어 `ts/src/fmt.ts`(68줄) 를 따로 두었다 — `pyRepr` 이 13절의 파이썬 `%r` 을 재현한다.
  `.gitignore` 에 `/rts/ts/node_modules/`·`/rts/ts/dist/` 추가(26MB·555KB, 재생성 가능).
  Next: 7단계 프런트엔드(pygame·LÖVE·Canvas + 덱 데모), 9단계 나머지 부.
- 2026-09-06 14:10 — **7단계 절반 (서브에이전트)**: `py/rts_pygame`(616줄) + `lua/love`(754줄).
  `make shots` 가 PNG 9장을 쓰고 **1200틱 해시가 골든과 전부 일치**, 틱 1200 프레임이
  `out/frame_1200.ppm` 과 바이트 일치. LÖVE 레코더도 같은 프레임버퍼 FNV(F73A3672)를 낸다 —
  두 프런트엔드가 엔진을 비켜 가지 않았다는 증거. 프런트엔드에 시뮬 상태를 쓰는 줄은 없다
  (grep 으로 확인, 유일한 히트는 "쓰면 안 된다"는 주석).
  **정직하게 남길 한계**: 이 환경의 LÖVE 는 창을 못 연다(dummy 드라이버에 OpenGL 없음).
  대화형 경로는 가짜 love.graphics 위에서 5프레임·입력 7건을 리허설했을 뿐 **실제 화면에서
  본 적이 없다**. pygame 창도 마찬가지이며 PNG 로만 확인했다. 25부에 그렇게 적는다.
  BUILD 명령은 두 UI 모두 없다(배치 고스트가 필요) — TRAIN 만 연결.
  **엔진이 프런트엔드에 준 마찰(12단계 리뷰 대상)**:
  (1) 명령 완료 신호가 없다 — `EV_ORDER` 는 적용 시점이고 §12.4 큐를 sim 이 모른다.
      시프트 큐를 프런트엔드가 `ST_IDLE` 폴링으로 흉내내고 있다.
  (2) `Orders.push` 가 STOP 을 삼킨다(명세대로지만 함정).
  (3) 스프라이트 알파 마스크가 없어 `select.pick` 용 마스크를 프런트엔드마다 다시 만든다
      — 웹까지 세 벌이 된다. `raster.mask()` 를 넣을 만하나, 넣으면 세 언어를 같이 고쳐야
      하고 시험 로그 바이트 일치가 깨지므로 리뷰에서 한꺼번에 판단한다.
  (4) 프런트엔드가 원하는 접근자가 `_` 로 시작한다(`sim._base_of`, `render._fill`).
  (5) `render.draw` 가 쓰지 않는 팔레트를 인자로 받는다.
  (6) `select.in_view` 는 화면 좌표, `render.edge_scroll` 은 뷰포트 좌표 — VIEW_X=0 이라
      우연히 일치할 뿐이다.
- 2026-09-06 14:55 — **7단계 완료 (서브에이전트)**: `ts/src/web`(canvas·minirts·data) + `tsconfig.web.json`
  + `tools/gen_webdata.py`·`bundle_web.py`·`check_web.js`·`check_demos.js` + `deck/engine.js`(273KB,
  모듈 27개) + `deck/demos.js`(77KB). `make web` 이 **브라우저 번들로 골든 트레이스를 다시 만들어
  100,608바이트 바이트 비교**를 통과한다(vm 의 가짜 window 에서 평가 — require 로 하면 브라우저
  전용 버그를 놓친다). `make demos` 19개 전부 통과, `make ts` 여전히 871/0.
  덱이 요구한 데모는 8개였는데 내가 그동안 부를 더 써서 19개가 되었고 전부 구현되었다.
  전부 `window.__rts.require` 로 **진짜 엔진**을 부른다 — 재구현이 하나 있는데(`influence-map`
  의 확산 슬라이더, `ai.spread` 가 모듈 사설이라) 그 데모가 스스로 `ai.influence()` 와
  704/704칸 일치를 확인하고 어긋나면 붉게 표시한다.
  받은 지적 둘을 반영: `make web` 의 `gen_webdata` 를 `tsc` 앞으로 옮겼고(낡은 data.ts 를 묶는
  사고 방지), 27부에 `mini-rts` 데모 슬라이드를 넣었다.
  `check_demos.js` 가 다시 쓰였다 — 이제 `deck/sections/*.html` 의 실제 마크업을 파싱해 DOM 을
  만들고, **등록되지 않은 data-demo 가 있으면 실패**한다. 옛 스텁은 모든 선택자에 null 을
  돌려줘서 깨진 데모도 통과시켰다.
- 2026-09-06 15:30 — **10·11단계 완료**: 24~26부를 `gen_fullsrc` 로 생성(파이썬 151조각·루아
  198조각·TS 164조각). **슬라이드 957장 · 소스 커버리지 100.0 % (19,274/19,274줄)** · 코드 블록
  639개 전부 원본과 일치 · 2.5 MB 자기완결형(외부 리소스 참조 0). index.html 카드와 README
  항목을 실제 숫자로 넣고 덱 수를 78 로 갱신.
  `make all` 전부 통과: py·lua·ts 시험 871×3, 브라우저 번들 트레이스 바이트 일치, PPM 세 언어
  일치, 락스텝 300틱 × 3언어 일치, float_bug 는 세 언어 모두 해시 1틱 / 타일 -1.
  Next: 12단계 리뷰 — (1) 프런트엔드가 보고한 엔진 마찰 여섯 항목 판단, (2) 덱의 모든 숫자를
  out/ 과 대조하는 2차 리뷰.
- 2026-09-06 12:13 — **12단계 리뷰 완료**. 덱 본문의 모든 숫자를 `out/` 과 대조했다.
  **사실오류 12건**: ① 명암표 0.065초 ② 렌더 6ms ③ "386 에서 6ms" ④ 프레임당 8ms
  ⑤ 전체 화면 0.006초 → 전부 `out/bench.txt` 의 실제 값(0.1초·10ms 안팎·0.008초)으로,
  ⑥ 란체스터 "A 17기" → 이산 시뮬은 **16기**(17.32 는 연속 폐형해),
  ⑦ **§25.4 의 500틱** → 대각 보정(§13.1)을 잊은 값. 실제로 (8,8)→(55,55) 를 재면 **752틱**.
  명세를 고치고 27부의 "명세가 틀린 자리" 를 여섯 → **일곱**으로 늘렸다,
  ⑧ d83 "항상 과소평가" → `mn/mx = 3/8` 에서 **+6.8 % 과대평가**(극대점이 계수와 같다),
  ⑨ dab ±3.96 % → 16.16 반올림 계수로는 **±4.02 %**, ⑩ "정리 29개" → **22개**,
  ⑪ 화면 "400틱" → 산출물은 **300틱**(800틱까지 늘려도 −1 인 것은 본문에 명시),
  ⑫ "병력이 두 배" → **26기 → 44기**.
  **마크업 27건**: `<div class="note">…</p>` — div 를 `</p>` 로 닫고 있었다. 전 파일 태그 균형 0건.
  **표기 6건**: 슬라이드 957→**977**, 엔진 19,274→**19,800줄**, 명세 오류 여섯→일곱,
  "26절"→"§0–§26", 0부에 프런트엔드 2,267줄 행 추가, `const`·`ts/src/fmt.ts` 커버리지 반영.
  **엔진 마찰 여섯 항목은 고치지 않고 27부에 두 장으로 실었다.** 고치면 `trace.jsonl` 과
  871건 시험 로그를 다시 얼려야 하고, `data-src` 653개가 어긋난다 — 그 대가를 표로 적었다.
  위험한 것은 여섯째(`select.in_view` 는 화면 좌표, `render.edge_scroll` 은 뷰포트 좌표 —
  `VIEW_X = 0` 이라 우연히 일치)뿐이고 경고 상자로 남겼다.
  검증: `make all` 전부 통과 · 역검증 653블록 0불일치 · 데모 19/19 · **977장 · 2,637 KB**
  · 커버리지 19,800/19,800 (100.0 %) · 외부 리소스 참조 0.
  **2차 리뷰(같은 작업 안에서)**: 손으로 쓴 `<pre class="term">` 블록 중 숫자를 담은 89개와
  27부의 파리티 요약표를 전부 원본과 대조했다 — `prim.txt` 14,398바이트 · 트레이스·해시 각
  1,200줄 · 871 assertions · 줄 수 차 35 % · `crc16("123456789") = 0x29B1` ·
  `lzss_encode(b"A"*8) = 01 41 00 04` · 사각파 진폭 0x40/0xC0 · G = 1638 ·
  `ORDER_MAX = 8` · 버킷 64개 · 다익스트라 636칸 → A* 144칸 · HPA* 평균 1.082(23줄) ·
  왕복 8타일 191틱/0.5235 · 이론 0.3676 대 실측 0.3333(−9.3 %) · D₄ 궤도 크기 합 47.
  **새로 나온 오류는 없다.**
