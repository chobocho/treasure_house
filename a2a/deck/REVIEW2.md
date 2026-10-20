# Review 2 guide — reader flow and style

Review 1 checked every statement against its capture, the spec and the SDK source. Review 2
does **not** re-check facts. It reads each part the way a learner does — front to back, on a
phone — and fixes what makes the reading stumble: order and connection, repetition,
inconsistent words, overloaded slides, uneven tone. You review and FIX. Working directory:
`a2a/`.

Read first: `deck/AUTHORING.md` (slide format, fixed terms, machine rules), `PLAN.md` §0, the
last section of `PLAN.md` ("Review 1 complete" and later entries), the `deck/OUTLINE.md` rows
of your parts and their neighbours, then this file to the end. Section F lists items earlier
reviewers left for your parts — handle every one.

## A. Flow — check per chapter, in reading order
1. **Frame.** The part intro (`pNN-intro`) lists the chapters with the titles the chapter
   covers really have; each chapter cover's `chsub` names the chapter's topics in the order
   the slides come; nothing important in the chapter is missing from it.
2. **First slide of a chapter motivates** (what problem in the workshop scenario, why now)
   before showing code or wire.
3. **Each slide connects to the one before.** A lead that says "앞에서 본", "같은 요청을",
   "이번에는" must have its antecedent on the previous slide or name/link the slide. If
   review 1 inserted a sentence or link in the middle of a sequence, check the sequence still
   reads in one breath and the neighbours' wording ("다음 슬라이드에서") is still right.
4. **×3 rhythm.** Concept → Python → TypeScript → Go → 세 언어 비교. A language slide that
   re-explains the concept is cut back to what is particular to that language; the
   comparison slide's lead says what to read from the table.
5. **Repetition inside the part.** The same point explained twice in different words →
   keep the better one, make the other a one-clause back-reference with a link.
