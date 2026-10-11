# Rust 기초 문법집 (Rust_기초_문법집.html) — Work Plan for the Building Agent

Read this file first in every session. The progress log at the bottom is the only
state that survives a killed session (this machine kills sessions — see §0.8).

## 0. Non-negotiables

1. **The deck HTML is a build artifact.** Never edit `../Rust_기초_문법집.html` by hand.
   Edit `deck/sections/*.html` (or the example/capture it points at) and run `make deck`.
2. **Only examples that run.** Every `<pre>` of code in the deck is cut from a real file under
   `ex/` by the builder; every output is a capture under `out/` written by `tools/rsrun.py`
   from this machine's `rustc 1.99.0`. No hand-written code, output, or compiler message in a
   section file. The builder rejects a hand-written `<pre>` (only `<pre class="fig">` ASCII
   diagrams are allowed, and they must not contain Rust code).
3. **Compile-error examples are allowed** (user decision 2026-10-11) when the error is the
   lesson: the file carries `//@ expect: E0382`, the capture is rustc's real message, and the
   same slide or the next one shows the fixed version that runs.
4. **std only.** No external crates, no network for cargo (`--offline`). async is a taste only
   (hand-made executor on std).
5. **Every history fact has a source.** Dates and version numbers are never typed from memory:
   release dates come from `data/releases.tsv` (generated from the official RELEASES.md) through
   `<!--REL v=1.65-->`; "since which version" badges come from `data/features.tsv` through
   `<!--SINCE key=let-else-->`; other history claims carry `<!--SRC key=...-->` from
   `data/sources.tsv`, and the cached source text must contain the evidence (`make data-check`).
6. **Knowledge-cutoff discipline.** The author model's knowledge ends 2026-06; rustc here is
   1.99.0 (2026-09-28). Anything about 1.9x releases is written only from the fetched release
   notes and from what this compiler actually does.
7. **Tests before code (RED → GREEN)** for every Python tool here (`tools/tests`, unittest).
   Never loosen an assertion to pass.
8. **Machine: Galaxy Fold, Termux/proot, swap nearly full.** At most **1 writing subagent**
   at a time (user decision 2026-10-11), each scoped to about half a part (≤ 50 slides) so its
   context stays small. `rustc`/`cargo` run one at a time (rsrun takes `scratch/rustc.lock`),
   `codegen-units=1`, cargo `-j1`. No `make -j`. Commit after every part; log here.
9. **Foldable layout.** Code `<pre>` ≤ 45 lines and ≤ 72 columns (Korean = 2 columns);
   captures ≤ 108 columns. `ex/rustfmt.toml` sets `max_width = 72`. One slide = one idea; a
   slide normally shows one example and its output (the `RUN` directive).
10. **Hard cap 1000 slides** (user decision). Target 945, band 850–960. `deck/budget.txt` holds
    per-part targets; the builder fails above 1000 total or above +10 % for a part.
11. **Language:** deck prose Korean 합니다체; identifiers in English; comments inside examples
    in Korean (short, ≤ 72 columns with the code). Commit messages Korean descriptive, no
    prefix (repo convention). No `git push` unless the user asks.
12. **Scope.** A beginner's grammar book with a history part. Not an async/web/embedded
    course, not a std API catalogue. Each syntax item: why it exists → smallest running example
    → the common mistake (compile error or surprising output) → the fix.

## 1. Directory layout

```
rust/
  Makefile            every command lives here (`make help`)
  PLAN.md             this file
  tools/rsrun.py      compile + run one example, write the capture (the only thing that runs code)
  tools/fetch_docs.py official sources → docs/ (cache, not committed)
  tools/make_data.py  docs/ → data/releases.tsv; --check validates features/sources/facts
  tools/tests/        unittest for the tools and the builder
  ex/NN/name.rs       single-file example (NN = part number)
  ex/NN/name/         multi-file or cargo example with a RUN file
  out/NN/name.txt     capture (committed — it is the evidence)
  out/MANIFEST.tsv    source sha256 ↔ capture sha256 ↔ rustc version
  data/               releases.tsv (generated), features.tsv, sources.tsv (hand-kept, checked)
  deck/base/          head.html + tail.html (split from ../template.html; engine untouched)
  deck/sections/      NN_name.html fragments — the only place prose is written
  deck/order.txt      fragment order;  deck/budget.txt  per-part slide targets
  deck/build_deck.py  fragments + examples + captures → ../Rust_기초_문법집.html
  deck/verify_deck.py re-reads the built deck and compares every <pre> with its source
  deck/check_deck.js  structure + engine contract on a DOM stub (no browser here)
  scratch/            binaries, cargo target, sandboxes, lock (not committed)
```

