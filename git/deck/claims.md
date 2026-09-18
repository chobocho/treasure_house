# 주장 대장 — 이 덱이 적는 모든 사실의 출처

> **규칙: 슬라이드에 적기 전에 여기 먼저 적는다.** (PLAN.md §0.4)
>
> 날짜·버전 번호·사람 이름·인용문·메일링 리스트 사건·CVE 번호·회사의 도입
> 사례 — 기억으로 적을 수 있을 것 같은 것일수록 반드시 틀린다. 한 줄을 여기
> 적는 일은 30초지만, 틀린 한 줄을 독자가 믿는 일은 되돌릴 수 없다.
>
> 출처의 우선순위 (위가 강하다):
>
> 1. git 저장소 그 자체 — 커밋 해시나 태그. `make mirror` 로 받은 부분 복제
>    (`mirror/git.git`)에서 `git log`·`git show` 로 확인한다.
> 2. `Documentation/RelNotes/*.adoc` — `make docs` 로 `docs/` 에 받아 둔 것.
> 3. lore.kernel.org 의 메일(메시지 id) · git-scm.com 문서.
> 4. Pro Git 책(CC BY-NC-SA 3.0) — **인용하고 풀어 쓸 뿐, 문단을 옮기지 않는다.**
> 5. 위키백과 — **그 문서의 각주를 따라가 원출처를 확인한 경우에만.**
>
> 근거를 못 찾은 문장은 둘 중 하나다: 빼거나,
> 슬라이드에 `<span class="unv">미확인</span>` 을 붙여 모른다고 적는다.
>
> **지식 기준일 규율** — 2025년 이후의 일(최신 git 버전, SHA-256 상호운용
> 현황, reftable 기본값, GitHub·GitLab 기능 변화, "현재의" CVE)은 만들 때
> WebSearch 나 mirror/ 로 다시 확인하고 본문에 "2026-09 기준" 을 박는다.
> 기준점은 이 기계에 설치된 git 2.55.0 과 그 `RelNotes/2.55.0.adoc` 이다.
> (PLAN.md §0.5)

## 적는 꼴

한 줄에 주장 하나. 칸은 넷이다.

```
| 주장 | 출처 | 어떻게 확인했나 | 확인한 날 |
```

- **주장** — 슬라이드에 적힐 문장 그대로. "대략", "약" 같은 말을 빼고 수를 적는다.
- **출처** — 커밋 해시·태그, RelNotes 파일과 절, 메일 메시지 id, URL 중 가장 강한 것.
- **어떻게 확인했나** — `mirror: git show -s --format=%ci e83c5163` ·
  `docs/relnotes-2.23.0.txt 1절 인용` · `WebSearch 2건 교차` 처럼, 다음 사람이 되짚을 수 있게.
- **확인한 날** — YYYY-MM-DD. 빠르게 바뀌는 사실은 이 날짜가 곧 유효기간이다.

`deck/check_claims.py` 가 조각 산문에 적힌 네 자리 연도를 전부 훑어,
이 파일이나 `data/*.tsv` 에 없으면 빌드를 멈춘다. 연도처럼 보이지만
연도가 아닌 수는 `deck/years_ok.txt` 에 적는다.

## 이미 알고 있던 함정 — 4단계(2026-09-18)에서 이렇게 풀었다

