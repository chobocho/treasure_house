# Bubble Tea Tetris — a beginner's guide to TUI programming in Go (deck + runnable source)

Agent-facing plan (for the Opus build session). Language: English here; **all
user-facing output, all deck body text and all source comments are Korean.**
Follow the global `~/.claude/CLAUDE.md` (Korean reports, TDD RED→GREEN, one task =
one commit, `history.md` entry per task) and the repo `CLAUDE.md` (self-contained deck
from `template.html`, Fold 374/768 px, index + README cards, Korean narrative commit
messages without a type prefix — the repo convention overrides the global one here).
This plan is modelled on `tetris_ts/PLAN.md` (343 slides, full-source coverage deck)
and `rts/PLAN.md`. **Reuse the `tetris_ts/deck/` tooling verbatim** (`build_deck.py`,
`hl.py` — it already highlights Go —, `chunks.py`, `base/`, `extra.css`).

## 0. What the user asked for (do not narrow it)

> "template.html 이용해서 bubble tea tui 프레임웍을 이용해 테트리스 만들기 가이드를
> 만들어줘. bubble tea 초보자(미경험자)를 위한 문서고, 테트리스 1인용, 2인용,
> ai와 함께하는 1:1까지 구현해줘. ai는 기존에 만든 ai 테트리스 만들기 가이드를
> 참고하면 될거고 300페이지 정도로 하고, 동작하는 풀 소스 포함시켜줘."

Interpretation (state it on the "how to read" slide):

| Requirement | Meaning in this plan |
|---|---|
| Bubble Tea beginner, never used it | Part 2–3 teach Bubble Tea from zero with 7 tiny runnable programs *before* any Tetris code. Every Bubble Tea concept used later is introduced there first. Assume the reader knows basic Go (variables, structs, interfaces, goroutines only at "exists" level). |
| 1인용 | Single-player Tetris in the terminal: SRS rotation, 7-bag, hold, ghost, soft/hard drop, lock delay, levels, scoring. |
| 2인용 | Two humans on **one keyboard** (P1 = WASD-side keys, P2 = arrow keys), two boards side by side, garbage exchange. Terminals cannot report key-up or chords → say so honestly (part 7). |
| AI와 1:1 | Human vs AI on the same rules; AI is a **Go port of `tetris_ai/ai.cpp`** (8 features, 1-move search) using the presets in `tetris_ai/weights.json` (easy/normal/hard/max). Also AI-vs-AI mode (used for recordings). |
| ~300 pages | Target 300–320 slides, **hard minimum 290**. Count with the builder, never estimate. |
| working full source | Every line of `tetris_tui/**/*.go`, `go.mod`, `Makefile`, `weights.json` appears in the deck exactly once (coverage 100 %, checked by the builder). Every terminal capture in the deck comes from a real run under `tetris_tui/out/`. |

## 1. Goal

One self-contained slide deck at repo root:

    Go_Bubble_Tea_테트리스_만들기.html        target 300–320 slides, hard minimum 290

plus a committed, runnable Go module under `tetris_tui/` (module name
`treasure/tetris_tui`), built and tested on this machine:

    go run ./cmd/tetris                # menu: 1인용 / 2인용 / AI 대전 / AI vs AI
    go run ./cmd/tetris --mode ai --level hard --seed 7

## 2. Non-negotiables

1. Every code block in the deck is cut from a real file under `tetris_tui/` by the
   builder (`<!--CODE file=… lines=A-B-->`). No hand-typed code in slides. Coverage
   must be 100 % of the covered file set (§6) — the build prints missing/duplicate lines.
2. Every terminal/output block comes from a real run captured under `tetris_tui/out/`
   (`<!--RUN file=out/….txt-->`), or a frame recorded by `tools/record`.
3. Tests first (RED before GREEN) for `core/`, `ai/`, `battle/` and every Bubble Tea
   model's `Update` — table tests that feed `tea.Msg` values and assert on the model.
4. **Bubble Tea v2 only**, imported as `charm.land/bubbletea/v2` (see §3 — the module
   path is *not* `github.com/charmbracelet/bubbletea/v2`; that path fails with
   "module declares its path as charm.land/…"). Never mix v1 idioms in. Verify every API
   claim with `go doc charm.land/bubbletea/v2.<Symbol>` from the warm module cache
   before writing it on a slide. Do not cite v1 tutorials' signatures.
