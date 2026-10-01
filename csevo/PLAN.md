# C#의 진화 (CSharp의_진화.html) — Work Plan for the Building Agent

> Audience of this file: the agent (Opus) that builds the deck. Written in English per the global
> language policy. The deck body itself is Korean (합니다체, like Go의_진화.html).
> Progress log goes at the END of this file (append one entry per commit; never rewrite old entries).
>
> Output: `CSharp의_진화.html` at the repo root (no `#` in the name: GitHub Pages would read it as
> a fragment). A single-file slide deck cut from `template.html` through the assembler lineage
> below, never by hand. **Hard cap 3000 slides; target band 2,600–2,950** (user decision
> 2026-10-01). The assembler must refuse to write a deck above the cap.
> Family: `모던_C++의_진화.html` (300) → `자바의_진화.html` (400) → `파이썬의_진화.html` (357) →
> `Go의_진화.html` (756). Same reading rhythm per feature — **왜 생겼나 → 문법 → 실행 예제 →
> 함정 → 근거** — plus the *history*: 1990s Microsoft/Java → 2000 announcement → C# 1.0 (2002)
> → C# 14 (2025-11, .NET 10). **The deck ends at C# 14** (user decision 2026-10-01): C# 15 /
> .NET 11 preview is not installable here, so it gets at most two prose slides ("진행 중인 제안"),
> no code.
> Tooling lineage: `git/` → **`goevo/`**. **Copy from `goevo/`, don't reinvent.** Every rule
> below that looks pedantic was paid for there (read goevo/PLAN.md progress log once).

---

## 0. Non-negotiables (read twice)

1. **The deck HTML is a build artifact.** Never edit it by hand. Edit `csevo/deck/sections/*.html`
   or the sources/data they cite, then `make all`.
