# 드론의 모든 것 (드론의_모든_것.html) — Work Plan for the Building Agent

> Audience of this file: the agent (Opus) that builds the deck. Written in English per the global
> language policy. The deck body itself is Korean (합니다체, like 수학적_최적화_완전_가이드.html and
> 밑바닥부터_만드는_트랜스포머.html). Progress log goes at the END of this file (append one entry per
> commit; never rewrite old entries).
>
> Output: `드론의_모든_것.html` at the repo root — a single-file slide deck cut from `template.html`
> (through the assembler lineage below, never by hand). Hard cap **3000 slides** (user decision
> 2026-09-24); target band **2,300–2,800**. The assembler must refuse to write a deck above the cap.
> Reader: **a first-year university student** (고등학교 수학 + 첫 학기 미적분·벡터 정도). Every
> proof in the deck must be readable by that reader after the deck's own maths part (7부); anything
> heavier is marked 심화 and given as a sketch plus a citation, never silently assumed.
>
> What this deck is: **everything about drones** — (1) history 1849 → 2026-09 (military UAVs, RC
> hobby, the multirotor revival, the consumer/DJI era, racing, delivery, drone shows), (2) the
> technology (airframe, propulsion, sensors, state estimation, communication, flight-controller
> software), (3) the **mathematics of attitude and position control with proofs** (rigid-body
> dynamics, quaternions, PID/cascade control, stability, minimum-snap trajectories, assignment for
> swarms), (4) **drone shows**: how they work, the industry, the production tools (Skybrush, Blender,
> Drone Show Software, Verge Aero …), and the **tricks** of the trade, and (5) two **working drone-show
> simulators built here — Python (stdlib only) and JavaScript (plain, in-deck demo)** that share one
> spec and one set of golden vectors, with every source line shown in the deck taken from the real
> files. Tooling lineage: `keycloak_ad/` → `compress/` → `wireless/` → `transformer/` → `git/` →
> `goevo/` (assembler, checks, Makefile, svgkit, claims, CITE badges, CSS math kit). **Copy from
> `git/deck` and the math kit from `transformer/deck/base/head.html`; don't reinvent.** Read
> `git/PLAN.md` §0–§1, `transformer/PLAN.md` §4 (formula policy) and the last three progress-log
> entries of each once before starting: every rule below that looks pedantic was paid for there.

---

## 0. Non-negotiables (read twice)

1. **The deck HTML is a build artifact.** Never edit it by hand. Edit `drone/deck/sections/*.html`
   or the sources/data they cite, then `make all`.
2. **No hand-written code, captures or numbers in the deck.** Every `<pre><code>` is a
   `<!--CODE file=… lines=A-B|sym=…-->` directive filled from a real file under `drone/py/`,
   `drone/js/`, `drone/ex/` or `drone/data/excerpts/`. Every terminal capture is `<!--OUT file=…-->`
   from `drone/out/`, produced by `run_all.py`. Every table of numbers (flight-time estimates, pole
   locations, minimum distances, assignment costs, timeline rows) is `<!--TABLE file=…-->` generated
   by `run_all.py`/`gen_tables.py` from `data/*.tsv` or `out/`. `verify_deck.py` re-checks
   deck ↔ source on every build.
3. **Three oracles, and only three.**
   (a) **The simulators built here** (`py/`, `js/`) for *everything that can be computed*: they are
   the numeric witness of every formula (§3.5). A formula that yields a number, a matrix, a gain,
   a trajectory or a pole must be checked by a test in `py/tests/` (and, where the JS port has it,
   `js/test/`) against the formula at a stated tolerance — the transformer deck's "every formula has
   a witness" rule. (b) **Primary documents fetched into `docs/`** (§2) for *everything technical
   and regulatory*: firmware source (PX4 `AttitudeControl.cpp`, ArduPilot `AC_AttitudeControl.cpp`,
   Betaflight `pid.c`), MAVLink `common.xml` + serialization guide, PX4/ArduPilot docs, Skybrush
   docs and protocol spec, Blender Python API docs, papers (arXiv PDFs, the Madgwick report),
   14 CFR Part 107 from eCFR, EASA drone pages, 항공안전법 from law.go.kr, FAA UAS pages.
   (c) **For history**: museum/manufacturer/organisation pages, Guinness World Records pages,
   press releases, and Wikipedia **only by following its own citation** to (b)/(c)-class sources.
   Nothing in this PLAN's topic lists (§4) is a source — they are *candidates to verify*, and some
   of them are wrong on purpose of being memory (names, years, drone counts, record holders).
4. **Every fact has a source** before it appears on a slide: dates, drone counts, record holders,
   company names, product launch years, prices, regulation article numbers, weight classes, paper
   titles/years, firmware behaviours. They go in `deck/claims.md` as
   `claim | source | verified-how | date`, and the slide carries `<!--CITE key=… sec=…-->` that
   `check_claims.py` resolves against `data/cite_keys.tsv` + a `§<TAB>heading` line in
   `docs/<key>.txt`. A claim that cannot be sourced is dropped or marked
   `<span class="unv">미확인</span>`. Numbers about *other people's* systems (max speed, flight time,
   positioning accuracy, LED brightness, show sizes) are **quoted with a CITE badge**, never
   measured or estimated here and never rounded differently from the source.
5. **Knowledge-cutoff discipline.** Anything dated 2025 or later — largest drone show records, the
   current Skybrush/Blender/PX4/ArduPilot/Betaflight versions, company status (acquisitions,
   shutdowns), Korean and US/EU rule changes (Remote ID, 특별비행승인 procedure), delivery-service
   status — is written **only** from `docs/` fetched at build time or a WebSearch result recorded
   in `claims.md`, stamped "2026-09 기준". Re-fetch `docs/` (`make docs`) at the start of every
   session that touches parts 3, 11, 12 or 17; `docs/FETCHED.txt` records date and sha256.