## 2. Example conventions (`tools/rsrun.py`)

- Toolchain: Termux `rustc`/`cargo` 1.99.0, host `aarch64-linux-android`. Linking needs the
  Termux clang (`-C linker=/data/data/com.termux/files/usr/bin/clang`); rsrun adds it and
  hides it from the shown command line (part 0 of the deck says so).
- Default edition 2024. Directives are **trailing** `//@ key: value` lines at the very end of
  the file (trailing so that line numbers in compiler messages match the code on the slide;
  the builder strips them from the slide and rsrun strips them before compiling):
  `edition: 2021` · `expect: E0382[,E0499]` (must fail to compile with these codes) ·
  `exit: 101` (expected exit code of the program) · `flags: -O` · `test` (compile with
  `--test`) · `args: a b` · `stdin: 3\n4\n` · `warnings: show` (compiler warnings are part of
  the lesson; otherwise a warning is an error for the author to fix) · `norun` (compile only).
- A directory example has a `RUN` file: one shell command per line (`cargo run -q`,
  `cargo test -q`, `rustc --edition 2024 main.rs`, `./main`), optional `#@ exit: N` after a
  command. It runs in a copy under `scratch/` so `ex/` stays clean.
- Capture format: `$ command` lines followed by merged stdout+stderr; `[종료 코드 N]` when
  non-zero. Declared normalizations (and nothing else): the thread id in panic messages
  (`thread 'main' (12345) panicked` → `(tid)`), test/cargo timings (`in 0.00s`), and the
  sandbox path (`/work`).
- `python3 tools/rsrun.py ex/06/move.rs` writes the capture; `--check` re-runs and compares;
  `--all` runs everything; `--manifest-check` only compares hashes (fast, used by `make all`).

## 3. Section directives (`deck/build_deck.py`)

One per line unless noted:

```
<!--RUN file=ex/06/move.rs note=한 줄 설명-->          code + its capture (the usual case)
<!--CODE file=ex/06/move.rs lines=3-10 note=...-->     part of a file
<!--OUT file=out/06/move.txt lines=2-6 note=...-->     part of a capture
<!--REL v=1.65-->        inline → "1.65(2022-11-03)" from data/releases.tsv
<!--SINCE key=let-else-->  inline badge "1.65" from data/features.tsv
<!--SRC key=rust-1.0-announce-->  inline source badge from data/sources.tsv
```

Slides: `<article class="card" id="pNN-slug">` (id required, unique, prefix = part).
Part cover `class="card section"` id `pNN`; chapter cover is a plain card with
`<p class="chnum">N장</p><h2>…</h2><p class="chsub">…</p>` and id `pNN-chM`.
Components (callouts `.note/.tip/.warn/.key`, tables `.tblwrap > table.kv`, `.steps`, `.flow`,
quiz) are catalogued in `../template.html` slides `c-*` — read that, do not invent CSS.

## 4. Parts and budgets

| # | file | part | slides |
|---|------|------|--------|
| 0 | 00_start | 읽는 법·증거 방식 | 15 |
| 1 | 01_history | Rust의 역사 | 60 |
| 2 | 02_first | 첫걸음 — rustc·cargo·fmt·clippy·println! | 40 |
| 3 | 03_types | 변수·기본 타입·형변환·오버플로 | 60 |
| 4 | 04_flow | 식과 문·제어 흐름 | 50 |
| 5 | 05_fn | 함수 | 35 |
| 6 | 06_own | 소유권·빌림·슬라이스 | 85 |
| 7 | 07_data | 구조체·열거형·패턴 매칭 | 80 |
| 8 | 08_coll | 문자열·컬렉션 | 70 |
| 9 | 09_err | 오류 처리 | 55 |
| 10 | 10_trait | 제네릭·트레이트 | 80 |
| 11 | 11_life | 수명 | 45 |
| 12 | 12_iter | 클로저·반복자 | 60 |
| 13 | 13_mod | 모듈·크레이트·시험·문서 | 50 |
| 14 | 14_ptr | 스마트 포인터 | 45 |
| 15 | 15_conc | 동시성 기초 | 40 |
| 16 | 16_more | 매크로·unsafe·async 맛보기 | 40 |
| 17 | 17_appendix | 부록 — 키워드·연산자 표, 용어집, 출처 | 35 |

