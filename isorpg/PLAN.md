# IsoRPG — the mathematics of DOS-era quarter-view RPGs (deck + 3-language engine)

Agent-facing plan (for the Opus build session). Language: English here; **all
user-facing output and all deck body text is Korean.** Follow the global
`~/.claude/CLAUDE.md` (Korean reports, TDD RED→GREEN, one task = one commit) and
the repo `CLAUDE.md` (self-contained deck, template.html, Fold 374/768 px, index +
README cards). This plan is modelled on `hexwar/PLAN.md`, which produced a 544-slide
deck with the same rules — reuse its tooling wherever possible.

## Goal

One self-contained slide deck at repo root:

    도스_쿼터뷰_RPG_수학_해부.html      target 380–420 slides (hard minimum 300)

plus a committed, runnable 3-language implementation of the same quarter-view
(2:1 dimetric, "쿼터뷰") RPG engine under `isorpg/`:

    isorpg/py/    Python 3.14  engine (pure stdlib) + pygame-ce front-end   (reference)
    isorpg/lua/   Lua 5.1-compatible engine (runs on luajit AND love 11.5) + LÖVE front-end
    isorpg/ts/    TypeScript 5 engine (node tests) + Canvas front-end that also runs LIVE inside the deck

The deck teaches the **mathematics** (linear algebra of the projection,
fixed-point arithmetic, painter's-algorithm ordering as a DAG, octile A*,
Bresenham, LCG/Hull–Dobell, dice convolution, CRC over GF(2), diamond-square…),
each theorem followed by working code from the three implementations, then the
captured output that proves it.

## Non-negotiables (identical to hexwar)

1. Every code block in the deck comes from a real file under `isorpg/` and is
   verified byte-for-byte by `deck/verify_deck.py`. No hand-typed code in slides.
2. Every terminal/output block comes from a real run captured under `isorpg/out/`.
3. The three engines are proven equivalent by golden vectors: identical primitive
   results, identical scripted-scenario trace, byte-identical 320×200 8-bit PPM frames.
4. Every historical/hardware claim (game titles, years, studios, Mode 13h numbers,
   PIT frequency, Borland LCG constants…) is verified with WebSearch before it goes in.
   Never invent a number. Keep a `deck/claims.md` ledger: claim → source URL → slide id.
5. Deck opens offline as a single file: no CDN, no web fonts, no external images.
6. Korean body text; comments in the engine sources in Korean too (repo convention).
7. Deck HTML is a build artifact. Never edit it by hand — edit `deck/sections/*.html`
   and rebuild.

## Environment (verified 2026-09-06 — do not re-discover)

| Tool | Status | Notes |
|---|---|---|
| python3 3.14.4 | ok | `pygame-ce 2.5.8` installed via `pip install --break-system-packages pygame-ce` (plain `pygame` has no 3.14 wheel). **Headless works:** `SDL_VIDEODRIVER=dummy`, `pygame.image.save()` writes PNG. |
| luajit 2.1 | ok | `/data/data/com.termux/files/usr/bin/luajit`. Use this for Lua tests (fast). |
| love 11.5 | ok (binary) | apt-installed; dpkg reported a post-install error but `love` runs. **Headless works** with `t.window = nil; t.modules.window=false; t.modules.graphics=false` in conf.lua + `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy`. **love.graphics cannot run** (no OpenGL) → no LÖVE screenshots, ever. |
| lua (5.5.1) | avoid | Termux `lua` is 5.5 — has no `bit` library and different integer semantics. The Lua engine must be **5.1 syntax** (no `//`, no `&`, use `bit.band` etc.); run it only under luajit / love. |
| node 24.18 | ok | `tsc` 5.9.3 lives in `hexwar/ts/node_modules/.bin/tsc`. Pin `"typescript": "^5.9.3"` in `isorpg/ts/package.json`; if `npm i` fails (network), `cp -r hexwar/ts/node_modules isorpg/ts/`. Latest TypeScript (native binary) does NOT run on android-arm64. |
| rsvg-convert | ok | Render SVG figures to PNG and Read them to eyeball (`sh tools/check_figs.sh`). CSS vars don't work inside SVG — hex colours only. |
| Playwright | unusable | node reports platform=android. Use the DOM stub `tools/check_demos.js` (copy from hexwar) to run deck demos without a browser. |
| RAM | tight | Galaxy Fold, ~300 MB free. **At most 2 subagents, never more than one compiler/JVM at a time, `free -m` before heavy steps.** Checkpoint often; the OS may kill the session. |

