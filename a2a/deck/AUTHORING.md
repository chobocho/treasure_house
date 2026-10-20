# Authoring guide — how to write one part of the A2A deck

You write **examples** (`ex/{py,ts,go}/NN/…`, `ex/run/NN/*.run`), run them
(`tools/a2arun.py`), and write **slides** (`deck/sections/NN_*.html`). You never touch the
built deck, the tools, `deck/base/`, the final agents in `ex/*/agents/` (report needed
changes instead), or another part's files. Working directory for every command: `a2a/`.

Read first: `PLAN.md` §0 (rules), `deck/SCENARIO.md` (the story every example serves),
`deck/OUTLINE.md` (your part's chapters and its "owns" list — and the neighbours' lists, so
you do not re-teach what they own), the model slides already written in
`deck/sections/02_basics.html`, and the component catalogue in `../template.html`
(slides `c-*`: callouts, tables, flow, quiz). Then the spec sections your part covers in
`docs/spec/docs/specification.md` (grep it; it is 3,600 lines) and `docs/spec/specification/a2a.proto`.

This guide starts from the lessons of the Rust deck (`../rust/deck/AUTHORING.md`, 169
lessons, ~1,800 review fixes). They are folded in below — follow them from the first slide.

## The loop

```
1. write   ex/py/NN/x.py · ex/ts/NN/x.ts · ex/go/NN/x/main.go    (≤ 45 lines, ≤ 72 columns)
           and, when servers are involved, ex/run/NN/x.run
2. format  ruff format --line-length 72 (py) · npx prettier --print-width 72 --write (ts)
           · gofmt -w (go) — only your own files
3. run     python3 tools/a2arun.py ex/run/NN/x.run   (or the single file)  → out/NN/x.txt
4. slide   <!--RUN …--> / <!--CODE …--> / <!--OUT …--> in deck/sections/NN_*.html
5. build   make deck SKEL=1                read every error line and fix it
```

Chapter by chapter: examples → run → slides → build → next chapter. If a capture surprises
you, the capture is right and your expectation was wrong — rewrite the prose, never the
capture. Never guess what an SDK does; read its installed source or run it.

## Examples

