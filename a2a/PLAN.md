# A2A 프로토콜 완전 가이드 (A2A_프로토콜_완전_가이드.html) — Work Plan for the Building Agent

Read this file first in every session. The progress log at the bottom is the only state that
survives a killed session (this machine kills sessions — see §0.9). Agent-facing text is
English; the deck itself is Korean.

## 0. Non-negotiables

1. **The deck HTML is a build artifact.** Never edit `../A2A_프로토콜_완전_가이드.html` by
   hand. Edit `deck/sections/*.html` (or the example/capture it points at) and run `make deck`.
2. **Only code that runs.** Every code `<pre>` in the deck is cut from a real file under `ex/`
   by the builder; every output (program output, HTTP wire exchange, SSE stream, error) is a
   capture under `out/` written by `tools/a2arun.py` on this machine. No hand-written code,
   output, JSON payload or HTTP exchange in a section file. Hand-written `<pre>` is rejected by
   the builder (only `<pre class="fig">` ASCII/box diagrams with no code are allowed).
3. **Three languages, one scenario.** Python, TypeScript, Go. Every agent of the scenario
   (§3) is implemented in all three languages, and part 16 runs the 3×3 interop matrix
   (every client language against every server language). The three implementations share
   `ex/fixtures/` and must agree on the golden vectors in `ex/fixtures/golden/`.
4. **Rule-based agents, no LLM.** No model calls, no API keys. Agents are deterministic
   functions of fixtures and input so captures are reproducible. The deck explains where an
   LLM would plug in (the executor), but never runs one.