Total 945. Large parts are split into `NN_` and `NNb_` files (one subagent task each).

## 5. Steps

1. Skeleton — tree, PLAN, base, placeholders; `make deck SKEL=1` opens.
2. Tools — rsrun, build_deck, verify_deck with tests (RED → GREEN); `make all SKEL=1` green.
3. Data — fetch_docs, make_data (releases.tsv), features/sources checks, with tests.
4. Parts 2 → 16 (one commit per part or half part), then 1 (history), 0, 17.
5. Wrap-up — `make all` without SKEL, font, index.html card, README.md, history.md.
6. Review — one pass, one subagent at a time; `rsrun --check --all` twice identical.

## 6. Decisions (user, 2026-10-11 — final, do not re-ask)

1. Compile-error examples allowed (real message, checked code, fixed twin).
2. std only; async as a taste.
3. File `Rust_기초_문법집.html`, directory `rust/`.
4. History: one part (~60) plus "since version" badges on syntax slides.
5. One writing subagent at a time.
6. Hard cap 1000 slides.

## Progress log (append only; newest at the bottom)

### Plan written, skeleton started (2026-10-11)
- Toolchain verified: rustc 1.99.0 compiles/runs/tests with the Termux clang linker;
  editions 2015–2024 accepted; panic exit code 101; sources (RELEASES.md, blog, reference)
  reachable.
- `deck/base/head.html`·`tail.html` split from `template.html` (NAV and DEMOS markers).

