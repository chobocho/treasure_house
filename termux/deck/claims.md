# 주장 대장 — 이 덱이 적는 모든 사실의 출처

> **규칙: 슬라이드에 적기 전에 여기 먼저 적는다.** (PLAN.md §0.3)
>
> 날짜·버전 번호·안드로이드 판별 동작·정책 사건(Play 스토어 동결, F-Droid,
> targetSdk 변경, 팬텀 프로세스 한도)·저장소 사실·사람 — Termux 이야기는
> "다들 아는" 주장이 판 하나나 해 하나씩 어긋나 있는 경우가 많다. 기억으로
> 적을 수 있을 것 같은 것일수록 반드시 틀린다.
>
> 출처의 우선순위 (위가 강하다):
>
> 1. upstream 소스나 커밋 그 자체 — `sources/<저장소>@<sha>` 를
>    `<!--SRC-->` 배지로 인용한다(PLAN.md §3.2).
> 2. upstream 문서를 글로 받은 것 — wiki.termux.com, termux-packages
>    GitHub 위키, termux-app·termux-api·termux-exec README,
>    agnostic-apollo 의 Android-Docs.
> 3. 안드로이드 개발자 문서(AOSP 소스나 developer.android.com) — OS 동작.
> 4. GitHub 이슈·릴리스 페이지 — **번호·태그로.**
> 5. 뉴스·블로그 — 커뮤니티 역사에만, 날짜와 함께.
>
> 근거를 못 찾은 문장은 둘 중 하나다: 빼거나,
> 슬라이드에 `<span class="unv">미확인</span>` 을 붙여 모른다고 적는다.
>
> **지식 기준일 규율** — 2025년 이후의 일(최신 릴리스, Play 스토어 판 상태,
> Android 15/16 동작, glibc 패키지, termux-x11 상태)은 만들 때 가져오기나
> WebSearch 로 다시 확인하고 본문에 "2026-09 기준" 을 박는다.
> `check_claims.py` 가 같은 장에 도장이 없으면 빌드를 멈춘다. (PLAN.md §0.4)

## 적는 꼴

한 줄에 주장 하나. 칸은 넷이다.

```
| 주장 | 출처 | 어떻게 확인했나 | 확인한 날 |
```

- **주장** — 슬라이드에 적힐 문장 그대로. "대략", "약" 같은 말을 빼고 수를 적는다.
- **출처** — `저장소@sha7:경로:줄`, 문서 URL(+리비전 id), 이슈 번호 중 가장 강한 것.
- **어떻게 확인했나** — `git show <sha>:<경로> 12–30행` · `wiki revid 1234 본문`
  · `out/dpkg_stats.txt 캡처` 처럼, 다음 사람이 되짚을 수 있게.
- **확인한 날** — YYYY-MM-DD. 빠르게 바뀌는 사실은 이 날짜가 곧 유효기간이다.

`deck/check_claims.py` 가 조각 산문에 적힌 네 자리 연도를 전부 훑어,
이 파일이나 `data/*.tsv` 에 없으면 빌드를 멈춘다. 연도처럼 보이지만
연도가 아닌 수는 `deck/years_ok.txt` 에 적는다.

## 확인해야 할 함정 (PLAN.md §3.1 — 아직 어느 것도 주장이 아니다)

아래는 "틀리기 쉬운 자리" 의 목록일 뿐이다. 3단계에서 출처를 붙여 위의
꼴로 옮기거나 미확인으로 남긴다. 이 목록의 문장을 그대로 슬라이드에
옮기지 말 것.

- 누가 언제 시작했나 — 첫 커밋 날짜는 GitHub API 의 커밋 목록 끝에서.
- 터미널 에뮬레이터의 계보 — `terminal-emulator/` 머리 주석의 저작권 표시.
- Play 스토어 판이 오래 멈춘 까닭 — Android 10(API 29)의 앱 데이터 실행
  제한과 targetSdk 의 관계. `Termux-and-Android-10` 위키와 이슈 번호로.
- F-Droid 배포 주기와 서명 키를 누가 가졌나 — README 의 해당 줄.
- `sharedUserId` 와 "같은 키로 서명" 규칙 — 매니페스트와 README.
- 팬텀 프로세스 한도(Android 12+)의 수와 범위 — README · 이슈 · Android-Docs,
  `settings_enable_monitor_phantom_procs` 우회. 이 기기의 값은 data/device.txt.
- termux-exec 의 시스템 링커 실행 방식 — 소스와 설치된 파일 이름.
- 부트스트랩 zip 을 누가 어디서 만들어 APK 에 싣나 — `TermuxInstaller` 와 CI.
- glibc 패키지의 이름 규칙과 러너 — 저장소에서 확인.
- 저장소 계층 main/x11/root 와 TUR — `tur-repo` 패키지, 이 기기의 sources.list.
- termux-app 판마다 요구하는 최소 안드로이드 — 태그마다 `minSdkVersion`.
- 최신 릴리스와 날짜 — `data/releases.tsv` 에서만 인용한다.

## 주장

| 주장 | 출처 | 어떻게 확인했나 | 확인한 날 |
|---|---|---|---|