5. **Spec = A2A v1.0.1** (tag `v1.0.1`, 2026-05-28) cached under `docs/spec/` (not committed,
   `make docs` re-fetches). Every normative claim ("MUST", field names, method names, error
   codes) is checked against `docs/spec/docs/specification.md` or
   `docs/spec/specification/a2a.proto`. Where the spec text and the proto disagree (they do —
   e.g. REST `SubscribeToTask` is `GET` in the proto but `POST` in §5.3's table), say so on
   the slide and show what the SDKs actually do.
6. **Knowledge-cutoff discipline.** The author model's knowledge ends 2026-06. A2A v1.0 and
   all three SDK versions below are at or past that edge. Write about SDK behaviour only from
   (a) the installed SDK source/type definitions and (b) captures. Never from memory.
7. **History facts have sources.** Dates, versions, organisations: `data/sources.tsv` +
   cached text under `docs/` + `make data-check` (evidence string must be in the cached
   text). Same mechanism as `../rust/` (`<!--SRC key=…-->`, `<!--FACT id=…-->`).
8. **Tests before code (RED → GREEN)** for every Python tool here (`tools/tests`, unittest).
   Never loosen an assertion to pass.
9. **Machine: Galaxy Fold, Termux/proot, swap nearly full.** At most **1 subagent** at a
   time besides the orchestrator. One runner at a time (`a2arun` takes `scratch/run.lock`),
   Go builds with `-p 1`, no `make -j`. Every subagent keeps a log file
   `scratch/<task>-log.md` (one line per finished unit) and resumes from it if present.
   Commit after every part (or half part); log here.
10. **Foldable layout.** Code `<pre>` ≤ 45 lines and ≤ 72 columns (Korean = 2 columns; Go
    tabs are shown as 4 spaces and counted as 4); captures ≤ 108 columns (wrapped on screen
    up to 200). One slide = one idea.
11. **Hard cap 2000 slides** (user decision 2026-10-16). Target band 1,600–1,850. Per-part
    budgets in `deck/budget.txt`; the builder fails above 2000 total or a part above +10 %.
    Never pad to reach a budget.
12. **Language:** deck prose Korean 합니다체; identifiers English; comments inside examples
    Korean (short). Commit messages Korean descriptive, no prefix (repo convention). No
    `git push` unless the user asks. Do not stage the user's unrelated uncommitted
    `user-select` CSS change in other decks/template.

## 1. Toolchain (verified 2026-10-16, hello 3×3 gate passed)

| Lang | Runtime | SDK | Notes |
|---|---|---|---|
| Python | `/usr/bin/python3` 3.14.4 → venv `a2a/.venv` | `a2a-sdk[http-server,grpc,signing]==1.2.2`, uvicorn, ruff | types are protobuf messages (`a2a.types`); `DefaultRequestHandler` = V2 |
| TypeScript | Node 24.18 (runs `.ts` directly by type stripping) | `@a2a-js/sdk` 1.3.0, express 5, typescript 7.0.2, prettier 3 | tsc 7 is native: `@typescript/typescript-android-arm64` is aliased to the linux-arm64 package and needs `npm install --force`. tsc only type-checks (`noEmit`). Part = `{content: {$case, value}}` (ts-proto) |
| Go | go 1.27.1 (Termux) | `github.com/a2aproject/a2a-go/v2` v2.6.0 | module `example.com/workshop` in `ex/go`; executor is `iter.Seq2[a2a.Event, error]` |

Wire facts seen at the gate: JSON-RPC method `SendMessage`, header `A2A-Version: 1.0`,
`"role":"ROLE_USER"`, Part `{"text":…}` (no `kind`), result `{"message":{…}}` or `{"task":…}`.
The TS card handler serialises empty fields (`"tenant":""`, `[]`); Python/Go omit them.

## 2. Directory layout

```
a2a/
  Makefile              every command (`make help`)
  PLAN.md               this file
  .venv/                python venv (ignored)          docs/  spec + source cache (ignored)
  data/sources.tsv      history sources; facts.tsv claims ↔ evidence
  ex/fixtures/          shared scenario data (JSON) + golden/ vectors
  ex/py/                PYTHONPATH root; package workshop/ (domain + agents); NN/*.py examples
  ex/ts/                package.json, tsconfig.json; workshop/*.ts; NN/*.ts
  ex/go/                go.mod (example.com/workshop); workshop/ pkg; NN/<name>/main.go
  ex/run/NN/<name>.run  multi-process capture specs (servers + clients + wire tap)
  out/NN/<name>.txt     captures (committed — they are the evidence); out/MANIFEST.tsv
  tools/a2arun.py       the only thing that runs examples and writes captures
  tools/wiretap.py      logging reverse proxy (HTTP + SSE) used by a2arun
  tools/tests/          unittest
  deck/build_deck.py    sections + ex + out → deck (adapted from ../rust/deck/build_deck.py)
  deck/base/{head,tail}.html   cut from ../template.html
  deck/sections/NN_*.html      deck/OUTLINE.md · AUTHORING.md · REVIEW.md · SCENARIO.md
  scratch/              work dir, logs, briefs (ignored)
```

## 3. The scenario (contract in `deck/SCENARIO.md`)

"보물상사 가을 워크숍 준비": a planner agent receives "1박 2일, 30명, 예산 600만 원" and
delegates to four agents. Together they exercise every A2A feature:

| Agent | Skill | A2A features |
|---|---|---|
| 숙소 lodging | find-lodging | blocking SendMessage → Task, DataPart in/out, `INPUT_REQUIRED` multi-turn, `REJECTED` |
| 식사 catering | plan-meals | SendStreamingMessage (SSE), status updates, artifact chunks (`append`, `lastChunk`), FilePart (raw/url) + DataPart |
| 교통 bus | book-bus | `returnImmediately`, long-running, push notifications (webhook + token), GetTask polling, ListTasks, CancelTask, SubscribeToTask |
| 정산 settlement | settle-budget | security schemes (OAuth2 client-credentials from a local token issuer, Bearer), `AUTH_REQUIRED`, extended Agent Card, signed Agent Card (JWS/JCS) |
| 기획 planner | plan-workshop | server *and* client: discovery by card/skills, fan-out, contextId/referenceTaskIds, aggregated plan artifact, streams progress |

Plus one custom extension (budget metadata, `A2A-Extensions` header) for part 14.

## 4. Parts and budgets (`deck/budget.txt` is authoritative)

| # | file | part | slides |
|---|------|------|--------|
| 0 | 00_start | 읽는 법·시나리오·환경 | 40 |
| 1 | 01_why | 왜 A2A인가 — MCP와의 관계·역사 | 60 |
| 2 | 02_basics | 바탕 지식 — HTTP·JSON-RPC 2.0·SSE (맨손, 3언어) | 70 |
| 3 | 03_card | Agent Card와 발견 | 100 |
| 4 | 04_message | Message·Part·Role·contextId | 100 |
| 5 | 05_task | Task 생애주기·상태 기계·다중 턴 | 120 |
| 6 | 06_bare | 맨손 구현 — 표준 라이브러리만으로 서버·클라이언트 | 130 |
| 7 | 07_py | 공식 SDK — Python | 120 |
| 8 | 08_ts | 공식 SDK — TypeScript | 120 |
| 9 | 09_go | 공식 SDK — Go | 120 |
| 10 | 10_stream | 스트리밍·아티팩트 청크·재구독 | 120 |
| 11 | 11_push | 푸시 알림·장기 작업·취소·목록 | 120 |
| 12 | 12_security | 보안 — 인증 스킴·OAuth2·확장 카드·서명 | 120 |
| 13 | 13_binding | 전송 바인딩 — JSON-RPC·HTTP+JSON·gRPC | 90 |
| 14 | 14_ext | 확장과 버전 협상 (v0.3 호환 포함) | 60 |
| 15 | 15_scenario | 시나리오 완성 — 다언어 에이전트 메시 | 140 |
| 16 | 16_interop | 3×3 상호운용·적합성·오류 처리 | 90 |
| 17 | 17_ops | 운영 — 타임아웃·재시도·영속 저장소·로깅 | 70 |
| 18 | 18_appendix | 부록 — 오류 코드표·필드 사전·용어집·찾아보기 | 60 |

Total 1,850. Parts larger than ~60 slides are written in halves (`NN_` + `NNb_`), one
subagent task each.

## 5. Steps

1. Environment gate (done 2026-10-16).
2. Skeleton + tools — tree, base, placeholders, `a2arun`, `wiretap`, `build_deck`, tests;
   `make deck SKEL=1` opens; `make all SKEL=1` green.
3. Scenario core — `deck/SCENARIO.md`, fixtures, golden vectors, `workshop` domain module in
   all three languages with tests (`make golden`).
4. Data — `make docs` (spec + history sources), sources/facts check.
5. Parts in dependency order: 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 → 14 →
   15 → 16 → 17, then 1, 0, 18. Commit per part / half.
6. Wrap-up — `make all` without SKEL, font, index.html card, README.md, history.md.
7. Review 1 (facts & evidence), review 2 (flow & style), `a2arun --check --all` twice.

## 6. Decisions (user, 2026-10-16 — final, do not re-ask)

1. Scenario: 보물상사 가을 워크숍 준비. 2. Every agent in all three languages + 3×3 matrix.
3. Bare-hands parts (2, 6) included. 4. Rule-based only, no LLM. 5. gRPC included.
6. File `A2A_프로토콜_완전_가이드.html`, directory `a2a/`. 7. Hard cap 2000 slides.

## Progress log (append only; newest at the bottom)

### Plan written, environment gate passed (2026-10-16)
- Installed the three SDKs (§1). Hello agents in py/ts/go, each language's client called all
  three servers over JSON-RPC: 9/9 OK (`scratch/gate/`, `ex/ts/gate/`, `ex/go/gate/` —
  throwaway, delete once real examples exist). Spec v1.0.1 cached in `docs/spec/`.

### Scenario contract and outline (2026-10-16)
- `deck/SCENARIO.md` (rules, fixtures, golden story numbers: 2,100,000 + 1,542,000 +
  1,200,000 = 4,842,000) and `deck/OUTLINE.md` (chapters, "owns" lists) written.
- Decision: parts 3–5 drive the *final* agents (`ex/<lang>/agents/`) as black boxes and read
  the wire, so step 3 builds domain ×3 **and** the five final agents ×3 before any part is
  written. Part 15 explains them; parts 6–9 teach how to build them.
- Tools subagent launched with `scratch/brief-tools.md` (log `scratch/tools-log.md`).

### Scenario core — domain ×3 and Python agents (2026-10-16)
- Fixtures `ex/fixtures/{workshop,clients}.json`, golden `ex/fixtures/golden/domain.json`
  (44 hand-computed cases). Domain in py/ts/go: 44/44 each (RED first via NotImplemented /
  "not implemented" / panic). Lint: ruff (line 72), prettier (72), gofmt/vet; width ≤ 72
  checked with Korean = 2 cols (`scratch` helper w.py — the tools must enforce this).
- Python final agents `ex/py/agents/`: common, lodging, catering, bus, settlement, planner,
  ask (scripted CLI), webhook. Full story run by hand: planner discovers 4 cards (verifies
  the settlement card's EdDSA signature with the *pinned* JWKS, not the card's `jku`),
  fans out, settlement → AUTH_REQUIRED → planner relays AUTH_REQUIRED → user "승인" →
  approve-scope token → COMPLETED; plan totals match golden (4,842,000).
- Findings for the deck: Python SDK serialises DataPart numbers as doubles (`30.0`,
  `2100000.0`) and Struct key order is not insertion order → `ask` sorts keys and shows
  integral floats as ints (part 4/16 must explain; Go typed decoding of `30.0` into int
  fails). python-multipart is not installed → token endpoint parses the form with
  `urllib.parse`. Keys switched to Ed25519 (deterministic signatures).
- Next: TS and Go ports of the agents (one subagent each, after the tools agent), with the
  rule that `ask` transcripts and server log lines are identical across languages.

### Tools landed; history sources (2026-10-16)
- Tools subagent done (report in session): a2arun/wiretap/build_deck/verify/check_deck, 126
  tests, `make all SKEL=1` green. Deviations accepted: single-file captures carry the
  language (`out/NN/x.py.txt`), Python directives are `# @ key:` (ruff), specs may continue
  with `\`, shared-source hashing covers every non-NN dir of a language root. Gate dirs
  deleted; first commit b042a020.
- History data: `tools/fetch_sources.py` + `tools/make_data.py` (facts only; 9 tests,
  RED first), `data/sources.tsv` (9 primary sources: Google launch 2025-04-09, Google
  donation + LF press 2025-06-23, LF AI & Data ACP merge 2025-08-29, Anthropic MCP
  2024-11-25, GitHub releases API, CHANGELOG / announcing-1.0 / whats-new at tag v1.0.1),
  `data/facts.tsv` 13 seed facts, all matched. `make sources data data-check`; data-check
  is in `make all`. Caveat for part 1: GitHub lists v0.1.0/v0.2.0 as published
  2025-06-09 (back-filled) — never present those as original release dates.
- TS port subagent running (`scratch/brief-port.md`, log `scratch/port-ts-log.md`).

### TS port done; follow-up Task rule (2026-10-16)
- `ex/ts/agents/` (8 files) by subagent; py/ts cross-checked in 6 combos (sub-agents ×
  planner × ask language) with `scratch/run_all.sh` (+ `h.sh`, `drive.py` for push/cancel):
  identical except one line, below. Signed card: Ed25519 signature byte-identical py/ts.
- **Spec §3.1.2** (Task stream MUST begin with the Task) also on follow-up turns. TS SDK
  enforces it; **Python SDK 1.2.2 neither emits it nor tolerates it**: if the executor
  re-enqueues the Task on a follow-up, `active_task._handle_initial_task` logs "already
  exists. Ignoring task replacement" and sets `message_to_save = None` → the user's reply
  is dropped from history (verified: planner forgot the 2nd answer). Decision: Python
  `begin()` enqueues only on the first turn; TS `begin()` re-publishes the Task with state
  WORKING (re-publishing the stale INPUT/AUTH_REQUIRED state makes a *blocking* Python-side
  call return at once). Consequence: when the *server* is TS, the ask transcript has one
  extra `task WORKING` line after each `> reply`. Part 16 shows this; refs: `scratch/ref/`
  (py servers) and `scratch/ref-ts/` (ts servers).
- Other TS findings for parts 8/12/16: `agentCardHandler` JSON.stringify's the ts-proto
  object (oneofs as `$case`, empty defaults) → agents serve `AgentCard.toJSON`;
  `canonicalizeAgentCard` drops oneofs on typed cards → sign/verify the JSON form; jose
  keeps header insertion order vs PyJWT sorted → insert `alg,jku,kid,typ`;
  `keepBusAliveStates` default keeps AUTH_REQUIRED streams open → set to INPUT_REQUIRED;
  second CancelTask: TS returns the task (§3.3.1 idempotent) vs Python -32002 (§3.1.5) —
  a real spec tension; TS logs "Reference task … not found." on stderr; Python card's
  `scopes` map order varies per process (JCS sorting keeps the signature stable).
- Python regions split to ≤ 45 lines (settlement: tokens/bearer/card/sign/executor;
  planner: discover/delegate/token/plan/settle; common: begin).

### Go port done — three languages interoperate (2026-10-16)
- `ex/go/agents/` (7 programs + `common/` package, 2,207 lines) by subagent; go.mod now
  requires a2a-go/v2 v2.6.0. Cross-checked 8 language mixes (sub-agents/planner/ask) and
  6 push pairings; Go servers match `scratch/ref-ts/` (Go re-publishes the follow-up Task
  as WORKING, like TS). Orchestrator re-ran go/go/py: identical to ref-ts.
- Accepted decisions: (1) **AUTH_REQUIRED in Go**: the SDK treats only terminal +
  INPUT_REQUIRED as final, keeps the run alive and refuses a new message on the task
  ("execution is already in progress"; SDK test `TestRequestHandler_SendMessage_AuthRequired`).
  `common/park.go` parks the executor and routes the follow-up message to it via a wrapper
  around `InterceptedHandler.Handler` — part 9/12 must explain this model difference.
  (2) Settlement card signed and served in the defaults-dropped form (the SDK's
  `NewSignedCardProducer` signs `json.Marshal` incl. `false`, which py/ts canonical forms
  drop → unverifiable cross-language); other Go cards keep `"pushNotifications":false`.
- More findings: Go push sender uses `A2A-Notification-Token` (py/ts use
  `X-A2A-Notification-Token`; spec names none), blocks private networks by default, and
  fails the task when a push fails → custom sender; in-memory store refuses anonymous
  ListTasks (-31401) → login hook "anonymous"; gob deep copy needs plain JSON values in
  DataParts; UUIDv7 ids; `Www-Authenticate` header casing.

### Part 2 written — 74 slides (2026-10-16)
- Subagent wrote `02_basics.html` (5 chapters, 74 slides, 28 example files, 9 specs, 22
  captures, all `--check` twice). Orchestrator review: "사건" → "이벤트" everywhere (terms
  list updated), Go rpc_client width fix, softened an unbacked "always" in the batch note.
- Tool fix (TDD): `a2arun._read` now keeps CR (`newline=''`) so `curl -i` captures can pass
  `--check`. Sources added: `jsonrpc`, `whatwg-sse` (part 2 cites them in prose; review
  should add SRC links).
- Findings for later parts: spec never mentions batch, Python SDK rejects it (-32600
  "Batch requests are not supported", jsonrpc_dispatcher.py:246); §9.3 template still says
  `"method": "category/action"`; §9.5 message strings differ from JSON-RPC 2.0's.

### Part 3 first half — 52 slides; wiretap sorts unordered maps (2026-10-16)
- Subagent wrote `03_card.html` ch1–4 (52 slides, 9 specs, `--check` ×3); `03b_card.html`
  added to order.txt for ch5–8 (ids must still start `p03-`).
- Python SDK (upb) map/Struct key order changes per process even with PYTHONHASHSEED → wire
  captures of Python artifacts were nondeterministic. Wiretap now sorts keys under
  `data`/`metadata` (deep) and `scopes`/`securitySchemes`/`schemes` (one level), TDD
  (wiretap tests 16). Part 0 must list this normalisation. AUTHORING updated.
- Findings (3a): Go card key order = struct order, writes `pushNotifications:false`; TS
  adds `charset=utf-8`; base URL with a path is resolved three different ways; Python
  client knows only JSON-RPC by default (TS/Go also HTTP+JSON) so the same two-door card
  leads to different doors; all three put card `tenant` into `params.tenant`; Go card fetch
  sends no A2A-Version header; connection-refused messages differ in detail.

### Part 3 complete — 103 slides (2026-10-16)
- Subagent wrote `03b_card.html` ch5–8 (51 slides; skills/pick ×3, capabilities §3.3.4
  errors provoked on a no-capability agent ×3 + client-side pre-checks, card caching /
  conditional GET 3×3, card validator ×3). Tool fix (TDD): spec inputs now include the
  data subdirectories beside the spec (`ex/run/NN/rpc/`, `cards/`).
- Findings: all three servers answer §3.3.4 with -32004 (stream, extended card) and
  -32003 (push) — extended card is not -32007; Go checks capabilities only with
  `a2asrv.WithCapabilityChecks`; Go wraps the stream error in an SSE event; clients
  pre-check the card differently (Python/TS return the public card for extended-card
  without asking; Go answers -32007 locally; TS blocks push before sending); cache
  headers: Python weak ETag only, TS weak ETag + max-age=3600, Go none; Node fetch adds
  no-cache to conditional requests so TS↔TS never gets 304; TS resolver returns raw JSON
  (omitted fields undefined despite types); input-mode validation differs (py defaults +
  skills, ts defaults only, go none).

### Part 4 first half — 54 slides (2026-10-16)
- `04_message.html` ch1–4 (Message anatomy, Part kinds ×3, Message vs Task replies ×3,
  DataPart numbers 3×3). `04b_message.html` added to order for ch5–8.
- Findings: required-field checks differ (py -32602 with proto field names, go -32602 per
  case, ts checks only messageId — accepts no role / empty parts); history storage differs
  (py/ts fill contextId/taskId, ts also appends the INPUT_REQUIRED agent message); unknown
  extension URIs accepted by all; v0.3 `file` part: py/ts accept as empty part, Go rejects
  with -32700 (wrong code — JSON is valid); two content fields: py -32602, ts keeps first
  silently, go -32700; TS client returns bare Message|Task; Go `%v` prints 2.1e+06; Go
  lists unknown part keys in random map order (avoid in captures).

### Part 4 complete — 102 slides (2026-10-16)
- `04b_message.html` ch5–8 (48 slides): FilePart/acceptedOutputModes/-32005 ×3 (new
  "접수 에이전트" intake ×3), §3.4 contextId rules ×3, duplicate messageId, ProtoJSON input
  tolerance ×3. Review fixes: intro wording (two experimental agents), "거르개" → "필터",
  `protojson.py` timestamp precision now taken as the max over all answers (one stamp with
  trailing zeros trimmed made a 0.1 % flake).
- Tool fix (TDD): runner normalises Go log headers `2026/10/16 11:53:57` → `<시각>` (Go SDK
  slog lines on stderr made Go-agent error captures flaky).
- Findings: TS JSON-RPC body limit 100 KB (`express.json()` default) → bare 413 without a
  JSON-RPC error; no server SDK reads acceptedOutputModes; -32005 only when py/ts input-
  mode validation is switched on, Go executor must return `ErrUnsupportedContentType`;
  duplicate messageId → all three run the executor twice; ProtoJSON input tolerance
  differs widely (snake_case, `"role":"user"`, numeric enums); **Python ListTasks silently
  ignores an unknown status filter and returns everything**; empty lists `[]` vs Go
  `null`; timestamp precision ms (ts) / µs (py) / ns (go); Go SDK stamps local time
  (`+09:00` on a KST host would violate §5.6.1 — this machine is UTC).

### Part 5 first half — 61 slides (2026-10-16)
- `05_task.html` ch1–5 (Task shape ×3, nine states / transitions ×3, blocking vs
  returnImmediately ×3, reading a COMPLETED task ×3, INPUT_REQUIRED multi-turn ×3).
  Orchestrator re-ran every part-5 capture 3× — all identical.
- Findings: no SDK enforces transitions; a late update after COMPLETED: Python stores it if
  a fresh TaskUpdater sends it (task "revives" as WORKING), TS ignores it (queue stopped),
  Go cancels the executor ctx (yield result racy — example checks ctx.Err()); every server
  returns SUBMITTED for returnImmediately; SUBMITTED Task has no status.timestamp; no
  createdAt/lastModified anywhere (whats-new-v1 claims them — check in review!); history
  of agent questions: py moves status.message into history on the next user message, ts
  appends at once, go never (4 turns → 7/7/4 messages); TS enforces the first-event rule,
  Go does not for stored tasks; §3.4.3 still says "input-required"; interrupted states
  that end an execution: py both, ts/go INPUT_REQUIRED only.

### Part 5 complete — 118 slides; Go history bug fixed (2026-10-16)
- `05b_task.html` ch6–9 (57 slides): REJECTED/FAILED/CANCELED ×3, historyLength ×3,
  artifacts ×3, task errors and ErrorInfo shapes ×3.
- **Our Go `common.Begin` dropped the agent's question from history** when re-publishing
  the Task (Go SDK stores Task events as-is, moving status messages into history only on
  status updates). Fixed in `working()` (moves the old status.message first; identity
  check `h[n-1] == cur` so a duplicate messageId keeps the right order). Rewrote
  p04-dup-hist, p05-ir-hist, p05-ir-hist-cmp, p05-hl-go-short, p05-hl-cmp; Go region
  `begin` split into `begin` + `working` (≤ 45 lines). Old term "사건" removed from all
  agent code comments.
- errors.run was flaky (1 in ~6): Python wording "already completed" vs "in terminal state"
  depends on SDK cleanup timing → `errors.py` waits 1 s first; that path makes the Python
  server print OpenTelemetry tracebacks with addresses → new runner option
  `serve … stderr=drop` (shown as `2>/dev/null`, TDD, 2 tests). Verified 3× identical.
- Findings: executor exceptions → py -32603 without data (FAILED stored silently), ts FAILED
  task with "Agent execution error: …", go FAILED task without message (or -32603 +
  INTERNAL_ERROR if no Task yet); negative historyLength: py -32602, ts/go treat as 0;
  ErrorInfo: py `metadata:{}`, ts no metadata, go `metadata.timestamp`, none puts taskId as
  §9.5's example does; TS has no artifact id generator; CancelTask/GetTask return the Task
  as `result` directly.

### Part 6 first third — 47 slides; lodging agents' history bug fixed (2026-10-16)
- `06_bare.html` ch1–3 (goal, dispatch/errors ×3, store/transitions ×3). The writer built
  the complete bare lodging server ×3 (`ex/{py,ts}/06/bare_lodging.*`, `ex/go/06/bare_lodging`
  + `bare_store`/`barestore`) with regions for 06b/06c (list in the 6a report: card,
  rpc-error, a2a-errors, version, lodging, work, check, begin, send, get, cancel, stream,
  methods, dispatch, call, http; store: states, ids, store, move, artifact, view; Go extra
  helpers, find, envelope, types, events). Bare servers start every stream with a Task
  (follow-ups with WORKING) → their transcripts equal `scratch/ref-ts/`.
- **Bug found by the writer, fixed by the orchestrator: all three final lodging agents
  read the whole history, including their own questions, so the example "(예: 2026-10-30)"
  counted as the user's date.** Now they read ROLE_USER messages only (py/ts/go). Verified:
  `'숙소 부탁합니다' '30명' '1박' '2026-11-06'` → asks the date until given → 춘천 1,860,000.
  Side effect: TS-accepted role-less message is now "not heard" → p04-msg-required-ts
  rewritten (INPUT_REQUIRED instead of COMPLETED).
- Findings: Go 1.27 has a std `uuid` package; Python SDK version validator accepts any
  same-major version ("1.5") although §3.6 says match Major.Minor (part 14).

### Part 6 second third — 45 slides (2026-10-16)
- `06b_bare.html` ch4 (SendMessage/GetTask/CancelTask ×3, 28) and ch5 (SSE ×3, 17).
  Writer fixed a real bug in the TS bare server: `body += chunk` split UTF-8 across chunk
  boundaries (100k '가' → 8 U+FFFD) → `req.setEncoding("utf8")`.
- Findings: Python bare SSE is HTTP/1.0, no length, ends by close (`wfile.flush()` is a
  no-op, wbufsize=0); Node/Go send chunked HTTP/1.1, one chunk per event. **Spec tension:
  §3.1.2 closes the stream at a terminal state, §11.7 at "terminal or interrupted"** (bare
  servers follow §11.7). Error shape before the first stream event is unspecified (Go SDK
  sends an SSE event, bare servers plain JSON). Open: Go bare ignores Unmarshal errors in
  getTask/cancelTask (`"historyLength":"2"` → full history; numeric id → taskId "") —
  handed to 06c ch8; ProtoJSON allows int32 as string, py/ts bare reject "2".

### Part 6 complete — 131 slides (2026-10-16)
- `06c_bare.html` ch6 bare client ×3 (14), ch7 interop matrices (9), ch8 what bare misses
  (15) + wrap. Go bare server fixed (`params` region: historyLength "2" → -32602, numeric id
  → taskId "5"); `lax_params` shows the old mechanism (Unmarshal allocates *int → &0).
- Matrix A: ask py/ts/go × (3 SDK + 3 bare servers) = 18 cells → exactly 2 transcripts
  (= scratch/ref for the Python SDK server, = ref-ts for the other five).
- Findings: ProtoJSON allows int32 as string — py/ts SDK accept `"historyLength":"2"`, Go SDK
  and bare servers reject; SDK client wire differences (JSON-RPC id UUID vs 1, `configuration:{}`,
  Accept headers); bare servers answer push/extended card with -32601 (violates §3.3.4);
  **version handling: TS SDK rejects "1.0.1" (exact match, violates §3.6), py accepts "1.5"
  (major only), Go SDK server never reads A2A-Version; none supports `?A2A-Version=`**;
  a half-sent request stalls the Python bare server (single-threaded).

### Part 7 first half — 62 slides; width check; part-dir inputs (2026-10-16)
- `07_py.html` ch1–5 (package map, types, executor, handler/store, serving), with
  reusable "N장 정리" tables for parts 8/9. Step examples `ex/py/07/step1_echo.py`,
  `step2_task.py` (7b continues with step3…). Terms fixed: 덤→extra(선택 설치 묶음),
  경로 공장→라우트 팩토리, 주인별 칸막이→소유자별 분리/저장소.
- Tools (TDD): `tools/check_width.py` in `make lint` (all example lines ≤ 72; 17 old lines
  fixed in parts 3–6); single-file and spec captures now hash their whole part dir
  `ex/<lang>/NN` (siblings imported by drivers); build_deck test fixture re-records the
  manifest when a test adds a new example file. One unexplained `make all` rc=2 that did
  not reproduce (suspect live tool tests' port timing) — watch for it.
- Findings: executor that enqueues nothing → blocking SendMessage hangs forever
  (active_task.py:967); Task with a different id → -32602 (blamed on the client); A2A error
  raised by the executor goes to the client but the task is stored FAILED; docstring says
  TASK_STATE_ERROR (doesn't exist); client transport parses responses strictly while the
  server ignores unknown fields (7b ch6 should run it); `related_tasks` empty by default
  (`should_populate_referred_tasks=False`, part 15); InMemoryTaskStore scoped by
  `user.user_name` (anonymous share ""); REST SubscribeToTask registered for GET and POST;
  `A2ARequest` union lacks ListTasksRequest; uvicorn is in no extra.

### Part 7 complete — 121 slides (2026-10-17)
- `07b_py.html` ch6 client (17), ch7 finished lodging agent (13), ch8 in-process tests (13),
  ch9 SDK-only features (16) + part wrap. Examples in `ex/py/07/` + `ex/run/07/`
  (client, strict, lodging, compat, otel). Lodging agents ×3 got `region:` markers; deck
  cites `region=` instead of `lines=` (03_card too); 07a chapter refs became links.
- Findings: `Client.send_message` docstring says it aggregates updates — it doesn't (first
  task stays SUBMITTED, re-read with get_task); py client transport raises ParseError on
  unknown response fields (violates §5.7 SHOULD) while server and card resolver ignore them;
  v0.3 compat is one switch (`enable_v0_3_compat=True`), off → -32601; DatabaseTaskStore
  imports but needs the sql extra, a2a-db needs Alembic; telemetry decorators are on but
  record nothing without a provider. Part 5's "Task was destroyed but it is pending!" noise
  is SDK 1.2.2 dropping `EventQueueSource._dispatch_loop` when refusing a finished task.
- Region markers changed agent hashes → 23 stale captures re-run, contents byte-identical.
  `make all SKEL=1` green (679 slides, 654 blocks, 0 mismatches).

### Part 8 first half — 67 slides (2026-10-17)
- `08_ts.html` cover+intro (2), ch1 package map (11), ch2 types (15), ch3 executor (13),
  ch4 handler/store (13), ch5 serving (13), "N장 정리" left columns match part 7. Examples
  `ex/ts/08/` (23 files), specs `ex/run/08/{drive,serve}.run`; ports 10801–10815. No final
  agent excerpted, no region added. Builder rejects dangling anchors → intro names ch6–9
  as plain text (08b should turn them into links).
- Findings (paths under `node_modules/@a2a-js/sdk/dist`): 15 self-contained bundles, classes
  copied per bundle — A2AError keeps instanceof via Symbol.for brand (`errors/index.js:4`),
  a same-named class of ours maps to -32603; types are interfaces + fromJSON/toJSON only,
  no Task helpers, no TaskUpdater; structuredClone (RequestContext, InMemoryTaskStore.load)
  turns raw Buffer into Uint8Array while the type says Buffer; `Part.fromJSON` text wins
  over other content keys, `{data:null}` → content undefined, unknown enum → -1; follow-up
  message is already in `ctx.task.history` before execute (py: opposite); ordering checks
  only on streams (`_advanceStreamPattern`) — blocking SendMessage accepts two Messages,
  Message after Task (stored task stays SUBMITTED), Task with a different id; silent
  executor → immediate -32603 (py hangs); any throw in execute → FAILED Task, never an
  error code; store owner = `userName || "unknown"` (`server/index.js:308`) — a user named
  "unknown" shares anonymous tasks, no delete; card handler JSON.stringify's what it gets
  (handler-as-provider leaks `"tenant":""`); off-path → express HTML 404; missing
  A2A-Version → -32009 plus an "Unhandled error" stack on stderr; requestedExtensions
  filtered to card-declared ones (py passes all).
- Spec tension: stream ordering violation → -32004 (py -32006 InvalidAgentResponse fits
  §3.3.2 better); wrong HTTP Content-Type → -32005 (meant for part media types).
- `make all SKEL=1` green (744 slides, 736 blocks, 0 mismatches); --check ×4 green.

### Part 8 complete — 126 slides (2026-10-17)
- `08b_ts.html` ch6 client (18), ch7 lodging (13), ch8 tests (14), ch9 TS-only + wrap (14);
  08_ts intro/prose ch6–9 mentions turned into links. `agents/lodging.ts` got one
  `region: execute` around the whole class (builder's brace check rejects TS regions that
  split a method — old `executor`/`quote` regions remain, candidates for removal in review);
  85 TS captures re-run, contents byte-identical. Ports 10850–10866.
- Findings (`node_modules/@a2a-js/sdk/dist`): Client has sendMessage/sendMessageStream, no
  close, returns bare Task|Message (`client/index.js:5882`); stream falls back to
  SendMessage without card `streaming` (`:5480`); caller's A2A-Version in serviceParameters
  is overwritten with 1.0 (`:5657`), interceptor headers survive (`:5701`);
  `returnImmediately ??= polling` (py `|=`) and always a `configuration` object (`:5623`);
  card resolver returns raw JSON; only JSON-RPC error bodies become A2AError (`:1899`) —
  card fetch failure plain Error, ECONNREFUSED TypeError, HTML 404 Error(cause SyntaxError);
  TS client ignores unknown response fields (follows §5.7, py violates), unknown enum → -1;
  mid-stream error wrapped as Error("SSE event contained an error…", {cause}) (`:6094`) so
  instanceof fails; step-3 history bug shows at turn 2 in TS (handler stores the question
  immediately); lodging.ts runs serve at top level → tests need `mock.module` +
  `--experimental-test-module-mocks` (not allowed in NODE_OPTIONS); express.json({limit})
  before the router lifts 100 KB but turns bad JSON into HTML 400 instead of -32700;
  `createAuthenticatingFetchWithRetry` retries once on 401 (py/go have none); legacyCompat
  routes empty/0.3 A2A-Version to v0.3 (§3.6.2) but validateVersion (`server/express:2164`)
  also needs a 0.3 interface on the card, and a v1.0 SendMessage without the header then
  gets -32601; ESM+CJS builds, instanceof survives via Symbol.for brand; no OpenTelemetry;
  `deleteTaskPushNotificationConfig` skips the card pushNotifications check (not on a slide).
- `make all SKEL=1` green (802 slides, 805 blocks, 0 mismatches); manifest 144, 0 stale.

### Part 9 first half — 67 slides (2026-10-17)
- `09_go.html` cover+intro (2), ch1 package map (10), ch2 types (15), ch3 executor (14),
  ch4 handler/store (15), ch5 serving (11); summaries carry py/ts/go columns. Examples
  `ex/go/09/` (helper pkgs `sdksrc`, `steps`; 18 single + 4 norun), specs
  `ex/run/09/{drive,serve}.run`; ports 10901–10915. No final agent changed.
- Findings (a2a-go@v2.6.0): 33 packages (12 internal), only imported modules downloaded;
  `a2acompat/a2av0` pulls old module a2a-go v0.3.15; hand-written structs (proto only in
  `a2apb/v1`), string enums accept unknown values, no-omitempty fields emit `"parts":null`,
  `NewDataPart(nil)` writes `{"data":null}` that `Part.UnmarshalJSON` rejects
  (`a2a/core.go:694/717`); doc drift — UUIDv7 ids vs "UUIDv4" (`a2asrv/exectx.go:43`), the
  executor doc template doesn't compile (`agentexec.go:39,58`), `doc.go` names
  `task.WithTaskStore`/`WithCallInterceptor`; yield after false panics; incoming message
  appended before Execute, status message moved to history only on the next status update
  (`a2aevent/event.go:121`) → stored order m-1·m-2·q-1; ordering checked for blocking and
  streaming (`taskupdate.Manager`); silent executor hangs unless
  `WithAgentInactivityTimeout`; OtherId → -32603 leaking SDK-internal text; plain error →
  -32603 raw text, nothing stored; store keyed TaskID+owner, tenant ignored
  (`taskstore/inmemory.go:52`), anonymous ListTasks unauthenticated (`:192`), gob copies
  (struct in DataPart → "type not registered" → FAILED), task versions + 
  ErrConcurrentModification (Go only); **bug: `ToJSONRPCError` iterates a map
  (`internal/jsonrpc/jsonrpc.go:163`) → two wrapped sentinels give -32602 or -32001 at
  random** (REST mapping is a slice, stable); JSON-RPC handler ignores path, GET → HTTP 200
  -32600 (`a2asrv/jsonrpc.go:52`); no A2A-Version and text/plain both accepted (§3.6.1
  says empty = 0.3); requested extensions unfiltered (as py); no capability checks without
  `WithCapabilityChecks`; default slog to stderr. Three-SDK rogue-executor table on
  `p09-rh-cmp`.
- Open for 09b: builder brace-checks Go regions too — lodging `executor` (+2) / `quote`
  (−2) are unusable, a whole-Execute region is ~61 lines (> 45); needs a split of
  `Execute` into helpers (agent change, verify golden) or another excerpt plan.
- `make all SKEL=1` green (867 slides, 884 blocks, 0 mismatches); manifest 164, 0 stale.

### Part 9 complete — 127 slides; SDK trilogy done (2026-10-17)
- `09b_go.html` ch6 client (17), ch7 lodging (14), ch8 tests (15), ch9 Go-only (12) +
  `p09-sdk3` three-SDK table + `p09-wrap` → #p10. 09_go / 07b / 08b plain ch mentions
  linked. Ports 10950–10981.
- `agents/lodging/main.go` refactored behaviour-preserving: Execute = Begin → `hear` →
  `missingOf`/`ask` → `quote`; balanced regions executor/hear/ask/quote (old unbalanced ones
  gone). 81 Go captures re-run byte-identical, golden green. TS `lodging.ts` still has the
  old unbalanced executor/quote regions (unused) — tidy in review.
- ch8 tests the final agent (package main) with `go test -overlay` from `09/testdata/`;
  `run_tests` prints `go test -json` without timings.
- Findings (a2a-go@v2.6.0): **manual A2A-Version is duplicated** — SDK key mixed-case
  (`a2aclient/client.go:270`) vs lowercased caller key → both "0.3" and "1.0" sent;
  **comma-separated A2A-Extensions never split** (`a2asrv/extensions.go:64`, §9.2/§14.2.2;
  py splits), two header lines work; **executor panic → -32603 with a 21-line goroutine
  stack in the message** unless `WithExecutionPanicHandler`
  (`internal/taskexec/execution_handler.go:199`); doc drift `a2aclient/doc.go:22-55`,
  `factory.go:274`, `exectx.go:32` (appends, doc says overrides); default JSON-RPC
  http.Client Timeout 3 min also cuts SSE (`a2aclient/transport.go:26`); card resolver sends
  no A2A-Version/Accept, base URL with a path is used as the card URL (`resolver.go:127`),
  reads file:// (`:106`); client drops unknown fields, unknown enum stays a string, stream
  errors are plain *a2a.Error (errors.Is works, unlike TS); stream falls back to
  SendMessage without card streaming (`client.go:110`); server interceptors Before in
  order / After reversed, early result still runs After (`intercepted_handler.go:231`);
  `a2acompat/a2av0` = separate handlers + migration adapters (needs module v0.3.15, read
  from source only); possible bug, source only: `handleCancelWithConcurrentRun` shadows err
  (`internal/taskexec/local_manager.go:369`). Go lodging transcript/log byte-identical to TS.
- `make all SKEL=1` green (926 slides, 956 blocks, 0 mismatches); manifest 172, 0 stale.

### Part 10 first half — 54 slides; part 10 split into 10_/10b_ (2026-10-17)
- `deck/sections/10b_stream.html` + `order.txt` line added (placeholder). `10_stream.html`
  cover+intro (2), ch1 wire (15), ch2 catering ×3 (15), ch3 closing rules (22). Examples
  `ex/{py,ts,go}/10/` (events, closer ×3, closes, frames), specs
  `ex/run/10/{wire,ask,closes,frames}.run`; ports 11001–11032. Region markers only in
  catering ×3, `common.ts` (artifact), `common/begin.go` (artifact); 05b `p05-art-chunks`
  lines= → region=chunk. 171 captures re-run byte-identical.
- Findings: `whats-new-v1.md:458` says `taskStatusUpdate`, proto/§6.2/SDKs use
  `statusUpdate`; §3.1.2 Outputs still lists "Final completion indicator" though `final` is
  gone (no `reserved` in proto); v0.3 compat rebuilds `final` differently (py/ts terminal
  only — `compat/v0_3/conversions.py:404`, `server/express/index.js:2825`; go also
  INPUT_REQUIRED — `a2acompat/a2av0/conversions.go:487`); catering stream identical on all
  three servers (10 events, no final Task snapshot, false chunk flags omitted); wire diffs
  — py Content-Type has charset, Go writes `id: <uuid>` per event (`internal/sse/sse.go:77`),
  py CRLF vs ts/go LF, all chunked HTTP/1.1 keep-alive; all clients send Accept
  text/event-stream. Close criterion: py when the executor returns (`active_task.py:617`),
  ts on Message/terminal/INPUT_REQUIRED else bus end unless `keepBusAliveStates` (default
  both interrupted, `server/index.js:2720`), go on IsFinal = terminal or INPUT_REQUIRED
  (`internal/taskupdate/final.go:37`). Observed: AUTH_REQUIRED + return → py closes, ts/go
  stay open (contradicts §11.7); WORKING + return → py/ts close (py matches neither
  §3.1.2 pattern), go stays open; events after INPUT_REQUIRED → py delivers and stores,
  ts/go close and silently lose them; mid-stream exception → py `event: error` -32603, ts
  synthesized FAILED statusUpdate, go FAILED task snapshot (shape unspecified).
- Notes for later: py pings every 15 s (sse-starlette), Go keep-alive off, TS none; Go
  catering ignores yield results (latent panic after false); Go yield after INPUT_REQUIRED
  is racy (not printed), BOOM case uses a 0.3 s pause for determinism — watch in review.
- `make all SKEL=1` green (979 slides, 995 blocks, 0 mismatches); --check ×4 green.

### Part 10 complete — 113 slides (2026-10-17)
- `10b_stream.html` ch4 fold ×3 (14), ch5 SubscribeToTask (17), ch6 FilePart+DataPart (15),
  ch7 no-streaming card (12), `p10-wrap` → #p11; 10_stream ch4–7 mentions linked. Examples
  `ex/{py,ts,go}/10/` fold/resub/paused/nosub, specs `ex/run/10/{fold,resume,resub,paused,
  nostream}.run`; ports 11050–11077. No final agent changed.
- Findings: spec has no fold rule beyond proto comments, `append` to an unknown artifactId
  unspecified — py raises InvalidAgentResponseError (`server/tasks/task_manager.py:92`), ts
  adds a new artifact (`server/index.js:2411`), go errors (`a2aevent/event.go:95`); client
  fold helpers: py `append_artifact_to_task`, go `a2aevent.ApplyUpdate` (needs the client to
  `gob.Register(map[string]any{})` — only `taskstore/inmemory.go:60` registers it), ts none;
  §3.5.2 holds on all three (same events/order for two subscribers, task survives cuts);
  SubscribeToTask terminal → -32004, unknown → -32001 everywhere (ts prints state as number,
  go leaks "no active execution" `a2asrv/handler.go:375`, go errors as SSE, py/ts plain
  JSON); resubscribe to a paused task after executor return — py keeps all open
  (`default_request_handler_v2.py:569`), ts keeps interrupted open while bus alive, WORKING
  closes, go closes INPUT_REQUIRED, keeps AUTH_REQUIRED/WORKING (`handler.go:371,382`);
  no-streaming card: capability check precedes lookup (-32004); py client refuses locally
  (`client/base_client.py:322`), ts/go send it; **bug: Go client stream path ignores
  Content-Type (`a2aclient/jsonrpc.go:213`) and SSE parser skips non-`data:` lines
  (`internal/sse/sse.go:120`) → a JSON error from py/ts servers becomes an empty stream**;
  Go SSE line cap 10 MB (`sse.go:39`, source only); TS client method still `resubscribeTask`.
- Timing: `resub.run`/`resume.run` run catering with `--step-ms 3000` (1000 flaked ~1/7);
  `paused.run` uses 2 s socket timeouts like `closes.run`. Revisit in review.
- `make all SKEL=1` green (1037 slides, 1050 blocks, 0 mismatches); --check ×5 green.

### Part 11 first half — 63 slides; runner ready timeout 60 s (2026-10-18)
- `11b_push.html` + `order.txt` line added (placeholder). `11_push.html` cover+intro (2),
  ch1 bus ×3 (13), ch2 polling (13), ch3 push config (16), ch4 webhook receivers ×3 (19).
  Examples `ex/py/11/{poll,setup,relay,notify,hook_check}.py`, `ex/{ts,go}/11/{setup,
  hook_check}`, specs `ex/run/11/{bus,poll,setup,cfgerr,hooks,auth}.run`; ports
  11100–11149. Region markers only in bus ×3 (execute, cancel, main; go push existed) and
  webhook ×3 (summary, hook/server). 185 captures re-run byte-identical.
- Runner: `--check` failed 2 of 3 passes with "bus-py 가 15초 안에 준비되지 않았다" (swap;
  no content diff) → `READY_TIMEOUT` 15 → 60 with a test (commit 66f04f11).
- Findings: py stores an id-less push config under the task id and replaces same-id
  configs (`push_notification_config_store.py:19`, `inmemory_…_store.py:56`) → inline +
  id-less Create leaves one; ts randomUUID, go new UUID; inline config to a no-push agent —
  py/ts silently drop (`default_request_handler_v2.py:364`, `server/index.js:3084`), go
  -32003 with leaked "bug: …" text (`a2asrv/agentexec.go:174`); Create on unknown task
  -32001 everywhere; config created after the task misses the SUBMITTED push (all three);
  multi-config dispatch concurrent in py/ts, sequential map order in go
  (`agentexec.go:513`); Content-Type py/go `application/json`, ts `application/a2a+json`
  (§4.3.3); token header `X-A2A-Notification-Token` (Go SDK default
  `A2A-Notification-Token`, `push/sender.go:40`; spec names none); AuthenticationInfo — py
  sends token + Authorization, ts drops the token (`server/index.js:2665`); webhook 401 →
  task still COMPLETED, no retry; py/go push after store update and wait for the webhook
  (py before enqueuing to subscribers, `active_task.py:235`), ts fire-and-forget per-task
  chain; Go `HTTPPushSender` blocks private networks by default (`sender.go:60`),
  `FailOnError` → FAILED; client push defaults py `push_notification_config`, ts
  `pushNotificationConfig` only with a taskId key (`client/index.js:5632`), go
  `Config.PushConfig`; polling every 2 s = 7 GetTasks (3 wasted), 8 s misses 2 steps, TS
  GetTask repeats the status message in history, historyLength 0 halves bytes.
- Spec: §4.3.1/§3.1.7 name `PushNotificationConfig`, absent from v1.0.1 proto.
- **Defect in our final Go bus agent:** `hookSender` ignores `cfg.Auth` (violates §4.3.3
  MUST) and does not check the webhook status code → to be fixed in 11b ch8.
- Timing: poll.run 1 s margin (500 ms flaked once), setup 2 s steps, hooks/auth 1.5 s steps;
  push completion waits on relay `/wait` (event-based).
- `make all SKEL=1` green (1099 slides, 1124 blocks, 0 mismatches); --check ×5 green.

### Part 11 complete — 116 slides; Go bus push auth fixed (2026-10-18)
- `11b_push.html` ch5 config CRUD (13), ch6 CancelTask (10), ch7 ListTasks (13), ch8 webhook
  security (16), `p11-wrap` → #p12; 11_push ch5–8 links + defect prose (`p11-hook-auth`,
  `p11-hook-401`, `p11-ch4-sum`). Examples `ex/py/11/{crud,cancel_watch,listing,url_check,
  guarded}.py`, `ex/ts/11/{crud,listing}.ts`, `ex/go/11/{crud,listing,guard,hookold}`
  (hookold = verbatim old hookSender for the before slide), specs
  `ex/run/11/{crud,cancel,list,sec}.run`; ports 11150–11184.
- **Fix:** `agents/bus/main.go` hookSender sends `Authorization: <scheme> <credentials>`
  when AuthenticationInfo has both (§4.3.3 MUST; scheme as given, py SDK skips empty
  credentials too) and logs `WARN push rejected` on non-2xx. Only `out/11/auth.txt` changed
  (Go POSTs gain Authorization; 6 WARN lines). `auth.run` step 1500 → 3000 ms after a
  traceback/step-line swap flaked once (slides use grep-filtered server output only).
- Findings: Go Get on unknown push config → -32603 (`push.ErrPushConfigNotFound` plain
  errors.New, `a2asrv/push/store.go:30`; §3.1.8 wants TaskNotFound; py/ts -32001); Go client
  `ListTaskPushConfigs` drops nextPageToken (`a2aclient/client.go:181`); no server paginates
  config lists (MAY); Delete → `result: null`, second Delete no error; TS client
  `listTaskPushNotificationConfig` (no s); **TS sends the CANCELED push twice** (two
  `_processEvents` loops on one bus, `server/index.js:2833`/`:3227`); cancel during a
  subscription delivers CANCELED then closes on all three; py ListTasks serialises with
  `always_print_fields_with_no_presence` (`server/routes/common.py:39`) → extra empty
  fields; pageSize 0 → py/ts -32602, go default 50 (`inmemory.go:197`), 101 → py/ts -32602,
  go -32600; Go orders ListTasks by store write time (`inmemory.go:208`); TS
  `statusTimestampAfter` uses `>` (proto says >=, `server/index.js:3587`); page tokens are
  unsigned base64(timestamp,id); SSRF — py `push_url_validator` default None (validator
  resolves, fails closed, rejects loopback/private/metadata/IPv4-mapped), TS none, Go blocks
  at dial (`sender.go:97`) and drops the token on cross-host redirect (`:152`), Go
  Authorization only Bearer/Basic (`:175`), token header `A2A-Notification-Token` → our
  `X-A2A-Notification-Token` receivers 401 the correct token; wiretap HEADERS list lacks
  `A2A-Notification-Token` (`tools/wiretap.py`); spec defines no webhook signature/replay
  protection (only `topics/streaming-and-async.md` recommends JWT/HMAC/jti) — replayed POST
  accepted twice.
- Spec tension: §4.3.3 "Clients MUST validate the task ID" vs §13.2 SHOULD; retry MAY vs
  SHOULD (`p11-sec-duties`).
- Open: our Go hookSender has no SSRF guard and forwards custom headers on redirect (slide
  defers to part 17). Timing: crud.run 2 s steps; cancel.run event-synchronised; Go WARN
  after "완료" race held so far — revisit with hooks.run 1.5 s in review.
- `make all SKEL=1` green (1151 slides, 1177 blocks, 0 mismatches); --check ×3 green after
  the auth.run change; manifest 192, 0 stale.

### Part 12 first half — 62 slides (2026-10-18)
- `12b_security.html` + `order.txt` line added (placeholder). `12_security.html` cover+intro
  (2), ch1 transport security (13), ch2 securitySchemes/requirements (17), ch3 local OAuth2
  issuer ×3 (14), ch4 Bearer check ×3 (16). Examples `ex/{py,ts,go}/12/` (tls_card,
  card_parse, auth_and, token_rand, settle_client, …), specs `ex/run/12/{tls,card,issuer,
  bearer,cardonly}.run`, test TLS fixtures `ex/run/12/tls/` (127.0.0.1 cert, 100 years,
  CA key deleted — untrusted outside these captures); ports 11201–11241. No final agent
  changed. Forward refs to 5–8장 left as plain text (`p12-iss-clients`, `p12-cl-cmp`,
  `p12-bearer-where`, `p12-sch-wire`, `p12-sch-cmp`) for 12b to link.
- Our settlement agents ×3 — teaching shortcuts disclosed on slides (`p12-iss-rfc`,
  `p12-bearer-wire`), kept: missing grant_type → unsupported_grant_type (RFC 6749 §5.2 says
  invalid_request), no HTTP Basic client auth (§2.3.1 MUST), no `Cache-Control: no-store`
  (§5.1 MUST), `expires_in: 3600` never enforced, `error="invalid_token"` even for a Basic
  header (RFC 6750 §3.1 SHOULD NOT). **Real defect → fix in 12b ch5:** the Bearer check never
  verifies the card's required scope `payment:read` (only the executor checks
  `payment:approve`).
- Findings: §3.1.11/§13.3 say `AgentCard.security` and the §8.5 sample uses the v0.3 shape;
  proto v1.0.1 has `securityRequirements {schemes:{n:{list:[…]}}}`; AND/OR semantics stated
  in neither (Go doc `a2a/agent.go:176` "OR of ANDs"; `a2a/auth.go:39` example contradicts
  its comment); requirement parsing differs — py maps legacy `security`
  (`_map_legacy_security`) but drops unwrapped scope arrays (`card_resolver.py:27`), ts drops
  both, go accepts unwrapped (`a2a/auth.go:53`) and drops `security`, none errors; client
  AuthInterceptors attach at most one credential (py `client/auth/interceptor.py:63`, go
  `a2aclient/auth.go:94`) → AND never met; go sends Bearer for any http scheme, py only
  bearer; ts has no card-driven interceptor; ts resolver returns ts-proto only for
  proto-shaped security (`client/index.js:5338`), JSON.stringify leaks `$case` (closes the
  `p03-agent-card-ts` promise); **no server SDK enforces the card's security** (card-only
  server COMPLETED a token-less request); no SDK checks https or sets HSTS, all three
  clients reject an unknown CA; Go ErrUnauthenticated/ErrUnauthorized → -31401/-31403,
  REST 401/403; a 401 reaches every SDK client as a plain HTTP error, none exposes
  WWW-Authenticate; TS auth-retry fetch costs one extra 401; Go sends `Www-Authenticate`.
- `auth_and.go` capture uses the 200-try set trick (false failure ≈ 2^-199). One
  `test_wiretap ... test_upstream_down_gives_502` flake in `make all` (rerun green) — the
  port-timing flake noted in part 7.
- `make all SKEL=1` green (1212 slides, 1238 blocks, 0 mismatches); --check ×4 green.

### Part 12 complete — 119 slides; settlement scope check fixed (2026-10-18)
- `12b_security.html` ch5 scopes + fix (13), ch6 extended card (11), ch7 AUTH_REQUIRED (15),
  ch8 signed card (17), `p12-wrap` → #p13; 12_security forward refs linked and prose
  (`p12-iss-guess`, `p12-bearer-*`, `p12-ch4-sum`, `p12-sch-*`) updated for the fix.
  Examples `ex/py/12/{scope_try,bearer_old,xcard,approve,auth_watch,planner_at,impostor,
  jcs,verify}.py`, `ex/{ts,go}/12/{xcard,approve,verify}`, specs `ex/run/12/{scope,xcard,
  auth,chain,sign}.run`; ports 11250–11295.
- **Fix:** settlement ×3 — constant `NEEDED`/`needed = ["payment:read"]` feeds both the card's
  securityRequirements (card bytes unchanged) and the Bearer check; lacking it → 403
  `WWW-Authenticate: Bearer realm="settlement", error="insufficient_scope",
  scope="payment:read"` (region `scope`); executor's payment:approve check kept. Planner ×3
  now requests `"payment:read payment:approve"` for the approval token (otherwise the story's
  approval would 403). 0 existing captures changed. Before copy `ex/py/12/bearer_old.py`.
- `planner_at.py` (runpy wrapper so `--agents` fits a 72-col spec line) was shown on no
  slide → builder error without SKEL; now shown on `p12-ar-chain`. **Check `알림 0건`
  after every half — unused examples are errors in the final build.**
- Findings: AUTH_REQUIRED subscriber — py streams artifact+COMPLETED, go WORKING→artifact→
  COMPLETED, ts one Task snapshot then closes (bus closed), first stream closes at
  AUTH_REQUIRED everywhere; Go `GetExtendedAgentCard` doesn't replace the client's card
  (`a2aclient/client.go:209`), py does (`base_client.py:368`), ts via `getAgentCard()`
  (`client/index.js:5428`), ts has no dedicated method; extended card served unsigned
  everywhere, Go in struct order with `"pushNotifications": false`; no server SDK checks
  auth for it, TS static provider returns the *public* card to anonymous users
  (`server/index.js:2744`); hooks py `extended_card_modifier`, ts provider fn, go
  `WithExtendedAgentCardProducer`; py/ts/go produce byte-identical Ed25519 signatures; an
  unknown field still verifies in py/ts (parsed first), not in Go (raw bytes,
  `a2acrypto/canonical.go:31`); following a forged card's `jku` verifies everywhere, pinned
  keys reject; alg allow-list only in py; TS verifier console.debug's failures
  (`dist/index.js:1617`) and requires kid/typ/alg; Go KeyResolver docs say jku MUST NOT
  establish trust (`keyresolver.go:30`), resolver verifies only signed cards
  (`resolver.go:210`); only Go has auth error codes (-31401/-31403); proto comment calls
  AUTH_REQUIRED authentication, §7.6 uses it for authorization; §8.4.2 lists ES256/RS256
  only as examples (EdDSA kept per SCENARIO); §8.4.3 never says not to trust jku.
- Open: Go settlement `sign` comment claims SDK `NewSignedCardProducer` output is
  unverifiable by py/ts because of `"pushNotifications": false` — source suggests otherwise,
  not measured; `p12-sig-go` attributes it to the comment. Verify in review.
- Timing: `auth_watch.py` 3 s socket timeout (never fired), `chain.run` bus step 100 ms.
- `make all SKEL=1` green (1268 slides, 1292 blocks, 0 mismatches, 0 notices); --check ×4.

### Part 13 first half — 46 slides; part 13 split into 13_/13b_ (2026-10-18)
- `13b_binding.html` + `order.txt` line added (placeholder). `13_binding.html` cover+intro
  (2), ch1 equivalence + method table (13), ch2 HTTP+JSON ×3 (31). Examples
  `ex/py/13/{http_rules,rest_agent,rest_raw,rest_client}.py`, `ex/ts/13/{rest_common,
  rest_agent,rest_client}.ts` (registerHooks swaps `./common.ts` for agents/), `ex/go/13/
  {restmount,rest_lodging,rest_catering,rest_client}` (`agent.go` symlink to the final
  agent + `init()` that serves REST — input hashes still cover `ex/go/agents`), specs
  `ex/run/13/{same,rest,stream,matrix}.run`; ports 11301–11346. No final agent changed.
- Findings: **Go client can't read TS REST errors** — TS sends `application/a2a+json`, Go
  `FromRESTError` only parses `application/json` (`internal/rest/rest.go:277`) → generic
  ErrServerError; Go client treats any non-200 as error (`a2aclient/rest.go:131`) — TS 201/204
  on push-config create/delete should fail (source only); **Go server sends stream-start
  errors inside a 200 SSE** (`a2asrv/rest.go:277`) as `data: {"error":…}` without `event:
  error` → py client protobuf ParseError (`client/transports/http_helpers.py:151`), TS client
  silently ends with an empty event (`client/index.js:6400`); py/ts answer plain 4xx JSON;
  Content-Type py success a2a+json / errors application/json, ts a2a+json;charset both, go
  application/json always, no client sends a2a+json, TS sends Content-Type on bodiless GETs;
  malformed JSON → 400 INVALID_ARGUMENT with reasons py INVALID_REQUEST / ts INVALID_PARAMS /
  go PARSE_ERROR; unknown path → py 307 (`Mount('/{tenant}')` + redirect_slashes), ts express
  HTML 404, go text 404; tenant path accepted by py/ts though the card declares none, Go
  `NewRESTHandler` 404 (`// TODO: handle tenant`, `rest.go:50`, `NewTenantRESTHandler`
  separate); proto `additional_bindings` give all 11 rules a `/{tenant}` twin absent from
  §5.3/§11.3; REST error metadata py `{}`, ts none, go taskId+timestamp (closest to §11.6) but
  leaks its error chain; py REST logs `Request error:` to stderr.