5. Every historical/library claim (Charm founded 2019, Bubble Tea first release 2020,
   Elm Architecture origin, SRS/7-bag/Tetris Guideline facts, Dellacherie/El-Tetris
   features, ANSI/VT100 history, Kitty keyboard protocol) is verified with WebSearch
   before it goes in. Keep `deck/claims.md`: claim → source URL → slide id.
6. Deck opens offline as a single file: no CDN, no web fonts, no external images.
7. Korean body text; Korean comments in all Go sources (explain *why*, not *what*).
8. Deck HTML is a build artifact. Never edit it by hand — edit `deck/sections/*.html`
   and rebuild. Always read the "오류 N건" / coverage lines of the build output.
9. The deck must stay openable at every commit (placeholders are fine, a broken file is not).
10. Do not modify anything under `tetris_ai/`, `tetris_ts/`, `tetris_net/`. Read only.

## 3. Environment (verified 2026-09-06 — do not re-discover)

| Tool | Status | Notes |
|---|---|---|
| go 1.27.0 android/arm64 | ok | `/data/data/com.termux/files/usr/bin/go`. `go test`, `go vet` work. Build with `GOFLAGS=-p=1` when RAM is tight. |
| Module cache | **warm** | `/root/go/pkg/mod` already holds `charm.land/bubbletea/v2 v2.0.9`, `charm.land/lipgloss/v2 v2.0.6`, `charm.land/bubbles/v2 v2.2.1` and their deps (fetched into a throwaway module). `go get` of these exact versions is instant and offline-safe. |
| Network | flaky | `proxy.golang.org` works but TLS handshakes time out sometimes. Retry once; pin exact versions; never depend on `@latest` resolving. `teatest` (`github.com/charmbracelet/x/exp/teatest/v2`) is **not cached** — only add it if one `go get` succeeds; otherwise drive models directly (see §5.4). |
| Bubble Tea v2 API facts | verified via `go doc` | `Model` = `Init() Cmd`, `Update(Msg) (Model, Cmd)`, `View() View`. `View` is a struct (`tea.NewView("…")`, field `Content` + others — run `go doc charm.land/bubbletea/v2.View` for AltScreen/cursor fields). Key input = `tea.KeyPressMsg` (type `Key` with `Text`, `Code rune`, `Mod`; `msg.String()` gives names like "left", "ctrl+c" — confirm exact spellings with `go doc` / a tiny test before relying on them). Timers: `tea.Tick`, `tea.Every`; `tea.Batch`; `tea.Quit`; `tea.WindowSizeMsg`; `tea.NewProgram(m, tea.WithInput(...), tea.WithOutput(...), tea.WithoutRenderer(), tea.WithWindowSize(w,h), tea.WithFPS(n))`. |
| tmux 3.x | ok | Real-PTY end-to-end smoke: `tmux new-session -d -s t -x 100 -y 40 'go run ./cmd/tetris --mode ai --seed 1'`, `tmux send-keys -t t Left Left space`, `tmux capture-pane -e -p -t t > out/tmux_ai.txt` (`-e` keeps ANSI). This is the only way to prove the program runs in a real terminal from an agent session. |
| python3 3.14.4 | ok | Deck builder. |
| clang/g++ | ok | Not needed unless you want to cross-check features against `tetris_ai/native_main.cpp` (optional). |
| rsvg-convert | ok | Render SVG figures to PNG to eyeball. CSS vars do not work inside SVG — hex colours only. |
| Playwright | unusable | node reports platform=android. Use the DOM stub (`tetris_ts/tools/check_deck.mjs` is Playwright-based → instead copy `hexwar/tools/check_demos.js` DOM-stub style) to run the in-deck frame player without a browser. |
| RAM | tight | Galaxy Fold, ~250 MB free. **At most 2 subagents, one `go build`/`go test` at a time, `free -m` before heavy steps.** Checkpoint progress in this file's log; the OS may kill the session. |

## 4. Repository layout

