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
10. **Hard cap 2000 slides** (user decision; 1000 until 2026-10-12). Per-part targets in
    `deck/budget.txt` are still the 945-slide ones until an expansion plan is agreed; the
    builder fails above 2000 total or above +10 % for a part.
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
6. Hard cap 2000 slides (raised from 1000 on 2026-10-12).

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

### Review 1 finished — 921 slides (2026-10-11)
- Last reviews committed: 16+0+17 (796f8f5e), part 1 (86b2eacf). Every part has now been
  read against its sources and captures by a reviewer (one at a time; the two largest
  reviewer conversations were 308k and 338k tokens — keep batches ≤ 80 slides next time).
- Part 1: 45 "source says less than the Korean" fixes, +68 facts (83 → 152), 17 unsourced
  sentences removed, the 32-length array limit corrected from 1.51 to 1.47, experiment pairs
  made byte-identical apart from `//@` lines, new E0554 slide for `#![feature]` on stable.
- Builder: a `note=` that merely starts with a quoted word is no longer cut at the closing
  quote (2 labels restored). 103 tests.
- Final verification: `make all` rc=0 (621 examples, 921 slides, 1254 blocks verified,
  font check passes); `rsrun --all --check` three passes in a row, each exit 0 with
  621 ✓ / 0 ✗ (counts taken from the logs this time).
- Open, recorded on the slides rather than resolved: the GC removal date differs between
  the Technology Review article ("by 2013") and the release notes (0.11/0.12, 2014);
  the cached Android post has only title and date. `rustup-beta` fact is cited nowhere.
- index.html card, README and history.md updated to the real figures. Not pushed.

### Review 2 in progress — reader flow and style (2026-10-11)
- Brief: `deck/REVIEW2.md` (ea97894b). One reviewer at a time, batches ≤ 90 slides,
  commit per batch only when `make deck` exits 0. Review-2 commits are NOT pushed yet
  (origin/main = 420c95d0); ask the user before pushing.
- Done: parts 0+2 (0f9b305a). Running: part 3.
- Remaining order: 4+5 → 6 → 7 → 8 → 9 → 10 → 11+14 → 12 → 13+15 → 16+appendix → 1.
- After the last batch: `make all` (no SKEL), `rsrun --all --check` ×3 with counts and exit
  codes logged, card/README figures only if slide or example counts changed, history.md
  entry, memory note, then report and ask about push.
- Review 2 batches committed so far: 0+2 (0f9b305a), 3 (9d4db97e), 4+5 (dea9684c). Running:
  part 6. Brief lesson: take part titles from OUTLINE.md (the 4+5 brief wrongly called
  part 5 "함수와 모듈"). ex/04/match_bind.rs now runs three values so the guard arm is
  evidenced. Decisions keep accumulating in REVIEW2.md ("Decisions added …" block).
- Notes for later batches — part 7: p07-pat-tuple/p07-pat-guard should acknowledge
  p04-match-bind (가드), p07-enum-missing-arm (E0004) should acknowledge p04-match-missing,
  07b line ~9 `#p04` → `#p04-ch4`, 튜플 풀기 → p03-tuple. Part 8: NaN → p03-nan, char →
  p03-char. Part 10: 실수 sort 오류 → p03-nan-sort. Part 12: "모음" → "컬렉션"
  (p12-three-iters). Part 15: static → p03-static. Part 0: p00-broken "3부에서" could go to
  p03-mut-type.
- Part 6 reviewed (review 2). Notes for later batches — part 1: p01-nll "그 변수의 범위가
  끝날 때까지" → 스코프, link `#p06` → `#p06-nll-early`. Part 8: 08_coll.html links
  "6부 N장" to the cover → p06-push-holding (p08-vec-capacity), p06-char-boundary /
  p06-str-slice, p06-take-slice, p06-vec-move (E0507), p06-literal-string. Parts 9 and 14:
  p09-panic-unwind and p14-drop-order must acknowledge p06-drop-scope; 14_ptr.html says
  "읽는 빌림" ×3 → 불변 빌림.
- Part 7 reviewed (review 2); two slides reordered inside their chapters (p07-unit-struct,
  p07-refutable), count unchanged. Decisions: clone = 복제, destructuring = 풀어 헤치기.
  Notes for later batches — cover links `#p07` to retarget: 01_history 593/659 (let … else →
  p07-let-else), 596 (→ p07-let-chain); 08_coll 22 ("7부에서 한 번 본" closure →
  p07-param-pattern); 09_err 184; 10b_trait 181; 13_mod 454 (derive → p07-struct-debug).
  Part 9: p09-opt-match / p09-opt-not-value must acknowledge p07-option-enum (its `.key`
  "null 대신 Option" overlaps part 9's "null 이 없는 언어").
- Part 8 reviewed (review 2). ex/08/str_methods.rs gained a Korean `find` line so "byte
  index, not char index" is shown, not asserted. Decision: index = 인덱스. Notes for later
  batches — part 10: 10_trait 63 (len 은 바이트 → p08-str-utf8), 317 (실수 키 오류 →
  p08-map-float-key), 10b_trait "색인" ×2 → 인덱스; part 11: 11_life 325 → p08-str-utf8;
  part 12: 12b_iter 282 ("8부에서 미뤄 둔" → p08-sort-strings), 300 (entry →
  p08-map-word-count), 38 (`#p08`); appendix: 17_appendix 45 "색인" → 인덱스, 132 `#p08`;
  parts 15/16: "N~M번 줄" → "N번부터 M번 줄까지". All later parts: "출력 N번째 줄" counts
  the `$ …` line — check each use.
- Part 9 reviewed (review 2); three slides reordered inside their chapters (p09-opt-iflet,
  p09-res-chain, p09-err-main-box), count unchanged. Notes for later batches — `#p09`
  cover links: 10_trait 222/268 → p09-err-display; 10b_trait 13 → p09-err-from; 11_life
  212 → p09-opt-question; 12b_iter 144 → p09-real-collect, 307 → p09-opt-defaults, 67;
  13_mod 323 → p09-res-main; 16_more 361 → p09-err-display. Part 14: p14-drop-order has no
  link to p09-panic-unwind / p06-drop-scope (section D chain).
- Part 10 reviewed (review 2), no reordering. Notes for later batches — overlaps that must
  acknowledge part 10: p11-static-bound ↔ p10-generic-fn; p12-impl-iterator ↔
  p10-trait-default / p10-assoc-type; p12-return-closure ↔ p10-return-impl; p14-box-dyn ↔
  p10-dyn-vec; p14-deref-coercion ↔ p10-as-ref. `#p10` / `#p10-chN` links to retarget in
  12_iter (ch2 ×3, ch5, ch6), 12b_iter (ch1), 13_mod 454, 14_ptr 73/112, 01_history
  (490 trait → p10-trait-basic, 499 dyn → p10-dyn-vec, 586 → p10-trait-param, 590/647 →
  p10-const-generic). Open evidence gaps to decide at the end: p09-err-display "Error 는
  Debug 도 요구", p09-todo unimplemented!/unreachable!, p10-mono "사본", p10-static-dynamic
  "한 벌씩".
- Parts 11 and 14 reviewed (review 2), no slide moved. Notes for later batches — part 12:
  p12-three-iters "모음" → 컬렉션, p12-closure-vec `#p14-ch1` → p14-box-dyn, part end of 11
  hands over via p12-return-closure. Part 13: last content slide p13-attr-table has no
  hand-over to part 14. Part 15: `#p14` → p14-rc-share / p14-rc-immutable /
  p14-refcell-basic on p15-rc-not-send / p15-arc-no-mutex / p15-refcell-not-sync;
  p15-borrow-err `#p11` → p11-static-bound and "꼬리표" for span labels; "7~9번 줄";
  cover/intro "범위 스레드" (scoped threads — decide the term). Evidence gaps noted:
  p14-cell-copy (`get` needs Copy — not stated), p14-drop-method "두 번 정리" is reasoning.
- Part 12 reviewed (review 2): 61 → 62 slides (new p12-adapter-table closing the adaptor
  catalogue; p12-closure-infer moved before capture). BOOK TOTAL IS NOW 922 — index.html
  card (line ~765), README.md (~47) and history must say 922 at the wrap-up. Notes — part
  15: 15_conc ~30 `#p12` → p12-closure-basic, ~64 → p12-capture-move; part 1: 01_history
  485 "(12부)". No performance/zero-cost note exists in part 12 (outline listed one); none
  was invented.
- Parts 13 and 15 reviewed (review 2), counts unchanged (47, 37; book 922). "범위 스레드" →
  "스코프 스레드" in sections, data/features.tsv and deck/glossary.tsv. p13-attr-table's
  caption used to say `#![…]` never appears in the book's examples — it does once
  (ex/01/feature_gate.rs on p01-nightly); now says so. Notes — part 1: p01-cratesio `#p13`
  → p13-crates-io; appendix/part 16: check for "범위 스레드". Remaining batches: 16+17, 1.
- Part 16 and the appendix reviewed (review 2): counts unchanged (37, 30; book 922).
  Glossary 59 → 64 rows (되감기·복제·스코프·정리·풀어 헤치기), still 8 pages — the card and
  README say "용어집 59낱말" and must say 64 at the wrap-up. Outline items that have no
  slide and were NOT added: part 16 ch 4 never type / impl Trait in more places / shadowed
  prelude; appendix edition table (p01-ed-table is the only one). Notes — part 1:
  p01-ed2024-setvar `#p16` → p16-unsafe-call, p01-async → p16-ch3, macro rows of
  p01-milestones → p16-derive. Remaining batch: part 1.

### Review 2 finished — 922 slides (2026-10-11)
- Last batch: part 1 (860119bc). Every part has been read straight through for flow and
  voice by one reviewer at a time (13 batches, largest reviewer conversation 282k tokens).
  About 1,570 fixes by the reviewers' own counts: 링크·시제 410 · 흐름 283 · 중복 239 ·
  용어 234 · 콜아웃 180 · 문체 101 · 분량 66 · 제목 49 · 퀴즈 4 · 예제 2 · 사실 1.
- What changed in substance: later parts no longer re-teach from zero — a repeated error
  number or idea is acknowledged in one clause with a slide-level link and only the new
  part is read; cross-part links went from part covers to slides; terms were unified
  (스코프, 불변/가변 참조·빌림, 복제, 풀어 헤치기, 인덱스, 컬렉션, 스코프 스레드 …);
  "출력 N번째 줄" phrases that ignored the `$ …` line were replaced by quoted values.
- Count changes: +1 slide (p12-adapter-table) → 922; glossary 59 → 64 terms. Two examples
  extended so the slide's claim is shown, not asserted (ex/04/match_bind.rs,
  ex/08/str_methods.rs). One false sentence fixed (p13-attr-table on `#![…]`).
- Reordered inside chapters: p07-unit-struct, p07-refutable, p09-opt-iflet, p09-res-chain,
  p09-err-main-box, p12-closure-infer.
