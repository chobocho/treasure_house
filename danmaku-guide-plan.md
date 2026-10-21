# Danmaku (Bullet-Hell) Shooter Guide — Execution Plan for Codex

> Agent-to-agent document. Written in English per CLAUDE.md §0.
> All user-facing output (the deck itself, code comments, history.md, chat replies) MUST be Korean.
> Read `/root/.claude/CLAUDE.md` first and follow its 5-step SOP for every task below.
> Decisions in §1 were confirmed by the user on 2026-10-20. Do not re-ask them.
> **Moved 2026-10-21:** the source and deck now live only in `/root/github/treasure_house` (user request). The book copy was deleted. Build reads `../template.html` of treasure_house; commits follow treasure_house conventions (Korean descriptive messages, push allowed on request).

---

## 0. Mission

Produce ONE self-contained HTML slide deck, `탄막-슈팅-가이드.html`, built from
`/root/github/treasure_house/template.html` (originally the book copy). It teaches how to build the same bullet-hell shooter,
levels 1–7, in four tracks:

| Track | Stack | Folder |
|---|---|---|
| A | Python + pygame | `examples/pygame/` |
| B | HTML5 Canvas 2D + TypeScript | `examples/canvas-ts/` |
| C | WebGL via Three.js + TypeScript | `examples/three-ts/` |
| D | C++ → wasm (clang `--target=wasm32`, hand-written JS glue, no Emscripten) | `examples/cpp-wasm/` |

Hard constraints from the user:

1. **Slide cap: 2000** (`article.card` count). No total minimum (user update, 2026-10-20). Never exceed 2000.
2. **Only working code.** Every code block in the deck is cut from a file that is built and
   executed by the test suite. No pseudo-code, no hand-typed snippets, no "should work".
3. **Assets:** emoji or free images only. **Licenses allowed: MIT, BSD, Apache-2.0, CC0.**
   No CC-BY, CC-BY-SA, GPL, or "free for personal use" assets.
4. **Audio:** MIT/BSD first (ZzFX, ZzFXM), or synthesized by our own code.
5. **Minimal agents:** work sequentially in one session. Do not spawn parallel sub-agents.

---

## 1. Fixed facts

### 1.1 User decisions (2026-10-20)

| Item | Decision |
|---|---|
| Output | single HTML `/root/github/treasure_house/탄막-슈팅-가이드.html` |
| wasm toolchain | clang 21 `--target=wasm32 -nostdlib`, `wasm-ld`, freestanding C++ (no libc/STL), JS glue written by us |
| Licenses | MIT / BSD / Apache-2.0 / CC0 only |
| Browser check | install Playwright Chromium locally under `danmaku-guide-src/` (if it cannot launch in PRoot, report to the user in Korean and fall back to Node-only checks) |
| Mono font | after each build run `python3 /root/github/treasure_house/tools/embed_mono_font.py 탄막-슈팅-가이드.html`; the validator runs it with `--check`. Do NOT copy the script into this repo |

### 1.2 Environment (verified 2026-10-20)

| Item | Value |
|---|---|
| Host | aarch64, PRoot on Termux/Android, `/root/github/treasure_house` (originally `/root/github/book`) |
| Python | 3.14, **pygame 2.5.8 installed**, no numpy, no pytest → use `python3 -m unittest` |
| Node | v24.18, npm 11.20. `tsc` NOT global → install locally |
| C/C++ | clang 21.1.8 + `wasm-ld` (wasm32 build verified), g++ 15.2 |
| Missing | emcc, any system browser |
| Font tool deps | fontTools 4.64, brotli, D2Coding at `/usr/share/fonts/truetype/nanum/` — all present |

### 1.3 Template facts (`template.html`, 1822 lines, 30 example slides)

| Item | Value |
|---|---|
| Working copy | has **uncommitted** edits (DeckMono font, user-select). Use the working copy as-is. Never modify or commit `template.html` |
| Slide grammar | `article.card.section.cover` (h1) / `article.card.section` (h2, opens a TOC group) / `article.card` (h3) |
| Required | every `article` has a unique `id`; never hand-write `.pno` |
| Components | `.note .tip .warn .key` callouts; `p.fname` + `pre>code[data-lang]`; `.tblwrap>table.kv`; `.g2 .g3`; `.flow`(`.box .arr`) / `.pipe`(`.st`); `.stack .pkgtree .sig .satisfy .term .cerr`; `.cmp.good/.bad`; `.demo[data-demo]` + `__demo(id, fn)`; `article.quiz[data-quiz]` |
| Highlighter langs | `js ts py c cpp go rust java lua rb sh sql lisp html css json yaml http bas text` — **no `glsl`**: tag shaders as `c` |
| Forbidden | box-drawing chars U+2500–U+257F, external CSS/JS/fonts (`<script src>`, `<link rel=stylesheet>`, `url(http`), hand-written page numbers |
| Nav | `<select id="nav">` options must list every part and chapter id |
| Reference | `paseo-guide-src/` (build.mjs, validate.mjs) is a working precedent — read it, copy patterns, do not import from it |