2. **No hand-written code, captures or numbers in the deck.** Every `<pre><code>` is a
   `<!--CODE file=… lines=A-B|sym=…-->` directive filled from a real file under `csevo/ex/`. Every
   terminal capture is `<!--OUT file=…-->` / `<!--CSVER …-->` from `csevo/out/`, produced by
   `run_all.py` running the **installed .NET SDK 10.0.112 (Roslyn 5.0.0, C# 14, runtime 10.0.12)**.
   Every table of numbers is `<!--TABLE file=…-->` generated from `data/*.tsv` / `docs/`.
   `verify_deck.py` re-checks deck ↔ source on every build.
3. **Two oracles, and only two.** (a) The installed compiler + runtime for *everything that can be
   run*. (b) The **official documents fetched into `docs/`** (§2) for *everything historical*:
   `dotnet/docs` whats-new markdown (version history, C# 12–14 pages, older pages from git history),
   `dotnet/csharplang` (Language-Version-History.md, `proposals/csharp-N/*.md` feature specs),
   `dotnet/roslyn` (Language Feature Status.md, compiler breaking-change docs), **Roslyn's
   `MessageID.cs` at the installed SDK's commit** (the `RequiredVersion()` switch: the compiler's
   own answer to "which C# version is feature X"), ECMA-334 edition list, the .NET release index
   (`releases-index.json`) for runtime dates, and devblogs.microsoft.com posts. A statement "C# N
   added X" must resolve to a `MessageID` row (for gated language features) or a heading in the
   version-history / whats-new / proposal text, and the slide carries a `<!--CITE key=… sec=…-->`
   badge that `check_claims.py` resolves. **Never write a version number from memory.**
4. **Every fact has a source** before it appears on a slide (dates, names, quotes, numbers) in
   `deck/claims/pNN.md` as `claim | source | verified-how | date`. Wikipedia **only** by following
   its own citation. Unsourceable → dropped or `<span class="unv">미확인</span>`. Performance
   numbers are quoted with a CITE, never measured here.
5. **Knowledge-cutoff discipline.** C# 14 / .NET 10 (2025-11) and anything after are written only
   from `docs/` fetched at build time, stamped "2026-10 기준". `make docs` at the start of every
   session that touches parts 14–15 and the C# 15 note.
6. **Old compilers cannot run here — the new one judges.** Roslyn accepts `-langversion:` 1, 2
   (ISO-1/ISO-2), 3 … 7.3, 8.0 … 14.0 (verified 2026-10-01). "Before/after" is shown by:
   (a) **language-version pairs** — the same source compiled at `N-1` (the compiler's own refusal
   `error CS8xxx: Feature 'X' is not available in C# N-1. Please use language version N or greater.`
   is the evidence) and at `N` (runs);
   (b) **behaviour switches that the compiler keys on langversion** (e.g. C# 5's `foreach` variable
   capture is *not* gated — verify each one before claiming; if not gated, show the old behaviour
   by an explicitly written desugaring and say so);
   (c) **runtime/library facts** shown as "the .NET 10 runtime does this" with a CITE for history;
   (d) **removed or changed syntax**: the old form + today's diagnostic as an OUT capture.
   Where none applies, the slide shows *current* behaviour, labelled "C# 14 / .NET 10 에서의 동작".
   Part 0 explains this policy in three sentences. All programs run on the .NET 10 runtime even
   when compiled at langversion 1 — say so on the reading-guide slide.
7. **Tests before code (RED → GREEN)** for every Python tool written here (fetch/convert, make_data
   parsers of MessageID.cs / version history / release index, csver normalisation, figure
   `need()`s). Fixtures are excerpts of the real fetched documents under `tools/tests/fixtures/`.
   Never loosen an assertion to pass. If a stated property of C# is false, fix the slide.
8. **Machine: Galaxy Fold, Termux/proot, ~200 MB–2 GB free, swap full.** At most **2 subagents**,
   no `-j`, **one dotnet process at a time** (flock `scratch/dotnet.lock`), every experiment ≤ 60 s,
   run_all strictly sequential, long runs in the background with a Monitor (never `&` in Bash).
   **`DOTNET_GCHeapHardLimit=0x30000000` must be exported for every dotnet process** — without it
   CoreCLR dies ("GC: Reserving 256 GiB … failed", 0x8007000E: Android VA limit). Compile with
   Roslyn `csc.dll` directly (0.7 s, no MSBuild, no NuGet): `tools/csrun` (≤ 30 lines, shown to
   the reader in part 0) = csc with the reference pack + `dotnet exec --runtimeconfig`.
   No VBCSCompiler server (`-shared` off) so nothing stays resident.
9. **Foldable layout.** `<pre>` ≤ 45 lines and ≤ 72 columns (Korean = 2), captures ≤ 108 columns
   (wider diagnostics → `term wrap`, ≤ 200), `<li>` ≤ 14, no box-drawing in prose, no `①②③` in
   monospace. Figures: SVG from `deck/gen_figs.py` (viewBox width 340), rendered with
   `rsvg-convert` and **looked at**.
10. **Determinism is evidence.** Every capture identical across three runs (`tools/record.sh
    --check`). Env: `LANG=C`, `TZ=UTC`, `DOTNET_CLI_TELEMETRY_OPTOUT=1`, `DOTNET_NOLOGO=1`,
    `DOTNET_TieredPGO=0`? (only if a capture needs it — verify), HOME/TMPDIR under scratch.
    Examples never print `GetHashCode()` of strings (randomised per process), times, GUIDs,
    thread ids, addresses or `Stopwatch` values. Normaliser: work path → `/work`, `0x…` addresses,
    `+0x…` IL offsets, temp names. Unhandled-exception traces are kept (portable pdb → `line N`).
11. **Commit granularity:** one tool, one data batch, one experiment batch, one deck part, one
    figure batch or one review per commit. Korean, no-prefix subject (repo convention),
    `Co-Authored-By` trailer. Never `git push` unless asked. `git add` by path only.
12. **Language:** deck prose Korean 합니다체; identifiers and C# comments inside `ex/` in English
    (captures match the wild), but every `ex/` source starts with one Korean line:
    `// 슬라이드 <id> — <feature>, C# N`. This file and subagent briefs in English.
13. **Scope.** This deck is *history + what changed per version*. It is not a C# tutorial, not a
    .NET API tour. A feature slide teaches the feature only as far as needed to show what changed
    and why. BCL/runtime changes appear only where the language feature depends on them (async →
    Task, LINQ → System.Linq, Span → ref struct, generic math → INumber, collection expressions →
    CollectionBuilder) plus one companion chapter per part ("같이 온 런타임").

---

## 1. Directory layout (goevo's, renamed)

```
csevo/
  PLAN.md  Makefile  run_all.py
  data/
    releases.tsv     version | date | vs | framework | source        HAND+CHECK (C# 1.0 … 14)
    dotnet.tsv       product | version | date | source               GENERATED (releases-index.json) + HAND (.NET Framework 1.0–4.8.1)
    langgates.tsv    message-id | feature-name | required-version    GENERATED from docs/roslyn/MessageID.cs
    cite_keys.tsv    key | name | file                               GENERATED from FETCHED
    features/pNN.tsv id | version | kind | title(ko) | cite-key | cite-sec | slide-id | msgid
    timeline.tsv     date | event(ko) | source | verified-how         HAND
  docs/              fetched cache (gitignored except FETCHED.txt)
  ex/<NN>/<slug>/    Program.cs (+ other *.cs) + ex.csproj (LangVersion, Nullable, AllowUnsafeBlocks,
                     ImplicitUsings=disable, OutputType) — a real csproj so readers can `dotnet run`;
                     csver translates its properties to csc flags. EXPECT_FAIL when deliberately broken.
  exps/pNN.py + ORDER
  out/               captures + generated tables (committed; ×3 identical)
  scratch/           gitignored (work copies, HOME, lock, review dumps, briefs)
  deck/  base/{head,tail}.html  sections/NN_*.html  claims/pNN.md  glossary/pNN.txt
         build_deck.py verify_deck.py check_slices.py check_xref.py check_claims.py check_deck.js
         cites.py chunks.py gen_glossary.py gen_tables.py gen_figs.py gen_demos.py svgkit.py
         order.txt pending.txt budget.txt figs/ demos_src.js demos.js
  tools/ width.py rewrap.py record.sh csrun csver.py fetch_docs.py md_text.py make_data.py
         budget_hint.py tests/(fixtures/)
```

Directive changes vs goevo: **GOVER → CSVER** `<!--CSVER v=7.3 file=ex/08/tuples tag=… note=…-->`
→ `out/08-tuples__cs7.3[-tag].txt`, first line `$ csrun -langversion:7.3 [flags] *.cs`; label
`ex/08/tuples · C# 7.3`. `REL v=7.3` → date from releases.tsv. Badge `<span class="vt v7_3">C# 7.3</span>`
(class = version with the trailing `.0` dropped and `.` → `_`: v1, v1_2, v2 … v7_3, v8 … v14 — plain
digits would make C# 1.2 and C# 12 both `v12`); every feature slide exactly one badge; badge slide ∈
features. LANG_OF: cs, csproj(xml), sh, txt, tsv, json. HARD_CAP 3000.

---

## 2. Sources (verified reachable 2026-10-01)

| Source | Use |
|---|---|
| raw.githubusercontent.com/dotnet/docs/main/docs/csharp/whats-new/{csharp-version-history,csharp-12,csharp-13,csharp-14,relationships-between-language-and-library,version-update-considerations,breaking-changes}.md | per-version feature lists, dates (VS/.NET pairing) |
| dotnet/docs git history (GitHub API commits?path=…) | older `csharp-7…11.md` whats-new pages (removed from main) — fetch at the last commit that had them |
| raw…/dotnet/csharplang/main/Language-Version-History.md, `proposals/csharp-N/` listings + spec md | feature specs, per-version proposal sets |
| raw…/dotnet/roslyn/main/docs/Language Feature Status.md, docs/compilers/CSharp/Compiler Breaking Changes*.md | merged-into versions, breaking changes |
| dotnet/dotnet (VMR) @ 95017c71: src/roslyn/src/Compilers/CSharp/Portable/Errors/MessageID.cs | **gate oracle** pinned to the installed compiler (fallback: roslyn tag matching 5.0.0) |
| dotnet/core release-notes/releases-index.json (+ per-channel releases.json) | .NET Core 1.0 → .NET 10 dates |
| ecma-international.org ECMA-334 page, dotnet/csharpstandard README | standard editions |
| devblogs.microsoft.com/dotnet "What's new in C# N" / "Welcome to C# N" posts | quotes, motivation |

---

## 3. Part outline and slide budgets (`deck/budget.txt`; > budget +10 % is an error)

| # | Part | Window | Budget |
|---|---|---|---|
| 0 | 표지 · 읽는 법 · 심판(Roslyn 5 와 공식 문서) · csrun · 형제 덱 | — | 20 |
| 1 | 탄생 이전 — Java·J++·소송, COOL, 헤일스버그(터보 파스칼·델파이), .NET 발표, ECMA | 1996–2002 | 60 |
| 2 | C# 1.0 · 1.2 — 형식 체계, 속성·이벤트·대리자, 박싱, 특성, unsafe | 2002–2003 | 200 |
| 3 | C# 2.0 — 제네릭, 반복기, nullable, 익명 메서드, partial, static class | 2005 | 210 |
| 4 | C# 3.0 — LINQ, 람다, 확장 메서드, var, 익명 형식, 식 트리 | 2007 | 240 |
| 5 | C# 4.0 — dynamic, 선택·명명 인수, 변성, COM | 2010 | 130 |
| 6 | C# 5.0 — async/await, caller info | 2012 | 170 |
| 7 | C# 6.0 — Roslyn 오픈 소스, 보간, nameof, `?.`, 식 본문 | 2015 | 170 |
| 8 | C# 7.0–7.3 — 튜플, 패턴, out var, 지역 함수, ref·Span | 2017–2018 | 260 |
| 9 | C# 8.0 — NRT, 비동기 스트림, 범위, switch 식, 기본 인터페이스 메서드 | 2019 | 220 |
| 10 | C# 9.0 — record, init, 최상위 문, 패턴 확장, 함수 포인터 | 2020 | 200 |
| 11 | C# 10 — record struct, global using, 파일 범위 네임스페이스 | 2021 | 150 |
| 12 | C# 11 — raw string, generic math, list pattern, required | 2022 | 190 |
| 13 | C# 12 — 기본 생성자, 컬렉션 식, 별칭, 인라인 배열 | 2023 | 170 |
| 14 | C# 13 — params 컬렉션, Lock, ref struct 제네릭, partial 속성 | 2024 | 170 |
| 15 | C# 14 — 확장 멤버, field, `?.=`, Span 변환, 부분 생성자 | 2025 | 200 |
| 16 | 흐름으로 다시 읽기 — 네 갈래, langversion 사다리, 같은 프로그램 다섯 시대, C# 15 진행 중 제안 | — | 90 |
| A(17) | 부록 — 버전 일정표, 게이트 표, 용어집, 퀴즈 색인, 출처 | — | 60 |
| | **Total** | | **2,910** (cap 3000) |

Within parts, feature slides per version ∝ the length of that version's sources (budget_hint),
latest three (12–14) ×1.5. Families before have landed *below* budget; never pad to reach it —
but this deck's band is a user decision, so if a part lands > 20 % short, deepen with more
runnable examples (traps, interactions with later versions), not prose.

Every version gets: chapter cover, overview slide (generated table from features), feature slides
(big features 4–10 slides), "같이 온 런타임" slide(s), one quiz.

---

## 4. Steps (in order; one commit each unless noted)

1. **Skeleton** (`make all SKEL=1` green): tree, Makefile, copied+adapted tooling (CSVER,
   badges, cap, budgets), palette (§6), covers for 0–16 + A, `.gitignore`.
2. **fetch_docs + md_text** (tests RED → GREEN); `make docs`; commit tools + FETCHED.txt.
3. **Data**: make_data (langgates from MessageID.cs, dotnet.tsv, cite_keys) with tests;
   releases.tsv by hand with sources; `make data-check` (feature rows with `msgid` must match
   `langgates.tsv` required version — catches "remembered the wrong version").
4. **csrun + csver + run_all** (tests); part 0 evidence (gate pair, csrun listing, runtime info).
5. **Sections** part by part (2 → 15, then 1, 16, A), each: features rows → examples → exps →
   `run_all.py --only pNN` ×2 identical → section → `make all SKEL=1` → commit with slide count.
   Large parts may be split into `NNb_` files so two subagents can write in parallel.
6. **Figures**, 7. **Demos** (timeline, langversion ladder, which-version quiz, era gallery),
8. **Wrap-up**: `make all` without SKEL; font; index.html card (new "C# 시리즈" or the language
   evolution group — check index.html) + README line from build numbers; history.md entry.
9. **Reviews** 1 (facts/evidence) and 2 (reader flow) with ≤ 2 subagents; `record.sh --check`.

---

## 5. Checks (`make all`)

test · data-check · examples-check (every ex/ compiles at its csproj LangVersion with **0
warnings** unless EXPECT_WARN/EXPECT_FAIL) · run-check · figs-check · demos-check · deck (cap,
budgets, pre 45×72, ids, badges) · deck-verify · deck-slices · deck-xref · deck-check (node DOM
stub: ←→↑↓, gamepad) · claims-check (every CITE resolves; every "C# N" and 4-digit year in prose
has a claims/data row) · width · font + font-check.

---

## 6. Decisions (user, 2026-10-01 — final, do not re-ask)

1. Install `dotnet-sdk-10.0` from apt — done (10.0.112).
2. Size: band 2,600–3,000, hard cap 3000.
3. End at C# 14; C# 15 only as a prose note in part 16 (no code).
4. File `CSharp의_진화.html`, directory `csevo/`.
Defaults taken without asking (repo norms): palette = .NET purple (`#512bd4` accent, titles
`#2a1b5c`, background `#1b1038 → #3a2a78`, `--special` `#6b3fd8`); no photos; English code
comments + Korean header line; two review passes before push.

---

## Progress log (append only; newest at the bottom; one entry per commit)

### Plan written (2026-10-01)

- dotnet-sdk-10.0 10.0.112 installed from apt (Roslyn 5.0.0-2.26422.108, runtime 10.0.12,
  ubuntu.26.04-arm64). CoreCLR needs DOTNET_GCHeapHardLimit (see §0.8). csc.dll direct compile
  0.7 s; `-langversion:8` on a record file gives CS8400 "Feature 'records' is not available in
  C# 8.0. Please use language version 9.0 or greater." — mode (a) works. C# 14 extension members
  compile and run. All sources of §2 answered 200.

### Step 1 — Skeleton (2026-10-01)

- The first session wrote this plan and copied goevo/ verbatim, then ended before committing. This
  session found no other claude process (`ps`) and continued from the raw copy.
- Removed (re-ported later from goevo/ in their own steps, tests first): tools/{gover,make_data,
  fetch_docs,html_text,make_timeline,budget_hint}.py, run_all.py, exps/, and their tests. gen_tables/
  gen_figs/gen_demos keep only their frames (VIEWS / FIGURES / DATA empty); check_deck.js CASES empty.
- build_deck: target `CSharp의_진화.html`; LANG_OF cs/csproj(xml)/sh/py/js/json/tsv/txt; **C# symbol
  finder** (cs_pattern + cs_end: modifiers, Allman braces, one-line record/enum, expression-bodied
  members, wrapped signatures, `///` and `[Attr]` lines attached; call sites and `return new X(...)`
  are not definitions); **CSVER** (`csverslug(file, v, env, tag)` → `<NN-slug>__cs<v>[-env-…][-tag]`,
  `csver_cmdline(cmd, v, flags, env)` → `[ENV=… ]csrun -langversion:<v> [flags] [rest of cmd]`,
  label `ex/… · C# v`); **REL** compares with `vnorm` (drop trailing `.0`) so `v=8`/`v=8.0` both hit
  the table row; HARD_CAP 3000; appendix = section 17 (`p17-quiz-index-N`, `p17-gl-N`); coverage
  dirs ex/*.cs (full), csproj partial.
- cites.py: keys only from data/cite_keys.tsv (no relnotes rows in releases.tsv); a `.cs` document
  (Roslyn MessageID.cs) is cited by a whole stripped line instead of a `§` heading. `vnorm` lives here.
- check_claims: prose versions are `C# N` / `C# N.M` (Korean particles may be glued; `C# 1.5.2`, `F# 6`,
  `C# 3배` are not); known = releases.tsv versions ∪ `C# N` mentioned in claims (vnorm). check_xref:
  badge text must be `C# N`, class rule above (**deviation from §1's first wording**, fixed there).
- Palette per §6 (#512bd4 accent — 7.9:1 on white, so accent-ink is the same colour; titles #2a1b5c;
  bg #1b1038→#3a2a78; special #6b3fd8); g1–g6 = lang/runtime/compiler/library/ecosystem/platform;
  `.vt` colours per era, 12–14 filled purple, `.vt.prev` dashed for preview features. Highlighter
  gained `cs` (keywords incl. contextual ones, `#` directives as preprocessor).
- Makefile exports DOTNET_GCHeapHardLimit=0x30000000, telemetry/logo off; examples-check will call
  `tools/csver.py --check` (step 4). Sections: cover + part 0 (7 placeholders) + 17 part covers =
  26 slides; budget.txt = §3 (2,910). claims/p00.md: the 16 `C# N` headings and "Released …" months of
  csharp-version-history.md (curl today). data/: releases/cite_keys/timeline headers only.
- Tests 41 (RED: 31 failed for the intended reasons; then GREEN). `make all SKEL=1`: exit 0, 26
  slides, 24 placeholders, claims 16 versions sourced, DeckMono 28 KB. .gitignore: /csevo/docs/*
  (except FETCHED.txt), /csevo/scratch/, /csevo/.svgrender/.

### Step 2 — fetch_docs + md_text (2026-10-01)

- tools/md_text.py (new; the C# sources are markdown): ATX and setext headings → `§<TAB>heading`
  with inline markup removed (`code`, [links](), *em*, `\#`, {#anchor}, tags); fenced code verbatim and
  never a heading (`#nullable`, `#:sdk`); YAML front matter kept and its closing `---` not read as a
  setext underline; BOM stripped (Roslyn breaking-change docs start with one — caught after the first
  fetch, test RED first). tools/html_text.py copied unchanged from goevo (ECMA page, devblogs).
- tools/fetch_docs.py: every GitHub source pinned to a commit — dotnet/docs 91cc9093, csharplang
  93d55a09, dotnet/core 44927bc8, csharpstandard 107068a0, and Roslyn at **the installed SDK's VMR
  commit 95017c711e** (MessageID.cs, LanguageVersion.cs, CSharpResources.resx, Language Feature
  Status, 12 compiler breaking-change docs, Deviations from Standard, warning waves). Whats-new pages
  removed from main (C# 6, 7, 7.1–7.3, 8, 9, 10, 11) come from the parent of the removing commit
  (found with the GitHub API today, hard-coded with the removing hashes in a comment). Proposals: the
  csharplang tree (one API call, cached in docs/raw) → every `proposals/csharp-N.M/*.md` (139; inactive
  and rejected excluded; csharp-15.0 kept for the part-16 note). .NET channel releases.json from the
  pinned dotnet/core copy (not builds.dotnet, which moves). 10 devblogs posts (only URLs that answered
  200 today; C# 13 has no "introducing" post at the guessed slug).
- Findings: dotnet/docs already has csharp-15.md and csharplang lists "C# 15.0 - .NET 11 and Visual
  Studio 2026 version 18.8" (unions, closed hierarchies, …) — part 16 note material, still no code.
  ECMA-334 page lists editions 1–7 (December 2001 … ; V7 = ECMA-334:2023).
- `make docs`: 203 documents, 0 failures, 29 MB (cache, gitignored); docs/FETCHED.txt committed.
  Tests 56 (md_text 7, plan 6, ledger 2 + 41 earlier); RED on stubs first.

### Step 3a — make_data + generated tables (2026-10-01)

- tools/make_data.py → four generated tables. **langgates.tsv** (183 rows): the `RequiredVersion()`
  switch of the installed compiler's MessageID.cs — versions read from the `return
  LanguageVersion.CSharpN` lines, *not* the comments (the fetched file labels the C# 14 group
  "C# 13.0 features"); feature names from CSharpResources.resx (the words printed in CS8xxx errors;
  9 gates have no resource name — left blank). Gates per version: 1:1 2:13 3:10 4:4 5:1 6:12 7:11
  7.1:4 7.2:8 7.3:13 8:22 9:25 10:18 11:15 12:8 13:9 14:9 — C# 5 (async) has a single gate, so most
  C# 1–5 "before/after" must use mode (b)–(d) of §0.6.
  **releases.tsv** (18 rows, **deviation**: generated, not hand-written): name and month from the
  version history (`C# version N` + `*Released Month YYYY*`), VS/.NET pairing from csharplang's
  Language-Version-History headings; C# 15 (LVH only) is left out. Dates are months (YYYY-MM) —
  the docs give no days. **dotnet.tsv** (13 rows): GA (`x.y.0`) date per channel from the pinned
  releases.json; .NET 11 has no GA yet. .NET Framework rows still to come by hand (with sources).
  **cite_keys.tsv** (202): whatsnew-N, history, lvh, prop-N-<name>, msgid, langversion, roslyn-*,
  rel-*, blog-* (titles from the raw page `<title>`, " - .NET Blog" removed), ecma-334, std-readme.
- `make data-check`: regenerate-and-compare + features rows (version ∈ releases via vnorm, kind ∈
  lang/runtime/compiler/library/ecosystem/platform, cite resolves, **msgid's gate version == row
  version**, unique id/slide-id). md_text: link targets with parentheses (LVH's `[C# 2](….aspx)`)
  — found in the first table run, test RED first.
- Tests 69. `make all SKEL=1` green.

### Step 4 — csrun + csver + run_all, part 0 (2026-10-01)

- tools/csrun (29 lines, shown on p0-csrun): reads ex.csproj's LangVersion/Nullable/
  AllowUnsafeBlocks/OutputType with sed, appends command-line flags after them (**csc takes the last
  `-langversion`**, verified), compiles `*.cs` with csc.dll `-noconfig -nostdlib -deterministic
  -debug:portable -pathmap:$PWD=/work` against the 10.0.12 ref pack, writes a runtimeconfig and
  `exec dotnet exec`. `CSRUN_COMPILE_ONLY=1` stops after compiling (examples-check).
- tools/csver.py (port of gover): copy to scratch/work/<stem>, `build_argv` puts `-langversion:v`
  + flags right after `csrun` (other commands untouched), env prefix → environment, flock
  scratch/dotnet.lock, 60 s; normalise = paths, ≥9-hex-digit addresses, CRLF. `--check` compiles
  every example at its csproj version, 0 warnings unless EXPECT_WARN, EXPECT_FAIL skipped, results
  cached by sha256 of sources+csproj+csrun (scratch/check/). run_all.py: goevo's with `ctx.cs(ex,
  cmd='csrun', v=None, flags, env, tag, expect)`; v defaults to the csproj LangVersion and is
  **always written in the first line** (`$ csrun -langversion:12.0`). csver_cmdline leaves
  non-csrun commands alone (`$ dotnet --version`) — test RED first.
- Findings: (1) under `-langversion:8.0`, `record Point(int X, int Y);` is not refused as
  "records" — it parses as a top-level local function returning type `record` (six diagnostics:
  CS8400 top-level statements, CS8112, CS0246 'record', …; with a class named Program it even gives
  CS0260 partial Program). Kept in scratch/later/ for part 10's trap slide. (2) Each refused version
  has its own error code (CS9058 for 11.0); not claimed on a slide until ErrorCode.cs is cited.
  (3) `-langversion:1` and `ISO-1` both accepted; a C# 1 program prints runtime 10.0.12.
  (4) **DOTNET_GCHeapHardLimit**: without it CoreCLR started fine 3/3 today, so the deck does not
  call it required (kept as a safety default in csrun/csver/Makefile; memory note corrected).
- gen_tables.gate_counts → tbl_gate_counts.html (test first): gates per version incl. zeros (1.2: 0,
  5.0: 1). Part 0 written: 15 slides (cover, 13 + part cover) — oracle, gate source, few-gate
  versions, four evidence modes, gate pair (collection expressions 12.0 vs 11.0), runtime under
  langversion 1/ISO-1, csrun listing, normalise, how-to, badges, machine, scope. p00 run twice:
  identical. Tests 88.

### Step 5 setup — standard docs, overview tables, chunked parts, subagent brief (2026-10-01)

- docs: + the C# standard draft chapters (csharpstandard `standard/*.md`, 32 files, keys `std-<chapter>`)
  — C# 1–5 features cite the spec text because their whats-new coverage is a few lines.
- gen_tables.release_tables (port, test first) → `out/tbl_rel_<vnorm>.html` per version: month,
  .NET · VS pair, feature titles per kind (links to slide-ids), gate count. Correction: the step-4 entry
  says tests 88 — it was 87; now 89.
- Parts are written in **chunks** (`NN_` + `NNb_` …) so two subagents can work at once and no
  subagent has to hold 200 slides: chunk = section file + data/features/pNNx.tsv + claims/glossary/
  exps of the same suffix. budget_report sums chunks by prefix; check_xref continues part/chapter
  numbering across chunk files. Brief for part writers: scratch/brief/BRIEF.md (gitignored; English).
- Wave 1 launched: p02 (C# 1.0 type system & expressions, ~100) and p03 (C# 2.0 generics, nullable,
  iterators, ~105). Next: p02b (C# 1.0 members/delegates/exceptions + C# 1.2), p03b (anonymous
  methods, delegate inference/variance, partial/static/accessors, small gates), then part 4 (C# 3.0)
  as p04/p04b.

### Part 2 first half (p02) + part 3 first half (p03) — subagents (2026-10-01)

- p02 (C# 1.0 type system & expressions): 97 slides (cover+intro, 1장 overview 9, 2장 형식 체계 45,
  3장 식·연산자·매개변수 41), 34 feature rows, 88 examples (23 EXPECT_FAIL, 1 EXPECT_WARN), 95
  captures, 14 claims, 14 glossary lines. p03 (C# 2.0 generics, nullable, iterators): 102 slides
  (1장 8, 2장 제네릭 42, 3장 nullable 23, 4장 반복기 28 + covers/quizzes), 17 rows (4 with msgid),
  96 examples (20 EXPECT_FAIL, 2 EXPECT_WARN), 108 captures, 28 claims, 13 glossary lines.
  Both re-ran their batch twice with identical bytes (p02 also after the csver fix).
- Shared tool bug found by p02: tools/csver.py `_run` had a comment word wrapped onto its own code line
  (`하나` → NameError) by my step-4 rewrap — fixed, test added (21912dc). Lesson: never machine-wrap
  code files; only docstrings/comment paragraphs with tools/rewrap.py.
- Findings (deck material): C# 1/2 refusal codes are CS8022/CS8023 (per target version); a file with
  several gated features at v=1 reports only the generics errors (one feature per refusal example);
  calling generic/extension methods is not gated — only the syntax (`<…>`, declarations); variance is
  gated on declaration only (`IEnumerable<object> e = new List<string>()` compiles at v2 because the
  BCL declares `out T`; declaring `out T` → CS8023 'type variance' needs 4); `??` has no gate and no
  version in docs (marked 미확인); unhandled exception exit code here is -6; .NET 10 throws
  OverflowException for unchecked int.MinValue / -1 (implementation-defined in the standard);
  `yield` in try-with-catch is still CS1626 at 14.0; ref locals in iterators refused at 12.0 (CS9202),
  accepted at 13.0; CS0171 at v1 suggests "language version '11.0' to auto-default the field".
- Commit discipline with a subagent (p02b) running: only p02/p03 files staged (p02b's three new
  ex/02 dirs unstaged); checks run on an export of the index (`git checkout-index --prefix`) with docs
  symlinked: tables, run-check, deck (231 slides, coverage 4385/4385, 오류 0), verify, slices, xref
  (54 badges), claims (0), deck-check, data-check (51 rows), glossary — all clean; the deck HTML of
  that export (font embedded) is what is committed.

### p02b + p03b finished; csrun -parallel-; aborted recapture (2026-10-01)

- p02b (C# 1.0 classes/members/delegates/exceptions/misc + C# 1.2): 98 slides (part 2 195/200),
  38 rows, 90 examples, 101 captures, 26 claims, 15 glossary; Artima quotes on virt/pme/del/nochecked
  "why" slides (tier c). p03b (anonymous methods & delegates, partial/static/accessors/aliases,
  #pragma/fixed buffers, C# 2.0 wrap-up): 101 slides (part 3 203/210), 14 rows (all 9 gated with
  msgid), 96 examples, 125 captures, 44 claims, 15 glossary.
- **Both found the same determinism bug**: csc compiles types in parallel, so diagnostics spanning
  several types/files come out in a different order per run (staticbad: 4 runs → 4 orders, measured
  with md5). tools/csrun now always passes `-parallel-` (4/4 identical; `-parallel+` varies again).
  Captures that passed `flags=-parallel-` explicitly keep it in their first line (redundant now).
- Other findings: method-group conversion, delegate inference and method-group variance are NOT gated
  (compile at v1); each target version has its own refusal code (CS8022 v1 … CS8026 v5, CS8320 7.2,
  CS8400 8.0, CS9058 11, CS9202 12, CS9260 13); method-group delegate caching differs at 10.0 vs 11.0;
  `module:` gate warning prints the raw enum name `IDS_FeatureModuleAttrLoc`; BeginInvoke throws
  PlatformNotSupportedException on .NET 10; `-langversion:1.2` is CS1617; declaration errors hide
  method-body errors (split refusal examples).
- **Incident**: a full recapture (p00…p03b) started while the p04/p04b subagents compiled → swap
  15.8/16.3 GB, every batch hit the 60 s csrun timeout *after* run_all had cleared that batch's old
  captures. Committed captures restored from HEAD (134 files, `git restore --source=HEAD` on deleted
  paths only). Rule: **recapture only when no subagent is running dotnet**; p02b/p03b (uncommitted)
  must be recaptured before they are committed.

### p02b + p03b committed after a clean recapture (2026-10-01)

- No subagent running → `run_all.py --only` p02 p02b p03 p03b, twice: sha256 of all 0[23]-*.txt +
  manifest identical across passes, and the committed p02/p03 captures came out byte-identical to HEAD
  (so `-parallel-` changed none of them). 460 captures in manifest.
- Committed from an index export (p04/p04b work-in-progress left unstaged): deck 429 slides (part 2
  195/200, part 3 203/210), coverage 9155/9155, verify 392 code + 434 output blocks, xref 82 links,
  claims 0 missing, glossary 57 terms, deck-check 0, font 587 glyphs.
- p04/p04b subagents from the previous session died with it: 04_cs3 97 slides (5장 unfinished; a
  3장 block that had been appended after 4장 was moved back), 04b_cs3 66 slides (6장·7장 done, 8장·9장
  missing), 179 example dirs, but **no exps/p04*.py, no captures, no claims/glossary** — every p04
  example is untested. Resume briefs: scratch/brief/p04_resume.md, p04b_resume.md.

### Part 4 (p04 + p04b, C# 3.0) — resumed subagents (2026-10-01)

- p04 112 slides (1장 10, 2장 var·익명 형식 30, 3장 초기화자·자동 속성·partial 26, 4장 람다 26, 5장 확장
  메서드 24), 16 rows, 98 examples (24 EXPECT_FAIL), 128 captures, 38 claims, 13 glossary. p04b 105 slides
  (6장 쿼리 식 36, 7장 LINQ to Objects 30, 8장 식 트리 28, 9장 정리 11), 11 rows, 90 examples (11 FAIL),
  96 captures, 28 claims, 11 glossary. Part 4 = 217/240. Both rewrote prose that disagreed with the first
  real captures (lambda count, dynamic receiver compiles and fails at run time, partial-method errors at
  v3 are worded with C# 9 rules, extension blocks at 13.0 are syntax errors not a gate message).
- **Shared-tool race**: run_all.py read-modify-writes out/batches.json, so two batches at once lose each
  other's key (p04b's vanished once). Fixed by rerun; rule until fixed: after parallel subagents, rerun
  the batches sequentially (done here: p04+p04b ×2, identical, same bytes as the subagents').
- Findings: extension `Add` in collection initializers compiles at v3 (no gate; docs place it in C# 6);
  non-capturing lambdas are cached as instances of a generated class at v3 and v14; `M(Func)` vs
  `M(Expression<Func>)` with a lambda is CS0121; at 14.0 `$"…"` is allowed in expression trees but
  `?.`, tuples, patterns, throw, switch expressions, `^` are refused; .NET 10 ExpressionType has 85
  values; List<T>.Sort of 20 items is unstable, OrderBy stable.
- `make all SKEL=1` green: 644 slides, tests 91, data 130 rows, examples 561 (125 FAIL), coverage
  13849/13849, verify, slices 12, xref 187 links, claims 0 missing, deck-check 0, font pass.
- Next: part 5 (C# 4.0, 130) as p05 + p05b, and part 6 (C# 5.0, 170) — two subagents.