- Left on purpose: outline items without a slide (part 8 borrow+push E0502 and formatting
  recap; part 10 Iterator preview and Drop; part 11 `T: 'a`; part 12 performance note;
  part 16 never type / impl Trait elsewhere / shadowed prelude; appendix edition table);
  19 fixed terms that do not fit the glossary's last page; part 1 has quizzes only for
  chapters 4 and 6. Documentation-based sentences kept: Mutex blocks while locked,
  Rc/RefCell counting is not thread-safe, `sort` is stable, get_unchecked skips the bounds
  check, monomorphization makes one copy per type. Two were compile-checked in scratch
  (Error requires Debug → E0277; unimplemented!/unreachable! exist).
- Final verification: `make all` rc=0 (103 tests OK, 606 sources rustfmt-clean, 922 slides
  0 errors 0 notices, 1254 blocks verified 0 mismatches, 1336 cross-references all real,
  font check passes).
  `rsrun --all --check` three passes in a row, each exit 0 with 621 ✓ / 0 ✗ (from the log).
- index.html card and README say 922 slides and 64 glossary terms; history.md has the
  review-2 entry. Review-2 commits (ea97894b … wrap-up) are NOT pushed — ask the user.
- 2026-10-12: pushed at the user's request — origin/main = b70b21f6.

## Expansion to ≈1,870 slides (approved by the user 2026-10-12)

- User decisions: hard cap 2000 ("상한 2000장으로 해"), then "약 1,890장까지" — the full
  list: additions to parts 0–16 plus ten new parts. Everything else as before (std only,
  only running examples, one subagent at a time, Korean to the user, push only on request).
- Structure: appendix renumbered 17 → 27 (ids p27-*, ex/27, out/27). New parts 17–26 have
  skeleton files in deck/sections and are listed COMMENTED OUT in deck/order.txt; a part's
  lines are uncommented when its writer starts, so a non-skeleton `make deck` always
  passes at commit time. Contracts: deck/OUTLINE.md "Expansion". Budgets: deck/budget.txt
  (appendix target is 36 for now; raise to 45 when it grows). Writers' rules:
  deck/AUTHORING.md "Expansion (parts 17–26)".
- Batches (one writer at a time, ≤ ~45 slides per run; then one reviewer per part):
  17a 17b · 18a 18b · 19a 19b · 20 (two runs: ch1–3, ch4–5) · 21a 21b · 22 (two runs) ·
  23 (two runs) · 24 24b 24c 24d · 25a 25b (after 17–23 exist) · 26 (two runs) ·
  additions to 0–16 (orchestrator) · appendix + part-0 map + p16 hand-over (orchestrator).
- After each writer: orchestrator checks the report, runs non-skeleton `make deck`,
  `rsrun --check ex/NN` twice, commits that part. After all: links to parts that did not
  exist yet, glossary rows, index rows, `make all`, `rsrun --all --check` ×3, card/README
  figures, history entry, memory note, report, ask about push.
- To do at the end (do not forget): part 0's map table (p00, lists parts 1–16 + 부록) and
  the sentence "2부부터 16부까지가 문법"; p16-underscore's closing note ("본문을 마치며")
  → hands over to part 17; index.html card / README text (parts count, slide count,
  example count, new topics); REVIEW2.md target lists for the new parts.

### Expansion progress log
- 2026-10-12: cap raised (a23149db). Appendix renumbered, outline/budget/authoring
  written, 18 skeleton files created (commented out in order.txt).
- 17a written (chapters 1–3, 46 slides, 32 examples; `rsrun --check ex/17` ×3 all 32 ✓).
  Badges wanted but no key yet (add rows to data/features.tsv in one batch at the end,
  release-note lines in docs/releases.txt): ExitCode 1.61 → p17-out-exitcode; Stdin::lines
  1.62 → p17-in-lines; io::read_to_string 1.65 → p17-in-all; fs::read_to_string / fs::read
  1.26 → p17-file-read-to-string, p17-file-bytes. Plain-text forward mentions to link once
  17b exists: p17-out-write-vec (4장·6장), p17-file-read-to-string (5장), p17-file-with-name
  (6장: own error with file name), p17-file-total (6장), p17-file-table (4장); in-file
  links that can be added now: p17-out-flush → p17-file-io-result, p17-in-all →
  p17-file-table, p17-in-redirect → p17-file-total. New terms for the glossary: 표준 출력 /
  표준 오류 / 표준 입력, 버퍼(링), 얇은 main. Not evidenced: file closed on drop.
- 17b written (chapters 4–6, 47 slides, 30 examples) → part 17 = 93 slides, 62 examples;
  `rsrun --check ex/17` all 62 ✓ on repeated runs. First-half forward mentions linked.
  Badges wanted: fs::write 1.26 → p17-write-fs-write; File::create_new 1.77 →
  p17-write-open-options; io::Error::other 1.74 → p17-write-buf-drop-fail. New terms:
  경로, 구분자, 덧붙이기, 확장자, 항목(read_dir), 대체 글자. out/17/path_str.txt contains one
  U+FFFD ON PURPOSE (display() of a non-UTF-8 name) — not mojibake. Unlinked: p17-summary
  "다음" names 18부 in plain text. Part 17 still needs its review pass.
- data/features.tsv: +6 rows (fs-read-to-string 1.26, exit-code 1.61, stdin-lines 1.62,
  io-read-to-string 1.65, io-error-other 1.74, file-create-new 1.77), `make data-check`
  0 errors (42 badges). SINCE directives still to add on p17-file-read-to-string,
  p17-file-bytes, p17-write-fs-write, p17-out-exitcode, p17-in-lines, p17-in-all,
  p17-write-buf-drop-fail, p17-write-open-options — after the part-17 review finishes.
  Card/README "버전 표기 36건" must be recounted at the wrap-up.