6. **Overlap with earlier parts.** The later slide acknowledges the earlier one ("<a
   href="#p05-…">5부</a>에서 본 대로 …") and is shorter; it does not re-teach. Forward
   references: one clause, the part named in plain text or linked.
7. **Load.** Review 1 added many file:line cites and qualifying clauses; some slides are now
   too long. A slide should be one idea a reader takes in with one scroll: title, lead, one
   piece of evidence, normally at most two callouts or one callout plus a short list. If a
   slide carries more: first cut redundancy (a note that repeats the lead, a list item that
   repeats the capture, two sentences saying the same thing), then merge related callouts.
   Never remove: a reading of a wire field or error, a `file:line` cite, a § cite, a link to
   another part, a FACT/SRC directive, or a qualification review 1 added ("TS 만", "팩토리를
   거치면") — tighten the wording around it instead. Move a run of several file:line cites
   into one parenthesis at the end of the sentence if that reads better. Do not split or
   merge slides unless there is no other way (at most ±2 per part; say so; the part must
   stay within `deck/budget.txt` × 1.1).
8. **Chapter end.** The quiz asks about the chapter's main point; no two quizzes in the part
   ask the same thing. The part's last slide has the `.note` headed "다음".
9. **Tables** have a lead or caption saying what to read from them; column heads are
   parallel; cells are short phrases.

## B. Style sheet (decisions for the whole deck — apply, do not re-decide)
**Counting words.** 부 = part, 장 = chapter, 슬라이드 = one slide. Never "장" for a slide
("앞 슬라이드 / 다음 슬라이드 / 이 슬라이드"). A slide two or more away is linked by id with a
short phrase from its title as link text, not "두 장 앞", "위 출력", "아래 표".

**Tense of references.** Earlier part → "N부에서 봤습니다 / 본 대로"; later part → "N부에서
봅니다". A reference to what a specific slide shows links that slide, not the part cover
(`#pNN` is for "the whole part"). Check the id exists:
`grep -o 'id="pNN[^"]*"' deck/sections/NN*.html`.

**Register.** Prose, callouts and full-sentence list items are 합니다체. Table cells are
noun phrases, or a short 한다체 clause when a condition must be stated ("팩토리를 거치면
붙는다") — not 합니다체, not "-음/-됨". 한다체 full sentences only inside example comments,
`<ol class="steps">` and quoted rules. No "-세요" endings: write a 합니다체 statement.

**Fixed terms.** AUTHORING.md's list is binding. Decisions added for review 2 (user,
2026-10-20):
- header (HTTP, SSE, gRPC) → **머리글** ("HTTP 머리글", "응답 머리글", "`A2A-Version`
  머리글", "머리글 메타데이터"). Not 머리 / 헤더. The gRPC trailer stays **꼬리 메타데이터
  (trailer)** ("꼬리" alone where the pair 머리글·꼬리 is obvious). Header names and code stay
  as written (`A2A-Extensions`, `sendMetadata`). "머리말" (a callout's head label) is not a
  header — leave it.
- interceptor → **가로채기** (English once on the defining slide, `p07-cl-interceptor`);
  SDK type names (`ClientCallInterceptor`, `CallInterceptor`) stay in code font.
- factory → **팩토리** (`ClientFactory`, 라우트 팩토리). "공장" is banned (review 1 removed
  every one; a new one is a defect).
- order of Latin strings (JSON keys, names) → **알파벳순**; "가나다순" only for Korean words.
- crash → 죽다 / 죽이다 (never 넘어지다); no playful coinages ("덤", "칸막이", "거르개").

**Decisions added after batch A (parts 0–2):**
- "this book" is **이 책** (136 uses), not 이 덱; "덱 다루기" (the UI) stays. Remaining 이 덱
  are in 09b, 10b, 11, 11b, 13b, 16.
- A space between a closing Korean quote and its particle ("…" 를, "…" 는) — the deck's
  majority form; fix the forms without it.
- 장 only for chapters — also not as a counter for files or sheets ("명세 한 장" → "명세
  하나", "한 장 요약" → "요약").
- 머리 that is not a header stays: 머리줄 (heading lines in a capture, the top bar) and 머리
  for the top of a document ("specification.md 머리에는"). 머리 meaning the front part of
  something ("와이어의 머리") → 앞부분.
- Part-wrap slides (`pNN-wrap` / `pNN-next`) need no lead — the title is the caption.
- A comparison or table slide without a lead gets one sentence saying which row/column to
  read, using only what the table already shows.
- A callout head that is a full sentence → a 2–4 word label, the sentence after " — ".
- Term defects found in example comments or captures are listed in the report; the
  orchestrator fixes them in one sweep after review 2 (known: `ex/py/02/raw_http.py:19`
  "헤더 끝").

**Decisions added after batch B (parts 3–4):**
- 장 is never a counter for cards, documents or captures either ("카드 하나", "카드 여섯",
  "JSON 문서").
- "N장" as link text for a slide in the same part is fine when the target slide really is in
  chapter N (the in-part form of "N부"); two adjacent links with the same "N장" text → use
  title phrases.
- Callout head: at most about 4 words, no comma or dash; a short 한다체 clause ("카드 받기는
  성공한다") is a valid head.
- "이 기계에서는 …" next to a capture that shows the fact ("이 기계는 UTC 라") is a
  statement, not an anecdote — keep it.
- "~" in ranges (ports "10381~10383", "터미널 1~3", "0~17부") stays.

**Decisions added after batch C (part 5):**
- Table cells: "없음" is a noun and stays ("아티팩트 없음"); verb nominals (-음/-됨/-림/-김:
  실림, 옮김, 취소됨, 숨김) become 한다체 ("실린다") or a noun phrase.
- A parenthetical aside inside 합니다체 prose is 합니다체 too; 한다체 parentheticals only in
  table cells and directive `note=`.
- artifact chunk → **조각**; 청크 only for HTTP chunked transfer coding. Parts 6b and 10
  still have 청크 for artifact chunks (6b ×11, 10 ×9) — fix them in batches D and H.
- "첫머리" follows the 머리 rule: "첫 이벤트" or "앞부분" by meaning.
- A circled step label ("④⑥") may stay as quiz link text when the target slide is introduced
  by that label; in prose use a title phrase.

**Decisions added after batch D (part 6):**
- 해요체 endings (-니까요, -려고요, -게요, "…면요?") → 합니다체 ("… 때문입니다", "… 위해서입니다").
- Accept/reject grid cells: "받음" → "받는다"; prose quoting the cell is reworded to match.
- Generic byte/stream pieces (Node `data` pieces, decoder input) are 조각 too; 청크 only for
  HTTP chunked framing, titles included.
- A title count counts items of one kind ("취소 다섯 번" with a message among them is a
  defect → "취소 넷과 말 하나").
- Example-comment sweep list (orchestrator, after review 2) grows: `ex/py/06/rpc_probe.py:30-31`
  "판 헤더" (also in out/06/errors.txt and quoted on p06-ch2-quiz — change all three
  together), "판 헤더는 늘" in `ex/py/06/client.py:31`, `ex/ts/06/client.ts:27`,
  `ex/go/06/client/main.go:100`, `ex/py/06/frames.py:1` "머리와", `ex/py/06/stall.py:2` "요청의 머리".

**Decisions added after batch E (part 7):**
- "판 헤더" (`A2A-Version`) → "판 머리글" deck-wide.
- 머리 for the top of a source file ("모듈 머리에서 import") stays (like the top of a document).
- "-십시오" (보십시오) is the 합니다체 imperative and is allowed; use it sparingly — a statement
  ("…부터 봅니다") is preferred.
- Chapter "N장 정리" tables get a one-sentence lead (they are table slides); part-wrap slides
  don't.
- In-part link text "조금 뒤" / "앞에서" for a slide two or more away → a title phrase.
- A title naming one key difference while the lead lists several → "핵심 차이는 …" pattern.
  p07-lg-final uses "핵심 차이는 heard 를 고르는 한 줄이다"; its siblings p08-lg-final and the
  matching part-9 slide should be parallel. p07-intro/p07-wrap say the "정리" tables of parts
  8 and 9 share the same left column — batches F and G confirm or adjust.
- Sweep list adds: `ex/py/07/headers.py:22`, `ex/py/07/client_hooks.py:1-2,22,29`,
  `ex/run/07/serve.run:3`, `ex/run/07/client.run:2` (헤더/인터셉터), `ex/py/07/types_fields.py:1`
  "걸려 넘어지는" (stumble — optional).

**Decisions added after batch F (part 8):**
- Chapter-summary tables of parts 8 and 9 share part 7's left column, in part 7's row order;
  rows only that part has go at the bottom. Their lead is one sentence starting "왼쪽 열은
  <a href="#p07-chN-sum">7부</a>와 같고, …" (with extra rows: "위 N줄은 …, 아래 M줄은 …").
  Part 8 now holds this; batch G checks part 9 the same way (p08-wrap says so).
- Repeated "이 장" link text inside a "어디서" column (p07/p08-only-list) stays.
- "`// src/…` 머리 줄" (per-source comment in a bundle) falls under the 머리줄 exception.
- Sweep list adds: `ex/ts/08/client_hooks.ts:1-2,17,28,34,62`, `ex/ts/08/auth_retry.ts:1`,
  `ex/run/08/serve.run:3`, `ex/run/08/client.run:3`, `ex/ts/agents/planner.ts:174` (agent file —
  changing it stales every TS capture; leave unless the sweep re-runs all anyway).

**Decisions added after batch G (part 9):**
- Capture/file names as link text (types_build, rules) only in an "증거/근거" table column; in
  prose and quizzes use a title phrase. "이 장 끝" is positional like "조금 뒤".
- A "N장 정리" row may be filled by moving content out of another cell of the same table when
  a slide in the chapter backs it.
- "멈춤" (hang) in cells → "끝없이 기다린다"; "멈춤 막기" stays (part 7's left-column label).
  "같음" → "같다". "그냥 둔다" → "바로 둔다".
- JWS protected header → **보호 머리글** (12b has "보호 헤더" ×8 — batch J).
- Sweep list adds: `ex/run/09/serve.run:3`, `ex/run/09/client.run:3` (헤더); agent files
  (stale everything): `ex/go/agents/catering/main.go:4` 청크, `bus/main.go:126` "토큰 헤더",
  `webhook/main.go:4` 헤더, `settlement/main.go:262` "보호 헤더".

**Decisions added after batch H (part 10):**
- "N장 정리" tables in 물음/답 form (not part 7's left column) get the lead "물음마다 이 장의
  답을 한 줄로 줄였습니다", plus at most one clause naming the row where the SDKs differ.
- "닫힘" as a real noun ("닫힘이 신호다") stays; as a cell predicate ("…면 닫힘") → "닫힌다".
- Spelling: 싣다 → 실으면 / 실어 ("싣으면" is a defect).
- "(이 장 뒤쪽)" is positional → title-phrase link.
- A particle right after a closing parenthesis with Latin inside ("`Buffer.from(menu)`(UTF-8)를")
  needs no space — leave either form.
- Sweep list adds: `ex/run/10/ask.run:3` 머리 (shown via SPEC on p10-cat-spec); agent files
  `ex/py/agents/catering.py:4`, `ex/ts/agents/catering.ts:4` "청크로 이어 붙이기".

**Decisions added after batch I (part 11):**
- Go slice → **슬라이스** (never 조각). A page of a paginated result → **페이지**.
- Summary tables with SDK columns (neither 물음/답 nor part 7's left column) get the lead
  "세 서버가 같은 줄은 한 칸으로 합쳤습니다. 갈리는 것은 … 줄입니다."
- No space between ")" and 입니다 ("(§3.3.4)입니다") — majority form.
- Push sender (the component) → "보내기" (noun), not "보내는 것".
- "칸" for an owner-scoped partition of a store is a plain word and may stay (unlike the
  banned "칸막이"); the fixed term for the design remains 소유자별 저장소(분리).
- "세 SDK 서버" only where all three servers use the SDK for that thing — the Go webhook POST
  comes from our own `hookSender`, so there it is "세 서버".
- Sweep list adds: `ex/run/11/auth.run:1`, `ex/go/11/guard/main.go:2,41` (머리),
  `ex/go/11/hookold/main.go:23` (토큰 헤더); agent files `ex/py/agents/webhook.py:4`,
  `ex/ts/agents/webhook.ts:4` (헤더).

**Authoring notes.** Sentences that report what happened while the deck was being written
and that no capture shows ("이 기계에서 한 번 어긋났습니다", "고치기 전에는 시험이 이렇게
실패했습니다") are removed, or reworded into a statement the slide's capture or source does
show. Keep the lesson, drop the anecdote.

**Line references.** Source lines "N번 줄" or `file:line` in code font. Never count capture
lines ("셋째 줄") — quote the value or field (AUTHORING).

**Spacing and punctuation** (deck convention — keep, and fix deviations): a space between
code/Latin text and a following particle ("`tenant` 가", "Go 는", "404 를"); " — " (em
dash with spaces) for an aside or after a callout head; "·" between parallel items; Korean
double quotes "…" for quoted words; no "~" for "about", no ellipsis for drama. Ranges of
parts/sections with "~" ("0~17부") are fine.

**Titles.** `<h3>` states the point as a short sentence or noun phrase ("카드의 url 은 바깥에서
닿는 주소다"), not a topic label. A title must not promise a count the slide does not have
("필수 넷" with three listed). Sibling slides (py/ts/go) have visibly parallel titles.

**Callouts.** `.note` neutral explanation; `.tip` advice; `.warn` a trap; `.key` the one
thing to remember — at most one per slide, not on every slide. The head (`<b>…</b>`) is a
short label, then " — ".

**Tone.** Plain and calm. No "쉽게", "간단히", "그냥", "매우", "굉장히", "놀랍게도", rows of
rhetorical questions, or exclamation marks. Sentences ≤ about 60 Korean characters where
possible; split long ones (review 1's additions are the usual offenders).

## C. What you must not change
- Slide ids; the number of slides (see A7); RUN/CODE/OUT/SPEC/FACT/SRC directives and their
  `lines=`/`region=`/`wire=`/`ex=` (you may reword a `note=`); any number, version, date,
  §, error code, field/method/enum name, `file:line`, or quoted wire/SDK text; the meaning of
  any sentence that states what a capture, the spec or the source shows. If tightening would
  change a claim, leave the claim and tighten around it. If you think a claim is wrong, do
  not fix it silently — report it.
- Examples (`ex/`), captures (`out/`), tools, data files, glossary/index tsv: not in this
  review. A term defect inside an example comment or a capture → report it (re-running
  captures is the orchestrator's job).
- Other parts' section files. Report cross-part problems under "found but not fixed".

## D. After fixing
`make deck SKEL=1` must show no ✗ and no `!` from your files and your parts' slide counts
unchanged (unless you reported a ±). Then `grep -n '공장\|넘어지\|헤더\|인터셉터' deck/sections/NN*.html`
for your parts — each remaining hit must be code or a quoted name. Machine rules as in
AUTHORING.md: one command at a time, no sub-agents, no `make all`, no `make -j`, no git
commit/stash/checkout/reset. Log `scratch/review2-<batch>-log.md`, one line per finished
part; resume from it if it exists.

## E. Report (English, short)
Counts by category — 흐름 (order/connection/frame), 중복 (repetition/overlap), 용어
(style-sheet terms), 문체 (register, tone, long sentences, spacing), 제목, 콜아웃, 분량
(overload), 퀴즈, 링크·시제 — then one line per non-trivial fix (`slide id — problem → what
you did`; batch trivial replacements as "N × 헤더→머리글"), then "found but not fixed"
(claims you think are wrong, term defects in examples/captures, cross-part problems, and any
style-sheet decision you think is mistaken, with the reason).

## F. Items left by review 1 (handle in the batch that owns the slide)
- 4부: p04-part-wire says "3장" where p04-intro says "(2장)" — make them agree with the
  real chapter.
- 5부: p05-task-fields — mention that the spec's §5.6.1 example uses `createdAt` /
  `lastModified` (not on the wire of our servers); p05-cancel-plan authoring note "이 기계에서
  한 번 어긋났습니다" → remove per B.
- 6부: p06-miss-params authoring note → B; p06-check-py title "필수 넷" vs a lead listing
  three → fix the title.
- 7부: p07-store-copy — the advice about DB reads reads oddly, rewrite; p07-test-red — a
  bullet is incomplete; p07-cl-interceptor is the defining slide of 가로채기.
- 8부: p08-lg-final title "filter 한 줄" vs three listed differences → fix the title.
- 10부: p10-sub-exp anecdote → B; p10-cat-reject note "이벤트 둘" vs the extra text line.
- 11부: p11-sec-fixed-run authoring note → B; its title "셋이 같은 자리" while TS differs.
- 12부: 머리/머리글/헤더 and 가나다순/알파벳순 mixes (B).
- 13부: header terms (SSE "머리를 씁니다", gRPC 머리/꼬리) → B; "키를 … 가나다순" →
  알파벳순.
- 14부: p14-ver-err — table head "모양(§5.4)" while the JSON-RPC row's `reason` comes from
  the ErrorInfo rule (§10.6·§11.6): make the head not over-attribute (no new claim);
  p14-ver-rest — the py REST server also logs "Task not found" for requests that pass: one
  clause so the reader is not misled.
- 15부: p15-twice-fixed, p15-fix-tests, p15-deny-tests — how tests failed before the fix
  has no capture → B; p15-fail-cmp row 6 "교통 Task CANCELED + 글(취소하는 쪽이 받음)" is
  ambiguous (`cancel_bus` prints only the state; the text reached the planner) → reword;
  p15-exec-go "(9부)" links p09-cl-planner — link the slide on the executor's shape instead.
- 16부: p16-er-probe lead "네 자리" vs more fields in the title; p16-er-fix "그 밖의 꼴은 0"
  glosses over Go's `Int` also taking int and float64 — one clause; p16-tck-cmp py cell
  "건너뜀" while the capture says NOT TESTED and the head says non-FAIL cells are "—" — make
  the cell and the head agree; p16-ch3-sum says HTTP+JSON statuses matched §5.4 but the Go
  -32009 cell is 404 — qualify; "머리 / 날 머리" → B.
- 17부: p17-ch4 `chsub` leaves out the p17-dp-key-code topic (and the new new-key-first
  overlap case added after review 1).
- 18부: p18-op-map "다룬 곳" — CancelTask points to p11-ch6 though cancel is first taught in
  5부 6장 (link the first teaching, keep 11부 as a second link if useful); p18-err-other
  body-limit row — only TS returns 413 on its own, py/go only with the 17부 middleware;
  p18-err-where -32007 — the 3부 first sighting is the Go server with checks off, not
  "기능만 켜고"; glossary term 서비스 매개변수 is used on p13-eq-parts before its glossary
  slide p14-ext-bind (report only — glossary tsv is out of scope); glossary "필드 존재" is
  not used in prose (report only).

## G. Batches
Same grouping as review 1, one reviewer at a time, commit per batch:
A 0–2 · B 3–4 · C 5 · D 6 · E 7 · F 8 · G 9 · H 10 · I 11 · J 12 · K 13–14 · L 15 · M 16–17 · N 18.