### 1.4 Git hygiene

The working tree has unrelated uncommitted changes (`saju-lovers-src/**`, `template.html`,
`사주-연인-운세.html`). **Never `git add -A` / `git add .`** — stage only paths you created or
changed for the current task. Commit on the current branch (`master`). Never push.

---

## 2. File layout

```
/root/github/treasure_house/
  danmaku-guide-plan.md          (this file)
  탄막-슈팅-가이드.html           FINAL deck (built artifact, committed)
  danmaku-guide-src/
    README.md                    Korean: how to build/test
    PROGRESS.md                  Korean: per-task status, slide counts, commit hashes (resume point)
    package.json                 exact-pinned devDeps (no ^ or ~): typescript, esbuild, three, @types/three, playwright
    .gitignore                   node_modules/, dist/, .cache/, test-results/
    nav.json                     [{id, label, kind: "part"|"chapter", minSlides}]
    parts/                       <article> fragments only, filename order = deck order
    build.mjs                    template shell + parts + snippets + nav → final HTML
    snippets.mjs                 region extractor (used by build and tests)
    validate.mjs / validate.test.mjs
    browser.test.mjs             Playwright smoke tests (deck + web demos)
    demos.js                     __demo registrations (embedded playable demos)
    spec/
      game-spec.md               Korean: the one game every track implements
      constants.json             shared numbers (screen, speeds, radii, seeds…)
      golden/lv1.json … lv7.json cross-track determinism targets (see §4)
    captures/                    real terminal output referenced by .term blocks
    examples/
      assets/                    downloaded third-party files + LICENSES.md (sha256 + URL + license)
      pygame/   lv1/ … lv7/      each level is a complete runnable snapshot
      canvas-ts/ lv1/ … lv7/
      three-ts/  lv1/ … lv7/
      cpp-wasm/  lv1/ … lv7/
      */antipatterns/            runnable "bad" examples used by .cmp.bad slides
```

Each `lvN/` is a full copy (cumulative), not a diff, so every level runs on its own.
Shared code between levels is duplicated on purpose — readers copy a folder and run it.

---

## 3. "Only working code" contract (the core of this project)

### 3.1 Regions

Source files mark slide-able regions:

```
# region player-move        (Python)
# endregion
// #region player-move      (TS, C++, JS, shaders)
// #endregion
```

Region names are kebab-case and unique per file. Regions may nest.
Marker lines themselves are never emitted into the deck.

### 3.2 Slides reference regions, never contain code

```html
<p class="fname">pygame/lv3/patterns.py</p>
<pre><code data-lang="py" data-src="pygame/lv3/patterns.py#spiral"></code></pre>
```

`build.mjs` fills the `<code>` with the region text (HTML-escaped, dedented, trailing
whitespace stripped). Whole file: `data-src="path"` without `#`. Shell commands live in
`examples/<track>/commands.sh` regions, and that file is executed by the tests.
Terminal output (`.term`) uses `data-src="captures/<name>.txt"`, produced by
`npm run capture`, which really runs the command and saves stdout.

### 3.3 Rules enforced

- A `<pre><code>` in `parts/` with literal content or without `data-src` → build error.
- Missing file / missing region → build error.
- Every file referenced by any `data-src` must be covered by a test that runs it (see §5);
  `validate.test.mjs` checks the referenced path is listed in `examples/<track>/TESTED.txt`,
  which each track's test runner regenerates.
- A region longer than 30 lines → build error (split the region; one idea per slide).

---

## 4. The game (identical in all tracks) and cross-track determinism

`spec/game-spec.md` (Korean) defines it; `spec/constants.json` holds the numbers.

