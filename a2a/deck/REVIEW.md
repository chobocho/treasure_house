# Review 1 guide — facts & evidence (one batch of parts)

You review and FIX. You do not write new material. Working directory: `a2a/`.
Read `deck/AUTHORING.md` first (the rules the writers followed, incl. the fixed-term list),
then `PLAN.md` §0–§1 and the progress-log entries of your parts (they list known findings,
open issues and "revisit in review" notes — handle those), then the `deck/OUTLINE.md` rows of
your parts and their neighbours.

For each slide of your parts, read the section HTML together with the example source and the
capture that its `<!--CODE …-->` / `<!--OUT …-->` / `<!--SPEC …-->` directives point at
(`ex/<lang>/NN/…`, `ex/run/NN/*.run`, `out/NN/*.txt`). Check, in this order:

1. **Prose vs capture (증거불일치).** Every statement about what a program prints, what goes
   over the wire (field names, values, states, error codes, HTTP status, headers, event
   order), or how many of something there are, must match the capture exactly. Quote values
   as they appear. A mismatch is the most serious defect.
2. **Spec claims (사실오류/근거없음).** Every "§x.y", MUST/SHOULD/MAY, field/method/enum name
   and error code must be checked against `docs/spec/docs/specification.md` and
   `docs/spec/specification/a2a.proto` (grep — never read them whole). Wrong section number,
   wrong normative word, or a paraphrase that changes the meaning is a defect.
3. **SDK claims (근거없음).** Every sentence about what an SDK does must be shown by a capture
   on that slide / a linked slide, or cite the installed source as `file:line` that you have
   opened and confirmed (`.venv/lib/python3.14/site-packages/a2a/`,
   `ex/ts/node_modules/@a2a-js/sdk/dist/`, `$(go env GOMODCACHE)/github.com/a2aproject/a2a-go/v2@v2.6.0/`).
   Line numbers cited in prose must still be right. Claims from memory → reword to what is
   shown, or remove.
4. **History facts.** Dates/versions/organisations carry `<!--FACT-->`/`<!--SRC-->`; plain
   unsourced history claims are defects (add a fact to `data/facts.tsv` with evidence from
   the cached `docs/*.txt`, run `make data`, `make data-check`).
5. **Slices (절단).** For each `lines=A-B` / `region=` cut, print the slice and check it starts
   and ends at a sensible boundary and that the `note=` and the prose describe it.
6. **References (순서).** The deck is read in part order; a slide must not rely on a later part
   without saying so. "앞 슬라이드 / 다음 슬라이드" must be the really adjacent slide; "N장 / 이
   장 / 다음 장" means a chapter — if one is used for a single slide, fix it ("앞 슬라이드" or a
   link by id). Every `href="#id"` must go where the text says.
7. **×3 consistency.** Where a slide compares py/ts/go, each cell must match that language's
   capture; the comparison table must not claim a difference the captures do not show.
8. **Quizzes (퀴즈).** The answer must follow from a capture in the same chapter.
9. **Korean (표기)** — only obvious defects in this pass (typos, wrong fixed term, 합니다체
   breaks). Style and flow are review 2's job.

## How to fix
- Edit only your parts' section files and their `ex/…/NN`, `ex/run/NN`, `out/NN`.
- **Never change a slide `id`**; do not add or remove slides unless a defect cannot be fixed
  otherwise (then at most ±2 per part, and say so).
- Changed an example or spec? Re-run it with `python3 tools/a2arun.py <spec>` (servers only
  through a2arun), re-read the new capture, re-check every slide that shows it, then
  `python3 tools/a2arun.py --check <spec>` twice. Changing `ex/*/agents/` makes every capture
  stale — don't, unless the defect is in an agent; then report it and stop for the
  orchestrator instead of re-running the world.
- After fixing: `make lint ts-check` (if you touched examples), `make data-check` (if facts),
  `make deck SKEL=1` with no ✗ from your files, `python3 tools/a2arun.py --manifest-check`
  0 stale.
- Machine rules as in AUTHORING.md: one command at a time, no sub-agents, no `make all`, no
  `make -j`, kill by PID only, no git commit/stash/checkout/reset.
- Log: `scratch/review1-<batch>-log.md`, one line per finished part; resume if it exists.

## Report (English, short)
Counts by category — 사실오류 (wrong statement), 증거불일치 (prose ≠ capture), 근거없음
(unbacked claim), 절단 (bad slice), 순서 (reading order / wrong reference), ×3 (comparison
wrong), 퀴즈, 표기 — then one line per fix (`slide id — what was wrong → what you did`), then
anything found but not fixed (with why).