- Spec: §11.1 SHOULD a2a+json (Go ignores it and its client breaks on it); no REST reasons
  for non-A2A errors (§5.4/§11.6); error shape inside a stream undefined (§11.7).
- Runner: one `--check` pass failed with "go 가 60초 안에 준비되지 않았다" on a prebuilt binary
  while swap was 13.3 GB; four isolated reruns ~5 s each, never a content diff. Watch it.
- `make all SKEL=1` green (1313 slides, 1346 blocks, 0 mismatches, 0 notices).

### Part 13 complete — 92 slides; gRPC deps added (2026-10-18)
- `13b_binding.html` ch3 gRPC ×3 (26), ch4 one server three bindings (12), ch5 spec skew (7),
  `p13-wrap` → #p14; 13_binding ch3–5 refs linked. Examples `ex/py/13/{grpc_*,doors,one_task,
  pick,rest_sub}.py`, `ex/ts/13/{grpc_common,bind_agent,grpc_client,doors_common,pick,
  rest_sub}.ts`, `ex/go/13/{grpcmount,grpc_lodging,grpc_catering,doors_lodging,grpc_client,
  pick,rest_sub}`, specs `ex/run/13/{grpc,gstream,gmatrix,doors,pick,verbs,gurl}.run`;
  ports 11350–11399. gRPC traffic shown by `13/grpc_tap.py` (gRPC relay decoding with
  a2a_pb2; drops grpc-js `date`) — the wiretap is HTTP/1.1 only.
- **Deps:** TS `@grpc/grpc-js` 1.14.5, `@bufbuild/protobuf` 2.16.0 (+32 lock packages); Go
  `google.golang.org/grpc` v1.83.2 direct + protobuf v1.36.11, genproto api/rpc
  v0.0.0-20260526163538-3dc84a4a5aaa, x/net v0.58.0, x/sys v0.47.0, x/text v0.41.0 indirect
  (go.sum +14, no `go mod tidy`). **Capture hashes don't cover go.mod/go.sum/package.json** —
  a full `--check --all` found 3 environment-snapshot captures changed truthfully
  (`out/08/sdk_exports.ts.txt`, `out/09/sdk_map.go.txt`, `out/09/test_tools.go.txt`):
  re-captured, prose fixed on `p09-map-deps` (title now "옛 v0.3 모듈은 우리 go.sum 에 없다",
  link to `p13-grpc-deps`) and `p08-map-pkg`. After any dependency change run the full check.
- The same full check exposed a race in **our** `ex/py/11/crud.py`: `arrivals` waited only
  for tok-2's end and then counted tok-1 (TS sends both concurrently → 5 vs 6). Now waits for
  one end per remaining config (`/wait?n=<List count>`); not on a slide; `crud.txt` gains the
  extra List exchange (appended after the cited `ex=5/6`); other part-11 captures re-run
  byte-identical.
- Findings: gRPC 3×3 consistent in all 9 cells (unlike REST's 3 broken pairs); A2A errors →
  FAILED_PRECONDITION / NOT_FOUND with ErrorInfo in trailers on all three (no ErrorInfo
  metadata); corrupt message → py UNKNOWN, ts/go INTERNAL; unknown method UNIMPLEMENTED;
  **version check differs** — TS rejects missing (read as 0.3) or 9.9 with
  VERSION_NOT_SUPPORTED, checked only against the card's GRPC interfaces
  (`server/grpc/index.js:952`), py GrpcHandler lacks `@validate_version` (REST/JSON-RPC have
  it, `rest_dispatcher.py:177`), Go never produces ErrVersionNotSupported (§3.6.2 MUST);
  activated extensions: TS header metadata (`:955`), Go trailer (`a2agrpc/v1/handler.go:313`),
  py none; gRPC opt-in py `grpc_channel_factory` (else ValueError, `client/transports/
  grpc.py:132`), TS `GrpcTransportFactory`, Go `WithGRPCTransport`; transport selection
  identical across SDKs (default JSONRPC, card order otherwise, py needs
  `use_client_preference`, `client.py:61`); **no client falls back** (§5.2 SHOULD) — Go
  `factory.go:154` skips only creation errors, `grpc.NewClient` is lazy; SubscribeToTask REST
  GET and POST accepted by all servers, PUT → py 404 text / ts 404 HTML / go 405, all
  clients POST (`rest.py:306`, `client/index.js:6378`, `a2aclient/rest.go:320`); gRPC URL
  must be `host:port` — `http://127.0.0.1:P` fails in all three clients although the proto
  comment and §8.5 sample use `https://…`; §10.2 metadata example says `a2a-version 0.3`.
