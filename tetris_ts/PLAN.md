# PLAN — TypeScript Tetris: Core + GA AI + 8-Player Online (single unified deck)

> Execution brief for the implementing agent (Opus). Written in English per repo
> language policy (agent-to-agent). **All user-facing output, deck prose, code
> comments, and commit messages must be Korean** (see Language rules below).

## 0. Goal

Reimplement the C++ WASM Tetris trilogy — core game, genetic-algorithm AI,
8-player online battle — **entirely in TypeScript**, and publish it as **one**
self-contained slide deck:

- Deck output: `TypeScript_테트리스_AI_8인_대전.html` (repo root)
- Source of truth: `tetris_ts/` (this directory) — every line of code shown in
  the deck is cut from real files here and verified by the build's coverage check
- Target size: **500–550 slides** honestly counted. Never pad. Never overstate
  the count in README/index cards — count the actual `<section class="slide">`s.

The C++ originals to mirror (read them for structure, tone, and demo ideas):
- `../C++_WASM_테트리스_만들기.html` (152 slides)
- `../C++_WASM_테트리스_AI_대전.html` (186 slides)
- `../C++_WASM_테트리스_8인_온라인.html` (307 slides)

## 1. Hard requirements (from repo CLAUDE.md — non-negotiable)

1. Deck is a single self-contained `.html`. No external JS/CSS/CDN/fonts.
2. Controls: `←`/`→` page prev/next, `↑`/`↓` in-page scroll, Gamepad API.
   Start from the shared deck chrome (see §5 — reuse `deck/base/` head/tail
   copied from `../tetris_net/deck/base/`, which came from `template.html`).
3. Must render without clipping at Galaxy Fold widths: ~374px and ~768px.
4. **Every code example actually runs.** No pseudocode. Nothing unverified.
5. When the deck is added: add a card to `../index.html` AND a row to
   `../README.md` in the same commit.
6. Commit messages: Korean, descriptive, no type prefix (repo convention, e.g.
   `TS 테트리스 통합 덱 1부 — 코어 엔진과 골든 트레이스 검증`).
   This repo has no `history.md`; git history is the log. Commit/push via `/cp`.

## 2. Source layout to build (all code Korean-commented, `--strict` clean)

```
tetris_ts/
  package.json          # devDependency: typescript only. No runtime deps.
  tsconfig.json         # strict, ES2020 modules, outDir dist/
  src/core.ts           # board 10x20, 7-bag RNG, SRS-style rotation, gravity,
                        #   line clear, scoring — port tetris.cpp semantics 1:1
  src/ai.ts             # 8 board features + 1-move search — port ai.cpp 1:1
  src/ga.ts             # GA: tournament selection, crossover, mutation
  src/battle.ts         # garbage rules, 1:N battle referee
  src/net/protocol.ts   # binary protocol — SAME spec as ../tetris_net/protocol.md
  src/net/ws.ts         # RFC 6455 server from scratch on node:http (zero deps)
  src/net/room.ts       # room engine — 4th implementation of the golden vectors
  src/net/server.ts     # 8-player server main (serves web/ + /ws endpoint)
  src/net/server_lib.ts # APPENDIX ONLY: same server on npm `ws` (not a dep of
                        #   the main build; install ad hoc when verifying it)
  train.ts              # Node GA trainer → weights.json + ga_log.json (real runs)
  bot_client.ts         # headless websocket bot for `make match`
  web/                  # browser glue (compiled JS + minimal page for server)
  test/                 # node:test suites — see §3
  tools/trace_wasm.mjs  # dumps golden traces from ../tetris_ai/tetris_ai.wasm
  Makefile              # build / test / train / match / web / deck / clean
  deck/                 # build_deck.py + base/ + sections/ — ported from
                        #   ../tetris_net/deck (keep coverage guarantee)
scratch/                # checkpoints for intermediate outputs (gitignored)
```

Naming/identifiers in English; comments explain *why*, in Korean; keep the
existing comment style of `tetris_ai/`/`tetris_net/` sources.

## 3. Verification strategy — the backbone of this project

Existing C++ artifacts are the **answer key**. TS must reproduce them:

1. **Core parity**: `tools/trace_wasm.mjs` loads `../tetris_ai/tetris_ai.wasm`
   (see `../tetris_ai/test_ai.mjs` for the export ABI) and dumps per-seed traces
   (piece sequence, board hash per step, cleared lines, score) to
   `test/golden/core_traces.json`. TS core must reproduce every trace exactly.
   This forces the RNG and rotation rules to match the C++ ones bit-for-bit —
   port the exact algorithms, do not improvise.
2. **Protocol**: reuse `../tetris_net/protocol_vectors.json` verbatim
   (shape: `{v, note, cases}`) in `test/protocol.test.ts`.
3. **Room engine**: reuse the golden room vectors used by
   `../tetris_net/test_room.mjs` — TS room becomes the 4th implementation
   (after JS/Go/Python) that must replay them identically.
4. **GA is really trained**: `make train` runs `train.ts` (e.g. pop 32, 50
   generations) producing `weights.json` + `ga_log.json`. Deck learning curves
   plot the **measured** log, never invented numbers.
5. **8-player measured run**: `make match` starts the TS server, connects
   4 PCs × 2 seats = 8 bot clients over real websockets, plays to completion,
   prints rankings. Deck quotes real output.
6. **Deck render check**: Playwright headless chromium at 374px and 768px
   viewports; assert no horizontal overflow, pages navigable, demos boot.
