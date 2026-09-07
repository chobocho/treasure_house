# Boricha (보리차) — build your own Bubble Tea: a TUI framework from scratch in Go (deck + runnable source)

Agent-facing plan (for the Opus build session). Language: English here; **all
user-facing output, all deck body text and all source comments are Korean.**
Follow the global `~/.claude/CLAUDE.md` (Korean reports, TDD RED→GREEN, one task =
one commit, ≤12-line `history.md` entry per commit, prepend only) and the repo
`CLAUDE.md` (self-contained deck from `template.html`, Fold 374/768 px, `index.html`
card + `README.md` row, embedded `DeckMono` font, Korean narrative commit messages
without a type prefix — the repo convention overrides the global one here).
This plan is modelled on `tetris_tui/PLAN.md` (337 slides, full-source coverage deck
about *using* Bubble Tea). **Reuse the `tetris_tui/deck/` tooling verbatim** —
`build_deck.py`, `hl.py`, `chunks.py`, `split_ranges.py`, `gen_appendix.py`,
`gen_fonts.py`, `test_fonts.py`, `untab.py`, `player.js`, `check_deck.js`, `base/`,
`extra.css` — copy them into `boricha/deck/` and change only title/brand/paths/modes.

## 0. What the user asked for (do not narrow it)

> "template.html이용해서 bubble tea tui 같은 프레임웍을 만드는 법을 500페이지 정도로
> 만들어줘, 동작하는 풀 소스 포함시켜줘."

Interpretation (state it on the "how to read" slide):

| Requirement | Meaning in this plan |
|---|---|
| "Bubble Tea 같은 프레임웍을 만드는 법" | We **write the framework itself**, not an app on top of Bubble Tea. Same architecture (Elm: Model/Init/Update/View, Msg, Cmd, Program), same shape of API, but every layer is ours: terminal driver, input decoder, renderer, text width, styling (a Lip Gloss subset) and components (a Bubbles subset). Zero third-party imports — only the Go standard library (`syscall`, `os`, `os/signal`, `time`, `sync`, `bufio`, `unicode/utf8`, …). |
| "template.html 이용해서" | Deck is assembled on `template.html` (already the base of `tetris_tui/deck/base/`). ←/→ pages, ↑/↓ scroll, gamepad, Fold 374/768, `DeckMono` embedded. |
| "500페이지 정도" | Target **500–520 slides, hard minimum 480**. Count with the builder, never estimate. |
| "동작하는 풀 소스" | Every line of `boricha/**/*.go`, `go.mod`, `Makefile` appears in the deck exactly once (coverage 100 %, checked by the builder). Every terminal capture comes from a real run under `boricha/out/`. Every example and the capstone apps run in a real PTY (tmux proof). |
| Reader | Knows basic Go (structs, interfaces, goroutines, channels at "has used once" level). Has **never** written a terminal program. Has maybe used Bubble Tea, maybe not — never assume they have. Bubble Tea is quoted only as the *reference design* we are re-creating. |

## 1. Goal

One self-contained slide deck at repo root:

    나만의_Bubble_Tea_만들기.html            target 500–520 slides, hard minimum 480

plus a committed, runnable, dependency-free Go module under `boricha/` (module name
`treasure/boricha`; package import path `treasure/boricha/tea` etc.), built and tested
on this machine:

    go run ./examples/01_hello
    go run ./cmd/todo                  # capstone 1: 할 일 목록 (textinput + list + help)
    go run ./cmd/monitor               # capstone 2: 시스템 모니터 (tick + progress + viewport + resize)
    go run ./cmd/showcase              # every component on one screen, tab to switch
    go test ./...                      # unit + headless integration, all offline

Name: **보리차 (boricha)** — a Korean tea, the deck's running joke: "Bubble Tea 대신 보리차".
Package names mirror the reference so the reader can map them 1:1
(`tea` ≈ bubbletea, `style` ≈ lipgloss, `widgets` ≈ bubbles).

## 2. Non-negotiables