| Item | Value |
|---|---|
| Logical screen | 480 × 640, origin top-left, y down |
| Timing | fixed step 1/60 s; render interpolates; logic never reads wall-clock |
| Player | speed 4.0 px/step (focus 1.6), hitbox radius 2.5, graze radius 16 |
| Pools | bullets 4096, enemies 128, particles 2048 (fixed arrays, swap-remove, no allocation in the loop) |
| RNG | xorshift32, seed 0x2F6E2B1, explicit uint32 masking in every language |
| Trig | **own** `dsin/dcos` (quarter-wave odd polynomial, angle in turns 0..1). No `math.sin`, `Math.sin`, `atan2`, or libm in game logic. Aimed shots use `sqrt` normalization only |
| Floats | IEEE double everywhere; C++ native tests and wasm built with `-ffp-contract=off` (aarch64 g++ fuses FMA by default and would diverge) |

Levels:

| Lv | Gameplay | Concepts taught |
|---|---|---|
| 1 | player moves, shoots | game loop, input, fixed timestep, sprite drawing |
| 2 | popcorn enemies, hits, lives | circle collision, object pools |
| 3 | patterns: ring, aimed fan, spiral, wave | polar coords, own trig, pattern functions |
| 4 | boss with 3 phases + HP bar | state machines, timers |
| 5 | graze, bomb, power-ups, score | separate hit/graze radii, event queue |
| 6 | stage timeline (data-driven script) | data-driven design, JSON stage files |
| 7 | particles, SFX/BGM, title/game-over, high score | polish, audio, persistence |

**Golden files.** Track A (pygame) is written first and produces `spec/golden/lvN.json`:
a scripted input sequence (frame → keys) and, at checkpoints (frames 60, 600, 1800),
`{frame, bullets, enemies, score, lives, phase, checksum}` where
`checksum = (Σ_i (floor(x_i*16) * 31 + floor(y_i*16))) mod 2^32` over live bullets in pool order.
Tracks B, C, D must reproduce the same values in their headless runners. A mismatch is a bug
in the new track, never a reason to regenerate the golden file. If you believe the golden file
itself is wrong, stop and report to the user.

---

## 5. Per-track build & test commands

All tests run from `danmaku-guide-src/`; `npm test` runs every track plus the validator.

| Track | Build / run | Test |
|---|---|---|
| A pygame | `python3 examples/pygame/lvN/main.py` | `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m unittest discover examples/pygame` — unit tests + headless N-frame run vs golden |
| B canvas-ts | `tsc --strict --noEmit -p examples/canvas-ts/lvN`; esbuild → `dist/canvas-lvN.js` | `node --test` on logic (pure modules, no DOM) vs golden; Playwright: page loads, 120 frames, zero console errors, canvas not blank |
| C three-ts | same as B | logic vs golden in Node; Playwright with `--use-gl=swiftshader` (or `--use-angle=swiftshader`): renders, zero console errors, draw calls > 0 |
| D cpp-wasm | native: `g++ -std=c++20 -Wall -Wextra -Werror -ffp-contract=off` unit tests of the same `game.cpp`; wasm: `clang++ --target=wasm32 -nostdlib -fno-exceptions -fno-rtti -O2 -ffp-contract=off -Wl,--no-entry -Wl,--export-dynamic` | native tests; Node loads the `.wasm`, runs golden script; Playwright runs the JS glue page |

Architecture rule for C/D tracks and B: game logic is pure (no DOM, no canvas, no Three.js
imports) so Node can run it headless. Rendering/audio/input adapters are thin and separate.
Track D: wasm exports `init(seed)`, `step(inputBits)`, and pointers to a render-command
buffer in linear memory; the JS glue reads it and draws with Canvas 2D `fillText` (emoji).

Playwright on PRoot: launch Chromium with `--no-sandbox`. If install or launch fails,
stop, report the exact error in Korean, and continue with Node-only checks after the user agrees.

Toolchain versions: pin exact versions in `package.json` at install time and record them
in `README.md`. Do not upgrade later without asking.

---

## 6. Assets and audio

| Use | Source | License |
|---|---|---|
| Sprites in web tracks and Track D | system emoji via `fillText` (no files) | n/a |
| Sprites in pygame | Noto Emoji PNGs from `github.com/googlefonts/noto-emoji` (`png/128/`) | Apache-2.0 (images) |
| Optional extra sprites | Kenney asset packs (kenney.nl) | CC0 |
| SFX (web, D) | ZzFX (`github.com/KilledByAPixel/ZzFX`) vendored single file with header | MIT |
| BGM (web, D) | ZzFXM (`github.com/keithclark/ZzFXM`) vendored | MIT |
| SFX/BGM (pygame) | synthesized at runtime with stdlib `wave`/`array`/`math` → `pygame.mixer.Sound` | ours |