6. **Proofs are proofs.** Every theorem, lemma or derivation on a slide is a row in
   `data/theorems.tsv`: `id | statement(ko) | level(1학년|심화) | proof-kind(full|sketch|cited) |
   prerequisites(ids from 7부) | witness-test | cite-key`. A `full` proof is self-contained given
   the listed prerequisites, has numbered steps in a `.proof` box, and states where each hypothesis
   is used. A `sketch` says in its first line what it skips and why (e.g. "리아푸노프 안정성 정리는
   증명 없이 씁니다 — 2학년 과정, 출처 …"). `cited` results (Lee–Leok–McClamroch SE(3) tracking,
   Lyapunov theory, Routh–Hurwitz general case, Kuhn's O(n³) bound) are stated precisely with the
   source and used, not re-proved. `check_xref.py` verifies every `.thm` id exists in the tsv, that
   `full` proofs have a witness test, and that no `심화` result is a prerequisite of a `1학년` proof.
   **Never loosen a theorem statement to make a proof shorter**; narrow the hypothesis and say so.
7. **Tests before code (RED → GREEN)** for every module in `py/` and `js/` and every Python tool
   (`tools/`, `deck/gen_*.py` via `need()`). The Python simulator is written first; **golden
   vectors** (`golden/*.json`: pinned states, controller outputs, assignments, polynomial
   coefficients, quaternion products) are produced by the Python implementation *after* its own
   formula-witness tests are green, and the JS port's tests are RED against those files before a
   line of JS exists. Never loosen an assertion to pass. If a stated property of the physics turns
   out to be false, fix the slide, not the oracle.
8. **This machine is a Galaxy Fold under Termux/proot with ~150 MB free and a nearly full swap**
   (`free -m` 2026-09-24: 143 MB free, 1.7 GB available, swap 13/16 GB used). At most **2
   subagents**, no `-j`, one simulator process at a time, every experiment ≤ 60 s and ≤ 200 MB
   RSS, `run_all.py` ≤ 20 min total and strictly sequential. Physics-accurate (6-DOF) scenarios use
   ≤ 20 drones; large shows (≤ 500 drones) run the **kinematic-follower mode** (§3.3) and the slide
   says which mode produced the capture. Check `free -m` before heavy steps. Checkpoint to disk;
   assume the session can be killed any moment. Long runs go in the background with a Monitor,
   never with `&` inside Bash (git/PLAN.md progress log, 2026-09-18).
9. **Foldable layout.** `<pre>` ≤ 45 lines and ≤ 72 columns (Korean counts as 2), captures ≤ 108
   columns, `<li>` ≤ 14 per list, no box-drawing characters in prose, no `①②③` inside monospace.
   Formulas are set with the **CSS math kit** (`.eq/.eqn/.mi/.frac/.vec/.thm/.proof` copied from
   `transformer/deck/base/head.html`), never as ASCII art, never as images of text, never with
   MathJax/KaTeX (no external scripts — repo rule). A formula wider than the 374 px fold is split
   across `.eq` lines. Figures are SVG from `deck/gen_figs.py` reading only `data/` and `out/`
   (`viewBox` width 340). Render every figure with `rsvg-convert` and **look at it**.
10. **Determinism is evidence.** Every capture in `out/` must be identical across three runs
    (`tools/record.sh --check`, sha256). Simulators take an explicit seed (`--seed 7`), use only
    `math`/`random` from the stdlib (Python) or a seeded xorshift (JS) — never `Math.random()`,
    never wall-clock; floats are printed with a fixed format (`%.6f`, JSON via `round(x, 9)`); PNG
    frames are written with a fixed zlib level; no timings appear anywhere in prose. Operation
    counts (for O(n³) claims) are counted in code, not timed.
11. **Commit granularity:** one tool, one data batch, one simulator module, one experiment batch,
    one deck part, one figure batch or one review per commit. Korean, no-prefix commit subject
    (repo convention), `Co-Authored-By` trailer as the session reminder says. Never `git push`
    unless asked. `git add` always by path — other sessions may work in this repository at once.
12. **Language:** deck prose in Korean 합니다체; identifiers and file names in English; **comments
    inside `py/` and `js/` in Korean** (§9 decision 8 — this is teaching code for a Korean
    freshman, unlike the goevo captures) with `tools/width.py` enforcing the 72-column rule;
    this file and subagent briefs in English.
13. **Scope discipline.** This deck teaches drones. It is **not** a control-theory textbook
    (state only what the drone needs, prove only what the reader can follow), not a Blender manual
    (12부 shows the workflow and the Python API calls we can verify, and links to
    `docs.blender.org`), not a GNSS/Wi-Fi deck (link `무선통신_대백과사전.html` for radio depth,
    `수학적_최적화_완전_가이드.html` for optimisation depth, `밑바닥부터_만드는_트랜스포머.html` for
    gradient/ML depth). Military history is encyclopedic (dates, programmes, why they mattered) —
    **no operational, targeting, payload or countermeasure detail**, and the deck never explains how
    to defeat geofences, Remote ID or no-fly zones. The reading-guide slide says this.
14. **Licences.** Firmware excerpts (PX4 BSD-3, ArduPilot GPL-3, Betaflight GPL-3, Skybrush GPL-3,
    MAVLink MIT) are ≤ 40 lines each, kept in `data/excerpts/` with a header line naming the file,
    commit sha (from the GitHub API), licence and fetch date, produced by `tools/excerpt.py` from
    `docs/` so they are reproducible. Papers are cited and paraphrased, never copied beyond a
    two-sentence quote. No photos, no logos, no screenshots of commercial tools (§9 decision 9).

---

## 1. Directory layout

```
drone/
  PLAN.md              this file (+ progress log at the end)
  SPEC.md              the simulator spec both languages implement (§3.3) — frames, units, parameters,
                       controller structure, show file format, golden-vector list, tolerances
  Makefile             the whole build; `make help` lists targets (trim git/Makefile: no java/cpp/go)
  data/                one fact per row, source column mandatory
    timeline.tsv       date | event(ko) | kind(military|hobby|multirotor|consumer|racing|delivery|show|law) | source | verified-how   HAND (≥ 220 rows, 1849 → 2026-09)
    shows.tsv          date | place | organiser | drone-count | record?(Guinness|claimed|none) | source     HAND (≥ 60 rows)
    products.tsv       year | maker | product | class | notable-for(ko) | source                            HAND (≥ 80 rows)
    firmware.tsv       project | first-release | licence | language | attitude-representation | source     HAND
    tools_show.tsv     tool | vendor | kind(design|server|live|sim) | open-source? | file-formats | source  HAND (≥ 12 rows)
    law.tsv            jurisdiction | rule | article/section | requirement(ko) | source                    HAND (KR/US/EU; ≥ 40 rows)
    theorems.tsv       see §0.6                                                                        HAND (≥ 90 rows)
    symbols.tsv        symbol | meaning(ko) | unit | first-slide                                          HAND (the notation slide is generated from it)
    params.tsv         parameter | value | unit | why(ko)                                                 HAND — the reference quadrotor of SPEC.md
    quotes.tsv         quote(en) | who | where | date | source   — verbatim, ≤ 2 sentences, translated on the slide
    cite_keys.tsv      key | url | kind | licence                                                        HAND — every CITE key
    excerpts/          firmware/protocol excerpts produced by tools/excerpt.py (committed, ≤ 40 lines each)
  docs/                fetched primary-document cache (gitignored; `make docs` re-fetches, writes docs/FETCHED.txt):
    raw/               html/pdf/xml/json as fetched
    *.txt              text conversions with `§<TAB>heading` lines for CITE (tools/html_text.py, tools/pdf_text.sh)
  py/                  the Python simulator (stdlib only, python3 ≥ 3.12; one module per concept, ≤ 300 lines each)
    droneshow/         package: vec3.py quat.py rigidbody.py motor.py quadrotor.py pid.py attitude.py
                       cascade.py mixer.py sensors.py estimator.py (complementary, kalman1d, ekf-lite)
                       poly.py (min-snap) profile.py (trapezoid) formation.py (grid/circle/sphere/heart/globe/
                       text/image) assign.py (hungarian + brute) collide.py show.py (Show model, JSON/CSV io)
                       render.py (SVG storyboard + PNG frames via zlib) cli.py
    tests/             unittest — formula witnesses (§3.5), golden writers, cli smoke tests
  js/                  the JavaScript port (plain ES2020, no build step, no libraries)
    droneshow.js       one file, same module boundaries as py/ in sections; runs in browser and node
    demo.js            canvas renderer, orbit camera, UI wiring for the in-deck demos
    test/              `node --test` — golden parity (1e-9 after rounding), renderer smoke in the DOM stub
  golden/              JSON produced by py/tests/write_golden.py; read by js/test and by deck tables
  ex/                  small standalone programs the deck cites that are not part of the simulator
                       (mavlink_parse.py, gps_trilateration.py, battery_time.py, hover_power.py, routh.py, …)
  exps/                one Python module per experiment batch (imported by run_all.py in ORDER)
  run_all.py           runs every experiment sequentially → out/manifest.json + out/*.txt|html|svg|png
  out/                 every capture, table, storyboard and show file the deck cites (committed; ×3 identical)
  scratch/             gitignored: work dirs, frame dumps, review dumps
  deck/
    base/{head,tail}.html   copy from git/deck/base (tail has the 2026-09-24 ←→ fix); re-title; palette (§9 decision 4);
                            append the math kit + .thm/.proof/.ill blocks from transformer/deck/base/head.html
    sections/NN_*.html      slide fragments, one file per part (§4)
    build_deck.py verify_deck.py check_slices.py check_xref.py check_claims.py check_deck.js
    chunks.py gen_glossary.py gen_tables.py gen_figs.py svgkit.py
    glossary.txt order.txt pending.txt budget.txt claims.md
    figs/               SVG figures generated from data/ and out/ (viewBox 340)
    demos.js            in-deck demos = js/droneshow.js + js/demo.js concatenated by the assembler (§3.7)
  tools/               width.py rewrap.py record.sh (copy from git/tools), fetch_docs.py, html_text.py,
                       pdf_text.sh (pdftotext wrapper, §2), excerpt.py, make_tables.py, tests/ (unittest, fixtures/)
```

Copy `git/deck/{build_deck.py,verify_deck.py,check_slices.py,check_xref.py,check_claims.py,
check_deck.js,chunks.py,gen_glossary.py,gen_tables.py,svgkit.py}`, `git/deck/base/{head,tail}.html`
and `git/tools/{width.py,rewrap.py,record.sh}` verbatim first, then adapt only: `TARGET`
(`../드론의_모든_것.html`), `LANG_OF` (py, js, json, csv, tsv, xml, txt, sh, c, cpp), `HARD_CAP`
**3000**, `COVER_DIRS` (`py/`, `js/`, `ex/`, `exps/`, `tools/`, `run_all.py`), part budgets from §4,
and the CITE resolver keyed by `data/cite_keys.tsv`. **Drop the `GIT` directive.** Add **two
directives**: `<!--THM id=…-->` expands to the theorem's statement box from `data/theorems.tsv`
(so a statement is typed once, and the proof slide and the appendix index agree), and
`<!--SHOW file=out/show_heart.json frame=120-->` expands to an inline SVG snapshot rendered by
`py/droneshow/render.py` at build time (so a formation picture is always the simulator's own
output). Keep `TABLE`, `FIG`, `FULLSRC` (≤ 45-line files only), `GLOSSARY`, `QUIZINDEX`, `SRCSTAT`,
`DEMOS`. Do not fork the check design.

---

## 2. Toolchains and sources on this machine (verified 2026-09-24)

| Tool / source | State | Notes |
|---|---|---|
| python3 3.14.4 | ok | **stdlib only** — no numpy/scipy/sympy/matplotlib/PIL installed; the simulator must not need them (§9 decision 6). `pip` exists; do not install into the system |
| node 24.18 | ok | `node --test` built-in runner; runs `check_deck.js` (DOM stub). Playwright unusable (platform=android) |
| rsvg-convert | ok | `make figs-png`, then look at the PNGs; also renders `SHOW` snapshots for eyeballing |
| pdftotext | **missing** | `poppler-utils` is available from apt (candidate 26.01.0). Install with `apt-get install -y --no-install-recommends poppler-utils` (§9 decision 7) — needed for arXiv PDFs and the Madgwick report. Fallback: skip PDF sources, cite abstracts only |
| `tools/embed_mono_font.py` | ok | `make font` after every deck build, `--check` in `make all` |
| free -m | 143 MB free / 1.7 GB available | see §0.8 |
| en.wikipedia.org (UAV, Drone_light_show), ko.wikipedia.org (무인_항공기) | 200 | starting points only — follow citations (§0.3). `ko.wikipedia.org/wiki/드론_쇼` is 404 |
| faa.gov/uas | 200 | Part 107 overview, waivers (night ops, ops over people), Remote ID pages |
| ecfr.gov …/part-107 | 200 (10 KB shell) | the article text loads from the eCFR API — fetch `https://www.ecfr.gov/api/versioner/v1/full/<date>/title-14.xml?part=107` (verify the endpoint; record what worked) |
| easa.europa.eu/en/light/topics/drones | 200 | open/specific/certified categories. `/en/domains/drones-air-mobility` is 404 — do not cite that path |
| law.go.kr/법령/항공안전법 | 200 but 1.3 KB (JS shell) | use `law.go.kr/lsSc.do?menuId=1&query=항공안전법` (200) or the DRF open API; the builder must find a URL that returns the article text (제129조 초경량비행장치 조종자 준수사항, 특별비행승인 조항, 신고·안전성인증 조항) and record it in FETCHED.txt. drone.onestop.go.kr is 200 (특별비행승인·비행승인 절차) |
| docs.px4.io controller_diagrams | 200, 1.5 MB | PX4 cascade diagram — the reference for 9부's cascade; quote structure, not gains |
| raw PX4 `AttitudeControl.cpp` | 200, 8.8 KB | quaternion attitude error with reduced attitude / yaw weight — excerpt for 9부 |
| raw ArduPilot `AC_AttitudeControl.cpp` | 200, 81 KB | thrust-vector-first error, input shaping — excerpt |
| raw Betaflight `pid.c` | 200, 68 KB | rate PID, D-term filtering, anti-gravity, feed-forward — excerpt |
| ardupilot.org copter docs | 200 | tuning docs, flight modes |
| mavlink.io serialization guide, raw `common.xml` | 200 | packet layout + CRC_EXTRA — `ex/mavlink_parse.py` parses a HEARTBEAT built by our own code and cross-checks the CRC (6부) |
| arxiv.org abs/pdf 1003.2005 (Lee–Leok–McClamroch, SE(3)) | 200 | export.arxiv.org API works over **https** (http returned nothing) — use it to find and cite swarm/min-snap/assignment papers; verify each PDF opens |
| x-io.co.uk madgwick_internal_report.pdf | 200, 1.5 MB | complementary/gradient-descent AHRS filter |
| research-collection.ethz.ch | root 200; the Brescianini handle URL returned 500 | retry; else cite via DOI/arXiv mirror or mark 미확인 |
| kumarrobotics.org | 200 | Mellinger–Kumar minimum snap (ICRA 2011) and Turpin–Michael–Kumar CAPT (IJRR 2014) PDFs — find the exact URLs on the publications page; if paywalled, cite title/venue/year and prove the results from scratch (they are provable at our level, §3.5) |
| skybrush.io, doc.collmot.com (studio-for-blender, live, server, **skybrush-protocol-spec**, firmware) | 200 | the open-source drone-show suite; docs are the CITE source for 12부. GitHub org `skybrush-io` has `libskybrush`, `skybrush-server`, `live`, `skybrush.js`, `flockwave-spec`, `pyledctrl`, forks of `ardupilot`/`crazyflie-firmware` (verified via the org page; `skybrush-studio-for-blender` as a repo name is 404 — find the plugin's real repo name on the org page, page 2) |
| docs.blender.org api/current, manual | 200 | `bpy` API for 12부; **Blender cannot run here** — Blender-side code is shown as CODE from `ex/blender_*.py` with a caption saying it was not executed on this machine, and every `bpy` call it uses is CITEd to the API docs page (§9 decision 10) |
| crazyswarm.readthedocs.io, github.com/bitcraze/crazyflie-firmware | 200 | research swarm platform history and architecture; bitcraze.io/documentation returned 403 — use github |
| guinnessworldrecords.com record page | 200 but JS-rendered (no numbers in HTML) | use WebFetch/WebSearch and record the rendered claim + date in claims.md; the current record holder and count are **post-cutoff** — never from memory |
| verge.aero, droneshowsoftware.com | 200 | commercial tools — features only as they state them, with dates |
| intel.com light-show page | 403 | Intel Shooting Star history via Wikipedia citations / press archives instead |
| api.semanticscholar.org | 429 | rate-limited; use arXiv API + publisher pages |

---

## 3. What gets written

### 3.1 `tools/fetch_docs.py` + `tools/html_text.py` + `tools/pdf_text.sh` → `docs/` (step 2)

- Fetch the list in §2 plus whatever `data/cite_keys.tsv` grows to, with `urllib` (retry ×3, 20 s
  timeout, `User-Agent` set, follow redirects). Raw files under `docs/raw/`, text conversions next
  to them. Every file gets a line in `docs/FETCHED.txt`: `path | url | date | sha256 | first-heading`.
- `html_text.py`: `html.parser`-based; keeps headings as `§<TAB><heading text>` lines (h1–h4, and
  `<dt>`/`id`-bearing section anchors), keeps `<pre>`/`<code>` blocks verbatim, drops nav/footer.
  Tests: fixtures cut from the PX4 controller page, the eCFR XML, a Skybrush docs page.
- `pdf_text.sh`: `pdftotext -layout`; section headings are detected by `tools/pdf_sections.py`
  (numbered headings `^\d+(\.\d+)*\s+\S`) and emitted as `§` lines. Tests: a fixture page of text.
- `excerpt.py FILE START END KEY`: cuts ≤ 40 lines from a `docs/raw/` source into
  `data/excerpts/<key>.<ext>` with the licence header (§0.14); the commit sha comes from the GitHub
  API (`repos/<owner>/<repo>/commits?path=…&per_page=1`) and is recorded in the header.

### 3.2 `data/*.tsv` (step 3) — the hand tables and their checks

- `timeline.tsv` is the backbone of parts 2, 3 and 11: ≥ 220 rows, every row with a source that is
  not Wikipedia itself. `make data-check` fails on a row whose `source` is a bare Wikipedia URL.
- `shows.tsv` holds every show the deck mentions with its drone count and the *kind* of the count
  (Guinness-certified / organiser claim / press figure); the slide wording follows the kind
  ("기네스 인증 N대" vs "주최측 발표 N대"). Post-2024 rows must have a `verified-how` of `fetched
  YYYY-MM-DD` (§0.5).
- `law.tsv` is the only place regulation text is paraphrased from; each row cites article/section.
  KR rows: 항공안전법·시행규칙 (기체 신고, 안전성 인증, 조종자 증명, 비행승인, 특별비행승인 —
  야간·비가시권, 조종자 준수사항), 드론 활용의 촉진 및 기반조성에 관한 법률; US rows: 14 CFR 107
  (§107.29 night, §107.35 multiple aircraft, §107.39 over people, §107.200 waivers, Remote ID part
  89); EU rows: open/specific/certified, C-class marks. Article numbers are **verified in the text**.
- `theorems.tsv` (§0.6) and `symbols.tsv` are written *before* parts 7–10 and drive the notation
  slide, every `THM` box and the appendix index.
- `params.tsv` fixes the reference quadrotor once (mass, arm length, inertia, kT, kQ, motor time
  constant, max thrust, battery capacity, LED power) with a "why" per row; SPEC.md quotes it.

### 3.3 `SPEC.md` and the two simulators (steps 4–5) — what both languages implement

- **Frames/units:** SI; world frame ENU (x east, y north, z up — the show-design convention; say
  once why PX4 uses NED and show the conversion). Body frame FRD→ we use FLU (x forward, y left,
  z up) to match ENU; the mixer for an **X-configuration** quadrotor is derived in 8부 and quoted
  by SPEC.md as the matrix `M` and its inverse.
- **State:** position `p`, velocity `v`, unit quaternion `q` (scalar-first), body rates `ω`;
  four motor speeds with a first-order lag (`τ_m` from params.tsv). Forces: thrust per rotor
  `kT·Ω²`, reaction torque `kQ·Ω²`, gravity, linear drag `−c·v`; optional deterministic wind
  (seeded Ornstein–Uhlenbeck gust, off by default).
- **Integrator:** fixed-step RK4 at `dt = 0.002 s` for the rigid body; quaternion renormalised after
  each step (the slide proves why drift appears and why renormalising is safe). Controller runs at
  250 Hz (rate loop), 250 Hz (attitude), 50 Hz (position) — the time-scale separation of 9부 is a
  parameter, so the "break it" experiment (rate loop at 50 Hz) is one flag.
- **Controller:** cascade position P → velocity PID → desired acceleration → desired thrust vector
  and yaw → desired quaternion → attitude P on the quaternion error (PX4-style reduced attitude,
  cited) → rate PID with D-term low-pass and integrator clamp → mixer → motor saturation with
  thrust-priority desaturation (cited from PX4/ArduPilot behaviour, implemented simply).
- **Estimation (5부, optional path):** ideal state feedback by default; `--sensors` enables the
  sensor models (gyro bias + noise, accelerometer noise, barometer noise, GNSS at 10 Hz with
  seeded error) and an estimator (complementary filter for attitude, 1-D/3-D Kalman for position);
  the slides compare estimate vs truth from `out/`.
- **Show layer:** `Show = {fps, dmin, drones:[{id, keyframes:[[t,x,y,z,r,g,b],…]}]}` as JSON; CSV
  export per drone using the column layout documented in the Skybrush Studio docs (verify the
  exact header and units there; if the import format is not publicly documented, name ours
  "Skybrush CSV 가져오기 형식을 따르려 시도" and mark `unv`). Formation generators: grid, circle,
  ring stack, sphere (Fibonacci lattice), heart (parametric), globe (lat/lon graticule), text
  (embedded 5×7 bitmap font → points, with a "readability vs point budget" table), image (PBM/PGM
  read with stdlib → threshold → Poisson-disk thinning → Lloyd relaxation), countdown digits.
  Transitions: Hungarian assignment on squared distances (+ brute force for n ≤ 7 in tests) →
  per-drone straight line with a trapezoidal velocity profile **or** a minimum-snap polynomial
  through waypoints; collision check = pairwise distance ≥ `dmin` at every frame with the minimum
  reported as a TABLE; light choreography = per-keyframe RGB with gamma (the 13부 tricks are
  functions here: `dark_move`, `stagger_takeoff`, `layered_depth`, `rotate_volume`, `wave`,
  `led_only_motion`, `dither_gradient`).
- **Two run modes:** `physics` (6-DOF + controller per drone, ≤ 20 drones — proves the controller
  can fly the show) and `kinematic` (drones follow the planned trajectory exactly — for ≤ 500-drone
  shows; the slide always says which). A `tracking` table (max/mean position error in physics
  mode) is the evidence that the plan is flyable at the chosen speeds/accelerations.
- **Renderer:** Python writes SVG storyboards (used by `SHOW`) and PNG frame sequences via
  `zlib`/`struct` (no PIL) into `scratch/frames/` — look at a few with the image viewer; JS renders
  on `<canvas>` with a hand-written perspective projection, orbit camera, additive LED glow and a
  ground grid — no three.js (repo rule: no libraries).
- **Golden vectors (`golden/`):** quaternion products/rotations (20 cases), mixer forward/inverse,
  hover trim, a 3-drone physics run (states at t = 0.5, 1, 2, 5 s), rate-PID step outputs,
  min-snap coefficients for 3 waypoint sets, Hungarian assignments for 6 point sets (n = 5…50),
  trapezoid profile samples, formation point sets for fixed seeds, a full 12-drone show JSON.
  JS parity at 1e-9 after `round(·, 9)` on both sides (JS and Python doubles agree on + − × ÷ √;
  `sin/cos/atan2` may differ in the last ulp, hence the tolerance). `make parity` runs both.
- **Sizes:** `py/droneshow/` ≤ 3,000 lines total, `js/droneshow.js` ≤ 2,500 lines, no module
  > 300 lines (so `FULLSRC`/`CODE lines=` windows stay ≤ 45 lines with readable boundaries).

### 3.4 `deck/sections/*.html` (step 7) — slide anatomy

- **Part cover** (`card section`): `chnum` = "N부", `h2` = part title, `chsub` = one-line promise +
  the part's prerequisites ("7부 3장을 읽고 오세요"). **Chapter cover** `chnum` = "N장" (never a
  part number — `check_xref` dies).
- **Concept slide:** `h3` title (Korean, English term once in parentheses), `why` paragraph (≤ 3
  sentences, CITE badge when it states a fact about the world), then *one* of: `.eq` block with a
  `THM`, a `CODE` (≤ 45 lines) + `OUT`, a `FIG`, a `SHOW` snapshot, or a `TABLE`; `warn` box for
  the trap; `note` box for "실제 드론에서는" (how PX4/ArduPilot/Betaflight do it, with an excerpt).
- **Proof slide(s):** `THM` box (statement + level badge `<span class="lv l1">1학년</span>` /
  `<span class="lv adv">심화</span>`), a "쓰는 도구" line listing prerequisite ids, numbered steps in
  `.proof` (≤ 8 steps per slide; longer proofs continue on the next slide with "증명 계속"), a
  closing "어디에 썼나" line, and a `witness` line naming the test (`py/tests/test_poly.py::
  test_min_snap_euler_lagrange`) with its OUT capture on the same or next slide.
- **History slides** (2부, 3부, 11부 1장): prose + `timeline.tsv`-fed tables + `quotes.tsv` quotes
  (verbatim English ≤ 2 sentences in a `blockquote`, Korean translation below, source line). No
  photos (§9 decision 9); where a picture is needed, an SVG schematic (e.g. Kettering Bug layout,
  Breguet-Richet rotor arrangement) generated by `gen_figs.py` with a caption "개념도".
- **Tool slides** (12부): a `kv` table per tool (vendor, licence, platform, file formats, what it
  does in the pipeline, source URL + fetch date); workflow diagrams as SVG; Skybrush and Blender
  get code (`ex/blender_*.py`, our CSV export); commercial tools get facts only.
- **Trick slides** (13부): trick name → why it works (one formula or one observation) → the
  simulator function that implements it (`CODE sym=`) → a `SHOW` before/after pair or a TABLE
  (e.g. minimum distance with vs without staggered take-off).
- **Quizzes:** one per chapter, `<details>`-based; `QUIZINDEX` in the appendix. Every 7–10부
  chapter also has one "손으로 풀어 보기" exercise with the answer checked by a test in `ex/`.
- Cross references: "(N부)" only for parts that exist; `check_xref.py` verifies ids.

### 3.5 Formula and proof policy (first-year level) — the theorem list, each with its witness

Derive, don't decorate. Prerequisites live in **7부** and are the only tools a `1학년` proof may
use: vectors, dot/cross product and their geometric meaning, matrices and determinants (2×2, 3×3),
inverse and rank by elimination, derivatives of polynomials/trig/exp, chain rule, Taylor to second
order, simple ODEs (`x' = ax`, `x'' + 2ζω x' + ω² x = 0`), complex numbers and Euler's formula,
Newton's laws, torque and angular momentum for a point mass, sums and induction. The notation slide
is generated from `symbols.tsv`.

| id | Result (full proof unless noted) | Witness test |
|---|---|---|
| T1 | Momentum theory: hover power `P = T^{3/2} / √(2ρA)`; induced velocity `v = √(T/(2ρA))` | `ex/hover_power.py` vs `motor.py` trim for the reference drone |
| T2 | Flight time from battery: `t = C·V·η / P` and why halving mass does not double time (T1) | `ex/battery_time.py` vs energy integration of a hover run |
| T3 | Reaction torque: sum of `kQ·Ω²` with opposite spins cancels at hover; yaw comes from imbalance | mixer rows, hover trim yaw torque = 0 |
| T4 | Rotation matrices are orthogonal with det 1; composition = matrix product | 20 random cases |
| T5 | Euler angles: rate-to-Euler matrix and its singularity at pitch ±90° (gimbal lock), det → 0 | determinant scan |
| T6 | Quaternion rotation formula `v' = q v q*` is a rotation; unit norm preserved by products; `q` and `−q` are the same rotation | numeric identities |
| T7 | Quaternion kinematics `q' = ½ q ⊗ (0, ω)`; Euler integration drifts in norm at O(dt²), renormalising is safe | norm drift measured vs dt |
| T8 | Newton–Euler equations for a rigid body; the gyroscopic term `ω × Jω` (sketch of the frame-derivative lemma, full for the diagonal-J case) | energy conservation of a torque-free tumble (≤ 1e-6 rel.) |
| T9 | Quadrotor 6-DOF model; the X-configuration mixer `M` is invertible (det computed symbolically) | `mixer.py` inverse check |
| T10 | Underactuation: 4 inputs, 6 DOF — rank of the input map is 4; position is controlled only through attitude | rank by elimination |
| T11 | Hover linearisation: small-angle model `x'' ≈ g·θ`, `y'' ≈ −g·φ`; error is O(θ²) | halve θ → error ÷ ~4 |
| T12 | Differential flatness (Mellinger–Kumar): `(x, y, z, ψ)` and derivatives determine the full state and inputs — full derivation of attitude from acceleration, yaw | reconstructed inputs fly the trajectory in physics mode |
| T13 | First-order system `x' = −a x + a u` response; time constant; motor lag effect | step capture |
| T14 | Second-order closed loop under PD: `s² + kd s + kp`; ζ, ωn; overshoot formula `e^{−πζ/√(1−ζ²)}` | measured overshoot vs formula |
| T15 | Why the I-term removes steady-state error under a constant disturbance (and the wind-up trap) | offset load capture |
| T16 | Routh–Hurwitz for degree ≤ 3 (full: all coefficients positive and `a1 a2 > a0 a3`); general case `cited` | gain scan: divergence exactly past the bound |
| T17 | Time-scale separation in a cascade: inner loop `k` times faster ⇒ outer loop may treat it as unity (sketch via singular perturbation; full for two first-order loops) | 10× vs 1× rate captures |
| T18 | Quaternion attitude error `q_e = q_d* ⊗ q` and the P law `ω_d = 2·k·sign(q_e0)·q_e,vec` is stable for the kinematic model (full: Lyapunov-free argument via the angle-axis form, angle decreases monotonically) | angle-vs-time capture |
| T19 | Reduced attitude (thrust-vector-first) error, why yaw gets a smaller weight (PX4 excerpt) — `sketch` + CITE | tilt-priority capture |
| T20 | Geometric tracking control on SE(3) (Lee–Leok–McClamroch) — `cited`, statement only | — |
| T21 | Discretisation: Euler vs RK4 error orders; controller sample time and delay margin (sketch) | dt scan table |
| T22 | D-term amplifies noise by `ω`; first-order low-pass gain `1/√(1+(ωτ)²)` (full) | noise spectrum table |
| T23 | Complementary filter: `α`-blend of integrated gyro and accelerometer tilt; error < either alone under bias + noise (full for the 1-axis case) | `estimator.py` capture |
| T24 | 1-D Kalman gain minimises posterior variance (full, calculus) | gain scan |
| T25 | Multi-D Kalman predict/update (sketch from T24; `cited` for the general derivation) | residual whiteness table |
| T26 | GNSS position from ≥ 4 pseudoranges — Newton iteration on 4 unknowns (full) | `ex/gps_trilateration.py` recovers a synthetic position |
| T27 | Minimum-jerk (5th degree) and minimum-snap (7th degree) polynomials: Euler–Lagrange gives `x^{(8)} = 0`; boundary conditions determine the 8 coefficients (full, calculus of variations at freshman level via perturbation argument) | 8th derivative = 0; random perturbations never lower cost |
| T28 | Trapezoidal velocity profile: minimum-time under `v_max`, `a_max`; triangular case condition | profile samples |
| T29 | Hungarian algorithm: optimality (sketch of duality; `cited` for O(n³)); equals brute force for n ≤ 7 | exhaustive compare |
| T30 | **No-crossing lemma:** for two agents, if straight-line paths cross, swapping goals strictly lowers the sum of *squared* distances — hence the squared-cost optimal assignment has no crossing paths (full, triangle-inequality argument) | Monte Carlo 0 crossings; counter-example with plain distances |
| T31 | CAPT (Turpin–Michael–Kumar): with synchronised start/finish and start/goal separation ≥ 2√2·R, the squared-cost assignment + straight lines is collision-free — full 2-agent core, `cited` for the general statement | seeded trials 0 collisions; violated spacing → collisions found |
| T32 | Sphere/Fibonacci lattice spacing bound; Poisson-disk minimum spacing ⇒ `dmin` guarantee (full for the spacing claim) | measured min distances |
| T33 | Perspective: a planar formation at distance `D` subtends `≈ W/D` rad; why shows are 2.5-D (full, similar triangles) | — (geometry) |
| T34 | LED gamma: perceived brightness ∝ luminance^γ (cited); why linear RGB ramps look wrong; dithering as error diffusion (sketch) | `render.py` ramp table |
| T35 | Downwash spacing and take-off staggering — `cited` facts + our own collision-check evidence | stagger table |

Level check: no Lyapunov theorems (used only as `cited` statements in T18's 심화 note and T20), no
Laplace transforms beyond "characteristic polynomial of a linear ODE" (7부 explains that bridge in
two slides), no measure theory, no manifold language (SE(3) named and described in words).
Every `full` proof was **re-derived by the builder on paper first**, then typed; the proof-review
pass (§5 step 12) checks each step against the tsv statement.

### 3.6 Figures (`deck/gen_figs.py`, step 8) — all from data/out, `need()`-guarded

1. Master timeline 1849 → 2026 (from `timeline.tsv`, kind-coloured lanes), one per history part
   cover with that part's window highlighted. 2. Drone-show size history (from `shows.tsv`, log
   scale, record kind by marker). 3. Frame geometries (+, X, H, hexa, octo, coaxial) with rotor
   spin directions. 4. Momentum-theory stream tube. 5. Rotation/Euler/quaternion diagrams (angle-
   axis, gimbal lock). 6. Free-body diagram of the quadrotor with forces/torques. 7. Cascade
   controller block diagram (mirrors the PX4 diagram, cited). 8. Step responses, gain scans, pole
   locations (from `out/`). 9. Complementary/Kalman estimate-vs-truth plots. 10. Min-snap curves vs
   straight lines. 11. Assignment crossing vs non-crossing example. 12. Formation storyboards
   (`SHOW`). 13. Show-day system diagram (RTK base, GCS, network, drones, safety). 14. Regulation
   category maps (KR weight classes, EU categories). `viewBox` 340; text through svgkit classes.

### 3.7 Demos (`deck/demos.js` = `js/droneshow.js` + `js/demo.js`, step 10) — plain JS

1. **Show player:** replays Python-generated shows embedded at build time (heart → globe → text →
   countdown), orbit camera, time scrubber, LED glow toggle, "관객 시점" preset (T33).
2. **Live physics:** 1–8 drones with sliders for rate/attitude/position gains, motor lag, wind;
   buttons for the canonical failures (too-slow inner loop, D-noise, wind-up).
3. **Attitude playground:** drag to set a desired orientation; shows quaternion error, angle-axis
   and the P-law response (T18).
4. **Formation lab:** type text or pick a shape → points → Hungarian assignment → animated
   transition with the crossing counter and minimum distance (T30/T31); toggle squared vs plain
   cost to see crossings appear.
5. **Trajectory lab:** drag waypoints; compare straight+trapezoid vs minimum-snap; shows velocity
   and acceleration traces and the `v_max`/`a_max` limits.
6. **PID tuner:** second-order plant, live poles and overshoot vs the T14 formula.
`check_deck.js` runs each demo's expectation function in the DOM stub (canvas stubbed with a
recording context, as in the transformer deck).

