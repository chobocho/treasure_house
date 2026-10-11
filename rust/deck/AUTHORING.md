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