### Steps 1–2 — skeleton and tools (2026-10-11)
- `tools/rsrun.py` (36 tests), `deck/build_deck.py` + `deck/verify_deck.py` (29 tests),
  `deck/check_deck.js` (goevo's, demo cases emptied), Makefile. `make all SKEL=1` green, 19 slides.
- Highlighter in `deck/base/tail.html` taught Rust: lifetimes (`.lt`) vs char literals, raw
  strings, attributes (`.at`), macros, suffixed numbers. Theme recoloured (rust orange).
- Authors: deliberate syntax-error examples that rustfmt cannot parse are listed in `ex/nofmt.txt`.
- The built deck HTML is not committed until wrap-up (rebuildable; avoids churn).

### Step 3 — data tools; authoring kit (2026-10-11)
- `tools/fetch_docs.py`, `tools/make_data.py` (+21 tests, 87 total). `data/releases.tsv`
  generated from RELEASES.md (155 releases, newest 1.99 2026-10-01). Builder gained `FACT`
  and the history-part rule (every slide cites; every year must appear in its evidence).
- rsrun: `expect: error` (syntax errors without a code), `--prune`, orphan check.
- `deck/OUTLINE.md` (chapter contract for all parts), `deck/AUTHORING.md` (subagent brief),
  part 2 chapter 1 written by the orchestrator as the model chapter (10 slides).
- Known red: `#p02-ch3` link dangles until part 2 chapter 3 exists.

### Parts 0, 1, 2 (2026-10-11)
- Part 1 (history, 60 slides, orchestrator): 24 sources in `data/sources.tsv`, 83 facts in
  `data/facts.tsv` → `data/evidence.tsv`; 19 experiments in `ex/01` (pre-1.0 leftovers and
  edition differences run on today's compiler). Facts: a space in an evidence regex matches
  any whitespace run (fetched text wraps mid-sentence).
- Part 0 (15 slides, orchestrator): `ex/00/machine` shows the toolchain and the rustc shim.
- Part 2 (43 slides): chapter 1 by the orchestrator, chapters 2–4 by a subagent (177k tokens,
  14 min). cargo new / clippy / cargo fmt all work offline in the sandbox. `cargo clean` must
  be `-q` (it prints a size that can drift).
- Builder: generated appendix slides `ECODES` / `GLOSSARY` / `SOURCES` (+4 tests, 93 total).
- `make all SKEL=1` green at 133 slides.

### Parts 4, 5 (2026-10-11)
- Part 4 (49 slides, 37 examples) and part 5 (34 slides, 24 examples) written by the
  orchestrator while the part-3a subagent ran. `rsrun --check` identical for ex/00,01,04,05.
- rustc 1.99 notes: "cannot find type" is E0425 (not E0412); `let b = a = 5;` warns
  `unused_assignments` unless `a` is read first; `5..1` gives no warning.

### Parts 3a, 9, 11, 14, 15 (2026-10-11)
- 3a (31 slides) by a subagent (143k tokens, 11 min); 3b running. Orchestrator wrote
  part 9 (51), part 11 (45), part 14 (41), part 15 (36) in parallel with the subagents.
- Authoring lessons added to AUTHORING.md: format only your own files (not `make fmt`);
  Korean counts 2 columns for the builder but 1 for rustfmt.
- Part 15 captures re-run 3× identical. Version badges now 25 rows in features.tsv.
- Remaining: 3b (running), 6, 7, 8, 10, 12, 13 (subagents, one at a time), 16 and the
  appendix (orchestrator), then wrap-up and review.

### All parts written — 912 slides (2026-10-11)
- Subagents wrote 2 (ch2–4), 3a, 3b, 6a, 6b; the orchestrator wrote 0, 1, 4, 5, 7, 8, 9, 10,
  11, 12, 13, 14, 15, 16 and the appendix in parallel. 610 examples, 30 version badges,
  27 sources, 83 history facts. `make all` (no SKEL) green: 98 tests, 1233 blocks verified.
- Builder fixes found late: (1) a `note=` containing `>` (`->`, `Option<u8>`, `=>`) made the
  directive silently vanish — 8 slides had lost their code; fixed with a regression test and
  the "unused example" check is what exposed it. (2) new check: a `.rs` CODE slice must be
  brace-balanced (cut at function/block boundaries).
- rsrun: doctest timings are normalized too (`ran in`, `compilation took`).
- Appendix: keyword and precedence tables are transcribed from the fetched Rust Reference
  pages (sources `ref-keywords`, `ref-expressions`); glossary in `deck/glossary.tsv` (46).
- Review 1 started: one subagent at a time, guide in `deck/REVIEW.md`. Parts 2–3 first.

### Review 1 in progress; full re-run (2026-10-11)
- Reviews done: parts 2–3 (8 fixes), part 6 (9 fixes), committed 9f5e6e75. Running: 4–5.
  Queue: 7, 8, 9+11, 10, 12+13, 14+15+16, 0+1+17 — one reviewer at a time (`deck/REVIEW.md`).
- New builder check: an E-code in a slide title must appear in that slide's capture
  (error); a code shown but missing from the title is a notice. 100 tests.
- Full `rsrun --all --check` (every example re-run and compared with its capture) reported
  no mismatch: the filtered log had no `✗` line and no `실패` summary. The log kept only
  non-`✓` lines, so the count is taken from the example list (611 at the time), not from
  the log. It ran while the 4–5 reviewer was editing; their own `--check ex/04 ex/05`
  covers anything they change afterwards.
- "장" is reserved for chapters; adjacent slides are "앞 슬라이드 / 다음 슬라이드"
  (rule added to REVIEW.md; parts 2, 3, 6 fixed by hand).

### Review 1 — parts 4–15 done; a real flake found (2026-10-11)
- Reviews committed: 4–5 (0c6942f8), 7 (f9d8c83d), 8 (cce5db57), 9 (dceea36a),
  10 (fbeb2214), 11+14 (a535c1ed), 12 (47dd770c), 13+15 (936479d7). Running: 16+0+17.
  Left: part 1 (history). Backing slides added by reviewers/orchestrator: 4부 +2, 11부 +2,
  12부 +2, 15부 +1 → 919 slides. index/README still say 912 — fix at the end of review.
- **Correction to the earlier "full re-run found no mismatch" entry:** that run did pass, but
  it did not prove determinism. The 13+15 reviewer hit a mismatch in `ex/13/test_asserts.rs`
  on a later run: libtest runs tests on several threads and prints result lines in
  completion order. Four multi-test examples were affected; all now carry
  `//@ args: --test-threads=1`, and rsrun refuses an unpinned multi-test example (test added,
  101 tests). One passing run is not evidence of determinism — thread-order cases need
  repeated runs (part 15 was run 10×, part 13 3×).
- Most frequent defect classes across my own parts: forward use without a pointer, slices
  that cut the top of a file (compiler line numbers then disagree with the box), error
  slides that did not read the message, claims a capture does not show (speed, other
  languages, "가장 흔한").