---

## 4. Part outline and slide budgets (`deck/budget.txt`; assembler errors above part budget +10 %)

| # | Part (Korean title on the cover) | Budget |
|---|---|---|
| 0 | 표지 · 읽는 법 · 기호표(생성) · 증거 등급(시뮬레이터/문서/역사) · 세 가지 오라클 · 형제 덱 안내 · 이 덱이 다루지 않는 것 | 18 |
| 1 | 드론이란 무엇인가 — 용어(UAV·UAS·RPAS·sUAS·드론·초경량비행장치), 분류(고정익·회전익·멀티로터·VTOL·하이브리드), 크기·무게 등급(KR/US/EU), 쓰임새 지도, 한 대의 해부도 | 60 |
| 2 | 역사 I — 사람 없는 비행의 꿈: 1849 풍선, 1898 테슬라, 1917 케터링 버그·휴잇-스페리, 1935 퀸 비와 "드론"이라는 이름, 라디오플레인 OQ-2, V-1, 파이어비, 이스라엘의 정찰 UAV, 프레데터·글로벌 호크, RC 취미의 계보 (사실 위주, 운용 세부 없음) | 120 |
| 3 | 역사 II — 멀티로터의 부활과 대중화: 1907 브레게-리셰, 1922 드 보테자, 1956 컨버터윙스, MEMS·리포·BLDC·스마트폰이 만든 2005–2010 전환점, MultiWii·Paparazzi·ArduPilot·PX4·Betaflight 계보, Parrot AR.Drone, DJI Phantom→Mavic, 레이싱, 배송(Zipline·Wing·Prime Air), 산업·농업, 규제 연대기, 드론쇼 연대기(2012 Spaxels → 2018 평창 → 기록 경신 — 2026-09 기준으로 재확인) | 140 |
| 4 | 기술 I — 기체와 추진: 프레임 기하, 프로펠러(모멘텀 이론 T1, 블레이드 요소 개념, kT·kQ), 반토크와 요(T3), BLDC·KV·ESC·PWM/DShot, 배터리(C율·에너지 밀도·비행시간 T2), 무게 예산과 추력 대 중량비, 진동과 밸런싱 | 140 |
| 5 | 기술 II — 센서와 상태 추정: MEMS 자이로·가속도계 원리, 자력계와 자기 간섭, 기압계, GNSS(T26)·RTK, UWB·광류·ToF·라이다·VIO, 자세 표현(오일러 T5·회전행렬 T4·쿼터니언 T6–T7), 상보 필터(T23), 칼만 필터(T24–T25), 캘리브레이션 | 200 |
| 6 | 기술 III — 통신과 소프트웨어: RC 링크(2.4 GHz·FHSS·ELRS), 텔레메트리, MAVLink 패킷 해부(실제 바이트·CRC 검증 예제), 비행 컨트롤러 하드웨어, 펌웨어 3대의 구조(발췌), 지상국, 영상 링크(아날로그 vs 디지털), 페일세이프·RTH·지오펜스, 원격 ID, 로그 분석 | 140 |
| 7 | 수학 준비 — 1학년을 위한 도구 상자: 벡터·내적·외적, 행렬·행렬식·역행렬·계수, 미분과 테일러 전개, 선형 미분방정식과 특성방정식, 복소수와 오일러 공식, 뉴턴 법칙·토크·각운동량, 증명 읽는 법(가정·단계·사용처) | 120 |
| 8 | 수학 II — 강체와 쿼드로터 모델: 뉴턴-오일러(T8), 관성 텐서, 쿼드로터 6자유도 모델과 믹서(T9), 언더액추에이션(T10), 호버 선형화(T11), 미분 평탄성(T12), 시뮬레이터 `rigidbody.py`·`quadrotor.py` 코드 대조 | 180 |
| 9 | 수학 III — 자세·위치 제어: 피드백 직관, 1차·2차 응답(T13–T14), PID와 I항(T15), 안정성(T16), 캐스케이드와 시간 척도(T17), 쿼터니언 자세 제어(T18–T19), SE(3) 소개(T20), 이산화(T21), 필터와 D항(T22), 포화·믹서 우선순위, 튜닝 실무(Ziegler–Nichols·Betaflight 발췌), 실패 사례 캡처 | 220 |
| 10 | 수학 IV — 궤적·편대·할당: 다항식 궤적과 최소 저크/스냅(T27), 속도 프로파일(T28), 베지어·스플라인 소개, 경로 계획(A*·RRT 소개), 편대와 합의(그래프 라플라시안 소개), 충돌 회피 개념(속도 장애물·포텐셜), 목표 할당(헝가리안 T29, 무교차 보조정리 T30, CAPT T31), 격자·구·포아송 간격(T32) | 200 |
| 11 | 드론쇼 I — 원리와 산업: 쇼의 구성 요소(RTK·시간 동기·LED·지상국·안전 파일럿), 운영 절차(설계→시뮬→검증→현장), 규제(KR 특별비행승인·야간, US 107 waiver, EU), 안전 설계(지오펜스·간격·바람·배터리·예비기·비상 착륙), 조명과 촬영(T33–T34), 산업 지도(회사·플랫폼·비용 구조, 2026-09 기준) | 150 |
| 12 | 드론쇼 II — 제작 툴: 파이프라인 개요, Skybrush(Studio for Blender·Server·Live, 프로토콜 스펙, 파일 형식), Blender 기초와 `bpy` 생성 코드(실행 안 한 코드임을 명시), Drone Show Software, Verge Aero, 기타(조사 후 확정), 파일 형식 비교, 우리 시뮬레이터의 CSV/JSON 내보내기 | 120 |
| 13 | 드론쇼 III — 트릭 모음: 이미지→점(에지·포아송·Lloyd), 전환 설계(할당·직선 vs 곡선·시간 = 거리/속도), 불 끄고 이동, 2.5-D와 관객 시점, 회전 볼륨과 층 깊이, 텍스트 가독성 대 점 예산, 모핑, 파동·나선 위상 트릭, 조명만으로 움직임, 색 디더링, 이륙·착륙 격자와 스태거링(T35), 예비기 배치, 클리셰 갤러리(하트·지구·QR·카운트다운) | 150 |
| 14 | 시뮬레이션 I — 파이썬으로 만드는 드론쇼: 설계(SPEC) → 벡터·쿼터니언 → 강체 → 모터·믹서 → PID·캐스케이드 → 센서·추정 → 궤적 → 포메이션 → 할당·충돌 → 쇼 파일·렌더 → CLI, 각 단계 테스트(RED→GREEN 캡처) | 200 |
| 15 | 시뮬레이션 II — 자바스크립트 이식과 덱 안의 쇼: 골든 벡터 파리티, 캔버스 투영·카메라·LED 글로우, 데모 6종의 구조, node 테스트, 파이썬↔JS 차이(정수·부동소수·모듈) | 180 |
| 16 | 실습 — 쇼 한 편 만들기 A to Z: "TREASURE" → 하트 → 지구 → 카운트다운, 12/60/300대 버전, 물리 모드 추적 오차표, CSV 내보내기, 체크리스트 | 80 |
| 17 | 미래와 진로 — 배송·UAM/eVTOL(개념), 규제 흐름(원격 ID·U-space·K-드론시스템), 안전·프라이버시·소음·환경, 군사 이용 논쟁(중립 서술), 진로와 자격(초경량비행장치 조종자 증명, Part 107) | 60 |
| A | 부록 — 정리 색인(생성) · 기호표(생성) · 연표 전체(생성) · 쇼 기록표(생성) · 규제 비교표(생성) · 도구 비교표 · 용어집 · 퀴즈 색인 · 출처 목록 | 80 |
| | **Total** | **2,558** (cap 3000) |