| 함정 | 결론 | 근거 |
|---|---|---|
| "발표" 2005-04-06 대 첫 커밋 2005-04-07 대 1.0 2005-12-21 | 셋 다 맞고 뜻이 다르다. 4-06 은 BitKeeper 를 떠난다는 LKML 메일(git 이라는 이름은 없다), 4-07 은 e83c5163, 12-21 은 1.0.0 태그와 발표 메일 | docs/mail-kernel-scm-saga.txt · mirror e83c5163 · docs/mail-announce-1.0.0.txt |
| Hamano 가 유지보수자가 된 날 7-26 대 7-27 | 메일은 태평양 시각 7-26 20:04 에 쓰였고(UTC 7-27 03:24), 본문은 "지난 24시간 동안" 이미 소유자가 바뀌어 있었다고 말한다. 덱에는 "2005-07-26(태평양 시각)" 으로 쓴다 | docs/mail-meet-new-maintainer.txt 의 Date·Message-Id |
| BitKeeper 무료판 철회 시점 | LWN 2005-04-06 기사가 "BitMover is now withdrawing support for the free version" 이라 적는다. 역공학을 한 개발자의 이름은 기사에 없으니 덱도 붙이지 않는다 | lwn.net/Articles/130746 |
| "git" 이름의 농담 | e83c5163 의 README 첫 줄 "GIT - the stupid content tracker" 와 네 가지 뜻 목록 — mirror 에서 그대로 인용한다(기억으로 옮기지 않는다) | mirror: git show e83c5163:README |
| GitHub 창업 대 공개 | 공개 2008-04-10 은 GitHub 블로그 원문으로 확인했다. **창업 날짜는 1차 출처를 찾지 못해 덱에 싣지 않는다** | github.blog "We launched" |
| SHAttered 와 sha1dc | SHAttered 2017-02-23(구글 보안 블로그). sha1dc 가 기본이 된 것은 2.13.0(태그 2017-05-09) | Google Security Blog · RelNotes 2.13.0 |
| SHA-256 | 2.29.0(2020-10-19) 노트가 "experimental" 표시와 "상호운용은 아직 없음" 을 함께 적는다. 도입의 기반은 2.16.0 부터 | RelNotes 2.29.0 · 2.16.0 |
| switch/restore | 2.23.0(2019-08-16) | RelNotes 2.23.0 |
| ort 기본 | 2.34.0(2021-11-14). 2.32 에서 시험 틀이 ort 를 기본으로 돌릴 수 있게 됐다 | RelNotes 2.34.0 · 2.32.0 |
| init.defaultBranch | 2.28.0(2020-07-26) 노트는 "첫 브랜치의 기본 이름을 설정할 수 있게 했다" 고만 쓰고 변수 이름은 적지 않는다 — 변수 이름은 v2.55 문서로 인용한다 | RelNotes 2.28.0 · docs/git-init.txt |
| reftable 의 현재 위치 | 2.45.0(2024-04-29) 에 백엔드로 들어왔고, 2026-09 기준 v2.55.0 의 BreakingChanges 는 Git 3.0 에서 새 저장소의 기본으로 바꿀 계획이라 적는다(출시일 미정) | RelNotes 2.45.0 · docs/BreakingChanges.txt |
| Mercurial 발표 4-19 대 4-20 | 본문 첫 줄은 "April 19, 2005", LKML 게시 시각은 4-20 05:12 EST — 둘 다 원문에 있다 | lkml.iu.edu 0504.2/0670 |
| "git 개발은 2005-04-03 에 시작" (위키백과 등) | 1차 출처를 찾지 못했다 — 덱에 싣지 않는다 | — |
| 리눅스 커널 100만 커밋 | BitKeeper 시절 역사를 옮긴 63,428개를 포함한 셈이라는 단서를 함께 적는다 | linuxfoundation.org 2020-09-30 |

---

## 주장 목록