```
tetris_tui/
  PLAN.md                 this file (+ progress log at the bottom)
  go.mod  go.sum          module treasure/tetris_tui, go 1.27, pinned charm.land/* v2
  Makefile                deps build vet test record tmux-smoke deck deck-check clean
  examples/               Bubble Tea ladder for beginners, each its own main package
    01_hello/main.go        Model with a fixed View, q to quit
    02_counter/main.go      Update on KeyPressMsg, model is a value (copy semantics!)
    03_keys/main.go         key names: msg.String(), Code, Text, Mod; shows what it received
    04_tick/main.go         tea.Tick clock, re-scheduling the tick (the gravity pattern)
    05_window/main.go       WindowSizeMsg, drawing a centred box that survives resize
    06_lipgloss/main.go     lipgloss v2 styles, borders, JoinHorizontal/Vertical
    07_cmds/main.go         Cmd = future Msg: Batch, Sequence, a fake "AI thinking" delay
  core/                   pure rules, zero Bubble Tea imports
    piece.go  board.go  rng.go  srs.go  game.go  score.go  garbage.go  *_test.go
  ai/                     port of tetris_ai/ai.cpp
    features.go  search.go  weights.go  weights.json(copied presets)  *_test.go
  ui/                     lipgloss rendering shared by all modes
    style.go  board.go  panel.go  keys.go  *_test.go
  game/                   single-player Bubble Tea model
    model.go  update.go  view.go  *_test.go
  battle/                 1:1 rules + two-board Bubble Tea model (2P local, vs AI, AI vs AI)
    rules.go  model.go  update.go  view.go  *_test.go
  cmd/tetris/main.go      flags + menu model, wires the three modes
  tools/record/main.go    headless frame recorder → out/frames_*.json (scripted seeds/keys)
  tools/ansi2html/main.go ANSI SGR → <span class="c…"> for the deck
  out/                    captured runs (committed; the deck quotes these)
  deck/                   build_deck.py hl.py chunks.py base/ extra.css player.js sections/ claims.md
  test/golden/            parity fixtures derived from tetris_ts/test/golden (see §5.1)
```

## 5. Design decisions (decided — do not re-litigate; record deviations in the log)

### 5.1 Core rules = the C++ core's rules, verifiable by golden traces
`core/` reimplements the rules of `tetris_ai/tetris.cpp` (10×20 visible + hidden rows,
SRS kick tables, 7-bag on the same LCG, lock delay, hold, ghost, hard/soft drop,
guideline scoring incl. back-to-back and combo if the C++ core has them). Read
`tetris_ai/tetris.cpp` and `tetris_ts/src/core.ts` **first**; copy the constants
(LCG multiplier/increment, spawn position, kick tables) rather than re-deriving them.
Then read `tetris_ts/test/golden/core_traces.json` and `tetris_ts/tools/trace_wasm.mjs`
to learn the trace format (per-step board hash `bh`, seeds, scripted inputs). Write
`core/parity_test.go` that replays those traces. **Decide the parity scope in step 1**:
full step-parity if the tick semantics can be matched in ≤1 day of work; otherwise at
minimum (a) the piece sequence for seeds 1–3, (b) every kick table entry, (c) line
clear + scoring on fixed boards. Whatever the scope, state it plainly on the
"검증" slides — never claim more parity than the tests prove.

### 5.2 AI = port of ai.cpp, verified against ai_traces.json
Same 8 features in the same order (`F_LINES … F_LAND`), same 1-move search over
(rotation, x) with reachability along the spawn row, same tie-breaking. Copy
`tetris_ai/weights.json` verbatim into `ai/weights.json` (`//go:embed`). Write
`ai/parity_test.go` from `tetris_ts/test/golden/ai_traces.json` (feature vectors and
chosen moves per board). The deck's AI part *summarises* the 2편 deck's theory in ~12
slides and links to it (`C++_WASM_테트리스_AI_대전.html`) instead of re-teaching GA.
No GA training in this project.

### 5.3 The AI lives in a Cmd, not a goroutine you manage
Pattern to teach: on piece spawn the battle model returns `aiThinkCmd(boardCopy,
piece, next, level)` → runs `ai.Best()` off the update loop → returns `aiMoveMsg{seat,
rot, x}` → `Update` replays it as a key script (rotate n, move dx, hard drop) spread
over ticks so the human can *see* the AI move at a level-dependent speed. Blunder
probability per level as in 2편 (`matchup.mjs` presets) — copy the numbers, cite them.