- Part 17 review running (facts + style in one pass).
- Part 17 reviewed (facts + style, one pass): 3 wrong statements (two generalisations about
  `Path` methods, the intro's claim about every example), 2 wrong references, 23
  unevidenced sentences decided one by one (3 got evidence: twin ex/17/ask_no_flush.rs,
  typed bindings in path_parts.rs, one more head invocation; the rest reworded to what the
  capture shows or attributed to the std docs). 93 slides, 63 examples. Orchestrator then
  hardened ex/17/yes (stderr to a file, `cat` afterwards — order no longer depends on which
  `head` is installed) and attached 7 version badges (io-error-other row dropped: its
  slide is not about that function). The reviewer's nine lessons are in AUTHORING.md
  items 11–19. Doc-attributed sentences (read_dir order, BufReader/BufWriter rationale,
  Stdin's own lines/read_line) are from memory of the std docs — no docs on this machine.
- 2026-10-12 pushed at the user's request ("푸시하고 계속 진행해"): origin/main = dec8bacf.
  That commit (part-0 map lists part 17, p16 closing note hands over to part 17, card and
  README say 19부 1,015슬라이드 · 예제 684 · 캡처 705 · 퀴즈 80 · 버전 표기 41건, font
  subset re-embedded) was made in a separate git worktree (scratchpad/wt, branch pub-sync)
  because the part-18 writer was mid-edit in the main tree. LOCAL main is one commit
  behind: when no agent is running, restore the built deck file and
  `git merge --ff-only pub-sync`, then `git worktree remove` + delete the branch.
- From now on: a new part's commit also updates the part-0 map, the card/README figures
  and runs `make font` (new Korean glyphs in code need the DeckMono subset re-embedded;
  `make deck` alone keeps the old subset).
- Local main fast-forwarded to dec8bacf; worktree and branch pub-sync removed.
- 18a written (chapters 1–3: 수 더 깊이 · 비교와 정렬 · 해시와 맵 더; 45 slides, 35
  examples, `rsrun --check ex/18` all ✓ on 9 runs; +15 badge rows, data-check 0 errors,
  56 badges). Second half may use at most 43 slides (part ceiling 88). Second-half writer
  must adjust p18-intro's descriptions of chapters 4–6 and its "이 부의 화면" note, and
  p18-map-table's "다음 장 … 4장" can then be linked. New terms: 비트(연산자), 밀기(shift),
  플래그, 진법, 마스크, 빅/리틀 엔디언, 이진 탐색, 안정 정렬, 해시, 씨앗. Doc-attributed
  sentences on p18-ord-impl, p18-stable, p18-binary-search, p18-partition-point,
  p18-hash-same, p18-hash-broken (from memory of the docs). hash_broken.rs uses a
  fixed-seed hasher on purpose; binary_search.rs prints Err(2) for an unsorted vector
  (this toolchain's result — the slide says so).
- 18b written (chapters 4–6: 시간 · 프로세스와 환경 · 그 밖의 도구; 39 slides, 31 examples)
  → part 18 = 84 slides, 66 examples; `rsrun --check ex/18` all 66 ✓ on 7 runs; +23 badge
  rows (79 badges, data-check 0 errors). Unlinked plain text: p18-size-align "21부",
  p18-misc-table "다음" → 19부. New terms: 시간의 길이, 순간, 마감, 기준 시각, 환경 변수,
  프로세스, 자식 프로세스/부모, 종료 상태, 신호, 파이프, 정렬(alignment — second sense),
  패딩. For the reviewer: p18-cmd-status names "유닉스 계열" (lesson 16), p18-cmd-fail's
  PermissionDenied is this machine's, p18-env-vars makes a negative claim about the docs,
  p18-size-align cites the Reference; system_time relies on the machine clock (> 1.7e9 s).
  Part 18 still needs its review pass.
- Part 18 reviewed (facts + style): 사실오류 3 · 증거불일치 4 · 근거없음 9 · 순서 3 · 표기 4 ·
  퀴즈 1 · 코드 3; style 21. 84 slides unchanged; 5 examples changed (cmd_fail gained a
  signal-killed child → `code()` None shown; opt_slot binds before printing; opt_layers
  shows `?` after transpose; system_time runs both arms; hash_same comment). All
  doc-attributed sentences kept with attribution; 11 badges spot-checked. Lessons 20–28
  added to AUTHORING.md. Open: "손잡이" now also for Child/ChildStdin (style sheet says
  JoinHandle — accept as the general word for a handle); shift under -O not shown.
  Outline note: split_whitespace/strip_prefix are part 8's, not part 18's.
- Next: 19a (19_gen.html ch 1–3), 19b, review 19; then 20 …
- 19a written (chapters 1–3: 바운드 더 깊이 · 연관 타입과 GATs · 트레이트 객체 심화; 47
  slides, 55 examples of which 26 are compile errors; `rsrun --check ex/19` all 55 ✓ on 5
  runs; new E-codes E0119, E0271, E0107; +1 badge row trait-upcasting 1.86). Second half
  has 52 slides of head-room. p01-let-else no longer says "GATs 는 이 책에서 다루지
  않습니다" — links p19-gat-trait. For the 19 reviewer: p19-clone-box's orphan-rule reason
  is from memory of the Reference; "쌍둥이 파일" is this part's word for a variant file
  (decide whether to keep); 다운캐스트/업캐스트 transliterations; p19-gat-trait's gloss of
  `Self: 'a`; slides with 3–4 blocks (p19-cond-derive, p19-gat-two-err). Second-half
  writer: chapter 4's marker traits must acknowledge p19-overlap-fix (표시 트레이트);
  p19-const-array promises "6장", p19-dyn-table promises "5장"; adjust p19-intro items 4–6.
  Later (additions to 0–16): p10-ch2-quiz can link p19-impl-arg-err; p10-derive-table can
  point forward to p19-cond-derive; `*box` moving a non-Copy value is taught nowhere.
- 2026-10-12 pushed again at the user's request: origin/main = 0dbe67fb (parts 17, 18 with
  reviews, and the first half of part 19; card and map match the pushed deck: 1,146
  slides). 19b is being written.
- 19b written (chapters 4–6: 타입으로 설계하기 · 고차 바운드와 함수 · const 와 제네릭; 49
  slides, 64 examples) → part 19 = 96 slides (ceiling 99), 119 examples; `rsrun --check
  ex/19` all 119 ✓ on 5 runs; new E-codes E0392, E0631, E0080; +4 badge rows (84).
  Appendix error index grew to 31 slides. Two titles carry two E-codes, three carry a code
  plus a SINCE badge (new title shapes — reviewer to judge). Doc-attributed from memory:
  p19-hrtb-sugar (Reference: elision in Fn sugar), p19-fn-sizes (fn item types are
  zero-sized), p19-clone-box (Box<local> is local for the orphan rule). Unlinked:
  p19-const-kinds "다음" → 20부. Later (0–16 additions): p12-three-iters "collection gone
  after into_iter" vs Copy arrays; array `Copy` taught nowhere; p01-const-generics on the
  32 limit vs `Default` still stopping at 32 (p19-cg-from-fn).
- Part 19 review will run in two halves (96 slides, 119 examples is too large for one).
- Part 19 first half reviewed: 사실오류 2 · 증거불일치 8 · 근거없음 9 · 절단 3 · 순서 6 ·
  표기 12; style 18. Main finding: six "쌍둥이" captures came from separately written
  programs, not strict twins (line numbers in the notes did not match the shown source) —
  all rebuilt by copy-and-change. +1 slide (p19-any-static split off p19-any-basic), +1
  example (clone_box_vec_err.rs: the orphan-rule boundary shown by the compiler, E0117).
  Part 19 = 97 slides; budget raised 90 → 95 (ceiling 104). Lessons 29–35 in AUTHORING.md.
  p19-clone-box's title now ends "— E0117" (forced by the twin in range) → split it
  (lesson 31) during the second-half review. Later (0–16 additions): p10-orphan needs a
  forward clause to p19-clone-box; p10-ch2-quiz → p19-impl-arg-err; part 11 `T: 'a` slide
  should be linked from p19-gat-trait when it exists.
- 2026-10-12 pushed at the user's request: origin/main = 56a08d98 (part 19 written, first half reviewed; 1,197 slides).
- Part 19 second half reviewed: 사실오류 1 · 증거불일치 14 · 근거없음 15 · 절단 3 · 순서 7 ·
  표기 15 · 퀴즈 1 · 코드 6; style 34. Fourteen of nineteen twins were not strict — all
  rebuilt (22 examples changed, 0 added). +4 slides: p19-clone-box-orphan (in 19_gen),
  p19-cg-add-slice, p19-cg-array-default-err, p19-fn-return-box. Part 19 = 101 slides
  (budget 95, ceiling 104), 120 examples, deck 1,201. Kept as one slide by the reviewer's
  call: the two-code titles p19-valid-private (E0451 · E0616) and p19-sealed-err (E0277 ·
  E0603). Lessons 36–43 in AUTHORING.md. Doc-attributed from memory, still unchecked:
  p19-fn-sizes (fn item type is zero-sized and coerces to a fn pointer). Later (0–16
  additions): p10-orphan → p19-clone-box-orphan; p12-return-closure's "15부에서 봅니다" →
  also p19-compose; p05-const-fn has no badge (const-fn 1.31 exists now); p07-state-machine
  → p19-typestate; glossary must keep 타입 상태 (removed feature, p01-change) and 타입 상태
  패턴 apart.
- Part 20 skeleton split into 20_conc.html (cover, intro, ch 1–3) and 20b_conc.html
  (ch 4–5) so each writer run ends with a file that builds without the skeleton flag.
  Do the same for 22, 23, 26 before their first run.
- 2026-10-12 pushed at the user's request: origin/main = 070af746 (part 19 fully reviewed; 1,201 slides).
- 20a written (chapters 1–3: 채널 더 · 기다리기와 깨우기 · 공유 상태 설계; 43 slides incl.
  cover and intro, 33 examples, no compile-error example, 3 quizzes). The writer's session
  ended before its report reached the log, so the orchestrator verified from the tree:
  `make all` (no SKEL) rc=0 at 1,244 slides, `rsrun --check ex/20` ×3 = 33 ✓ / 0 ✗ each.
  Six badge rows added to data/features.tsv (recv-timeout 1.12, try-iter 1.15,
  compare-exchange 1.10, condvar-wait-while 1.42, atomic-fetch-max 1.45,
  mutex-clear-poison 1.77; data-check green, 90 badges). Part-0 map, card and README set
  to 22부 · 1,244슬라이드 · 예제 903 · 캡처 929 · 퀴즈 95 · 버전 표기 90건.
  For the 20b writer: plain-text forward mentions to link — p20-jobs ("스레드 풀은 4장에서"),
  p20-share-table ("다음 장" note), the intro's 4장/5장 bullets; the intro's "이 부의 화면"
  note says "1장부터 3장까지의 예제는" and "sleep 으로 잠드는 예제는 … 하나" — extend or
  correct it for chapters 4–5. Second half may use at most 34 slides (budget 70,
  ceiling 77). Unchecked by a reviewer: everything in 20a (review comes after 20b).
- 20b written (chapters 4–5: 스레드 풀 만들기 · thread_local 과 나눠 풀기; 26 slides, 18
  examples, 2 quizzes) → part 20 = 69 slides (budget 70), 51 examples, deck 1,270.
  Orchestrator re-ran: `make all` rc=0, `rsrun --check ex/20` ×3 = 51 ✓ / 0 ✗ each; the
  writer also ran each of the 13 threaded binaries 200× (one distinct output each).
  Error slides: E0277 (p20-pool-rx-share, p20-tl-static-err), E0499 (p20-split-mut-err) —
  no new codes. Badges +4 (available-parallelism 1.59, local-key-cell 1.73,
  local-key-refcell 1.73, int-div-ceil 1.73) → 94. Not evidenced, left out: thread_local!
  `const { }` init. Orchestrator edits in 20a: intro bullets unlinked again (book
  convention), p20-atomic-ordering "1장부터 3장까지의 예제는" → "이 부의 예제는".
  For the reviewer — sentences that rest on inference, not on a run: p20-pool-drop (warn:
  join before dropping the sender never finishes), p20-pool-together (warn: the
  `while let … lock().recv()` form keeps the gate closed), p20-pool-panic (no poisoning
  cascade), p20-pool-drop-waits (queued jobs drain before Err), p20-pool-table (no
  respawn), p20-split-mut-err (reading of the '1 labels), p20-pool-rx-mutex ("may differ
  per run"), p20-tl-with (LocalKey<RefCell>::take "same release" — badge regex matches
  only with_borrow); doc-attributed: p20-split-auto ×2. Determinism by argument:
  pool_panic, pool_together, pool_drop, split_auto (spawns 100 scoped threads), tl_init.
  New terms for the glossary: 스레드 풀, 일꾼, 스레드 지역 값, 올림 나눗셈(div_ceil).
  Later (0–16 additions): p15-many → p20-pool-why; p15-scope → p20-split-sum; p15-channel,
  p15-refcell-not-sync → p20-pool-rx-share; p15-arc-mutex → p20-pool-rx-mutex;
  p15-panic-join → p20-pool-panic; p15-choose → p20-split-table; p15-once-lock,
  p15-lazy-lock, p14-cell-copy → p20-tl-basic; p03-static → p20-tl-static-err;
  p06-option-take, p14-drop-order → p20-pool-drop; p06-split-at-mut, p12-windows-chunks →
  p20-split-fill; p12-closure-vec, p19-dyn-send → p20-pool-struct; 19b's closing note
  ("20부 동시성 심화는") can link #p20.
- Part 20 reviewed (one reviewer over both halves; the first reviewer run died without an
  edit and was restarted): 사실오류 0 · 증거불일치 2 · 근거없음 8 · 절단 0 · 순서 4 ·
  표기 4 · 퀴즈 1 · 코드 2; style 5. Chapters 1–3 came out close to clean, most defects sat
  in 20b and at the seam. Examples changed 3 (send_error, split_auto, tl_basic comment),
  none added; slides ±0 → part 20 = 69, deck 1,270, card numbers unchanged. Orchestrator
  re-ran: `make all` rc=0 (1,270장 · 오류 0 · 어긋남 0), `rsrun --check ex/20` ×3 =
  51 ✓ / 0 ✗ each; spot-check found one off-by-one the reviewer left (p20-split-auto
  "45번 줄" → 44). Term decisions: 일꾼(worker) is now glossed on p20-jobs (glossary row
  must target p20-jobs); 조각 = slice chunk only, pool components = 부품; thread-local =
  스레드 지역 값; div_ceil = 올림 나눗셈 / 올려 나누다 (no English gloss). Removed:
  p20-share-table's "다음 장" handover note (duplicated p20-pool-why). Lessons 44–51 in
  AUTHORING.md. Open: `Job` is spelled with and without `+ 'static` (jobs.rs vs pool
  files) and no capture shows they are one type; p20-park's "표(token)" collides with
  표 = table; std API "문서는 … 적습니다" sentences in the part were checked from memory
  only (no local API docs) — loosest are p20-atomic-ops and p20-cas. Later (0–19
  additions, beyond the 20b list): p15-mutex "Err … 다루지 않습니다" → p20-poison;
  p15-atomic "나머지 선택지 …" → p20-atomic-ordering; p15-arc-mutex → also p20-try-lock;
  p15-deadlock → p20-lock-order-safe; p15-channel-multi → p20-try-iter; p16-underscore,
  p17-out-lock → p20-guard-scope; p18-ordering → p20-atomic-ordering; p06-vec-two →
  p20-split-mut-err. Glossary candidates from 20a: 조건 변수, 바쁜 대기, 까닭 없는 깨어남,
  자리가 정해진 채널, 만나서 건네는 채널, 파이프라인, 독, 메모리 순서.
- The working tree carries an uncommitted two-line CSS change that is the user's, not this
  work's (`user-select: text` on main.prose in template.html, every deck/base/head.html
  and the built decks). Review commits stage the Rust deck WITHOUT that hunk; do not fold
  it in or revert it.
- 21a written (chapters 1–2: macro_rules! 심화 · 날 포인터와 메모리; 41 slides incl. cover
  and intro — ch 1 = 23, ch 2 = 16; 45 examples: 43 files + directory examples `export/`,
  `dollar/`; 14 compile-error files; 2 quizzes). order.txt: `21_low.html` uncommented by
  the orchestrator (the writer could not; its own green build was on a shadow copy).
  Orchestrator re-ran: `make all` rc=0 at 1,311 slides (one notice: part 21 under 80 % of
  budget), `rsrun --check ex/21` ×3 = 45 ✓ / 0 ✗ each; read alloc_drop, uninit_array,
  raw_parts, write_drop for soundness — no objection. New codes in out/: E0432, E0433,
  E0512 (61 distinct; the appendix lookup still lists 56 — orchestrator's part-27 job).
  Badges +12 → 106 (macro-literal 1.32, macro-rep-opt 1.32, macro-use-path 1.30, ptr-add
  1.26, ptr-offset-from 1.47, nonnull 1.25, std-alloc 1.28, drop-in-place 1.8,
  maybe-uninit 1.36, maybe-uninit-write 1.55, maybe-uninit-read 1.60, float-to-bits 1.20).
  Part-0 map, card and README set to 23부 · 1,311슬라이드 · 예제 966 · 캡처 998 · 퀴즈 99 ·
  버전 표기 106건.
  For the 21b writer: plain-text forward mentions to link — p21 cover chsub, p21-intro
  lead ("뒤의 두 장은 …") and its 3장/4장 bullets (bullets stay unlinked, book
  convention), p21-mem-table lead ("3장처럼 … 4장처럼 …"); the intro note is headed
  "1장과 2장의 화면" and covers only chapters 1–2 — extend or correct it; `Noisy` (a Drop
  type printing "  정리: 이름") is reused in four ch-2 examples; p18-size-align promises
  `#[repr(C)]` "21부에서 봅니다" → chapter 4 must cash it; words kept from earlier parts:
  자리를 잡다 / 돌려주다 (alloc / dealloc; "할당" is used nowhere), 배치 (layout), 종류
  (fragment specifier). Second half may use at most 47 slides (budget 80, ceiling 88).
  For the reviewer — inference rather than capture: p21-ambiguity ("1 other option"),
  p21-literal-commit (rests on one twin pair), p21-crate-bare (title generalises from two
  captures), p21-muncher (which arm took which item), p21-nonnull ("same look as
  Option<Box<u8>>"), p21-alloc (handle_alloc_error branch never ran — said on the slide);
  doc-attributed sentences were checked against doc.rust-lang.org by the writer, not
  against this toolchain's text: p21-ptr-rules table, p21-ptr-add, p21-ptr-end,
  p21-write-drop, p21-read-swap, p21-nonnull, p21-alloc, p21-uninit, p21-uninit-array,
  p21-raw-parts, p21-transmute-size, p21-export; "Miri catches some of these" is from
  memory. Loose badge labels: macro-rep-opt ("2015 에디션은 1.37"), std-alloc, ptr-add,
  macro-use-path. Left out for lack of evidence: expansion traces, `expr_2021`/edition
  differences, default recursion limit as a number, `vis`/`lifetime`/`ty`/`path`/`stmt`/
  `meta`, `from_raw_parts_mut`, `unsafe fn` bodies. New terms for the glossary: 메타변수,
  토큰, 토큰 한 덩이(token tree), 항목(item), 재귀 한도, tt 떼어 내기(tt muncher), 내부 규칙,
  별칭 규칙. Unchecked by a reviewer: everything in 21a (review comes after 21b).
- 21b written (chapters 3–4: 작은 Vec 만들기 · FFI, plus p21-wrap; 38 slides — ch 3 = 17,
  ch 4 = 20, wrap 1; 35 examples: 14 `vec_*.rs` + 20 files + directory `ffi_export/`;
  6 compile-error files, 2 compile-only warning files, 2 expected panics; 2 quizzes) →
  part 21 = 79 slides (budget 80), 80 examples, deck 1,349. order.txt: `21b_low.html`
  uncommented. Orchestrator re-ran: `make all` rc=0 (1,349장 · 오류 0 · 알림 0 · 어긋남 0),
  `rsrun --check ex/21` ×3 = 80 ✓ / 0 ✗ each; read all of MyVec/MyIter (vec_iter.rs
  1–185) for soundness — no objection (grow computes the new layout before touching
  state; into_iter's `mem::forget` on line 149 prevents the double free; both Drop impls
  free only when cap != 0, with layout(cap)). Badges +6 → 112 (unsafe-extern 1.82,
  unsafe-attr 1.82, extern-c-abort 1.81, union 1.19, ffi-c-types 1.64, static-mut-refs
  1.77). No new error codes in out/ (61). Card and README set to 23부 · 1,349슬라이드 ·
  예제 1,001 · 캡처 1,035 · 퀴즈 101 · 버전 표기 112건.
  The `vec_*.rs` files were GENERATED from `scratch/w21b/pieces/*.rs` by
  `scratch/w21b/pieces/mk.py` (git-ignored; lines 1–81 are byte-identical in all 14).
  The committed ex/ files are the source of truth; whoever changes MyVec edits the piece,
  rustfmts it, runs mk.py and re-runs rsrun on all vec_*.rs — or, without the pieces,
  applies the same change to every file and checks the chain with `diff`.
  Outline deviation: `Index` is not implemented; `v[i]` comes through
  `Deref<Target = [T]>` (reason on p21-vec-deref; intro bullet changed to match).
  21a edits by the 21b writer: p21-intro lead links, 3장/4장 bullets, note re-headed
  "이 부의 화면" and extended; p21-mem-table lead links.
  For the reviewer: p21-intro's second note ("돌려 보이지 않는 것 — 2장은 …") still speaks
  only of chapter 2; MyVec has no PhantomData (nothing about variance/drop check is on a
  slide); `main` could bypass the const assert with a struct literal (no example does);
  an element whose drop panics leaks the rest (not on a slide); doc-attributed sentences
  in 21b were checked from memory only — least sure: p21-no-mangle-2021 (the edition
  guide's reason for unsafe attributes); `ffi_export/main.rs` calls `calc::add` by path,
  which is also what makes rustc link the rlib (the slide presents it only as contrast);
  `div`'s field order was read from this machine's stdlib.h. Target-specific values
  printed: c_types (i32 4, i64 8), repr_c aligns [1, 2, 4].
  New terms for the glossary: FFI, 콜백, 기호(symbol), 매달린 포인터, 공용체. Sorting is
  "줄 세우다" in ch 4 so that 정렬 stays alignment.
  Later (0–20 additions): p16-unsafe-what says `static mut`, unsafe traits and `union`
  "은 이 책에서 다루지 않습니다" — now wrong, reword + link p21-static-mut / p21-union /
  p21-vec-send; p18-size-align "21부에서 봅니다" → #p21-repr-c; p19-gat-for-err →
  #p21-vec-into-iter; p01-ed2024 / p01-ed-table `unsafe extern` row → #p21-ffi-extern-2021
  (unsafe attributes and static mut references are not in part 1's list: could add
  #p21-no-mangle-2021, #p21-static-mut-ref); p16-extern-c → #p21-ffi-safe; p20-wrap's
  "다음" note → #p21. Unchecked by a reviewer: all of part 21.
- Part 21 first half reviewed (chapters 1–2, 41 slides): 사실오류 3 · 증거불일치 2 ·
  근거없음 11 · 절단 2 · 순서 3 · 표기 6 · 퀴즈 0 · 코드 2; style 5. All 13 chapter-2
  `unsafe` examples judged sound as written (no redesign; two `// 안전:` comments
  completed — raw_parts, write_drop — captures byte-identical). The three factual fixes:
  p21-pat's title (an `expr` capture CAN sit in pattern position when it is a literal —
  narrowed to `Some(_)`), p21-err-expanded's title (not every post-expansion error points
  at two places), p21-ptr-rules' table (now scoped to non-zero-sized access and says the
  docs call the precise rules undetermined). Titles narrowed to their example (ids
  intact): p21-op-err, p21-expr-unit, p21-pat, p21-ambiguity, p21-err-expanded,
  p21-crate-bare. Badge labels tightened: macro-rep-opt, macro-use-path. Slides ±0,
  examples ±0 → part 21 = 79, deck 1,349, card numbers unchanged. Orchestrator re-ran:
  `make all` rc=0 (오류 0 · 알림 0 · 어긋남 0), `rsrun --check ex/21` ×3 = 80 ✓ / 0 ✗.
  Term decisions: in part 21 a Rust item is "정의" (the word `item` shown once) and 항목
  stays "list entry" — do NOT add 항목(item) to the glossary; 토큰 한 덩이 (not 덩어리);
  야간판(nightly) as in part 1; dangling in ch 2 = "사라진 값을 가리키다", 매달린 포인터
  is defined in ch 3. Lessons 52–59 in AUTHORING.md. Vouched from memory only (no local
  API docs): every "문서는 … 적습니다" of ch 2; least sure — NonNull "may dangle",
  "precise rules not determined yet", the zero-sized exception, "Miri catches some".
  Open: p21-alloc-drop's title would be shown more directly by a leak twin; inner_top.rs
  and geom_hidden.rs carry a stale comment (sources not shown); a private twin
  (scratch/r21a/munch_end.rs) confirms p21-muncher's end cases but is not an example.
  For the 21b reviewer: p21-intro now asserts for ch 3–4 that no program the docs call UB
  is run and that the two compile-only files state their reason — confirm; p21-ptr-rules'
  caption asserts no example in the part reads/writes a zero-sized type through a
  pointer — confirm; p21-vec-zst uses past tense for the appendix (lesson 58);
  p21-vec-plan's "Miri" sentence drops the "일부"; screen ordinals: p21-vec-deref counts
  captures, p21-vec-send counts CODE boxes too (lesson 56). Later (0–20 additions): part
  13's two unglossed 항목 (item) → 정의 or one gloss.
- Part 21 second half reviewed (chapters 3–4 + wrap, 38 slides): 사실오류 4 · 증거불일치
  11 · 근거없음 8 · 절단 0 · 순서 6 · 표기 6 · 퀴즈 1 · 코드 5; style 2; badges 3 re-placed,
  2 labels tightened. No soundness defect: MyVec judged sound in every state walked
  (never allocated, after grow, grow panicking in layout, pop to empty, into_iter of an
  empty vector, half-consumed iterator, element whose drop panics → leak only), provided
  values come from `new()`; the struct-literal bypass of the const assertion is now said
  on p21-vec-zst. Every extern declaration checked against bionic's headers (sqrt,
  strlen, atoi, abs, strtol, qsort, div match; getenv returns `*const c_char` for C's
  `char *` — ABI-identical, left). Examples changed 17, all comment-level except
  ffi_export/calc.rs (`add` now takes/returns c_int); the 14 vec_*.rs were regenerated
  through scratch/w21b/pieces + mk.py (first confirmed to reproduce the committed files
  byte-for-byte); every capture byte-identical. Slides ±0 → part 21 = 79, deck 1,349.
  Orchestrator: p21-intro's ch-4 bullet "C 쪽에 내놓기" → "정한 이름으로 내놓기" (matches
  the new p21-ffi-export title); re-ran `make all` rc=0 (오류 0 · 알림 0 · 어긋남 0),
  `rsrun --check ex/21` ×3 = 80 ✓ / 0 ✗; spot-checked four new line readings — all match.
  Decision kept: p21-ffi-export says in three sentences that deleting main.rs line 11
  (the only use of the `calc` crate name) ends in a linker error, from a run that is not
  shown because the message carries temp names (scratch/r21b/ffi_nopath).
  Terms: `MyVec` 은/을/이/과, `MyIter` 는/를/가; 매달린 포인터 defined at p21-vec-new
  (acknowledges p11-dangle-scope); FFI, 콜백, 링커, 기호 glossed at first use; extern
  items are "선언". Glossary candidates: FFI, 콜백, 기호, 링커, 매달린 포인터, 공용체.
  Lessons 60–66 in AUTHORING.md. Vouched from memory only: every doc/Reference/C-standard
  sentence of 21b except p21-qsort (1.81) and p21-static-mut-ref (1.77), which are in
  docs/releases.txt; least sure p21-no-mangle-2021. Open: no twin shows the
  panicking-drop leak or the struct-literal bypass. Later (0–20 additions): REVIEW2.md
  calls p11-dangle-fix "the definition" of 매달린 참조 but the word is only on
  p11-dangle-scope — check other links to it.
