# Review guide — how to review one or two finished parts of the deck

You review and FIX. You do not write new material. Working directory: `rust/`.
Read `deck/AUTHORING.md` first (the rules the writers followed), then `PLAN.md` §0, then
the `deck/OUTLINE.md` rows of the parts you review and their neighbours.

For each slide of your parts, read the section HTML together with the example source
(`ex/NN/…`) and its capture (`out/NN/….txt`) that the slide's RUN/CODE/OUT directives point
at. Check, in this order:

1. **Prose vs capture.** Every statement about what the program prints or what the compiler
   says must match the capture exactly: numbers, line numbers ("5번 줄"), quoted wording,
   which `help:`/`note:` exists, exit codes. A mismatch is the most serious defect.
2. **Unbacked claims.** A factual claim about Rust behaviour that no capture on that slide
   (or a slide it links to) shows. Either reword it to what is shown, back it with a new small
   example (run it), or remove it. Version claims ("1.65 부터") must be `<!--SINCE-->` badges
   with evidence in `docs/releases.txt`; plain-text version numbers are defects.
3. **Slices.** For every `<!--CODE … lines=A-B-->` and `<!--OUT … lines=A-B-->`, print the
   slice (`sed -n 'A,Bp'` on the file — for `.rs` files count lines WITHOUT trailing `//@`
   lines) and check that it starts and ends at a sensible boundary (whole function, whole
   diagnostic block), and that the `note=` describes it.
4. **Reading order.** The book is read in part order. A slide must not rely on something a
   later part teaches unless it says so in a clause ("…는 N부에서 봅니다"). "앞 장 / 다음 장 /
   위의" must point at the slide that is really adjacent. Links `href="#id"` must go where the
   text says.
5. **Titles and quizzes.** A title ending "— E0xxx" must be the code in that slide's capture
   (and every slide showing a coded error should carry it). Quiz answers must follow from an
   example in the same chapter.
6. **Korean.** 합니다체 throughout; fixed terms from AUTHORING.md's glossary (소유권, 빌림, 참조,
   수명, 이동, 트레이트, 구조체, 열거형, 변형, 가리기, 식, 문 …); typos, spacing, awkward
   literal translations; no hype words.
7. **Code quality.** Examples are idiomatic, minimal, and their Korean comments say why.

## How to fix
- Edit only the section files and `ex/NN`, `out/NN` of the parts you were given.
- **Never change a slide `id`** (other parts link to them) and do not add or remove slides
  unless a defect cannot be fixed otherwise (then at most ±2, and say so).
- Changed an example? Format only that file
  (`/data/data/com.termux/files/usr/bin/rustfmt --config-path ex/rustfmt.toml ex/NN/x.rs`),
  re-run it (`python3 tools/rsrun.py ex/NN/x.rs`), re-read the new capture, and re-check
  every slide that shows it (line numbers in prose and `lines=` may shift).
- After fixing: `python3 tools/rsrun.py --check ex/NN` for your parts and
  `make deck SKEL=1` must show no ✗ from your files.
- Machine rules as in AUTHORING.md: one command at a time, foreground, no sub-agents, no
  `make all`, no `make fmt`, no git commit/stash/checkout/reset.

## Report (English, short)
Counts by category — 사실오류 (wrong statement), 증거불일치 (prose ≠ capture), 근거없음 (unbacked
claim), 절단 (bad slice), 순서 (reading order / wrong reference), 표기 (Korean/typo/term),
퀴즈, 코드 (example quality) — then one line per fix (`slide id — what was wrong → what you
did`), then anything you found but could not fix.