Topic candidates inside each part are the builder's to verify against `docs/` and `data/`. Fixed
rules: every theorem in §3.5 has its own slide(s); every part 14–15 module has a RED capture, a
GREEN capture and a `CODE` window; every trick in 13부 is a function in the simulator; the reader
can skim 7–10부 by the `THM` boxes alone.

---

## 5. Steps (in order; one commit each unless noted)

0. Read §0–§4 of this file, `git/PLAN.md` §0–§1 + its last three progress-log entries,
   `transformer/PLAN.md` §4 + the math-kit CSS block, the docstrings of `git/deck/build_deck.py`,
   `git/run_all.py`, `git/tools/record.sh`, and `template.html`'s "사용법" slides. Say in the log
   what you copied. Run `free -m`; if another session is building (goevo is, as of 2026-09-24),
   keep to **one** subagent.
1. **Skeleton** (`make all SKEL=1` green): `drone/` tree, Makefile (targets: help docs data
   data-check test-py test-js parity run run-check record figs figs-check figs-png tables width
   deck deck-verify deck-slices deck-xref deck-check claims-check thm-check font font-check all
   clean), copied tooling with the §1 adaptations (`THM`, `SHOW` directives), `base/head.html`
   palette (§9 decision 4) + math kit, 18 part covers + reading-guide placeholders, `.gitignore`
   entries (`/drone/docs/`, `/drone/scratch/`). Nothing in index/README yet.
