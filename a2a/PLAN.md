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
