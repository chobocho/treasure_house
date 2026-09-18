# Termux Encyclopedia (Termux_대백과사전.html) — Work Plan for the Building Agent

> Audience of this file: the agent (Opus) that builds the deck. Written in English per the global
> language policy. The deck body itself is Korean (합니다체 prose, as in the transformer deck).
> Progress log goes at the END of this file (append one entry per commit; never rewrite old entries).
>
> Output: `Termux_대백과사전.html` at the repo root — a single-file slide deck whose chrome (nav,
> ←/→ pages, ↑/↓ in-page scroll, Gamepad API, fold-aware CSS) comes from `template.html` via the
> `wireless/deck/base/{head,tail}.html` copies. Hard cap **3000 slides** (user decision 2026-09-18);
> target band **1,800–2,600**. Lineage: `keycloak_ad/` → `compress/` → `wireless/` → `transformer/`
> (assembler, checks, Makefile, svgkit, claims, CITE badge). **Copy, don't reinvent.** Read
> `transformer/PLAN.md` §0–§2 and §9, then the last three entries of its progress log, once before
> starting. Every pedantic rule below was paid for in one of those decks.
>
> What makes this deck different from its ancestors: **the subject is the machine it is built on.**
> This session runs in an Ubuntu proot *inside* Termux on a Galaxy Fold, and Termux's own bionic
> binaries (`pkg`, `apt`, `termux-*`, `proot-distro`) run from here. So the deck's evidence is not
> a simulation of Termux — it is Termux, captured live, plus the upstream source code it explains.
> Scope, in the user's words: **모든 것 · 역사 · 원리 · 한계 · 활용 가이드** — an encyclopedia.

---

## 0. Non-negotiables (read twice)

1. **The deck HTML is a build artifact.** Never edit it by hand. Edit `termux/deck/sections/*.html`
   or the sources they cite, then `make all`.
2. **No hand-written code, captures or numbers in the deck.** Every `<pre><code>` is a
   `<!--CODE file=… lines=A-B|sym=…-->` directive filled from a real file under `termux/` or from the
   pinned upstream cache `termux/sources/` (§3.2). Every terminal capture is `<!--OUT file=…-->` from
   `termux/out/`, produced by `run_all.py` through the wrapper `tools/tmx.sh` (§2) — i.e. by the real
   Termux userland on this device, or by this proot when the slide is *about* proot. Every table of
   measured numbers (package counts, sizes, timings, exit codes, API command lists) is
   `<!--TABLE file=…-->` generated from `out/` or `data/`. `verify_deck.py` re-checks deck ↔ source
   on every build.
3. **Every fact has a source.** Dates, version numbers, Android-version behaviours, policy events
   (Play Store freeze, F-Droid, targetSdk changes, phantom-process limit), repository facts and
   people go in `deck/claims.md` as `claim | source | verified-how | date` **before** they appear
   on a slide. Sources in order of preference: (1) the upstream source code or commit itself
   (`sources/<repo>@<sha>`, cited with the `SRC` badge, §3.2); (2) upstream documentation fetched to
   text — `wiki.termux.com`, the `termux-packages` GitHub wiki, `termux-app`/`termux-api`/`termux-exec`
   READMEs, agnostic-apollo's Android-Docs; (3) Android developer documentation (AOSP source or
   developer.android.com) for OS behaviour; (4) a GitHub issue or release page **by number/tag**;
   (5) a news article or blog only for community history, with the date. Nothing from memory: the
   Termux story is full of "everyone knows" claims that are off by a version or a year. A claim that
   cannot be sourced is either dropped or marked `<span class="unv">미확인</span>`.
4. **Knowledge-cutoff discipline.** Anything dated 2025 or later (latest release, Play Store branch
   status, Android 15/16 behaviour, glibc packages, termux-x11 state) must be re-verified with a
   fetch or WebSearch at build time and written with an explicit "2026-09 기준" stamp. The
   verified anchor on 2026-09-18: `termux-app` latest release **v0.118.3 (2025-05-22)** from the
   GitHub API — quote it from `data/releases.tsv`, not from this sentence.
5. **Tests before code (RED → GREEN)** for every script in `tools/` and `py/`, and for every
   experiment program in `exp/` (§3.4). Never loosen an assertion to pass. If a stated property
   of Termux turns out to be false on this device, the slide says what *is* true and cites the
   capture; do not "fix" the capture.
6. **This machine is a Galaxy Fold under Termux/proot with ~350 MB free RAM and a nearly full
   swap** (`free -m` on 2026-09-18: 355 MB free, swap 10.9/16 GB used). At most **2 subagents**, no
   JVM, no Docker (impossible anyway), no `pkg upgrade`, no builds of large packages. Check
   `free -m` before heavy steps. Checkpoint everything to disk; assume the session can be killed at
   any moment (the phantom-process killer that Part 8 teaches is real and has killed sessions here).
7. **Do no harm to the host Termux.** This deck is built *on* the user's daily environment. The
   denylist in `tools/tmx.sh` (§2) refuses: `termux-reset`, `termux-restore`, `termux-change-repo`
   (non-interactive editing of `sources.list` too), `pkg upgrade`/`apt upgrade`/`dist-upgrade`,
   `apt remove|purge|autoremove`, `rm -rf` under `$PREFIX` or `$HOME` outside `termux/scratch`, any
   write to `~/.termux/`, `termux-wifi-enable`, `termux-telephony-call`, `termux-sms-send`,
   `termux-wallpaper`, `termux-brightness`, `termux-volume` set, `termux-torch on`, `am start` of
   anything but `termux-open` of a file in `termux/`. Installing packages is allowed only within
   decision 5 (§9) and each install is logged in the progress log with its size.
8. **Privacy of captures is a build check.** `tools/scrub.py` runs over every file in `out/` and
   fails the build on: phone numbers, IMEI/IMSI/serial patterns, MAC/BSSID, SSID (replaced by
   `<ssid>`), GPS coordinates, contact names, e-mail addresses, IPv4/IPv6 other than loopback and
   RFC 1918 (replaced by `<ip>`), `$HOME` paths outside `/data/data/com.termux/files/home/github/
   treasure_house/termux` (replaced), and the user's login names. Privacy-sensitive Termux:API
   commands (`termux-sms-*`, `termux-call-log`, `termux-contact-list`, `termux-location`,
   `termux-camera-photo`, `termux-microphone-record`, `termux-telephony-*`, `termux-notification-list`,
   `termux-fingerprint`, `termux-keystore`, `termux-nfc`, `termux-usb`) are **never executed**; their
   output format is quoted from the wiki/source with badge `b` (§6).
9. **Two kinds of capture, declared up front.** `out/manifest.json` marks every capture `stable`
   (must be md5-identical across three `run_all.py` runs — package lists, `dpkg -S`, source
   excerpts, exit codes, deterministic experiment output) or `snapshot` (battery, sensors, disk
   usage, timings, `apt` mirror responses — recorded once, frozen with the date in the file's
   first line, never re-recorded silently). `tools/record.sh --check` compares only `stable`.
   Every `snapshot` capture cited on a slide carries the visible stamp "이 기기 · 2026-09 캡처".
   No wall-clock numbers in prose; timing tables come from `out/` and are labelled snapshot.
10. **Foldable layout.** `<pre>` ≤ 45 lines and ≤ 72 columns (Korean counts as 2), captures ≤ 108
    columns, `<li>` ≤ 14 per list, no box-drawing characters in prose, no `①②③` inside monospace,
    SVG figures use `viewBox` width 340 so they fit 374 px. The assembler errors on all of these.
    Long captures (`pkg list-all`, the 84 `termux-*` names) go in the appendix as generated tables,
    not on teaching slides.
11. **Commit granularity:** one tool, one experiment batch, one data table batch, one figure
    batch, or one deck part per commit; split "source/capture commit" from "deck-body commit".
    Korean, no-prefix commit subject (repo convention), `Co-Authored-By` trailer per the session
    reminder. Never `git push` unless asked.
12. Keep Korean comments in code (UTF-8, no BOM), 72 columns. Identifiers in English. Do not touch
    other decks. Big writes are ≤ 250 lines each (append for more); the deck must open at every
    commit. `Linux_명령어_핸드북.html` and `SSH 고급 가이드북.html` already teach the shell and
    SSH — cross-link them (`href` to the file, not to a slide id) instead of re-teaching.

---

## 1. Directory layout

