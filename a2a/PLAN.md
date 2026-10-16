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