7. TDD per repo SOP: write failing tests first (RED), then implement (GREEN).
   Full `make test` before every commit. Never weaken a test to pass it.

### Environment gotchas (this Android/PRoot device — do not skip)

- **TypeScript is NOT installed.** The npm-cached `tsc` package is a bogus
  squatter. Run `npm install --no-save typescript` inside `tetris_ts/`, then
  use `npx tsc`. Never `npx tsc` without the real package installed.
- Node is v24 (`node:test`, `WebSocket` client global available).
- Memory limits: at most 2 parallel subagents; **one** headless browser at a
  time; no JVM. Exceeding this gets the session killed by the OS.
- Playwright: ESM ignores NODE_PATH — symlink the cache first:
  `ln -sfn /root/.npm/_npx/e41f203b7505f1fb/node_modules node_modules`
  (chromium already at `~/.cache/ms-playwright/`). Korean shows as □ in
  screenshots (missing CJK font) — harmless, not a rendering bug.
- Files are UTF-8 no BOM, LF. Patch-edit; avoid full-file rewrites.

## 4. Makefile targets

```
make build   # npx tsc (strict) → dist/
make test    # node --test  (core parity · ai · ga · battle · protocol · ws · room)
make train   # node dist/train.js --pop 32 --gen 50 → weights.json, ga_log.json
make run     # node dist/net/server.js --port 8787  (serves web/ + /ws)
make match   # server + 8 bot seats over real websockets, prints result
make web     # assemble browser bundle from dist/ into web/
make deck    # python3 deck/build_deck.py → ../TypeScript_테트리스_AI_8인_대전.html
make clean
```

## 5. Deck build system

Port `../tetris_net/deck/` (`build_deck.py`, `hl.py`, `chunks.py`, `extra.css`,
`base/deck_head.html`, `base/deck_tail_scripts.html`):

- Keep both guarantees: (a) slide code is cut from real files, (b) line
  coverage — every line of every registered source file appears exactly once.
- Extend `hl.py` with a `ts` highlighter (start from the `js` rules + TS
  keywords: `interface type enum readonly implements declare as satisfies
  private public protected abstract`).
- Embedded runnables: compile TS → JS with tsc and inline the **compiled JS**
  for in-deck demos (far simpler than the old wasm-b64 path). Slides show the
  TS source; demos run its compiled output — state this honestly in the deck.
- `chunks.py` helps pick slide-sized code cuts (~38 lines).

## 6. Deck outline (~17 parts, 500–550 slides)

0. 시작하기 — what we build, controls, why TS after C++ (~10)
1. TS 프로젝트 셋업 — tsconfig, strict, node:test (~15)
2. 코어 엔진 — types, board, 7-bag, rotation, gravity, line clear (~70)
3. 렌더링과 조작 — canvas glue, **playable in-deck demo** (~30)
4. 골든 트레이스 — proving TS ≡ C++ wasm, trace tool + tests (~20)
5. AI 8특징 — heights, holes, bumpiness… with board diagrams (~40)
6. 1수 탐색 — enumerate placements, evaluate, execute; **live AI demo** (~30)
7. 유전 알고리즘 — encoding, selection, crossover, mutation (~40)
8. 트레이너 — train.ts, real learning curves from ga_log.json (~25)
9. 브라우저 라이브 학습 — **in-deck GA training demo** (~20)
10. 대전 규칙 — garbage table, battle.ts, 1:1 demo (~30)
11. 프로토콜 — binary layout, golden vectors (~30)
12. RFC 6455 직접 구현 — handshake, frames, masking, close (~45)
13. 룸 엔진 — lockstep rooms, seats, 4th golden implementation (~35)
14. 클라이언트·로비·아레나 — net client, seats UI, **in-deck 8P live arena**
    (local simulation, same code path as network mode) (~50)
15. 봇 클라이언트와 실측 — bot_client.ts, `make match` real output (~25)
16. 테스트·빌드 — test suites, Makefile, coverage guarantee (~20)
17. 부록: ws 라이브러리판 + 더 나아가기 (~15)

Follow the Large Document Generation Protocol: skeleton deck on disk first
(placeholders per part, always openable), fill sections in order, one Write
≤ ~250 lines, checkpoint intermediates under `scratch/`.

## 7. Work order = commit plan (one task, one commit; verify before each)

1. Scaffold: package/tsconfig/Makefile + `core.ts` + core tests + golden
   trace tool → parity green.
2. `ai.ts` + search + tests (feature values checked against wasm AI where the
   ABI allows; otherwise property tests + fixed-board fixtures).
3. `ga.ts` + `train.ts` + **real training run** committing weights + log.
4. `battle.ts` + garbage rules + tests.
5. `protocol.ts` + `ws.ts` + `room.ts` + `server.ts` + golden-vector tests.
6. `bot_client.ts` + `make match` measured 8-player run.
7. Deck build system port (`deck/`) + skeleton deck that opens.
8. Deck sections filled, part by part (split into 2–4 commits if large;
   deck must stay openable at every commit).
9. `index.html` card + `README.md` row + final slide-count sync.
10. Appendix `server_lib.ts` (verify with ad-hoc `npm i --no-save ws`).

Review pass at the end (fresh eyes over every demo + counts), committed as
`… 리뷰 — <defect counts by type> 정정` per repo convention.

## 8. Language rules recap

- Deck prose, code comments, README/index text, commit messages: **Korean**.
- Sub-agent instructions and internal notes: English.
- Final session reports to the user: Korean.
