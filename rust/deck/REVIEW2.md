# Review 2 — reader flow and style

Review 1 checked every statement against its capture or source. Review 2 does **not**
re-check facts. It reads each part the way a learner does — front to back, on a phone —
and fixes what makes the reading stumble: order and connection, repetition, inconsistent
words, overloaded slides, uneven tone. You review and FIX. Working directory: `rust/`.

Read first: `deck/AUTHORING.md` (slide format, machine rules), `PLAN.md` §0, the
`deck/OUTLINE.md` rows of your parts and their neighbours, then this file to the end.

## A. Flow — check per chapter, in reading order
1. **Frame.** The part intro (`pNN-intro`) lists the chapters with the titles the chapter
   covers really have; each chapter cover's `chsub` names the chapter's topics in the order
   the slides come; nothing important in the chapter is missing from it.
2. **First slide of a chapter motivates** (what problem, why now) before showing syntax.
3. **Each slide connects to the one before.** A lead that says "앞에서 본", "같은 코드를",
   "이번에는" must have its antecedent on the previous slide or name/link the slide. An
   error slide is followed by its fix (same slide, next slide, or a link); if review 1
   added a backing slide in the middle of a sequence, check the sequence still reads in one
   breath and the neighbours' wording ("다음 슬라이드에서") is still right.
4. **Repetition inside the part.** The same point explained twice in different words →
   keep the better one, make the other a one-clause back-reference with a link.
5. **Overlap with earlier parts** (list in section D). The later slide must acknowledge the
   earlier one ("4부에서 본 대로 …" with a link to the slide) and be shorter, not re-teach
   from zero. Overlap with later parts: one clause pointing forward is enough.