2. **`fetch_docs.py` + `html_text.py` + `pdf_text.sh`/`pdf_sections.py` + `excerpt.py`** with
   tests RED → GREEN; install poppler-utils (decision 7); `make docs`; commit tools + tests +
   `docs/FETCHED.txt` + `data/excerpts/` only (docs/ is a cache). Record in the log which URL
   worked for 항공안전법 article text and for eCFR Part 107.
3. **`SPEC.md`** in full: frames, units, `params.tsv` values with reasons, controller structure and
   rates, show JSON/CSV schema, formation generator signatures, the golden-vector list with
   tolerances, the two run modes, the seeded RNG (xorshift128+ constants pinned; Python uses the
   same generator implemented by hand — **not** `random.Random`, so both languages draw identical
   streams). Both test suites quote it.
4. **Data + theorems**: `symbols.tsv`, `theorems.tsv` (≥ 90 rows: the 35 of §3.5 plus lemmas and
   7부 tool statements), `params.tsv`, `cite_keys.tsv`, `law.tsv`, `firmware.tsv`, `tools_show.tsv`;
   `claims.md` seeded. `make data-check thm-check` green. Split: (a) symbols/theorems/params,
   (b) law/firmware/tools/cite keys.
5. **Python simulator** (`py/`), module by module in SPEC order, each with RED → GREEN tests and
   the formula witnesses of §3.5 as they become expressible: vec3/quat (T4–T7) → rigidbody (T8) →
   motor/mixer/quadrotor (T1–T3, T9–T11) → pid/attitude/cascade (T13–T19, T21–T22) → sensors/
   estimator (T23–T26) → poly/profile (T27–T28) → formation/assign/collide (T29–T32) → show/render
   (T33–T35 tables) → cli. Save the RED and GREEN test output of each module with `record.sh` into
   `out/red_<module>.txt` / `out/green_<module>.txt` (these are 14부's captures). One commit per
   module or module pair. Then `write_golden.py` → `golden/`; commit.
6. **JavaScript port** (`js/droneshow.js`): tests in `js/test/` RED against `golden/` first, then
   the port section by section; `make parity` green; `js/demo.js` renderer with a DOM-stub smoke
   test. Then `ex/` programs (mavlink_parse, gps_trilateration, hover_power, battery_time, routh,
   blender_* — the Blender ones are not executed here, but they must at least `python3 -m
   py_compile` and their `bpy` calls must be CITE-able) with tests where executable.
7. **Experiments** (`exps/`, `run_all.py`): batches in part order (4, 5, 6, 8, 9, 10, 11, 13, 14,
   15, 16) — each capture ≤ 60 s; `record.sh --check` ×3 identical. One commit per batch.
8. **History tables**: `timeline.tsv` (≥ 220 rows), `shows.tsv` (≥ 60), `products.tsv` (≥ 80),
   `quotes.tsv`, with `claims.md` rows — 2–3 commits (pre-2005 / 2005–2019 / 2020–2026-09 with
   WebSearch verification). This step may run as the single subagent while step 7 runs in the
   foreground — its brief is `scratch/BRIEF_history.md` containing §0.3–§0.5 and §3.2 verbatim.
9. **Sections** in order 0 → 7 → 8 → 9 → 10 → 14 → 15 → 4 → 5 → 6 → 1 → 2 → 3 → 11 → 12 → 13 → 16 →
   17 → A (maths and simulators first, because every later part cites their theorem ids and
   captures; history last, because it needs the tables of step 8). `make all` after each part;
   commit per part with the slide count in the subject.
10. **Figures** (`gen_figs.py`, `make figs figs-png`, look at every PNG) and `SHOW` snapshots
    (look at a heart, a globe and a text frame at 374 px width).
11. **Demos** (`demos.js` assembly, `check_deck.js` expectations, hand-test in a browser if one is
    available; otherwise the DOM-stub run plus a careful read).
12. **Wrap-up**: `make all` green without `SKEL=1`; `make font`; `index.html` card in the section
    chosen by §9 decision 2 + `README.md` line, with the real counts printed by the build (slides,
    parts, chapters, theorems with full proofs, captures = files in `out/`, tests passed in py/js,
    demos, quizzes); `history.md` entry (≤ 12 lines, top of file); commit.
13. **Review 1 — facts and citations** (≤ 1 subagent while goevo runs; per-part plain-text dumps in
    `scratch/review1/`, BRIEF.md with §0 rules): every date/count/name against `docs/` and
    `claims.md`, post-2024 facts re-fetched, licence headers on excerpts, Korean style. Fix,
    rebuild, commit with the defect counts by kind in the subject (repo convention).
14. **Review 2 — proof audit**: for every `full` theorem, a checklist per proof: hypotheses stated,
    each step justified by a 7부 tool or an earlier theorem, hypothesis-use line present, witness
    test exists and is green, no `심화` prerequisite, level badge correct, statement identical to
    the tsv. Report as `scratch/review2/proofs.tsv`; fix; commit with counts.
15. **Review 3 — freshman reading flow + device**: read parts 7–10 and 14–16 as the target reader
    (do the exercises), check every slide at 374 px (`check_slices.py`, `width`), run the six demos
    in the DOM stub, verify sibling-deck overlap is by link not by copy. Fix; commit.
16. Append the progress log entry after every commit (below).

---

## 6. Checks the build must pass (`make all`)

`data-check` (tsv schemas; no bare-Wikipedia sources; post-2024 rows carry `fetched`) ·
`thm-check` (every `.thm` id in `theorems.tsv`; `full` ⇒ witness test named and present in
`py/tests`; no `심화` prerequisite under a `1학년` proof; every `THM` referenced at least once) ·
`test-py` (unittest, all green, ≤ 90 s) · `test-js` (`node --test`) · `parity` (golden ↔ JS at
1e-9) · `run-check` (manifest sha256 vs `out/`) · `figs-check` · `deck` (cap 3000, part budgets,
`<pre>` 45×72, captures 108, `<li>` ≤ 14, no box-drawing, no hand-typed page numbers, unique
`article` ids, every proof slide has exactly one level badge, no `<script src=`/`<link href=http`) ·
`deck-verify` (CODE/OUT/TABLE/SHOW bytes match sources) · `deck-slices` · `deck-xref` (ids,
"(N부)", theorem ids, symbol ids) · `deck-check` (node DOM stub: engine keys ←→↑↓, gamepad hook,
demos' expectations) · `claims-check` (every CITE resolves; every 4-digit year, drone count and
article number in prose has a claims/data row) · `width` · `font` + `font-check`. `make all`
prints the slide count and the "오류 N건" line; read it every time.

---

## 7. Card text (fill from the build, never by hand-count)

"🛸 1849년 무인 풍선에서 2026년 수천 대 드론쇼까지 — 역사·기체·센서·통신·펌웨어를 훑고, 강체
동역학·쿼터니언·PID·캐스케이드·최소 스냅·헝가리안 할당을 **대학 1학년 수준의 증명 T개**로
다지는 PPT형 M부 K장 S슬라이드. 드론쇼의 원리·제작 툴(Skybrush·Blender·DSS·Verge Aero)·트릭
N종을 다루고, 파이썬(표준 라이브러리만)과 자바스크립트로 같은 스펙의 드론쇼 시뮬레이터를
직접 만들어 덱 안에서 재생. 테스트 P개·캡처 C개·데모 D종·퀴즈 Q문 🚁" — the numbers come from
`make all`'s summary line.

---

## 8. Risks and how the plan handles them

| Risk | Mitigation |
|---|---|
| Wrong dates/counts/names from memory (records, launches, article numbers) | claims.md + CITE resolver; post-2024 rows must be `fetched`; Guinness/press numbers labelled by kind |
| Proof that is wrong or too hard for a freshman | theorems.tsv levels + prerequisites; `thm-check`; witness tests; proof audit (step 14); narrow the hypothesis rather than hand-wave |
| Formula ↔ code drift | every numeric formula has a `py/tests` witness; JS parity on golden vectors |
| Memory kill (two sessions on the device) | ≤ 1–2 subagents, one simulator process, ≤ 20 physics drones, kinematic mode for big shows, checkpoints, Monitor for long runs |
| Non-deterministic captures | seeded hand-written RNG in both languages, fixed float formats, no timings, `record.sh --check` ×3 |
| Blender cannot run here | `bpy` code shown as not-executed with a caption; every call CITEd to the API docs; our exporter produces the CSV/JSON Blender-side scripts consume |
| Skybrush CSV/`.skyc` format not fully public | verify in the Studio docs and `libskybrush`; if not documented, label ours as an attempt and mark `unv` |
| Slide inflation past 3000 | assembler hard cap; part budgets +10 %; proof continuation slides counted in budget |
| Regulation text unreachable (law.go.kr JS shell) | try the search URL / DRF API / drone.onestop.go.kr; if the article text cannot be fetched, quote only what onestop states and mark article numbers 미확인 |
| Sensitive military content | §0.13: encyclopedic only; review 1 checks every 2부/17부 slide against that rule |
| Overlap with 무선통신/최적화/트랜스포머 decks | link by name; review 3 checks by example text |

---

## 9. Decisions for the user (recommendation first; the user's answer is final — do not re-ask)

1. **File and title:** `드론의_모든_것.html`, title "드론의 모든 것", brand "🛸 드론의 모든 것".
   *(Recommended.)*
2. **Index/README section:** a **new section "🛸 드론 & 비행 로봇 🚁"** placed right after
   "📡 네트워크 & 무선", with this deck as its first card. *(Recommended; alternative: under
   "🔢 수학 & 알고리즘".)*
3. **Directory:** `drone/`. *(Recommended.)*
4. **Palette:** night-sky navy background gradient (`#0b1026` → `#1b2350`), white cards, LED cyan
   `#22d3ee` as accent, magenta `#f472b6` as the second show colour, amber `#f59e0b` as `--special`
   (evidence colour), titles in navy `#1e293b` on cards. *(Recommended.)*
5. **Reader level:** first-year university, with 7부 as the only prerequisite for `1학년` proofs;
   `심화` results are sketches + citations. *(Recommended.)*
6. **Python dependencies:** **stdlib only** for the simulator, examples and tools (no numpy;
   pure-Python PNG/SVG writers). *(Recommended — runs on any machine the reader has, deterministic,
   matches repo practice; alternative: numpy in a gitignored venv for speed, which changes every
   code slide.)*
7. **System package:** install `poppler-utils` via apt for `pdftotext` (papers). *(Recommended;
   alternative: cite abstracts only.)*
8. **Comment language in `py/`/`js/`:** Korean comments (teaching code), English identifiers.
   *(Recommended; alternative: English comments as in goevo.)*
9. **Images:** none — no photos, logos or tool screenshots; SVG schematics generated from data
   with "개념도" captions. *(Recommended, as in every sibling deck.)*
10. **Blender code:** shown as CODE with an explicit "이 기계에서 실행하지 않음" caption and
    per-call CITEs to the API docs; our exporter produces the files it consumes. *(Recommended;
    alternative: omit Blender code and describe the workflow only.)*
11. **Simulation modes:** `physics` (≤ 20 drones) + `kinematic` (≤ 500 drones), both stated on
    slides. *(Recommended; alternative: physics only, shows capped at 20 drones.)*
12. **Coordinate frames:** ENU/FLU in our simulator with one conversion slide to PX4's NED/FRD.
    *(Recommended; alternative: NED throughout, which makes "z up" formations awkward for readers.)*
13. **Demos:** the six of §3.7. *(Recommended; alternative: show player + formation lab only.)*
14. **Review depth:** three review passes (facts, proof audit, reading flow) before push.
    *(Recommended — the proof audit is new and specific to this deck; repo norm is 2–3.)*
15. **Military history depth:** one chapter in 2부 plus a neutral debate slide in 17부, dates and
    programme names only. *(Recommended; alternative: omit military history except as timeline rows.)*

---

## Progress log (append only; newest at the bottom; one entry per commit)

### Plan written (2026-09-24)

- PLAN.md written by the orchestrator (Fable) after verifying §2 on this machine (source
  reachability, missing pdftotext/numpy, memory state). No code, data or docs fetched yet. Waiting
  for the user's answers to §9 before step 1.

### §9 decisions confirmed (2026-09-24)

- The user confirmed all 15 recommendations of §9 as written ("권고안 그대로 확정"). **Do not re-ask
  any of them.** Step 1 (skeleton) may begin. Nothing else changed.

### Step 1 — Skeleton (2026-09-25)

- Step 0 read: §0–§4 here, goevo/PLAN.md step 1–4 log (the freshest copy of the git/deck
  lineage), goevo build_deck/cites/check_claims/check_xref/verify_deck/gen_glossary/
  check_deck.js/Makefile/record.sh. **Copied from goevo/ instead of git/** (deviation, same
  lineage one generation later): deck/{build_deck,verify_deck,check_slices,check_xref,
  check_claims,chunks,gen_glossary,svgkit,cites}.py, check_deck.js, base/{head,tail}.html
  (tail carries the 2026-09-24 ←→ fix; head already carries the transformer math kit incl.
  .thm/.proof/ol.pf), tools/{width,rewrap}.py, tools/record.sh. goevo's per-part split
  (deck/claims/pNN.md, deck/glossary/pNN.txt) is kept so one subagent can write a part
  while the foreground writes another.
- build_deck: TARGET `드론의_모든_것.html`; LANG_OF py/js/json/csv/tsv/xml/txt/sh/c/cpp;
  find_symbol learned `.js` (function/class/const and indented methods); GOVER and REL
  removed; **THM** (`<!--THM id=T14-->` → statement box + level badge from theorems.tsv,
  `cont` → continuation header with the badge only), **WITNESS** (`<!--WITNESS id=T14-->` →
  the witness-test name from the tsv) and **SHOW** (imports py/droneshow/render.py and calls
  `snapshot_svg(show, frame, view)`; wrapped in `<div class="show" data-show data-frame
  data-view>`) added; verify_deck re-renders every SHOW and compares bytes. HARD_CAP 3000,
  budget +10 % error. APPENDIX = section 18 (`p18-quiz-index-N`, `p18-gl-N`). COVER_DIRS
  py/ js/ ex/ (full) + exps/ tools/ Makefile run_all.py (partial); `ex/blender_*` partial.
- deck/cites.py: keys only from data/cite_keys.tsv, columns **key | name | url | kind |
  licence | file** (name and file added to §1's list: the badge needs a name, the resolver a
  path). New deck/check_thm.py (`make thm-check`): tsv schema, unknown/심화 prerequisites
  under 1학년 full proofs, full ⇒ witness `path::name` whose `def` (or node `test('name')`)
  exists, cited ⇒ cite-key in cite_keys.tsv; sections: THM ids exist, every `.proof` slide
  has exactly one level badge, and (without `--skeleton`) every tsv row is used.
  check_claims: version check dropped; **drone counts** (`N대`, N ≥ 100, comma-insensitive,
  own-simulator counts in deck/counts_ok.txt) and **article numbers** (`제N조(의M)`,
  `§107.N`) must appear in claims/data. check_xref: version badges dropped; bare "N부" must
  be 0–17; "정리/보조정리/도구 T14|L3|M5" must be a theorems.tsv id.
- Palette (decision 4): bg #0b1026→#121838→#1b2350, accent #22d3ee with **--accent-ink
  #0e7490** for text, --show2 #f472b6 / --show2-ink #be185d, --special #f59e0b with
  **--special-ink #a16207** for text (amber on white is ~2:1), titles #1e293b; g1–g8 = the
  eight timeline kinds; `.lv.l1/.lv.adv`, `.thmref`, `.witness`, `.show` (dark sky panel).
- Makefile: every §5 step-1 target + `test`; SKEL=1 → `--skeleton` for thm-check and
  deck-check; targets whose tool does not exist yet print which step adds it.
- tools/tests/test_deck_rules.py: 31 tests — RED 22 failures on stubs (the 9 passing were
  the cite resolver written first and the constants), then GREEN.
- Sections: cover + 0부 (7 placeholder guide slides) + 17 part covers + 부록 cover = 27 slides.
- `make all SKEL=1`: exit 0, 27 slides, 14 placeholders, DeckMono 6 KB. Not in index/README.

### Step 2 — Primary-document tooling, cite keys, docs cache, excerpts (2026-09-25)

- Commits: fccf334 (tools + tests + 14 fixtures), ee607be (data/cite_keys.tsv 57 rows,
  docs/FETCHED.txt, data/excerpts/ 5 + INDEX.tsv). poppler-utils 26.01.0 installed via apt
  (decision 7).
- tools/html_text.py (from goevo, widened): `§ heading` for h1–**h6** (EASA puts its body
  headings in h5 — deviation from "h1–h4") and `<dt>` except Sphinx field lists ("Type:");
  **`§ #id` anchor lines** for id-bearing headings/dt and for `<section id>`/`div.section`
  that open with a heading (Drupal `block-*` ids dropped) — CITE can use the URL fragment
  (`#HEARTBEAT`, `#bpy.types.Object.location`, `#107.29`). Drops nav/footer/aside/button/
  script/style and ¶/zero-width anchors; `<header>` inside `<main>` is kept (EASA title).
  `convert_ecfr` (HEAD → §, DIV8 N → `§ #107.29`) and `convert_law` (법제처 DRF XML: 장 →
  §, each 조문 → `§ 제129조` + `§ 제129조(제목)`, then 항/호/목 lines; 부칙·별표 skipped).
- tools/pdf_text.sh + pdf_sections.py: `pdftotext -layout` first; if > 40 % of lines have an
  inner 3-space gap (two-column paper) it re-extracts in reading order (deviation: -layout
  interleaves IEEE columns). Headings: numbered (≤ 8 words, no comma, no final period, first
  number ≤ 20, a 3-letter word), roman/lettered, ALL-CAPS (small-caps "R EFERENCES" joined,
  wrapped caps lines merged, running heads > 3× dropped), named words (Abstract, Contents…);
  TOC lines skipped. 1003.2005 → 15 clean sections, Madgwick → 25.
- tools/fetch_docs.py: reads cite_keys.tsv (validates columns/kind/https/.txt/unique),
  dispatch by content+URL (pdf/c/md/ecfr/law/html/xml/json/text); C/C++ gets `§ file` +
  `§ Class::function` before each top-level definition (`{` before `;` within 8 lines,
  `__attribute__` stripped, comments skipped; source lines unchanged). Sends
  `Accept-Encoding: gzip` (eCFR API answers **406** without it). 20 s timeout, ×3 retry,
  0.3 s pause; `--missing`, `--only KEY`; FETCHED.txt merged, not truncated, on partial runs.
- tools/excerpt.py: refuses branch URLs (sha must be in the raw URL), ≤ 40 lines, header in
  the language's comment (`//`, `#`, `<!-- -->`): `repo path @sha Lstart-end · licence ·
  fetched date`; `--pin OWNER/REPO PATH` asks the GitHub API; `--all` (= `make data`)
  re-cuts byte-identically from INDEX.tsv after checking the sha against cite_keys.tsv.
- Tests: tools/tests/test_docs_tools.py, 58 tests; RED 45 failures on stubs (assertions,
  after two index/IndexError tests were rewritten as assertions), +2 RED later for PDF
  formula debris ("1 T T", "2 Ω d") and "vs." titles found on the full papers; GREEN.
  `make test` 89 OK (31 + 58). width.py clean on all new tools.
- Sources that worked (57/57 fetched, 0 failed):
  - 항공안전법 text: **`https://www.law.go.kr/DRF/lawService.do?OC=test&target=law&type=XML&ID=012524`**
    (법령ID, so it always returns the current version; MST=286927 gave identical bytes on
    2026-09-25 — 공포 2026-06-16 제21822호, 시행 2026-09-17). Same API: 시행령 ID=012843,
    시행규칙 ID=012848 (제312조의2 특별비행승인 is there), 드론법 ID=013479. IDs came from
    `DRF/lawSearch.do?OC=test&target=law&type=XML&query=…`.
  - eCFR: **`https://www.ecfr.gov/api/versioner/v1/full/2026-09-23/title-14.xml?part=107`**
    and `…?part=89` (date = `up_to_date_as_of` from `/api/versioner/v1/titles.json`; needs
    gzip). Pinned date — bump it when re-fetching for a later session.
  - Madgwick report: x-io.co.uk returns **403** (Cloudflare) even with a browser UA; fetched
    from `https://www.samba.org/tridge/UAV/madgwick_internal_report.pdf` (same 1.5 MB report,
    "April 30, 2010").
  - Mellinger–Kumar 2011 and Turpin–Michael–Kumar CAPT 2014: kumarrobotics.org lists both
    (teachPress search `?tsr=`) but links no PDF → cited via Crossref JSON
    (`api.crossref.org/works/10.1109/ICRA.2011.5980409`, `…/10.1177/0278364913515307`);
    prove the results ourselves (§3.5) as planned.
  - Skybrush docs moved: doc.collmot.com → `docs.skybrush.io/public/…`; the CSV import format
    is on Studio's `panels/formations/formations.html` (dt "From static CSV file": `Name,
    x_m, y_m, z_m, Red, Green, Blue`; zipped per-drone CSV with `Time_msec`). Plugin repo is
    `skybrush-io/studio-blender` (GPL-3.0).
  - drone.onestop.go.kr: systemintro1/2/4 fetched; no `<main>`, so the text starts with the
    menu (content follows). Special-flight procedure text is thin there — cite the 시행규칙.
- Not added: PX4 parameter reference (3.7 MB — too big), ardupilot `copter/docs/tuning.html`
  (page says "superseded and ARCHIVED" — used tuning-process-instructions + common-tuning),
  history/Wikipedia rows (later step).
- Licences recorded: PX4 BSD-3-Clause, ArduPilot/Betaflight/Skybrush/crazyflie GPL-3.0
  (GitHub API spdx). **MAVLink is not plain MIT**: mavlink/mavlink COPYING = (L)GPL-3 for the
  generator/definitions with an MIT grant for generated code → rows say "LGPL-3.0 (생성 코드는
  MIT)"; c_library_v2 has no licence file of its own, recorded "MIT (MAVLink 생성 코드)".
- Excerpts (data/excerpts/, INDEX.tsv has the why):
  - px4-att-quat-error.cpp — AttitudeControl.cpp L141-180 @2a0e0481713c (2026-06-26)
  - ardupilot-thrust-vector-rotation.cpp — AC_AttitudeControl.cpp L1064-1103 @e4b7c11761da
    (2026-08-30): `thrust_vector_rotation_angles` (thrust_heading_rotation_angles still
    exists but delegates the two-rotation split to it)
  - betaflight-antigravity-dterm.c — pid.c L1126-1154 @46acf611013e (2026-09-17)
  - mavlink-heartbeat.xml — **minimal.xml** L747-755 @2e0efccfa88e (2026-08-27): HEARTBEAT
    is no longer in common.xml (common → standard → minimal include); cite key
    `mavlink-minimal-xml` added (common.xml @dc252db7ba20 kept for the rest)
  - mavlink-crc-accumulate.h — c_library_v2 checksum.h L22-55 @27ffe84e79d2 (2022-01-06)
- For later steps: upstream lines exceed 72 columns (PX4/ArduPilot/Betaflight comments reach
  100–200) — CODE slides need `lines=` sub-windows or a wrap policy; the header line (full
  40-char sha) is ~150 columns, so CODE should start at line 2 (build_deck LANG_OF already
  maps .h/.xml). check_claims: 57 keys, 0 missing.

### Step 3 + 5 — SPEC.md and the Python simulator (2026-09-25)

- Commits: 0eb2fd3 (SPEC.md, data/params.tsv, 9 base modules), 3ed2205 (control, estimation,
  trajectory), 7c84fea (formation/assign/collide/show/tricks/render/cli + golden/ 11 files).
  `py/droneshow/` 21 modules, 2,364 lines (cap 3,000; largest formation.py 224); 223 tests,
  ~11 s (`python3 -m unittest discover -s tests -t .` in py/). Widths clean.
- **RNG deviation:** xorshift128 on four 32-bit words instead of xorshift128+ (the + variant
  needs 64-bit integers = BigInt in JS). SPEC §2 pins the state/seed rule; Box–Muller.
- tools/testcap.py + testcap_run.py: timing-free test captures (`green MODULE`), and
  **reproducible RED**: `red MODULE` copies py/ to scratch/red and replaces every function
  body of that module with `raise NotImplementedError('구현 전')` via ast — names and
  signatures stay, so the RED is "not implemented", never an import error. Runs the tests as
  one suite (class fixtures work). 14부's RED/GREEN captures come from this (run_all).
- Measured facts that **changed the plan's statements** (fix the slide, not the oracle):
  1. **T17** — lowering only the *sample rate* of the rate+attitude loops to 50 Hz does not
     break the cascade (tilt 20.0° vs 19.9°); lowering the rate-loop *gain* (bandwidth) to a
     quarter of the attitude gain does (tilt > 2×, never settles). SPEC §5.6 updated;
     p09_timescale must use the gain version and show the 50 Hz non-failure too.
  2. **T30 as written in §3.5 is false.** Counterexample (test_assign.Crossing): a1 = X − u,
     b1 = X + 10u, a2 = X − 10w, b2 = X + w, u·w = 0.9 — paths cross, squared cost keep 242 <
     swap 383.8. The classic non-crossing result holds for the **plain** distance cost
     (triangle inequality). Restate T30: "plain-distance optimum has no crossings (full);
     squared optimum may cross (counterexample)". What squared costs *do* give: every pair of
     the optimum satisfies (a_i − a_j)·(b_i − b_j) ≥ 0 (else a swap lowers the cost by
     −2(Δa·Δb)), hence under synchronised straight-line motion |x_i − x_j|² = (1−β)²|Δa|² +
     β²|Δb|² + 2β(1−β)Δa·Δb ≥ δ²/2 — distance ≥ δ/√2 (δ = min start/goal spacing). That is
     T31's full freshman proof (CAPT core, any dimension); formations for a dmin show must be
     spaced √2·dmin. test_assign also finds a plain-cost assignment that collides.
  3. **T12** — the yaw rate from flatness is r = (β p + ψ̇ y_B·y_C)/α (α = x_C·x_B, β = x_C·z_B),
     obtained by differentiating y_B ⊥ x_C; it matches finite differences of the attitude to
     1e-6. The often-quoted r = ψ̇ z_W·z_B is not exact for this construction — do not put it
     on a slide without the source text.
  4. Circle tracking (r 2 m, 0.8 rad/s): max error 1.28 m without feed-forward, 0.36 with v,
     0.086 with v+a, 0.115 with v+a+jerk-rates; with drag off 0.057/0.053 — the unmodelled drag
     (not the missing jerk term) dominates. 9부 shows this 4-level table.
- Show format extended (SPEC §9.1): optional 8th keyframe element = segment kind (T/S/J/L)
  and an optional per-drone `lights` track, so light-only tricks never touch motion.
  Colour rounding uses floor(x+½) (Python's round is banker's; JS Math.round is not).
- Tricks as functions (tricks.py): dark_move, takeoff (stagger by target height), under_count
  (downwash exposure metric), layered_depth, rotate_volume, wave, led_only_motion, dither.
- golden/: rng, quat, mixer, hover, pid, physics (3 drones × 4 times), poly, assign
  (n = 5…50), profile, formation (9 shapes), show12 (+ frames every 10). test_golden checks
  they are current.

### Step 4b — data-check, law / firmware / show-tools tables (2026-09-25)

- Commits: 9468acf (tools/data_check.py + tools/tests/test_data_check.py, 34 tests),
  74ede3e (data/law.tsv 69, firmware.tsv 9, tools_show.tsv 15, header-only timeline/shows/
  products/quotes, cite_keys.tsv +34 keys = 91, docs/FETCHED.txt).
- data_check: exact headers, empty required cells (line numbers), cell count, kinds
  (jurisdiction KR|US|EU, tools kind design|server|live|sim|hardware, open-source
  yes|no|partial, timeline kinds, shows record Guinness|claimed|none), drone-count a plain
  integer, dates YYYY|YYYY-MM|YYYY-MM-DD checked against the calendar (products.year YYYY
  only), source = cite key or https:// (any *.wikipedia.org host rejected; several sources
  joined by ';'). verified-how must start `fetched|websearch YYYY-MM-DD` for rows dated
  >= 2025 **and for every row of the "current state" tables** (law, firmware, tools_show —
  licences, articles and product features change; deviation: the brief only asked for
  dated rows). `미확인` is allowed only in firmware first-release/attitude-representation
  and only if verified-how says why. Law: `제N조(의M)` must be an exact `§ 제N조` heading,
  `§N.M` an exact `§ #N.M` line (so 제131조 does not pass on 제131조의2, §107.2 not on
  §107.29); anything else (EU `Article 4`, `UAS.OPEN.020`, `PART 1`) is found in the body
  with a boundary (Article 4 != Article 40). A `docs §HEADING` quoted in verified-how must be
  a § line of the cited doc. Below-minimum tables are warnings printed as "(미달)"; exit 1
  only on errors. RED: 30 failures / 4 passing on stubs (all assertion failures), then GREEN.
- New sources (all fetched 2026-09-25, 0 failed): EUR-Lex consolidated
  **2019/947 @2025-05-01** and **2019/945 @2025-06-24** (latest consolidations listed on the
  ELI pages; html_text gives no § lines for EUR-Lex, so EU rows quote the article line in
  verified-how instead of `docs §`). GitHub API repo JSON for PX4, ArduPilot, Betaflight,
  INAV, MultiWii, Paparazzi, crazyflie, crazyswarm and the skybrush-io org listing (licence
  spdx, main language, created_at, fork flag); release-by-tag JSON for Betaflight 2.1.0 and
  INAV 1.0; sha-pinned sources INAV pid.c, crazyflie attitude_pid_controller.c,
  MultiWii.cpp, Paparazzi stabilization_attitude_{quat,euler}_int.c; ArduPilot history,
  Auterion PX4 history, Paparazzi readthedocs; Skybrush home, Blender licence, DSS
  (software, creator, EULA), Verge Aero (system, studio, VVIZ doc), Finale 3D (import, VVIZ
  spec), Depence, FWsim, DAMODA.
- Facts that surprised: the DSS EULA (rev. 2026-08-07) names **UVIFY CO., LTD. (Korea)** as
  licensor while the site header still shows the SPH logo — vendor written "SPH Engineering /
  UVIFY" with both facts in notes (WebSearch found only a partnership, no acquisition).
  MultiWii: GitHub API has no licence; the source header says GPL-3. multiwii.com is a parked
  domain. Crazyswarm docs say Crazyswarm1 is not recommended for new projects.
- first-release: PX4 2013 (Auterion: born 2011, first stable "two years later"; GitHub's
  earliest release object is v1.0.0-rc4 2014-12 — both in verified-how), ArduPilot 2009,
  Betaflight 2015, INAV 2016; MultiWii, Paparazzi ("founded in 2003" only), Crazyflie and the
  two Skybrush forks 미확인. Attitude: PX4/ArduPilot quaternion, Betaflight/INAV/MultiWii/
  Crazyflie (PID controller only) Euler, Paparazzi both (two implementations).
- Every law article was found in the fetched text (69/69). Not added: Part 107 Subpart D
  categories 2–4, 107.145; KR 벌칙 조항.
- `make test` 136 OK (includes other sessions' new tests), `make data-check` 통과 (timeline/
  shows/products 미달 warnings), `check_claims.py` 0 missing, width clean.

### Step 6 + 4a — JS port, ex/ programs, theorems (2026-09-25)

- c790577: js/droneshow.js (1,070 lines, one IIFE, sections = py modules) + js/test/
  parity.test.js (11 golden checks). RED 11/11 on a stub that throws, then GREEN. Parity
  needed three things on the Python side (golden values unchanged or regenerated): Python
  3.12+ `sum()` is compensated (Neumaier) and `math.dist` uses its own algorithm, so the core
  modules now use `vec3.total` (plain left-to-right) and `vec3.dist` (√Σd²); `16*sin³` is
  written as products; **golden inputs are rounded to 9 digits before the outputs are
  computed** (quat/mixer/assign failed at 1e-9 because JS read rounded inputs). node 24's
  `node --test DIR` does not take a directory: Makefile uses `js/test/*.test.js`.
- 533009d: ex/ — mavlink_parse (x25 from the checksum.h excerpt; **CRC_EXTRA computed from
  the message definition = 50**, the value in c_library_v2 minimal.h MAVLINK_MESSAGE_CRCS;
  `uint8_t_mavlink_version` counts as `uint8_t` as pymavlink's mavparse.py does — both files
  peeked with curl, need cite keys `mavlink-minimal-h`, `pymavlink-mavparse` before 6부),
  hover_power (T1), battery_time (T2), routh (T16), gps_trilateration (T26, Newton + normal
  equations, toy geometry), blender_import_show (not executed; tested against a fake bpy that
  records calls). 15 tests. **kQ corrected 1.5e-8 → 1.24e-8**: the old value implied a figure
  of merit 0.50 against params' fm 0.6; now formula 64.2 W and integrated hover 64.05 W agree.
- 34557c6: data/theorems.tsv 91 rows (M1–M28 tools, L1–L28 lemmas, T1–T35), 70 full proofs
  each with a witness `path::test`, no 심화 prerequisite under a 1학년 full proof; T20 cited
  (lee2010-se3), T35 cited (skybrush-formations "Takeoff": layered takeoff ordered to minimise
  downwash). data/symbols.tsv 40 rows (first-slide filled while writing parts).

### Step 7 infra + Part 0 (2026-09-25)

- run_all.py (goevo lineage): ctx.cmd/py (argv run in drone/, `$ cmd` first line with shell
  quoting and `VAR=val` prefixes for env), red/green (tools/testcap), text, table
  (out/tbl_<name>.html, `num=` columns), show (out/show_<name>.json), adopt (a file a command
  wrote into out/). Manifest = files registered in out/batches.json only (deck/gen_tables.py's
  tbl_d_* are data views, checked by `gen_tables.py --check`). tools/tests/test_run_all.py 9
  tests (written right after run_all.py, not RED-first — noted).
- deck/gen_tables.py: tbl_d_params_phys/ctrl_N, tbl_d_symbols_N, tbl_d_theorems_N (level
  badge, kind, statement HTML, link to the first slide with that THM box); 3 tests.
- exps/ORDER p00 p04 p05 p06 p07 p08 p09 p10 p11 p13 p14 p15 p16; exps/p00 (python/node
  versions, `droneshow plan` of ex/spec_hello.json → out/show_hello.json 30 drones, `info`).
- Part 0: 18 slides (cover, 2 part maps, oracles, badges, levels with THM M1, proof anatomy,
  3 notation tables, first show with SHOW snapshot frame 540, code/capture reading, machine,
  siblings, what the deck does not cover, quiz). The SHOW snapshot was rendered to PNG and
  looked at (12 drones do not read as a heart; 30 do). deck/pending.txt lists every py/js/ex
  source until its part is written. `make all SKEL=1`: exit 0, 36 slides.
- params.tsv `why` cells reworded where they asserted unsourced facts about real products.

### Part 7 — 수학 준비 (2026-09-25)

- tools/witness.py (+3 tests): runs the single witness test of a theorem id (loads the test
  file by path — py/tests and ex/tests are both a package named `tests`); exps/pw writes
  out/w_<id>.txt for every theorem with a witness (83). `<!--WITNESS id=…-->` now appends that
  capture (error if missing) — proof slides show the result, not only the name.
- ex/vectors_demo.py, matrix_demo.py, exercises7.py (+ ex/tests/test_exercises.py, 8 tests
  that recompute each answer from the definition); exps/p07: tables small_angle (θ³/6 visibly
  constant), lag (6-DOF RK4 vs 1−e^(−t/τ), diff ≤ 6.4e-8), order (Euler ÷2, RK4 ÷16),
  roots, normal (seed 7).
- Part 7: 94 slides, 9 chapters (vectors, matrices, calculus, linear ODEs, complex numbers,
  Newton, numerical integration, minimum & variance, reading proofs), a "손으로 풀어 보기" per
  chapter answered by the ex/exercises7.py capture, a quiz per chapter. Full proofs written
  out: M1 (law of cosines), M2, M3 (Lagrange), M4, M5, M6 (det = triple product), M7, M10,
  M14 (**integral-inequality proof**: sin θ ≤ θ, 1−cos θ ≤ θ²/2, θ−sin θ ≤ θ³/6, tan t ≤ 2t on
  [0,1] by convexity ⇒ tan θ − θ ≤ 4θ³/3), M15 (y = x e^(−at)), M16, M18 (factor into two
  first-order equations — no "guess the solution" step), M19, M21, M23. Sketches say what they
  skip. p7-read4 tells the T30 story (plan's statement falsified by its own witness).
- Assembler: OUT `lines=N` (single line). check_claims: `§` articles need a 2–3-digit part
  (`§107.29`), so "SPEC §4.3" is not an article.

### Part 8 — 강체와 쿼드로터 모델 (2026-09-25)

- 63 slides (budget 180 — kept dense, no padding; candidates for a later expansion pass:
  inertia tensor from a point-mass model, numeric state-space linearisation at hover,
  full-file walk-throughs). 7 chapters: frames (ENU/FLU vs MAVLink NED/FRD, cited
  `SET_ATTITUDE_TARGET (82)`), rigid-body rotation (L3 sketch, **T8 full**: derivation +
  energy and |Jω| conservation), rotor model (L19 full), X mixer (**L4, T9** — invertibility
  from L4, det = 16a²c by elimination to a 3×3; **T10**), 6-DOF model and code, hover
  linearisation (**T11**), differential flatness (**L26, T12** over two slides: thrust/attitude,
  then p, q from the unit-vector derivative and r from differentiating y_B·x_C = 0).
- exps/p08: tumble conservation vs dt (RK4 ÷16), intermediate-axis flip table, mixer M and
  M⁻¹, allocation cases (**yaw authority at hover is only ≈0.049 N·m**), derived params,
  open loop with one motor +1 % (**roll 148° after 2 s**), linearisation error table,
  flatness rates vs finite differences (≤2e-11), feed-forward levels × drag on/off.
  ex/exercises8.py (+6 tests).
- **Correction:** mixer.py's docstring and SPEC §4.2 claimed the roll/pitch > collective > yaw
  order is "what PX4 and ArduPilot document". The fetched PX4 page documents only Airmode
  (boost or reduce the collective to keep torques); yaw-first sacrifice is now labelled as
  this deck's choice (slide p8-saturation says so, with the CITE).

### Part 9 — 자세·위치 제어 (2026-09-25)

- 87 slides (budget 220), 12 chapters. Full proofs: **T13**; **T14** (solve e(t), ė has a
  single factor sin ω_d t ⇒ first peak at π/ω_d ⇒ overshoot e^{σπ/ω_d}); **T15** (steady state
  ⇒ ż = 1 − x = 0); **T16** over two slides (positive coefficients ⇒ a real root −c by the
  intermediate value theorem; p = (s+c)(s²+bs+e); a₂a₁ − a₀ = b(a₁ + c²) ⇒ stable ⟺ b > 0 ⟺
  a₂a₁ > a₀; converse); **T17** (inner first-order b, outer P k: slow root between k and
  k(1+4k/b) from ε/2 ≤ 1−√(1−ε) ≤ ε/2+ε²/2); **T18** (error quaternion ODE, v̇ = −k|w|v ⇒ axis
  fixed, θ̇ = −2k sin(θ/2), g = ln tan(θ/4) has ġ = −k); **T22** (complex steady state);
  L5, L6, L25. Sketches T19 (with the PX4 excerpt), T21; T20 cited from Lee et al.
  Proposition 4 (§V) — statement checked against the fetched PDF text.
- exps/p09 (15 files): P on first order, PD overshoot table (measured = formula to 5
  digits; ζ≈0.8 settles fastest), PD/PID/saturation/clamp table, cascade poles, time-scale
  table (sample rate 25 Hz harmless; kp_rate 2 fails), attitude law vs closed form (≤4e-12),
  yaw-weight table, D noise split into signal/noise parts, low-pass gains, step/yaw/wind/
  10 m-step flights. ex/exercises9.py (+5 tests); ex/routh.py now fully shown.
- Assembler: `<!--CODE … wrap=1-->` for data/excerpts/ only → `<pre class="wrap">` (CSS
  pre-wrap, ≤ 480 columns — upstream firmware/XML lines cannot be re-wrapped); own sources
  asking for wrap are an error (2 tests). check_slices: the excerpt's line 1 (licence
  header) may be skipped without E3. Makefile `width` no longer scans exps/ (partial quotes
  are re-checked by the assembler's <pre> rule, as in goevo).
- `make all SKEL=1`: every check green except claims-check, which fails only on two cite
  keys the concurrently running history subagent has added but not fetched yet.

### Part 10 — 궤적·편대·할당 (2026-09-25)

- 65 slides (budget 200), 9 chapters. Full proofs: **L11** (t⁴(1−t)⁴ divides the difference),
  **L12** (four integrations by parts), **T27** (J(y) = J(x) + J(h)), **L14, L13, T28** (velocity
  ceiling min(at, a(T−t), v_max) ⇒ area bound ⇒ trapezoid is optimal), **L8, T30** (plain
  distance: triangle inequality with strictness from non-collinearity), **L24** (explicit
  counterexample capture), **L21, L9, L10, T31** (CAPT core; design rule: spacing √2·d),
  **M26, T32**, L16, L17, L23. T29 sketch with a full optimality certificate (u_i + v_j ≤ c_ij,
  tight perfect matching ⇒ optimal). 4–5장 (curves/A*/RRT/consensus/VO) are concept slides
  without claims about products or dates.