- Part 22 skeleton split into 22_async.html (cover, intro, ch 1–3) and 22b_async.html
  (ch 4–5); OUTLINE.md heading and order.txt updated to match.
- 22a written (chapters 1–3: Future 를 손으로 · 실행기 키우기 · Pin; 37 slides incl. cover
  and intro — ch 1 = 10, ch 2 = 13, ch 3 = 12; 27 examples, 5 compile-error files
  (E0277 ×2, E0596, E0382, E0599), one expected panic (async_again); 3 quizzes). No
  `unsafe`, no threads, no clock, no external crate anywhere in ex/22. Orchestrator
  re-ran: `make all` rc=0 at 1,386 slides (one notice: part 22 under 80 % of budget),
  `rsrun --check ex/22` ×3 = 27 ✓ / 0 ✗ each; read selfref_move (the stale pointer goes
  only to `ptr::eq`; stack slot vs `Box` forces the addresses apart) and the final
  executor (exec5_yield.rs 63–120). No new error codes in out/ (61). Badges +7 → 119
  (future-trait 1.36, task-wake 1.51, pin-type 1.33, unpin-trait 1.33, phantom-pinned
  1.33, box-into-pin 1.63, pin-macro 1.68). Part-0 map, card and README set to 24부 ·
  1,386슬라이드 · 예제 1,028 · 캡처 1,063 · 퀴즈 104 · 버전 표기 119건.
  The chapter-2 chain exec1_block_on → exec2_queue → exec3_wake → exec4_join →
  exec5_yield and its twins (exec2_forget, exec3_forget, exec3_rc) were GENERATED from
  `scratch/w22a/pieces/*.rs` by `scratch/w22a/mk.py` + `spec.py` (git-ignored;
  re-running reproduces ex/22 byte for byte); `scratch/w22a/lines.py` prints the source
  line behind every "N번 줄" per slide. The first two chain steps are replacements, not
  pure extensions (the slides say so).
  For the 22b writer: reuse `ex/22/exec5_yield.rs` — 8–25 `Countdown(u32)` (wakes itself,
  Output = &'static str), 27–61 `Shared` + `Gate(Rc<RefCell<Shared>>)` (`open()`, stores
  the waker), 63–120 the executor (`type Task = Pin<Box<dyn Future<Output = ()>>>`,
  `type ReadyQueue = Arc<Mutex<VecDeque<usize>>>`, `TaskWaker { id, ready }`,
  `Executor { tasks: Vec<Option<Task>>, ready, log }`, `spawn(&mut self, impl Future<Output
  = ()> + 'static)`, `run(&mut self) -> usize` = number of unfinished tasks when the ready
  queue is empty — the hook for a tick counter), 122–174 `Fut`, `Join2`, `join2`, `after`,
  197–219 `yield_now`, `walk`, `race`. A task cannot spawn (`spawn` takes &mut self);
  there is no join handle; duplicate wake-ups print "(N번은 이미 끝났다)" and are skipped —
  a channel that wakes without `take()` will produce those lines. p22-intro's notes
  "이 부의 화면" and "돌려 보이지 않는 것" speak only of chapters 1–3; its 4장/5장 bullets
  are from the outline. Conventions: no `use std::future::Future;` (2024 prelude, said on
  p22-poll-ready), SeqCst, `pin!` + `as_mut().poll(&mut cx)` for hand polling, particles
  `Countdown` 은/을/이 · `Join2` 는/를/가 · `Gate` 는/를/가, 큐 (not 줄) for queue, "정해진
  순서". What happens to unfinished tasks when the executor is dropped is not shown —
  that is ch 4's "cancel = drop". Sourced but unused badge lines: poll_fn / task::ready! /
  IntoFuture 1.64, future::ready / pending 1.48. Second half may use at most 29 slides
  (budget 60, ceiling 66).
  For the reviewer — vouched from memory only (no local docs): p22-waker-count (who
  returns Pending must arrange a wake-up), p22-poll-after-ready, p22-exec-waker-rc,
  p22-pin-box, p22-pin-swap-err, p22-unpin-free, p22-async-size (WHY async futures are
  !Unpin — the writer's least sure), p22-ch3-table. Unsure: p22-self-ref's wording about
  the stale pointer (does not say "UB" flatly); p22-pin-macro's title ends "— E0382" though
  half the slide is the fix (lesson 31 tension); p22-exec-wake-run's "already finished"
  branch does not run in exec3_wake (said, links p22-join2-run); outline items without a
  slide of their own: `Pin<&mut T>`, "run until all done". Toolchain-specific values:
  async_size's three `true` lines, `{async block@…}` type names, a /rustc/… path in
  pin_new_err, the "`async fn` resumed after completion" panic text. New terms: 태스크
  (task; part 1 uses the word for old Rust's tasks), 깨우다/깨움 (wake), 고정하다 (pin).
  Later (0–21 additions): p16-block-on "까닭은 이 책에서 다루지 않습니다" → now false,
  link p22-poll-needs-pin; p16-async-why "여기까지만 봅니다" and p01-async "맛보기만"
  predate part 22; p21-intro "async 는 22부에서 잇습니다" → #p22; p21-wrap "다음" note →
  #p22. Unchecked by a reviewer: everything in 22a.
- 22b written (chapters 4–5: async 문법 더 · 타이머 없이, plus p22-wrap; 27 slides — ch 4 =
  17, ch 5 = 9, wrap 1; 21 examples, 6 compile-error files: E0373, E0382 ×2 in one file,
  E0038, E0277, and two code-less "future cannot be sent between threads safely";
  2 quizzes) → part 22 = 64 slides (budget 60, ceiling 66), 48 examples, deck 1,413.
  order.txt: `22b_async.html` uncommented. Orchestrator re-ran: `make all` rc=0 (1,413장 ·
  오류 0 · 알림 0 · 어긋남 0), `rsrun --check ex/22` ×3 = 48 ✓ / 0 ✗ each; grep finds no
  `unsafe`, thread, or clock in ex/22; read Timer/Sleep (timeout.rs 75–147): `advance`
  wakes while holding the RefCell borrow, which is fine because TaskWaker only touches
  the Mutex-guarded ready queue. Badges +3 → 122 (async-closures 1.85, asyncfn-prelude
  1.85, rpit-in-traits 1.75). No new error codes in out/ (61 distinct; the appendix
  lookup still lists 56). Card and README set to 24부 · 1,413슬라이드 · 예제 1,049 ·
  캡처 1,084 · 퀴즈 106 · 버전 표기 122건.
  Generated twins: pieces + `mk.py`/`spec.py` under `scratch/w22b/` (git-ignored);
  `lines.py` audits "N번 줄". Executor prefix: exec5_yield.rs 1–121 byte-identical in
  spawn_borrow_err, spawn_no_move, afit_run, afit_dyn_err, cancel_exec, select2;
  exec1_block_on.rs 1–36 in closure_async, closure_block, closure_asyncfn. Chapter 5
  deviates (said on the slides and in p22-intro): chan.rs drops `Gate` (unused → dead-code
  warning); sleep_ticks.rs is a twin step of the executor (field `timer`, `run`'s `else`
  calls `self.timer.advance()`); timeout.rs = tick executor + Timer/Sleep + channel +
  Select2; timeout_nodrop.rs = timeout.rs minus `impl Drop for Sleep`.
  22a edits by the 22b writer (p22-intro only): 4장/5장 bullets, both notes extended to
  the whole part.
  For the reviewer — inference rather than capture: p22-select2-run ("the .await drops
  Select2 when it yields"), p22-spawn-borrow ("the block took `waiting` by value without
  move"), p22-async-closure (key sentence), p22-not-send (key head generalises from one
  example + the compiler's note); attributed: p22-cancel-drop ("Future has only poll" —
  from memory), p22-afit-dyn / p22-not-send-fix / p22-runtime (AFIT announcement,
  docs/afit-2023.txt lines 70, 76, 84–85 — no FACT rows for the dyn/Send sentences),
  p22-runtime (two rows are "알려져 있다" with no source, said in the note). Four-box
  slides: p22-afit-send, p22-tick-run, p22-timeout. afit_dyn_err's note cites line 124,
  visible only in the capture's excerpt; p22-tick-run cites "exec5_yield.rs 의 103번 줄"
  inside a note= attribute; afit_send_fixed.rs changes a comment line as well as the
  parameter line. p22-ch3-table's note "1장부터 3장까지의 예제에는 unsafe 가 없습니다" is
  true but narrower than the part. The `async_fn_in_trait` lint is avoided (non-pub
  trait), not mentioned. Toolchain-specific: the Rc-across-.await error has no code and
  `drop(shared)` before the .await still fails; E0038's "because method `fetch` is
  `async`"; two E0382 in closure_block. New terms: async 클로저, 취소 (cancellation), 틱.
  Unchecked by a reviewer: all of part 22.
- Part 22 reviewed (one reviewer over both halves, 64 slides): 사실오류 4 · 증거불일치 1 ·
  근거없음 7 · 절단 0 · 순서 0 · 표기 4 · 퀴즈 0 · 코드 1; style 1. Slices, "N번 줄", quizzes
  and all 71 external link targets came out clean. The one code defect: cancel_exec.rs
  had two tasks awaiting clones of one `Gate`, whose single Waker slot the second waiter
  overwrote (a lost wake-up had the gate ever opened) → each task has its own gate;
  p22-waker-stored now states the one-waiter capacity. Executor, Join2, Select2,
  Chan/Recv, Timer/Sleep walked for lost wake-ups, RefCell double borrows and
  termination — judged correct (`Chan` has the same one-receiver limit, never violated,
  not stated). Titles fixed: p22-pin-swap-err ("Unpin 이 아닌 값은 …"), p22-self-ref
  ("옛 자리를 가리킨다"). Examples changed 15 through the pieces + mk.py of scratch/w22a
  and scratch/w22b (a shared comment in the executor; cancel_exec's main); line counts
  unchanged, every capture byte-identical. Slides ±0 → part 22 = 64 (budget 60, ceiling
  66), deck 1,413, card numbers unchanged. Orchestrator re-ran: `make all` rc=0 (오류 0 ·
  알림 0 · 어긋남 0), `rsrun --check ex/22` ×3 = 48 ✓ / 0 ✗; prefix exec5_yield 1–121
  still byte-identical in its six files; three new line readings spot-checked — match.
  Kept by the reviewer's call: p22-pin-macro as one slide with its "— E0382" title.
  Vouched from memory only: all contract sentences (Poll::Pending, Future::poll's Panics
  section, Wake vs RawWaker, Pin, Unpin, DerefMut for Pin, new_unchecked); not sure of the
  exact docs wording: p22-async-size's lead. Sourced in docs/afit-2023.txt: p22-afit-dyn,
  p22-not-send-fix, p22-runtime row 1. Lessons 67–72 in AUTHORING.md. Open:
  p22-closure-block's second E0382 labels are read only as "같은 꼴"; p22-box-stays' key
  is unqualified ("Unpin 이 아니면"); p22-pin-swap-err acknowledges E0596 through
  p14-rc-immutable, whose headline differs. Glossary rows to add: 태스크, 깨우다/깨움,
  고정하다, 취소, 틱, async 클로저. Later (0–21 additions): as listed under "22a written",
  plus p08-vecdeque's title calls a queue "줄" where part 22 says 큐; p22-wrap's "23부"
  mention becomes a link when part 23 exists.
- Part 23 skeleton split into 23_cargo.html (cover, intro, ch 1–3) and 23b_cargo.html
  (ch 4–5); OUTLINE.md heading and order.txt updated to match.
- 23a written (chapters 1–3: 워크스페이스 · features · build.rs 와 컴파일 때 정보; 35 slides
  incl. cover and intro — 11 per chapter; 18 examples: 17 directory + env_missing.rs; six
  end in an error (Cargo's own in ws, ws_more ×2, feat_fixed; rustc's in feat_gated E0425,
  inc, env_missing), three carry a deliberate warning (ws_noresolver, feat_typo,
  build_cfg_nocheck); 3 quizzes). Orchestrator re-ran: `make all` rc=0 at 1,448 slides
  (one notice: part 23 under 80 % of budget), `rsrun --check ex/23` ×3 = 18 ✓ / 0 ✗ each
  (a full check takes about 45 s); no `target/` or `Cargo.lock` under ex/23. No new error
  codes in out/ (61). Badges +13 → 135 (cargo-run-ws 1.30, lockfile-v4 1.78,
  resolver-field 1.51, resolver-3 1.84, ws-inherit 1.64, cargo-new-inherit 1.71,
  cargo-new-member 1.75, cargo-all-features 1.13, check-cfg-rustc 1.79, check-cfg-cargo
  1.80, build-rerun-if-changed 1.6, build-rustc-env 1.19, cargo-directive-colons 1.77).
  Part-0 map, card and README set to 25부 · 1,448슬라이드 · 예제 1,067 · 캡처 1,114 ·
  퀴즈 109 · 버전 표기 135건.
  The captures depend on the caller's environment: `GREETING` and `WITH_BANNER` must be
  UNSET where rsrun runs (rsrun strips only CARGO*/RUST*), or four captures change.
  rsrun facts the writer designed around (nothing patched): only RUN lines that START
  with `cargo ` or `rustc ` get the 120 s timeout — `X=1 cargo …` and `cd x && cargo …`
  get 10 s; the sandbox is `scratch/run/<basename>`, so directory names must be unique;
  rsrun sets CARGO_TARGET_DIR to `<sandbox>/target` (same as Cargo's default for a
  workspace — checked in a probe with the variable unset); RUN files spell `-q` unless
  Cargo's own lines are the evidence and never `--offline` (rsrun sets
  CARGO_NET_OFFLINE); `#@ exit: 101` for Cargo failures; twins are separate directories
  (a `sed -i` inside a RUN gave a timing-dependent rebuild); `cargo::warning` is replayed
  from cache, so it is no evidence that build.rs ran; never print a hashed `target/` path
  (use a glob).
  For the 23b writer: `ex/23/ws` (text-kit lib with `shout` + one unit test, and `app`)
  suits "testing a binary through its lib" — copy it under a new name; p23-intro's note
  "이 부의 화면" is scoped "1장부터 3장까지"; plain-text forward mentions to link —
  p23-ws-two-bins ("한 패키지에 실행 파일이 여럿인 경우는 5장에서"), p23-check-cfg
  ("`[lints]` 표는 5장에서" — its warning prints a ready-made `[lints.rust]
  unexpected_cfgs` table); words: 워크스페이스, 멤버, 의존성 / path 의존성, 기본 기능, 빌드
  스크립트, 묶음 (test group), "뿌리의 Cargo.toml", `Cargo.lock` (not 잠금 파일 — 잠금 is
  the mutex word). Second half may use at most 31 slides (budget 60, ceiling 66).
  For the reviewer — captures with Cargo progress lines whose content rests on Cargo's
  caching: ws, ws_more (three `Compiling` lines, order under -j1), ws_noresolver,
  ws_inherit, feat_ws (`cargo build` prints exactly `Compiling plain` — the unification
  evidence), build_env (run 2 prints no `Compiling`; the rebuild after `echo purple >>
  colors.txt` rests on colors.txt's mtime being newer than the build-script output —
  judge whether a coarse-mtime filesystem could make it flaky), build_cfg_norerun (stale
  output rests on Cargo's default rerun rule). Attributed from memory (no local Cargo
  book): p23-ws-resolver ("virtual workspace"), p23-ws-lock (`version = 4` is the
  lock-file format number), p23-feat-unify (the additive-features advice), p23-build-rs
  (Cargo compiles and runs build.rs before the package). Unsure: p23-feat-unify's title
  generalises from one workspace; p23-ws-p calls the second test group the doc-test group
  "13부에서 본 차례대로라면"; p23-env-missing merges the `env!` error and `option_env!`
  on one four-box slide; `cd` and `rm` appear in captures for the first time in the book;
  ws_more's capture lines 1–6 are shown on no slide; feat has six cargo commands.
  Toolchain-specific text: `Finished \`dev\` profile [unoptimized + debuginfo]`,
  `version = 4`, "and 34 more", nightly doc URLs in rustc warnings, "(os error 2)".
  Later (0–22 additions): p02-cargo-toml "`[dependencies]` … 늘 빈칸" and p13-crates-io
  "그 칸이 늘 비어 있습니다" → acknowledge p23-ws-path-dep; p13-cargo-toml says
  `[workspace]` and profiles are named only → link p23-ws-root (and ch 5 when written);
  p16-macro-std shows `concat!` but never reads it; p22-wrap's "23부" → #p23.
  Unchecked by a reviewer: everything in 23a.
- 23b written (chapters 4–5: 시험 더 · 실행 파일 여러 개와 프로필, plus p23-wrap; 28 slides —
  ch 4 = 14, ch 5 = 13, wrap 1; 19 directory examples; 2 quizzes) → part 23 = 63 slides
  (budget 60, ceiling 66), 37 examples, deck 1,476. order.txt: `23b_cargo.html`
  uncommented. Orchestrator re-ran: `make all` rc=0 (1,476장 · 오류 0 · 알림 0 · 어긋남 0),
  `rsrun --check ex/23` ×3 = 37 ✓ / 0 ✗ each (about 94 s per run); no `target/` or
  `Cargo.lock` under ex/23. New error code in out/: E0453 (62 distinct; the appendix
  lookup still lists 56). Badges +6 → 141 (cargo-bin-exe 1.43, test-threads 1.12,
  test-threads-one 1.33, default-run 1.37, custom-profiles 1.57, lints-table 1.74). Card
  and README set to 25부 · 1,476슬라이드 · 예제 1,086 · 캡처 1,147 · 퀴즈 111 ·
  버전 표기 141건.
  Environment: `UPDATE_GOLDEN` must be UNSET where rsrun runs (with `GREETING` and
  `WITH_BANNER`), or test_golden_changed's first command passes. rsrun does NOT add
  `--test-threads=1` to RUN-file `cargo test` lines (only single-file `//@ test`);
  the RUN files use `-q` (dots) and spell the pin only where named lines could reorder.
  Four optimized builds in the part (prof, prof_keys ×2 profiles, prof_inherit).
  Machine-specific on screen: prof_abort's `Aborted` + exit 134; `ls` error text + exit 2.
  23a edits by the 23b writer: p23-intro's note (scope widened to the part, `(tid)`,
  twin wording), links in p23-ws-two-bins and p23-check-cfg.
  For the reviewer: p23-intro's lead still describes chapters 1–3 only ("패키지가 여럿인
  프로젝트와, 컴파일하는 동안 정해지는 것들"); p23-test-threads' title ("이름 순으로 선다")
  rests on one three-test run + libtest's help text + the 1.33 note; four-box slides
  p23-bin-dir (carries src/bin AND default-run), p23-test-common, p23-test-bin-lib,
  p23-test-shared, p23-lints-forbid; p23-test-common-rs translates Cargo's "in default-run
  packages" literally (collides with ch 5's `default-run` key; `-p wordbox` gives a
  cleaner message); p23-prof-abort does not say who prints `Aborted`; p23-prof-custom's
  inheritance claim rests on the prof_inherit twin; p23-lints-cfg re-shows a mid-diagnostic
  slice (lines 10–12) of build_cfg_nocheck.txt; `sed -n "/…/,/…/p"`, `grep -E`, `cd`,
  `rm`, `find … | sort` appear in captures — each glossed once?; from memory (no local
  Cargo/libtest docs): p23-prof-overflow ("프로필은 컴파일 설정 한 벌에 붙인 이름"),
  p23-examples (what examples/ is for), p23-lints-deny ("경고마다 수준이 있고");
  inference worded as reading: p23-lints-deny (`-D unused-variables` is what Cargo
  passed), p23-test-shared warn, p23-prof-abort warn (BufWriter), p23-test-golden-fail
  warn. Terms: 기준 파일 (golden file), 프로필 (first gloss in the book), 수준 (lint level),
  시험 대상 / 실행 파일 대상 (target), 조각 (expected substring), 도우미; a lint is "경고"
  (part 13's word; p02-clippy says "검사 도구(lint)"); Cargo's examples are "examples/ 의
  프로그램", never "예제". Left out: any multi-threaded capture, `[workspace.lints]`,
  `[lints.clippy]`, opt-level, speed/size claims, `--nocapture`.
  Later (0–22 additions): p03-overflow-release "cargo 에서도 같습니다" → p23-prof-overflow;
  p13-cargo-toml (profiles named only; "예제" for Cargo's examples) → p23-prof-keys;
  p13-test-should-panic → p23-test-expected; p13-test-integration → p23-test-common;
  p13-attr-allow → p23-lints-deny. Unchecked by a reviewer: all of part 23.
- Part 23 reviewed (one reviewer over both halves, 63 slides): 사실오류 1 · 증거불일치 2 ·
  근거없음 6 · 절단 1 · 순서 2 · 표기 5 · 퀴즈 0 · 코드 1; style 2. Chapters 2, 3 and 5 came
  out close to clean; most defects sat in chapter 1, the intro and p23-test-threads.
  Examples changed 6 (no .rs touched): `members` reordered to app-first in ws,
  ws_noresolver, ws_inherit, ws_more so that "text-kit compiled first" is evidence of
  dependency order (lesson 74); test_helpers and test_common_rs now run
  `cargo test -q -p wordbox --test common` so Cargo's message says "in `wordbox` package"
  instead of "in default-run packages" (lesson 77). Captures changed through rsrun:
  ws_inherit (1 line), test_helpers (2), test_common_rs (1). Slides ±0 → part 23 = 63
  (budget 60, ceiling 66), deck 1,476, card numbers unchanged. Orchestrator re-ran:
  `make all` rc=0 (오류 0 · 알림 0 · 어긋남 0), `rsrun --check ex/23` ×3 = 37 ✓ / 0 ✗;
  no `target/` or `Cargo.lock` under ex/23. All 19 badge rows checked against
  docs/releases.txt — unchanged. All twin pairs `diff -r` strict. p23-intro now says:
  each `$` line starts at the sandbox root, `VAR=v` lasts one line, GREETING ·
  WITH_BANNER · UPDATE_GOLDEN are unset elsewhere, and what a twin directory is.
  Kept unsplit: the six four-box slides. Vouched from memory only: "virtual workspace",
  the additive-features advice, what examples/ is for, "프로필은 컴파일 설정 한 벌에 붙인
  이름"; p23-prof-abort's "the shell prints Aborted" rests on a scratch probe. Lessons
  73–80 in AUTHORING.md. Open: p23-build-rerun's capture does not isolate the
  `rerun-if-changed` line (colors.txt is inside the package; the slide admits the default
  rule is not shown — a twin editing an unlisted file would isolate it); p23-ws-p's
  "13부에서 본 차례대로라면" is still an inference; test_common_rs/tests/count.rs line 1
  comment says "common/mod.rs" (strict twin, shown on no slide); build_env could flake
  only on a filesystem with 1-second mtimes. Glossary candidates: 워크스페이스, 멤버,
  path 의존성, 기본 기능, 빌드 스크립트, 프로필, 기준 파일, 수준, 시험 대상. Later (0–22
  additions, beyond the 23a/23b lists): p00-normalize says "세 가지뿐" but rsrun also
  normalises doctest times, and it does not say that a directory example runs each `$`
  line from the root; the appendix error index needs E0453.
- Part 24 is written project by project, each followed at once by its own review
  (write wc → review wc → write grep → …), so that review lessons reach the next writer.
- 24 project 1 written (part cover, p24-intro for all four projects, chapter 1 낱말 세기
  wc; 37 slides — cover 1, intro 1, chapter 35 incl. its cover; 10 directory examples:
  the eight-step chain wc1_count → wc2_chars → wc3_files → wc4_total → wc5_flags →
  wc6_error → wc7_tests → wc8_final and the E0277 twin pair wc7_array / wc7_slice; 1
  quiz). order.txt: `24_proj.html` uncommented. Orchestrator re-ran: `make all` rc=0 at
  1,513 slides (one notice: part 24 under 80 % of budget), `rsrun --check ex/24` ×3 =
  10 ✓ / 0 ✗ each (about 32 s per run); no `target/` or `Cargo.lock` under ex/24; no
  `unwrap`/`expect`/`panic!`/`unsafe` in main.rs or in lib.rs outside `mod tests`; the
  final capture's totals add up. No badge rows added (141); no new error codes (62).
  Part-0 map, card and README set to 26부 · 1,513슬라이드 · 예제 1,096 · 캡처 1,174 ·
  퀴즈 112 · 버전 표기 141건.
  Generated: `scratch/w24a/mk.py` (+ `pieces/`, `twins.py`; git-ignored) — lib.rs is ONE
  master file with marker lines `//@@ a+` / `//@@ a-b`, step k gets the lines whose
  range contains k, so the twins are strict by construction; data-file bytes are Python
  literals in mk.py; `lines.py` audits "N번 줄"; `probe.py DIR` runs a scratch directory
  through rsrun's sandbox without touching out/.
  This program's definitions (stated on p24-wc-rules, each tested): line = number of
  `\n` bytes; word = maximal run between ASCII whitespace on bytes; character =
  `String::from_utf8_lossy(bytes).chars().count()`; columns `{:>5}` in the fixed order
  lines · words · chars · bytes; total line when two or more names were given; exit 0 /
  1 (something unreadable) / 2 (bad invocation); `-` alone stays a file name; whole-input
  reads, no speed claim. bad.bin (invalid UTF-8) is created inside the RUN, never
  committed.
  For the next project writers: slide prefix `p24-wc-…` and directories `wcN_…` are
  taken — use `p24-grep-…` / `grepN_…`, `p24-calc-…` / `calcN_…`, `p24-kv-…` /
  `kvN_…`; chapter layout = reuse table → finished program in use → steps table → steps
  (code slice, then capture) → tests → rules table → files table → quiz → "더 해 볼 것"
  with a "다음" note; code-box captions start with the step directory name and "N번 줄"
  always means that step's file; RUN conventions: `cargo build -q` once, then
  `./target/debug/<name>`; stdin only through `|` or `<` on that line; `cargo test -q
  --lib` / `--test <file>` rather than bare `cargo test` except once at the end; a
  whole-file OUT of a test capture ends on a blank line — slice it; decide the final
  program first and tag lines by step; put the unit-test module at the bottom so earlier
  line numbers stay stable; let `run` take its final signature the first time it appears
  (introduce the config struct BEFORE `run` exists — the writer's own regret). p24-intro
  lists chapters 2–4 as plain text from the outline (no glosses for tokenizer / parser /
  REPL — each writer corrects their own line) and its "이 부의 화면" note is scoped to
  chapter 1 ("1장의 화면은…", "1장의 예제는 환경 변수를 읽지 않습니다") — widen it per
  project. p24-wc-more's "다음" note names chapter 2 in plain text.
  For the reviewer: statements not shown by a capture — p24-wc-count (what
  `is_ascii_whitespace` answers; five bytes tested, vertical tab not mentioned),
  p24-wc-count-space / p24-wc-chars-bad (Unicode names; "\xff/\xfe never appear in
  UTF-8"), p24-wc-run ("read_to_end is the byte-side sibling of read_to_string"; `mut` on
  stdin attributed to p17-file-open), p24-wc-stdin-fail (the `?` after `writeln!` is
  never exercised — said, links p17-out-writeln-fail), p24-wc-test-files ("ran at the
  package root" inferred), p24-wc-test-array ("converted" read off two outcomes),
  p24-wc-test-all (which group is which inferred from counts), p24-wc-error-test (the
  `else { panic! }` arm never runs — said). Unsure: key head of p24-wc-flags-row and
  title of p24-wc-chars-bad rest on few cases; p24-wc-test-array has four boxes;
  p24-wc-rules and p24-wc-summary are two tables in a row; prose says "첫 / 셋째 단계"
  while tables say "1단계 / 3단계"; quiz ① links a step-5 capture though it asks about
  "이 장의 wc". Machine-specific on screen: os errors 2 and 21, `od`'s format, the shell
  accepting `< data` for a directory, the E0277 diagnostic with a /rustc/… path. New
  terms: 전각 빈칸 (U+3000), 대체 문자 (U+FFFD), 쪽 넘김 (form feed); first uses in the
  book: `String::from_utf8_lossy`, `Read::read_to_end`, `u8::is_ascii_whitespace`, slice
  `split` with a closure, `od -An -tx1`. Badge wanted but not sourced:
  `is_ascii_whitespace`.
  Later (0–23 additions): p17-tool-wc-count runs this machine's `wc memo.txt` in its
  capture and says "다른 것은 칸의 폭뿐" — relabel or drop; part 17's wc reads with
  `read_line` into a String (non-UTF-8 input not shown) → could point to
  p24-wc-bad-bytes; p17-tool-test's key ("run and main left untested") → p24-wc-test-run /
  p24-wc-test-cli; p13-libbin-lib, p23-test-bin-lib → p24-wc-main; p23-wrap's "24부" → #p24.
  Unchecked by a reviewer: all of 24 project 1.
- 24 project 1 reviewed (38 slides after the review): 사실오류 6 · 증거불일치 3 · 근거없음 11 ·
  절단 0 · 순서 1 · 표기 6 · 퀴즈 1 · 코드 1; style 8. The writer's numbers and line
  references were all correct; the defects were over-general frame sentences, mechanism
  words, unread capture rows, and one hole: the rules table promised exit codes 0/1/2
  but a non-UTF-8 argument panics inside `env::args()` (exit 101). Kept as the book's
  taught idiom and SHOWN: new slide p24-wc-args-bad (wc3_files' RUN gained
  `./target/debug/wc "$(printf 'caf\351.txt')"` with `#@ exit: 101`), a rules-table row
  "받지 못하는 것", exercise 9 (`args_os`). Also: a vertical-tab assertion in the step-1
  test (the word rule's one surprising edge — `is_ascii_whitespace` is true only for
  09 0a 0c 0d 20), CODE boxes for the `use` lines added at steps 3 and 6, "N단계"
  everywhere, 대체 글자 (part 17's word, not 대체 문자), quiz questions name their step.
  Generator used (pieces/lib.rs +2 lines, RUN.3 +2 lines); chain sizes re-verified;
  only out/24/wc3_files.txt changed (+6 lines). Slides +1 → project 1 = 38, part 24 = 38,
  deck 1,514. Orchestrator re-ran: `make all` rc=0 (오류 0 · 어긋남 0; the budget notice
  stays), `rsrun --check ex/24` ×3 = 10 ✓ / 0 ✗; card and README set to 1,514슬라이드 ·
  캡처 1,175. This entry supersedes the "24 project 1 written" entry where they differ
  (slide count, wc3's RUN, lib.rs line counts 61/84/131/147/254/288, "0.00s only").
  Edges probed and consistent with the rules: empty argument, `--` ("모르는 옵션 --"),
  flag after path, repeated flag, six-digit number (column widens — said in the rules
  cap), whitespace-only file, CRLF, lone \r, two unreadable files, unreadable file as
  the only argument, stdin + flags, stdout write error (EPIPE → "wc: Broken pipe", 1;
  not shown), stderr write error (`eprintln!` panics, 101 — one sentence). Lessons
  81–93 in AUTHORING.md. Open: `--help` prints "모르는 옵션 --"; the write-error path
  is an exercise (a failing-`Write` test would evidence it); p24-wc-test-array is still
  four boxes. p24-intro's "이 부의 화면" note is still scoped to chapter 1 and now also
  carries `(tid)` and the RUST_BACKTRACE caveat — each project writer widens it.
  Edges the remaining projects must probe first — grep: non-UTF-8 pattern / file names,
  invalid UTF-8 inside a file (`lines()` returns Err mid-file: decide and show), `-`,
  `--`, an empty pattern, exit 1 "no match" vs "unreadable"; calc: integer overflow and
  division by zero must not panic, deep nesting overflows the recursive-descent stack
  (state a limit), error positions in bytes or chars for Korean input, empty line and
  EOF in the REPL; kv: keys/values containing the separator or a newline, a missing or
  corrupt store file, `lock().unwrap()` poisoning, worker-thread output order fixed.
  Later (0–23 additions): the four part-17 tools use `env::args()` and never say a
  non-UTF-8 argument panics → p17-path-to-str or p02-args could point to
  p24-wc-args-bad; p17's wc counts words with `split_whitespace` (p24-wc-count-space now
  says the rule differs). Glossary candidates: 전각 빈칸, 대체 글자, 쪽 넘김, 깨진 바이트.
- 24 project 2 written (chapter 2 미니 grep; 41 slides incl. its cover; 9 directory
  examples: the eight-step chain grep1_match → grep2_config → grep3_search → grep4_run →
  grep5_number → grep6_count → grep7_tests → grep8_final and the E0106 twin grep3_nolife;
  1 quiz) → part 24 = 79, deck 1,555. order.txt: `24b_proj.html` uncommented.
  Orchestrator re-ran: `make all` rc=0 (오류 0 · 어긋남 0; the budget notice stays),
  `rsrun --check ex/24` ×3 = 19 ✓ / 0 ✗ each (61–69 s per run for both projects); no
  `target/`, `Cargo.lock` or `bad.bin` under ex/24; no `unwrap`/`expect`/`panic!`/
  `unsafe` in main.rs or in lib.rs above `#[cfg(test)]`. No badge rows added (141); no
  new error codes (62). Card and README set to 1,555슬라이드 · 예제 1,105 · 캡처 1,203 ·
  퀴즈 113.
  Generated: `scratch/w24b/mk.py` (+ `pieces/`, `twins.py`, `probe.py`, `lines.py`,
  `links.py`, `slices.py`; git-ignored) — same marker mechanism as w24a plus a
  72-column check (wide characters count 2) and an "only my prefix" guard; the SLIDE file
  was assembled from `scratch/w24b/sec/01…06.html` by `asm.py` — edit 24b_proj.html
  directly from now on (the pieces are stale after the first direct edit).
  This program's rules (stated on p24-grep-rules, each tested): match =
  `line.contains(pattern)`, plain text, no regex; an empty pattern matches every line, a
  missing pattern is a usage error; a line = what `str::lines()` yields (ends at \n or
  \r\n, terminator not part of the line — so CRLF input comes out with \n only; a lone
  \r does not split); row = `[name:][number:]body`; `-i` = ASCII only
  (`to_ascii_lowercase` on both sides); `-v` inverts after `-i`; `-n` = 1-based number
  in the original text; `-c` = one count line per input, `-n` then does nothing; name
  cell only when two or more names were GIVEN; flags anywhere / joined / repeated, `--`
  ends flags, lone `-` is positional; whole-input read as `String`, so any invalid UTF-8
  makes that whole input unreadable; exit 0 selected / 1 none / 2 usage error or anything
  unreadable, and 2 outranks 0 and 1 (pure fn `exit_code`); a write failure makes `run`
  return Err (shown by a failing `Write` impl `Broken` in tests/run.rs), main prints
  `grep: reason` and exits 2.
  24_proj.html edits by this writer: p24-intro's 2장 item and "이 부의 화면" note
  (widened to chapters 1–2), p24-wc-more's "다음" link.
  For the reviewer: not shown by a capture — p24-grep-main warn (the non-UTF-8-argument
  panic is acknowledged by link to p24-wc-args-bad, probed only in scratch), p24-grep-run-out
  / p24-grep-stdin second notes (order of -i then -v; the \n comes from writeln!),
  p24-grep-bad-utf8 (that main's Err arm printed the nameless notice), p24-grep-test-write
  ("쓸 줄이 없으면 쓰기를 부르지 않습니다" inferred from Ok(1)), p24-grep-rules row
  "읽거나 쓰지 못한 표준 입출력" (write failure → exit 2 through the binary is not
  captured; stderr-unwritable `eprintln!` panic not probed), p24-grep-config-dash (why
  `--help` gives "모르는 옵션 --"), p24-grep-quiz (answers rest on the tail of
  grep8_final.txt, which no slide shows). Unsure: four boxes on p24-grep-number and
  p24-grep-count; p24-grep-rules has 16 rows; p24-grep-bad-utf8's title rests on one
  file; step 4 is large (10 slides off one capture); `write_hits` gains its `name`
  parameter at step 5 (+45 −5, not purely additive); grep3_nolife's diff is +1 −4 because
  rustfmt joins the header (said on the slide), and one of its capture lines is 140
  columns; read_error_keeps_path_and_kind duplicates chapter 1's test. Machine/toolchain
  text on screen: os errors 2 and 21, "stream did not contain valid UTF-8", `od`/`tail`
  formats, the E0106 wording. New words: 정규식, 패턴 as "the text to search for"
  (disambiguated from Rust patterns on p24-grep-match; kept out of p24-intro), 번호 칸,
  콜론 (the book's word for ":"). First uses on a slide: `str::to_ascii_lowercase`,
  `bool != bool` as XOR, `tail -c`, `od -An -c`, `str::repeat`. Badge wanted but not
  sourced: `str::to_ascii_lowercase`.
  For the next two project writers: copy `scratch/w24b/mk.py` (not w24a's); put every
  precedence or decision rule in a tiny pure function with one unit test; add struct
  fields at the step that uses them and write earlier whole-struct tests with
  `..Default::default()`; a binary named like a system tool is always invoked as
  `./target/debug/<name>`; quiz commands go at the END of the final RUN; give helper
  functions their final parameters at first appearance so later steps are purely
  additive; probe std helpers before stating their edges (the brief wrongly assumed \r
  stays in a `lines()` line); taken names: grep1_match … grep8_final, grep3_nolife,
  ids p24-grep-….
  Later (0–23 and chapter-1 additions): p17-tool-rules / p17-tool-head-main state "0 · 1 ·
  2 — 성공, 일하다 난 실패, 잘못 부른 것" as the rule for small tools → forward pointer to
  p24-grep-read (which redefines 1); p08-str-split says nothing about \r\n or an
  unterminated last line → p24-grep-search-test; p24-wc-more's exercises 2 (`--`) and 7
  (failing-Write test) are now worked in chapter 2 — point forward; p18-hash-impl uses
  `to_ascii_lowercase` without saying ASCII-only → p24-grep-search-flags.
  Unchecked by a reviewer: all of 24 project 2.
- 24 project 2 reviewed (42 slides after the review): 사실오류 7 · 증거불일치 2 · 근거없음 10 ·
  절단 0 · 순서 5 · 표기 7 · 퀴즈 1 · 코드 0; style 3 (one of them re-teaching chapter 1).
  The program needed no change and no example, capture or generator was touched; numbers,
  line references, slices and step sizes were all correct. Defects: over-general frame
  sentences, false "first / only / same" statements (e.g. "main 은 1장과 한 줄이 다르다"
  — the diff shows five lines; "여기서 처음 쓰는 메서드" — part 18 already used it), a
  rules row that was false for stderr (`eprintln!` panics, 101), unlabelled inferences.
  p24-grep-rules (16 rows) split into p24-grep-rules ("① 고르는 줄과 찍는 모양", 9 rows)
  and the new p24-grep-rules-run ("② 명령 줄, 읽기, 종료 코드", 7 rows); the quiz now
  carries its OUT slice (grep8_final.txt 89–95) inside the answer block — the first quiz
  in the book with a capture box in `.a` (builder, verify and deck-check pass; look at it
  once on a phone). 24_proj.html: p24-wc-more's exercises 2 and 7 point forward to
  p24-grep-config and p24-grep-test-write; p24-intro checked and unchanged. Slides +1 →
  project 2 = 42, part 24 = 80, deck 1,556. Orchestrator re-ran: `make all` rc=0 (오류 0 ·
  어긋남 0), `rsrun --check ex/24` ×3 = 19 ✓ / 0 ✗; checked the quiz slice against the
  capture and the main.rs diff claim; card and README set to 1,556슬라이드 · 캡처 1,204.
  Edges probed (all consistent with the rules, nothing changed): pattern equal to / longer
  than a line, tab or colon in the pattern (rows with colons are ambiguous — nothing claims
  otherwise), `-c` with zero in one of two files (`name:0`, exit 0) and with an unreadable
  file, zero-byte file vs one empty line, `-- milk -n`, `-- -- file`, a directory as the
  only file, repeated/joined flags, `< data`, a NUL byte, É/é · Σ/σ · Ａ/ａ under `-i`
  (not folded), `"a\r"` at EOF, `--help`, newline inside the pattern, stdout closed early
  (Broken pipe, 2 — probe only), non-UTF-8 argument (panic, 101), stderr unwritable
  (panic, 101). Lessons 94–104 in AUTHORING.md. Open: `selects` lowercases the pattern
  once per line (not a book contradiction); a colon in a file name makes a row
  unparseable (could be an exercise). Glossary candidates: 정규식, 번호 칸. Later (0–23
  additions): p17-in-all / p17-file-bad-utf8 → p24-grep-bad-utf8 (others as listed under
  "24 project 2 written").
  For calc: probe overflow, division by zero and nesting depth before writing the rules
  table; decide byte vs char positions with a Korean input in a test; REPL notices go to
  stderr — state what happens when it is unwritable. For kv: fix worker output order by
  joining in a fixed order; state what a poisoned lock does; test a key or value
  containing the separator or a newline.