### 5.4 Headless testing without teatest
Models are plain values: tests call `m.Update(tea.KeyPressMsg{Code: tea.KeyLeft})`
and `m.View().Content` directly. `tools/record` does the same with a scripted key/tick
sequence and a fixed seed and dumps every frame (ANSI string) to JSON; `ansi2html`
turns frames into HTML; `deck/player.js` (≈80 lines, no deps) steps through frames
with ←/→ inside a slide and autoplays. Six recordings: hello ladder (1), 1P game (1),
2P local (1), vs AI (1), AI vs AI full match to KO (1), resize demo (1). Plus the tmux
captures (§3) as proof-of-real-terminal slides. Strip nothing: colour comes through.

### 5.5 Keys
1P / P2: ← → move, ↓ soft, ↑ or x rotate CW, z rotate CCW, space hard drop, c hold.
P1 (2P mode): a d move, s soft, w rotate CW, q rotate CCW, f hard drop, e hold.
Global: p pause, esc/ctrl+c quit, r restart, F1 help. Put the table in `ui/keys.go`
as data so the help panel and the deck both read from one place. Explain DAS/ARR
honestly: terminals deliver OS key-repeat presses only; no key-up (except Kitty
protocol — mention, do not depend on it).

### 5.6 Rendering
Cells are two characters wide (`██` / `  `) so the board is square on any monospace
font; ghost = `░░`; colours = lipgloss v2 `Color`/`Style` with a 16-colour fallback
table for TERM without truecolor. Layout with `lipgloss.JoinHorizontal`. Minimum
terminal 80×24 for 2 boards; below that show a "터미널을 키워 주세요 (need 80×24, have
W×H)" view — that is the `05_window` lesson paying off.

### 5.7 Deck pedagogy (beginner contract)
- Every Bubble Tea concept gets: ① one sentence of *why*, ② the smallest program that
  shows it (from `examples/`), ③ its recorded frame, ④ the Tetris code that uses it.
- Introduce exactly one new API per slide in parts 2–3. Never show a function before
  its concept slide.
- "Elm Architecture" diagram (inline SVG) appears in part 2 and is reused with the
  Tetris names in part 5 and the two-seat names in part 7.
- Reserve ~10 "함정" slides for real beginner mistakes you *actually hit* (value-model
  copy semantics, forgetting to re-schedule Tick, blocking in Update, mutating shared
  slices between seats, lipgloss width with wide characters, Windows terminals).

## 6. Coverage file set

Covered 100 %: `**/*.go` (incl. `_test.go`, `examples/`, `tools/`), `go.mod`, `Makefile`,
`ai/weights.json`. Not covered but shown as a file tree slide: `go.sum`, `deck/*`,
`out/*`, `test/golden/*`. Code block limit 45 lines (`chunks.py` computes boundaries).
Put full-file appendix chunks in part 10 only for files whose narrative use is partial.

## 7. Deck outline (section → target slides; total 300–320)