- exps/p10: β table, limits, snap-cost perturbations (min increase > 0 over 200), multi-segment
  derivative jumps (C⁶, jump at 7th), profile times (min-snap 1.4–1.9× trapezoid), Hungarian
  relaxation counts (÷n³ ≤ 0.34), brute-force agreement 70/70, **crossing table: plain-cost
  optimum 0 crossings but min distance 0.18δ; squared-cost optimum 80 crossings but ≥ 0.78δ**,
  Fibonacci spacing (m₁√n ≈ 3.09), Poisson spacing, five static shape shows for SHOW.
  ex/exercises10.py (+4 tests).
- Assembler: SHOW counts as evidence for the "실행 검증" badge. SHOW snapshots rendered to PNG
  and inspected: heart/text read well; rings from the top collapse into one circle, so that
  slide uses the audience view.

### Part 14 — 파이썬 시뮬레이터 (2026-09-25)

- 144 slides (budget 200), 9 chapters. Every module: what/why (+ the theorems it witnesses)
  → one test excerpt (`CODE sym=`) → RED and GREEN captures on one slide → FULLSRC. All
  2,364 lines of py/droneshow/ are now shown (pending.txt no longer lists them).
- exps/p14: `red_<m>`/`green_<m>` for 22 modules (+ green_golden), CLI captures (help, plan
  of ex/spec_small.json → out/show_p14.json, info, fly kinematic/physics, csv head). 23 s.