```
termux/
  PLAN.md              this file (+ progress log at the end)
  Makefile             the whole build; `make help` lists targets
  tools/
    tmx.sh             run a command in the real Termux userland from this proot (§2); denylist
    scrub.py           privacy filter + build check for out/ (§0.8)
    fetch_src.sh       clone/refresh upstream repos into sources/ at the SHAs in data/repos.tsv
    doc_text.py        wiki/GitHub-wiki/README HTML or Markdown → text with `sec<TAB>title` lines
    gh_api.py          GitHub REST helper (releases, first commit, tags) → data/*.tsv rows + JSON cache
    width.py rewrap.py record.sh     copied from transformer/tools
  py/                  small stdlib-only helpers the deck cites (elf.py: read DT_NEEDED/RUNPATH/
                       interpreter of a binary; deb.py: parse .deb/control; pkgstat.py: dpkg db stats)
                       + tests/
  exp/                 experiments the deck runs on both sides (§3.4): C99 + sh + py, tests/
  run_all.py           runs every capture/experiment sequentially → out/manifest.json + out/*.txt
  out/                 every capture and table the deck cites (committed; stable ×3 identical)
  data/                hand-curated fact tables (TSV, one fact per row, source column mandatory)
    repos.tsv          repo | url | pinned-sha | pinned-date | why-pinned
    releases.tsv       repo | tag | date | notable-change | source-url
    timeline.tsv       year | month | event(ko) | source | evidence-kind
    android.tsv        android-version | api | year | behaviour-that-affects-termux | source
    repos_apt.tsv      apt-repo | package | url | signing-key-fingerprint | source
    api_cmds.tsv       command | owner-package | needs-app | permission | privacy | run-in-deck | source
    plugins.tsv        plugin | package-id | purpose | first-release | source
    people.tsv         handle | role | years | source   (maintainers as named in upstream files only)
    device.txt         pasted by the user from native Termux (termux-info etc.; §9 decision 8)
  sources/             upstream repo checkouts + doc texts, gitignored, re-fetchable (`make sources`)
  deck/
    base/{head,tail}.html   copy from transformer/deck/base; re-title; new palette (§5 step 1)
    sections/NN_*.html      slide fragments, one file per part (§6)
    build_deck.py verify_deck.py check_slices.py check_xref.py check_claims.py check_deck.js
    chunks.py gen_glossary.py gen_tables.py gen_figs.py svgkit.py
    glossary.txt order.txt pending.txt budget.txt claims.md years_ok.txt
    figs/               SVG figures (architecture, process model, filesystem map, timelines)
    demos.js            in-deck interactive demos (plain JS, §5 step 10)
  scratch/             per-step checkpoints (gitignored)
```

Copy `transformer/deck/{build_deck.py,verify_deck.py,check_slices.py,check_xref.py,check_claims.py,
check_deck.js,chunks.py,gen_glossary.py,gen_tables.py,svgkit.py}`, `transformer/deck/base/{head,tail}.html`
and `transformer/tools/{width.py,rewrap.py,record.sh}` verbatim first, then adapt only: `TARGET`,
`LANG_OF` (sh, py, c, h, js, tsv, txt, java, kt, properties, diff), `HARD_CAP` 3000, `COVER_DIRS`
(tools/ py/ exp/ run_all.py — coverage 100 % applies to *our* code only), `PARTIAL` (sources/ — cited
by excerpt, never fully inlined), part budgets from §6, and **one directive renamed**:
`<!--CITE key=… sec=…-->` becomes `<!--SRC repo=termux-exec path=src/exec/exec.c sha=… lines=A-B-->` —
a badge that must resolve to a `data/repos.tsv` row whose pinned SHA matches and to an existing file
at those lines in `sources/<repo>/` (`make claims-check`). Its visible text is `repo@sha7 · path:lines`.
Keep `CODE` (extended so `file=sources/…` is allowed with a mandatory `sha=`), `OUT`, `TABLE`, `FIG`,
`FULLSRC`, `GLOSSARY`, `SRCSTAT`. Drop `PHOTO` (decision 6). Do not fork the check design.

---

## 2. Environment on this machine (verified 2026-09-18) — the deck's laboratory

| Thing | State | Notes |
|---|---|---|
| Host | Galaxy Fold, Android (version: see `data/device.txt`) | `/system/bin/getprop` is **blocked from proot** ("Operation not permitted") — a real proot limitation, itself a slide in Part 9 |
| Termux prefix | `/data/data/com.termux/files/usr`, bind-mounted read-write into this proot | 326 dpkg packages installed (`dpkg -l` count), 84 `termux-*` executables in `$PREFIX/bin` |
| Running Termux binaries from proot | **works**: `/data/data/com.termux/files/usr/bin/bash -c '…'` executes bionic bash; `dpkg`, `apt`, `termux-info`, `termux-battery-status` run | `$PREFIX`/`$PATH` are **not** set by that bash — `tools/tmx.sh` must export `PREFIX`, `PATH=$PREFIX/bin`, `HOME=/data/data/com.termux/files/home`, `TMPDIR=$PREFIX/tmp`, `LANG=en_US.UTF-8`, `TERM=xterm-256color`, and unset proot's `LD_*` |
| Termux:API | app + socket present: `termux-battery-status` returned JSON from proot | proves the `termux-api` ↔ app socket path crosses proot; capture the mechanism (Part 7) |
| apt sources here | main mirror `mirror.example.com/termux/apt/termux-main`, `tur.list` → `tur.kcubeterm.com` | read-only evidence for Part 6; `apt update` is allowed (network, no state change beyond lists), `apt install` per decision 5 |
| proot side | Ubuntu 26.04.1 LTS, python3 3.14.4, gcc 15.2, node 24.18, git 2.55 | stdlib-only Python; node runs `check_deck.js` (DOM stub); Playwright unusable |
| Termux side toolchain | `aarch64-linux-android-clang` present in `$PREFIX/bin` | compile `exp/*.c` **twice**: bionic (Termux clang) and glibc (proot gcc) — the differences are Part 3/5 evidence |
| Network | wiki.termux.com, github.com, raw.githubusercontent.com, api.github.com, f-droid.org all HTTP 200 | `gh_api.py` sends a User-Agent; unauthenticated rate limit 60/h — cache every response in `sources/gh/` |
| rsvg-convert | ok (Nanum fonts) | render every SVG in `deck/figs/` to PNG and look at it |
| Font | `tools/embed_mono_font.py` | `make font` after every deck build, `--check` in `make all` |

### 2.1 `tools/tmx.sh` — the only door to the host Termux

```
usage: tools/tmx.sh [--cwd DIR] [--timeout SEC] -- CMD [ARGS…]
       tools/tmx.sh --proot -- CMD …     # run on the proot side instead (same env logging)
```

- Execs `/data/data/com.termux/files/usr/bin/bash --noprofile --norc -c "$*"` with the environment
  from §2 table row 3; prints `## tmx: side=termux cwd=… exit=N` as the **last line** so captures
  carry their exit code (the assembler strips nothing; the slide shows it).
- Refuses the denylist in §0.7 by regex on the whole command line **before** running; tests in
  `exp/tests/test_tmx.sh` prove each denied pattern exits 99 without executing (RED first).
- Default timeout 120 s (`timeout` from the proot side); every capture in `run_all.py` names its
  side explicitly (`side=termux|proot`) so a slide never shows a proot capture as if it were Termux.
- Never runs interactive commands; `DEBIAN_FRONTEND=noninteractive`, `apt -y` only inside the
  allowed install path, and `pkg` is called as `pkg` (the wrapper is itself a slide: `sym=` cite of
  `$PREFIX/bin/pkg`, which is a shell script — cite it from `sources/termux-tools` at its SHA, and
  `diff` it against the installed copy as a capture to prove the pin matches the device).

### 2.2 What cannot be captured from here (write these as `b`-badge slides, or ask the user once)

`getprop`, `termux-info`'s Android fields, `settings get global settings_enable_monitor_phantom_procs`,
the app UI (drawer, extra-keys row, styling), notifications as seen on screen, Termux:Boot start-up,
Termux:Widget/Tasker invocations, on-screen keyboard behaviour. The user pastes the text outputs once
into `data/device.txt` (decision 8); UI is drawn as SVG (decision 6); plugin behaviour is cited from
their READMEs/sources.

---

## 3. What gets written

### 3.1 Research corpus — `data/*.tsv` + `deck/claims.md` (step 3; before any prose)

Fetch, don't recall. `tools/fetch_src.sh` shallow-clones (`--depth 1 --filter=blob:none` then
`git fetch --depth 1 origin <sha>`; sizes are logged; `termux-packages` is large — clone with
`--sparse` and check out only `packages/{termux-tools,termux-api,termux-exec,termux-am,proot-distro,
proot,apt,dpkg,bash,python,nodejs,clang,glibc*}`, `scripts/`, `sample/`, `README.md`, `docs/` if present)
into `sources/` at SHAs pinned in `data/repos.tsv`:

| repo | why the deck needs its source |
|---|---|
| `termux/termux-app` | terminal emulator (`terminal-emulator/`, `terminal-view/`), `TermuxInstaller` bootstrap, `TermuxService`, RUN_COMMAND intent, `termux.properties` keys, `sharedUserId`, `targetSdkVersion` in `build.gradle`/manifest, first commit date, releases |
| `termux/termux-packages` | `build-package.sh`, `scripts/build/termux_step_*.sh`, `sample/build.sh`, patch policy, bootstrap generation (`scripts/generate-bootstraps.sh` or successor), `termux-tools`, `termux-exec`, `termux-am`, `proot-distro`, glibc packages (verify naming), repo layout |
| `termux/termux-api` (app) + `termux-api-package` | the socket/`am` broadcast mechanism, `TermuxApiReceiver`, per-command Java classes, the shell scripts under `scripts/` — every command's JSON schema is cited from here |
| `termux/termux-exec` | `execve` interposition via `LD_PRELOAD`, shebang rewriting, the "system linker exec" mode; `TERMUX_EXEC__*` variables |
| `termux/proot` and `termux/proot-distro` | ptrace tracer, bind mounts, `--link2symlink`, distro plist/metadata, `login` options |
| `termux/termux-boot`, `termux-widget`, `termux-tasker`, `termux-float`, `termux-styling`, `termux-x11` | README + manifest per plugin (package id, permissions, intents) |
| `termux-play-store/termux-apps` (verify name) | the Play Store branch and why it differs |
| `agnostic-apollo/Android-Docs` | phantom/cached/empty process docs; `TERMUX_APP__*` env docs |
| `wiki.termux.com` (MediaWiki API `action=parse&prop=wikitext`) | Installation, Getting started, Package Management, Termux:API, Boot/Widget/Tasker/Float/Styling, Terminal Settings, FAQ, Hardware, Software, Differences from Linux, Remote Access, Backing up, Sharing Data, Graphical Environment, Development Environments, Package Tips, Working with the file system, Bypassing NAT (verify page names; record revision ids) |
| `termux-packages` GitHub wiki | Termux-and-Android-10, Termux-file-system-layout, Build-environment, Building-packages, Package-guidelines, Creating-new-package, For-maintainers, Termux-bootstrap (verify names) |
| F-Droid `com.termux` page + `fdroiddata` metadata | version history dates; the F-Droid signing/`sharedUserId` story |
| GitHub API | `releases` for termux-app/termux-api/termux-boot/…; first commit (`commits?per_page=1` + `Link: last`); tags |