- `make all SKEL=1` green (1358 slides, 1405 blocks, 0 mismatches, 0 notices); full
  `--check --all` (224) then re-checks green.

### Part 14 complete — 61 slides; Go build-cache bug fixed (2026-10-18)
- `14_ext.html` cover+intro (2), ch1 declaration/activation (12), ch2 budget extension ×3
  (22), ch3 versions (10), ch4 v0.3 coexistence (14), `p14-wrap` → #p15. Examples
  `ex/py/14/{budget_agent,budget_client,versions,old_agent,old_client}.py`,
  `ex/ts/14/{budget_agent,budget_common,budget_client,old_agent,old_common,old_client}.ts`,
  `ex/go/14/{budget,budget_lodging,budget_client,v03mount,old_lodging,old_client}`, specs
  `ex/run/14/{unknown,budget,required,clients,versions,old}.run`; ports 11401–11496.
- **Budget extension contract** (`https://treasure-house.example/a2a/ext/budget/v1`): card
  `capabilities.extensions` with `params {"currency":"KRW"}` (`--required` makes it
  required); client activates via `A2A-Extensions`, lists the URI in `message.extensions`,
  puts `metadata[URI] = {"limit": KRW}` on the message (§4.6.1); agent leaves the quote,
  adds `extensions:[URI]` + `metadata[URI] = {"limit","within"}` to the quote artifact; on
  without limit → -32602; required but not activated → -32008; echo `A2A-Extensions` where
  the SDK can; metadata without the header is ignored. Wrapper around the final lodging
  executors only — final agents unchanged. Part 15 can forward header+metadata in the
  planner; note Go `a2aext` propagator relays request `params.metadata`, not message
  metadata (topics/extensions.md also uses params.metadata) — decide in part 15.