| # | Section (Korean title in deck) | Slides | Content |
|---|---|---|---|
| 0 | 시작하기 | 10 | cover, how to read, what you'll build (3 mode screenshots from tmux), prerequisites, install, repo map, how the deck proves itself (coverage/RUN) |
| 1 | 터미널이라는 캔버스 | 16 | what a terminal is, cells & monospace, ANSI/SGR colours, cursor, alt screen, raw mode, why hand-rolling this is painful → why a framework |
| 2 | Bubble Tea 첫걸음 | 36 | Elm Architecture, Model/Init/Update/View, `01_hello`→`07_cmds` one at a time, KeyPressMsg anatomy, Tick re-scheduling, WindowSizeMsg, Cmd vs Msg, Batch/Sequence, value semantics, running/quitting, debugging with a log file |
| 3 | Lip Gloss로 꾸미기 | 16 | Style, Color & profiles, padding/border, width/height, Join*, Place, the 2-char cell trick, measuring width (wide chars) |
| 4 | 테트리스 규칙과 코어 엔진 | 46 | board & pieces, rotation states, SRS kicks (tables with diagrams), 7-bag + LCG, spawn/lock delay/ghost, line clear, scoring, hold, tests, golden parity results |
| 5 | 1인용 게임 만들기 | 44 | game model, gravity tick per level, key → action, soft/hard drop, hold, pause, game over, side panel (next×N, hold, score), resize handling, `cmd/tetris` menu, tmux capture, 함정 |
| 6 | AI 상대 | 32 | link to 2편, 8 features (1 slide each, board figures), search & reachability, weights presets, parity with ai_traces, the Cmd pattern (§5.3), replaying a move as keys, blunders per level |
| 7 | 1:1 대전 — 사람·AI·둘 다 | 44 | attack table & garbage (from 2편 §8), garbage queue timing, two seats in one model, 2P key split & terminal limits, vs AI, AI vs AI, KO & rematch, side-by-side layout, recordings |
| 8 | 테스트와 기록 | 22 | table tests for Update, View snapshot tests, `tools/record`, `ansi2html`, deck player, tmux smoke, `make test` output |
| 9 | 마무리 | 12 | packaging (`go install`), cross-compiling, Windows/macOS notes, ideas (bubbles list/viewport, netcode → 3편), further reading, credits |
| 10 | 부록 — 전체 소스 | 22 | remaining chunks for coverage, file tree, claims sources |
| | **Total** | **300** | |

## 8. Work order = commit plan (one task, one commit; verify before each)

1. Scaffold: `go.mod` (pinned versions), `Makefile`, `examples/01–07` with a
   `go vet ./...` + tiny `_test.go` each (RED→GREEN on `Update` behaviour), recorder
   skeleton. Commit: `Bubble Tea 테트리스 1단계 — 모듈·예제 사다리 7개·레코더 뼈대`.
2. `core/` with tests + parity against `tetris_ts/test/golden/core_traces.json`
   (scope decided and logged). Commit.
3. `ai/` port + parity against `ai_traces.json` + weights embed. Commit.
4. `ui/` + `game/` single player + `cmd/tetris` (1P only) + tmux smoke capture. Commit.
5. `battle/` rules (tests from 2편 attack table) + vs-AI + AI-vs-AI + 2P local + menu
   wiring + tmux captures. Commit.
6. `tools/record`, `tools/ansi2html`, `deck/player.js`, six recordings under `out/`.
   Commit.
7. Deck build system copied from `tetris_ts/deck/` and adapted (title, brand, RUN/
   frame directives, Go-only LANGNAME) + skeleton deck with all section headers and
   placeholders that opens (do not commit the HTML yet — repo rule: no deck without
   its card). Commit tooling + sections skeleton only.
8. Fill sections part by part, 2–4 commits, ≤250 lines per Write, coverage climbing
   to 100 %. Run the DOM-stub player check and the 374/768 px check each time.
9. `index.html` card + `README.md` row + final slide-count sync + first deck HTML
   commit. Card text template (adjust numbers from the build output):
   `🍵 Go Bubble Tea 테트리스 — TUI 프레임워크 입문부터 AI 1:1 대전까지` /
   `🍵 Bubble Tea 를 처음 쓰는 사람을 위해 예제 7개로 Elm 아키텍처를 익힌 뒤, 터미널
   테트리스를 1인용 → 같은 키보드 2인용 → 8특징 AI 와의 1:1 대전까지 만든다.
   슬라이드 N장 — tetris_tui/ 전체 소스 M줄이 한 줄도 빠짐없이 실려 있고, 코어·AI 는
   기존 C++ 덱의 골든 트레이스로 검증했다 🎮`
10. Review pass with fresh eyes (every recording, every count, every claim), committed
    as `Bubble Tea 테트리스 덱 리뷰 — <defect counts by type> 정정`.

`history.md` gets one ≤12-line entry per commit (prepend; never read the whole file).

## 9. Verification commands (all must pass before step 9)

```sh
cd tetris_tui
go vet ./... && go test -p 1 ./...            # unit + parity + model tests
make record                                    # regenerates out/frames_*.json (deterministic → git diff must be empty)
make tmux-smoke                                # out/tmux_*.txt refreshed, program exited cleanly
make deck                                      # prints slide count, coverage X/X, 오류 0건
make deck-check                                # DOM-stub: player mounts on every frame slide; no line wider than 374px viewport rules
```

