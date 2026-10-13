# Authoring guide — how to write one part of the deck

You write **examples** (`ex/NN/*.rs`), run them (`tools/rsrun.py`), and write **slides**
(`deck/sections/NN_*.html`). You never touch the built deck, the tools, `deck/base/`, or
another part's files. Working directory for every command: `rust/`.

Read first: `PLAN.md` §0 (rules), `deck/OUTLINE.md` (your part's row and its neighbours),
`deck/sections/02_first.html` (the model chapter — copy its rhythm), and the component
catalogue in `../template.html` (slides `c-callout`, `c-table`, `c-flow`, `c-quiz`).

## The loop

```
1. write   ex/NN/name.rs                      (≤ 30 lines is ideal, hard limit 45; ≤ 72 columns)
2. format  rustfmt --config-path ex/rustfmt.toml ex/NN/name.rs   (only your own files —
           other writers have work in progress; rustfmt is /data/data/com.termux/files/usr/bin/rustfmt)
3. run     python3 tools/rsrun.py ex/NN/name.rs    → out/NN/name.txt, capture printed
4. slide   <!--RUN file=ex/NN/name.rs note=…-->    in deck/sections/NN_*.html
5. build   make deck SKEL=1                   read every "✗" line and fix it
```

Work chapter by chapter: examples for a chapter → run → slides → `make deck SKEL=1` →
next chapter. Do not write all examples first. If `rsrun` output surprises you, the
capture is right and your expectation was wrong — rewrite the prose, never the capture.

## Examples

- One idea per file. Names are short English snake_case (`move_fn.rs`), shown to the reader.
- Comments inside examples are Korean, short, and say *why* (not what). Identifiers English.
  The builder counts a Korean character as 2 columns (limit 72); rustfmt counts it as 1.
  Put a Korean comment on its own line when the code line is long.
- Output must be **deterministic**: no time, no random, no addresses (`{:p}`), no HashMap
  iteration order (sort or use BTreeMap), no racing threads. `rsrun --check` must pass twice.
- Must compile **without warnings** (prefix unused names with `_`), unless the warning is
  the lesson → add `//@ warnings: show`.
- Directives are trailing lines at the very end of the file:
  `//@ expect: E0382` (must fail to compile with that code; `expect: error` for syntax errors
  that carry no code) · `//@ exit: 101` (a panic is expected) · `//@ edition: 2021` ·
  `//@ flags: -O` · `//@ test` (compile with `--test`) · `//@ args: a b` ·
  `//@ stdin: 3\n4\n` · `//@ warnings: show` · `//@ norun`.
- A `//@ test` example with more than one `#[test]` must add `//@ args: --test-threads=1`:
  libtest runs tests on several threads and prints result lines in completion order, so the
  capture would differ between runs. rsrun refuses the example otherwise.
- An example that rustfmt cannot parse (deliberate syntax error) is listed in `ex/nofmt.txt`.
- Multi-file / cargo examples: a directory `ex/NN/name/` with a `RUN` file (one shell
  command per line: `cargo run -q`, `cargo test -q`, `rustc --edition 2024 main.rs`,
  `./main`; `#@ exit: 101` on the next line for an expected non-zero exit). Show its files
  with `<!--CODE file=ex/NN/name/src/main.rs-->` and its capture with
  `<!--OUT file=out/NN/name.txt-->`. Use only when the lesson is about files (part 13).
- std only. No external crates. No network. No `unsafe` outside part 16.
- Never guess what the compiler says. Error slides exist only for errors you have captured.
- Compile-error examples: keep them minimal so the diagnostic is short (aim ≤ 20 lines,
  ≤ 108 columns). Always follow with the fixed version (same slide if short, else the next).
- cargo output that depends on sizes or counts drifts between toolchains — use `-q`
  (`cargo clean -q`). `cargo new --vcs none`, `cargo fmt --check`, `cargo clippy` all work
  offline in the sandbox (see part 2 chapter 2).
- A slide whose `<h3>` ends with "— E0382" is picked up by the appendix error-code index, so
  put the code in the title of every slide that shows that error (and only those).
- Renamed or deleted an example? `python3 tools/rsrun.py --prune` removes the orphan capture.

## Slides

```html
<article class="card" id="p06-move-assign">
<h3>대입하면 소유권이 옮겨 간다</h3>
<p class="lead">왜 이것이 필요한지 한두 문장.</p>
<!--RUN file=ex/06/move_assign.rs note=s1 은 더 쓸 수 없다-->
<div class="key"><b>머리말</b> — 이 장에서 하나만 기억할 것.</div>
</article>
```

- `id` is required, unique, and starts with your part prefix `pNN-`. Part cover is
  `<article class="card section" id="pNN">`; second slide is `pNN-intro` ("이 부에서 할 일",
  a chapter list); each chapter opens with a cover card `pNN-chM` carrying
  `<p class="chnum">M장</p><h2>…</h2><p class="chsub">…</p>`.
- One slide = one idea = normally one `RUN`. Title `<h3>` states the point, not the topic
  ("대입하면 소유권이 옮겨 간다", not "이동"). Then: `p.lead` (why, 1–2 sentences) → `RUN` →
  one callout (`.note` neutral, `.tip` advice, `.warn` trap, `.key` the one thing) **or**
  a 2–3 item `<ul>`. Keep prose short; the example is the content.
- Error slides: title ends with the code ("— E0382"); the callout teaches how to read
  *this* message (which line, what the `help:` says).
- Use `<!--CODE file=… lines=A-B-->` / `<!--OUT file=out/… lines=A-B-->` to show a part of
  a long file or capture; otherwise `RUN`.
- No hand-written `<pre>` — the builder rejects it. For a memory picture use
  `<pre class="fig">…</pre>` (ASCII only inside it besides Korean labels, ≤ 72 columns,
  no Rust code). Prefer `.flow` boxes or a table when they do the job.
- Tables: `<div class="tblwrap"><table class="kv">…</table></div>`. Inline code:
  `<code>…</code>`; escape `<`, `>`, `&` (`&lt;` `&gt;` `&amp;`) — `Vec&lt;T&gt;`, `&amp;str`.
- End every chapter with one quiz slide (template `c-quiz` markup: `class="card quiz"`,
  `data-quiz`, `.q`, `<button>답 보기</button>`, `.a`). Quiz answers must be backed by an
  example you ran (in this chapter).
- Links: inside your part, any id. To other parts, only the part cover `#pNN`.
  (Superseded once the whole book existed: REVIEW2.md asks for slide-level links.)
- Version claims ("1.65 부터"): do not type a version from memory. Find the line in
  `docs/releases.txt` (`grep -n -i 'let.else' docs/releases.txt`, then look up which
  `Version` heading it is under), add a row to `data/features.tsv`
  (`key<TAB>version<TAB>label<TAB>regex-that-matches-that-line`), run `make data-check`,
  and write `<!--SINCE key=…-->` next to the title. If you cannot find evidence, make no
  version claim.
- Korean 합니다체, plain words, no hype. English term in parentheses on first use:
  "빌림(borrowing)". Glossary of fixed translations: ownership 소유권, borrow 빌림,
  reference 참조, lifetime 수명, move 이동, trait 트레이트, struct 구조체, enum 열거형,
  pattern 패턴, closure 클로저, iterator 반복자, slice 슬라이스, crate 크레이트,
  module 모듈, macro 매크로, panic 패닉, generic 제네릭, smart pointer 스마트 포인터,
  mutable 가변, immutable 불변, shadowing 가리기, expression 식, statement 문,
  trait object 트레이트 객체, thread 스레드, variant 변형.

## Done means

- `make fmt-check run-check` clean; `python3 tools/rsrun.py --check ex/NN` passes.
- `make deck SKEL=1` shows no `✗` from your files and your part's count is within ±10 %
  of its budget (`deck/budget.txt`).
- Your final message (English, short): files written, slide count, number of examples,
  every E-code shown (code → slide id), version badges added, anything you could not do
  and why. Do not commit — the orchestrator reviews and commits.

## Machine rules (the session dies if you ignore these)

Memory is nearly exhausted on this device. Run **one** command at a time, never in the
background, never in parallel, no sub-agents, no `cargo` unless the part needs it, no
`make all` (the orchestrator runs it), no `make -j`. Do not read whole large files
(`docs/releases.txt` is 930 KB — grep it). Do not read the built deck HTML.

## Expansion (parts 17–26) — what is different from the first edition

Read `deck/OUTLINE.md` → "Expansion" for your part's contract, then the style sheet in
`deck/REVIEW2.md` (section B and the "Decisions added …" block). The first edition was
written before that sheet existed and needed ~1,570 fixes; you write to it from the start.

1. **The reader has read parts 0–16.** Nothing in them is re-taught. When you use
   something they teach, acknowledge it in one clause with a SLIDE-level link
   (`<a href="#p09-res-question">9부</a>에서 본 <code>?</code>`) and say only what is new.
   REVIEW2.md lists the stable target ids per part; list others with
   `grep -o 'id="pNN[^"]*"' deck/sections/NN*.html`.
2. **Links.** Slide-level to parts that exist in `deck/order.txt`. A part that is still
   commented out there does not exist yet: mention it in plain text ("24부에서 봅니다"),
   no link — the orchestrator links it later. Never link a commented-out part.
3. **Terms** come from REVIEW2.md (스코프, 불변/가변 참조·빌림, 복제, 붙잡기, 풀어 헤치기,
   인덱스, 컬렉션, 되감기, 트레이트 바운드, 스코프 스레드 …). A new term gets its English
   gloss once, on the slide that defines it, and a row in your report under "new terms"
   (the orchestrator adds glossary rows — do not edit `deck/glossary.tsv`).
4. **Reading a capture.** Error slides carry a `.note` headed "읽는 법" that reads the
   message (headline = "오류 첫 줄", labels by source line "N번 줄"). Never count output
   lines ("둘째 줄") — quote the value or cite the source line that printed it. A repeated
   error number is read in full only the first time in the BOOK; later: one clause + link.
5. **Evidence.** Every sentence about what code does is shown by the capture on that
   slide (or links the slide whose capture shows it). No speed claims, no "most common",
   no comparisons with other languages. If the natural sentence needs evidence the
   example lacks, extend the example.
6. **Determinism (parts 17, 18, 20, 22, 23 especially).** A capture must be byte-identical
   on every run: sort `read_dir` results and map keys; never print time, addresses,
   thread ids, absolute paths, random hasher output or anything from racing threads;
   join threads in a fixed order. Run each such example at least 5 times
   (`python3 tools/rsrun.py --check ex/NN/x.rs` after the first run) before you trust it.
   Examples run in a fresh sandbox directory, so creating files in the current directory
   is safe; a directory example (`ex/NN/name/` + `RUN`) may ship input files and use
   shell commands (`cat`, `ls`, `printf … |`) in `RUN`.
7. **Structure.** Part cover `chsub`, chapter covers' `chsub` (topics in slide order),
   `pNN-intro` with the chapter list, a quiz per chapter (`data-quiz`), a table that
   closes a catalogue chapter (with a sentence saying how to read it), and a last slide
   whose `.note` headed "다음" hands over to the next part.
8. **Version badges.** A feature newer than 1.0 that the slide is about gets
   `<!--SINCE key=…-->`; the key must exist in `data/features.tsv` (see PLAN.md §3 for
   how a row is checked against the cached release notes). If you need a new key, do not
   guess the version: report it and write the slide without the badge.
9. **Budget.** `deck/budget.txt` has your part's target; the builder fails above +10 %.
   Aim for the target; under 80 % is a warning.
10. **Machine.** One `rustc`/`cargo` at a time (rsrun takes a lock — never bypass it,
    never run `cargo` directly outside rsrun), `rustfmt` only on your own files, no
    `make fmt`, no `git stash/checkout/reset`, do not commit.

### Lessons from the review of part 17 (apply from part 18 on)
11. Do not generalise from one example ("X 의 메서드는 …", "항상 …"). Say what the lines
    shown do. Both factual errors in part 17 were generalisations the same chapter
    contradicted a few slides later.
12. A "because" needs its own evidence. A mechanism attached to a correct observation
    (why append lands at the end, why drop cannot report, what the buffer does) is either
    shown (typed `let` bindings, a counter, a twin run) or attributed to the std
    documentation in so many words, saying what the screen does and does not show.
13. "X 가 없으면 …" needs a twin: write the variant and show its capture on the same
    slide with an OUT directive.
14. Exercise every branch that prints a message with a RUN invocation or a test. If a
    branch cannot be triggered deterministically, say so on the slide.
15. Pipes and two processes: decide by mechanism who writes last. When the order would
    depend on the other tool, send the program's stderr to a file (`2> err.txt`) and
    `cat` it afterwards. `/dev/full` is not usable in this sandbox; the machine runs as
    root, so permission errors cannot be produced.
16. Statements about the shell, the OS or the terminal are worded "이 기계에서는 … /
    셸이 …" and never name other systems.
17. At most two callouts per slide. A third is usually a source-line gloss or a key
    repeating the title — fold it into the reading note.
18. "앞 슬라이드 / 다음 슬라이드" only for the adjacent slide; anything further away is
    an id link, forward references included.
19. The part intro's description of how the part's screens work is a factual claim about
    every example: write it last and check it against all of them.

### Lessons from the review of part 18 (apply from part 19 on)
20. A title is a claim too. A generalising `<h3>` ("같은 값이면 해시도 같다") gets
    contradicted by the next slide. Lesson 11 applies to titles and to example comments.
21. Do not rely on evaluation order inside one `println!` (a mutating call as a positional
    argument next to an inline-captured `{name}`). Bind the result with `let` first.
22. A quiz answer's last step ("then add `?`") needs a capture like any other sentence; so
    does "이 모양이면 … 할 수 있습니다".
23. Every `match` arm that prints must run — helper functions included. Call the helper
    both ways rather than leave a dead arm.
24. No negative claims about documentation ("문서에 약속이 없어서"): they cannot be checked.
    Say what the example does ("순서에 기대지 않으려고 정렬했다").
25. "N번부터 M번 줄까지는 X 를 했다": check that every line in the range does X.
26. A link target must teach the linked word itself, not a neighbour (`mem::replace` is on
    p06-mem-swap, not p06-mem-take). Grep the target slide for the word before linking.
27. A word with two senses in one part (정렬: sort / alignment) is disambiguated at the
    definition and avoided in the intro and `chsub`.
28. Machine-dependent `true` lines (clock, environment, installed programs): name every
    such line on the slide, not only the obvious one.

### Lessons from the review of part 19, first half (apply from part 20 on)
29. Strict twins only. A variant file ("쌍둥이 파일") is made by COPYING the shown file and
    changing only the lines the slide names; `diff` the two before writing the note. Six
    twins in part 19 were separately written shorter programs, so every "N번 줄" in their
    notes pointed at numbering the shown source did not have.
30. Direction words for boxes: "둘째 화면" / "위 화면", never "아래 화면" for a box that
    sits above the sentence.
31. If the builder forces "— E0xxx" into a title because a twin's error headline is in the
    shown range, and the slide's point is not that error, the slide carries two ideas:
    split it or move the twin.
32. No "only" / "last" claims about a partly shown capture ("마지막 note:", "…고만
    적습니다") when the cut hides more; do not end a slice on a `note:` header whose
    snippet is cut off.
33. No forward use by idiom inside the part: a construct a later chapter of the same part
    teaches (a function path as a value, say) is not used casually in an earlier chapter.
34. No untested alternatives ("…하는 길도 있는데 돌려 보지 않았다"): run it or leave it out.
35. A compiler-source path (`/rustc/<hash>/library/…:line`) inside a shown range gets one
    clause saying what it is (this toolchain's std source) — it is not something to cite.

### Lessons from the review of part 19, second half (apply from part 20 on)
36. When acknowledging a repeated E-number, link the slide whose capture has the SAME
    headline (grep the earlier capture), and do not call a `note:` "new" that an earlier
    slide already read.
37. Do not rely silently on an untaught `Copy` of a composite value (an array or a closure
    reused after `into_iter()` or after `Box::new(x)`). Use `iter()` / a fresh value.
38. A SINCE badge sits on the feature it is about. Not on a title whose subject is a
    different or newer feature, and not after "— E0xxx" (it reads as "the error since
    N"): put it in the prose there, as "(1.57 부터)" with the directive.
39. A line that exists only to silence a lint (dead_code) still prints on screen: read it
    in the note or restructure so it is not needed.
40. A table row or quiz step must rest on a RUNNING capture, not on "that line was not
    flagged in a file that failed to compile".
41. `//@ expect:` names the code when the capture has one (`expect: E0631`, not
    `expect: error`).
42. At most four boxes (code + captures) on a slide. A run-time "before" plus its
    compile-time "after" plus a twin is two slides.
43. A slice (`lines=a-b`) does not end on a blank line or a bare `|` line.
44. A "N번 줄" must be inside the slice shown on that slide. If it points into a function
    shown on another slide, name the function and link that slide.
45. When a part is written in two runs, the second run re-reads the first half for anything
    that counts chapters ("세 장"), for the intro lead, for type aliases reused under the
    same name, and for words it is about to give a second sense (lesson 27 across halves).
46. If the screen cannot tell which branch produced a value (`map_or(default, …)`,
    `unwrap_or`), the branch is unexercised even if it ran. Put the expression in a helper
    and call it with a hand-made value for each side.
47. Do not spawn O(n) threads to show a boundary case; shrink the input instead.
48. A caption that claims an order must be checked against the slide order after the last
    slide is written.
49. Every field of a printed tuple or struct is read in the note, or not printed.
50. A term gets its gloss at first technical use in the part, not where its chapter starts;
    grep the earlier chapters before glossing.
51. After an example changes length, re-count every "N번 줄" that points at its last lines
    (the closing `}` is a line; the part-20 review left one such number off by one).
52. Before writing "X 는 … 못 한다" in a title, run the smallest counter-case from the
    neighbouring category (a literal for `expr`-in-pattern). A title about how a class of
    diagnostics looks ("두 자리를 짚는다") is checked against every other diagnostic in
    the chapter.
53. A `// 안전:` comment answers every condition the slide's "문서의 조건" sentence lists
    (non-null, aligned, in bounds, initialised, aliasing), or the slide says which one is
    left out and why.
54. If the example removes the values before the call whose "does not do Y" is the title,
    the capture shows nothing. Say what the function receives, or add a leak twin.
55. Two inputs that print the same thing (`[] []`) do not show which branch ran. Write
    "소스를 따라가면", not "…했습니다".
56. "N째 화면" counts captures only; on CODE+OUT slides name the screen by content.
57. A badge label and the sentence it sits in may not mention anything the matched
    release-note line does not ("경로로", "2018 에디션부터").
58. The appendix is a later part: present tense ("부록의 표에도 … 나옵니다").
59. A negative "there is no way to show it" is itself a claim. Write what the book does
    not do.
60. A `// 안전:` comment lists only real preconditions — "fits in the type" is one for
    `atoi`/`abs`/`div`, not for `strtol`.
61. An example obeys the rule its own chapter's table states (`c_int`, not `i32`, in a
    function that is declared with `c_int` on the other side).
62. On a slide showing two differently numbered files, say which box each "N번 줄"
    belongs to.
63. Before writing "the caller knows only X", delete the "contrast" line and run it — it
    may be what links the crate. A run that cannot be shown (temp paths in the message)
    is said to be unshown, with the reason.
64. A table lead describing a column must hold for every row; rows go in slide order when
    the caption mentions order.
65. Grep the whole book before the first use of a term (링커), and fix a code name's
    particle once per part (`MyVec` 은/을/이/과).
66. Every printed line gets read, including the ones before the interesting one.
67. A hand-made primitive with a single slot (`Option<Waker>`, one receiver) states its
    capacity where it is defined, and no later example exceeds it — even on a path that
    "never fires".
68. "X 가 먼저 찍혔다, 그러므로 Y 는 아직 돌지 않았다" needs Y to print something. If the
    body is silent, read a counter ("poll 2번") or add a print.
69. In a file that uses a metaphor word (문 = door), do not use the same word in another
    sense (문 = statement) in a comment; write "let 문".
70. An intro sentence of the form "X 는 N장에서만 본다" is grepped against the other
    half of the part before it is written.
71. When an earlier capture of the same error carried a `note:` that the new capture
    lacks, say so, rather than paraphrasing the old note as if it were on this screen.
72. A key head is a title too: "A 가 B 를 정한다" drawn from one error message is a
    generalisation. Head it with what the message pointed at.
73. Each `$` line of a directory example runs from the sandbox root; `cd x && …` and
    `VAR=v …` last one line. Say so in the part's intro, and never write "typed in order"
    unqualified.
74. Order evidence needs an order that could have been otherwise: do not list the
    dependency first in `members` and then say Cargo ordered it.
75. "Same command" across twins means byte-identical RUN lines; the intro's definition of
    a twin covers add, remove and move, and says when the commands differ.
76. A cut inside a failing run still shows the result line and `[종료 코드 N]` (use two
    slices); the cut note names the slides that showed the omitted blocks, not "앞의 두
    슬라이드".
77. Cargo messages change with how the package was selected ("in default-run packages"
    vs "in `x` package"); probe both and prefer wording that does not collide with a key
    the part teaches.
78. Every environment variable an example reads at build or test time is a dependence on
    the caller's shell (rsrun strips only CARGO*/RUST*); list them in the part's intro.
79. `cargo new` in a workspace inserts into a sorted `members` list in sorted position, so
    a later `cat Cargo.toml` depends on the members order.
80. For a line the program did not print (`Aborted`, `ls:`), find the printer with a
    scratch probe and write "이 기계의 셸이 …"; use "Cargo 문서는 …" only for sentences you
    can place, otherwise "이 책은 … 로 읽습니다" hung on a release-note line.

### Lessons from the review of part 24, project 1 (building a program in step directories)

81. Probe the finished program before writing slides: an empty argument, a non-UTF-8
    argument (`"$(printf 'caf\351.txt')"`), `--`, a repeated flag, a six-digit number, a
    just-outside-the-set byte, an unwritable stdout and stderr. Each outcome becomes a
    rules-table row with a capture or test, an exercise, or a "받지 못하는 것" row.
82. `env::args()` panics (exit 101) on a non-UTF-8 argument, and `eprintln!` panics when
    stderr cannot be written. A chapter that promises "exit codes 0/1/2" shows or states
    these.
83. A definition that leans on a std predicate (`is_ascii_whitespace`,
    `char::is_whitespace`, `is_alphanumeric`, `trim`) names the exact set and tests one
    member just outside it.
84. "The slide shows only the new lines" is a claim about every box: a box holds only new
    lines, or its caption says which are new. A `use` or `const` added at the top gets
    its own one- or two-line CODE box on the slide that first needs it.
85. Steps are "N단계" with N from the directory name, defined once in the steps table.
86. A quiz about "the program" names the step whose capture answers it, or the command
    goes into the final step's RUN.
87. Decide every edge assertion of a definition before writing slides: one assertion
    inserted into the step-1 test moved seven slices and 25 line references across four
    steps. Re-run the line audit (`lines.py`) after every generator run.
88. In step chapters, read the rows that are not new as well (totals, columns not under
    discussion).
89. A refactoring step's capture is identical before and after: say so in the title and
    give the step a test only the new code can pass.
90. When the new program changes a rule of the earlier-part program it builds on, say so
    where the rule is introduced ("17부의 … 와 다른 점").
91. Mechanism words ("converted", "the sibling of", "the code decides") become the
    compiler's own word quoted from the screen, or "소스를 따라가면".
92. Relative `data/…` paths next to `CARGO_MANIFEST_DIR`: say why each is used; the
    screen shows only that cargo was typed at the package root.
93. `/dev/full` cannot be opened on this machine and a broken-pipe run is timing-dependent;
    show a write failure with a failing `Write` impl in a test.

### Lessons from the review of part 24, project 2

94. "여기서 처음 쓰는 X" is a claim about the whole book: `grep -rn X ex/ deck/sections`
    before writing it.
95. "N줄이 다르다 / 이름만 다르다 / 한 줄이 다르다" about a file inherited from an earlier
    project: `diff` the two files and list the lines; comments count.
96. A frame sentence in a steps-table cap is checked against every row of that table.
97. A gloss of a shell tool's output format ("한 줄에") is checked against every later
    use of that tool in the chapter.
98. "이 책이 만들지 않았다 / 다시 싣지 않았다": grep the earlier parts first, and count
    how many screens the earlier chapter really has.
99. A rules-table row that says "X → 알리고 N 으로 끝낸다" is probed for every channel the
    row's label covers. stderr is a channel.
100. Ordering claims between two options need an input where the other order would
     differ; otherwise write "소스를 따라가면".
101. Quiz commands placed at the end of the final RUN must be shown: put the OUT slice
     inside the answer block.
102. A term reused in a new sense is glossed on the first slide that uses it (usually the
     reuse slide), not at its "definition" slide.
103. Machine- or toolchain-made text is labelled on the slide where it first appears —
     usually the "다 만들면" slide.
104. A rules table over about 10 rows is split by theme into two slides from the start.

### Lessons from the review of part 24, project 3

105. Re-count every number word against the screen after the last generator run (files
     under `src/`, modules with tests, tokens on a line).
106. A term's counting rule is part of its definition: decide whether sentinels (`End`)
     count, say it once, and grep every count.
107. A source-following proof lists every return path and every function on a cycle.
108. If a limit exists because of function B, test B at the limit, not only the function
     that enforces it.
109. Phrase failure rows from the code's view ("쓸 곳이 Err 를 돌려주면") unless every
     channel was probed from outside: EPIPE on stderr → 101, a closed descriptor (`>&-`)
     → writes silently succeed.
110. "같다" about an inherited signature: diff the header, binding modes (`mut`) included.
111. Grep first uses in TEST code too.
112. Do not reuse a chapter-wide word (줄) for a second thing without a qualifier
     ("문법의 줄").
113. An exercise states a convention as a choice ("이 과제에서는 … 로 정합니다"), not a
     fact.
114. A twin whose RUN differs from its sibling's names both commands on the slide.
115. `make deck` alone leaves the base font: run `make all` (or `make font`) before
     comparing the built deck with the committed one. The builder already prints the full
     path on every CODE box.
116. Before a storage/CLI project: probe separator, newline, CR, NUL and empty strings in
     every user-supplied field; missing, empty, corrupt, non-UTF-8 and unterminated data
     files; duplicate keys; wrong argument counts and unknown commands; state and sort
     any listing order; make thread output deterministic by design (fixed join order,
     print after join), never by a claim about interleaving; say what a poisoned lock
     does.

### Lessons from the review of part 24, project 4 (apply from part 25 on)
117. Before writing "N부에서 본 대로 X", read the target slide's sentence for X. A slide
     whose title matches can teach the opposite case (`p20-guard-scope` is about a
     temporary guard dying at the end of the statement; a guard bound to a variable is
     `p15-mutex`).
118. "N째 명령 / N째 실행" is recounted against the `$` lines of the capture. Where a
     chapter defines a word as its own term (명령 = a line the program reads), the
     everyday sense gets its full name everywhere, captions included (셸의 명령).
119. "Outside the test module there is no `unwrap`" must account for `#[cfg(test)]`
     functions that are not inside `mod tests`.
120. In a Cargo error capture, `For more information about this error, try …` is
     rustc's line and only `error: could not compile …` is Cargo's. Say which, on every
     slide that reads the tail of such a capture.
121. A path under a directory that does not exist gives a deterministic write failure
     even for root: use it to put a write failure on a binary screen instead of
     "소스를 따라가면".
122. For a threaded program, decide and SHOW what happens when one worker fails. Three
     inputs (harmless, failing, harmless) with disjoint effects give a deterministic
     screen that shows "earlier written, later not".
123. "X 로는 만들 수 없는 것들" over a list: probe each member. A closing generalisation
     over N programs is checked clause by clause against each program, and its counted
     words ("세 층") must match the chapters' own counts. An exercise slide's frame
     ("과제마다 파일과 함수를 적었다") is checked item by item.
124. A definition of "a step copy" must cover deletion: `diff` every step pair and look
     for hunks that only remove.
125. Do not reuse, as a callout head, a phrase the previous slide just disambiguated.
126. When acknowledging a repeated E-code, compare the two captures note by note and
     read every `note:` the new one prints, including ones the earlier slide showed but
     did not read.
127. "A 는 N번 줄에서 둔 것" — check for an earlier line that set it first.
128. A rules row about failure names the mode (stdin vs files/threads) whenever what
     "has already happened" differs between them.
129. A determinism argument covers every artefact a screen shows (the answers AND the
     file that `cat` prints) and the failure path, not only the happy path.

### Lessons from the review of part 25, first half (exercises; apply from 25b's review and part 26 on)
130. In a fix-it pair, line numbers on the solution slide come from the SOLUTION file;
     every line after the first changed one differs between the twins.
131. A compound condition in a solution needs an input where each operand alone decides
     a printed line. Check by deleting the operand in a scratch copy and diffing the
     capture.
132. An edge is "unexercised" only if two reasonable implementations would print
     different things there; when both branches give the same value, do not list it.
133. A token audit misses implicit steps: deref coercion at an argument (`&&str` where
     `&str` is expected), copying `&T` out of `&&T`, array to slice. Audit the TYPES at
     every call and every `*`, not only the tokens.
134. For "same headline as the teaching slide", normalise names and positions and diff
     the two captures. If only names differ, the bad program is the teaching example
     renamed — say so or change the situation.
135. A solution obeys the preferences the named parts state in their own titles (an
     index loop where `p04-for-index` says to loop over the elements is a defect).
136. After adding a line to a given `main`, re-read every "화면의 마지막 줄" and every
     `lines=` of both the problem and the solution slide.
137. A statement that licenses `unwrap` or plain arithmetic by "fits in T" bounds the
     VALUES by the domain ("0 부터 100 까지"), or sums can overflow.
138. No "X 로 했다면 … 해야 합니다" about an alternative that was not run; say what the
     linked example did.

### Lessons from the review of part 25, second half (apply from part 26 on)
139. Before "그때의 note:/help: 는 …", check the teaching slide's `lines=`: compare with
     the slice the slide SHOWS, not with the whole capture file.
140. For every bad twin, apply the compiler's `help:` literally in a scratch copy and
     run it. Note whether it compiles, errors again, or prints a different screen —
     and say on the slide only what you ran.
141. A twin whose cure is the teaching slide's cure trains recall. Make the cure differ
     (a missing method instead of a skipped call; a non-`Send` capture instead of a
     missing `+ Send`), or say in one clause that it is the same situation.
142. A screen shows hygiene or shadowing only if the other reading would print
     something else.
143. An annotation that exists only to keep the error count at one is said on the
     slide, with the unshown run named as unshown.
144. rustfmt wraps method chains at 60 columns, before the 72-column limit: run
     `rustfmt --check` before fixing line numbers on a slide.
145. A headline and a label can name the same type differently (`Parcel<State>` /
     `Parcel<Packed>`): read both as written.
146. A fix that needs a supertrait (`Ord: Eq + PartialOrd`), an inherent associated
     const, `*self = value`, a block-bodied closure or `|_|` leans on something no
     slide of parts 2–23 teaches in prose: avoid it in a bad/fixed pair or gloss it in
     one clause with the closest slide.

### Lessons from the review of part 26, first half (error entries)
147. A symptom title is a claim over the whole book: grep `ex/` for the same construct
     COMPILING (`3.min(8)`, `42.to_string()`) before writing "X 를 했다 — E0xxx", and
     name the method or type when only that case fails.
148. "Same headline" is grepped by its TEXT, not by its code: the same sentence can
     carry another number (`cannot find type` is E0425 at `p01-int`, E0433 elsewhere),
     and the closest capture may sit on a slide that showed it without reading it.
149. When an unshown run is a neighbouring mistake, first grep `out/` for a SHOWN
     capture of that shape and link it; keep "(싣지 않은 실행)" only for what no slide
     shows, at most two per entry, and record every warning of such a run, not only
     its errors.
150. A part intro's definition of a working word is checked against every kind of use
     in the whole part; a rule about titles is checked against every title.
151. A word with two senses in a part (실수 = mistake / float) stays out of titles.
152. "N번 줄의 f" for a method names the `fn` line; the line that does the thing is
     cited separately.