- **Dep:** `github.com/a2aproject/a2a-go v0.3.15 // indirect` (go.sum +2). Full
  `--check --all`: `out/09/sdk_map.go.txt` (no ✗ left) and `out/09/test_tools.go.txt`
  changed truthfully → re-captured, prose on `p09-map-deps`, `p09-compat-go` updated.
- **Runner bug fixed (2f98d15c):** `_go_build` keyed the binary cache only on the example
  dir, so editing a sibling helper package (`13/restmount`, `14/budget`) reused a stale
  binary while the manifest said fresh. Key is now the whole `ex/go/NN`. Then `scratch/bin`
  cleared and full `--check --all` (230, 27 min) green — no committed capture came from a
  stale binary.
- Findings: py 1.2.2 server cannot report activated extensions (`ServerCallContext` only
  `requested_extensions`, `server/context.py:25`) nor check required ones — -32008 from the
  executor leaves a FAILED task + two tracebacks; TS checks required only in
  `_createRequestContext` (`server/index.js:2776`), echoes `addActivatedExtension` as a
  header (`server/express/index.js:3428`); Go with `WithCapabilityChecks` checks required on
  **every** method (`a2asrv/intercepted_handler.go:93`) → GetTask without header -32008
  (py/ts -32001); Go `Extensions.Activate` only read by gRPC handlers
  (`a2agrpc/v1/handler.go:314`) — JSON-RPC/REST never echo; `a2aext.NewActivator` only for
  card-declared extensions (`a2aext/activator.go:37`); TS executor throw → FAILED task, py/go
  -32602; py Struct shows `2000000.0`; budget 3×3 verdicts 9/9 identical. Versions: py any
  1.x (rejects 2.0, 0.3, empty), TS only exact "1.0", Go everything; JSON-RPC and REST same;
  `?A2A-Version=` read by none; REST version error 400 FAILED_PRECONDITION with supported
  versions only in the text. v0.3: TS `legacyAgentCardRouter` picks card shape by header,
  py/go always serve a mixed v1.0+v0.3 card; py dispatches by method name, TS by header, Go
  we split ourselves; v0.3 3×3 9/9 `message/send` with `A2A-Version: 0.3`; v0.3 extension
  header `X-A2A-Extensions` (`compat/v0_3/extension_headers.py:12`), not in the v1.0 docs.