- The section file was produced from a per-module table by scratch/gen14.py (not committed;
  the section file is the source from now on — edit it directly).
- deck/chunks.py: Python cut points also at indented `def`/`@` after a blank line (class
  methods were cut mid-body at 42 lines), JS cut points at two-space `function/class/const/
  let/// ─` (droneshow.js is one IIFE), and a ≤ 6-line tail chunk is merged into the
  previous one when the result fits in 45 lines.

### Step 8 — History tables: timeline, shows, products, quotes (2026-09-25)

- Commits: d727954 (timeline 1849–2004, 59 rows; cite_keys.tsv +64 keys = 155; docs/FETCHED.txt;
  claims/p02.md), 35b85fd (timeline 2005–2019, +102 rows; products.tsv 84; claims/p03.md),
  3e2f5e3 (timeline 2020–2026-09, +64 = 225; shows.tsv 60; quotes.tsv 19; claims/p11.md).
  `make data-check` passes with no "(미달)"; check_claims 0 unsupported; `make test` 142 OK.
- Sources that carry most rows (all fetched 2026-09-25 into docs/ via fetch_docs): FAA's own
  "Timeline of Drone Integration" (the page is a Knightlab embed; its Google-Sheet CSV export is
  the cite key `faa-uas-timeline`, 2005-09 → 2019-09 only), IWM "brief history of drones" and
  V-weapons, NASM (Pioneer, Predator story, 2008 UAV exhibit release, Hewitt-Sperry photo),
  VFS Vertipedia milestones (Breguet 1907, PKZ 2 1918, de Bothezat 1922, Kaman HTK-1K 1953,
  Convertawings 1956, X-22A 1966 — legacy milestone pages are server-rendered; ids 1–120 scanned),
  Model Aviation (RC history, Denny targets), Yamaha history stories 28/44, Tesla Museum exhibit
  007, Airminded (Morning Chronicle 1849), GA-ASI Predator-25, Apple 2007 iPhone release, Intel
  investor-site press releases (intc.com works; intel.com/newsroom is 403), Guinness news and
  record pages (both server-rendered now — 13 news + 8 record keys), Sky Elements record list,
  EHang/Pablo Air releases, korea.kr policy weekly (UVify), Parrot press archive (2013–2017 only),
  Wing, Zipline. Korean law dates: version-pinned DRF XML (`MST=`) for 드론법 제정본 and 항공안전법
  2016 제정본/2017 개정본 — the DRF `lsHistory` list is inside a `<form>` that html_text drops,
  so the history list was not usable as a cite source.