## Repository layout

    isorpg/
      PLAN.md              this file; append a dated progress log at the bottom (no history.md in this repo)
      SPEC.md              normative engine spec — written FIRST, fixes all three ports
      Makefile             make all | py | lua | love | ts | parity | bench | frames | golden | verify-log
      golden/              prim.txt (hand-derived), pick_mask.txt, palette.txt, tiles.rle, map.txt,
                           script.txt (scripted inputs), trace.jsonl (frozen from reference)
      py/isorpg/           engine modules (see below) — stdlib only
      py/isorpg_pygame/    pygame-ce front-end: main.py (window/input/blit/scaling), shots.py (headless screenshots)
      py/tests/            test_prim.py test_engine.py test_trace.py test_fixed.py test_sort.py …
      lua/isorpg/          engine (Lua 5.1)          lua/love/  main.lua conf.lua (front-end)   lua/tests/
      lua/tools/           love_headless/ (conf with t.window=nil) + gfx_recorder.lua (love.graphics stub)
      ts/src/              engine                    ts/src/web/  canvas front-end + deck demos
      ts/tests/  ts/package.json  ts/tsconfig.json
      tools/               gen_prim.py gen_palette.py gen_tiles.py gen_map.py gen_script.py
                           ppm2png.py gen_figs.py check_figs.sh measure.py check_demos.js
      out/                 every captured run: *_prim.txt *_trace.txt parity.txt bench.txt frame_*.ppm/png shots/*.png
      deck/                sections/NN-*.html  order.txt  build_deck.py  verify_deck.py  chunks.py  demos.js  figs/  claims.md

Copy `hexwar/deck/{build_deck.py,verify_deck.py,chunks.py}` and
`hexwar/tools/{ppm2png.py,check_figs.sh,check_demos.js}` as the starting point;
change only paths/target names. Directives available after copying:

    <!--CODE file=py/isorpg/proj.py sym=project lang=py note=...-->     (sym=A..B ranges, Class.method)
    <!--OUT file=py_prim.txt sec=3 note=...-->
    <!--FULLSRC lang=py file=py/isorpg/proj.py prefix=... title=...-->
    <div class="fig" data-svg="fig_proj.svg"></div>
    <img class="shot" data-shot="shots/pygame_town.png">

Never write line numbers by hand — `sym=` finds symbols by name.

## Engine design (one design, three ports)

**Decision: the engines rasterise into an 8-bit indexed 320×200 framebuffer
(Mode 13h), and the pygame / LÖVE / Canvas front-ends only convert palette +
blit + scale + read input.** Rationale: (a) this is literally how DOS games
worked — the deck's whole point; (b) it makes the three ports byte-comparable
(PPM parity, as in hexwar); (c) LÖVE has no headless graphics, so a LÖVE-native
renderer could never be verified here. Trade-off: the front-ends are thin. The
deck compensates with one chapter (part 16) comparing *native* draw paths
(`pygame.draw`/`Surface.blit`, `love.graphics.draw` with quads, `ctx.drawImage`)
including verified pygame screenshots and a draw-call-recorder test for LÖVE.

Fixed constants (put in SPEC §0): TW=32 TH=16 (2:1 dimetric), TZ=8 px per
height level, map 48×48 diamond layout, screen 320×200, FP = 16.16 fixed
point, palette 256 entries with 6-bit DAC values, 16 light levels.

Engine modules (same names in all three languages):

| module | contents | key math |
|---|---|---|
| `fixed` | 16.16 add/mul/div/sqrt/sin/cos tables, floordiv/mod on negatives | error bounds, isqrt, octagonal distance approx |
| `proj` | tile→screen, world(FP)→screen, screen→tile (algebraic inverse AND rect+corner-mask DOS method), visible tile range from viewport corners | 2×2 basis/inverse/determinant, L1 ball = diamond |
| `camera` | integer scroll, clamping, follow with dead zone | |
| `map` | tile array (1 byte terrain + 1 byte height packed), passability, RLE load/save, diamond-square generator, LCG | Hull–Dobell, fractal midpoint displacement |
| `sort` | painter's depth keys, multi-tile box "behind" relation, topological sort with cycle detection & split | DAG, partial order |
| `raster` | framebuffer, clipped blit, colour-key blit, RLE sprite blit, light-table shading, dirty rects, palette cycling | clipping algebra, nearest colour in RGB |
| `path` | 8-neighbour grid, Dijkstra + bucket queue, A* octile (10/14), corner-cut rule, sub-tile FP movement with diagonal 46341/65536 | admissibility/consistency proof |
| `los` | Bresenham line, LOS with height, fog bits, light radius falloff table | error-term derivation |
| `rng`/`dice` | LCG (Borland constants, verified), NdM distribution by convolution, hit/damage tables, XP curve | expectation, variance |
| `save` | serialise game state, CRC-16 table, round-trip | polynomial division over GF(2) |
| `game` | entities, turn/real-time tick at 18.2 Hz, scripted scenario runner, trace emitter | fixed timestep |
| `main` | CLI: `prim | trace | render <ppm> [step] | bench | play` | |

Budget ≈ 2,000 lines per language (≈6,000 total incl. front-ends). Full source of
all three is printed in the deck via FULLSRC + chunks.py coverage check
(every line appears exactly once).

## Golden vectors (RED before any implementation)

- `prim.txt`: ~80 hand-derived lines — projection of 12 tiles/heights, inverse of
  20 pixels (incl. negatives and diamond edges), FP mul/div/sqrt for 10 values,
  octile h for 8 pairs, dice distribution 2d6/3d6 exact fractions, CRC-16 of
  "123456789" (=0x29B1 for CCITT-FALSE — verify), first 8 outputs of the LCG from
  seed 1 (verify against a documented Borland sequence), diamond-square 5×5 from seed.
- `pick_mask.txt`: full 32×16 corner mask; the exhaustive test proves
  algebraic inverse == mask method for **all 64,000 screen pixels**.
- `sort` cases: 6 hand-drawn box configurations incl. one cycle.
- `trace.jsonl`: ~150-step scripted play (walk, open chest, fight, level up,
  save/load) frozen from the Python reference once primitives pass.
- Frames: PPM at steps {1, 30, 60, 90, 120, final}, hashed (FNV-1a) and byte-compared.

## Verification matrix

| layer | Python | Lua | TypeScript |
|---|---|---|---|
| engine unit tests | `python3 py/tests/*.py` | `luajit lua/tests/*.lua` **and** `love lua/tools/love_headless` (same tests under the real LÖVE runtime, proves 5.1/JIT compatibility) | `tsc && node dist/tests/*.js` |
| golden trace / PPM parity | `make parity` — cmp bytes | same | same |
| front-end | pygame headless (`SDL_VIDEODRIVER=dummy`) → `out/shots/*.png` shown in deck | `luajit -bl main.lua` (compiles) + `gfx_recorder.lua` stub asserts the draw-call sequence for 3 frames; **no screenshot — say so honestly in the deck** | compiled bundle embedded as `deck/demos.js`; `node tools/check_demos.js` runs every demo through the DOM stub |
| in-deck demos | — | — | 10 live demos (list below) |
| deck | `build_deck.py` → `verify_deck.py` (code+output byte match, coverage, slide count, no external URLs in `<script src>`/`<link>`) |

## Deck structure (target ≈ 400 slides)

Slide recipe per topic: 정의/정리 → 증명 스케치 (or 도해 SVG) → 코드(CODE) → 출력(OUT)/화면(shot) → 라이브 데모 → 함정/퀴즈.
Section covers use `article.section`. Every part ends with a one-slide 정리표.

| 부 | 제목 | 내용 | 장 |
|---|---|---|---|
| 0 | 표지·안내 | 조작법(←→↑↓·게임패드)·읽는 법·세 언어 소개 | 6 |
| 1 | 도스라는 무대 | 8086~486·FPU 없음·Mode 13h(320×200×256, A000h, 64,000B)·VGA DAC 6비트·PIT 18.2Hz·640KB·키보드/마우스 인터럽트 | 18 |
| 2 | 쿼터뷰 고증 | 등각 vs 2:1 다이메트릭(26.565° vs 30°)·Zaxxon/Q*bert/Knight Lore 계보·도스 RPG 실례(어스토니시아 스토리·창세기전·Ultima VIII·LBA·X-COM·Crusader·Fallout; Diablo는 Win95 경계) — 전부 WebSearch 검증 | 16 |
| 3 | 투영의 선형대수 | 3D 회전(45°+arctan(1/√2))→2D·기저벡터·2×2 행렬·행렬식·역행렬·2:1이 정수인 이유·다이아몬드 vs 지그재그 맵·높이 항 | 30 |
| 4 | 픽셀→타일 | 역행렬 풀이·floor 나눗셈과 음수·마름모 = L1 단위공·도스식 사각형+모서리 마스크 룩업·64,000픽셀 전수 일치 증명 | 22 |
| 5 | 고정소수점 | 16.16 표현·곱셈 오버플로·나눗셈·반올림·오차 상계 증명·정수 sqrt·팔각 거리 근사·sin/cos 테이블 생성 | 26 |
| 6 | 카메라와 가시 영역 | 스크롤 오프셋·뷰포트 네 모서리 역투영→타일 범위·클램프·데드존 추적 | 18 |
| 7 | 그리기 순서 | 화가 알고리즘·깊이 키 x+y·높이·서브타일 FP 깊이·다중 타일 상자의 '뒤' 관계·위상정렬·사이클 검출과 분할 | 28 |
| 8 | 스프라이트와 블릿 | 투명 컬러키·RLE 인코딩·클리핑 산술·더티 렉트·더블 버퍼·라이트 테이블(16단계 × 256색, RGB 최근접)·팔레트 사이클링(물) | 30 |
| 9 | 지형·높이·맵 생성 | 1바이트 패킹·절벽/경사 렌더·LCG(Hull–Dobell 정리)·다이아몬드-스퀘어·RLE 저장 | 22 |
| 10 | 이동과 경로 | 8방향·옥타일 거리 10/14·다익스트라·양동이 큐·A* 허용성/일관성 증명·코너 컷 규칙·대각 속도 보정 46341/65536 | 28 |
| 11 | 시야·안개·조명 | 브레젠험 오차항 유도·높이 LOS·안개 비트·감쇠 테이블 | 18 |
| 12 | 전투와 성장의 확률 | 주사위 합성곱·2d6/3d6 분포·명중 확률표·기대 피해·분산·경험치 곡선(기하/다항)·LCG 하위 비트 함정 | 26 |
| 13 | 시간·애니메이션·저장 | PIT 재프로그래밍·고정 타임스텝·프레임 스킵·보간·세이브 직렬화·CRC-16(GF(2) 다항식 나눗셈) | 18 |
| 14 | 파이썬 전문 (pygame-ce) | 엔진 전체 소스 + pygame 프런트엔드·헤드리스 스크린샷 | 30 |
| 15 | 루아 전문 (LÖVE) | 엔진 전체 소스(5.1 제약 설명) + main.lua/conf.lua·헤드리스 love 실행 로그·draw-call 레코더 | 26 |
| 16 | 타입스크립트 전문 (Canvas) | 엔진 전체 소스 + 캔버스 프런트엔드·**라이브 미니 RPG**·네이티브 그리기 경로 3종 비교 | 28 |
| 17 | 파리티 증명과 마무리 | 골든 벡터·PPM 바이트 일치·성능 비교(실측 그대로)·현대 대응표(행렬→GPU, 고정소수점→float, 화가→z-buffer)·체크리스트·참고문헌 | 16 |
| | **합계** | | **≈402** |

Live demos (TypeScript, compiled into `deck/demos.js`, each registered with
`__demo(id, fn)` per template.html; arrow-key demos MUST call
`e.preventDefault()` or the deck flips slides):
`proj-playground`, `pick`, `fixed-error`, `viewport-range`, `painter-sort`
(drag boxes, shows DAG & cycles), `rle-blit`, `diamond-square`, `astar-octile`,
`los-fog`, `dice-dist`, `lcg-bits`, `mini-rpg` (playable: walk, chest, fight, level).

Figures: ~20 inline SVGs from `tools/gen_figs.py` (projection basis, diamond
L1 ball, corner mask, box-behind relation, Bresenham error, diamond-square
steps…). Render each with rsvg and look at it before use.

## Order of work (commit boundaries)

Each numbered step is one commit (Korean, no prefix, e.g. `쿼터뷰 RPG 덱 — 3부 투영의 선형대수 30장`).
Append a dated line to the log at the bottom of this file at each step.

1. `SPEC.md` (normative, with every formula from the module table) + `deck/claims.md` skeleton.
   WebSearch the historical/hardware claims now and record sources.
2. `golden/prim.txt`, `pick_mask.txt`, sort cases — hand-derived. Tests written; RED.
3. `py/isorpg/` module by module (fixed → proj → map → sort → raster → path → los → rng → save → game → main). GREEN per module; commit per 2–3 modules.
4. Freeze `golden/trace.jsonl` + frames from the reference. Commit.
5. `lua/isorpg/` (5.1) — luajit tests green, then the same under `love` headless. Commit.
6. `ts/src/` — node tests green; PPM parity for all three (`make all`). Commit.
7. Front-ends: `py/isorpg_pygame` (+ headless shots), `lua/love` (+ recorder test), `ts/src/web` (+ check_demos). Commit each.
8. `tools/gen_figs.py`, `measure.py`, `make bench`. Commit.
9. Deck sections, part by part, in the table order; `build_deck.py` after every part so the deck always opens. Commit per part (or per 2 short parts).
10. Full-source parts 14–16 via FULLSRC; coverage must be 100 %. Commit.
11. `verify_deck.py` clean, slide count counted by script (never by hand), `index.html` card + `README.md` entry with the real slide count and the real line counts (`wc -l`). One commit.
12. Full review pass (facts, 표기, demo bugs) as a separate review commit, hexwar style: `쿼터뷰 RPG 덱 리뷰 — …정정`.

Subagent use: at most 2 in parallel (RAM). Good splits: (Lua port ‖ TS port)
after step 4; (sections 3–6 ‖ sections 7–9) in step 9. The orchestrator writes
SPEC, golden vectors and the Python reference itself — those fix everything else.

## Content rules for the deck body

- Korean, 존댓말 없이 서술체 (match hexwar deck). Theorem slides: `정의 N.M` / `정리 N.M` labels in `<span class="h">`; cross-references must resolve (script-check like optim did).
- One idea per slide; ≤ 46 code lines per slide (chunks.py default); tables ≤ 6 columns for Fold 374 px.
- Every measured number quoted in prose comes from `out/` (bench.txt, measure.py); quote timings as ranges ("약 30배"), never exact ms.
- Do not oversell: LÖVE has no screenshot here — the deck says so and shows the headless test log instead.
- `index.html` card: emoji ◆, title `도스 쿼터뷰 RPG 수학 해부`, desc mentions the three languages, total source lines, slide count, demo count — all from scripts.

## Claims to verify (starter list — add as you go)

Mode 13h 320×200×256 / 64,000 B at A000:0000; VGA DAC 6 bits/channel (262,144 colours);
PIT 1,193,182 Hz ÷ 65,536 ≈ 18.2065 Hz; true isometric 30° vs 2:1 dimetric arctan(1/2)=26.565°,
isometric tilt arctan(1/√2)=35.264°; Borland `rand()` LCG constants (22695477, +1, >>16 & 0x7FFF — verify);
Hull–Dobell (1962); Fournier–Fussell–Carpenter diamond-square (1982); Zaxxon 1982; Q*bert 1982;
Knight Lore 1984 (Filmation); 어스토니시아 스토리 1994 손노리; 창세기전 1995 소프트맥스;
Ultima VIII: Pagan 1994; Little Big Adventure 1994; X-COM: UFO Defense 1994; Crusader: No Remorse 1995;
Fallout 1997 (DOS + Win95); Diablo 1996 Win95-only; CRC-16/CCITT-FALSE check value 0x29B1;
Doom 16.16 fixed point (`FRACBITS 16`).

## Progress log
(append below: `- YYYY-MM-DD HH:MM — step N: what, commit hash`)
- 2026-09-06 00:44 — plan approved by the user as written (LÖVE screenshot limitation accepted, deck name and isorpg/ dir confirmed). Next: step 1 (SPEC.md + claims.md).
- 2026-09-06 00:57 — step 1: SPEC.md(14장, 정리 3.1~8.4) + deck/claims.md(32건 검증) + 툴체인 복사(build_deck/verify_deck/chunks/ppm2png/check_figs/check_demos)
- 2026-09-06 01:13 — step 2: 골든 벡터(prim 208줄·pick_mask·palette 256색·tiles.rle 48스프라이트·sortcase 6·script 204틱) + 파이썬 테스트 12종 RED. CORDIC 은 N=20/GUARD=8 로 오차 ±1 실측