| 주장 | 출처 | 어떻게 확인했나 | 확인한 날 |
|---|---|---|---|
| 실험의 고정 시각 1700000000 은 2023-11-14 22:13:20 UTC 이다 | tools/gitenv.sh 의 GIT_*_DATE | `date -u -d @1700000000` | 2026-09-18 |
| 이 덱의 기준 git 은 2.55.0 이다 | 이 기계의 `git --version` | `git --version` → git version 2.55.0 | 2026-09-18 |
| git 2.14 에서 diff 의 들여쓰기 휴리스틱(diff.indentHeuristic)이 기본값이 되었다 | git 저장소 v2.14.0 의 Documentation/RelNotes/2.14.0.txt 21–23·69–71행 | mirror: `git show v2.14.0:Documentation/RelNotes/2.14.0.txt`, 태그 날짜 2017-08-04 | 2026-09-18 |
| Myers 1986 논문의 그림 2 가 탐욕 LCS/SES 알고리즘, 4b 절이 "A Linear Space Refinement" 이다 | E. W. Myers, "An O(ND) Difference Algorithm and Its Variations", Algorithmica 1(2), 1986 (xmailserver.org/diff2.pdf) | PDF 본문에서 "Figure 2 below"·"4b. A Linear Space Refinement" 확인 | 2026-09-18 |
| 첫 커밋 e83c5163 의 시각은 2005-04-07 15:13:13 -0700, 제목은 Initial revision of "git", the information manager from hell | git 저장소 커밋 e83c5163316f89bfbde7d9ab23ca2e25604af290 | mirror: `git show -s --format='%H %ad %s' --date=iso e83c5163` | 2026-09-18 |
| git 을 떠나기 전 커널은 BitKeeper 를 3년 썼다("We've been using BK for three years") | LKML "Kernel SCM saga..", 2005-04-06 | docs/mail-kernel-scm-saga.txt 인용 | 2026-09-18 |
| Torvalds 는 "Kernel SCM saga.." 추신에서 subversion 대신 monotone 을 읽어 보라고 했다 | 같은 메일 PS | docs/mail-kernel-scm-saga.txt 인용 | 2026-09-18 |
| e83c5163 에는 파일 11개(Makefile, README, cache.h, cat-file.c, commit-tree.c, init-db.c, read-cache.c, read-tree.c, show-diff.c, update-cache.c, write-tree.c)가 있다 | 커밋 e83c5163 | mirror: git ls-tree e83c5163 | 2026-09-18 |
| Junio C Hamano 의 첫 커밋은 2005-04-12(31cedfb95, 작성 날짜) | 커밋 31cedfb95 | mirror: git log --reverse --author=Junio v1.0.0 | 2026-09-18 |
| 첫 머지 커밋은 2005-04-18(b51ad4314) | 커밋 b51ad4314 | mirror: git log --reverse --merges v1.0.0 | 2026-09-18 |
| v0.99 태그에는 태거 날짜가 없고, 가리키는 커밋은 2005-07-10 | 태그 v0.99 | mirror: git for-each-ref · git log -1 v0.99 | 2026-09-18 |
| 1.0.0 까지 커밋 2,930개·기여자 115명, 2.0.0 까지 36,430개, 2.55.0 까지 81,348개·2,335명 | 태그들 | mirror: rev-list --count · shortlog -sn (data/growth.tsv) | 2026-09-18 |
| 2026-09 기준 최신 정식판은 git 2.55.0(태그 2026-06-29), 다음 판은 v2.56.0-rc1(2026-09-16) | 태그 v2.55.0 · v2.56.0-rc1 | mirror(2026-09-18 복제): git for-each-ref --sort=-creatordate | 2026-09-18 |
| 2026-09 기준 Git 3.0 은 출시일이 정해지지 않았고, SHA-256 기본·reftable 기본·main 기본 브랜치·Rust 필수를 계획한다 | Documentation/BreakingChanges.adoc (v2.55.0) | docs/BreakingChanges.txt 의 Git 3.0 절 인용 | 2026-09-18 |
| 2.49.0 에 Rust 외부 언어 인터페이스가 들어왔다 | RelNotes 2.49.0 · BreakingChanges | docs 인용 | 2026-09-18 |
| 2.26.0 에서 프로토콜 v2 가 기본이 됐다가 2.27.0 에서 내렸고 2.29.0 에서 다시 기본이 됐다 | RelNotes 2.26.0·2.27.0·2.29.0 | docs 인용 | 2026-09-18 |
| 2.9.0 부터 diff·log 가 기본으로 이름 변경을 감지한다 | RelNotes 2.9.0 | docs 인용 | 2026-09-18 |
| 2.0.0 에서 push.default 를 정하지 않은 push 가 matching 에서 simple 로 바뀌었다 | RelNotes 2.0.0 | docs 인용 | 2026-09-18 |
| 2.37.0 에 크러프트 팩이 들어오고 2.41.0 에서 gc 의 기본이 됐다 | RelNotes 2.37.0·2.41.0 | docs 인용 | 2026-09-18 |
| Subversion 1.0.0 은 2004-02-23, Milestone 1 은 2000-10-20 | subversion.apache.org release-history | 원문 curl | 2026-09-18 |
| SCCS 논문 1975(IEEE TSE), RCS 논문 1985(SP&E), CVS 셸 스크립트 1986(Grune), CVS II 1990(Berliner) | 각 논문 서지 · Berliner 논문 본문 | WebSearch 서지 + 논문 PDF 본문 | 2026-09-18 |
| GitHub 정식 공개 2008-04-10 | github.blog "We launched" | 원문 curl | 2026-09-18 |
| Microsoft 의 GitHub 인수 발표 2018-06-04(75억 달러), 완료 2018-10-26 | news.microsoft.com · blogs.microsoft.com | 원문 curl | 2026-09-18 |
| GitHub 새 저장소의 기본 브랜치 main — 2020-10-01 | GitHub Changelog | 원문 curl | 2026-09-18 |
| SHAttered 2017-02-23, SHA-1 계산 9,223,372,036,854,775,808 번 | Google Security Blog | 원문 curl | 2026-09-18 |
| Windows 코드 약 350만 파일·약 300GB·엔지니어 약 4,000명(2017-05-24) | Brian Harry 블로그 | 원문 curl | 2026-09-18 |
| 리눅스 커널 100만 번째 커밋 — Ricardo Neri 의 85b23fbc7d88(2020-07-26), BitKeeper 시절 63,428개 포함 | Linux Foundation 블로그 2020-09-30 | 원문 curl | 2026-09-18 |
| CVE 40건과 고쳐진 판 | Documentation/RelNotes/*.adoc (v2.55.0) | tools/make_data.py → data/cves.tsv | 2026-09-18 |