- Spec: §14.2.1/§14.2.2 cite "Section 3.2.5" (service parameters are §3.2.6); response
  `A2A-Extensions` echo only in topics/extensions.md; data location §4.6.1 message.metadata
  vs topics params.metadata; §6.4 version-error example `application/problem+json`
  contradicts §11.6; topics lists "State Machine Extensions" but forbids new enum values;
  py "1.1" violates §3.6.2 Major.Minor, TS rejecting "1.0.1" violates §3.6 patch rule.
- `make all SKEL=1` green (1417 slides, 1468 blocks, 0 mismatches, 0 notices).

### Part 15 first third — 50 slides; part 15 split into 15_/15b_/15c_ (2026-10-18)
- `15b_scenario.html`, `15c_scenario.html` + `order.txt` lines added (placeholders).
  `15_scenario.html` cover+intro (2), ch1 planner design (15), ch2 registry/skill matching
  (17), ch3 concurrent delegation (16). Region markers only: planner py/ts (roles, say,
  parse, resume, finish), go (roles, say, parse, finish), `workshop/domain.py` (parse).
  Examples `ex/{py,ts,go}/15/parse`, `ex/py/15/{skills,gate}.py` (gate = barrier proxy that
  releases the three SendMessages in a fixed order), `ex/ts/15/planner_at.ts`,
  `ex/go/15/{planner_at,nilcard}`; specs `ex/run/15/{intake,missing,fan}.run`; ports
  11500–11532. Pre-existing captures byte-identical (3 ready-timeout flakes under swap
  re-ran identical).
- **Defects in our final planners (not yet fixed → next commit):** (1) TS planner builds
  `[...task.history, ctx.userMessage]` though begin()/the SDK already put the message in
  history → "…채식 2명…" without headcount proceeds with headcount 2 (py/go ask);
  (2) py `\d` matches full-width digits (`re` Unicode) → "３０명" = 30 in py, missing in
  ts/go (RE2 ASCII) — golden lacks the case; (3) no planner checks that all four roles were
  found — py -32603 `'settle'`, ts FAILED "Cannot read properties of undefined", go nil-card
  panic recovered by the SDK → FAILED without reason, or **process crash** when the panic
  is inside a `wg.Go` fan-out goroutine; (4) py planner streams -32603 containing the
  internal registry/card URL when a peer is unreachable. Also `p03-cache-clients` claims the
  part-15 planner uses conditional GET — it re-runs discovery every request, no cache.
- Findings: py SDK sends A2A-Version on the card GET via `create_client` but not via
  `A2ACardResolver`; ts sends it, go sends no headers; dead peer → py JSON-RPC error inside
  SSE, ts FAILED "fetch failed", go FAILED without message; planner sends its own contextId
  to the peers (§3.4.1 SHOULD NOT; all accept); fan-out DataPart is the whole parsed
  request; Go fans out with `sync.WaitGroup.Go` and waits for all, py gather / ts Promise.all
  fail fast and leave other delegations running; the final planner does not use the budget
  extension.
- Timing: `fan.run` has a deliberate 10 s gate timeout (lone request → 504); gate fixes the
  order by construction; Go planner stderr dropped in `missing.run` (goroutine ids vary),
  `--no-stream` there (streaming lost yielded WORKING updates).
- `make all SKEL=1` green (1467 slides, 1516 blocks, 0 mismatches, 0 notices).

### Planner defects fixed ×3; part 15 first third now 56 slides (2026-10-18)
- (1) TS planner reads `task.history` only (message no longer counted twice). (2) py
  `workshop/domain.py` regexes `re.ASCII`; golden case `fullwidth-digits` ("…３０명" →
  missing headcount) went RED in py only. (3) all three check discovery up front (region
  `lost`): missing role → `TASK_STATE_FAILED` "동료를 찾지 못했습니다: <역할>" before any
  delegation (FAILED not REJECTED: the same request can succeed once the planner side is
  fixed — `p15-fix-state`); Go fan-out moved to `fanOut` (region `fan`) with `recover()` in
  each `wg.Go`; py `gather(return_exceptions=True)`, ts `Promise.allSettled` — all wait for
  all three, first failure reported in fixed order. (4) unusable cards are skipped (URL only
  in the server log); delegation/token/settle failures → FAILED "<역할> 에이전트에게 맡기지
  못했습니다" (region `cannot`), no URL/exception text.