- DJI: dji.com geo-redirects (KR IP) — `Cookie: region=US` makes /media-center/announcements
  pages load; the newsroom tag listings (`/newsroom/news/tags/{product-releases,dji-news}?page=N`)
  give title+date for 2012–2023; rows cite the article URL and quote the listing title/date.
  DJI URLs are sources, not cite keys (fetch_docs has no cookie).
- Failed/not used: navy.mil (fetch_docs 403; curl worked → URL source), olympics.com (fetch_docs
  timeout; curl worked → URL source), NMUSAF and af.mil (DNS/403 — no Kettering Bug/Firebee/
  Radioplane fact sheets), analog.com (403), Northrop investor release (no response),
  blog.wing.com and geoscan.ru (no response), hankyung (403), sz.gov.cn (no response).
- Plan candidates that were wrong or unverifiable: "1917 Kettering Bug" → first flight Oct 1918
  (1917-03 is the British Aerial Target); "2018 PyeongChang 1,218" → Guinness flight recorded
  Dec 2017, aired 2018-02-09; my own recalled "5,293 drones, Sky Elements, Texas 2024" → UVify,
  Korea, 2024-05-01; Firebee first flight and Israeli RPV dates not verified (NMUSAF down) — only
  NASM's 1967/1982/1984/1986 statements used; MultiWii start year unverified (only GitHub
  2012-07-20); Amazon Part 135 month, first UK delivery day, Zipline launch month unverified.
- Disagreements recorded (claims/p02, p03, p11): Venice 1849 date (15 Jul vs 22 Aug); Big Guff
  1938 vs 1937; Radioplane 14,891 vs 15,000; Folsom 2,018 (Intel) vs 2,066 (GWR); Russia 2,198
  (Geoscan, 3 Sep) vs 2,200 (GWR, 4 Sep); 2021 mosaic 5,184/5,164/5,200; 2024 mosaic 7,998 vs
  8,100; Manvel 9,985 (GWR) vs "1만 대" (정책브리핑) and 24 vs 31 Mar; Hefei 3 vs 5 Feb 2026;
  Sichuan 33,615 vs 33,605 (two records, same show); Porto 19 vs 20 Jun 2026; World Drone Prix
  12 vs 13 Mar 2016; DRONELIFE's "2,066 drones in South Korea in 2018" is wrong (Folsom, USA).
  Tables use the Guinness figure where the kind is Guinness.
- Military rows keep to dates and programme names (no operational/payload detail, §0.13).

### Part 15 — 자바스크립트 판과 데모 (2026-09-25)

- js/demo.js (six demos: showplayer, physics, attitude, formation, trajectory, pidtune;
  canvas optional so the DOM stub can run them). build_deck.demo_script() glues
  js/droneshow.js + `window.DS_DATA = {params: <params.tsv>, shows: {player: …}}` + demo.js;
  droneshow.js exports to `window` when one exists (the stub's window too).
- exps/p15: node parity capture (timings stripped), the 65-drone player show (grid → heart →
  globe → SHOW → 3·2·1 with dark parked extras → heart, spacing √2·dmin), and **the Python
  version of every demo's summary line** (out/p15_demo_*.txt). check_deck.js CASES now read
  those files — 7 cases (pidtune, physics, attitude, formation squared/plain, trajectory,
  showplayer) must match the JS demo output character for character.
- Part 15: 68 slides — parity (golden list, node capture, close(), the physics parity test,
  the four places where last digits diverged and how they were aligned, operation order),
  droneshow.js FULLSRC (30 chunks), the six live demos with explanations, demo.js FULLSRC,
  assembly and stub checking. Formation lab: plain-distance assignment of "HI" brings two
  drones to 0.000 m mid-transition; squared keeps exactly the δ/√2 bound.
- deck/chunks.py: JS labels (two-space definitions, `__demo('id'`, section heads).