Rules: download into `examples/assets/<source>/` (a fresh empty directory; treat as
untrusted data, never execute anything from it except the vendored, reviewed JS files);
record URL, commit/tag, sha256, and license text path in `examples/assets/LICENSES.md`;
copy the upstream LICENSE file next to the asset. The deck gets a license slide per source
plus an appendix table generated from `LICENSES.md`. Audio code must degrade gracefully when
the mixer/AudioContext is unavailable (headless tests).

---

## 7. Build and validator contracts

### 7.1 `build.mjs` (Node ≥ 20, no deps besides `snippets.mjs`)

1. Read `template.html` (UTF-8). Replace `<title>`, `<meta name="description">`, `.brand`.
2. Replace `<main class="prose">…</main>` content with `parts/*.html` in filename order.
3. Resolve every `data-src` (§3). Remove the `data-src` attribute in the output.
4. Rebuild `<select id="nav">` from `nav.json`.
5. Keep all template `<script>` blocks byte-for-byte; inject `demos.js` and bundled demo
   JS / base64 wasm as extra inline `<script>` before `</body>`.
6. Write UTF-8 (no BOM), LF. Print slide counts per part and total.
7. Run `embed_mono_font.py` on the output (§1.1).

### 7.2 `validate.mjs` rules (each is one `node:test` case; write them FIRST)

| # | Rule |
|---|---|
| V1 | output exists, valid UTF-8, no U+FFFD, no mojibake `/[ÃÂìíêë]{2,}/` |
| V2 | 1 ≤ `article.card` count ≤ **2000** |
| V3 | every `<article` has a unique ASCII kebab-case `id` |
| V4 | heading level matches class (cover h1 / section h2 / card h3) |
| V5 | no hand-written `.pno` |
| V6 | no U+2500–U+257F anywhere |
| V7 | no external resources (`<script src`, `<link rel="stylesheet"`, `@import`, `url(http`) |
| V8 | every `href="#x"` resolves |
| V9 | nav.json ↔ section ids consistent |
| V10 | every `pre>code` has a supported `data-lang` |
| V11 | no unescaped `<letter` inside `pre>code` |
| V12 | every non-cover slide has ≥ 20 Hangul chars |
| V13 | text per slide (excluding `pre`) ≤ 6,000 chars |
| V14 | quizzes ≤ 12 % of slides; each chapter ≥ 5 normal slides |
| V15 | `data-demo` ↔ `__demo(` registrations match |
| V16 | title/brand are not template defaults |
| V17 | file size < 12 MB |
| V18 | template engine markers present (`__deckInitHash`, `#tocBtn`, `#bar`, bookmark code) |
| V19 | every `parts/` code block uses `data-src`; every referenced region exists (§3.3) |
| V20 | every `data-src` path is listed in its track's `TESTED.txt` |
| V21 | per-part `minSlides` from `nav.json` met |
| V22 | `embed_mono_font.py --check` exits 0 |
| V23 | every asset file under `examples/assets/` has a `LICENSES.md` row with allowed license |

Never weaken a rule to make it pass. Fix the content or code.

---

## 8. Outline (part → chapter, original estimates; hard cap 2000)

User update (2026-10-20): the total 1,500-slide minimum is removed.
For upcoming wasm chapters and the appendix, choose chapter minimums to fit
the verified material rather than filling the original estimates below.
Existing registered chapter minimums remain enforced.

Track D reference: `../C++_WASM_테트리스_만들기.html`.
Follow its direct clang/wasm-ld workflow, C ABI, explicit initialization,
linear-memory views and handwritten JavaScript loading. Verify every claim
and example locally; do not reuse Tetris-specific rules or benchmark numbers.
Keep the shared shooter fixed-step and golden replay contracts.

| Part | File prefix | Chapters (minSlides) | Min |
|---|---|---|---|
| 0부 들어가며 | `00-` | how to read, the 4 tracks, the final game preview | 10 |
| 1부 공통 기초 | `10-`…`12-` | genre & design (15), vectors/polar/own trig (30), fixed-step loop (15), collision (15), pools & perf (15), determinism & RNG (10), assets & licenses (10) | 110 |
| 2부 pygame | `20-`…`28-` | setup (20), Lv1–Lv7 (40 each), packaging & debugging (25) | 325 |
| 3부 Canvas+TS | `30-`…`38-` | setup/tsc/esbuild (20), Lv1–Lv7 (40 each), deploy & perf (25) | 325 |
| 4부 Three.js | `40-`…`48-` | setup & scene/camera (20), Lv1–Lv7 (40 each; instanced bullets in Lv2–3, shaders in Lv7), perf (35) | 335 |
| 5부 C++ wasm | `50-`…`59-` | setup & clang flags (20), memory/ABI/glue (30), Lv1–Lv7 (40 each), debugging (30) | 360 |
| 6부 부록 | `60-` | 4-track comparison, perf numbers (measured, from captures), troubleshooting, license table, glossary | 60 |