- Tests: `ex/py/15/test_planner.py`, `ex/ts/15/test_planner.ts` (+ `15/run_tests.ts`),
  `ex/go/15/plantest/` (+ `15/run_tests`), run by `ex/run/15/tests.run` (kept out of the
  agent dirs so 7–9 `used_names` captures don't change). Before-copies
  `ex/{py,ts}/15/planner_old.*`, `ex/go/15/old_at/` + `ex/run/15/before.run`; new
  `ex/run/15/down.run`, `ex/py/15/digits.py`; ports 11550–11569.
- Captures changed (intended): `out/15/{intake,missing,parse.py}.txt`, and
  `out/09/used_names.go.txt` (Go planner now uses `a2a.TaskStateFailed`, 81 → 82 names;
  `p09-map-used` title updated). `p03-cache-clients` corrected (no conditional GET, discovery
  every request). Slides +6 (`p15-twice-fixed`, `p15-reg-before`, `p15-fix-state`,
  `p15-fix-code`, `p15-fix-run`, `p15-fix-tests`).
- Not fixed: JS `\s` still matches U+3000 (only `출발\s*(\S+)`); planner still sends its own
  contextId and does not cancel sibling delegations on failure (on slides).
- Watch: `out/09/direct.go.txt` (returnImmediately) flipped SUBMITTED→COMPLETED once under
  swap; 3 isolated reruns identical — a latent race for review.
- `make all SKEL=1` green (1473 slides, 1543 blocks, 0 mismatches, 0 notices).

### Part 15 second third — 47 slides; six full meshes match §2.6 (2026-10-18)
- `15b_scenario.html` ch4 referenceTaskIds → settlement (19), ch5 planner progress
  streaming (12), ch6 full runs (16); 15_scenario ch4–6 linked (ch7 still plain text).
  Examples `ex/{py,ts,go}/15/refs`, `ex/py/15/check.py` (ListTasks COMPLETED +
  include_artifacts → compares the plan markdown and DataPart summary with golden, numbers by
  value), `planner_via` ×3 (planner_at + tap/card port); specs `ex/run/15/{mesh_py,mesh_ts,
  mesh_go,mix_py,mix_ts,mix_go}.run` — mixed meshes are a Latin square (every language plays
  every role once); all six runs: 2,100,000 / 1,542,000 / 1,200,000 / total 4,842,000 /
  remaining 1,158,000, summary 8/8 keys. **a2arun only accepts ports 11500–11599 for part 15**
  — the mixed meshes reuse 11580–11597 of the single meshes; 15c must reuse ports too.
- Findings: referenceTaskIds resolution is per server — TS looks them up in its own store and
  console.warn's "Reference task X not found." (`server/index.js:2803`), py needs a custom
  `SimpleRequestContextBuilder(should_populate_referred_tasks=True, task_store=…)` and drops
  misses silently (`simple_request_context_builder.py:63`), Go only via
  `ReferencedTasksLoader` + `WithExecutorContextInterceptor` (`a2asrv/exectx.go:78`); no SDK
  can resolve cross-server refs (§3.4.3 SHOULD vs server-generated ids §3.4.2); settle
  request wire — py `2100000.0`, Accept py `*/*` / ts `application/json` / go none, TS
  JSON-RPC `"id": 1` always, Go omits `configuration`; **py planner's follow-up stream starts
  with artifactUpdate (§3.1.2 Task-first violated; known py limitation in `common.py`
  begin)**; status messages into history: TS on arrival, Go on the next update; our agents
  close the stream at AUTH_REQUIRED (SDK defaults would hang `ask` on TS/Go); one story run
  = 14 HTTP requests (5 card GETs, 2 tokens, 5 SendMessage, 2 streams).
- Defects (not fixed): Go planner ignores `say`/`up.Status` bool in `plan`
  (`agents/planner/main.go:372`, latent, like part 10's Go catering); approval waits never
  cleaned up (py/ts `waiting` map forever, Go parked goroutine until ctx ends) and on a
  non-"승인" answer the AUTH_REQUIRED settlement task is never cancelled → 15c ch7.
- `make all SKEL=1` green (1519 slides, 1614 blocks, 0 mismatches, 0 notices).

### Part 15 complete — 133 slides; approval denial now cancels settlement (2026-10-18)
- `15c_scenario.html` ch7 failure paths (28) + `p15-defects` + `p15-wrap` → #p16; 15_/15b_ ch7
  mentions linked, line ranges re-pointed after the fix. Specs `ex/run/15/{fail_py,fail_ts,
  fail_go,deny_old}.run` (six sentences each, taps on lodging + settlement only),
  `ex/py/15/{cancel_bus,settle_left}.py`.
- Outcomes identical ×3: lodging rejected (2026-12-31, 70명) → `REJECTED 숙소: …` (siblings
  still finish — 70명 books a 45+25 bus that is never used); meals rejected (`채식 40명`)
  → `REJECTED 식사: …` (caps case unreachable via the parser → `p10-cat-reject`); over
  budget → `REJECTED 정산: 예산을 초과합니다 (842,000원)`, no AUTH_REQUIRED; approval denied
  → `REJECTED 결재가 반려되어 멈춥니다`; bus cancelled mid-run → `REJECTED 교통: 배차를
  취소했습니다`. Tables `p15-fail-cmp`, `p15-fail-map`.
- **Fix:** planner ×3 region `withdraw` — on denial get a `payment:read` token and CancelTask
  the settlement task before REJECTED (planner stays REJECTED per `p15-fix-state`;
  `p15-deny-state`), settlement ends CANCELED; wait state was already dropped. Tests RED→GREEN
  ×3 with a fake settlement server (Go via `common.Serve` on 11566, `waiter` unexported).
  Before/after: `deny_old.run` AUTH_REQUIRED 1 → CANCELED 1 everywhere. Captures changed:
  `out/15/tests.txt`, `out/07/used_names.py.txt` (+CancelTaskRequest, 37→38),
  `out/09/used_names.go.txt` (82→83) — counts updated on `p07-map-used`, 08_ts lead,
  `p09-map-used`. Everything else (incl. the six meshes) byte-identical.
- Findings: TS `cancelTask` without a live execution writes CANCELED itself with "Task
  cancellation requested by user." into history (`server/index.js:3225`); py runs the
  executor's cancel if active else writes CANCELED (`default_request_handler_v2.py:240`); Go
  cancels via the live queue (`internal/taskexec/local_manager.go:397`); CancelTask returns
  the Task as `result` (not `result.task`); §7.6.2 lets a client reject authorization by a
  message, our settlement executors treat any follow-up as an approval attempt.
- Open (not fixed): peer CANCELED → planner REJECTED with the peer text verbatim (by the
  book's rule FAILED; a peer SDK's English cancel text would leak); siblings keep running after
  a failure; Go `say` bool ignored; no timeout on approval waits; py `withdraw` creates an
  `httpx.AsyncClient` it never closes explicitly. Timing: `fail_*.run` canceller polls
  ListTasks every 0.05 s, assumes CancelTask lands within the second 2 s bus step.
- `make all SKEL=1` green (1548 slides, 1652 blocks, 0 mismatches, 0 notices).

### Part 16 first half — 42 slides; 45-cell matrix all pass; part 16 split into 16_/16b_ (2026-10-19)
- `16_interop.html`: cover + intro, ch1 3×3 matrix (24), ch2 wire differences (16). `16b_interop.html`
  placeholder (`p16-todo-b`, builder needs `^p16(-|$)`), added to order.txt.
- Specs `ex/run/16/` (ports 11600–11692): lodging/catering/push (taps, 9 clients), bus/cancel
  (no tap, polling count varies), `settle_{py,ts,go}` (token numbers per client language),
  `planner_{py,ts,go}` (single-language meshes, 3 `ask` runs), `raw.run` (curl, header casing).
  New example `16/cancel` ×3 (returnImmediately → poll WORKING → CancelTask → GetTask after 2.5 s).
- Matrix: 45 cells / 81 client runs pass; differences only along whole rows/columns — Go client
  keeps the public card and its verify rejects the card with an added unknown field (row); py
  planner server has no `task WORKING` after "승인" (column, `p15-say-second`). No agent fix.
- Wire findings (new): Go client sends `"taskId": ""` in inline push config (`a2a/push.go:71`,
  no omitempty); py ErrorInfo carries empty `"metadata": {}`, TS none, Go adds a timestamp;
  Accept `*/*` py / `application/json` ts / none go; Go card GET lacks A2A-Version (§3.6.1
  MUST); TS JSON-RPC id always `1`; Go SSE adds `id:` lines; Go history messages lack ids.
- Notes for 16b: do NOT add a subdirectory under `ex/run/16/` (every part-16 spec would go
  stale, ~6 min recheck) — inline JSON or another place. `p16-mx-same` cuts ask.py by
  `lines=28-47` (no region). Timestamp precision not capturable (normalised) → link only.
- `make all SKEL=1` green (1589 slides, 0 errors, 0 notices).

### Part 16 complete — 90 slides; agent int parsing fixed; official TCK run ×3 (2026-10-19)
- `16b_interop.html` (48): ch3 error table (32, `p16-ch3`…`p16-ch3-quiz`), ch4 conformance (16,
  `p16-ch4`…`p16-wrap` → part 17 in plain text). 16_ intro links ch3/ch4; `p16-wd-num-why` fixed
  (as_ints/asInts/common.Int truncate, not reject).
- Specs `ex/run/16/{errs,bench,borrow,rest_errs,tests,tck_py,tck_ts,tck_go,tck_why,tck_spec}`;
  ports filled in gaps 11606–08, 11616–18, 11633–38, 11667–69, 11676–79, 11686–89, 11693
  (a2arun rejects 11700+ for part 16). Bench agent and integer tests ×3.
- **Fix:** DataPart `{"headcount":"서른"}` → py -32603 leaking `int()` text, TS COMPLETED "NaN원",
  Go REJECTED. py `_int` (region `int`, common.py) and TS `asInts … || 0` now give 0 → business
  rule rejects, like Go. TS line count unchanged (part 3 `lines=271-277` still aligned). RED kept
  in `tests.run` via `16/ints_old.*`. All 227 stale captures re-run byte-identical.
- Error deviations: `[]` body py -32600 / ts,go -32602; TS -32602 for malformed requests
  (`server/express/index.js:1908`) and no params type check (§3.3.2 MUST); `"id": 5` TS -32001;
  `pageSize` 1000 Go -32600; executor exception TS → FAILED task; TS never sends -32006
  (`server/index.js:3114/:3481`); Go never sends -32009 (`a2a/errors.go:74` defined only); Go
  -32005 only from our executor; py -32008 from the part-14 wrapper; stream-request errors: Go
  200 + SSE event, py/ts JSON body (§9.4.2 silent). HTTP+JSON statuses per §5.4 except Go 9.9 → 404.
- TCK: a2a-tck 263b9cf (targets spec v1.0.0) in `scratch/tck/{src,venv}` — new `make tck`
  target pins it. Against part-13 three-door lodging: MUST/SHOULD/MAY failures py 4/1/1, ts 7/0/1,
  go 13/3/1. Causes: SUT script prefixes (`tck-*`), v1.0.0 vs v1.0.1 table (§5.4 gRPC/HTTP codes,
  `application/json`), real SDK gaps (Go `"tasks": null` core.go:870, Go SendMessage ignores
  historyLength handler.go:265, no ETag/Cache-Control Go, no Cache-Control py, version unchecked
  Go and py/go gRPC, Go subscribe unknown → 200 SSE). No agent bug from the TCK. Checklist slides
  map MUST clauses the TCK does not test (signing, auth, TLS, binding equivalence) to captures.
- Risk: py TCK has 3 skips depending on a 10 s subscribe timeout — stable twice, may flip under swap.
- New terms: TCK/적합성 시험, SUT 대본, 시험대 에이전트.
- `make all SKEL=1` green (1636 slides, 0 errors, 0 notices); manifest 276 examples, 0 stale.

### Part 17 first half — 38 slides; a2arun `restart` verb; part 17 split into 17_/17b_ (2026-10-19)
- `17_ops.html`: cover + intro, ch1 timeouts/retry/idempotency (21), ch2 file TaskStore (15).
  `17b_ops.html` placeholder `p17-todo-b`, in order.txt. Specs `ex/run/17/{defaults,resend,
  stream_to,retry,safe,store_py,store_ts,store_go,recover}` (ports 11701–11762, 11799 = dead
  port); 11763–11798 free for 17b. No subdirs under `ex/run/17/`.
- **Tool:** a2arun verb `restart name=N` (SIGKILL process group, same cmd, wait ready; one server
  header with a marker line) and a fresh `TMPDIR` per spec run (kept across restarts). RED→GREEN in
  `tools/tests/test_a2arun.py` (150 tests). Manifest showed nothing stale from the env change.
- Findings: default client timeouts py 5 s per read (httpx), TS none (per-call signal only), Go
  3 min whole call incl. body (`a2aclient/transport.go:26`) → the same 1.5 s cuts a 3 s stream
  on ts/go but not py. No SDK reads `Retry-After`. All three servers keep executing after the
  client gives up (py `active_task.py:548`, ts `index.js:2916`, go `local_manager.go:182`
  WithoutCancel) → resend with same messageId = 2 COMPLETED tasks everywhere (links p04-dup-*).
  Safe pattern: client-chosen contextId → ListTasks → SubscribeToTask (one task) ×3.
- Store: py save/get/list/delete (handler strips artifacts, `default_request_handler_v2.py:212`),
  ts save/load/list (store strips), go Create/Update/Get/List with version (`taskstore/api.go`).
  After SIGKILL+restart: finished tasks back with artifacts, push configs 1→0 (in-memory store),
  WORKING task orphaned forever; subscribe py silent / ts,go close; CancelTask works ×3 (TS
  writes English "Task cancellation requested by user."). `--recover` rule ×3: SUBMITTED/
  WORKING → FAILED at startup.
- Orchestrator edits: crash wording "넘어지다/넘어뜨리다" → "죽다/죽이다" (17_ops + 4 spec
  comments), "무작위 흔들기" → "지터" (slide + retry ×3 comments); terms added to AUTHORING's
  fixed list. Re-captured store/recover/defaults/resend/retry/safe/stream_to, `--check` green.
  One transient store_py run failure on first re-run (passed on retry + check) — watch for flake.
- Forward refs that could now become links (for the wrap-up): p06-store-what→#p17-ch2,
  06c:340 & 04b:363→#p17-ch1, 07_py:68/481·08_ts:497·09_go:513→#p17-st-prod,
  09b:584→#p17-st-go, 07b:550→#p17-st-py. 03b:410 (ETag/Cache-Control), 16b:507 (key
  rotation) belong to 17b ch4.
- `make all SKEL=1` green (1673 slides, 0 errors, 0 notices); manifest 285 examples, 0 stale.

### Part 17 complete — 69 slides; 20 forward refs to part 17 linked (2026-10-19)
- `17b_ops.html` (31): ch3 logging/tracing (15, `p17-ch3`…`p17-ch3-quiz`), ch4 deploy checklist
  (16, `p17-ch4`…`p17-wrap` → part 18 plain text). 17_ intro links ch3/ch4.
- Examples: py `17/{jsonlog,logged,follow,otel_grep,rotate,bus_ops,edge_check}.py` + test-only
  key `17/next-ed25519.pem`; ts `17/{jsonlog,logged}.ts`; go `17/{jsonlog,deploy,busops}`.
  Final agents untouched (py wrapped via runpy, ts by patching express, Go bus copied). Specs
  `ex/run/17/{trace,sdklog,edge}.run` (11763–65, 11770–74, 11780–84); first-half specs re-run
  byte-identical.
- Findings: py logs nothing per request at INFO; at DEBUG the request body
  (`jsonrpc_dispatcher.py:241`) and the call context incl. all headers (`active_task.py:517`,
  `routes/common.py:115`) → Bearer token in logs (§13.4 MUST NOT) — source only, not capturable.
  Go `NewLoggingInterceptor` (`a2asrv/logging.go:43`) request_id = fresh UUID, not the JSON-RPC
  id; task/context ids only as sent; `After` per stream event; JSON-RPC code mapping internal.
  TS no logger; card `cache.maxAge` default 3600. No SDK sends/reads `traceparent`; only py has
  OTel (`utils/telemetry.py`). py ETag excludes `signatures` (`agent_card_routes.py:40-59`) →
  bump card `version` on key rotation. Body limit 150 KB: TS 413 HTML; final py/go agents accept;
  Go MaxBytesReader on chunked → 200 + -32700 "unexpected EOF" (`a2asrv/jsonrpc.go:373`).
- **Open (not fixed):** py verifier catches only `PyJWTError` (`utils/signing.py:158`); a key
  provider raising `KeyError` on an unknown kid escapes — final py planner
  (`agents/planner.py:104`) and part 12 `verify.py` have it; surfaces once settlement signs
  only with a new key. Fixing touches agents → all captures stale. Decide at review.
- Not done: key rotation py only; Go traceparent propagator untested; Go final agents not
  wrappable (mesh uses copied Go bus).
- Links converted (20) in 03b/04b/06/06c/07/07b/08/09/09b/11b/16b; left plain: 06:445,
  06c:265, 06c:266 (no matching part-17 slide).
- `make all SKEL=1` green (1703 slides, 0 errors, 0 notices); manifest 290 examples, 0 stale.
- Next per §5: part 1, then 0, then 18; then wrap-up.

### Part 1 complete — 60 slides; 61 facts, 3 sources added (2026-10-19)
- `01_why.html`: cover + intro, ch1 problem (8), ch2 principles (11), ch3 MCP (8, sources only),
  ch4 history (11), ch5 v0.3→v1.0 (10), ch6 spec structure (8); `p01-wrap` → #p02. 22 cross-part
  `OUT` cites (parts 2–5, 10–16), 124 links (83 ids). No new examples.
- Sources `a2a-spec`, `a2a-what-is`, `a2a-and-mcp` (v1.0.1 raw); facts 74 total, data-check green.
- Inconsistencies (slides): v0.1.0/v0.2.0 GitHub dates back-filled (after v0.2.1); CHANGELOG
  1.0.1 = 2026-05-26 vs release 2026-05-28; spec header says "Latest Released Version 1.0.0";
  §1.4 path `spec/a2a.proto` (real: `specification/`); §1.4 MUST regenerate types vs Go
  hand-written `a2a` types; §2.2 role "user"/"agent" vs wire `ROLE_*`; Appendix A "≥0.5.0" with
  no 0.4/0.5; whats-new pagination `cursor/limit/nextCursor` vs proto `pageToken/pageSize/
  nextPageToken`, v0.3 `"taskStatusUpdate"` vs py compat `'status-update'`, push config
  `configId/createdAt` vs proto `id`; what-is-a2a expands MCP as "Multi-agent Control Platform
  (Model Context Protocol)" (verified in cached text) and uses `POST /sendMessage`.
- Orchestrator edits: "짝마다 통합" → "점대점 통합"; terms 불투명 실행, 점대점 통합, 기술 운영
  위원회(TSC) added to AUTHORING. Fact `v1-tsc` unused (duplicate of `v1-tsc-list`) — drop at
  review. `p01-mcp-here` links only `#p00` cover until part 0 exists.
- `make all SKEL=1` green (1761 slides, 0 errors, 0 notices).

### Part 0 complete — 42 slides; wiretap 502 log race fixed (2026-10-20)
- `00_start.html` (incl. deck cover `#top`): ch1 promises (`p00-no-llm`, `p00-versions` — protocol
  constants "1.0" ×3), ch2 scenario (feature tables link every feature), ch3 setup ×3
  (`p00-env-tsc` alias story), ch4 reading captures (`p00-norm` lists a2arun RULES: path,
  timestamp, `<ms>`, port ≥12000 (no capture triggers it), UUID `<idN>`; `p00-tap-sort`,
  `p00-marks`), ch5 guide; `p00-wrap` → #p01.
- Examples `00/versions` ×3; specs `ex/run/00/{env,tour}.run`. `env.run` is `sh:` only → manifest
  tracks only spec + fixtures; changes to package.json/requirements/toolchain are caught by
  `--check`, not by the manifest.
- Links converted (10): 01_why `p01-mcp-here` → `#p00-no-llm`; 04b, 06, 06b, 07, 10b, 16b → p00 ids.
- **Tool fix:** wiretap wrote the 502 log line after sending the response → `test_upstream_down_
  gives_502` flaky (2/9 runs: empty log / missing file). Log now written first; 8/8 OK. 113
  captures re-run (`--all --stale`) byte-identical.
- AUTHORING: "캡처 정규화" entry (distinct from JCS 정규화).
- `make all SKEL=1` green (1800 slides, 0 errors, 0 notices); manifest 295, 0 stale.

### Part 18 complete — 60 slides; all parts written, full `make all` green (2026-10-20)
- `18_appendix.html`: error tables (6), method tables (6, SDK client names ×3), field dictionary
  (18, generated), glossary (10), index (11), sources + quizzes (5), `p18-wrap` → #top, `p18-end`.
- New `tools/appendix.py` (24 tests): proto → `deck/fields.tsv` (44 messages, 2 enums, 176 fields,
  11 rpcs) and sections' `<code>` → `deck/index.tsv` (216 entries; vocab = proto names +
  `deck/index_extra.tsv`, first slide from `deck/proto_where.tsv`). `make deck` depends on
  `appendix`; `--check` fails if stale; without `docs/` the committed fields.tsv is kept.