## 10. Deck formatting traps (inherited — obey)

- No box-drawing characters (─ │ ┌) inside `<pre>`; the Fold's fonts misalign them.
  Frame captures may contain them only inside the player (rendered per-cell as spans).
- In `<pre class="code txt">` never put Korean at the start of a column that other
  columns align to; put Korean at line ends or use `<table>` / `svg.diag`.
- Code block ≤45 lines; slide must not need horizontal scroll at 374 px.
- Slide numbers `{{N}}` are filled by the builder; `<!--SLIDE sec=N t="…"-->` heads
  each slide; section titles live in `sections.json`.
- Page/slide counts in index/README must equal the builder's count.

## 11. Language rules recap

Deck body, source comments, `history.md`, commit messages, user reports → Korean.
Identifiers, this plan, subagent instructions → English. Never leak this plan's
English into a user-facing message; translate and condense.

---

## Progress log (newest first; Korean, ≤12 lines each, same shape as history.md)

- 2026-09-06 14:20 — **2단계: core/ 이식 + 골든 파리티 (전 스텝 일치)**.
  §5.1 의 파리티 범위 결정: **full step-parity**. 시드 6개 × 1500스텝의 보드 해시·
  stats 해시가 **전부** 정답지와 같고, 배치 1960경우·연쇄 36라운드도 전부 같다.
  `piece/rng/srs/board/score/garbage/game/trace.go` + 테스트 7개(단위 60건 + 파리티 5건).
  Stats 는 C++ 의 int 배열 대신 이름 있는 구조체 — 다만 필드 **순서**는 원본 그대로 두고
  `Pack()` 이 배열을 되살려 해시를 대조한다. 정답지 두 개는 tetris_ts 에서 test/golden 으로 복사.
  **변이 테스트로 검출력 확인**: ClearLines 의 `y++` 제거 → 파리티가 시드 2654435769 의
  1018스텝에서 잡음. 킥 표 한 칸 변조 → 파리티는 못 잡고(그 킥을 안 밟는다)
  구조 단위 테스트(CCW = CW 의 역)가 잡음. 둘이 서로를 메운다.
  내 테스트 기대값 3건이 틀려서 고쳤다: RowMask 는 "지운 순간의 y"라 붙은 두 줄이 한 비트,
  `Update` 는 dt 를 100ms 로 자른다, 우물 4줄만 심으면 퍼펙트 클리어가 돼 공격이 +10.
  검증: `go vet` 0건 · `go test -p 1 ./...` 9패키지 통과 · gofmt 0건.

- 2026-09-06 13:35 — **1단계: 모듈·예제 사다리 7개·레코더 뼈대**.
  `go.mod`(module `treasure/tetris_tui`, `charm.land/bubbletea/v2 v2.0.9` ·
  `lipgloss/v2 v2.0.6` 고정, bubbles 는 안 쓰기로 결정 — 의존성 최소화) ·
  `Makefile`(deps build vet test record tmux-smoke deck deck-check fmt clean).
  예제 01_hello~07_cmds, 각각 main.go + main_test.go. **RED→GREEN 실제로 밟았다**
  (스텁 + 테스트 → 단언 실패 확인 → 구현). 테스트가 확인한 API 사실:
  `Model = Init() Cmd / Update(Msg)(Model,Cmd) / View() View`, 키 이름 "q" "esc"
  "ctrl+c" "left" "space", 특수 키의 `Text` 는 빈 문자열.
  `tools/record` — 스크립트(키/wait/WxH) → 프레임 JSON, 결정론 테스트 포함.
  Cmd 는 일부러 실행하지 않고 `TickMsg` 를 직접 주입한다(잠들지 않게).
  검증: `go vet` 0건 · `go test -p 1 ./...` 8패키지 전부 통과 · gofmt 0건 ·
  `make tmux-smoke` 로 80×24 실제 PTY 에서 7개 예제 전부 화면 확인(`out/tmux_*.txt`).
  tmux 가 넣는 탭을 `deck/untab.py` 로 칸 단위 공백으로 되돌린다(폴드 폭 어긋남 방지).
  비고: `make deck` / `make deck-check` 는 7단계에서 도구가 생겨야 돈다.