Slide ids: `p{part}-{chapter-slug}-{slug}`, covers `part{N}`, chapters `ch{N}-{slug}`.
One quiz per chapter. Each level chapter ends with a "실행해 보기" slide showing the run
command (from `commands.sh`) and a real capture or screenshot description.

Embedded playable demos (≤ 4): canvas-ts Lv7, three-ts Lv7, cpp-wasm Lv7, plus one small
interactive pattern viewer in 1부. All are covered by `browser.test.mjs`.

---

## 9. Slide-writing rules

1. One idea per slide: h3 claim + one code region or one diagram/table + ≤ 2 callouts.
2. Korean prose, English identifiers. Comments inside example code are Korean, explaining *why*;
   state complexity for non-trivial algorithms (CLAUDE.md §1.2).
3. Diagrams with `.flow/.pipe/.g2/.g3/.stack/table.kv` only (V6).
4. `.cmp.bad` code also comes from `antipatterns/` and its test asserts the bad behavior
   (e.g. frame-rate-dependent speed really diverges).
5. Do not claim performance numbers you did not measure; numbers come from `captures/`.
6. If something cannot be verified in this environment, write "확인 필요" in a `.note`.

---

## 10. Task list (each task = CLAUDE.md Step 1→5 = one commit + one history.md entry)

| Task | Content | Commit |
|---|---|---|
| T0 | scaffold: package.json (pinned), validator + tests (RED), snippets.mjs + tests, build.mjs, nav.json, spec/, PROGRESS.md, 0부 | `feat(danmaku): scaffold guide build, validator and spec` |
| T0b | Playwright install + `browser.test.mjs` on the template-only deck | `test(danmaku): add playwright smoke tests` |
| T1 | 1부 공통 기초 (+ pattern-viewer demo) | `docs(danmaku): add part 1 shared foundations (N slides)` |
| T2.0–T2.8 | pygame: setup, then per level **example + tests + slides together**, then wrap-up. Lv1–7 also produce golden files | `feat(danmaku): add pygame lvN example and slides (N slides)` |
| T3.x | Canvas+TS, same pattern, must match golden | same pattern |
| T4.x | Three.js, same pattern | same pattern |
| T5.x | C++ wasm, same pattern | same pattern |
| T6 | 부록 (comparison + perf from captures + generated license table) | `docs(danmaku): add appendix` |
| T7 | finalize: full `npm test`, Playwright screenshots (cover, code, diagram, TOC, 3 demos), size check, Korean final report | `docs(danmaku): finalize danmaku shooter guide` |

Per task:
1. **Step 1:** read `PROGRESS.md` and `head -c 4000 history.md` only. Write the slide-title list
   for the task into `PROGRESS.md`. The whole outline in §8 is pre-approved; report the
   per-task plan in Korean and keep going unless something is ambiguous.
2. **Step 2 (RED):** write tests first (golden run, unit tests, `minSlides` for the new chapter).
   Confirm they fail for the intended reason (not a compile error).
3. **Step 3 (GREEN):** example code, then slides; rebuild.
4. **Step 4:** `npm test` (everything, not just the new track), review `git diff --stat`
   and the diff of each changed file, check Korean text is not mangled.
5. **Step 5:** history.md entry (≤ 12 lines, rotation rule §3.2 of CLAUDE.md), stage only
   this task's paths, commit, update `PROGRESS.md` with the hash (amend is not allowed —
   put the hash in the next task's commit).

Context budget: one task per session is fine; always commit before a session ends. On resume,
read `PROGRESS.md` + `head -c 4000 history.md` only, never the whole deck.

---

## 11. Definition of done

- `npm test` green: validator V1–V23, all four tracks' unit + golden tests, Playwright smoke.
- 1 ≤ slides ≤ 2000; every code block traced to a tested region.
- All tracks reproduce `spec/golden/lv1–7.json` exactly.
- Deck opens offline; ←/→, swipe, TOC, bookmarks, and the embedded demos work with no
  console errors (Playwright).
- `LICENSES.md` complete; only MIT/BSD/Apache-2.0/CC0 assets.
- `PROGRESS.md` all ✅ with hashes; one `history.md` entry per task.