- Builder directives `<!--FIELDS-->`, `<!--INDEX-->`, `<!--QUIZZES-->` (6 tests). Hand-written
  `deck/glossary.tsv` (105 terms, every `where` a real id) — orchestrator fixed 테넌트 to the
  proto's "opaque routing identifier". Field descriptions are the proto's English comments.
- `deck/check_deck.js` counted SDK-source `TODO:` quoted inside `<code>` on 13_binding as
  placeholders → inline code now excluded from the placeholder count.
- `make all` (no SKEL) green: 1857 slides, 0 placeholders, 1856 blocks 0 mismatches, 179 tests.
- Next: wrap-up (font is in make all; index.html card, README, history.md, commit deck HTML),
  then review 1 and 2.

### Wrap-up (step 6) — deck published in index/README (2026-10-20)
- `make all` (no SKEL) green; deck HTML committed for the first time (3.4 MB, font embedded).
- index.html card (🧠 AI & 머신러닝, after the transformer card) and README line: 19부(0~17+부록)
  1,857 slides, examples 490 files, captures 295, quizzes 123, glossary 105, facts 74.
- history.md rotated (20 oldest → archive, eee4b897) and back-filled with one entry per part
  commit of this session (16a…18) plus this wrap-up.
- Next: step 7 — review 1 (facts & evidence), review 2 (flow & style), `a2arun --check --all` ×2.
  Open decisions for review: py planner KeyError on unknown kid (part 17b), unused fact `v1-tsc`.

### Review 1 started — guide `deck/REVIEW.md`, 14 batches (2026-10-20)
- Batches (sequential, one reviewer at a time, commit per batch, log `scratch/review1-<X>-log.md`):
  A 0–2 · B 3–4 · C 5 · D 6 · E 7 · F 8 · G 9 · H 10 · I 11 · J 12 · K 13–14 · L 15 · M 16–17 · N 18.
- Batch A (0–2) done: 사실오류 5 · 증거불일치 1 · 근거없음 4 · 순서 5 · 표기 3 (+8 SRC links on part 2
  quotes; fact `v1-tsc` dropped, `rel-v0-2-1` added). For batch L: p15-reg-roles says the role
  table uses "둘째 태그" — tags put the role first and planner.py:128-130 matches any tag.
- Batch B (3~4부) done: 사실오류 3 · 절단 1 · 순서 1 (p03-iface-cmp TS/Go planners register HTTP+JSON too; p03-skill-five role tag first; p04-ctx-plan py/go check context before terminal, ts terminal first). Review 2: p04-part-wire '3장' vs p04-intro '(2장)'.
- Batch C (5부) done: 사실오류 3 · 증거불일치 3 · 근거없음 3 · 순서 2 · 절단 1 · 퀴즈 1 · 표기 1 (TS ClientConfig.polling; Go history now moved on next reply; ch9 quiz answer from capture). Review 2: spec §5.6.1 example uses createdAt/lastModified (add to p05-task-fields); p05-cancel-plan unverifiable authoring note '이 기계에서 한 번 어긋났습니다'.
- Batch D (6부) done: 순서 9 · 사실오류 2 · 증거불일치 2 · 절단 2 · 근거없음 1 · 표기 1 (source protojson added, 15 sources; wrong '17부' forward refs reworded). Review 2: p06-miss-params unverifiable authoring note; p06-check-py title '필수 넷' vs lead listing three.
- Batch E (7부) done: 사실오류 6 · 순서 6 · 증거불일치 4 · 근거없음 4 · 표기 1 (+ orchestrator: banned words '덤' 03b, '넘어지면' 16b). '공장' (banned) remains in 08b, 09b, 13, 13b, 14 incl. example comments and ts/08/client_api.ts output → batches F, G, K. Review 2: p07-store-copy advice about DB reads oddly; p07-test-red bullet incomplete.
- Batch F (8부) done: 표기 4 (공장→팩토리 11곳 incl. client_api.ts output) · 사실오류 2 · 증거불일치 2 · 순서 2. 29 captures re-run, only the one word changed. Any change to ex/ts/08 stales ex/run/09/strict.run. Review 2: p08-lg-final title 'filter 한 줄' vs three listed differences. Open: unused executor/quote regions in ex/ts/agents/lodging.ts (agent edit = all captures stale).
- Batch G (9부) done: 표기 9 (공장→팩토리) · 사실오류 5 · 순서 5 · 증거불일치 3 · 근거없음 3 (many file:line off by 1; '17부' refs qualified; 81→83 names). 28 part-9 captures re-run byte-identical.
- Batch H (10부) done: 순서 4 (+orchestrator p10-fold-last) · 표기 3 (넘어지다 → 죽다 incl. closer ×3 output) · 근거없음 2 · 증거불일치 1 · 사실오류 1 · 절단 1 · ×3 1. closes/paused/resub/resume --check 4/4, no flake. Review 2: p10-sub-exp anecdote; p10-cat-reject note '이벤트 둘' vs extra text line.
- Batch I (11부) done: 근거없음 8 (file:line off by 1, uncited Go claims) · 순서 3 · 증거불일치 2 · 퀴즈 2 · 사실오류 1 (Go sends no result key, not null). hooks/auth --check ×2, no flake. Review 2: p11-sec-fixed-run authoring note + title '셋이 같은 자리' vs TS differs.
- Batch J (12부) done: 근거없음 8 · 순서 5 · 사실오류 4 (unsigned cards: py/ts reject given a verifier, only Go passes; pinned provider KeyError) · 증거불일치 2. Sources rfc6749/6750/8037 added (18); SOURCES per=9 keeps 18부 at 60. Open (decide after review 1): py planner KeyError on unknown kid aborts the SDK signature loop before a valid 2nd signature — matters for key rotation (p17). Review 2: 머리/머리글/헤더 mixed; 가나다순/알파벳순.
- Batch K (13~14부) done: 근거없음 15 · 표기 11 (공장→팩토리 incl. 7 example comments, 19 captures re-run byte-identical) · 사실오류 9 (Go fails at first RPC not NewClient; Go picks newest version not card order; §3.2.6→§3.6.1) · 순서 8 · 증거불일치 3. Review 2: p14-ver-err header §5.4 vs ErrorInfo rule; p14-ver-rest py logs Task-not-found on passing requests too.
- Batch L (15부) done: 사실오류 5 (role tag is first, matched at any position — planner.py:128-130; optional bool in card-cmp) · 증거불일치 5 · 근거없음 4 · 순서 3 · 절단 1 (before.run 1-26). mesh_py re-run byte-identical. For 17부: py planner skips a card whose first signature has an unknown kid even if the 2nd is valid. Review 2: RED-run claims in p15-twice-fixed/fix-tests/deny-tests have no capture; p15-fail-cmp row 6 ambiguous.
- Batch M (16~17부) done: 사실오류 8 (optional bool false survives signing §8.4.1; TCK SUT generators incl. a2a-jakarta; §13.4 quote completed; card url §4.4.6) · 증거불일치 4 (restart shows ListTasks only) · 근거없음 3 · 순서 1 · 퀴즈 1. KeyError: part 17 scenario signs card(OLD, NEW) so it never triggers; only a new-first overlap card would be wrongly skipped (source-read, uncaptured). Decide: agent fix (all captures stale) vs a card(NEW, OLD) case in ex/py/17/rotate.py.
- Batch N (18부) done: 순서 15 (error-table first sightings, glossary where ids, OAuthFlow rows in proto_where → index 221, INDEX per=23 keeps 60 slides) · 사실오류 4 (TS names differ in 4 places; py 10 abstract methods) · 표기 4 (+orchestrator: last 공장 in ex/py/07/client_v03.py, 30 part-7 captures re-run byte-identical). REVIEW 1 COMPLETE (A–N). Open: py planner KeyError decision; 9 vocab names lack index entries (only inside longer code). Review 2 notes: 가로채기/인터셉터 mix, 머리/머리글/헤더 mix.

### Review 1 complete (A–N) — decisions for what follows (2026-10-20)
- Batch N (18부) committed c33ba8c5; review 1 finished for all 19 parts.
- User decisions: (1) py planner KeyError — do NOT change the agent; add a `card(NEW, OLD)` case to
  `ex/py/17/rotate.py` so the trap is shown by a capture (part 17 only). (2) Review 2 fixed terms:
  header → **머리글** (not 머리/헤더; code names unchanged), interceptor → **가로채기** (SDK class
  names like ClientCallInterceptor stay as code).
- KeyError case added (decision 1): `ex/py/17/rotate.py` ⑥ `card(NEW, OLD)` + KeyError provider → KeyError escapes on
  'settlement-2027'; ⑦ same card + PyJWKError provider → 맞음 (signing.py:158 catches only PyJWTError).
  p17-dp-key-trap/-run/-code now read the capture (lines 9-12). 13 other part-17 captures re-run byte-identical.
  Flake: `recover.run` twice gained an extra "[교통] 기사 배정" line (py step at 1000 ms beat the SIGKILL); 3rd run
  and two later `--check` passes identical — watch it under load.
- R2 batch A (0~2부) done: 용어 29 (21 헤더/머리→머리글, 2 가나다순→알파벳순, 5 이 덱→이 책) · 문체 28 · 링크·시제 16 · 흐름 12 (chsub order, table leads) · 중복 7 (re-taught 0부 capture rules → back-links) · 제목 4 · 콜아웃 4. 7 style decisions added to REVIEW2 §B. Example comment for the final sweep: ex/py/02/raw_http.py:19 헤더.
- R2 batch B (3~4부) done: 용어 30 (13 헤더→머리글, 16 장 as card/sheet counter) · 흐름 20 (17 table leads; p04-part-wire vs intro chapter fixed) · 문체 17 · 콜아웃 14 · 링크·시제 8 · 중복 3 · 제목 1. 5 style decisions added to REVIEW2 §B.
- R2 batch C (5부) done: 문체 33 (24 -음/-됨 table cells) · 링크·시제 16 · 콜아웃 8 · 흐름 6 (9장 label, 4 cmp leads) · 용어 4 (청크→조각) · 제목 2. §F: p05-task-fields createdAt/lastModified; p05-cancel-plan anecdote removed. Term decision: artifact chunk = 조각 (AUTHORING); 6b and 10 still have 청크.