6. **Load.** Review 1 added many reading notes; some slides are now too long. A slide
   should be one idea a reader can take in with one scroll: title, lead, one example, and
   normally at most two callouts or one callout plus a short list. If a slide carries more:
   first cut redundancy (a note that repeats the lead, a list item that repeats the output,
   two sentences that say the same thing), then merge related callouts. Never remove: the
   reading of an error message, a pointer to another part, a FACT/SRC/SINCE/REL directive,
   or a sentence review 1 added to explain an output line — tighten their wording instead.
   A slide that is nothing but a title and an example with no sentence gets one lead
   sentence. Do not split or merge slides unless there is no other way (at most ±2 per part;
   say so in the report; never exceed the part's limit in `deck/budget.txt` × 1.1).
7. **Chapter end.** The quiz asks about the chapter's main point, is answerable from the
   chapter, and no two quizzes in the part ask the same thing. The last content slide of
   the part leaves the reader with a summary or a "what next" (many parts have a table;
   if a part just stops, add two sentences to the last slide — not a new slide).
8. **Tables** have a caption or lead sentence saying what to read from them; column heads
   are parallel; cells are short phrases, not sentences.

## B. Style sheet (decisions for the whole book — apply, do not re-decide)
**Counting words.** 부 = part, 장 = chapter, 슬라이드 = one slide. Never "장" for a slide
("앞 슬라이드 / 다음 슬라이드 / 이 슬라이드"). A slide two or more away is linked by id with
its title as link text, not "두 장 앞".

**Tense of references.** Earlier part → "N부에서 봤습니다 / 본 대로"; later part →
"N부에서 봅니다"; link the text ("<a href="#p06">6부</a>"; a specific slide when the
reader benefits).

**Register.** Prose, callouts and full-sentence list items are 합니다체. Short noun-phrase
list items and table cells stay noun phrases ("없으면 기본값"). 한다체 full sentences are
allowed only inside example comments, `<ol class="steps">` rule lists and quoted rules
(e.g. the three ownership rules) — be consistent within one list.

**Fixed terms** (Korean — English; use exactly these; English in parentheses at first use
in each part, not again):
소유권 ownership · 빌림 borrowing · 참조 reference · 가변 참조 `&mut T` · 불변 참조 `&T`
("읽는 참조" only as a gloss in parentheses) · 수명 lifetime · 이동 move (verb: 옮겨 가다,
옮기다) · 복사 copy · 스코프 scope — **"범위" is reserved for ranges (`a..b`) and for the
range of values a type can hold; a value "스코프를 벗어나면" is dropped** · 정리 drop/cleanup
(verb 정리되다; `drop` in code font for the function/trait) · 식 expression · 문 statement
(never 문장) · 블록 block · 가리기 shadowing · 갈래 match arm · 가드 guard (pattern) ·
변형 variant · 패턴 pattern · 구조체 struct · 열거형 enum · 트레이트 trait · 트레이트 바운드
trait bound · 트레이트 객체 trait object · 제네릭 generic · 연관 타입 associated type ·
클로저 closure · 붙잡기 capture (closure) — **"캡처" means only the dark output box of this
book** · 반복자 iterator · 어댑터 adapter · 소비자 consumer · 슬라이스 slice · 크레이트 crate ·
모듈 module · 매크로 macro · 패닉 panic (verb 패닉하다; `panic!` in code font for the macro) ·
오류 error (never 에러) · 경고 warning · 메서드 method · 연관 함수 associated function ·
매개변수 parameter (in the definition) · 인자 argument (at the call) · 반환 타입 / 반환값
(nouns), 돌려주다 (verb) · 스레드 thread · 열쇠 lock guard (MutexGuard) · 낱말 word ·
글자 character in general, 문자 only for the `char` type · 견주다 compare (비교 only in fixed
nouns such as "비교 연산자") · 자리 capacity / memory place · 꼬리표 file label / enum tag ·
화면 what the dark box shows as a whole, 출력 what the program printed.

**Decisions added after the first review-2 pass (parts 0 and 2):**
- Table cells are noun phrases; when a cell must state a condition or a sentence it is a
  short 한다체 clause ("있어야 붙는다", "판마다 깨진다") — not 합니다체, not "-음/-됨".
- No "-세요" endings ("보세요", "의심하세요"): write a 합니다체 statement ("…부터 봅니다",
  "…를 먼저 의심합니다") or a noun-phrase callout head.
- A crate from outside the standard library is "바깥 크레이트" (not "외부 크레이트").
- "자리" may also mean a position in the source or on the screen ("패닉이 난 자리").
- 화면/출력: do not hunt for these. Fix only where the choice misleads (calling a compiler
  message "the program's output"); "출력" for the whole dark box is fine in titles.
- Reading notes are `.note` with the head "읽는 법". `.key` is for the one takeaway, not for
  how to read a message.
- When you add a sentence that says what a capture shows (review 1 did not see it), list
  it in your report under "new capture-reading sentences" so it can be double-checked.
- English gloss: once per part, on the slide that defines or first explains the term —
  not in the part intro's chapter list.
- A reference to something a specific slide teaches links to that slide, not to the part
  cover (`#pNN` stays for "the whole part"). Check the id exists with
  `grep -o 'id="pNN[^"]*"' deck/sections/NN*.html`. Part 3 targets other parts quote:
  p03-scope (스코프 — later parts say "스코프를 벗어나면"), p03-shadow, p03-immut/p03-mut,
  p03-overflow, p03-overflow-release, p03-nan, p03-nan-sort (실수 sort 오류, E0277),
  p03-static, p03-ch4 (형변환), p03-as-int, p03-int-methods (abs), p03-char, p03-tuple
  (튜플 풀기), p03-array-get (배열 인덱스 패닉), p03-ch5.
- A later error slide that repeats an error number or message seen earlier says so in one
  clause with a link ("2부에서 본 E0277 과 같은 꼴"), then reads only what is new.
- collection = "컬렉션" everywhere (part 8's title); "모음" only for vowels.
- `&T` is "불변 참조", `&mut T` "가변 참조"; the act is "불변 빌림 / 가변 빌림" (the
  compiler's immutable/mutable borrow). "읽는 참조/읽는 빌림" only as a gloss at the
  definition (p06-ref-no-write). "읽는 쪽 여럿 아니면 고치는 쪽 하나" is the book's phrase
  for the rule and stays.
- `clone()` is "복제(하다)" / "복제본"; "복사" is for `Copy` types and plain copying of
  bytes ("힙까지 복사" as a description is fine). Defined on p06-clone.
- destructuring = "풀어 헤치기" (glossed on p03-tuple and p07-pat-struct), not "구조 분해".
  refutable / irrefutable = "안 맞을 수 있는 패턴 / 반드시 맞는 패턴" (p07-refutable).
- index (noun) = "인덱스" (parts 6, 8; the trait is `Index`); "번호" / "N번 칸" stays as
  the plain word for a position; not "색인".
- "꼬리표" is not used for the compiler's span labels (say "N번 줄에 붙은 …").
- Line ranges: "3번부터 6번 줄까지", not "3~6번 줄".
- A sentence added about what a method does must be shown by the capture on that slide; if
  it rests only on documentation, either leave it out or report it so the example can be
  extended (p08-str-methods got a Korean `find` line for this reason).
- Part 8 targets other parts quote: p08-str-two (String vs &str), p08-str-format,
  p08-str-index (no s[0], E0277), p08-str-utf8 (len 은 바이트), p08-str-chars-bytes,
  p08-str-nth, p08-str-split, p08-str-parse (first `unwrap`), p08-str-compare,
  p08-vec-create, p08-vec-push-pop, p08-vec-index-get, p08-vec-iterate, p08-vec-capacity,
  p08-vec-bulk (retain/sort/dedup), p08-vec-strings, p08-map-basic (get → Option<&V>),
  p08-map-entry, p08-map-word-count (entry + 순서가 정해지지 않음), p08-map-moves-key,
  p08-map-float-key (Hash/Eq, E0277), p08-btreemap, p08-sets, p08-choose,
  p08-to-string-ways, p08-sort-strings (sort_by_key; full treatment p12-sorting), p08-cow,
  p08-grapheme, p08-str-cheat. collect chain: p02-args → p08-intro → p12-collect.
- Part 7 targets other parts quote: p07-struct-basic, p07-struct-debug (derive(Debug),
  `{:#?}`), p07-tuple-struct-mixup (newtype), p07-method-basic, p07-self-table (three
  receiver shapes), p07-assoc-fn (`new`, `Self`), p07-enum-data, p07-enum-missing-arm
  (E0004 on an enum), p07-option-enum ("null 대신 Option" — part 9 ch 2 builds on it and
  must not re-teach it), p07-ch4, p07-pat-struct, p07-pat-guard, p07-pat-slice,
  p07-pat-moved / p07-pat-ref / p07-pat-mut, p07-if-let, p07-let-else, p07-while-let,
  p07-matches, p07-let-chain, p07-refutable (E0005), p07-let-destructure,
  p07-param-pattern (the reader's first closure), p07-state-machine.
- Part 6 targets other parts quote: p06-drop-scope (정리/drop), p06-rules, p06-move-assign
  (first E0382), p06-move-fn, p06-clone, p06-borrow-rule (the rule), p06-nll-early (빌림은
  마지막으로 쓴 줄까지), p06-push-holding (push 와 참조; loop variant p06-iter-invalid),
  p06-char-boundary, p06-str-slice, p06-take-str / p06-take-slice (&str·&[T] 로 받기),
  p06-vec-move (E0507), p06-mem-take, p06-three-ways (보기·고치기·갖기), p06-stack-heap.
- "갈래" is a branch of `match` or of `if`/`else`.
- "범위를 넘다/벗어나다" for an index outside an array or slice is fine (a value range).
- Space between a closing Korean quote and a particle (`"…" 입니다` / `"…"입니다`): parts
  differ; not a defect, do not change either way.
- Link text for a slide two or more away may be a short phrase taken from its title; it
  need not be the whole title.
- "출력 N번째 줄" counts the lines of the dark box as shown, the `$ …` command line
  included. Prefer "출력 첫 줄/마지막 줄" or quoting the words when that is clearer.
- Part titles and scope come from deck/OUTLINE.md, not from the orchestrator's brief — if
  the brief disagrees with the outline, follow the outline and say so in the report.

**Line references.** Source lines: "N번 줄". Lines of a capture: "출력 N번째 줄" (or
"화면의 N번째 줄"). Columns are not cited.

**Spacing and punctuation** (book convention — keep, and fix deviations): a space between
code/Latin text and a following particle ("`mut` 를", "Rust 는", "5 를"); " — " (em dash
with spaces) for an aside or a callout head; "·" between parallel items; Korean double
quotes "…" for quoted words; no "~" for approximate, no ellipsis for drama.

**Titles.** `<h3>` states the point of the slide as a short sentence or noun phrase, not a
topic label ("대입하면 소유권이 옮겨 간다", not "이동"). Error slides end "— E0xxx". Titles
within a chapter should not all have the same shape, but sibling slides (before/after
pairs) should be visibly parallel.

**Callouts.** `.note` neutral explanation and "읽는 법"; `.tip` advice / how to fix;
`.warn` a trap; `.key` the one thing to remember — at most one `.key` per slide and not on
every slide. The head (`<b>…</b>`) is a short label, then " — ". Reading notes are headed
"읽는 법" (not "오류 읽는 법", "메시지 읽는 법").

**Tone.** Plain and calm. No "쉽게", "간단히", "그냥", "매우", "굉장히", "놀랍게도", rhetorical
questions in a row, or exclamation marks. Second person is implied, never "여러분은" more
than once per part. Sentences ≤ about 60 Korean characters where possible; split long
ones.

## C. What you must not change
- Slide ids; the number of slides (see A6); RUN/CODE/OUT/FACT/SRC/REL/SINCE directives
  (you may reword a `note=`); any number, version, date, error code, line number or quoted
  compiler text; the meaning of any sentence that states what a capture or source shows.
  If tightening a sentence would change what it claims, leave the claim and tighten around
  it. If you think a claim is wrong, do not fix it silently — report it.
- Examples: only Korean comments may change, and only for the style sheet (then format
  that file with `/data/data/com.termux/files/usr/bin/rustfmt --config-path
  ex/rustfmt.toml ex/NN/x.rs`, re-run `python3 tools/rsrun.py ex/NN/x.rs`, and re-check
  that every "N번 줄" on slides showing it still points at the same line — comments shown in
  a capture's source excerpt change the capture).
- Other parts, tools, data files. Report cross-part problems under "found but not fixed".

## D. Known overlaps between parts (the LATER part acknowledges the earlier)
세미콜론과 마지막 식: p04-block-semicolon → p05-tail-semicolon · match 기초: 4부 4장 → 7부
4장 · if let / let else: p01-let-else(역사) → 7부 5장 → p09-opt-iflet · Option: p07-option-enum
→ 9부 2장 · `{:?}` 와 Debug: p02-no-display, p02-debug → p07-struct-debug → p10-derive-debug ·
Drop 과 정리 순서: p06-drop-scope → p09-panic-unwind → p14-drop-order · 문자 경계: 6부 5장 →
8부 1장 · push 와 무효가 되는 참조: 6부 4장 → p08-vec-capacity · collect: p02-args → p08-intro
→ p12-collect · move 클로저: p12-capture-move → p15-move · 'static: 11부 5장 → p15-borrow-err ·
Rc: 14부 3장 → p15-rc-not-send · E0277 읽기: p02-no-display → … → p10-trait-not-impl ·
에디션: 1부 4장 → p02-edition-2015 · `?`: p01-question → 9부 3장 · const 제네릭:
p01-const-generics → p10-const-generic · NLL: p01-nll → 6부 4장.

## E. After fixing
`make deck SKEL=1` must show no ✗ and no `!` from your files; if you touched an example,
`python3 tools/rsrun.py --check ex/NN`. Machine rules as in AUTHORING.md: one command at a
time, foreground, no sub-agents, no `make all`, no `make fmt`, no git
commit/stash/checkout/reset.

## Report (English, short)
Counts by category — 흐름 (order/connection/frame), 중복 (repetition/overlap), 용어 (style-sheet
terms incl. 스코프/범위, 장/슬라이드, 캡처/붙잡기), 문체 (register, tone, long sentences,
spacing), 제목, 콜아웃, 분량 (overload/underload), 퀴즈, 링크·시제 — then one line per
non-trivial fix (`slide id — problem → what you did`; batch the trivial term replacements
as "N × 범위→스코프" etc.), then "found but not fixed" (including any claim you believe is
wrong, and any style-sheet decision you think is mistaken, with your reason).