`deck/claims.md` rows are written as the tables are filled. Known traps to record with sources
(each is a claim row, verified or marked 미확인 — never asserted from this list):
Termux started 2015 by Fredrik Fornwall (first-commit date from the API); terminal-emulator lineage
(check `terminal-emulator/` headers for the Android Terminal Emulator / Jack Palevich attribution);
the Play Store build stayed at 0.101 for years because of the Android 10 (API 29) `execve`-from-app-data
restriction with `targetSdk ≥ 29` (cite `Termux-and-Android-10` and the issue numbers); F-Droid
release cadence and key ownership (README says maintainers do not hold F-Droid keys — cite line);
`sharedUserId com.termux` and the same-signing-key rule; phantom-process limit **32 for all apps
combined** on Android 12+ (README + issue #2366 + Android-Docs; the `settings put global
settings_enable_monitor_phantom_procs false` workaround — cite, and note it is already applied on
this device per the memory note); `termux-exec` system-linker-exec (present here as
`$PREFIX/bin/termux-exec-system-linker-exec`); bootstrap zips built per ABI in termux-packages CI and
bundled in the APK (verify against `TermuxInstaller` and the CI workflow); glibc packages in the main
repo (verify prefix `glibc-`/`gpkg` and the `glibc-runner`); repositories main/x11/root and TUR
(`tur-repo` package, `tur.kcubeterm.com` as seen on this device); Android minimum version per
termux-app release (check `minSdkVersion` at each tag: 0.118.x requires Android 7? — verify);
latest release v0.118.3 (2025-05-22).

### 3.2 Upstream citations — the `SRC` badge

A slide that explains a mechanism shows the code that implements it: ≤ 45 lines excerpted with
`<!--CODE file=sources/<repo>/<path> sha=<sha> lines=A-B-->` and a `<!--SRC …-->` badge on the same
slide. `check_claims.py` verifies (a) the SHA equals `data/repos.tsv`, (b) the file and lines exist at
that SHA (`git -C sources/<repo> show <sha>:<path>` — so the check works even if the working tree
drifted), (c) every `SRC` on a slide has a matching `CODE` or `OUT` (a badge without an excerpt is an
error: "cite what you show"). Upstream licences (termux-app GPLv3, termux-packages varies, Android
AOSP Apache-2.0) are recorded in `data/repos.tsv` and listed in the appendix; excerpts stay ≤ 45
lines and are attributed on the slide, which is fair use for teaching and within GPL quotation
practice — say so once in the 읽는 법 slide.

### 3.3 Live captures — `run_all.py` → `out/` (each ≤ 2 min, strictly sequential)

| Capture id | side | stable? | What the deck shows |
|---|---|---|---|
| `env_termux` / `env_proot` | both | stable (scrubbed) | `env` sorted, `id`, `uname -a`, `cat /proc/self/status` (Uid/Gid/Seccomp lines), `ls -la /`, `readlink /proc/self/exe` — the two worlds side by side (Part 3, 9) |
| `prefix_tree` | termux | stable | `ls $PREFIX`, `ls $PREFIX/etc`, `find $PREFIX -maxdepth 1`, sizes by `du -s` (snapshot copy for sizes) — the "why not /usr" slides (Part 5) |
| `linker` | termux | stable | `py/elf.py` on `$PREFIX/bin/bash`, `python3`, `ls`: `PT_INTERP`, `DT_NEEDED`, `DT_RUNPATH`; proot-side same for `/bin/bash` — bionic vs glibc (Part 3, 5) |
| `shebang` | termux | stable | a script with `#!/bin/sh` and `#!/usr/bin/env python3` executed with and without `LD_PRELOAD=$PREFIX/lib/libtermux-exec*.so` (`termux-exec` variable names from source); the failure text and the rewritten path (Part 5) |
| `exec_data` | termux | stable | compile `exp/hello.c` with Termux clang into `$HOME/…/termux/scratch`, run it; also copy to `/sdcard` (if storage set up) and run → the "noexec on shared storage" error (Part 5, 8) |
| `dpkg_stats` | termux | stable + snapshot | `dpkg -l` count, `py/pkgstat.py` size histogram, `dpkg -S` for every `termux-*` binary → `data/api_cmds.tsv` owner column is **generated**, not typed (Part 6, 7) |
| `apt_sources` | termux | stable | `sources.list`, `sources.list.d/*`, `apt-key`/`trusted.gpg.d` fingerprints (`gpg --show-keys`), `apt-cache policy` (snapshot) (Part 6) |
| `pkg_script` | termux | stable | `diff $PREFIX/bin/pkg sources/termux-packages/…/pkg` exit 0 — proves the cited source is what runs here (Part 6) |
| `deb_by_hand` | termux | stable | `exp/mkdeb/`: build a 1-file `.deb` with `dpkg-deb --build`, `dpkg-deb -I/-c`, `apt install ./x.deb` (decision 5), run it, `apt remove` **of our own package only** (the denylist exempts the exact name `treasure-hello`) (Part 6) |
| `bootstrap_layout` | termux | stable | `$PREFIX/etc/termux/`, `~/.termux/` names only (no contents — user config), `termux-info` **tools section only** (Android fields come from `data/device.txt`) |
| `api_safe` | termux | snapshot | `termux-battery-status`, `termux-clipboard-get` after `termux-clipboard-set "안녕"`, `termux-toast` exit code, `termux-notification` + `termux-notification-remove`, `termux-vibrate -d 50`, `termux-tts-engines`, `termux-audio-info`, `termux-camera-info` (capabilities only), `termux-sensor -l`, `termux-wifi-connectioninfo` (SSID/BSSID/IP scrubbed), `termux-volume` (get), `termux-dialog` **skipped** (interactive), `termux-saf-dirs` — plus `strace`-free evidence of the mechanism: `ls -l $PREFIX/bin/termux-api`, the socket path from source (Part 7) |
| `api_mechanism` | termux | stable | `cat $PREFIX/bin/termux-battery-status` (a 3-line script calling `termux-api`), `termux-api --help` if any, `py/elf.py` on `termux-api` binary; `am` version (Part 7) |
| `proot_probe` | proot | stable | `cat /proc/self/status | grep TracerPid` (proot = ptrace tracer, non-zero), `getprop` denial, `mount | grep termux`, `/proc/version`, `ls /host-rootfs` or the bind list from `proot-distro login --help` (Part 9) |
| `proot_cost` | both | snapshot | `exp/syscall_loop.c` (1e6 `getpid()`) and `exp/fork_loop.sh` timed on both sides via `exp/timeit.py` (3 runs, median) — the ptrace overhead **as a ratio**, labelled snapshot (Part 9) |
| `phantom` | termux | stable | `cat /proc/sys/kernel/pid_max`, `ulimit -a`, `ps -o pid,ppid,comm` count (snapshot); the README notice quoted with `b`; the killer is **not** triggered on purpose (Part 8) |
| `net_limits` | termux | stable | `exp/bind_port.c` on 80 (EACCES) and 8080 (ok) — the "ports < 1024" slide; `ping` availability (Part 8, 11) |
| `storage` | termux | stable | `ls -la ~/storage` if set up, `df -h /sdcard` (snapshot), `termux-setup-storage` **not run** (interactive/permission) — described with `b` (Part 8, 10) |
| `services` | termux | stable | `sv status` / `runsvdir` if `termux-services` installed (decision 5); `crond` presence (Part 11) |
| `sshd` | termux | stable | `sshd -T | head`, `ls $PREFIX/etc/ssh` names, `sshd` port 8022 default from config — **no keys, no authorized_keys contents** (Part 10) |
| `toolchains` | termux | snapshot | `clang --version`, `python3 --version`, `node --version`, `go version`, `rustc --version`, `git --version` — whichever exist (Part 10) |
| `proot_distro` | termux | stable | `proot-distro list`, `proot-distro --help`, the ubuntu container path (Part 9) |
| `x11` | termux | stable | package presence `dpkg -l | grep -E 'termux-x11|xfce|vnc'`, `termux-x11 --help` if installed — **not launched** (Part 12, decision 7) |
| `session_self` | proot | snapshot | `ps -o pid,rss,comm` of this very session, `free -m` — "이 덱을 만든 환경" (Part 13) |

`tools/record.sh --check` runs `run_all.py` three times and compares md5 of every `stable` file;
expect ≤ 15 min per run. Run it in the background with a Monitor; never while a subagent compiles.

### 3.4 Experiments — `exp/` (C99 + sh + py, tests first, compiled on **both** sides)

| # | File | Property demonstrated | Test (RED first) |
|---|---|---|---|
| 1 | `hello.c` | same source, two libcs: `ldd`-equivalent via `py/elf.py`; sizes | both binaries print the same line; interpreters differ (`/system/bin/linker64` vs `/lib/ld-linux-aarch64.so.1`) |
| 2 | `passwd.c` | `getpwuid(getuid())` on bionic (synthesised names, no `/etc/passwd`) vs glibc | fields differ as the source of termux's `$USER` confusion; documented in `claims.md` from bionic source |
| 3 | `paths.c` | `/tmp`, `/etc`, `/bin/sh` existence probes with `access()` | proot side true, termux side false for `/tmp` and `/bin/sh` (unless termux-exec mode is on — capture both) |
| 4 | `bind_port.c` | `bind()` on 80 vs 8080 | errno EACCES on 80 for both sides (proot is not root on Android either — a common misconception; verify live and say what is true) |
| 5 | `syscall_loop.c`, `fork_loop.sh`, `timeit.py` | ptrace overhead of proot | timings are snapshot; the test only checks the harness (3 runs, median, monotonic clock) |
| 6 | `mkdeb/` (`control`, `postinst`, `build.sh`) | a `.deb` by hand | `dpkg-deb -I` shows our fields; installed file appears in `dpkg -L treasure-hello` |
| 7 | `api_call.sh` | how `termux-battery-status` reaches the app: read the script, call `termux-api` directly with the method name from source | JSON parses; keys match the `termux-api` Java class's output fields (cite) |
| 8 | `shebang/` | scripts with `/bin/sh`, `/usr/bin/env`, `$PREFIX/bin/sh` shebangs under three exec modes | exit codes and error strings pinned; `termux-fix-shebang` result diffed |
| 9 | `signals.sh` | what `[Process completed (signal 9)]` looks like vs a normal exit — **simulated with `kill -9` on our own child**, never by exhausting the phantom limit | exit status 137 captured |
| 10 | `wakelock.sh` | `termux-wake-lock` / `termux-wake-unlock` exit codes and the notification (described) | exit 0 both; lock released in `trap` |

Each program ≤ 120 lines, Korean comments explain *why*; the C files compile with
`-std=c99 -Wall -Wextra -Werror` on both compilers (bionic needs `_GNU_SOURCE`? — record what it needs).

---

## 4. Figures and demos

**Figures** (`deck/gen_figs.py` → `deck/figs/*.svg`, svgkit, viewBox 340; render with `make figs-png`
and *look*): Android app sandbox (uid per app, app-data dir, `/system`), Termux app architecture
(Activity ↔ `TermuxService` ↔ PTY ↔ bash; `terminal-emulator` library), plugin IPC (Termux:API app ↔
`termux-api` binary ↔ socket/`am`), filesystem map (`/data/data/com.termux/files/{usr,home}`, `/sdcard`,
`~/storage` symlinks, `/system`, `/apex`), `execve` path with and without termux-exec, package flow
(termux-packages CI → apt repo → mirror → `pkg` → `dpkg`), bootstrap installation sequence, proot
ptrace loop (tracee syscall → tracer rewrites path → resume), process-limit timeline (Android 12 phantom
limit), version timeline 2015→2026 (from `data/releases.tsv`), repository tiers (main/x11/root/TUR/
glibc), the Play Store vs F-Droid vs GitHub decision tree, Termux:Boot/Widget/Tasker trigger paths,
remote-access topology (sshd 8022, phone ↔ PC), backup/restore flow, threat model diagram (Part 14).
Every number on a figure comes from `out/` or `data/` (generator reads them; no literals).

**Demos** (`deck/demos.js`, plain JS, `window.__demo(id, fn)` as in the transformer deck):
`$PREFIX` path translator (type `/usr/bin/python`, see the termux-exec rewrite rule applied — rule
table transcribed *from the source excerpt on the same slide* and pinned in `check_deck.js` CASES),
shebang doctor (paste a shebang, get the verdict per exec mode), `pkg` command decoder (`pkg in` →
`apt install`, from the cited script), Termux:API command explorer (filter the 84 commands by
permission/privacy/plugin from `data/api_cmds.tsv` inlined), phantom-process budget calculator
(32 total, per-app subtraction — cite), port-permission checker, `.deb` control-file linter,
timeline scrubber (`data/timeline.tsv`), "which install source should I use" decision helper
(decision tree from README lines), release-date lookup. `check_deck.js` CASES pin ≥ 2 outputs per
demo, taken from `data/` or `out/` (never typed).

---

## 5. Work order (do not reorder; each numbered item is at least one commit)

1. **Skeleton** — dirs, Makefile, copied assembler/checks, `SRC` directive replacing `CITE`,
   `CODE file=sources/… sha=…` support, `deck/base` re-titled (new palette: decide once, record in
   the log — suggestion: "terminal on AMOLED": near-black `#0b0f14` paper, light grey ink, Termux's
   green-ish accent measured from the app icon SVG in `termux-app` at the pinned SHA), `data/*.tsv`
   headers, ~35-slide skeleton (cover, 읽는 법, 증거 등급, 캡처의 두 종류, 전체 지도 + 18 part covers)
   that passes `make all SKEL=1`. Nothing in index/README yet.
2. **`tools/tmx.sh` + `tools/scrub.py` + tests** (§2.1, §0.8). RED: denylist cases, scrub cases
   with synthetic phone numbers/MACs/SSIDs/paths. GREEN. Then the first capture `env_termux` to prove
   the door works, committed with its manifest entry.
3. **Research** — `tools/fetch_src.sh`, `tools/doc_text.py`, `tools/gh_api.py` (tests on cached
   fixtures), `sources/` populated at pinned SHAs, then `data/repos.tsv`, `releases.tsv` (every
   termux-app tag with date; plugins' latest), `timeline.tsv` (≥ 80 rows, 2015-…→2026-09),
   `android.tsv` (≥ 15 rows: API 21…36 behaviours that touch Termux), `repos_apt.tsv`, `plugins.tsv`,
   `people.tsv` (from upstream `README`/`AUTHORS`/commit metadata only — no doxxing, handles only),
   and `deck/claims.md`. Re-verify every 2025+ row with WebSearch and stamp it. **Ask the user for
   `data/device.txt` now** (decision 8) so Part 1/8 can cite the device's Android version.
4. **`py/` helpers** (`elf.py`, `deb.py`, `pkgstat.py`) with unit tests on fixture ELF/`.deb` files
   built in the test itself (no binary fixtures committed).
5. **`exp/` 1–10** (§3.4) tests first; compile both sides through `tmx.sh`; commit per batch of 3.
6. **`run_all.py` + `out/manifest.json` + `tools/record.sh --check`** (×3 on `stable`). `api_safe`
   runs last and only after a `free -m` check. Every snapshot file starts with `# snapshot 2026-09-DD`.
7. **Figures** (§4) — generate, `make figs-png`, look, fix, commit.
8. **Deck body, part by part** (§6): fragments with CODE/OUT/TABLE/FIG/SRC directives, quizzes
   every ~15 slides, `make all` green, `budget.txt` within band, one commit per part. Writing order:
   0 → 3 → 5 → 4 → 6 → 7 → 9 → 8 (the "원리" core first so later parts cross-reference real ids) →
   10 → 11 → 12 → 14 → 15 → 1 → 2 → 13 → 16 → 17. Part 2 (history) is written late so each event
   slide can point at the mechanism slide it changed.
9. **Demos** (`deck/demos.js`) + `check_deck.js` CASES from `data/`/`out/`.
10. **Glossary** (`deck/glossary.txt`, `word | meaning | first-slide-id`, ≥ 250 entries) + appendix:
    command index (84 `termux-*` with owner package, generated), package-repository index, release
    table, timeline, full `<!--FULLSRC-->` of `tools/`, `py/`, `exp/`, `run_all.py` (coverage 100 %,
    `pending.txt` empty), quiz answers, bibliography from `claims.md` with fetch dates, licence notes.
11. **Publish**: `make font`, `make font-check`, count slides from the build output, add the
    `index.html` card (section per decision 1) and `README.md` row with the *actual* counts (slides,
    captures, experiments, figures, demos, quizzes, glossary words, cited upstream files). Commit.
12. **Review pass 1 — 정독 with sources open.** Two subagents (parts 0–8 / 9–17), each with
    `claims.md`, `data/`, and `sources/` beside them; every finding re-verified by re-running the
    capture or re-reading the pinned source before fixing. Commit title counts by category:
    `Termux 덱 전수 리뷰 — 사실오류 N건·캡처불일치 N건·인용범위 N건·표기 N건 정정`.
13. **Review pass 2 — a different angle**: beginner reading flow, prose ↔ capture agreement, Korean
    style, demo wording. (The transformer deck needed three passes; budget for two, do a third if
    pass 2 still finds > 20.)

---

## 6. Deck structure and slide budget (cap 3000; assembler prints per-part actual vs target)

| Part | Title (Korean, as in the deck) | Target | Key evidence |
|---|---|---|---|
| 0 | 표지 · 읽는 법 · 증거 등급 · 캡처의 두 종류(고정/스냅샷) · 이 기기 · 전체 지도 | 30 | device.txt |
| 1 | 첫 10분 — Termux 란 · 설치처 고르기(F-Droid/GitHub/Play) · 첫 실행과 부트스트랩 · `pkg` 첫 명령 · 저장소 접근 · 키보드와 추가 키 · 세션과 서랍 · 도움 받는 곳 | 90 | README lines, captures |
| 2 | 역사 — 2015 시작과 계보 · 0.x 릴리스 연표 · Termux:API 와 플러그인 탄생 · Play 스토어 동결(0.101)과 Android 10 · F-Droid 와 서명 키 · Android 11/12 팬텀 프로세스 사건 · 0.118 시대 · TUR·glibc·X11 · Play 스토어 재도전 · 커뮤니티(위키·IRC·이슈) · "2026-09 기준" | 140 | releases, timeline, claims |
| 3 | 안드로이드 위의 리눅스 — 앱 샌드박스와 uid · 앱 데이터 디렉터리 · bionic vs glibc(실험 1·2) · `/system`·`/apex`·`/vendor` · SELinux·seccomp · Zygote 와 앱 프로세스 · 권한 모델 · 스코프드 스토리지 · 리눅스지만 리눅스 배포판이 아닌 이유 | 160 | env captures, exp 1–3 |
| 4 | 원리 I: 앱 — termux-app 구조 · 터미널 에뮬레이터 라이브러리 · PTY 와 `TermuxService` · 부트스트랩 설치 순서 · `sharedUserId` 와 플러그인 · RUN_COMMAND 인텐트 · `termux.properties` · 알림·웨이크락 · targetSdk 가 정하는 것 | 170 | SRC termux-app |
| 5 | 원리 II: 파일시스템과 실행 — `$PREFIX` 가 `/usr` 이 아닌 이유 · 디렉터리 지도 · 셔뱅 문제와 `termux-exec`(LD_PRELOAD execve 후킹 · 시스템 링커 실행) · `termux-fix-shebang` · `/tmp`·`/etc` 대체 · rpath/RUNPATH 패치 · 링커 읽기(elf.py) · 공유저장소 noexec | 160 | exp 3·8, SRC termux-exec |
| 6 | 원리 III: 패키지 시스템 — apt/dpkg 가 안드로이드에서 도는 법 · `pkg` 래퍼 해부 · 미러·서명 키·저장소 계층(main/x11/root/TUR/glibc) · 부트스트랩 zip 이 만들어지는 곳 · termux-packages 빌드 시스템(`build.sh`·`termux_step_*`·패치 정책·NDK 크로스컴파일) · 새 패키지 만들기 절차 · `.deb` 손으로 만들기(실험 6) · 온디바이스 빌드 | 210 | SRC termux-packages, dpkg captures |
| 7 | Termux:API 와 플러그인 — 아키텍처(앱 ↔ `termux-api` ↔ 소켓/`am`) · 명령 84개 카탈로그(소유 패키지·권한·개인정보 등급 자동 표) · 안전한 명령 실습(배터리·클립보드·알림·TTS·센서·진동) · 개인정보 명령의 출력 형식(인용만) · Boot · Widget · Tasker · Float · Styling · X11 앱 | 170 | api_cmds.tsv, api_* captures |
| 8 | 한계와 우회 — 루트 없음 · 팬텀 프로세스 32개와 CPU 킬러 · Doze·배터리 최적화 · targetSdk 와 W^X · 1024 미만 포트(실험 4) · 스코프드 스토리지 · systemd·cron 없음 · bionic 비호환 이식 실패 사례(패치 디렉터리 인용) · proot 오버헤드 · 키보드·화면 · 백업 없이 지우면 끝 · 각 한계의 우회법과 대가 | 160 | README, Android-Docs, exp 4·9 |
| 9 | proot 와 리눅스 배포판 — ptrace 원리 · `proot-distro` 해부 · 설치·로그인·바인드 · 이 세션 자체(proot 안에서 Termux 를 부르는 문) · `getprop` 거부 같은 실제 한계 · 성능 비율(스냅샷) · chroot(루트 기기) · 언제 proot 를 쓰고 언제 안 쓰나 | 130 | proot_* captures, exp 5 |
| 10 | 활용 I: 개발 환경 — 셸·편집기·tmux · git · ssh 클라이언트/`sshd`(8022) · Python·Node·C/Clang·Rust·Go · 빌드 도구 · 동기화(rsync/scp) · 백업과 복원(`termux-backup`) · 도트파일 · 폰 ↔ PC 워크플로 | 190 | toolchains, sshd captures |
| 11 | 활용 II: 자동화와 서버 — `termux-services`(runit)·cron · Termux:Boot 로 부팅 시 실행 · 웹/파일 서버 · 알림 스크립트 · 위젯 단축 · Tasker 연동 · 웨이크락과 배터리 · 원격 접속 토폴로지 · NAT 우회 | 150 | services, exp 10 |
| 12 | 활용 III: GUI 와 데스크톱 — termux-x11 원리 · VNC · 데스크톱 환경 · GPU 가속(virgl/turnip, 인용) · 오디오(pulseaudio) · 성능 기대치 · 무엇이 안 되나 | 100 | x11 capture, wiki |
| 13 | 활용 IV: AI 에이전트와 이 저장소 — Claude Code 를 proot 에서 돌리기 · 메모리와 팬텀 킬러 해제 · 이 덱이 만들어진 환경(session_self) · 서브에이전트 한도 · 이 저장소의 덱들이 Termux 에서 태어난 방법 | 60 | session_self, memory notes |
| 14 | 보안과 개인정보 — 권한 모델 · API 명령의 개인정보 등급 · 키 관리(`termux-keystore`) · `sshd` 노출 · 백업 암호화 · 위협 모델 · 이 덱의 스크러빙 규칙 | 90 | scrub.py, api_cmds.tsv |
| 15 | 문제 해결 사전 — 오류 메시지 → 원인 → 해결(부트스트랩 실패·`signal 9`·`Permission denied`·`No such file /bin/sh`·미러 오류·서명 불일치·`App not installed`·저장소 접근 불가·시계 오차·`CANNOT LINK EXECUTABLE`) | 110 | exp 8·9, README lines |
| 16 | 마무리 — 배운 것의 지도 · 흔한 오해 12가지 · 종합 퀴즈 · 다음 단계 | 40 | — |
| 17 | 부록 — 용어집(≥250) · `termux-*` 명령 색인(84) · 저장소·미러 색인 · 릴리스 표 · 연표 · 소스 전문(tools/py/exp ≈ 2,500줄) · 퀴즈 정답 · 참고문헌(fetch 날짜) · 라이선스 | 320 | FULLSRC + tables |
| | **Total** | **≈ 2,480 (band 1,800–2,600, cap 3,000)** | |

The transformer deck landed at 60 % of its pre-writing estimate (952 of 1,575) and the compression
deck at 44 %; if that repeats here the body lands near 1,500 and that is fine — **do not pad.** If
the total approaches 2,900, tighten parts 10/11 prose — never the evidence, never the appendix.
Per-slide conventions: `id` prefix per part (`p0-` … `p17-`; the assembler rejects collisions), one
idea per slide, quiz every ~15 slides (`<details>` answer), cross-references only as `href="#id"`
(checked by `check_xref.py`).

**Evidence badges** on every slide (`data-ev`): `a` = live capture from this device (`out/`, stable
or snapshot — the snapshot stamp is added automatically from the manifest), `s` = upstream source
excerpt (`SRC`), `b` = documentation/issue cited in `claims.md`, `c` = historical/news source cited,
`ill` = illustration/diagram. The assembler counts them per part; a part with < 60 % a+s+b+c is a
warning to look at. Parts 4–7 should be mostly `a`+`s`; Part 2 mostly `b`+`c`.

---

## 7. Makefile targets (implement all; `make all` is the gate)

`test` (python unittest over tools/ py/ exp/tests; `exp/*.c` compiled both sides) · `sources`
(fetch_src.sh + doc_text.py, idempotent, pinned SHAs) · `sources-check` (every `data/repos.tsv` SHA
present in `sources/`) · `run` (run_all.py → out/) · `run-check` · `record` (×3, md5 of `stable`) ·
`scrub` (fails on any privacy hit in out/) · `figs` · `figs-png` · `figs-check` · `tables` ·
`claims-check` (every `SRC` resolves at its SHA; every year in the body is in claims.md or data/;
every `2025+` claim carries a stamp) · `width` · `deck` · `deck-verify` · `deck-slices` · `deck-xref`
· `deck-check` (DOM stub + demo CASES) · `font` · `font-check` · `all` = sources-check tables
run-check scrub figs-check deck deck-verify deck-slices deck-xref deck-check claims-check width font
font-check · `clean` (never touches `$PREFIX` or `$HOME` — only `termux/out/`, `termux/scratch/`,
`termux/sources/` on `distclean`).

---

## 8. Definition of done

- `make test` green (expect ~120 Python tests + the exp/ assertions on both sides); the `tmx.sh`
  denylist tests pass; `scrub.py` finds nothing in `out/`.
- `make record` three times → identical md5 for every `stable` file in `out/`; every `snapshot` file
  carries its date line; `manifest.json` lists every file in `out/` (no orphans).
- `pkg` script diff against the pinned source is exit 0; every `SRC` badge resolves at its SHA.
- `make all` green: 0 assembler errors, coverage 100 % for our code, ≤ 3000 slides, every year
  sourced, layout check passes at 374 px and 768 px, font check passes, demo CASES pass.
- Every 2025+ statement carries a "2026-09 기준" stamp and a fetched source in claims.md; the
  latest-release slide matches `data/releases.tsv` on the build date.
- The host Termux is unchanged except for packages installed under decision 5 and the `treasure-hello`
  test package (removed at the end of `run_all.py`); `~/.termux/` untouched; no `$PREFIX/etc` edits.
- `index.html` card + `README.md` row with real counts; one commit per §5 step; progress log below.
- Review passes 1 and 2 done with category counts in the commit titles.

---

## 9. Decisions — CONFIRMED by the user on 2026-09-18 (do not re-ask)

The user approved every recommendation below as-is. Each row is now a decision.

| # | Question | Decision |
|---|---|---|
| 1 | File name / card placement | `Termux_대백과사전.html` (matches 압축·무선통신 naming); card in the existing **"🖥️ 시스템 & 셸 도구"** section of `index.html` and `README.md`, next to the Linux 명령어 핸드북 |
| 2 | Slide cap / band | 3000 hard (user); target band 1,800–2,600; never pad |
| 3 | Live captures from the host Termux | **Yes** via `tools/tmx.sh` with the denylist in §0.7 — this is the deck's unique evidence. Alternative (captures re-typed from the wiki) would make it a summary of the wiki |
| 4 | Privacy-sensitive Termux:API commands | **Never executed**; output formats cited from source (§0.8). Safe set in §3.3 `api_safe` runs once as snapshot |
| 5 | Installing packages on the host | Allowed for **≤ 20 MB each, ≤ 5 packages total**, needed by a slide (expected: `termux-services`, `runit`, `cronie`, `termux-api` if missing, `tur-repo` already present), each logged with size in the progress log. Never `pkg upgrade`, never remove existing packages. The hand-made `treasure-hello` `.deb` is installed and removed inside `run_all.py` |
| 6 | Screenshots / photos | **None**: the app UI, notifications and plugin screens are drawn as SVG from the source's layout/strings. The user may add real screenshots later as a `PHOTO`-style directive if wanted |
| 7 | GUI part (termux-x11/VNC) | Written from wiki/source with `b`/`s` badges plus package-presence captures; **not launched** on this device (RAM). Say so on the part cover |
| 8 | Device facts proot cannot read | The user runs, once, in native Termux (not proot): `termux-info > ~/github/treasure_house/termux/data/device.txt; getprop ro.build.version.release >> …; getprop ro.build.version.sdk >> …; settings get global settings_enable_monitor_phantom_procs >> …` — the file is scrubbed (`scrub.py` runs on `data/` too) and committed |
| 9 | Part 13 (AI agents / this repository) | **Include** at ~60 slides: it is the one part no other Termux document has, and it is verifiable from `session_self` and the memory notes. Drop to 20 if the user prefers a purely Termux-focused deck |
| 10 | Bionic/glibc experiments | Compile `exp/*.c` both sides (Termux clang + proot gcc) — 10 small programs, no third toolchain, no Rust/Go builds (RAM) |
| 11 | Depth of the package-build-system part (Part 6) | Read and cite `termux-packages` scripts; **no** Docker/on-device full build (impossible/too heavy). One hand-made `.deb` is the practical exercise |
| 12 | Language register | 합니다체 prose, as in the transformer deck; shell prompts shown as `$` (Termux) and `#` (proot, uid 0) so the side is visible in every capture |

---

## Progress log (append only; newest at the bottom; one entry per commit)

### Plan (2026-09-18)

- Plan written; §9 decisions 1–12 confirmed by the user as recommended. No code yet.
  `data/device.txt` (decision 8) is still to be pasted by the user — ask for it at step 3, once.

### Step 1 — Skeleton (2026-09-18)

- Copied verbatim from `transformer/`: `deck/{build_deck,verify_deck,check_slices,check_xref,check_claims,
  chunks,gen_glossary,gen_tables,svgkit}.py`, `deck/check_deck.js`, `deck/base/{head,tail}.html`,
  `tools/{width,rewrap}.py`, `tools/record.sh`. Then adapted only what §1 lists.
- **New `deck/srcpin.py`** (+ `deck/tests/test_srcpin.py`, 17 tests, RED on NotImplementedError
  stubs → GREEN): reads `sources/<repo>/<path>` **at the pinned SHA via `git show`**, never the
  worktree; `check(repo, sha)` accepts ≥ 7-char prefixes of the pin; `missing()` backs
  `make sources-check`. build/verify/check_claims/check_slices all read upstream through it.
- `build_deck.py`: TARGET → `Termux_대백과사전.html`; `LANG_OF` adds java/kt/kts/gradle (java
  highlighter), xml, properties, diff/patch; `COVER_DIRS` = py/ exp/ tools/ (+ Makefile, run_all.py);
  `PARTIAL` = tests, deck/, out/, data/, sources/, scratch/ (tools/ is **not** partial here — §1 says
  100 % for our code); `HARD_CAP` 3000. `CITE` → **`SRC`** (`repo= path= sha= lines=`), badge text
  `repo@sha7 · path:A–B`, logged to `deck/src_used.txt`; new post-pass "cite what you show": a slide
  with a SRC badge must carry a CODE of that file or a capture. `CODE file=sources/…` requires `sha=`
  equal to the pin and emits `data-sha`. `OUT` reads `out/manifest.json` (format fixed now:
  `{file: {kind: stable|snapshot, side: termux|proot|both, date}}`) → side tag "Termux $"/"proot #"
  and, for snapshots, a `<p class="stamp">이 기기 · YYYY-MM 캡처</p>`; a capture missing from an
  existing manifest is an error. Evidence tiers are now **a·s·b·c·ill** (§6): every slide except
  covers/part covers/quizzes must carry one; `a` needs a capture/table/figure/demo on screen, `s`
  needs a SRC badge; per-part a+s+b+c < 60 % is a warning (part 0 exempt — it describes the deck).
  The old "C ≤ 10 %" warning was dropped (c is legitimate history evidence here). Quiz index and
  glossary ids moved to `p17-`.
- `check_claims.py`: section check → SRC line check at the SHA; years are checked per `<article>`
  and any year ≥ 2025 needs "2026-09 기준" on the same slide (§0.4). Unit filter rewritten.
- `verify_deck.py`: upstream CODE compared with the pinned blob (and `data-sha` must equal the
  current pin); SRC badges must carry `data-repo`/`data-sha` equal to the pin; snapshot stamps
  must carry a date. `check_slices.py`: finds `lines=` anywhere in the directive (sha= sits
  between). `check_deck.js`: CASES emptied (comment: expected values come from data/ or out/).
- Smoke-tested in a scratch copy with a throwaway git repo: SRC+CODE at the pin, worktree drift
  (verify still matched the pinned blob), stable + snapshot OUT; and eight failure paths (sha
  mismatch, unknown repo, badge without excerpt, a/s without proof, missing tier, capture not in
  manifest, SRC lines past EOF, 2025 without stamp) each produced its error.
- **Palette decided (once): "AMOLED terminal", measured from termux-app@084d709.** The plan
  assumed a "green-ish accent from the app icon"; **the icon has no green** — `art/ic_launcher.svg`
  is a `#000` screen, `#BFCBCD` bezel, `#FFF` block cursor, and the adaptive icon is white on
  `@android:color/black`. So: paper `#000`→`#0b0f14`, ink `#e5e5e5` (dim white), titles `#fff`,
  accent `#00cd00` (dim green), special `#6495ed` (dim blue = "captured on this device"),
  border = bezel `#BFCBCD` at 26 %, all taken from `TerminalColorScheme.java`'s
  `DEFAULT_COLORSCHEME` first 16 colours; `--bad #ff5f5f` (256-cube) because `#cd0000` is
  unreadable on black. `--g1..g6` now mean layers: Android/OS yellow, Termux green, packages cyan,
  proot magenta, limits red, device/outside bezel grey. Every hard-coded light colour in head.html
  (~90 sites) was remapped; svgkit fallbacks match; `make figs-png` renders with `-b '#000000'`.
  New CSS: `.tier.s`, `.srcb`, `.stamp`, `.side.termux/.proot`; `.cite` removed.
  **Not yet eyeballed in a browser** (no Playwright here) — first look is the user's.
- `Makefile`: every §7 target; ones whose inputs arrive later print "아직 없다 (§5 N단계)".
  `clean` touches only this dir; `distclean` adds `sources/`. `.gitignore`: sources/ scratch/
  .build/ .svgrender/ __pycache__/.
- `data/` header-only TSVs: repos (with a `license` column, §3.2), releases, timeline, android,
  repos_apt, api_cmds, plugins, people. `deck/claims.md` lists the §3.1 traps as *things to
  verify*, not claims. `budget.txt` = §6 table; `pending.txt` = Makefile, run_all.py, tools/*.
- 34-slide skeleton: cover, part-0 cover, 15 part-0 slides (다른 점 · 약속 · 읽는 법 · 증거 등급 ·
  소스 배지 · 캡처 두 종류 · $ 와 # · 개인정보 · 인용과 라이선스 · 이 기기(placeholder until
  device.txt) · 층 색 · 지도 · 쓴 순서 · 함께 볼 덱 · 접힌 화면) + 17 part covers.
  Part 12's cover says X11/VNC are **not launched** here (decision 7).
- `make all SKEL=1` green: 0 assembler errors, verify passes, slices 0, xref 17 OK,
  check_deck 11/11, claims-check 0, width clean, DeckMono 32 KB embedded, font-check passes.
  Budget line: "쓴 것 34장 · 남은 부 목표 합 2450장 · 예상 합계 2484장 (상한 3000)".
- **Deviations, recorded:** (1) accent colour — see palette above. (2) Evidence badges use the
  inherited `<span class="tier X">` rather than a `data-ev` attribute; the assembler enforces them
  on every content slide, which is what §6 asks. (3) Part covers carry no numbers or versions that
  §6 lists (0.101, 32, 84, 8022) — no claims.md rows yet. (4) `tools/record.sh` is still the
  transformer's (md5 over out/*.txt + ckpt); it is rewritten with tests at step 6 to compare only
  manifest `stable` files. (5) The upstream pin used for the palette (termux-app 084d709,
  2026-09-16) is provisional; step 3 pins repos.tsv and re-checks the colour source lines.

### Step 2 — tmx.sh + scrub.py + first capture (2026-09-18)

- `tools/tmx.sh` (+ `tools/tests/test_tmx.py`, 12 tests incl. 52 denied sub-cases; RED 71 → GREEN).
  Denylist runs **before** execution for both sides; each denied case is proven not to run by a
  trailing `touch` that must not create its marker. Covers every §0.7 item plus all §0.8 privacy
  commands, `termux-open*`/`termux-am`/`am start…`, `termux-setup-storage`, `termux-dialog`;
  installs need `--allow-install` (decision 5); `treasure-hello` removal is exempt; `rm` of
  anything under `$PREFIX`/`$HOME`/`/root` outside `termux/scratch` (and any recursive rm outside
  scratch or `/tmp/`) is refused. `--dry-run` prints the verdict only. Deviation: tests are Python
  (`tools/tests/test_tmx.py`) instead of `exp/tests/test_tmx.sh`, so `make test` runs one runner.
- **Finding that changes the deck's framing:** Termux binaries launched from here are still
  **ptrace'd by proot** (`TracerPid` non-zero, captured). Files, dpkg db and ELF headers are real,
  but `id` (uid=0), `uname` (`6.17.0-PRoot-Distro`) and `getcwd` (returns the guest path `/root/…`
  even after `cd /data/data/…/home/…`) are proot's view. So `side=termux` means "Termux's binaries
  and environment", never "native Termux". Native identity/kernel values must come from the
  user-run file (decision 8, extended at step 3). An attempt to probe for a native launch path was
  refused by the session's permission classifier as a containment escape; not pursued.
- Also true, and a Part 5 slide: `bash -c 'readlink /proc/$$/exe'` prints `…/bin/coreutils`,
  because bash execs the last simple command in place (the test was corrected to measure bash
  while it is still alive — the assertion itself was unchanged).
- `tools/scrub.py` (+ 34 tests; RED 32 → GREEN): `fix()` replaces SSID/BSSID/public IPv4+IPv6/
  paths under `$HOME` or `/root` outside the repo/shared-storage file names; `problems()` fails on
  phone, 15-digit IMEI/IMSI, serial, MAC (Android's 02:00:… placeholder allowed), GPS, e-mail
  (public noreply allowlist), leftovers of the above, and the user's names — **known only as
  SHA-256 prefixes**, never in plain text. Reports mask values. One real false positive
  (`main/x11/root/TUR` read as `/root`) was turned into a test before fixing.
- `run_all.py` skeleton (+ 17 tests with a fake runner): `Capture`/`Step`, sections `== N. 제목 ==`,
  prompt `$`/`#` by side (decision 12), scrub before write, snapshots frozen with
  `# snapshot DATE` and never re-recorded without `--resnap`, stable entries carry **no date** (so
  the manifest is stable too), `--check` = manifest ↔ files, ≤ 108 cells, scrub problems.
  First capture `env_termux` (stable): md5 identical over three runs.
- `make test` 80 passed; `make all SKEL=1` 0 errors.

### Step 3a — research tools (2026-09-18)

- `tools/fetch_src.sh` (+ 8 tests on local `file://` remotes with filter/any-SHA enabled): clones each
  `data/repos.tsv` row at its pin; `history=full` = all commits with `--filter=tree:0` (first-commit
  and tag dates come from git, not the 60/h API), `shallow` = the pin only; `paths` = sparse cone.
  `repos.tsv` gained two columns (`history`, `paths`) — srcpin reads by header, nothing else moved.
- `tools/doc_text.py` (+ 21 tests): MediaWiki wikitext / Markdown / HTML → text whose headings are
  `N.N<TAB>title`. **MediaWiki pages are pinned by revid** (`action=parse&oldid=`), Markdown is read
  at the repo pin, HTML (developer.android.com) is cached raw and pinned by its SHA-256 prefix.
  A real duplicate-number bug (`### A` then `## B` both "1.1", seen in Build-environment.md) became
  a test before the fix; `page=` queries follow redirects.
- `tools/gh_api.py` (+ 7 tests on cached fixtures): every response cached in `sources/gh/`;
  releases paged oldest-first; 21 of 60 hourly calls used in total for step 3.
- `tools/native_facts.sh` (+ 5 tests with fake getprop/settings/termux-info on PATH): decision 8,
  **extended** with `id`, `uname -a` and `/proc/self/status` identity lines because step 2 showed
  proot fakes them. Read-only by test. The user was asked once (terminal notification) to run it in
  native Termux; until `data/device.txt` exists the "이 기기" slide stays a placeholder.
- `scrub.py`: second real false positive (15 digits inside a 40-hex SHA read as IMEI) → test → fix
  (alnum boundaries).

### Step 3b — sources pinned, data tables, claims (2026-09-18)

- `data/repos.tsv`: 26 repos pinned at the 2026-09-18 remote HEADs (ls-remote), pinned-date = commit
  date, licence read from each pin's LICENSE/COPYING (README where no file); 208 MB in `sources/`
  (termux-packages sparse: 20 package dirs + scripts + .github). Includes the three GitHub wikis and
  `termux.github.io` (dated announcement posts).
- `data/docs.tsv`: 127 documents — 69 wiki.termux.com pages (revid-pinned), 20 GitHub-wiki pages,
  22 READMEs, 2 Android-Docs pages, 4 website posts, 10 developer.android.com pages.
- `data/releases.tsv` 330 releases of 12 repos (GitHub API); `data/app_sdk.tsv` (new) minSdk/targetSdk
  of all 95 termux-app tags from `git show <tag>:app/build.gradle`.
- Findings worth slides: targetSdk has been 28 since v0.66 (2019-01-21); minSdk went 21→24 at v0.76
  (2019-10-20) while the README dates the Android 5/6 drop to "2020-01-01 at v0.83" — and there is
  no v0.83 tag; the 0.119 betas are back at minSdk 21. The last old Play build was v0.101 (2022-02-15
  post). The app icon has no green (palette note, step 1).
- `timeline.tsv` 81 rows (git first commits, GitHub releases, SDK changes, issue/PR dates via API,
  wiki first revisions via MediaWiki API, website posts); `android.tsv` 19 rows (API mapping from
  developer.android.com; `year` left empty — no source for release years was fetched, so the deck
  does not state them); `repos_apt.tsv` 5 tiers (fingerprints to be filled from the step 6 capture —
  gpg is not installed on the proot side); `plugins.tsv` 7; `people.tsv` 7 (names only as they
  appear in commit metadata or upstream files); `claims.md` 49 sourced rows.

### Step 4 — py/ helpers (2026-09-18)

- `py/elf.py` (+ 10 tests): reads PT_INTERP, DT_NEEDED, DT_RUNPATH/RPATH, DT_SONAME from program
  headers only (what the linker reads), ELF32/64 · LSB/MSB; DT_STRTAB vaddr mapped through PT_LOAD.
  Tests build ELF bytes in-process (64/32/big-endian/static/truncated/non-ELF) and cross-check a
  gcc binary against `readelf -d -l`. On the device: Termux bash → `/system/bin/linker64`,
  RUNPATH `$PREFIX/lib`, needs libandroid-support/libreadline/libiconv/libdl/libc; Ubuntu bash →
  `/lib/ld-linux-aarch64.so.1`, libtinfo/libc.so.6.
- `py/deb.py` (+ 10 tests): ar parser + tarfile (none/gz/xz/bz2; zst named and refused, not
  guessed); control parser with continuation and ` .`; tests build .debs by hand and against real
  `dpkg-deb --build`; report clipped by display cells (Korean = 2).
- `py/pkgstat.py` (+ 6 tests): dpkg status paragraphs → installed-only summary, KiB histogram with
  1024-based edges (the first test draft used 1000 and mislabelled it "1 MiB" — corrected in the
  test before implementing). Device, proot-read: 170 installed, 3,393,552 KiB, 30 Essential.
  (The plan's "326 dpkg packages" was a line count, not a package count.)
- Tests 146 total pass; `make all SKEL=1` 0 errors.

### Step 5 — experiments 1–10 (2026-09-18)

- C (1–5): `hello.c passwd.c paths.c bind_port.c syscall_loop.c`, each compiled **twice** in
  `exp/tests/test_exp.py` — proot gcc (glibc) and Termux clang via `tmx.sh` (bionic), both with
  `-std=c99 -Wall -Wextra -Werror -D_DEFAULT_SOURCE` (bionic needed nothing extra). Builds go to
  `scratch/build/{glibc,bionic}/`. Scripts (6–10): `mkdeb/` (control, postinst, payload, build.sh),
  `api_call.sh`, `shebang/` (three shebangs + runner), `signals.sh`, `wakelock.sh`, plus
  `fork_loop.sh` and `timeit_exp.py` (renamed from `timeit.py`: it would shadow the stdlib module).
  18 tests, RED 17 → GREEN.
- **Findings (captured in step 6, all proot-side):**
  1. Bionic `getpwuid(10123)` → `u0_a123`, home = Termux `$HOME`, shell = `$PREFIX/bin/login`,
     because termux-packages `ndk-patches/29/pwd.h.patch` replaces getpwuid with an inline
     polyfill (SRC-citable). glibc: `(없음)`.
  2. Under proot the Termux binaries see Ubuntu's filesystem: `/tmp`, `/bin/sh`, `/etc/passwd` all
     exist, and all three shebangs run. The native answer needs the user-run script.
  3. `bind()` on 127.0.0.1, scanning 1–1100 (both libcs, identical): only **20–23, 80, 443, 445,
     515, 631** succeed below 1024; everything else below 1024 is EACCES. Not proot's port_switch
     (`getsockname` returns the same port; `-p` shifts by +2000 only when enabled) and not found in
     the proot sources — the cause is **unverified** and the deck will say so (미확인), showing the
     capture only. The plan's expectation "80 fails with EACCES" is false on this device.
  4. `api_call.sh` now reads the method name from the installed `termux-battery-status` script
     (`$PREFIX/libexec/termux-api BatteryStatus`) instead of hard-coding it; the test was rewritten
     to assert that property (the first draft faked `termux-api` on PATH, which is not where it lives).
- `tools/native_facts.sh` extended (+2 tests): `$LD_PRELOAD`, `/proc/mounts` line for
  `/storage/emulated` (noexec evidence, read-only — no file is written to shared storage), pid_max,
  `ulimit -a`, and the bionic experiments + shebang runner with and without `LD_PRELOAD`. Missing
  builds are reported, not skipped silently.
- Tests: 166 pass; `make all SKEL=1` 0 errors.

### Step 6 — run_all.py captures + record.sh (2026-09-18)

- `run_all.py`: 26 captures (20 stable, 6 snapshot) + `Import('native_device', data/device.txt)`
  (+3 tests) which turns the user-run native file into a `side=native` snapshot once it exists.
  `record.sh` rewritten (+3 tests with a fake run_all in a temp dir) to md5 only manifest-`stable`
  files. **`make record`: stable captures 20 identical over three runs.** Long commands moved into
  tested scripts (`exp/build.sh`, `exp/pkg_diff.sh`) so every capture line stays ≤ 108 cells.
- Incident, recorded: the first draft of `test_record.py` ran against the *old* record.sh, which
  launched the real run_all.py concurrently with the background first run. It was stopped within
  two minutes; the two snapshots taken in that window (`apt_policy`, `proot_cost`) were re-taken
  with `--resnap`, and the new record.sh takes `RECORD_BASE` so tests never touch the real tree.
  A careless `pkill -f` also matched its own shell once — no other effect.
- **Decision 5 is unusable from this session:** Termux's apt refuses uid 0
  (`packages/apt/0010-prevent-usage-as-root.patch`, SRC-citable), and proot reports uid 0. No
  package was installed; the host keeps its 170 packages. `dpkg -i` has no such check, so the
  hand-made `treasure-hello` is installed and removed inside `deb_by_hand` (host unchanged after).
  Parts 11 (services, cron) will be written from sources/docs, not captures.
- Other proot-side facts captured: `getprop` → "Operation not permitted" (exit 126);
  `proot-distro` refuses to run inside proot; `termux-info` prints "Running as root. Cannot check
  package updates." and empty Android fields; Termux:API commands time out (exit 124) — so the
  "safe API" outputs moved to `tools/native_facts.sh` (read-only ones only; no toast/vibrate/
  notification/clipboard, which would touch the user's screen or clipboard — deviation from §3.3).
- `pkg_script`: `termux-tools` was re-pinned from HEAD to tag **v1.45.0** (the installed version is
  `1.46.0+really1.45.0-1`). With the four `@…@` placeholders filled, the only difference between
  the pinned `pkg.in` and the installed `$PREFIX/bin/pkg` is line 1, the shebang
  (`#!/bin/bash` → `#!$PREFIX/bin/bash`) — the build rewrites it (Part 5/6 evidence).
- `proot_cost` (snapshot): 200 000 `getpid` in 47 ms median but 100 `true` execs in 8.2 s under
  proot — proot does not stop on every syscall (to be sourced in Part 9 before any claim);
  native timings for the ratio come from `native_facts.sh` (timeit added, +test).

### Step 7 — figures (2026-09-18)

- `deck/gen_figs.py`: 18 SVGs (viewBox 340). Structural: sandbox, app_arch, api_path, execve_path,
  package_flow, bootstrap_seq (the five steps of TermuxInstaller's header comment), proot_loop,
  install_tree, plugin_dirs, ssh_topology, backup_scope, threat_model. Data-driven: repo_tiers
  (repos_apt.tsv), release_bars (releases.tsv), sdk_steps (app_sdk.tsv), phantom_steps
  (android.tsv, new `short` column), pkg_sizes (out/dpkg_stats), port_scan (out/exp_bionic).
- Rendered with `make figs-png` (black background) and **looked at**: 5 of 18 fixed — truncated
  path in sandbox, phantom text cut mid-word and an unrelated `am` row, SDK legend over the line,
  release bars silently skipping 2023 (a year with no release), identical subtitles in plugin_dirs;
  proot_loop's title narrowed to path syscalls after the proot_cost snapshot contradicted it.

### Step 8 · Part 3 — 안드로이드 위의 리눅스 (2026-09-18)

- Tooling first (own commit): `srcpin.py grep repo:path PATTERN` (+3 tests) prints `line:match` from
  the **pinned** blob — used by new `src_*` captures for files whose lines exceed 72 cells (XML
  manifests). Such captures run on the Termux side because this session's `git` is Termux's
  (`$PREFIX/bin/git`, bionic under proot) and the proot-side tmx PATH has none. `scrub.py` keeps
  Android's standard shared-storage directory names (DCIM, Download, …, Termux's own
  `Android/{media,data}/com.termux…`) and hides only what is below them (+1 test).
- Part 3 written: 54 slides (budget 160; not padded). Evidence: a 13 · s 5 · b 17 · ill 16 + 3
  quizzes. Key captured facts: proot shows uid 0 but supplementary groups keep
  `20123(u0_a123_cache)`/`50123(all_a123)` → app id 123 (AID arithmetic from
  android_filesystem_config.h); `/storage/emulated` is `fuse … noexec` in `/proc/mounts`; Termux clang
  targets `__ANDROID_API__ 24`; bionic `getpwuid` home/shell come from the `pwd.h` NDK patch (SRC).
  `/apex`/`/vendor` were dropped from the chapter — no source fetched for them; the wiki's rootfs
  table (which does not list them) is what the slide shows.

### Step 8 · Part 5 — 파일시스템과 실행 (2026-09-18)

- Pins: `termux-exec` stays at HEAD 2cd0ba6 (= tag v2.5.0, the installed `1:2.5.0-1`); new repo
  `termux-core-package` pinned at tag v0.4.0 (installed `0.4.0-1`; MIT) because `termuxPrefixPath()`
  lives there. Installed versions of termux-exec/core are now in the `pkg_script` capture.
- Assembler: `<pre>` blocks whose code comes from `sources/` may be up to 108 cells (like
  captures) — re-wrapping upstream code would falsify it; longer lines must still be cut out of the
  cited range (hit twice: paths.h line 15 at 168 cells, manifest lines). `.srcb` badges now wrap.
- `doc_text.py`: `__bold__` stripping ate the `__` inside identifiers such as
  `TERMUX_EXEC__SYSTEM_LINKER_EXEC__MODE` — test first, then word-boundary fix.
- New capture step: `env_termux` 6 = `/proc/self/attr/current` → **`u:r:untrusted_app_27`**, which
  proot cannot fake; with the sepolicy quoted in Android-Docs (targetSdk 26–28 keep
  `execute_no_trans` on app data) it is the direct evidence of why targetSdk 28 matters. The first
  take leaked a trailing NUL into the capture; `run_all --check` now rejects control characters
  (+1 test) and the command strips it visibly (`tr -d '\0'`).
- `prefix_du` re-snapped: `du` dies inside proot-distro's container bind paths, so the container is
  excluded (stated on the slide).
- Part 5 written: 47 slides (budget 160). a 12 · s 13 · b 12 · ill 10, 2 quizzes, 18 cited ranges
  all passing check_slices (two moved to blank-line boundaries; `py/elf.py` got one blank line so
  its excerpt starts on a block boundary — code unchanged, tests green).