- **×3 means three files that do the same thing** in Python, TypeScript and Go, printing
  the *same* output where the protocol allows. When outputs differ because the SDKs differ
  (e.g. Python's DataPart numbers arrive as `30.0`), that difference is a finding: show it
  on a slide, do not hide it.
- One idea per file. Short English names (`card_fetch.py`). Korean comments that say *why*.
  Korean counts 2 columns, Go tabs count 4 (the builder enforces it; formatters count Korean
  as 1, so put a long Korean comment on its own line).
- Use the scenario: lodging/catering/bus/settlement/planner, 보물상사, the fixture data.
  Domain rules come from `workshop` (do not re-implement them in an example).
- Running agents in a capture: prefer the final agents (`py:agents/lodging.py --port …`)
  when the part is about the protocol (parts 3–5, 10–16); write focused servers under
  `ex/<lang>/NN/` when the part is about building (parts 2, 6–9).
- **Determinism**: no wall-clock time, randomness, unsorted map iteration, racing output.
  IDs and timestamps are normalised by the runner (`<id1>`, `<시각>`) — nothing else is.
  Concurrent requests in one tap need `order=sorted`.
- **Python servers scramble map order**: the Python SDK (upb) emits protobuf Struct/map keys
  (`data`, `metadata`, `scopes`, …) in a different order in every process (PYTHONHASHSEED
  does not help). The wire tap sorts keys under `data`/`metadata` (deeply) and
  `scopes`/`securitySchemes`/`schemes` (one level) — declared in part 0. So show a Python
  server's JSON **through the tap or the `ask` CLI** (which sorts), never as raw `curl`
  stdout, or `--check` will fail.
- **Python SDK stderr noise**: on some error paths (e.g. a message to a terminal task) the
  Python SDK prints OpenTelemetry "Failed to detach context" tracebacks with memory
  addresses. If a server's stderr is not part of the lesson, add `stderr=drop` to its
  `serve` line (the capture shows `2>/dev/null` on the command). Never drop stderr that a
  slide talks about.
- **Python SDK timing-dependent wording**: right after a task finishes, a message to it
  gets "is already completed."; after the SDK cleans up its in-memory task it gets "is
  in terminal state: …". Wait (≥ 1 s) before such a request so the capture is stable.
- **Go agents' `Begin`** moves the previous status message into history before
  re-publishing the Task (the Go SDK stores Task events as-is). Do not describe "Go keeps
  no agent questions in history" — that was a bug in our code, fixed 2026-10-16. Run `a2arun --check` on every capture
  at least twice before you trust it.
- Ports: 10000 + NN·100 + k. One runner at a time (it locks).
- **Every line of every example file is ≤ 72 columns** (`make lint` runs
  `tools/check_width.py` over all of `ex/`), not only the excerpted regions.
- Examples may import siblings in the same part directory; the whole `ex/<lang>/NN/`
  directory is an input of every capture made from it.
- Trailing directives: Python `# @ key: value` (ruff rewrites `#@` to `# @`), TS/Go
  `//@ key: value`. Keys: `args stdin exit timeout norun env`. Captures of single files
  carry the language: `out/NN/name.py.txt`, `.ts.txt`, `.go.txt`; specs `out/NN/name.txt`.
- `.run` spec lines may continue with a trailing `\` (keep specs ≤ 72 columns — SPEC
  shows them). `ready=` must point at the server port, not the tap.
- Code you want to excerpt goes between `# region: name` / `# endregion` (`//` in TS/Go);
  use `<!--CODE … region=name-->` rather than `lines=` (line numbers drift).
- Errors are lessons too: provoke the real error (`-32001` …, 401, invalid_scope) and show
  the real response; never type an error message.

## Slides

```html
<article class="card" id="p05-input-required">
<h3>모자란 정보는 INPUT_REQUIRED 로 되묻는다</h3>
<p class="lead">왜 이것이 필요한지 한두 문장.</p>
<!--RUN …-->
<div class="key"><b>머리말</b> — 이 장에서 하나만 기억할 것.</div>
</article>
```

- `id` required, unique, prefix `pNN-`. Part cover `class="card section" id="pNN"`; second
  slide `pNN-intro` (이 부에서 할 일 + chapter list); chapter covers `pNN-chM` with
  `<p class="chnum">M장</p><h2>…</h2><p class="chsub">…</p>` (topics in slide order).
- One slide = one idea. The `<h3>` states the point ("카드의 url 은 바깥에서 닿는 주소다"),
  not the topic. `p.lead` (why) → evidence (RUN/CODE/OUT) → one callout or a 2–3 item list.
- **×3 rhythm**: concept slide → Python → TypeScript → Go → "세 언어 비교" slide (a table of
  what differs: type names, how a Part is built, where the event goes). Do not repeat the
  concept prose on each language slide; each says only what is particular to that language.
- **Wire slides**: show the exchange with `<!--OUT … wire=… ex=N-->`; the callout reads it
  ("`result.task.status.state` 가 …"). Quote field names exactly as on the wire.
- **Reading a capture**: never count output lines ("셋째 줄") — quote the value or the field.
- **Evidence**: every sentence about behaviour is shown by the capture on that slide or links
  the slide that shows it. Spec claims cite the section ("§3.2.2") and use the spec's words
  for MUST/SHOULD. No speed claims, no "most popular", no claims about other protocols
  beyond what part 1's sources say.
- **Don't re-teach**: the reader has read the earlier parts. Use what an earlier part owns
  with one clause + a slide-level link (`<a href="#p04-part-kinds">4부</a>에서 본 Part`) and
  say only what is new. Parts not yet in `deck/order.txt` are mentioned in plain text.
- No hand-written `<pre>` (rejected). Diagrams: `<pre class="fig">` (ASCII/box, ≤ 72 cols,
  no code, Korean labels at line ends), `.flow`, or a table. Inline `<code>`; escape
  `<`, `>`, `&`.
- Tables: `<div class="tblwrap"><table class="kv">…</table></div>`.
- Each chapter ends with one quiz (`class="card quiz"`, `data-quiz`, `.q`,
  `<button>답 보기</button>`, `.a`) whose answer a capture in that chapter proves.
- The part's last slide has a `.note` headed "다음" handing over to the next part.
- Korean 합니다체, plain words. English term in parentheses once, on the defining slide.
  Fixed translations (add to this list via the orchestrator, never invent a second one):
  agent 에이전트, Agent Card 에이전트 카드(Agent Card — keep the English in titles),
  task 작업(Task), message 메시지, part 파트, artifact 아티팩트, skill 스킬,
  capability 기능(capability), context 맥락(contextId 는 그대로), stream 스트림,
  push notification 푸시 알림, webhook 웹훅, binding 바인딩, interface 인터페이스,
  extension 확장, security scheme 보안 스킴, scope 스코프, token 토큰,
  signature 서명, canonicalization 정규화(JCS), executor 실행기(AgentExecutor),
  request handler 요청 처리기, event queue 이벤트 큐, orchestrator 오케스트레이터,
  delegate 맡기다/위임, interop 상호운용, event 이벤트(SSE 이벤트·스트림 이벤트 —
  "사건" 은 쓰지 않는다), JSON-RPC notification JSON-RPC 알림(푸시 알림과 헷갈리지
  않게 앞에 JSON-RPC 를 붙인다), batch 배치, wiretap 와이어 탭, filter 필터("거르개"는
  쓰지 않는다), body limit 본문 한도, exponential backoff 지수 백오프, jitter 지터,
  crashed server 죽은 서버(죽이다·죽다 — "넘어지다" 는 쓰지 않는다), orphaned task
  주인 없는 작업, recovery rule 복구 규칙, ActiveTask 활성 작업, TCK 적합성 시험(TCK),
  opaque execution 불투명 실행, point-to-point integration 점대점 통합("짝마다 통합" 은
  쓰지 않는다), Technical Steering Committee 기술 운영 위원회(TSC),
  capture normalisation 캡처 정규화(러너가 id·시각을 바꾸는 일 — JCS 정규화와 헷갈릴 자리
  에서는 앞에 "캡처" 를 붙인다).
  factory 팩토리, header 머리글(머리·헤더 는 쓰지 않는다; gRPC trailer 꼬리 메타데이터),
  interceptor 가로채기, Latin 문자열 순서 알파벳순(가나다순은 한글에만).
  Python extra → "extra(선택 설치 묶음)", route factory 라우트 팩토리, owner-scoped
  store 소유자별 저장소(분리). Never coin playful new words ("덤", "공장", "칸막이").
  Enum values and method names stay in English as on the wire (`TASK_STATE_WORKING`,
  `SendMessage`).

## Done means

- Every example of your part passes `a2arun --check` twice; `make lint ts-check` clean for
  your files; `make deck SKEL=1` shows no error from your files; your part's slide count is
  within ±10 % of `deck/budget.txt`.
- Final message (English, short): files written, slide count, examples (×3 count), captures,
  findings about SDK differences or spec inconsistencies (deck-worthy), new terms, anything
  you could not do and why. Do not commit — the orchestrator reviews and commits.

## Machine rules (the session dies if you ignore these)

One command at a time; no sub-agents; no `make all`, no `make -j`; never more than one
compiler/`go build`; servers only through `a2arun` (it kills them) — if you start one by
hand for exploring, kill it **by PID**, never `pkill -f` (it matches your own shell).
Do not read whole large files (spec: grep; built deck: never). Keep a log
`scratch/<your-task>-log.md`, one line per finished chapter, and resume from it.
No `git stash/checkout/reset`, no commits.