1. Every code block in the deck is cut from a real file under `boricha/` by the builder
   (`<!--CODE file=… lines=A-B-->`). No hand-typed code in slides. Coverage must be
   100 % of the covered file set (§6) — read the build's missing/duplicate/"오류 N건" lines.
2. Every terminal/output block comes from a real run captured under `boricha/out/`
   (`<!--RUN file=out/….txt-->`, `<!--CAP file=out/tmux_….html-->`, `<!--PLAYER name=…-->`).
3. Tests first (RED before GREEN) for every package. The input decoder and the renderer
   are table-driven byte-level tests; every widget's `Update` is tested by feeding `tea.Msg`
   values and asserting on the model and on `View()`.
4. **Standard library only.** `go.mod` has no `require`. If you find yourself wanting
   `golang.org/x/sys` or `go-runewidth`, that is a chapter to write, not a dependency to add.
5. Every claim about the reference design is verified with `go doc charm.land/bubbletea/v2.<Symbol>`
   (warm cache under `tetris_tui/` — run `go doc` from that directory with `GOPROXY=off`;
   see §3). Every historical/standard claim (VT100 1978, ECMA-48/ANSI X3.64, xterm
   sequences, DEC private modes 1049/2004/1006/2026, kitty keyboard protocol, Elm
   Architecture, Charm/Bubble Tea dates, East Asian Width UAX #11, wcwidth) is verified
   with WebSearch/WebFetch before it goes in. Keep `deck/claims.md`: claim → source URL → slide id.
6. Deck opens offline as a single file: no CDN, no web fonts (DeckMono is embedded by
   the builder), no external images. Inline SVG only, hex colours inside SVG.
7. Korean body text; Korean comments in all Go sources (explain *why*, not *what*).
   Non-trivial algorithms (diff, decoder, width lookup) state complexity in a comment.
8. Deck HTML is a build artifact. Never edit it by hand — edit `deck/sections/*.html` and
   rebuild. The deck must stay openable at every commit (placeholders are fine).
9. Do not modify anything under `tetris_tui/`, `tetris_ts/`, `tetris_ai/`, `tetris_net/`,
   `template.html`, `tools/`. Read/copy only.
10. Honesty rule for platforms: this machine is `android/arm64` (build tag `linux` also
    applies). Linux is tested; macOS is written against `syscall.TIOCGETA/TIOCSETA`
    behind `//go:build darwin` but **cannot be run here** — say so on the slide. Windows
    gets a stub (`ErrUnsupported`) and one slide explaining what a console driver would need.

## 3. Environment (verified 2026-09-07 — do not re-discover)

| Tool | Status | Notes |
|---|---|---|
| go 1.27.0 android/arm64 | ok | `/data/data/com.termux/files/usr/bin/go`. `GOPROXY=off GOTOOLCHAIN=local`, `-p 1`. No network needed — this module has no deps. |
| `syscall` constants | ok | `syscall.TCGETS`, `syscall.TCSETS`, `syscall.Termios`, `syscall.TIOCGWINSZ`, `syscall.SIGWINCH` exist on linux/arm64. **`syscall.Winsize` does not exist** — define `type winsize struct{ Row, Col, X, Y uint16 }` yourself and call `syscall.Syscall(syscall.SYS_IOCTL, fd, TIOCGWINSZ, uintptr(unsafe.Pointer(&ws)))`. Raw mode = clear `ICANON|ECHO|ISIG|IEXTEN` in Lflag, `IXON|ICRNL|BRKINT|INPCK|ISTRIP` in Iflag, `OPOST` in Oflag, set `CS8`, `VMIN=1 VTIME=0` (teach exactly what each bit does — one slide per group). |
| Bubble Tea v2 reference | warm cache | `cd tetris_tui && GOPROXY=off go doc charm.land/bubbletea/v2.Program` etc. Use it to quote the real API on the "나란히 보기" slides. Also `charm.land/lipgloss/v2` and `charm.land/bubbles/v2` v2.2.1 are cached. Never import them from `boricha/`. |
| tmux 3.x | ok | Real-PTY end-to-end proof: `tmux new-session -d -s b -x 80 -y 24 'go run ./cmd/todo'`, `tmux send-keys -t b …`, `tmux capture-pane -e -p -t b > out/tmux_todo.txt`. `sleep 8` after launch (cold `go run` needs it). |
| python3 3.14 + fontTools + brotli | ok | Deck builder and DeckMono subset. Font file `/usr/share/fonts/truetype/nanum/D2Coding-Ver1.3.2-20180524-ligature.ttf`. |
| node | ok for DOM stub | `deck/check_deck.js` (copied) runs the frame player without a browser. Playwright is **unusable** (node reports platform=android) — do not try. |
| rsvg-convert | ok | Render every inline SVG figure to PNG and look at it once. |
| RAM | tight (~1 GB free, swap nearly full) | **At most 2 subagents, one `go build`/`go test` at a time, `free -m` before heavy steps.** Checkpoint progress in this file's log after every commit; the OS may kill the session. |

## 4. Repository layout

```
boricha/
  PLAN.md                 this file (+ progress log at the bottom, newest first)
  go.mod                  module treasure/boricha, go 1.27, NO require block
  Makefile                build vet test record html logs tmux-smoke deck deck-check clean
  tea/                    the core: Elm loop (≈ bubbletea)
    msg.go                Msg, KeyMsg, MouseMsg, WindowSizeMsg, FocusMsg/BlurMsg, PasteMsg, QuitMsg, tickMsg…
    cmd.go                Cmd = func() Msg; Batch, Sequence, Tick, Every, Quit, Println(debug)
    model.go              Model interface (Init/Update/View)
    program.go            Program: NewProgram, options, Run, Send, Kill/Wait; the goroutine plan
    options.go            WithInput/WithOutput/WithoutRenderer/WithAltScreen/WithMouse/WithFPS/WithWindowSize
    key.go                Key type, KeyType enum, String() names ("ctrl+c", "left", "shift+tab", "한")
    *_test.go             loop semantics: Batch order, Quit, panic recovery, Tick re-schedule, headless run
  term/                   the terminal driver (what x/term + termios do)
    term.go               Terminal interface: MakeRaw/Restore/Size/EnableAltScreen/HideCursor/…
    term_unix.go          //go:build linux || darwin — ioctl helpers, SIGWINCH watcher
    termios_linux.go      TCGETS/TCSETS
    termios_darwin.go     TIOCGETA/TIOCSETA (untested here — say so)
    term_windows.go       stub returning ErrUnsupported
    seq.go                escape sequence constants: CSI, SGR reset, alt screen 1049, cursor, 2004, 1006, 2026
    *_test.go             sequence strings, raw-mode flag arithmetic on a fake Termios
  input/                  bytes → tea.Msg (what bubbletea/key.go + cancelreader do)
    decoder.go            state machine: ESC ambiguity, CSI/SS3, modifiers ";2"…";8", UTF-8 assembly
    keys.go               sequence → Key table (arrows, F1–F12, home/end/pgup/pgdn/ins/del, alt+x, ctrl+x)
    mouse.go              SGR 1006 "\e[<b;x;yM/m" → MouseMsg
    paste.go              bracketed paste 200~ / 201~ → PasteMsg
    reader.go             goroutine reading os.Stdin with an ESC timeout (50 ms) and cancel on quit
    *_test.go             table tests on byte slices incl. split-across-reads and Korean/emoji input
  render/                 View string → minimal terminal writes (what the standard renderer does)
    buffer.go             frame = []line (cells), from a string with ANSI kept intact
    diff.go               line-level diff against last frame; only changed lines rewritten  O(lines·width)
    renderer.go           FPS-capped loop (default 60), flush on demand, sync output 2026 when supported
    cursor.go             cursor position tracking, ClearToEOL, avoid trailing-space flicker
    *_test.go             golden byte output for scripted frame sequences
  width/                  text measurement (what go-runewidth/uniseg do for us)
    width.go              RuneWidth (UAX #11 EA table subset: Hangul, CJK, fullwidth, emoji), StringWidth (ANSI-aware)
    table.go              generated ranges (tools/gen_width writes it from the Unicode data file — commit both)
    truncate.go           Truncate, PadRight, Wrap (word wrap, wide-char safe)
    *_test.go             "한글" = 4 cells, "a한b" = 4, ANSI-stripped width, wrap at wide boundary
  style/                  a Lip Gloss subset (value semantics)
    color.go              Color (16 / 256 / truecolor), profile detection from TERM/COLORTERM/NO_COLOR, downsampling
    style.go              Style: Bold/Italic/Underline/Faint/Reverse, Foreground/Background, Padding, Margin, Width/Height, Align
    border.go             border sets (normal/rounded/thick/double/ascii), Border(top,right,bottom,left)
    render.go             Render(string) — the ordering: pad → align → border → margin
    join.go               JoinHorizontal/JoinVertical with positions, Place(w,h,hpos,vpos)
    *_test.go             rendered-string goldens (ANSI on, ANSI off)
  widgets/                a Bubbles subset, one file each with its own model/update/view
    spinner.go  progress.go  textinput.go  list.go  viewport.go  help.go  keymap.go
    *_test.go
  testkit/                headless driver (what teatest is)
    testkit.go            RunScript(model, script) → frames; fake terminal (fixed size), fake clock
    script.go             "80x24 j j enter wait 한글 tab" mini-language shared with tools/record
  examples/               the ladder — each its own main package, one new concept each
    01_hello  02_counter  03_keys  04_tick  05_window  06_style  07_cmds  08_mouse  09_paste  10_widgets
  cmd/todo  cmd/monitor  cmd/showcase   capstone programs
  tools/record/main.go    headless frame recorder → out/frames_*.json (uses testkit)
  tools/ansi2html/main.go ANSI SGR → <span class="c…"> for the deck (copy from tetris_tui, keep Korean comments)
  tools/gen_width/main.go generates width/table.go from EastAsianWidth.txt (vendored copy + version noted)
  out/                    captured runs (committed; the deck quotes these)
  deck/                   build_deck.py hl.py chunks.py split_ranges.py gen_appendix.py gen_fonts.py test_fonts.py
                          untab.py player.js check_deck.js base/ extra.css sections/ claims.md
```

## 5. Design decisions (decided — do not re-litigate; record deviations in the log)

### 5.1 The loop is three goroutines and two channels — and the deck draws it
`Program.Run`: (a) input goroutine `input.Reader` → `msgs chan Msg`; (b) command
goroutine pool: each `Cmd` runs in its own goroutine and sends its `Msg` back on `msgs`;
(c) the main goroutine owns the model: `for msg := range msgs { model, cmd = model.Update(msg); renderer.Write(model.View()); go run(cmd) }`.
`Batch` fans out (order not guaranteed — write a test that proves it), `Sequence` runs one
after the other. `Quit` is a `Cmd` returning `QuitMsg`. `tea.Tick(d, fn)` is a `Cmd` that
sleeps; it does **not** re-arm itself — the "재예약" pattern is a whole slide, as in the
tetris deck's 함정 list. Panics in `Update` restore the terminal before re-panicking
(`defer term.Restore()` first, then `recover`/re-panic) — one slide shows the screen
*without* this and why the shell looks broken (`stty sane` rescue).

### 5.2 Model is a value; View returns a string
Keep the v1-style `View() string` (simpler to teach and to diff) but explain on the
comparison slide that Bubble Tea v2 returns a `View` struct (verify with `go doc`).
`Update(Msg) (Model, Cmd)` returns the model by value — the copy-semantics trap gets its
own slide with a failing test that a beginner would write.

### 5.3 Input decoder is a table + a small state machine, with an ESC timeout
Bytes arrive in arbitrary chunks. The decoder is `func (d *Decoder) Feed(b []byte) []tea.Msg`
with internal carry-over; a lone `0x1b` is emitted as `esc` only after 50 ms without a
follow-up byte (the reader owns the timer; the decoder exposes `Flush()`). Tests feed the
same sequence split at every byte boundary and expect identical messages. Key names follow
Bubble Tea's spelling (`"ctrl+c"`, `"alt+enter"`, `"shift+tab"`, `"f5"`, `"한"`) so the
comparison slide can show them side by side — confirm spellings from `go doc … Key.String`
before writing the table. UTF-8: assemble multi-byte runes (Korean typed via IME arrives as
complete 3-byte sequences per syllable — capture it in tmux and show it).
Mouse: SGR 1006 only (say why: no 223 limit, release events). Bracketed paste on by option.
Kitty keyboard protocol: one slide, "we do not implement it, here is what you'd gain".

### 5.4 Renderer = line diff, not cell diff
Keep the last frame's lines; on each flush compare line by line, move the cursor only to
changed lines, `\e[2K` + rewrite, then park the cursor. Frame bigger than the terminal →
clip to height and warn once. Line longer than width → truncate with `width.Truncate`
(never let the terminal wrap — that is the #1 flicker bug; show it happening in a tmux
capture *before* the fix). FPS cap with a ticker (default 60, `WithFPS`). Synchronized
output (`\e[?2026h/l`) wrapped around a flush when `TERM` is known to support it — cite.
Teach the cost model: O(lines·width) per frame, and why that's fine for a TUI.

### 5.5 Width is our own table, generated, committed, and tested against Korean text
`width/table.go` is generated by `tools/gen_width` from a vendored `EastAsianWidth.txt`
(record the Unicode version in the file header; the data file itself is **not** in the
coverage set — say which version and where it came from on a slide). Rules: W/F → 2,
combining marks (Mn/Me — a small hard-coded range list) → 0, control → 0, everything
else → 1; emoji presentation ranges → 2. Ambiguous (A) → 1 (state the choice). Lookup is
binary search over ranges, O(log n). This is the chapter that makes the whole deck's
Korean UI line up — connect it to the `DeckMono` font story from `template.html`.

### 5.6 Style = an immutable value with a render pipeline
`style.New().Bold(true).Foreground(style.Color("205")).Padding(1,2).Border(style.Rounded)`.
`Render(s)` order: apply SGR to each line → pad → align to Width → border → margin. Colour
profile is detected once from `TERM`, `COLORTERM`, `NO_COLOR`, `CLICOLOR_FORCE` and the
output being a TTY; truecolor → 256 → 16 downsampling with the nearest-distance table
(one slide with the math). `JoinHorizontal` pads every block to equal height using
`width.StringWidth` — this is where 5.5 pays off. Show one bug slide: joining Korean
text without our width table (misaligned columns, real capture).

### 5.7 Widgets are ordinary models, composed by embedding
Each widget is `type Model struct{…}` with `Update(tea.Msg) (Model, tea.Cmd)` and
`View() string`, exactly like the app. The parent forwards messages and keeps the
returned value (copy-semantics slide again, now with a real bug). `keymap` + `help`
make the help bar data-driven so the capstone's key table and the deck's key slide come
from one place. `textinput` handles Korean by runes and cursor by cell width. `list` has
filtering; `viewport` has ↑/↓/PgUp/PgDn and mouse wheel. Scope stops there — no tables,
no file picker (mention as exercises).

### 5.8 Headless testing is a first-class feature, not an afterthought
`testkit.RunScript(m, "80x24 j j enter wait 한 tab q")` runs the real `Program` with a fake
terminal (`WithInput(bytes)`, `WithOutput(buffer)`, `WithoutRenderer` off — we want the
diff output too) and a fake clock for `Tick`. It returns every frame as an ANSI string.
`tools/record` uses it to produce `out/frames_*.json`; `tools/ansi2html` (copied from
`tetris_tui/tools/ansi2html`, comments kept) turns frames into HTML; `deck/player.js`
plays them inside a slide. Recordings (≥ 12): the ten ladder examples, todo, monitor,
showcase, plus "before/after" bug captures (wrap flicker, width misalignment, Tick not
re-armed). Determinism is the contract: `make record` twice → empty `git diff`.

### 5.9 Deck pedagogy (beginner contract)
- Every layer gets: ① the pain without it (a raw program or a real broken capture),
  ② the smallest design that removes the pain, ③ tests first, ④ the code, ⑤ the ladder
  example that uses it, ⑥ its recorded frames, ⑦ "Bubble Tea는 이렇게 한다" one slide.
- Introduce exactly one new type or function per slide in parts 3–9. Never show a symbol
  before its concept slide.
- The three-goroutine diagram (inline SVG) appears in part 2 and is reused with more
  detail in parts 3, 5 and 6.
- Reserve ~14 "함정" slides for mistakes you *actually hit* while building (log them in
  the progress log as you go, then write the slides from the log — do not invent them).
- Exercises at the end of each part (2–3 per part, with an answer pointer into the source).

## 6. Coverage file set

Covered 100 %: `**/*.go` (incl. `_test.go`, `examples/`, `cmd/`, `tools/`, generated
`width/table.go`), `go.mod`, `Makefile`. Not covered but shown on a file-tree slide:
`deck/*`, `out/*`, `width/EastAsianWidth.txt` (vendored data). Code block limit 45 lines
(`chunks.py`/`split_ranges.py`). `width/table.go` may be long — show its head and tail in
part 7 and let the appendix generator take the rest (that is what part 14 is for).
Expected source size ≈ 9,000–12,000 lines incl. tests (tetris_tui was 11,261 → 337 slides;
500 slides leaves room, do not pad with code — pad with explanation, figures and captures).

## 7. Deck outline (section → target slides; total 500)

| # | Section (Korean title in deck) | Slides | Content |
|---|---|---|---|
| 0 | 시작하기 | 12 | cover, how to read, what you'll build (3 tmux captures: todo/monitor/showcase), prerequisites, repo map, "Bubble Tea 대신 보리차" naming, how the deck proves itself (coverage/RUN/PLAYER) |
| 1 | 터미널의 실체 — 바이트로 말하기 | 30 | tty/pty, line discipline, cooked vs raw, termios bits, ESC/CSI/SS3 grammar, SGR, cursor, alt screen 1049, TIOCGWINSZ, SIGWINCH, a 60-line hand-rolled program (`examples/00_raw`, in coverage) and everything that goes wrong with it → why a framework |
| 2 | 설계 — Elm 아키텍처와 Bubble Tea 해부 | 28 | Elm Architecture origin, Model/Update/View as a pure loop, Msg vs Cmd, Bubble Tea's package map (go doc-verified), our package map, the 3-goroutine diagram, API contract we commit to, what we leave out |
| 3 | 1단계 — tea: 핵심 루프 | 50 | Msg/Cmd/Model types, Program & options, the loop, Batch/Sequence semantics + tests, Quit, Tick/Every and re-arming, panic restore, Send from outside, headless run, `01_hello`…`04_tick`, 함정 ×3 |
| 4 | 2단계 — term: 터미널 드라이버 | 36 | Terminal interface, ioctl by hand, MakeRaw bit by bit, Restore & defer order, size query, SIGWINCH → WindowSizeMsg, alt screen/cursor/mouse/paste enable-disable, build tags linux/darwin/windows, `05_window`, the `stty sane` slide |
| 5 | 3단계 — input: 입력 파서 | 52 | byte chunks problem, decoder state machine, ESC timeout, CSI parameters & modifiers table, SS3 keys, ctrl/alt encoding, UTF-8 assembly & Korean input, Key.String naming, mouse SGR, bracketed paste, focus events, split-boundary tests, kitty protocol (not implemented), `03_keys`, `08_mouse`, `09_paste`, 함정 ×2 |
| 6 | 4단계 — render: 렌더러 | 44 | naive full redraw and its flicker (capture), frame buffer, line diff algorithm + complexity, cursor bookkeeping, clip/truncate rules, FPS cap, sync output 2026, cursor show/hide, golden byte tests, before/after captures, 함정 ×2 |
| 7 | 5단계 — width: 글자 폭 | 24 | why "한" is 2 cells, UAX #11 classes, the generator, binary-search lookup, combining/zero-width, emoji, ANSI-aware StringWidth, Truncate/Pad/Wrap, the DeckMono connection, tests on Korean strings |
| 8 | 6단계 — style: 꾸미기 | 48 | Style value, SGR composition, colour profiles & detection, downsampling math, padding/margin, Width/Height/Align, border sets, render order, JoinHorizontal/Vertical, Place, `06_style`, misaligned-Korean bug capture, 함정 ×2 |
| 9 | 7단계 — widgets: 부품 | 56 | composition by embedding, keymap+help, spinner, progress, textinput (Korean, cursor by cells), list (+filter), viewport (+mouse wheel), each: tests → code → frames, `10_widgets`, 함정 ×2 |
| 10 | 8단계 — testkit·record: 시험과 기록 | 28 | fake terminal, fake clock, script language, RunScript, tools/record, ansi2html, the deck player, tmux smoke, determinism contract, `make test` output |
| 11 | 9단계 — 응용: 할 일·모니터·전시장 | 40 | `cmd/todo` (state, keys, persistence to a JSON file), `cmd/monitor` (`/proc` read in a Cmd, progress bars, resize), `cmd/showcase` (tabs), tmux captures for all three, 함정 ×3 |
| 12 | 10단계 — Bubble Tea와 나란히 | 20 | API comparison table (go doc-verified), what Bubble Tea does that we skipped (cancelreader, Windows console, View struct, kitty, layers), porting a boricha app to Bubble Tea in 10 lines, performance numbers from `out/bench.txt` |
| 13 | 마무리 | 12 | packaging, cross-compiling, exercises index, further reading (with the claims sources), credits, what to build next |
| 14 | 부록 — 전체 소스 | 20 | remaining chunks for coverage (generated), file tree, claims table |
| | **Total** | **500** | |

## 8. Work order = commit plan (one task, one commit; verify before each)

1. Scaffold: `go.mod`, `Makefile`, `examples/00_raw` (hand-rolled raw-mode program, the
   "pain" demo), `term/` with tests (fake Termios flag arithmetic RED→GREEN), tmux capture
   of `00_raw`. Commit: `보리차 1단계 — 모듈·Makefile·날것 터미널 예제·term 드라이버`.
2. `tea/`: Msg/Cmd/Model/Program/options + loop tests + `examples/01_hello`…`04_tick`.
   Commit.
3. `input/`: decoder + key table + mouse + paste + reader, split-boundary tests,
   `examples/03_keys`, `08_mouse`, `09_paste` (they use a temporary plain renderer). Commit.
4. `width/`: generator, vendored data, table, tests. Commit.
5. `render/`: buffer/diff/renderer/cursor + golden tests; wire into `Program`;
   `examples/05_window`; before/after flicker captures. Commit.
6. `style/`: color/style/border/render/join + goldens; `examples/06_style`, `07_cmds`. Commit.
7. `widgets/` + `examples/10_widgets`. Commit.
8. `testkit/` + `tools/record` + `tools/ansi2html` + recordings under `out/` + `logs`
   (`go test`, `go vet`, `loc`, `bench`). Commit.
9. `cmd/todo`, `cmd/monitor`, `cmd/showcase` + tmux smoke captures. Commit.
10. Deck build system copied from `tetris_tui/deck/` and adapted (title, brand, OUT path,
    FRAME_FILES, MODES) + skeleton `sections/00–14` with headers and placeholders that opens.
    Commit tooling + skeleton only (no deck HTML in the repo without its card).
11. Fill sections part by part, 3–5 commits, ≤250 lines per Write, coverage climbing to
    100 %. After each: `make deck && make deck-check`, read "오류 N건", check 374/768 px
    (DOM stub width check from `check_deck.js`), render new SVGs with rsvg-convert.
12. `index.html` card + `README.md` row + final slide-count sync + first deck HTML commit.
    Card text template (adjust numbers from the build output):
    `🍵 나만의 Bubble Tea 만들기 — Go로 TUI 프레임워크를 바닥부터` /
    `🫖 Bubble Tea 같은 터미널 UI 프레임워크를 표준 라이브러리만으로 직접 만듭니다.
    termios 원시 모드 → 이스케이프 시퀀스 파서 → 줄 단위 diff 렌더러 → 한글 폭 표 →
    Lip Gloss식 스타일 → 부품(스피너·입력창·목록·뷰포트)까지 한 층씩 쌓아 올리고,
    할 일 관리·시스템 모니터 앱으로 마무리합니다. 슬라이드 N장 — boricha/ 전체 소스
    M줄이 한 줄도 빠짐없이 실려 있고, 모든 화면은 실제 실행 기록입니다 🍵`
13. Review pass with fresh eyes (every recording, every count, every claim, every 함정
    slide against the log), committed as `보리차 덱 리뷰 — <defect counts by type> 정정`.
14. `python3 tools/embed_mono_font.py --check` on the final deck (the builder's
    `gen_fonts.py` embeds; the check must pass), memory note update.

`history.md` gets one ≤12-line Korean entry per commit (prepend with a heredoc + temp
file; never read the whole file — `head -c 4000` only).

## 9. Verification checklist (before calling any step done)

- `make vet test` green, `go test -count=1 ./...` output saved to `out/go_test.txt`.
- `make record` twice → `git diff --stat out/` empty.
- `make tmux-smoke` captures show real colours (`-e`) and Korean text in the right columns.
- Build output: coverage 100 %, "오류 0건", slide count printed and ≥ 480.
- `node deck/check_deck.js` passes (slides, player, frames, widths ≤ 374 px content, fonts).
- `python3 deck/test_fonts.py` passes; `tools/embed_mono_font.py --check` passes.
- `deck/claims.md` has a source for every dated or standard-numbered claim on a slide.
- `index.html`/`README.md` numbers equal the build's slide count and `out/loc.txt`.

## 10. Open questions for the user (answer before step 1; defaults in bold)

1. Framework name/dir: **`boricha/` (보리차)** — or another name?
2. Capstone apps: **todo + monitor + showcase** — or replace one (e.g. a file browser)?
3. Windows: **stub + one slide** — or skip the file entirely?
4. Deck file name: **`나만의_Bubble_Tea_만들기.html`**.

## Progress log (newest first)

- 2026-09-07 01:47 — **commit 1 done.** go.mod (no require), Makefile (build/vet/test/cross/
  tmux-smoke/logs/deck), `term/` (seq, Term wrapper over io.Reader/io.Writer, unix ioctl +
  SIGWINCH, linux/darwin termios request consts, windows stub), `examples/00_raw`.
  1,058 lines. `go test` green, `go vet` clean, cross-compiles for darwin/arm64 and
  windows/amd64, real tmux capture in `out/tmux_00_raw.txt` (arrow key = `1B 5B 44`).
  Notes for later slides: (a) `Term` takes io.Reader/io.Writer so every sequence is
  testable without a tty — reuse this for testkit; (b) linux `syscall.Termios` fields are
  uint32 but darwin's are uint64 — portable test trick is `raw.Iflag = ^raw.Iflag`;
  (c) `syscall.SYS_IOCTL` does exist on darwin/arm64 (cross-build proved it);
  (d) CS8 == CSIZE == 0x30 on linux/arm64, so an all-ones Cflag passes the CS8 assertion
  by accident — the PARENB assertion is the one with teeth.
  함정 log: `deck/claims.md` not started yet; web verification of VT100/ECMA-48/DEC-mode
  claims still owed (batch it before part 1 is written).
- 2026-09-07 — plan written (Fable session). No code yet.
